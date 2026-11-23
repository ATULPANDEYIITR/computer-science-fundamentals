import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;

/**
 * Physical and Data Link Layer
 *
 * Enterprise Ethernet infrastructure simulation.
 *
 * Java 17
 * No third-party dependencies.
 *
 * Includes:
 * - Physical signal encoding
 * - NRZ and Manchester encoding
 * - MAC address management
 * - Ethernet frame construction
 * - CRC-32/FCS validation
 * - Switch port administration
 * - Dynamic MAC learning
 * - Forwarding and flooding
 * - MAC aging
 * - Network policy evaluation
 * - Operational statistics
 */

public class NetworkLayerSimulation {

    // ========================================================
    // 1. EXCEPTIONS
    // ========================================================

    static class NetworkException extends RuntimeException {
        NetworkException(String message) {
            super(message);
        }
    }

    static class IntegrityException extends NetworkException {
        IntegrityException(String message) {
            super(message);
        }
    }

    static class PolicyException extends NetworkException {
        PolicyException(String message) {
            super(message);
        }
    }

    // ========================================================
    // 2. MAC ADDRESS
    // ========================================================

    record MacAddress(String value) {

        MacAddress {
            Objects.requireNonNull(value, "MAC address required");

            value = value.toUpperCase().replace('-', ':');

            if (!value.matches("([0-9A-F]{2}:){5}[0-9A-F]{2}")) {
                throw new IllegalArgumentException("Invalid MAC address.");
            }
        }

        byte[] bytes() {
            String[] parts = value.split(":");
            byte[] result = new byte[6];

            for (int i = 0; i < 6; i++) {
                result[i] = (byte) Integer.parseInt(parts[i], 16);
            }

            return result;
        }

        boolean isMulticast() {
            return (bytes()[0] & 1) != 0;
        }

        boolean isBroadcast() {
            return value.equals("FF:FF:FF:FF:FF:FF");
        }

        @Override
        public String toString() {
            return value;
        }
    }

    static final MacAddress BROADCAST =
        new MacAddress("FF:FF:FF:FF:FF:FF");

    // ========================================================
    // 3. PHYSICAL LAYER
    // ========================================================

    static class PhysicalLayer {

        static void validate(String bits) {
            if (bits == null || !bits.matches("[01]+")) {
                throw new IllegalArgumentException(
                    "A non-empty binary sequence is required."
                );
            }
        }

        static int[] encodeNRZ(String bits) {
            validate(bits);

            int[] signals = new int[bits.length()];

            for (int i = 0; i < bits.length(); i++) {
                signals[i] = bits.charAt(i) - '0';
            }

            return signals;
        }

        static String decodeNRZ(int[] signals) {
            if (signals == null || signals.length == 0) {
                throw new IllegalArgumentException("Empty signal.");
            }

            StringBuilder result = new StringBuilder();

            for (int signal : signals) {
                if (signal != 0 && signal != 1) {
                    throw new NetworkException("Invalid NRZ level.");
                }

                result.append(signal);
            }

            return result.toString();
        }

        static int[] encodeManchester(String bits) {
            validate(bits);

            int[] signals = new int[bits.length() * 2];

            for (int i = 0; i < bits.length(); i++) {
                if (bits.charAt(i) == '0') {
                    signals[2 * i] = 0;
                    signals[2 * i + 1] = 1;
                } else {
                    signals[2 * i] = 1;
                    signals[2 * i + 1] = 0;
                }
            }

            return signals;
        }

        static String decodeManchester(int[] signals) {
            if (signals == null ||
                signals.length == 0 ||
                signals.length % 2 != 0) {
                throw new NetworkException(
                    "Invalid Manchester signal length."
                );
            }

            StringBuilder bits = new StringBuilder();

            for (int i = 0; i < signals.length; i += 2) {
                int first = signals[i];
                int second = signals[i + 1];

                if (first == 0 && second == 1) {
                    bits.append('0');
                } else if (first == 1 && second == 0) {
                    bits.append('1');
                } else {
                    throw new IntegrityException(
                        "Invalid Manchester transition."
                    );
                }
            }

            return bits.toString();
        }
    }

    // ========================================================
    // 4. CRC-32
    // ========================================================

    static class FrameChecksum {

        static long calculate(byte[] data) {
            java.util.zip.CRC32 crc = new java.util.zip.CRC32();
            crc.update(data);
            return crc.getValue();
        }
    }

    // ========================================================
    // 5. ETHERNET FRAME
    // ========================================================

    static final class EthernetFrame {

        static final int HEADER_LENGTH = 14;
        static final int FCS_LENGTH = 4;
        static final int MIN_PAYLOAD = 46;
        static final int MAX_PAYLOAD = 1500;

