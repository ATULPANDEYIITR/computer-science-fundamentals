import java.util.*;
import java.util.function.Predicate;
import java.util.stream.Collectors;

/*
 * GRAPH ALGORITHMS I
 *
 * Enterprise dependency and infrastructure graph analysis.
 * Java 17, no external dependencies.
 */
public class Main {

    enum GraphType {
        DIRECTED,
        UNDIRECTED
    }

    enum TraversalStatus {
        DISCOVERED,
        PROCESSED
    }

    static class GraphException extends RuntimeException {
        GraphException(String message) {
            super(message);
        }
    }

    static class VertexNotFoundException extends GraphException {
        VertexNotFoundException(String vertex) {
            super("Vertex does not exist: " + vertex);
        }
    }

    record Edge(String source, String target) {}

    record PathResult(
        String source,
        String target,
        List<String> path,
        int distance,
        boolean reachable
    ) {
        PathResult {
            path = List.copyOf(path);
        }
    }

    record ComponentReport(
        List<List<String>> components,
        int componentCount,
        int largestComponentSize,
        List<String> isolatedVertices
    ) {
        ComponentReport {
            components = components.stream()
                .map(List::copyOf)
                .toList();

            isolatedVertices = List.copyOf(isolatedVertices);
        }
    }

    record DependencyReport(
        List<String> traversalOrder,
        List<String> topologicalOrder,
        boolean cyclic
    ) {
        DependencyReport {
            traversalOrder = List.copyOf(traversalOrder);
            topologicalOrder = List.copyOf(topologicalOrder);
        }
    }

    interface GraphAnalyzer {
        PathResult shortestPath(String source, String target);

        ComponentReport connectedComponents();

        DependencyReport analyzeDependencies();
    }

    // ---------------------------------------------------------
    // GRAPH DOMAIN MODEL
    // ---------------------------------------------------------

    static final class Graph implements GraphAnalyzer {

        private final GraphType type;

        private final Map<String, Set<String>> adjacency =
            new TreeMap<>();

        Graph(GraphType type) {
            this.type = Objects.requireNonNull(type);
        }

        public GraphType getType() {
            return type;
        }

        public void addVertex(String vertex) {
            validateName(vertex);
            adjacency.computeIfAbsent(
                vertex,
                ignored -> new TreeSet<>()
            );
        }

        public void addEdge(String source, String target) {
            addVertex(source);
            addVertex(target);

            if (!adjacency.get(source).add(target)) {
                return;
            }

            if (type == GraphType.UNDIRECTED) {
                adjacency.get(target).add(source);
            }
        }

        private void validateName(String vertex) {
            if (vertex == null || vertex.isBlank()) {
                throw new IllegalArgumentException(
                    "Vertex name must not be blank."
                );
            }
        }

        private void requireVertex(String vertex) {
            if (!adjacency.containsKey(vertex)) {
                throw new VertexNotFoundException(vertex);
            }
        }

        public Set<String> vertices() {
            return Collections.unmodifiableSet(
                new TreeSet<>(adjacency.keySet())
            );
        }

        public List<Edge> edges() {
            List<Edge> result = new ArrayList<>();

            for (String source : adjacency.keySet()) {
                for (String target : adjacency.get(source)) {
                    if (
                        type == GraphType.DIRECTED ||
                        source.compareTo(target) < 0
                    ) {
                        result.add(new Edge(source, target));
                    }
                }
            }

            return List.copyOf(result);
        }

        // -----------------------------------------------------
        // BFS: shortest unweighted paths
        // -----------------------------------------------------

        @Override
        public PathResult shortestPath(
            String source,
            String target
        ) {
            requireVertex(source);
            requireVertex(target);

            Queue<String> queue = new ArrayDeque<>();

            Map<String, Integer> distance = new HashMap<>();
            Map<String, String> parent = new HashMap<>();

            queue.add(source);
            distance.put(source, 0);

            while (!queue.isEmpty()) {
                String current = queue.remove();

                if (current.equals(target)) {
                    break;
                }

                for (String neighbor : adjacency.get(current)) {
                    if (!distance.containsKey(neighbor)) {
                        distance.put(
                            neighbor,
                            distance.get(current) + 1
                        );

                        parent.put(neighbor, current);
                        queue.add(neighbor);
                    }
                }
            }

            if (!distance.containsKey(target)) {
                return new PathResult(
                    source,
                    target,
                    List.of(),
                    -1,
                    false
                );
            }

            List<String> path = new ArrayList<>();
            String current = target;

            while (current != null) {
                path.add(current);
                current = parent.get(current);
            }

            Collections.reverse(path);

            return new PathResult(
                source,
                target,
                path,
                distance.get(target),
                true
            );
        }

