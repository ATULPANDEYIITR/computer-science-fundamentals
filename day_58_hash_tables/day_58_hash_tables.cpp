#include <algorithm>
#include <cstdint>
#include <exception>
#include <functional>
#include <iomanip>
#include <iostream>
#include <optional>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

enum class SlotState {
    Empty,
    Occupied,
    Deleted
};

struct ReviewPolicy {
    int requiredApprovals{};
    bool requirePassingChecks{};
    bool requireConversationResolution{};
};

struct PullRequestRecord {
    std::string id;
    std::string sourceBranch;
    std::string targetBranch;
    std::size_t changedFiles{};
    bool draft{false};
    bool hasMergeConflicts{false};
    bool closed{false};
};

struct ReviewRecord {
    std::string reviewer;
    bool eligible{false};
    bool approved{false};
    bool dismissed{false};
};

struct StatusCheck {
    std::string name;
    bool passed{false};
};

struct RepositoryKey {
    std::string organization;
    std::string name;

    bool operator==(const RepositoryKey& other) const {
        return organization == other.organization && name == other.name;
    }
};

struct RepositoryKeyHash {
    std::size_t operator()(const RepositoryKey& key) const noexcept {
        // Hash-combine keeps organization and repository names distinct.
        const std::size_t h1 = std::hash<std::string>{}(key.organization);
        const std::size_t h2 = std::hash<std::string>{}(key.name);

        return h1 ^ (h2 + static_cast<std::size_t>(0x9e3779b9) +
                     (h1 << 6U) + (h1 >> 2U));
    }
};


/*
 * A compact generic hash table using separate chaining.
 *
 * It deliberately implements the bucket mechanics instead of delegating
 * storage to std::unordered_map so collision behavior is observable.
 */
template <typename Key, typename Value, typename Hash = std::hash<Key>>
class ChainedHashTable {
private:
    struct Entry {
        Key key;
        Value value;
    };

    std::vector<std::vector<Entry>> buckets_;
    std::size_t size_{0};
    std::size_t collisions_{0};
    std::size_t rehashes_{0};
    double maxLoadFactor_;
    Hash hasher_;

    std::size_t indexFor(const Key& key) const {
        return hasher_(key) % buckets_.size();
    }

    void resize(std::size_t newCapacity) {
        std::vector<std::vector<Entry>> oldBuckets;
        oldBuckets.swap(buckets_);

        buckets_.resize(newCapacity);
        collisions_ = 0;

        for (const auto& bucket : oldBuckets) {
            for (const auto& entry : bucket) {
                const std::size_t index = indexFor(entry.key);

                if (!buckets_[index].empty()) {
                    ++collisions_;
                }

                buckets_[index].push_back(entry);
            }
        }

        ++rehashes_;
    }

    void ensureCapacity() {
        if (static_cast<double>(size_ + 1) /
                static_cast<double>(buckets_.size()) >
            maxLoadFactor_) {
            resize(buckets_.size() * 2);
        }
    }

public:
    explicit ChainedHashTable(
        std::size_t capacity = 8,
        double maxLoadFactor = 0.75)
        : buckets_(capacity),
          maxLoadFactor_(maxLoadFactor) {
        if (capacity < 2) {
            throw std::invalid_argument("capacity must be at least 2");
        }
        if (maxLoadFactor <= 0.1 || maxLoadFactor > 0.95) {
            throw std::invalid_argument("invalid load factor");
        }
    }

    void put(const Key& key, const Value& value) {
        ensureCapacity();

        const std::size_t index = indexFor(key);

        for (auto& entry : buckets_[index]) {
            if (entry.key == key) {
                entry.value = value;
                return;
            }
        }

        if (!buckets_[index].empty()) {
            ++collisions_;
        }

        buckets_[index].push_back({key, value});
        ++size_;
    }

    bool contains(const Key& key) const {
        const std::size_t index = indexFor(key);

        return std::any_of(
            buckets_[index].begin(),
            buckets_[index].end(),
            [&](const Entry& entry) {
                return entry.key == key;
            });
    }

    std::optional<Value> get(const Key& key) const {
        const std::size_t index = indexFor(key);

        for (const auto& entry : buckets_[index]) {
            if (entry.key == key) {
                return entry.value;
            }
        }

        return std::nullopt;
    }

    Value require(const Key& key) const {
        const auto result = get(key);

        if (!result.has_value()) {
            throw std::out_of_range("hash-table key not found");
        }

        return *result;
    }

    Value remove(const Key& key) {
        const std::size_t index = indexFor(key);
        auto& bucket = buckets_[index];

        const auto iterator = std::find_if(
            bucket.begin(),
            bucket.end(),
            [&](const Entry& entry) {
                return entry.key == key;
            });

        if (iterator == bucket.end()) {
            throw std::out_of_range("hash-table key not found");
        }

        Value value = iterator->value;
        bucket.erase(iterator);
        --size_;

        return value;
    }

    std::size_t size() const noexcept {
        return size_;
    }

    double loadFactor() const noexcept {
        return static_cast<double>(size_) /
               static_cast<double>(buckets_.size());
    }

    std::size_t collisions() const noexcept {
        return collisions_;
    }

    std::size_t rehashes() const noexcept {
        return rehashes_;
    }

    std::size_t longestChain() const {
        std::size_t result = 0;

        for (const auto& bucket : buckets_) {
            result = std::max(result, bucket.size());
        }

        return result;
    }
};


