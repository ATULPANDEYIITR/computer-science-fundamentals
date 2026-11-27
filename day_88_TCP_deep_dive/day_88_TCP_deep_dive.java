import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

/*
 * TCP Deep Dive: Enterprise-oriented TCP transport model.
 *
 * Java 17 implementation.
 *
 * Concepts:
 * - Connection lifecycle
 * - Three-way handshake
 * - Sequence number tracking
 * - Cumulative acknowledgments
 * - Sliding windows
 * - Retransmission
 * - Congestion control
 * - RTT estimation
 * - Connection termination
 * - Immutable domain records
 * - Concurrent connection management
 *
 * Run:
 * javac TCPDeepDive.java
 * java TCPDeepDive
 */

public class TCPDeepDive {

    private static final int DEFAULT_MSS = 1000;
    private static final int DEFAULT_RECEIVE_WINDOW = 65535;

    enum ConnectionState {
        CLOSED,
        LISTEN,
        SYN_SENT,
        SYN_RECEIVED,
        ESTABLISHED,
        FIN_WAIT_1,
        FIN_WAIT_2,
        CLOSE_WAIT,
        LAST_ACK,
        TIME_WAIT
    }

    enum CongestionState {
        SLOW_START,
        CONGESTION_AVOIDANCE,
        FAST_RECOVERY
    }

    enum SegmentFlag {
        SYN,
        ACK,
        FIN,
        DATA
    }

    static class TCPException extends RuntimeException {
        TCPException(String message) {
            super(message);
        }
    }

    record Segment(
        long sequence,
        long acknowledgment,
        int payloadLength,
        Set<SegmentFlag> flags
    ) {
        Segment {
            if (sequence < 0 || acknowledgment < 0) {
                throw new IllegalArgumentException(
                    "Sequence and ACK numbers cannot be negative"
                );
            }

            if (payloadLength < 0) {
                throw new IllegalArgumentException(
                    "Payload length cannot be negative"
                );
            }

            flags = Collections.unmodifiableSet(
                EnumSet.copyOf(
                    flags.isEmpty()
                        ? EnumSet.noneOf(SegmentFlag.class)
                        : flags
                )
            );
        }

        long sequenceLength() {
            return payloadLength
                + (flags.contains(SegmentFlag.SYN) ? 1 : 0)
                + (flags.contains(SegmentFlag.FIN) ? 1 : 0);
        }
    }

    record ConnectionSnapshot(
        String name,
        ConnectionState state,
        long sndUna,
        long sndNxt,
        long rcvNxt,
        double congestionWindow,
        double slowStartThreshold,
        CongestionState congestionState,
        double retransmissionTimeout
    ) {}

    record Statistics(
        long transmittedSegments,
        long retransmissions,
        long acknowledgedBytes,
        long duplicateAcknowledgments,
        long timeouts,
        long droppedSegments
    ) {}

    static final class RTTEstimator {

        private Double smoothedRtt;
        private Double rttVariation;

        private double rto = 1000.0;

        private static final double ALPHA = 0.125;
        private static final double BETA = 0.25;

        void observe(double sample) {
            if (!Double.isFinite(sample) || sample <= 0) {
                throw new IllegalArgumentException(
                    "RTT must be a positive finite value"
                );
            }

            if (smoothedRtt == null) {
                smoothedRtt = sample;
                rttVariation = sample / 2.0;
            } else {
                double difference =
                    Math.abs(smoothedRtt - sample);

                rttVariation =
                    (1 - BETA) * rttVariation
                    + BETA * difference;

                smoothedRtt =
                    (1 - ALPHA) * smoothedRtt
                    + ALPHA * sample;
            }

            rto = Math.max(
                200,
                Math.min(
                    60000,
                    smoothedRtt + 4 * rttVariation
                )
            );
        }

        void backoff() {
            rto = Math.min(rto * 2, 60000);
        }

        double getRto() {
            return rto;
        }

