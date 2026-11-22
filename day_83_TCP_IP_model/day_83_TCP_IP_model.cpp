#include <algorithm>
#include <array>
#include <cstdint>
#include <exception>
#include <iostream>
#include <map>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

/*
 * TCP/IP Model: C++17 Network Stack and Routing Engine
 *
 * Demonstrates:
 * - Four-layer TCP/IP architecture
 * - IPv4 addressing and subnet operations
 * - TCP and UDP transport protocols
 * - TCP connection state transitions
 * - IPv4 packet construction
 * - Internet checksum calculation
 * - Routing table management
 * - Longest-prefix matching
 * - Ethernet framing
 * - MTU and fragmentation
 * - Network policy and diagnostics
 */

class NetworkException : public std::runtime_error {
public:
    explicit NetworkException(const std::string& message)
        : std::runtime_error(message) {}
};

class ValidationException : public NetworkException {
public:
    using NetworkException::NetworkException;
};

class RoutingException : public NetworkException {
public:
    using NetworkException::NetworkException;
};

// ============================================================
// 1. TCP/IP LAYER ARCHITECTURE
// ============================================================

enum class Layer {
    Application = 4,
    Transport = 3,
    Internet = 2,
    NetworkAccess = 1
};

struct LayerInfo {
    Layer layer;
    std::string name;
    std::vector<std::string> responsibilities;
};

class Architecture {
public:
    static std::vector<LayerInfo> layers() {
        return {
            {
                Layer::Application,
                "Application",
                {"HTTP", "HTTPS", "DNS", "DHCP", "SMTP"}
            },
            {
                Layer::Transport,
                "Transport",
                {"TCP", "UDP", "Ports", "Segmentation"}
            },
            {
                Layer::Internet,
                "Internet",
                {"IPv4", "ICMP", "Routing", "Forwarding"}
            },
            {
                Layer::NetworkAccess,
                "Network Access",
                {"Ethernet", "MAC", "Framing"}
            }
        };
    }

    static void display() {
        std::cout << "\nTCP/IP FOUR-LAYER ARCHITECTURE\n";

        for (const auto& layer : layers()) {
            std::cout << "\n" << layer.name << ": ";

            for (const auto& item : layer.responsibilities) {
                std::cout << item << " ";
            }

            std::cout << "\n";
        }
    }
};

// ============================================================
// 2. IPV4 ADDRESS
// ============================================================

class IPv4Address {
private:
    uint32_t value_;

public:
    explicit IPv4Address(const std::string& address) {
        std::istringstream input(address);

        uint32_t octets[4];

        char separator1, separator2, separator3;
        std::string extra;

        if (!(input >> octets[0] >> separator1
                    >> octets[1] >> separator2
                    >> octets[2] >> separator3
                    >> octets[3]) ||
            separator1 != '.' ||
            separator2 != '.' ||
            separator3 != '.' ||
            (input >> extra)) {
            throw ValidationException("Invalid IPv4 address.");
        }

        for (uint32_t octet : octets) {
            if (octet > 255) {
                throw ValidationException(
                    "IPv4 octet exceeds 255."
                );
            }
        }

        value_ =
            (octets[0] << 24) |
            (octets[1] << 16) |
            (octets[2] << 8) |
            octets[3];
    }

    uint32_t value() const {
        return value_;
    }

    std::string toString() const {
        std::ostringstream output;

        output
            << ((value_ >> 24) & 255) << "."
            << ((value_ >> 16) & 255) << "."
            << ((value_ >> 8) & 255) << "."
            << (value_ & 255);

        return output.str();
    }

    bool operator==(const IPv4Address& other) const {
        return value_ == other.value_;
    }
};

// ============================================================
// 3. IPV4 NETWORK AND SUBNET
// ============================================================

class IPv4Network {
private:
    uint32_t network_;
    uint32_t mask_;
    int prefix_;

public:
    IPv4Network(const IPv4Address& address, int prefix)
        : prefix_(prefix) {

        if (prefix < 0 || prefix > 32) {
            throw ValidationException("Invalid subnet prefix.");
        }

        mask_ = prefix == 0
            ? 0
            : (0xFFFFFFFFu << (32 - prefix));

        network_ = address.value() & mask_;
    }

