#include <algorithm>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <optional>
#include <queue>
#include <set>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_map>
#include <utility>
#include <vector>

/*
 * Routing Fundamentals
 * C++17 network routing and forwarding engine.
 *
 * Implements:
 * - Network topology
 * - Static routing
 * - Routing table lookup
 * - Longest prefix matching
 * - Administrative distance
 * - Dijkstra's shortest-path algorithm
 * - Distance-vector routing
 * - Link failure simulation
 * - Route eligibility and packet forwarding
 */

using namespace std;

class RoutingException : public runtime_error {
public:
    using runtime_error::runtime_error;
};

enum class Protocol {
    STATIC,
    OSPF,
    RIP
};

string protocolName(Protocol protocol) {
    switch (protocol) {
        case Protocol::STATIC: return "STATIC";
        case Protocol::OSPF: return "OSPF";
        case Protocol::RIP: return "RIP";
    }
    return "UNKNOWN";
}

int administrativeDistance(Protocol protocol) {
    switch (protocol) {
        case Protocol::STATIC: return 1;
        case Protocol::OSPF: return 110;
        case Protocol::RIP: return 120;
    }
    throw RoutingException("Invalid protocol.");
}

struct IPv4Network {
    uint32_t network;
    int prefix;

    static uint32_t parseAddress(const string& address) {
        uint32_t result = 0;
        size_t start = 0;

        for (int i = 0; i < 4; ++i) {
            size_t end = address.find('.', start);

            if (i == 3) {
                end = string::npos;
            }

            string part = address.substr(
                start,
                end == string::npos
                    ? string::npos
                    : end - start
            );

            if (part.empty() || part.size() > 3) {
                throw RoutingException("Invalid IPv4 address.");
            }

            for (char c : part) {
                if (!isdigit(static_cast<unsigned char>(c))) {
                    throw RoutingException("Invalid IPv4 octet.");
                }
            }

            int octet = stoi(part);

            if (octet > 255) {
                throw RoutingException("IPv4 octet exceeds 255.");
            }

            result = (result << 8) | static_cast<uint32_t>(octet);

            if (i < 3 && end == string::npos) {
                throw RoutingException("Incomplete IPv4 address.");
            }

            if (i == 3 && end != string::npos) {
                throw RoutingException("Invalid IPv4 address.");
            }

            start = end == string::npos ? address.size() : end + 1;
        }

        return result;
    }

    static IPv4Network parse(const string& cidr) {
        size_t separator = cidr.find('/');

        if (separator == string::npos) {
            throw RoutingException("CIDR prefix is required.");
        }

        uint32_t address = parseAddress(
            cidr.substr(0, separator)
        );

        string prefixText = cidr.substr(separator + 1);

        if (prefixText.empty()) {
            throw RoutingException("Missing prefix length.");
        }

        int prefix = stoi(prefixText);

        if (prefix < 0 || prefix > 32) {
            throw RoutingException("Invalid prefix length.");
        }

        uint32_t mask = prefix == 0
            ? 0
            : (0xFFFFFFFFu << (32 - prefix));

        return {
            address & mask,
            prefix
        };
    }

    bool contains(uint32_t address) const {
        uint32_t mask = prefix == 0
            ? 0
            : (0xFFFFFFFFu << (32 - prefix));

        return (address & mask) == network;
    }

    bool overlaps(const IPv4Network& other) const {
        if (prefix <= other.prefix) {
            return contains(other.network);
        }
        return other.contains(network);
    }

    string toString() const {
        return to_string((network >> 24) & 255) + "." +
               to_string((network >> 16) & 255) + "." +
               to_string((network >> 8) & 255) + "." +
               to_string(network & 255) + "/" +
               to_string(prefix);
    }
};

struct Link {
    string destination;
    double cost;
    bool available = true;
};

struct Route {
    IPv4Network network;
    optional<string> nextHop;
    string interfaceName;
    double metric;
    Protocol protocol;
    int distance;
    bool active = true;
};

struct PathResult {
    double cost = numeric_limits<double>::infinity();
    optional<string> nextHop;
};

class RoutingTable {
private:
    string routerId;
    vector<Route> routes;

public:
    explicit RoutingTable(string id)
        : routerId(move(id)) {}

