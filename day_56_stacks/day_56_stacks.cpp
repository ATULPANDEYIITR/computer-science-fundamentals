#include <algorithm>
#include <cmath>
#include <exception>
#include <functional>
#include <iomanip>
#include <iostream>
#include <limits>
#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

template <typename T>
class Stack {
public:
    explicit Stack(std::size_t capacity = 0) : capacity_(capacity) {}

    void push(const T& value) {
        if (capacity_ != 0 && data_.size() >= capacity_) {
            throw std::overflow_error("stack capacity reached");
        }
        data_.push_back(value);
    }

    T pop() {
        if (data_.empty()) {
            throw std::underflow_error("cannot pop from empty stack");
        }
        T value = data_.back();
        data_.pop_back();
        return value;
    }

    const T& peek() const {
        if (data_.empty()) {
            throw std::underflow_error("cannot peek at empty stack");
        }
        return data_.back();
    }

    bool empty() const noexcept {
        return data_.empty();
    }

    std::size_t size() const noexcept {
        return data_.size();
    }

    void clear() noexcept {
        data_.clear();
    }

private:
    std::vector<T> data_;
    std::size_t capacity_;
};

enum class ReviewState {
    Draft,
    Open,
    Approved,
    ChangesRequested,
    Merged,
    Closed
};

enum class CheckState {
    Pending,
    Passed,
    Failed
};

struct Commit {
    std::string id;
    std::string message;
};

struct Review {
    std::string reviewer;
    ReviewState state;
    std::string comment;
};

struct StatusCheck {
    std::string name;
    CheckState state;
};

struct BranchProtection {
    std::size_t requiredApprovals{2};
    bool requirePassingChecks{true};
    bool requireConversationResolution{true};
    bool requireLinearHistory{true};
    bool allowForcePush{false};
    bool allowDirectPush{false};
};

struct PullRequest {
    int number{};
    std::string sourceBranch;
    std::string targetBranch;
    std::vector<Commit> commits;
    std::vector<Review> reviews;
    std::vector<StatusCheck> checks;
    bool draft{true};
    bool conversationsResolved{false};
    bool hasConflicts{false};
    bool branchUpToDate{true};
    bool linearHistory{true};
    ReviewState state{ReviewState::Draft};
};

class GovernanceError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

class MergeEligibilityEngine {
public:
    explicit MergeEligibilityEngine(BranchProtection policy)
        : policy_(std::move(policy)) {}

    std::vector<std::string> violations(const PullRequest& pr) const {
        std::vector<std::string> failures;

        if (pr.draft) {
            failures.emplace_back("pull request is still a draft");
        }

        if (pr.sourceBranch.empty() || pr.targetBranch.empty()) {
            failures.emplace_back("source and target branches are required");
        }

        if (pr.sourceBranch == pr.targetBranch) {
            failures.emplace_back("source and target branches must differ");
        }

        if (pr.commits.empty()) {
            failures.emplace_back("pull request contains no commits");
        }

        if (pr.hasConflicts) {
            failures.emplace_back("merge conflicts must be resolved");
        }

        if (!pr.branchUpToDate) {
            failures.emplace_back("source branch is behind the target branch");
        }

        if (policy_.requireLinearHistory && !pr.linearHistory) {
            failures.emplace_back("linear history is required");
        }

        if (policy_.requireConversationResolution && !pr.conversationsResolved) {
            failures.emplace_back("review conversations remain unresolved");
        }

        if (policy_.requirePassingChecks) {
            for (const auto& check : pr.checks) {
                if (check.state != CheckState::Passed) {
                    failures.emplace_back(
                        "required check is not passing: " + check.name);
                }
            }

            if (pr.checks.empty()) {
                failures.emplace_back("at least one required status check is expected");
            }
        }

        const std::size_t approvals = countCurrentApprovals(pr);
        if (approvals < policy_.requiredApprovals) {
            failures.emplace_back(
                "required approvals: " +
                std::to_string(policy_.requiredApprovals) +
                ", current approvals: " +
                std::to_string(approvals));
        }

        return failures;
    }

