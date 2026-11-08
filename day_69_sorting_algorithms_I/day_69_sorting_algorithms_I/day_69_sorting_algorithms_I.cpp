#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <iomanip>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;
using namespace std::chrono;

enum class Algorithm {
    Bubble,
    Selection,
    Insertion
};

struct Metrics {
    string algorithm;
    long long comparisons = 0;
    long long swaps = 0;
    long long shifts = 0;
    long long passes = 0;
    double durationMs = 0.0;
};

template <typename T>
struct SortResult {
    vector<T> values;
    Metrics metrics;
};

struct InventoryItem {
    string productId;
    string productName;
    int stock;
    double price;
};

class SortingEngine {
private:
    template <typename T>
    static void validate(const vector<T>& values) {
        if (values.size() > 1000000) {
            throw invalid_argument(
                "Input exceeds the maximum supported size."
            );
        }
    }

public:
    template <typename T, typename Compare = less<T>>
    static SortResult<T> bubbleSort(
        vector<T> values,
        Compare compare = Compare{}
    ) {
        validate(values);

        Metrics metrics;
        metrics.algorithm = "Bubble Sort";

        auto start = steady_clock::now();

        for (size_t i = 0; i + 1 < values.size(); ++i) {
            bool swapped = false;
            metrics.passes++;

            for (size_t j = 0; j + 1 < values.size() - i; ++j) {
                metrics.comparisons++;

                if (compare(values[j + 1], values[j])) {
                    swap(values[j], values[j + 1]);
                    metrics.swaps++;
                    swapped = true;
                }
            }

            if (!swapped) break;
        }

        auto end = steady_clock::now();

        metrics.durationMs =
            duration<double, milli>(end - start).count();

        return {move(values), metrics};
    }

    template <typename T, typename Compare = less<T>>
    static SortResult<T> selectionSort(
        vector<T> values,
        Compare compare = Compare{}
    ) {
        validate(values);

        Metrics metrics;
        metrics.algorithm = "Selection Sort";

        auto start = steady_clock::now();

        for (size_t i = 0; i + 1 < values.size(); ++i) {
            metrics.passes++;

            size_t selected = i;

            for (size_t j = i + 1; j < values.size(); ++j) {
                metrics.comparisons++;

                if (compare(values[j], values[selected])) {
                    selected = j;
                }
            }

            if (selected != i) {
                swap(values[i], values[selected]);
                metrics.swaps++;
            }
        }

        auto end = steady_clock::now();

        metrics.durationMs =
            duration<double, milli>(end - start).count();

        return {move(values), metrics};
    }

    template <typename T, typename Compare = less<T>>
    static SortResult<T> insertionSort(
        vector<T> values,
        Compare compare = Compare{}
    ) {
        validate(values);

        Metrics metrics;
        metrics.algorithm = "Insertion Sort";

        auto start = steady_clock::now();

        for (size_t i = 1; i < values.size(); ++i) {
            metrics.passes++;

            T current = values[i];
            size_t j = i;

            while (j > 0) {
                metrics.comparisons++;

                if (!compare(current, values[j - 1])) {
                    break;
                }

                values[j] = values[j - 1];
                metrics.shifts++;
                --j;
            }

            values[j] = move(current);
        }

        auto end = steady_clock::now();

        metrics.durationMs =
            duration<double, milli>(end - start).count();

        return {move(values), metrics};
    }
};

class InventoryService {
private:
    vector<InventoryItem> inventory;

public:
    explicit InventoryService(vector<InventoryItem> items)
        : inventory(move(items)) {

        if (inventory.size() > 100000) {
            throw invalid_argument("Inventory is too large.");
        }

        for (const auto& item : inventory) {
            if (
                item.productId.empty() ||
                item.productName.empty() ||
                item.stock < 0 ||
                !isfinite(item.price) ||
                item.price < 0
            ) {
                throw invalid_argument(
                    "Invalid inventory record."
                );
            }
        }

        for (size_t i = 0; i < inventory.size(); ++i) {
            for (size_t j = i + 1; j < inventory.size(); ++j) {
                if (
                    inventory[i].productId ==
                    inventory[j].productId
                ) {
                    throw invalid_argument(
                        "Duplicate product identifier."
                    );
                }
            }
        }
    }

    SortResult<InventoryItem> sortByStock() const {
        return SortingEngine::insertionSort(
            inventory,
            [](const InventoryItem& a,
               const InventoryItem& b) {
                return a.stock < b.stock;
            }
        );
    }

    SortResult<InventoryItem> sortByPrice() const {
        return SortingEngine::selectionSort(
            inventory,
            [](const InventoryItem& a,
               const InventoryItem& b) {
                return a.price < b.price;
            }
        );
    }
};

void printMetrics(const Metrics& metrics) {
    cout << left << setw(16) << metrics.algorithm
         << " Comparisons: " << setw(8) << metrics.comparisons
         << " Swaps: " << setw(8) << metrics.swaps
         << " Shifts: " << setw(8) << metrics.shifts
         << " Passes: " << setw(6) << metrics.passes
         << " Time: " << fixed << setprecision(4)
         << metrics.durationMs << " ms\n";
}

