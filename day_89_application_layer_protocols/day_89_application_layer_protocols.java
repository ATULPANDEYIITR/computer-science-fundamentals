import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

// ============================================================
// Application Layer Protocols
// Enterprise Protocol Governance
// Java 17
// ============================================================

public class ApplicationProtocolEnterprise {

    // ========================================================
    // 1. Protocol domain model
    // ========================================================

    enum Protocol {
        HTTP(80, Transport.TCP, false),
        HTTPS(443, Transport.TCP, true),
        DNS(53, Transport.TCP_UDP, false),
        SMTP(587, Transport.TCP, true),
        FTP(21, Transport.TCP, false),
        SSH(22, Transport.TCP, true);

        private final int defaultPort;
        private final Transport transport;
        private final boolean encrypted;

        Protocol(
            int defaultPort,
            Transport transport,
            boolean encrypted
        ) {
            this.defaultPort = defaultPort;
            this.transport = transport;
            this.encrypted = encrypted;
        }

        public int defaultPort() {
            return defaultPort;
        }

        public Transport transport() {
            return transport;
        }

        public boolean encrypted() {
            return encrypted;
        }
    }

    enum Transport {
        TCP,
        UDP,
        TCP_UDP
    }

    enum ConnectionState {
        DISCONNECTED,
        CONNECTING,
        CONNECTED,
        AUTHENTICATED,
        CLOSED,
        FAILED
    }

    enum DNSRecordType {
        A,
        AAAA,
        MX,
        NS,
        CNAME,
        TXT
    }

    enum ReviewStatus {
        ACCEPTED,
        REJECTED
    }

    // ========================================================
    // 2. Exceptions
    // ========================================================

    static class ProtocolException extends RuntimeException {
        ProtocolException(String message) {
            super(message);
        }
    }

    static class PolicyViolationException extends ProtocolException {
        PolicyViolationException(String message) {
            super(message);
        }
    }

    // ========================================================
    // 3. Validated value objects
    // ========================================================

    record Endpoint(String hostname, int port) {

        private static final Pattern HOSTNAME = Pattern.compile(
            "^(?=.{1,253}$)"
            + "[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}"
            + "[a-zA-Z0-9])?"
            + "(?:\\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}"
            + "[a-zA-Z0-9])?)*\\.?$"
        );

        Endpoint {
            Objects.requireNonNull(hostname);

            if (!HOSTNAME.matcher(hostname).matches()) {
                throw new ProtocolException("Invalid hostname.");
            }

            if (port < 1 || port > 65535) {
                throw new ProtocolException("Invalid port.");
            }
        }
    }

    record DNSRecord(
        String hostname,
        DNSRecordType type,
        String value,
        int ttl
    ) {
        DNSRecord {
            Objects.requireNonNull(hostname);
            Objects.requireNonNull(type);
            Objects.requireNonNull(value);

            if (hostname.isBlank() || value.isBlank()) {
                throw new ProtocolException(
                    "DNS record fields cannot be blank."
                );
            }

            if (ttl <= 0) {
                throw new ProtocolException(
                    "DNS TTL must be positive."
                );
            }
        }
    }

    record ProtocolRequest(
        UUID id,
        Protocol protocol,
        Endpoint endpoint,
        String operation,
        boolean authenticated,
        boolean certificateVerified,
        boolean hostKeyVerified,
        long payloadBytes,
        Instant createdAt
    ) {
        ProtocolRequest {
            Objects.requireNonNull(id);
            Objects.requireNonNull(protocol);
            Objects.requireNonNull(endpoint);
            Objects.requireNonNull(operation);
            Objects.requireNonNull(createdAt);

            if (operation.isBlank()) {
                throw new ProtocolException(
                    "Operation cannot be empty."
                );
            }

            if (payloadBytes < 0) {
                throw new ProtocolException(
                    "Payload size cannot be negative."
                );
            }
        }
    }

    // ========================================================
    // 4. Immutable policy object
    // ========================================================

