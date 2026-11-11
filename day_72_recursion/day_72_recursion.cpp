#include <algorithm>
#include <chrono>
#include <cstddef>
#include <exception>
#include <functional>
#include <iostream>
#include <limits>
#include <map>
#include <memory>
#include <numeric>
#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

using namespace std;

class RecursionException : public runtime_error {
public:
    explicit RecursionException(const string& message)
        : runtime_error(message) {}
};

class ValidationException : public RecursionException {
public:
    explicit ValidationException(const string& message)
        : RecursionException(message) {}
};

class DepthLimitException : public RecursionException {
public:
    explicit DepthLimitException(const string& message)
        : RecursionException(message) {}
};

enum class TraversalOrder {
    PREORDER,
    INORDER,
    POSTORDER
};

struct Metrics {
    size_t calls = 0;
    size_t maximumDepth = 0;
    size_t cacheHits = 0;
    size_t comparisons = 0;

    void enter(size_t depth, size_t maximumAllowed) {
        if (depth > maximumAllowed) {
            throw DepthLimitException(
                "Configured recursion depth exceeded."
            );
        }

        ++calls;
        maximumDepth = max(maximumDepth, depth);
    }
};

struct TreeNode {
    int value;
    unique_ptr<TreeNode> left;
    unique_ptr<TreeNode> right;

    explicit TreeNode(int v) : value(v) {}
};

struct RecursionTreeNode {
    string problem;
    size_t depth;
    vector<RecursionTreeNode> children;
    bool isBaseCase = false;
};

class RecursionEngine {
private:
    size_t maxDepth;
    Metrics metrics;

    void checkInput(size_t n, size_t maximum) const {
        if (n > maximum) {
            throw ValidationException(
                "Input exceeds configured algorithm limit."
            );
        }
    }

    long long fibonacciMemo(
        int n,
        unordered_map<int, long long>& cache,
        size_t depth
    ) {
        metrics.enter(depth, maxDepth);

        if (n <= 1) {
            return n;
        }

        auto found = cache.find(n);

        if (found != cache.end()) {
            ++metrics.cacheHits;
            return found->second;
        }

        long long result =
            fibonacciMemo(n - 1, cache, depth + 1) +
            fibonacciMemo(n - 2, cache, depth + 1);

        cache.emplace(n, result);
        return result;
    }

    int binarySearchRecursive(
        const vector<int>& values,
        int target,
        int left,
        int right,
        size_t depth
    ) {
        metrics.enter(depth, maxDepth);

        if (left > right) {
            return -1;
        }

        int middle = left + (right - left) / 2;
        ++metrics.comparisons;

        if (values[middle] == target) {
            return middle;
        }

        if (target < values[middle]) {
            return binarySearchRecursive(
                values, target, left, middle - 1, depth + 1
            );
        }

        return binarySearchRecursive(
            values, target, middle + 1, right, depth + 1
        );
    }

    void merge(
        vector<int>& values,
        vector<int>& buffer,
        int left,
        int middle,
        int right
    ) {
        int i = left;
        int j = middle + 1;
        int k = left;

        while (i <= middle && j <= right) {
            ++metrics.comparisons;

            if (values[i] <= values[j]) {
                buffer[k++] = values[i++];
            } else {
                buffer[k++] = values[j++];
            }
        }

        while (i <= middle) {
            buffer[k++] = values[i++];
        }

        while (j <= right) {
            buffer[k++] = values[j++];
        }

        for (int index = left; index <= right; ++index) {
            values[index] = buffer[index];
        }
    }

    void mergeSortRecursive(
        vector<int>& values,
        vector<int>& buffer,
        int left,
        int right,
        size_t depth
    ) {
        metrics.enter(depth, maxDepth);

        if (left >= right) {
            return;
        }

        int middle = left + (right - left) / 2;

        mergeSortRecursive(
            values, buffer, left, middle, depth + 1
        );

        mergeSortRecursive(
            values, buffer, middle + 1, right, depth + 1
        );

        merge(values, buffer, left, middle, right);
    }

    void traverseRecursive(
        const TreeNode* node,
        TraversalOrder order,
        vector<int>& output,
        unordered_set<const TreeNode*>& visited,
        size_t depth
    ) {
        metrics.enter(depth, maxDepth);

        if (node == nullptr) {
            return;
        }

        if (!visited.insert(node).second) {
            throw ValidationException(
                "Tree contains a repeated node or cycle."
            );
        }

        if (order == TraversalOrder::PREORDER) {
            output.push_back(node->value);
        }

        traverseRecursive(
            node->left.get(), order, output, visited, depth + 1
        );

        if (order == TraversalOrder::INORDER) {
            output.push_back(node->value);
        }

        traverseRecursive(
            node->right.get(), order, output, visited, depth + 1
        );

        if (order == TraversalOrder::POSTORDER) {
            output.push_back(node->value);
        }
    }

