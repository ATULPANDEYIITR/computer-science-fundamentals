#include <algorithm>
#include <chrono>
#include <exception>
#include <functional>
#include <iomanip>
#include <iostream>
#include <memory>
#include <optional>
#include <sstream>
#include <string>
#include <type_traits>
#include <unordered_map>
#include <utility>
#include <vector>

/*
 * Case study: a type-safe repository policy engine.
 *
 * The system demonstrates:
 * - lexical and block scope
 * - name binding
 * - object lifetime through RAII and smart pointers
 * - static typing and compile-time constraints
 * - runtime polymorphism
 * - templates and concepts
 * - std::variant-style type alternatives
 *
 * The repository domain is used because type, lifetime, and binding
 * decisions have concrete consequences in a long-running service.
 */

namespace governance {

enum class ReviewState {
    Pending,
    Approved,
    ChangesRequested
};

enum class PullRequestState {
    Draft,
    Open,
    Closed,
    Merged
};

struct StatusCheck {
    std::string name;
    bool passed;
};

struct Review {
    std::string reviewer;
    ReviewState state;
    std::string comment;
};

struct PullRequest {
    int number;
    std::string sourceBranch;
    std::string targetBranch;
    PullRequestState state;
    std::vector<Review> reviews;
    std::vector<StatusCheck> checks;
};

struct BranchPolicy {
    std::string branchName;
    int requiredApprovals;
    bool requirePassingChecks;
    bool allowForcePush;
    bool allowDirectPush;
};

class AuditLog {
private:
    std::vector<std::string> entries_;

public:
    void record(const std::string& event) {
        entries_.push_back(event);
    }

    void print() const {
        for (const auto& entry : entries_) {
            std::cout << "AUDIT: " << entry << '\n';
        }
    }
};

/*
 * RAII binds resource ownership to object lifetime.
 * The AuditLog is destroyed automatically when its owning scope ends.
 */
class RepositorySession {
private:
    std::string repository_;
    std::unique_ptr<AuditLog> audit_;

public:
    explicit RepositorySession(std::string repository)
        : repository_(std::move(repository)),
          audit_(std::make_unique<AuditLog>()) {
        audit_->record("Opened repository session: " + repository_);
    }

    ~RepositorySession() {
        audit_->record("Closing repository session: " + repository_);
        audit_->print();
    }

    AuditLog& audit() {
        return *audit_;
    }

    const std::string& repository() const {
        return repository_;
    }
};

class MergeEligibilityEngine {
private:
    static int approvedReviews(const PullRequest& pr) {
        int count = 0;

        for (const Review& review : pr.reviews) {
            if (review.state == ReviewState::Approved) {
                ++count;
            }
        }

        return count;
    }

    static bool checksPassed(const PullRequest& pr) {
        return std::all_of(
            pr.checks.begin(),
            pr.checks.end(),
            [](const StatusCheck& check) {
                return check.passed;
            }
        );
    }

public:
    bool eligible(
        const PullRequest& pr,
        const BranchPolicy& policy,
        std::string& reason
    ) const {
        if (pr.state != PullRequestState::Open) {
            reason = "Pull Request is not open";
            return false;
        }

        if (pr.sourceBranch == pr.targetBranch) {
            reason = "Source and target branches must differ";
            return false;
        }

        if (policy.requirePassingChecks && !checksPassed(pr)) {
            reason = "Required status checks have not all passed";
            return false;
        }

        const int approvals = approvedReviews(pr);

        if (approvals < policy.requiredApprovals) {
            std::ostringstream message;
            message << "Required approvals: " << policy.requiredApprovals
                    << ", current approvals: " << approvals;
            reason = message.str();
            return false;
        }

        reason = "Pull Request satisfies merge policy";
        return true;
    }
};

/*
 * Templates demonstrate compile-time type binding.
 * The operation is restricted to arithmetic types before execution.
 */
template <typename T>
concept Numeric = std::is_arithmetic_v<T>;

template <Numeric T>
T checkedAdd(T left, T right) {
    return left + right;
}

/*
 * Runtime polymorphism demonstrates late method dispatch while preserving
 * a statically checked interface through the abstract base class.
 */
class ReviewRule {
public:
    virtual ~ReviewRule() = default;
    virtual bool accepts(const Review& review) const = 0;
};

class NoSelfApprovalRule final : public ReviewRule {
private:
    std::string author_;

public:
    explicit NoSelfApprovalRule(std::string author)
        : author_(std::move(author)) {}

