#include <algorithm>
#include <chrono>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;

// ============================================================
// Application Layer Protocol Governance Engine
// C++17
// ============================================================

enum class Protocol {
    HTTP,
    HTTPS,
    DNS,
    SMTP,
    FTP,
    SSH
};

enum class Transport {
    TCP,
    UDP,
    TCP_UDP
};

enum class SecurityLevel {
    PLAINTEXT,
    TLS,
    SSH_ENCRYPTION
};

enum class ConnectionState {
    DISCONNECTED,
    CONNECTING,
    CONNECTED,
    AUTHENTICATED,
    CLOSED,
    FAILED
};

enum class Operation {
    REQUEST,
    RESOLUTION,
    EMAIL_SUBMISSION,
    FILE_TRANSFER,
    REMOTE_COMMAND
};

string toString(Protocol protocol) {
    switch (protocol) {
        case Protocol::HTTP: return "HTTP";
        case Protocol::HTTPS: return "HTTPS";
        case Protocol::DNS: return "DNS";
        case Protocol::SMTP: return "SMTP";
        case Protocol::FTP: return "FTP";
        case Protocol::SSH: return "SSH";
    }

    throw invalid_argument("Unknown protocol.");
}

struct ProtocolDefinition {
    Protocol protocol;
    int port;
    Transport transport;
    SecurityLevel security;
    string purpose;
};

class ProtocolRegistry {
private:
    map<Protocol, ProtocolDefinition> definitions;

public:
    ProtocolRegistry() {
        definitions.emplace(
            Protocol::HTTP,
            ProtocolDefinition{
                Protocol::HTTP, 80, Transport::TCP,
                SecurityLevel::PLAINTEXT,
                "Web communication"
            }
        );

        definitions.emplace(
            Protocol::HTTPS,
            ProtocolDefinition{
                Protocol::HTTPS, 443, Transport::TCP,
                SecurityLevel::TLS,
                "Secure web communication"
            }
        );

        definitions.emplace(
            Protocol::DNS,
            ProtocolDefinition{
                Protocol::DNS, 53, Transport::TCP_UDP,
                SecurityLevel::PLAINTEXT,
                "Domain name resolution"
            }
        );

        definitions.emplace(
            Protocol::SMTP,
            ProtocolDefinition{
                Protocol::SMTP, 587, Transport::TCP,
                SecurityLevel::TLS,
                "Email submission"
            }
        );

        definitions.emplace(
            Protocol::FTP,
            ProtocolDefinition{
                Protocol::FTP, 21, Transport::TCP,
                SecurityLevel::PLAINTEXT,
                "File transfer control"
            }
        );

        definitions.emplace(
            Protocol::SSH,
            ProtocolDefinition{
                Protocol::SSH, 22, Transport::TCP,
                SecurityLevel::SSH_ENCRYPTION,
                "Secure remote administration"
            }
        );
    }

    const ProtocolDefinition& get(Protocol protocol) const {
        auto it = definitions.find(protocol);

        if (it == definitions.end()) {
            throw invalid_argument("Protocol not registered.");
        }

        return it->second;
    }

    void display() const {
        cout << left
             << setw(10) << "Protocol"
             << setw(10) << "Port"
             << setw(15) << "Encryption"
             << "Purpose\n";

        for (const auto& [protocol, definition] : definitions) {
            string security;

            switch (definition.security) {
                case SecurityLevel::PLAINTEXT:
                    security = "None";
                    break;
                case SecurityLevel::TLS:
                    security = "TLS";
                    break;
                case SecurityLevel::SSH_ENCRYPTION:
                    security = "SSH";
                    break;
            }

            cout << setw(10) << toString(protocol)
                 << setw(10) << definition.port
                 << setw(15) << security
                 << definition.purpose << '\n';
        }
    }
};

// ============================================================
// Domain entities
// ============================================================

struct NetworkEndpoint {
    string hostname;
    int port;

    void validate() const {
        if (hostname.empty() || hostname.size() > 253) {
            throw invalid_argument("Invalid hostname.");
        }

        if (port < 1 || port > 65535) {
            throw invalid_argument("Invalid network port.");
        }

        if (hostname.find_first_of(" \t\r\n") != string::npos) {
            throw invalid_argument("Whitespace in hostname.");
        }
    }
};

struct ProtocolRequest {
    uint64_t id;
    Protocol protocol;
    NetworkEndpoint endpoint;
    Operation operation;
    bool authenticated;
    bool certificate_verified;
    bool host_key_verified;
    size_t payload_bytes;
};

struct ProtocolPolicy {
    set<Protocol> permitted_protocols;
    set<int> permitted_ports;

    bool require_encryption = true;
    bool require_authentication = true;
    size_t max_payload_bytes = 1024 * 1024;
};

// ============================================================
// Policy evaluation
// ============================================================

struct PolicyDecision {
    bool allowed;
    vector<string> violations;
};

