/*
 * MEMORY HIERARCHY
 * C++17 technical case study
 *
 * Scenario:
 *     A high-throughput transaction analytics engine processes a large
 *     collection of account transactions.
 *
 * The program develops the system progressively:
 *
 *     1. Contiguous data representation
 *     2. Cache locality
 *     3. Cache simulation
 *     4. LRU replacement
 *     5. Multi-level memory model
 *     6. Virtual address translation
 *     7. TLB simulation
 *     8. Performance measurement
 *     9. Validation and failure handling
 *
 * Build:
 *     g++ -std=c++17 -O2 memory_hierarchy.cpp -o memory_hierarchy
 *
 * Run:
 *     ./memory_hierarchy
 */

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <deque>
#include <iomanip>
#include <iostream>
#include <limits>
#include <list>
#include <map>
#include <numeric>
#include <optional>
#include <random>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using Clock = std::chrono::steady_clock;

// ============================================================================
// 1. BASIC DATA MODEL
// ============================================================================

struct Transaction {
    std::uint64_t id;
    std::uint32_t account_id;
    double amount;
};

void print_section(const std::string& title) {
    std::cout << "\n" << std::string(78, '=') << "\n";
    std::cout << title << "\n";
    std::cout << std::string(78, '=') << "\n";
}


// ============================================================================
// 2. CONTIGUOUS DATA AND SEQUENTIAL LOCALITY
// ============================================================================

double sum_transactions(const std::vector<Transaction>& transactions) {
    double total = 0.0;

    // Sequential iteration accesses adjacent Transaction objects.
    // This generally provides strong spatial locality for contiguous storage.
    for (const Transaction& transaction : transactions) {
        total += transaction.amount;
    }

    return total;
}

double sum_transactions_strided(
    const std::vector<Transaction>& transactions,
    std::size_t stride
) {
    if (stride == 0) {
        throw std::invalid_argument("stride must be greater than zero");
    }

    double total = 0.0;

    for (std::size_t index = 0; index < transactions.size(); index += stride) {
        total += transactions[index].amount;
    }

    return total;
}

void demonstrate_contiguous_data() {
    print_section("1. Contiguous data and spatial locality");

    std::vector<Transaction> transactions;
    transactions.reserve(500'000);

    for (std::uint64_t index = 0; index < 500'000; ++index) {
        transactions.push_back({
            index,
            static_cast<std::uint32_t>(index % 100'000),
            static_cast<double>(index % 1000) * 0.75
        });
    }

    const auto start_sequential = Clock::now();
    const double sequential_total = sum_transactions(transactions);
    const auto end_sequential = Clock::now();

    const auto start_strided = Clock::now();
    const double strided_total =
        sum_transactions_strided(transactions, 16);
    const auto end_strided = Clock::now();

    const auto sequential_time =
        std::chrono::duration<double, std::milli>(
            end_sequential - start_sequential
        ).count();

    const auto strided_time =
        std::chrono::duration<double, std::milli>(
            end_strided - start_strided
        ).count();

    std::cout << "Transaction count: " << transactions.size() << "\n";
    std::cout << "Sequential total: " << sequential_total << "\n";
    std::cout << "Stride-16 total:  " << strided_total << "\n";
    std::cout << "Sequential time:  " << sequential_time << " ms\n";
    std::cout << "Stride-16 time:   " << strided_time << " ms\n";

    std::cout << R"(
std::vector stores elements contiguously. This makes it a useful structure
for workloads that scan records sequentially.

The exact timing depends on CPU architecture, compiler optimization,
operating-system state, cache state, memory frequency, and measurement
conditions. The benchmark demonstrates access-pattern effects rather than
providing a universal cache-latency number.
)";
}


// ============================================================================
// 3. DIRECT-MAPPED CACHE
// ============================================================================

struct CacheLine {
    bool valid = false;
    std::uint64_t tag = 0;
    std::uint64_t block = 0;
};

class DirectMappedCache {
private:
    std::vector<CacheLine> lines_;
    std::size_t hits_ = 0;
    std::size_t misses_ = 0;

public:
    explicit DirectMappedCache(std::size_t line_count)
        : lines_(line_count) {
        if (line_count == 0) {
            throw std::invalid_argument(
                "cache must contain at least one line"
            );
        }
    }

    bool access(std::uint64_t block_number) {
        const std::size_t index =
            static_cast<std::size_t>(block_number % lines_.size());

        const std::uint64_t tag =
            block_number / lines_.size();

        CacheLine& line = lines_[index];

        if (line.valid && line.tag == tag) {
            ++hits_;
            return true;
        }

        ++misses_;

        line.valid = true;
        line.tag = tag;
        line.block = block_number;

        return false;
    }

    double hit_rate() const {
        const std::size_t accesses = hits_ + misses_;

        if (accesses == 0) {
            return 0.0;
        }

        return static_cast<double>(hits_) /
               static_cast<double>(accesses);
    }

    std::size_t hits() const {
        return hits_;
    }

    std::size_t misses() const {
        return misses_;
    }
};

void demonstrate_direct_mapped_cache() {
    print_section("2. Direct-mapped cache simulation");

    DirectMappedCache cache(4);

    const std::vector<std::uint64_t> access_sequence = {
        0, 4, 0, 8, 4, 0, 12, 0, 16
    };

    for (const auto block : access_sequence) {
        const bool hit = cache.access(block);

        std::cout
            << "Block " << std::setw(2) << block
            << " -> "
            << (hit ? "HIT" : "MISS")
            << "\n";
    }

    std::cout << "Hits: " << cache.hits() << "\n";
    std::cout << "Misses: " << cache.misses() << "\n";
    std::cout
        << "Hit rate: "
        << std::fixed
        << std::setprecision(2)
        << cache.hit_rate() * 100.0
        << "%\n";

    std::cout << R"(
A direct-mapped cache gives each block exactly one possible cache-line
location:

    line = block_number % number_of_lines

This makes lookup simple, but blocks that map to the same line can repeatedly
evict one another.
)";
}


