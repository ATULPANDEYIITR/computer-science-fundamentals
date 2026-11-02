import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.Set;

public class GraphGovernanceDemo {

    enum GraphType {
        DIRECTED,
        UNDIRECTED
    }

    record Edge(String source, String target, double weight) {}

    record ShortestPath(List<String> path, double distance) {}

    static final class GraphException extends RuntimeException {
        GraphException(String message) {
            super(message);
        }
    }

    interface GraphAnalyzer {
        List<String> breadthFirstSearch(String start);
        List<String> depthFirstSearch(String start);
        ShortestPath shortestPath(String start, String target);
        List<String> topologicalSort();
        boolean hasCycle();
    }

    static final class WeightedGraph implements GraphAnalyzer {
        private final GraphType type;
        private final Map<String, Map<String, Double>> adjacency = new HashMap<>();

        WeightedGraph(GraphType type) {
            this.type = type;
        }

        void addVertex(String vertex) {
            if (vertex == null || vertex.isBlank()) {
                throw new GraphException("Vertex must be non-empty.");
            }
            adjacency.putIfAbsent(vertex, new HashMap<>());
        }

        void addEdge(String source, String target, double weight) {
            if (!Double.isFinite(weight) || weight < 0) {
                throw new GraphException(
                    "Weighted shortest-path processing requires non-negative finite weights."
                );
            }

            addVertex(source);
            addVertex(target);

            adjacency.get(source).put(target, weight);

            if (type == GraphType.UNDIRECTED) {
                adjacency.get(target).put(source, weight);
            }
        }

        List<String> vertices() {
            return adjacency.keySet()
                    .stream()
                    .sorted()
                    .toList();
        }

        List<Edge> edges() {
            List<Edge> result = new ArrayList<>();

            for (Map.Entry<String, Map<String, Double>> entry : adjacency.entrySet()) {
                for (Map.Entry<String, Double> edge : entry.getValue().entrySet()) {
                    result.add(new Edge(
                        entry.getKey(),
                        edge.getKey(),
                        edge.getValue()
                    ));
                }
            }

            result.sort(
                Comparator.comparing(Edge::source)
                    .thenComparing(Edge::target)
            );

            return result;
        }

        @Override
        public List<String> breadthFirstSearch(String start) {
            requireVertex(start);

            ArrayDeque<String> queue = new ArrayDeque<>();
            Set<String> visited = new HashSet<>();
            List<String> order = new ArrayList<>();

            queue.add(start);
            visited.add(start);

            while (!queue.isEmpty()) {
                String current = queue.remove();
                order.add(current);

                adjacency.get(current)
                        .keySet()
                        .stream()
                        .sorted()
                        .forEach(neighbor -> {
                            if (visited.add(neighbor)) {
                                queue.add(neighbor);
                            }
                        });
            }

            return order;
        }

        @Override
        public List<String> depthFirstSearch(String start) {
            requireVertex(start);

            Set<String> visited = new HashSet<>();
            List<String> order = new ArrayList<>();

            depthFirstVisit(start, visited, order);
            return order;
        }

        private void depthFirstVisit(
            String vertex,
            Set<String> visited,
            List<String> order
        ) {
            visited.add(vertex);
            order.add(vertex);

            adjacency.get(vertex)
                    .keySet()
                    .stream()
                    .sorted()
                    .forEach(neighbor -> {
                        if (!visited.contains(neighbor)) {
                            depthFirstVisit(neighbor, visited, order);
                        }
                    });
        }

        @Override
        public ShortestPath shortestPath(String start, String target) {
            requireVertex(start);
            requireVertex(target);

            Map<String, Double> distance = new HashMap<>();
            Map<String, String> previous = new HashMap<>();

            for (String vertex : adjacency.keySet()) {
                distance.put(vertex, Double.POSITIVE_INFINITY);
            }

            distance.put(start, 0.0);

            record Node(String vertex, double distance) {}

            PriorityQueue<Node> queue =
                new PriorityQueue<>(Comparator.comparingDouble(Node::distance));

            queue.add(new Node(start, 0.0));

            while (!queue.isEmpty()) {
                Node current = queue.poll();

                if (current.distance() != distance.get(current.vertex())) {
                    continue;
                }

                for (Map.Entry<String, Double> edge :
                    adjacency.get(current.vertex()).entrySet()) {

                    String neighbor = edge.getKey();
                    double candidate =
                        current.distance() + edge.getValue();

                    if (candidate < distance.get(neighbor)) {
                        distance.put(neighbor, candidate);
                        previous.put(neighbor, current.vertex());
                        queue.add(new Node(neighbor, candidate));
                    }
                }
            }

            if (Double.isInfinite(distance.get(target))) {
                return new ShortestPath(List.of(), Double.POSITIVE_INFINITY);
            }

            List<String> path = new ArrayList<>();
            String current = target;

            while (current != null) {
                path.add(current);
                current = previous.get(current);
            }

            java.util.Collections.reverse(path);
            return new ShortestPath(path, distance.get(target));
        }

        @Override
        public List<String> topologicalSort() {
            if (type != GraphType.DIRECTED) {
                throw new GraphException(
                    "Topological sorting requires a directed graph."
                );
            }

            Map<String, Integer> indegree = new HashMap<>();

            for (String vertex : adjacency.keySet()) {
                indegree.put(vertex, 0);
            }

            for (Map<String, Double> targets : adjacency.values()) {
                for (String target : targets.keySet()) {
                    indegree.merge(target, 1, Integer::sum);
                }
            }

            PriorityQueue<String> ready = new PriorityQueue<>();

            for (Map.Entry<String, Integer> entry : indegree.entrySet()) {
                if (entry.getValue() == 0) {
                    ready.add(entry.getKey());
                }
            }

            List<String> order = new ArrayList<>();

            while (!ready.isEmpty()) {
                String current = ready.poll();
                order.add(current);

                for (String neighbor : adjacency.get(current).keySet()) {
                    int remaining = indegree.merge(
                        neighbor,
                        -1,
                        Integer::sum
                    );

                    if (remaining == 0) {
                        ready.add(neighbor);
                    }
                }
            }

            if (order.size() != adjacency.size()) {
                throw new GraphException(
                    "Directed graph contains a cycle."
                );
            }

            return order;
        }

