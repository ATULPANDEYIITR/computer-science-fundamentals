#include <algorithm>
#include <chrono>
#include <cmath>
#include <functional>
#include <iomanip>
#include <iostream>
#include <limits>
#include <random>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>

using namespace std;

enum class AlgorithmType {
    Searching,
    Sorting,
    Optimization,
    Multiplication
};

struct AlgorithmMetrics {
    string name;
    size_t inputSize;
    size_t recursiveCalls;
    double elapsedMilliseconds;
};

struct Recurrence {
    string name;
    int a;
    int b;
    double d;

    double criticalExponent() const {
        if (a < 1 || b < 2 || d < 0) {
            throw invalid_argument("Invalid recurrence.");
        }

        return log(static_cast<double>(a)) /
               log(static_cast<double>(b));
    }

    string complexity() const {
        double critical = criticalExponent();
        constexpr double EPS = 1e-10;

        if (d < critical - EPS) {
            ostringstream result;
            result << "Theta(n^" << fixed
                   << setprecision(3) << critical << ")";
            return result.str();
        }

        if (abs(d - critical) <= EPS) {
            ostringstream result;
            result << "Theta(n^" << fixed
                   << setprecision(3) << critical << " log n)";
            return result.str();
        }

        ostringstream result;
        result << "Theta(n^" << fixed
               << setprecision(3) << d << ")";
        return result.str();
    }
};

class DivideAndConquerEngine {
private:
    size_t recursiveCalls = 0;

    vector<int> merge(
        const vector<int>& left,
        const vector<int>& right
    ) {
        vector<int> result;
        result.reserve(left.size() + right.size());

        size_t i = 0, j = 0;

        while (i < left.size() && j < right.size()) {
            if (left[i] <= right[j]) {
                result.push_back(left[i++]);
            } else {
                result.push_back(right[j++]);
            }
        }

        result.insert(result.end(), left.begin() + i, left.end());
        result.insert(result.end(), right.begin() + j, right.end());

        return result;
    }

    vector<int> mergeSortInternal(const vector<int>& values) {
        ++recursiveCalls;

        if (values.size() <= 1) {
            return values;
        }

        size_t middle = values.size() / 2;

        vector<int> left(
            values.begin(),
            values.begin() + middle
        );

        vector<int> right(
            values.begin() + middle,
            values.end()
        );

        return merge(
            mergeSortInternal(left),
            mergeSortInternal(right)
        );
    }

    void quickSortInternal(
        vector<int>& values,
        int low,
        int high
    ) {
        if (low >= high) return;

        ++recursiveCalls;

        int middle = low + (high - low) / 2;
        int pivot = values[middle];

        int i = low;
        int j = high;

        while (i <= j) {
            while (values[i] < pivot) ++i;
            while (values[j] > pivot) --j;

            if (i <= j) {
                swap(values[i], values[j]);
                ++i;
                --j;
            }
        }

        if (low < j) quickSortInternal(values, low, j);
        if (i < high) quickSortInternal(values, i, high);
    }

    tuple<long long, int, int> maximumSubarrayInternal(
        const vector<int>& values,
        int left,
        int right
    ) {
        ++recursiveCalls;

        if (left == right) {
            return {values[left], left, right};
        }

        int middle = left + (right - left) / 2;

        auto first = maximumSubarrayInternal(
            values, left, middle
        );

        auto second = maximumSubarrayInternal(
            values, middle + 1, right
        );

        long long leftSum = numeric_limits<long long>::lowest();
        long long current = 0;
        int start = middle;

        for (int i = middle; i >= left; --i) {
            current += values[i];

            if (current > leftSum) {
                leftSum = current;
                start = i;
            }
        }

        long long rightSum = numeric_limits<long long>::lowest();
        current = 0;
        int end = middle + 1;

        for (int i = middle + 1; i <= right; ++i) {
            current += values[i];

            if (current > rightSum) {
                rightSum = current;
                end = i;
            }
        }

        auto cross = make_tuple(
            leftSum + rightSum,
            start,
            end
        );

        return max({first, second, cross});
    }

    long long karatsubaInternal(
        long long x,
        long long y
    ) {
        ++recursiveCalls;

        if (x < 10 || y < 10) {
            return x * y;
        }

        int digits = max(
            static_cast<int>(to_string(x).size()),
            static_cast<int>(to_string(y).size())
        );

        int half = digits / 2;
        long long power = 1;

        for (int i = 0; i < half; ++i) {
            power *= 10;
        }

        long long highX = x / power;
        long long lowX = x % power;
        long long highY = y / power;
        long long lowY = y % power;

        long long z0 = karatsubaInternal(lowX, lowY);
        long long z2 = karatsubaInternal(highX, highY);
        long long z1 = karatsubaInternal(
            lowX + highX,
            lowY + highY
        );

        return z2 * power * power
             + (z1 - z2 - z0) * power
             + z0;
    }

public:
    size_t getRecursiveCalls() const {
        return recursiveCalls;
    }

    vector<int> mergeSort(const vector<int>& values) {
        recursiveCalls = 0;
        return mergeSortInternal(values);
    }

    vector<int> quickSort(vector<int> values) {
        recursiveCalls = 0;

        if (!values.empty()) {
            quickSortInternal(
                values,
                0,
                static_cast<int>(values.size()) - 1
            );
        }

        return values;
    }

