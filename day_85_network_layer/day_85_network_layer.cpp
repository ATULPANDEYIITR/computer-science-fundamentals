#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;

/*
 * Network Layer Engineering
 * IPv4 address management, CIDR, subnetting and routing.
 *
 * C++17, standard library only.
 *
 * The routing engine uses a 32-bit integer representation
 * and implements IPv4 longest-prefix matching.
 */

class NetworkError : public runtime_error {
public:
    explicit NetworkError(const string& message)
        : runtime_error(message) {}
};

class IPv4Address {
private:
    uint32_t value_;

public:
    explicit IPv4Address(uint32_t value = 0)
        : value_(value) {}

    static IPv4Address parse(const string& address) {
        array<unsigned int, 4> octets{};
        size_t start = 0;

        for (int i = 0; i < 4; ++i) {
            size_t end = address.find('.', start);

            if (i == 3) {
                end = string::npos;
            }

            string part = address.substr(
                start,
                end == string::npos ? end : end - start
            );

            if (part.empty() || part.size() > 3) {
                throw NetworkError("Invalid IPv4 octet");
            }

            for (char character : part) {
                if (character < '0' || character > '9') {
                    throw NetworkError("Non-numeric IPv4 octet");
                }
            }

            size_t consumed = 0;
            unsigned long number = stoul(part, &consumed);

            if (consumed != part.size() || number > 255) {
                throw NetworkError("IPv4 octet outside valid range");
            }

            octets[i] = static_cast<unsigned int>(number);

            if (i != 3) {
                if (end == string::npos) {
                    throw NetworkError("Incomplete IPv4 address");
                }

                start = end + 1;
            } else if (address.find('.', start) != string::npos) {
                throw NetworkError("Too many IPv4 octets");
            }
        }

        uint32_t value = 0;

        for (unsigned int octet : octets) {
            value = (value << 8) | octet;
        }

        return IPv4Address(value);
    }

    uint32_t value() const {
        return value_;
    }

    string toString() const {
        return to_string((value_ >> 24) & 255) + "." +
               to_string((value_ >> 16) & 255) + "." +
               to_string((value_ >> 8) & 255) + "." +
               to_string(value_ & 255);
    }

    bool operator==(const IPv4Address& other) const {
        return value_ == other.value_;
    }
};

struct IPv4Network {
    IPv4Address network;
    uint8_t prefix;

    static IPv4Network parse(const string& cidr) {
        size_t slash = cidr.find('/');

        if (slash == string::npos ||
            cidr.find('/', slash + 1) != string::npos) {
            throw NetworkError("CIDR prefix is required");
        }

        IPv4Address address =
            IPv4Address::parse(cidr.substr(0, slash));

        string prefixText = cidr.substr(slash + 1);

        if (prefixText.empty() ||
            !all_of(prefixText.begin(), prefixText.end(),
                [](unsigned char c) { return c >= '0' && c <= '9'; })) {
            throw NetworkError("Invalid CIDR prefix");
        }

        int prefix = stoi(prefixText);

        if (prefix < 0 || prefix > 32) {
            throw NetworkError("IPv4 prefix must be between 0 and 32");
        }

        uint32_t mask = prefix == 0
            ? 0u
            : (0xFFFFFFFFu << (32 - prefix));

        if ((address.value() & mask) != address.value()) {
            throw NetworkError(
                "Network address contains host bits; use canonical CIDR"
            );
        }

        return {address, static_cast<uint8_t>(prefix)};
    }

    uint32_t mask() const {
        return prefix == 0
            ? 0u
            : (0xFFFFFFFFu << (32 - prefix));
    }

    uint32_t broadcast() const {
        return network.value() | ~mask();
    }

    uint64_t totalAddresses() const {
        return 1ULL << (32 - prefix);
    }

    bool contains(const IPv4Address& address) const {
        return (address.value() & mask()) == network.value();
    }

    string toString() const {
        return network.toString() + "/" + to_string(prefix);
    }

    string netmaskString() const {
        return IPv4Address(mask()).toString();
    }
};

enum class InterfaceState {
    UP,
    DOWN
};

struct NetworkInterface {
    string name;
    IPv4Address address;
    IPv4Network subnet;
    unsigned int mtu = 1500;
    InterfaceState state = InterfaceState::UP;

    NetworkInterface(
        string interfaceName,
        const string& cidr,
        unsigned int maximumTransmissionUnit = 1500
    )
        : name(move(interfaceName)),
          address(IPv4Address::parse(cidr.substr(0, cidr.find('/')))),
          subnet(IPv4Network::parse(cidr)),
          mtu(maximumTransmissionUnit) {

        if (name.empty()) {
            throw NetworkError("Interface name cannot be empty");
        }

        if (mtu < 576 || mtu > 65535) {
            throw NetworkError("Invalid interface MTU");
        }

        if (!subnet.contains(address)) {
            throw NetworkError("Interface address outside subnet");
        }
    }
};