// ============================================================================
// 4. SET-ASSOCIATIVE CACHE WITH LRU
// ============================================================================

struct CacheEntry {
    std::uint64_t tag;
    std::uint64_t last_used;
};

class SetAssociativeCache {
private:
    std::vector<std::vector<CacheEntry>> sets_;
    std::size_t ways_;
    std::uint64_t clock_ = 0;
    std::size_t hits_ = 0;
    std::size_t misses_ = 0;
    std::size_t evictions_ = 0;

public:
    SetAssociativeCache(std::size_t set_count, std::size_t ways)
        : sets_(set_count), ways_(ways) {
        if (set_count == 0 || ways == 0) {
            throw std::invalid_argument(
                "set count and associativity must be positive"
            );
        }
    }

    bool access(std::uint64_t block_number) {
        ++clock_;

        const std::size_t set_index =
            static_cast<std::size_t>(block_number % sets_.size());

        const std::uint64_t tag =
            block_number / sets_.size();

        auto& target_set = sets_[set_index];

        for (auto& entry : target_set) {
            if (entry.tag == tag) {
                ++hits_;
                entry.last_used = clock_;
                return true;
            }
        }

        ++misses_;

        if (target_set.size() >= ways_) {
            auto oldest = std::min_element(
                target_set.begin(),
                target_set.end(),
                [](const CacheEntry& left, const CacheEntry& right) {
                    return left.last_used < right.last_used;
                }
            );

            target_set.erase(oldest);
            ++evictions_;
        }

        target_set.push_back({tag, clock_});
        return false;
    }

    double hit_rate() const {
        const std::size_t accesses = hits_ + misses_;

        return accesses == 0
            ? 0.0
            : static_cast<double>(hits_) / accesses;
    }

    std::size_t evictions() const {
        return evictions_;
    }
};

void demonstrate_set_associativity() {
    print_section("3. Set-associative cache and LRU");

    SetAssociativeCache cache(2, 2);

    const std::vector<std::uint64_t> accesses = {
        0, 2, 4, 0, 2, 4, 0
    };

    for (const auto block : accesses) {
        std::cout
            << "Block " << block
            << ": "
            << (cache.access(block) ? "HIT" : "MISS")
            << "\n";
    }

    std::cout
        << "Hit rate: "
        << std::fixed
        << std::setprecision(2)
        << cache.hit_rate() * 100.0
        << "%\n";

    std::cout << "Evictions: " << cache.evictions() << "\n";
}


