#include <algorithm>
#include <cassert>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

constexpr uint32_t MSS = 1000;
constexpr uint32_t MAX_WINDOW = 65535;

enum class ConnectionState {
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
};

enum class CongestionState {
    SLOW_START,
    CONGESTION_AVOIDANCE,
    FAST_RECOVERY
};

enum class SegmentFlag {
    SYN,
    ACK,
    FIN,
    DATA
};

struct Segment {
    uint32_t sequence = 0;
    uint32_t acknowledgment = 0;
    uint32_t payloadLength = 0;
    vector<SegmentFlag> flags;

    uint32_t sequenceLength() const {
        return payloadLength
            + (find(flags.begin(), flags.end(), SegmentFlag::SYN)
               != flags.end())
            + (find(flags.begin(), flags.end(), SegmentFlag::FIN)
               != flags.end());
    }
};

struct TransmissionStatistics {
    uint64_t sent = 0;
    uint64_t acknowledgedBytes = 0;
    uint64_t retransmissions = 0;
    uint64_t duplicateAcks = 0;
    uint64_t timeouts = 0;
    uint64_t dropped = 0;
};

struct OutstandingData {
    Segment segment;
    uint64_t sentAt = 0;
    bool retransmitted = false;
};

class CongestionController {
private:
    double cwnd = 1.0;
    double ssthresh = 16.0;
    CongestionState state = CongestionState::SLOW_START;

public:
    void acknowledge() {
        if (state == CongestionState::SLOW_START) {
            cwnd += 1.0;

            if (cwnd >= ssthresh) {
                state = CongestionState::CONGESTION_AVOIDANCE;
            }
        } else if (state == CongestionState::CONGESTION_AVOIDANCE) {
            cwnd += 1.0 / cwnd;
        } else {
            cwnd = ssthresh;
            state = CongestionState::CONGESTION_AVOIDANCE;
        }
    }

    void tripleDuplicateAck() {
        ssthresh = max(cwnd / 2.0, 2.0);
        cwnd = ssthresh + 3.0;
        state = CongestionState::FAST_RECOVERY;
    }

    void timeout() {
        ssthresh = max(cwnd / 2.0, 2.0);
        cwnd = 1.0;
        state = CongestionState::SLOW_START;
    }

    double window() const {
        return cwnd;
    }

    double threshold() const {
        return ssthresh;
    }

    CongestionState getState() const {
        return state;
    }
};

class RTTEstimator {
private:
    optional<double> srtt;
    optional<double> rttvar;
    double rto = 1000.0;

public:
    void observe(double sample) {
        if (sample <= 0.0) {
            throw invalid_argument("RTT sample must be positive.");
        }

        if (!srtt.has_value()) {
            srtt = sample;
            rttvar = sample / 2.0;
        } else {
            double variation = abs(*srtt - sample);

            *rttvar = 0.75 * *rttvar + 0.25 * variation;
            *srtt = 0.875 * *srtt + 0.125 * sample;
        }

        rto = clamp(
            *srtt + 4.0 * *rttvar,
            200.0,
            60000.0
        );
    }

    void backoff() {
        rto = min(rto * 2.0, 60000.0);
    }

    double getRTO() const {
        return rto;
    }

    optional<double> getSRTT() const {
        return srtt;
    }
};

class TCPConnection {
private:
    string name;

    uint32_t iss;
    uint32_t sndUna;
    uint32_t sndNxt;
    uint32_t rcvNxt;

    uint32_t mss;
    uint32_t receiverWindow;

    uint32_t duplicateAcks = 0;

    ConnectionState state = ConnectionState::CLOSED;

    CongestionController congestion;
    RTTEstimator rtt;

    map<uint32_t, OutstandingData> outstanding;

    TransmissionStatistics statistics;

public:
    TCPConnection(
        string connectionName,
        uint32_t initialSequence,
        uint32_t maximumSegmentSize = MSS,
        uint32_t receiveWindow = MAX_WINDOW
    )
        : name(move(connectionName)),
          iss(initialSequence),
          sndUna(initialSequence),
          sndNxt(initialSequence),
          rcvNxt(0),
          mss(maximumSegmentSize),
          receiverWindow(receiveWindow) {

        if (mss == 0 || receiverWindow > MAX_WINDOW) {
            throw invalid_argument("Invalid TCP configuration.");
        }
    }

