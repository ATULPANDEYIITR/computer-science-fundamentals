/*
 * Cache Memory and Cache Simulator
 * =================================
 *
 * C++17 case study:
 * A configurable multi-set cache simulator for studying CPU cache behavior.
 *
 * Demonstrates:
 * - Cache blocks and lines
 * - Direct mapping
 * - Set associativity
 * - Fully associative mapping
 * - Tags, sets, and offsets
 * - LRU and FIFO replacement
 * - Cache hits and misses
 * - Compulsory/conflict/capacity-oriented classification
 * - Write-back and write-through policies
 * - Write-allocate and no-write-allocate
 * - Memory-reference traces
 * - Multi-level cache behavior
 * - AMAT calculations
 * - Matrix traversal and locality
 *
 * Compile:
 *     g++ -std=c++17 -O2 cache_simulator.cpp -o cache_simulator
 *
 * Run:
 *     ./cache_simulator
 */

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <iomanip>
#include <iostream>
#include <limits>
#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

using namespace std;

// ---------------------------------------------------------------------------
// Enumerations
// ---------------------------------------------------------------------------

enum class ReplacementPolicy {
    LRU,
    FIFO
};

enum class WritePolicy {
    WriteBack,
    WriteThrough
};

enum class AllocationPolicy {
    WriteAllocate,
    NoWriteAllocate
};

// ---------------------------------------------------------------------------
// Cache line
// ---------------------------------------------------------------------------

struct CacheLine {
    bool valid = false;
    bool dirty = false;
    uint64_t tag = 0;
    uint64_t lastUsed = 0;
    uint64_t insertedAt = 0;
};

// ---------------------------------------------------------------------------
// Address fields
// ---------------------------------------------------------------------------

struct AddressFields {
    uint64_t blockNumber;
    uint64_t offset;
    uint64_t setIndex;
    uint64_t tag;
};

// ---------------------------------------------------------------------------
// Access result
// ---------------------------------------------------------------------------

struct AccessResult {
    uint64_t address = 0;
    uint64_t blockNumber = 0;
    uint64_t setIndex = 0;
    uint64_t tag = 0;
    bool hit = false;
    uint64_t latency = 0;
    optional<uint64_t> evictedTag;
    bool dirtyEviction = false;
};

// ---------------------------------------------------------------------------
// Statistics
// ---------------------------------------------------------------------------

struct Statistics {
    uint64_t accesses = 0;
    uint64_t hits = 0;
    uint64_t misses = 0;
    uint64_t compulsoryMisses = 0;
    uint64_t conflictMisses = 0;
    uint64_t capacityMisses = 0;
    uint64_t writeHits = 0;
    uint64_t writeMisses = 0;
    uint64_t writeBacks = 0;

    double hitRate() const {
        if (accesses == 0) {
            return 0.0;
        }

        return static_cast<double>(hits) /
               static_cast<double>(accesses);
    }

    double missRate() const {
        if (accesses == 0) {
            return 0.0;
        }

        return static_cast<double>(misses) /
               static_cast<double>(accesses);
    }

    void print(const string& name) const {
        cout << "\n" << name << "\n";
        cout << string(name.size(), '-') << "\n";

        cout << "Accesses:           " << accesses << "\n";
        cout << "Hits:               " << hits << "\n";
        cout << "Misses:             " << misses << "\n";

        cout << fixed << setprecision(2);
        cout << "Hit rate:           "
             << hitRate() * 100.0 << "%\n";
        cout << "Miss rate:          "
             << missRate() * 100.0 << "%\n";

        cout << "Compulsory misses:  "
             << compulsoryMisses << "\n";
        cout << "Conflict misses:    "
             << conflictMisses << "\n";
        cout << "Capacity misses:    "
             << capacityMisses << "\n";
        cout << "Write hits:         "
             << writeHits << "\n";
        cout << "Write misses:       "
             << writeMisses << "\n";
        cout << "Write-backs:        "
             << writeBacks << "\n";
    }
};

// ---------------------------------------------------------------------------
// Utility functions
// ---------------------------------------------------------------------------

bool isPowerOfTwo(uint64_t value) {
    return value != 0 && (value & (value - 1)) == 0;
}

unsigned integerLog2(uint64_t value) {
    if (!isPowerOfTwo(value)) {
        throw invalid_argument(
            "Value must be a positive power of two."
        );
    }

    unsigned result = 0;

    while (value > 1) {
        value >>= 1;
        ++result;
    }

    return result;
}

