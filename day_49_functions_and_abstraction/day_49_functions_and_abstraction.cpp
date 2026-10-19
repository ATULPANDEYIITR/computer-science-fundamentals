#include <algorithm>
#include <functional>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;

/*
 * Technical case study:
 * A repository governance engine evaluates pull requests using separate
 * abstractions for pull-request state, review decisions, status checks,
 * and branch policies.
 *
 * The program demonstrates how C++ functions can be composed into a
 * deterministic policy engine rather than embedding all rules in main().
 */

enum class PullRequestState {
    Draft,
    Open,
    Closed,
    Merged
};

enum class ReviewState {
    Commented,
    Approved,
    ChangesRequested
};

struct Review {
    string reviewer;
    ReviewState state;
    string comment;
};

struct StatusCheck {
    string name;
    bool passed;
};

struct BranchProtection {
    string branch;
    size_t requiredApprovals;
    bool requirePassingChecks;
    bool requireConversationResolution;
    bool allowForcePush;
    bool allowDirectPush;
};

struct PullRequest {
    int number;
    string author;
    string sourceBranch;
    string targetBranch;
    PullRequestState state = PullRequestState::Draft;
    vector<string> commits;
    vector<Review> reviews;
    vector<StatusCheck> checks;
    size_t unresolvedConversations = 0;
    bool mergeConflict = false;

    void addCommit(const string& sha) {
        if (state == PullRequestState::Closed || state == PullRequestState::Merged) {
            throw logic_error("cannot add commits after the pull request is closed");
        }

        if (sha.size() < 7 || sha.size() > 40) {
            throw invalid_argument("commit identifier must contain 7 to 40 characters");
        }

        commits.push_back(sha);
    }

    void open() {
        if (commits.empty()) {
            throw logic_error("a pull request cannot be opened without commits");
        }

        if (state != PullRequestState::Draft) {
            throw logic_error("only draft pull requests can be opened");
        }

        state = PullRequestState::Open;
    }

    void addReview(const Review& review) {
        if (state != PullRequestState::Open) {
            throw logic_error("reviews require an open pull request");
        }

        reviews.push_back(review);
    }

    void addStatusCheck(const StatusCheck& check) {
        checks.push_back(check);
    }
};

class GovernanceEngine {
private:
    BranchProtection policy;

    static size_t countApprovals(const PullRequest& pullRequest) {
        set<string> approvingReviewers;

        for (const auto& review : pullRequest.reviews) {
            if (review.state == ReviewState::Approved) {
                approvingReviewers.insert(review.reviewer);
            }
        }

        return approvingReviewers.size();
    }

    static bool hasRequestedChanges(const PullRequest& pullRequest) {
        return any_of(
            pullRequest.reviews.begin(),
            pullRequest.reviews.end(),
            [](const Review& review) {
                return review.state == ReviewState::ChangesRequested;
            }
        );
    }

    static bool checksPass(const PullRequest& pullRequest) {
        return all_of(
            pullRequest.checks.begin(),
            pullRequest.checks.end(),
            [](const StatusCheck& check) {
                return check.passed;
            }
        );
    }

public:
    explicit GovernanceEngine(BranchProtection protection)
        : policy(std::move(protection)) {}

    vector<string> evaluate(const PullRequest& pullRequest) const {
        vector<string> failures;

        if (pullRequest.targetBranch != policy.branch) {
            failures.push_back("target branch is not governed by this policy");
        }

        if (pullRequest.state != PullRequestState::Open) {
            failures.push_back("pull request is not open");
        }

        if (pullRequest.commits.empty()) {
            failures.push_back("pull request contains no commits");
        }

        if (pullRequest.mergeConflict) {
            failures.push_back("merge conflict must be resolved");
        }

        if (hasRequestedChanges(pullRequest)) {
            failures.push_back("a reviewer has requested changes");
        }

        if (countApprovals(pullRequest) < policy.requiredApprovals) {
            failures.push_back("required approval threshold has not been met");
        }

        if (policy.requirePassingChecks && !checksPass(pullRequest)) {
            failures.push_back("one or more required status checks failed");
        }

        if (policy.requireConversationResolution &&
            pullRequest.unresolvedConversations > 0) {
            failures.push_back("review conversations remain unresolved");
        }

        return failures;
    }

    bool mergeEligible(const PullRequest& pullRequest) const {
        return evaluate(pullRequest).empty();
    }

    void merge(PullRequest& pullRequest) const {
        const auto failures = evaluate(pullRequest);

        if (!failures.empty()) {
            throw logic_error(
                "merge blocked: " + failures.front()
            );
        }

        pullRequest.state = PullRequestState::Merged;
    }
};

// Function templates allow one algorithm to work across compatible types.
// This utility deliberately separates selection from the data structure.
template <typename Container, typename Predicate>
size_t countMatching(const Container& values, Predicate predicate) {
    return static_cast<size_t>(
        count_if(values.begin(), values.end(), predicate)
    );
}

