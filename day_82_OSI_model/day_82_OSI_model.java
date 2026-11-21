import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;

/*
 * OSI Model: Enterprise Network Communication Architecture.
 *
 * Enterprise-oriented features:
 * - Explicit domain types.
 * - Seven-layer processing pipeline.
 * - Network endpoint validation.
 * - Protocol policy management.
 * - Session state transitions.
 * - TCP and UDP transport modeling.
 * - Packet encapsulation.
 * - Immutable packet records.
 * - Diagnostics and audit events.
 * - Failure isolation.
 */

public class OSIEnterprise {

    enum OSILayer {
        PHYSICAL(1, "Physical"),
        DATA_LINK(2, "Data Link"),
        NETWORK(3, "Network"),
        TRANSPORT(4, "Transport"),
        SESSION(5, "Session"),
        PRESENTATION(6, "Presentation"),
        APPLICATION(7, "Application");

        private final int number;
        private final String description;

        OSILayer(int number, String description) {
            this.number = number;
            this.description = description;
        }

        public int number() {
            return number;
        }

        public String description() {
            return description;
        }
    }

    enum TransportProtocol {
        TCP(6),
        UDP(17);

        private final int ipProtocolNumber;

        TransportProtocol(int number) {
            ipProtocolNumber = number;
        }

        public int ipProtocolNumber() {
            return ipProtocolNumber;
        }
    }

    enum SessionState {
        ACTIVE,
        CLOSED,
        FAILED
    }

    static class NetworkException extends RuntimeException {
        private final OSILayer layer;

        NetworkException(OSILayer layer, String message) {
            super(message);
            this.layer = layer;
        }

        OSILayer layer() {
            return layer;
        }
    }

    record Endpoint(
        String ipAddress,
        String macAddress,
        int port
    ) {
        Endpoint {
            Objects.requireNonNull(ipAddress);
            Objects.requireNonNull(macAddress);

            if (!isValidIPv4(ipAddress)) {
                throw new IllegalArgumentException("Invalid IPv4 address");
            }

            if (!macAddress.matches(
                "(?i)^([0-9a-f]{2}:){5}[0-9a-f]{2}$"
            )) {
                throw new IllegalArgumentException("Invalid MAC address");
            }

            if (port < 0 || port > 65535) {
                throw new IllegalArgumentException("Invalid port");
            }
        }
    }

    record ApplicationData(
        String protocol,
        String content,
        String encoding
    ) {
        ApplicationData {
            if (protocol == null || protocol.isBlank()) {
                throw new IllegalArgumentException(
                    "Application protocol is required"
                );
            }

            if (content == null || content.isEmpty()) {
                throw new IllegalArgumentException(
                    "Application content is required"
                );
            }

            if (!"UTF-8".equalsIgnoreCase(encoding)) {
                throw new IllegalArgumentException(
                    "Unsupported character encoding"
                );
            }
        }
    }

    record TransportSegment(
        TransportProtocol protocol,
        int sourcePort,
        int destinationPort,
        String payload
    ) {
        TransportSegment {
            Objects.requireNonNull(protocol);

            validatePort(sourcePort);
            validatePort(destinationPort);

            Objects.requireNonNull(payload);
        }
    }

    record IPv4Packet(
        String source,
        String destination,
        int ttl,
        int protocolNumber,
        String payload
    ) {
        IPv4Packet {
            if (!isValidIPv4(source) || !isValidIPv4(destination)) {
                throw new IllegalArgumentException(
                    "Invalid IPv4 packet addressing"
                );
            }

            if (ttl < 1 || ttl > 255) {
                throw new IllegalArgumentException("Invalid TTL");
            }

            if (payload == null) {
                throw new IllegalArgumentException("Missing payload");
            }

            if (payload.getBytes(StandardCharsets.UTF_8).length > 65515) {
                throw new IllegalArgumentException(
                    "IPv4 payload exceeds supported size"
                );
            }
        }
    }

    record EthernetFrame(
        String sourceMac,
        String destinationMac,
        int etherType,
        String payload
    ) {
        EthernetFrame {
            Objects.requireNonNull(payload);

            if (etherType != 0x0800) {
                throw new IllegalArgumentException(
                    "Unsupported EtherType"
                );
            }
        }
    }

    record AuditEvent(
        Instant timestamp,
        OSILayer layer,
        String operation,
        String sessionId,
        String outcome
    ) {}

    static final class NetworkSession {
        private final String id;
        private final Instant createdAt;
        private SessionState state;