// ---------------------------------------------------------------------------
// Cache simulator
// ---------------------------------------------------------------------------

class CacheSimulator {
private:
    uint64_t cacheSize;
    uint64_t blockSize;
    uint64_t associativity;
    uint64_t numberOfLines;
    uint64_t numberOfSets;

    uint64_t hitLatency;
    uint64_t missLatency;

    ReplacementPolicy replacementPolicy;
    WritePolicy writePolicy;
    AllocationPolicy allocationPolicy;

    vector<vector<CacheLine>> sets;

    Statistics statistics;

    uint64_t clock = 0;

    unordered_set<uint64_t> seenBlocks;
    unordered_set<uint64_t> evictedBlocks;

public:
    CacheSimulator(
        uint64_t cacheSize,
        uint64_t blockSize,
        uint64_t associativity,
        uint64_t hitLatency = 1,
        uint64_t missLatency = 50,
        ReplacementPolicy replacementPolicy =
            ReplacementPolicy::LRU,
        WritePolicy writePolicy =
            WritePolicy::WriteBack,
        AllocationPolicy allocationPolicy =
            AllocationPolicy::WriteAllocate
    )
        : cacheSize(cacheSize),
          blockSize(blockSize),
          associativity(associativity),
          hitLatency(hitLatency),
          missLatency(missLatency),
          replacementPolicy(replacementPolicy),
          writePolicy(writePolicy),
          allocationPolicy(allocationPolicy) {

        validateConfiguration();

        numberOfLines = cacheSize / blockSize;
        numberOfSets = numberOfLines / associativity;

        sets.resize(numberOfSets);

        for (auto& currentSet : sets) {
            currentSet.resize(associativity);
        }
    }

    void validateConfiguration() const {
        if (cacheSize == 0 ||
            blockSize == 0 ||
            associativity == 0) {
            throw invalid_argument(
                "Cache parameters must be positive."
            );
        }

        if (!isPowerOfTwo(cacheSize) ||
            !isPowerOfTwo(blockSize) ||
            !isPowerOfTwo(associativity)) {
            throw invalid_argument(
                "Cache size, block size, and associativity "
                "must be powers of two."
            );
        }

        if (cacheSize < blockSize) {
            throw invalid_argument(
                "Cache size cannot be smaller than block size."
            );
        }

        const uint64_t lines = cacheSize / blockSize;

        if (associativity > lines ||
            lines % associativity != 0) {
            throw invalid_argument(
                "Invalid associativity for cache size."
            );
        }
    }

    void reset() {
        for (auto& currentSet : sets) {
            for (auto& line : currentSet) {
                line = CacheLine{};
            }
        }

        statistics = Statistics{};
        clock = 0;
        seenBlocks.clear();
        evictedBlocks.clear();
    }

    AddressFields decomposeAddress(uint64_t address) const {
        const uint64_t blockNumber =
            address / blockSize;

        const uint64_t offset =
            address % blockSize;

        const uint64_t setIndex =
            blockNumber % numberOfSets;

        const uint64_t tag =
            blockNumber / numberOfSets;

        return {
            blockNumber,
            offset,
            setIndex,
            tag
        };
    }

private:
    CacheLine* findLine(
        uint64_t setIndex,
        uint64_t tag
    ) {
        for (auto& line : sets[setIndex]) {
            if (line.valid && line.tag == tag) {
                return &line;
            }
        }

        return nullptr;
    }

    CacheLine* chooseVictim(uint64_t setIndex) {
        auto& currentSet = sets[setIndex];

        for (auto& line : currentSet) {
            if (!line.valid) {
                return &line;
            }
        }

        if (replacementPolicy == ReplacementPolicy::LRU) {
            return &*min_element(
                currentSet.begin(),
                currentSet.end(),
                [](const CacheLine& a, const CacheLine& b) {
                    return a.lastUsed < b.lastUsed;
                }
            );
        }

        return &*min_element(
            currentSet.begin(),
            currentSet.end(),
            [](const CacheLine& a, const CacheLine& b) {
                return a.insertedAt < b.insertedAt;
            }
        );
    }

    string classifyMiss(uint64_t blockNumber) const {
        if (!seenBlocks.contains(blockNumber)) {
            return "compulsory";
        }

        if (evictedBlocks.contains(blockNumber)) {
            if (associativity == 1) {
                return "conflict";
            }

            return "capacity-or-conflict";
        }

        return "unknown";
    }