    void addRoute(const Route& route) {
        if (route.metric < 0 || !isfinite(route.metric)) {
            throw RoutingException("Invalid route metric.");
        }

        if (route.distance < 0) {
            throw RoutingException("Invalid administrative distance.");
        }

        routes.push_back(route);
    }

    bool removeRoute(
        const string& network,
        optional<Protocol> protocol = nullopt
    ) {
        size_t before = routes.size();

        routes.erase(
            remove_if(
                routes.begin(),
                routes.end(),
                [&](const Route& route) {
                    return route.network.toString() == network &&
                           (!protocol || route.protocol == *protocol);
                }
            ),
            routes.end()
        );

        return routes.size() != before;
    }

    const Route& lookup(const string& destination) const {
        uint32_t address = IPv4Network::parseAddress(destination);

        const Route* best = nullptr;

        for (const Route& route : routes) {
            if (!route.active ||
                !route.network.contains(address)) {
                continue;
            }

            if (
                best == nullptr ||
                route.network.prefix > best->network.prefix ||
                (
                    route.network.prefix == best->network.prefix &&
                    route.distance < best->distance
                ) ||
                (
                    route.network.prefix == best->network.prefix &&
                    route.distance == best->distance &&
                    route.metric < best->metric
                )
            ) {
                best = &route;
            }
        }

        if (best == nullptr) {
            throw RoutingException(
                "No matching route for " + destination
            );
        }

        return *best;
    }

    const vector<Route>& getRoutes() const {
        return routes;
    }

    void display() const {
        cout << "\nRouting Table: " << routerId << '\n';

        cout << left
             << setw(20) << "Network"
             << setw(14) << "Next Hop"
             << setw(12) << "Interface"
             << setw(10) << "Metric"
             << setw(10) << "Protocol"
             << '\n';

        cout << string(66, '-') << '\n';

        for (const auto& route : routes) {
            if (!route.active) continue;

            cout << left
                 << setw(20) << route.network.toString()
                 << setw(14) << route.nextHop.value_or("DIRECT")
                 << setw(12) << route.interfaceName
                 << setw(10) << route.metric
                 << setw(10) << protocolName(route.protocol)
                 << '\n';
        }
    }
};

class NetworkTopology {
private:
    unordered_map<string, vector<Link>> adjacency;

public:
    void addRouter(const string& router) {
        if (router.empty()) {
            throw RoutingException("Router ID cannot be empty.");
        }

        adjacency.try_emplace(router);
    }

    void addLink(
        const string& source,
        const string& destination,
        double cost,
        bool bidirectional = true
    ) {
        if (source == destination) {
            throw RoutingException("Self-links are not supported.");
        }

        if (cost < 0 || !isfinite(cost)) {
            throw RoutingException("Invalid link cost.");
        }

        addRouter(source);
        addRouter(destination);

        auto& links = adjacency.at(source);

        links.erase(
            remove_if(
                links.begin(),
                links.end(),
                [&](const Link& link) {
                    return link.destination == destination;
                }
            ),
            links.end()
        );

        links.push_back({destination, cost, true});

        if (bidirectional) {
            addLink(destination, source, cost, false);
        }
    }

    void setLinkState(
        const string& source,
        const string& destination,
        bool available
    ) {
        if (!adjacency.count(source)) {
            throw RoutingException("Unknown source router.");
        }

        for (auto& link : adjacency.at(source)) {
            if (link.destination == destination) {
                link.available = available;
                return;
            }
        }

        throw RoutingException("Link does not exist.");
    }

    const vector<Link>& neighbors(const string& router) const {
        auto it = adjacency.find(router);

        if (it == adjacency.end()) {
            throw RoutingException("Unknown router.");
        }

        return it->second;
    }

    vector<string> routers() const {
        vector<string> result;

        for (const auto& entry : adjacency) {
            result.push_back(entry.first);
        }

        sort(result.begin(), result.end());
        return result;
    }

    bool containsRouter(const string& router) const {
        return adjacency.count(router) != 0;
    }
};

