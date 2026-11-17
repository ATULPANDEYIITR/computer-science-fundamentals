import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Deque;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;

/*
 * Graph Algorithms III
 *
 * Enterprise route-analysis engine.
 *
 * Java 17 features:
 * - Records and enums.
 * - Immutable result objects.
 * - Generic validation patterns.
 * - Service-oriented architecture.
 * - Explicit shortest-path states.
 * - Negative-cycle analysis.
 * - Policy-based path validation.
 * - Graph versioning.
 *
 * Compile:
 * javac GraphAlgorithmsIII.java
 *
 * Run:
 * java GraphAlgorithmsIII
 */

public class GraphAlgorithmsIII {

    private static final double INF = Double.POSITIVE_INFINITY;

    enum PathStatus {
        FINITE,
        UNREACHABLE,
        NEGATIVE_INFINITY
    }

    enum Algorithm {
        BELLMAN_FORD,
        FLOYD_WARSHALL
    }

    record Edge(int source, int destination, double weight) {
        Edge {
            if (source < 0 || destination < 0) {
                throw new IllegalArgumentException(
                    "Vertex identifiers cannot be negative."
                );
            }

            if (!Double.isFinite(weight)) {
                throw new IllegalArgumentException(
                    "Edge weight must be finite."
                );
            }
        }
    }

    record GraphSnapshot(
        int vertexCount,
        long version,
        List<Edge> edges
    ) {
        GraphSnapshot {
            edges = List.copyOf(edges);
        }
    }

    record AnalysisPolicy(
        boolean rejectNegativeCycles,
        boolean requireReachableDestination
    ) {}

    record RouteDecision(
        boolean permitted,
        String reason,
        List<Integer> path,
        double distance
    ) {
        RouteDecision {
            path = List.copyOf(path);
        }
    }

    static class GraphException extends RuntimeException {
        GraphException(String message) {
            super(message);
        }
    }

    static class NegativeCycleException extends GraphException {
        NegativeCycleException(String message) {
            super(message);
        }
    }

    static class WeightedGraph {
        private final int vertexCount;
        private final List<Edge> edges = new ArrayList<>();
        private final List<List<Integer>> adjacency;
        private long version = 0;

        WeightedGraph(int vertexCount) {
            if (vertexCount <= 0) {
                throw new IllegalArgumentException(
                    "Graph must contain at least one vertex."
                );
            }

            this.vertexCount = vertexCount;
            this.adjacency = new ArrayList<>();

            for (int i = 0; i < vertexCount; i++) {
                adjacency.add(new ArrayList<>());
            }
        }

        private void validateVertex(int vertex) {
            if (vertex < 0 || vertex >= vertexCount) {
                throw new GraphException(
                    "Invalid vertex identifier: " + vertex
                );
            }
        }

        void addEdge(Edge edge) {
            Objects.requireNonNull(edge, "Edge cannot be null.");

            validateVertex(edge.source());
            validateVertex(edge.destination());

            edges.add(edge);
            adjacency.get(edge.source()).add(edge.destination());
            version++;
        }

        GraphSnapshot snapshot() {
            return new GraphSnapshot(
                vertexCount,
                version,
                edges
            );
        }

        int size() {
            return vertexCount;
        }

        List<Integer> neighbors(int vertex) {
            validateVertex(vertex);
            return Collections.unmodifiableList(
                adjacency.get(vertex)
            );
        }
    }

    record BellmanFordResult(
        int source,
        long graphVersion,
        List<Double> distances,
        List<Integer> predecessors,
        Set<Integer> affectedVertices,
        List<Integer> negativeCycle
    ) {
        BellmanFordResult {
            distances = List.copyOf(distances);
            predecessors = Collections.unmodifiableList(
                new ArrayList<>(predecessors)
            );
            affectedVertices = Set.copyOf(affectedVertices);
            negativeCycle = List.copyOf(negativeCycle);
        }

        PathStatus status(int vertex) {
            if (affectedVertices.contains(vertex)) {
                return PathStatus.NEGATIVE_INFINITY;
            }

            if (distances.get(vertex) == INF) {
                return PathStatus.UNREACHABLE;
            }

            return PathStatus.FINITE;
        }
    }

