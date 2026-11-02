#include <algorithm>
#include <cmath>
#include <exception>
#include <iomanip>
#include <iostream>
#include <limits>
#include <queue>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

enum class GraphKind {
    Directed,
    Undirected
};

struct Edge {
    std::string source;
    std::string target;
    double weight;
};

class GraphError : public std::runtime_error {
public:
    explicit GraphError(const std::string& message)
        : std::runtime_error(message) {}
};

class WeightedGraph {
private:
    GraphKind kind;
    std::unordered_map<std::string, std::vector<std::pair<std::string, double>>> adjacency;

    void validateVertex(const std::string& vertex) const {
        if (vertex.empty()) {
            throw GraphError("Vertex name cannot be empty.");
        }
    }

public:
    explicit WeightedGraph(GraphKind graphKind)
        : kind(graphKind) {}

    void addVertex(const std::string& vertex) {
        validateVertex(vertex);
        adjacency.try_emplace(vertex);
    }

    void addEdge(
        const std::string& source,
        const std::string& target,
        double weight
    ) {
        validateVertex(source);
        validateVertex(target);

        if (!std::isfinite(weight) || weight < 0.0) {
            throw GraphError("Weight must be finite and non-negative.");
        }

        addVertex(source);
        addVertex(target);

        auto update = [&](const std::string& from, const std::string& to) {
            auto& edges = adjacency[from];

            for (auto& [neighbor, existingWeight] : edges) {
                if (neighbor == to) {
                    existingWeight = weight;
                    return;
                }
            }

            edges.emplace_back(to, weight);
        };

        update(source, target);

        if (kind == GraphKind::Undirected) {
            update(target, source);
        }
    }

    std::vector<std::string> vertices() const {
        std::vector<std::string> result;

        for (const auto& [vertex, _] : adjacency) {
            result.push_back(vertex);
        }

        std::sort(result.begin(), result.end());
        return result;
    }

    std::vector<Edge> edges() const {
        std::vector<Edge> result;

        for (const auto& [source, targets] : adjacency) {
            for (const auto& [target, weight] : targets) {
                result.push_back({source, target, weight});
            }
        }

        std::sort(result.begin(), result.end(),
                  [](const Edge& a, const Edge& b) {
                      if (a.source != b.source) {
                          return a.source < b.source;
                      }
                      return a.target < b.target;
                  });

        return result;
    }

    std::vector<std::string> bfs(const std::string& start) const {
        if (!adjacency.contains(start)) {
            throw GraphError("Unknown start vertex: " + start);
        }

        std::queue<std::string> queue;
        std::unordered_set<std::string> visited;
        std::vector<std::string> order;

        queue.push(start);
        visited.insert(start);

        while (!queue.empty()) {
            std::string current = queue.front();
            queue.pop();
            order.push_back(current);

            std::vector<std::string> neighbors;
            for (const auto& [neighbor, _] : adjacency.at(current)) {
                neighbors.push_back(neighbor);
            }

            std::sort(neighbors.begin(), neighbors.end());

            for (const auto& neighbor : neighbors) {
                if (visited.insert(neighbor).second) {
                    queue.push(neighbor);
                }
            }
        }

        return order;
    }

    std::vector<std::string> dfs(const std::string& start) const {
        if (!adjacency.contains(start)) {
            throw GraphError("Unknown start vertex: " + start);
        }

        std::unordered_set<std::string> visited;
        std::vector<std::string> order;

        std::function<void(const std::string&)> visit =
            [&](const std::string& vertex) {
                visited.insert(vertex);
                order.push_back(vertex);

                std::vector<std::string> neighbors;
                for (const auto& [neighbor, _] : adjacency.at(vertex)) {
                    neighbors.push_back(neighbor);
                }

                std::sort(neighbors.begin(), neighbors.end());

                for (const auto& neighbor : neighbors) {
                    if (!visited.contains(neighbor)) {
                        visit(neighbor);
                    }
                }
            };

        visit(start);
        return order;
    }