        private final MacAddress destination;
        private final MacAddress source;
        private final int etherType;
        private final byte[] payload;

        EthernetFrame(
            MacAddress destination,
            MacAddress source,
            byte[] payload,
            int etherType
        ) {
            Objects.requireNonNull(destination);
            Objects.requireNonNull(source);
            Objects.requireNonNull(payload);

            if (source.isMulticast()) {
                throw new IllegalArgumentException(
                    "Source MAC must be unicast."
                );
            }

            if (source.equals(destination)) {
                throw new IllegalArgumentException(
                    "Source and destination must differ."
                );
            }

            if (payload.length > MAX_PAYLOAD) {
                throw new IllegalArgumentException(
                    "Ethernet payload exceeds MTU."
                );
            }

            if (etherType < 0 || etherType > 65535) {
                throw new IllegalArgumentException("Invalid EtherType.");
            }

            this.destination = destination;
            this.source = source;
            this.payload = payload.clone();
            this.etherType = etherType;
        }

        MacAddress destination() {
            return destination;
        }

        MacAddress source() {
            return source;
        }

        byte[] payload() {
            return payload.clone();
        }

        private byte[] content() {
            int payloadLength = Math.max(payload.length, MIN_PAYLOAD);

            ByteBuffer buffer = ByteBuffer.allocate(
                HEADER_LENGTH + payloadLength
            ).order(ByteOrder.BIG_ENDIAN);

            buffer.put(destination.bytes());
            buffer.put(source.bytes());
            buffer.putShort((short) etherType);
            buffer.put(payload);
            buffer.position(HEADER_LENGTH + payloadLength);

            return buffer.array();
        }

        long fcs() {
            return FrameChecksum.calculate(content());
        }

        byte[] serialize() {
            byte[] content = content();

            ByteBuffer buffer = ByteBuffer.allocate(
                content.length + FCS_LENGTH
            ).order(ByteOrder.LITTLE_ENDIAN);

            buffer.put(content);
            buffer.putInt((int) FrameChecksum.calculate(content));

            return buffer.array();
        }

        static EthernetFrame deserialize(byte[] raw) {
            Objects.requireNonNull(raw);

            if (raw.length < 64 || raw.length > 1518) {
                throw new IntegrityException(
                    "Invalid Ethernet frame length."
                );
            }

            byte[] content = Arrays.copyOf(raw, raw.length - 4);

            long expected = FrameChecksum.calculate(content);

            ByteBuffer checksumBuffer = ByteBuffer.wrap(
                raw,
                raw.length - 4,
                4
            ).order(ByteOrder.LITTLE_ENDIAN);

            long actual = Integer.toUnsignedLong(
                checksumBuffer.getInt()
            );

            if (expected != actual) {
                throw new IntegrityException("FCS verification failed.");
            }

            ByteBuffer buffer = ByteBuffer.wrap(content)
                .order(ByteOrder.BIG_ENDIAN);

            byte[] destinationBytes = new byte[6];
            byte[] sourceBytes = new byte[6];

            buffer.get(destinationBytes);
            buffer.get(sourceBytes);

            int type = Short.toUnsignedInt(buffer.getShort());

            byte[] payload = new byte[buffer.remaining()];
            buffer.get(payload);

            return new EthernetFrame(
                new MacAddress(formatMac(destinationBytes)),
                new MacAddress(formatMac(sourceBytes)),
                payload,
                type
            );
        }

        private static String formatMac(byte[] bytes) {
            StringBuilder result = new StringBuilder();

            for (byte value : bytes) {
                if (!result.isEmpty()) {
                    result.append(':');
                }

                result.append(
                    String.format("%02X", value & 0xFF)
                );
            }

            return result.toString();
        }
    }

    // ========================================================
    // 6. SWITCH POLICY AND PORT TYPES
    // ========================================================

    enum PortStatus {
        ACTIVE,
        DISABLED
    }

    enum ForwardingDecision {
        FORWARD,
        FLOOD,
        DROP
    }

    record SwitchPolicy(
        boolean allowBroadcast,
        boolean allowMulticast,
        int maximumPorts
    ) {
        SwitchPolicy {
            if (maximumPorts < 1) {
                throw new IllegalArgumentException(
                    "At least one port is required."
                );
            }
        }

        void validate(EthernetFrame frame, int portCount) {
            if (portCount > maximumPorts) {
                throw new PolicyException(
                    "Switch port capacity exceeded."
                );
            }

            if (frame.destination().isBroadcast() &&
                !allowBroadcast) {
                throw new PolicyException(
                    "Broadcast traffic prohibited."
                );
            }

            if (frame.destination().isMulticast() &&
                !frame.destination().isBroadcast() &&
                !allowMulticast) {
                throw new PolicyException(
                    "Multicast traffic prohibited."
                );
            }
        }
    }

