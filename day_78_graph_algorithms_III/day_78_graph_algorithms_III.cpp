#include <algorithm>
#include <cmath>
#include <iostream>
#include <limits>
#include <queue>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

constexpr double INF = numeric_limits<double>::infinity();

enum class PathStatus {
    FINITE,
    UNREACHABLE,
    NEGATIVE_INFINITY
};

struct Edge {
    int source;
    int destination;
    double weight;
};

struct BellmanFordResult {
    vector<double> distances;
    vector<int> predecessors;
    vector<bool> affected;
    vector<int> negativeCycle;
};

struct FloydWarshallResult {
    vector<vector<double>> distances;
    vector<vector<int>> next;
    vector<int> negativeCycles;
};

class GraphError : public runtime_error {
public:
    explicit GraphError(const string& message)
        : runtime_error(message) {}
};

class WeightedGraph {
private:
    int vertexCount;
    vector<Edge> edges;
    vector<vector<int>> adjacency;

    void validateVertex(int vertex) const {
        if (vertex < 0 || vertex >= vertexCount) {
            throw GraphError("Vertex index is out of range.");
        }
    }

    vector<int> reconstructCycle(
        int vertex,
        const vector<int>& predecessors
    ) const {
        if (vertex == -1) {
            return {};
        }

        int current = vertex;

        // Enter the cycle by following predecessor edges V times.
        for (int i = 0; i < vertexCount; ++i) {
            current = predecessors[current];

            if (current == -1) {
                return {};
            }
        }

        vector<int> cycle;
        int start = current;

        do {
            cycle.push_back(current);
            current = predecessors[current];

            if (current == -1 || cycle.size() > vertexCount) {
                return {};
            }
        } while (current != start);

        cycle.push_back(start);
        reverse(cycle.begin(), cycle.end());

        return cycle;
    }

public:
    explicit WeightedGraph(int vertices)
        : vertexCount(vertices),
          adjacency(vertices > 0 ? vertices : 0) {

        if (vertices <= 0) {
            throw GraphError("Graph must contain at least one vertex.");
        }
    }

    int size() const {
        return vertexCount;
    }

    const vector<Edge>& getEdges() const {
        return edges;
    }

    void addEdge(int source, int destination, double weight) {
        validateVertex(source);
        validateVertex(destination);

        if (!isfinite(weight)) {
            throw GraphError("Edge weight must be finite.");
        }

        edges.push_back({source, destination, weight});
        adjacency[source].push_back(destination);
    }

    BellmanFordResult bellmanFord(int source) const {
        validateVertex(source);

        vector<double> distances(vertexCount, INF);
        vector<int> predecessors(vertexCount, -1);
        vector<bool> affected(vertexCount, false);

        distances[source] = 0;

        // Standard V-1 relaxation rounds.
        for (int iteration = 0; iteration < vertexCount - 1; ++iteration) {
            bool changed = false;

            for (const Edge& edge : edges) {
                if (distances[edge.source] == INF) {
                    continue;
                }

                double candidate =
                    distances[edge.source] + edge.weight;

                if (candidate < distances[edge.destination]) {
                    distances[edge.destination] = candidate;
                    predecessors[edge.destination] = edge.source;
                    changed = true;
                }
            }

            if (!changed) {
                break;
            }
        }

        int witness = -1;
        queue<int> pending;

        // Identify vertices that can still be relaxed.
        for (const Edge& edge : edges) {
            if (distances[edge.source] == INF) {
                continue;
            }

            double candidate =
                distances[edge.source] + edge.weight;

            if (candidate < distances[edge.destination]) {
                distances[edge.destination] = candidate;
                predecessors[edge.destination] = edge.source;

                if (!affected[edge.destination]) {
                    affected[edge.destination] = true;
                    pending.push(edge.destination);
                }

                witness = edge.destination;
            }
        }

        // Propagate negative-infinity status through outgoing edges.
        while (!pending.empty()) {
            int vertex = pending.front();
            pending.pop();

            for (int destination : adjacency[vertex]) {
                if (!affected[destination]) {
                    affected[destination] = true;
                    pending.push(destination);
                }
            }
        }

        return {
            move(distances),
            move(predecessors),
            move(affected),
            reconstructCycle(witness, predecessors)
        };
    }