    void establish(TCPConnection& peer) {
        if (state != ConnectionState::CLOSED) {
            throw logic_error("Sender must be closed.");
        }

        if (
            peer.state != ConnectionState::CLOSED &&
            peer.state != ConnectionState::LISTEN
        ) {
            throw logic_error("Peer cannot accept connection.");
        }

        state = ConnectionState::SYN_SENT;
        peer.state = ConnectionState::LISTEN;

        Segment syn;
        syn.sequence = sndNxt;
        syn.flags = {SegmentFlag::SYN};

        sndNxt++;

        statistics.sent++;

        cout << name << " -> " << peer.name
             << " SYN seq=" << syn.sequence << '\n';

        peer.rcvNxt = syn.sequence + 1;
        peer.iss = peer.sndNxt;
        peer.sndUna = peer.iss;
        peer.sndNxt++;

        peer.state = ConnectionState::SYN_RECEIVED;

        Segment synAck;
        synAck.sequence = peer.iss;
        synAck.acknowledgment = peer.rcvNxt;
        synAck.flags = {SegmentFlag::SYN, SegmentFlag::ACK};

        peer.statistics.sent++;

        cout << peer.name << " -> " << name
             << " SYN-ACK seq=" << synAck.sequence
             << " ack=" << synAck.acknowledgment << '\n';

        rcvNxt = synAck.sequence + 1;
        sndUna = synAck.acknowledgment;

        Segment ack;
        ack.sequence = sndNxt;
        ack.acknowledgment = rcvNxt;
        ack.flags = {SegmentFlag::ACK};

        statistics.sent++;

        peer.sndUna = ack.acknowledgment;

        state = ConnectionState::ESTABLISHED;
        peer.state = ConnectionState::ESTABLISHED;

        cout << name << " -> " << peer.name
             << " ACK ack=" << ack.acknowledgment << '\n';

        cout << "Connection established.\n";
    }

    uint32_t sendData(
        uint32_t bytes,
        uint64_t timestamp,
        bool packetDropped = false
    ) {
        if (state != ConnectionState::ESTABLISHED) {
            throw logic_error("Connection is not established.");
        }

        if (bytes == 0) {
            return 0;
        }

        uint32_t congestionLimit = static_cast<uint32_t>(
            congestion.window() * mss
        );

        uint32_t effectiveWindow = min(
            congestionLimit,
            receiverWindow
        );

        uint32_t inFlight = sndNxt - sndUna;

        uint32_t available =
            effectiveWindow > inFlight
            ? effectiveWindow - inFlight
            : 0;

        uint32_t payload = min({
            bytes,
            mss,
            available
        });

        if (payload == 0) {
            return 0;
        }

        Segment segment;
        segment.sequence = sndNxt;
        segment.acknowledgment = rcvNxt;
        segment.payloadLength = payload;
        segment.flags = {SegmentFlag::ACK, SegmentFlag::DATA};

        outstanding.emplace(
            segment.sequence,
            OutstandingData{segment, timestamp, false}
        );

        sndNxt += payload;
        statistics.sent++;

        cout << "Sending DATA seq=" << segment.sequence
             << " bytes=" << payload << '\n';

        if (packetDropped) {
            statistics.dropped++;
            cout << "Network dropped segment.\n";
        }

        return payload;
    }

    void receiveData(uint32_t sequence, uint32_t bytes) {
        if (sequence == rcvNxt) {
            rcvNxt += bytes;

            cout << "Receiver accepted " << bytes
                 << " bytes. Next expected=" << rcvNxt << '\n';
        } else {
            cout << "Out-of-order segment. Expected="
                 << rcvNxt << ", received=" << sequence << '\n';
        }
    }

    void acknowledge(uint32_t acknowledgment) {
        if (acknowledgment > sndNxt) {
            throw invalid_argument("ACK exceeds transmitted sequence.");
        }

        if (acknowledgment < sndUna) {
            return;
        }

        if (acknowledgment == sndUna) {
            duplicateAcks++;
            statistics.duplicateAcks++;

            if (duplicateAcks == 3) {
                fastRetransmit();
            }

            return;
        }

        uint32_t newlyAcknowledged = acknowledgment - sndUna;

        sndUna = acknowledgment;
        duplicateAcks = 0;

        auto iterator = outstanding.begin();

        while (iterator != outstanding.end()) {
            uint32_t endSequence =
                iterator->first +
                iterator->second.segment.sequenceLength();

            if (endSequence <= acknowledgment) {
                iterator = outstanding.erase(iterator);
            } else {
                ++iterator;
            }
        }

        statistics.acknowledgedBytes += newlyAcknowledged;

        congestion.acknowledge();

        cout << "ACK=" << acknowledgment
             << " acknowledgedBytes=" << newlyAcknowledged
             << " cwnd=" << fixed << setprecision(2)
             << congestion.window() << " MSS\n";
    }

    void fastRetransmit() {
        if (outstanding.empty()) {
            return;
        }

        congestion.tripleDuplicateAck();

        auto& oldest = outstanding.begin()->second;

        oldest.retransmitted = true;
        statistics.retransmissions++;

        cout << "FAST RETRANSMIT seq="
             << oldest.segment.sequence << '\n';
    }

    bool checkTimeout(
        uint64_t currentTime,
        uint64_t timeoutDuration
    ) {
        if (outstanding.empty()) {
            return false;
        }

        auto& oldest = outstanding.begin()->second;

        if (currentTime < oldest.sentAt + timeoutDuration) {
            return false;
        }

        oldest.sentAt = currentTime;
        oldest.retransmitted = true;

        congestion.timeout();
        rtt.backoff();

        statistics.retransmissions++;
        statistics.timeouts++;

        cout << "RTO expired. Retransmitting seq="
             << oldest.segment.sequence << '\n';

        return true;
    }

