#include <algorithm>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

/*
 * Repository governance engine.
 *
 * C++17 case study: evaluate whether a change can enter a protected release
 * branch. Value types model commits and reviews; a policy engine calculates
 * eligibility without changing the pull request.
 *
 * Compile:
 *   g++ -std=c++17 -Wall -Wextra -pedantic programming_paradigms.cpp -o paradigms
 */

enum class ReviewState {
    Commented,
    Approved,
    ChangesRequested
};

enum class PullRequestState {
    Draft,
    Open,
    Closed,
    Merged
};

struct Commit {
    std::string id;
    std::string author;
    std::set<std::string> files;
    int additions;
    int deletions;
};

struct Review {
    std::string reviewer;
    std::string commitId;
    ReviewState state;
    bool dismissed = false;
};

struct StatusCheck {
    std::string name;
    bool passed;
};

struct PullRequest {
    int number;
    std::string title;
    std::string sourceBranch;
    std::string targetBranch;
    PullRequestState state;
    std::vector<Commit> commits;
    std::vector<Review> reviews;
    std::map<std::string, bool> checks;
    bool conversationsResolved = true;
    bool linearHistory = true;
};

struct BranchPolicy {
    std::set<std::string> protectedBranches;
    std::set<std::string> requiredChecks;
    std::size_t requiredApprovals = 2;
    bool requireResolvedConversations = true;
    bool requireLinearHistory = true;
    bool restrictDirectPushes = true;
    bool prohibitForcePush = true;
    bool prohibitDeletion = true;
};

struct Decision {
    bool eligible = true;
    std::vector<std::string> reasons;

    void reject(std::string reason) {
        eligible = false;
        reasons.push_back(std::move(reason));
    }
};

class GovernanceEngine {
private:
    BranchPolicy policy_;

    static void validate(const PullRequest& pr) {
        if (pr.number <= 0 || pr.title.empty()) {
            throw std::invalid_argument(
                "Pull request requires a positive number and a title."
            );
        }

        if (pr.sourceBranch.empty() || pr.targetBranch.empty() ||
            pr.sourceBranch == pr.targetBranch) {
            throw std::invalid_argument(
                "Source and target branches must be distinct and non-empty."
            );
        }

        if (pr.commits.empty()) {
            throw std::invalid_argument(
                "Pull request must contain at least one commit."
            );
        }

        std::set<std::string> commitIds;
        for (const auto& commit : pr.commits) {
            if (commit.id.empty() || commit.author.empty() ||
                commit.files.empty()) {
                throw std::invalid_argument(
                    "Each commit requires an ID, author, and changed file."
                );
            }
            if (!commitIds.insert(commit.id).second) {
                throw std::invalid_argument("Commit IDs must be unique.");
            }
            if (commit.additions < 0 || commit.deletions < 0) {
                throw std::invalid_argument(
                    "Commit line counts cannot be negative."
                );
            }

            for (const auto& file : commit.files) {
                if (file.empty() || file.front() == '/' ||
                    file.find("../") != std::string::npos ||
                    file == "..") {
                    throw std::invalid_argument(
                        "Changed file path escapes the repository."
                    );
                }
            }
        }
    }

public:
    explicit GovernanceEngine(BranchPolicy policy)
        : policy_(std::move(policy)) {}

    Decision evaluate(const PullRequest& pr) const {
        validate(pr);
        Decision decision;

        if (pr.state == PullRequestState::Draft) {
            decision.reject("Draft pull requests are not mergeable.");
        } else if (pr.state != PullRequestState::Open) {
            decision.reject("Pull request is not open.");
        }

        const bool protectedTarget =
            policy_.protectedBranches.count(pr.targetBranch) > 0;

        // Preserve the latest active review from each reviewer. Review
        // submission order is assumed to be chronological in this fixture.
        std::map<std::string, Review> latestReviews;
        for (const auto& review : pr.reviews) {
            if (review.dismissed) {
                continue;
            }

            const auto knownCommit = std::find_if(
                pr.commits.begin(), pr.commits.end(),
                [&](const Commit& commit) {
                    return commit.id == review.commitId;
                }
            );

            if (knownCommit == pr.commits.end()) {
                decision.reject(
                    "Review references a commit outside the pull request."
                );
                continue;
            }

            latestReviews[review.reviewer] = review;
        }

        std::set<std::string> authors;
        for (const auto& commit : pr.commits) {
            authors.insert(commit.author);
        }

        std::set<std::string> approvers;
        for (const auto& entry : latestReviews) {
            const Review& review = entry.second;

            if (review.state == ReviewState::ChangesRequested) {
                decision.reject(
                    "Unresolved change request from " + review.reviewer + "."
                );
            }

            if (review.state == ReviewState::Approved) {
                if (authors.count(review.reviewer) > 0) {
                    decision.reject(
                        "Commit authors cannot approve their own change."
                    );
                } else {
                    approvers.insert(review.reviewer);
                }
            }
        }

        if (approvers.size() < policy_.requiredApprovals) {
            decision.reject(
                "Insufficient distinct eligible reviewers: " +
                std::to_string(approvers.size()) + " of " +
                std::to_string(policy_.requiredApprovals) + "."
            );
        }

        for (const auto& required : policy_.requiredChecks) {
            const auto found = pr.checks.find(required);
            if (found == pr.checks.end() || !found->second) {
                decision.reject(
                    "Required status check is missing or failing: " +
                    required + "."
                );
            }
        }

        if (protectedTarget && policy_.requireResolvedConversations &&
            !pr.conversationsResolved) {
            decision.reject(
                "Protected branch requires resolved review conversations."
            );
        }

        if (protectedTarget && policy_.requireLinearHistory &&
            !pr.linearHistory) {
            decision.reject(
                "Protected branch requires linear history."
            );
        }

        return decision;
    }

