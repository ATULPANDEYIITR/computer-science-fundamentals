import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/*
 * Routing Fundamentals
 * Enterprise-oriented routing management system.
 *
 * Java 17
 * No external dependencies.
 *
 * Features:
 * - Typed routing domain
 * - Static route configuration
 * - OSPF-style shortest-path calculation
 * - Distance-vector calculation
 * - Routing policy evaluation
 * - Longest prefix matching
 * - Administrative distance
 * - Link-state changes
 * - Packet forwarding decisions
 * - Route validation and error handling
 */

public class RoutingEnterprise {

    enum Protocol {
        STATIC(1),
        OSPF(110),
        RIP(120);

        private final int administrativeDistance;

        Protocol(int distance) {
            this.administrativeDistance = distance;
        }

        public int administrativeDistance() {
            return administrativeDistance;
        }
    }

    enum LinkState {
        UP,
        DOWN
    }

    static class RoutingException extends RuntimeException {
        RoutingException(String message) {
            super(message);
        }
    }

    static class ValidationException extends RoutingException {
        ValidationException(String message) {
            super(message);
        }
    }

    static class RouteNotFoundException extends RoutingException {
        RouteNotFoundException(String message) {
            super(message);
        }
    }

    record IPv4Network(long network, int prefix) {

        IPv4Network {
            if (prefix < 0 || prefix > 32) {
                throw new ValidationException(
                    "Prefix must be between 0 and 32."
                );
            }
        }

        static long parseAddress(String address) {
            String[] parts = address.split("\\.", -1);

            if (parts.length != 4) {
                throw new ValidationException(
                    "Invalid IPv4 address: " + address
                );
            }

            long result = 0;

            for (String part : parts) {
                if (!part.matches("\\d{1,3}")) {
                    throw new ValidationException(
                        "Invalid IPv4 octet."
                    );
                }

                int value = Integer.parseInt(part);

                if (value > 255) {
                    throw new ValidationException(
                        "IPv4 octet exceeds 255."
                    );
                }

                result = (result << 8) | value;
            }

            return result;
        }

        static IPv4Network parse(String cidr) {
            String[] parts = cidr.split("/", -1);

            if (parts.length != 2) {
                throw new ValidationException(
                    "CIDR notation is required."
                );
            }

            long address = parseAddress(parts[0]);

            int prefix;

            try {
                prefix = Integer.parseInt(parts[1]);
            } catch (NumberFormatException exception) {
                throw new ValidationException(
                    "Invalid prefix length."
                );
            }

            if (prefix < 0 || prefix > 32) {
                throw new ValidationException(
                    "Invalid prefix length."
                );
            }

            long mask = prefix == 0
                ? 0L
                : (0xFFFFFFFFL << (32 - prefix))
                    & 0xFFFFFFFFL;

            return new IPv4Network(address & mask, prefix);
        }

        boolean contains(String address) {
            long ip = parseAddress(address);

            long mask = prefix == 0
                ? 0L
                : (0xFFFFFFFFL << (32 - prefix))
                    & 0xFFFFFFFFL;

            return (ip & mask) == network;
        }

        @Override
        public String toString() {
            return ((network >>> 24) & 255) + "." +
                ((network >>> 16) & 255) + "." +
                ((network >>> 8) & 255) + "." +
                (network & 255) + "/" + prefix;
        }
    }

    record Link(
        String destination,
        double cost,
        LinkState state
    ) {
        Link {
            Objects.requireNonNull(destination);
            Objects.requireNonNull(state);

            if (!Double.isFinite(cost) || cost < 0) {
                throw new ValidationException(
                    "Link cost must be non-negative."
                );
            }
        }
    }

    record Route(
        IPv4Network network,
        String nextHop,
        String interfaceName,
        double metric,
        Protocol protocol,
        boolean active
    ) {
        Route {
            Objects.requireNonNull(network);
            Objects.requireNonNull(interfaceName);
            Objects.requireNonNull(protocol);

            if (!Double.isFinite(metric) || metric < 0) {
                throw new ValidationException(
                    "Invalid route metric."
                );
            }
        }

        int administrativeDistance() {
            return protocol.administrativeDistance();
        }
    }

    record PathResult(
        double cost,
        String nextHop
    ) {
        static PathResult unreachable() {
            return new PathResult(
                Double.POSITIVE_INFINITY,
                null
            );
        }

        boolean reachable() {
            return Double.isFinite(cost);
        }
    }

    static class NetworkTopology {

        private final Map<String, Map<String, Link>> adjacency =
            new LinkedHashMap<>();

        public synchronized void addRouter(String id) {
            validateRouterId(id);
            adjacency.putIfAbsent(id, new LinkedHashMap<>());
        }

