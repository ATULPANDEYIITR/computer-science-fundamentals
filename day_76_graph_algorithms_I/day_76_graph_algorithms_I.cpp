#include <algorithm>
#include <iostream>
#include <map>
#include <queue>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>
#include <functional>
#include <limits>
#include <utility>

using namespace std;

enum class GraphType {
    Directed,
    Undirected
};

struct BFSResult {
    string source;
    map<string, int> distance;
    map<string, string> parent;

    vector<string> shortestPath(const string& target) const {
        if (distance.find(target) == distance.end()) {
            return {};
        }

        vector<string> path;
        string current = target;

        while (true) {
            path.push_back(current);

            auto it = parent.find(current);
            if (it == parent.end()) break;

            current = it->second;
        }

        reverse(path.begin(), path.end());
        return path;
    }
};

struct DFSResult {
    vector<string> discovery;
    vector<string> finish;
    bool hasCycle = false;
    vector<string> topologicalOrder;
};

class Graph {
private:
    GraphType type;
    map<string, set<string>> adjacency;

public:
    explicit Graph(GraphType graphType = GraphType::Undirected)
        : type(graphType) {}

    void addVertex(const string& vertex) {
        if (vertex.empty()) {
            throw invalid_argument("Vertex cannot be empty.");
        }

        adjacency.try_emplace(vertex);
    }

    void addEdge(const string& source, const string& target) {
        addVertex(source);
        addVertex(target);

        if (!adjacency[source].insert(target).second) {
            return;
        }

        if (type == GraphType::Undirected) {
            adjacency[target].insert(source);
        }
    }

    bool contains(const string& vertex) const {
        return adjacency.find(vertex) != adjacency.end();
    }

    void validate(const string& vertex) const {
        if (!contains(vertex)) {
            throw out_of_range("Unknown vertex: " + vertex);
        }
    }

    size_t vertexCount() const {
        return adjacency.size();
    }

    vector<string> vertices() const {
        vector<string> result;

        for (const auto& [vertex, neighbors] : adjacency) {
            result.push_back(vertex);
        }

        return result;
    }

    // ---------------------------------------------------------
    // 1. BREADTH-FIRST SEARCH
    // ---------------------------------------------------------

    BFSResult bfs(const string& source) const {
        validate(source);

        BFSResult result;
        result.source = source;

        queue<string> pending;

        pending.push(source);
        result.distance[source] = 0;
        result.parent[source] = "";

        while (!pending.empty()) {
            string current = pending.front();
            pending.pop();

            for (const string& neighbor : adjacency.at(current)) {
                if (result.distance.find(neighbor) ==
                    result.distance.end()) {

                    result.distance[neighbor] =
                        result.distance[current] + 1;

                    result.parent[neighbor] = current;
                    pending.push(neighbor);
                }
            }
        }

        return result;
    }

    vector<string> shortestPath(
        const string& source,
        const string& target
    ) const {
        validate(source);
        validate(target);

        return bfs(source).shortestPath(target);
    }

    map<string, int> multiSourceBFS(
        const vector<string>& sources
    ) const {
        map<string, int> distance;
        queue<string> pending;

        for (const string& source : sources) {
            validate(source);

            if (distance.emplace(source, 0).second) {
                pending.push(source);
            }
        }

        while (!pending.empty()) {
            string current = pending.front();
            pending.pop();

            for (const string& neighbor : adjacency.at(current)) {
                if (distance.find(neighbor) == distance.end()) {
                    distance[neighbor] = distance[current] + 1;
                    pending.push(neighbor);
                }
            }
        }

        return distance;
    }

    // ---------------------------------------------------------
    // 2. DEPTH-FIRST SEARCH
    // ---------------------------------------------------------

