# TCP Deep Dive: Three-Way Handshake, Congestion Control, Retransmission and Reliability

## 1. Technical Scope

Transmission Control Protocol (TCP) is a connection-oriented transport-layer protocol that provides reliable, ordered, byte-stream communication between applications operating across IP networks.

TCP operates above IP and provides services that IP alone does not guarantee.

IP delivers datagrams using a best-effort delivery model. Packets may be lost, duplicated, delayed, or delivered out of order. TCP addresses these conditions through sequence numbers, acknowledgments, retransmission, flow control, congestion control, and connection-state management.

The implementations in this project demonstrate TCP behavior using five complementary perspectives:

| Implementation | Engineering perspective |
|---|---|
| Python | Transport-state simulation and algorithmic behavior |
| JavaScript | Event-driven networking and asynchronous packet processing |
| C++17 | Efficient sequence tracking and congestion-control modeling |
| Java 17 | Enterprise-oriented domain modeling and connection management |
| PostgreSQL | Relational storage, telemetry, auditing, and reliability reporting |

These implementations are educational transport models. They do not replace the operating system's TCP implementation or generate real TCP packets through network interfaces.

## 2. TCP Architecture

TCP belongs to the transport layer of the Internet protocol architecture.

Its primary responsibilities are:

- Establishing logical connections.
- Maintaining byte-stream ordering.
- Detecting missing data through acknowledgment information.
- Recovering from packet loss.
- Preventing receiver-buffer overflow.
- Controlling transmission according to network congestion.
- Managing connection establishment and termination.

### TCP and IP distinction

| Characteristic | IP | TCP |
|---|---|---|
| Protocol layer | Network | Transport |
| Communication model | Datagram | Connection-oriented byte stream |
| Reliability | Best effort | Reliable delivery mechanism |
| Ordering | Not guaranteed | Ordered byte delivery |
| Acknowledgments | Not provided by basic IP | Provided |
| Retransmission | Not provided by basic IP | Provided |
| Flow control | Not provided | Provided |
| Congestion control | Not provided by basic IP | Provided |
| Connection establishment | Not applicable | Three-way handshake |

TCP connections are identified using endpoint addresses and port numbers.

A connection is commonly identified by a four-tuple:

- Source IP address.
- Source port.
- Destination IP address.
- Destination port.

The protocol number identifies TCP at the IP layer.

## 3. TCP Segment Structure

TCP communicates through segments carried inside IP packets.

A TCP segment contains a header and an optional application-data payload.

| Header field | Purpose |
|---|---|
| Source port | Identifies the sending application endpoint |
| Destination port | Identifies the receiving application endpoint |
| Sequence number | Identifies the first byte represented by the segment |
| Acknowledgment number | Identifies the next byte expected |
| Data offset | Specifies TCP header length |
| Control flags | Indicate connection and transmission conditions |
| Window size | Advertises receiver capacity |
| Checksum | Detects corruption in the TCP segment and pseudo-header |
| Urgent pointer | Supports urgent-data semantics |
| Options | Support MSS, window scaling, timestamps, and other features |
| Payload | Contains application data |

The minimum TCP header is 20 bytes. TCP options can increase its size.

### Important TCP flags

| Flag | Function |
|---|---|
| SYN | Initiates connection establishment |
| ACK | Indicates acknowledgment information |
| FIN | Initiates orderly connection termination |
| RST | Resets a connection |
| PSH | Requests prompt delivery of received data to the application |
| URG | Indicates an urgent-data pointer |
| ECE | Participates in ECN signaling |
| CWR | Indicates congestion-window reduction in ECN operation |
| NS | Supports ECN nonce functionality |

The Python, JavaScript, C++17, and Java implementations model the essential SYN, ACK, FIN, and data behavior.

## 4. TCP Three-Way Handshake

The three-way handshake establishes the initial communication state and synchronizes the sequence-number spaces of both endpoints.

It also allows each endpoint to communicate its initial sequence number.

### 4.1 Handshake sequence

Consider a client connecting to a server.

The client chooses an initial sequence number of 1000, while the server chooses 5000.

The exchange is:

1. Client sends SYN.
2. Server responds with SYN-ACK.
3. Client responds with ACK.

Plain-text representation:

