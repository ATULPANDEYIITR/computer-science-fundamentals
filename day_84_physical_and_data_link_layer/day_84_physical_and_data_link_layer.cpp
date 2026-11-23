#include <algorithm>
#include <array>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * Physical and Data Link Layer
 *
 * C++17 Ethernet switching and repository-independent
 * network governance simulation.
 *
 * Features:
 * - NRZ and Manchester encoding
 * - MAC address representation
 * - Ethernet frame modeling
 * - CRC-32/FCS verification
 * - MAC address learning
 * - Unknown unicast flooding
 * - Broadcast and multicast forwarding
 * - Port-state management
 * - MAC table aging
 * - Forwarding statistics
 */

using Byte = std::uint8_t;
using Bytes = std::vector<Byte>;

// ============================================================
// 1. NETWORK EXCEPTIONS
// ============================================================

class NetworkException : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

// ============================================================
// 2. MAC ADDRESS
// ============================================================

class MACAddress {
private:
    std::array<Byte, 6> address{};

public:
    explicit MACAddress(const std::string& input) {
        std::istringstream stream(input);
        std::string part;

        for (int i = 0; i < 6; ++i) {
            if (!std::getline(stream, part, ':') || part.size() != 2) {
                throw NetworkException("Invalid MAC address.");
            }

            try {
                std::size_t position = 0;
                unsigned long value = std::stoul(part, &position, 16);

                if (position != 2 || value > 255) {
                    throw NetworkException("Invalid MAC octet.");
                }

                address[i] = static_cast<Byte>(value);
            } catch (const std::exception&) {
                throw NetworkException("Invalid hexadecimal MAC address.");
            }
        }

        if (std::getline(stream, part, ':')) {
            throw NetworkException("MAC address has extra octets.");
        }
    }

    explicit MACAddress(std::array<Byte, 6> value)
        : address(value) {}

    const std::array<Byte, 6>& bytes() const {
        return address;
    }

    bool isMulticast() const {
        return (address[0] & 1) != 0;
    }

    bool isBroadcast() const {
        return std::all_of(
            address.begin(),
            address.end(),
            [](Byte value) { return value == 0xFF; }
        );
    }

    bool operator<(const MACAddress& other) const {
        return address < other.address;
    }

    bool operator==(const MACAddress& other) const {
        return address == other.address;
    }

    std::string toString() const {
        std::ostringstream output;

        output << std::uppercase << std::hex << std::setfill('0');

        for (std::size_t i = 0; i < address.size(); ++i) {
            if (i) output << ':';

            output << std::setw(2)
                   << static_cast<int>(address[i]);
        }

        return output.str();
    }
};

const MACAddress BROADCAST({
    0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF
});

// ============================================================
// 3. PHYSICAL LAYER ENCODING
// ============================================================

class PhysicalLayer {
public:
    static void validateBits(const std::string& bits) {
        if (bits.empty() ||
            !std::all_of(bits.begin(), bits.end(),
                [](char bit) {
                    return bit == '0' || bit == '1';
                })) {
            throw NetworkException("Invalid binary sequence.");
        }
    }

    static std::vector<int> encodeNRZ(const std::string& bits) {
        validateBits(bits);

        std::vector<int> signals;

        for (char bit : bits) {
            signals.push_back(bit - '0');
        }

        return signals;
    }

    static std::string decodeNRZ(const std::vector<int>& signals) {
        if (signals.empty()) {
            throw NetworkException("Empty signal.");
        }

        std::string bits;

        for (int signal : signals) {
            if (signal != 0 && signal != 1) {
                throw NetworkException("Invalid NRZ level.");
            }

            bits += static_cast<char>('0' + signal);
        }

        return bits;
    }

    static std::vector<int> encodeManchester(
        const std::string& bits
    ) {
        validateBits(bits);

        std::vector<int> signals;

        for (char bit : bits) {
            if (bit == '0') {
                signals.push_back(0);
                signals.push_back(1);
            } else {
                signals.push_back(1);
                signals.push_back(0);
            }
        }

        return signals;
    }

