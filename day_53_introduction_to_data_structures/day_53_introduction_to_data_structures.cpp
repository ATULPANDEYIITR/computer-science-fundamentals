#include <algorithm>
#include <chrono>
#include <functional>
#include <iomanip>
#include <iostream>
#include <memory>
#include <optional>
#include <queue>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace std;

/*
 * A repository build system is modeled as a dependency graph.
 * The implementation deliberately uses C++ ownership and standard containers
 * to show how data-structure choices affect correctness and performance.
 */

template <typename T>
class Stack {
private:
    vector<T> items;

public:
    void push(const T& value) {
        items.push_back(value);
    }

    T pop() {
        if (items.empty()) {
            throw runtime_error("Cannot pop from an empty stack");
        }

        T value = items.back();
        items.pop_back();
        return value;
    }

    const T& peek() const {
        if (items.empty()) {
            throw runtime_error("Cannot inspect an empty stack");
        }
        return items.back();
    }

    bool empty() const {
        return items.empty();
    }
};


template <typename T>
class Queue {
private:
    queue<T> items;

public:
    void enqueue(const T& value) {
        items.push(value);
    }

    T dequeue() {
        if (items.empty()) {
            throw runtime_error("Cannot dequeue from an empty queue");
        }

        T value = items.front();
        items.pop();
        return value;
    }

    bool empty() const {
        return items.empty();
    }

    size_t size() const {
        return items.size();
    }
};


class BinarySearchTree {
private:
    struct Node {
        int value;
        unique_ptr<Node> left;
        unique_ptr<Node> right;

        explicit Node(int value) : value(value) {}
    };

    unique_ptr<Node> root;

    static void inorder(const unique_ptr<Node>& node, vector<int>& result) {
        if (!node) {
            return;
        }

        inorder(node->left, result);
        result.push_back(node->value);
        inorder(node->right, result);
    }

public:
    void insert(int value) {
        if (!root) {
            root = make_unique<Node>(value);
            return;
        }

        Node* current = root.get();

        while (true) {
            if (value == current->value) {
                return;
            }

            if (value < current->value) {
                if (!current->left) {
                    current->left = make_unique<Node>(value);
                    return;
                }
                current = current->left.get();
            } else {
                if (!current->right) {
                    current->right = make_unique<Node>(value);
                    return;
                }
                current = current->right.get();
            }
        }
    }

    bool contains(int value) const {
        const Node* current = root.get();

        while (current) {
            if (current->value == value) {
                return true;
            }

            current = value < current->value
                ? current->left.get()
                : current->right.get();
        }

        return false;
    }

    vector<int> sortedValues() const {
        vector<int> result;
        inorder(root, result);
        return result;
    }
};


class BuildGraph {
private:
    unordered_map<string, vector<string>> adjacency;

public:
    void addTask(const string& task) {
        if (task.empty()) {
            throw invalid_argument("Task name cannot be empty");
        }

        adjacency.try_emplace(task);
    }

    void addDependency(const string& prerequisite, const string& dependent) {
        if (!adjacency.contains(prerequisite) ||
            !adjacency.contains(dependent)) {
            throw invalid_argument("Dependency references an unknown task");
        }

        adjacency[prerequisite].push_back(dependent);
    }

    vector<string> topologicalOrder() const {
        unordered_map<string, int> indegree;

        for (const auto& [task, _] : adjacency) {
            indegree[task] = 0;
        }

        for (const auto& [_, dependents] : adjacency) {
            for (const string& dependent : dependents) {
                ++indegree[dependent];
            }
        }

        queue<string> ready;

        for (const auto& [task, degree] : indegree) {
            if (degree == 0) {
                ready.push(task);
            }
        }

        vector<string> order;

        while (!ready.empty()) {
            string task = ready.front();
            ready.pop();
            order.push_back(task);

            auto it = adjacency.find(task);
            for (const string& dependent : it->second) {
                if (--indegree[dependent] == 0) {
                    ready.push(dependent);
                }
            }
        }

        if (order.size() != adjacency.size()) {
            throw runtime_error("Build dependency cycle detected");
        }

        return order;
    }
};