    static final class SwitchPort {

        private final String name;
        private final MacAddress mac;
        private PortStatus status = PortStatus.ACTIVE;

        private long received;
        private long transmitted;
        private long dropped;

        SwitchPort(String name, MacAddress mac) {
            if (name == null || name.isBlank()) {
                throw new IllegalArgumentException(
                    "Port name required."
                );
            }

            this.name = name;
            this.mac = Objects.requireNonNull(mac);
        }

        void receive() {
            if (status != PortStatus.ACTIVE) {
                dropped++;
                throw new NetworkException("Port disabled: " + name);
            }

            received++;
        }

        void transmit() {
            if (status != PortStatus.ACTIVE) {
                dropped++;
                throw new NetworkException("Port disabled: " + name);
            }

            transmitted++;
        }

        void setStatus(PortStatus status) {
            this.status = Objects.requireNonNull(status);
        }

        String name() {
            return name;
        }

        PortStatus status() {
            return status;
        }
    }

    record MACLearningEntry(
        String port,
        long lastSeen
    ) {}

    record SwitchReport(
        long received,
        long forwarded,
        long flooded,
        long dropped
    ) {}

    // ========================================================
    // 7. ENTERPRISE SWITCH SERVICE
    // ========================================================

    static final class EthernetSwitchService {

        private final String name;
        private final long agingTime;
        private long clock;

        private final Map<String, SwitchPort> ports =
            new LinkedHashMap<>();

        private final Map<MacAddress, MACLearningEntry> macTable =
            new HashMap<>();

        private final SwitchPolicy policy;

        private long received;
        private long forwarded;
        private long flooded;
        private long dropped;

        EthernetSwitchService(
            String name,
            long agingTime,
            SwitchPolicy policy
        ) {
            if (agingTime <= 0) {
                throw new IllegalArgumentException(
                    "MAC aging time must be positive."
                );
            }

            this.name = Objects.requireNonNull(name);
            this.agingTime = agingTime;
            this.policy = Objects.requireNonNull(policy);
        }

        void registerPort(SwitchPort port) {
            Objects.requireNonNull(port);

            if (ports.containsKey(port.name())) {
                throw new NetworkException("Duplicate switch port.");
            }

            if (ports.size() >= policy.maximumPorts()) {
                throw new PolicyException("Port limit reached.");
            }

            ports.put(port.name(), port);
        }

        void updatePort(
            String portName,
            PortStatus status
        ) {
            SwitchPort port = ports.get(portName);

            if (port == null) {
                throw new NetworkException("Unknown port.");
            }

            port.setStatus(status);
        }

        private void expireEntries() {
            macTable.entrySet().removeIf(
                entry -> clock - entry.getValue().lastSeen() >= agingTime
            );
        }

        private void learn(
            MacAddress source,
            String incomingPort
        ) {
            if (source.isMulticast()) {
                throw new NetworkException(
                    "Cannot learn multicast source address."
                );
            }

            macTable.put(
                source,
                new MACLearningEntry(incomingPort, clock)
            );
        }

        List<String> process(
            EthernetFrame frame,
            String incomingPort
        ) {
            Objects.requireNonNull(frame);

            SwitchPort ingress = ports.get(incomingPort);

            if (ingress == null ||
                ingress.status() != PortStatus.ACTIVE) {
                dropped++;
                throw new NetworkException("Invalid ingress port.");
            }

            try {
                policy.validate(frame, ports.size());
            } catch (PolicyException exception) {
                dropped++;
                throw exception;
            }

            ingress.receive();
            received++;

            clock++;
            expireEntries();

            learn(frame.source(), incomingPort);

            if (frame.source().equals(frame.destination())) {
                return List.of();
            }

            List<String> outgoing = new ArrayList<>();

            if (frame.destination().isMulticast()) {
                for (SwitchPort port : ports.values()) {
                    if (port.status() == PortStatus.ACTIVE &&
                        !port.name().equals(incomingPort)) {
                        outgoing.add(port.name());
                    }
                }

                if (frame.destination().isBroadcast()) {
                    flooded++;
                }
            } else {
                MACLearningEntry entry =
                    macTable.get(frame.destination());

                if (entry == null) {
                    flooded++;

                    for (SwitchPort port : ports.values()) {
                        if (port.status() == PortStatus.ACTIVE &&
                            !port.name().equals(incomingPort)) {
                            outgoing.add(port.name());
                        }
                    }
                } else if (!entry.port().equals(incomingPort)) {
                    SwitchPort target = ports.get(entry.port());

                    if (target != null &&
                        target.status() == PortStatus.ACTIVE) {
                        outgoing.add(target.name());
                    }
                }
            }

            for (String portName : outgoing) {
                SwitchPort target = ports.get(portName);

                try {
                    target.transmit();
                    forwarded++;
                } catch (NetworkException exception) {
                    dropped++;
                }
            }

            return Collections.unmodifiableList(outgoing);
        }