        private void validateRouterId(String id) {
            if (
                id == null ||
                !id.matches("[A-Za-z0-9_-]{1,32}")
            ) {
                throw new ValidationException(
                    "Invalid router identifier."
                );
            }
        }

        public synchronized void addLink(
            String source,
            String destination,
            double cost,
            boolean bidirectional
        ) {
            validateRouterId(source);
            validateRouterId(destination);

            if (source.equals(destination)) {
                throw new ValidationException(
                    "Self-links are not supported."
                );
            }

            if (!Double.isFinite(cost) || cost < 0) {
                throw new ValidationException(
                    "Invalid link cost."
                );
            }

            addRouter(source);
            addRouter(destination);

            adjacency.get(source).put(
                destination,
                new Link(destination, cost, LinkState.UP)
            );

            if (bidirectional) {
                addLink(destination, source, cost, false);
            }
        }

        public synchronized void setLinkState(
            String source,
            String destination,
            LinkState state
        ) {
            Map<String, Link> links = adjacency.get(source);

            if (links == null || !links.containsKey(destination)) {
                throw new ValidationException(
                    "Link does not exist."
                );
            }

            Link old = links.get(destination);

            links.put(
                destination,
                new Link(destination, old.cost(), state)
            );
        }

        public synchronized List<Link> neighbors(String router) {
            Map<String, Link> links = adjacency.get(router);

            if (links == null) {
                throw new ValidationException(
                    "Unknown router: " + router
                );
            }

            return links.values()
                .stream()
                .filter(link -> link.state() == LinkState.UP)
                .toList();
        }

        public synchronized List<String> routers() {
            return List.copyOf(adjacency.keySet());
        }

        public synchronized boolean containsRouter(String id) {
            return adjacency.containsKey(id);
        }
    }

    static class RoutingTable {

        private final String routerId;

        private final List<Route> routes =
            new ArrayList<>();

        RoutingTable(String routerId) {
            this.routerId = routerId;
        }

        public synchronized void add(Route route) {
            Objects.requireNonNull(route);

            routes.removeIf(existing ->
                existing.network().equals(route.network()) &&
                existing.protocol() == route.protocol()
            );

            routes.add(route);
        }

        public synchronized boolean remove(
            IPv4Network network,
            Protocol protocol
        ) {
            return routes.removeIf(route ->
                route.network().equals(network) &&
                route.protocol() == protocol
            );
        }

        public synchronized Route lookup(String destination) {
            IPv4Network.parseAddress(destination);

            return routes.stream()
                .filter(Route::active)
                .filter(route ->
                    route.network().contains(destination)
                )
                .sorted(
                    Comparator
                        .comparingInt(
                            (Route route) ->
                                route.network().prefix()
                        )
                        .reversed()
                        .thenComparingInt(
                            Route::administrativeDistance
                        )
                        .thenComparingDouble(Route::metric)
                )
                .findFirst()
                .orElseThrow(() ->
                    new RouteNotFoundException(
                        "No route for " + destination
                    )
                );
        }

        public synchronized List<Route> getRoutes() {
            return List.copyOf(routes);
        }

        public synchronized void display() {
            System.out.println(
                "\nRouting Table: " + routerId
            );

            System.out.printf(
                "%-20s %-14s %-12s %-10s %-10s%n",
                "Network",
                "Next Hop",
                "Interface",
                "Metric",
                "Protocol"
            );

            for (Route route : routes) {
                if (!route.active()) continue;

                System.out.printf(
                    "%-20s %-14s %-12s %-10.2f %-10s%n",
                    route.network(),
                    route.nextHop() == null
                        ? "DIRECT"
                        : route.nextHop(),
                    route.interfaceName(),
                    route.metric(),
                    route.protocol()
                );
            }
        }
    }

    static class RoutingAlgorithms {

        private record QueueNode(
            String router,
            double cost
        ) {}

