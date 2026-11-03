import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Deque;
import java.util.EnumMap;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.PriorityQueue;
import java.util.Set;
import java.util.TreeSet;
import java.util.regex.Pattern;

/*
 * Graph Traversal: enterprise service dependency analysis.
 *
 * Java 17 implementation featuring:
 * - Immutable dependency graph snapshots
 * - Explicit domain records and criticality levels
 * - BFS for service outage impact analysis
 * - DFS for dependency inspection
 * - Shortest dependency chains
 * - Topological deployment ordering
 * - Cycle detection
 * - Identifier validation and domain exceptions
 *
 * Compile:
 *   javac GraphTraversalDemo.java
 *
 * Run:
 *   java GraphTraversalDemo
 */

public class GraphTraversalDemo {

    private static final Pattern SERVICE_ID_PATTERN =
        Pattern.compile("[A-Za-z0-9][A-Za-z0-9._-]{0,63}");

    enum Criticality {
        CRITICAL,
        HIGH,
        MEDIUM,
        LOW
    }

    static void validateServiceId(String id) {
        if (id == null || !SERVICE_ID_PATTERN.matcher(id).matches()) {
            throw new IllegalArgumentException(
                "Invalid service identifier: " + id
            );
        }
    }

    record ServiceNode(String id, Criticality criticality) {
        ServiceNode {
            validateServiceId(id);
            Objects.requireNonNull(
                criticality,
                "Criticality cannot be null."
            );
        }
    }

    record TraversalResult(
        String start,
        List<String> order,
        Map<String, String> parent,
        Map<String, Integer> depth
    ) {
        TraversalResult {
            order = List.copyOf(order);

            // The root has a null parent, so Map.copyOf cannot be used.
            parent = Collections.unmodifiableMap(
                new LinkedHashMap<>(parent)
            );

            depth = Collections.unmodifiableMap(
                new LinkedHashMap<>(depth)
            );
        }

        List<String> pathTo(String target) {
            if (!parent.containsKey(target)) {
                return null;
            }

            List<String> path = new ArrayList<>();
            String current = target;

            while (current != null) {
                path.add(current);
                current = parent.get(current);
            }

            Collections.reverse(path);
            return List.copyOf(path);
        }
    }

    record ImpactReport(
        String failedService,
        List<String> affectedServices,
        Map<String, Integer> hopDistances,
        Map<Criticality, Long> affectedByCriticality
    ) {
        ImpactReport {
            affectedServices = List.copyOf(affectedServices);
            hopDistances = Map.copyOf(hopDistances);

            EnumMap<Criticality, Long> copy =
                new EnumMap<>(Criticality.class);

            copy.putAll(affectedByCriticality);
            affectedByCriticality = Collections.unmodifiableMap(copy);
        }
    }

    static class GraphDomainException extends RuntimeException {
        GraphDomainException(String message) {
            super(message);
        }
    }

    static class CycleDetectedException extends GraphDomainException {
        private final Set<String> blockedServices;

        CycleDetectedException(Set<String> blockedServices) {
            super("Dependency cycle prevents topological ordering: "
                + blockedServices);

            this.blockedServices = Set.copyOf(blockedServices);
        }

        Set<String> blockedServices() {
            return blockedServices;
        }
    }

    /*
     * The graph stores dependency -> consumer edges.
     *
     * Example:
     * database -> orders-api
     *
     * If the database fails, BFS follows outgoing edges to identify
     * downstream services that may be affected.
     */
    static final class DependencyGraph {

        private final Map<String, ServiceNode> nodes;
        private final Map<String, List<String>> adjacency;

        private DependencyGraph(
            Map<String, ServiceNode> sourceNodes,
            Map<String, Set<String>> sourceAdjacency
        ) {
            Map<String, ServiceNode> nodeCopy =
                new LinkedHashMap<>(sourceNodes);

            Map<String, List<String>> adjacencyCopy =
                new LinkedHashMap<>();

            for (String id : nodeCopy.keySet()) {
                List<String> neighbors = new ArrayList<>(
                    sourceAdjacency.getOrDefault(id, Set.of())
                );

                Collections.sort(neighbors);
                adjacencyCopy.put(id, List.copyOf(neighbors));
            }

            this.nodes = Collections.unmodifiableMap(nodeCopy);
            this.adjacency = Collections.unmodifiableMap(adjacencyCopy);
        }

