#include <algorithm>
#include <cstdint>
#include <exception>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <memory>
#include <queue>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace std;

// ============================================================
// INTRODUCTION TO COMPUTER NETWORKS
// C++17 packet switching and routing engine
// ============================================================

// ============================================================
// 1. NETWORK MODELS
// ============================================================

enum class OSILayer {
    Physical = 1,
    DataLink,
    Network,
    Transport,
    Session,
    Presentation,
    Application
};

enum class DeviceType {
    Host,
    Switch,
    Router
};

enum class NetworkType {
    LAN,
    WAN
};

enum class Protocol {
    TCP,
    UDP,
    ICMP
};

string toString(DeviceType type) {
    switch (type) {
        case DeviceType::Host: return "HOST";
        case DeviceType::Switch: return "SWITCH";
        case DeviceType::Router: return "ROUTER";
    }
    return "UNKNOWN";
}

string toString(NetworkType type) {
    return type == NetworkType::LAN ? "LAN" : "WAN";
}

// ============================================================
// 2. IPV4 ADDRESS IMPLEMENTATION
// ============================================================

class IPv4 {
private:
    uint32_t value_;

public:
    explicit IPv4(const string& address) {
        stringstream stream(address);
        string part;
        uint32_t result = 0;
        int count = 0;

        while (getline(stream, part, '.')) {
            if (part.empty() || part.size() > 3) {
                throw invalid_argument("Invalid IPv4 address");
            }

            if (!all_of(part.begin(), part.end(), ::isdigit)) {
                throw invalid_argument("Invalid IPv4 octet");
            }

            int octet = stoi(part);

            if (octet < 0 || octet > 255) {
                throw out_of_range("IPv4 octet outside range");
            }

            result = (result << 8) | static_cast<uint32_t>(octet);
            count++;
        }

        if (count != 4) {
            throw invalid_argument("IPv4 requires four octets");
        }

        value_ = result;
    }

    explicit IPv4(uint32_t value) : value_(value) {}

    uint32_t value() const {
        return value_;
    }

    string toString() const {
        return to_string((value_ >> 24) & 255) + "." +
               to_string((value_ >> 16) & 255) + "." +
               to_string((value_ >> 8) & 255) + "." +
               to_string(value_ & 255);
    }
};

// ============================================================
// 3. SUBNET IMPLEMENTATION
// ============================================================

class Subnet {
private:
    IPv4 network_;
    int prefix_;
    uint32_t mask_;

public:
    Subnet(const string& address, int prefix)
        : network_(address), prefix_(prefix), mask_(0) {

        if (prefix < 0 || prefix > 32) {
            throw invalid_argument("Invalid subnet prefix");
        }

        mask_ = prefix == 0
            ? 0
            : (0xFFFFFFFFu << (32 - prefix));

        network_ = IPv4(network_.value() & mask_);
    }

    bool contains(const IPv4& address) const {
        return (address.value() & mask_) == network_.value();
    }

    int prefix() const {
        return prefix_;
    }

    string networkAddress() const {
        return network_.toString();
    }

    string maskAddress() const {
        return IPv4(mask_).toString();
    }

    uint64_t totalAddresses() const {
        return uint64_t{1} << (32 - prefix_);
    }
};

// ============================================================
// 4. NETWORK INTERFACES AND DEVICES
// ============================================================

struct NetworkInterface {
    string name;
    IPv4 address;
    Subnet subnet;
    string macAddress;

    NetworkInterface(
        string interfaceName,
        const string& ip,
        const string& cidrAddress,
        int prefix,
        string mac
    )
        : name(move(interfaceName)),
          address(ip),
          subnet(cidrAddress, prefix),
          macAddress(move(mac)) {

        if (!subnet.contains(address)) {
            throw invalid_argument("IP is outside interface subnet");
        }

        if (macAddress.size() != 17) {
            throw invalid_argument("Invalid MAC address length");
        }

        for (size_t i = 0; i < macAddress.size(); ++i) {
            if (i % 3 == 2) {
                if (macAddress[i] != ':') {
                    throw invalid_argument("Invalid MAC separator");
                }
            } else if (!isxdigit(
                           static_cast<unsigned char>(macAddress[i]))) {
                throw invalid_argument("Invalid MAC character");
            }
        }
    }
};

struct NetworkDevice {
    string id;
    string name;
    DeviceType type;
    vector<NetworkInterface> interfaces;

    NetworkDevice(
        string deviceId,
        string deviceName,
        DeviceType deviceType
    )
        : id(move(deviceId)),
          name(move(deviceName)),
          type(deviceType) {}

