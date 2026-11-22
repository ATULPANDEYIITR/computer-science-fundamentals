import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;

/*
 * TCP/IP Model: Enterprise Network Communication Architecture
 *
 * Java 17
 *
 * Features:
 * - Four-layer TCP/IP architecture
 * - Immutable domain records
 * - IPv4 and CIDR validation
 * - TCP connection management
 * - UDP datagram processing
 * - IP packet forwarding
 * - Routing policies
 * - Ethernet frame validation
 * - Application protocol management
 * - DNS caching
 * - Network observability
 * - Exception handling
 */

// ============================================================
// 1. EXCEPTIONS
// ============================================================

class NetworkException extends RuntimeException {
    public NetworkException(String message) {
        super(message);
    }
}

class InvalidPacketException extends NetworkException {
    public InvalidPacketException(String message) {
        super(message);
    }
}

class RoutingException extends NetworkException {
    public RoutingException(String message) {
        super(message);
    }
}

class ConnectionStateException extends NetworkException {
    public ConnectionStateException(String message) {
        super(message);
    }
}

// ============================================================
// 2. ARCHITECTURE
// ============================================================

enum NetworkLayer {
    APPLICATION(4),
    TRANSPORT(3),
    INTERNET(2),
    NETWORK_ACCESS(1);

    private final int number;

    NetworkLayer(int number) {
        this.number = number;
    }

    public int number() {
        return number;
    }
}

record LayerDescription(
    NetworkLayer layer,
    String name,
    List<String> responsibilities
) {}

class TCPIPArchitecture {

    public static List<LayerDescription> definitions() {
        return List.of(
            new LayerDescription(
                NetworkLayer.APPLICATION,
                "Application",
                List.of("HTTP", "HTTPS", "DNS", "DHCP", "SMTP")
            ),
            new LayerDescription(
                NetworkLayer.TRANSPORT,
                "Transport",
                List.of("TCP", "UDP", "Ports", "Segmentation")
            ),
            new LayerDescription(
                NetworkLayer.INTERNET,
                "Internet",
                List.of("IPv4", "ICMP", "Routing", "Forwarding")
            ),
            new LayerDescription(
                NetworkLayer.NETWORK_ACCESS,
                "Network Access",
                List.of("Ethernet", "MAC", "Framing")
            )
        );
    }

    public static void display() {
        System.out.println("\nTCP/IP FOUR-LAYER ARCHITECTURE");

        definitions().forEach(layer ->
            System.out.println(
                layer.name() + ": " +
                String.join(", ", layer.responsibilities())
            )
        );
    }
}

// ============================================================
// 3. IPV4 ADDRESS
// ============================================================

record IPv4Address(long value) {

    public IPv4Address {
        if (value < 0 || value > 0xFFFFFFFFL) {
            throw new InvalidPacketException("Invalid IPv4 value.");
        }
    }

    public static IPv4Address parse(String address) {
        Objects.requireNonNull(address);

        String[] octets = address.split("\\.", -1);

        if (octets.length != 4) {
            throw new InvalidPacketException("Invalid IPv4 address.");
        }

        long value = 0;

        for (String octet : octets) {
            try {
                if (octet.isEmpty() ||
                    (octet.length() > 1 && octet.startsWith("+"))) {
                    throw new NumberFormatException();
                }

                int number = Integer.parseInt(octet);

                if (number < 0 || number > 255) {
                    throw new NumberFormatException();
                }

                value = (value << 8) | number;

            } catch (NumberFormatException exception) {
                throw new InvalidPacketException(
                    "Invalid IPv4 octet: " + octet
                );
            }
        }

        return new IPv4Address(value);
    }

    public String formatted() {
        return String.format(
            "%d.%d.%d.%d",
            (value >> 24) & 255,
            (value >> 16) & 255,
            (value >> 8) & 255,
            value & 255
        );
    }

    @Override
    public String toString() {
        return formatted();
    }
}

// ============================================================
// 4. CIDR NETWORK
// ============================================================

record IPv4Network(long network, long mask, int prefix) {

    public IPv4Network {
        if (prefix < 0 || prefix > 32) {
            throw new InvalidPacketException("Invalid CIDR prefix.");
        }
    }

