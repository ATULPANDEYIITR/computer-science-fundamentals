#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <exception>
#include <functional>
#include <iomanip>
#include <iostream>
#include <limits>
#include <random>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

using namespace std;

enum class Algorithm {
    Merge,
    Quick,
    Heap
};

struct SortMetrics {
    string algorithm;
    uint64_t comparisons = 0;
    uint64_t swaps = 0;
    uint64_t writes = 0;
    uint64_t partitions = 0;
    double elapsedMilliseconds = 0.0;
};

template <typename T>
struct SortResult {
    vector<T> values;
    SortMetrics metrics;
};

template <typename T>
using Comparator = function<bool(const T&, const T&)>;

template <typename T>
Comparator<T> defaultComparator() {
    return [](const T& a, const T& b) {
        return a < b;
    };
}

template <typename T>
class SortingEngine {
private:
    Comparator<T> comparator;

    bool lessThan(
        const T& a,
        const T& b,
        SortMetrics& metrics
    ) const {
        metrics.comparisons++;
        return comparator(a, b);
    }

    static void exchange(
        vector<T>& data,
        size_t i,
        size_t j,
        SortMetrics& metrics
    ) {
        if (i == j) return;

        swap(data[i], data[j]);
        metrics.swaps++;
        metrics.writes += 2;
    }

    T medianOfThree(
        const T& a,
        const T& b,
        const T& c,
        SortMetrics& metrics
    ) const {
        if (lessThan(b, a, metrics)) {
            return lessThan(c, b, metrics)
                ? b
                : (lessThan(c, a, metrics) ? c : a);
        }

        if (lessThan(c, b, metrics)) {
            return lessThan(c, a, metrics) ? a : c;
        }

        return b;
    }

public:
    explicit SortingEngine(
        Comparator<T> compare = defaultComparator<T>()
    ) : comparator(move(compare)) {
        if (!comparator) {
            throw invalid_argument("Comparator cannot be empty");
        }
    }

    SortResult<T> mergeSort(const vector<T>& input) const {
        SortResult<T> result;
        result.values = input;
        result.metrics.algorithm = "merge_sort";

        auto start = chrono::steady_clock::now();

        const size_t n = result.values.size();

        if (n < 2) {
            result.metrics.elapsedMilliseconds = 0;
            return result;
        }

        vector<T> buffer(n);

        function<void(size_t, size_t)> merge =
            [&](size_t left, size_t right) {
                if (right - left <= 1) return;

                size_t middle = left + (right - left) / 2;

                merge(left, middle);
                merge(middle, right);

                size_t i = left;
                size_t j = middle;
                size_t k = left;

                while (i < middle && j < right) {
                    // Left-first selection preserves stability.
                    if (!lessThan(
                        result.values[j],
                        result.values[i],
                        result.metrics
                    )) {
                        buffer[k++] = result.values[i++];
                    } else {
                        buffer[k++] = result.values[j++];
                    }

                    result.metrics.writes++;
                }

                while (i < middle) {
                    buffer[k++] = result.values[i++];
                    result.metrics.writes++;
                }

                while (j < right) {
                    buffer[k++] = result.values[j++];
                    result.metrics.writes++;
                }

                for (size_t p = left; p < right; ++p) {
                    result.values[p] = buffer[p];
                    result.metrics.writes++;
                }
            };

        merge(0, n);

        auto end = chrono::steady_clock::now();

        result.metrics.elapsedMilliseconds =
            chrono::duration<double, milli>(end - start).count();

        return result;
    }