    DFSResult dfs() const {
        DFSResult result;

        unordered_set<string> visited;
        unordered_set<string> active;

        function<void(const string&, const string&)> visit =
            [&](const string& vertex, const string& parent) {

            visited.insert(vertex);
            active.insert(vertex);
            result.discovery.push_back(vertex);

            for (const string& neighbor : adjacency.at(vertex)) {
                if (!visited.count(neighbor)) {
                    visit(neighbor, vertex);
                } else if (type == GraphType::Directed) {
                    if (active.count(neighbor)) {
                        result.hasCycle = true;
                    }
                } else if (neighbor != parent) {
                    result.hasCycle = true;
                }
            }

            active.erase(vertex);
            result.finish.push_back(vertex);
        };

        for (const auto& [vertex, neighbors] : adjacency) {
            if (!visited.count(vertex)) {
                visit(vertex, "");
            }
        }

        if (type == GraphType::Directed && !result.hasCycle) {
            result.topologicalOrder = result.finish;
            reverse(
                result.topologicalOrder.begin(),
                result.topologicalOrder.end()
            );
        }

        return result;
    }

    // ---------------------------------------------------------
    // 3. CONNECTED COMPONENTS
    // ---------------------------------------------------------

    vector<vector<string>> connectedComponents() const {
        if (type != GraphType::Undirected) {
            throw logic_error(
                "Connected components require an undirected graph."
            );
        }

        unordered_set<string> visited;
        vector<vector<string>> components;

        for (const auto& [vertex, neighbors] : adjacency) {
            if (visited.count(vertex)) continue;

            vector<string> component;
            queue<string> pending;

            pending.push(vertex);
            visited.insert(vertex);

            while (!pending.empty()) {
                string current = pending.front();
                pending.pop();

                component.push_back(current);

                for (const string& neighbor : adjacency.at(current)) {
                    if (!visited.count(neighbor)) {
                        visited.insert(neighbor);
                        pending.push(neighbor);
                    }
                }
            }

            sort(component.begin(), component.end());
            components.push_back(move(component));
        }

        return components;
    }

    void printGraph() const {
        for (const auto& [vertex, neighbors] : adjacency) {
            cout << vertex << " -> ";

            for (const string& neighbor : neighbors) {
                cout << neighbor << " ";
            }

            cout << '\n';
        }
    }
};

// -------------------------------------------------------------
// Repository infrastructure example
// -------------------------------------------------------------

Graph buildInfrastructure() {
    Graph graph(GraphType::Undirected);

    vector<pair<string, string>> connections = {
        {"API", "Gateway"},
        {"Gateway", "Authentication"},
        {"Gateway", "Orders"},
        {"Orders", "Database"},
        {"Orders", "Cache"},
        {"Monitoring", "Logging"},
        {"Backup", "Storage"}
    };

    for (const auto& [source, target] : connections) {
        graph.addEdge(source, target);
    }

    graph.addVertex("OfflineNode");

    return graph;
}

Graph buildDependencyGraph() {
    Graph graph(GraphType::Directed);

    graph.addEdge("Core", "Authentication");
    graph.addEdge("Authentication", "API");
    graph.addEdge("API", "Frontend");
    graph.addEdge("Core", "Reporting");

    return graph;
}

void printPath(const vector<string>& path) {
    if (path.empty()) {
        cout << "No path exists\n";
        return;
    }

    for (size_t i = 0; i < path.size(); ++i) {
        if (i) cout << " -> ";
        cout << path[i];
    }

    cout << '\n';
}

void demonstrateBFS(const Graph& graph) {
    cout << "\n=== BREADTH-FIRST SEARCH ===\n";

    BFSResult result = graph.bfs("API");

    cout << "Shortest path API -> Database: ";
    printPath(result.shortestPath("Database"));

    cout << "Shortest path API -> OfflineNode: ";
    printPath(result.shortestPath("OfflineNode"));

    cout << "Distances:\n";

    for (const auto& [vertex, distance] : result.distance) {
        cout << "  " << vertex << ": " << distance << '\n';
    }

    auto multi = graph.multiSourceBFS({"API", "Monitoring"});

    cout << "Multi-source distances:\n";

    for (const auto& [vertex, distance] : multi) {
        cout << "  " << vertex << ": " << distance << '\n';
    }
}