    void recordMissClassification(
        const string& classification
    ) {
        if (classification == "compulsory") {
            ++statistics.compulsoryMisses;
        } else if (classification == "conflict") {
            ++statistics.conflictMisses;
        } else if (
            classification == "capacity-or-conflict"
        ) {
            /*
             * Exact capacity/conflict classification can require a
             * parallel reference model. This educational simulator records
             * the ambiguous category as capacity-oriented.
             */
            ++statistics.capacityMisses;
        }
    }

public:
    AccessResult access(
        uint64_t address,
        const string& operation = "read",
        bool verbose = false
    ) {
        if (operation != "read" &&
            operation != "write") {
            throw invalid_argument(
                "Operation must be read or write."
            );
        }

        ++clock;
        ++statistics.accesses;

        const AddressFields fields =
            decomposeAddress(address);

        CacheLine* line =
            findLine(fields.setIndex, fields.tag);

        if (line != nullptr) {
            ++statistics.hits;

            if (operation == "write") {
                ++statistics.writeHits;

                if (writePolicy == WritePolicy::WriteBack) {
                    line->dirty = true;
                } else {
                    line->dirty = false;
                }
            }

            line->lastUsed = clock;

            AccessResult result{
                address,
                fields.blockNumber,
                fields.setIndex,
                fields.tag,
                true,
                hitLatency,
                nullopt,
                false
            };

            if (verbose) {
                printAccess(result, operation);
            }

            return result;
        }

        ++statistics.misses;

        if (operation == "write") {
            ++statistics.writeMisses;
        }

        const string classification =
            classifyMiss(fields.blockNumber);

        recordMissClassification(classification);

        seenBlocks.insert(fields.blockNumber);

        /*
         * With no-write-allocate, a write miss bypasses this cache.
         */
        if (
            operation == "write" &&
            allocationPolicy ==
                AllocationPolicy::NoWriteAllocate
        ) {
            AccessResult result{
                address,
                fields.blockNumber,
                fields.setIndex,
                fields.tag,
                false,
                missLatency,
                nullopt,
                false
            };

            if (verbose) {
                printAccess(result, operation);
            }

            return result;
        }

        CacheLine* victim =
            chooseVictim(fields.setIndex);

        optional<uint64_t> evictedTag;
        bool dirtyEviction = false;

        if (victim->valid) {
            evictedTag = victim->tag;
            dirtyEviction = victim->dirty;

            const uint64_t evictedBlock =
                victim->tag * numberOfSets +
                fields.setIndex;

            evictedBlocks.insert(evictedBlock);

            if (
                victim->dirty &&
                writePolicy == WritePolicy::WriteBack
            ) {
                ++statistics.writeBacks;
            }
        }

        /*
         * Fill the cache line with the requested block.
         */
        victim->valid = true;
        victim->tag = fields.tag;
        victim->lastUsed = clock;
        victim->insertedAt = clock;

        victim->dirty =
            operation == "write" &&
            writePolicy == WritePolicy::WriteBack;

        AccessResult result{
            address,
            fields.blockNumber,
            fields.setIndex,
            fields.tag,
            false,
            hitLatency + missLatency,
            evictedTag,
            dirtyEviction
        };

        if (verbose) {
            printAccess(result, operation);
        }

        return result;
    }

    void run(
        const vector<uint64_t>& addresses,
        const string& operation = "read",
        bool verbose = false
    ) {
        for (uint64_t address : addresses) {
            access(address, operation, verbose);
        }
    }

    const Statistics& getStatistics() const {
        return statistics;
    }

    uint64_t getHitLatency() const {
        return hitLatency;
    }

    uint64_t getMissLatency() const {
        return missLatency;
    }

    void printAccess(
        const AccessResult& result,
        const string& operation
    ) const {
        cout << left
             << setw(6)
             << operation
             << " address=" << setw(4)
             << result.address
             << " block=" << setw(4)
             << result.blockNumber
             << " set=" << setw(3)
             << result.setIndex
             << " tag=" << setw(4)
             << result.tag
             << (result.hit ? "HIT " : "MISS")
             << " latency="
             << result.latency;

        if (result.evictedTag.has_value()) {
            cout << " evictedTag="
                 << *result.evictedTag;
        }

        if (result.dirtyEviction) {
            cout << " dirtyWriteback=true";
        }

        cout << "\n";
    }