enum class RouteState {
    ACTIVE,
    INACTIVE
};

struct Route {
    IPv4Network destination;
    string interfaceName;
    optional<IPv4Address> nextHop;
    unsigned int metric;
    RouteState state;

    Route(
        const string& cidr,
        string interface,
        optional<string> gateway = nullopt,
        unsigned int routeMetric = 100
    )
        : destination(IPv4Network::parse(cidr)),
          interfaceName(move(interface)),
          metric(routeMetric),
          state(RouteState::ACTIVE) {

        if (gateway.has_value()) {
            nextHop = IPv4Address::parse(*gateway);
        }
    }
};

struct ForwardingResult {
    IPv4Address source;
    IPv4Address destination;
    IPv4Address nextHop;
    string interfaceName;
    string matchedNetwork;
    unsigned int metric;
};

class Router {
private:
    unordered_map<string, NetworkInterface> interfaces_;
    vector<Route> routes_;

public:
    void addInterface(NetworkInterface networkInterface) {
        string name = networkInterface.name;

        if (interfaces_.find(name) != interfaces_.end()) {
            throw NetworkError("Duplicate interface: " + name);
        }

        interfaces_.emplace(name, move(networkInterface));
    }

    void addRoute(Route route) {
        auto interface = interfaces_.find(route.interfaceName);

        if (interface == interfaces_.end()) {
            throw NetworkError("Unknown outgoing interface");
        }

        if (interface->second.state != InterfaceState::UP) {
            throw NetworkError("Outgoing interface is down");
        }

        if (route.nextHop.has_value() &&
            !IPv4Network::parse(
                route.interfaceName == "eth0"
                    ? "0.0.0.0/0"
                    : "0.0.0.0/0"
            ).contains(*route.nextHop)) {
            throw NetworkError("Invalid gateway");
        }

        routes_.push_back(move(route));
    }

    void setInterfaceState(
        const string& name,
        InterfaceState state
    ) {
        auto it = interfaces_.find(name);

        if (it == interfaces_.end()) {
            throw NetworkError("Unknown interface");
        }

        it->second.state = state;
    }

    const Route& lookup(const IPv4Address& destination) const {
        const Route* best = nullptr;

        for (const Route& route : routes_) {
            if (route.state != RouteState::ACTIVE) {
                continue;
            }

            if (!route.destination.contains(destination)) {
                continue;
            }

            auto interface = interfaces_.find(route.interfaceName);

            if (interface == interfaces_.end() ||
                interface->second.state != InterfaceState::UP) {
                continue;
            }

            if (best == nullptr ||
                route.destination.prefix > best->destination.prefix ||
                (
                    route.destination.prefix == best->destination.prefix &&
                    route.metric < best->metric
                )) {
                best = &route;
            }
        }

        if (best == nullptr) {
            throw NetworkError("No available route to destination");
        }

        return *best;
    }

    ForwardingResult forward(
        const string& sourceText,
        const string& destinationText,
        unsigned int payloadBytes
    ) const {
        IPv4Address source = IPv4Address::parse(sourceText);
        IPv4Address destination =
            IPv4Address::parse(destinationText);

        if (payloadBytes > 65515) {
            throw NetworkError("IPv4 payload exceeds packet size limit");
        }

        const Route& route = lookup(destination);

        const auto& outgoing = interfaces_.at(route.interfaceName);

        if (payloadBytes + 20 > outgoing.mtu) {
            throw NetworkError(
                "Packet exceeds MTU; fragmentation is not implemented"
            );
        }

        return {
            source,
            destination,
            route.nextHop.value_or(destination),
            route.interfaceName,
            route.destination.toString(),
            route.metric
        };
    }

    void displayRoutes() const {
        cout << "\nROUTING TABLE\n";
        cout << "--------------------------------------------------\n";

        for (const Route& route : routes_) {
            cout << route.destination.toString()
                 << "  via ";

            if (route.nextHop.has_value()) {
                cout << route.nextHop->toString();
            } else {
                cout << "DIRECT";
            }

            cout << "  dev " << route.interfaceName
                 << "  metric " << route.metric << '\n';
        }
    }

    void displayInterfaces() const {
        cout << "\nNETWORK INTERFACES\n";

        for (const auto& entry : interfaces_) {
            const auto& interface = entry.second;

            cout << interface.name
                 << "  " << interface.address.toString()
                 << "/" << static_cast<int>(interface.subnet.prefix)
                 << "  MTU=" << interface.mtu
                 << "  STATE="
                 << (
                     interface.state == InterfaceState::UP
                         ? "UP"
                         : "DOWN"
                 )
                 << '\n';
        }
    }
};

