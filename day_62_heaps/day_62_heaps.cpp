#include <algorithm>
#include <chrono>
#include <functional>
#include <iomanip>
#include <iostream>
#include <limits>
#include <queue>
#include <random>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_map>
#include <utility>
#include <vector>

enum class HeapType {
    Min,
    Max
};

template <typename T, typename Compare>
class BinaryHeap {
private:
    std::vector<T> data;
    Compare compare;

    void siftUp(std::size_t index) {
        while (index > 0) {
            const std::size_t parent = (index - 1) / 2;

            if (!compare(data[index], data[parent])) {
                break;
            }

            std::swap(data[index], data[parent]);
            index = parent;
        }
    }

    void siftDown(std::size_t index) {
        while (true) {
            const std::size_t left = index * 2 + 1;
            const std::size_t right = index * 2 + 2;
            std::size_t best = index;

            if (left < data.size() && compare(data[left], data[best])) {
                best = left;
            }

            if (right < data.size() && compare(data[right], data[best])) {
                best = right;
            }

            if (best == index) {
                break;
            }

            std::swap(data[index], data[best]);
            index = best;
        }
    }

public:
    explicit BinaryHeap(Compare comparator = Compare{})
        : compare(std::move(comparator)) {}

    bool empty() const noexcept {
        return data.empty();
    }

    std::size_t size() const noexcept {
        return data.size();
    }

    const T& top() const {
        if (data.empty()) {
            throw std::out_of_range("top() called on empty heap");
        }
        return data.front();
    }

    void push(const T& value) {
        data.push_back(value);
        siftUp(data.size() - 1);
    }

    void push(T&& value) {
        data.push_back(std::move(value));
        siftUp(data.size() - 1);
    }

    T pop() {
        if (data.empty()) {
            throw std::out_of_range("pop() called on empty heap");
        }

        T result = std::move(data.front());
        data.front() = std::move(data.back());
        data.pop_back();

        if (!data.empty()) {
            siftDown(0);
        }

        return result;
    }

    void build(std::vector<T> values) {
        data = std::move(values);

        if (data.empty()) {
            return;
        }

        for (std::size_t i = data.size() / 2; i-- > 0;) {
            siftDown(i);
        }
    }

    T replaceTop(T value) {
        if (data.empty()) {
            throw std::out_of_range("replaceTop() called on empty heap");
        }

        T old = std::move(data.front());
        data.front() = std::move(value);
        siftDown(0);
        return old;
    }

    bool validate() const {
        for (std::size_t child = 1; child < data.size(); ++child) {
            const std::size_t parent = (child - 1) / 2;

            if (compare(data[child], data[parent])) {
                return false;
            }
        }

        return true;
    }
};

using MinHeap = BinaryHeap<int, std::less<int>>;
using MaxHeap = BinaryHeap<int, std::greater<int>>;

struct Job {
    std::string name;
    int priority;
    int duration;
    std::size_t sequence;
};

struct JobCompare {
    bool operator()(const Job& a, const Job& b) const {
        if (a.priority != b.priority) {
            return a.priority > b.priority;
        }

        return a.sequence > b.sequence;
    }
};

class GovernanceScheduler {
private:
    BinaryHeap<Job, JobCompare> queue;
    std::size_t sequence = 0;

public:
    void submit(std::string name, int priority, int duration) {
        if (name.empty()) {
            throw std::invalid_argument("job name cannot be empty");
        }

        if (priority < 0) {
            throw std::invalid_argument("priority cannot be negative");
        }

        if (duration <= 0) {
            throw std::invalid_argument("duration must be positive");
        }

        queue.push(Job{
            std::move(name),
            priority,
            duration,
            sequence++
        });
    }

    std::vector<Job> execute() {
        std::vector<Job> completed;

        while (!queue.empty()) {
            completed.push_back(queue.pop());
        }

        return completed;
    }
};