class RoutingEngine {
public:
    static unordered_map<string, PathResult> dijkstra(
        const NetworkTopology& topology,
        const string& source
    ) {
        if (!topology.containsRouter(source)) {
            throw RoutingException("Unknown source router.");
        }

        unordered_map<string, PathResult> result;

        for (const auto& router : topology.routers()) {
            result[router] = {};
        }

        result[source].cost = 0;

        using State = pair<double, string>;

        priority_queue<
            State,
            vector<State>,
            greater<State>
        > queue;

        queue.push({0, source});

        while (!queue.empty()) {
            auto [cost, current] = queue.top();
            queue.pop();

            if (cost > result[current].cost) {
                continue;
            }

            for (const auto& edge : topology.neighbors(current)) {
                if (!edge.available) continue;

                double candidate = cost + edge.cost;

                if (candidate < result[edge.destination].cost) {
                    result[edge.destination].cost = candidate;

                    result[edge.destination].nextHop =
                        current == source
                            ? edge.destination
                            : result[current].nextHop;

                    queue.push({
                        candidate,
                        edge.destination
                    });
                }
            }
        }

        return result;
    }

    static unordered_map<string, PathResult> distanceVector(
        const NetworkTopology& topology,
        const string& source
    ) {
        if (!topology.containsRouter(source)) {
            throw RoutingException("Unknown source router.");
        }

        auto routers = topology.routers();

        unordered_map<string, PathResult> result;

        for (const auto& router : routers) {
            result[router] = {};
        }

        result[source].cost = 0;

        for (size_t iteration = 0;
             iteration + 1 < routers.size();
             ++iteration) {

            auto previous = result;
            bool changed = false;

            for (const auto& router : routers) {
                if (!isfinite(previous[router].cost)) {
                    continue;
                }

                for (const auto& edge : topology.neighbors(router)) {
                    if (!edge.available) continue;

                    double candidate =
                        previous[router].cost + edge.cost;

                    if (candidate < result[edge.destination].cost) {
                        result[edge.destination].cost = candidate;

                        result[edge.destination].nextHop =
                            router == source
                                ? edge.destination
                                : previous[router].nextHop;

                        changed = true;
                    }
                }
            }

            if (!changed) break;
        }

        return result;
    }
};

class Router {
private:
    string id;
    const NetworkTopology& topology;
    RoutingTable table;

public:
    Router(
        string routerId,
        const NetworkTopology& network
    )
        : id(move(routerId)),
          topology(network),
          table(id) {}

    void addStaticRoute(
        const string& network,
        optional<string> nextHop,
        const string& interfaceName,
        double metric = 1
    ) {
        if (nextHop && !topology.containsRouter(*nextHop)) {
            throw RoutingException("Invalid next-hop router.");
        }

        table.addRoute({
            IPv4Network::parse(network),
            nextHop,
            interfaceName,
            metric,
            Protocol::STATIC,
            administrativeDistance(Protocol::STATIC),
            true
        });
    }

    void installDynamicRoutes(
        const map<string, string>& destinationNetworks,
        Protocol protocol
    ) {
        unordered_map<string, PathResult> paths;

        if (protocol == Protocol::OSPF) {
            paths = RoutingEngine::dijkstra(topology, id);
        } else if (protocol == Protocol::RIP) {
            paths = RoutingEngine::distanceVector(topology, id);
        } else {
            throw RoutingException(
                "Static routes are installed separately."
            );
        }

        for (const auto& [router, network] : destinationNetworks) {
            if (!paths.count(router)) {
                throw RoutingException("Unknown destination router.");
            }

            const auto& path = paths.at(router);

            if (!isfinite(path.cost)) continue;

            table.addRoute({
                IPv4Network::parse(network),
                path.nextHop,
                "eth-" + path.nextHop.value_or("local"),
                path.cost,
                protocol,
                administrativeDistance(protocol),
                true
            });
        }
    }

    void forwardPacket(const string& destination) const {
        const Route& route = table.lookup(destination);

        cout << "Packet forwarding decision\n"
             << "Router: " << id << '\n'
             << "Destination: " << destination << '\n'
             << "Matched network: " << route.network.toString() << '\n'
             << "Next hop: "
             << route.nextHop.value_or("DIRECT") << '\n'
             << "Interface: " << route.interfaceName << '\n'
             << "Protocol: " << protocolName(route.protocol) << '\n'
             << "Metric: " << route.metric << '\n';
    }

