#include <algorithm>
#include <iomanip>
#include <iostream>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

enum class AllocationStrategy {
    FirstFit,
    BestFit,
    WorstFit
};

struct Block {
    std::size_t start{};
    std::size_t size{};
    bool allocated{false};
    std::string owner{};

    std::size_t end() const {
        return start + size;
    }
};

class MemoryError : public std::runtime_error {
public:
    explicit MemoryError(const std::string& message)
        : std::runtime_error(message) {}
};

/*
 * Case study:
 * A build server owns a fixed 1024-unit memory arena. Build jobs request
 * contiguous regions. Jobs may finish in arbitrary order, producing holes.
 * The governance layer reports whether a new job can fit, distinguishes
 * total free memory from the largest contiguous region, and can compact
 * memory when relocation is acceptable.
 */
class BuildServerMemory {
private:
    std::size_t total_;
    AllocationStrategy strategy_;
    std::vector<Block> blocks_;

    std::vector<std::size_t> candidates(std::size_t requested) const {
        std::vector<std::size_t> result;

        for (std::size_t i = 0; i < blocks_.size(); ++i) {
            if (!blocks_[i].allocated && blocks_[i].size >= requested) {
                result.push_back(i);
            }
        }

        return result;
    }

    std::size_t selectCandidate(std::size_t requested) const {
        const auto choices = candidates(requested);

        if (choices.empty()) {
            throw MemoryError(
                "no single contiguous block can satisfy the request"
            );
        }

        if (strategy_ == AllocationStrategy::FirstFit) {
            return choices.front();
        }

        if (strategy_ == AllocationStrategy::BestFit) {
            return *std::min_element(
                choices.begin(),
                choices.end(),
                [this](std::size_t left, std::size_t right) {
                    return blocks_[left].size < blocks_[right].size;
                }
            );
        }

        return *std::max_element(
            choices.begin(),
            choices.end(),
            [this](std::size_t left, std::size_t right) {
                return blocks_[left].size < blocks_[right].size;
            }
        );
    }

    void coalesce() {
        std::vector<Block> merged;

        for (const auto& block : blocks_) {
            if (!merged.empty() &&
                !merged.back().allocated &&
                !block.allocated &&
                merged.back().end() == block.start) {
                merged.back().size += block.size;
            } else {
                merged.push_back(block);
            }
        }

        blocks_ = std::move(merged);
    }

public:
    BuildServerMemory(
        std::size_t total,
        AllocationStrategy strategy
    )
        : total_(total), strategy_(strategy) {
        if (total == 0) {
            throw std::invalid_argument("total memory must be positive");
        }

        blocks_.push_back({0, total, false, {}});
    }

    std::size_t allocate(const std::string& owner, std::size_t requested) {
        if (owner.empty()) {
            throw std::invalid_argument("owner cannot be empty");
        }

        if (requested == 0) {
            throw std::invalid_argument("requested memory must be positive");
        }

        for (const auto& block : blocks_) {
            if (block.allocated && block.owner == owner) {
                throw MemoryError("owner already has an allocation");
            }
        }

        const std::size_t index = selectCandidate(requested);
        const Block original = blocks_[index];

        if (original.size == requested) {
            blocks_[index].allocated = true;
            blocks_[index].owner = owner;
        } else {
            Block allocation{
                original.start,
                requested,
                true,
                owner
            };

            Block remainder{
                original.start + requested,
                original.size - requested,
                false,
                {}
            };

            blocks_.erase(blocks_.begin() + static_cast<long>(index));
            blocks_.insert(
                blocks_.begin() + static_cast<long>(index),
                {allocation, remainder}
            );
        }

        return original.start;
    }

    void release(const std::string& owner) {
        for (auto& block : blocks_) {
            if (block.allocated && block.owner == owner) {
                block.allocated = false;
                block.owner.clear();
                coalesce();
                return;
            }
        }

        throw MemoryError("allocation not found for owner: " + owner);
    }

    void compact() {
        std::vector<Block> compacted;
        std::size_t cursor = 0;

        for (const auto& block : blocks_) {
            if (!block.allocated) {
                continue;
            }

            compacted.push_back({
                cursor,
                block.size,
                true,
                block.owner
            });

            cursor += block.size;
        }

        if (cursor < total_) {
            compacted.push_back({
                cursor,
                total_ - cursor,
                false,
                {}
            });
        }

        blocks_ = std::move(compacted);
    }

