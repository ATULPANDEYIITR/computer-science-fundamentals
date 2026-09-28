/*
 * Parallel Computing Fundamentals
 *
 * Industry-style case study:
 * ---------------------------
 * A parallel analytics engine processes a large collection of transaction
 * records. It demonstrates:
 *
 *   1. Sequential processing
 *   2. Task partitioning
 *   3. Multicore parallel execution with std::thread
 *   4. Data parallelism
 *   5. MIMD-style independent analytical operations
 *   6. Mutex-protected shared statistics
 *   7. Condition-variable coordination
 *   8. Error handling and validation
 *   9. Load balancing
 *  10. Performance measurement
 *  11. Speedup and efficiency
 *  12. Amdahl's Law
 *
 * Compile:
 *   g++ -std=c++17 -O2 -pthread parallel_computing.cpp -o parallel_computing
 *
 * Run:
 *   ./parallel_computing
 *
 * Windows with MinGW:
 *   g++ -std=c++17 -O2 -pthread parallel_computing.cpp -o parallel_computing.exe
 */

#include <algorithm>
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <cmath>
#include <cstddef>
#include <exception>
#include <functional>
#include <iomanip>
#include <iostream>
#include <limits>
#include <mutex>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

using namespace std;
using Clock = chrono::steady_clock;

// ============================================================================
// Data model
// ============================================================================

struct Transaction {
    int id;
    double amount;
    int category;
};

struct WorkerStatistics {
    double total = 0.0;
    double maximum = 0.0;
    size_t transactionCount = 0;
    size_t highValueCount = 0;
};

// ============================================================================
// Utility functions
// ============================================================================

void printSection(const string& title) {
    cout << "\n" << string(78, '=') << "\n";
    cout << title << "\n";
    cout << string(78, '=') << "\n";
}

double elapsedMilliseconds(Clock::time_point start,
                           Clock::time_point end) {
    return chrono::duration<double, milli>(end - start).count();
}

size_t recommendedWorkerCount() {
    const unsigned int hardware =
        thread::hardware_concurrency();

    /*
     * hardware_concurrency() may return zero when the implementation cannot
     * determine the value, so a safe fallback is required.
     */
    return hardware == 0 ? 2 : hardware;
}

// ============================================================================
// Dataset generation
// ============================================================================

vector<Transaction> generateTransactions(size_t count) {
    if (count == 0) {
        return {};
    }

    mt19937 generator(42);
    uniform_real_distribution<double> amountDistribution(5.0, 5000.0);
    uniform_int_distribution<int> categoryDistribution(1, 8);

    vector<Transaction> transactions;
    transactions.reserve(count);

    for (size_t index = 0; index < count; ++index) {
        transactions.push_back({
            static_cast<int>(index + 1),
            amountDistribution(generator),
            categoryDistribution(generator)
        });
    }

    return transactions;
}

// ============================================================================
// CPU-intensive operation
// ============================================================================

bool isPrime(int number) {
    if (number < 2) {
        return false;
    }

    if (number == 2) {
        return true;
    }

    if (number % 2 == 0) {
        return false;
    }

    for (int divisor = 3;
         divisor <= number / divisor;
         divisor += 2) {
        if (number % divisor == 0) {
            return false;
        }
    }

    return true;
}

/*
 * Artificial CPU work models an expensive analytical operation. The purpose
 * is to create enough computation for the parallel design to be measurable.
 */
int analyticalRiskScore(const Transaction& transaction) {
    const int seed =
        static_cast<int>(transaction.amount) +
        transaction.id * 13 +
        transaction.category * 101;

    int score = 0;

    for (int offset = 0; offset < 120; ++offset) {
        if (isPrime(seed + offset)) {
            ++score;
        }
    }

    return score;
}

// ============================================================================
// Sequential baseline
// ============================================================================