Client                         Server

CLOSED                         LISTEN

SYN, Seq=1000  ---------------->

                <-------------- SYN-ACK
                                 Seq=5000
                                 Ack=1001

ACK, Seq=1001 ----------------->
     Ack=5001

ESTABLISHED                     ESTABLISHED

### 4.2 First step: SYN

The client sends a segment with:

- SYN = 1.
- Sequence number = 1000.

The SYN consumes one sequence number.

The client advances its next sequence number to 1001.

The client enters `SYN_SENT`.

### 4.3 Second step: SYN-ACK

The server receives the SYN and responds with:

- SYN = 1.
- ACK = 1.
- Sequence number = 5000.
- Acknowledgment number = 1001.

The acknowledgment confirms receipt of the client's SYN.

The server's SYN also consumes one sequence number.

The server advances its sequence space to 5001 and enters `SYN_RECEIVED`.

### 4.4 Third step: ACK

The client acknowledges the server's SYN:

- ACK = 1.
- Sequence number = 1001.
- Acknowledgment number = 5001.

Both endpoints enter `ESTABLISHED`.

### 4.5 Why three messages are necessary

The exchange establishes that:

- The client can transmit to the server.
- The server can transmit to the client.
- Both endpoints have received the other's initial sequence information.
- Both endpoints can maintain independent sequence-number spaces.

A two-message exchange would not provide the same confirmation that the server's initial sequence number was received by the client.

### 4.6 Initial sequence numbers

TCP uses 32-bit sequence numbers.

Sequence numbers identify positions in a byte stream, rather than packet identifiers.

Initial sequence numbers should be difficult to predict because predictable sequence numbers can facilitate TCP injection and spoofing attacks.

Real implementations also account for sequence-number wraparound.

The simplified programs use integer sequence spaces to demonstrate the underlying mechanics.

## 5. TCP Connection State Machine

TCP maintains a state machine to control connection establishment, communication, and termination.

| State | Meaning |
|---|---|
| CLOSED | No active connection |
| LISTEN | Waiting for an incoming connection |
| SYN_SENT | Connection initiation transmitted |
| SYN_RECEIVED | Initial SYN received and SYN-ACK transmitted |
| ESTABLISHED | Bidirectional communication available |
| FIN_WAIT_1 | Local endpoint initiated termination |
| FIN_WAIT_2 | Local FIN acknowledged |
| CLOSE_WAIT | Remote endpoint initiated termination |
| LAST_ACK | Waiting for acknowledgment of local FIN |
| TIME_WAIT | Waiting to ensure delayed segments cannot interfere with future connections |

### Important distinctions

`SYN_SENT` and `SYN_RECEIVED` belong to connection establishment.

`ESTABLISHED` represents the normal data-transfer state.

`FIN_WAIT_1`, `FIN_WAIT_2`, `CLOSE_WAIT`, and `LAST_ACK` represent different stages of orderly connection termination.

`TIME_WAIT` protects against delayed segments from an earlier connection instance.

The full TCP state machine also includes states and transitions not exhaustively represented by the educational simulations.

## 6. Sequence Numbers and Acknowledgments

TCP provides reliable byte-stream delivery using sequence numbers and acknowledgments.

### 6.1 Sequence numbers

Suppose a sender transmits three segments:

| Segment | Starting sequence | Payload size |
|---|---:|---:|
| A | 1001 | 1000 bytes |
| B | 2001 | 1000 bytes |
| C | 3001 | 500 bytes |

The receiver expects bytes beginning at sequence 1001.

After receiving segment A, the receiver expects sequence 2001.

After receiving segment B, it expects sequence 3001.

After receiving segment C, it expects sequence 3501.

### 6.2 Cumulative acknowledgments

An acknowledgment number identifies the next byte expected.

If a receiver sends:

`ACK = 2001`

It indicates that all bytes before sequence 2001 have been received in order.

Cumulative acknowledgments allow one acknowledgment to confirm multiple contiguous segments.

### 6.3 Out-of-order data

Suppose a receiver expects sequence 2001 but receives sequence 3001.

The receiver cannot advance its cumulative acknowledgment beyond the missing data.

It continues acknowledging sequence 2001.