    void updateRTT(double milliseconds) {
        rtt.observe(milliseconds);
    }

    void terminate(TCPConnection& peer) {
        if (state != ConnectionState::ESTABLISHED) {
            throw logic_error("Cannot terminate non-established connection.");
        }

        state = ConnectionState::FIN_WAIT_1;

        Segment fin;
        fin.sequence = sndNxt;
        fin.flags = {SegmentFlag::FIN, SegmentFlag::ACK};

        sndNxt++;

        statistics.sent++;

        cout << name << " -> " << peer.name << " FIN\n";

        peer.rcvNxt = fin.sequence + 1;
        peer.state = ConnectionState::CLOSE_WAIT;

        sndUna = sndNxt;
        state = ConnectionState::FIN_WAIT_2;

        cout << peer.name << " -> " << name << " ACK\n";

        peer.state = ConnectionState::LAST_ACK;
        peer.sndNxt++;
        peer.sndUna = peer.sndNxt;

        rcvNxt = peer.sndNxt;

        cout << peer.name << " -> " << name << " FIN\n";
        cout << name << " -> " << peer.name << " ACK\n";

        state = ConnectionState::TIME_WAIT;
        peer.state = ConnectionState::CLOSED;
    }

    void report() const {
        cout << "\n--- " << name << " statistics ---\n";

        cout << "State: " << static_cast<int>(state) << '\n';
        cout << "SND.UNA: " << sndUna << '\n';
        cout << "SND.NXT: " << sndNxt << '\n';

        cout << "cwnd: " << congestion.window() << " MSS\n";
        cout << "ssthresh: " << congestion.threshold() << " MSS\n";
        cout << "RTO: " << rtt.getRTO() << " ms\n";

        cout << "Segments sent: " << statistics.sent << '\n';
        cout << "Acknowledged bytes: "
             << statistics.acknowledgedBytes << '\n';
        cout << "Retransmissions: "
             << statistics.retransmissions << '\n';
        cout << "Duplicate ACKs: "
             << statistics.duplicateAcks << '\n';
        cout << "Timeouts: " << statistics.timeouts << '\n';
        cout << "Dropped segments: " << statistics.dropped << '\n';
    }

    uint32_t nextSequence() const {
        return sndNxt;
    }

    uint32_t unacknowledgedSequence() const {
        return sndUna;
    }

    size_t outstandingCount() const {
        return outstanding.size();
    }
};

void demonstrateHandshake() {
    cout << "\n=== THREE-WAY HANDSHAKE ===\n";

    TCPConnection client("Client", 1000);
    TCPConnection server("Server", 5000);

    client.establish(server);

    assert(
        client.nextSequence() == 1001
    );
}

void demonstrateReliability() {
    cout << "\n=== RELIABLE DATA TRANSMISSION ===\n";

    TCPConnection sender("Sender", 1000);
    TCPConnection receiver("Receiver", 5000);

    sender.establish(receiver);

    uint32_t bytes = sender.sendData(800, 1000);

    assert(bytes == 800);

    sender.acknowledge(sender.nextSequence());

    assert(sender.outstandingCount() == 0);

    sender.report();
}

void demonstrateTimeout() {
    cout << "\n=== RETRANSMISSION TIMEOUT ===\n";

    TCPConnection sender("TimeoutSender", 2000);
    TCPConnection receiver("TimeoutReceiver", 8000);

    sender.establish(receiver);

    sender.sendData(1000, 1000, true);

    bool retransmitted = sender.checkTimeout(3000, 1000);

    assert(retransmitted);

    sender.report();
}

void demonstrateRTT() {
    cout << "\n=== RTT ESTIMATION ===\n";

    RTTEstimator estimator;

    vector<double> samples = {
        120, 150, 110, 180, 140
    };

    for (double sample : samples) {
        estimator.observe(sample);

        cout << "RTT sample=" << sample
             << " ms, RTO=" << estimator.getRTO()
             << " ms\n";
    }
}

void demonstrateFastRetransmit() {
    cout << "\n=== FAST RETRANSMISSION ===\n";

    TCPConnection sender("FastSender", 3000);
    TCPConnection receiver("FastReceiver", 9000);

    sender.establish(receiver);

    sender.sendData(1000, 1000);

    uint32_t expected = sender.unacknowledgedSequence();

    sender.acknowledge(expected);
    sender.acknowledge(expected);
    sender.acknowledge(expected);

    sender.report();
}

int main() {
    try {
        cout << "TCP DEEP DIVE - C++17\n";

        demonstrateHandshake();
        demonstrateReliability();
        demonstrateTimeout();
        demonstrateRTT();
        demonstrateFastRetransmit();

        cout << "\nAll TCP demonstrations completed.\n";
    } catch (const exception& error) {
        cerr << "TCP error: " << error.what() << '\n';
        return 1;
    }

    return 0;
}
