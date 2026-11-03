#include <algorithm>
#include <cassert>
#include <iostream>
#include <optional>
#include <queue>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

/*
 * Graph Traversal: emergency transport network.
 *
 * C++17 implementation featuring:
 * - Undirected adjacency-list graph
 * - Open and closed road segments
 * - BFS for minimum-hop emergency routes
 * - DFS for systematic network inspection
 * - Connected components after road closures
 * - Path reconstruction
 * - Input and graph-invariant validation
 *
 * Compile:
 *   g++ -std=c++17 -O2 -Wall -Wextra -pedantic graph_traversal.cpp -o graph_traversal
 *
 * Run:
 *   ./graph_traversal
 */

struct TraversalResult {
    std::vector<int> order;
    std::vector<int> parent;
    std::vector<int> depth;

    std::optional<std::vector<int>> pathTo(int target) const {
        if (target < 0 || target >= static_cast<int>(parent.size())) {
            throw std::out_of_range("Target vertex is outside the graph.");
        }

        if (depth[target] == -1) {
            return std::nullopt;
        }

        std::vector<int> path;
        int current = target;

        while (current != -1) {
            path.push_back(current);
            current = parent[current];
        }

        std::reverse(path.begin(), path.end());
        return path;
    }
};

class RoadNetwork {
private:
    std::vector<std::string> labels_;
    std::vector<std::vector<int>> adjacency_;

    // Each undirected road is represented once in this set.
    std::set<std::pair<int, int>> closed_roads_;

    void validateVertex(int vertex) const {
        if (vertex < 0 || vertex >= static_cast<int>(labels_.size())) {
            throw std::out_of_range(
                "Invalid vertex identifier: " + std::to_string(vertex)
            );
        }
    }

    static std::pair<int, int> normalizedEdge(int first, int second) {
        return {std::min(first, second), std::max(first, second)};
    }

    bool containsRoad(int first, int second) const {
        const auto& neighbors = adjacency_[first];

        return std::binary_search(
            neighbors.begin(),
            neighbors.end(),
            second
        );
    }

    bool isRoadOpen(int first, int second) const {
        return closed_roads_.find(
            normalizedEdge(first, second)
        ) == closed_roads_.end();
    }

    void insertSorted(int vertex, int neighbor) {
        auto& neighbors = adjacency_[vertex];

        const auto position = std::lower_bound(
            neighbors.begin(),
            neighbors.end(),
            neighbor
        );

        if (position != neighbors.end() && *position == neighbor) {
            throw std::invalid_argument("Duplicate road segment.");
        }

        neighbors.insert(position, neighbor);
    }

public:
    explicit RoadNetwork(std::vector<std::string> labels)
        : labels_(std::move(labels)),
          adjacency_(labels_.size()) {

        if (labels_.empty()) {
            throw std::invalid_argument(
                "A road network must contain at least one location."
            );
        }

        for (const auto& label : labels_) {
            if (label.empty() || label.size() > 128) {
                throw std::invalid_argument(
                    "Location labels must contain 1 to 128 characters."
                );
            }
        }
    }

    int size() const {
        return static_cast<int>(labels_.size());
    }

    const std::string& label(int vertex) const {
        validateVertex(vertex);
        return labels_[vertex];
    }

    void addRoad(int first, int second) {
        validateVertex(first);
        validateVertex(second);

        if (first == second) {
            throw std::invalid_argument(
                "Self-loop roads are not permitted in this network."
            );
        }

        if (containsRoad(first, second)) {
            throw std::invalid_argument("Duplicate road segment.");
        }

        insertSorted(first, second);
        insertSorted(second, first);
    }

    void setRoadOpen(int first, int second, bool open) {
        validateVertex(first);
        validateVertex(second);

        if (!containsRoad(first, second)) {
            throw std::invalid_argument(
                "Cannot change the status of a road that does not exist."
            );
        }

        const auto edge = normalizedEdge(first, second);

        if (open) {
            closed_roads_.erase(edge);
        } else {
            closed_roads_.insert(edge);
        }
    }

    bool roadIsOpen(int first, int second) const {
        validateVertex(first);
        validateVertex(second);

        if (!containsRoad(first, second)) {
            throw std::invalid_argument("Road segment does not exist.");
        }

        return isRoadOpen(first, second);
    }

    TraversalResult breadthFirstSearch(int start) const {
        validateVertex(start);

        const int count = size();

        TraversalResult result{
            {},
            std::vector<int>(count, -1),
            std::vector<int>(count, -1)
        };

        std::vector<bool> discovered(count, false);
        std::queue<int> pending;

        discovered[start] = true;
        result.parent[start] = -1;
        result.depth[start] = 0;

        pending.push(start);

        while (!pending.empty()) {
            const int current = pending.front();
            pending.pop();

            result.order.push_back(current);

            for (const int neighbor : adjacency_[current]) {
                if (!isRoadOpen(current, neighbor)) {
                    continue;
                }

                if (discovered[neighbor]) {
                    continue;
                }

                // Mark on enqueue, not dequeue, to prevent duplicate work.
                discovered[neighbor] = true;
                result.parent[neighbor] = current;
                result.depth[neighbor] = result.depth[current] + 1;

                pending.push(neighbor);
            }
        }

        return result;
    }