    SortResult<T> quickSort(const vector<T>& input) const {
        SortResult<T> result;
        result.values = input;
        result.metrics.algorithm = "quick_sort";

        auto start = chrono::steady_clock::now();

        auto& data = result.values;

        if (data.size() > 1) {
            struct Range {
                size_t low;
                size_t high;
            };

            vector<Range> stack;
            stack.push_back({0, data.size() - 1});

            while (!stack.empty()) {
                Range range = stack.back();
                stack.pop_back();

                size_t low = range.low;
                size_t high = range.high;

                if (low >= high) continue;

                T pivot = medianOfThree(
                    data[low],
                    data[low + (high - low) / 2],
                    data[high],
                    result.metrics
                );

                size_t less = low;
                size_t current = low;
                size_t greater = high;

                result.metrics.partitions++;

                // Three-way partition separates less, equal and greater.
                while (current <= greater) {
                    if (lessThan(
                        data[current],
                        pivot,
                        result.metrics
                    )) {
                        exchange(
                            data, less++, current++,
                            result.metrics
                        );
                    } else if (lessThan(
                        pivot,
                        data[current],
                        result.metrics
                    )) {
                        exchange(
                            data, current, greater,
                            result.metrics
                        );

                        if (greater == 0) break;
                        --greater;
                    } else {
                        ++current;
                    }
                }

                size_t leftSize = less - low;
                size_t rightSize = high - greater;

                if (leftSize < rightSize) {
                    if (greater < high) {
                        stack.push_back({greater + 1, high});
                    }

                    if (low < less && less - low > 1) {
                        stack.push_back({low, less - 1});
                    }
                } else {
                    if (low < less && less - low > 1) {
                        stack.push_back({low, less - 1});
                    }

                    if (greater < high) {
                        stack.push_back({greater + 1, high});
                    }
                }
            }
        }

        auto end = chrono::steady_clock::now();

        result.metrics.elapsedMilliseconds =
            chrono::duration<double, milli>(end - start).count();

        return result;
    }

    SortResult<T> heapSort(const vector<T>& input) const {
        SortResult<T> result;
        result.values = input;
        result.metrics.algorithm = "heap_sort";

        auto start = chrono::steady_clock::now();

        auto& data = result.values;
        const size_t n = data.size();

        auto siftDown = [&](size_t root, size_t end) {
            while (root < end) {
                size_t child = 2 * root + 1;

                if (child >= end) return;

                if (
                    child + 1 < end &&
                    lessThan(
                        data[child],
                        data[child + 1],
                        result.metrics
                    )
                ) {
                    ++child;
                }

                if (!lessThan(
                    data[root],
                    data[child],
                    result.metrics
                )) {
                    return;
                }

                exchange(data, root, child, result.metrics);
                root = child;
            }
        };

        // Bottom-up max heap construction.
        for (size_t i = n / 2; i > 0; --i) {
            siftDown(i - 1, n);
        }

        // Repeated maximum extraction.
        for (size_t end = n; end > 1; --end) {
            exchange(data, 0, end - 1, result.metrics);
            siftDown(0, end - 1);
        }

        auto finish = chrono::steady_clock::now();

        result.metrics.elapsedMilliseconds =
            chrono::duration<double, milli>(
                finish - start
            ).count();

        return result;
    }

    SortResult<T> sort(
        const vector<T>& input,
        Algorithm algorithm
    ) const {
        switch (algorithm) {
            case Algorithm::Merge:
                return mergeSort(input);

            case Algorithm::Quick:
                return quickSort(input);

            case Algorithm::Heap:
                return heapSort(input);
        }

        throw invalid_argument("Unknown sorting algorithm");
    }
};

template <typename T>
void verifyResult(
    const vector<T>& original,
    const vector<T>& sorted,
    Comparator<T> comparator = defaultComparator<T>()
) {
    if (original.size() != sorted.size()) {
        throw runtime_error("Element count mismatch");
    }

    vector<T> expected = original;
    vector<T> actual = sorted;

    sort(expected.begin(), expected.end(), comparator);
    sort(actual.begin(), actual.end(), comparator);

    if (expected != actual) {
        throw runtime_error("Element preservation failed");
    }

    for (size_t i = 1; i < sorted.size(); ++i) {
        if (comparator(sorted[i], sorted[i - 1])) {
            throw runtime_error("Sorted order validation failed");
        }
    }
}

struct Employee {
    int id;
    string department;
    double salary;

    bool operator==(const Employee& other) const {
        return id == other.id &&
               department == other.department &&
               salary == other.salary;
    }
};

