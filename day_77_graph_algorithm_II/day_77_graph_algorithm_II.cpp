#include <algorithm>
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

/*
 * Graph Algorithms II
 * Dijkstra's Shortest Path and Repository-Independent
 * Transportation Network Routing Engine.
 *
 * Standard: C++17
 *
 * Features:
 * - Weighted directed and undirected graphs
 * - Adjacency-list representation
 * - Priority queue
 * - Shortest path computation
 * - Predecessor-based path reconstruction
 * - Multi-source shortest paths
 * - Early destination termination
 * - Negative-weight validation
 * - Unreachable vertex detection
 * - Route diagnostics
 */

using Vertex = string;
using Distance = double;

constexpr Distance INF =
    numeric_limits<Distance>::infinity();

struct Edge {
    Vertex destination;
    Distance weight;
};

struct PathResult {
    Vertex source;

    unordered_map<Vertex, Distance> distances;
    unordered_map<Vertex, Vertex> predecessors;

    vector<Vertex> settled;
    size_t examinedEdges = 0;
    size_t relaxations = 0;

    Distance distanceTo(const Vertex& destination) const {
        auto it = distances.find(destination);

        if (it == distances.end()) {
            throw invalid_argument("Unknown destination: " + destination);
        }

        return it->second;
    }

    vector<Vertex> pathTo(const Vertex& destination) const {
        Distance distance = distanceTo(destination);

        if (!isfinite(distance)) {
            return {};
        }

        vector<Vertex> path;
        Vertex current = destination;

        while (true) {
            path.push_back(current);

            if (current == source) {
                break;
            }

            auto it = predecessors.find(current);

            if (
                it == predecessors.end() ||
                it->second.empty()
            ) {
                return {};
            }

            current = it->second;

            if (path.size() > distances.size()) {
                throw logic_error("Invalid predecessor chain");
            }
        }

        reverse(path.begin(), path.end());
        return path;
    }
};

class WeightedGraph {
private:
    unordered_map<Vertex, vector<Edge>> adjacency;
    bool directed;

public:
    explicit WeightedGraph(bool isDirected = true)
        : directed(isDirected) {}

    void addVertex(const Vertex& vertex) {
        if (vertex.empty()) {
            throw invalid_argument("Vertex cannot be empty");
        }

        adjacency.try_emplace(vertex);
    }

    void addEdge(
        const Vertex& source,
        const Vertex& destination,
        Distance weight
    ) {
        if (source.empty() || destination.empty()) {
            throw invalid_argument("Invalid vertex name");
        }

        if (!isfinite(weight)) {
            throw invalid_argument("Weight must be finite");
        }

        if (weight < 0) {
            throw invalid_argument(
                "Dijkstra does not support negative weights"
            );
        }

        addVertex(source);
        addVertex(destination);

        adjacency[source].push_back({
            destination,
            weight
        });

        if (!directed) {
            adjacency[destination].push_back({
                source,
                weight
            });
        }
    }

    size_t vertexCount() const {
        return adjacency.size();
    }

    size_t edgeCount() const {
        size_t count = 0;

        for (const auto& [vertex, edges] : adjacency) {
            count += edges.size();
        }

        return count;
    }

    bool contains(const Vertex& vertex) const {
        return adjacency.find(vertex) != adjacency.end();
    }