// ============================================================================
// 5. MULTI-LEVEL CACHE MODEL
// ============================================================================

class LRUBlockCache {
private:
    std::size_t capacity_;
    std::list<std::uint64_t> order_;
    std::unordered_map<
        std::uint64_t,
        std::list<std::uint64_t>::iterator
    > positions_;

public:
    explicit LRUBlockCache(std::size_t capacity)
        : capacity_(capacity) {
        if (capacity == 0) {
            throw std::invalid_argument(
                "cache capacity must be positive"
            );
        }
    }

    bool contains(std::uint64_t block) {
        const auto found = positions_.find(block);

        if (found == positions_.end()) {
            return false;
        }

        order_.erase(found->second);
        order_.push_back(block);
        found->second = std::prev(order_.end());

        return true;
    }

    void insert(std::uint64_t block) {
        const auto existing = positions_.find(block);

        if (existing != positions_.end()) {
            order_.erase(existing->second);
            positions_.erase(existing);
        }

        if (order_.size() >= capacity_) {
            const auto oldest = order_.front();
            order_.pop_front();
            positions_.erase(oldest);
        }

        order_.push_back(block);
        positions_[block] = std::prev(order_.end());
    }
};

struct MemoryAccessResult {
    std::string level;
    bool hit;
    double latency_ns;
};

class MultiLevelMemory {
private:
    LRUBlockCache l1_;
    LRUBlockCache l2_;
    LRUBlockCache l3_;

    const double l1_latency_ns_ = 1.0;
    const double l2_latency_ns_ = 4.0;
    const double l3_latency_ns_ = 12.0;
    const double ram_latency_ns_ = 80.0;

public:
    MultiLevelMemory()
        : l1_(4),
          l2_(8),
          l3_(16) {}

    MemoryAccessResult access(std::uint64_t block) {
        if (l1_.contains(block)) {
            return {"L1", true, l1_latency_ns_};
        }

        if (l2_.contains(block)) {
            l1_.insert(block);
            return {"L2", true, l1_latency_ns_ + l2_latency_ns_};
        }

        if (l3_.contains(block)) {
            l2_.insert(block);
            l1_.insert(block);

            return {
                "L3",
                true,
                l1_latency_ns_ +
                    l2_latency_ns_ +
                    l3_latency_ns_
            };
        }

        // A real system would have many additional operations here:
        // coherence checks, fills, write policies, queues, prefetching,
        // memory controllers, and potentially NUMA routing.
        l3_.insert(block);
        l2_.insert(block);
        l1_.insert(block);

        return {
            "RAM",
            false,
            l1_latency_ns_ +
                l2_latency_ns_ +
                l3_latency_ns_ +
                ram_latency_ns_
        };
    }
};

void demonstrate_multi_level_memory() {
    print_section("4. Multi-level cache and RAM model");

    MultiLevelMemory memory;

    const std::vector<std::uint64_t> accesses = {
        1, 2, 3, 4, 1, 2, 3, 4, 20, 21, 1, 2, 20, 21
    };

    for (const auto block : accesses) {
        const MemoryAccessResult result = memory.access(block);

        std::cout
            << "Block " << std::setw(2) << block
            << " -> " << std::setw(3) << result.level
            << ", "
            << (result.hit ? "hit" : "lower-level access")
            << ", modeled latency="
            << result.latency_ns
            << " ns\n";
    }
}


// ============================================================================
// 6. VIRTUAL MEMORY
// ============================================================================

struct PageTableEntry {
    std::uint64_t frame;
    bool present;
    bool writable;
    bool executable;
};

class PageTable {
private:
    std::uint64_t page_size_;
    std::unordered_map<std::uint64_t, PageTableEntry> entries_;