    public static IPv4Network create(String cidr) {
        String[] parts = cidr.split("/", -1);

        if (parts.length != 2) {
            throw new InvalidPacketException("CIDR notation required.");
        }

        IPv4Address address = IPv4Address.parse(parts[0]);

        int prefix;

        try {
            prefix = Integer.parseInt(parts[1]);
        } catch (NumberFormatException exception) {
            throw new InvalidPacketException("Invalid CIDR prefix.");
        }

        if (prefix < 0 || prefix > 32) {
            throw new InvalidPacketException("Invalid CIDR prefix.");
        }

        long mask = prefix == 0
            ? 0L
            : (0xFFFFFFFFL << (32 - prefix)) & 0xFFFFFFFFL;

        return new IPv4Network(
            address.value() & mask,
            mask,
            prefix
        );
    }

    public boolean contains(IPv4Address address) {
        return (address.value() & mask) == network;
    }

    public String networkAddress() {
        return new IPv4Address(network).formatted();
    }

    @Override
    public String toString() {
        return networkAddress() + "/" + prefix;
    }
}

// ============================================================
// 5. APPLICATION LAYER
// ============================================================

enum ApplicationProtocol {
    HTTP(80),
    HTTPS(443),
    DNS(53),
    DHCP(67);

    private final int defaultPort;

    ApplicationProtocol(int defaultPort) {
        this.defaultPort = defaultPort;
    }

    public int defaultPort() {
        return defaultPort;
    }
}

record ApplicationMessage(
    ApplicationProtocol protocol,
    byte[] payload,
    Instant createdAt
) {
    public ApplicationMessage {
        Objects.requireNonNull(protocol);
        Objects.requireNonNull(payload);
        Objects.requireNonNull(createdAt);

        if (payload.length == 0) {
            throw new InvalidPacketException("Empty application payload.");
        }

        payload = payload.clone();
    }

    public static ApplicationMessage fromText(
        ApplicationProtocol protocol,
        String content
    ) {
        return new ApplicationMessage(
            protocol,
            content.getBytes(StandardCharsets.UTF_8),
            Instant.now()
        );
    }

    @Override
    public byte[] payload() {
        return payload.clone();
    }
}

// ============================================================
// 6. TRANSPORT LAYER: TCP
// ============================================================

enum TCPState {
    CLOSED,
    SYN_SENT,
    SYN_RECEIVED,
    ESTABLISHED,
    FIN_WAIT,
    TIME_WAIT
}

record TCPEvent(
    TCPState previous,
    TCPState current,
    String description,
    Instant timestamp
) {}

class TCPConnection {

    private final int sourcePort;
    private final int destinationPort;

    private final SecureRandom random = new SecureRandom();

    private TCPState state = TCPState.CLOSED;

    private long sequenceNumber;
    private long acknowledgmentNumber;

    private final List<TCPEvent> events = new ArrayList<>();

    public TCPConnection(int sourcePort, int destinationPort) {
        validatePort(sourcePort);
        validatePort(destinationPort);

        this.sourcePort = sourcePort;
        this.destinationPort = destinationPort;

        this.sequenceNumber =
            random.nextInt(Integer.MAX_VALUE);
    }

    private static void validatePort(int port) {
        if (port < 1 || port > 65535) {
            throw new InvalidPacketException("Invalid transport port.");
        }
    }

    private void transition(
        TCPState expected,
        TCPState next,
        String description
    ) {
        if (state != expected) {
            throw new ConnectionStateException(
                "Expected " + expected + " but found " + state
            );
        }

        TCPState previous = state;

        state = next;

        events.add(
            new TCPEvent(
                previous,
                next,
                description,
                Instant.now()
            )
        );
    }

    public void connect() {
        transition(
            TCPState.CLOSED,
            TCPState.SYN_SENT,
            "Client sends SYN"
        );

        transition(
            TCPState.SYN_SENT,
            TCPState.SYN_RECEIVED,
            "Server responds with SYN-ACK"
        );

        acknowledgmentNumber = sequenceNumber + 1;

        transition(
            TCPState.SYN_RECEIVED,
            TCPState.ESTABLISHED,
            "Client sends ACK"
        );
    }

