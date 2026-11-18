import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.Set;
import java.util.Objects;

/*
 * Enterprise Minimum Spanning Tree Management System.
 *
 * Domain model:
 * InfrastructureNetwork -> Vertices -> WeightedConnections
 *                       -> MSTCalculation -> NetworkPlan
 *
 * Both algorithms return minimum spanning forests for disconnected
 * networks. A spanning tree requires exactly one connected component.
 */

public class Main {

    enum Algorithm {
        KRUSKAL,
        PRIM
    }

    enum NetworkStatus {
        CONNECTED,
        DISCONNECTED
    }

    record Edge(String source, String target, double weight) {
        Edge {
            if (source == null || source.isBlank() ||
                target == null || target.isBlank()) {
                throw new IllegalArgumentException(
                    "Vertex identifiers cannot be empty."
                );
            }

            if (source.equals(target)) {
                throw new IllegalArgumentException(
                    "Self-loops are not allowed."
                );
            }

            if (!Double.isFinite(weight)) {
                throw new IllegalArgumentException(
                    "Weight must be finite."
                );
            }
        }
    }

    record NetworkPlan(
        Algorithm algorithm,
        List<Edge> selectedEdges,
        double totalWeight,
        int vertexCount,
        int componentCount,
        long graphRevision
    ) {
        NetworkPlan {
            Objects.requireNonNull(algorithm);
            selectedEdges = List.copyOf(selectedEdges);

            if (vertexCount < 1 || componentCount < 1 ||
                componentCount > vertexCount) {
                throw new IllegalArgumentException(
                    "Invalid network dimensions."
                );
            }

            if (!Double.isFinite(totalWeight)) {
                throw new IllegalArgumentException(
                    "Invalid calculated weight."
                );
            }

            if (selectedEdges.size() != vertexCount - componentCount) {
                throw new IllegalArgumentException(
                    "Forest edge-count invariant violated."
                );
            }
        }

        boolean isSpanningTree() {
            return componentCount == 1 &&
                   selectedEdges.size() == vertexCount - 1;
        }

        boolean isSpanningForest() {
            return selectedEdges.size() == vertexCount - componentCount;
        }
    }

    static class NetworkException extends RuntimeException {
        NetworkException(String message) {
            super(message);
        }
    }

    static class DisjointSet {
        private final Map<String, String> parent = new HashMap<>();
        private final Map<String, Integer> rank = new HashMap<>();
        private int components;

        DisjointSet(Set<String> vertices) {
            for (String vertex : vertices) {
                parent.put(vertex, vertex);
                rank.put(vertex, 0);
            }

            components = vertices.size();
        }

        String find(String vertex) {
            if (!parent.containsKey(vertex)) {
                throw new NetworkException(
                    "Unknown vertex: " + vertex
                );
            }

            String root = vertex;

            while (!root.equals(parent.get(root))) {
                root = parent.get(root);
            }

            String current = vertex;

            while (!current.equals(root)) {
                String next = parent.get(current);
                parent.put(current, root);
                current = next;
            }

            return root;
        }

        boolean union(String a, String b) {
            String rootA = find(a);
            String rootB = find(b);

            if (rootA.equals(rootB)) {
                return false;
            }

            int rankA = rank.get(rootA);
            int rankB = rank.get(rootB);

            if (rankA < rankB) {
                String temporary = rootA;
                rootA = rootB;
                rootB = temporary;
            }

            parent.put(rootB, rootA);

            if (rankA == rankB) {
                rank.put(rootA, rank.get(rootA) + 1);
            }

            components--;
            return true;
        }

        int componentCount() {
            return components;
        }
    }

    static class InfrastructureNetwork {

        private final Set<String> vertices = new HashSet<>();
        private final List<Edge> edges = new ArrayList<>();

        private final Map<String, List<Edge>> adjacency =
            new HashMap<>();

        private final Set<String> edgeKeys = new HashSet<>();

        private long revision = 0;

        InfrastructureNetwork(List<String> vertexNames) {
            if (vertexNames == null || vertexNames.isEmpty()) {
                throw new NetworkException(
                    "At least one vertex is required."
                );
            }

            for (String vertex : vertexNames) {
                if (vertex == null || vertex.isBlank()) {
                    throw new NetworkException(
                        "Invalid vertex identifier."
                    );
                }

                if (!vertices.add(vertex)) {
                    throw new NetworkException(
                        "Duplicate vertex: " + vertex
                    );
                }

                adjacency.put(vertex, new ArrayList<>());
            }
        }

        void addConnection(String source, String target, double weight) {
            if (!vertices.contains(source) ||
                !vertices.contains(target)) {
                throw new NetworkException(
                    "Both endpoints must exist."
                );
            }

            Edge edge = new Edge(source, target, weight);
            String key = createKey(source, target);

            if (!edgeKeys.add(key)) {
                throw new NetworkException(
                    "Duplicate undirected connection."
                );
            }

            edges.add(edge);
            adjacency.get(source).add(edge);
            adjacency.get(target).add(edge);
            revision++;
        }

        private String createKey(String a, String b) {
            return a.compareTo(b) < 0
                ? a + "\u0000" + b
                : b + "\u0000" + a;
        }