    PathStatus status(
        const BellmanFordResult& result,
        int destination
    ) const {
        validateVertex(destination);

        if (result.affected[destination]) {
            return PathStatus::NEGATIVE_INFINITY;
        }

        if (result.distances[destination] == INF) {
            return PathStatus::UNREACHABLE;
        }

        return PathStatus::FINITE;
    }

    vector<int> reconstructPath(
        const BellmanFordResult& result,
        int source,
        int destination
    ) const {
        validateVertex(source);
        validateVertex(destination);

        PathStatus currentStatus = status(result, destination);

        if (currentStatus == PathStatus::NEGATIVE_INFINITY) {
            throw GraphError(
                "Shortest path is undefined because of a negative cycle."
            );
        }

        if (currentStatus == PathStatus::UNREACHABLE) {
            return {};
        }

        vector<int> path;
        int current = destination;

        for (int i = 0; i <= vertexCount; ++i) {
            path.push_back(current);

            if (current == source) {
                reverse(path.begin(), path.end());
                return path;
            }

            current = result.predecessors[current];

            if (current == -1) {
                break;
            }
        }

        throw GraphError("Invalid predecessor chain.");
    }

    FloydWarshallResult floydWarshall() const {
        vector<vector<double>> distances(
            vertexCount,
            vector<double>(vertexCount, INF)
        );

        vector<vector<int>> next(
            vertexCount,
            vector<int>(vertexCount, -1)
        );

        for (int i = 0; i < vertexCount; ++i) {
            distances[i][i] = 0;
            next[i][i] = i;
        }

        for (const Edge& edge : edges) {
            if (edge.weight < distances[edge.source][edge.destination]) {
                distances[edge.source][edge.destination] = edge.weight;
                next[edge.source][edge.destination] = edge.destination;
            }
        }

        for (int k = 0; k < vertexCount; ++k) {
            for (int i = 0; i < vertexCount; ++i) {
                if (distances[i][k] == INF) {
                    continue;
                }

                for (int j = 0; j < vertexCount; ++j) {
                    if (distances[k][j] == INF) {
                        continue;
                    }

                    double candidate =
                        distances[i][k] + distances[k][j];

                    if (candidate < distances[i][j]) {
                        distances[i][j] = candidate;
                        next[i][j] = next[i][k];
                    }
                }
            }
        }

        vector<int> negativeCycles;

        for (int i = 0; i < vertexCount; ++i) {
            if (distances[i][i] < 0) {
                negativeCycles.push_back(i);
            }
        }

        return {
            move(distances),
            move(next),
            move(negativeCycles)
        };
    }

    PathStatus floydStatus(
        const FloydWarshallResult& result,
        int source,
        int destination
    ) const {
        validateVertex(source);
        validateVertex(destination);

        for (int cycle : result.negativeCycles) {
            if (
                result.distances[source][cycle] != INF &&
                result.distances[cycle][destination] != INF
            ) {
                return PathStatus::NEGATIVE_INFINITY;
            }
        }

        return result.distances[source][destination] == INF
            ? PathStatus::UNREACHABLE
            : PathStatus::FINITE;
    }

    vector<int> reconstructFloydPath(
        const FloydWarshallResult& result,
        int source,
        int destination
    ) const {
        PathStatus currentStatus =
            floydStatus(result, source, destination);

        if (currentStatus == PathStatus::NEGATIVE_INFINITY) {
            throw GraphError(
                "Path is undefined because a negative cycle is reachable."
            );
        }

        if (currentStatus == PathStatus::UNREACHABLE) {
            return {};
        }

        if (source == destination) {
            return {source};
        }

        vector<int> path = {source};
        int current = source;

        for (int i = 0; i < vertexCount; ++i) {
            current = result.next[current][destination];

            if (current == -1) {
                return {};
            }

            path.push_back(current);

            if (current == destination) {
                return path;
            }
        }

        throw GraphError("Path reconstruction exceeded vertex limit.");
    }
};

void printPath(const vector<int>& path) {
    if (path.empty()) {
        cout << "No path";
        return;
    }

    for (size_t i = 0; i < path.size(); ++i) {
        if (i > 0) {
            cout << " -> ";
        }

        cout << path[i];
    }
}

void printDistance(double distance) {
    if (distance == INF) {
        cout << "INF";
    } else {
        cout << distance;
    }
}

