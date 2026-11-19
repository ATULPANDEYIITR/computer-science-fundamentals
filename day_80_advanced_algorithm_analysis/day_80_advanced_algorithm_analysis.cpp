#include <algorithm>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;

/*
 * Advanced Algorithm Analysis
 *
 * C++17 implementation:
 * 1. Amortized analysis using a two-stack queue.
 * 2. Potential method for queue operations.
 * 3. Randomized quicksort with instrumentation.
 * 4. Probabilistic analysis of hashing.
 * 5. Monte Carlo coupon collector experiment.
 */

class ValidationError : public runtime_error {
public:
    explicit ValidationError(const string& message)
        : runtime_error(message) {}
};


struct QueueStatistics {
    uint64_t enqueueOperations = 0;
    uint64_t dequeueOperations = 0;
    uint64_t elementTransfers = 0;
    uint64_t actualCost = 0;
    uint64_t amortizedCost = 0;
};


/*
 * Queue implemented with two stacks.
 *
 * Each element is:
 * - Pushed onto the input stack once.
 * - Transferred to the output stack at most once.
 * - Popped from the output stack at most once.
 *
 * Therefore, m queue operations perform O(m) total
 * stack operations, giving O(1) amortized queue cost.
 *
 * Potential function:
 *     Phi = 2 * number_of_elements_in_input_stack
 */

template<typename T>
class AmortizedQueue {
private:
    vector<T> inputStack;
    vector<T> outputStack;
    QueueStatistics statistics;

    size_t potential() const {
        return 2 * inputStack.size();
    }

public:
    void enqueue(const T& value) {
        size_t oldPotential = potential();

        inputStack.push_back(value);
        statistics.enqueueOperations++;
        statistics.actualCost++;

        size_t newPotential = potential();

        statistics.amortizedCost +=
            1 + newPotential - oldPotential;
    }

    bool dequeue(T& result) {
        if (inputStack.empty() && outputStack.empty()) {
            return false;
        }

        size_t oldPotential = potential();
        uint64_t cost = 0;

        if (outputStack.empty()) {
            while (!inputStack.empty()) {
                outputStack.push_back(inputStack.back());
                inputStack.pop_back();

                statistics.elementTransfers++;
                cost += 2;
            }
        }

        result = outputStack.back();
        outputStack.pop_back();
        cost++;

        statistics.dequeueOperations++;
        statistics.actualCost += cost;

        size_t newPotential = potential();

        statistics.amortizedCost +=
            cost + newPotential - oldPotential;

        return true;
    }

    size_t size() const {
        return inputStack.size() + outputStack.size();
    }

    bool empty() const {
        return size() == 0;
    }

    const QueueStatistics& getStatistics() const {
        return statistics;
    }
};


struct SortStatistics {
    uint64_t comparisons = 0;
    uint64_t swaps = 0;
    uint64_t partitions = 0;
};


class RandomizedQuickSort {
private:
    mt19937_64 generator;
    SortStatistics statistics;

    int partition(vector<int>& values, int low, int high) {
        statistics.partitions++;

        uniform_int_distribution<int> distribution(low, high);
        int pivotIndex = distribution(generator);

        swap(values[pivotIndex], values[high]);
        statistics.swaps++;

        int pivot = values[high];
        int boundary = low - 1;

        for (int i = low; i < high; i++) {
            statistics.comparisons++;

            if (values[i] <= pivot) {
                boundary++;
                if (boundary != i) {
                    swap(values[boundary], values[i]);
                    statistics.swaps++;
                }
            }
        }

        if (boundary + 1 != high) {
            swap(values[boundary + 1], values[high]);
            statistics.swaps++;
        }

        return boundary + 1;
    }

    void sortRange(vector<int>& values, int low, int high) {
        /*
         * Tail-recursion elimination:
         * recurse into the smaller partition and iterate
         * over the larger partition.
         *
         * This limits recursion depth to O(log n)
         * even when partitions are highly unbalanced.
         */

        while (low < high) {
            int pivot = partition(values, low, high);

            int leftSize = pivot - low;
            int rightSize = high - pivot;

            if (leftSize < rightSize) {
                sortRange(values, low, pivot - 1);
                low = pivot + 1;
            } else {
                sortRange(values, pivot + 1, high);
                high = pivot - 1;
            }
        }
    }

public:
    explicit RandomizedQuickSort(uint64_t seed = 42)
        : generator(seed) {}