        long revision() {
            return revision;
        }

        int vertexCount() {
            return vertices.size();
        }

        NetworkStatus status() {
            DisjointSet dsu = new DisjointSet(vertices);

            for (Edge edge : edges) {
                dsu.union(edge.source(), edge.target());
            }

            return dsu.componentCount() == 1
                ? NetworkStatus.CONNECTED
                : NetworkStatus.DISCONNECTED;
        }

        NetworkPlan calculateKruskal() {
            DisjointSet dsu = new DisjointSet(vertices);

            List<Edge> sorted = new ArrayList<>(edges);
            sorted.sort(
                Comparator.comparingDouble(Edge::weight)
                    .thenComparing(Edge::source)
                    .thenComparing(Edge::target)
            );

            List<Edge> selected = new ArrayList<>();
            double totalWeight = 0;

            for (Edge edge : sorted) {
                if (dsu.union(edge.source(), edge.target())) {
                    selected.add(edge);
                    totalWeight += edge.weight();

                    if (selected.size() == vertices.size() - 1) {
                        break;
                    }
                }
            }

            return new NetworkPlan(
                Algorithm.KRUSKAL,
                selected,
                totalWeight,
                vertices.size(),
                dsu.componentCount(),
                revision
            );
        }

        NetworkPlan calculatePrim(String startingVertex) {
            if (!vertices.contains(startingVertex)) {
                throw new NetworkException(
                    "Starting vertex does not exist."
                );
            }

            Comparator<Edge> comparator =
                Comparator.comparingDouble(Edge::weight)
                    .thenComparing(Edge::source)
                    .thenComparing(Edge::target);

            PriorityQueue<Edge> queue =
                new PriorityQueue<>(comparator);

            Set<String> visited = new HashSet<>();
            List<Edge> selected = new ArrayList<>();

            List<String> roots = new ArrayList<>();
            roots.add(startingVertex);

            vertices.stream()
                .filter(v -> !v.equals(startingVertex))
                .sorted()
                .forEach(roots::add);

            double totalWeight = 0;

            for (String root : roots) {
                if (!visited.add(root)) {
                    continue;
                }

                queue.addAll(adjacency.get(root));

                while (!queue.isEmpty()) {
                    Edge edge = queue.poll();

                    boolean sourceVisited =
                        visited.contains(edge.source());

                    boolean targetVisited =
                        visited.contains(edge.target());

                    if (sourceVisited == targetVisited) {
                        continue;
                    }

                    String next = sourceVisited
                        ? edge.target()
                        : edge.source();

                    visited.add(next);
                    selected.add(edge);
                    totalWeight += edge.weight();

                    queue.addAll(adjacency.get(next));
                }
            }

            return new NetworkPlan(
                Algorithm.PRIM,
                selected,
                totalWeight,
                vertices.size(),
                vertices.size() - selected.size(),
                revision
            );
        }

        boolean verify(NetworkPlan plan) {
            if (plan.vertexCount() != vertices.size()) {
                return false;
            }

            DisjointSet original = new DisjointSet(vertices);
            DisjointSet candidate = new DisjointSet(vertices);

            for (Edge edge : edges) {
                original.union(edge.source(), edge.target());
            }

            double calculatedWeight = 0;

            for (Edge edge : plan.selectedEdges()) {
                if (!candidate.union(edge.source(), edge.target())) {
                    return false;
                }

                calculatedWeight += edge.weight();
            }

            return (
                original.componentCount() ==
                    candidate.componentCount() &&
                candidate.componentCount() ==
                    plan.componentCount() &&
                Math.abs(calculatedWeight - plan.totalWeight()) < 1e-9
            );
        }
    }

    interface NetworkPolicy {
        void validate(NetworkPlan plan);
    }

    static class StandardNetworkPolicy implements NetworkPolicy {

        private final boolean requireConnected;
        private final double maximumAllowedWeight;

        StandardNetworkPolicy(
            boolean requireConnected,
            double maximumAllowedWeight
        ) {
            if (!Double.isFinite(maximumAllowedWeight) ||
                maximumAllowedWeight < 0) {
                throw new IllegalArgumentException(
                    "Invalid maximum weight."
                );
            }

            this.requireConnected = requireConnected;
            this.maximumAllowedWeight = maximumAllowedWeight;
        }

        @Override
        public void validate(NetworkPlan plan) {
            if (requireConnected && !plan.isSpanningTree()) {
                throw new NetworkException(
                    "Policy requires a connected spanning tree."
                );
            }

            if (plan.totalWeight() > maximumAllowedWeight) {
                throw new NetworkException(
                    "Network plan exceeds the approved cost limit."
                );
            }
        }
    }

    static class NetworkService {

        private final InfrastructureNetwork network;
        private final NetworkPolicy policy;

        NetworkService(
            InfrastructureNetwork network,
            NetworkPolicy policy
        ) {
            this.network = Objects.requireNonNull(network);
            this.policy = Objects.requireNonNull(policy);
        }