void demonstrateSingleSource() {
    cout << "\n=== BELLMAN-FORD ===\n";

    WeightedGraph graph(6);

    vector<Edge> input = {
        {0, 1, 4},
        {0, 2, 5},
        {1, 2, -2},
        {1, 3, 6},
        {2, 3, 3},
        {3, 4, 2},
        {4, 5, 1}
    };

    for (const Edge& edge : input) {
        graph.addEdge(edge.source, edge.destination, edge.weight);
    }

    BellmanFordResult result = graph.bellmanFord(0);

    for (int i = 0; i < graph.size(); ++i) {
        cout << "Vertex " << i << ": ";
        printDistance(result.distances[i]);
        cout << '\n';
    }

    cout << "Path 0 -> 5: ";
    printPath(graph.reconstructPath(result, 0, 5));
    cout << '\n';

    if (result.distances[5] != 8) {
        throw GraphError("Bellman-Ford verification failed.");
    }
}

void demonstrateNegativeCycle() {
    cout << "\n=== NEGATIVE CYCLE ===\n";

    WeightedGraph graph(6);

    vector<Edge> input = {
        {0, 1, 2},
        {1, 2, 2},
        {2, 3, -5},
        {3, 1, 1},
        {3, 4, 4},
        {0, 5, 10}
    };

    for (const Edge& edge : input) {
        graph.addEdge(edge.source, edge.destination, edge.weight);
    }

    BellmanFordResult result = graph.bellmanFord(0);

    cout << "Negative cycle: ";
    printPath(result.negativeCycle);
    cout << "\nAffected vertices: ";

    for (int i = 0; i < graph.size(); ++i) {
        if (result.affected[i]) {
            cout << i << ' ';
        }
    }

    cout << '\n';

    if (!result.affected[4] || result.affected[5]) {
        throw GraphError("Negative-cycle propagation failed.");
    }
}

void demonstrateAllPairs() {
    cout << "\n=== FLOYD-WARSHALL ===\n";

    WeightedGraph graph(5);

    vector<Edge> input = {
        {0, 1, 3},
        {0, 2, 10},
        {1, 2, -2},
        {1, 3, 7},
        {2, 3, 2},
        {3, 4, 1},
        {4, 1, 8}
    };

    for (const Edge& edge : input) {
        graph.addEdge(edge.source, edge.destination, edge.weight);
    }

    FloydWarshallResult result = graph.floydWarshall();

    for (const auto& row : result.distances) {
        for (double distance : row) {
            cout.width(6);
            printDistance(distance);
        }

        cout << '\n';
    }

    cout << "Path 0 -> 4: ";
    printPath(graph.reconstructFloydPath(result, 0, 4));
    cout << '\n';

    if (result.distances[0][4] != 4) {
        throw GraphError("Floyd-Warshall verification failed.");
    }
}

void demonstrateCrossValidation() {
    cout << "\n=== CROSS-VALIDATION ===\n";

    WeightedGraph graph(5);

    vector<Edge> input = {
        {0, 1, 6},
        {0, 2, 7},
        {1, 2, 8},
        {1, 3, 5},
        {1, 4, -4},
        {2, 3, -3},
        {2, 4, 9},
        {3, 1, -2},
        {4, 0, 2},
        {4, 3, 7}
    };

    for (const Edge& edge : input) {
        graph.addEdge(edge.source, edge.destination, edge.weight);
    }

    FloydWarshallResult allPairs = graph.floydWarshall();

    for (int source = 0; source < graph.size(); ++source) {
        BellmanFordResult singleSource = graph.bellmanFord(source);

        for (int destination = 0; destination < graph.size(); ++destination) {
            if (
                graph.status(singleSource, destination) ==
                PathStatus::FINITE
            ) {
                if (
                    singleSource.distances[destination] !=
                    allPairs.distances[source][destination]
                ) {
                    throw GraphError("Cross-validation mismatch.");
                }
            }
        }
    }

    cout << "Both algorithms produce consistent finite distances.\n";
}

int main() {
    try {
        cout << "GRAPH ALGORITHMS III\n";
        cout << "Bellman-Ford | Floyd-Warshall | Negative Cycles\n";

        demonstrateSingleSource();
        demonstrateNegativeCycle();
        demonstrateAllPairs();
        demonstrateCrossValidation();

        cout << "\nAll verification checks passed.\n";
    } catch (const exception& error) {
        cerr << "Execution error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
