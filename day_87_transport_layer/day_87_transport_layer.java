import java.time.Duration;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

/**
 * Transport Layer Enterprise Engineering Model.
 *
 * Covers:
 * - TCP and UDP.
 * - Port allocation.
 * - Endpoint addressing.
 * - TCP connection state transitions.
 * - Sliding-window flow control.
 * - Cumulative acknowledgements.
 * - Retransmission monitoring.
 * - Enterprise transport policy enforcement.
 *
 * Java 17, standard library only.
 */
public class TransportLayerEnterprise {

    enum Protocol {
        TCP, UDP
    }

    enum ConnectionState {
        CLOSED,
        LISTEN,
        SYN_SENT,
        SYN_RECEIVED,
        ESTABLISHED,
        FIN_WAIT,
        CLOSE_WAIT,
        TIME_WAIT
    }

    enum TransportEvent {
        CONNECTION_CREATED,
        CONNECTION_ESTABLISHED,
        DATA_SENT,
        DATA_ACKNOWLEDGED,
        CONNECTION_CLOSED,
        DATAGRAM_SENT
    }

    static class TransportException extends RuntimeException {
        TransportException(String message) {
            super(message);
        }
    }

    static class PolicyViolationException extends TransportException {
        PolicyViolationException(String message) {
            super(message);
        }
    }

    record Endpoint(String ip, int port) {
        Endpoint {
            Objects.requireNonNull(ip, "IP address is required.");

            if (!ip.matches(
                    "^(?:\\d{1,3}\\.){3}\\d{1,3}$")) {
                throw new IllegalArgumentException(
                    "Invalid IPv4 address format."
                );
            }

            String[] octets = ip.split("\\.");

            for (String octet : octets) {
                int value = Integer.parseInt(octet);

                if (value > 255) {
                    throw new IllegalArgumentException(
                        "Invalid IPv4 octet."
                    );
                }
            }

            if (port < 0 || port > 65535) {
                throw new IllegalArgumentException(
                    "Port must be between 0 and 65535."
                );
            }
        }

        @Override
        public String toString() {
            return ip + ":" + port;
        }
    }

    record ConnectionKey(
        Endpoint local,
        Endpoint remote,
        Protocol protocol
    ) {
        ConnectionKey {
            Objects.requireNonNull(local);
            Objects.requireNonNull(remote);
            Objects.requireNonNull(protocol);
        }
    }

    record Transmission(
        long sequence,
        int length,
        byte[] payload,
        Instant transmittedAt
    ) {
        Transmission {
            payload = payload.clone();
        }

        @Override
        public byte[] payload() {
            return payload.clone();
        }
    }

    static class PortRegistry {
        private final Map<Endpoint, Protocol> bindings =
            new HashMap<>();

        private final Set<Integer> reservedPorts = Set.of(
            20, 21, 22, 23, 25, 53, 80, 110, 143, 443
        );

        public synchronized void bind(
            Endpoint endpoint,
            Protocol protocol
        ) {
            if (endpoint.port() == 0) {
                throw new PolicyViolationException(
                    "Port zero cannot be registered as a listening port."
                );
            }

            Protocol existing = bindings.putIfAbsent(
                endpoint,
                protocol
            );

            if (existing != null) {
                throw new PolicyViolationException(
                    "Endpoint is already bound to " + existing
                );
            }

            System.out.println(
                "Registered " + protocol + " endpoint " + endpoint
            );
        }

        public synchronized void unbind(Endpoint endpoint) {
            if (bindings.remove(endpoint) == null) {
                throw new TransportException(
                    "Endpoint does not exist."
                );
            }
        }

        public synchronized boolean isBound(Endpoint endpoint) {
            return bindings.containsKey(endpoint);
        }

        public boolean isReserved(int port) {
            return reservedPorts.contains(port);
        }

        public synchronized int activeBindings() {
            return bindings.size();
        }
    }

    static class TCPConnection {
        private static final Map<ConnectionState,
            Set<ConnectionState>> TRANSITIONS =
            new EnumMap<>(ConnectionState.class);

        static {
            TRANSITIONS.put(
                ConnectionState.CLOSED,
                Set.of(
                    ConnectionState.LISTEN,
                    ConnectionState.SYN_SENT
                )
            );

            TRANSITIONS.put(
                ConnectionState.LISTEN,
                Set.of(
                    ConnectionState.SYN_RECEIVED,
                    ConnectionState.CLOSED
                )
            );

            TRANSITIONS.put(
                ConnectionState.SYN_SENT,
                Set.of(
                    ConnectionState.SYN_RECEIVED,
                    ConnectionState.CLOSED
                )
            );

            TRANSITIONS.put(
                ConnectionState.SYN_RECEIVED,
                Set.of(
                    ConnectionState.ESTABLISHED,
                    ConnectionState.CLOSED
                )
            );

            TRANSITIONS.put(
                ConnectionState.ESTABLISHED,
                Set.of(
                    ConnectionState.FIN_WAIT,
                    ConnectionState.CLOSE_WAIT
                )
            );

            TRANSITIONS.put(
                ConnectionState.FIN_WAIT,
                Set.of(
                    ConnectionState.TIME_WAIT,
                    ConnectionState.CLOSED
                )
            );

            TRANSITIONS.put(
                ConnectionState.CLOSE_WAIT,
                Set.of(ConnectionState.CLOSED)
            );

            TRANSITIONS.put(
                ConnectionState.TIME_WAIT,
                Set.of(ConnectionState.CLOSED)
            );
        }