    record ProtocolPolicy(
        Set<Protocol> allowedProtocols,
        Set<Integer> allowedPorts,
        boolean requireEncryption,
        boolean requireAuthentication,
        long maximumPayloadBytes
    ) {
        ProtocolPolicy {
            allowedProtocols = Collections.unmodifiableSet(
                new HashSet<>(allowedProtocols)
            );

            allowedPorts = Collections.unmodifiableSet(
                new HashSet<>(allowedPorts)
            );

            if (maximumPayloadBytes < 1) {
                throw new ProtocolException(
                    "Invalid maximum payload size."
                );
            }
        }

        static ProtocolPolicy enterpriseDefault() {
            return new ProtocolPolicy(
                Set.of(
                    Protocol.HTTPS,
                    Protocol.DNS,
                    Protocol.SMTP,
                    Protocol.SSH
                ),
                Set.of(53, 443, 587, 22),
                true,
                true,
                1_048_576
            );
        }
    }

    // ========================================================
    // 5. Policy decision
    // ========================================================

    record PolicyDecision(
        ReviewStatus status,
        List<String> violations
    ) {
        PolicyDecision {
            violations = List.copyOf(violations);
        }

        boolean allowed() {
            return status == ReviewStatus.ACCEPTED;
        }
    }

    // ========================================================
    // 6. Policy evaluation service
    // ========================================================

    static class ProtocolPolicyService {

        private final ProtocolPolicy policy;

        ProtocolPolicyService(ProtocolPolicy policy) {
            this.policy = Objects.requireNonNull(policy);
        }

        PolicyDecision evaluate(ProtocolRequest request) {

            List<String> violations = new ArrayList<>();

            Protocol protocol = request.protocol();

            if (!policy.allowedProtocols().contains(protocol)) {
                violations.add(
                    "Protocol is not authorized."
                );
            }

            if (!policy.allowedPorts().contains(
                request.endpoint().port()
            )) {
                violations.add(
                    "Destination port is not authorized."
                );
            }

            if (
                policy.requireEncryption()
                && !protocol.encrypted()
            ) {
                violations.add(
                    "Encrypted transport is required."
                );
            }

            if (
                policy.requireAuthentication()
                && !request.authenticated()
            ) {
                violations.add(
                    "Authentication is required."
                );
            }

            if (
                request.payloadBytes()
                > policy.maximumPayloadBytes()
            ) {
                violations.add(
                    "Payload exceeds enterprise limit."
                );
            }

            if (
                protocol == Protocol.HTTPS
                && !request.certificateVerified()
            ) {
                violations.add(
                    "TLS certificate validation failed."
                );
            }

            if (
                protocol == Protocol.SSH
                && !request.hostKeyVerified()
            ) {
                violations.add(
                    "SSH host-key validation failed."
                );
            }

            return new PolicyDecision(
                violations.isEmpty()
                    ? ReviewStatus.ACCEPTED
                    : ReviewStatus.REJECTED,
                violations
            );
        }
    }

    // ========================================================
    // 7. Connection lifecycle service
    // ========================================================

    static class ProtocolSession {

        private final Protocol protocol;

        private ConnectionState state =
            ConnectionState.DISCONNECTED;

        ProtocolSession(Protocol protocol) {
            this.protocol = Objects.requireNonNull(protocol);
        }

        public ConnectionState state() {
            return state;
        }

        public void connect() {
            transition(
                ConnectionState.DISCONNECTED,
                ConnectionState.CONNECTING
            );

            state = ConnectionState.CONNECTED;
        }

        public void authenticate() {
            transition(
                ConnectionState.CONNECTED,
                ConnectionState.AUTHENTICATED
            );
        }

        public void close() {
            if (state == ConnectionState.CLOSED) {
                return;
            }

            state = ConnectionState.CLOSED;
        }

        public void fail() {
            state = ConnectionState.FAILED;
        }