class PolicyEngine {
private:
    const ProtocolRegistry& registry;

public:
    explicit PolicyEngine(const ProtocolRegistry& r)
        : registry(r) {}

    PolicyDecision evaluate(
        const ProtocolRequest& request,
        const ProtocolPolicy& policy
    ) const {

        PolicyDecision decision{true, {}};

        try {
            request.endpoint.validate();

            const auto& definition = registry.get(request.protocol);

            if (!policy.permitted_protocols.count(request.protocol)) {
                decision.violations.push_back(
                    "Protocol prohibited by network policy."
                );
            }

            if (!policy.permitted_ports.count(request.endpoint.port)) {
                decision.violations.push_back(
                    "Destination port prohibited."
                );
            }

            if (
                policy.require_encryption &&
                definition.security == SecurityLevel::PLAINTEXT
            ) {
                decision.violations.push_back(
                    "Encryption requirement not satisfied."
                );
            }

            if (
                policy.require_authentication &&
                !request.authenticated
            ) {
                decision.violations.push_back(
                    "Authentication required."
                );
            }

            if (
                request.payload_bytes > policy.max_payload_bytes
            ) {
                decision.violations.push_back(
                    "Payload exceeds configured limit."
                );
            }

            if (
                request.protocol == Protocol::HTTPS &&
                !request.certificate_verified
            ) {
                decision.violations.push_back(
                    "HTTPS certificate verification failed."
                );
            }

            if (
                request.protocol == Protocol::SSH &&
                !request.host_key_verified
            ) {
                decision.violations.push_back(
                    "SSH host key is not trusted."
                );
            }

        } catch (const exception& error) {
            decision.violations.push_back(error.what());
        }

        decision.allowed = decision.violations.empty();

        return decision;
    }
};

// ============================================================
// Connection state machine
// ============================================================

class ProtocolConnection {
private:
    ConnectionState state = ConnectionState::DISCONNECTED;
    Protocol protocol;

public:
    explicit ProtocolConnection(Protocol p)
        : protocol(p) {}

    ConnectionState getState() const {
        return state;
    }

    void connect() {
        if (state != ConnectionState::DISCONNECTED) {
            throw logic_error("Connection already initialized.");
        }

        state = ConnectionState::CONNECTING;
        state = ConnectionState::CONNECTED;
    }

    void authenticate() {
        if (state != ConnectionState::CONNECTED) {
            throw logic_error("Connection is not ready for authentication.");
        }

        state = ConnectionState::AUTHENTICATED;
    }

    void close() {
        if (state == ConnectionState::CLOSED) {
            return;
        }

        state = ConnectionState::CLOSED;
    }

    void fail() {
        state = ConnectionState::FAILED;
    }
};

// ============================================================
// DNS record management
// ============================================================

enum class DNSRecordType {
    A,
    AAAA,
    MX,
    CNAME,
    TXT
};

struct DNSRecord {
    string hostname;
    DNSRecordType type;
    string value;
    uint32_t ttl;
};

class DNSDatabase {
private:
    unordered_map<string, vector<DNSRecord>> records;

    static string key(const string& hostname) {
        string normalized = hostname;

        transform(
            normalized.begin(),
            normalized.end(),
            normalized.begin(),
            ::tolower
        );

        return normalized;
    }

public:
    void addRecord(const DNSRecord& record) {
        if (record.hostname.empty() || record.value.empty()) {
            throw invalid_argument("DNS fields cannot be empty.");
        }

        if (record.ttl == 0) {
            throw invalid_argument("DNS TTL must be positive.");
        }

        if (record.type == DNSRecordType::A) {
            string value = record.value;

            size_t first = value.find('.');

            if (first == string::npos) {
                throw invalid_argument("Invalid IPv4 address.");
            }

            int octets = 0;
            size_t start = 0;

            while (start <= value.size()) {
                size_t end = value.find('.', start);

                string part = value.substr(
                    start,
                    end == string::npos
                        ? string::npos
                        : end - start
                );

                if (
                    part.empty() ||
                    part.size() > 3 ||
                    !all_of(part.begin(), part.end(), ::isdigit) ||
                    stoi(part) > 255
                ) {
                    throw invalid_argument("Invalid IPv4 address.");
                }

                ++octets;

                if (end == string::npos) {
                    break;
                }

                start = end + 1;
            }

            if (octets != 4) {
                throw invalid_argument("IPv4 requires four octets.");
            }
        }

        records[key(record.hostname)].push_back(record);
    }

    vector<DNSRecord> lookup(
        const string& hostname,
        DNSRecordType type
    ) const {

        auto it = records.find(key(hostname));

        if (it == records.end()) {
            return {};
        }

        vector<DNSRecord> result;

        copy_if(
            it->second.begin(),
            it->second.end(),
            back_inserter(result),
            [type](const DNSRecord& record) {
                return record.type == type;
            }
        );

        return result;
    }
};

// ============================================================
// Protocol audit and performance metrics
// ============================================================