The sender can use repeated acknowledgments to detect possible loss.

TCP implementations may buffer out-of-order data and use Selective Acknowledgment (SACK) information to identify successfully received ranges.

The educational receivers primarily demonstrate contiguous-data acceptance and cumulative ACK behavior.

### 6.4 Sequence-number wraparound

TCP sequence numbers use a 32-bit unsigned sequence space.

The sequence number after 4,294,967,295 wraps to zero.

Comparisons must use serial-number arithmetic rather than ordinary unbounded integer comparison.

The implementations use simplified integer arithmetic and do not implement production-grade 32-bit wraparound handling.

## 7. TCP Reliability Mechanisms

TCP reliability depends on several interacting mechanisms.

| Mechanism | Responsibility |
|---|---|
| Sequence numbers | Identify byte positions |
| Acknowledgments | Confirm received data |
| Checksum | Detect corruption |
| Retransmission | Recover from missing data |
| RTO | Determine when retransmission may be necessary |
| Duplicate ACK detection | Detect possible missing segments |
| Sliding window | Permit multiple bytes to remain in flight |
| SACK | Communicate selectively received data ranges |

### 7.1 Retransmission

A sender retains information about unacknowledged segments.

When the expected acknowledgment does not arrive within the retransmission timeout, the sender may retransmit the missing data.

Example:

Sender                         Receiver

DATA Seq=1001 ----------------> Lost

DATA Seq=1001 ----------------> Retransmission

                <-------------- ACK=2001

The sender removes acknowledged data from its outstanding-data tracking structure.

### 7.2 Retransmission timeout

The Retransmission Timeout (RTO) is the time threshold used to detect potentially lost data.

A timeout does not prove that a packet was lost.

It indicates that the sender has not received the expected acknowledgment within the calculated interval.

Network congestion, delayed packets, and acknowledgment loss can also cause timeout expiration.

### 7.3 RTT measurement

Round-Trip Time (RTT) measures the time between transmitting a segment and receiving the corresponding acknowledgment.

TCP estimates RTT to adapt retransmission timing to network conditions.

The smoothed RTT calculation uses:

`SRTT = (1 - α) × SRTT + α × RTT_sample`

A commonly used value is:

`α = 0.125`

RTT variation is estimated using:

`RTTVAR = (1 - β) × RTTVAR + β × |SRTT_previous - RTT_sample|`

A commonly used value is:

`β = 0.25`

The retransmission timeout is calculated using:

`RTO = SRTT + 4 × RTTVAR`

Actual TCP implementations also apply minimum and maximum RTO bounds and account for retransmission backoff.

### 7.4 Exponential backoff

Repeated timeout expiration indicates that the network may be experiencing significant congestion or disruption.

The sender increases the retransmission timeout.

A simplified calculation is:

`New RTO = min(2 × Previous RTO, Maximum RTO)`

This reduces the frequency of retransmission attempts during persistent network problems.

### 7.5 Karn's algorithm

RTT samples obtained from retransmitted segments can be ambiguous.

If an acknowledgment arrives after retransmission, the sender may not know whether it corresponds to the original transmission or the retransmission.

Karn's algorithm avoids using ambiguous retransmission samples for RTT estimation.

The JavaScript implementation also avoids sampling retransmitted segments.

## 8. Fast Retransmission

TCP can detect likely segment loss before the retransmission timeout expires.

The traditional fast retransmission mechanism uses three duplicate acknowledgments.

Consider the following transmission:

Sender                         Receiver

Segment A --------------------> Received

Segment B --------------------> Lost

Segment C --------------------> Received

Segment D --------------------> Received

ACK for next expected byte <---

Duplicate ACK                 <---

Duplicate ACK                 <---

Duplicate ACK                 <---

Fast retransmission of B ---->

The repeated acknowledgment indicates that the receiver continues expecting the missing byte range.

After three duplicate ACKs, the sender can retransmit the presumed missing segment.

This improves recovery speed compared with waiting for the retransmission timeout.

Duplicate ACKs are evidence of possible loss, not definitive proof of it.

Reordering and other network conditions can also produce duplicate acknowledgments.

## 9. TCP Flow Control

Flow control prevents a sender from overwhelming the receiver.

