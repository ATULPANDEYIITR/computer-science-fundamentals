#include <algorithm>
#include <cstdint>
#include <deque>
#include <exception>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

using namespace std;

enum class Protocol {
    TCP,
    UDP
};

enum class ConnectionState {
    CLOSED,
    LISTEN,
    SYN_SENT,
    SYN_RECEIVED,
    ESTABLISHED,
    FIN_WAIT,
    CLOSE_WAIT,
    TIME_WAIT
};

string toString(Protocol protocol) {
    return protocol == Protocol::TCP ? "TCP" : "UDP";
}

string toString(ConnectionState state) {
    switch (state) {
        case ConnectionState::CLOSED: return "CLOSED";
        case ConnectionState::LISTEN: return "LISTEN";
        case ConnectionState::SYN_SENT: return "SYN_SENT";
        case ConnectionState::SYN_RECEIVED: return "SYN_RECEIVED";
        case ConnectionState::ESTABLISHED: return "ESTABLISHED";
        case ConnectionState::FIN_WAIT: return "FIN_WAIT";
        case ConnectionState::CLOSE_WAIT: return "CLOSE_WAIT";
        case ConnectionState::TIME_WAIT: return "TIME_WAIT";
    }

    throw logic_error("Unknown connection state.");
}

struct Endpoint {
    string ip;
    uint16_t port;

    Endpoint(string address, int portNumber)
        : ip(move(address)) {

        if (ip.empty()) {
            throw invalid_argument("IP address cannot be empty.");
        }

        if (portNumber < 0 || portNumber > 65535) {
            throw out_of_range("Port must be between 0 and 65535.");
        }

        port = static_cast<uint16_t>(portNumber);
    }

    string toString() const {
        return ip + ":" + std::to_string(port);
    }
};

struct ConnectionKey {
    Endpoint local;
    Endpoint remote;
    Protocol protocol;

    ConnectionKey(
        Endpoint source,
        Endpoint destination,
        Protocol transport
    ) : local(move(source)),
        remote(move(destination)),
        protocol(transport) {}
};

struct Segment {
    uint32_t sequence;
    uint32_t length;
    string payload;
};

class FlowControlEngine {
private:
    uint32_t receiveWindow;
    uint32_t maximumWindow;
    uint32_t nextSequence = 0;
    uint32_t acknowledgedSequence = 0;

    deque<Segment> outstanding;

public:
    explicit FlowControlEngine(
        uint32_t initialWindow,
        uint32_t maximum = 65535
    ) : receiveWindow(initialWindow),
        maximumWindow(maximum) {

        if (maximum == 0 || initialWindow > maximum) {
            throw invalid_argument("Invalid receive window.");
        }
    }

    uint32_t inFlightBytes() const {
        uint64_t total = 0;

        for (const auto& segment : outstanding) {
            total += segment.length;
        }

        return static_cast<uint32_t>(total);
    }

    uint32_t availableWindow() const {
        const uint32_t used = inFlightBytes();

        return used >= receiveWindow
            ? 0
            : receiveWindow - used;
    }

    optional<uint32_t> send(const string& payload) {
        if (payload.empty()) {
            throw invalid_argument("Payload cannot be empty.");
        }

        if (payload.size() > availableWindow()) {
            cout << "Transmission blocked: receive window full.\n";
            return nullopt;
        }

        const uint32_t sequence = nextSequence;
        const uint32_t length =
            static_cast<uint32_t>(payload.size());

        outstanding.push_back({
            sequence,
            length,
            payload
        });

        nextSequence += length;

        cout << "Transmitted sequence=" << sequence
             << ", bytes=" << length
             << ", remaining_window=" << availableWindow()
             << '\n';

        return sequence;
    }

    void acknowledge(uint32_t acknowledgement) {
        if (acknowledgement < acknowledgedSequence ||
            acknowledgement > nextSequence) {
            throw invalid_argument("Invalid cumulative ACK.");
        }

        if (acknowledgement == acknowledgedSequence) {
            return;
        }

        while (!outstanding.empty()) {
            const auto& segment = outstanding.front();

            const uint32_t end =
                segment.sequence + segment.length;

            if (end <= acknowledgement) {
                outstanding.pop_front();
            } else {
                break;
            }
        }

        acknowledgedSequence = acknowledgement;

        cout << "ACK=" << acknowledgement
             << ", remaining_window=" << availableWindow()
             << '\n';
    }