    bool eligible(const PullRequest& pr) const {
        return violations(pr).empty();
    }

    void merge(PullRequest& pr) const {
        const auto failures = violations(pr);

        if (!failures.empty()) {
            throw GovernanceError(buildFailureMessage(failures));
        }

        pr.state = ReviewState::Merged;
    }

private:
    BranchProtection policy_;

    static std::size_t countCurrentApprovals(const PullRequest& pr) {
        std::unordered_set<std::string> approvedReviewers;
        std::unordered_set<std::string> latestReviewerDecision;

        // The latest review state for each reviewer controls approval.
        for (const auto& review : pr.reviews) {
            latestReviewerDecision.insert(review.reviewer);
        }

        for (const auto& review : pr.reviews) {
            // This example assumes reviews are supplied in chronological order.
            if (review.state == ReviewState::Approved) {
                approvedReviewers.insert(review.reviewer);
            } else {
                approvedReviewers.erase(review.reviewer);
            }
        }

        return approvedReviewers.size();
    }

    static std::string buildFailureMessage(
        const std::vector<std::string>& failures) {
        std::string result = "merge rejected:";
        for (const auto& failure : failures) {
            result += "\n - " + failure;
        }
        return result;
    }
};

bool balancedDelimiters(const std::string& text) {
    Stack<char> stack;
    const std::unordered_map<char, char> pairs{
        {')', '('},
        {']', '['},
        {'}', '{'}
    };

    for (char c : text) {
        if (c == '(' || c == '[' || c == '{') {
            stack.push(c);
        } else if (pairs.contains(c)) {
            if (stack.empty() || stack.pop() != pairs.at(c)) {
                return false;
            }
        }
    }

    return stack.empty();
}

std::vector<int> nextGreaterElements(const std::vector<int>& values) {
    std::vector<int> result(values.size(), -1);
    Stack<std::size_t> indices;

    for (std::size_t i = 0; i < values.size(); ++i) {
        while (!indices.empty() && values[indices.peek()] < values[i]) {
            result[indices.pop()] = values[i];
        }
        indices.push(i);
    }

    return result;
}

class PostfixEvaluator {
public:
    static double evaluate(const std::vector<std::string>& tokens) {
        Stack<double> operands;

        for (const auto& token : tokens) {
            if (isNumber(token)) {
                operands.push(std::stod(token));
                continue;
            }

            if (token == "u-") {
                operands.push(-operands.pop());
                continue;
            }

            if (operands.size() < 2) {
                throw std::invalid_argument("insufficient operands");
            }

            const double right = operands.pop();
            const double left = operands.pop();

            if ((token == "/" || token == "%") && right == 0.0) {
                throw std::domain_error("division or modulo by zero");
            }

            double result = 0.0;

            if (token == "+") result = left + right;
            else if (token == "-") result = left - right;
            else if (token == "*") result = left * right;
            else if (token == "/") result = left / right;
            else if (token == "%") result = std::fmod(left, right);
            else if (token == "^") result = std::pow(left, right);
            else throw std::invalid_argument("unknown operator: " + token);

            if (!std::isfinite(result)) {
                throw std::domain_error("non-finite arithmetic result");
            }

            operands.push(result);
        }

        if (operands.size() != 1) {
            throw std::invalid_argument("malformed postfix expression");
        }

        return operands.pop();
    }

private:
    static bool isNumber(const std::string& token) {
        if (token.empty()) return false;

        std::size_t consumed = 0;
        try {
            std::stod(token, &consumed);
        } catch (...) {
            return false;
        }

        return consumed == token.size();
    }
};

void assertCondition(bool condition, const std::string& message) {
    if (!condition) {
        throw std::runtime_error("assertion failed: " + message);
    }
}