class ReviewStatistics {
public:
    static map<string, size_t> approvalsByReviewer(
        const vector<PullRequest>& pullRequests
    ) {
        map<string, size_t> result;

        for (const auto& pullRequest : pullRequests) {
            for (const auto& review : pullRequest.reviews) {
                if (review.state == ReviewState::Approved) {
                    ++result[review.reviewer];
                }
            }
        }

        return result;
    }
};

static string stateName(PullRequestState state) {
    switch (state) {
        case PullRequestState::Draft:
            return "draft";
        case PullRequestState::Open:
            return "open";
        case PullRequestState::Closed:
            return "closed";
        case PullRequestState::Merged:
            return "merged";
    }

    return "unknown";
}

static void printEvaluation(
    const PullRequest& pullRequest,
    const GovernanceEngine& engine
) {
    cout << "\nPR #" << pullRequest.number
         << " [" << stateName(pullRequest.state) << "]\n";

    const auto failures = engine.evaluate(pullRequest);

    if (failures.empty()) {
        cout << "Merge eligibility: APPROVED\n";
        return;
    }

    cout << "Merge eligibility: BLOCKED\n";

    for (const auto& failure : failures) {
        cout << "  " << failure << '\n';
    }
}

int main() {
    try {
        BranchProtection mainPolicy{
            "main",
            2,
            true,
            true,
            false,
            false
        };

        GovernanceEngine engine(mainPolicy);

        PullRequest secureFeature{
            501,
            "alice",
            "feature/secure-review",
            "main"
        };

        secureFeature.addCommit("abc1234");
        secureFeature.addCommit("def5678");
        secureFeature.open();

        secureFeature.addReview({
            "reviewer-a",
            ReviewState::Approved,
            "Implementation is consistent with the policy."
        });

        secureFeature.addReview({
            "reviewer-b",
            ReviewState::Approved,
            "Validation and error handling are sufficient."
        });

        secureFeature.addStatusCheck({"unit-tests", true});
        secureFeature.addStatusCheck({"static-analysis", true});
        secureFeature.unresolvedConversations = 0;

        printEvaluation(secureFeature, engine);

        if (engine.mergeEligible(secureFeature)) {
            engine.merge(secureFeature);
        }

        cout << "Post-merge state: "
             << stateName(secureFeature.state) << '\n';

        PullRequest blockedFeature{
            502,
            "bob",
            "feature/payment-change",
            "main"
        };

        blockedFeature.addCommit("1122334");
        blockedFeature.open();

        blockedFeature.addReview({
            "reviewer-a",
            ReviewState::Approved,
            "Needs a second independent approval."
        });

        blockedFeature.addReview({
            "reviewer-c",
            ReviewState::ChangesRequested,
            "The authorization boundary is incomplete."
        });

        blockedFeature.addStatusCheck({"unit-tests", true});
        blockedFeature.addStatusCheck({"security-scan", false});
        blockedFeature.unresolvedConversations = 2;

        printEvaluation(blockedFeature, engine);

        cout << "\nReviewer approval counts:\n";

        vector<PullRequest> history{secureFeature, blockedFeature};
        const auto statistics = ReviewStatistics::approvalsByReviewer(history);

        for (const auto& [reviewer, count] : statistics) {
            cout << reviewer << ": " << count << '\n';
        }

        const size_t failedChecks = countMatching(
            blockedFeature.checks,
            [](const StatusCheck& check) {
                return !check.passed;
            }
        );

        cout << "\nFailed status checks: " << failedChecks << '\n';

        // A policy is intentionally enforced in the service rather than
        // trusting callers to decide whether a protected branch is safe.
        try {
            engine.merge(blockedFeature);
        } catch (const logic_error& error) {
            cout << "Expected merge rejection: "
                 << error.what() << '\n';
        }

        // Demonstrate the distinction between "approval exists" and
        // "approval is sufficient": duplicate approval by the same reviewer
        // cannot inflate the threshold because the engine uses a set.
        PullRequest duplicateApproval{
            503,
            "carol",
            "feature/documentation",
            "main"
        };

        duplicateApproval.addCommit("7654321");
        duplicateApproval.open();

        duplicateApproval.addReview({
            "reviewer-a",
            ReviewState::Approved,
            "Approved."
        });

        duplicateApproval.addReview({
            "reviewer-a",
            ReviewState::Approved,
            "Repeated approval by the same reviewer."
        });

        duplicateApproval.addStatusCheck({"unit-tests", true});

        printEvaluation(duplicateApproval, engine);

        cout << "\nCase-study design:\n";
        cout << "PullRequest owns change state and review data.\n";
        cout << "BranchProtection expresses repository-level governance.\n";
        cout << "GovernanceEngine evaluates merge eligibility without mutating the request.\n";
        cout << "ReviewStatistics provides a separate analytical abstraction.\n";

    } catch (const exception& error) {
        cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