    void display() const {
        table.display();
    }
};

void demonstrate() {
    NetworkTopology topology;

    for (const string& id : {"R1", "R2", "R3", "R4"}) {
        topology.addRouter(id);
    }

    topology.addLink("R1", "R2", 2);
    topology.addLink("R1", "R3", 5);
    topology.addLink("R2", "R3", 1);
    topology.addLink("R2", "R4", 7);
    topology.addLink("R3", "R4", 2);

    cout << "DIJKSTRA SHORTEST PATHS\n";

    auto shortest = RoutingEngine::dijkstra(topology, "R1");

    for (const auto& router : topology.routers()) {
        const auto& path = shortest.at(router);

        cout << "R1 -> " << router
             << ": cost=" << path.cost
             << ", next-hop="
             << path.nextHop.value_or("LOCAL")
             << '\n';
    }

    cout << "\nDISTANCE VECTOR ROUTING\n";

    auto vectors = RoutingEngine::distanceVector(
        topology,
        "R1"
    );

    for (const auto& router : topology.routers()) {
        cout << "R1 -> " << router
             << ": cost=" << vectors.at(router).cost
             << ", next-hop="
             << vectors.at(router).nextHop.value_or("LOCAL")
             << '\n';
    }

    Router r1("R1", topology);

    cout << "\nSTATIC ROUTING\n";

    r1.addStaticRoute(
        "192.168.10.0/24",
        "R2",
        "eth0"
    );

    r1.forwardPacket("192.168.10.25");

    cout << "\nDYNAMIC ROUTING\n";

    r1.installDynamicRoutes(
        {
            {"R2", "10.0.2.0/24"},
            {"R3", "10.0.3.0/24"},
            {"R4", "10.0.4.0/24"}
        },
        Protocol::OSPF
    );

    r1.display();

    cout << "\nLINK FAILURE\n";

    topology.setLinkState("R2", "R3", false);

    auto updated = RoutingEngine::dijkstra(
        topology,
        "R1"
    );

    cout << "New cost to R4: "
         << updated.at("R4").cost << '\n';

    cout << "\nLONGEST PREFIX MATCHING\n";

    RoutingTable testTable("R5");

    testTable.addRoute({
        IPv4Network::parse("192.168.0.0/16"),
        "R2",
        "eth0",
        10,
        Protocol::STATIC,
        1,
        true
    });

    testTable.addRoute({
        IPv4Network::parse("192.168.10.0/24"),
        "R3",
        "eth1",
        5,
        Protocol::OSPF,
        110,
        true
    });

    cout << "Selected network: "
         << testTable.lookup("192.168.10.50")
                .network.toString()
         << '\n';
}

void runTests() {
    NetworkTopology topology;

    topology.addLink("A", "B", 2);
    topology.addLink("B", "C", 3);
    topology.addLink("A", "C", 10);

    auto dijkstra = RoutingEngine::dijkstra(topology, "A");
    auto vector = RoutingEngine::distanceVector(topology, "A");

    if (dijkstra.at("C").cost != 5 ||
        vector.at("C").cost != 5) {
        throw RoutingException("Shortest-path test failed.");
    }

    if (dijkstra.at("C").nextHop != optional<string>("B")) {
        throw RoutingException("Next-hop test failed.");
    }

    RoutingTable table("A");

    table.addRoute({
        IPv4Network::parse("10.0.0.0/8"),
        "B",
        "eth0",
        10,
        Protocol::STATIC,
        1,
        true
    });

    table.addRoute({
        IPv4Network::parse("10.1.0.0/16"),
        "C",
        "eth1",
        5,
        Protocol::OSPF,
        110,
        true
    });

    if (
        table.lookup("10.1.2.3").network.toString()
        != "10.1.0.0/16"
    ) {
        throw RoutingException("Longest-prefix test failed.");
    }

    topology.setLinkState("B", "C", false);

    auto updated = RoutingEngine::dijkstra(topology, "A");

    if (updated.at("C").cost != 10) {
        throw RoutingException("Link failure test failed.");
    }

    cout << "\nAll C++ routing tests passed.\n";
}

int main() {
    try {
        demonstrate();
        runTests();
    } catch (const exception& error) {
        cerr << "Routing error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