TCP uses the advertised receive window, commonly represented as `rwnd`.

The receiver communicates how much additional data it can accept.

### 9.1 Receive window

Suppose:

- Receiver buffer capacity is 64,000 bytes.
- Data currently occupying the buffer is 16,000 bytes.

The remaining advertised capacity may be:

`rwnd = 64,000 - 16,000`

`rwnd = 48,000 bytes`

The sender must respect the advertised receive capacity.

A zero receive window indicates that the receiver currently cannot accept additional data.

TCP uses zero-window probing mechanisms to detect when the receiver becomes able to accept data again.

### 9.2 Sliding window

The sliding-window mechanism allows a sender to transmit multiple bytes without waiting for an individual acknowledgment after every segment.

The sender tracks:

- `SND.UNA`: oldest unacknowledged sequence number.
- `SND.NXT`: next sequence number to transmit.
- `RCV.NXT`: next expected sequence number at the receiver.
- `rwnd`: advertised receiver window.

The outstanding data is:

`Bytes in flight = SND.NXT - SND.UNA`

The receiver-window constraint limits additional transmission.

## 10. TCP Congestion Control

Flow control and congestion control solve different problems.

Flow control protects the receiver.

Congestion control protects the network from excessive traffic.

TCP congestion control adjusts the amount of unacknowledged data that can remain in flight.

The principal congestion-control variables are:

| Variable | Meaning |
|---|---|
| `cwnd` | Congestion window |
| `ssthresh` | Slow-start threshold |
| `rwnd` | Receiver-advertised window |
| `MSS` | Maximum Segment Size |
| `bytes_in_flight` | Outstanding transmitted data |

A simplified sending-window constraint is:

`Effective sending window = min(cwnd, rwnd)`

The actual TCP implementation also considers bytes already in flight, recovery state, pacing, and other protocol conditions.

### 10.1 Slow start

Slow start increases the congestion window rapidly when acknowledgments arrive.

A simplified educational model starts with:

`cwnd = 1 MSS`

Each acknowledgment of one MSS increases the congestion window by approximately one MSS.

Under ideal acknowledgment behavior, the window grows approximately exponentially per RTT.

| RTT round | Congestion window |
|---|---:|
| Initial | 1 MSS |
| 1 | 2 MSS |
| 2 | 4 MSS |
| 3 | 8 MSS |
| 4 | 16 MSS |

Growth continues until the slow-start threshold or another congestion-control condition is reached.

Modern TCP implementations may use different initial-window and congestion-control algorithms.

### 10.2 Congestion avoidance

When the congestion window reaches the slow-start threshold, the sender enters congestion avoidance.

A simplified additive-increase rule is:

`cwnd = cwnd + MSS² / cwnd`

For an acknowledgment covering one MSS, this is approximately:

`cwnd = cwnd + 1 / cwnd`

when the window is measured in MSS units.

This produces approximately linear growth over each RTT.

### 10.3 Congestion detection

TCP can infer congestion from:

- Retransmission timeouts.
- Duplicate acknowledgments.
- Explicit Congestion Notification (ECN).
- Other congestion signals supported by the congestion-control algorithm.

Packet loss can indicate congestion, but not every loss is necessarily caused by congestion.

### 10.4 Multiplicative decrease

After a congestion signal, the sender reduces its congestion window.

A simplified model uses:

`ssthresh = max(cwnd / 2, 2 MSS)`

The exact response depends on the congestion-control algorithm and the type of congestion signal.

### 10.5 Fast recovery

Fast recovery allows a sender to respond to detected packet loss without necessarily returning immediately to the initial congestion window.

In the traditional Reno-style model:

- Three duplicate ACKs indicate likely loss.
- The slow-start threshold is reduced.
- The congestion window is temporarily adjusted.
- The missing segment is retransmitted.
- Recovery continues as acknowledgments arrive.

The C++17 and Java implementations explicitly model slow start, congestion avoidance, and fast recovery as separate states.

### 10.6 Timeout response

A retransmission timeout generally causes a stronger congestion response than a triple-duplicate-ACK event.

The educational models reset the congestion window to one MSS and enter slow start.

Production TCP congestion-control behavior depends on the selected algorithm and implementation.

## 11. Flow Control Versus Congestion Control

