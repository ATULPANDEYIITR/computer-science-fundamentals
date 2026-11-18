#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <queue>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace std;

struct Edge {
    int source;
    int target;
    double weight;

    bool operator<(const Edge& other) const {
        if (weight != other.weight) {
            return weight < other.weight;
        }

        if (source != other.source) {
            return source < other.source;
        }

        return target < other.target;
    }
};

enum class Algorithm {
    KRUSKAL,
    PRIM
};

struct MSTResult {
    Algorithm algorithm;
    vector<Edge> selectedEdges;
    double totalWeight = 0.0;
    int components = 0;
    int vertices = 0;

    bool isSpanningTree() const {
        return vertices > 0 &&
               components == 1 &&
               static_cast<int>(selectedEdges.size()) == vertices - 1;
    }

    bool isSpanningForest() const {
        return static_cast<int>(selectedEdges.size()) ==
               vertices - components;
    }
};

class DisjointSet {
private:
    vector<int> parent;
    vector<int> rank;

    int componentCount;

public:
    explicit DisjointSet(int n)
        : parent(n), rank(n, 0), componentCount(n) {

        iota(parent.begin(), parent.end(), 0);
    }

    int find(int vertex) {
        if (vertex < 0 ||
            vertex >= static_cast<int>(parent.size())) {
            throw out_of_range("Invalid vertex index.");
        }

        while (parent[vertex] != vertex) {
            parent[vertex] = parent[parent[vertex]];
            vertex = parent[vertex];
        }

        return vertex;
    }

    bool unite(int a, int b) {
        a = find(a);
        b = find(b);

        if (a == b) {
            return false;
        }

        if (rank[a] < rank[b]) {
            swap(a, b);
        }

        parent[b] = a;

        if (rank[a] == rank[b]) {
            rank[a]++;
        }

        componentCount--;
        return true;
    }

    bool connected(int a, int b) {
        return find(a) == find(b);
    }

    int components() const {
        return componentCount;
    }
};

class WeightedGraph {
private:
    vector<string> names;
    unordered_map<string, int> indices;
    vector<Edge> edges;
    vector<vector<pair<int, double>>> adjacency;
    unordered_set<string> edgeKeys;

    static string edgeKey(int a, int b) {
        if (a > b) {
            swap(a, b);
        }

        return to_string(a) + ":" + to_string(b);
    }

    int getIndex(const string& name) const {
        auto it = indices.find(name);

        if (it == indices.end()) {
            throw invalid_argument("Unknown vertex: " + name);
        }

        return it->second;
    }

public:
    explicit WeightedGraph(const vector<string>& vertices)
        : names(vertices), adjacency(vertices.size()) {

        if (vertices.empty()) {
            throw invalid_argument("Graph must contain vertices.");
        }

        for (int i = 0; i < static_cast<int>(vertices.size()); i++) {
            if (vertices[i].empty()) {
                throw invalid_argument("Empty vertex name.");
            }

            if (!indices.emplace(vertices[i], i).second) {
                throw invalid_argument("Duplicate vertex name.");
            }
        }
    }

    int vertexCount() const {
        return static_cast<int>(names.size());
    }

    const vector<Edge>& getEdges() const {
        return edges;
    }

    void addEdge(
        const string& source,
        const string& target,
        double weight
    ) {
        int u = getIndex(source);
        int v = getIndex(target);

        if (u == v) {
            throw invalid_argument("Self-loops are not allowed.");
        }

        if (!isfinite(weight)) {
            throw invalid_argument("Weight must be finite.");
        }

        string key = edgeKey(u, v);

        if (edgeKeys.count(key)) {
            throw invalid_argument("Duplicate undirected edge.");
        }

        edgeKeys.insert(key);

        edges.push_back({u, v, weight});
        adjacency[u].push_back({v, weight});
        adjacency[v].push_back({u, weight});
    }

    MSTResult kruskal() const {
        vector<Edge> sortedEdges = edges;
        sort(sortedEdges.begin(), sortedEdges.end());

        DisjointSet dsu(vertexCount());

        MSTResult result{
            Algorithm::KRUSKAL,
            {},
            0.0,
            vertexCount(),
            vertexCount()
        };

        for (const Edge& edge : sortedEdges) {
            if (dsu.unite(edge.source, edge.target)) {
                result.selectedEdges.push_back(edge);
                result.totalWeight += edge.weight;

                if (static_cast<int>(
                    result.selectedEdges.size()
                ) == vertexCount() - 1) {
                    break;
                }
            }
        }

        result.components = dsu.components();
        return result;
    }

    MSTResult prim(int start = 0) const {
        if (start < 0 || start >= vertexCount()) {
            throw out_of_range("Invalid starting vertex.");
        }

        using HeapEntry = tuple<double, int, int>;

        priority_queue<
            HeapEntry,
            vector<HeapEntry>,
            greater<HeapEntry>
        > heap;

        vector<bool> visited(vertexCount(), false);

        MSTResult result{
            Algorithm::PRIM,
            {},
            0.0,
            vertexCount(),
            vertexCount()
        };

        vector<int> roots;
        roots.push_back(start);

        for (int i = 0; i < vertexCount(); i++) {
            if (i != start) {
                roots.push_back(i);
            }
        }

        for (int root : roots) {
            if (visited[root]) {
                continue;
            }

            visited[root] = true;

            for (const auto& [neighbor, weight] : adjacency[root]) {
                heap.push({weight, root, neighbor});
            }

            while (!heap.empty()) {
                auto [weight, source, target] = heap.top();
                heap.pop();

                if (visited[target]) {
                    continue;
                }

                visited[target] = true;

                result.selectedEdges.push_back({
                    source,
                    target,
                    weight
                });

                result.totalWeight += weight;

                for (const auto& [neighbor, nextWeight] :
                     adjacency[target]) {

                    if (!visited[neighbor]) {
                        heap.push({
                            nextWeight,
                            target,
                            neighbor
                        });
                    }
                }
            }
        }

        result.components =
            vertexCount() -
            static_cast<int>(result.selectedEdges.size());

        return result;
    }