        private void transition(
            ConnectionState expected,
            ConnectionState next
        ) {
            if (state != expected) {
                throw new ProtocolException(
                    protocol + " cannot transition from "
                    + state + " to " + next
                );
            }

            state = next;
        }
    }

    // ========================================================
    // 8. DNS repository
    // ========================================================

    static class DNSRepository {

        private final Map<String, List<DNSRecord>> records =
            new HashMap<>();

        public void save(DNSRecord record) {
            String key = record.hostname().toLowerCase();

            records.computeIfAbsent(
                key,
                ignored -> new ArrayList<>()
            ).add(record);
        }

        public List<DNSRecord> find(
            String hostname,
            DNSRecordType type
        ) {
            return records.getOrDefault(
                hostname.toLowerCase(),
                List.of()
            )
            .stream()
            .filter(record -> record.type() == type)
            .toList();
        }

        public long countRecords() {
            return records.values()
                .stream()
                .mapToLong(List::size)
                .sum();
        }
    }

    // ========================================================
    // 9. Protocol audit repository
    // ========================================================

    record AuditEntry(
        UUID requestId,
        Protocol protocol,
        ReviewStatus status,
        List<String> violations,
        Instant timestamp
    ) {
        AuditEntry {
            violations = List.copyOf(violations);
        }
    }

    static class AuditRepository {

        private final List<AuditEntry> entries =
            new ArrayList<>();

        public void save(AuditEntry entry) {
            entries.add(entry);
        }

        public List<AuditEntry> findFailures() {
            return entries.stream()
                .filter(entry ->
                    entry.status() == ReviewStatus.REJECTED
                )
                .toList();
        }

        public Map<Protocol, Long> countByProtocol() {
            return entries.stream().collect(
                Collectors.groupingBy(
                    AuditEntry::protocol,
                    () -> new EnumMap<>(Protocol.class),
                    Collectors.counting()
                )
            );
        }

        public List<AuditEntry> all() {
            return List.copyOf(entries);
        }
    }

    // ========================================================
    // 10. Application service
    // ========================================================

    static class ProtocolApplicationService {

        private final ProtocolPolicyService policyService;
        private final AuditRepository auditRepository;

        ProtocolApplicationService(
            ProtocolPolicyService policyService,
            AuditRepository auditRepository
        ) {
            this.policyService = policyService;
            this.auditRepository = auditRepository;
        }

        public PolicyDecision process(
            Protocol protocol,
            Endpoint endpoint,
            String operation,
            boolean authenticated,
            boolean certificateVerified,
            boolean hostKeyVerified,
            long payloadBytes
        ) {

            ProtocolRequest request = new ProtocolRequest(
                UUID.randomUUID(),
                protocol,
                endpoint,
                operation,
                authenticated,
                certificateVerified,
                hostKeyVerified,
                payloadBytes,
                Instant.now()
            );

            PolicyDecision decision =
                policyService.evaluate(request);

            auditRepository.save(
                new AuditEntry(
                    request.id(),
                    protocol,
                    decision.status(),
                    decision.violations(),
                    Instant.now()
                )
            );

            return decision;
        }
    }

    // ========================================================
    // 11. SMTP transaction model
    // ========================================================

    static class SMTPTransaction {

        private final ProtocolSession session =
            new ProtocolSession(Protocol.SMTP);

        private String sender;

        private final Set<String> recipients =
            new HashSet<>();

        public void establishSecureSession() {
            session.connect();
            session.authenticate();
        }

        public void setSender(String sender) {
            if (session.state() != ConnectionState.AUTHENTICATED) {
                throw new ProtocolException(
                    "SMTP authentication required."
                );
            }

            if (!validEmail(sender)) {
                throw new ProtocolException(
                    "Invalid sender address."
                );
            }

            this.sender = sender;
        }

        public void addRecipient(String recipient) {
            if (sender == null) {
                throw new ProtocolException(
                    "Sender must be specified first."
                );
            }

            if (!validEmail(recipient)) {
                throw new ProtocolException(
                    "Invalid recipient address."
                );
            }

            recipients.add(recipient);
        }

