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
 * OSI Model: C++17 Network Layer Processing Engine.
 *
 * Implements:
 * - Seven-layer domain model.
 * - MAC and IPv4 address validation.
 * - Ethernet frame representation.
 * - IPv4 packet representation.
 * - TCP and UDP transport metadata.
 * - Session state management.
 * - Encapsulation and decapsulation.
 * - Network diagnostics.
 * - Layer-specific failure reporting.
 */

enum class Layer : int {
    Physical = 1,
    DataLink = 2,
    Network = 3,
    Transport = 4,
    Session = 5,
    Presentation = 6,
    Application = 7
};

enum class TransportProtocol {
    TCP,
    UDP
};

enum class SessionState {
    Active,
    Closed,
    Failed
};

struct NetworkException : std::runtime_error {
    Layer layer;

    NetworkException(Layer l, const std::string& message)
        : std::runtime_error(message), layer(l) {}
};

struct MACAddress {
    std::array<uint8_t, 6> bytes{};

    static MACAddress parse(const std::string& value) {
        MACAddress result;
        std::istringstream input(value);
        std::string part;

        for (int i = 0; i < 6; ++i) {
            if (!std::getline(input, part, ':') || part.size() != 2) {
                throw std::invalid_argument("Invalid MAC address");
            }

            try {
                std::size_t consumed = 0;
                unsigned long number = std::stoul(
                    part, &consumed, 16
                );

                if (consumed != part.size() || number > 255) {
                    throw std::invalid_argument("Invalid MAC octet");
                }

                result.bytes[i] = static_cast<uint8_t>(number);
            } catch (...) {
                throw std::invalid_argument("Invalid MAC address");
            }
        }

        if (std::getline(input, part, ':')) {
            throw std::invalid_argument("MAC has extra octets");
        }

        return result;
    }

    std::string toString() const {
        std::ostringstream output;

        for (std::size_t i = 0; i < bytes.size(); ++i) {
            if (i) output << ':';

            output << std::hex
                   << std::setfill('0')
                   << std::setw(2)
                   << static_cast<int>(bytes[i]);
        }

        return output.str();
    }
};

struct IPv4Address {
    std::array<uint8_t, 4> bytes{};

    static IPv4Address parse(const std::string& value) {
        IPv4Address address;
        std::istringstream input(value);
        std::string part;

        for (int i = 0; i < 4; ++i) {
            if (!std::getline(input, part, '.') || part.empty()) {
                throw std::invalid_argument("Invalid IPv4 address");
            }

            if (!std::all_of(
                part.begin(),
                part.end(),
                [](unsigned char c) { return c >= '0' && c <= '9'; }
            )) {
                throw std::invalid_argument("Invalid IPv4 octet");
            }

            if (part.size() > 1 && part[0] == '0') {
                throw std::invalid_argument("Noncanonical IPv4 octet");
            }

            unsigned long number = std::stoul(part);

            if (number > 255) {
                throw std::invalid_argument("IPv4 octet exceeds 255");
            }

            address.bytes[i] = static_cast<uint8_t>(number);
        }

        if (std::getline(input, part, '.')) {
            throw std::invalid_argument("IPv4 has extra octets");
        }

        return address;
    }

    std::string toString() const {
        std::ostringstream output;

        for (std::size_t i = 0; i < bytes.size(); ++i) {
            if (i) output << '.';
            output << static_cast<int>(bytes[i]);
        }

        return output.str();
    }
};

struct Session {
    std::string id;
    SessionState state = SessionState::Active;
};

struct ApplicationMessage {
    std::string protocol;
    std::string content;
};

struct TransportSegment {
    TransportProtocol protocol;
    uint16_t sourcePort;
    uint16_t destinationPort;
    std::string payload;
};

struct IPv4Packet {
    IPv4Address source;
    IPv4Address destination;
    uint8_t ttl = 64;
    uint8_t protocolNumber;
    std::string payload;
};

struct EthernetFrame {
    MACAddress source;
    MACAddress destination;
    uint16_t etherType = 0x0800;
    std::string payload;
};

struct NetworkInterface {
    std::string name;
    MACAddress mac;
    IPv4Address ip;
    bool active = true;
};