void runTests() {
    SortingEngine<int> engine;

    vector<vector<int>> testCases = {
        {},
        {1},
        {2, 1},
        {5, 3, 8, 1, 2},
        {4, 4, 4, 4},
        {-10, 0, 10, -5},
        {100, 90, 80, 70, 60},
        vector<int>(1000, 7)
    };

    mt19937 generator(42);
    uniform_int_distribution<int> distribution(-10000, 10000);

    vector<int> randomData(1000);

    for (int& value : randomData) {
        value = distribution(generator);
    }

    testCases.push_back(randomData);

    array<Algorithm, 3> algorithms = {
        Algorithm::Merge,
        Algorithm::Quick,
        Algorithm::Heap
    };

    for (const auto& values : testCases) {
        for (Algorithm algorithm : algorithms) {
            auto result = engine.sort(values, algorithm);

            vector<int> expected = values;
            sort(expected.begin(), expected.end());

            if (result.values != expected) {
                throw runtime_error("Sorting test failed");
            }

            verifyResult(values, result.values);
        }
    }

    // Verify stable ordering using an employee salary comparator.
    vector<Employee> employees = {
        {1, "Engineering", 80000},
        {2, "Research", 70000},
        {3, "Security", 80000},
        {4, "Operations", 70000}
    };

    SortingEngine<Employee> employeeEngine(
        [](const Employee& a, const Employee& b) {
            return a.salary < b.salary;
        }
    );

    auto stable = employeeEngine.mergeSort(employees);

    if (
        stable.values[0].id != 2 ||
        stable.values[1].id != 4 ||
        stable.values[2].id != 1 ||
        stable.values[3].id != 3
    ) {
        throw runtime_error("Merge sort stability test failed");
    }

    cout << "All C++17 sorting tests passed.\n";
}

void runBenchmark(size_t size) {
    if (size > 1000000) {
        throw invalid_argument("Benchmark size exceeds safety limit");
    }

    mt19937 generator(42);
    uniform_int_distribution<int> distribution(-100000, 100000);

    vector<int> randomData(size);

    for (int& value : randomData) {
        value = distribution(generator);
    }

    vector<int> sortedData(size);
    iota(sortedData.begin(), sortedData.end(), 0);

    vector<int> reverseData = sortedData;
    reverse(reverseData.begin(), reverseData.end());

    vector<int> duplicateData(size, 5);

    SortingEngine<int> engine;

    struct Dataset {
        string name;
        const vector<int>* values;
    };

    vector<Dataset> datasets = {
        {"random", &randomData},
        {"sorted", &sortedData},
        {"reverse", &reverseData},
        {"duplicates", &duplicateData}
    };

    array<Algorithm, 3> algorithms = {
        Algorithm::Merge,
        Algorithm::Quick,
        Algorithm::Heap
    };

    cout << "\nBenchmark results\n";

    cout << left
         << setw(16) << "Dataset"
         << setw(16) << "Algorithm"
         << setw(14) << "Comparisons"
         << setw(12) << "Swaps"
         << setw(14) << "Time(ms)"
         << '\n';

    for (const auto& dataset : datasets) {
        for (Algorithm algorithm : algorithms) {
            auto result = engine.sort(
                *dataset.values,
                algorithm
            );

            verifyResult(*dataset.values, result.values);

            const auto& metrics = result.metrics;

            cout << left
                 << setw(16) << dataset.name
                 << setw(16) << metrics.algorithm
                 << setw(14) << metrics.comparisons
                 << setw(12) << metrics.swaps
                 << fixed << setprecision(4)
                 << metrics.elapsedMilliseconds
                 << '\n';
        }
    }
}

int main() {
    try {
        runTests();

        vector<int> sample = {
            38, 27, 43, 3, 9, 82, 10, 3
        };

        SortingEngine<int> engine;

        cout << "\nSample sorting\n";

        for (Algorithm algorithm : {
            Algorithm::Merge,
            Algorithm::Quick,
            Algorithm::Heap
        }) {
            auto result = engine.sort(sample, algorithm);

            cout << result.metrics.algorithm << ": ";

            for (int value : result.values) {
                cout << value << ' ';
            }

            cout << "\nComparisons: "
                 << result.metrics.comparisons
                 << ", Swaps: "
                 << result.metrics.swaps
                 << ", Time: "
                 << fixed << setprecision(4)
                 << result.metrics.elapsedMilliseconds
                 << " ms\n\n";
        }

        runBenchmark(10000);

        return 0;
    } catch (const exception& error) {
        cerr << "Execution error: "
             << error.what() << '\n';

        return 1;
    }
}
