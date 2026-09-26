#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <exception>
#include <functional>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * Computer Performance Case Study
 *
 * Scenario:
 * A company operates a transaction-processing service. The engineering team
 * wants to understand why two processors with different clock frequencies can
 * have different execution times and why application throughput can improve
 * without reducing the latency of every individual transaction.
 *
 * The program progressively models:
 *   1. Clock frequency and CPU time
 *   2. CPI and IPC
 *   3. Instruction mix
 *   4. Cache and memory penalties
 *   5. Pipeline throughput
 *   6. Amdahl's Law
 *   7. A practical benchmark
 *   8. Percentiles and variability
 *   9. Validation and failure conditions
 *
 * Compile with:
 *   g++ -std=c++17 -O2 computer_performance.cpp -o computer_performance
 */

using Clock = std::chrono::steady_clock;


// ---------------------------------------------------------------------------
// 1. BASIC PERFORMANCE FORMULAS
// ---------------------------------------------------------------------------

double executionTime(
    double instructionCount,
    double cpi,
    double clockRateHz
) {
    if (instructionCount < 0.0) {
        throw std::invalid_argument("instruction count cannot be negative");
    }

    if (cpi <= 0.0) {
        throw std::invalid_argument("CPI must be positive");
    }

    if (clockRateHz <= 0.0) {
        throw std::invalid_argument("clock rate must be positive");
    }

    return (instructionCount * cpi) / clockRateHz;
}

double cpiFromCounters(
    std::uint64_t cycles,
    std::uint64_t instructions
) {
    if (instructions == 0) {
        throw std::invalid_argument(
            "instruction count cannot be zero"
        );
    }

    return static_cast<double>(cycles) /
           static_cast<double>(instructions);
}

double ipcFromCounters(
    std::uint64_t cycles,
    std::uint64_t instructions
) {
    if (cycles == 0) {
        throw std::invalid_argument("cycle count cannot be zero");
    }

    return static_cast<double>(instructions) /
           static_cast<double>(cycles);
}

double amdahlSpeedup(
    double improvedFraction,
    double improvementFactor
) {
    if (improvedFraction < 0.0 || improvedFraction > 1.0) {
        throw std::invalid_argument(
            "improved fraction must be between 0 and 1"
        );
    }

    if (improvementFactor <= 0.0) {
        throw std::invalid_argument(
            "improvement factor must be positive"
        );
    }

    return 1.0 /
           ((1.0 - improvedFraction) +
            improvedFraction / improvementFactor);
}


// ---------------------------------------------------------------------------
// 2. INSTRUCTION MIX
// ---------------------------------------------------------------------------

struct InstructionClass {
    std::string name;
    std::uint64_t count;
    double cpi;
};

struct InstructionMixResult {
    std::uint64_t instructions;
    double cycles;
    double averageCpi;
    double ipc;
};

InstructionMixResult analyzeInstructionMix(
    const std::vector<InstructionClass>& classes
) {
    if (classes.empty()) {
        throw std::invalid_argument(
            "instruction mix cannot be empty"
        );
    }

    std::uint64_t totalInstructions = 0;
    double totalCycles = 0.0;

    for (const auto& instructionClass : classes) {
        if (instructionClass.cpi <= 0.0) {
            throw std::invalid_argument(
                "instruction CPI must be positive"
            );
        }

        totalInstructions += instructionClass.count;

        totalCycles +=
            static_cast<double>(instructionClass.count) *
            instructionClass.cpi;
    }

    if (totalInstructions == 0) {
        throw std::invalid_argument(
            "total instructions cannot be zero"
        );
    }

    return {
        totalInstructions,
        totalCycles,
        totalCycles /
            static_cast<double>(totalInstructions),
        static_cast<double>(totalInstructions) /
            totalCycles
    };
}


// ---------------------------------------------------------------------------
// 3. CPU MODEL
// ---------------------------------------------------------------------------

class CpuModel {
private:
    std::string name_;
    double frequencyHz_;
    double cpi_;

public:
    CpuModel(
        std::string name,
        double frequencyHz,
        double cpi
    )
        : name_(std::move(name)),
          frequencyHz_(frequencyHz),
          cpi_(cpi) {
        if (name_.empty()) {
            throw std::invalid_argument(
                "CPU name cannot be empty"
            );
        }

        if (frequencyHz_ <= 0.0 || cpi_ <= 0.0) {
            throw std::invalid_argument(
                "frequency and CPI must be positive"
            );
        }
    }