        public static Map<String, PathResult> dijkstra(
            NetworkTopology topology,
            String source
        ) {
            if (!topology.containsRouter(source)) {
                throw new ValidationException(
                    "Unknown source router."
                );
            }

            Map<String, Double> distances =
                new HashMap<>();

            Map<String, String> nextHops =
                new HashMap<>();

            for (String router : topology.routers()) {
                distances.put(router, Double.POSITIVE_INFINITY);
                nextHops.put(router, null);
            }

            distances.put(source, 0.0);

            PriorityQueue<QueueNode> queue =
                new PriorityQueue<>(
                    Comparator.comparingDouble(QueueNode::cost)
                );

            Set<String> visited = new HashSet<>();

            queue.add(new QueueNode(source, 0));

            while (!queue.isEmpty()) {
                QueueNode current = queue.poll();

                if (!visited.add(current.router())) {
                    continue;
                }

                if (
                    current.cost() >
                    distances.get(current.router())
                ) {
                    continue;
                }

                for (Link link :
                    topology.neighbors(current.router())) {

                    double candidate =
                        current.cost() + link.cost();

                    if (
                        candidate <
                        distances.get(link.destination())
                    ) {
                        distances.put(
                            link.destination(),
                            candidate
                        );

                        nextHops.put(
                            link.destination(),
                            current.router().equals(source)
                                ? link.destination()
                                : nextHops.get(current.router())
                        );

                        queue.add(
                            new QueueNode(
                                link.destination(),
                                candidate
                            )
                        );
                    }
                }
            }

            Map<String, PathResult> results =
                new LinkedHashMap<>();

            for (String router : topology.routers()) {
                results.put(
                    router,
                    new PathResult(
                        distances.get(router),
                        nextHops.get(router)
                    )
                );
            }

            return Collections.unmodifiableMap(results);
        }

        public static Map<String, PathResult> distanceVector(
            NetworkTopology topology,
            String source
        ) {
            if (!topology.containsRouter(source)) {
                throw new ValidationException(
                    "Unknown source router."
                );
            }

            List<String> routers = topology.routers();

            Map<String, PathResult> current =
                new LinkedHashMap<>();

            for (String router : routers) {
                current.put(
                    router,
                    PathResult.unreachable()
                );
            }

            current.put(source, new PathResult(0, null));

            // Bellman-Ford relaxation using a previous-round snapshot.
            for (int iteration = 0;
                 iteration < routers.size() - 1;
                 iteration++) {

                Map<String, PathResult> previous =
                    new LinkedHashMap<>(current);

                boolean changed = false;

                for (String router : routers) {
                    PathResult sourcePath = previous.get(router);

                    if (!sourcePath.reachable()) continue;

                    for (Link link : topology.neighbors(router)) {
                        double candidate =
                            sourcePath.cost() + link.cost();

                        PathResult existing =
                            current.get(link.destination());

                        if (candidate < existing.cost()) {
                            String hop = router.equals(source)
                                ? link.destination()
                                : sourcePath.nextHop();

                            current.put(
                                link.destination(),
                                new PathResult(candidate, hop)
                            );

                            changed = true;
                        }
                    }
                }

                if (!changed) break;
            }

            return Collections.unmodifiableMap(current);
        }
    }

    static class RouterService {

        private final NetworkTopology topology;

        private final Map<String, RoutingTable> tables =
            new ConcurrentHashMap<>();

        RouterService(NetworkTopology topology) {
            this.topology = topology;
        }

        public void registerRouter(String id) {
            topology.addRouter(id);
            tables.putIfAbsent(id, new RoutingTable(id));
        }

        public RoutingTable getTable(String router) {
            RoutingTable table = tables.get(router);

            if (table == null) {
                throw new ValidationException(
                    "Unknown router: " + router
                );
            }

            return table;
        }

        public void installStaticRoute(
            String router,
            String network,
            String nextHop,
            String interfaceName,
            double metric
        ) {
            if (
                nextHop != null &&
                !topology.containsRouter(nextHop)
            ) {
                throw new ValidationException(
                    "Invalid next-hop router."
                );
            }

            getTable(router).add(
                new Route(
                    IPv4Network.parse(network),
                    nextHop,
                    interfaceName,
                    metric,
                    Protocol.STATIC,
                    true
                )
            );
        }

        public void installDynamicRoutes(
            String router,
            Map<String, String> networks,
            Protocol protocol
        ) {
            Map<String, PathResult> paths;

            if (protocol == Protocol.OSPF) {
                paths = RoutingAlgorithms.dijkstra(
                    topology,
                    router
                );
            } else if (protocol == Protocol.RIP) {
                paths = RoutingAlgorithms.distanceVector(
                    topology,
                    router
                );
            } else {
                throw new ValidationException(
                    "Use static route installation for STATIC."
                );
            }

            RoutingTable table = getTable(router);

            for (Map.Entry<String, String> entry :
                networks.entrySet()) {

                PathResult path = paths.get(entry.getKey());

                if (path == null) {
                    throw new ValidationException(
                        "Unknown destination router."
                    );
                }

                if (!path.reachable()) continue;

                table.add(
                    new Route(
                        IPv4Network.parse(entry.getValue()),
                        path.nextHop(),
                        "eth-" + path.nextHop(),
                        path.cost(),
                        protocol,
                        true
                    )
                );
            }
        }

        public Route forward(
            String router,
            String destination
        ) {
            return getTable(router).lookup(destination);
        }
    }