    RecursionTreeNode buildTreeRecursive(
        int n,
        size_t depth,
        size_t displayLimit
    ) {
        RecursionTreeNode node{
            "T(" + to_string(n) + ")",
            depth,
            {},
            n <= 1
        };

        if (n <= 1 || depth >= displayLimit) {
            return node;
        }

        int next = n / 2;

        node.children.push_back(
            buildTreeRecursive(next, depth + 1, displayLimit)
        );

        node.children.push_back(
            buildTreeRecursive(next, depth + 1, displayLimit)
        );

        return node;
    }

public:
    explicit RecursionEngine(size_t depthLimit = 500)
        : maxDepth(depthLimit) {
        if (depthLimit == 0) {
            throw ValidationException(
                "Depth limit must be positive."
            );
        }
    }

    void resetMetrics() {
        metrics = Metrics{};
    }

    const Metrics& getMetrics() const {
        return metrics;
    }

    unsigned long long factorial(unsigned int n) {
        checkInput(n, 20);
        resetMetrics();

        function<unsigned long long(unsigned int, size_t)> solve =
            [&](unsigned int value, size_t depth) {
                metrics.enter(depth, maxDepth);

                if (value <= 1) {
                    return 1ULL;
                }

                return static_cast<unsigned long long>(value) *
                    solve(value - 1, depth + 1);
            };

        return solve(n, 0);
    }

    long long fibonacciMemoized(int n) {
        if (n < 0 || n > 90) {
            throw ValidationException(
                "Fibonacci input must be between 0 and 90."
            );
        }

        resetMetrics();

        unordered_map<int, long long> cache;
        return fibonacciMemo(n, cache, 0);
    }

    int binarySearch(
        const vector<int>& values,
        int target
    ) {
        if (!is_sorted(values.begin(), values.end())) {
            throw ValidationException(
                "Binary search requires sorted input."
            );
        }

        resetMetrics();

        return binarySearchRecursive(
            values,
            target,
            0,
            static_cast<int>(values.size()) - 1,
            0
        );
    }

    vector<int> mergeSort(vector<int> values) {
        resetMetrics();

        if (values.size() > 10000000) {
            throw ValidationException(
                "Input exceeds configured sorting limit."
            );
        }

        if (values.empty()) {
            return values;
        }

        vector<int> buffer(values.size());

        mergeSortRecursive(
            values,
            buffer,
            0,
            static_cast<int>(values.size()) - 1,
            0
        );

        return values;
    }

    vector<int> traverse(
        const TreeNode* root,
        TraversalOrder order
    ) {
        resetMetrics();

        vector<int> result;
        unordered_set<const TreeNode*> visited;

        traverseRecursive(
            root, order, result, visited, 0
        );

        return result;
    }

    RecursionTreeNode recursionTree(
        int n,
        size_t displayLimit = 5
    ) {
        if (n < 0) {
            throw ValidationException(
                "Recursion-tree input cannot be negative."
            );
        }

        return buildTreeRecursive(n, 0, displayLimit);
    }
};

class DependencyGraph {
private:
    map<string, vector<string>> graph;

public:
    void addTask(
        const string& task,
        const vector<string>& dependencies
    ) {
        if (task.empty()) {
            throw ValidationException("Task name cannot be empty.");
        }

        if (graph.count(task)) {
            throw ValidationException("Duplicate task: " + task);
        }

        graph.emplace(task, dependencies);
    }

    vector<string> executionOrder() const {
        enum class State {
            UNVISITED,
            ACTIVE,
            COMPLETE
        };

        unordered_map<string, State> states;
        vector<string> order;

        for (const auto& [task, dependencies] : graph) {
            for (const auto& dependency : dependencies) {
                if (!graph.count(dependency)) {
                    throw ValidationException(
                        "Unknown dependency: " + dependency
                    );
                }
            }
        }

        function<void(const string&)> visit =
            [&](const string& task) {
                State state = states[task];

                if (state == State::COMPLETE) {
                    return;
                }

                if (state == State::ACTIVE) {
                    throw ValidationException(
                        "Circular dependency detected at " + task
                    );
                }

                states[task] = State::ACTIVE;

                for (const auto& dependency : graph.at(task)) {
                    visit(dependency);
                }

                states[task] = State::COMPLETE;
                order.push_back(task);
            };

        for (const auto& [task, dependencies] : graph) {
            visit(task);
        }

        return order;
    }
};

void printTree(
    const RecursionTreeNode& node,
    const string& prefix = ""
) {
    cout << prefix << node.problem;

    if (node.isBaseCase) {
        cout << " [base case]";
    }

    cout << '\n';

    for (const auto& child : node.children) {
        printTree(child, prefix + "  ");
    }
}