        NetworkSession() {
            id = UUID.randomUUID().toString();
            createdAt = Instant.now();
            state = SessionState.ACTIVE;
        }

        String id() {
            return id;
        }

        Instant createdAt() {
            return createdAt;
        }

        SessionState state() {
            return state;
        }

        void close() {
            transition(SessionState.CLOSED);
        }

        void fail() {
            if (state == SessionState.ACTIVE) {
                state = SessionState.FAILED;
            }
        }

        private void transition(SessionState next) {
            if (state != SessionState.ACTIVE ||
                next != SessionState.CLOSED) {
                throw new IllegalStateException(
                    "Invalid session state transition"
                );
            }

            state = next;
        }

        void validate() {
            if (state != SessionState.ACTIVE) {
                throw new NetworkException(
                    OSILayer.SESSION,
                    "Session is not active"
                );
            }
        }
    }

    interface LayerHandler<T, R> {
        R process(T input);
    }

    static final class ProtocolPolicy {
        private final Map<String, Integer> protocols;

        ProtocolPolicy() {
            Map<String, Integer> supported = new HashMap<>();

            supported.put("HTTP", 80);
            supported.put("HTTPS", 443);
            supported.put("DNS", 53);
            supported.put("SSH", 22);
            supported.put("SMTP", 25);
            supported.put("FTP", 21);

            protocols = Collections.unmodifiableMap(supported);
        }

        int resolvePort(String protocol) {
            Integer port = protocols.get(protocol.toUpperCase());

            if (port == null) {
                throw new NetworkException(
                    OSILayer.APPLICATION,
                    "Application protocol is not permitted"
                );
            }

            return port;
        }
    }

    static final class NetworkService {

        private final ProtocolPolicy policy;
        private final Map<String, NetworkSession> sessions;
        private final List<AuditEvent> audit;
        private final EnumMap<OSILayer, Integer> failures;

        NetworkService() {
            policy = new ProtocolPolicy();
            sessions = new HashMap<>();
            audit = new ArrayList<>();
            failures = new EnumMap<>(OSILayer.class);

            for (OSILayer layer : OSILayer.values()) {
                failures.put(layer, 0);
            }
        }

        NetworkSession openSession() {
            NetworkSession session = new NetworkSession();

            sessions.put(session.id(), session);

            record(
                OSILayer.SESSION,
                "OPEN_SESSION",
                session.id(),
                "SUCCESS"
            );

            return session;
        }

        private void record(
            OSILayer layer,
            String operation,
            String sessionId,
            String outcome
        ) {
            audit.add(new AuditEvent(
                Instant.now(),
                layer,
                operation,
                sessionId,
                outcome
            ));
        }

        private void recordFailure(
            OSILayer layer,
            String sessionId,
            String operation
        ) {
            failures.merge(layer, 1, Integer::sum);

            record(
                layer,
                operation,
                sessionId,
                "FAILURE"
            );
        }

        String transmit(
            NetworkSession session,
            Endpoint source,
            Endpoint destination,
            String applicationProtocol,
            TransportProtocol transportProtocol,
            String message
        ) {
            Objects.requireNonNull(session);
            Objects.requireNonNull(source);
            Objects.requireNonNull(destination);

            try {
                session.validate();

                // Layer 7: Application protocol policy.
                int destinationPort = policy.resolvePort(
                    applicationProtocol
                );

                ApplicationData application = new ApplicationData(
                    applicationProtocol,
                    message,
                    "UTF-8"
                );

                record(
                    OSILayer.APPLICATION,
                    "VALIDATE_APPLICATION",
                    session.id(),
                    "SUCCESS"
                );

                // Layer 6: Presentation encoding.
                byte[] encoded = application.content().getBytes(
                    StandardCharsets.UTF_8
                );

                String presentationPayload = new String(
                    encoded,
                    StandardCharsets.UTF_8
                );

                record(
                    OSILayer.PRESENTATION,
                    "ENCODE_UTF8",
                    session.id(),
                    "SUCCESS"
                );

                // Layer 5: Session association.
                session.validate();

                record(
                    OSILayer.SESSION,
                    "ASSOCIATE_SESSION",
                    session.id(),
                    "SUCCESS"
                );

                // Layer 4: Transport segmentation metadata.
                TransportSegment segment = new TransportSegment(
                    transportProtocol,
                    source.port() == 0 ? 52000 : source.port(),
                    destinationPort,
                    presentationPayload
                );

                record(
                    OSILayer.TRANSPORT,
                    "CREATE_TRANSPORT_SEGMENT",
                    session.id(),
                    "SUCCESS"
                );

                // Layer 3: Logical addressing and routing metadata.
                IPv4Packet packet = new IPv4Packet(
                    source.ipAddress(),
                    destination.ipAddress(),
                    64,
                    transportProtocol.ipProtocolNumber(),
                    segment.payload()
                );

                record(
                    OSILayer.NETWORK,
                    "CREATE_IPV4_PACKET",
                    session.id(),
                    "SUCCESS"
                );

                // Layer 2: Local-link delivery metadata.
                EthernetFrame frame = new EthernetFrame(
                    source.macAddress(),
                    destination.macAddress(),
                    0x0800,
                    packet.payload()
                );

                record(
                    OSILayer.DATA_LINK,
                    "CREATE_ETHERNET_FRAME",
                    session.id(),
                    "SUCCESS"
                );

                // Layer 1: Physical transmission abstraction.
                byte[] transmitted = frame.payload().getBytes(
                    StandardCharsets.UTF_8
                );

                if (transmitted.length == 0) {
                    throw new NetworkException(
                        OSILayer.PHYSICAL,
                        "Empty physical transmission"
                    );
                }

                record(
                    OSILayer.PHYSICAL,
                    "TRANSMIT_BITS",
                    session.id(),
                    "SUCCESS"
                );

                return sha256(transmitted);

            } catch (NetworkException exception) {
                session.fail();

                recordFailure(
                    exception.layer(),
                    session.id(),
                    "TRANSMISSION"
                );

                throw exception;

            } catch (IllegalArgumentException exception) {
                session.fail();

                recordFailure(
                    OSILayer.NETWORK,
                    session.id(),
                    "VALIDATION"
                );

                throw exception;
            }
        }