    public void close() {
        transition(
            TCPState.ESTABLISHED,
            TCPState.FIN_WAIT,
            "Connection termination begins"
        );

        transition(
            TCPState.FIN_WAIT,
            TCPState.TIME_WAIT,
            "Final acknowledgment processing"
        );

        transition(
            TCPState.TIME_WAIT,
            TCPState.CLOSED,
            "Connection closed"
        );
    }

    public TCPState state() {
        return state;
    }

    public List<TCPEvent> events() {
        return List.copyOf(events);
    }

    public int sourcePort() {
        return sourcePort;
    }

    public int destinationPort() {
        return destinationPort;
    }

    public long acknowledgmentNumber() {
        return acknowledgmentNumber;
    }
}

// ============================================================
// 7. TRANSPORT LAYER: UDP
// ============================================================

record UDPDatagram(
    int sourcePort,
    int destinationPort,
    byte[] payload
) {
    public UDPDatagram {
        if (sourcePort < 1 || sourcePort > 65535 ||
            destinationPort < 1 || destinationPort > 65535) {
            throw new InvalidPacketException("Invalid UDP port.");
        }

        if (payload.length > 65507) {
            throw new InvalidPacketException("UDP payload too large.");
        }

        payload = payload.clone();
    }

    @Override
    public byte[] payload() {
        return payload.clone();
    }

    public int length() {
        return 8 + payload.length;
    }
}

// ============================================================
// 8. INTERNET LAYER
// ============================================================

record IPv4Packet(
    IPv4Address source,
    IPv4Address destination,
    int protocol,
    int ttl,
    int identification,
    byte[] payload
) {
    public IPv4Packet {
        Objects.requireNonNull(source);
        Objects.requireNonNull(destination);

        if (protocol < 0 || protocol > 255) {
            throw new InvalidPacketException("Invalid IP protocol.");
        }

        if (ttl < 1 || ttl > 255) {
            throw new InvalidPacketException("Invalid TTL.");
        }

        if (identification < 0 || identification > 65535) {
            throw new InvalidPacketException("Invalid IP identification.");
        }

        if (payload.length + 20 > 65535) {
            throw new InvalidPacketException("IPv4 packet too large.");
        }

        payload = payload.clone();
    }

    @Override
    public byte[] payload() {
        return payload.clone();
    }

    public int totalLength() {
        return 20 + payload.length;
    }

    public IPv4Packet forward() {
        if (ttl <= 1) {
            throw new RoutingException("TTL expired.");
        }

        return new IPv4Packet(
            source,
            destination,
            protocol,
            ttl - 1,
            identification,
            payload
        );
    }

    public int checksum() {
        int[] header = new int[10];

        header[0] = 0x4500;
        header[1] = totalLength();
        header[2] = identification;
        header[3] = 0;
        header[4] = (ttl << 8) | protocol;
        header[5] = 0;

        header[6] = (int) (source.value() >>> 16);
        header[7] = (int) (source.value() & 0xFFFF);

        header[8] = (int) (destination.value() >>> 16);
        header[9] = (int) (destination.value() & 0xFFFF);

        long sum = 0;

        for (int word : header) {
            sum += word;
        }

        while ((sum >>> 16) != 0) {
            sum = (sum & 0xFFFF) + (sum >>> 16);
        }

        return (int) (~sum) & 0xFFFF;
    }
}

// ============================================================
// 9. NETWORK ACCESS LAYER
// ============================================================

record EthernetFrame(
    String sourceMAC,
    String destinationMAC,
    int etherType,
    byte[] payload
) {
    public EthernetFrame {
        String pattern = "^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$";

        if (!sourceMAC.matches(pattern) ||
            !destinationMAC.matches(pattern)) {
            throw new InvalidPacketException("Invalid MAC address.");
        }

        if (etherType < 0 || etherType > 65535) {
            throw new InvalidPacketException("Invalid EtherType.");
        }

        if (payload.length > 1500) {
            throw new InvalidPacketException("Ethernet MTU exceeded.");
        }

        payload = payload.clone();
    }

    @Override
    public byte[] payload() {
        return payload.clone();
    }

    public int frameSize() {
        return 14 + payload.length + 4;
    }
}