    record FloydWarshallResult(
        long graphVersion,
        double[][] distances,
        int[][] next,
        Set<Integer> negativeCycles
    ) {
        FloydWarshallResult {
            distances = copyMatrix(distances);
            next = copyMatrix(next);
            negativeCycles = Set.copyOf(negativeCycles);
        }

        private static double[][] copyMatrix(double[][] source) {
            double[][] copy = new double[source.length][];

            for (int i = 0; i < source.length; i++) {
                copy[i] = source[i].clone();
            }

            return copy;
        }

        private static int[][] copyMatrix(int[][] source) {
            int[][] copy = new int[source.length][];

            for (int i = 0; i < source.length; i++) {
                copy[i] = source[i].clone();
            }

            return copy;
        }

        PathStatus status(int source, int destination) {
            for (int cycle : negativeCycles) {
                if (
                    distances[source][cycle] != INF &&
                    distances[cycle][destination] != INF
                ) {
                    return PathStatus.NEGATIVE_INFINITY;
                }
            }

            return distances[source][destination] == INF
                ? PathStatus.UNREACHABLE
                : PathStatus.FINITE;
        }

        double distance(int source, int destination) {
            return distances[source][destination];
        }
    }

    interface ShortestPathService {
        BellmanFordResult analyze(
            GraphSnapshot graph,
            int source
        );
    }

    static class BellmanFordService
        implements ShortestPathService {

        @Override
        public BellmanFordResult analyze(
            GraphSnapshot graph,
            int source
        ) {
            int n = graph.vertexCount();

            if (source < 0 || source >= n) {
                throw new GraphException("Invalid source vertex.");
            }

            double[] distances = new double[n];
            int[] predecessors = new int[n];

            java.util.Arrays.fill(distances, INF);
            java.util.Arrays.fill(predecessors, -1);

            distances[source] = 0;

            for (int iteration = 0; iteration < n - 1; iteration++) {
                boolean changed = false;

                for (Edge edge : graph.edges()) {
                    if (distances[edge.source()] == INF) {
                        continue;
                    }

                    double candidate =
                        distances[edge.source()] + edge.weight();

                    if (candidate < distances[edge.destination()]) {
                        distances[edge.destination()] = candidate;
                        predecessors[edge.destination()] = edge.source();
                        changed = true;
                    }
                }

                if (!changed) {
                    break;
                }
            }

            Set<Integer> affected = new HashSet<>();
            Deque<Integer> queue = new ArrayDeque<>();
            int witness = -1;

            for (Edge edge : graph.edges()) {
                if (distances[edge.source()] == INF) {
                    continue;
                }

                double candidate =
                    distances[edge.source()] + edge.weight();

                if (candidate < distances[edge.destination()]) {
                    distances[edge.destination()] = candidate;
                    predecessors[edge.destination()] = edge.source();

                    if (affected.add(edge.destination())) {
                        queue.add(edge.destination());
                    }

                    witness = edge.destination();
                }
            }

            List<List<Integer>> adjacency =
                buildAdjacency(graph);

            while (!queue.isEmpty()) {
                int vertex = queue.remove();

                for (int destination : adjacency.get(vertex)) {
                    if (affected.add(destination)) {
                        queue.add(destination);
                    }
                }
            }

            List<Integer> cycle = reconstructCycle(
                witness,
                predecessors,
                n
            );

            List<Double> distanceList = new ArrayList<>();
            List<Integer> predecessorList = new ArrayList<>();

            for (int i = 0; i < n; i++) {
                distanceList.add(distances[i]);
                predecessorList.add(predecessors[i]);
            }

            return new BellmanFordResult(
                source,
                graph.version(),
                distanceList,
                predecessorList,
                affected,
                cycle
            );
        }

        private List<List<Integer>> buildAdjacency(
            GraphSnapshot graph
        ) {
            List<List<Integer>> adjacency = new ArrayList<>();

            for (int i = 0; i < graph.vertexCount(); i++) {
                adjacency.add(new ArrayList<>());
            }

            for (Edge edge : graph.edges()) {
                adjacency.get(edge.source()).add(edge.destination());
            }

            return adjacency;
        }

        private List<Integer> reconstructCycle(
            int witness,
            int[] predecessors,
            int n
        ) {
            if (witness == -1) {
                return List.of();
            }

            int current = witness;

            for (int i = 0; i < n; i++) {
                current = predecessors[current];

                if (current == -1) {
                    return List.of();
                }
            }

            List<Integer> cycle = new ArrayList<>();
            int start = current;

            do {
                cycle.add(current);
                current = predecessors[current];

                if (current == -1 || cycle.size() > n) {
                    return List.of();
                }
            } while (current != start);

            cycle.add(start);
            Collections.reverse(cycle);

            return cycle;
        }
    }