        void closeSession(NetworkSession session) {
            session.close();

            record(
                OSILayer.SESSION,
                "CLOSE_SESSION",
                session.id(),
                "SUCCESS"
            );
        }

        List<AuditEvent> getAuditEvents() {
            return List.copyOf(audit);
        }

        Map<OSILayer, Integer> getFailures() {
            return Collections.unmodifiableMap(failures);
        }
    }

    static boolean isValidIPv4(String value) {
        if (value == null) {
            return false;
        }

        String[] parts = value.split("\\.", -1);

        if (parts.length != 4) {
            return false;
        }

        for (String part : parts) {
            if (!part.matches("0|[1-9][0-9]{0,2}")) {
                return false;
            }

            int number = Integer.parseInt(part);

            if (number > 255) {
                return false;
            }
        }

        return true;
    }

    static void validatePort(int port) {
        if (port < 1 || port > 65535) {
            throw new IllegalArgumentException(
                "Port must be between 1 and 65535"
            );
        }
    }

    static String sha256(byte[] data) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");

            byte[] result = digest.digest(data);

            StringBuilder output = new StringBuilder();

            for (byte value : result) {
                output.append(
                    String.format("%02x", value & 0xff)
                );
            }

            return output.toString();

        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException(
                "SHA-256 unavailable",
                exception
            );
        }
    }

    public static void main(String[] args) {

        NetworkService service = new NetworkService();

        Endpoint source = new Endpoint(
            "192.168.1.10",
            "00:11:22:33:44:55",
            52000
        );

        Endpoint destination = new Endpoint(
            "192.168.1.20",
            "AA:BB:CC:DD:EE:FF",
            443
        );

        NetworkSession session = service.openSession();

        String digest = service.transmit(
            session,
            source,
            destination,
            "HTTPS",
            TransportProtocol.TCP,
            "Enterprise OSI communication"
        );

        System.out.println("Transmission successful");
        System.out.println("Session ID: " + session.id());
        System.out.println("SHA-256: " + digest);

        service.closeSession(session);

        // Closed session rejection.
        try {
            session.validate();
        } catch (NetworkException exception) {
            System.out.println(
                "Expected session rejection: " + exception.getMessage()
            );
        }

        // Application policy rejection.
        NetworkSession failedSession = service.openSession();

        try {
            service.transmit(
                failedSession,
                source,
                destination,
                "UNSUPPORTED",
                TransportProtocol.TCP,
                "Invalid application"
            );
        } catch (NetworkException exception) {
            System.out.println(
                "Expected policy rejection: " + exception.getMessage()
            );
        }

        System.out.println("\nLayer Failure Statistics");

        for (OSILayer layer : OSILayer.values()) {
            System.out.println(
                layer.description() + ": "
                + service.getFailures().get(layer)
            );
        }

        System.out.println(
            "\nRecorded audit events: "
            + service.getAuditEvents().size()
        );
    }
}