// ============================================================
// 10. ROUTING POLICY
// ============================================================

record Route(
    IPv4Network network,
    IPv4Address nextHop,
    String interfaceName,
    int metric
) {
    public Route {
        Objects.requireNonNull(network);
        Objects.requireNonNull(nextHop);

        if (interfaceName == null || interfaceName.isBlank()) {
            throw new IllegalArgumentException("Interface required.");
        }

        if (metric < 0) {
            throw new IllegalArgumentException("Invalid route metric.");
        }
    }
}

class RoutingTable {

    private final List<Route> routes = new ArrayList<>();

    public void add(Route route) {
        routes.add(route);

        routes.sort(
            Comparator
                .comparingInt(
                    (Route item) -> item.network().prefix()
                )
                .reversed()
                .thenComparingInt(Route::metric)
        );
    }

    public Optional<Route> find(IPv4Address destination) {
        return routes.stream()
            .filter(route -> route.network().contains(destination))
            .findFirst();
    }

    public Route requireRoute(IPv4Address destination) {
        return find(destination).orElseThrow(
            () -> new RoutingException(
                "No route to " + destination
            )
        );
    }

    public IPv4Packet forward(IPv4Packet packet) {
        Route route = requireRoute(packet.destination());

        System.out.println(
            "Interface: " + route.interfaceName() +
            ", next hop: " + route.nextHop()
        );

        return packet.forward();
    }

    public List<Route> routes() {
        return List.copyOf(routes);
    }
}

// ============================================================
// 11. DNS CACHE
// ============================================================

record DNSRecord(
    IPv4Address address,
    Instant expiresAt
) {}

class DNSCache {

    private final Map<String, DNSRecord> records = new HashMap<>();

    public void add(String domain, String address, long ttlSeconds) {
        if (domain == null || domain.isBlank()) {
            throw new IllegalArgumentException("Domain required.");
        }

        if (ttlSeconds <= 0) {
            throw new IllegalArgumentException("Invalid DNS TTL.");
        }

        records.put(
            domain.toLowerCase(),
            new DNSRecord(
                IPv4Address.parse(address),
                Instant.now().plusSeconds(ttlSeconds)
            )
        );
    }

    public Optional<IPv4Address> resolve(String domain) {
        String key = domain.toLowerCase();

        DNSRecord record = records.get(key);

        if (record == null) {
            return Optional.empty();
        }

        if (!Instant.now().isBefore(record.expiresAt())) {
            records.remove(key);
            return Optional.empty();
        }

        return Optional.of(record.address());
    }
}

// ============================================================
// 12. FRAGMENTATION
// ============================================================

class FragmentationService {

    public static List<Integer> calculate(
        int packetSize,
        int mtu
    ) {
        final int HEADER_SIZE = 20;

        if (packetSize <= HEADER_SIZE || packetSize > 65535) {
            throw new InvalidPacketException("Invalid packet size.");
        }

        if (mtu <= HEADER_SIZE) {
            throw new InvalidPacketException("Invalid MTU.");
        }

        int maximumPayload =
            ((mtu - HEADER_SIZE) / 8) * 8;

        int remaining = packetSize - HEADER_SIZE;

        List<Integer> fragments = new ArrayList<>();

        while (remaining > 0) {
            int size = Math.min(remaining, maximumPayload);

            fragments.add(size);

            remaining -= size;
        }

        return List.copyOf(fragments);
    }
}

// ============================================================
// 13. NETWORK MONITORING
// ============================================================

record NetworkMetrics(
    long transmitted,
    long forwarded,
    long dropped,
    long failures
) {}

class NetworkMonitor {

    private long transmitted;
    private long forwarded;
    private long dropped;
    private long failures;

    public void recordTransmission() {
        transmitted++;
    }

    public void recordForwarding() {
        forwarded++;
    }

    public void recordDrop() {
        dropped++;
    }

    public void recordFailure() {
        failures++;
    }

    public NetworkMetrics report() {
        return new NetworkMetrics(
            transmitted,
            forwarded,
            dropped,
            failures
        );
    }
}

// ============================================================
// 14. NETWORK SERVICE
// ============================================================