    std::size_t freeMemory() const {
        std::size_t total = 0;

        for (const auto& block : blocks_) {
            if (!block.allocated) {
                total += block.size;
            }
        }

        return total;
    }

    std::size_t largestFreeBlock() const {
        std::size_t largest = 0;

        for (const auto& block : blocks_) {
            if (!block.allocated) {
                largest = std::max(largest, block.size);
            }
        }

        return largest;
    }

    std::size_t externalFragmentation() const {
        return freeMemory() - largestFreeBlock();
    }

    bool canAllocate(std::size_t requested) const {
        return std::any_of(
            blocks_.begin(),
            blocks_.end(),
            [requested](const Block& block) {
                return !block.allocated && block.size >= requested;
            }
        );
    }

    void printReport() const {
        std::cout << "\nMemory map\n";
        std::cout << "---------------------------------------------\n";

        for (const auto& block : blocks_) {
            std::cout
                << std::setw(5) << block.start
                << " - "
                << std::setw(5) << block.end() - 1
                << " | "
                << std::setw(9)
                << (block.allocated ? "ALLOCATED" : "FREE")
                << " | "
                << (block.allocated ? block.owner : "-")
                << '\n';
        }

        std::cout << "Free memory: "
                  << freeMemory()
                  << "\nLargest free block: "
                  << largestFreeBlock()
                  << "\nExternal fragmentation: "
                  << externalFragmentation()
                  << '\n';
    }
};

static void fragmentationCaseStudy() {
    std::cout << "=== Build server contiguous-memory case study ===\n";

    BuildServerMemory memory(1024, AllocationStrategy::BestFit);

    memory.allocate("compiler-A", 180);
    memory.allocate("compiler-B", 240);
    memory.allocate("test-runner", 120);
    memory.allocate("linker", 200);

    memory.printReport();

    memory.release("compiler-B");
    memory.release("test-runner");

    std::cout << "\nAfter two jobs finish:\n";
    memory.printReport();

    const std::size_t requested = 300;

    std::cout << "\nChecking request for " << requested << " units:\n";
    std::cout
        << "Total free memory = "
        << memory.freeMemory()
        << ", largest contiguous block = "
        << memory.largestFreeBlock()
        << '\n';

    if (!memory.canAllocate(requested)) {
        std::cout
            << "The request cannot be satisfied without compaction. "
            << "The failure is caused by external fragmentation, not merely "
            << "by insufficient total free memory.\n";
    }

    std::cout << "\nCompacting the arena...\n";
    memory.compact();

    memory.printReport();

    const auto address = memory.allocate("large-linker", requested);

    std::cout
        << "\nlarge-linker allocated at address "
        << address
        << " after compaction.\n";
}

static void fixedPartitionCase() {
    std::cout << "\n=== Fixed-partition internal fragmentation ===\n";

    constexpr std::size_t partitionSize = 64;
    const std::vector<std::size_t> requests{7, 31, 60, 64};

    std::size_t reserved = 0;
    std::size_t requested = 0;

    for (const auto size : requests) {
        reserved += partitionSize;
        requested += size;
    }

    std::cout
        << "Requested memory: " << requested << '\n'
        << "Reserved memory: " << reserved << '\n'
        << "Internal fragmentation: "
        << reserved - requested
        << '\n';

    std::cout
        << "The unused bytes are inside allocated partitions. This differs "
        << "from external fragmentation, where unused memory exists between "
        << "allocated regions.\n";
}

static void strategyComparison() {
    std::cout << "\n=== Allocation strategy comparison ===\n";

    const std::vector<std::pair<std::string, AllocationStrategy>> strategies{
        {"First fit", AllocationStrategy::FirstFit},
        {"Best fit", AllocationStrategy::BestFit},
        {"Worst fit", AllocationStrategy::WorstFit}
    };

    for (const auto& [name, strategy] : strategies) {
        BuildServerMemory memory(200, strategy);

        memory.allocate("A", 40);
        memory.allocate("B", 70);
        memory.allocate("C", 30);
        memory.allocate("D", 20);

        memory.release("B");
        memory.release("D");

        bool success = true;

        try {
            memory.allocate("E", 25);
        } catch (const MemoryError&) {
            success = false;
        }

        std::cout
            << std::left
            << std::setw(12)
            << name
            << " request result="
            << (success ? "allocated" : "failed")
            << ", largest free="
            << memory.largestFreeBlock()
            << '\n';
    }
}

int main() {
    try {
        fragmentationCaseStudy();
        fixedPartitionCase();
        strategyComparison();
    } catch (const std::exception& error) {
        std::cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