    // These controls model protected-branch operations independently from
    // pull-request merge evaluation.
    bool directPushAllowed(const std::string& branch, bool authorizedBypass) const {
        if (policy_.protectedBranches.count(branch) == 0) {
            return true;
        }
        return !policy_.restrictDirectPushes || authorizedBypass;
    }

    bool forcePushAllowed(const std::string& branch, bool authorizedBypass) const {
        if (policy_.protectedBranches.count(branch) == 0) {
            return true;
        }
        return !policy_.prohibitForcePush || authorizedBypass;
    }

    bool deletionAllowed(const std::string& branch, bool authorizedBypass) const {
        if (policy_.protectedBranches.count(branch) == 0) {
            return true;
        }
        return !policy_.prohibitDeletion || authorizedBypass;
    }
};

static int countUniqueChangedFiles(const PullRequest& pr) {
    std::set<std::string> files;
    for (const auto& commit : pr.commits) {
        files.insert(commit.files.begin(), commit.files.end());
    }
    return static_cast<int>(files.size());
}

static int countNetLines(const PullRequest& pr) {
    int net = 0;
    for (const auto& commit : pr.commits) {
        net += commit.additions - commit.deletions;
    }
    return net;
}

static std::string stateName(ReviewState state) {
    switch (state) {
        case ReviewState::Commented:
            return "commented";
        case ReviewState::Approved:
            return "approved";
        case ReviewState::ChangesRequested:
            return "changes requested";
    }
    throw std::logic_error("Unknown review state.");
}

int main() {
    try {
        BranchPolicy policy{
            {"main", "release"},
            {"unit-tests", "security-scan", "integration-tests"},
            2,
            true,
            true,
            true,
            true,
            true
        };

        GovernanceEngine engine(policy);

        PullRequest pr{
            517,
            "Enforce signed session expiry validation",
            "feature/session-expiry",
            "main",
            PullRequestState::Open,
            {
                {"f201", "maya",
                    {"src/session.cpp", "tests/session_test.cpp"}, 95, 18},
                {"f202", "liam",
                    {"src/session.cpp", "docs/security.md"}, 37, 9}
            },
            {
                {"olivia", "f202", ReviewState::Approved, false},
                {"ethan", "f202", ReviewState::Approved, false},
                {"maya", "f202", ReviewState::Approved, false}
            },
            {
                {"unit-tests", true},
                {"security-scan", true},
                {"integration-tests", true}
            },
            true,
            true
        };

        std::cout << "Repository governance case study\n";
        std::cout << "Pull request #" << pr.number << ": " << pr.title << '\n';
        std::cout << "Changed files: " << countUniqueChangedFiles(pr) << '\n';
        std::cout << "Net line change: " << countNetLines(pr) << '\n';

        std::cout << "\nReview states\n";
        for (const auto& review : pr.reviews) {
            std::cout << review.reviewer << ": "
                      << stateName(review.state);
            if (review.dismissed) {
                std::cout << " (dismissed)";
            }
            std::cout << '\n';
        }

        std::cout << "\nMerge eligibility\n";
        Decision decision = engine.evaluate(pr);
        std::cout << (decision.eligible ? "ELIGIBLE" : "BLOCKED") << '\n';
        for (const auto& reason : decision.reasons) {
            std::cout << "  " << reason << '\n';
        }

        std::cout << "\nProtected branch operations\n";
        std::cout << "Direct push without bypass: "
                  << std::boolalpha
                  << engine.directPushAllowed("main", false) << '\n';
        std::cout << "Force push without bypass: "
                  << engine.forcePushAllowed("main", false) << '\n';
        std::cout << "Delete main without bypass: "
                  << engine.deletionAllowed("main", false) << '\n';
        std::cout << "Direct push to feature branch: "
                  << engine.directPushAllowed("feature/cleanup", false) << '\n';

        std::cout << "\nFailure simulation\n";
        pr.checks["security-scan"] = false;
        pr.conversationsResolved = false;
        pr.linearHistory = false;

        Decision failed = engine.evaluate(pr);
        std::cout << (failed.eligible ? "ELIGIBLE" : "BLOCKED") << '\n';
        for (const auto& reason : failed.reasons) {
            std::cout << "  " << reason << '\n';
        }

        std::cout << "\nDismissed approval simulation\n";
        pr.reviews[0].dismissed = true;
        Decision dismissed = engine.evaluate(pr);
        for (const auto& reason : dismissed.reasons) {
            std::cout << "  " << reason << '\n';
        }
    } catch (const std::exception& error) {
        std::cerr << "Governance error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