class NetworkService {

    private final RoutingTable routingTable;
    private final NetworkMonitor monitor;

    public NetworkService(
        RoutingTable routingTable,
        NetworkMonitor monitor
    ) {
        this.routingTable = routingTable;
        this.monitor = monitor;
    }

    public IPv4Packet transmit(IPv4Packet packet) {
        monitor.recordTransmission();

        try {
            IPv4Packet forwarded = routingTable.forward(packet);

            monitor.recordForwarding();

            return forwarded;

        } catch (NetworkException exception) {
            monitor.recordDrop();
            monitor.recordFailure();

            throw exception;
        }
    }
}

// ============================================================
// 15. INTEGRATED ENTERPRISE SCENARIO
// ============================================================

public class Main {

    public static void main(String[] args) {

        try {
            TCPIPArchitecture.display();

            System.out.println("\nAPPLICATION LAYER");

            ApplicationMessage message =
                ApplicationMessage.fromText(
                    ApplicationProtocol.HTTPS,
                    "GET /api/status HTTP/1.1"
                );

            System.out.println(
                "Protocol: " + message.protocol()
            );

            System.out.println(
                "Payload size: " + message.payload().length
            );

            System.out.println("\nTCP TRANSPORT");

            TCPConnection connection =
                new TCPConnection(50000, 443);

            connection.connect();

            System.out.println("State: " + connection.state());

            connection.events().forEach(event ->
                System.out.println(
                    event.description() +
                    ": " + event.previous() +
                    " -> " + event.current()
                )
            );

            System.out.println("\nUDP TRANSPORT");

            UDPDatagram datagram = new UDPDatagram(
                53000,
                53,
                "DNS query".getBytes(StandardCharsets.UTF_8)
            );

            System.out.println(
                "UDP length: " + datagram.length()
            );

            System.out.println("\nINTERNET LAYER");

            IPv4Address client =
                IPv4Address.parse("192.168.1.10");

            IPv4Address server =
                IPv4Address.parse("203.0.113.20");

            IPv4Packet packet = new IPv4Packet(
                client,
                server,
                6,
                64,
                100,
                message.payload()
            );

            System.out.println("Source: " + packet.source());
            System.out.println("Destination: " + packet.destination());
            System.out.println("Packet length: " + packet.totalLength());

            System.out.printf(
                "Header checksum: %04X%n",
                packet.checksum()
            );

            System.out.println("\nNETWORK ACCESS");

            EthernetFrame frame = new EthernetFrame(
                "02:00:00:00:00:01",
                "02:00:00:00:00:02",
                0x0800,
                packet.payload()
            );

            System.out.println(
                "Ethernet frame size: " + frame.frameSize()
            );

            System.out.println("\nROUTING");

            RoutingTable routingTable = new RoutingTable();

            routingTable.add(
                new Route(
                    IPv4Network.create("203.0.113.0/24"),
                    IPv4Address.parse("192.168.1.1"),
                    "eth0",
                    1
                )
            );

            routingTable.add(
                new Route(
                    IPv4Network.create("0.0.0.0/0"),
                    IPv4Address.parse("192.168.1.254"),
                    "eth1",
                    10
                )
            );

            NetworkMonitor monitor = new NetworkMonitor();

            NetworkService service =
                new NetworkService(routingTable, monitor);

            IPv4Packet forwarded = service.transmit(packet);

            System.out.println(
                "Forwarded TTL: " + forwarded.ttl()
            );

            System.out.println("\nDNS");

            DNSCache dns = new DNSCache();

            dns.add("example.com", "93.184.216.34", 120);

            System.out.println(
                "Resolved: " + dns.resolve("example.com")
            );

            System.out.println("\nFRAGMENTATION");

            System.out.println(
                FragmentationService.calculate(4000, 1500)
            );

            System.out.println("\nMONITORING");

            System.out.println(monitor.report());

            System.out.println("\nTCP TERMINATION");

            connection.close();

            System.out.println(
                "Final state: " + connection.state()
            );

            System.out.println("\nNETWORK EXECUTION COMPLETED");

        } catch (NetworkException exception) {
            System.err.println(
                "Network operation failed: " + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