    static std::string decodeManchester(
        const std::vector<int>& signals
    ) {
        if (signals.empty() || signals.size() % 2 != 0) {
            throw NetworkException("Invalid Manchester signal length.");
        }

        std::string bits;

        for (std::size_t i = 0; i < signals.size(); i += 2) {
            if (signals[i] == 0 && signals[i + 1] == 1) {
                bits += '0';
            } else if (signals[i] == 1 && signals[i + 1] == 0) {
                bits += '1';
            } else {
                throw NetworkException("Invalid Manchester transition.");
            }
        }

        return bits;
    }
};

// ============================================================
// 4. CRC-32
// ============================================================

class CRC32 {
public:
    static std::uint32_t calculate(const Bytes& data) {
        std::uint32_t crc = 0xFFFFFFFF;

        for (Byte byte : data) {
            crc ^= byte;

            for (int i = 0; i < 8; ++i) {
                if (crc & 1) {
                    crc = (crc >> 1) ^ 0xEDB88320;
                } else {
                    crc >>= 1;
                }
            }
        }

        return crc ^ 0xFFFFFFFF;
    }
};

// ============================================================
// 5. ETHERNET FRAME
// ============================================================

struct EthernetFrame {
    static constexpr std::size_t MIN_PAYLOAD = 46;
    static constexpr std::size_t MAX_PAYLOAD = 1500;

    MACAddress destination;
    MACAddress source;
    std::uint16_t etherType;
    Bytes payload;

    EthernetFrame(
        MACAddress destinationAddress,
        MACAddress sourceAddress,
        Bytes data,
        std::uint16_t type = 0x0800
    )
        : destination(destinationAddress),
          source(sourceAddress),
          etherType(type),
          payload(std::move(data)) {

        if (source.isMulticast()) {
            throw NetworkException("Source MAC must be unicast.");
        }

        if (source == destination) {
            throw NetworkException("Source and destination cannot match.");
        }

        if (payload.size() > MAX_PAYLOAD) {
            throw NetworkException("Payload exceeds Ethernet MTU.");
        }
    }

    Bytes serializeWithoutFCS() const {
        Bytes result;

        result.insert(
            result.end(),
            destination.bytes().begin(),
            destination.bytes().end()
        );

        result.insert(
            result.end(),
            source.bytes().begin(),
            source.bytes().end()
        );

        result.push_back(static_cast<Byte>(etherType >> 8));
        result.push_back(static_cast<Byte>(etherType & 0xFF));

        result.insert(
            result.end(),
            payload.begin(),
            payload.end()
        );

        result.resize(14 + std::max(payload.size(), MIN_PAYLOAD), 0);

        return result;
    }

    std::uint32_t calculateFCS() const {
        return CRC32::calculate(serializeWithoutFCS());
    }

    Bytes serialize() const {
        Bytes result = serializeWithoutFCS();

        std::uint32_t fcs = CRC32::calculate(result);

        // Ethernet transmits the FCS least-significant byte first.
        for (int i = 0; i < 4; ++i) {
            result.push_back(
                static_cast<Byte>((fcs >> (8 * i)) & 0xFF)
            );
        }

        return result;
    }

    static void verify(const Bytes& raw) {
        if (raw.size() < 64 || raw.size() > 1518) {
            throw NetworkException("Invalid Ethernet frame size.");
        }

        Bytes content(raw.begin(), raw.end() - 4);

        std::uint32_t received =
            static_cast<std::uint32_t>(raw[raw.size() - 4]) |
            (static_cast<std::uint32_t>(raw[raw.size() - 3]) << 8) |
            (static_cast<std::uint32_t>(raw[raw.size() - 2]) << 16) |
            (static_cast<std::uint32_t>(raw[raw.size() - 1]) << 24);

        if (CRC32::calculate(content) != received) {
            throw NetworkException("Ethernet FCS verification failed.");
        }
    }
};