    static bool is_power_of_two(std::uint64_t value) {
        return value != 0 && (value & (value - 1)) == 0;
    }

public:
    explicit PageTable(std::uint64_t page_size = 4096)
        : page_size_(page_size) {
        if (!is_power_of_two(page_size)) {
            throw std::invalid_argument(
                "page size must be a power of two"
            );
        }
    }

    void map_page(
        std::uint64_t virtual_page,
        std::uint64_t frame,
        bool writable = true,
        bool executable = false
    ) {
        entries_[virtual_page] = {
            frame,
            true,
            writable,
            executable
        };
    }

    std::uint64_t translate(std::uint64_t virtual_address) const {
        const std::uint64_t virtual_page =
            virtual_address / page_size_;

        const std::uint64_t offset =
            virtual_address % page_size_;

        const auto found = entries_.find(virtual_page);

        if (found == entries_.end() || !found->second.present) {
            throw std::runtime_error(
                "page fault: virtual page is not resident"
            );
        }

        return found->second.frame * page_size_ + offset;
    }

    std::uint64_t page_size() const {
        return page_size_;
    }

    const PageTableEntry& entry(std::uint64_t virtual_page) const {
        return entries_.at(virtual_page);
    }
};

void demonstrate_virtual_memory() {
    print_section("5. Virtual memory and paging");

    PageTable page_table;

    page_table.map_page(0, 10);
    page_table.map_page(1, 11);
    page_table.map_page(2, 20);

    const std::vector<std::uint64_t> addresses = {
        0, 100, 4095, 4096, 8192, 9000
    };

    for (const auto address : addresses) {
        try {
            const auto physical = page_table.translate(address);

            std::cout
                << "Virtual address "
                << std::setw(5)
                << address
                << " -> physical address "
                << std::setw(6)
                << physical
                << "\n";
        } catch (const std::exception& error) {
            std::cout
                << "Virtual address "
                << std::setw(5)
                << address
                << " -> "
                << error.what()
                << "\n";
        }
    }
}


// ============================================================================
// 7. TLB
// ============================================================================

class TLB {
private:
    struct Entry {
        std::uint64_t frame;
        std::uint64_t last_used;
    };

    std::size_t capacity_;
    std::uint64_t clock_ = 0;
    std::unordered_map<std::uint64_t, Entry> entries_;

public:
    explicit TLB(std::size_t capacity)
        : capacity_(capacity) {
        if (capacity == 0) {
            throw std::invalid_argument(
                "TLB capacity must be positive"
            );
        }
    }

    std::optional<std::uint64_t> lookup(
        std::uint64_t virtual_page
    ) {
        ++clock_;

        const auto found = entries_.find(virtual_page);

        if (found == entries_.end()) {
            return std::nullopt;
        }

        found->second.last_used = clock_;
        return found->second.frame;
    }

    void insert(
        std::uint64_t virtual_page,
        std::uint64_t frame
    ) {
        ++clock_;

        if (entries_.size() >= capacity_ &&
            entries_.find(virtual_page) == entries_.end()) {

            auto oldest = entries_.begin();

            for (auto current = entries_.begin();
                 current != entries_.end();
                 ++current) {

                if (current->second.last_used <
                    oldest->second.last_used) {
                    oldest = current;
                }
            }

            entries_.erase(oldest);
        }

        entries_[virtual_page] = {
            frame,
            clock_
        };
    }
};

void demonstrate_tlb() {
    print_section("6. Translation Lookaside Buffer");

    PageTable page_table;
    page_table.map_page(1, 100);
    page_table.map_page(2, 200);
    page_table.map_page(3, 300);

    TLB tlb(2);

    const std::vector<std::uint64_t> pages = {
        1, 1, 2, 1, 3, 1, 2, 3
    };

    std::size_t tlb_hits = 0;
    std::size_t tlb_misses = 0;

    for (const auto page : pages) {
        auto frame = tlb.lookup(page);

        if (frame.has_value()) {
            ++tlb_hits;

            std::cout
                << "Virtual page " << page
                << " -> frame " << *frame
                << " [TLB]\n";
        } else {
            ++tlb_misses;

            const auto physical =
                page_table.translate(page * page_table.page_size());

            const auto resolved_frame =
                physical / page_table.page_size();

            tlb.insert(page, resolved_frame);

            std::cout
                << "Virtual page " << page
                << " -> frame " << resolved_frame
                << " [page table]\n";
        }
    }

    std::cout << "TLB hits:   " << tlb_hits << "\n";
    std::cout << "TLB misses: " << tlb_misses << "\n";
}