void runTests() {
    Stack<int> stack(2);
    stack.push(10);
    stack.push(20);

    try {
        stack.push(30);
        throw std::runtime_error("overflow was not detected");
    } catch (const std::overflow_error&) {
    }

    assertCondition(stack.pop() == 20, "LIFO pop");
    assertCondition(stack.peek() == 10, "peek");

    assertCondition(balancedDelimiters("{[()]}"), "balanced delimiters");
    assertCondition(!balancedDelimiters("{[(])}"), "invalid delimiters");

    const auto next = nextGreaterElements({4, 5, 2, 10, 8});
    assertCondition(
        next == std::vector<int>({5, 10, 10, -1, -1}),
        "next greater elements");

    const double value = PostfixEvaluator::evaluate(
        {"3", "4", "2", "*", "1", "5", "-", "2", "^", "/", "+"});

    assertCondition(std::abs(value - 3.5) < 1e-9, "postfix evaluation");
}

int main() {
    try {
        runTests();

        std::cout << "STACK OPERATIONS\n";
        Stack<std::string> stack;
        stack.push("parse");
        stack.push("validate");
        stack.push("execute");

        std::cout << "top: " << stack.peek() << '\n';
        std::cout << "pop: " << stack.pop() << '\n';

        std::cout << "\nDELIMITER VALIDATION\n";
        std::cout << "{[()]} -> "
                  << std::boolalpha
                  << balancedDelimiters("{[()]}")
                  << '\n';
        std::cout << "{[(])} -> "
                  << balancedDelimiters("{[(])}")
                  << '\n';

        std::cout << "\nMONOTONIC STACK\n";
        const std::vector<int> values{4, 5, 2, 10, 8};
        const auto result = nextGreaterElements(values);

        std::cout << "values: ";
        for (int value : values) std::cout << value << ' ';

        std::cout << "\nnext greater: ";
        for (int value : result) std::cout << value << ' ';
        std::cout << '\n';

        std::cout << "\nPOSTFIX EVALUATION\n";
        const std::vector<std::string> postfix{
            "3", "4", "2", "*", "1", "5", "-", "2", "^", "/", "+"
        };

        std::cout << "3 4 2 * 1 5 - 2 ^ / + = "
                  << PostfixEvaluator::evaluate(postfix)
                  << '\n';

        std::cout << "\nMERGE-GOVERNANCE CASE STUDY\n";

        BranchProtection policy{
            2,     // required approvals
            true,  // required checks
            true,  // conversations resolved
            true,  // linear history
            false, // force push forbidden
            false  // direct push forbidden
        };

        PullRequest pr;
        pr.number = 1042;
        pr.sourceBranch = "feature/stack-parser";
        pr.targetBranch = "main";
        pr.commits = {
            {"a1b2c3", "Implement expression parser"},
            {"d4e5f6", "Add stack validation tests"}
        };
        pr.draft = false;
        pr.conversationsResolved = true;
        pr.hasConflicts = false;
        pr.branchUpToDate = true;
        pr.linearHistory = true;

        pr.reviews = {
            {"reviewer-a", ReviewState::Approved, "Correct stack invariant."},
            {"reviewer-b", ReviewState::Approved, "Expression tests are sufficient."}
        };

        pr.checks = {
            {"unit-tests", CheckState::Passed},
            {"static-analysis", CheckState::Passed}
        };

        MergeEligibilityEngine engine(policy);

        if (engine.eligible(pr)) {
            engine.merge(pr);
            std::cout << "PR #" << pr.number << " merged successfully.\n";
        }

        pr.state = ReviewState::Open;
        pr.hasConflicts = true;

        try {
            engine.merge(pr);
        } catch (const GovernanceError& error) {
            std::cout << "Expected rejection:\n"
                      << error.what() << '\n';
        }

        std::cout << "\nComplexity:\n";
        std::cout << "- Stack push/pop/peek: O(1) amortized.\n";
        std::cout << "- Delimiter validation: O(n).\n";
        std::cout << "- Monotonic next-greater processing: O(n).\n";
        std::cout << "- Postfix evaluation: O(n).\n";
        std::cout << "- Governance evaluation: O(R + C), where R is reviews and C is checks.\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }
}