template <typename T>
void printVector(const vector<T>& values) {
    cout << "[ ";

    for (const auto& value : values) {
        cout << value << " ";
    }

    cout << "]\n";
}

void demonstrateBasicSorting() {
    cout << "\n=== BASIC SORTING ===\n";

    vector<int> values = {64, 34, 25, 12, 22, 11, 90};

    cout << "Original: ";
    printVector(values);

    auto bubble = SortingEngine::bubbleSort(values);
    auto selection = SortingEngine::selectionSort(values);
    auto insertion = SortingEngine::insertionSort(values);

    cout << "\nBubble Sort: ";
    printVector(bubble.values);
    printMetrics(bubble.metrics);

    cout << "\nSelection Sort: ";
    printVector(selection.values);
    printMetrics(selection.metrics);

    cout << "\nInsertion Sort: ";
    printVector(insertion.values);
    printMetrics(insertion.metrics);
}

void demonstrateDescending() {
    cout << "\n=== DESCENDING ORDER ===\n";

    vector<int> values = {4, 9, 2, 7, 1, 5};

    auto result = SortingEngine::insertionSort(
        values,
        greater<int>{}
    );

    printVector(result.values);
    printMetrics(result.metrics);
}

void demonstrateInventory() {
    cout << "\n=== INVENTORY PRIORITIZATION ===\n";

    vector<InventoryItem> items = {
        {"P101", "Keyboard", 45, 1200.0},
        {"P102", "Monitor", 12, 9500.0},
        {"P103", "Mouse", 80, 650.0},
        {"P104", "Laptop", 8, 55000.0},
        {"P105", "Headphones", 25, 1800.0}
    };

    InventoryService service(items);

    auto stockResult = service.sortByStock();

    cout << "\nProducts ordered by stock:\n";

    for (const auto& item : stockResult.values) {
        cout << item.productId << " | "
             << setw(12) << left << item.productName
             << " | Stock: " << setw(3) << item.stock
             << " | Price: " << item.price << '\n';
    }

    printMetrics(stockResult.metrics);

    auto priceResult = service.sortByPrice();

    cout << "\nProducts ordered by price:\n";

    for (const auto& item : priceResult.values) {
        cout << item.productName
             << " | " << item.price << '\n';
    }
}

void benchmark() {
    cout << "\n=== PERFORMANCE BENCHMARK ===\n";

    mt19937 generator(42);
    uniform_int_distribution<int> distribution(1, 10000);

    vector<int> sizes = {20, 100, 300};

    for (int size : sizes) {
        vector<int> values(size);

        for (int& value : values) {
            value = distribution(generator);
        }

        cout << "\nDataset size: " << size << '\n';

        auto bubble = SortingEngine::bubbleSort(values);
        auto selection = SortingEngine::selectionSort(values);
        auto insertion = SortingEngine::insertionSort(values);

        vector<int> expected = values;
        sort(expected.begin(), expected.end());

        if (
            bubble.values != expected ||
            selection.values != expected ||
            insertion.values != expected
        ) {
            throw runtime_error("Sorting verification failed.");
        }

        printMetrics(bubble.metrics);
        printMetrics(selection.metrics);
        printMetrics(insertion.metrics);
    }
}

void runTests() {
    cout << "\n=== VALIDATION TESTS ===\n";

    vector<vector<int>> cases = {
        {},
        {1},
        {5, 4, 3, 2, 1},
        {1, 2, 3, 4, 5},
        {3, 3, 3, 3},
        {-5, 0, 10, -20, 7}
    };

    for (const auto& values : cases) {
        vector<int> expected = values;
        sort(expected.begin(), expected.end());

        auto a = SortingEngine::bubbleSort(values);
        auto b = SortingEngine::selectionSort(values);
        auto c = SortingEngine::insertionSort(values);

        if (
            a.values != expected ||
            b.values != expected ||
            c.values != expected
        ) {
            throw runtime_error("Test case failed.");
        }
    }

    try {
        InventoryService invalid({
            {"P101", "Keyboard", -5, 100.0}
        });

        throw runtime_error("Invalid stock was accepted.");
    } catch (const invalid_argument&) {
        // Expected validation failure.
    }

    try {
        SortingEngine::bubbleSort(vector<int>(1000001, 1));

        throw runtime_error("Oversized input was accepted.");
    } catch (const invalid_argument&) {
        // Expected size validation failure.
    }

    cout << "All tests passed.\n";
}

int main() {
    try {
        cout << "====================================\n";
        cout << "SORTING ALGORITHMS I - C++17\n";
        cout << "====================================\n";

        demonstrateBasicSorting();
        demonstrateDescending();
        demonstrateInventory();
        benchmark();
        runTests();

        cout << "\nAll sorting operations completed.\n";

    } catch (const exception& error) {
        cerr << "Application error: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