    bool verify(const MSTResult& result) const {
        if (result.vertices != vertexCount()) {
            return false;
        }

        DisjointSet original(vertexCount());
        DisjointSet candidate(vertexCount());

        for (const Edge& edge : edges) {
            original.unite(edge.source, edge.target);
        }

        double calculatedWeight = 0.0;

        for (const Edge& edge : result.selectedEdges) {
            if (!candidate.unite(edge.source, edge.target)) {
                return false;
            }

            calculatedWeight += edge.weight;
        }

        return (
            candidate.components() == original.components() &&
            candidate.components() == result.components &&
            result.selectedEdges.size() ==
                static_cast<size_t>(
                    vertexCount() - candidate.components()
                ) &&
            abs(calculatedWeight - result.totalWeight) < 1e-9
        );
    }

    void display(const MSTResult& result) const {
        cout << "\n"
             << (result.algorithm == Algorithm::KRUSKAL
                 ? "Kruskal"
                 : "Prim")
             << " result\n";

        cout << string(45, '-') << '\n';

        for (const Edge& edge : result.selectedEdges) {
            cout << names[edge.source]
                 << " -- "
                 << names[edge.target]
                 << " : "
                 << edge.weight
                 << '\n';
        }

        cout << "Total weight: " << result.totalWeight << '\n';
        cout << "Components: " << result.components << '\n';
        cout << "Selected edges: "
             << result.selectedEdges.size() << '\n';
        cout << "Spanning tree: "
             << boolalpha << result.isSpanningTree() << '\n';
        cout << "Spanning forest: "
             << result.isSpanningForest() << '\n';
        cout << "Verified: " << verify(result) << '\n';
    }
};

void demonstrateUnionFind() {
    cout << "\nUNION-FIND DEMONSTRATION\n";

    DisjointSet dsu(5);

    dsu.unite(0, 1);
    dsu.unite(2, 3);

    cout << "0 connected to 1: "
         << dsu.connected(0, 1) << '\n';

    cout << "0 connected to 2: "
         << dsu.connected(0, 2) << '\n';

    dsu.unite(1, 2);

    cout << "0 connected to 3: "
         << dsu.connected(0, 3) << '\n';

    cout << "Components: " << dsu.components() << '\n';
}

void testAlgorithms() {
    WeightedGraph graph({"A", "B", "C", "D", "E", "F"});

    graph.addEdge("A", "B", 4);
    graph.addEdge("A", "C", 3);
    graph.addEdge("B", "C", 1);
    graph.addEdge("B", "D", 2);
    graph.addEdge("C", "D", 4);
    graph.addEdge("C", "E", 5);
    graph.addEdge("D", "E", 2);
    graph.addEdge("D", "F", 6);
    graph.addEdge("E", "F", 3);

    MSTResult kruskal = graph.kruskal();
    MSTResult prim = graph.prim();

    if (!graph.verify(kruskal) ||
        !graph.verify(prim) ||
        abs(kruskal.totalWeight - prim.totalWeight) > 1e-9) {
        throw runtime_error("MST verification failed.");
    }

    if (!kruskal.isSpanningTree()) {
        throw runtime_error("Expected a spanning tree.");
    }

    WeightedGraph negative({"A", "B", "C"});
    negative.addEdge("A", "B", -5);
    negative.addEdge("B", "C", 2);
    negative.addEdge("A", "C", 4);

    if (abs(negative.kruskal().totalWeight - (-3)) > 1e-9) {
        throw runtime_error("Negative weight test failed.");
    }

    WeightedGraph disconnected({"A", "B", "C", "D"});
    disconnected.addEdge("A", "B", 2);
    disconnected.addEdge("C", "D", 1);

    MSTResult forest = disconnected.kruskal();

    if (forest.components != 2 ||
        !forest.isSpanningForest() ||
        forest.isSpanningTree()) {
        throw runtime_error("Disconnected graph test failed.");
    }

    WeightedGraph singleton({"A"});

    if (!singleton.kruskal().isSpanningTree() ||
        !singleton.prim().isSpanningTree()) {
        throw runtime_error("Singleton graph test failed.");
    }

    bool duplicateRejected = false;

    try {
        graph.addEdge("B", "A", 10);
    } catch (const invalid_argument&) {
        duplicateRejected = true;
    }

    if (!duplicateRejected) {
        throw runtime_error("Duplicate edge validation failed.");
    }

    cout << "\nAll C++17 tests passed.\n";
}

int main() {
    try {
        cout << fixed << setprecision(2);

        WeightedGraph graph({
            "Warehouse",
            "Factory",
            "Office",
            "Distribution",
            "DataCenter"
        });

        graph.addEdge("Warehouse", "Factory", 12);
        graph.addEdge("Warehouse", "Office", 8);
        graph.addEdge("Factory", "Office", 5);
        graph.addEdge("Factory", "Distribution", 7);
        graph.addEdge("Office", "Distribution", 9);
        graph.addEdge("Office", "DataCenter", 11);
        graph.addEdge("Distribution", "DataCenter", 4);

        cout << "MINIMUM SPANNING TREE ENGINE\n";

        MSTResult kruskal = graph.kruskal();
        MSTResult prim = graph.prim();

        graph.display(kruskal);
        graph.display(prim);

        demonstrateUnionFind();
        testAlgorithms();

    } catch (const exception& error) {
        cerr << "Execution error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