// ============================================================
// 6. SWITCH DOMAIN MODEL
// ============================================================

enum class PortState {
    ACTIVE,
    DISABLED
};

struct SwitchPort {
    std::string name;
    MACAddress mac;
    PortState state = PortState::ACTIVE;
    std::uint64_t received = 0;
    std::uint64_t transmitted = 0;
    std::uint64_t dropped = 0;
};

struct MACEntry {
    std::string port;
    std::uint64_t lastSeen;
};

struct SwitchStatistics {
    std::uint64_t received = 0;
    std::uint64_t forwarded = 0;
    std::uint64_t flooded = 0;
    std::uint64_t dropped = 0;
};

// ============================================================
// 7. ETHERNET SWITCHING ENGINE
// ============================================================

class EthernetSwitch {
private:
    std::string name;
    std::uint64_t agingTime;
    std::uint64_t clock = 0;

    std::map<std::string, SwitchPort> ports;
    std::map<MACAddress, MACEntry> macTable;

    SwitchStatistics statistics;

    void expireEntries() {
        for (auto iterator = macTable.begin();
             iterator != macTable.end();) {

            if (clock - iterator->second.lastSeen >= agingTime) {
                iterator = macTable.erase(iterator);
            } else {
                ++iterator;
            }
        }
    }

    void learn(const MACAddress& source, const std::string& port) {
        if (source.isMulticast()) {
            throw NetworkException("Cannot learn multicast source.");
        }

        macTable[source] = {port, clock};
    }

public:
    explicit EthernetSwitch(
        std::string switchName,
        std::uint64_t aging = 300
    )
        : name(std::move(switchName)),
          agingTime(aging) {

        if (agingTime == 0) {
            throw NetworkException("Invalid MAC aging interval.");
        }
    }

    void addPort(const std::string& portName, MACAddress mac) {
        if (ports.count(portName)) {
            throw NetworkException("Duplicate switch port.");
        }

        ports.emplace(
            portName,
            SwitchPort{portName, mac}
        );
    }

    void setPortState(
        const std::string& portName,
        PortState state
    ) {
        auto iterator = ports.find(portName);

        if (iterator == ports.end()) {
            throw NetworkException("Unknown port.");
        }

        iterator->second.state = state;
    }

    std::vector<std::string> receive(
        const EthernetFrame& frame,
        const std::string& incomingPort
    ) {
        auto ingress = ports.find(incomingPort);

        if (ingress == ports.end() ||
            ingress->second.state != PortState::ACTIVE) {
            statistics.dropped++;
            throw NetworkException("Ingress port unavailable.");
        }

        ingress->second.received++;
        statistics.received++;

        clock++;
        expireEntries();

        learn(frame.source, incomingPort);

        std::vector<std::string> destinations;

        if (frame.source == frame.destination) {
            return destinations;
        }

        if (frame.destination.isMulticast()) {
            for (const auto& [name, port] : ports) {
                if (name != incomingPort &&
                    port.state == PortState::ACTIVE) {
                    destinations.push_back(name);
                }
            }
        } else {
            auto destination = macTable.find(frame.destination);

            if (destination == macTable.end()) {
                // Unknown unicast: flood all active ports except ingress.
                statistics.flooded++;

                for (const auto& [name, port] : ports) {
                    if (name != incomingPort &&
                        port.state == PortState::ACTIVE) {
                        destinations.push_back(name);
                    }
                }
            } else if (destination->second.port != incomingPort) {
                auto target = ports.find(destination->second.port);

                if (target != ports.end() &&
                    target->second.state == PortState::ACTIVE) {
                    destinations.push_back(destination->second.port);
                }
            }
        }

        for (const auto& destination : destinations) {
            auto& port = ports.at(destination);
            port.transmitted++;
            statistics.forwarded++;
        }

        return destinations;
    }