    SortStatistics sort(vector<int>& values) {
        statistics = {};

        if (!values.empty()) {
            sortRange(
                values,
                0,
                static_cast<int>(values.size()) - 1
            );
        }

        return statistics;
    }
};


double harmonicNumber(int n) {
    if (n < 0) {
        throw ValidationError("n cannot be negative.");
    }

    double result = 0.0;

    for (int i = 1; i <= n; i++) {
        result += 1.0 / i;
    }

    return result;
}


double expectedQuickSortComparisons(int n) {
    if (n < 0) {
        throw ValidationError("Invalid input size.");
    }

    if (n <= 1) return 0.0;

    return 2.0 * (n + 1) * harmonicNumber(n) - 4.0 * n;
}


/*
 * Monte Carlo simulation of the coupon collector problem.
 *
 * E[T] = n * H(n)
 *
 * Expected time is Theta(n log n).
 */

struct ProbabilityResult {
    double observedMean;
    double theoreticalMean;
    double minimum;
    double maximum;
    double standardDeviation;
};


ProbabilityResult couponCollector(
    int couponTypes,
    int trials,
    uint64_t seed
) {
    if (couponTypes <= 0 || trials <= 0) {
        throw ValidationError(
            "Coupon types and trials must be positive."
        );
    }

    mt19937_64 generator(seed);

    uniform_int_distribution<int> distribution(
        0, couponTypes - 1
    );

    vector<double> observations;
    observations.reserve(trials);

    for (int trial = 0; trial < trials; trial++) {
        vector<bool> collected(couponTypes, false);
        int uniqueCount = 0;
        int draws = 0;

        while (uniqueCount < couponTypes) {
            int coupon = distribution(generator);
            draws++;

            if (!collected[coupon]) {
                collected[coupon] = true;
                uniqueCount++;
            }
        }

        observations.push_back(draws);
    }

    double average = accumulate(
        observations.begin(),
        observations.end(),
        0.0
    ) / trials;

    double variance = 0.0;

    for (double value : observations) {
        variance += (value - average) * (value - average);
    }

    variance /= trials;

    auto bounds = minmax_element(
        observations.begin(),
        observations.end()
    );

    return {
        average,
        couponTypes * harmonicNumber(couponTypes),
        *bounds.first,
        *bounds.second,
        sqrt(variance)
    };
}


/*
 * Hash table with linear probing.
 *
 * Demonstrates probabilistic hashing behavior and
 * the impact of load factor on expected search cost.
 */

class LinearProbingHashTable {
private:
    vector<int> keys;
    vector<bool> occupied;
    size_t capacity;
    size_t elements = 0;

    size_t hashFunction(int key) const {
        return static_cast<size_t>(
            hash<int>{}(key) % capacity
        );
    }

public:
    explicit LinearProbingHashTable(size_t requestedCapacity)
        : keys(requestedCapacity),
          occupied(requestedCapacity, false),
          capacity(requestedCapacity) {

        if (capacity == 0) {
            throw ValidationError(
                "Hash table capacity must be positive."
            );
        }
    }

    bool insert(int key) {
        if (elements == capacity) {
            return false;
        }

        size_t position = hashFunction(key);

        for (size_t attempts = 0; attempts < capacity; attempts++) {
            if (!occupied[position]) {
                keys[position] = key;
                occupied[position] = true;
                elements++;
                return true;
            }

            if (keys[position] == key) {
                return false;
            }

            position = (position + 1) % capacity;
        }

        return false;
    }

    bool contains(int key, size_t& probes) const {
        probes = 0;
        size_t position = hashFunction(key);

        for (size_t attempts = 0; attempts < capacity; attempts++) {
            probes++;

            if (!occupied[position]) {
                return false;
            }

            if (keys[position] == key) {
                return true;
            }

            position = (position + 1) % capacity;
        }

        return false;
    }

    double loadFactor() const {
        return static_cast<double>(elements) / capacity;
    }

    size_t size() const {
        return elements;
    }
};