    private static void demonstrate() {

        NetworkTopology topology =
            new NetworkTopology();

        RouterService service =
            new RouterService(topology);

        for (String id :
            List.of("R1", "R2", "R3", "R4")) {
            service.registerRouter(id);
        }

        topology.addLink("R1", "R2", 2, true);
        topology.addLink("R1", "R3", 5, true);
        topology.addLink("R2", "R3", 1, true);
        topology.addLink("R2", "R4", 7, true);
        topology.addLink("R3", "R4", 2, true);

        System.out.println("DIJKSTRA SHORTEST PATHS");

        Map<String, PathResult> ospf =
            RoutingAlgorithms.dijkstra(topology, "R1");

        ospf.forEach((router, result) ->
            System.out.printf(
                "R1 -> %s: cost=%.2f, nextHop=%s%n",
                router,
                result.cost(),
                Objects.toString(result.nextHop(), "LOCAL")
            )
        );

        System.out.println("\nDISTANCE VECTOR");

        Map<String, PathResult> rip =
            RoutingAlgorithms.distanceVector(topology, "R1");

        rip.forEach((router, result) ->
            System.out.printf(
                "R1 -> %s: cost=%.2f, nextHop=%s%n",
                router,
                result.cost(),
                Objects.toString(result.nextHop(), "LOCAL")
            )
        );

        System.out.println("\nSTATIC ROUTING");

        service.installStaticRoute(
            "R1",
            "192.168.10.0/24",
            "R2",
            "eth0",
            1
        );

        System.out.println(
            service.forward(
                "R1",
                "192.168.10.25"
            )
        );

        System.out.println("\nDYNAMIC OSPF");

        service.installDynamicRoutes(
            "R1",
            Map.of(
                "R2", "10.0.2.0/24",
                "R3", "10.0.3.0/24",
                "R4", "10.0.4.0/24"
            ),
            Protocol.OSPF
        );

        service.getTable("R1").display();

        System.out.println("\nLINK FAILURE");

        topology.setLinkState(
            "R2",
            "R3",
            LinkState.DOWN
        );

        Map<String, PathResult> updated =
            RoutingAlgorithms.dijkstra(topology, "R1");

        System.out.println(
            "New route to R4: " + updated.get("R4")
        );

        System.out.println("\nLONGEST PREFIX MATCHING");

        RoutingTable table = new RoutingTable("R5");

        table.add(new Route(
            IPv4Network.parse("192.168.0.0/16"),
            "R2",
            "eth0",
            10,
            Protocol.STATIC,
            true
        ));

        table.add(new Route(
            IPv4Network.parse("192.168.10.0/24"),
            "R3",
            "eth1",
            5,
            Protocol.OSPF,
            true
        ));

        System.out.println(
            table.lookup("192.168.10.50")
        );

        System.out.println("\nERROR HANDLING");

        try {
            table.lookup("172.16.0.10");
        } catch (RouteNotFoundException exception) {
            System.out.println(exception.getMessage());
        }
    }

    private static void runTests() {

        NetworkTopology topology =
            new NetworkTopology();

        topology.addLink("A", "B", 2, true);
        topology.addLink("B", "C", 3, true);
        topology.addLink("A", "C", 10, true);

        Map<String, PathResult> dijkstra =
            RoutingAlgorithms.dijkstra(topology, "A");

        Map<String, PathResult> vector =
            RoutingAlgorithms.distanceVector(topology, "A");

        if (dijkstra.get("C").cost() != 5 ||
            vector.get("C").cost() != 5) {
            throw new AssertionError("Path calculation failed.");
        }

        if (!"B".equals(dijkstra.get("C").nextHop())) {
            throw new AssertionError("Next-hop calculation failed.");
        }

        RoutingTable table = new RoutingTable("A");

        table.add(new Route(
            IPv4Network.parse("10.0.0.0/8"),
            "B",
            "eth0",
            10,
            Protocol.STATIC,
            true
        ));

        table.add(new Route(
            IPv4Network.parse("10.1.0.0/16"),
            "C",
            "eth1",
            5,
            Protocol.OSPF,
            true
        ));

        if (!table.lookup("10.1.2.3")
            .network().toString().equals("10.1.0.0/16")) {
            throw new AssertionError("Prefix selection failed.");
        }

        topology.setLinkState("B", "C", LinkState.DOWN);

        Map<String, PathResult> updated =
            RoutingAlgorithms.dijkstra(topology, "A");

        if (updated.get("C").cost() != 10) {
            throw new AssertionError("Link failure test failed.");
        }

        System.out.println("\nAll Java routing tests passed.");
    }

    public static void main(String[] args) {

        try {
            demonstrate();
            runTests();
        } catch (RoutingException exception) {
            System.err.println(
                "Routing operation failed: " +
                exception.getMessage()
            );
            System.exit(1);
        }
    }
}
