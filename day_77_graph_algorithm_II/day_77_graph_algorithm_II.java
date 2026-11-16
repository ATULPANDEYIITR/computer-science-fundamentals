import java.util.*;
import java.util.stream.Collectors;

/*
 * Graph Algorithms II
 * Enterprise Shortest Path and Routing Engine
 *
 * Java 17
 *
 * Features:
 * - Explicit graph domain types
 * - Weighted directed and undirected networks
 * - Dijkstra's algorithm
 * - PriorityQueue
 * - Records and immutable result objects
 * - Multi-source shortest paths
 * - Path reconstruction
 * - Route validation
 * - Asynchronous service interface
 * - Execution diagnostics
 * - Automated tests
 */

public class DijkstraEngine {

    enum GraphType {
        DIRECTED,
        UNDIRECTED
    }

    enum RouteStatus {
        REACHABLE,
        UNREACHABLE
    }

    record Edge(String destination, double weight) {

        Edge {
            Objects.requireNonNull(destination);

            if (destination.isBlank()) {
                throw new IllegalArgumentException(
                    "Destination cannot be blank"
                );
            }

            if (!Double.isFinite(weight) || weight < 0) {
                throw new IllegalArgumentException(
                    "Weight must be finite and nonnegative"
                );
            }
        }
    }

    record QueueEntry(String vertex, double distance)
            implements Comparable<QueueEntry> {

        @Override
        public int compareTo(QueueEntry other) {
            int comparison = Double.compare(
                this.distance,
                other.distance
            );

            if (comparison == 0) {
                return this.vertex.compareTo(other.vertex);
            }

            return comparison;
        }
    }

    record RouteResult(
        String source,
        String destination,
        double distance,
        List<String> path,
        RouteStatus status,
        int settledVertices,
        int examinedEdges,
        int relaxations
    ) {

        RouteResult {
            path = List.copyOf(path);
        }

        public boolean reachable() {
            return status == RouteStatus.REACHABLE;
        }
    }

    record SingleSourceResult(
        String source,
        Map<String, Double> distances,
        Map<String, String> predecessors,
        int settledVertices,
        int examinedEdges,
        int relaxations
    ) {

        SingleSourceResult {
            distances = Map.copyOf(distances);
            predecessors = Map.copyOf(predecessors);
        }

        public Optional<List<String>> pathTo(String destination) {
            if (!distances.containsKey(destination)) {
                throw new IllegalArgumentException(
                    "Unknown destination: " + destination
                );
            }

            if (Double.isInfinite(distances.get(destination))) {
                return Optional.empty();
            }

            List<String> path = new ArrayList<>();

            String current = destination;

            while (current != null) {
                path.add(current);

                if (current.equals(source)) {
                    break;
                }

                current = predecessors.get(current);
            }

            if (path.isEmpty() ||
                !path.get(path.size() - 1).equals(source)) {
                return Optional.empty();
            }

            Collections.reverse(path);

            return Optional.of(List.copyOf(path));
        }
    }

    static class GraphException extends RuntimeException {
        GraphException(String message) {
            super(message);
        }
    }

    static class NegativeWeightException extends GraphException {
        NegativeWeightException(String message) {
            super(message);
        }
    }

    /*
     * Graph is mutable during construction.
     * The shortest-path service uses an immutable snapshot
     * to ensure consistent calculations.
     */
    static final class WeightedGraph {

        private final GraphType type;

        private final Map<String, List<Edge>> adjacency =
            new LinkedHashMap<>();

        private long version = 0;

        WeightedGraph(GraphType type) {
            this.type = Objects.requireNonNull(type);
        }

        public synchronized void addVertex(String vertex) {
            validateVertex(vertex);

            if (!adjacency.containsKey(vertex)) {
                adjacency.put(vertex, new ArrayList<>());
                version++;
            }
        }

