#include <algorithm>
#include <chrono>
#include <cmath>
#include <functional>
#include <iomanip>
#include <iostream>
#include <limits>
#include <queue>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

using namespace std;

enum class AlgorithmStatus {
    Registered,
    Executing,
    Passed,
    Failed
};

struct Edge {
    string destination;
    double weight;
};

struct RouteResult {
    unordered_map<string, double> distances;
    unordered_map<string, string> predecessors;
};

struct ExecutionMetrics {
    size_t vertices = 0;
    size_t edges = 0;
    size_t relaxations = 0;
    size_t queue_operations = 0;
    double elapsedMilliseconds = 0.0;
};

class WeightedGraph {
private:
    unordered_map<string, vector<Edge>> adjacency;

public:
    void addVertex(const string& vertex) {
        if (vertex.empty()) {
            throw invalid_argument("Vertex cannot be empty.");
        }

        adjacency.try_emplace(vertex);
    }

    void addEdge(
        const string& source,
        const string& destination,
        double weight
    ) {
        if (!adjacency.count(source) ||
            !adjacency.count(destination)) {
            throw invalid_argument("Unknown graph vertex.");
        }

        if (!isfinite(weight) || weight < 0.0) {
            throw invalid_argument(
                "Dijkstra requires finite nonnegative weights."
            );
        }

        adjacency[source].push_back({destination, weight});
    }

    const auto& vertices() const {
        return adjacency;
    }

    size_t vertexCount() const {
        return adjacency.size();
    }

    size_t edgeCount() const {
        size_t total = 0;

        for (const auto& [vertex, edges] : adjacency) {
            total += edges.size();
        }

        return total;
    }

    RouteResult shortestPaths(
        const string& source,
        ExecutionMetrics& metrics
    ) const {
        if (!adjacency.count(source)) {
            throw invalid_argument("Source vertex does not exist.");
        }

        const double INF = numeric_limits<double>::infinity();

        RouteResult result;

        for (const auto& [vertex, edges] : adjacency) {
            result.distances[vertex] = INF;
        }

        result.distances[source] = 0.0;

        using QueueEntry = pair<double, string>;

        priority_queue<
            QueueEntry,
            vector<QueueEntry>,
            greater<QueueEntry>
        > pending;

        pending.push({0.0, source});
        metrics.queue_operations++;

        while (!pending.empty()) {
            auto [distance, current] = pending.top();
            pending.pop();

            if (distance > result.distances.at(current)) {
                continue;
            }

            for (const Edge& edge : adjacency.at(current)) {
                metrics.relaxations++;

                double candidate = distance + edge.weight;

                if (!isfinite(candidate)) {
                    throw overflow_error(
                        "Path distance overflow."
                    );
                }

                if (candidate <
                    result.distances.at(edge.destination)) {
                    result.distances[edge.destination] = candidate;
                    result.predecessors[edge.destination] = current;

                    pending.push({
                        candidate,
                        edge.destination
                    });

                    metrics.queue_operations++;
                }
            }
        }

        return result;
    }

    vector<string> reconstructPath(
        const string& source,
        const string& destination,
        const RouteResult& result
    ) const {
        if (!result.distances.count(destination) ||
            result.distances.at(destination) ==
                numeric_limits<double>::infinity()) {
            return {};
        }

        vector<string> path;
        unordered_set<string> visited;

        string current = destination;

        while (true) {
            if (!visited.insert(current).second) {
                throw logic_error("Predecessor cycle detected.");
            }

            path.push_back(current);

            if (current == source) {
                break;
            }

            auto it = result.predecessors.find(current);

            if (it == result.predecessors.end()) {
                throw logic_error("Broken predecessor chain.");
            }

            current = it->second;
        }

        reverse(path.begin(), path.end());
        return path;
    }
};

class AlgorithmRegistry {
private:
    struct Definition {
        string name;
        string category;
        string timeComplexity;
        string spaceComplexity;
        AlgorithmStatus status;
    };

    unordered_map<string, Definition> algorithms;

public:
    void registerAlgorithm(
        const string& name,
        const string& category,
        const string& time,
        const string& space
    ) {
        if (name.empty() ||
            time.empty() ||
            space.empty()) {
            throw invalid_argument(
                "Algorithm metadata cannot be empty."
            );
        }

        auto [it, inserted] = algorithms.emplace(
            name,
            Definition{
                name,
                category,
                time,
                space,
                AlgorithmStatus::Registered
            }
        );

        if (!inserted) {
            throw invalid_argument(
                "Algorithm already registered."
            );
        }
    }

    void updateStatus(
        const string& name,
        AlgorithmStatus status
    ) {
        auto it = algorithms.find(name);

        if (it == algorithms.end()) {
            throw invalid_argument("Unknown algorithm.");
        }

        it->second.status = status;
    }

    void display() const {
        cout << "\nAlgorithm Registry\n";
        cout << string(75, '-') << '\n';

        for (const auto& [name, definition] : algorithms) {
            cout
                << left << setw(20) << definition.name
                << setw(15) << definition.category
                << setw(22) << definition.timeComplexity
                << definition.spaceComplexity
                << '\n';
        }
    }
};