    std::pair<
        std::unordered_map<std::string, double>,
        std::unordered_map<std::string, std::string>
    > dijkstra(const std::string& start) const {
        if (!adjacency.contains(start)) {
            throw GraphError("Unknown start vertex: " + start);
        }

        const double infinity = std::numeric_limits<double>::infinity();

        std::unordered_map<std::string, double> distance;
        std::unordered_map<std::string, std::string> previous;

        for (const auto& [vertex, _] : adjacency) {
            distance[vertex] = infinity;
        }

        distance[start] = 0.0;

        using QueueItem = std::pair<double, std::string>;
        std::priority_queue<
            QueueItem,
            std::vector<QueueItem>,
            std::greater<>
        > queue;

        queue.push({0.0, start});

        while (!queue.empty()) {
            auto [currentDistance, current] = queue.top();
            queue.pop();

            if (currentDistance > distance[current]) {
                continue;
            }

            for (const auto& [neighbor, weight] : adjacency.at(current)) {
                const double candidate = currentDistance + weight;

                if (candidate < distance[neighbor]) {
                    distance[neighbor] = candidate;
                    previous[neighbor] = current;
                    queue.push({candidate, neighbor});
                }
            }
        }

        return {distance, previous};
    }

    std::pair<std::vector<std::string>, double> shortestPath(
        const std::string& start,
        const std::string& target
    ) const {
        auto [distance, previous] = dijkstra(start);

        if (!adjacency.contains(target)) {
            throw GraphError("Unknown target vertex: " + target);
        }

        if (std::isinf(distance[target])) {
            return {{}, std::numeric_limits<double>::infinity()};
        }

        std::vector<std::string> path;

        for (std::string current = target; !current.empty();) {
            path.push_back(current);

            auto iterator = previous.find(current);
            if (iterator == previous.end()) {
                break;
            }

            current = iterator->second;
        }

        std::reverse(path.begin(), path.end());
        return {path, distance[target]};
    }

    std::vector<std::string> topologicalSort() const {
        if (kind != GraphKind::Directed) {
            throw GraphError("Topological sort requires a directed graph.");
        }

        std::unordered_map<std::string, int> indegree;

        for (const auto& [vertex, _] : adjacency) {
            indegree[vertex] = 0;
        }

        for (const auto& [_, targets] : adjacency) {
            for (const auto& [target, _] : targets) {
                ++indegree[target];
            }
        }

        std::priority_queue<
            std::string,
            std::vector<std::string>,
            std::greater<>
        > ready;

        for (const auto& [vertex, degree] : indegree) {
            if (degree == 0) {
                ready.push(vertex);
            }
        }

        std::vector<std::string> order;

        while (!ready.empty()) {
            const std::string current = ready.top();
            ready.pop();
            order.push_back(current);

            for (const auto& [neighbor, _] : adjacency.at(current)) {
                if (--indegree[neighbor] == 0) {
                    ready.push(neighbor);
                }
            }
        }

        if (order.size() != adjacency.size()) {
            throw GraphError("Graph contains a cycle.");
        }

        return order;
    }

    bool hasCycle() const {
        if (kind == GraphKind::Undirected) {
            std::unordered_set<std::string> visited;

            std::function<bool(const std::string&, const std::string&)> visit =
                [&](const std::string& vertex, const std::string& parent) {
                    visited.insert(vertex);

                    for (const auto& [neighbor, _] : adjacency.at(vertex)) {
                        if (!visited.contains(neighbor)) {
                            if (visit(neighbor, vertex)) {
                                return true;
                            }
                        } else if (neighbor != parent) {
                            return true;
                        }
                    }

                    return false;
                };

            for (const auto& [vertex, _] : adjacency) {
                if (!visited.contains(vertex) && visit(vertex, "")) {
                    return true;
                }
            }

            return false;
        }

        std::unordered_set<std::string> visiting;
        std::unordered_set<std::string> visited;

        std::function<bool(const std::string&)> visit =
            [&](const std::string& vertex) {
                if (visiting.contains(vertex)) {
                    return true;
                }

                if (visited.contains(vertex)) {
                    return false;
                }

                visiting.insert(vertex);

                for (const auto& [neighbor, _] : adjacency.at(vertex)) {
                    if (visit(neighbor)) {
                        return true;
                    }
                }

                visiting.erase(vertex);
                visited.insert(vertex);
                return false;
            };

        for (const auto& [vertex, _] : adjacency) {
            if (!visited.contains(vertex) && visit(vertex)) {
                return true;
            }
        }

        return false;
    }
};