    void displayMACTable() const {
        std::cout << "\nMAC ADDRESS TABLE: " << name << "\n";

        std::cout << std::left
                  << std::setw(22) << "MAC ADDRESS"
                  << std::setw(15) << "PORT"
                  << "LAST SEEN\n";

        for (const auto& [mac, entry] : macTable) {
            std::cout << std::setw(22) << mac.toString()
                      << std::setw(15) << entry.port
                      << entry.lastSeen << '\n';
        }
    }

    void displayStatistics() const {
        std::cout << "\nSWITCH STATISTICS\n"
                  << "Received: " << statistics.received << '\n'
                  << "Forwarded: " << statistics.forwarded << '\n'
                  << "Flooded: " << statistics.flooded << '\n'
                  << "Dropped: " << statistics.dropped << '\n';
    }
};

// ============================================================
// 8. EXECUTION AND TESTING
// ============================================================

int main() {
    try {
        std::cout << "PHYSICAL LAYER\n";

        const std::string bits = "10110010";

        auto encoded = PhysicalLayer::encodeManchester(bits);

        std::cout << "Original bits: " << bits << "\nEncoded: ";

        for (int signal : encoded) {
            std::cout << signal;
        }

        std::cout << "\nDecoded: "
                  << PhysicalLayer::decodeManchester(encoded)
                  << "\n";

        if (PhysicalLayer::decodeManchester(encoded) != bits) {
            throw NetworkException("Manchester round-trip failed.");
        }

        std::cout << "\nDATA LINK LAYER\n";

        MACAddress hostA("00:11:22:33:44:AA");
        MACAddress hostB("00:11:22:33:44:BB");
        MACAddress hostC("00:11:22:33:44:CC");

        EthernetFrame frame(
            hostB,
            hostA,
            Bytes{'H', 'e', 'l', 'l', 'o'}
        );

        Bytes serialized = frame.serialize();

        EthernetFrame::verify(serialized);

        std::cout << "Ethernet frame bytes: "
                  << serialized.size() << '\n';

        std::cout << "FCS: 0x"
                  << std::hex << frame.calculateFCS()
                  << std::dec << '\n';

        EthernetSwitch networkSwitch("SW-CORE", 10);

        networkSwitch.addPort("eth0", hostA);
        networkSwitch.addPort("eth1", hostB);
        networkSwitch.addPort("eth2", hostC);

        std::cout << "\nUnknown unicast forwarding:\n";

        auto first = networkSwitch.receive(frame, "eth0");

        for (const auto& port : first) {
            std::cout << "Flooded to: " << port << '\n';
        }

        EthernetFrame response(
            hostA,
            hostB,
            Bytes{'O', 'K'}
        );

        std::cout << "\nKnown unicast forwarding:\n";

        auto second = networkSwitch.receive(response, "eth1");

        for (const auto& port : second) {
            std::cout << "Forwarded to: " << port << '\n';
        }

        EthernetFrame broadcast(
            BROADCAST,
            hostA,
            Bytes{'D', 'I', 'S', 'C'}
        );

        std::cout << "\nBroadcast forwarding:\n";

        auto third = networkSwitch.receive(broadcast, "eth0");

        for (const auto& port : third) {
            std::cout << "Broadcast to: " << port << '\n';
        }

        networkSwitch.displayMACTable();
        networkSwitch.displayStatistics();

        std::cout << "\nCORRUPTION TEST\n";

        serialized[15] ^= 0x01;

        try {
            EthernetFrame::verify(serialized);
            throw NetworkException("Corrupted frame was accepted.");
        } catch (const NetworkException& error) {
            std::cout << "Rejected: " << error.what() << '\n';
        }

        std::cout << "\nAll network operations completed.\n";

    } catch (const std::exception& error) {
        std::cerr << "Network error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