vector<int> mergeSort(const vector<int>& values) {
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

    left = mergeSort(left);
    right = mergeSort(right);

    vector<int> result;
    result.reserve(values.size());

    size_t i = 0;
    size_t j = 0;

    while (i < left.size() && j < right.size()) {
        if (left[i] <= right[j]) {
            result.push_back(left[i++]);
        } else {
            result.push_back(right[j++]);
        }
    }

    while (i < left.size()) {
        result.push_back(left[i++]);
    }

    while (j < right.size()) {
        result.push_back(right[j++]);
    }

    return result;
}

int binarySearch(
    const vector<int>& values,
    int target
) {
    if (!is_sorted(values.begin(), values.end())) {
        throw invalid_argument(
            "Binary search requires sorted input."
        );
    }

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

bool verifySorting() {
    vector<vector<int>> cases = {
        {},
        {1},
        {5, 4, 3, 2, 1},
        {1, 2, 3, 4, 5},
        {4, 4, 2, 2, 1},
        {-10, 5, 0, -3, 12}
    };

    for (const auto& input : cases) {
        auto result = mergeSort(input);
        auto expected = input;

        sort(expected.begin(), expected.end());

        if (result != expected) {
            return false;
        }

        if (result.size() != input.size()) {
            return false;
        }
    }

    return true;
}

bool verifyShortestPaths() {
    WeightedGraph graph;

    for (const string& vertex :
         {"A", "B", "C", "D", "E"}) {
        graph.addVertex(vertex);
    }

    graph.addEdge("A", "B", 4);
    graph.addEdge("A", "C", 1);
    graph.addEdge("C", "B", 2);
    graph.addEdge("B", "D", 1);
    graph.addEdge("C", "D", 5);

    ExecutionMetrics metrics;

    auto result = graph.shortestPaths("A", metrics);

    return result.distances.at("A") == 0 &&
           result.distances.at("B") == 3 &&
           result.distances.at("C") == 1 &&
           result.distances.at("D") == 4 &&
           isinf(result.distances.at("E"));
}

void demonstrateSorting() {
    vector<int> values = {
        64, 25, 12, 22, 11, 90, 3, 25
    };

    auto start = chrono::steady_clock::now();

    vector<int> sorted = mergeSort(values);

    auto finish = chrono::steady_clock::now();

    auto elapsed =
        chrono::duration<double, milli>(finish - start).count();

    cout << "\nSorting Demonstration\n";

    cout << "Input: ";

    for (int value : values) {
        cout << value << ' ';
    }

    cout << "\nOutput: ";

    for (int value : sorted) {
        cout << value << ' ';
    }

    cout << "\nTime: "
         << fixed << setprecision(4)
         << elapsed << " ms\n";

    cout << "Search for 22: "
         << binarySearch(sorted, 22)
         << '\n';
}

void demonstrateGraph() {
    WeightedGraph graph;

    for (const string& vertex :
         {"Warehouse", "Hub-A", "Hub-B", "Hub-C", "Customer"}) {
        graph.addVertex(vertex);
    }

    graph.addEdge("Warehouse", "Hub-A", 8);
    graph.addEdge("Warehouse", "Hub-B", 3);
    graph.addEdge("Hub-B", "Hub-A", 2);
    graph.addEdge("Hub-A", "Hub-C", 4);
    graph.addEdge("Hub-B", "Hub-C", 7);
    graph.addEdge("Hub-C", "Customer", 2);
    graph.addEdge("Hub-A", "Customer", 10);

    ExecutionMetrics metrics;

    metrics.vertices = graph.vertexCount();
    metrics.edges = graph.edgeCount();

    auto start = chrono::steady_clock::now();

    RouteResult result = graph.shortestPaths(
        "Warehouse",
        metrics
    );

    auto finish = chrono::steady_clock::now();

    metrics.elapsedMilliseconds =
        chrono::duration<double, milli>(
            finish - start
        ).count();

    cout << "\nLogistics Route Optimization\n";

    for (const auto& [vertex, distance] : result.distances) {
        cout << vertex << ": ";

        if (isinf(distance)) {
            cout << "Unreachable";
        } else {
            cout << distance;
        }

        cout << '\n';
    }

    auto path = graph.reconstructPath(
        "Warehouse",
        "Customer",
        result
    );

    cout << "Optimal route: ";

    for (size_t i = 0; i < path.size(); ++i) {
        if (i > 0) cout << " -> ";
        cout << path[i];
    }

    cout << "\nRelaxations: " << metrics.relaxations;
    cout << "\nQueue operations: " << metrics.queue_operations;
    cout << "\nExecution time: "
         << metrics.elapsedMilliseconds << " ms\n";
}

int main() {
    try {
        AlgorithmRegistry registry;

        registry.registerAlgorithm(
            "Binary Search",
            "Searching",
            "O(log n)",
            "O(1)"
        );

        registry.registerAlgorithm(
            "Merge Sort",
            "Sorting",
            "O(n log n)",
            "O(n)"
        );

        registry.registerAlgorithm(
            "Dijkstra",
            "Graph",
            "O((V+E) log V)",
            "O(V+E)"
        );

        registry.display();

        if (!verifySorting()) {
            throw runtime_error("Sorting correctness failed.");
        }

        if (!verifyShortestPaths()) {
            throw runtime_error("Shortest-path correctness failed.");
        }

        cout << "\nAll correctness tests passed.\n";

        demonstrateSorting();
        demonstrateGraph();

        cout << "\nAlgorithm execution completed.\n";
    }
    catch (const exception& error) {
        cerr << "Execution error: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}
