import java.util.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.Collectors;

/*
 * INTRODUCTION TO COMPUTER NETWORKS
 *
 * Enterprise network architecture and packet delivery model.
 *
 * Covers:
 * - LAN and WAN infrastructure
 * - OSI and TCP/IP models
 * - Network addressing
 * - Device and interface management
 * - Network topology
 * - Routing
 * - Packet switching
 * - Network policies
 * - Connectivity and failure handling
 *
 * Runtime: Java 17
 */

public class Main {

    // ========================================================
    // 1. NETWORK MODELS
    // ========================================================

    enum OSILayer {
        PHYSICAL(1),
        DATA_LINK(2),
        NETWORK(3),
        TRANSPORT(4),
        SESSION(5),
        PRESENTATION(6),
        APPLICATION(7);

        private final int number;

        OSILayer(int number) {
            this.number = number;
        }

        public int number() {
            return number;
        }
    }

    enum DeviceType {
        HOST, SWITCH, ROUTER
    }

    enum NetworkType {
        LAN, WAN
    }

    enum Protocol {
        TCP, UDP, ICMP
    }

    enum PacketStatus {
        CREATED, FORWARDED, DELIVERED, DROPPED
    }

    static void displayModels() {
        System.out.println("\nOSI MODEL");

        Arrays.stream(OSILayer.values())
                .sorted(Comparator.comparingInt(
                        OSILayer::number).reversed())
                .forEach(layer ->
                        System.out.println(
                                layer.number() + ". " + layer));

        System.out.println("\nTCP/IP MODEL");

        Map<String, List<Integer>> model = Map.of(
                "Application", List.of(5, 6, 7),
                "Transport", List.of(4),
                "Internet", List.of(3),
                "Network Access", List.of(1, 2)
        );

        model.forEach((layer, mappedLayers) ->
                System.out.println(layer + " -> " + mappedLayers));
    }

    // ========================================================
    // 2. IPV4 ADDRESSING
    // ========================================================

    record IPv4(long value) {

        IPv4 {
            if (value < 0 || value > 0xFFFFFFFFL) {
                throw new IllegalArgumentException(
                        "IPv4 address outside valid range");
            }
        }

        static IPv4 parse(String address) {
            String[] octets = address.split("\\.", -1);

            if (octets.length != 4) {
                throw new IllegalArgumentException(
                        "IPv4 requires four octets");
            }

            long result = 0;

            for (String octet : octets) {
                if (!octet.matches("\\d{1,3}")) {
                    throw new IllegalArgumentException(
                            "Invalid IPv4 octet");
                }

                int number = Integer.parseInt(octet);

                if (number > 255) {
                    throw new IllegalArgumentException(
                            "IPv4 octet exceeds 255");
                }

                result = (result << 8) | number;
            }

            return new IPv4(result);
        }

        @Override
        public String toString() {
            return ((value >>> 24) & 255) + "." +
                    ((value >>> 16) & 255) + "." +
                    ((value >>> 8) & 255) + "." +
                    (value & 255);
        }
    }

    // ========================================================
    // 3. SUBNET AND ADDRESS MANAGEMENT
    // ========================================================

    record Subnet(IPv4 network, int prefix) {

        Subnet {
            Objects.requireNonNull(network);

            if (prefix < 0 || prefix > 32) {
                throw new IllegalArgumentException(
                        "Invalid subnet prefix");
            }

            long mask = maskFor(prefix);
            network = new IPv4(network.value() & mask);
        }

        private static long maskFor(int prefix) {
            return prefix == 0
                    ? 0
                    : (0xFFFFFFFFL << (32 - prefix))
                    & 0xFFFFFFFFL;
        }

        public boolean contains(IPv4 address) {
            return (address.value() & maskFor(prefix))
                    == network.value();
        }

        public IPv4 broadcast() {
            long hostMask = (~maskFor(prefix)) & 0xFFFFFFFFL;

            return new IPv4(network.value() | hostMask);
        }

        public long totalAddresses() {
            return 1L << (32 - prefix);
        }
    }

    // ========================================================
    // 4. NETWORK INTERFACES
    // ========================================================