std::vector<int> topK(const std::vector<int>& values, std::size_t k) {
    if (k == 0 || k > values.size()) {
        throw std::invalid_argument("k must be in the range 1..values.size()");
    }

    MinHeap heap;

    for (int value : values) {
        if (heap.size() < k) {
            heap.push(value);
        } else if (value > heap.top()) {
            heap.replaceTop(value);
        }
    }

    std::vector<int> result;
    result.reserve(k);

    while (!heap.empty()) {
        result.push_back(heap.pop());
    }

    std::sort(result.rbegin(), result.rend());
    return result;
}

void printVector(const std::vector<int>& values) {
    std::cout << "[";

    for (std::size_t i = 0; i < values.size(); ++i) {
        if (i > 0) {
            std::cout << ", ";
        }

        std::cout << values[i];
    }

    std::cout << "]\n";
}

void basicHeapDemo() {
    std::cout << "=== Binary Heaps ===\n";

    MinHeap minHeap;
    MaxHeap maxHeap;

    const std::vector<int> values{9, 4, 7, 1, 3, 8, 2};

    minHeap.build(values);
    maxHeap.build(values);

    std::vector<int> ascending;
    std::vector<int> descending;

    while (!minHeap.empty()) {
        ascending.push_back(minHeap.pop());
    }

    while (!maxHeap.empty()) {
        descending.push_back(maxHeap.pop());
    }

    std::cout << "Ascending: ";
    printVector(ascending);

    std::cout << "Descending: ";
    printVector(descending);
}

void priorityQueueDemo() {
    std::cout << "\n=== Priority Queue ===\n";

    GovernanceScheduler scheduler;

    scheduler.submit("database-backup", 2, 15);
    scheduler.submit("security-alert", 0, 3);
    scheduler.submit("report-generation", 4, 20);
    scheduler.submit("cache-refresh", 2, 5);
    scheduler.submit("incident-analysis", 1, 10);

    const auto completed = scheduler.execute();

    for (const auto& job : completed) {
        std::cout
            << job.name
            << " priority=" << job.priority
            << " duration=" << job.duration
            << '\n';
    }
}

void topKDemo() {
    std::cout << "\n=== Top-K Using a Bounded Min Heap ===\n";

    const std::vector<int> values{
        17, 4, 29, 11, 35, 8, 42, 19, 23
    };

    const auto result = topK(values, 3);
    printVector(result);
}

void edgeCaseDemo() {
    std::cout << "\n=== Edge Cases ===\n";

    MinHeap heap;

    try {
        heap.pop();
    } catch (const std::exception& ex) {
        std::cout << "Expected failure: " << ex.what() << '\n';
    }

    try {
        GovernanceScheduler invalid;
        invalid.submit("", 1, 5);
    } catch (const std::exception& ex) {
        std::cout << "Invalid job: " << ex.what() << '\n';
    }

    try {
        topK({1, 2, 3}, 0);
    } catch (const std::exception& ex) {
        std::cout << "Invalid k: " << ex.what() << '\n';
    }
}

void performanceDemo() {
    std::cout << "\n=== Heap Construction Performance ===\n";

    std::mt19937 generator(42);
    std::uniform_int_distribution<int> distribution(1, 1'000'000);

    std::vector<int> values;
    values.reserve(100'000);

    for (int i = 0; i < 100'000; ++i) {
        values.push_back(distribution(generator));
    }

    MinHeap heap;

    const auto start = std::chrono::steady_clock::now();
    heap.build(values);
    const auto end = std::chrono::steady_clock::now();

    const std::chrono::duration<double, std::milli> elapsed = end - start;

    std::cout
        << "Elements: " << values.size() << '\n'
        << "Bottom-up heap construction: "
        << std::fixed << std::setprecision(3)
        << elapsed.count() << " ms\n"
        << "Heap valid: " << std::boolalpha
        << heap.validate() << '\n';
}

int main() {
    try {
        basicHeapDemo();
        priorityQueueDemo();
        topKDemo();
        edgeCaseDemo();
        performanceDemo();
    } catch (const std::exception& ex) {
        std::cerr << "Fatal error: " << ex.what() << '\n';
        return 1;
    }

    return 0;
}