    int binarySearch(
        const vector<int>& values,
        int target
    ) const {
        if (!is_sorted(values.begin(), values.end())) {
            throw invalid_argument(
                "Binary search requires sorted input."
            );
        }

        int left = 0;
        int right = static_cast<int>(values.size()) - 1;

        while (left <= right) {
            int middle = left + (right - left) / 2;

            if (values[middle] == target) return middle;

            if (values[middle] < target) {
                left = middle + 1;
            } else {
                right = middle - 1;
            }
        }

        return -1;
    }

    tuple<long long, int, int> maximumSubarray(
        const vector<int>& values
    ) {
        if (values.empty()) {
            throw invalid_argument(
                "Maximum subarray requires non-empty input."
            );
        }

        recursiveCalls = 0;

        return maximumSubarrayInternal(
            values,
            0,
            static_cast<int>(values.size()) - 1
        );
    }

    long long karatsuba(long long x, long long y) {
        if (x < 0 || y < 0) {
            throw invalid_argument(
                "Karatsuba inputs must be non-negative."
            );
        }

        recursiveCalls = 0;
        return karatsubaInternal(x, y);
    }
};

template <typename Function>
AlgorithmMetrics measure(
    const string& name,
    size_t size,
    size_t calls,
    Function operation
) {
    auto start = chrono::steady_clock::now();

    operation();

    auto finish = chrono::steady_clock::now();

    double elapsed = chrono::duration<double, milli>(
        finish - start
    ).count();

    return {
        name,
        size,
        calls,
        elapsed
    };
}

void demonstrateRecurrences() {
    vector<Recurrence> examples = {
        {"Binary Search", 1, 2, 0},
        {"Merge Sort", 2, 2, 1},
        {"Karatsuba", 3, 2, 1},
        {"Strassen", 7, 2, 2},
        {"Quadratic Combine", 2, 2, 2}
    };

    cout << "\nRECURRENCE RELATIONS\n";

    for (const auto& item : examples) {
        cout << left << setw(22)
             << item.name
             << item.complexity()
             << '\n';
    }
}

int main() {
    try {
        DivideAndConquerEngine engine;

        cout << "DIVIDE AND CONQUER ENGINE\n";
        cout << string(55, '=') << '\n';

        vector<int> input = {
            38, 27, 43, 3, 9, 82, 10, 27
        };

        cout << "\n1. MERGE SORT\n";

        vector<int> sorted = engine.mergeSort(input);

        for (int value : sorted) {
            cout << value << " ";
        }

        cout << "\nRecursive calls: "
             << engine.getRecursiveCalls() << '\n';

        if (!is_sorted(sorted.begin(), sorted.end())) {
            throw runtime_error("Merge sort validation failed.");
        }

        cout << "\n2. BINARY SEARCH\n";

        int position = engine.binarySearch(sorted, 27);
        cout << "Position: " << position << '\n';

        if (position == -1 || sorted[position] != 27) {
            throw runtime_error("Binary search failed.");
        }

        cout << "\n3. QUICK SORT\n";

        vector<int> quickInput = {
            9, 3, 7, 3, 1, 8, 2, 10
        };

        vector<int> quickResult = engine.quickSort(quickInput);

        for (int value : quickResult) {
            cout << value << " ";
        }

        cout << "\nRecursive calls: "
             << engine.getRecursiveCalls() << '\n';

        if (!is_sorted(
            quickResult.begin(),
            quickResult.end()
        )) {
            throw runtime_error("Quick sort validation failed.");
        }

        cout << "\n4. MAXIMUM SUBARRAY\n";

        vector<int> sequence = {
            -2, 1, -3, 4, -1, 2, 1, -5, 4
        };

        auto result = engine.maximumSubarray(sequence);

        cout << "Maximum sum: " << get<0>(result) << '\n';
        cout << "Start index: " << get<1>(result) << '\n';
        cout << "End index: " << get<2>(result) << '\n';

        if (get<0>(result) != 6) {
            throw runtime_error("Maximum subarray validation failed.");
        }

        cout << "\n5. KARATSUBA MULTIPLICATION\n";

        long long x = 123456789;
        long long y = 987654321;

        long long product = engine.karatsuba(x, y);

        cout << "Product: " << product << '\n';
        cout << "Recursive calls: "
             << engine.getRecursiveCalls() << '\n';

        if (product != x * y) {
            throw runtime_error("Karatsuba validation failed.");
        }

        demonstrateRecurrences();

        cout << "\n6. EDGE CASES\n";

        vector<int> empty;
        vector<int> emptySorted = engine.mergeSort(empty);

        if (!emptySorted.empty()) {
            throw runtime_error("Empty input test failed.");
        }

        vector<int> duplicates = {4, 4, 4, 4};
        auto duplicateResult = engine.mergeSort(duplicates);

        if (duplicateResult != duplicates) {
            throw runtime_error("Duplicate handling failed.");
        }

        try {
            engine.binarySearch({5, 2, 8}, 5);
        } catch (const invalid_argument& error) {
            cout << "Expected validation: "
                 << error.what() << '\n';
        }

        try {
            engine.maximumSubarray({});
        } catch (const invalid_argument& error) {
            cout << "Expected validation: "
                 << error.what() << '\n';
        }

        try {
            engine.karatsuba(-5, 10);
        } catch (const invalid_argument& error) {
            cout << "Expected validation: "
                 << error.what() << '\n';
        }

        cout << "\nAll C++17 tests passed.\n";

    } catch (const exception& error) {
        cerr << "Execution error: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
