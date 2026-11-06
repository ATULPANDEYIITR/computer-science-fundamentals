#include <algorithm>
#include <cstdint>
#include <exception>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

using namespace std;

/*
 * SPACE COMPLEXITY
 *
 * Memory-aware data processing and resource allocation.
 *
 * Demonstrates:
 * - Constant auxiliary space
 * - Linear auxiliary space
 * - Recursive versus iterative algorithms
 * - In-place operations
 * - Hash-based memory consumption
 * - Dynamic programming optimization
 * - Memory budgeting
 * - STL capacity and allocation considerations
 */

enum class Complexity {
    CONSTANT,
    LOGARITHMIC,
    LINEAR,
    QUADRATIC
};

string complexityName(Complexity complexity) {
    switch (complexity) {
        case Complexity::CONSTANT:
            return "O(1)";
        case Complexity::LOGARITHMIC:
            return "O(log n)";
        case Complexity::LINEAR:
            return "O(n)";
        case Complexity::QUADRATIC:
            return "O(n^2)";
    }

    return "Unknown";
}

struct MemoryEstimate {
    string algorithm;
    size_t inputSize;
    uint64_t estimatedBytes;
    Complexity complexity;
    string explanation;
};

class MemoryBudget {
private:
    uint64_t limitBytes;

public:
    explicit MemoryBudget(uint64_t limit) : limitBytes(limit) {
        if (limit == 0) {
            throw invalid_argument("Memory budget must be positive.");
        }
    }

    void validate(uint64_t required) const {
        if (required > limitBytes) {
            throw runtime_error(
                "Memory budget exceeded. Required: " +
                to_string(required) +
                ", available: " +
                to_string(limitBytes)
            );
        }
    }

    uint64_t available() const {
        return limitBytes;
    }
};

class DataProcessor {
public:
    static int64_t sumConstantSpace(const vector<int>& values) {
        int64_t total = 0;

        for (int value : values) {
            total += value;
        }

        return total;
    }

    static vector<int> copyData(const vector<int>& values) {
        return vector<int>(values.begin(), values.end());
    }

    static void reverseInPlace(vector<int>& values) {
        size_t left = 0;
        size_t right = values.size();

        while (left < right && left < --right) {
            swap(values[left], values[right]);
            ++left;
        }
    }

    static int iterativeBinarySearch(
        const vector<int>& values,
        int target
    ) {
        int left = 0;
        int right = static_cast<int>(values.size()) - 1;

        while (left <= right) {
            int middle = left + (right - left) / 2;

            if (values[middle] == target) {
                return middle;
            }

            if (values[middle] < target) {
                left = middle + 1;
            } else {
                right = middle - 1;
            }
        }

        return -1;
    }

    static int recursiveBinarySearch(
        const vector<int>& values,
        int target,
        int left,
        int right
    ) {
        if (left > right) {
            return -1;
        }

        int middle = left + (right - left) / 2;

        if (values[middle] == target) {
            return middle;
        }

        if (values[middle] > target) {
            return recursiveBinarySearch(
                values, target, left, middle - 1
            );
        }

        return recursiveBinarySearch(
            values, target, middle + 1, right
        );
    }

    static vector<int> uniqueValues(const vector<int>& values) {
        unordered_set<int> seen;
        vector<int> result;

        seen.reserve(values.size());
        result.reserve(values.size());

        for (int value : values) {
            if (seen.insert(value).second) {
                result.push_back(value);
            }
        }

        return result;
    }

    static int64_t fibonacciFullTable(int n) {
        validateN(n);

        if (n == 0) {
            return 0;
        }

        vector<int64_t> dp(n + 1, 0);
        dp[1] = 1;

        for (int i = 2; i <= n; ++i) {
            if (dp[i - 1] >
                numeric_limits<int64_t>::max() - dp[i - 2]) {
                throw overflow_error("Fibonacci result exceeds int64_t.");
            }

            dp[i] = dp[i - 1] + dp[i - 2];
        }

        return dp[n];
    }