    void describe() const {
        const string mapping =
            associativity == 1
                ? "direct-mapped"
                : associativity == numberOfLines
                    ? "fully-associative"
                    : "set-associative";

        cout << "\nCACHE CONFIGURATION\n";
        cout << "-------------------\n";
        cout << "Capacity:           "
             << cacheSize << " bytes\n";
        cout << "Block size:         "
             << blockSize << " bytes\n";
        cout << "Lines:              "
             << numberOfLines << "\n";
        cout << "Sets:               "
             << numberOfSets << "\n";
        cout << "Associativity:      "
             << associativity << "-way\n";
        cout << "Mapping:            "
             << mapping << "\n";
        cout << "Hit latency:        "
             << hitLatency << "\n";
        cout << "Miss penalty:       "
             << missLatency << "\n";
    }

    void dump() const {
        cout << "\nCACHE CONTENTS\n";
        cout << "--------------\n";

        for (size_t setIndex = 0;
             setIndex < sets.size();
             ++setIndex) {

            cout << "Set "
                 << setIndex
                 << ": ";

            for (
                size_t way = 0;
                way < sets[setIndex].size();
                ++way
            ) {
                const CacheLine& line =
                    sets[setIndex][way];

                if (!line.valid) {
                    cout << "way "
                         << way
                         << "=EMPTY ";
                    continue;
                }

                cout << "way "
                     << way
                     << "=tag:"
                     << line.tag
                     << (line.dirty ? "*" : " ")
                     << " ";
            }

            cout << "\n";
        }
    }
};

// ---------------------------------------------------------------------------
// AMAT
// ---------------------------------------------------------------------------

double calculateAMAT(
    double hitTime,
    double missRate,
    double missPenalty
) {
    if (
        hitTime < 0 ||
        missRate < 0 ||
        missRate > 1 ||
        missPenalty < 0
    ) {
        throw invalid_argument(
            "Invalid AMAT parameters."
        );
    }

    return hitTime +
           missRate * missPenalty;
}

// ---------------------------------------------------------------------------
// Locality examples
// ---------------------------------------------------------------------------

vector<uint64_t> sequentialTrace(
    uint64_t start,
    uint64_t end,
    uint64_t stride
) {
    vector<uint64_t> trace;

    for (
        uint64_t address = start;
        address < end;
        address += stride
    ) {
        trace.push_back(address);
    }

    return trace;
}

vector<uint64_t> repeatedTrace(
    const vector<uint64_t>& values,
    size_t repetitions
) {
    vector<uint64_t> trace;

    for (size_t i = 0; i < repetitions; ++i) {
        trace.insert(
            trace.end(),
            values.begin(),
            values.end()
        );
    }

    return trace;
}

// ---------------------------------------------------------------------------
// Matrix traversal
// ---------------------------------------------------------------------------

vector<uint64_t> rowMajorMatrix(
    size_t rows,
    size_t columns
) {
    vector<uint64_t> trace;

    for (size_t row = 0; row < rows; ++row) {
        for (size_t column = 0;
             column < columns;
             ++column) {

            trace.push_back(
                static_cast<uint64_t>(
                    row * columns + column
                )
            );
        }
    }

    return trace;
}

vector<uint64_t> columnWiseMatrix(
    size_t rows,
    size_t columns
) {
    vector<uint64_t> trace;

    for (size_t column = 0;
         column < columns;
         ++column) {

        for (size_t row = 0;
             row < rows;
             ++row) {

            trace.push_back(
                static_cast<uint64_t>(
                    row * columns + column
                )
            );
        }
    }

    return trace;
}

// ---------------------------------------------------------------------------
// Demonstrations
// ---------------------------------------------------------------------------

void demonstrateAddressMapping() {
    cout << "\nADDRESS MAPPING\n";
    cout << "===============\n";

    CacheSimulator cache(
        64,
        8,
        1
    );

    const auto fields =
        cache.decomposeAddress(37);

    cout << "Address:       37\n";
    cout << "Block number:  "
         << fields.blockNumber << "\n";
    cout << "Offset:        "
         << fields.offset << "\n";
    cout << "Set index:     "
         << fields.setIndex << "\n";
    cout << "Tag:           "
         << fields.tag << "\n";

    cout << "Formula:\n";
    cout << "  block = address / block_size\n";
    cout << "  offset = address % block_size\n";
    cout << "  set = block % number_of_sets\n";
    cout << "  tag = block / number_of_sets\n";
}