void demonstrateDFS(const Graph& graph) {
    cout << "\n=== DEPTH-FIRST SEARCH ===\n";

    DFSResult result = graph.dfs();

    cout << "Discovery order: ";
    for (const auto& vertex : result.discovery) {
        cout << vertex << " ";
    }

    cout << "\nCycle detected: "
         << boolalpha << result.hasCycle << '\n';

    Graph dependencies = buildDependencyGraph();
    DFSResult dependencyResult = dependencies.dfs();

    cout << "Dependency topological order: ";

    for (const auto& vertex : dependencyResult.topologicalOrder) {
        cout << vertex << " ";
    }

    cout << '\n';

    Graph cyclic(GraphType::Directed);
    cyclic.addEdge("A", "B");
    cyclic.addEdge("B", "C");
    cyclic.addEdge("C", "A");

    cout << "Cyclic dependency detected: "
         << cyclic.dfs().hasCycle << '\n';
}

void demonstrateComponents(const Graph& graph) {
    cout << "\n=== CONNECTED COMPONENTS ===\n";

    auto components = graph.connectedComponents();

    cout << "Number of components: " << components.size() << '\n';

    size_t largest = 0;

    for (size_t i = 0; i < components.size(); ++i) {
        cout << "Component " << i + 1 << ": ";

        for (const auto& vertex : components[i]) {
            cout << vertex << " ";
        }

        largest = max(largest, components[i].size());
        cout << '\n';
    }

    cout << "Largest component size: " << largest << '\n';
}

// -------------------------------------------------------------
// Automated tests
// -------------------------------------------------------------

void runTests() {
    Graph graph;

    graph.addEdge("A", "B");
    graph.addEdge("B", "C");
    graph.addVertex("D");

    auto path = graph.shortestPath("A", "C");

    if (path != vector<string>{"A", "B", "C"}) {
        throw runtime_error("BFS shortest path test failed.");
    }

    if (!graph.shortestPath("A", "D").empty()) {
        throw runtime_error("Unreachable path test failed.");
    }

    if (graph.connectedComponents().size() != 2) {
        throw runtime_error("Connected components test failed.");
    }

    Graph directed(GraphType::Directed);
    directed.addEdge("A", "B");
    directed.addEdge("B", "C");

    DFSResult result = directed.dfs();

    if (result.hasCycle) {
        throw runtime_error("Acyclic graph incorrectly marked cyclic.");
    }

    Graph cyclic(GraphType::Directed);
    cyclic.addEdge("A", "B");
    cyclic.addEdge("B", "C");
    cyclic.addEdge("C", "A");

    if (!cyclic.dfs().hasCycle) {
        throw runtime_error("Cycle detection test failed.");
    }

    auto multi = graph.multiSourceBFS({"A", "D"});

    if (multi.at("C") != 2) {
        throw runtime_error("Multi-source BFS test failed.");
    }

    bool exceptionRaised = false;

    try {
        graph.bfs("UNKNOWN");
    } catch (const out_of_range&) {
        exceptionRaised = true;
    }

    if (!exceptionRaised) {
        throw runtime_error("Invalid vertex validation failed.");
    }

    cout << "All C++17 tests passed.\n";
}

int main() {
    try {
        cout << "GRAPH ALGORITHMS I\n";
        cout << "==================\n";

        Graph infrastructure = buildInfrastructure();

        cout << "\nInfrastructure graph:\n";
        infrastructure.printGraph();

        demonstrateBFS(infrastructure);
        demonstrateDFS(infrastructure);
        demonstrateComponents(infrastructure);

        cout << "\n=== VALIDATION ===\n";
        runTests();

    } catch (const exception& error) {
        cerr << "Execution error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