    static int64_t fibonacciOptimized(int n) {
        validateN(n);

        int64_t previous = 0;
        int64_t current = 1;

        for (int i = 0; i < n; ++i) {
            if (current >
                numeric_limits<int64_t>::max() - previous) {
                throw overflow_error("Fibonacci result exceeds int64_t.");
            }

            int64_t next = previous + current;
            previous = current;
            current = next;
        }

        return previous;
    }

    static int knapsackFull(
        const vector<int>& weights,
        const vector<int>& values,
        int capacity
    ) {
        validateKnapsack(weights, values, capacity);

        size_t rows = weights.size() + 1;
        size_t columns = static_cast<size_t>(capacity) + 1;

        vector<vector<int>> dp(
            rows,
            vector<int>(columns, 0)
        );

        for (size_t i = 1; i < rows; ++i) {
            for (int current = 0; current <= capacity; ++current) {
                dp[i][current] = dp[i - 1][current];

                if (weights[i - 1] <= current) {
                    dp[i][current] = max(
                        dp[i][current],
                        values[i - 1] +
                        dp[i - 1][current - weights[i - 1]]
                    );
                }
            }
        }

        return dp.back()[capacity];
    }

    static int knapsackOptimized(
        const vector<int>& weights,
        const vector<int>& values,
        int capacity
    ) {
        validateKnapsack(weights, values, capacity);

        vector<int> dp(
            static_cast<size_t>(capacity) + 1,
            0
        );

        for (size_t i = 0; i < weights.size(); ++i) {
            for (int current = capacity;
                 current >= weights[i];
                 --current) {

                dp[current] = max(
                    dp[current],
                    values[i] + dp[current - weights[i]]
                );
            }
        }

        return dp[capacity];
    }

private:
    static void validateN(int n) {
        if (n < 0 || n > 92) {
            throw invalid_argument(
                "n must be between 0 and 92 for int64_t Fibonacci."
            );
        }
    }

    static void validateKnapsack(
        const vector<int>& weights,
        const vector<int>& values,
        int capacity
    ) {
        if (weights.size() != values.size()) {
            throw invalid_argument(
                "Weights and values must have equal lengths."
            );
        }

        if (capacity < 0 || capacity > 1000000) {
            throw invalid_argument("Invalid capacity.");
        }

        for (int weight : weights) {
            if (weight <= 0) {
                throw invalid_argument(
                    "Weights must be positive."
                );
            }
        }

        for (int value : values) {
            if (value < 0) {
                throw invalid_argument(
                    "Values cannot be negative."
                );
            }
        }
    }
};

class MemoryAnalyzer {
public:
    static uint64_t linearEstimate(
        uint64_t count,
        uint64_t bytesPerElement
    ) {
        if (
            bytesPerElement != 0 &&
            count > numeric_limits<uint64_t>::max() / bytesPerElement
        ) {
            throw overflow_error("Memory estimate overflow.");
        }

        return count * bytesPerElement;
    }

    static vector<MemoryEstimate> analyze(size_t n) {
        if (n > 1000000) {
            throw invalid_argument("Input size exceeds analysis limit.");
        }

        uint64_t linear = linearEstimate(n, sizeof(int));

        uint64_t quadratic = linearEstimate(
            linear,
            static_cast<uint64_t>(n)
        );

        return {
            {
                "Constant-space sum",
                n,
                sizeof(int64_t),
                Complexity::CONSTANT,
                "One accumulator and loop variables."
            },
            {
                "Vector copy",
                n,
                linear,
                Complexity::LINEAR,
                "One additional array of integer values."
            },
            {
                "Matrix allocation",
                n,
                quadratic,
                Complexity::QUADRATIC,
                "An n by n integer matrix, excluding container overhead."
            },
            {
                "Binary search recursion",
                n,
                n == 0 ? 0 : 64 * (64 - __builtin_clzll(n)),
                Complexity::LOGARITHMIC,
                "Approximate call-stack estimate, not an ABI measurement."
            }
        };
    }
};

