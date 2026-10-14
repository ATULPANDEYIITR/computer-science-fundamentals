#include <algorithm>
#include <chrono>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

/*
 * Repository-independent operating-system security case study:
 * an enterprise host access-control decision engine.
 *
 * C++17 implementation of identity sessions, discretionary access control,
 * role-based permissions, mandatory sensitivity labels, explicit denials,
 * audit records, and administrative boundaries.
 *
 * This is a policy simulation, not an operating-system enforcement mechanism.
 */

using Clock = std::chrono::system_clock;
using TimePoint = Clock::time_point;

enum class Right : std::uint8_t {
    Read = 1,
    Write = 2,
    Execute = 4
};

unsigned bits(Right right) {
    return static_cast<unsigned>(right);
}

bool has_right(unsigned rights, Right requested) {
    return (rights & bits(requested)) == bits(requested);
}

std::string right_name(Right right) {
    switch (right) {
        case Right::Read: return "READ";
        case Right::Write: return "WRITE";
        case Right::Execute: return "EXECUTE";
    }
    throw std::invalid_argument("Unknown right");
}

enum class Label {
    Public = 0,
    Internal = 1,
    Confidential = 2,
    Restricted = 3
};

std::string label_name(Label label) {
    switch (label) {
        case Label::Public: return "PUBLIC";
        case Label::Internal: return "INTERNAL";
        case Label::Confidential: return "CONFIDENTIAL";
        case Label::Restricted: return "RESTRICTED";
    }
    throw std::invalid_argument("Unknown label");
}

struct Identity {
    std::string id;
    std::set<std::string> groups;
    Label clearance;
    bool enabled = true;
    bool administrator = false;
};

struct FileObject {
    std::string path;
    std::string owner;
    std::string group;
    unsigned mode;
    Label classification;
    bool immutable = false;
};

struct Session {
    std::string token;
    std::string principal;
    TimePoint expires_at;
    bool authenticated = false;
};

struct AuditRecord {
    std::string principal;
    std::string operation;
    std::string resource;
    bool allowed;
    std::string reason;
};

class AccessControlEngine {
private:
    std::map<std::string, Identity> identities_;
    std::map<std::string, FileObject> files_;
    std::map<std::string, Session> sessions_;
    std::map<std::string, unsigned> role_rights_;
    std::map<std::string, std::set<std::string>> user_roles_;
    std::set<std::pair<std::string, std::string>> explicit_denies_;
    std::vector<AuditRecord> audit_;

    void record(const std::string& principal,
                const std::string& operation,
                const std::string& resource,
                bool allowed,
                const std::string& reason) {
        audit_.push_back({principal, operation, resource, allowed, reason});
    }

    static unsigned class_rights(unsigned mode, unsigned shift) {
        return (mode >> shift) & 7U;
    }

public:
    void add_identity(Identity identity) {
        if (identity.id.empty() || identities_.count(identity.id)) {
            throw std::invalid_argument("Identity must be named and unique");
        }
        identities_.emplace(identity.id, std::move(identity));
    }

    void add_role(const std::string& role, unsigned rights) {
        if (role.empty() || (rights & ~7U) != 0 || role_rights_.count(role)) {
            throw std::invalid_argument("Invalid or duplicate role");
        }
        role_rights_[role] = rights;
    }

    void assign_role(const std::string& user, const std::string& role) {
        if (!identities_.count(user) || !role_rights_.count(role)) {
            throw std::invalid_argument("Unknown user or role");
        }
        user_roles_[user].insert(role);
    }

    void add_file(FileObject file) {
        if (file.path.empty() || file.path.front() != '/' ||
            file.path.find("/../") != std::string::npos ||
            file.path.ends_with("/..")) {
            throw std::invalid_argument("File path must be absolute and normalized");
        }
        if (!identities_.count(file.owner)) {
            throw std::invalid_argument("File owner must exist");
        }
        if (file.mode > 0777U || files_.count(file.path)) {
            throw std::invalid_argument("Invalid mode or duplicate path");
        }
        files_.emplace(file.path, std::move(file));
    }

    void establish_session(const std::string& token,
                           const std::string& user,
                           std::chrono::seconds lifetime) {
        auto identity = identities_.find(user);
        if (token.empty() || sessions_.count(token) ||
            identity == identities_.end() || !identity->second.enabled ||
            lifetime <= std::chrono::seconds::zero()) {
            throw std::invalid_argument("Cannot establish session");
        }
        sessions_.emplace(token, Session{
            token, user, Clock::now() + lifetime, true
        });
    }

    void deny_user_resource(const std::string& user, const std::string& path) {
        if (!identities_.count(user) || !files_.count(path)) {
            throw std::invalid_argument("Unknown identity or file");
        }
        explicit_denies_.insert({user, path});
    }