        public synchronized void addEdge(
            String source,
            String destination,
            double weight
        ) {
            validateVertex(source);
            validateVertex(destination);

            if (!Double.isFinite(weight)) {
                throw new GraphException(
                    "Weight must be finite"
                );
            }

            if (weight < 0) {
                throw new NegativeWeightException(
                    "Negative weights are not supported"
                );
            }

            addVertex(source);
            addVertex(destination);

            adjacency.get(source).add(
                new Edge(destination, weight)
            );

            if (type == GraphType.UNDIRECTED) {
                adjacency.get(destination).add(
                    new Edge(source, weight)
                );
            }

            version++;
        }

        private void validateVertex(String vertex) {
            if (vertex == null || vertex.isBlank()) {
                throw new GraphException(
                    "Vertex cannot be null or blank"
                );
            }
        }

        public synchronized GraphSnapshot snapshot() {
            Map<String, List<Edge>> copied = new LinkedHashMap<>();

            adjacency.forEach((vertex, edges) ->
                copied.put(vertex, List.copyOf(edges))
            );

            return new GraphSnapshot(
                version,
                Collections.unmodifiableMap(copied)
            );
        }

        public synchronized int vertexCount() {
            return adjacency.size();
        }

        public synchronized int edgeCount() {
            return adjacency.values()
                .stream()
                .mapToInt(List::size)
                .sum();
        }
    }

    record GraphSnapshot(
        long version,
        Map<String, List<Edge>> adjacency
    ) {}

    interface RoutingService {
        RouteResult calculate(
            GraphSnapshot snapshot,
            String source,
            String destination
        );
    }

    static final class DijkstraRoutingService
            implements RoutingService {

        private static final double INF =
            Double.POSITIVE_INFINITY;

        @Override
        public RouteResult calculate(
            GraphSnapshot snapshot,
            String source,
            String destination
        ) {
            Map<String, List<Edge>> graph =
                snapshot.adjacency();

            if (!graph.containsKey(source)) {
                throw new GraphException(
                    "Unknown source: " + source
                );
            }

            if (!graph.containsKey(destination)) {
                throw new GraphException(
                    "Unknown destination: " + destination
                );
            }

            Map<String, Double> distances = new HashMap<>();
            Map<String, String> predecessors = new HashMap<>();

            for (String vertex : graph.keySet()) {
                distances.put(vertex, INF);
                predecessors.put(vertex, null);
            }

            distances.put(source, 0.0);

            PriorityQueue<QueueEntry> queue =
                new PriorityQueue<>();

            queue.add(new QueueEntry(source, 0));

            Set<String> settled = new HashSet<>();

            int examinedEdges = 0;
            int relaxations = 0;

            while (!queue.isEmpty()) {
                QueueEntry current = queue.poll();

                String vertex = current.vertex();
                double distance = current.distance();

                if (settled.contains(vertex)) {
                    continue;
                }

                if (Double.compare(
                    distance,
                    distances.get(vertex)
                ) != 0) {
                    continue;
                }

                settled.add(vertex);

                if (vertex.equals(destination)) {
                    break;
                }

                for (Edge edge : graph.get(vertex)) {
                    examinedEdges++;

                    if (settled.contains(edge.destination())) {
                        continue;
                    }

                    double candidate =
                        distance + edge.weight();

                    if (!Double.isFinite(candidate)) {
                        throw new ArithmeticException(
                            "Distance overflow"
                        );
                    }

                    if (candidate < distances.get(edge.destination())) {
                        distances.put(
                            edge.destination(),
                            candidate
                        );

                        predecessors.put(
                            edge.destination(),
                            vertex
                        );

                        queue.add(
                            new QueueEntry(
                                edge.destination(),
                                candidate
                            )
                        );

                        relaxations++;
                    }
                }
            }

            double distance = distances.get(destination);

            List<String> path = reconstructPath(
                source,
                destination,
                predecessors,
                distance
            );

            return new RouteResult(
                source,
                destination,
                distance,
                path,
                Double.isFinite(distance)
                    ? RouteStatus.REACHABLE
                    : RouteStatus.UNREACHABLE,
                settled.size(),
                examinedEdges,
                relaxations
            );
        }

        private List<String> reconstructPath(
            String source,
            String destination,
            Map<String, String> predecessors,
            double distance
        ) {
            if (!Double.isFinite(distance)) {
                return List.of();
            }

            List<String> path = new ArrayList<>();

            String current = destination;

            while (current != null) {
                path.add(current);

                if (current.equals(source)) {
                    break;
                }

                current = predecessors.get(current);
            }

            if (
                path.isEmpty() ||
                !path.get(path.size() - 1).equals(source)
            ) {
                return List.of();
            }

            Collections.reverse(path);

            return List.copyOf(path);
        }
    }