    const std::string& name() const {
        return name_;
    }

    double executionTime(
        std::uint64_t instructionCount
    ) const {
        return ::executionTime(
            static_cast<double>(instructionCount),
            cpi_,
            frequencyHz_
        );
    }

    double effectiveIpc() const {
        return 1.0 / cpi_;
    }
};


// ---------------------------------------------------------------------------
// 4. MEMORY AND CACHE MODEL
// ---------------------------------------------------------------------------

struct MemoryModel {
    std::uint64_t computeInstructions;
    double baseCpi;
    std::uint64_t memoryAccesses;
    double cacheHitRate;
    double hitPenaltyCycles;
    double missPenaltyCycles;

    double totalCycles() const {
        if (computeInstructions == 0) {
            throw std::invalid_argument(
                "compute instructions cannot be zero"
            );
        }

        if (baseCpi <= 0.0) {
            throw std::invalid_argument(
                "base CPI must be positive"
            );
        }

        if (cacheHitRate < 0.0 || cacheHitRate > 1.0) {
            throw std::invalid_argument(
                "cache hit rate must be between 0 and 1"
            );
        }

        const double hits =
            static_cast<double>(memoryAccesses) *
            cacheHitRate;

        const double misses =
            static_cast<double>(memoryAccesses) -
            hits;

        return
            static_cast<double>(computeInstructions) *
                baseCpi +
            hits * hitPenaltyCycles +
            misses * missPenaltyCycles;
    }

    double effectiveCpi() const {
        return totalCycles() /
               static_cast<double>(computeInstructions);
    }
};


// ---------------------------------------------------------------------------
// 5. PIPELINE MODEL
// ---------------------------------------------------------------------------

double pipelinedCompletionTime(
    std::size_t jobs,
    double latencySeconds,
    double initiationIntervalSeconds
) {
    if (latencySeconds < 0.0 ||
        initiationIntervalSeconds < 0.0) {
        throw std::invalid_argument(
            "pipeline timing cannot be negative"
        );
    }

    if (jobs == 0) {
        return 0.0;
    }

    /*
     * The first item experiences the complete latency.
     * Once the pipeline is full, new results can appear at the initiation
     * interval. This explains why latency and throughput are different.
     */
    return latencySeconds +
           static_cast<double>(jobs - 1) *
               initiationIntervalSeconds;
}


// ---------------------------------------------------------------------------
// 6. BENCHMARK FRAMEWORK
// ---------------------------------------------------------------------------

struct BenchmarkResult {
    std::string name;
    std::vector<double> milliseconds;

    double mean() const {
        return std::accumulate(
                   milliseconds.begin(),
                   milliseconds.end(),
                   0.0
               ) /
               static_cast<double>(milliseconds.size());
    }

    double median() const {
        std::vector<double> sorted = milliseconds;

        std::sort(
            sorted.begin(),
            sorted.end()
        );

        const std::size_t middle =
            sorted.size() / 2;

        if (sorted.size() % 2 == 0) {
            return (
                sorted[middle - 1] +
                sorted[middle]
            ) / 2.0;
        }

        return sorted[middle];
    }

    double minimum() const {
        return *std::min_element(
            milliseconds.begin(),
            milliseconds.end()
        );
    }

    double maximum() const {
        return *std::max_element(
            milliseconds.begin(),
            milliseconds.end()
        );
    }

    double standardDeviation() const {
        if (milliseconds.size() < 2) {
            return 0.0;
        }

        const double average = mean();

        double sumSquaredDifferences = 0.0;

        for (double value : milliseconds) {
            const double difference =
                value - average;

            sumSquaredDifferences +=
                difference * difference;
        }

        return std::sqrt(
            sumSquaredDifferences /
            static_cast<double>(milliseconds.size())
        );
    }
};


BenchmarkResult benchmark(
    const std::string& name,
    const std::function<std::uint64_t()>& operation,
    std::size_t warmupRuns,
    std::size_t repetitions
) {
    if (repetitions == 0) {
        throw std::invalid_argument(
            "benchmark repetitions must be positive"
        );
    }

    // Warm-up avoids making initialization effects look like normal runtime.
    for (std::size_t i = 0; i < warmupRuns; ++i) {
        volatile std::uint64_t result = operation();
        (void)result;
    }

    BenchmarkResult result;
    result.name = name;
    result.milliseconds.reserve(repetitions);

    for (std::size_t i = 0; i < repetitions; ++i) {
        const auto start = Clock::now();

        volatile std::uint64_t output = operation();
        (void)output;

        const auto end = Clock::now();

        const std::chrono::duration<double, std::milli> elapsed =
            end - start;

        result.milliseconds.push_back(
            elapsed.count()
        );
    }

    return result;
}