These mechanisms must not be treated as interchangeable.

| Characteristic | Flow control | Congestion control |
|---|---|---|
| Protected resource | Receiver buffer | Network capacity |
| Main variable | `rwnd` | `cwnd` |
| Feedback source | Receiver | Network congestion signals |
| Objective | Avoid receiver overflow | Avoid excessive network load |
| Typical limitation | Receiver processing and memory | Network bandwidth and queue capacity |
| Zero window | Possible | Not equivalent to congestion window reduction |

The effective sending window is constrained by both mechanisms.

A sender may have available congestion capacity but still be limited by the receiver window.

Likewise, a receiver may advertise a large window while the sender remains constrained by congestion control.

## 12. Connection Termination

TCP supports orderly termination using FIN and ACK segments.

Each direction of a TCP connection is closed independently.

Consequently, one endpoint can stop sending while continuing to receive data.

### 12.1 Four-segment termination

A common termination sequence is:

Client                         Server

FIN -------------------------->

                <-------------- ACK

                <-------------- FIN

ACK -------------------------->

The active closer generally enters:

`FIN_WAIT_1 → FIN_WAIT_2 → TIME_WAIT`

The passive closer generally enters:

`CLOSE_WAIT → LAST_ACK → CLOSED`

The exact transition sequence can vary depending on simultaneous close and acknowledgment timing.

### 12.2 TIME_WAIT

TIME_WAIT is important for two reasons:

1. It allows delayed segments from an earlier connection to expire.
2. It provides an opportunity to retransmit the final ACK if the peer retransmits its FIN.

The conventional TIME_WAIT duration is twice the Maximum Segment Lifetime (2MSL).

The actual duration and handling depend on operating-system implementation and protocol configuration.

## 13. Python Implementation

The Python file models a TCP endpoint using classes, enumerations, dictionaries, and dataclasses.

### Main components

| Component | Responsibility |
|---|---|
| `TCPConnection` | Endpoint state and sequence management |
| `Segment` | TCP segment representation |
| `NetworkSimulator` | Packet-loss simulation |
| `TCPStatistics` | Transmission statistics |
| `OutstandingSegment` | Unacknowledged transmission tracking |
| `RTTEstimator` logic | Smoothed RTT and RTO calculation |
| `CongestionState` | Congestion-control phase |

### Important implementation decisions

The outstanding-segment dictionary provides efficient sequence-based lookup.

Cumulative ACK processing removes segments whose sequence ranges have been fully acknowledged.

The network simulator introduces configurable packet loss without requiring actual network access.

The connection lifecycle demonstrates handshake establishment and termination.

The implementation also includes assertions to verify successful connection establishment and data acknowledgment.

### Limitations

The Python implementation is a simplified simulator.

It does not implement:

- A complete TCP packet parser.
- TCP checksum calculation.
- Real socket communication.
- Full 32-bit sequence-number wraparound.
- SACK-based recovery.
- Production-grade retransmission timer scheduling.
- Complete RFC-compliant TCP state transitions.

## 14. JavaScript Implementation

The JavaScript implementation uses an event-driven architecture.

It emphasizes asynchronous packet delivery and separation of networking responsibilities.

### Main components

| Component | Responsibility |
|---|---|
| `NetworkLink` | Simulated asynchronous network |
| `TCPSender` | Transmission and acknowledgment handling |
| `TCPReceiver` | Receive-side sequence management |
| `RTTEstimator` | Adaptive timeout calculation |
| `CongestionController` | Congestion-window management |
| `TCPConnectionManager` | Connection registration and lookup |
| `TCPError` | Structured transport errors |

### Event-driven behavior

The `NetworkLink` extends Node.js `EventEmitter`.

It emits events when packets are:

- Delivered.
- Dropped.

The sender emits additional events for:

- Successful connection establishment.
- Acknowledgments.
- Packet loss.
- Retransmission.
- Timeout expiration.

This architecture separates protocol-state changes from event consumers.

### Asynchronous transmission

The `transmit()` method returns a Promise.

The sender waits for packet delivery before invoking the receiver.

This allows the simulator to model network latency without blocking the event loop.

### Buffer management

Node.js `Buffer` objects represent binary payloads.