void compareMapping() {
    cout << "\nMAPPING TECHNIQUES\n";
    cout << "==================\n";

    const vector<uint64_t> trace = {
        0, 32, 64, 96,
        0, 32, 64, 96,
        0, 32, 64, 96
    };

    struct Configuration {
        string name;
        uint64_t associativity;
    };

    const vector<Configuration> configurations = {
        {"Direct mapped", 1},
        {"2-way set associative", 2},
        {"Fully associative", 8}
    };

    for (const auto& configuration :
         configurations) {

        CacheSimulator cache(
            64,
            8,
            configuration.associativity
        );

        cache.run(trace);

        const auto& stats =
            cache.getStatistics();

        cout << left
             << setw(28)
             << configuration.name
             << "hits=" << setw(3)
             << stats.hits
             << "misses=" << setw(3)
             << stats.misses
             << "hitRate="
             << fixed
             << setprecision(2)
             << stats.hitRate() * 100.0
             << "%\n";
    }
}

void compareReplacementPolicies() {
    cout << "\nREPLACEMENT POLICIES\n";
    cout << "====================\n";

    const vector<uint64_t> trace = {
        0, 8, 16, 0, 8, 24, 0, 8
    };

    for (
        ReplacementPolicy policy :
        {
            ReplacementPolicy::LRU,
            ReplacementPolicy::FIFO
        }
    ) {
        CacheSimulator cache(
            16,
            8,
            2,
            1,
            50,
            policy
        );

        cache.run(trace);

        const auto& stats =
            cache.getStatistics();

        cout << (
            policy == ReplacementPolicy::LRU
                ? "LRU"
                : "FIFO"
        );

        cout << ": hits="
             << stats.hits
             << ", misses="
             << stats.misses
             << ", hitRate="
             << fixed
             << setprecision(2)
             << stats.hitRate() * 100.0
             << "%\n";
    }
}

void demonstrateWritePolicies() {
    cout << "\nWRITE POLICIES\n";
    cout << "==============\n";

    const vector<pair<string, uint64_t>> trace = {
        {"write", 0},
        {"read", 0},
        {"write", 0},
        {"write", 16},
        {"read", 0}
    };

    for (
        WritePolicy policy :
        {
            WritePolicy::WriteBack,
            WritePolicy::WriteThrough
        }
    ) {
        CacheSimulator cache(
            16,
            8,
            1,
            1,
            50,
            ReplacementPolicy::LRU,
            policy,
            AllocationPolicy::WriteAllocate
        );

        cout << "\n"
             << (
                 policy == WritePolicy::WriteBack
                     ? "Write-back"
                     : "Write-through"
             )
             << "\n";

        for (const auto& [operation, address] :
             trace) {

            cache.access(
                address,
                operation,
                true
            );
        }

        cache.getStatistics().print(
            "Write policy statistics"
        );
    }
}

void demonstrateMultiLevelCache() {
    cout << "\nMULTI-LEVEL CACHE\n";
    cout << "=================\n";

    CacheSimulator l1(
        32,
        8,
        2,
        1,
        4
    );

    CacheSimulator l2(
        128,
        8,
        4,
        8,
        40
    );

    const vector<uint64_t> trace = {
        0, 8, 16, 24,
        0, 8,
        64, 72,
        0, 8
    };

    uint64_t totalCycles = 0;

    for (uint64_t address : trace) {
        const AccessResult l1Result =
            l1.access(address);

        if (l1Result.hit) {
            totalCycles += l1.getHitLatency();

            cout << "address="
                 << address
                 << " -> L1 HIT\n";

            continue;
        }

        const AccessResult l2Result =
            l2.access(address);

        if (l2Result.hit) {
            totalCycles +=
                l1.getMissLatency() +
                l2.getHitLatency();

            cout << "address="
                 << address
                 << " -> L1 MISS, L2 HIT\n";
        } else {
            totalCycles +=
                l1.getMissLatency() +
                l2.getMissLatency();

            cout << "address="
                 << address
                 << " -> L1 MISS, L2 MISS, RAM\n";
        }
    }

    cout << "Estimated cycles: "
         << totalCycles
         << "\n";

    l1.getStatistics().print("L1");
    l2.getStatistics().print("L2");
}