void runTests() {
    vector<int> values = {1, 2, 3, 4};

    if (DataProcessor::sumConstantSpace(values) != 10) {
        throw runtime_error("Sum test failed.");
    }

    vector<int> reversed = values;
    DataProcessor::reverseInPlace(reversed);

    if (reversed != vector<int>({4, 3, 2, 1})) {
        throw runtime_error("Reverse test failed.");
    }

    vector<int> sorted = {1, 3, 5, 7, 9};

    if (DataProcessor::iterativeBinarySearch(sorted, 7) != 3) {
        throw runtime_error("Iterative search test failed.");
    }

    if (DataProcessor::recursiveBinarySearch(
            sorted, 5, 0, 4
        ) != 2) {
        throw runtime_error("Recursive search test failed.");
    }

    vector<int> duplicates = {1, 1, 2, 2, 3};

    if (DataProcessor::uniqueValues(duplicates).size() != 3) {
        throw runtime_error("Unique-value test failed.");
    }

    if (DataProcessor::fibonacciFullTable(10) != 55) {
        throw runtime_error("Full Fibonacci test failed.");
    }

    if (DataProcessor::fibonacciOptimized(10) != 55) {
        throw runtime_error("Optimized Fibonacci test failed.");
    }

    vector<int> weights = {2, 3, 4, 5};
    vector<int> profits = {3, 4, 5, 6};

    if (DataProcessor::knapsackFull(weights, profits, 5) != 7) {
        throw runtime_error("Full knapsack test failed.");
    }

    if (DataProcessor::knapsackOptimized(weights, profits, 5) != 7) {
        throw runtime_error("Optimized knapsack test failed.");
    }

    cout << "All C++17 tests passed.\n";
}

int main() {
    try {
        cout << "SPACE COMPLEXITY ANALYSIS\n";
        cout << "=========================\n";

        runTests();

        cout << "\nMEMORY COMPLEXITY REPORT\n";

        const size_t n = 1000;

        for (const auto& report : MemoryAnalyzer::analyze(n)) {
            cout << "\nAlgorithm: " << report.algorithm << '\n';
            cout << "Input size: " << report.inputSize << '\n';

            cout << "Estimated bytes: "
                 << report.estimatedBytes << '\n';

            cout << "Complexity: "
                 << complexityName(report.complexity) << '\n';

            cout << "Explanation: "
                 << report.explanation << '\n';
        }

        cout << "\nSTL MEMORY CHARACTERISTICS\n";

        vector<int> data;
        data.reserve(10000);

        for (int i = 0; i < 10000; ++i) {
            data.push_back(i);
        }

        cout << "Vector size: " << data.size() << '\n';
        cout << "Vector capacity: " << data.capacity() << '\n';

        cout << "Allocated element storage estimate: "
             << data.capacity() * sizeof(int)
             << " bytes\n";

        unordered_set<int> unique(data.begin(), data.end());

        cout << "Hash-set distinct elements: "
             << unique.size() << '\n';

        cout << "Hash-set bucket count: "
             << unique.bucket_count() << '\n';

        cout << "\nDYNAMIC PROGRAMMING TRADE-OFF\n";

        vector<int> weights = {2, 3, 4, 5};
        vector<int> profits = {3, 4, 5, 6};

        cout << "Full-table result: "
             << DataProcessor::knapsackFull(
                    weights, profits, 5
                ) << '\n';

        cout << "Optimized result: "
             << DataProcessor::knapsackOptimized(
                    weights, profits, 5
                ) << '\n';

        cout << "\nMEMORY BUDGET VALIDATION\n";

        MemoryBudget budget(1024 * 1024);

        uint64_t estimate = MemoryAnalyzer::linearEstimate(
            100000,
            sizeof(int)
        );

        budget.validate(estimate);

        cout << "Accepted: " << estimate
             << " bytes within "
             << budget.available() << " bytes.\n";

        cout << "\nPROCESS COMPLETE\n";
    }
    catch (const exception& error) {
        cerr << "Execution error: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