        private final ConnectionKey key;
        private ConnectionState state = ConnectionState.CLOSED;
        private long sequenceNumber;
        private long acknowledgementNumber;

        TCPConnection(ConnectionKey key) {
            if (key.protocol() != Protocol.TCP) {
                throw new IllegalArgumentException(
                    "TCP connection requires TCP protocol."
                );
            }

            this.key = key;
        }

        public synchronized void transition(
            ConnectionState next
        ) {
            Set<ConnectionState> allowed =
                TRANSITIONS.getOrDefault(state, Set.of());

            if (!allowed.contains(next)) {
                throw new TransportException(
                    "Invalid state transition: " +
                    state + " -> " + next
                );
            }

            System.out.println(
                "Connection state: " + state + " -> " + next
            );

            state = next;
        }

        public synchronized void establish() {
            transition(ConnectionState.SYN_SENT);
            System.out.println("SYN transmitted.");

            transition(ConnectionState.SYN_RECEIVED);
            System.out.println("SYN-ACK received.");

            transition(ConnectionState.ESTABLISHED);
            System.out.println("ACK transmitted.");
        }

        public synchronized void close() {
            if (state != ConnectionState.ESTABLISHED) {
                throw new TransportException(
                    "Connection is not established."
                );
            }

            transition(ConnectionState.FIN_WAIT);
            transition(ConnectionState.TIME_WAIT);
            transition(ConnectionState.CLOSED);
        }

        public synchronized void sendData(int bytes) {
            if (state != ConnectionState.ESTABLISHED) {
                throw new TransportException(
                    "Data requires an established connection."
                );
            }

            if (bytes <= 0) {
                throw new IllegalArgumentException(
                    "Payload length must be positive."
                );
            }

            sequenceNumber += bytes;

            System.out.println(
                "TCP data transmitted. Next sequence: " +
                sequenceNumber
            );
        }

        public synchronized void acknowledge(long value) {
            if (value < acknowledgementNumber ||
                value > sequenceNumber) {
                throw new TransportException(
                    "Invalid acknowledgement number."
                );
            }

            acknowledgementNumber = value;
        }

        public synchronized ConnectionState state() {
            return state;
        }

        public ConnectionKey key() {
            return key;
        }
    }

    static class FlowControlService {
        private final Deque<Transmission> outstanding =
            new ArrayDeque<>();

        private final long maximumWindow;

        private long receiveWindow;
        private long nextSequence;
        private long lastAcknowledged;

        FlowControlService(long initialWindow) {
            this(initialWindow, 65535);
        }

        FlowControlService(
            long initialWindow,
            long maximumWindow
        ) {
            if (maximumWindow <= 0 ||
                initialWindow < 0 ||
                initialWindow > maximumWindow) {
                throw new IllegalArgumentException(
                    "Invalid flow-control configuration."
                );
            }

            this.receiveWindow = initialWindow;
            this.maximumWindow = maximumWindow;
        }

        private long inFlightBytes() {
            return outstanding.stream()
                .mapToLong(Transmission::length)
                .sum();
        }

        public synchronized long availableWindow() {
            return Math.max(
                0,
                receiveWindow - inFlightBytes()
            );
        }

        public synchronized boolean send(byte[] payload) {
            Objects.requireNonNull(payload);

            if (payload.length == 0) {
                throw new IllegalArgumentException(
                    "Empty payload is not permitted."
                );
            }

            if (payload.length > availableWindow()) {
                System.out.println(
                    "Transmission blocked by receive window."
                );

                return false;
            }

            Transmission transmission = new Transmission(
                nextSequence,
                payload.length,
                payload,
                Instant.now()
            );

            outstanding.addLast(transmission);
            nextSequence += payload.length;

            System.out.println(
                "Sent sequence=" + transmission.sequence() +
                ", bytes=" + transmission.length() +
                ", availableWindow=" + availableWindow()
            );

            return true;
        }

        public synchronized void acknowledge(long ack) {
            if (ack < lastAcknowledged || ack > nextSequence) {
                throw new TransportException(
                    "Invalid cumulative acknowledgement."
                );
            }

            if (ack == lastAcknowledged) {
                return;
            }

            while (!outstanding.isEmpty()) {
                Transmission first = outstanding.peekFirst();

                if (first.sequence() + first.length() <= ack) {
                    outstanding.removeFirst();
                } else {
                    break;
                }
            }

            lastAcknowledged = ack;

            System.out.println(
                "ACK=" + ack +
                ", availableWindow=" + availableWindow()
            );
        }