void printMetrics(const Metrics& metrics) {
    cout << "Recursive calls: " << metrics.calls << '\n';
    cout << "Maximum depth: " << metrics.maximumDepth << '\n';
    cout << "Cache hits: " << metrics.cacheHits << '\n';
    cout << "Comparisons: " << metrics.comparisons << '\n';
}

void runTests() {
    RecursionEngine engine;

    if (engine.factorial(5) != 120) {
        throw runtime_error("Factorial test failed.");
    }

    if (engine.factorial(0) != 1) {
        throw runtime_error("Factorial base case failed.");
    }

    if (engine.fibonacciMemoized(40) != 102334155) {
        throw runtime_error("Fibonacci test failed.");
    }

    vector<int> sorted = engine.mergeSort({8, 2, 5, 1, 9});

    if (sorted != vector<int>({1, 2, 5, 8, 9})) {
        throw runtime_error("Merge sort test failed.");
    }

    if (engine.binarySearch({1, 3, 5, 7, 9}, 7) != 3) {
        throw runtime_error("Binary search test failed.");
    }

    auto root = make_unique<TreeNode>(8);
    root->left = make_unique<TreeNode>(4);
    root->right = make_unique<TreeNode>(12);

    if (
        engine.traverse(root.get(), TraversalOrder::INORDER)
        != vector<int>({4, 8, 12})
    ) {
        throw runtime_error("Tree traversal test failed.");
    }

    DependencyGraph graph;
    graph.addTask("deploy", {"test"});
    graph.addTask("test", {"build"});
    graph.addTask("build", {"compile"});
    graph.addTask("compile", {});

    vector<string> order = graph.executionOrder();

    if (order != vector<string>({
        "compile", "build", "test", "deploy"
    })) {
        throw runtime_error("Dependency evaluation failed.");
    }

    cout << "All tests passed.\n";
}

int main() {
    try {
        RecursionEngine engine;

        cout << "1. FACTORIAL\n";
        cout << "5! = " << engine.factorial(5) << '\n';
        printMetrics(engine.getMetrics());

        cout << "\n2. MEMOIZED FIBONACCI\n";
        cout << "F(40) = " << engine.fibonacciMemoized(40) << '\n';
        printMetrics(engine.getMetrics());

        cout << "\n3. RECURSIVE BINARY SEARCH\n";

        vector<int> numbers = {
            2, 4, 6, 8, 10, 12, 14
        };

        cout << "Position of 10: "
             << engine.binarySearch(numbers, 10) << '\n';

        printMetrics(engine.getMetrics());

        cout << "\n4. MERGE SORT\n";

        vector<int> input = {
            45, 12, 78, 3, 29, 18, 1
        };

        vector<int> sorted = engine.mergeSort(input);

        for (int value : sorted) {
            cout << value << ' ';
        }

        cout << '\n';
        printMetrics(engine.getMetrics());

        cout << "\n5. BINARY TREE TRAVERSAL\n";

        auto root = make_unique<TreeNode>(10);

        root->left = make_unique<TreeNode>(5);
        root->right = make_unique<TreeNode>(15);

        root->left->left = make_unique<TreeNode>(2);
        root->left->right = make_unique<TreeNode>(7);
        root->right->right = make_unique<TreeNode>(20);

        vector<int> traversal = engine.traverse(
            root.get(), TraversalOrder::INORDER
        );

        for (int value : traversal) {
            cout << value << ' ';
        }

        cout << '\n';
        printMetrics(engine.getMetrics());

        cout << "\n6. RECURSION TREE\n";
        printTree(engine.recursionTree(16));

        cout << "\n7. DEPENDENCY GRAPH\n";

        DependencyGraph dependencies;

        dependencies.addTask("deploy", {"integration-test"});
        dependencies.addTask("integration-test", {"unit-test"});
        dependencies.addTask("unit-test", {"build"});
        dependencies.addTask("build", {"compile"});
        dependencies.addTask("compile", {});

        for (const string& task : dependencies.executionOrder()) {
            cout << task << '\n';
        }

        cout << "\n8. PERFORMANCE MEASUREMENT\n";

        vector<int> largeInput(100000);
        iota(largeInput.rbegin(), largeInput.rend(), 0);

        auto start = chrono::steady_clock::now();

        vector<int> result = engine.mergeSort(largeInput);

        auto finish = chrono::steady_clock::now();

        auto elapsed =
            chrono::duration_cast<chrono::microseconds>(
                finish - start
            ).count();

        cout << "Elements sorted: " << result.size() << '\n';
        cout << "Elapsed microseconds: " << elapsed << '\n';

        cout << "\n9. AUTOMATED TESTS\n";
        runTests();

    } catch (const exception& error) {
        cerr << "Execution error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