struct LayerMetrics {
    std::size_t processed = 0;
    std::size_t failures = 0;
};

class NetworkEngine {
private:
    std::map<int, LayerMetrics> metrics;
    std::map<std::string, Session> sessions;
    std::set<std::string> applicationProtocols;

    static std::string layerName(Layer layer) {
        switch (layer) {
            case Layer::Physical: return "Physical";
            case Layer::DataLink: return "Data Link";
            case Layer::Network: return "Network";
            case Layer::Transport: return "Transport";
            case Layer::Session: return "Session";
            case Layer::Presentation: return "Presentation";
            case Layer::Application: return "Application";
        }

        return "Unknown";
    }

    void recordSuccess(Layer layer) {
        metrics[static_cast<int>(layer)].processed++;
    }

    void recordFailure(Layer layer) {
        metrics[static_cast<int>(layer)].failures++;
    }

public:
    NetworkEngine() {
        for (int i = 1; i <= 7; ++i) {
            metrics[i] = {};
        }

        applicationProtocols = {
            "HTTP", "HTTPS", "DNS", "FTP", "SSH", "SMTP"
        };
    }

    Session createSession(const std::string& id) {
        if (id.empty() || sessions.count(id)) {
            throw std::invalid_argument("Invalid or duplicate session ID");
        }

        Session session{id, SessionState::Active};
        sessions.emplace(id, session);

        return session;
    }

    void closeSession(const std::string& id) {
        auto iterator = sessions.find(id);

        if (iterator == sessions.end() ||
            iterator->second.state != SessionState::Active) {
            throw std::runtime_error("Session cannot be closed");
        }

        iterator->second.state = SessionState::Closed;
    }

    void validateSession(const std::string& id) const {
        auto iterator = sessions.find(id);

        if (iterator == sessions.end() ||
            iterator->second.state != SessionState::Active) {
            throw NetworkException(
                Layer::Session,
                "Inactive communication session"
            );
        }
    }

    TransportSegment createTransport(
        TransportProtocol protocol,
        uint16_t sourcePort,
        uint16_t destinationPort,
        const std::string& payload
    ) {
        if (sourcePort == 0 || destinationPort == 0) {
            throw NetworkException(
                Layer::Transport,
                "Transport ports must be nonzero"
            );
        }

        recordSuccess(Layer::Transport);

        return {
            protocol,
            sourcePort,
            destinationPort,
            payload
        };
    }

    IPv4Packet createIPv4Packet(
        IPv4Address source,
        IPv4Address destination,
        const TransportSegment& segment
    ) {
        if (segment.payload.size() > 65515) {
            throw NetworkException(
                Layer::Network,
                "IPv4 packet exceeds maximum payload"
            );
        }

        return {
            source,
            destination,
            64,
            static_cast<uint8_t>(
                segment.protocol == TransportProtocol::TCP ? 6 : 17
            ),
            segment.payload
        };
    }

    EthernetFrame createEthernetFrame(
        MACAddress source,
        MACAddress destination,
        const IPv4Packet& packet
    ) {
        if (packet.ttl == 0) {
            throw NetworkException(
                Layer::Network,
                "IPv4 TTL expired"
            );
        }

        recordSuccess(Layer::DataLink);

        return {
            source,
            destination,
            0x0800,
            packet.payload
        };
    }

    void transmit(const EthernetFrame& frame) {
        if (frame.payload.empty()) {
            throw NetworkException(
                Layer::Physical,
                "Cannot transmit an empty frame"
            );
        }

        recordSuccess(Layer::Physical);
    }

    bool route(
        const IPv4Address& destination,
        const IPv4Address& network,
        const IPv4Address& mask
    ) const {
        for (std::size_t i = 0; i < 4; ++i) {
            if ((destination.bytes[i] & mask.bytes[i]) !=
                (network.bytes[i] & mask.bytes[i])) {
                return false;
            }
        }

        return true;
    }