    PathResult dijkstra(
        const Vertex& source,
        const Vertex& target = ""
    ) const {
        if (!contains(source)) {
            throw invalid_argument("Unknown source: " + source);
        }

        if (!target.empty() && !contains(target)) {
            throw invalid_argument("Unknown target: " + target);
        }

        PathResult result;
        result.source = source;

        for (const auto& [vertex, edges] : adjacency) {
            result.distances[vertex] = INF;
            result.predecessors[vertex] = "";
        }

        result.distances[source] = 0;

        /*
         * The standard priority_queue is a max-heap.
         * greater<> reverses ordering to create a min-heap.
         *
         * Entries contain distance and vertex.
         */
        using QueueEntry = pair<Distance, Vertex>;

        priority_queue<
            QueueEntry,
            vector<QueueEntry>,
            greater<QueueEntry>
        > pq;

        pq.push({0, source});

        unordered_set<Vertex> settled;

        while (!pq.empty()) {
            auto [currentDistance, current] = pq.top();
            pq.pop();

            if (settled.count(current)) {
                continue;
            }

            if (currentDistance != result.distances[current]) {
                continue;
            }

            settled.insert(current);
            result.settled.push_back(current);

            if (!target.empty() && current == target) {
                break;
            }

            for (const Edge& edge : adjacency.at(current)) {
                result.examinedEdges++;

                if (settled.count(edge.destination)) {
                    continue;
                }

                Distance candidate =
                    currentDistance + edge.weight;

                if (!isfinite(candidate)) {
                    throw overflow_error("Distance overflow");
                }

                if (
                    candidate <
                    result.distances[edge.destination]
                ) {
                    result.distances[edge.destination] = candidate;

                    result.predecessors[edge.destination] = current;

                    pq.push({
                        candidate,
                        edge.destination
                    });

                    result.relaxations++;
                }
            }
        }

        return result;
    }

    PathResult multiSourceDijkstra(
        const vector<Vertex>& sources
    ) const {
        if (sources.empty()) {
            throw invalid_argument("Source list cannot be empty");
        }

        PathResult result;
        result.source = sources.front();

        for (const auto& [vertex, edges] : adjacency) {
            result.distances[vertex] = INF;
            result.predecessors[vertex] = "";
        }

        priority_queue<
            pair<Distance, Vertex>,
            vector<pair<Distance, Vertex>>,
            greater<pair<Distance, Vertex>>
        > pq;

        unordered_set<Vertex> uniqueSources;

        for (const Vertex& source : sources) {
            if (!contains(source)) {
                throw invalid_argument("Unknown source: " + source);
            }

            if (!uniqueSources.insert(source).second) {
                throw invalid_argument("Duplicate source");
            }

            result.distances[source] = 0;
            pq.push({0, source});
        }

        unordered_set<Vertex> settled;

        while (!pq.empty()) {
            auto [distance, current] = pq.top();
            pq.pop();

            if (settled.count(current)) {
                continue;
            }

            if (distance != result.distances[current]) {
                continue;
            }

            settled.insert(current);
            result.settled.push_back(current);

            for (const Edge& edge : adjacency.at(current)) {
                result.examinedEdges++;

                if (settled.count(edge.destination)) {
                    continue;
                }

                Distance candidate = distance + edge.weight;

                if (!isfinite(candidate)) {
                    throw overflow_error("Distance overflow");
                }

                if (candidate < result.distances[edge.destination]) {
                    result.distances[edge.destination] = candidate;
                    result.predecessors[edge.destination] = current;

                    pq.push({
                        candidate,
                        edge.destination
                    });

                    result.relaxations++;
                }
            }
        }

        return result;
    }

    vector<Vertex> vertices() const {
        vector<Vertex> result;

        for (const auto& [vertex, edges] : adjacency) {
            result.push_back(vertex);
        }

        sort(result.begin(), result.end());

        return result;
    }
};

void printPath(
    const PathResult& result,
    const Vertex& destination
) {
    Distance distance = result.distanceTo(destination);

    cout << "\nDestination: " << destination << '\n';

    if (!isfinite(distance)) {
        cout << "Status: UNREACHABLE\n";
        return;
    }

    vector<Vertex> path = result.pathTo(destination);

    cout << "Path: ";

    for (size_t i = 0; i < path.size(); ++i) {
        if (i > 0) {
            cout << " -> ";
        }

        cout << path[i];
    }

    cout << "\nDistance: "
         << distance << " minutes\n";
}