    TraversalResult depthFirstSearch(int start) const {
        validateVertex(start);

        const int count = size();

        TraversalResult result{
            {},
            std::vector<int>(count, -1),
            std::vector<int>(count, -1)
        };

        struct Frame {
            int vertex;
            std::size_t nextNeighbor;
        };

        std::vector<bool> discovered(count, false);
        std::vector<Frame> stack;

        discovered[start] = true;
        result.parent[start] = -1;
        result.depth[start] = 0;
        result.order.push_back(start);

        stack.push_back({start, 0});

        while (!stack.empty()) {
            Frame& frame = stack.back();
            const auto& neighbors = adjacency_[frame.vertex];

            bool advanced = false;

            while (frame.nextNeighbor < neighbors.size()) {
                const int neighbor = neighbors[frame.nextNeighbor++];

                if (!isRoadOpen(frame.vertex, neighbor)) {
                    continue;
                }

                if (discovered[neighbor]) {
                    continue;
                }

                discovered[neighbor] = true;
                result.parent[neighbor] = frame.vertex;
                result.depth[neighbor] = result.depth[frame.vertex] + 1;
                result.order.push_back(neighbor);

                stack.push_back({neighbor, 0});
                advanced = true;
                break;
            }

            if (!advanced) {
                stack.pop_back();
            }
        }

        return result;
    }

    std::optional<std::vector<int>> shortestRoute(
        int start,
        int destination
    ) const {
        validateVertex(start);
        validateVertex(destination);

        const TraversalResult result = breadthFirstSearch(start);
        return result.pathTo(destination);
    }

    std::vector<std::vector<int>> connectedComponents() const {
        std::vector<bool> visited(size(), false);
        std::vector<std::vector<int>> components;

        for (int vertex = 0; vertex < size(); ++vertex) {
            if (visited[vertex]) {
                continue;
            }

            const TraversalResult component =
                breadthFirstSearch(vertex);

            components.push_back(component.order);

            for (const int member : component.order) {
                visited[member] = true;
            }
        }

        return components;
    }

    void printTraversal(
        const std::string& title,
        const TraversalResult& result
    ) const {
        std::cout << "\n" << title << "\n";

        for (std::size_t index = 0; index < result.order.size(); ++index) {
            if (index > 0) {
                std::cout << " -> ";
            }

            std::cout << label(result.order[index]);
        }

        std::cout << "\n";
    }

    void printPath(
        const std::string& title,
        const std::optional<std::vector<int>>& path
    ) const {
        std::cout << title << ": ";

        if (!path.has_value()) {
            std::cout << "No available route\n";
            return;
        }

        for (std::size_t index = 0; index < path->size(); ++index) {
            if (index > 0) {
                std::cout << " -> ";
            }

            std::cout << label((*path)[index]);
        }

        std::cout << "\n";
    }

    void printComponents() const {
        const auto components = connectedComponents();

        std::cout << "\nConnected components: "
                  << components.size() << "\n";

        for (std::size_t index = 0; index < components.size(); ++index) {
            std::cout << "Component " << index + 1 << ": ";

            for (std::size_t position = 0;
                 position < components[index].size();
                 ++position) {

                if (position > 0) {
                    std::cout << ", ";
                }

                std::cout << label(components[index][position]);
            }

            std::cout << "\n";
        }
    }
};

int main() {
    try {
        RoadNetwork network({
            "Dispatch Center",
            "West Junction",
            "East Junction",
            "West Shelter",
            "Central Bridge",
            "South Shelter",
            "Supply Depot",
            "Remote Outpost"
        });

        network.addRoad(0, 1);
        network.addRoad(0, 2);
        network.addRoad(1, 3);
        network.addRoad(1, 4);
        network.addRoad(2, 4);
        network.addRoad(4, 5);
        network.addRoad(5, 6);
        network.addRoad(2, 7);

        /*
         * Both access roads to Central Bridge are closed.
         * The bridge, shelter, and depot form a separate component.
         */
        network.setRoadOpen(1, 4, false);
        network.setRoadOpen(2, 4, false);

        const auto bfs = network.breadthFirstSearch(0);
        const auto dfs = network.depthFirstSearch(0);

        std::cout << "EMERGENCY TRANSPORT NETWORK\n";

        network.printTraversal("BFS reachable locations", bfs);
        network.printTraversal("DFS inspection order", dfs);

        network.printPath(
            "\nShortest available route to West Shelter",
            network.shortestRoute(0, 3)
        );

        network.printPath(
            "Shortest available route to South Shelter",
            network.shortestRoute(0, 5)
        );

        network.printComponents();

        // The closed bridge separates the south area from dispatch.
        assert(bfs.depth[3] == 2);
        assert(bfs.depth[5] == -1);
        assert(bfs.depth[6] == -1);
        assert(network.connectedComponents().size() == 2);

        const auto route = network.shortestRoute(0, 3);
        assert(route.has_value());
        assert(route->size() == 3);

        const auto unavailableRoute = network.shortestRoute(0, 5);
        assert(!unavailableRoute.has_value());

        std::cout << "\nAll network traversal checks passed.\n";
    }
    catch (const std::exception& error) {
        std::cerr << "Network processing failed: "
                  << error.what() << "\n";
        return 1;
    }

    return 0;
}
