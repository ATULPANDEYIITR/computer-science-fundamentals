#include <algorithm>
#include <chrono>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>
#include <numeric>

using namespace std;

enum class ComplexityClass {
    Constant,
    Logarithmic,
    Linear,
    Linearithmic,
    Quadratic,
    Cubic,
    Exponential
};

string complexityName(ComplexityClass type) {
    switch (type) {
        case ComplexityClass::Constant: return "O(1)";
        case ComplexityClass::Logarithmic: return "O(log n)";
        case ComplexityClass::Linear: return "O(n)";
        case ComplexityClass::Linearithmic: return "O(n log n)";
        case ComplexityClass::Quadratic: return "O(n^2)";
        case ComplexityClass::Cubic: return "O(n^3)";
        case ComplexityClass::Exponential: return "O(2^n)";
    }

    throw logic_error("Unknown complexity class.");
}

struct ComplexityBounds {
    string name;
    string upper;
    string lower;
    string tight;
    string description;
};

struct Measurement {
    string algorithm;
    size_t inputSize;
    unsigned long long operations;
    double elapsedMicroseconds;
    ComplexityClass classification;
};

class ComplexityAnalyzer {
public:
    static void validateSize(size_t n, size_t maximum = 100000) {
        if (n > maximum) {
            throw invalid_argument("Input exceeds permitted workload.");
        }
    }

    static unsigned long long constant(size_t n) {
        validateSize(n);
        return 1;
    }

    static unsigned long long logarithmic(size_t n) {
        validateSize(n);

        unsigned long long count = 0;
        size_t value = 1;

        while (value < n) {
            if (value > numeric_limits<size_t>::max() / 2) {
                break;
            }

            value *= 2;
            ++count;
        }

        return count;
    }

    static unsigned long long linear(size_t n) {
        validateSize(n);
        return n;
    }

    static unsigned long long linearithmic(size_t n) {
        validateSize(n);

        if (n <= 1) return n;

        size_t levels = 0;
        size_t width = 1;

        while (width < n) {
            width *= 2;
            ++levels;
        }

        return static_cast<unsigned long long>(n) * levels;
    }

    static unsigned long long quadratic(size_t n) {
        validateSize(n);
        return static_cast<unsigned long long>(n) * n;
    }

    static unsigned long long triangular(size_t n) {
        validateSize(n);
        return static_cast<unsigned long long>(n) * (n + 1) / 2;
    }

    static unsigned long long cubic(size_t n) {
        validateSize(n, 10000);

        return static_cast<unsigned long long>(n) * n * n;
    }

    static unsigned long long exponential(size_t n) {
        validateSize(n, 25);

        unsigned long long calls = 0;

        function<unsigned long long(size_t)> fibonacciCalls =
            [&](size_t k) -> unsigned long long {
                ++calls;

                if (k <= 1) return 1;

                fibonacciCalls(k - 1);
                fibonacciCalls(k - 2);

                return calls;
            };

        fibonacciCalls(n);
        return calls;
    }

    static double logGrowth(size_t n) {
        return n == 0 ? 0.0 : log2(static_cast<double>(n));
    }

    static map<string, double> growthTable(size_t n) {
        validateSize(n);

        double value = static_cast<double>(n);
        double logarithm = logGrowth(n);

        return {
            {"1", 1.0},
            {"log2(n)", logarithm},
            {"n", value},
            {"n log2(n)", value * logarithm},
            {"n^2", value * value},
            {"n^3", value * value * value}
        };
    }

    static bool satisfiesUpperBound(
        double measured,
        double reference,
        double constant
    ) {
        if (
            !isfinite(measured) ||
            !isfinite(reference) ||
            !isfinite(constant) ||
            measured < 0 ||
            reference <= 0 ||
            constant <= 0
        ) {
            throw invalid_argument("Invalid asymptotic bound arguments.");
        }

        return measured <= constant * reference;
    }
};

class SearchEngine {
public:
    struct SearchResult {
        int index;
        unsigned long long comparisons;
        ComplexityClass complexity;
    };

    static SearchResult linearSearch(
        const vector<int>& values,
        int target
    ) {
        unsigned long long comparisons = 0;

        for (size_t i = 0; i < values.size(); ++i) {
            ++comparisons;

            if (values[i] == target) {
                return {
                    static_cast<int>(i),
                    comparisons,
                    ComplexityClass::Linear
                };
            }
        }

        return {-1, comparisons, ComplexityClass::Linear};
    }