WorkerStatistics analyzeSequential(
    const vector<Transaction>& transactions) {

    WorkerStatistics statistics;

    for (const auto& transaction : transactions) {
        statistics.total += transaction.amount;
        statistics.maximum =
            max(statistics.maximum, transaction.amount);

        ++statistics.transactionCount;

        if (transaction.amount >= 4000.0) {
            ++statistics.highValueCount;
        }

        /*
         * CPU-bound work is deliberately performed for each record.
         * The result is accumulated so the compiler cannot trivially remove
         * the computation.
         */
        statistics.maximum +=
            analyticalRiskScore(transaction) * 0.000001;
    }

    return statistics;
}

// ============================================================================
// Work partitioning
// ============================================================================

struct Range {
    size_t begin;
    size_t end;
};

vector<Range> partitionRange(size_t total, size_t workers) {
    if (workers == 0) {
        throw invalid_argument("Worker count must be positive.");
    }

    workers = min(workers, max<size_t>(1, total));

    vector<Range> ranges;
    ranges.reserve(workers);

    for (size_t index = 0; index < workers; ++index) {
        const size_t begin =
            (total * index) / workers;

        const size_t end =
            (total * (index + 1)) / workers;

        if (begin < end) {
            ranges.push_back({begin, end});
        }
    }

    return ranges;
}

// ============================================================================
// Parallel data processing
// ============================================================================

WorkerStatistics analyzeRange(
    const vector<Transaction>& transactions,
    Range range) {

    WorkerStatistics local;

    for (size_t index = range.begin;
         index < range.end;
         ++index) {

        const auto& transaction = transactions[index];

        local.total += transaction.amount;

        local.maximum =
            max(local.maximum, transaction.amount);

        ++local.transactionCount;

        if (transaction.amount >= 4000.0) {
            ++local.highValueCount;
        }

        local.maximum +=
            analyticalRiskScore(transaction) * 0.000001;
    }

    return local;
}

WorkerStatistics combineStatistics(
    const vector<WorkerStatistics>& partialResults) {

    WorkerStatistics combined;

    for (const auto& partial : partialResults) {
        combined.total += partial.total;
        combined.maximum =
            max(combined.maximum, partial.maximum);
        combined.transactionCount += partial.transactionCount;
        combined.highValueCount += partial.highValueCount;
    }

    return combined;
}

WorkerStatistics analyzeParallel(
    const vector<Transaction>& transactions,
    size_t workerCount) {

    const auto ranges =
        partitionRange(transactions.size(), workerCount);

    vector<WorkerStatistics> partialResults(ranges.size());
    vector<thread> workers;

    workers.reserve(ranges.size());

    for (size_t index = 0; index < ranges.size(); ++index) {
        workers.emplace_back(
            [&transactions, &partialResults, range = ranges[index], index]() {
                /*
                 * Each worker writes only to its own result slot.
                 * This avoids a shared write hotspot and therefore does not
                 * require a mutex for partial results.
                 */
                partialResults[index] =
                    analyzeRange(transactions, range);
            }
        );
    }

    for (auto& worker : workers) {
        worker.join();
    }

    return combineStatistics(partialResults);
}

// ============================================================================
// Shared-state example with mutex
// ============================================================================

class ThreadSafeCounter {
private:
    mutable mutex mutex_;
    size_t value_ = 0;

public:
    void increment() {
        lock_guard<mutex> lock(mutex_);
        ++value_;
    }

    size_t value() const {
        lock_guard<mutex> lock(mutex_);
        return value_;
    }
};

void demonstrateSynchronization() {
    printSection("Synchronization: Mutex-Protected Shared State");

    ThreadSafeCounter counter;
    vector<thread> workers;

    constexpr size_t workerCount = 8;
    constexpr size_t incrementsPerWorker = 10'000;

    for (size_t worker = 0;
         worker < workerCount;
         ++worker) {

        workers.emplace_back(
            [&counter]() {
                for (size_t index = 0;
                     index < incrementsPerWorker;
                     ++index) {
                    counter.increment();
                }
            }
        );
    }

    for (auto& worker : workers) {
        worker.join();
    }

    cout << "Expected: "
         << workerCount * incrementsPerWorker << "\n";

    cout << "Actual:   "
         << counter.value() << "\n";

    cout << "The mutex provides mutual exclusion around the shared counter.\n";
}