void demonstrateAMAT() {
    cout << "\nAVERAGE MEMORY ACCESS TIME\n";
    cout << "==========================\n";

    const vector<tuple<double, double, double>> examples = {
        {1.0, 0.05, 50.0},
        {1.0, 0.10, 50.0},
        {2.0, 0.02, 80.0}
    };

    for (const auto& [hitTime, missRate, penalty] :
         examples) {

        const double amat =
            calculateAMAT(
                hitTime,
                missRate,
                penalty
            );

        cout << "hit="
             << hitTime
             << ", missRate="
             << missRate * 100.0
             << "%, penalty="
             << penalty
             << " => AMAT="
             << fixed
             << setprecision(2)
             << amat
             << "\n";
    }
}

void demonstrateLocality() {
    cout << "\nLOCALITY\n";
    cout << "========\n";

    CacheSimulator cache(
        64,
        16,
        2
    );

    const auto sequential =
        sequentialTrace(0, 64, 4);

    cache.run(sequential);

    cache.getStatistics().print(
        "Sequential spatial locality"
    );

    cache.reset();

    const auto repeated =
        repeatedTrace(
            {0, 4, 8, 12},
            16
        );

    cache.run(repeated);

    cache.getStatistics().print(
        "Repeated temporal locality"
    );
}

void demonstrateMatrixLocality() {
    cout << "\nMATRIX TRAVERSAL\n";
    cout << "================\n";

    const auto rowTrace =
        rowMajorMatrix(16, 16);

    const auto columnTrace =
        columnWiseMatrix(16, 16);

    for (
        const auto& [name, trace] :
        vector<pair<string, vector<uint64_t>>>{
            {"Row-major", rowTrace},
            {"Column-wise", columnTrace}
        }
    ) {
        CacheSimulator cache(
            128,
            16,
            4
        );

        cache.run(trace);

        const auto& stats =
            cache.getStatistics();

        cout << left
             << setw(16)
             << name
             << "hits="
             << setw(4)
             << stats.hits
             << "misses="
             << setw(4)
             << stats.misses
             << "hitRate="
             << fixed
             << setprecision(2)
             << stats.hitRate() * 100.0
             << "%\n";
    }
}

void demonstrateEdgeCases() {
    cout << "\nEDGE CASES\n";
    cout << "==========\n";

    CacheSimulator cache(
        16,
        4,
        2
    );

    for (
        uint64_t address :
        {0ULL, 3ULL, 4ULL, 7ULL,
         8ULL, 12ULL, 15ULL, 16ULL}
    ) {
        const auto result =
            cache.access(address);

        cout << "address="
             << setw(2)
             << address
             << " block="
             << setw(2)
             << result.blockNumber
             << " set="
             << result.setIndex
             << " tag="
             << result.tag
             << " hit="
             << boolalpha
             << result.hit
             << "\n";
    }

    try {
        CacheSimulator invalid(
            16,
            3,
            1
        );
    } catch (const exception& error) {
        cout << "Rejected invalid configuration: "
             << error.what()
             << "\n";
    }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

int main() {
    try {
        cout << string(72, '=') << "\n";
        cout << "CACHE MEMORY AND CACHE SIMULATOR\n";
        cout << string(72, '=') << "\n";

        cout << "\nCACHE LEVELS\n";
        cout << "============\n";
        cout << "L1: smallest and fastest cache level.\n";
        cout << "L2: larger and slower than L1.\n";
        cout << "L3: larger and often shared between CPU cores.\n";
        cout << "RAM: larger capacity with substantially higher latency.\n";

        demonstrateAddressMapping();
        demonstrateLocality();
        compareMapping();
        compareReplacementPolicies();
        demonstrateWritePolicies();
        demonstrateMultiLevelCache();
        demonstrateAMAT();
        demonstrateMatrixLocality();
        demonstrateEdgeCases();

        cout << "\nKEY FORMULAS\n";
        cout << "============\n";
        cout << "lines = cache_size / block_size\n";
        cout << "sets = lines / associativity\n";
        cout << "block = address / block_size\n";
        cout << "offset = address % block_size\n";
        cout << "set = block % sets\n";
        cout << "tag = block / sets\n";
        cout << "hit rate = hits / accesses\n";
        cout << "miss rate = misses / accesses\n";
        cout << "AMAT = hit time + miss rate * miss penalty\n";

        cout << "\nSIMULATION COMPLETE\n";
    }
    catch (const exception& error) {
        cerr << "Fatal error: "
             << error.what()
             << "\n";

        return 1;
    }

    return 0;
}