void testQueue() {
    AmortizedQueue<int> queue;

    for (int i = 1; i <= 10000; i++) {
        queue.enqueue(i);
    }

    int value = 0;

    for (int i = 1; i <= 10000; i++) {
        if (!queue.dequeue(value)) {
            throw runtime_error("Unexpected empty queue.");
        }

        if (value != i) {
            throw runtime_error("FIFO invariant violated.");
        }
    }

    if (!queue.empty()) {
        throw runtime_error("Queue should be empty.");
    }

    const auto& stats = queue.getStatistics();

    cout << "\nAMORTIZED QUEUE ANALYSIS\n";
    cout << "Enqueues: " << stats.enqueueOperations << '\n';
    cout << "Dequeues: " << stats.dequeueOperations << '\n';
    cout << "Transfers: " << stats.elementTransfers << '\n';
    cout << "Actual stack operations: " << stats.actualCost << '\n';
    cout << "Amortized accounting cost: "
         << stats.amortizedCost << '\n';

    if (stats.actualCost > 3 * 20000) {
        throw runtime_error("Unexpected queue cost.");
    }
}


void testRandomizedSort() {
    vector<int> values(10000);
    iota(values.begin(), values.end(), 1);

    mt19937_64 generator(12345);
    shuffle(values.begin(), values.end(), generator);

    RandomizedQuickSort sorter(2026);
    SortStatistics stats = sorter.sort(values);

    if (!is_sorted(values.begin(), values.end())) {
        throw runtime_error("Sorting validation failed.");
    }

    cout << "\nRANDOMIZED QUICKSORT\n";
    cout << "Elements: " << values.size() << '\n';
    cout << "Comparisons: " << stats.comparisons << '\n';
    cout << "Swaps: " << stats.swaps << '\n';
    cout << "Partitions: " << stats.partitions << '\n';
    cout << "Expected comparisons: "
         << expectedQuickSortComparisons(
                static_cast<int>(values.size())
            ) << '\n';
}


void testHashTable() {
    LinearProbingHashTable table(20000);

    for (int i = 0; i < 10000; i++) {
        if (!table.insert(i * 7)) {
            throw runtime_error("Hash insertion failed.");
        }
    }

    uint64_t totalProbes = 0;

    for (int i = 0; i < 10000; i++) {
        size_t probes = 0;

        if (!table.contains(i * 7, probes)) {
            throw runtime_error("Inserted key not found.");
        }

        totalProbes += probes;
    }

    cout << "\nPROBABILISTIC HASHING\n";
    cout << "Elements: " << table.size() << '\n';
    cout << "Load factor: " << table.loadFactor() << '\n';
    cout << "Average successful search probes: "
         << static_cast<double>(totalProbes) / 10000
         << '\n';
}


void testProbability() {
    ProbabilityResult result = couponCollector(
        30,
        10000,
        2026
    );

    cout << "\nCOUPON COLLECTOR EXPERIMENT\n";
    cout << "Observed mean: " << result.observedMean << '\n';
    cout << "Theoretical mean: " << result.theoreticalMean << '\n';
    cout << "Minimum: " << result.minimum << '\n';
    cout << "Maximum: " << result.maximum << '\n';
    cout << "Standard deviation: "
         << result.standardDeviation << '\n';
}


void runEdgeCaseTests() {
    vector<int> empty;
    RandomizedQuickSort sorter;
    sorter.sort(empty);

    if (!empty.empty()) {
        throw runtime_error("Empty sorting test failed.");
    }

    vector<int> duplicates = {5, 5, 5, 5, 5};
    sorter.sort(duplicates);

    if (!is_sorted(duplicates.begin(), duplicates.end())) {
        throw runtime_error("Duplicate sorting test failed.");
    }

    AmortizedQueue<int> queue;
    int value = 0;

    if (queue.dequeue(value)) {
        throw runtime_error("Empty dequeue should fail.");
    }

    try {
        LinearProbingHashTable invalid(0);
        throw runtime_error("Invalid hash capacity accepted.");
    } catch (const ValidationError&) {
        // Expected validation failure.
    }

    cout << "\nEDGE CASE TESTS PASSED\n";
}


int main() {
    try {
        cout << fixed << setprecision(4);
        cout << "ADVANCED ALGORITHM ANALYSIS\n";

        testQueue();
        testRandomizedSort();
        testHashTable();
        testProbability();
        runEdgeCaseTests();

        cout << "\nALL TESTS PASSED\n";
    } catch (const exception& error) {
        cerr << "Execution error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