    bool accepts(const Review& review) const override {
        return review.reviewer != author_;
    }
};

class ReviewPolicy {
private:
    std::vector<std::unique_ptr<ReviewRule>> rules_;

public:
    void addRule(std::unique_ptr<ReviewRule> rule) {
        rules_.push_back(std::move(rule));
    }

    bool accepts(const Review& review) const {
        return std::all_of(
            rules_.begin(),
            rules_.end(),
            [&review](const auto& rule) {
                return rule->accepts(review);
            }
        );
    }
};

void scopeAndBindingDemo() {
    const std::string repository = "payments-service";

    {
        const std::string branch = "main";
        std::cout << "Inner branch binding: " << branch << '\n';
    }

    // The branch binding above no longer exists after its scope ends.
    std::cout << "Repository binding remains: " << repository << '\n';
}

void lifetimeDemo() {
    std::cout << "\nRAII lifetime demonstration\n";

    {
        RepositorySession session("payments-service");
        session.audit().record("Evaluating pull request #184");
        session.audit().record("Policy evaluation completed");
    }

    std::cout << "The session and audit log were destroyed at scope exit.\n";
}

void staticTypeDemo() {
    const int attempts = 3;
    const double threshold = 0.85;

    std::cout << "\nCompile-time types\n";
    std::cout << "Attempts: " << attempts << '\n';
    std::cout << "Threshold: " << threshold << '\n';
    std::cout << "Integer addition: " << checkedAdd(10, 20) << '\n';
    std::cout << "Floating addition: "
              << checkedAdd(0.25, 0.50) << '\n';
}

void governanceCaseStudy() {
    BranchPolicy mainPolicy{
        "main",
        2,
        true,
        false,
        false
    };

    PullRequest pr{
        184,
        "feature/payment-validation",
        "main",
        PullRequestState::Open,
        {
            {"alice", ReviewState::Approved, "Validation logic is sound"},
            {"bob", ReviewState::Approved, "Tests cover failure paths"},
            {"carol", ReviewState::ChangesRequested, "Improve error reporting"}
        },
        {
            {"unit-tests", true},
            {"security-scan", true},
            {"integration-tests", true}
        }
    };

    MergeEligibilityEngine engine;
    std::string reason;

    const bool eligible = engine.eligible(pr, mainPolicy, reason);

    std::cout << "\nMerge eligibility\n";
    std::cout << "PR #" << pr.number << ": "
              << (eligible ? "ELIGIBLE" : "BLOCKED") << '\n';
    std::cout << "Reason: " << reason << '\n';

    ReviewPolicy reviewPolicy;
    reviewPolicy.addRule(
        std::make_unique<NoSelfApprovalRule>("author")
    );

    Review validReview{
        "reviewer",
        ReviewState::Approved,
        "Approved after validation"
    };

    Review selfReview{
        "author",
        ReviewState::Approved,
        "Looks good"
    };

    std::cout << "Independent review accepted: "
              << std::boolalpha
              << reviewPolicy.accepts(validReview) << '\n';

    std::cout << "Self-review accepted: "
              << reviewPolicy.accepts(selfReview) << '\n';

    /*
     * The policy engine counts approvals independently from the presence
     * of comments. A review that requests changes therefore does not satisfy
     * an approval threshold, even when the reviewer participated.
     */
}

} // namespace governance

int main() {
    try {
        std::cout << std::boolalpha;

        governance::scopeAndBindingDemo();
        governance::lifetimeDemo();
        governance::staticTypeDemo();
        governance::governanceCaseStudy();

        std::cout << "\nCase study completed successfully.\n";
    } catch (const std::exception& error) {
        std::cerr << "Unhandled error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