// ============================================================================
// Condition variable example
// ============================================================================

class WorkSignal {
private:
    mutex mutex_;
    condition_variable condition_;
    bool ready_ = false;

public:
    void waitUntilReady() {
        unique_lock<mutex> lock(mutex_);

        condition_.wait(
            lock,
            [this]() {
                return ready_;
            }
        );
    }

    void signalReady() {
        {
            lock_guard<mutex> lock(mutex_);
            ready_ = true;
        }

        condition_.notify_all();
    }
};

void demonstrateConditionVariable() {
    printSection("Thread Coordination: Condition Variable");

    WorkSignal signal;

    thread worker([&signal]() {
        cout << "Worker waiting for initialization...\n";
        signal.waitUntilReady();
        cout << "Worker received initialization signal.\n";
    });

    this_thread::sleep_for(
        chrono::milliseconds(50)
    );

    cout << "Main thread completed initialization.\n";
    signal.signalReady();

    worker.join();
}

// ============================================================================
// MIMD-style analytical tasks
// ============================================================================

double calculateTotal(
    const vector<Transaction>& transactions) {

    return accumulate(
        transactions.begin(),
        transactions.end(),
        0.0,
        [](double total, const Transaction& transaction) {
            return total + transaction.amount;
        }
    );
}

double calculateAverage(
    const vector<Transaction>& transactions) {

    if (transactions.empty()) {
        return 0.0;
    }

    return calculateTotal(transactions) /
           static_cast<double>(transactions.size());
}

size_t countHighValue(
    const vector<Transaction>& transactions,
    double threshold) {

    return count_if(
        transactions.begin(),
        transactions.end(),
        [threshold](const Transaction& transaction) {
            return transaction.amount >= threshold;
        }
    );
}

void demonstrateMIMD(
    const vector<Transaction>& transactions) {

    printSection("MIMD-Style Independent Analytical Tasks");

    /*
     * These threads perform different operations:
     *   - total
     *   - average
     *   - high-value count
     *
     * This is conceptually MIMD because the workers execute different
     * instruction paths over the data.
     */

    double total = 0.0;
    double average = 0.0;
    size_t highValueCount = 0;

    thread totalWorker(
        [&]() {
            total = calculateTotal(transactions);
        }
    );

    thread averageWorker(
        [&]() {
            average = calculateAverage(transactions);
        }
    );

    thread highValueWorker(
        [&]() {
            highValueCount =
                countHighValue(transactions, 4000.0);
        }
    );

    totalWorker.join();
    averageWorker.join();
    highValueWorker.join();

    cout << fixed << setprecision(2);
    cout << "Total:          " << total << "\n";
    cout << "Average:        " << average << "\n";
    cout << "High-value:     " << highValueCount << "\n";
}

// ============================================================================
// SIMD-style data operation
// ============================================================================

vector<double> scalarVectorAdd(
    const vector<double>& left,
    const vector<double>& right) {

    if (left.size() != right.size()) {
        throw invalid_argument(
            "Vector sizes must match."
        );
    }

    vector<double> result(left.size());

    for (size_t index = 0;
         index < left.size();
         ++index) {

        result[index] =
            left[index] + right[index];
    }

    return result;
}

/*
 * This function expresses vector-style processing in groups of four.
 * A compiler may transform suitable loops into real SIMD instructions when
 * optimization is enabled, but grouping alone does not guarantee SIMD.
 */
vector<double> conceptualSIMDAdd(
    const vector<double>& left,
    const vector<double>& right) {

    if (left.size() != right.size()) {
        throw invalid_argument(
            "Vector sizes must match."
        );
    }

    vector<double> result(left.size());

    constexpr size_t lanes = 4;

    size_t index = 0;

    for (; index + lanes <= left.size(); index += lanes) {
        result[index] =
            left[index] + right[index];

        result[index + 1] =
            left[index + 1] + right[index + 1];

        result[index + 2] =
            left[index + 2] + right[index + 2];

        result[index + 3] =
            left[index + 3] + right[index + 3];
    }

    /*
     * The remainder is processed normally when the vector length is not
     * divisible by the conceptual lane count.
     */
    for (; index < left.size(); ++index) {
        result[index] =
            left[index] + right[index];
    }

    return result;
}