        @Override
        public boolean hasCycle() {
            Set<String> visiting = new HashSet<>();
            Set<String> visited = new HashSet<>();

            for (String vertex : adjacency.keySet()) {
                if (!visited.contains(vertex)
                    && hasDirectedCycle(vertex, visiting, visited)) {
                    return true;
                }
            }

            return false;
        }

        private boolean hasDirectedCycle(
            String vertex,
            Set<String> visiting,
            Set<String> visited
        ) {
            if (visiting.contains(vertex)) {
                return true;
            }

            if (visited.contains(vertex)) {
                return false;
            }

            visiting.add(vertex);

            for (String neighbor : adjacency.get(vertex).keySet()) {
                if (hasDirectedCycle(neighbor, visiting, visited)) {
                    return true;
                }
            }

            visiting.remove(vertex);
            visited.add(vertex);
            return false;
        }

        private void requireVertex(String vertex) {
            if (!adjacency.containsKey(vertex)) {
                throw new GraphException("Unknown vertex: " + vertex);
            }
        }
    }

    static final class RouteService {
        private final WeightedGraph graph;

        RouteService(WeightedGraph graph) {
            this.graph = graph;
        }

        void printRoute(String source, String target) {
            ShortestPath result = graph.shortestPath(source, target);

            if (result.path().isEmpty()) {
                System.out.println("No route exists.");
                return;
            }

            System.out.println(
                "Route: " + String.join(" -> ", result.path())
            );
            System.out.printf(
                "Travel time: %.1f hours%n",
                result.distance()
            );
        }
    }

    private static WeightedGraph buildNetwork() {
        WeightedGraph graph = new WeightedGraph(GraphType.DIRECTED);

        List<Edge> routes = List.of(
            new Edge("Lucknow", "Kanpur", 1.5),
            new Edge("Lucknow", "Ayodhya", 2.0),
            new Edge("Kanpur", "Agra", 3.0),
            new Edge("Ayodhya", "Varanasi", 2.5),
            new Edge("Agra", "Delhi", 2.0),
            new Edge("Varanasi", "Patna", 4.0),
            new Edge("Delhi", "Jaipur", 3.0),
            new Edge("Delhi", "Patna", 5.0),
            new Edge("Jaipur", "Ahmedabad", 4.0),
            new Edge("Patna", "Kolkata", 5.0),
            new Edge("Ahmedabad", "Mumbai", 6.0),
            new Edge("Kolkata", "Guwahati", 7.0),
            new Edge("Mumbai", "Bengaluru", 7.0)
        );

        routes.forEach(edge ->
            graph.addEdge(edge.source(), edge.target(), edge.weight())
        );

        return graph;
    }

    public static void main(String[] args) {
        try {
            WeightedGraph graph = buildNetwork();

            System.out.println("DIRECTED WEIGHTED GRAPH");
            System.out.println("=======================");

            System.out.println("\nEdges:");
            graph.edges().forEach(edge ->
                System.out.printf(
                    "  %s -> %s (%.1f hours)%n",
                    edge.source(),
                    edge.target(),
                    edge.weight()
                )
            );

            System.out.println("\nBFS:");
            System.out.println(
                String.join(" -> ", graph.breadthFirstSearch("Lucknow"))
            );

            System.out.println("\nDFS:");
            System.out.println(
                String.join(" -> ", graph.depthFirstSearch("Lucknow"))
            );

            System.out.println("\nShortest route:");
            RouteService service = new RouteService(graph);
            service.printRoute("Lucknow", "Mumbai");

            System.out.println("\nCycle present: " + graph.hasCycle());

            WeightedGraph workflow =
                new WeightedGraph(GraphType.DIRECTED);

            workflow.addEdge("Design", "Implement", 1);
            workflow.addEdge("Implement", "Test", 1);
            workflow.addEdge("Test", "Deploy", 1);

            System.out.println("\nTopological workflow:");
            System.out.println(
                String.join(" -> ", workflow.topologicalSort())
            );

            workflow.addEdge("Deploy", "Design", 1);

            try {
                workflow.topologicalSort();
            } catch (GraphException exception) {
                System.out.println(
                    "Cycle validation: " + exception.getMessage()
                );
            }

            try {
                graph.addEdge("Delhi", "Mumbai", -4);
            } catch (GraphException exception) {
                System.out.println(
                    "Weight validation: " + exception.getMessage()
                );
            }

            double expected = 18.5;
            double actual =
                graph.shortestPath("Lucknow", "Mumbai").distance();

            if (Math.abs(expected - actual) > 0.000001) {
                throw new GraphException(
                    "Shortest-path assertion failed."
                );
            }

            System.out.println("\nComplexity:");
            System.out.println("  Adjacency-list storage: O(V + E)");
            System.out.println("  BFS/DFS: O(V + E)");
            System.out.println("  Dijkstra: O((V + E) log V)");
            System.out.println("  Topological sort: O(V + E)");

        } catch (GraphException exception) {
            System.err.println("Graph error: " + exception.getMessage());
            System.exit(1);
        }
    }
}