They are more appropriate than ordinary strings for transport-layer data because TCP carries arbitrary bytes.

### Limitations

The JavaScript implementation does not provide a full TCP implementation or a production timer scheduler.

Its retransmission method demonstrates retransmission decisions rather than complete network recovery.

## 15. C++17 Implementation

The C++17 implementation emphasizes explicit transport state and efficient data structures.

### Main components

| Component | Responsibility |
|---|---|
| `TCPConnection` | Endpoint behavior |
| `Segment` | Segment metadata |
| `CongestionController` | Congestion-window adaptation |
| `RTTEstimator` | RTT and RTO estimation |
| `OutstandingData` | Outstanding segment information |
| `TransmissionStatistics` | Reliability measurements |

### Data structures

The implementation uses:

- `std::map` for sequence-ordered outstanding data.
- `std::vector` for segment flags and sample collections.
- `std::optional` for RTT values that may not yet exist.
- `std::enum class` for strongly typed protocol states.

The ordered map allows the oldest outstanding segment to be accessed efficiently.

For a map containing N outstanding segments:

- Lookup: O(log N).
- Insertion: O(log N).
- Deletion: O(log N).
- Access to the oldest segment: O(1) through `begin()`.

### Engineering considerations

C++ provides explicit control over data structures and memory representation.

This is useful when implementing high-throughput networking components.

The implementation uses exceptions for invalid configuration and protocol operations.

It does not include operating-system socket integration or complete TCP wire-format handling.

## 16. Java 17 Implementation

The Java implementation presents TCP as an enterprise-oriented domain model.

It uses typed records, enumerations, service-like classes, and a connection registry.

### Main components

| Component | Responsibility |
|---|---|
| `TCPEndpoint` | Endpoint lifecycle |
| `Segment` | Immutable segment representation |
| `ConnectionSnapshot` | Immutable state snapshot |
| `Statistics` | Transmission measurements |
| `CongestionController` | Congestion management |
| `RTTEstimator` | RTT calculation |
| `OutstandingSegment` | Outstanding transmission state |
| `ConnectionRegistry` | Concurrent endpoint registration |

### Domain modeling

Java records represent immutable data structures.

This is useful for segment metadata and connection snapshots because these values represent observations rather than mutable business objects.

Enumerations constrain the available protocol states and congestion-control phases.

The connection registry uses `ConcurrentHashMap` for thread-safe registration and lookup.

`AtomicLong` generates connection identifiers.

### Enterprise considerations

A production transport-monitoring service would require:

- Authenticated endpoint registration.
- Connection lifecycle auditing.
- Controlled telemetry ingestion.
- Structured error reporting.
- Concurrency-safe state transitions.
- Bounded resource usage.
- Monitoring and operational alerting.

The implementation demonstrates selected domain and concurrency patterns rather than a complete production TCP server.

## 17. PostgreSQL Implementation

The PostgreSQL implementation stores TCP connection and reliability telemetry in a relational schema.

It separates connection-level information from individual segment observations and congestion-control measurements.

### Relational structure

Endpoints
    |
    | 1:N
    |
TCP Connections
    |
    | 1:N
    |
TCP Segments

TCP Connections
    |
    | 1:N
    |
Congestion Observations

TCP Connections
    |
    | 1:N
    |
Connection Events

### Tables

| Table | Purpose |
|---|---|
| `endpoints` | Stores network endpoint information |
| `tcp_connections` | Stores connection state and sequence information |
| `tcp_segments` | Stores segment-level transmission history |
| `congestion_observations` | Stores congestion-control measurements |
| `connection_events` | Maintains state-transition and operational history |

### Referential integrity

Primary keys uniquely identify database records.

Foreign keys ensure that segments and observations reference valid connections.

Check constraints enforce valid ports, sequence values, MSS values, receiver windows, and retransmission counters.

### State-transition enforcement

The `validate_tcp_transition()` trigger function checks permitted connection-state transitions.

Invalid transitions generate database exceptions.

The `audit_tcp_state_change()` trigger records state changes automatically.

This supports historical investigation and operational auditing.

### Stored procedures

The SQL implementation includes procedures and functions for:

- Creating connections.
- Processing the three-way handshake.
- Recording data transmissions.
- Processing cumulative acknowledgments.
- Recording congestion observations.
- Marking segments as retransmitted.

The `FOR UPDATE` locking mechanism protects connection-state updates against conflicting concurrent operations.

### Reporting

The `connection_reliability` view provides segment and acknowledgment statistics.

The `congestion_report` view aggregates congestion-window, RTT, RTO, and congestion-phase measurements.

Additional queries identify retransmission activity, packet-loss observations, and transmission eligibility.

### Transaction management

The complete demonstration uses a transaction.

This ensures that sample records, state transitions, and telemetry operations are committed together.

A failed transaction can be rolled back rather than leaving partially applied sample data.

### Production database considerations

A real packet telemetry system can generate substantial write volume.

A production deployment should consider:

- Time-based partitioning of segment tables.
- Retention and archival policies.
- Appropriate indexing for connection and time-based queries.
- Restricted database privileges.
- Authenticated ingestion.
- Connection-level access controls.
- Monitoring of index and table growth.
- Batched telemetry insertion.

The SQL schema stores analytical observations. It does not independently implement the TCP transport protocol.

## 18. Reliability and Performance Metrics

TCP performance should be evaluated using multiple measurements.

| Metric | Meaning | Operational relevance |
|---|---|---|
| RTT | Round-trip communication delay | Latency |
| SRTT | Smoothed RTT | Timeout estimation |
| RTTVAR | RTT variation | Network stability |
| RTO | Retransmission timeout | Loss recovery |
| MSS | Maximum Segment Size | Payload sizing |
| cwnd | Congestion window | Congestion control |
| rwnd | Receiver window | Flow control |
| Retransmission count | Repeated transmissions | Reliability and congestion investigation |
| Duplicate ACK count | Repeated cumulative ACKs | Possible loss detection |
| Bytes in flight | Unacknowledged transmitted data | Transmission utilization |
| Goodput | Useful application data delivered per unit time | Application performance |

### Throughput and bandwidth

Bandwidth represents the available transmission capacity.

Throughput represents the actual data-transfer rate.

Goodput measures useful application data delivered, excluding retransmitted data and protocol overhead.

A high-bandwidth connection can still achieve poor throughput because of:

- High RTT.
- Packet loss.
- Small congestion windows.
- Receiver limitations.
- Network congestion.
- Inefficient application transmission patterns.

### Bandwidth-delay product

The bandwidth-delay product estimates the amount of data required in flight to fully utilize a network path.

`BDP = Bandwidth × RTT`

For example:

- Bandwidth = 100 Mbps.
- RTT = 100 milliseconds.

`BDP = 100,000,000 × 0.1 / 8`

`BDP = 1,250,000 bytes`

Approximately 1.25 MB of data must be in flight to fully utilize the path under these assumptions.

A congestion window smaller than the bandwidth-delay product can restrict throughput.

## 19. Security Considerations

TCP provides reliable transport, not application confidentiality or authentication.

Important security concerns include:

| Threat | Description | Relevant protection |
|---|---|---|
| SYN flood | Large volumes of incomplete connection requests | SYN cookies, rate limiting, resource controls |
| TCP spoofing | Forged source addresses or transport information | Network filtering, unpredictable sequence numbers |
| TCP injection | Unauthorized insertion of data into a connection | Strong endpoint and transport security |
| Sequence prediction | Predictable sequence values exploited by attackers | Secure sequence-number generation |
| RST injection | Forged reset segments interrupt communication | RFC-compliant reset validation and protected connections |
| Session hijacking | Unauthorized interference with an established session | Authentication and encryption |
| Traffic analysis | Observation of communication patterns | Appropriate network-level privacy controls |
| Resource exhaustion | Excessive connection or buffer consumption | Connection limits and monitoring |

TLS can provide confidentiality, integrity, and endpoint authentication for application communication when correctly configured.

TCP checksums detect certain accidental transmission errors but do not provide cryptographic integrity.

SYN cookies help reduce server resource consumption during SYN flood conditions.

ECN provides congestion signaling without requiring packet loss as the signal.

## 20. Important Protocol Distinctions

Several concepts frequently appear together but perform different functions.