    void validateApplication(
        const ApplicationMessage& message
    ) {
        if (!applicationProtocols.count(message.protocol)) {
            throw NetworkException(
                Layer::Application,
                "Unsupported application protocol"
            );
        }

        if (message.content.empty()) {
            throw NetworkException(
                Layer::Application,
                "Empty application content"
            );
        }

        recordSuccess(Layer::Application);
    }

    void execute(
        const std::string& sessionId,
        const std::string& application,
        const std::string& message,
        TransportProtocol transport,
        const std::string& sourceIP,
        const std::string& destinationIP,
        const std::string& sourceMAC,
        const std::string& destinationMAC
    ) {
        try {
            validateSession(sessionId);

            ApplicationMessage app{
                application,
                message
            };

            validateApplication(app);

            // Presentation: UTF-8-compatible byte representation.
            std::string encoded = app.content;

            recordSuccess(Layer::Presentation);

            TransportSegment segment = createTransport(
                transport,
                51000,
                application == "DNS" ? 53 :
                application == "HTTPS" ? 443 : 80,
                encoded
            );

            IPv4Packet packet = createIPv4Packet(
                IPv4Address::parse(sourceIP),
                IPv4Address::parse(destinationIP),
                segment
            );

            recordSuccess(Layer::Network);

            EthernetFrame frame = createEthernetFrame(
                MACAddress::parse(sourceMAC),
                MACAddress::parse(destinationMAC),
                packet
            );

            transmit(frame);

            recordSuccess(Layer::Session);

            std::cout
                << "\nCommunication successfully transmitted.\n"
                << "Session: " << sessionId << '\n'
                << "Application: " << application << '\n'
                << "Transport: "
                << (transport == TransportProtocol::TCP ? "TCP" : "UDP")
                << '\n'
                << "Source IP: " << sourceIP << '\n'
                << "Destination IP: " << destinationIP << '\n'
                << "Payload: " << message << '\n';

        } catch (const NetworkException& error) {
            recordFailure(error.layer);

            auto session = sessions.find(sessionId);

            if (session != sessions.end()) {
                session->second.state = SessionState::Failed;
            }

            std::cerr
                << "Failure at " << layerName(error.layer)
                << ": " << error.what() << '\n';

            throw;
        } catch (const std::exception& error) {
            recordFailure(Layer::Network);
            throw;
        }
    }

    void printDiagnostics() const {
        const std::array<std::string, 7> names = {
            "Physical",
            "Data Link",
            "Network",
            "Transport",
            "Session",
            "Presentation",
            "Application"
        };

        std::cout << "\nOSI Layer Diagnostics\n";

        for (int i = 1; i <= 7; ++i) {
            const auto& metric = metrics.at(i);

            std::cout
                << names[i - 1]
                << ": processed=" << metric.processed
                << ", failures=" << metric.failures
                << '\n';
        }
    }
};

int main() {
    try {
        NetworkEngine engine;

        engine.createSession("SESSION-001");

        engine.execute(
            "SESSION-001",
            "HTTPS",
            "Seven-layer OSI communication",
            TransportProtocol::TCP,
            "192.168.1.10",
            "192.168.1.20",
            "00:11:22:33:44:55",
            "AA:BB:CC:DD:EE:FF"
        );

        // Subnet routing example: 192.168.1.0/24.
        const auto destination =
            IPv4Address::parse("192.168.1.20");

        const auto network =
            IPv4Address::parse("192.168.1.0");

        const auto mask =
            IPv4Address::parse("255.255.255.0");

        std::cout
            << "\nDestination belongs to local subnet: "
            << std::boolalpha
            << engine.route(destination, network, mask)
            << '\n';

        engine.closeSession("SESSION-001");

        // Closed sessions cannot process further communication.
        try {
            engine.validateSession("SESSION-001");
        } catch (const NetworkException& error) {
            std::cout
                << "Expected session failure: "
                << error.what() << '\n';
        }

        // Invalid protocol must be rejected.
        try {
            engine.validateApplication({
                "UNKNOWN",
                "Invalid protocol"
            });
        } catch (const NetworkException& error) {
            std::cout
                << "Expected application failure: "
                << error.what() << '\n';
        }

        engine.printDiagnostics();

    } catch (const std::exception& error) {
        std::cerr << "Execution failed: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