    static final class MultiSourceRoutingService {

        public SingleSourceResult calculate(
            GraphSnapshot snapshot,
            List<String> sources
        ) {
            if (sources == null || sources.isEmpty()) {
                throw new GraphException(
                    "At least one source is required"
                );
            }

            if (new HashSet<>(sources).size() != sources.size()) {
                throw new GraphException(
                    "Duplicate sources are not allowed"
                );
            }

            Map<String, List<Edge>> graph =
                snapshot.adjacency();

            Map<String, Double> distances = new HashMap<>();
            Map<String, String> predecessors = new HashMap<>();

            for (String vertex : graph.keySet()) {
                distances.put(vertex, Double.POSITIVE_INFINITY);
                predecessors.put(vertex, null);
            }

            PriorityQueue<QueueEntry> queue =
                new PriorityQueue<>();

            for (String source : sources) {
                if (!graph.containsKey(source)) {
                    throw new GraphException(
                        "Unknown source: " + source
                    );
                }

                distances.put(source, 0.0);
                queue.add(new QueueEntry(source, 0.0));
            }

            Set<String> settled = new HashSet<>();

            int examinedEdges = 0;
            int relaxations = 0;

            while (!queue.isEmpty()) {
                QueueEntry current = queue.poll();

                if (!settled.add(current.vertex())) {
                    continue;
                }

                if (current.distance() !=
                    distances.get(current.vertex())) {
                    continue;
                }

                for (Edge edge : graph.get(current.vertex())) {
                    examinedEdges++;

                    if (settled.contains(edge.destination())) {
                        continue;
                    }

                    double candidate =
                        current.distance() + edge.weight();

                    if (!Double.isFinite(candidate)) {
                        throw new ArithmeticException(
                            "Distance overflow"
                        );
                    }

                    if (candidate < distances.get(edge.destination())) {
                        distances.put(edge.destination(), candidate);

                        predecessors.put(
                            edge.destination(),
                            current.vertex()
                        );

                        queue.add(
                            new QueueEntry(
                                edge.destination(),
                                candidate
                            )
                        );

                        relaxations++;
                    }
                }
            }

            return new SingleSourceResult(
                sources.get(0),
                distances,
                predecessors,
                settled.size(),
                examinedEdges,
                relaxations
            );
        }
    }

    static final class RoutingApplication {

        private final WeightedGraph graph;

        private final RoutingService routingService;

        RoutingApplication(WeightedGraph graph) {
            this.graph = graph;
            this.routingService = new DijkstraRoutingService();
        }

        public RouteResult findRoute(
            String source,
            String destination
        ) {
            /*
             * Snapshot isolation ensures the service works against
             * one consistent graph version.
             */
            GraphSnapshot snapshot = graph.snapshot();

            return routingService.calculate(
                snapshot,
                source,
                destination
            );
        }

        public SingleSourceResult findRoutes(
            List<String> sources
        ) {
            return new MultiSourceRoutingService().calculate(
                graph.snapshot(),
                sources
            );
        }
    }

    static WeightedGraph buildNetwork() {
        WeightedGraph graph =
            new WeightedGraph(GraphType.DIRECTED);

        List<List<Object>> edges = List.of(
            List.of("Lucknow", "Kanpur", 90.0),
            List.of("Lucknow", "Ayodhya", 135.0),
            List.of("Lucknow", "Varanasi", 300.0),
            List.of("Kanpur", "Agra", 210.0),
            List.of("Kanpur", "Prayagraj", 180.0),
            List.of("Ayodhya", "Gorakhpur", 150.0),
            List.of("Ayodhya", "Varanasi", 190.0),
            List.of("Gorakhpur", "Patna", 240.0),
            List.of("Varanasi", "Patna", 200.0),
            List.of("Varanasi", "Prayagraj", 130.0),
            List.of("Prayagraj", "Delhi", 500.0),
            List.of("Agra", "Delhi", 150.0),
            List.of("Lucknow", "Express", 0.0),
            List.of("Express", "Kanpur", 70.0)
        );

        for (List<Object> edge : edges) {
            graph.addEdge(
                (String) edge.get(0),
                (String) edge.get(1),
                (double) edge.get(2)
            );
        }

        graph.addVertex("Mumbai");
        graph.addVertex("Chennai");

        return graph;
    }