// ============================================================================
// 8. WRITE-BACK CACHE
// ============================================================================

struct WriteEntry {
    std::uint64_t value;
    bool dirty;
};

class WriteBackCache {
private:
    std::size_t capacity_;
    std::list<std::uint64_t> order_;
    std::unordered_map<
        std::uint64_t,
        std::pair<WriteEntry, std::list<std::uint64_t>::iterator>
    > entries_;

    std::unordered_map<std::uint64_t, std::uint64_t> memory_;
    std::size_t dirty_evictions_ = 0;

public:
    explicit WriteBackCache(std::size_t capacity)
        : capacity_(capacity) {
        if (capacity == 0) {
            throw std::invalid_argument(
                "cache capacity must be positive"
            );
        }
    }

    void write(std::uint64_t address, std::uint64_t value) {
        const auto existing = entries_.find(address);

        if (existing != entries_.end()) {
            order_.erase(existing->second.second);
            entries_.erase(existing);
        } else if (entries_.size() >= capacity_) {
            const std::uint64_t oldest = order_.front();
            order_.pop_front();

            auto old_entry = entries_.find(oldest);

            if (old_entry != entries_.end()) {
                if (old_entry->second.first.dirty) {
                    memory_[oldest] = old_entry->second.first.value;
                    ++dirty_evictions_;
                }

                entries_.erase(old_entry);
            }
        }

        order_.push_back(address);

        entries_[address] = {
            {value, true},
            std::prev(order_.end())
        };
    }

    void flush() {
        for (const auto& [address, entry] : entries_) {
            if (entry.first.dirty) {
                memory_[address] = entry.first.value;
            }
        }
    }

    std::size_t dirty_evictions() const {
        return dirty_evictions_;
    }

    std::uint64_t memory_value(std::uint64_t address) const {
        const auto found = memory_.find(address);

        if (found == memory_.end()) {
            return 0;
        }

        return found->second;
    }
};

void demonstrate_write_back() {
    print_section("7. Write-back cache");

    WriteBackCache cache(2);

    cache.write(10, 100);
    cache.write(20, 200);

    std::cout
        << "Memory[10] before eviction: "
        << cache.memory_value(10)
        << "\n";

    cache.write(30, 300);

    std::cout
        << "Memory[10] after eviction:  "
        << cache.memory_value(10)
        << "\n";

    cache.flush();

    std::cout
        << "Memory[20] after flush:      "
        << cache.memory_value(20)
        << "\n";

    std::cout
        << "Dirty evictions: "
        << cache.dirty_evictions()
        << "\n";
}


// ============================================================================
// 9. AMAT
// ============================================================================

double average_memory_access_time(
    double hit_time,
    double miss_rate,
    double miss_penalty
) {
    if (hit_time < 0 ||
        miss_rate < 0 ||
        miss_rate > 1 ||
        miss_penalty < 0) {
        throw std::invalid_argument(
            "invalid AMAT parameters"
        );
    }

    return hit_time + miss_rate * miss_penalty;
}

void demonstrate_amat() {
    print_section("8. Average Memory Access Time");

    const double l1_hit_time = 1.0;
    const double l1_miss_rate = 0.05;
    const double l2_penalty = 10.0;

    const double amat = average_memory_access_time(
        l1_hit_time,
        l1_miss_rate,
        l2_penalty
    );

    std::cout << "L1 hit time:  " << l1_hit_time << " ns\n";
    std::cout << "L1 miss rate: " << l1_miss_rate * 100.0 << "%\n";
    std::cout << "Miss penalty: " << l2_penalty << " ns\n";
    std::cout << "AMAT:         " << amat << " ns\n";

    std::cout << R"(
The simplified relationship is:

    AMAT = hit time + miss rate * miss penalty

With several cache levels, the miss penalty at one level includes the lookup
time and possible misses at lower levels.
)";
}