void demonstrateSIMD() {
    printSection("SIMD: Single Instruction, Multiple Data");

    vector<double> left{
        1, 2, 3, 4, 5, 6, 7
    };

    vector<double> right{
        10, 20, 30, 40, 50, 60, 70
    };

    const auto result =
        conceptualSIMDAdd(left, right);

    cout << "Vector addition result: ";

    for (double value : result) {
        cout << value << " ";
    }

    cout << "\n";
}

// ============================================================================
// Amdahl's Law
// ============================================================================

double amdahlSpeedup(
    double serialFraction,
    size_t processors) {

    if (serialFraction < 0.0 ||
        serialFraction > 1.0) {
        throw invalid_argument(
            "Serial fraction must be between 0 and 1."
        );
    }

    if (processors == 0) {
        throw invalid_argument(
            "Processor count must be positive."
        );
    }

    return 1.0 /
           (serialFraction +
            (1.0 - serialFraction) /
                static_cast<double>(processors));
}

void demonstrateAmdahl() {
    printSection("Amdahl's Law");

    constexpr double serialFraction = 0.10;

    cout << fixed << setprecision(2);

    for (size_t processors :
         {1, 2, 4, 8, 16, 32, 64}) {

        cout << processors
             << " processors -> "
             << amdahlSpeedup(
                    serialFraction,
                    processors)
             << "x theoretical speedup\n";
    }

    cout <<
        "The serial fraction limits the maximum speedup.\n";
}

// ============================================================================
// Load balancing
// ============================================================================

void demonstrateLoadBalancing() {
    printSection("Load Balancing");

    vector<int> taskCosts{
        1, 1, 1, 25, 1, 1, 30, 1, 1, 20
    };

    const size_t workers = 3;

    const auto ranges =
        partitionRange(taskCosts.size(), workers);

    for (size_t worker = 0;
         worker < ranges.size();
         ++worker) {

        int work = 0;

        for (size_t index = ranges[worker].begin;
             index < ranges[worker].end;
             ++index) {

            work += taskCosts[index];
        }

        cout << "Worker " << worker
             << " estimated workload: "
             << work << "\n";
    }

    cout <<
        "Equal item counts do not guarantee equal execution times.\n";
}

// ============================================================================
// Validation
// ============================================================================

void demonstrateValidation() {
    printSection("Validation and Edge Cases");

    const vector<Transaction> empty;

    const auto emptyResult =
        analyzeSequential(empty);

    cout << "Empty transaction count: "
         << emptyResult.transactionCount << "\n";

    try {
        partitionRange(10, 0);
    } catch (const exception& error) {
        cout << "Invalid worker count handled: "
             << error.what() << "\n";
    }

    try {
        scalarVectorAdd(
            {1.0, 2.0},
            {1.0}
        );
    } catch (const exception& error) {
        cout << "Mismatched vectors handled: "
             << error.what() << "\n";
    }
}

// ============================================================================
// Performance experiment
// ============================================================================