    void addInterface(NetworkInterface interface) {
        auto duplicate = find_if(
            interfaces.begin(),
            interfaces.end(),
            [&](const NetworkInterface& existing) {
                return existing.name == interface.name;
            }
        );

        if (duplicate != interfaces.end()) {
            throw invalid_argument("Duplicate interface name");
        }

        interfaces.push_back(move(interface));
    }
};

// ============================================================
// 5. PACKET DOMAIN
// ============================================================

struct Packet {
    int id;
    IPv4 source;
    IPv4 destination;
    Protocol protocol;
    string payload;
    int ttl;
    int sourcePort;
    int destinationPort;
    vector<string> hops;

    Packet(
        int packetId,
        const string& sourceIP,
        const string& destinationIP,
        Protocol packetProtocol,
        string packetPayload,
        int initialTTL = 64,
        int sourcePortValue = 0,
        int destinationPortValue = 0
    )
        : id(packetId),
          source(sourceIP),
          destination(destinationIP),
          protocol(packetProtocol),
          payload(move(packetPayload)),
          ttl(initialTTL),
          sourcePort(sourcePortValue),
          destinationPort(destinationPortValue) {

        if (ttl < 1 || ttl > 255) {
            throw invalid_argument("Invalid packet TTL");
        }

        if (payload.size() > 65507) {
            throw length_error("Packet payload too large");
        }

        for (int port : {sourcePort, destinationPort}) {
            if (port < 0 || port > 65535) {
                throw invalid_argument("Invalid transport port");
            }
        }
    }

    size_t sizeBytes() const {
        return 20 +
               (protocol == Protocol::TCP ? 20 : 8) +
               payload.size();
    }
};

// ============================================================
// 6. NETWORK LINKS
// ============================================================

struct Link {
    string source;
    string destination;
    NetworkType type;
    double bandwidthMbps;
    double latencyMs;
    bool available;

    Link(
        string from,
        string to,
        NetworkType networkType,
        double bandwidth,
        double latency
    )
        : source(move(from)),
          destination(move(to)),
          type(networkType),
          bandwidthMbps(bandwidth),
          latencyMs(latency),
          available(true) {

        if (bandwidth <= 0 || latency < 0) {
            throw invalid_argument("Invalid link parameters");
        }
    }
};

// ============================================================
// 7. NETWORK TOPOLOGY AND PATH FINDING
// ============================================================

class NetworkTopology {
private:
    unordered_map<string, NetworkDevice> devices;
    unordered_map<string, vector<Link>> adjacency;

public:
    void addDevice(NetworkDevice device) {
        if (devices.count(device.id)) {
            throw invalid_argument("Duplicate device ID");
        }

        devices.emplace(device.id, move(device));
    }

    void connect(Link link) {
        if (!devices.count(link.source) ||
            !devices.count(link.destination)) {
            throw invalid_argument("Unknown link endpoint");
        }

        if (link.source == link.destination) {
            throw invalid_argument("Self-links are prohibited");
        }

        auto& edges = adjacency[link.source];

        if (any_of(
            edges.begin(),
            edges.end(),
            [&](const Link& existing) {
                return existing.destination == link.destination;
            }
        )) {
            throw invalid_argument("Duplicate connection");
        }

        edges.push_back(move(link));
    }

    vector<string> shortestPath(
        const string& source,
        const string& destination
    ) const {

        if (!devices.count(source) || !devices.count(destination)) {
            throw invalid_argument("Unknown endpoint");
        }

        queue<vector<string>> pending;
        set<string> visited;

        pending.push({source});
        visited.insert(source);

        while (!pending.empty()) {
            auto path = pending.front();
            pending.pop();

            const string& current = path.back();

            if (current == destination) {
                return path;
            }

            auto iterator = adjacency.find(current);

            if (iterator == adjacency.end()) {
                continue;
            }

            for (const auto& link : iterator->second) {
                if (!link.available ||
                    visited.count(link.destination)) {
                    continue;
                }

                visited.insert(link.destination);

                auto nextPath = path;
                nextPath.push_back(link.destination);
                pending.push(move(nextPath));
            }
        }

        throw runtime_error("No available route");
    }

    const Link& getLink(
        const string& source,
        const string& destination
    ) const {

        auto iterator = adjacency.find(source);

        if (iterator == adjacency.end()) {
            throw runtime_error("Link unavailable");
        }

        for (const auto& link : iterator->second) {
            if (link.destination == destination && link.available) {
                return link;
            }
        }

        throw runtime_error("Link unavailable");
    }