        Map<MacAddress, MACLearningEntry> macTable() {
            return Collections.unmodifiableMap(
                new HashMap<>(macTable)
            );
        }

        SwitchReport report() {
            return new SwitchReport(
                received,
                forwarded,
                flooded,
                dropped
            );
        }

        void display() {
            System.out.println("\nSwitch: " + name);

            System.out.println("\nMAC LEARNING TABLE");

            macTable.forEach((mac, entry) ->
                System.out.printf(
                    "%-22s %-12s %d%n",
                    mac,
                    entry.port(),
                    entry.lastSeen()
                )
            );

            System.out.println("\nOPERATIONAL REPORT");
            System.out.println(report());
        }
    }

    // ========================================================
    // 8. MAIN EXECUTION
    // ========================================================

    public static void main(String[] args) {

        try {
            System.out.println("PHYSICAL LAYER");

            String bits = "10110010";

            int[] signals =
                PhysicalLayer.encodeManchester(bits);

            System.out.println("Input: " + bits);
            System.out.println("Manchester: " +
                Arrays.toString(signals));

            String decoded =
                PhysicalLayer.decodeManchester(signals);

            System.out.println("Decoded: " + decoded);

            if (!bits.equals(decoded)) {
                throw new NetworkException(
                    "Signal decoding failed."
                );
            }

            System.out.println("\nDATA LINK LAYER");

            MacAddress hostA =
                new MacAddress("00:11:22:33:44:AA");

            MacAddress hostB =
                new MacAddress("00:11:22:33:44:BB");

            MacAddress hostC =
                new MacAddress("00:11:22:33:44:CC");

            SwitchPolicy policy = new SwitchPolicy(
                true,
                true,
                24
            );

            EthernetSwitchService ethernetSwitch =
                new EthernetSwitchService(
                    "CORE-SWITCH",
                    10,
                    policy
                );

            ethernetSwitch.registerPort(
                new SwitchPort("eth0", hostA)
            );

            ethernetSwitch.registerPort(
                new SwitchPort("eth1", hostB)
            );

            ethernetSwitch.registerPort(
                new SwitchPort("eth2", hostC)
            );

            EthernetFrame request = new EthernetFrame(
                hostB,
                hostA,
                "Enterprise network request"
                    .getBytes(StandardCharsets.UTF_8),
                0x0800
            );

            byte[] serialized = request.serialize();

            EthernetFrame decodedFrame =
                EthernetFrame.deserialize(serialized);

            System.out.println(
                "Frame bytes: " + serialized.length
            );

            System.out.printf(
                "FCS: %08X%n",
                request.fcs()
            );

            System.out.println("\nUnknown unicast:");

            System.out.println(
                ethernetSwitch.process(decodedFrame, "eth0")
            );

            EthernetFrame response = new EthernetFrame(
                hostA,
                hostB,
                "Response".getBytes(StandardCharsets.UTF_8),
                0x0800
            );

            System.out.println("\nKnown unicast:");

            System.out.println(
                ethernetSwitch.process(response, "eth1")
            );

            EthernetFrame broadcast = new EthernetFrame(
                BROADCAST,
                hostA,
                "Discovery".getBytes(StandardCharsets.UTF_8),
                0x0800
            );

            System.out.println("\nBroadcast:");

            System.out.println(
                ethernetSwitch.process(broadcast, "eth0")
            );

            ethernetSwitch.display();

            System.out.println("\nERROR VALIDATION");

            byte[] corrupted = serialized.clone();
            corrupted[15] ^= 1;

            try {
                EthernetFrame.deserialize(corrupted);

                throw new NetworkException(
                    "Corrupted frame was accepted."
                );

            } catch (IntegrityException exception) {
                System.out.println(
                    "Corrupted frame rejected: " +
                    exception.getMessage()
                );
            }

            ethernetSwitch.updatePort(
                "eth2",
                PortStatus.DISABLED
            );

            System.out.println("\nPort eth2 disabled.");

            System.out.println(
                "Enterprise switch simulation completed."
            );

        } catch (NetworkException | IllegalArgumentException exception) {
            System.err.println(
                "Network processing error: " +
                exception.getMessage()
            );

            System.exit(1);
        }
    }
}