// ---------------------------------------------------------------------------
// 7. REALISTIC TRANSACTION WORKLOAD
// ---------------------------------------------------------------------------

struct Transaction {
    std::uint64_t accountId;
    double amount;
    bool approved;
};

std::uint64_t processTransactions(
    const std::vector<Transaction>& transactions
) {
    /*
     * This represents a simplified business workload:
     * - inspect transactions
     * - reject invalid amounts
     * - count approved transactions
     *
     * It is intentionally deterministic so benchmark repetitions execute
     * equivalent work.
     */
    std::uint64_t approvedCount = 0;

    for (const Transaction& transaction : transactions) {
        if (transaction.amount > 0.0 &&
            transaction.amount <= 1'000'000.0 &&
            transaction.approved) {
            ++approvedCount;
        }
    }

    return approvedCount;
}

std::vector<Transaction> createWorkload(
    std::size_t size
) {
    std::vector<Transaction> transactions;
    transactions.reserve(size);

    std::mt19937_64 generator(42);

    std::uniform_real_distribution<double> amountDistribution(
        1.0,
        100'000.0
    );

    for (std::size_t i = 0; i < size; ++i) {
        transactions.push_back({
            static_cast<std::uint64_t>(i),
            amountDistribution(generator),
            (i % 10) != 0
        });
    }

    return transactions;
}


// ---------------------------------------------------------------------------
// 8. PERCENTILE
// ---------------------------------------------------------------------------

double percentile(
    const std::vector<double>& values,
    double percentileValue
) {
    if (values.empty()) {
        throw std::invalid_argument(
            "cannot calculate percentile of empty data"
        );
    }

    if (percentileValue < 0.0 ||
        percentileValue > 100.0) {
        throw std::invalid_argument(
            "percentile must be between 0 and 100"
        );
    }

    std::vector<double> sorted = values;

    std::sort(
        sorted.begin(),
        sorted.end()
    );

    if (sorted.size() == 1) {
        return sorted[0];
    }

    const double position =
        (static_cast<double>(sorted.size()) - 1.0) *
        percentileValue /
        100.0;

    const std::size_t lower =
        static_cast<std::size_t>(
            std::floor(position)
        );

    const std::size_t upper =
        static_cast<std::size_t>(
            std::ceil(position)
        );

    if (lower == upper) {
        return sorted[lower];
    }

    const double fraction =
        position -
        static_cast<double>(lower);

    return sorted[lower] +
           fraction *
               (sorted[upper] - sorted[lower]);
}


// ---------------------------------------------------------------------------
// 9. PERFORMANCE REPORTING
// ---------------------------------------------------------------------------

void printBenchmark(
    const BenchmarkResult& result
) {
    std::cout
        << std::left
        << std::setw(30)
        << result.name
        << " mean="
        << std::setw(10)
        << std::fixed
        << std::setprecision(4)
        << result.mean()
        << " ms median="
        << std::setw(10)
        << result.median()
        << " ms min="
        << std::setw(10)
        << result.minimum()
        << " ms max="
        << std::setw(10)
        << result.maximum()
        << " ms\n";
}


// ---------------------------------------------------------------------------
// 10. MAIN CASE STUDY
// ---------------------------------------------------------------------------