WeightedGraph buildNetwork() {
    WeightedGraph graph(true);

    const vector<tuple<Vertex, Vertex, Distance>> edges = {
        {"Lucknow", "Kanpur", 90},
        {"Lucknow", "Ayodhya", 135},
        {"Lucknow", "Varanasi", 300},
        {"Kanpur", "Agra", 210},
        {"Kanpur", "Prayagraj", 180},
        {"Ayodhya", "Gorakhpur", 150},
        {"Ayodhya", "Varanasi", 190},
        {"Gorakhpur", "Patna", 240},
        {"Varanasi", "Patna", 200},
        {"Varanasi", "Prayagraj", 130},
        {"Prayagraj", "Delhi", 500},
        {"Agra", "Delhi", 150},
        {"Lucknow", "Express", 0},
        {"Express", "Kanpur", 70}
    };

    for (const auto& [source, destination, weight] : edges) {
        graph.addEdge(source, destination, weight);
    }

    graph.addVertex("Mumbai");
    graph.addVertex("Chennai");

    return graph;
}

void runTests() {
    WeightedGraph graph(true);

    graph.addEdge("A", "B", 4);
    graph.addEdge("A", "C", 1);
    graph.addEdge("C", "B", 2);
    graph.addEdge("B", "D", 1);
    graph.addVertex("Z");

    PathResult result = graph.dijkstra("A");

    if (result.distanceTo("D") != 4) {
        throw runtime_error("Shortest distance test failed");
    }

    vector<Vertex> expected = {"A", "C", "B", "D"};

    if (result.pathTo("D") != expected) {
        throw runtime_error("Path reconstruction test failed");
    }

    if (!result.pathTo("Z").empty()) {
        throw runtime_error("Unreachable vertex test failed");
    }

    bool rejected = false;

    try {
        graph.addEdge("A", "D", -5);
    } catch (const invalid_argument&) {
        rejected = true;
    }

    if (!rejected) {
        throw runtime_error("Negative weight test failed");
    }

    WeightedGraph undirected(false);
    undirected.addEdge("X", "Y", 8);

    if (undirected.dijkstra("Y").distanceTo("X") != 8) {
        throw runtime_error("Undirected graph test failed");
    }

    PathResult multi = graph.multiSourceDijkstra({"A", "D"});

    if (multi.distanceTo("B") != 2) {
        throw runtime_error("Multi-source test failed");
    }

    cout << "\nAll correctness tests passed.\n";
}

int main() {
    try {
        cout << fixed << setprecision(2);

        WeightedGraph graph = buildNetwork();

        cout << "DIJKSTRA SHORTEST PATH ENGINE\n";
        cout << "=============================\n";

        cout << "Vertices: " << graph.vertexCount() << '\n';
        cout << "Directed edges: " << graph.edgeCount() << '\n';

        PathResult result = graph.dijkstra("Lucknow");

        vector<Vertex> destinations = {
            "Delhi",
            "Patna",
            "Gorakhpur",
            "Mumbai"
        };

        for (const Vertex& destination : destinations) {
            printPath(result, destination);
        }

        cout << "\nExecution diagnostics\n";
        cout << "Settled vertices: "
             << result.settled.size() << '\n';

        cout << "Examined edges: "
             << result.examinedEdges << '\n';

        cout << "Relaxations: "
             << result.relaxations << '\n';

        cout << "\nEarly termination query\n";

        PathResult optimized = graph.dijkstra(
            "Lucknow",
            "Delhi"
        );

        printPath(optimized, "Delhi");

        cout << "\nMulti-source shortest distances\n";

        PathResult multi = graph.multiSourceDijkstra({
            "Lucknow",
            "Patna"
        });

        for (const Vertex& vertex : graph.vertices()) {
            cout << left << setw(18) << vertex
                 << right << setw(10)
                 << multi.distanceTo(vertex) << '\n';
        }

        runTests();

        cout << "\nComplexity\n";
        cout << "Storage: O(V + E)\n";
        cout << "Dijkstra: O((V + E) log V)\n";
        cout << "Path reconstruction: O(V)\n";
        cout << "Auxiliary space: O(V)\n";

    } catch (const exception& error) {
        cerr << "Error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