        public Map<String, Integer> multiSourceBfs(
            Collection<String> sources
        ) {
            Queue<String> queue = new ArrayDeque<>();
            Map<String, Integer> distance = new HashMap<>();

            for (String source : new LinkedHashSet<>(sources)) {
                requireVertex(source);
                distance.put(source, 0);
                queue.add(source);
            }

            while (!queue.isEmpty()) {
                String current = queue.remove();

                for (String neighbor : adjacency.get(current)) {
                    if (!distance.containsKey(neighbor)) {
                        distance.put(
                            neighbor,
                            distance.get(current) + 1
                        );

                        queue.add(neighbor);
                    }
                }
            }

            return Collections.unmodifiableMap(distance);
        }

        // -----------------------------------------------------
        // Connected components
        // -----------------------------------------------------

        @Override
        public ComponentReport connectedComponents() {
            if (type != GraphType.UNDIRECTED) {
                throw new GraphException(
                    "Connected components require an undirected graph."
                );
            }

            Set<String> visited = new HashSet<>();
            List<List<String>> components = new ArrayList<>();
            List<String> isolated = new ArrayList<>();

            for (String vertex : adjacency.keySet()) {
                if (visited.contains(vertex)) continue;

                List<String> component = new ArrayList<>();
                Queue<String> queue = new ArrayDeque<>();

                queue.add(vertex);
                visited.add(vertex);

                while (!queue.isEmpty()) {
                    String current = queue.remove();
                    component.add(current);

                    for (String neighbor : adjacency.get(current)) {
                        if (visited.add(neighbor)) {
                            queue.add(neighbor);
                        }
                    }
                }

                component.sort(String::compareTo);

                if (component.size() == 1 &&
                    adjacency.get(vertex).isEmpty()) {
                    isolated.add(vertex);
                }

                components.add(component);
            }

            int largest = components.stream()
                .mapToInt(List::size)
                .max()
                .orElse(0);

            return new ComponentReport(
                components,
                components.size(),
                largest,
                isolated
            );
        }

        // -----------------------------------------------------
        // DFS and topological ordering
        // -----------------------------------------------------

        @Override
        public DependencyReport analyzeDependencies() {
            Set<String> visited = new HashSet<>();
            Set<String> active = new HashSet<>();

            List<String> discovery = new ArrayList<>();
            List<String> finish = new ArrayList<>();

            boolean[] cycle = {false};

            for (String vertex : adjacency.keySet()) {
                if (!visited.contains(vertex)) {
                    dfsVisit(
                        vertex,
                        visited,
                        active,
                        discovery,
                        finish,
                        cycle
                    );
                }
            }

            List<String> topological =
                type == GraphType.DIRECTED && !cycle[0]
                    ? new ArrayList<>(finish)
                    : List.of();

            if (!topological.isEmpty()) {
                Collections.reverse(topological);
            }

            return new DependencyReport(
                discovery,
                topological,
                cycle[0]
            );
        }

        private void dfsVisit(
            String vertex,
            Set<String> visited,
            Set<String> active,
            List<String> discovery,
            List<String> finish,
            boolean[] cycle
        ) {
            visited.add(vertex);
            active.add(vertex);
            discovery.add(vertex);

            for (String neighbor : adjacency.get(vertex)) {
                if (!visited.contains(neighbor)) {
                    dfsVisit(
                        neighbor,
                        visited,
                        active,
                        discovery,
                        finish,
                        cycle
                    );
                } else if (type == GraphType.DIRECTED) {
                    if (active.contains(neighbor)) {
                        cycle[0] = true;
                    }
                }
            }

            active.remove(vertex);
            finish.add(vertex);
        }

        public List<String> breadthFirstOrder(String source) {
            requireVertex(source);

            List<String> order = new ArrayList<>();
            Set<String> visited = new HashSet<>();
            Queue<String> queue = new ArrayDeque<>();

            queue.add(source);
            visited.add(source);

            while (!queue.isEmpty()) {
                String current = queue.remove();
                order.add(current);

                for (String neighbor : adjacency.get(current)) {
                    if (visited.add(neighbor)) {
                        queue.add(neighbor);
                    }
                }
            }

            return List.copyOf(order);
        }
    }

    // ---------------------------------------------------------
    // ENTERPRISE DEPENDENCY SERVICE
    // ---------------------------------------------------------

    static final class DependencyService {

        private final Graph graph;

        DependencyService(Graph graph) {
            if (graph.getType() != GraphType.DIRECTED) {
                throw new GraphException(
                    "Dependency service requires a directed graph."
                );
            }

            this.graph = graph;
        }

        public List<String> deploymentOrder() {
            DependencyReport report =
                graph.analyzeDependencies();

            if (report.cyclic()) {
                throw new GraphException(
                    "Deployment blocked: dependency cycle detected."
                );
            }

            return report.topologicalOrder();
        }

        public boolean isDeploymentSafe() {
            return !graph.analyzeDependencies().cyclic();
        }
    }

    // ---------------------------------------------------------
    // APPLICATION SCENARIOS
    // ---------------------------------------------------------