void runPerformanceExperiment(
    const vector<Transaction>& transactions) {

    printSection("Performance Experiment");

    const size_t workers =
        min(
            recommendedWorkerCount(),
            static_cast<size_t>(8)
        );

    auto sequentialStart = Clock::now();

    const auto sequential =
        analyzeSequential(transactions);

    const auto sequentialEnd = Clock::now();

    auto parallelStart = Clock::now();

    const auto parallel =
        analyzeParallel(transactions, workers);

    const auto parallelEnd = Clock::now();

    const double sequentialTime =
        elapsedMilliseconds(
            sequentialStart,
            sequentialEnd
        );

    const double parallelTime =
        elapsedMilliseconds(
            parallelStart,
            parallelEnd
        );

    cout << fixed << setprecision(3);

    cout << "Logical hardware concurrency: "
         << recommendedWorkerCount() << "\n";

    cout << "Workers used: "
         << workers << "\n";

    cout << "Transactions: "
         << transactions.size() << "\n";

    cout << "Sequential time: "
         << sequentialTime << " ms\n";

    cout << "Parallel time:   "
         << parallelTime << " ms\n";

    if (parallelTime > 0.0) {
        const double speedup =
            sequentialTime / parallelTime;

        const double efficiency =
            speedup /
            static_cast<double>(workers);

        cout << "Speedup:         "
             << speedup << "x\n";

        cout << "Efficiency:      "
             << efficiency * 100.0 << "%\n";
    }

    /*
     * The tiny adjustment in maximum exists only to make the CPU calculation
     * observable in both versions. The primary business statistics should
     * still agree to practical floating-point precision.
     */
    cout << "Sequential count: "
         << sequential.transactionCount << "\n";

    cout << "Parallel count:   "
         << parallel.transactionCount << "\n";

    cout << "Sequential total: "
         << sequential.total << "\n";

    cout << "Parallel total:   "
         << parallel.total << "\n";

    cout <<
        "\nObserved speedup depends on workload size, CPU architecture, "
        "compiler optimization, scheduling, memory bandwidth, thread "
        "creation, cache behavior, and other system activity.\n";
}

// ============================================================================
// Architecture discussion
// ============================================================================

void printArchitectureConcepts() {
    printSection("Architecture and Design Concepts");

    cout <<
R"(
Concurrency:
    Multiple activities can make progress during overlapping periods.

Parallelism:
    Multiple operations execute simultaneously.

Multicore:
    Multiple physical CPU cores execute instruction streams.

SIMD:
    One instruction operates on multiple data lanes.

MIMD:
    Multiple instruction streams operate on multiple data sets.

Data parallelism:
    Same operation on separate partitions of data.

Task parallelism:
    Different operations execute concurrently.

Synchronization:
    Mechanisms such as mutexes and condition variables coordinate access
    and execution order.

Race condition:
    Program behavior depends on an uncontrolled ordering of concurrent
    accesses.

Deadlock:
    Two or more execution units wait indefinitely for resources held by
    one another.

Load imbalance:
    Some workers finish much earlier than others.

Granularity:
    The amount of work assigned to a parallel task. Very fine-grained
    tasks can suffer from excessive scheduling and synchronization cost.

Cache locality:
    Access patterns that reuse nearby data can reduce expensive memory
    accesses.

False sharing:
    Independent variables modified by different cores can still cause
    cache-coherence traffic when they occupy the same cache line.

A good parallel design attempts to maximize useful computation while
minimizing synchronization, communication, memory contention, and idle time.
)";
}

// ============================================================================
// Main
// ============================================================================

int main() {
    try {
        printSection("Parallel Computing Fundamentals");

        printArchitectureConcepts();

        const auto transactions =
            generateTransactions(20'000);

        cout << "Generated transactions: "
             << transactions.size() << "\n";

        demonstrateSynchronization();
        demonstrateConditionVariable();
        demonstrateSIMD();
        demonstrateMIMD(transactions);
        demonstrateLoadBalancing();
        demonstrateValidation();

        runPerformanceExperiment(transactions);

        demonstrateAmdahl();

        printSection("Case Study Design Decisions");

        cout <<
R"(
1. The sequential implementation establishes a baseline.
2. The dataset is divided into independent ranges.
3. Each worker processes its own range without shared mutable state.
4. Partial results are combined after workers finish.
5. A mutex example demonstrates controlled shared-state access.
6. A condition variable demonstrates explicit coordination.
7. Independent analytical operations illustrate MIMD.
8. Vector addition illustrates the SIMD programming model.
9. Validation handles empty inputs, invalid worker counts, and mismatched
   vectors.
10. Performance is measured rather than assumed.
11. Amdahl's Law demonstrates why unlimited cores do not produce unlimited
    speedup.
12. Load balancing is treated as a first-class design concern.
)";

        printSection("Program Completed");

        return 0;
    }
    catch (const exception& error) {
        cerr << "Fatal error: "
             << error.what() << "\n";

        return 1;
    }
}