/*
 * Repository governance engine.
 *
 * The hash table is used as an index from repository identity to policy.
 * Merge eligibility is kept outside the table so data storage and policy
 * evaluation remain separate responsibilities.
 */
class GovernanceEngine {
private:
    ChainedHashTable<RepositoryKey, ReviewPolicy, RepositoryKeyHash> policies_;

    static bool allChecksPass(const std::vector<StatusCheck>& checks) {
        return std::all_of(
            checks.begin(),
            checks.end(),
            [](const StatusCheck& check) {
                return check.passed;
            });
    }

    static std::size_t activeApprovals(
        const std::vector<ReviewRecord>& reviews) {

        std::size_t count = 0;

        for (const auto& review : reviews) {
            if (review.eligible &&
                review.approved &&
                !review.dismissed) {
                ++count;
            }
        }

        return count;
    }

public:
    void registerPolicy(
        const RepositoryKey& repository,
        const ReviewPolicy& policy) {

        if (policy.requiredApprovals < 0) {
            throw std::invalid_argument(
                "required approvals cannot be negative");
        }

        policies_.put(repository, policy);
    }

    bool mergeEligible(
        const RepositoryKey& repository,
        const PullRequestRecord& pullRequest,
        const std::vector<ReviewRecord>& reviews,
        const std::vector<StatusCheck>& checks,
        bool conversationsResolved) const {

        const ReviewPolicy policy = policies_.require(repository);

        if (pullRequest.closed ||
            pullRequest.draft ||
            pullRequest.hasMergeConflicts) {
            return false;
        }

        if (policy.requirePassingChecks &&
            !allChecksPass(checks)) {
            return false;
        }

        if (policy.requireConversationResolution &&
            !conversationsResolved) {
            return false;
        }

        return activeApprovals(reviews) >=
               static_cast<std::size_t>(policy.requiredApprovals);
    }

    const auto& policies() const {
        return policies_;
    }
};


int main() {
    try {
        GovernanceEngine engine;

        const RepositoryKey repository{
            "security-platform",
            "gateway"
        };

        engine.registerPolicy(
            repository,
            ReviewPolicy{
                .requiredApprovals = 2,
                .requirePassingChecks = true,
                .requireConversationResolution = true
            });

        PullRequestRecord pullRequest{
            .id = "PR-184",
            .sourceBranch = "feature/hash-index",
            .targetBranch = "main",
            .changedFiles = 7,
            .draft = false,
            .hasMergeConflicts = false,
            .closed = false
        };

        std::vector<ReviewRecord> reviews{
            {"reviewer-1", true, true, false},
            {"reviewer-2", true, true, false},
            {"reviewer-3", false, true, false},
            {"reviewer-4", true, true, true}
        };

        std::vector<StatusCheck> checks{
            {"unit-tests", true},
            {"static-analysis", true},
            {"security-scan", true}
        };

        const bool eligible = engine.mergeEligible(
            repository,
            pullRequest,
            reviews,
            checks,
            true);

        std::cout << std::boolalpha;
        std::cout << "Merge eligible: " << eligible << '\n';

        // Demonstrate a failure caused by a dismissed approval.
        reviews[1].dismissed = true;

        const bool rejected = engine.mergeEligible(
            repository,
            pullRequest,
            reviews,
            checks,
            true);

        std::cout << "After dismissing one approval: "
                  << rejected << '\n';

        // Restore the approval and demonstrate a failed status check.
        reviews[1].dismissed = false;
        checks[2].passed = false;

        const bool failedCheck = engine.mergeEligible(
            repository,
            pullRequest,
            reviews,
            checks,
            true);

        std::cout << "After failed security scan: "
                  << failedCheck << '\n';

        checks[2].passed = true;

        std::cout << "\nHash-table statistics\n"
                  << "Entries: " << engine.policies().size() << '\n'
                  << "Load factor: "
                  << std::fixed << std::setprecision(3)
                  << engine.policies().loadFactor() << '\n'
                  << "Collisions: "
                  << engine.policies().collisions() << '\n'
                  << "Rehashes: "
                  << engine.policies().rehashes() << '\n'
                  << "Longest chain: "
                  << engine.policies().longestChain() << '\n';

        // A second repository verifies that composite keys are handled
        // independently even when repository names are identical.
        const RepositoryKey secondRepository{
            "research-platform",
            "gateway"
        };

        engine.registerPolicy(
            secondRepository,
            ReviewPolicy{
                .requiredApprovals = 1,
                .requirePassingChecks = true,
                .requireConversationResolution = false
            });

        std::cout << "\nComposite-key lookup succeeded: "
                  << engine.policies().contains(secondRepository)
                  << '\n';

        try {
            engine.policies().require(
                RepositoryKey{"unknown", "repository"});
        } catch (const std::out_of_range& error) {
            std::cout << "Expected lookup failure: "
                      << error.what() << '\n';
        }

        if (!eligible) {
            throw std::runtime_error(
                "initial governance scenario should be eligible");
        }

        if (rejected) {
            throw std::runtime_error(
                "dismissed approval should prevent eligibility");
        }

        if (failedCheck) {
            throw std::runtime_error(
                "failed status check should prevent eligibility");
        }

        std::cout << "\nAll assertions passed.\n";
    } catch (const std::exception& error) {
        std::cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