    record NetworkInterface(
            String name,
            IPv4 address,
            Subnet subnet,
            String macAddress
    ) {
        NetworkInterface {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                        "Interface name required");
            }

            Objects.requireNonNull(address);
            Objects.requireNonNull(subnet);

            if (!subnet.contains(address)) {
                throw new IllegalArgumentException(
                        "IP is outside subnet");
            }

            if (macAddress == null ||
                    !macAddress.matches(
                            "(?i)([0-9a-f]{2}:){5}[0-9a-f]{2}")) {
                throw new IllegalArgumentException(
                        "Invalid MAC address");
            }

            macAddress = macAddress.toUpperCase(Locale.ROOT);
        }
    }

    // ========================================================
    // 5. NETWORK DEVICES
    // ========================================================

    static final class NetworkDevice {

        private final String id;
        private final String name;
        private final DeviceType type;

        private final Map<String, NetworkInterface> interfaces =
                new LinkedHashMap<>();

        NetworkDevice(
                String id,
                String name,
                DeviceType type
        ) {
            if (id == null || id.isBlank() ||
                    name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                        "Device identity required");
            }

            this.id = id;
            this.name = name;
            this.type = Objects.requireNonNull(type);
        }

        void addInterface(NetworkInterface networkInterface) {
            if (interfaces.putIfAbsent(
                    networkInterface.name(),
                    networkInterface) != null) {
                throw new IllegalArgumentException(
                        "Duplicate interface");
            }
        }

        public String id() {
            return id;
        }

        public String name() {
            return name;
        }

        public DeviceType type() {
            return type;
        }

        public Map<String, NetworkInterface> interfaces() {
            return Collections.unmodifiableMap(interfaces);
        }
    }

    // ========================================================
    // 6. PACKET DOMAIN
    // ========================================================

    record Packet(
            long id,
            IPv4 source,
            IPv4 destination,
            Protocol protocol,
            String payload,
            int ttl,
            Integer sourcePort,
            Integer destinationPort
    ) {

        Packet {
            Objects.requireNonNull(source);
            Objects.requireNonNull(destination);
            Objects.requireNonNull(protocol);
            Objects.requireNonNull(payload);

            if (ttl < 1 || ttl > 255) {
                throw new IllegalArgumentException("Invalid TTL");
            }

            if (payload.getBytes(
                    java.nio.charset.StandardCharsets.UTF_8).length
                    > 65507) {
                throw new IllegalArgumentException(
                        "Payload too large");
            }

            validatePort(sourcePort);
            validatePort(destinationPort);
        }

        private static void validatePort(Integer port) {
            if (port != null && (port < 1 || port > 65535)) {
                throw new IllegalArgumentException(
                        "Invalid transport port");
            }
        }

        public int sizeBytes() {
            int transportHeader =
                    protocol == Protocol.TCP ? 20 : 8;

            return 20 +
                    transportHeader +
                    payload.getBytes(
                            java.nio.charset.StandardCharsets.UTF_8
                    ).length;
        }

        public Packet decrementTTL() {
            if (ttl <= 1) {
                throw new IllegalStateException("TTL_EXPIRED");
            }

            return new Packet(
                    id,
                    source,
                    destination,
                    protocol,
                    payload,
                    ttl - 1,
                    sourcePort,
                    destinationPort
            );
        }
    }

    // ========================================================
    // 7. NETWORK LINKS
    // ========================================================

    static final class NetworkLink {

        private final String source;
        private final String destination;
        private final NetworkType type;
        private final double bandwidthMbps;
        private final double latencyMs;

        private boolean available = true;

        NetworkLink(
                String source,
                String destination,
                NetworkType type,
                double bandwidthMbps,
                double latencyMs
        ) {
            if (bandwidthMbps <= 0 || latencyMs < 0) {
                throw new IllegalArgumentException(
                        "Invalid link parameters");
            }

            this.source = source;
            this.destination = destination;
            this.type = type;
            this.bandwidthMbps = bandwidthMbps;
            this.latencyMs = latencyMs;
        }

        boolean available() {
            return available;
        }

        void setAvailable(boolean value) {
            available = value;
        }

        String source() {
            return source;
        }

        String destination() {
            return destination;
        }

        double latencyMs() {
            return latencyMs;
        }

        double bandwidthMbps() {
            return bandwidthMbps;
        }

        NetworkType type() {
            return type;
        }
    }

    // ========================================================
    // 8. NETWORK TOPOLOGY SERVICE
    // ========================================================

    static final class NetworkTopology {

        private final Map<String, NetworkDevice> devices =
                new LinkedHashMap<>();

        private final Map<String, List<NetworkLink>> adjacency =
                new HashMap<>();

        void addDevice(NetworkDevice device) {
            if (devices.putIfAbsent(device.id(), device) != null) {
                throw new IllegalArgumentException(
                        "Duplicate device ID");
            }
        }

        void connect(NetworkLink link) {
            if (!devices.containsKey(link.source()) ||
                    !devices.containsKey(link.destination())) {
                throw new IllegalArgumentException(
                        "Unknown connection endpoint");
            }

            if (link.source().equals(link.destination())) {
                throw new IllegalArgumentException(
                        "Self-links prohibited");
            }

            List<NetworkLink> edges =
                    adjacency.computeIfAbsent(
                            link.source(),
                            ignored -> new ArrayList<>());

            if (edges.stream().anyMatch(
                    existing -> existing.destination()
                            .equals(link.destination()))) {
                throw new IllegalArgumentException(
                        "Duplicate connection");
            }

            edges.add(link);
        }

        List<String> shortestPath(
                String source,
                String destination
        ) {
            if (!devices.containsKey(source) ||
                    !devices.containsKey(destination)) {
                throw new IllegalArgumentException(
                        "Unknown endpoint");
            }

            Queue<List<String>> queue = new ArrayDeque<>();
            Set<String> visited = new HashSet<>();

            queue.add(List.of(source));
            visited.add(source);

            while (!queue.isEmpty()) {
                List<String> path = queue.remove();

                String current =
                        path.get(path.size() - 1);

                if (current.equals(destination)) {
                    return path;
                }

                for (NetworkLink link :
                        adjacency.getOrDefault(
                                current, Collections.emptyList())) {

                    if (!link.available() ||
                            !visited.add(link.destination())) {
                        continue;
                    }

                    List<String> next =
                            new ArrayList<>(path);

                    next.add(link.destination());
                    queue.add(next);
                }
            }

            throw new IllegalStateException("NO_ROUTE");
        }

        NetworkLink getLink(String source, String destination) {
            return adjacency.getOrDefault(
                            source,
                            Collections.emptyList())
                    .stream()
                    .filter(link ->
                            link.destination().equals(destination)
                                    && link.available())
                    .findFirst()
                    .orElseThrow(() ->
                            new IllegalStateException(
                                    "LINK_UNAVAILABLE"));
        }

        void setLinkStatus(
                String source,
                String destination,
                boolean available
        ) {
            NetworkLink link = adjacency.getOrDefault(
                            source,
                            Collections.emptyList())
                    .stream()
                    .filter(item ->
                            item.destination().equals(destination))
                    .findFirst()
                    .orElseThrow(() ->
                            new IllegalArgumentException(
                                    "Link not found"));

            link.setAvailable(available);
        }
    }

    // ========================================================
    // 9. ROUTING TABLE
    // ========================================================

    record Route(
            Subnet destination,
            String nextHop,
            int metric
    ) {
        Route {
            Objects.requireNonNull(destination);

            if (nextHop == null || nextHop.isBlank() || metric < 0) {
                throw new IllegalArgumentException(
                        "Invalid route");
            }
        }
    }

    static final class RoutingTable {

        private final List<Route> routes =
                new ArrayList<>();

        void add(Route route) {
            routes.add(route);

            routes.sort(
                    Comparator
                            .comparingInt(
                                    (Route r) ->
                                            r.destination().prefix())
                            .reversed()
                            .thenComparingInt(Route::metric)
            );
        }

        Optional<Route> lookup(IPv4 destination) {
            return routes.stream()
                    .filter(route ->
                            route.destination().contains(destination))
                    .findFirst();
        }
    }

    // ========================================================
    // 10. PACKET DELIVERY RESULT
    // ========================================================

    record TransmissionResult(
            long packetId,
            PacketStatus status,
            List<String> path,
            double latencyMs,
            double bottleneckMbps,
            int remainingTTL,
            String message
    ) {
        TransmissionResult {
            path = List.copyOf(path);
        }
    }

    // ========================================================
    // 11. PACKET SWITCHING SERVICE
    // ========================================================

    static final class PacketSwitch {

        private final NetworkTopology topology;

        private final AtomicLong sequence =
                new AtomicLong(1);

        private long transmitted;
        private long delivered;
        private long dropped;
        private long bytes;

        PacketSwitch(NetworkTopology topology) {
            this.topology = Objects.requireNonNull(topology);
        }

        Packet createPacket(
                String source,
                String destination,
                String payload,
                Protocol protocol,
                int ttl
        ) {
            return new Packet(
                    sequence.getAndIncrement(),
                    IPv4.parse(source),
                    IPv4.parse(destination),
                    protocol,
                    payload,
                    ttl,
                    50000,
                    443
            );
        }

        TransmissionResult transmit(
                Packet original,
                String source,
                String destination
        ) {
            transmitted++;

            List<String> path = new ArrayList<>();

            Packet current = original;

            try {
                path = topology.shortestPath(
                        source, destination);

                double latency = 0;
                double bandwidth = Double.POSITIVE_INFINITY;

                for (int i = 0; i < path.size(); i++) {
                    String currentDevice = path.get(i);

                    if (i == path.size() - 1) {
                        break;
                    }

                    String nextDevice = path.get(i + 1);

                    NetworkLink link =
                            topology.getLink(
                                    currentDevice, nextDevice);

                    current = current.decrementTTL();

                    latency += link.latencyMs();

                    bandwidth = Math.min(
                            bandwidth,
                            link.bandwidthMbps());
                }

                delivered++;
                bytes += current.sizeBytes();

                return new TransmissionResult(
                        current.id(),
                        PacketStatus.DELIVERED,
                        path,
                        latency,
                        bandwidth,
                        current.ttl(),
                        "Packet delivered successfully"
                );

            } catch (IllegalStateException error) {
                dropped++;

                return new TransmissionResult(
                        current.id(),
                        PacketStatus.DROPPED,
                        path,
                        0,
                        0,
                        current.ttl(),
                        error.getMessage()
                );
            }
        }

        void printStatistics() {
            System.out.println("\nNETWORK STATISTICS");

            System.out.println("Transmitted: " + transmitted);
            System.out.println("Delivered: " + delivered);
            System.out.println("Dropped: " + dropped);
            System.out.println("Bytes: " + bytes);

            double rate = transmitted == 0
                    ? 0
                    : 100.0 * delivered / transmitted;

            System.out.printf(
                    Locale.ROOT,
                    "Delivery rate: %.2f%%%n",
                    rate
            );
        }
    }

    // ========================================================
    // 12. ENTERPRISE NETWORK CONSTRUCTION
    // ========================================================

    static NetworkTopology createNetwork() {
        NetworkTopology topology = new NetworkTopology();

        topology.addDevice(new NetworkDevice(
                "PC1", "Development Workstation", DeviceType.HOST));

        topology.addDevice(new NetworkDevice(
                "SW1", "Office Switch", DeviceType.SWITCH));

        topology.addDevice(new NetworkDevice(
                "R1", "Office Router", DeviceType.ROUTER));

        topology.addDevice(new NetworkDevice(
                "R2", "Remote Router", DeviceType.ROUTER));

        topology.addDevice(new NetworkDevice(
                "SW2", "Remote Switch", DeviceType.SWITCH));

        topology.addDevice(new NetworkDevice(
                "SRV1", "Application Server", DeviceType.HOST));

        topology.connect(new NetworkLink(
                "PC1", "SW1", NetworkType.LAN, 1000, 0.1));

        topology.connect(new NetworkLink(
                "SW1", "R1", NetworkType.LAN, 1000, 0.2));

        topology.connect(new NetworkLink(
                "R1", "R2", NetworkType.WAN, 100, 20));

        topology.connect(new NetworkLink(
                "R2", "SW2", NetworkType.LAN, 1000, 0.2));

        topology.connect(new NetworkLink(
                "SW2", "SRV1", NetworkType.LAN, 1000, 0.1));

        return topology;
    }

    // ========================================================
    // 13. EXECUTION AND VALIDATION
    // ========================================================

    static void printResult(TransmissionResult result) {
        System.out.println("\nPacket ID: " + result.packetId());
        System.out.println("Status: " + result.status());
        System.out.println("Path: " +
                String.join(" -> ", result.path()));
        System.out.println("Message: " + result.message());

        if (result.status() == PacketStatus.DELIVERED) {
            System.out.println(
                    "Latency: " + result.latencyMs() + " ms");

            System.out.println(
                    "Bandwidth: " + result.bottleneckMbps()
                            + " Mbps");

            System.out.println(
                    "Remaining TTL: " + result.remainingTTL());
        }
    }

    public static void main(String[] args) {

        try {
            System.out.println(
                    "INTRODUCTION TO COMPUTER NETWORKS");

            displayModels();

            System.out.println("\nIP ADDRESSING");

            Subnet subnet = new Subnet(
                    IPv4.parse("192.168.1.10"), 24);

            System.out.println(
                    "Network: " + subnet.network());

            System.out.println(
                    "Broadcast: " + subnet.broadcast());

            System.out.println(
                    "Total addresses: " + subnet.totalAddresses());

            if (!subnet.contains(
                    IPv4.parse("192.168.1.100"))) {
                throw new IllegalStateException(
                        "Subnet validation failed");
            }

            RoutingTable routing = new RoutingTable();

            routing.add(new Route(
                    new Subnet(
                            IPv4.parse("10.0.0.0"), 8),
                    "R1",
                    10
            ));

            routing.add(new Route(
                    new Subnet(
                            IPv4.parse("10.1.0.0"), 16),
                    "R2",
                    5
            ));

            Route selected = routing.lookup(
                    IPv4.parse("10.1.2.3")
            ).orElseThrow();

            if (!selected.nextHop().equals("R2")) {
                throw new IllegalStateException(
                        "Routing selection failed");
            }

            System.out.println(
                    "Selected next hop: " + selected.nextHop());

            NetworkTopology topology = createNetwork();

            PacketSwitch packetSwitch =
                    new PacketSwitch(topology);

            System.out.println("\nPACKET SWITCHING");

            Packet packet = packetSwitch.createPacket(
                    "192.168.1.10",
                    "10.0.0.10",
                    "Enterprise network communication",
                    Protocol.TCP,
                    64
            );

            TransmissionResult result =
                    packetSwitch.transmit(
                            packet, "PC1", "SRV1");

            printResult(result);

            if (result.status() != PacketStatus.DELIVERED) {
                throw new IllegalStateException(
                        "Expected successful delivery");
            }

            System.out.println("\nTTL FAILURE");

            Packet ttlPacket = packetSwitch.createPacket(
                    "192.168.1.10",
                    "10.0.0.10",
                    "TTL test",
                    Protocol.TCP,
                    2
            );

            TransmissionResult ttlResult =
                    packetSwitch.transmit(
                            ttlPacket, "PC1", "SRV1");

            printResult(ttlResult);

            if (ttlResult.status() != PacketStatus.DROPPED) {
                throw new IllegalStateException(
                        "TTL test should fail");
            }

            System.out.println("\nWAN FAILURE");

            topology.setLinkStatus(
                    "R1", "R2", false);

            Packet failedPacket = packetSwitch.createPacket(
                    "192.168.1.10",
                    "10.0.0.10",
                    "WAN failure test",
                    Protocol.TCP,
                    64
            );

            TransmissionResult failedResult =
                    packetSwitch.transmit(
                            failedPacket, "PC1", "SRV1");

            printResult(failedResult);

            if (failedResult.status() != PacketStatus.DROPPED) {
                throw new IllegalStateException(
                        "WAN failure not detected");
            }

            packetSwitch.printStatistics();

            System.out.println("\nAll tests passed.");

        } catch (RuntimeException error) {
            System.err.println(
                    "Network error: " + error.getMessage());

            System.exit(1);
        }
    }
}