        NetworkPlan approveKruskalPlan() {
            NetworkPlan plan = network.calculateKruskal();

            if (!network.verify(plan)) {
                throw new NetworkException(
                    "Kruskal verification failed."
                );
            }

            policy.validate(plan);
            return plan;
        }

        NetworkPlan approvePrimPlan(String start) {
            NetworkPlan plan = network.calculatePrim(start);

            if (!network.verify(plan)) {
                throw new NetworkException(
                    "Prim verification failed."
                );
            }

            policy.validate(plan);
            return plan;
        }
    }

    static void display(NetworkPlan plan) {
        System.out.println("\nAlgorithm: " + plan.algorithm());

        for (Edge edge : plan.selectedEdges()) {
            System.out.printf(
                "%s -- %s : %.2f%n",
                edge.source(),
                edge.target(),
                edge.weight()
            );
        }

        System.out.println(
            "Total weight: " + plan.totalWeight()
        );

        System.out.println(
            "Components: " + plan.componentCount()
        );

        System.out.println(
            "Spanning tree: " + plan.isSpanningTree()
        );

        System.out.println(
            "Spanning forest: " + plan.isSpanningForest()
        );
    }

    static void runTests() {
        InfrastructureNetwork graph =
            new InfrastructureNetwork(
                List.of("A", "B", "C", "D", "E", "F")
            );

        graph.addConnection("A", "B", 4);
        graph.addConnection("A", "C", 3);
        graph.addConnection("B", "C", 1);
        graph.addConnection("B", "D", 2);
        graph.addConnection("C", "D", 4);
        graph.addConnection("C", "E", 5);
        graph.addConnection("D", "E", 2);
        graph.addConnection("D", "F", 6);
        graph.addConnection("E", "F", 3);

        NetworkPlan kruskal = graph.calculateKruskal();
        NetworkPlan prim = graph.calculatePrim("A");

        assert graph.verify(kruskal);
        assert graph.verify(prim);
        assert kruskal.isSpanningTree();
        assert prim.isSpanningTree();

        assert Math.abs(
            kruskal.totalWeight() - prim.totalWeight()
        ) < 1e-9;

        // Policy acceptance.
        NetworkPolicy policy =
            new StandardNetworkPolicy(true, 20);

        NetworkService service =
            new NetworkService(graph, policy);

        assert service.approveKruskalPlan().isSpanningTree();

        // Cost policy rejection.
        try {
            new StandardNetworkPolicy(true, 1)
                .validate(kruskal);

            throw new AssertionError(
                "Expected cost-policy rejection."
            );
        } catch (NetworkException expected) {
            System.out.println("Cost policy rejection verified.");
        }

        // Disconnected network.
        InfrastructureNetwork disconnected =
            new InfrastructureNetwork(
                List.of("A", "B", "C", "D")
            );

        disconnected.addConnection("A", "B", 2);
        disconnected.addConnection("C", "D", 1);

        NetworkPlan forest = disconnected.calculateKruskal();

        assert forest.componentCount() == 2;
        assert forest.isSpanningForest();
        assert !forest.isSpanningTree();

        // Negative weights.
        InfrastructureNetwork negative =
            new InfrastructureNetwork(List.of("A", "B", "C"));

        negative.addConnection("A", "B", -5);
        negative.addConnection("B", "C", 2);
        negative.addConnection("A", "C", 4);

        assert negative.calculateKruskal().totalWeight() == -3;

        // Singleton network.
        InfrastructureNetwork singleton =
            new InfrastructureNetwork(List.of("A"));

        assert singleton.calculateKruskal().isSpanningTree();

        // Duplicate edge.
        try {
            graph.addConnection("B", "A", 3);
            throw new AssertionError("Duplicate edge accepted.");
        } catch (NetworkException expected) {
            System.out.println("Duplicate-edge validation verified.");
        }

        // Invalid starting vertex.
        try {
            graph.calculatePrim("UNKNOWN");
            throw new AssertionError("Invalid vertex accepted.");
        } catch (NetworkException expected) {
            System.out.println("Starting-vertex validation verified.");
        }

        System.out.println("\nAll Java 17 tests passed.");
    }

    public static void main(String[] args) {
        InfrastructureNetwork network =
            new InfrastructureNetwork(
                List.of(
                    "Warehouse",
                    "Factory",
                    "Office",
                    "Distribution",
                    "DataCenter"
                )
            );

        network.addConnection("Warehouse", "Factory", 12);
        network.addConnection("Warehouse", "Office", 8);
        network.addConnection("Factory", "Office", 5);
        network.addConnection("Factory", "Distribution", 7);
        network.addConnection("Office", "Distribution", 9);
        network.addConnection("Office", "DataCenter", 11);
        network.addConnection("Distribution", "DataCenter", 4);

        System.out.println("ENTERPRISE NETWORK OPTIMIZATION");
        System.out.println("Network status: " + network.status());

        NetworkPolicy policy =
            new StandardNetworkPolicy(true, 100);

        NetworkService service =
            new NetworkService(network, policy);

        NetworkPlan kruskal = service.approveKruskalPlan();
        NetworkPlan prim = service.approvePrimPlan("Warehouse");

        display(kruskal);
        display(prim);

        runTests();
    }
}