    bool contains(const IPv4Address& address) const {
        return (address.value() & mask_) == network_;
    }

    int prefix() const {
        return prefix_;
    }

    uint32_t networkValue() const {
        return network_;
    }

    IPv4Address networkAddress() const {
        return IPv4Address(toAddress(network_));
    }

    std::string toAddress(uint32_t value) const {
        return IPv4Address(
            std::to_string((value >> 24) & 255) + "." +
            std::to_string((value >> 16) & 255) + "." +
            std::to_string((value >> 8) & 255) + "." +
            std::to_string(value & 255)
        ).toString();
    }

    std::string toString() const {
        return networkAddress().toString() +
               "/" + std::to_string(prefix_);
    }
};

// ============================================================
// 4. APPLICATION LAYER
// ============================================================

enum class ApplicationProtocol {
    HTTP,
    HTTPS,
    DNS,
    DHCP
};

struct ApplicationMessage {
    ApplicationProtocol protocol;
    std::string payload;
};

std::string protocolName(ApplicationProtocol protocol) {
    switch (protocol) {
        case ApplicationProtocol::HTTP:
            return "HTTP";
        case ApplicationProtocol::HTTPS:
            return "HTTPS";
        case ApplicationProtocol::DNS:
            return "DNS";
        case ApplicationProtocol::DHCP:
            return "DHCP";
    }

    throw ValidationException("Unknown application protocol.");
}

// ============================================================
// 5. TRANSPORT LAYER
// ============================================================

enum class TCPState {
    Closed,
    SynSent,
    SynReceived,
    Established,
    FinWait,
    TimeWait
};

std::string stateName(TCPState state) {
    switch (state) {
        case TCPState::Closed:
            return "CLOSED";
        case TCPState::SynSent:
            return "SYN_SENT";
        case TCPState::SynReceived:
            return "SYN_RECEIVED";
        case TCPState::Established:
            return "ESTABLISHED";
        case TCPState::FinWait:
            return "FIN_WAIT";
        case TCPState::TimeWait:
            return "TIME_WAIT";
    }

    return "UNKNOWN";
}

class TCPConnection {
private:
    uint16_t sourcePort_;
    uint16_t destinationPort_;
    uint32_t sequence_;
    uint32_t acknowledgment_;
    TCPState state_;

    void transition(TCPState expected, TCPState next) {
        if (state_ != expected) {
            throw NetworkException("Invalid TCP state transition.");
        }

        std::cout
            << stateName(state_) << " -> "
            << stateName(next) << "\n";

        state_ = next;
    }

public:
    TCPConnection(
        uint16_t sourcePort,
        uint16_t destinationPort
    )
        : sourcePort_(sourcePort),
          destinationPort_(destinationPort),
          sequence_(1000),
          acknowledgment_(0),
          state_(TCPState::Closed) {

        if (sourcePort == 0 || destinationPort == 0) {
            throw ValidationException("Invalid TCP port.");
        }
    }

    void connect() {
        transition(TCPState::Closed, TCPState::SynSent);

        std::cout << "Client sends SYN\n";

        transition(TCPState::SynSent, TCPState::SynReceived);

        acknowledgment_ = sequence_ + 1;

        std::cout << "Server sends SYN-ACK\n";

        transition(
            TCPState::SynReceived,
            TCPState::Established
        );

        std::cout << "Client sends ACK\n";
    }

    void close() {
        transition(TCPState::Established, TCPState::FinWait);

        std::cout << "FIN and ACK exchange\n";

        transition(TCPState::FinWait, TCPState::TimeWait);

        transition(TCPState::TimeWait, TCPState::Closed);
    }

    TCPState state() const {
        return state_;
    }

    uint16_t sourcePort() const {
        return sourcePort_;
    }

    uint16_t destinationPort() const {
        return destinationPort_;
    }
};