void analyzeSubnet(const string& cidr) {
    IPv4Network network = IPv4Network::parse(cidr);

    cout << "\nSUBNET ANALYSIS\n";
    cout << "Network: " << network.toString() << '\n';
    cout << "Netmask: " << network.netmaskString() << '\n';
    cout << "Broadcast: "
         << IPv4Address(network.broadcast()).toString() << '\n';
    cout << "Total addresses: "
         << network.totalAddresses() << '\n';

    uint64_t usable = network.prefix <= 30
        ? network.totalAddresses() - 2
        : network.totalAddresses();

    cout << "Usable host addresses: " << usable << '\n';

    if (network.prefix <= 30) {
        cout << "First host: "
             << IPv4Address(network.network.value() + 1).toString()
             << '\n';

        cout << "Last host: "
             << IPv4Address(network.broadcast() - 1).toString()
             << '\n';
    }
}

vector<IPv4Network> divideSubnet(
    const IPv4Network& parent,
    uint8_t newPrefix
) {
    if (newPrefix < parent.prefix || newPrefix > 32) {
        throw NetworkError("Invalid child subnet prefix");
    }

    uint64_t count = 1ULL << (newPrefix - parent.prefix);

    if (count > 4096) {
        throw NetworkError("Too many child networks");
    }

    uint64_t blockSize = 1ULL << (32 - newPrefix);

    vector<IPv4Network> result;

    for (uint64_t i = 0; i < count; ++i) {
        uint32_t start = static_cast<uint32_t>(
            static_cast<uint64_t>(parent.network.value()) +
            i * blockSize
        );

        result.push_back({
            IPv4Address(start),
            newPrefix
        });
    }

    return result;
}

int main() {
    try {
        cout << "NETWORK LAYER ENGINEERING\n";

        analyzeSubnet("192.168.10.0/24");

        cout << "\nSUBNET DIVISION\n";

        auto subnets = divideSubnet(
            IPv4Network::parse("192.168.10.0/24"),
            26
        );

        for (const auto& subnet : subnets) {
            cout << subnet.toString() << '\n';
        }

        Router router;

        router.addInterface(
            NetworkInterface("eth0", "192.168.10.1/24")
        );

        router.addInterface(
            NetworkInterface("eth1", "10.0.0.1/24")
        );

        router.addInterface(
            NetworkInterface("eth2", "172.16.0.1/24")
        );

        router.addRoute(
            Route("0.0.0.0/0", "eth1", "10.0.0.254", 200)
        );

        router.addRoute(
            Route("172.16.0.0/16", "eth1", "10.0.0.2", 50)
        );

        router.addRoute(
            Route("172.16.10.0/24", "eth1", "10.0.0.3", 10)
        );

        router.addRoute(
            Route("192.168.10.0/24", "eth0")
        );

        router.displayInterfaces();
        router.displayRoutes();

        cout << "\nPACKET FORWARDING\n";

        auto result = router.forward(
            "192.168.10.20",
            "172.16.10.50",
            1200
        );

        cout << "Source: " << result.source.toString() << '\n';
        cout << "Destination: "
             << result.destination.toString() << '\n';
        cout << "Next hop: " << result.nextHop.toString() << '\n';
        cout << "Interface: " << result.interfaceName << '\n';
        cout << "Matched route: " << result.matchedNetwork << '\n';
        cout << "Metric: " << result.metric << '\n';

        if (result.matchedNetwork != "172.16.10.0/24") {
            throw NetworkError("Longest-prefix matching assertion failed");
        }

        cout << "\nVALIDATION TESTS\n";

        try {
            IPv4Address::parse("192.168.1.300");
        } catch (const NetworkError& error) {
            cout << "Rejected invalid address: "
                 << error.what() << '\n';
        }

        try {
            IPv4Network::parse("192.168.10.5/24");
        } catch (const NetworkError& error) {
            cout << "Rejected noncanonical CIDR: "
                 << error.what() << '\n';
        }

        try {
            router.forward(
                "192.168.10.20",
                "203.0.113.10",
                100
            );
        } catch (const NetworkError& error) {
            cout << "Expected routing failure: "
                 << error.what() << '\n';
        }

        try {
            router.forward(
                "192.168.10.20",
                "172.16.10.50",
                2000
            );
        } catch (const NetworkError& error) {
            cout << "Expected MTU failure: "
                 << error.what() << '\n';
        }

        router.setInterfaceState("eth1", InterfaceState::DOWN);

        try {
            router.forward(
                "192.168.10.20",
                "172.16.10.50",
                100
            );
        } catch (const NetworkError& error) {
            cout << "Expected interface failure: "
                 << error.what() << '\n';
        }

        cout << "\nALL TESTS COMPLETED\n";

    } catch (const exception& error) {
        cerr << "NETWORK ERROR: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