// ============================================================================
// 10. TRANSACTION ANALYTICS CASE STUDY
// ============================================================================

class TransactionAnalyticsEngine {
private:
    std::vector<Transaction> transactions_;

public:
    explicit TransactionAnalyticsEngine(
        std::vector<Transaction> transactions
    )
        : transactions_(std::move(transactions)) {}

    double total_value() const {
        return sum_transactions(transactions_);
    }

    std::unordered_map<std::uint32_t, double>
    totals_by_account() const {
        std::unordered_map<std::uint32_t, double> result;

        for (const auto& transaction : transactions_) {
            result[transaction.account_id] += transaction.amount;
        }

        return result;
    }

    const std::vector<Transaction>& transactions() const {
        return transactions_;
    }
};

void demonstrate_transaction_engine() {
    print_section("9. Industry-style transaction analytics case study");

    std::vector<Transaction> transactions;
    transactions.reserve(1'000'000);

    std::mt19937 generator(42);
    std::uniform_int_distribution<std::uint32_t> account_distribution(
        1,
        50'000
    );
    std::uniform_real_distribution<double> amount_distribution(
        1.0,
        10'000.0
    );

    for (std::uint64_t id = 1; id <= 1'000'000; ++id) {
        transactions.push_back({
            id,
            account_distribution(generator),
            amount_distribution(generator)
        });
    }

    TransactionAnalyticsEngine engine(std::move(transactions));

    const auto start = Clock::now();
    const double total = engine.total_value();
    const auto end = Clock::now();

    const double elapsed =
        std::chrono::duration<double, std::milli>(
            end - start
        ).count();

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "Transactions processed: "
              << engine.transactions().size()
              << "\n";

    std::cout << "Total transaction value: "
              << total
              << "\n";

    std::cout << "Sequential processing time: "
              << elapsed
              << " ms\n";

    const auto totals = engine.totals_by_account();

    std::cout
        << "Accounts represented: "
        << totals.size()
        << "\n";

    std::cout << R"(
The case study intentionally uses std::vector<Transaction> because the
analytics operation scans every record.

The design has several memory-hierarchy advantages:

    - records are stored contiguously
    - sequential traversal has strong spatial locality
    - reserve() avoids repeated vector growth
    - the working set can be processed in predictable batches

The unordered_map used for account aggregation has a different access
pattern. Hash-table lookups involve buckets and may require pointer or
indirect accesses, which can have less predictable locality than a simple
vector scan.

The choice of data structure therefore influences both algorithmic complexity
and memory-system behavior.
)";
}


// ============================================================================
// 11. WORKING SET SIZE
// ============================================================================

void demonstrate_working_set() {
    print_section("10. Working-set behavior");

    constexpr std::size_t small_size = 32 * 1024;
    constexpr std::size_t large_size = 16 * 1024 * 1024;

    std::vector<std::uint64_t> small(small_size / sizeof(std::uint64_t));
    std::vector<std::uint64_t> large(large_size / sizeof(std::uint64_t));

    std::iota(small.begin(), small.end(), 1);
    std::iota(large.begin(), large.end(), 1);

    auto measure = [](const std::vector<std::uint64_t>& data) {
        volatile std::uint64_t total = 0;

        const auto start = Clock::now();

        for (const auto value : data) {
            total += value;
        }

        const auto end = Clock::now();

        return std::chrono::duration<double, std::micro>(
            end - start
        ).count();
    };

    const double small_time = measure(small);
    const double large_time = measure(large);

    std::cout
        << "Small working set: "
        << small.size() * sizeof(std::uint64_t) / 1024
        << " KiB, time="
        << small_time
        << " microseconds\n";

    std::cout
        << "Large working set: "
        << large.size() * sizeof(std::uint64_t) / (1024 * 1024)
        << " MiB, time="
        << large_time
        << " microseconds\n";

    std::cout << R"(
A working set is the subset of data actively used during a period of
execution.

If the working set fits into a particular cache level, accesses may obtain
a high hit rate at that level. As the working set grows beyond cache capacity,
capacity misses can increase.

This experiment is intentionally not treated as a fixed hardware benchmark.
)";
}