    void advertiseWindow(uint32_t newWindow) {
        if (newWindow > maximumWindow) {
            throw out_of_range("Advertised window exceeds maximum.");
        }

        receiveWindow = newWindow;

        cout << "Receiver window updated to "
             << receiveWindow << '\n';
    }

    void retransmitExpired(uint64_t currentTime,
                           uint64_t timeout) const {
        if (timeout == 0) {
            throw invalid_argument("Timeout must be positive.");
        }

        cout << "Retransmission candidates: ";

        bool found = false;

        for (const auto& segment : outstanding) {
            // The simulation uses transmission timestamps in production.
            // This method reports the outstanding sequence ranges.
            (void)currentTime;

            if (segment.length > 0) {
                cout << '[' << segment.sequence
                     << ','
                     << segment.sequence + segment.length
                     << ") ";

                found = true;
            }
        }

        if (!found) {
            cout << "none";
        }

        cout << '\n';
    }
};

class Connection {
private:
    Endpoint local;
    Endpoint remote;
    Protocol protocol;
    ConnectionState state;

    static bool validTransition(
        ConnectionState from,
        ConnectionState to
    ) {
        static const map<ConnectionState, vector<ConnectionState>>
            transitions = {
                {ConnectionState::CLOSED,
                    {ConnectionState::LISTEN,
                     ConnectionState::SYN_SENT}},
                {ConnectionState::LISTEN,
                    {ConnectionState::SYN_RECEIVED,
                     ConnectionState::CLOSED}},
                {ConnectionState::SYN_SENT,
                    {ConnectionState::SYN_RECEIVED,
                     ConnectionState::CLOSED}},
                {ConnectionState::SYN_RECEIVED,
                    {ConnectionState::ESTABLISHED,
                     ConnectionState::CLOSED}},
                {ConnectionState::ESTABLISHED,
                    {ConnectionState::FIN_WAIT,
                     ConnectionState::CLOSE_WAIT}},
                {ConnectionState::FIN_WAIT,
                    {ConnectionState::TIME_WAIT,
                     ConnectionState::CLOSED}},
                {ConnectionState::CLOSE_WAIT,
                    {ConnectionState::CLOSED}},
                {ConnectionState::TIME_WAIT,
                    {ConnectionState::CLOSED}}
            };

        auto it = transitions.find(from);

        if (it == transitions.end()) {
            return false;
        }

        const auto& allowed = it->second;

        return find(allowed.begin(), allowed.end(), to)
               != allowed.end();
    }

public:
    Connection(
        Endpoint source,
        Endpoint destination,
        Protocol transport
    ) : local(move(source)),
        remote(move(destination)),
        protocol(transport),
        state(ConnectionState::CLOSED) {}

    void transition(ConnectionState next) {
        if (!validTransition(state, next)) {
            throw logic_error(
                "Invalid transition: " +
                toString(state) + " -> " +
                toString(next)
            );
        }

        cout << toString(state)
             << " -> "
             << toString(next)
             << '\n';

        state = next;
    }

    void establish() {
        if (protocol != Protocol::TCP) {
            throw logic_error(
                "UDP does not establish TCP-style connections."
            );
        }

        transition(ConnectionState::SYN_SENT);
        cout << "SYN transmitted.\n";

        transition(ConnectionState::SYN_RECEIVED);
        cout << "SYN-ACK received.\n";

        transition(ConnectionState::ESTABLISHED);
        cout << "ACK transmitted. Connection established.\n";
    }

    void close() {
        if (protocol != Protocol::TCP) {
            throw logic_error("TCP close is not applicable to UDP.");
        }

        transition(ConnectionState::FIN_WAIT);
        cout << "FIN transmitted.\n";

        transition(ConnectionState::TIME_WAIT);
        cout << "Waiting for delayed segments to expire.\n";

        transition(ConnectionState::CLOSED);
    }