        OptionalDouble getSmoothedRtt() {
            return smoothedRtt == null
                ? OptionalDouble.empty()
                : OptionalDouble.of(smoothedRtt);
        }
    }

    static final class CongestionController {

        private double cwnd = 1.0;
        private double ssthresh = 16.0;

        private CongestionState state =
            CongestionState.SLOW_START;

        void onAcknowledgment() {
            switch (state) {
                case SLOW_START -> {
                    cwnd += 1;

                    if (cwnd >= ssthresh) {
                        state =
                            CongestionState.CONGESTION_AVOIDANCE;
                    }
                }

                case CONGESTION_AVOIDANCE ->
                    cwnd += 1.0 / cwnd;

                case FAST_RECOVERY -> {
                    cwnd = ssthresh;
                    state =
                        CongestionState.CONGESTION_AVOIDANCE;
                }
            }
        }

        void onTripleDuplicateAck() {
            ssthresh = Math.max(cwnd / 2.0, 2.0);
            cwnd = ssthresh + 3.0;
            state = CongestionState.FAST_RECOVERY;
        }

        void onTimeout() {
            ssthresh = Math.max(cwnd / 2.0, 2.0);
            cwnd = 1.0;
            state = CongestionState.SLOW_START;
        }

        double getCwnd() {
            return cwnd;
        }

        double getSsthresh() {
            return ssthresh;
        }

        CongestionState getState() {
            return state;
        }
    }

    static final class OutstandingSegment {

        private final Segment segment;

        private long sentAt;

        private boolean retransmitted;

        OutstandingSegment(Segment segment, long sentAt) {
            this.segment = segment;
            this.sentAt = sentAt;
        }

        Segment getSegment() {
            return segment;
        }

        long getSentAt() {
            return sentAt;
        }

        void markRetransmitted(long timestamp) {
            sentAt = timestamp;
            retransmitted = true;
        }

        boolean wasRetransmitted() {
            return retransmitted;
        }
    }

    static final class TCPEndpoint {

        private final String name;

        private ConnectionState state =
            ConnectionState.CLOSED;

        private long iss;
        private long sndUna;
        private long sndNxt;
        private long rcvNxt;

        private final int mss;
        private final int receiverWindow;

        private int duplicateAcks;

        private final NavigableMap<Long, OutstandingSegment>
            outstanding = new TreeMap<>();

        private final CongestionController congestion =
            new CongestionController();

        private final RTTEstimator rtt =
            new RTTEstimator();

        private long transmitted;
        private long retransmissions;
        private long acknowledgedBytes;
        private long duplicateAcknowledgments;
        private long timeouts;
        private long dropped;

        TCPEndpoint(
            String name,
            long initialSequence,
            int mss,
            int receiverWindow
        ) {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                    "Endpoint name is required"
                );
            }

            if (
                initialSequence < 0 ||
                mss <= 0 ||
                receiverWindow < 0 ||
                receiverWindow > 65535
            ) {
                throw new IllegalArgumentException(
                    "Invalid endpoint configuration"
                );
            }