        boolean contains(String serviceId) {
            return nodes.containsKey(serviceId);
        }

        ServiceNode node(String serviceId) {
            ServiceNode node = nodes.get(serviceId);

            if (node == null) {
                throw new GraphDomainException(
                    "Unknown service: " + serviceId
                );
            }

            return node;
        }

        List<String> neighbors(String serviceId) {
            List<String> result = adjacency.get(serviceId);

            if (result == null) {
                throw new GraphDomainException(
                    "Unknown service: " + serviceId
                );
            }

            return result;
        }

        Set<String> serviceIds() {
            return nodes.keySet();
        }

        static final class Builder {

            private final Map<String, ServiceNode> nodes =
                new LinkedHashMap<>();

            private final Map<String, Set<String>> adjacency =
                new LinkedHashMap<>();

            Builder addService(ServiceNode node) {
                Objects.requireNonNull(node, "Service node is required.");

                if (nodes.putIfAbsent(node.id(), node) != null) {
                    throw new GraphDomainException(
                        "Duplicate service: " + node.id()
                    );
                }

                adjacency.put(node.id(), new TreeSet<>());
                return this;
            }

            Builder addDependency(
                String dependency,
                String dependent
            ) {
                validateServiceId(dependency);
                validateServiceId(dependent);

                if (!nodes.containsKey(dependency)) {
                    throw new GraphDomainException(
                        "Dependency does not exist: " + dependency
                    );
                }

                if (!nodes.containsKey(dependent)) {
                    throw new GraphDomainException(
                        "Dependent service does not exist: " + dependent
                    );
                }

                if (dependency.equals(dependent)) {
                    throw new GraphDomainException(
                        "A service cannot depend on itself."
                    );
                }

                adjacency.get(dependency).add(dependent);
                return this;
            }

            DependencyGraph build() {
                return new DependencyGraph(nodes, adjacency);
            }
        }
    }

    interface TraversalStrategy {
        TraversalResult traverse(
            DependencyGraph graph,
            String start
        );
    }

    static final class BreadthFirstTraversal
        implements TraversalStrategy {

        @Override
        public TraversalResult traverse(
            DependencyGraph graph,
            String start
        ) {
            graph.node(start);

            Deque<String> queue = new ArrayDeque<>();
            List<String> order = new ArrayList<>();

            Map<String, String> parent = new LinkedHashMap<>();
            Map<String, Integer> depth = new LinkedHashMap<>();

            // containsKey distinguishes a discovered root from an
            // undiscovered vertex even though the root parent is null.
            parent.put(start, null);
            depth.put(start, 0);
            queue.addLast(start);

            while (!queue.isEmpty()) {
                String current = queue.removeFirst();
                order.add(current);

                for (String neighbor : graph.neighbors(current)) {
                    if (parent.containsKey(neighbor)) {
                        continue;
                    }

                    parent.put(neighbor, current);
                    depth.put(neighbor, depth.get(current) + 1);
                    queue.addLast(neighbor);
                }
            }

            return new TraversalResult(
                start,
                order,
                parent,
                depth
            );
        }
    }