    static class FloydWarshallService {

        FloydWarshallResult analyze(GraphSnapshot graph) {
            int n = graph.vertexCount();

            double[][] distances = new double[n][n];
            int[][] next = new int[n][n];

            for (int i = 0; i < n; i++) {
                java.util.Arrays.fill(distances[i], INF);
                java.util.Arrays.fill(next[i], -1);

                distances[i][i] = 0;
                next[i][i] = i;
            }

            for (Edge edge : graph.edges()) {
                if (
                    edge.weight() <
                    distances[edge.source()][edge.destination()]
                ) {
                    distances[edge.source()][edge.destination()] =
                        edge.weight();

                    next[edge.source()][edge.destination()] =
                        edge.destination();
                }
            }

            for (int k = 0; k < n; k++) {
                for (int i = 0; i < n; i++) {
                    if (distances[i][k] == INF) {
                        continue;
                    }

                    for (int j = 0; j < n; j++) {
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

            Set<Integer> negativeCycles = new HashSet<>();

            for (int i = 0; i < n; i++) {
                if (distances[i][i] < 0) {
                    negativeCycles.add(i);
                }
            }

            return new FloydWarshallResult(
                graph.version(),
                distances,
                next,
                negativeCycles
            );
        }
    }

    static class RouteGovernanceService {

        RouteDecision evaluate(
            BellmanFordResult result,
            int destination,
            AnalysisPolicy policy
        ) {
            PathStatus status = result.status(destination);

            if (
                status == PathStatus.NEGATIVE_INFINITY &&
                policy.rejectNegativeCycles()
            ) {
                return new RouteDecision(
                    false,
                    "Route affected by a reachable negative cycle.",
                    List.of(),
                    Double.NEGATIVE_INFINITY
                );
            }

            if (
                status == PathStatus.UNREACHABLE &&
                policy.requireReachableDestination()
            ) {
                return new RouteDecision(
                    false,
                    "Destination is unreachable.",
                    List.of(),
                    INF
                );
            }

            if (status != PathStatus.FINITE) {
                return new RouteDecision(
                    false,
                    "No finite shortest route is available.",
                    List.of(),
                    result.distances().get(destination)
                );
            }

            List<Integer> path = reconstructPath(result, destination);

            return new RouteDecision(
                true,
                "Route passed analysis policy.",
                path,
                result.distances().get(destination)
            );
        }

        private List<Integer> reconstructPath(
            BellmanFordResult result,
            int destination
        ) {
            List<Integer> path = new ArrayList<>();
            int current = destination;

            for (int i = 0; i <= result.distances().size(); i++) {
                path.add(current);

                if (current == result.source()) {
                    Collections.reverse(path);
                    return path;
                }

                current = result.predecessors().get(current);

                if (current == -1) {
                    break;
                }
            }

            throw new GraphException("Invalid predecessor chain.");
        }
    }

    private static WeightedGraph createSampleGraph() {
        WeightedGraph graph = new WeightedGraph(6);

        List<Edge> edges = List.of(
            new Edge(0, 1, 4),
            new Edge(0, 2, 5),
            new Edge(1, 2, -2),
            new Edge(1, 3, 6),
            new Edge(2, 3, 3),
            new Edge(3, 4, 2),
            new Edge(4, 5, 1)
        );

        edges.forEach(graph::addEdge);

        return graph;
    }

    private static void demonstrateBellmanFord() {
        System.out.println("\n=== BELLMAN-FORD ===");

        WeightedGraph graph = createSampleGraph();
        GraphSnapshot snapshot = graph.snapshot();

        ShortestPathService service = new BellmanFordService();

        BellmanFordResult result = service.analyze(snapshot, 0);

        for (int i = 0; i < graph.size(); i++) {
            System.out.println(
                "Vertex " + i +
                ": distance=" + result.distances().get(i) +
                ", status=" + result.status(i)
            );
        }

        RouteGovernanceService governance =
            new RouteGovernanceService();

        RouteDecision decision = governance.evaluate(
            result,
            5,
            new AnalysisPolicy(true, true)
        );

        System.out.println("Route permitted: " + decision.permitted());
        System.out.println("Route: " + decision.path());
        System.out.println("Distance: " + decision.distance());

        if (decision.distance() != 8) {
            throw new GraphException("Unexpected shortest distance.");
        }
    }

    private static void demonstrateNegativeCycle() {
        System.out.println("\n=== NEGATIVE CYCLE ===");

        WeightedGraph graph = new WeightedGraph(6);

        List<Edge> edges = List.of(
            new Edge(0, 1, 2),
            new Edge(1, 2, 2),
            new Edge(2, 3, -5),
            new Edge(3, 1, 1),
            new Edge(3, 4, 4),
            new Edge(0, 5, 10)
        );

        edges.forEach(graph::addEdge);

        BellmanFordResult result =
            new BellmanFordService().analyze(graph.snapshot(), 0);

        System.out.println("Cycle witness: " + result.negativeCycle());
        System.out.println("Affected vertices: " + result.affectedVertices());

        if (!result.affectedVertices().contains(4)) {
            throw new GraphException("Affected vertex detection failed.");
        }

        if (result.status(5) != PathStatus.FINITE) {
            throw new GraphException("Independent route was incorrectly marked.");
        }
    }

    private static void demonstrateFloydWarshall() {
        System.out.println("\n=== FLOYD-WARSHALL ===");

        WeightedGraph graph = new WeightedGraph(5);

        List<Edge> edges = List.of(
            new Edge(0, 1, 3),
            new Edge(0, 2, 10),
            new Edge(1, 2, -2),
            new Edge(1, 3, 7),
            new Edge(2, 3, 2),
            new Edge(3, 4, 1),
            new Edge(4, 1, 8)
        );

        edges.forEach(graph::addEdge);

        FloydWarshallResult result =
            new FloydWarshallService().analyze(graph.snapshot());

        for (int i = 0; i < graph.size(); i++) {
            for (int j = 0; j < graph.size(); j++) {
                double distance = result.distance(i, j);

                System.out.printf(
                    "%10s",
                    distance == INF ? "INF" : distance
                );
            }

            System.out.println();
        }

        if (result.distance(0, 4) != 4) {
            throw new GraphException("All-pairs result is incorrect.");
        }
    }

    private static void demonstrateCrossValidation() {
        System.out.println("\n=== CROSS-VALIDATION ===");

        WeightedGraph graph = new WeightedGraph(5);

        List<Edge> edges = List.of(
            new Edge(0, 1, 6),
            new Edge(0, 2, 7),
            new Edge(1, 2, 8),
            new Edge(1, 3, 5),
            new Edge(1, 4, -4),
            new Edge(2, 3, -3),
            new Edge(2, 4, 9),
            new Edge(3, 1, -2),
            new Edge(4, 0, 2),
            new Edge(4, 3, 7)
        );

        edges.forEach(graph::addEdge);

        GraphSnapshot snapshot = graph.snapshot();

        FloydWarshallResult allPairs =
            new FloydWarshallService().analyze(snapshot);

        ShortestPathService singleSource =
            new BellmanFordService();

        for (int source = 0; source < graph.size(); source++) {
            BellmanFordResult result =
                singleSource.analyze(snapshot, source);

            for (int destination = 0; destination < graph.size(); destination++) {
                if (result.status(destination) == PathStatus.FINITE) {
                    if (
                        result.distances().get(destination) !=
                        allPairs.distance(source, destination)
                    ) {
                        throw new GraphException(
                            "Shortest-path implementations disagree."
                        );
                    }
                }
            }
        }

        System.out.println("Cross-validation passed.");
    }

    public static void main(String[] args) {
        try {
            System.out.println("GRAPH ALGORITHMS III");
            System.out.println(
                "Bellman-Ford | Floyd-Warshall | Negative Cycles"
            );

            demonstrateBellmanFord();
            demonstrateNegativeCycle();
            demonstrateFloydWarshall();
            demonstrateCrossValidation();

            System.out.println("\nAll enterprise validation checks passed.");

        } catch (RuntimeException exception) {
            System.err.println(
                "Analysis failed: " + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