            this.name = name;
            this.iss = initialSequence;
            this.sndUna = initialSequence;
            this.sndNxt = initialSequence;
            this.mss = mss;
            this.receiverWindow = receiverWindow;
        }

        void connect(TCPEndpoint peer) {

            if (state != ConnectionState.CLOSED) {
                throw new TCPException(
                    "Local endpoint is not closed"
                );
            }

            if (
                peer.state != ConnectionState.CLOSED &&
                peer.state != ConnectionState.LISTEN
            ) {
                throw new TCPException(
                    "Peer cannot accept a connection"
                );
            }

            state = ConnectionState.SYN_SENT;
            peer.state = ConnectionState.LISTEN;

            Segment syn = new Segment(
                sndNxt,
                0,
                0,
                EnumSet.of(SegmentFlag.SYN)
            );

            sndNxt++;
            transmitted++;

            System.out.println(
                name + " -> " + peer.name
                + " SYN seq=" + syn.sequence()
            );

            peer.rcvNxt = syn.sequence() + 1;

            peer.iss = peer.sndNxt;
            peer.sndUna = peer.iss;
            peer.sndNxt++;

            peer.state = ConnectionState.SYN_RECEIVED;

            Segment synAck = new Segment(
                peer.iss,
                peer.rcvNxt,
                0,
                EnumSet.of(
                    SegmentFlag.SYN,
                    SegmentFlag.ACK
                )
            );

            peer.transmitted++;

            System.out.println(
                peer.name + " -> " + name
                + " SYN-ACK seq=" + synAck.sequence()
                + " ack=" + synAck.acknowledgment()
            );

            rcvNxt = synAck.sequence() + 1;
            sndUna = synAck.acknowledgment();

            Segment ack = new Segment(
                sndNxt,
                rcvNxt,
                0,
                EnumSet.of(SegmentFlag.ACK)
            );

            transmitted++;
            peer.sndUna = ack.acknowledgment();

            state = ConnectionState.ESTABLISHED;
            peer.state = ConnectionState.ESTABLISHED;

            System.out.println(
                name + " -> " + peer.name
                + " ACK ack=" + ack.acknowledgment()
            );

            System.out.println("Connection established.");
        }

        int send(byte[] data, long timestamp) {

            if (state != ConnectionState.ESTABLISHED) {
                throw new TCPException(
                    "Connection is not established"
                );
            }

            Objects.requireNonNull(data);

            if (data.length == 0) {
                return 0;
            }

            int congestionLimit = (int)
                Math.floor(congestion.getCwnd() * mss);

            int effectiveWindow = Math.min(
                congestionLimit,
                receiverWindow
            );

            long inFlight = sndNxt - sndUna;

            int available = (int) Math.max(
                0,
                effectiveWindow - inFlight
            );

            int payloadLength = Math.min(
                data.length,
                Math.min(mss, available)
            );

            if (payloadLength == 0) {
                return 0;
            }

            Segment segment = new Segment(
                sndNxt,
                rcvNxt,
                payloadLength,
                EnumSet.of(
                    SegmentFlag.ACK,
                    SegmentFlag.DATA
                )
            );

            outstanding.put(
                sndNxt,
                new OutstandingSegment(segment, timestamp)
            );

            sndNxt += payloadLength;
            transmitted++;

            System.out.println(
                "Sending DATA seq=" + segment.sequence()
                + " bytes=" + payloadLength
            );

            return payloadLength;
        }

        void receiveData(
            long sequence,
            int payloadLength,
            TCPEndpoint sender
        ) {
            if (sequence == rcvNxt) {
                rcvNxt += payloadLength;

                System.out.println(
                    name + " accepted " + payloadLength
                    + " bytes; expected=" + rcvNxt
                );
            } else {
                System.out.println(
                    name + " out-of-order data. Expected="
                    + rcvNxt + ", received=" + sequence
                );
            }

            sender.processAck(rcvNxt);
        }

        void processAck(long acknowledgment) {

            if (acknowledgment > sndNxt) {
                throw new TCPException(
                    "ACK exceeds transmitted sequence"
                );
            }

            if (acknowledgment < sndUna) {
                return;
            }

            if (acknowledgment == sndUna) {
                duplicateAcks++;
                duplicateAcknowledgments++;

                if (duplicateAcks == 3) {
                    fastRetransmit();
                }

                return;
            }

            long newlyAcknowledged =
                acknowledgment - sndUna;

            sndUna = acknowledgment;
            duplicateAcks = 0;

            Iterator<Map.Entry<Long, OutstandingSegment>>
                iterator = outstanding.entrySet().iterator();

            while (iterator.hasNext()) {
                Map.Entry<Long, OutstandingSegment> entry =
                    iterator.next();

                long end = entry.getKey()
                    + entry.getValue()
                        .getSegment()
                        .sequenceLength();

                if (end <= acknowledgment) {
                    iterator.remove();
                }
            }

            acknowledgedBytes += newlyAcknowledged;

            congestion.onAcknowledgment();

            System.out.println(
                "ACK=" + acknowledgment
                + ", acknowledged=" + newlyAcknowledged
                + ", cwnd=" + congestion.getCwnd()
            );
        }

        private void fastRetransmit() {

            if (outstanding.isEmpty()) {
                return;
            }

            congestion.onTripleDuplicateAck();

            OutstandingSegment oldest =
                outstanding.firstEntry().getValue();

            oldest.markRetransmitted(
                System.currentTimeMillis()
            );

            retransmissions++;

            System.out.println(
                "Fast retransmission: seq="
                + oldest.getSegment().sequence()
            );
        }

        boolean processTimeout(
            long sequence,
            long currentTime
        ) {
            OutstandingSegment segment =
                outstanding.get(sequence);

            if (segment == null) {
                return false;
            }

            if (
                currentTime - segment.getSentAt()
                < rtt.getRto()
            ) {
                return false;
            }

            segment.markRetransmitted(currentTime);

            rtt.backoff();
            congestion.onTimeout();

            retransmissions++;
            timeouts++;
            duplicateAcks = 0;

            System.out.println(
                "Timeout. Retransmitting sequence "
                + sequence + "; RTO=" + rtt.getRto()
            );

            return true;
        }

        void observeRtt(double sample) {
            rtt.observe(sample);
        }

        void terminate(TCPEndpoint peer) {

            if (state != ConnectionState.ESTABLISHED) {
                throw new TCPException(
                    "Only established connections can close"
                );
            }

            state = ConnectionState.FIN_WAIT_1;

            Segment fin = new Segment(
                sndNxt,
                0,
                0,
                EnumSet.of(
                    SegmentFlag.FIN,
                    SegmentFlag.ACK
                )
            );

            sndNxt++;
            transmitted++;

            peer.rcvNxt = fin.sequence() + 1;
            peer.state = ConnectionState.CLOSE_WAIT;

            sndUna = sndNxt;
            state = ConnectionState.FIN_WAIT_2;

            peer.state = ConnectionState.LAST_ACK;
            peer.sndNxt++;
            peer.sndUna = peer.sndNxt;

            rcvNxt = peer.sndNxt;

            state = ConnectionState.TIME_WAIT;
            peer.state = ConnectionState.CLOSED;

            System.out.println(
                "FIN/ACK exchange completed. "
                + "Active endpoint enters TIME_WAIT."
            );
        }

        ConnectionSnapshot snapshot() {
            return new ConnectionSnapshot(
                name,
                state,
                sndUna,
                sndNxt,
                rcvNxt,
                congestion.getCwnd(),
                congestion.getSsthresh(),
                congestion.getState(),
                rtt.getRto()
            );
        }

        Statistics statistics() {
            return new Statistics(
                transmitted,
                retransmissions,
                acknowledgedBytes,
                duplicateAcknowledgments,
                timeouts,
                dropped
            );
        }
    }

    static final class ConnectionRegistry {

        private final Map<String, TCPEndpoint> endpoints =
            new ConcurrentHashMap<>();

        private final AtomicLong connectionCounter =
            new AtomicLong();

        String register(TCPEndpoint endpoint) {
            Objects.requireNonNull(endpoint);

            String id = "TCP-" +
                connectionCounter.incrementAndGet();

            if (endpoints.putIfAbsent(id, endpoint) != null) {
                throw new TCPException(
                    "Duplicate connection identifier"
                );
            }

            return id;
        }

        TCPEndpoint find(String id) {
            TCPEndpoint endpoint = endpoints.get(id);

            if (endpoint == null) {
                throw new TCPException(
                    "Connection not found: " + id
                );
            }

            return endpoint;
        }

        void remove(String id) {
            if (endpoints.remove(id) == null) {
                throw new TCPException(
                    "Cannot remove unknown connection"
                );
            }
        }

        int size() {
            return endpoints.size();
        }
    }

    private static void demonstrateHandshake() {
        System.out.println("\n=== THREE-WAY HANDSHAKE ===");

        TCPEndpoint client = new TCPEndpoint(
            "Client", 1000,
            DEFAULT_MSS,
            DEFAULT_RECEIVE_WINDOW
        );

        TCPEndpoint server = new TCPEndpoint(
            "Server", 5000,
            DEFAULT_MSS,
            DEFAULT_RECEIVE_WINDOW
        );

        client.connect(server);

        if (
            client.snapshot().state()
            != ConnectionState.ESTABLISHED
        ) {
            throw new AssertionError(
                "Handshake failed"
            );
        }
    }

    private static void demonstrateTransmission() {
        System.out.println("\n=== DATA TRANSMISSION ===");

        TCPEndpoint sender = new TCPEndpoint(
            "Sender", 2000,
            DEFAULT_MSS,
            DEFAULT_RECEIVE_WINDOW
        );

        TCPEndpoint receiver = new TCPEndpoint(
            "Receiver", 8000,
            DEFAULT_MSS,
            DEFAULT_RECEIVE_WINDOW
        );

        sender.connect(receiver);

        int sent = sender.send(
            "TCP reliable transmission".getBytes(),
            1000
        );

        receiver.receiveData(
            sender.snapshot().sndUna() + 1,
            sent,
            sender
        );

        System.out.println(sender.snapshot());
        System.out.println(sender.statistics());
    }

    private static void demonstrateTimeout() {
        System.out.println("\n=== RETRANSMISSION ===");

        TCPEndpoint sender = new TCPEndpoint(
            "TimeoutSender", 3000,
            DEFAULT_MSS,
            DEFAULT_RECEIVE_WINDOW
        );

        TCPEndpoint receiver = new TCPEndpoint(
            "TimeoutReceiver", 9000,
            DEFAULT_MSS,
            DEFAULT_RECEIVE_WINDOW
        );

        sender.connect(receiver);

        sender.send(
            new byte[1000],
            1000
        );

        boolean retransmitted =
            sender.processTimeout(3001, 3000);

        if (!retransmitted) {
            throw new AssertionError(
                "Expected retransmission"
            );
        }

        System.out.println(sender.snapshot());
    }

    private static void demonstrateRTT() {
        System.out.println("\n=== RTT ESTIMATION ===");

        RTTEstimator estimator = new RTTEstimator();

        for (double sample : List.of(
            120.0, 150.0, 110.0, 180.0, 140.0
        )) {
            estimator.observe(sample);

            System.out.printf(
                Locale.ROOT,
                "Sample %.2f ms, RTO %.2f ms%n",
                sample,
                estimator.getRto()
            );
        }
    }

    private static void demonstrateRegistry() {
        System.out.println("\n=== CONNECTION REGISTRY ===");

        ConnectionRegistry registry =
            new ConnectionRegistry();

        TCPEndpoint endpoint = new TCPEndpoint(
            "EnterpriseEndpoint",
            10000,
            DEFAULT_MSS,
            DEFAULT_RECEIVE_WINDOW
        );

        String id = registry.register(endpoint);

        System.out.println(
            "Registered: " + id
        );

        System.out.println(
            "Endpoint: " + registry.find(id).snapshot()
        );

        System.out.println(
            "Active endpoints: " + registry.size()
        );

        registry.remove(id);
    }

    public static void main(String[] args) {

        try {
            System.out.println(
                "TCP DEEP DIVE - JAVA 17"
            );

            demonstrateHandshake();
            demonstrateTransmission();
            demonstrateTimeout();
            demonstrateRTT();
            demonstrateRegistry();

            System.out.println(
                "\nTCP demonstrations completed."
            );

        } catch (RuntimeException exception) {
            System.err.println(
                "TCP execution error: "
                + exception.getMessage()
            );

            System.exit(1);
        }
    }
}