// ============================================================================
// 12. SECURITY AND MEMORY PROTECTION
// ============================================================================

void explain_security() {
    print_section("11. Memory hierarchy and security");

    std::cout << R"(
Virtual memory provides process isolation and enables page-level permissions.

Important security mechanisms include:

    - read/write/execute page permissions
    - non-executable memory
    - address-space randomization
    - protected kernel/user address spaces
    - cache side-channel defenses
    - speculative-execution mitigations
    - careful treatment of sensitive memory

Cache behavior can leak information through timing even when software follows
architectural access rules. This is why security engineering sometimes needs
to consider microarchitectural behavior in addition to source-level logic.

A normal C++ program should also avoid undefined behavior such as:

    - use-after-free
    - out-of-bounds access
    - uninitialized reads
    - double deletion
    - invalid pointer arithmetic

These errors can corrupt process memory independently of CPU cache design.
)";
}


// ============================================================================
// 13. EDGE CASES
// ============================================================================

void demonstrate_edge_cases() {
    print_section("12. Validation and failure conditions");

    try {
        DirectMappedCache invalid_cache(0);
    } catch (const std::exception& error) {
        std::cout
            << "Invalid cache correctly rejected: "
            << error.what()
            << "\n";
    }

    try {
        PageTable invalid_page_table(3000);
    } catch (const std::exception& error) {
        std::cout
            << "Invalid page size correctly rejected: "
            << error.what()
            << "\n";
    }

    try {
        average_memory_access_time(1.0, 1.5, 10.0);
    } catch (const std::exception& error) {
        std::cout
            << "Invalid miss rate correctly rejected: "
            << error.what()
            << "\n";
    }

    try {
        sum_transactions_strided(
            std::vector<Transaction>{},
            0
        );
    } catch (const std::exception& error) {
        std::cout
            << "Invalid stride correctly rejected: "
            << error.what()
            << "\n";
    }
}


// ============================================================================
// 14. ARCHITECTURAL TRADE-OFFS
// ============================================================================

void explain_tradeoffs() {
    print_section("13. Memory hierarchy design trade-offs");

    std::cout << R"(
Cache capacity:
    Larger caches can reduce capacity misses but require more silicon area,
    power, and potentially longer lookup paths.

Associativity:
    Higher associativity reduces conflict misses but requires more tag
    comparisons and replacement logic.

Write-through:
    Simple lower-level visibility, but potentially higher write traffic.

Write-back:
    Reduces lower-level write traffic, but requires dirty tracking and
    more complicated eviction behavior.

Prefetching:
    Can hide latency for predictable workloads, but incorrect predictions
    consume bandwidth and cache capacity.

Contiguous data:
    Often improves spatial locality.

Pointer-heavy structures:
    Can provide flexible relationships but may increase indirection and
    reduce locality.

Large working sets:
    May exceed cache and TLB capacity, increasing latency.

There is no single memory layout or cache design that is optimal for every
workload.
)";
}


// ============================================================================
// 15. MAIN
// ============================================================================

int main() {
    try {
        print_section("MEMORY HIERARCHY TECHNICAL CASE STUDY");

        std::cout << R"(
Scenario:
    A transaction analytics engine must process large volumes of financial
    records efficiently.

The implementation connects application-level data structures to the
underlying memory hierarchy:

    Registers
        ↓
    CPU cache
        ↓
    RAM
        ↓
    Persistent storage

The C++ program models the cache and translation mechanisms explicitly
while using a realistic data-processing workload for the application layer.
)";

        demonstrate_contiguous_data();
        demonstrate_direct_mapped_cache();
        demonstrate_set_associativity();
        demonstrate_multi_level_memory();
        demonstrate_virtual_memory();
        demonstrate_tlb();
        demonstrate_write_back();
        demonstrate_amat();
        demonstrate_transaction_engine();
        demonstrate_working_set();
        explain_security();
        demonstrate_edge_cases();
        explain_tradeoffs();

        print_section("Completed");
        std::cout
            << "Memory hierarchy C++ case study completed successfully.\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << "\n";

        return 1;
    }
}