    ConnectionState getState() const {
        return state;
    }

    string description() const {
        return toString(protocol) + " " +
               local.toString() + " -> " +
               remote.toString();
    }
};

class PortRegistry {
private:
    map<pair<string, uint16_t>, Protocol> bindings;

public:
    void bind(const Endpoint& endpoint, Protocol protocol) {
        auto key = make_pair(endpoint.ip, endpoint.port);

        if (endpoint.port == 0) {
            throw invalid_argument(
                "Port zero cannot represent a listening endpoint."
            );
        }

        if (bindings.count(key)) {
            throw runtime_error("Address and port already bound.");
        }

        bindings.emplace(key, protocol);

        cout << "Bound " << toString(protocol)
             << " to " << endpoint.toString() << '\n';
    }

    void unbind(const Endpoint& endpoint) {
        auto key = make_pair(endpoint.ip, endpoint.port);

        if (bindings.erase(key) == 0) {
            throw runtime_error("Port binding not found.");
        }
    }

    bool isBound(const Endpoint& endpoint) const {
        return bindings.count(
            make_pair(endpoint.ip, endpoint.port)
        ) > 0;
    }
};

class TransportEngine {
private:
    PortRegistry registry;

public:
    void demonstratePorts() {
        cout << "\n--- Port Management ---\n";

        registry.bind(
            Endpoint("192.168.1.10", 443),
            Protocol::TCP
        );

        registry.bind(
            Endpoint("192.168.1.10", 53),
            Protocol::UDP
        );

        cout << "HTTPS endpoint bound: "
             << boolalpha
             << registry.isBound(
                    Endpoint("192.168.1.10", 443)
                )
             << '\n';
    }

    void demonstrateConnections() {
        cout << "\n--- TCP Connection ---\n";

        Connection connection(
            Endpoint("192.168.1.10", 52000),
            Endpoint("192.168.1.20", 443),
            Protocol::TCP
        );

        cout << connection.description() << '\n';

        connection.establish();
        connection.close();

        cout << "\n--- UDP Communication Model ---\n";

        Connection udp(
            Endpoint("192.168.1.10", 52001),
            Endpoint("192.168.1.20", 53),
            Protocol::UDP
        );

        cout << udp.description() << '\n';
        cout << "Datagrams are sent without a TCP handshake.\n";
    }

    void demonstrateFlowControl() {
        cout << "\n--- TCP Flow Control ---\n";

        FlowControlEngine engine(10);

        engine.send("123456");
        engine.send("ABCD");
        engine.send("XYZ");

        engine.acknowledge(6);

        engine.send("XYZ");

        engine.acknowledge(13);

        engine.advertiseWindow(12);

        engine.send("PAYLOAD");

        engine.retransmitExpired(10000, 1000);
    }

    void demonstrateFailures() {
        cout << "\n--- Failure Handling ---\n";

        try {
            Endpoint invalid("192.168.1.10", 70000);
        } catch (const exception& error) {
            cout << "Invalid endpoint: "
                 << error.what() << '\n';
        }

        try {
            FlowControlEngine engine(5);
            engine.send("TOOLONG");
        } catch (const exception& error) {
            cout << "Flow control failure: "
                 << error.what() << '\n';
        }

        try {
            Connection connection(
                Endpoint("127.0.0.1", 50000),
                Endpoint("127.0.0.1", 443),
                Protocol::TCP
            );

            connection.transition(
                ConnectionState::ESTABLISHED
            );
        } catch (const exception& error) {
            cout << "State validation failure: "
                 << error.what() << '\n';
        }
    }
};

int main() {
    try {
        cout << "TRANSPORT LAYER GOVERNANCE ENGINE\n";

        TransportEngine engine;

        engine.demonstratePorts();
        engine.demonstrateConnections();
        engine.demonstrateFlowControl();
        engine.demonstrateFailures();

        cout << "\nExecution completed successfully.\n";

    } catch (const exception& error) {
        cerr << "Fatal error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