        public synchronized void advertiseWindow(long size) {
            if (size < 0 || size > maximumWindow) {
                throw new PolicyViolationException(
                    "Advertised window violates configured limits."
                );
            }

            receiveWindow = size;

            System.out.println(
                "Receive window updated: " + receiveWindow
            );
        }

        public synchronized List<Transmission> timedOut(
            Duration timeout
        ) {
            if (timeout.isNegative() || timeout.isZero()) {
                throw new IllegalArgumentException(
                    "Timeout must be positive."
                );
            }

            Instant threshold = Instant.now().minus(timeout);

            return outstanding.stream()
                .filter(item ->
                    item.transmittedAt().isBefore(threshold)
                )
                .toList();
        }

        public synchronized int outstandingSegments() {
            return outstanding.size();
        }
    }

    static class UDPDatagramService {
        private final int maximumDatagramSize;

        UDPDatagramService(int maximumDatagramSize) {
            if (maximumDatagramSize < 1 ||
                maximumDatagramSize > 65507) {
                throw new IllegalArgumentException(
                    "Invalid UDP payload limit."
                );
            }

            this.maximumDatagramSize = maximumDatagramSize;
        }

        public void send(
            Endpoint destination,
            byte[] payload
        ) {
            Objects.requireNonNull(destination);
            Objects.requireNonNull(payload);

            if (destination.port() == 0) {
                throw new PolicyViolationException(
                    "UDP destination port cannot be zero."
                );
            }

            if (payload.length == 0 ||
                payload.length > maximumDatagramSize) {
                throw new TransportException(
                    "UDP payload violates datagram size policy."
                );
            }

            System.out.println(
                "UDP datagram sent to " + destination +
                ", bytes=" + payload.length
            );

            // This model records transmission intent.
            // It does not claim delivery or acknowledgement.
        }
    }

    static class EnterpriseTransportService {
        private final PortRegistry registry =
            new PortRegistry();

        private final Map<ConnectionKey, TCPConnection>
            connections = new HashMap<>();

        private final FlowControlService flowControl =
            new FlowControlService(10);

        private final UDPDatagramService udp =
            new UDPDatagramService(1200);

        public void registerEndpoints() {
            registry.bind(
                new Endpoint("192.168.1.10", 443),
                Protocol.TCP
            );

            registry.bind(
                new Endpoint("192.168.1.10", 53),
                Protocol.UDP
            );

            registry.bind(
                new Endpoint("192.168.1.10", 8080),
                Protocol.TCP
            );
        }

        public void createConnection() {
            ConnectionKey key = new ConnectionKey(
                new Endpoint("192.168.1.10", 52000),
                new Endpoint("192.168.1.20", 443),
                Protocol.TCP
            );

            if (connections.containsKey(key)) {
                throw new TransportException(
                    "Connection already exists."
                );
            }

            TCPConnection connection = new TCPConnection(key);

            connections.put(key, connection);

            connection.establish();
            connection.sendData(512);
            connection.acknowledge(512);

            connection.close();

            connections.remove(key);
        }

        public void demonstrateFlowControl() {
            flowControl.send("123456".getBytes());
            flowControl.send("ABCD".getBytes());
            flowControl.send("XYZ".getBytes());

            flowControl.acknowledge(6);

            flowControl.send("XYZ".getBytes());

            flowControl.acknowledge(13);
            flowControl.advertiseWindow(12);

            flowControl.send("PAYLOAD".getBytes());
        }

        public void demonstrateUDP() {
            udp.send(
                new Endpoint("192.168.1.20", 53),
                "DNS query".getBytes()
            );
        }

        public void report() {
            System.out.println(
                "Registered endpoints: " +
                registry.activeBindings()
            );

            System.out.println(
                "Active modeled connections: " +
                connections.size()
            );

            System.out.println(
                "Outstanding TCP segments: " +
                flowControl.outstandingSegments()
            );
        }
    }

    public static void main(String[] args) {
        System.out.println(
            "TRANSPORT LAYER ENTERPRISE MODEL"
        );

        EnterpriseTransportService service =
            new EnterpriseTransportService();

        try {
            System.out.println("\n--- Endpoint Registration ---");
            service.registerEndpoints();

            System.out.println("\n--- TCP Connection ---");
            service.createConnection();

            System.out.println("\n--- TCP Flow Control ---");
            service.demonstrateFlowControl();

            System.out.println("\n--- UDP Datagram ---");
            service.demonstrateUDP();

            System.out.println("\n--- Operational Report ---");
            service.report();

        } catch (TransportException |
                 IllegalArgumentException error) {

            System.err.println(
                "Transport operation rejected: " +
                error.getMessage()
            );

            System.exitCode = 1;
        }
    }
}