    static SearchResult binarySearch(
        const vector<int>& values,
        int target
    ) {
        if (!is_sorted(values.begin(), values.end())) {
            throw invalid_argument("Binary search requires sorted input.");
        }

        size_t left = 0;
        size_t right = values.size();
        unsigned long long comparisons = 0;

        while (left < right) {
            size_t middle = left + (right - left) / 2;
            ++comparisons;

            if (values[middle] == target) {
                return {
                    static_cast<int>(middle),
                    comparisons,
                    ComplexityClass::Logarithmic
                };
            }

            if (values[middle] < target) {
                left = middle + 1;
            } else {
                right = middle;
            }
        }

        return {-1, comparisons, ComplexityClass::Logarithmic};
    }
};

class SortingEngine {
public:
    struct SortResult {
        vector<int> sorted;
        unsigned long long comparisons;
        unsigned long long moves;
    };

    static SortResult mergeSort(const vector<int>& values) {
        unsigned long long comparisons = 0;
        unsigned long long moves = 0;

        function<vector<int>(const vector<int>&)> sort =
            [&](const vector<int>& input) -> vector<int> {
                if (input.size() <= 1) return input;

                size_t middle = input.size() / 2;

                vector<int> left(
                    input.begin(),
                    input.begin() + middle
                );

                vector<int> right(
                    input.begin() + middle,
                    input.end()
                );

                left = sort(left);
                right = sort(right);

                vector<int> result;
                result.reserve(input.size());

                size_t i = 0;
                size_t j = 0;

                while (i < left.size() && j < right.size()) {
                    ++comparisons;

                    if (left[i] <= right[j]) {
                        result.push_back(left[i++]);
                    } else {
                        result.push_back(right[j++]);
                    }

                    ++moves;
                }

                while (i < left.size()) {
                    result.push_back(left[i++]);
                    ++moves;
                }

                while (j < right.size()) {
                    result.push_back(right[j++]);
                    ++moves;
                }

                return result;
            };

        return {sort(values), comparisons, moves};
    }

    static SortResult insertionSort(const vector<int>& values) {
        vector<int> result = values;
        unsigned long long comparisons = 0;
        unsigned long long moves = 0;

        for (size_t i = 1; i < result.size(); ++i) {
            int key = result[i];
            size_t j = i;

            while (j > 0) {
                ++comparisons;

                if (result[j - 1] <= key) break;

                result[j] = result[j - 1];
                --j;
                ++moves;
            }

            result[j] = key;
            ++moves;
        }

        return {result, comparisons, moves};
    }
};

class PerformanceMonitor {
private:
    vector<Measurement> measurements;

public:
    template <typename Function>
    Measurement measure(
        const string& name,
        size_t inputSize,
        Function operation,
        ComplexityClass classification
    ) {
        auto start = chrono::high_resolution_clock::now();

        unsigned long long operations = operation(inputSize);

        auto end = chrono::high_resolution_clock::now();

        double elapsed =
            chrono::duration<double, micro>(end - start).count();

        Measurement result {
            name,
            inputSize,
            operations,
            elapsed,
            classification
        };

        measurements.push_back(result);
        return result;
    }

    const vector<Measurement>& getMeasurements() const {
        return measurements;
    }
};

void printMeasurements(const PerformanceMonitor& monitor) {
    cout << "\nOPERATION COUNT BENCHMARK\n";
    cout << string(85, '-') << '\n';

    cout << left
         << setw(18) << "Algorithm"
         << setw(12) << "Input"
         << setw(18) << "Operations"
         << setw(18) << "Time (us)"
         << "Complexity\n";

    for (const auto& item : monitor.getMeasurements()) {
        cout << left
             << setw(18) << item.algorithm
             << setw(12) << item.inputSize
             << setw(18) << item.operations
             << setw(18) << fixed << setprecision(3)
             << item.elapsedMicroseconds
             << complexityName(item.classification)
             << '\n';
    }
}

void demonstrateBounds() {
    vector<ComplexityBounds> bounds = {
        {"Constant", "O(1)", "Omega(1)", "Theta(1)", "Fixed work."},
        {"Logarithmic", "O(log n)", "Omega(log n)", "Theta(log n)", "Repeated halving."},
        {"Linear", "O(n)", "Omega(n)", "Theta(n)", "One complete traversal."},
        {"Linearithmic", "O(n log n)", "Omega(n log n)", "Theta(n log n)", "Efficient sorting."},
        {"Quadratic", "O(n^2)", "Omega(n^2)", "Theta(n^2)", "Two nested loops."},
        {"Cubic", "O(n^3)", "Omega(n^3)", "Theta(n^3)", "Three nested loops."},
        {"Exponential", "O(2^n)", "Omega(2^n)", "Theta(2^n)", "Exponential branching."}
    };

    cout << "\nASYMPTOTIC BOUNDS\n";

    for (const auto& bound : bounds) {
        cout << left
             << setw(15) << bound.name
             << setw(18) << bound.upper
             << setw(20) << bound.lower
             << setw(18) << bound.tight
             << bound.description << '\n';
    }
}