    static Graph buildInfrastructure() {
        Graph graph = new Graph(GraphType.UNDIRECTED);

        List<Edge> edges = List.of(
            new Edge("API", "Gateway"),
            new Edge("Gateway", "Authentication"),
            new Edge("Gateway", "Orders"),
            new Edge("Orders", "Database"),
            new Edge("Orders", "Cache"),
            new Edge("Monitoring", "Logging"),
            new Edge("Backup", "Storage")
        );

        edges.forEach(
            edge -> graph.addEdge(edge.source(), edge.target())
        );

        graph.addVertex("OfflineNode");

        return graph;
    }

    static Graph buildDependencies() {
        Graph graph = new Graph(GraphType.DIRECTED);

        graph.addEdge("Core", "Authentication");
        graph.addEdge("Authentication", "API");
        graph.addEdge("API", "Frontend");
        graph.addEdge("Core", "Reporting");

        return graph;
    }

    static void demonstrateBfs(Graph graph) {
        System.out.println("\n=== BFS APPLICATIONS ===");

        PathResult result = graph.shortestPath(
            "API",
            "Database"
        );

        System.out.println("Shortest path: " + result.path());
        System.out.println("Distance: " + result.distance());

        PathResult unavailable = graph.shortestPath(
            "API",
            "OfflineNode"
        );

        System.out.println(
            "Offline node reachable: " + unavailable.reachable()
        );

        System.out.println(
            "Multi-source distances: " +
            graph.multiSourceBfs(List.of("API", "Monitoring"))
        );
    }

    static void demonstrateDfs() {
        System.out.println("\n=== DFS APPLICATIONS ===");

        Graph graph = buildDependencies();

        DependencyService service = new DependencyService(graph);

        System.out.println(
            "Deployment order: " + service.deploymentOrder()
        );

        System.out.println(
            "Deployment safe: " + service.isDeploymentSafe()
        );

        graph.addEdge("Frontend", "Core");

        System.out.println(
            "Cycle after modification: " +
            graph.analyzeDependencies().cyclic()
        );

        try {
            service.deploymentOrder();
        } catch (GraphException exception) {
            System.out.println(
                "Deployment rejected: " + exception.getMessage()
            );
        }
    }

    static void demonstrateComponents(Graph graph) {
        System.out.println("\n=== CONNECTED COMPONENTS ===");

        ComponentReport report = graph.connectedComponents();

        System.out.println("Components: " + report.components());
        System.out.println("Count: " + report.componentCount());
        System.out.println(
            "Largest component: " + report.largestComponentSize()
        );
        System.out.println(
            "Isolated vertices: " + report.isolatedVertices()
        );
    }

    // ---------------------------------------------------------
    // AUTOMATED VALIDATION
    // ---------------------------------------------------------

    static void runTests() {
        Graph graph = new Graph(GraphType.UNDIRECTED);

        graph.addEdge("A", "B");
        graph.addEdge("B", "C");
        graph.addVertex("D");

        PathResult result = graph.shortestPath("A", "C");

        if (!result.path().equals(List.of("A", "B", "C"))) {
            throw new AssertionError("BFS path test failed.");
        }

        if (graph.shortestPath("A", "D").reachable()) {
            throw new AssertionError("Unreachable path test failed.");
        }

        if (graph.connectedComponents().componentCount() != 2) {
            throw new AssertionError("Component test failed.");
        }

        if (!graph.connectedComponents()
                .isolatedVertices().equals(List.of("D"))) {
            throw new AssertionError("Isolated vertex test failed.");
        }

        Graph directed = new Graph(GraphType.DIRECTED);
        directed.addEdge("A", "B");
        directed.addEdge("B", "C");

        if (directed.analyzeDependencies().cyclic()) {
            throw new AssertionError("False cycle detected.");
        }

        directed.addEdge("C", "A");

        if (!directed.analyzeDependencies().cyclic()) {
            throw new AssertionError("Cycle detection failed.");
        }

        boolean invalidVertex = false;

        try {
            graph.shortestPath("A", "UNKNOWN");
        } catch (VertexNotFoundException exception) {
            invalidVertex = true;
        }

        if (!invalidVertex) {
            throw new AssertionError("Vertex validation failed.");
        }

        boolean directedComponentsRejected = false;

        try {
            directed.connectedComponents();
        } catch (GraphException exception) {
            directedComponentsRejected = true;
        }

        if (!directedComponentsRejected) {
            throw new AssertionError("Graph type validation failed.");
        }

        System.out.println("All Java 17 tests passed.");
    }

    public static void main(String[] args) {
        try {
            System.out.println("GRAPH ALGORITHMS I");

            Graph infrastructure = buildInfrastructure();

            demonstrateBfs(infrastructure);
            demonstrateDfs();
            demonstrateComponents(infrastructure);

            System.out.println("\n=== VALIDATION ===");
            runTests();

        } catch (RuntimeException exception) {
            System.err.println(
                "Execution failed: " + exception.getMessage()
            );
            System.exit(1);
        }
    }
}