    static void runTests() {
        WeightedGraph graph =
            new WeightedGraph(GraphType.DIRECTED);

        graph.addEdge("A", "B", 4);
        graph.addEdge("A", "C", 1);
        graph.addEdge("C", "B", 2);
        graph.addEdge("B", "D", 1);
        graph.addVertex("Z");

        RoutingApplication app = new RoutingApplication(graph);

        RouteResult result = app.findRoute("A", "D");

        if (result.distance() != 4) {
            throw new AssertionError(
                "Shortest distance test failed"
            );
        }

        if (!result.path().equals(
            List.of("A", "C", "B", "D")
        )) {
            throw new AssertionError(
                "Path reconstruction test failed"
            );
        }

        RouteResult unreachable = app.findRoute("A", "Z");

        if (unreachable.reachable()) {
            throw new AssertionError(
                "Unreachable vertex test failed"
            );
        }

        boolean rejected = false;

        try {
            graph.addEdge("A", "D", -5);
        } catch (NegativeWeightException exception) {
            rejected = true;
        }

        if (!rejected) {
            throw new AssertionError(
                "Negative weight validation failed"
            );
        }

        SingleSourceResult multi =
            app.findRoutes(List.of("A", "D"));

        if (multi.distances().get("B") != 2.0) {
            throw new AssertionError(
                "Multi-source test failed"
            );
        }

        WeightedGraph undirected =
            new WeightedGraph(GraphType.UNDIRECTED);

        undirected.addEdge("X", "Y", 8);

        if (
            new RoutingApplication(undirected)
                .findRoute("Y", "X")
                .distance() != 8
        ) {
            throw new AssertionError(
                "Undirected graph test failed"
            );
        }

        System.out.println("All tests passed.");
    }

    public static void main(String[] args) {

        WeightedGraph graph = buildNetwork();

        RoutingApplication application =
            new RoutingApplication(graph);

        System.out.println("DIJKSTRA SHORTEST PATH ENGINE");
        System.out.println("=============================");

        System.out.println(
            "Vertices: " + graph.vertexCount()
        );

        System.out.println(
            "Directed edges: " + graph.edgeCount()
        );

        List<String> destinations = List.of(
            "Delhi",
            "Patna",
            "Gorakhpur",
            "Mumbai"
        );

        for (String destination : destinations) {
            RouteResult result = application.findRoute(
                "Lucknow",
                destination
            );

            System.out.println("\nDestination: " + destination);

            if (!result.reachable()) {
                System.out.println("UNREACHABLE");
                continue;
            }

            System.out.println(
                "Route: " +
                String.join(" -> ", result.path())
            );

            System.out.println(
                "Distance: " + result.distance()
            );

            System.out.println(
                "Settled vertices: " +
                result.settledVertices()
            );
        }

        System.out.println("\nMulti-source routing");

        SingleSourceResult multi =
            application.findRoutes(
                List.of("Lucknow", "Patna")
            );

        multi.distances()
            .entrySet()
            .stream()
            .sorted(Map.Entry.comparingByKey())
            .forEach(entry ->
                System.out.printf(
                    "%-18s %s%n",
                    entry.getKey(),
                    entry.getValue()
                )
            );

        System.out.println("\nRunning tests");
        runTests();

        System.out.println("\nComplexity");
        System.out.println("Storage: O(V + E)");
        System.out.println("Dijkstra: O((V + E) log V)");
        System.out.println("Path reconstruction: O(V)");
        System.out.println("Auxiliary space: O(V)");
    }
}