    static final class DepthFirstTraversal
        implements TraversalStrategy {

        private record Frame(
            String serviceId,
            Iterator<String> neighbors
        ) {}

        @Override
        public TraversalResult traverse(
            DependencyGraph graph,
            String start
        ) {
            graph.node(start);

            List<String> order = new ArrayList<>();

            Map<String, String> parent = new LinkedHashMap<>();
            Map<String, Integer> depth = new LinkedHashMap<>();

            Deque<Frame> stack = new ArrayDeque<>();

            parent.put(start, null);
            depth.put(start, 0);
            order.add(start);

            stack.push(
                new Frame(start, graph.neighbors(start).iterator())
            );

            while (!stack.isEmpty()) {
                Frame frame = stack.peek();

                if (!frame.neighbors().hasNext()) {
                    stack.pop();
                    continue;
                }

                String neighbor = frame.neighbors().next();

                if (parent.containsKey(neighbor)) {
                    continue;
                }

                parent.put(neighbor, frame.serviceId());
                depth.put(
                    neighbor,
                    depth.get(frame.serviceId()) + 1
                );

                order.add(neighbor);

                stack.push(
                    new Frame(
                        neighbor,
                        graph.neighbors(neighbor).iterator()
                    )
                );
            }

            return new TraversalResult(
                start,
                order,
                parent,
                depth
            );
        }
    }

    static final class TraversalService {

        private final TraversalStrategy breadthFirst =
            new BreadthFirstTraversal();

        private final TraversalStrategy depthFirst =
            new DepthFirstTraversal();

        TraversalResult breadthFirst(
            DependencyGraph graph,
            String start
        ) {
            return breadthFirst.traverse(graph, start);
        }

        TraversalResult depthFirst(
            DependencyGraph graph,
            String start
        ) {
            return depthFirst.traverse(graph, start);
        }

        List<String> topologicalOrder(DependencyGraph graph) {
            Map<String, Integer> indegree = new LinkedHashMap<>();

            for (String serviceId : graph.serviceIds()) {
                indegree.put(serviceId, 0);
            }

            for (String serviceId : graph.serviceIds()) {
                for (String dependent : graph.neighbors(serviceId)) {
                    indegree.merge(dependent, 1, Integer::sum);
                }
            }

            PriorityQueue<String> ready = new PriorityQueue<>();

            for (Map.Entry<String, Integer> entry : indegree.entrySet()) {
                if (entry.getValue() == 0) {
                    ready.add(entry.getKey());
                }
            }

            List<String> result = new ArrayList<>();

            while (!ready.isEmpty()) {
                String current = ready.remove();
                result.add(current);

                for (String dependent : graph.neighbors(current)) {
                    int updated = indegree.merge(
                        dependent,
                        -1,
                        Integer::sum
                    );

                    if (updated == 0) {
                        ready.add(dependent);
                    }
                }
            }

            if (result.size() != graph.serviceIds().size()) {
                Set<String> blocked = new TreeSet<>();

                for (Map.Entry<String, Integer> entry : indegree.entrySet()) {
                    if (entry.getValue() > 0) {
                        blocked.add(entry.getKey());
                    }
                }

                throw new CycleDetectedException(blocked);
            }

            return List.copyOf(result);
        }
    }

    static final class ImpactAssessmentService {

        private final TraversalService traversalService;

        ImpactAssessmentService(TraversalService traversalService) {
            this.traversalService = Objects.requireNonNull(
                traversalService,
                "Traversal service is required."
            );
        }

        ImpactReport assess(
            DependencyGraph graph,
            String failedService
        ) {
            TraversalResult traversal =
                traversalService.breadthFirst(graph, failedService);

            List<String> affected = traversal.order().stream()
                .filter(service -> !service.equals(failedService))
                .toList();

            EnumMap<Criticality, Long> counts =
                new EnumMap<>(Criticality.class);

            for (String serviceId : affected) {
                Criticality criticality =
                    graph.node(serviceId).criticality();

                counts.merge(criticality, 1L, Long::sum);
            }

            Map<String, Integer> affectedDistances =
                new LinkedHashMap<>();

            for (String serviceId : affected) {
                affectedDistances.put(
                    serviceId,
                    traversal.depth().get(serviceId)
                );
            }

            return new ImpactReport(
                failedService,
                affected,
                affectedDistances,
                counts
            );
        }
    }