    bool authorize(const std::string& token,
                   const std::string& path,
                   Right requested) {
        auto session_it = sessions_.find(token);
        std::string actor = session_it == sessions_.end()
            ? "anonymous" : session_it->second.principal;

        auto deny = [&](const std::string& reason) {
            record(actor, right_name(requested), path, false, reason);
            return false;
        };

        if (session_it == sessions_.end() ||
            !session_it->second.authenticated) {
            return deny("No authenticated session");
        }

        if (Clock::now() >= session_it->second.expires_at) {
            sessions_.erase(session_it);
            return deny("Session expired");
        }

        auto user_it = identities_.find(actor);
        auto file_it = files_.find(path);
        if (user_it == identities_.end() || !user_it->second.enabled) {
            return deny("Identity disabled or missing");
        }
        if (file_it == files_.end()) {
            return deny("File does not exist");
        }

        const Identity& user = user_it->second;
        const FileObject& file = file_it->second;

        if (explicit_denies_.count({actor, path})) {
            return deny("Explicit resource denial");
        }

        // The Unix owner/group/other selection is mutually exclusive.
        unsigned discretionary_rights;
        if (actor == file.owner) {
            discretionary_rights = class_rights(file.mode, 6);
        } else if (user.groups.count(file.group)) {
            discretionary_rights = class_rights(file.mode, 3);
        } else {
            discretionary_rights = class_rights(file.mode, 0);
        }

        if (!has_right(discretionary_rights, requested)) {
            return deny("Discretionary file mode denies operation");
        }

        // Mandatory access control is an independent restriction.
        // Administrative identity does not automatically bypass classification.
        if (static_cast<int>(user.clearance) <
            static_cast<int>(file.classification)) {
            return deny("Clearance below resource classification");
        }

        // Role permissions add a second policy layer. Ownership alone does not
        // grant EXECUTE, and administrative membership is not a universal bypass.
        unsigned assigned_rights = 0;
        auto roles = user_roles_.find(actor);
        if (roles != user_roles_.end()) {
            for (const auto& role : roles->second) {
                assigned_rights |= role_rights_.at(role);
            }
        }

        if (!has_right(assigned_rights, requested)) {
            return deny("Assigned roles do not grant requested right");
        }

        if (file.immutable && requested == Right::Write) {
            return deny("Immutable resource rejects writes");
        }

        record(actor, right_name(requested), path, true,
               "All access-control layers permit operation");
        return true;
    }

    bool revoke_session(const std::string& token) {
        auto it = sessions_.find(token);
        if (it == sessions_.end()) return false;
        record(it->second.principal, "REVOKE_SESSION", "-", true,
               "Session removed");
        sessions_.erase(it);
        return true;
    }

    void print_audit() const {
        std::cout << "\nAudit trail\n";
        for (const auto& event : audit_) {
            std::cout << std::left
                      << std::setw(14) << event.principal
                      << std::setw(10) << event.operation
                      << std::setw(32) << event.resource
                      << (event.allowed ? "ALLOW " : "DENY  ")
                      << event.reason << '\n';
        }
    }

    std::size_t denial_count() const {
        return static_cast<std::size_t>(std::count_if(
            audit_.begin(), audit_.end(),
            [](const AuditRecord& event) { return !event.allowed; }
        ));
    }
};

int main() {
    try {
        AccessControlEngine engine;

        engine.add_identity({
            "maya", {"engineering"}, Label::Confidential, true, false
        });
        engine.add_identity({
            "liam", {"support"}, Label::Internal, true, false
        });
        engine.add_identity({
            "security-admin", {"security"}, Label::Restricted, true, true
        });

        engine.add_role("reader", bits(Right::Read));
        engine.add_role("maintainer",
                        bits(Right::Read) | bits(Right::Write));
        engine.add_role("deployer",
                        bits(Right::Read) | bits(Right::Execute));

        engine.assign_role("maya", "maintainer");
        engine.assign_role("liam", "reader");
        engine.assign_role("security-admin", "deployer");

        engine.add_file({
            "/srv/engineering/design.conf",
            "maya", "engineering", 0640, Label::Confidential, false
        });
        engine.add_file({
            "/srv/engineering/deploy.sh",
            "security-admin", "security", 0750, Label::Restricted, false
        });
        engine.add_file({
            "/srv/engineering/release.lock",
            "security-admin", "security", 0644, Label::Internal, true
        });

        engine.establish_session("session-maya", "maya",
                                 std::chrono::hours(1));
        engine.establish_session("session-liam", "liam",
                                 std::chrono::hours(1));
        engine.establish_session("session-admin", "security-admin",
                                 std::chrono::hours(1));

        auto show = [](const std::string& description, bool result) {
            std::cout << description << ": "
                      << (result ? "ALLOW" : "DENY") << '\n';
        };

        show("Maya reads confidential design",
             engine.authorize("session-maya",
                              "/srv/engineering/design.conf", Right::Read));

        show("Maya writes confidential design",
             engine.authorize("session-maya",
                              "/srv/engineering/design.conf", Right::Write));

        show("Liam reads confidential design",
             engine.authorize("session-liam",
                              "/srv/engineering/design.conf", Right::Read));

        show("Admin executes deployment script",
             engine.authorize("session-admin",
                              "/srv/engineering/deploy.sh", Right::Execute));

        show("Admin writes immutable release lock",
             engine.authorize("session-admin",
                              "/srv/engineering/release.lock", Right::Write));

        engine.deny_user_resource("maya", "/srv/engineering/design.conf");
        show("Maya after explicit deny",
             engine.authorize("session-maya",
                              "/srv/engineering/design.conf", Right::Read));

        engine.revoke_session("session-maya");
        show("Maya after session revocation",
             engine.authorize("session-maya",
                              "/srv/engineering/design.conf", Right::Read));

        engine.print_audit();
        std::cout << "\nDenied operations: " << engine.denial_count() << '\n';
    } catch (const std::exception& error) {
        std::cerr << "Security configuration error: "
                  << error.what() << '\n';
        return 1;
    }
    return 0;
}