    void setLinkStatus(
        const string& source,
        const string& destination,
        bool available
    ) {

        auto iterator = adjacency.find(source);

        if (iterator == adjacency.end()) {
            throw invalid_argument("Link not found");
        }

        for (auto& link : iterator->second) {
            if (link.destination == destination) {
                link.available = available;
                return;
            }
        }

        throw invalid_argument("Link not found");
    }
};

// ============================================================
// 8. ROUTING TABLE AND LONGEST PREFIX MATCHING
// ============================================================

struct Route {
    Subnet destination;
    string nextHop;
    int metric;
};

class RoutingTable {
private:
    vector<Route> routes;

public:
    void addRoute(
        const string& network,
        int prefix,
        const string& nextHop,
        int metric = 1
    ) {
        if (metric < 0 || nextHop.empty()) {
            throw invalid_argument("Invalid route");
        }

        routes.push_back({
            Subnet(network, prefix),
            nextHop,
            metric
        });
    }

    const Route* lookup(const IPv4& destination) const {
        const Route* best = nullptr;

        for (const auto& route : routes) {
            if (!route.destination.contains(destination)) {
                continue;
            }

            if (!best ||
                route.destination.prefix() >
                    best->destination.prefix() ||
                (route.destination.prefix() ==
                     best->destination.prefix() &&
                 route.metric < best->metric)) {
                best = &route;
            }
        }

        return best;
    }
};

// ============================================================
// 9. PACKET SWITCHING ENGINE
// ============================================================

struct TransmissionResult {
    int packetId;
    bool delivered;
    string reason;
    vector<string> path;
    double latencyMs;
    double bottleneckMbps;
    int remainingTTL;
};

class PacketSwitch {
private:
    const NetworkTopology& topology;
    int nextPacketId = 1;

    uint64_t transmitted = 0;
    uint64_t delivered = 0;
    uint64_t dropped = 0;
    uint64_t transmittedBytes = 0;

public:
    explicit PacketSwitch(const NetworkTopology& network)
        : topology(network) {}

    Packet createPacket(
        const string& source,
        const string& destination,
        const string& payload,
        Protocol protocol = Protocol::TCP,
        int ttl = 64
    ) {
        return Packet(
            nextPacketId++,
            source,
            destination,
            protocol,
            payload,
            ttl
        );
    }

    TransmissionResult transmit(
        Packet& packet,
        const string& source,
        const string& destination
    ) {
        transmitted++;

        try {
            vector<string> path =
                topology.shortestPath(source, destination);

            double latency = 0;
            double bandwidth = numeric_limits<double>::max();

            for (size_t i = 0; i < path.size(); ++i) {
                packet.hops.push_back(path[i]);

                if (i + 1 == path.size()) {
                    break;
                }

                if (packet.ttl <= 1) {
                    throw runtime_error("TTL expired");
                }

                packet.ttl--;

                const Link& link =
                    topology.getLink(path[i], path[i + 1]);

                latency += link.latencyMs;
                bandwidth = min(bandwidth, link.bandwidthMbps);
            }

            delivered++;
            transmittedBytes += packet.sizeBytes();

            return {
                packet.id,
                true,
                "DELIVERED",
                packet.hops,
                latency,
                bandwidth,
                packet.ttl
            };

        } catch (const exception& error) {
            dropped++;

            return {
                packet.id,
                false,
                error.what(),
                packet.hops,
                0,
                0,
                packet.ttl
            };
        }
    }

    void displayStatistics() const {
        cout << "\nNETWORK STATISTICS\n";
        cout << "Packets transmitted: " << transmitted << '\n';
        cout << "Packets delivered:   " << delivered << '\n';
        cout << "Packets dropped:     " << dropped << '\n';
        cout << "Bytes transmitted:   " << transmittedBytes << '\n';

        double ratio = transmitted == 0
            ? 0
            : 100.0 * delivered / transmitted;

        cout << fixed << setprecision(2);
        cout << "Delivery rate:       " << ratio << "%\n";
    }
};

// ============================================================
// 10. DISPLAY UTILITIES
// ============================================================

void displayOSIModel() {
    const vector<string> layers = {
        "Physical",
        "Data Link",
        "Network",
        "Transport",
        "Session",
        "Presentation",
        "Application"
    };

    cout << "\nOSI MODEL\n";

    for (int i = 6; i >= 0; --i) {
        cout << "Layer " << i + 1 << ": " << layers[i] << '\n';
    }

    cout << "\nTCP/IP MODEL\n";
    cout << "Application: Application, Presentation, Session\n";
    cout << "Transport:   TCP, UDP\n";
    cout << "Internet:    IP, ICMP\n";
    cout << "Network Access: Ethernet, Wi-Fi\n";
}