    private static DependencyGraph buildProductionGraph() {
        DependencyGraph.Builder builder =
            new DependencyGraph.Builder();

        builder
            .addService(new ServiceNode("customer-db", Criticality.CRITICAL))
            .addService(new ServiceNode("identity-service", Criticality.CRITICAL))
            .addService(new ServiceNode("orders-api", Criticality.HIGH))
            .addService(new ServiceNode("billing-api", Criticality.HIGH))
            .addService(new ServiceNode("checkout-api", Criticality.HIGH))
            .addService(new ServiceNode("web-frontend", Criticality.MEDIUM))
            .addService(new ServiceNode("finance-report", Criticality.LOW));

        builder
            .addDependency("customer-db", "orders-api")
            .addDependency("customer-db", "billing-api")
            .addDependency("orders-api", "checkout-api")
            .addDependency("billing-api", "checkout-api")
            .addDependency("billing-api", "finance-report")
            .addDependency("checkout-api", "web-frontend")
            .addDependency("identity-service", "checkout-api");

        return builder.build();
    }

    private static void demonstrateCycleDetection(
        TraversalService traversalService
    ) {
        DependencyGraph cycleGraph =
            new DependencyGraph.Builder()
                .addService(new ServiceNode("service-a", Criticality.HIGH))
                .addService(new ServiceNode("service-b", Criticality.HIGH))
                .addService(new ServiceNode("service-c", Criticality.MEDIUM))
                .addDependency("service-a", "service-b")
                .addDependency("service-b", "service-c")
                .addDependency("service-c", "service-a")
                .build();

        try {
            traversalService.topologicalOrder(cycleGraph);

            throw new AssertionError(
                "Expected a dependency cycle to be detected."
            );
        } catch (CycleDetectedException exception) {
            System.out.println(
                "\nExpected cycle detection: "
                    + exception.getMessage()
            );
        }
    }

    public static void main(String[] args) {
        try {
            DependencyGraph graph = buildProductionGraph();

            TraversalService traversalService =
                new TraversalService();

            ImpactAssessmentService impactService =
                new ImpactAssessmentService(traversalService);

            TraversalResult bfs = traversalService.breadthFirst(
                graph,
                "customer-db"
            );

            TraversalResult dfs = traversalService.depthFirst(
                graph,
                "customer-db"
            );

            System.out.println("ENTERPRISE SERVICE DEPENDENCY ANALYSIS");

            System.out.println("\nBFS outage-impact order:");
            System.out.println(bfs.order());

            System.out.println("\nDFS dependency inspection order:");
            System.out.println(dfs.order());

            System.out.println("\nShortest dependency chain:");
            System.out.println(
                bfs.pathTo("web-frontend")
            );

            ImpactReport report = impactService.assess(
                graph,
                "customer-db"
            );

            System.out.println("\nAffected services:");
            System.out.println(report.affectedServices());

            System.out.println("\nHop distances:");
            System.out.println(report.hopDistances());

            System.out.println("\nAffected services by criticality:");
            System.out.println(report.affectedByCriticality());

            System.out.println("\nValid deployment order:");
            System.out.println(
                traversalService.topologicalOrder(graph)
            );

            if (bfs.depth().get("web-frontend") != 3) {
                throw new AssertionError(
                    "Unexpected dependency distance."
                );
            }

            if (report.affectedServices().size() != 5) {
                throw new AssertionError(
                    "Unexpected number of affected services."
                );
            }

            if (bfs.pathTo("unknown-service") != null) {
                throw new AssertionError(
                    "An unreachable service must not have a path."
                );
            }

            demonstrateCycleDetection(traversalService);

            try {
                validateServiceId("invalid service id");

                throw new AssertionError(
                    "Invalid service identifier was accepted."
                );
            } catch (IllegalArgumentException expected) {
                System.out.println(
                    "\nInvalid service identifier handled correctly."
                );
            }

            System.out.println(
                "\nAll enterprise graph traversal checks passed."
            );
        } catch (GraphDomainException exception) {
            System.err.println(
                "Graph processing failed: " + exception.getMessage()
            );
            System.exit(1);
        }
    }
}