int main() {
    try {
        std::cout
            << "============================================================\n"
            << "COMPUTER PERFORMANCE CASE STUDY\n"
            << "Transaction Processing Service\n"
            << "============================================================\n";

        // -----------------------------------------------------------------
        // Stage 1: Clock speed
        // -----------------------------------------------------------------

        const double clockRate = 3.5e9;

        std::cout
            << "\n1. CLOCK SPEED\n"
            << "Clock rate: "
            << clockRate / 1e9
            << " GHz\n"
            << "Clock period: "
            << (1e9 / clockRate)
            << " ns\n";

        // -----------------------------------------------------------------
        // Stage 2: CPU execution time
        // -----------------------------------------------------------------

        const std::uint64_t instructions =
            1'000'000'000ULL;

        const double cpi = 1.5;

        const double cpuTime =
            executionTime(
                static_cast<double>(instructions),
                cpi,
                clockRate
            );

        const double cycles =
            static_cast<double>(instructions) *
            cpi;

        std::cout
            << "\n2. CPU EXECUTION TIME\n"
            << "Instructions: "
            << instructions
            << "\nCPI: "
            << cpi
            << "\nCycles: "
            << cycles
            << "\nCPU time: "
            << cpuTime * 1000.0
            << " ms\n";

        // -----------------------------------------------------------------
        // Stage 3: CPU architecture comparison
        // -----------------------------------------------------------------

        std::cout
            << "\n3. CPU COMPARISON\n";

        std::vector<CpuModel> cpus = {
            CpuModel("CPU A: 3.0 GHz, CPI 1.0", 3.0e9, 1.0),
            CpuModel("CPU B: 4.0 GHz, CPI 1.5", 4.0e9, 1.5),
            CpuModel("CPU C: 3.2 GHz, CPI 0.8", 3.2e9, 0.8)
        };

        for (const auto& cpu : cpus) {
            const double time =
                cpu.executionTime(2'000'000'000ULL);

            std::cout
                << std::left
                << std::setw(32)
                << cpu.name()
                << " time="
                << std::fixed
                << std::setprecision(3)
                << time * 1000.0
                << " ms, IPC="
                << cpu.effectiveIpc()
                << "\n";
        }

        std::cout
            << "A higher clock frequency alone does not guarantee lower "
               "execution time.\n";

        // -----------------------------------------------------------------
        // Stage 4: Instruction mix
        // -----------------------------------------------------------------

        std::cout
            << "\n4. INSTRUCTION MIX\n";

        const std::vector<InstructionClass> mix = {
            {"integer arithmetic", 500'000, 1.0},
            {"load/store",         300'000, 2.0},
            {"branch",             100'000, 4.0},
            {"floating point",     100'000, 3.0}
        };

        const InstructionMixResult mixResult =
            analyzeInstructionMix(mix);

        for (const auto& item : mix) {
            std::cout
                << std::left
                << std::setw(22)
                << item.name
                << " count="
                << std::setw(9)
                << item.count
                << " CPI="
                << item.cpi
                << "\n";
        }

        std::cout
            << "Weighted CPI: "
            << mixResult.averageCpi
            << "\nIPC: "
            << mixResult.ipc
            << "\n";

        // -----------------------------------------------------------------
        // Stage 5: Cache and memory effects
        // -----------------------------------------------------------------

        std::cout
            << "\n5. CACHE AND MEMORY EFFECTS\n";

        const MemoryModel memoryModel {
            1'000'000,
            1.0,
            200'000,
            0.95,
            2.0,
            100.0
        };

        std::cout
            << "Modeled cycles: "
            << memoryModel.totalCycles()
            << "\nEffective CPI: "
            << memoryModel.effectiveCpi()
            << "\n";

        std::cout
            << "A small cache-miss rate can contribute a large number of "
               "cycles when misses have high latency.\n";

        // -----------------------------------------------------------------
        // Stage 6: Latency versus throughput
        // -----------------------------------------------------------------

        std::cout
            << "\n6. LATENCY VERSUS THROUGHPUT\n";

        const std::size_t transactionCount = 100;
        const double transactionLatency = 10e-6;
        const double initiationInterval = 2e-6;

        const double pipelineTime =
            pipelinedCompletionTime(
                transactionCount,
                transactionLatency,
                initiationInterval
            );

        std::cout
            << "Individual latency: "
            << transactionLatency * 1e6
            << " microseconds\n"
            << "Pipeline completion time: "
            << pipelineTime * 1000.0
            << " ms\n"
            << "Steady-state throughput: "
            << 1.0 / initiationInterval
            << " transactions/s\n";

        // -----------------------------------------------------------------
        // Stage 7: Amdahl's Law
        // -----------------------------------------------------------------

        std::cout
            << "\n7. AMDAHL'S LAW\n";

        const double improvedFraction = 0.80;
        const double improvementFactor = 5.0;

        std::cout
            << "System speedup: "
            << amdahlSpeedup(
                   improvedFraction,
                   improvementFactor
               )
            << "x\n"
            << "Infinite-improvement limit: "
            << 1.0 / (1.0 - improvedFraction)
            << "x\n";

        // -----------------------------------------------------------------
        // Stage 8: Realistic workload
        // -----------------------------------------------------------------

        std::cout
            << "\n8. TRANSACTION WORKLOAD\n";

        const std::vector<Transaction> workload =
            createWorkload(500'000);

        std::cout
            << "Transactions: "
            << workload.size()
            << "\nApproved transactions: "
            << processTransactions(workload)
            << "\n";

        // -----------------------------------------------------------------
        // Stage 9: Benchmark
        // -----------------------------------------------------------------

        std::cout
            << "\n9. BENCHMARK\n";

        const BenchmarkResult transactionBenchmark =
            benchmark(
                "Transaction processing",
                [&workload]() {
                    return processTransactions(workload);
                },
                3,
                10
            );

        printBenchmark(transactionBenchmark);

        // -----------------------------------------------------------------
        // Stage 10: Benchmark statistics
        // -----------------------------------------------------------------

        std::cout
            << "\n10. BENCHMARK STATISTICS\n";

        std::cout
            << "P50: "
            << percentile(
                   transactionBenchmark.milliseconds,
                   50.0
               )
            << " ms\n"
            << "P95: "
            << percentile(
                   transactionBenchmark.milliseconds,
                   95.0
               )
            << " ms\n"
            << "P99: "
            << percentile(
                   transactionBenchmark.milliseconds,
                   99.0
               )
            << " ms\n"
            << "Standard deviation: "
            << transactionBenchmark.standardDeviation()
            << " ms\n";

        // -----------------------------------------------------------------
        // Stage 11: Counter-derived metrics
        // -----------------------------------------------------------------

        std::cout
            << "\n11. HARDWARE-COUNTER INTERPRETATION\n";

        const std::uint64_t measuredCycles =
            4'500'000'000ULL;

        const std::uint64_t retiredInstructions =
            3'000'000'000ULL;

        std::cout
            << "Measured CPI: "
            << cpiFromCounters(
                   measuredCycles,
                   retiredInstructions
               )
            << "\n"
            << "Measured IPC: "
            << ipcFromCounters(
                   measuredCycles,
                   retiredInstructions
               )
            << "\n";

        // -----------------------------------------------------------------
        // Stage 12: Practical engineering interpretation
        // -----------------------------------------------------------------

        std::cout
            << "\n12. ENGINEERING INTERPRETATION\n"
            << "Clock speed describes clock cycles per second.\n"
            << "CPI describes cycles consumed per instruction.\n"
            << "IPC describes instructions completed per cycle.\n"
            << "Latency describes the time associated with an individual result.\n"
            << "Throughput describes completed work per unit time.\n"
            << "Benchmarks measure a workload under a particular environment.\n"
            << "Compiler settings, memory hierarchy, branch behavior, caches,\n"
            << "thermal conditions, operating-system activity, and workload\n"
            << "characteristics can all change observed performance.\n";

        // -----------------------------------------------------------------
        // Stage 13: Edge cases
        // -----------------------------------------------------------------

        std::cout
            << "\n13. FAILURE CONDITIONS\n";

        try {
            executionTime(
                1000.0,
                1.0,
                0.0
            );
        }
        catch (const std::exception& error) {
            std::cout
                << "Invalid clock rate correctly rejected: "
                << error.what()
                << "\n";
        }

        try {
            percentile({}, 95.0);
        }
        catch (const std::exception& error) {
            std::cout
                << "Empty percentile data correctly rejected: "
                << error.what()
                << "\n";
        }

        try {
            CpuModel invalidCpu(
                "Invalid CPU",
                -1.0,
                1.0
            );
        }
        catch (const std::exception& error) {
            std::cout
                << "Invalid CPU correctly rejected: "
                << error.what()
                << "\n";
        }

        // -----------------------------------------------------------------
        // Final technical relationships
        // -----------------------------------------------------------------

        std::cout
            << "\n============================================================\n"
            << "CORE RELATIONSHIPS\n"
            << "============================================================\n"
            << "CPU time = Instruction Count × CPI / Clock Rate\n"
            << "CPI = Cycles / Instructions\n"
            << "IPC = Instructions / Cycles\n"
            << "Speedup = Old Time / New Time\n"
            << "Throughput = Completed Work / Time\n"
            << "Amdahl = 1 / ((1-p) + p/s)\n"
            << "============================================================\n";

        return 0;
    }
    catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << "\n";

        return 1;
    }
}