struct UDPDatagram {
    uint16_t sourcePort;
    uint16_t destinationPort;
    std::string payload;

    void validate() const {
        if (sourcePort == 0 || destinationPort == 0) {
            throw ValidationException("Invalid UDP port.");
        }

        if (payload.size() > 65507) {
            throw ValidationException("UDP payload too large.");
        }
    }

    size_t length() const {
        return 8 + payload.size();
    }
};

// ============================================================
// 6. INTERNET LAYER
// ============================================================

struct IPv4Packet {
    IPv4Address source;
    IPv4Address destination;
    uint8_t protocol;
    uint8_t ttl;
    uint16_t identification;
    std::string payload;

    IPv4Packet(
        IPv4Address sourceAddress,
        IPv4Address destinationAddress,
        uint8_t protocolNumber,
        std::string packetPayload,
        uint8_t timeToLive = 64
    )
        : source(std::move(sourceAddress)),
          destination(std::move(destinationAddress)),
          protocol(protocolNumber),
          ttl(timeToLive),
          identification(1),
          payload(std::move(packetPayload)) {

        if (ttl == 0) {
            throw ValidationException("TTL must be positive.");
        }

        if (payload.size() + 20 > 65535) {
            throw ValidationException("IPv4 packet too large.");
        }
    }

    size_t totalLength() const {
        return 20 + payload.size();
    }

    IPv4Packet forward() const {
        if (ttl <= 1) {
            throw RoutingException("TTL expired.");
        }

        IPv4Packet forwarded(
            source,
            destination,
            protocol,
            payload,
            ttl - 1
        );

        forwarded.identification = identification;

        return forwarded;
    }

    uint16_t checksum() const {
        std::array<uint16_t, 10> header{};

        header[0] = 0x4500;
        header[1] = static_cast<uint16_t>(totalLength());
        header[2] = identification;
        header[3] = 0;
        header[4] = static_cast<uint16_t>(
            (ttl << 8) | protocol
        );
        header[5] = 0;

        const uint32_t sourceIP = source.value();
        const uint32_t destinationIP = destination.value();

        header[6] = sourceIP >> 16;
        header[7] = sourceIP & 0xFFFF;
        header[8] = destinationIP >> 16;
        header[9] = destinationIP & 0xFFFF;

        uint32_t sum = 0;

        for (uint16_t word : header) {
            sum += word;
        }

        while (sum >> 16) {
            sum = (sum & 0xFFFF) + (sum >> 16);
        }

        return static_cast<uint16_t>(~sum);
    }
};

// ============================================================
// 7. NETWORK ACCESS LAYER
// ============================================================

class EthernetFrame {
private:
    std::string sourceMAC_;
    std::string destinationMAC_;
    std::string payload_;

    static bool validMAC(const std::string& mac) {
        if (mac.size() != 17) {
            return false;
        }

        for (size_t i = 0; i < mac.size(); ++i) {
            if (i % 3 == 2) {
                if (mac[i] != ':') {
                    return false;
                }
            } else if (!std::isxdigit(
                           static_cast<unsigned char>(mac[i]))) {
                return false;
            }
        }

        return true;
    }

public:
    EthernetFrame(
        std::string source,
        std::string destination,
        std::string payload
    )
        : sourceMAC_(std::move(source)),
          destinationMAC_(std::move(destination)),
          payload_(std::move(payload)) {

        if (!validMAC(sourceMAC_) || !validMAC(destinationMAC_)) {
            throw ValidationException("Invalid MAC address.");
        }

        if (payload_.size() > 1500) {
            throw ValidationException("Ethernet MTU exceeded.");
        }
    }

    size_t frameSize() const {
        return 14 + payload_.size() + 4;
    }

    void display() const {
        std::cout
            << "Source MAC: " << sourceMAC_ << "\n"
            << "Destination MAC: " << destinationMAC_ << "\n"
            << "Frame size: " << frameSize() << " bytes\n";
    }
};

// ============================================================
// 8. ROUTING TABLE
// ============================================================

struct Route {
    IPv4Network network;
    IPv4Address nextHop;
    std::string interfaceName;
    int metric;