optional<size_t> binarySearch(const vector<int>& values, int target) {
    size_t left = 0;
    size_t right = values.size();

    // Half-open interval [left, right) avoids unsigned underflow.
    while (left < right) {
        const size_t middle = left + (right - left) / 2;

        if (values[middle] == target) {
            return middle;
        }

        if (values[middle] < target) {
            left = middle + 1;
        } else {
            right = middle;
        }
    }

    return nullopt;
}


void printVector(const vector<string>& values) {
    cout << "[";
    for (size_t i = 0; i < values.size(); ++i) {
        if (i > 0) {
            cout << ", ";
        }
        cout << values[i];
    }
    cout << "]\n";
}


int main() {
    try {
        Stack<string> executionStack;
        executionStack.push("compile");
        executionStack.push("test");
        executionStack.push("package");

        cout << "Stack pop: " << executionStack.pop() << "\n";
        cout << "Stack peek: " << executionStack.peek() << "\n";

        Queue<string> requestQueue;
        requestQueue.enqueue("build-101");
        requestQueue.enqueue("build-102");
        requestQueue.enqueue("build-103");

        cout << "Queue dequeue: " << requestQueue.dequeue() << "\n";
        cout << "Queue size: " << requestQueue.size() << "\n";

        BinarySearchTree buildNumbers;

        for (int value : {50, 30, 70, 20, 40, 60, 80}) {
            buildNumbers.insert(value);
        }

        cout << "BST sorted values: ";
        for (int value : buildNumbers.sortedValues()) {
            cout << value << " ";
        }
        cout << "\n";

        cout << boolalpha
             << "BST contains 60: "
             << buildNumbers.contains(60)
             << "\n";

        BuildGraph buildGraph;

        for (const string& task :
             {"compile", "unit-test", "package", "security-scan", "deploy"}) {
            buildGraph.addTask(task);
        }

        buildGraph.addDependency("compile", "unit-test");
        buildGraph.addDependency("unit-test", "package");
        buildGraph.addDependency("package", "security-scan");
        buildGraph.addDependency("security-scan", "deploy");

        const vector<string> order = buildGraph.topologicalOrder();

        cout << "Build order: ";
        printVector(order);

        const vector<int> sortedBuildIds = {
            1001, 1007, 1012, 1020, 1031, 1044, 1059
        };

        const auto found = binarySearch(sortedBuildIds, 1031);

        if (found.has_value()) {
            cout << "Binary-search position: " << *found << "\n";
        } else {
            cout << "Build identifier was not found\n";
        }

        /*
         * unordered_set gives average O(1) duplicate detection.
         * The container does not preserve insertion order.
         */
        unordered_set<string> changedFiles = {
            "src/parser.cpp",
            "src/parser.cpp",
            "tests/parser_test.cpp",
            "README.md"
        };

        cout << "Changed-file count after deduplication: "
             << changedFiles.size() << "\n";

        /*
         * A vector has contiguous storage and good cache locality.
         * This matters when an operation scans every element.
         */
        constexpr size_t sampleSize = 1'000'000;
        vector<int> measurements;
        measurements.reserve(sampleSize);

        for (size_t i = 0; i < sampleSize; ++i) {
            measurements.push_back(static_cast<int>(i));
        }

        const auto start = chrono::steady_clock::now();

        volatile long long checksum = 0;
        for (int value : measurements) {
            checksum += value;
        }

        const auto end = chrono::steady_clock::now();

        const chrono::duration<double, milli> elapsed = end - start;

        cout << fixed << setprecision(3);
        cout << "Sequential scan time: "
             << elapsed.count() << " ms\n";
        cout << "Checksum: " << checksum << "\n";

    } catch (const exception& error) {
        cerr << "Operation failed: " << error.what() << "\n";
        return 1;
    }

    return 0;
}