struct AuditEntry {
    uint64_t request_id;
    Protocol protocol;
    bool accepted;
    double duration_ms;
    string reason;
};

class ProtocolAudit {
private:
    vector<AuditEntry> entries;

public:
    void record(const AuditEntry& entry) {
        entries.push_back(entry);
    }

    size_t failures() const {
        return count_if(
            entries.begin(),
            entries.end(),
            [](const AuditEntry& entry) {
                return !entry.accepted;
            }
        );
    }

    void report() const {
        cout << "\nProtocol audit report\n";

        for (const auto& entry : entries) {
            cout << "Request " << entry.request_id
                 << " | " << toString(entry.protocol)
                 << " | "
                 << (entry.accepted ? "ACCEPTED" : "REJECTED")
                 << " | " << entry.duration_ms << " ms"
                 << " | " << entry.reason << '\n';
        }

        cout << "Total requests: " << entries.size() << '\n';
        cout << "Failed requests: " << failures() << '\n';
    }
};

// ============================================================
// Application service
// ============================================================

class ProtocolGovernanceService {
private:
    ProtocolRegistry registry;
    PolicyEngine engine;
    ProtocolPolicy policy;
    ProtocolAudit audit;
    uint64_t nextId = 1;

public:
    ProtocolGovernanceService()
        : engine(registry) {

        policy.permitted_protocols = {
            Protocol::HTTPS,
            Protocol::DNS,
            Protocol::SMTP,
            Protocol::SSH
        };

        policy.permitted_ports = {
            53, 443, 587, 22
        };

        policy.require_encryption = true;
        policy.require_authentication = true;
        policy.max_payload_bytes = 1024 * 1024;
    }

    void displayRegistry() const {
        registry.display();
    }

    PolicyDecision process(
        Protocol protocol,
        const NetworkEndpoint& endpoint,
        Operation operation,
        bool authenticated,
        bool certificateVerified,
        bool hostKeyVerified,
        size_t payloadBytes
    ) {

        auto start = chrono::steady_clock::now();

        ProtocolRequest request{
            nextId++,
            protocol,
            endpoint,
            operation,
            authenticated,
            certificateVerified,
            hostKeyVerified,
            payloadBytes
        };

        PolicyDecision decision = engine.evaluate(
            request,
            policy
        );

        auto end = chrono::steady_clock::now();

        double duration = chrono::duration<double, milli>(
            end - start
        ).count();

        string reason = decision.allowed
            ? "All controls satisfied."
            : decision.violations.front();

        audit.record({
            request.id,
            protocol,
            decision.allowed,
            duration,
            reason
        });

        return decision;
    }

    void displayAudit() const {
        audit.report();
    }
};

// ============================================================
// Demonstration
// ============================================================

int main() {
    try {
        cout << "APPLICATION LAYER PROTOCOL GOVERNANCE\n\n";

        ProtocolGovernanceService service;

        service.displayRegistry();

        cout << "\nPolicy evaluation\n";

        auto https = service.process(
            Protocol::HTTPS,
            {"api.example.com", 443},
            Operation::REQUEST,
            true,
            true,
            false,
            2048
        );

        cout << "HTTPS request: "
             << (https.allowed ? "ALLOWED" : "DENIED")
             << '\n';

        auto http = service.process(
            Protocol::HTTP,
            {"api.example.com", 80},
            Operation::REQUEST,
            true,
            false,
            false,
            1024
        );

        cout << "HTTP request: "
             << (http.allowed ? "ALLOWED" : "DENIED")
             << '\n';

        auto ssh = service.process(
            Protocol::SSH,
            {"server.example.com", 22},
            Operation::REMOTE_COMMAND,
            true,
            false,
            true,
            512
        );

        cout << "SSH request: "
             << (ssh.allowed ? "ALLOWED" : "DENIED")
             << '\n';

        auto untrustedSSH = service.process(
            Protocol::SSH,
            {"server.example.com", 22},
            Operation::REMOTE_COMMAND,
            true,
            false,
            false,
            512
        );

        cout << "Untrusted SSH request: "
             << (untrustedSSH.allowed ? "ALLOWED" : "DENIED")
             << '\n';

        // DNS data model.
        DNSDatabase dns;

        dns.addRecord({
            "example.com",
            DNSRecordType::A,
            "192.0.2.10",
            300
        });

        dns.addRecord({
            "example.com",
            DNSRecordType::MX,
            "mail.example.com",
            600
        });

        cout << "\nDNS lookup:\n";

        for (const auto& record : dns.lookup(
            "example.com",
            DNSRecordType::A
        )) {
            cout << record.hostname
                 << " -> " << record.value
                 << " TTL=" << record.ttl << '\n';
        }

        // Connection lifecycle.
        ProtocolConnection connection(Protocol::SSH);

        connection.connect();
        connection.authenticate();

        cout << "\nSSH connection authenticated.\n";

        connection.close();

        cout << "SSH connection closed.\n";

        service.displayAudit();

    } catch (const exception& error) {
        cerr << "Application error: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