void demonstrateGrowth() {
    cout << "\nGROWTH FUNCTIONS\n";

    for (size_t n : {10, 100, 1000}) {
        cout << "\nn = " << n << '\n';

        for (const auto& [name, value] :
             ComplexityAnalyzer::growthTable(n)) {
            cout << setw(15) << name << value << '\n';
        }
    }
}

void demonstrateAlgorithms() {
    vector<int> data(1000);
    iota(data.begin(), data.end(), 0);

    auto linear = SearchEngine::linearSearch(data, 750);
    auto binary = SearchEngine::binarySearch(data, 750);

    cout << "\nSEARCH ALGORITHMS\n";

    cout << "Linear search: index=" << linear.index
         << ", comparisons=" << linear.comparisons << '\n';

    cout << "Binary search: index=" << binary.index
         << ", comparisons=" << binary.comparisons << '\n';

    vector<int> input = {45, 12, 89, 3, 22, 67, 1, 9, 9};

    auto merge = SortingEngine::mergeSort(input);
    auto insertion = SortingEngine::insertionSort(input);

    cout << "\nSORTING ALGORITHMS\n";

    cout << "Merge sort comparisons: "
         << merge.comparisons << '\n';

    cout << "Insertion sort comparisons: "
         << insertion.comparisons << '\n';

    if (!is_sorted(merge.sorted.begin(), merge.sorted.end()) ||
        !is_sorted(insertion.sorted.begin(), insertion.sorted.end())) {
        throw runtime_error("Sorting validation failed.");
    }

    cout << "Sorted values: ";

    for (int value : merge.sorted) {
        cout << value << ' ';
    }

    cout << '\n';
}

void demonstrateBenchmarking() {
    PerformanceMonitor monitor;

    vector<size_t> sizes = {10, 100, 500};

    for (size_t n : sizes) {
        monitor.measure(
            "Constant", n,
            ComplexityAnalyzer::constant,
            ComplexityClass::Constant
        );

        monitor.measure(
            "Logarithmic", n,
            ComplexityAnalyzer::logarithmic,
            ComplexityClass::Logarithmic
        );

        monitor.measure(
            "Linear", n,
            ComplexityAnalyzer::linear,
            ComplexityClass::Linear
        );

        monitor.measure(
            "Linearithmic", n,
            ComplexityAnalyzer::linearithmic,
            ComplexityClass::Linearithmic
        );

        monitor.measure(
            "Quadratic", n,
            ComplexityAnalyzer::quadratic,
            ComplexityClass::Quadratic
        );

        monitor.measure(
            "Triangular", n,
            ComplexityAnalyzer::triangular,
            ComplexityClass::Quadratic
        );
    }

    printMeasurements(monitor);
}

void demonstrateValidation() {
    cout << "\nVALIDATION\n";

    if (ComplexityAnalyzer::linear(0) != 0) {
        throw runtime_error("Empty input test failed.");
    }

    if (ComplexityAnalyzer::logarithmic(1) != 0) {
        throw runtime_error("Logarithmic boundary test failed.");
    }

    if (ComplexityAnalyzer::triangular(5) != 15) {
        throw runtime_error("Triangular count test failed.");
    }

    if (!ComplexityAnalyzer::satisfiesUpperBound(10, 10, 1)) {
        throw runtime_error("Upper bound validation failed.");
    }

    try {
        ComplexityAnalyzer::quadratic(100001);
    } catch (const invalid_argument& error) {
        cout << "Expected error: " << error.what() << '\n';
    }

    try {
        SearchEngine::binarySearch({9, 2, 5}, 2);
    } catch (const invalid_argument& error) {
        cout << "Expected error: " << error.what() << '\n';
    }

    cout << "All validation tests passed.\n";
}

int main() {
    try {
        cout << "TIME COMPLEXITY AND ASYMPTOTIC ANALYSIS\n";
        cout << string(85, '=') << '\n';

        demonstrateBounds();
        demonstrateGrowth();
        demonstrateAlgorithms();
        demonstrateBenchmarking();
        demonstrateValidation();

        cout << "\nEXECUTION COMPLETED\n";
    } catch (const exception& error) {
        cerr << "Execution failure: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