        public boolean readyToSubmit() {
            return sender != null && !recipients.isEmpty();
        }

        private boolean validEmail(String email) {
            return email != null &&
                Pattern.matches(
                    "^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$",
                    email
                );
        }
    }

    // ========================================================
    // 12. Application execution
    // ========================================================

    public static void main(String[] args) {

        System.out.println(
            "APPLICATION LAYER PROTOCOL ENTERPRISE MODEL\n"
        );

        ProtocolPolicy policy =
            ProtocolPolicy.enterpriseDefault();

        ProtocolPolicyService policyService =
            new ProtocolPolicyService(policy);

        AuditRepository auditRepository =
            new AuditRepository();

        ProtocolApplicationService application =
            new ProtocolApplicationService(
                policyService,
                auditRepository
            );

        System.out.println("Protocol definitions:");

        for (Protocol protocol : Protocol.values()) {
            System.out.printf(
                "%-8s Port=%-4d Transport=%-7s Encrypted=%s%n",
                protocol,
                protocol.defaultPort(),
                protocol.transport(),
                protocol.encrypted()
            );
        }

        System.out.println("\nPolicy evaluation:");

        PolicyDecision https = application.process(
            Protocol.HTTPS,
            new Endpoint("api.example.com", 443),
            "GET /api/data",
            true,
            true,
            false,
            2048
        );

        System.out.println(
            "HTTPS: " + https.status()
        );

        PolicyDecision http = application.process(
            Protocol.HTTP,
            new Endpoint("api.example.com", 80),
            "GET /",
            true,
            false,
            false,
            512
        );

        System.out.println(
            "HTTP: " + http.status()
        );

        PolicyDecision ssh = application.process(
            Protocol.SSH,
            new Endpoint("server.example.com", 22),
            "Remote administration",
            true,
            false,
            false,
            1024
        );

        System.out.println(
            "SSH: " + ssh.status()
        );

        // DNS repository.
        DNSRepository dns = new DNSRepository();

        dns.save(new DNSRecord(
            "example.com",
            DNSRecordType.A,
            "192.0.2.10",
            300
        ));

        dns.save(new DNSRecord(
            "example.com",
            DNSRecordType.MX,
            "mail.example.com",
            600
        ));

        System.out.println("\nDNS records:");

        dns.find("example.com", DNSRecordType.A)
            .forEach(System.out::println);

        // SMTP transaction.
        SMTPTransaction smtp = new SMTPTransaction();

        smtp.establishSecureSession();
        smtp.setSender("sender@example.com");
        smtp.addRecipient("recipient@example.com");

        System.out.println(
            "\nSMTP ready for submission: "
            + smtp.readyToSubmit()
        );

        // Connection lifecycle.
        ProtocolSession session =
            new ProtocolSession(Protocol.SSH);

        session.connect();
        session.authenticate();

        System.out.println(
            "SSH session state: " + session.state()
        );

        session.close();

        System.out.println(
            "SSH final state: " + session.state()
        );

        // Audit reporting.
        System.out.println("\nProtocol audit:");

        auditRepository.all().forEach(System.out::println);

        System.out.println("\nFailures:");

        auditRepository.findFailures()
            .forEach(System.out::println);

        System.out.println("\nProtocol request counts:");

        auditRepository.countByProtocol()
            .forEach((protocol, count) ->
                System.out.println(protocol + ": " + count)
            );

        // Assertions.
        if (!https.allowed()) {
            throw new AssertionError(
                "Valid HTTPS request was rejected."
            );
        }

        if (http.allowed()) {
            throw new AssertionError(
                "Unencrypted HTTP request was accepted."
            );
        }

        if (dns.countRecords() != 2) {
            throw new AssertionError(
                "DNS repository integrity failure."
            );
        }

        System.out.println(
            "\nAll enterprise protocol checks passed."
        );
    }
}