    Route(
        IPv4Network destinationNetwork,
        IPv4Address gateway,
        std::string interface,
        int routeMetric = 1
    )
        : network(std::move(destinationNetwork)),
          nextHop(std::move(gateway)),
          interfaceName(std::move(interface)),
          metric(routeMetric) {

        if (metric < 0) {
            throw ValidationException("Invalid route metric.");
        }
    }
};

class RoutingTable {
private:
    std::vector<Route> routes_;

public:
    void addRoute(Route route) {
        routes_.push_back(std::move(route));

        std::sort(
            routes_.begin(),
            routes_.end(),
            [](const Route& a, const Route& b) {
                if (a.network.prefix() != b.network.prefix()) {
                    return a.network.prefix() >
                           b.network.prefix();
                }

                return a.metric < b.metric;
            }
        );
    }

    const Route& lookup(const IPv4Address& destination) const {
        for (const auto& route : routes_) {
            if (route.network.contains(destination)) {
                return route;
            }
        }

        throw RoutingException("No matching route.");
    }

    IPv4Packet forward(const IPv4Packet& packet) const {
        const Route& route = lookup(packet.destination);

        std::cout
            << "Selected interface: "
            << route.interfaceName << "\n"
            << "Next hop: "
            << route.nextHop.toString() << "\n";

        return packet.forward();
    }

    size_t size() const {
        return routes_.size();
    }
};

// ============================================================
// 9. MTU AND FRAGMENTATION
// ============================================================

std::vector<size_t> calculateFragments(
    size_t packetSize,
    size_t mtu
) {
    constexpr size_t HEADER_SIZE = 20;

    if (packetSize <= HEADER_SIZE || packetSize > 65535) {
        throw ValidationException("Invalid packet size.");
    }

    if (mtu <= HEADER_SIZE) {
        throw ValidationException("Invalid MTU.");
    }

    size_t remaining = packetSize - HEADER_SIZE;

    const size_t maximumPayload =
        ((mtu - HEADER_SIZE) / 8) * 8;

    std::vector<size_t> fragments;

    while (remaining > 0) {
        const size_t fragment = std::min(
            remaining,
            maximumPayload
        );

        fragments.push_back(fragment);
        remaining -= fragment;
    }

    return fragments;
}

// ============================================================
// 10. NETWORK DIAGNOSTICS
// ============================================================

struct Diagnostic {
    std::string component;
    bool passed;
    std::string message;
};

class Diagnostics {
public:
    static Diagnostic checkTTL(uint8_t ttl) {
        return {
            "TTL",
            ttl > 0,
            ttl > 0 ? "Valid TTL" : "TTL expired"
        };
    }

    static Diagnostic checkMTU(size_t size, size_t mtu) {
        return {
            "MTU",
            size <= mtu,
            size <= mtu
                ? "Packet fits interface MTU"
                : "Packet requires fragmentation or rejection"
        };
    }
};

// ============================================================
// 11. NETWORK SIMULATION
// ============================================================