static void printPath(const std::vector<std::string>& path) {
    for (std::size_t i = 0; i < path.size(); ++i) {
        if (i > 0) {
            std::cout << " -> ";
        }
        std::cout << path[i];
    }
    std::cout << '\n';
}

int main() {
    try {
        WeightedGraph network(GraphKind::Directed);

        const std::vector<Edge> routes = {
            {"Lucknow", "Kanpur", 1.5},
            {"Lucknow", "Ayodhya", 2.0},
            {"Kanpur", "Agra", 3.0},
            {"Ayodhya", "Varanasi", 2.5},
            {"Agra", "Delhi", 2.0},
            {"Varanasi", "Patna", 4.0},
            {"Delhi", "Jaipur", 3.0},
            {"Delhi", "Patna", 5.0},
            {"Jaipur", "Ahmedabad", 4.0},
            {"Patna", "Kolkata", 5.0},
            {"Ahmedabad", "Mumbai", 6.0},
            {"Kolkata", "Guwahati", 7.0},
            {"Mumbai", "Bengaluru", 7.0}
        };

        for (const auto& edge : routes) {
            network.addEdge(edge.source, edge.target, edge.weight);
        }

        std::cout << "DIRECTED WEIGHTED GRAPH\n";
        std::cout << "=======================\n\n";

        std::cout << "Edges:\n";
        for (const auto& edge : network.edges()) {
            std::cout << "  " << edge.source << " -> "
                      << edge.target << " ("
                      << edge.weight << " hours)\n";
        }

        std::cout << "\nBFS from Lucknow:\n";
        printPath(network.bfs("Lucknow"));

        std::cout << "\nDFS from Lucknow:\n";
        printPath(network.dfs("Lucknow"));

        auto [path, distance] = network.shortestPath("Lucknow", "Mumbai");

        std::cout << "\nShortest route to Mumbai:\n";
        printPath(path);
        std::cout << std::fixed << std::setprecision(1)
                  << "Travel time: " << distance << " hours\n";

        std::cout << "\nCycle present: "
                  << std::boolalpha << network.hasCycle() << '\n';

        WeightedGraph workflow(GraphKind::Directed);
        workflow.addEdge("Design", "Implement", 1);
        workflow.addEdge("Implement", "Test", 1);
        workflow.addEdge("Test", "Deploy", 1);

        std::cout << "\nTopological workflow:\n";
        printPath(workflow.topologicalSort());

        workflow.addEdge("Deploy", "Design", 1);

        try {
            workflow.topologicalSort();
        } catch (const GraphError& error) {
            std::cout << "Cycle validation: "
                      << error.what() << '\n';
        }

        try {
            network.addEdge("Delhi", "Mumbai", -2.0);
        } catch (const GraphError& error) {
            std::cout << "Weight validation: "
                      << error.what() << '\n';
        }

        auto shortest = network.shortestPath("Lucknow", "Mumbai");
        if (std::fabs(shortest.second - 18.5) > 1e-9) {
            throw GraphError("Shortest-path validation failed.");
        }

        std::cout << "\nComplexity:\n";
        std::cout << "  Adjacency-list storage: O(V + E)\n";
        std::cout << "  BFS/DFS: O(V + E)\n";
        std::cout << "  Dijkstra: O((V + E) log V)\n";
        std::cout << "  Topological sort: O(V + E)\n";
        std::cout << "  Non-negative weights are required by Dijkstra.\n";

    } catch (const std::exception& error) {
        std::cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
