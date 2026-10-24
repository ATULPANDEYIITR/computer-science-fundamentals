#include <algorithm>
#include <cassert>
#include <cstddef>
#include <exception>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

enum class Operation {
    Access,
    Search,
    Insert,
    Delete,
    Update
};

struct OperationStats {
    std::size_t accesses = 0;
    std::size_t searches = 0;
    std::size_t insertions = 0;
    std::size_t deletions = 0;
    std::size_t updates = 0;

    void record(Operation operation) {
        switch (operation) {
            case Operation::Access: ++accesses; break;
            case Operation::Search: ++searches; break;
            case Operation::Insert: ++insertions; break;
            case Operation::Delete: ++deletions; break;
            case Operation::Update: ++updates; break;
        }
    }
};

class ArrayError : public std::runtime_error {
public:
    explicit ArrayError(const std::string& message)
        : std::runtime_error(message) {}
};

class RepositoryArray {
private:
    std::vector<int> values_;
    std::size_t capacity_;
    OperationStats stats_;

    void validateIndex(std::size_t index, bool allowEnd) const {
        const std::size_t upper =
            allowEnd ? values_.size() : (values_.empty() ? 0 : values_.size() - 1);

        if (values_.empty() || index > upper || (!allowEnd && index >= values_.size())) {
            throw ArrayError("Array index is outside the valid range.");
        }
    }

    void growIfRequired() {
        if (values_.size() >= capacity_) {
            capacity_ *= 2;
            values_.reserve(capacity_);
        }
    }

public:
    explicit RepositoryArray(std::size_t capacity = 4)
        : capacity_(capacity) {
        if (capacity == 0) {
            throw std::invalid_argument("Capacity must be positive.");
        }
        values_.reserve(capacity_);
    }

    std::size_t size() const {
        return values_.size();
    }

    std::size_t capacity() const {
        return capacity_;
    }

    const OperationStats& stats() const {
        return stats_;
    }

    int access(std::size_t index) {
        validateIndex(index, false);
        stats_.record(Operation::Access);
        return values_[index];
    }

    void update(std::size_t index, int value) {
        validateIndex(index, false);
        values_[index] = value;
        stats_.record(Operation::Update);
    }

    void insert(std::size_t index, int value) {
        if (index > values_.size()) {
            throw ArrayError("Insertion index is outside the valid range.");
        }

        growIfRequired();

        /*
         * vector::insert shifts the suffix while preserving contiguous storage.
         * This is the central cost of arbitrary-position insertion.
         */
        values_.insert(values_.begin() + static_cast<std::ptrdiff_t>(index), value);
        stats_.record(Operation::Insert);
    }

    void append(int value) {
        insert(values_.size(), value);
    }

    int erase(std::size_t index) {
        validateIndex(index, false);
        const int removed = values_[index];
        values_.erase(values_.begin() + static_cast<std::ptrdiff_t>(index));
        stats_.record(Operation::Delete);
        return removed;
    }

    int linearSearch(int value) {
        stats_.record(Operation::Search);

        for (std::size_t index = 0; index < values_.size(); ++index) {
            if (values_[index] == value) {
                return static_cast<int>(index);
            }
        }

        return -1;
    }

    int binarySearch(int value) {
        if (!std::is_sorted(values_.begin(), values_.end())) {
            throw ArrayError("Binary search requires sorted data.");
        }

        stats_.record(Operation::Search);

        std::size_t left = 0;
        std::size_t right = values_.size();

        while (left < right) {
            const std::size_t middle = left + (right - left) / 2;

            if (values_[middle] == value) {
                return static_cast<int>(middle);
            }

            if (values_[middle] < value) {
                left = middle + 1;
            } else {
                right = middle;
            }
        }

        return -1;
    }

    void reverse() {
        std::reverse(values_.begin(), values_.end());
    }

    void print() const {
        std::cout << '[';
        for (std::size_t i = 0; i < values_.size(); ++i) {
            if (i != 0) {
                std::cout << ", ";
            }
            std::cout << values_[i];
        }
        std::cout << "]\n";
    }
};

void runTests() {
    RepositoryArray array(2);

    array.append(10);
    array.append(20);
    array.append(30);
    array.append(40);

    assert(array.size() == 4);
    assert(array.capacity() >= 4);
    assert(array.access(2) == 30);

    array.update(1, 25);
    assert(array.linearSearch(25) == 1);

    array.insert(2, 27);
    assert(array.access(2) == 27);

    assert(array.erase(1) == 25);
    array.reverse();
    assert(array.access(0) == 40);

    RepositoryArray sorted(4);
    for (int value : {10, 20, 30, 40, 50}) {
        sorted.append(value);
    }

    assert(sorted.binarySearch(40) == 3);
    assert(sorted.binarySearch(999) == -1);
}

void demonstrateFailures() {
    RepositoryArray array;
    array.append(10);

    try {
        array.access(5);
    } catch (const ArrayError& error) {
        std::cout << "Invalid access rejected: "
                  << error.what() << '\n';
    }

    try {
        RepositoryArray unsorted;
        unsorted.append(30);
        unsorted.append(10);
        unsorted.binarySearch(10);
    } catch (const ArrayError& error) {
        std::cout << "Invalid binary search rejected: "
                  << error.what() << '\n';
    }

    try {
        array.insert(3, 99);
    } catch (const ArrayError& error) {
        std::cout << "Invalid insertion rejected: "
                  << error.what() << '\n';
    }
}

int main() {
    try {
        runTests();

        RepositoryArray repositoryData(2);
        for (int value : {101, 203, 305, 407, 509}) {
            repositoryData.append(value);
        }

        repositoryData.update(2, 306);
        repositoryData.insert(1, 150);

        std::cout << "Repository array: ";
        repositoryData.print();

        std::cout << "Search for 306: "
                  << repositoryData.linearSearch(306) << '\n';

        std::cout << "Removed value: "
                  << repositoryData.erase(1) << '\n';

        std::cout << "After deletion: ";
        repositoryData.print();

        const auto& stats = repositoryData.stats();
        std::cout << "Accesses: " << stats.accesses << '\n';
        std::cout << "Searches: " << stats.searches << '\n';
        std::cout << "Insertions: " << stats.insertions << '\n';
        std::cout << "Deletions: " << stats.deletions << '\n';
        std::cout << "Updates: " << stats.updates << '\n';

        demonstrateFailures();

        std::cout << "\nComplexity:\n"
                  << "Indexed access: O(1)\n"
                  << "Linear search: O(n)\n"
                  << "Binary search: O(log n), sorted input required\n"
                  << "Indexed insertion/deletion: O(n)\n"
                  << "Append: amortized O(1)\n"
                  << "Traversal: O(n)\n";
    } catch (const std::exception& error) {
        std::cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