class NetworkSimulator {
public:
    void run() {
        Architecture::display();

        std::cout << "\nIP ADDRESSING\n";

        IPv4Address client("192.168.1.10");
        IPv4Address server("203.0.113.20");

        IPv4Network subnet(
            IPv4Address("192.168.1.0"),
            24
        );

        std::cout
            << "Network: " << subnet.toString() << "\n"
            << "Client belongs to network: "
            << subnet.contains(client) << "\n";

        std::cout << "\nAPPLICATION LAYER\n";

        ApplicationMessage message{
            ApplicationProtocol::HTTPS,
            "GET /api/status HTTP/1.1"
        };

        std::cout
            << "Protocol: "
            << protocolName(message.protocol) << "\n"
            << "Payload: " << message.payload << "\n";

        std::cout << "\nTRANSPORT LAYER: TCP\n";

        TCPConnection connection(50000, 443);

        connection.connect();

        std::cout
            << "TCP state: "
            << stateName(connection.state()) << "\n";

        std::cout << "\nTRANSPORT LAYER: UDP\n";

        UDPDatagram datagram{
            53000,
            53,
            "DNS query"
        };

        datagram.validate();

        std::cout
            << "UDP datagram length: "
            << datagram.length() << "\n";

        std::cout << "\nINTERNET LAYER\n";

        IPv4Packet packet(
            client,
            server,
            6,
            message.payload
        );

        std::cout
            << "Source IP: " << packet.source.toString() << "\n"
            << "Destination IP: "
            << packet.destination.toString() << "\n"
            << "Protocol number: "
            << static_cast<int>(packet.protocol) << "\n"
            << "Packet size: "
            << packet.totalLength() << "\n"
            << "Header checksum: "
            << std::hex << packet.checksum()
            << std::dec << "\n";

        std::cout << "\nNETWORK ACCESS LAYER\n";

        EthernetFrame frame(
            "02:00:00:00:00:01",
            "02:00:00:00:00:02",
            packet.payload
        );

        frame.display();

        std::cout << "\nROUTING\n";

        RoutingTable routing;

        routing.addRoute(
            Route(
                IPv4Network(
                    IPv4Address("203.0.113.0"),
                    24
                ),
                IPv4Address("192.168.1.1"),
                "eth0"
            )
        );

        routing.addRoute(
            Route(
                IPv4Network(
                    IPv4Address("0.0.0.0"),
                    0
                ),
                IPv4Address("192.168.1.254"),
                "eth1",
                10
            )
        );

        IPv4Packet forwarded = routing.forward(packet);

        std::cout
            << "Original TTL: "
            << static_cast<int>(packet.ttl) << "\n"
            << "Forwarded TTL: "
            << static_cast<int>(forwarded.ttl) << "\n";

        std::cout << "\nFRAGMENTATION\n";

        const auto fragments = calculateFragments(4000, 1500);

        for (size_t i = 0; i < fragments.size(); ++i) {
            std::cout
                << "Fragment " << i + 1
                << ": " << fragments[i]
                << " payload bytes\n";
        }

        std::cout << "\nDIAGNOSTICS\n";

        const auto ttlCheck = Diagnostics::checkTTL(64);
        const auto mtuCheck = Diagnostics::checkMTU(4000, 1500);

        std::cout
            << ttlCheck.component << ": "
            << ttlCheck.message << "\n"
            << mtuCheck.component << ": "
            << mtuCheck.message << "\n";

        std::cout << "\nTCP TERMINATION\n";

        connection.close();

        std::cout
            << "Final TCP state: "
            << stateName(connection.state()) << "\n";
    }
};

// ============================================================
// 12. VALIDATION TESTS
// ============================================================

void runTests() {
    IPv4Address address("192.168.1.10");

    IPv4Network network(
        IPv4Address("192.168.1.0"),
        24
    );

    if (!network.contains(address)) {
        throw std::runtime_error("Subnet test failed.");
    }

    const auto fragments = calculateFragments(4000, 1500);

    if (fragments != std::vector<size_t>{1480, 1480, 1020}) {
        throw std::runtime_error("Fragmentation test failed.");
    }

    IPv4Packet packet(
        IPv4Address("192.168.1.10"),
        IPv4Address("203.0.113.20"),
        6,
        "test"
    );

    if (packet.forward().ttl != 63) {
        throw std::runtime_error("TTL test failed.");
    }

    TCPConnection connection(40000, 443);

    connection.connect();

    if (connection.state() != TCPState::Established) {
        throw std::runtime_error("TCP handshake test failed.");
    }

    connection.close();

    if (connection.state() != TCPState::Closed) {
        throw std::runtime_error("TCP termination test failed.");
    }

    std::cout << "\nAll C++17 tests passed.\n";
}

// ============================================================
// 13. MAIN
// ============================================================

int main() {
    try {
        NetworkSimulator simulator;

        simulator.run();

        runTests();

    } catch (const std::exception& error) {
        std::cerr
            << "Network failure: "
            << error.what() << "\n";

        return 1;
    }

    return 0;
}