| Concept | Primary purpose |
|---|---|
| Three-way handshake | Establish a connection |
| Sequence number | Identify byte-stream position |
| ACK | Confirm received sequence space |
| Retransmission | Recover missing data |
| RTO | Detect potentially missing data through elapsed time |
| Fast retransmission | Recover likely loss using duplicate ACKs |
| Sliding window | Permit outstanding data |
| Flow control | Protect receiver capacity |
| Congestion control | Manage network load |
| RTT estimation | Measure and smooth communication delay |
| FIN | Initiate orderly directional closure |
| TIME_WAIT | Protect against delayed segments |

These mechanisms operate together to provide reliable transport.

None independently provides all TCP reliability guarantees.

## 21. Practical Execution

### Python

- Save the first source block as `tcp_deep_dive.py`.
- Execute using `python tcp_deep_dive.py`.
- Inspect handshake, transmission, retransmission, RTT, and connection-state output.

### JavaScript

- Save the second source block as `tcp_deep_dive.js`.
- Execute using `node tcp_deep_dive.js`.
- Observe asynchronous packet delivery and event-driven connection behavior.

### C++17

- Save the third source block as `tcp_deep_dive.cpp`.
- Compile using `g++ -std=c++17 -O2 -Wall -Wextra -pedantic tcp_deep_dive.cpp -o tcp_deep_dive`.
- Execute using `./tcp_deep_dive` or `tcp_deep_dive.exe` on Windows.

### Java 17

- Save the fourth source block as `TCPDeepDive.java`.
- Compile using `javac TCPDeepDive.java`.
- Execute using `java TCPDeepDive`.

### PostgreSQL

- Save the fifth source block as `tcp_deep_dive.sql`.
- Execute against a PostgreSQL 15 or later database using `psql -d your_database -f tcp_deep_dive.sql`.
- The script creates the `tcp_lab` schema, domain tables, constraints, triggers, procedures, reporting views, and demonstration records.

The SQL script creates a dedicated schema and commits its sample data. Re-running it against the same database requires handling the existing schema and its objects.

## 22. Implementation Comparison

| Technical capability | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| Three-way handshake | Yes | Yes | Yes | Yes | Yes |
| Sequence tracking | Yes | Yes | Yes | Yes | Yes |
| Cumulative ACK | Yes | Yes | Yes | Yes | Yes |
| Sliding-window model | Yes | Yes | Yes | Yes | Partial |
| RTT estimation | Yes | Yes | Yes | Yes | Stores observations |
| Retransmission timeout | Yes | Yes | Yes | Yes | Stores retransmission events |
| Fast retransmission | Yes | Yes | Yes | Yes | Records retransmissions |
| Slow start | Yes | Yes | Yes | Yes | Stores observations |
| Congestion avoidance | Yes | Yes | Yes | Yes | Stores observations |
| Fast recovery | Yes | Yes | Yes | Yes | Stores observations |
| Flow control | Yes | Yes | Yes | Yes | Yes |
| Connection termination | Yes | Yes | Yes | Yes | State transitions |
| Event auditing | Console | EventEmitter | Console | Snapshots | Trigger-based |
| Persistent storage | No | No | No | No | Yes |

## 23. Technical Limitations

The five implementations model selected TCP mechanisms rather than implementing the complete TCP specification.

Important omitted production mechanisms include:

- Full TCP option negotiation.
- Selective Acknowledgment (SACK) block processing.
- Window scaling negotiation.
- TCP timestamps and PAWS.
- Complete 32-bit sequence-number wraparound.
- Delayed acknowledgment behavior.
- Persist timer and complete zero-window probing.
- Nagle's algorithm.
- TCP segmentation offload.
- Explicit Congestion Notification negotiation.
- Production-grade pacing.
- Complete simultaneous-open and simultaneous-close handling.
- Modern congestion-control algorithms such as CUBIC and BBR.
- Full TCP checksum and packet-header processing.

The congestion-control examples intentionally use simplified educational rules.

Actual TCP implementations have evolved beyond basic Reno-style behavior. Their congestion-control and loss-recovery mechanisms depend on the operating system, configuration, and negotiated TCP capabilities.

The examples therefore provide an implementation-oriented understanding of TCP's fundamental reliability mechanisms, rather than claiming wire-level protocol compliance.
