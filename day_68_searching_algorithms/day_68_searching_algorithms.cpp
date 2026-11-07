#include <algorithm>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <limits>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

enum class SearchType {
    Linear,
    Binary,
    Interpolation
};

struct SearchResult {
    SearchType algorithm;
    int target;
    int index;
    uint64_t comparisons;
    double elapsedMicroseconds;

    bool found() const {
        return index >= 0;
    }
};

class SensorRegistry {
private:
    vector<int> sensorIds;

    static void validateSorted(const vector<int>& data) {
        if (!is_sorted(data.begin(), data.end())) {
            throw invalid_argument(
                "Binary and interpolation searches require sorted data."
            );
        }
    }

    static string algorithmName(SearchType type) {
        switch (type) {
            case SearchType::Linear:
                return "Linear Search";
            case SearchType::Binary:
                return "Binary Search";
            case SearchType::Interpolation:
                return "Interpolation Search";
        }

        throw invalid_argument("Unknown search algorithm.");
    }

public:
    explicit SensorRegistry(vector<int> ids)
        : sensorIds(move(ids)) {
        sort(sensorIds.begin(), sensorIds.end());
    }

    SearchResult search(SearchType type, int target) const {
        uint64_t comparisons = 0;
        int result = -1;

        const auto start = chrono::steady_clock::now();

        switch (type) {
            case SearchType::Linear: {
                for (size_t i = 0; i < sensorIds.size(); ++i) {
                    ++comparisons;

                    if (sensorIds[i] == target) {
                        result = static_cast<int>(i);
                        break;
                    }
                }
                break;
            }

            case SearchType::Binary: {
                validateSorted(sensorIds);

                int left = 0;
                int right = static_cast<int>(sensorIds.size()) - 1;

                while (left <= right) {
                    const int middle = left + (right - left) / 2;
                    ++comparisons;

                    if (sensorIds[middle] == target) {
                        result = middle;
                        right = middle - 1;
                    } else if (sensorIds[middle] < target) {
                        left = middle + 1;
                    } else {
                        right = middle - 1;
                    }
                }
                break;
            }

            case SearchType::Interpolation: {
                validateSorted(sensorIds);

                int low = 0;
                int high = static_cast<int>(sensorIds.size()) - 1;

                while (low <= high) {
                    ++comparisons;

                    if (target < sensorIds[low] ||
                        target > sensorIds[high]) {
                        break;
                    }

                    if (sensorIds[low] == sensorIds[high]) {
                        if (sensorIds[low] == target) {
                            result = low;
                        }
                        break;
                    }

                    // Widen arithmetic to prevent multiplication overflow.
                    const int64_t numerator =
                        (static_cast<int64_t>(target) - sensorIds[low]) *
                        (high - low);

                    const int64_t denominator =
                        static_cast<int64_t>(sensorIds[high]) -
                        sensorIds[low];

                    int64_t estimated = low + numerator / denominator;

                    estimated = max(
                        static_cast<int64_t>(low),
                        min(estimated, static_cast<int64_t>(high))
                    );

                    const int position = static_cast<int>(estimated);
                    ++comparisons;

                    if (sensorIds[position] == target) {
                        result = position;
                        high = position - 1;
                    } else if (sensorIds[position] < target) {
                        low = position + 1;
                    } else {
                        high = position - 1;
                    }
                }
                break;
            }
        }

        const auto end = chrono::steady_clock::now();

        const double elapsed =
            chrono::duration<double, micro>(end - start).count();

        return {
            type,
            target,
            result,
            comparisons,
            elapsed
        };
    }

    void registerSensor(int id) {
        auto position = lower_bound(
            sensorIds.begin(),
            sensorIds.end(),
            id
        );

        sensorIds.insert(position, id);
    }

    bool unregisterSensor(int id) {
        auto position = lower_bound(
            sensorIds.begin(),
            sensorIds.end(),
            id
        );

        if (position == sensorIds.end() || *position != id) {
            return false;
        }

        sensorIds.erase(position);
        return true;
    }

    const vector<int>& getSensorIds() const {
        return sensorIds;
    }

    static string name(SearchType type) {
        return algorithmName(type);
    }
};

void printResult(const SearchResult& result) {
    cout << SensorRegistry::name(result.algorithm) << "\n";

    if (result.found()) {
        cout << "  Sensor found at index: " << result.index << "\n";
    } else {
        cout << "  Sensor not found\n";
    }

    cout << "  Comparisons: " << result.comparisons << "\n";
    cout << "  Execution time: "
         << result.elapsedMicroseconds << " microseconds\n\n";
}

void runTests() {
    vector<int> data = {10, 20, 30, 40, 50, 60};

    SensorRegistry registry(data);

    if (registry.search(SearchType::Linear, 40).index != 3)
        throw runtime_error("Linear search test failed.");

    if (registry.search(SearchType::Binary, 40).index != 3)
        throw runtime_error("Binary search test failed.");

    if (registry.search(SearchType::Interpolation, 40).index != 3)
        throw runtime_error("Interpolation search test failed.");

    SensorRegistry duplicates({5, 5, 5, 10, 10, 20});

    if (duplicates.search(SearchType::Binary, 10).index != 3)
        throw runtime_error("Binary duplicate test failed.");

    if (duplicates.search(SearchType::Interpolation, 10).index != 3)
        throw runtime_error("Interpolation duplicate test failed.");

    if (registry.search(SearchType::Binary, 999).found())
        throw runtime_error("Missing-value test failed.");

    SensorRegistry empty({});

    if (empty.search(SearchType::Interpolation, 10).found())
        throw runtime_error("Empty collection test failed.");

    SensorRegistry identical({7, 7, 7});

    if (identical.search(SearchType::Interpolation, 7).index != 0)
        throw runtime_error("Identical-value test failed.");

    if (!registry.unregisterSensor(30))
        throw runtime_error("Deletion test failed.");

    registry.registerSensor(35);

    if (!binary_search(
            registry.getSensorIds().begin(),
            registry.getSensorIds().end(),
            35)) {
        throw runtime_error("Insertion test failed.");
    }

    cout << "All C++17 tests passed.\n";
}

int main() {
    try {
        cout << "SEARCHING ALGORITHMS\n";
        cout << "====================\n\n";

        SensorRegistry registry({
            1020, 1005, 1040, 1010, 1030, 1050, 1060
        });

        const int target = 1030;

        cout << "Sorted sensor identifiers: ";

        for (int id : registry.getSensorIds()) {
            cout << id << " ";
        }

        cout << "\nTarget sensor: " << target << "\n\n";

        printResult(registry.search(SearchType::Linear, target));
        printResult(registry.search(SearchType::Binary, target));
        printResult(registry.search(SearchType::Interpolation, target));

        cout << "Missing sensor:\n";
        printResult(registry.search(SearchType::Binary, 9999));

        cout << "Inventory management:\n";

        registry.registerSensor(1070);
        registry.unregisterSensor(1005);

        cout << "Updated sensor IDs: ";

        for (int id : registry.getSensorIds()) {
            cout << id << " ";
        }

        cout << "\n\n";

        runTests();

    } catch (const exception& error) {
        cerr << "Error: " << error.what() << "\n";
        return 1;
    }

    return 0;
}