void displayResult(const TransmissionResult& result) {
    cout << "\nPACKET " << result.packetId << '\n';
    cout << "Status: " << result.reason << '\n';

    cout << "Path: ";

    for (size_t i = 0; i < result.path.size(); ++i) {
        if (i) cout << " -> ";
        cout << result.path[i];
    }

    cout << '\n';

    if (result.delivered) {
        cout << "Latency: " << result.latencyMs << " ms\n";
        cout << "Bottleneck: " << result.bottleneckMbps
             << " Mbps\n";
        cout << "Remaining TTL: " << result.remainingTTL << '\n';
    }
}

// ============================================================
// 11. NETWORK CONSTRUCTION
// ============================================================

NetworkTopology buildNetwork() {
    NetworkTopology topology;

    topology.addDevice({
        "PC1", "Development Workstation", DeviceType::Host
    });

    topology.addDevice({
        "SW1", "Office Switch", DeviceType::Switch
    });

    topology.addDevice({
        "R1", "Office Router", DeviceType::Router
    });

    topology.addDevice({
        "R2", "Remote Router", DeviceType::Router
    });

    topology.addDevice({
        "SW2", "Remote Switch", DeviceType::Switch
    });

    topology.addDevice({
        "PC2", "Remote Server", DeviceType::Host
    });

    topology.connect({
        "PC1", "SW1", NetworkType::LAN, 1000, 0.1
    });

    topology.connect({
        "SW1", "R1", NetworkType::LAN, 1000, 0.2
    });

    topology.connect({
        "R1", "R2", NetworkType::WAN, 100, 20
    });

    topology.connect({
        "R2", "SW2", NetworkType::LAN, 1000, 0.2
    });

    topology.connect({
        "SW2", "PC2", NetworkType::LAN, 1000, 0.1
    });

    return topology;
}

// ============================================================
// 12. EXECUTION AND VALIDATION
// ============================================================

int main() {
    try {
        cout << "INTRODUCTION TO COMPUTER NETWORKS\n";
        cout << "=================================\n";

        displayOSIModel();

        cout << "\nIP ADDRESSING AND SUBNETTING\n";

        Subnet subnet("192.168.1.10", 24);

        cout << "Network: " << subnet.networkAddress() << '\n';
        cout << "Mask: " << subnet.maskAddress() << '\n';
        cout << "Total addresses: " << subnet.totalAddresses() << '\n';

        IPv4 localIP("192.168.1.100");

        if (!subnet.contains(localIP)) {
            throw runtime_error("Subnet validation failed");
        }

        RoutingTable routing;

        routing.addRoute("10.0.0.0", 8, "R1");
        routing.addRoute("10.1.0.0", 16, "R2");

        const Route* selected =
            routing.lookup(IPv4("10.1.2.3"));

        if (!selected || selected->nextHop != "R2") {
            throw runtime_error("Longest-prefix routing failed");
        }

        cout << "\nSelected next hop: " << selected->nextHop << '\n';

        NetworkTopology topology = buildNetwork();
        PacketSwitch engine(topology);

        cout << "\nPACKET SWITCHING\n";

        Packet packet = engine.createPacket(
            "192.168.1.10",
            "10.0.0.10",
            "Network communication demonstration",
            Protocol::TCP
        );

        auto result = engine.transmit(packet, "PC1", "PC2");
        displayResult(result);

        if (!result.delivered) {
            throw runtime_error("Expected packet delivery");
        }

        cout << "\nTTL FAILURE TEST\n";

        Packet ttlPacket = engine.createPacket(
            "192.168.1.10",
            "10.0.0.10",
            "TTL test",
            Protocol::TCP,
            2
        );

        auto ttlResult =
            engine.transmit(ttlPacket, "PC1", "PC2");

        displayResult(ttlResult);

        if (ttlResult.delivered) {
            throw runtime_error("TTL test should have failed");
        }

        cout << "\nWAN FAILURE TEST\n";

        topology.setLinkStatus("R1", "R2", false);

        Packet failedPacket = engine.createPacket(
            "192.168.1.10",
            "10.0.0.10",
            "WAN failure test"
        );

        auto failedResult =
            engine.transmit(failedPacket, "PC1", "PC2");

        displayResult(failedResult);

        if (failedResult.delivered) {
            throw runtime_error("WAN failure was not detected");
        }

        engine.displayStatistics();

        cout << "\nAll validation tests passed.\n";

        return 0;

    } catch (const exception& error) {
        cerr << "Network simulation error: "
             << error.what() << '\n';

        return 1;
    }
}
