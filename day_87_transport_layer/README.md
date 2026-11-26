# Transport Layer Engineering: TCP, UDP, Ports, Connections and Flow Control

## 1. Transport Layer Architecture

The transport layer is responsible for communication between application processes running on different hosts. It operates above the Internet Protocol (IP) layer and provides services that applications use to exchange data.

The transport layer performs several important functions:

- Process-to-process communication.
- Application endpoint identification through port numbers.
- Segmentation and reassembly of application data.
- Reliable data delivery when using TCP.
- Connection management.
- Error detection and recovery mechanisms.
- Flow control.
- Multiplexing and demultiplexing.
- Transmission management.

The two principal transport protocols are:

| Property | TCP | UDP |
|---|---|---|
| Full name | Transmission Control Protocol | User Datagram Protocol |
| Communication | Connection-oriented | Connectionless |
| Reliability | Reliable byte stream | Best-effort datagrams |
| Ordering | Ordered delivery | No ordering guarantee |
| Acknowledgements | Yes | No transport-level ACK |
| Retransmission | Yes | Not provided by UDP |
| Flow control | Yes | No built-in mechanism |
| Congestion control | Yes | No built-in mechanism |
| Data representation | Byte stream | Individual datagrams |
| Header size | Minimum 20 bytes | 8 bytes |
| Typical applications | HTTPS, SSH, email | DNS, streaming, real-time applications |

TCP and UDP provide different communication guarantees. Selecting a protocol depends on application requirements, latency constraints, reliability expectations and network behavior.

## 2. Transport Layer Position in the Network Stack

The transport layer belongs to the TCP/IP networking architecture.

The encapsulation relationship is:

Application Data
    |
    v
Transport Layer
    |
    +---- TCP Segment
    |
    +---- UDP Datagram
    |
    v
Internet Layer
    |
    +---- IP Packet
    |
    v
Network Access Layer
    |
    v
Physical Network Transmission

Each layer adds information required by the next layer.

For example, when an application sends an HTTPS request:

1. The application produces HTTP data.
2. TCP divides the byte stream into segments.
3. TCP adds source and destination port information.
4. IP adds source and destination IP addresses.
5. The network access layer encapsulates the IP packet into a frame.
6. The receiving system processes the information in reverse order.

The transport layer identifies the destination application, while IP identifies the destination host or network interface.

## 3. Port Numbers and Application Identification

A port number is a 16-bit identifier used to identify an application endpoint on a host.

The valid port range is 0 to 65535.

Port zero has special purposes and is not used as a normal listening service port.

### Port classifications

| Range | Classification | Typical purpose |
|---|---|---|
| 0–1023 | Well-known ports | Standard network services |
| 1024–49151 | Registered ports | Registered application services |
| 49152–65535 | Dynamic or private ports | Temporary client connections |

Common services include:

| Port | Protocol | Service |
|---|---|---|
| 20 | TCP | FTP data |
| 21 | TCP | FTP control |
| 22 | TCP | SSH |
| 25 | TCP | SMTP |
| 53 | UDP/TCP | DNS |
| 80 | TCP | HTTP |
| 443 | TCP | HTTPS |
| 67 | UDP | DHCP server |
| 68 | UDP | DHCP client |
| 123 | UDP | NTP |
| 161 | UDP | SNMP |

The protocol is part of the endpoint identification. TCP port 53 and UDP port 53 are separate transport endpoints.

### Socket addressing

A socket endpoint is generally identified using:

- IP address.
- Transport protocol.
- Port number.

For TCP, an established connection is identified by a four-tuple:

Source IP address
Source port
Destination IP address
Destination port

The protocol distinguishes TCP connections from UDP communication.

Multiple client connections can communicate with the same server port because their source addresses and source ports differ.

Example:

| Connection | Source | Destination |
|---|---|---|
| 1 | 192.168.1.10:52000 | 192.168.1.20:443 |
| 2 | 192.168.1.11:52001 | 192.168.1.20:443 |
| 3 | 192.168.1.12:52002 | 192.168.1.20:443 |

The server can accept multiple TCP connections on port 443.

## 4. Transmission Control Protocol

TCP provides reliable, ordered, connection-oriented communication.

Applications use TCP when missing, duplicated or incorrectly ordered data would affect correctness.

Examples include:

- HTTPS communication.
- SSH sessions.
- Database connections.
- File transfers.
- Email transmission.
- Remote application access.

### 4.1 TCP connection establishment

TCP establishes a connection using a three-way handshake.

<escape>CLIENT                         SERVER</escape>
<escape>  |                              |</escape>
<escape>  |---------- SYN -------------->|</escape>
<escape>  |                              |</escape>
<escape>  |<--------- SYN-ACK -----------|</escape>
<escape>  |                              |</escape>
<escape>  |---------- ACK -------------->|</escape>
<escape>  |                              |</escape>
<escape>  |       CONNECTION READY        |</escape>

The three messages perform different functions.

**SYN**

The client requests connection establishment and communicates its initial sequence number.

**SYN-ACK**

The server acknowledges the client's SYN and communicates its own initial sequence number.

**ACK**

The client acknowledges the server's sequence number.

After the handshake, both systems can exchange application data.

TCP sequence numbers and acknowledgements provide the foundation for ordered and reliable transmission.

### 4.2 TCP connection states

TCP maintains connection state to manage communication.

| State | Meaning |
|---|---|
| CLOSED | No active connection |
| LISTEN | Server waiting for connection requests |
| SYN_SENT | Client has transmitted SYN |
| SYN_RECEIVED | SYN received and SYN-ACK transmitted |
| ESTABLISHED | Connection is active |
| FIN_WAIT_1 | Local endpoint initiated closure |
| FIN_WAIT_2 | Local FIN acknowledged |
| CLOSE_WAIT | Remote endpoint initiated closure |
| CLOSING | Both endpoints initiated closure |
| LAST_ACK | Waiting for final acknowledgement |
| TIME_WAIT | Waiting for delayed segments to expire |

The implementations use a simplified state machine for educational simulation. A complete TCP implementation includes additional states and transition conditions.

### 4.3 TCP data transmission

TCP provides a continuous byte stream rather than preserving application message boundaries.

Suppose an application writes 4,000 bytes.

TCP may divide the data into multiple segments depending on:

- Maximum Segment Size (MSS).
- Path Maximum Transmission Unit (PMTU).
- Available congestion window.
- Available receive window.
- Network conditions.
- Operating system implementation.

The receiving TCP implementation reassembles the ordered byte stream before delivering it to the application.

### 4.4 Sequence numbers

TCP assigns sequence numbers to bytes in the transmitted stream.

Suppose the first transmitted data byte has sequence number 1000.

A segment containing 500 bytes covers:

- First byte: 1000.
- Last byte: 1499.
- Next expected byte: 1500.

TCP sequence numbers operate modulo \(2^{32}\).

They allow TCP to identify transmitted data, detect missing portions and reconstruct the original byte stream.

### 4.5 Acknowledgements

An acknowledgement communicates the next byte expected by the receiving endpoint.

If a receiver has successfully received bytes 1000 through 1499, it can acknowledge:

\[
ACK = 1500
\]

This is a cumulative acknowledgement.

The sender can use acknowledgement information to determine which previously transmitted bytes no longer need to remain outstanding.

TCP also supports mechanisms such as Selective Acknowledgement (SACK), which can provide information about non-contiguous received data.

### 4.6 TCP connection termination

TCP normally uses FIN and ACK exchanges to close a connection gracefully.

A typical termination sequence is:

CLIENT                         SERVER
  |                              |
  |------------ FIN ----------->|
  |                              |
  |<----------- ACK ------------|
  |                              |
  |<----------- FIN ------------|
  |                              |
  |------------ ACK ----------->|
  |                              |
  |       CONNECTION CLOSED      |

The endpoint entering TIME_WAIT retains state for a period to help prevent delayed segments from interfering with a subsequent connection.

An abrupt connection termination may use RST instead of the graceful FIN exchange.

## 5. User Datagram Protocol

UDP is a connectionless transport protocol.

It allows an application to transmit individual datagrams without establishing a TCP-style connection.

UDP is useful when an application values low protocol overhead or implements its own communication behavior.

Typical applications include:

- DNS queries.
- Real-time audio.
- Video transmission.
- Online gaming.
- Network monitoring.
- DHCP.
- Time synchronization.

### 5.1 UDP communication

A basic UDP communication sequence is:

CLIENT                         SERVER
  |                              |
  |-------- DATAGRAM ----------->|
  |                              |
  |<------- RESPONSE ------------|
  |                              |
  |-------- DATAGRAM ----------->|
  |                              |

UDP does not require a connection handshake.

Each datagram is independently addressed.

The receiving application can process datagrams without maintaining a TCP-style connection state machine.

### 5.2 UDP header

A UDP header contains four fields.

| Field | Size |
|---|---:|
| Source port | 16 bits |
| Destination port | 16 bits |
| Length | 16 bits |
| Checksum | 16 bits |

The UDP header is 8 bytes.

UDP provides checksum-based error detection. IPv4 UDP checksums may be omitted, while IPv6 requires UDP checksums except for narrowly defined exceptions.

A checksum does not provide reliability or retransmission.

### 5.3 UDP limitations

UDP does not inherently provide:

- Reliable delivery.
- Ordered delivery.
- Duplicate suppression.
- Connection establishment.
- Transport-level acknowledgements.
- Built-in receiver flow control.
- Built-in congestion control.

Applications that need these features must implement suitable mechanisms or use a higher-level protocol.

For example, QUIC operates over UDP while implementing connection management, reliability and congestion control at the QUIC layer.

## 6. TCP and UDP: Engineering Comparison

The choice between TCP and UDP should be based on application behavior rather than assumptions that one protocol is universally faster.

| Requirement | Suitable approach |
|---|---|
| Reliable file transfer | TCP |
| Ordered database communication | TCP |
| Traditional HTTPS | TCP |
| Real-time datagrams | UDP-based application protocol |
| DNS queries | Usually UDP, with TCP also supported |
| Video communication | Often UDP-based protocols |
| Remote administration | TCP |
| Custom reliable transport | UDP with an appropriate higher-level protocol |

TCP includes additional mechanisms for reliability and congestion control.

UDP has less transport-level overhead, but an application using UDP may need to implement reliability, pacing, retransmission, authentication and congestion management.

The actual performance depends on the workload, network, implementation and application requirements.

## 7. Flow Control

Flow control prevents a sender from transmitting data faster than the receiver can accept and buffer it.

TCP implements receiver flow control using the advertised receive window.

The receiver communicates the amount of additional data it is prepared to accept.

The sender must respect the available receive window.

### 7.1 Sliding-window mechanism

A sliding window allows multiple bytes to remain in transmission before acknowledgements arrive.

Consider:

- Initial receive window: 10 bytes.
- First segment: 6 bytes.
- Second segment: 4 bytes.

The receiver's advertised window is now fully occupied.

The sender cannot transmit additional data within that window.

When the receiver acknowledges the first 6 bytes, the sender can reuse the released capacity.

Example:

| Operation | Outstanding bytes | Available window |
|---|---:|---:|
| Initial state | 0 | 10 |
| Send 6 bytes | 6 | 4 |
| Send 4 bytes | 10 | 0 |
| Additional 3-byte transmission | 10 | 0 |
| ACK 6 bytes | 4 | 6 |
| Send 3 bytes | 7 | 3 |

The window moves forward as acknowledgements arrive.

### 7.2 Receive window

The receive window represents the amount of additional data the receiver can accept.

It is advertised in TCP headers.

A zero receive window indicates that the receiver currently has no advertised capacity for additional data.

TCP includes mechanisms such as zero-window probing to discover when the receiver becomes ready to accept additional data.

### 7.3 Send window

The sender uses transmission and acknowledgement information to determine which bytes can be transmitted or removed from the outstanding-data queue.

The sender must account for both receiver flow control and congestion control.

A simplified effective sending limit is:

\[
\text{Effective Window}
=
\min(\text{Receive Window},\text{Congestion Window})
\]

The actual TCP transmission process includes additional conditions, such as outstanding data, sequence numbers, retransmission state and implementation-specific algorithms.

### 7.4 Flow control versus congestion control

These mechanisms address different problems.

| Aspect | Flow Control | Congestion Control |
|---|---|---|
| Primary concern | Receiver capacity | Network capacity |
| Main mechanism | Receive window | Congestion window |
| Protects | Receiving application and buffers | Network path |
| Controlled by | Receiver advertisement | Sender congestion algorithm |
| Main objective | Prevent receiver overload | Reduce network congestion |

A receiver may advertise a large window while the network is congested.

Similarly, the network may have available capacity while the receiver has insufficient buffer space.

Both mechanisms are necessary for TCP transmission.

## 8. TCP Reliability and Retransmission

TCP reliability depends on multiple cooperating mechanisms.

### Sequence tracking

Identifies the position of bytes in the stream.

### Acknowledgements

Communicate successfully received data.

### Retransmission

Resends data that is believed to have been lost.

### Retransmission timeout

Determines when an unacknowledged transmission should be retransmitted.

### Duplicate acknowledgements

Repeated acknowledgements can provide evidence of missing segments.

### Selective Acknowledgement

Allows receivers to identify successfully received non-contiguous blocks.

TCP retransmission timeout calculations adapt to observed round-trip time and its variation.

A simplified conceptual representation is:

\[
RTO = SRTT + 4 \times RTTVAR
\]

Actual TCP implementations also apply minimum and maximum timeout limits, clock granularity and retransmission backoff.

## 9. Practical Port and Connection Security

Transport-layer communication creates several security considerations.

### Port exposure

Every listening service introduces a potential attack surface.

Unused services should not remain unnecessarily exposed.

### Port scanning

Attackers can examine open ports to identify available services.

Network monitoring and firewall policies help restrict unauthorized access.

### SYN flooding

An attacker can send large numbers of SYN requests to consume connection-management resources.

Defensive mechanisms include SYN cookies, connection-rate limits and appropriate network filtering.

### UDP amplification

Certain UDP services can produce responses substantially larger than their requests.

Attackers may exploit misconfigured services in reflection and amplification attacks.

Appropriate controls include restricting unnecessary public services and implementing response-rate limits.

### Source address spoofing

Some UDP-based communication can be abused when applications trust source addresses without appropriate verification.

Applications should authenticate messages when required.

### Encryption

TCP and UDP do not independently guarantee application confidentiality.

TLS is commonly used with TCP, while QUIC integrates TLS 1.3 security mechanisms over UDP.

### Firewall policies

Network access policies should specify:

- Permitted source addresses.
- Permitted destination addresses.
- Transport protocols.
- Destination ports.
- Connection state requirements.
- Traffic-rate restrictions.

## 10. Python Implementation

The Python implementation combines protocol simulation and actual loopback socket communication.

### Core components

| Component | Responsibility |
|---|---|
| `Endpoint` | Validates IP addresses and ports |
| `Connection` | Models TCP connection states |
| `FlowControl` | Simulates sliding-window transmission |
| `TCPServer` | Runs a TCP echo server |
| `UDPServer` | Runs a UDP echo server |
| `tcp_client()` | Creates a TCP client connection |
| `udp_client()` | Sends and receives UDP datagrams |

### Practical mechanisms

The TCP server uses:

- `socket.AF_INET` for IPv4.
- `socket.SOCK_STREAM` for TCP.
- `bind()` for local endpoint registration.
- `listen()` for connection requests.
- `accept()` for incoming connections.
- `sendall()` for reliable socket-level transmission.

The UDP server uses:

- `socket.SOCK_DGRAM`.
- `recvfrom()` for datagram reception.
- `sendto()` for datagram transmission.

Both servers use dynamically allocated ports to avoid depending on fixed local port availability.

The flow-control simulator maintains outstanding segments and cumulative acknowledgements.

The socket demonstrations use the operating system's networking stack. The simulated flow-control mechanism is separate from the kernel's actual TCP implementation.

## 11. JavaScript Implementation

The JavaScript implementation uses Node.js event-driven networking.

### Core components

| Component | Responsibility |
|---|---|
| `Endpoint` | Validates IPv4 endpoints |
| `Connection` | Models state transitions |
| `SlidingWindow` | Manages outstanding data |
| `createTCPServer()` | Creates an asynchronous TCP server |
| `sendTCP()` | Establishes and communicates over TCP |
| `createUDPServer()` | Receives UDP datagrams |
| `sendUDP()` | Sends UDP datagrams asynchronously |

### Event-driven communication

Node.js networking is built around asynchronous operations.

The TCP server handles incoming data through socket events.

Important events include:

- `connect`
- `data`
- `end`
- `timeout`
- `error`
- `close`

UDP communication uses datagram events such as `message` and `error`.

Promises allow the calling application to wait for communication results without blocking the entire event loop.

### Backpressure

Node.js TCP sockets expose backpressure-related behavior through the return value of `socket.write()` and the `drain` event.

The demonstration uses a separate sliding-window model to explain receiver flow control.

Application-level backpressure and TCP receive-window management are related but distinct mechanisms.

## 12. C++17 Implementation

The C++17 implementation emphasizes explicit domain modeling and state management.

### Core components

| Component | Responsibility |
|---|---|
| `Endpoint` | Represents a network endpoint |
| `Connection` | Enforces TCP state transitions |
| `FlowControlEngine` | Maintains outstanding segments |
| `PortRegistry` | Tracks protocol-specific port bindings |
| `TransportEngine` | Coordinates transport demonstrations |

### Data structures

The implementation uses:

- `std::map` for endpoint registration and transition lookup.
- `std::deque` for outstanding segments.
- `std::vector` for permitted state transitions.
- `std::optional` for transmissions that may be blocked.
- Enumerations for protocol and connection states.

### Design decisions

The port registry prevents duplicate endpoint registration.

The connection state machine rejects invalid state transitions.

The flow-control engine calculates outstanding bytes and available receiver capacity.

The implementation uses cumulative acknowledgements to remove completely acknowledged segments.

Its flow-control model is deliberately independent of operating-system socket behavior.

## 13. Java 17 Implementation

The Java implementation adopts an enterprise-oriented service architecture.

### Core components

| Component | Responsibility |
|---|---|
| `Endpoint` record | Immutable endpoint representation |
| `ConnectionKey` record | Connection identity |
| `Transmission` record | Immutable transmission metadata |
| `PortRegistry` | Endpoint registration |
| `TCPConnection` | Connection state and sequence management |
| `FlowControlService` | Receiver-window management |
| `UDPDatagramService` | Datagram validation |
| `EnterpriseTransportService` | Service orchestration |

### Enterprise engineering characteristics

The design separates transport policies from operational state.

Custom exceptions represent rejected transport operations.

Immutable records reduce accidental modification of endpoint and transmission metadata.

Synchronized methods protect shared connection and flow-control state in concurrent execution environments.

The implementation also maintains a retransmission-monitoring interface based on transmission timestamps.

It models transport behavior rather than implementing a complete production TCP/IP stack.

## 14. PostgreSQL Implementation

The PostgreSQL implementation represents transport-layer operations as relational data.

### Database structure

| Table | Purpose |
|---|---|
| `network_devices` | Network device inventory |
| `port_assignments` | Protocol-specific port registration |
| `transport_connections` | TCP and UDP connection records |
| `connection_events` | Connection lifecycle history |
| `tcp_flow_control` | TCP window and sequence information |
| `tcp_segments` | Transmitted segment records |
| `udp_datagrams` | UDP transmission telemetry |
| `transport_policies` | Transport configuration and restrictions |

### Referential integrity

Foreign keys maintain relationships between devices, endpoints, connections, flow-control records and transmission records.

Check constraints enforce valid port numbers, payload sizes, sequence numbers and window values.

Indexes support common operational queries.

Partial indexes reduce the indexed data volume for frequently accessed active connections and unacknowledged segments.

### Trigger-based event recording

The `log_connection_state()` function automatically records state transitions.

The trigger creates an event-history record when a connection changes state.

This provides a persistent audit trail of connection lifecycle operations.

### Flow-control validation

The `validate_flow_control()` function enforces several conditions:

- Flow-control records must reference TCP connections.
- Acknowledgement numbers cannot exceed transmitted sequence numbers.
- Outstanding bytes cannot exceed the advertised receive window.
- Window values must remain within configured limits.

### Transactional connection creation

The `create_tcp_connection()` function validates source and destination devices, verifies the destination TCP port and creates the connection and corresponding flow-control record.

Because the function executes within its calling transaction, database changes can be committed or rolled back together.

### Operational views

| View | Purpose |
|---|---|
| `v_connection_inventory` | Connection inventory and endpoint details |
| `v_tcp_flow_monitor` | Receive-window utilization |
| `v_transport_performance` | Protocol-level transmission aggregation |
| `v_udp_delivery_report` | UDP delivery and checksum statistics |

These views support monitoring and reporting without repeatedly writing complex joins.

## 15. Relationship Between the Five Implementations

The implementations approach the same transport-layer domain from different engineering perspectives.

| Engineering area | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| Endpoint validation | Dataclass | Class | Struct | Record | Constraints |
| TCP lifecycle | State model | Event emitter | State engine | State service | Connection states |
| UDP | Datagram sockets | Datagram sockets | Protocol model | Datagram service | Datagram records |
| Ports | Endpoint objects | Endpoint objects | Port registry | Port registry | Port assignments |
| Flow control | Sliding window | Event-driven window | Window engine | Flow-control service | Window records |
| Acknowledgements | Cumulative ACK | Cumulative ACK | Cumulative ACK | Cumulative ACK | ACK function |
| Error handling | Exceptions | Promise rejection | Exceptions | Custom exceptions | SQL exceptions |
| Persistence | In-memory | In-memory | In-memory | In-memory | Relational database |

The socket-based Python and JavaScript programs demonstrate real local network communication.

The C++ and Java programs concentrate on explicit transport behavior, validation and domain modeling.

The PostgreSQL implementation provides persistence, reporting and integrity enforcement.

## 16. Performance Considerations

Transport-layer performance depends on multiple interacting factors.

### Network latency

Round-trip time affects acknowledgement arrival and the time required to recover from packet loss.

### Bandwidth

The maximum possible data throughput depends partly on available network bandwidth.

### Window size

A larger receive window can allow more data to remain in flight.

A small receive window may restrict throughput even when the network has available capacity.

### Bandwidth-delay product

The bandwidth-delay product estimates how much data must be in flight to fully utilize a network path.

\[
BDP = Bandwidth \times RTT
\]

For example, a network with:

- Bandwidth: 100 Mbps.
- Round-trip time: 50 milliseconds.

The approximate bandwidth-delay product is:

\[
100,000,000 \times 0.05
= 5,000,000 \text{ bits}
\]

This corresponds to approximately 625,000 bytes.

A sender may need an appropriately sized effective transmission window to fully utilize the path.

TCP window scaling supports receive windows larger than the original 16-bit window field permits.

### Buffer management

Large buffers can increase memory consumption and potentially contribute to bufferbloat.

Applications should use suitable buffering, backpressure and concurrency limits.

### Database performance

The PostgreSQL implementation uses indexes on connection identifiers, timestamps, protocol states and outstanding segments.

For very large telemetry datasets, partitioning event and datagram tables by time can improve operational management.

## 17. Edge Cases and Failure Conditions

| Scenario | Expected behavior |
|---|---|
| Port outside 0–65535 | Reject endpoint |
| Port zero used for listening registration | Reject registration |
| Duplicate endpoint registration | Reject duplicate binding |
| TCP data sent before establishment | Reject operation |
| Invalid TCP state transition | Reject transition |
| Invalid cumulative ACK | Reject acknowledgement |
| ACK greater than transmitted sequence | Reject acknowledgement |
| Receiver window becomes zero | Block additional transmission |
| Payload exceeds available window | Defer transmission |
| UDP destination unavailable | Datagram may not be delivered |
| UDP datagram lost | No automatic UDP retransmission |
| TCP server unavailable | Connection attempt fails |
| Socket timeout | Abort or handle operation |
| Invalid IPv4 address | Reject endpoint |
| Duplicate database record | Apply uniqueness constraints |
| Flow-control record references UDP | Reject insertion |

A significant distinction exists between a modeled transmission and actual network delivery.

A successful UDP send operation generally means that the local networking stack accepted the datagram for transmission. It does not establish that the destination received it.

Similarly, a successful TCP write does not necessarily establish that the remote application processed the transmitted data.

## 18. Testing and Execution

### Python

Requirements:

- Python 3.10 or later.
- Standard library.

The program starts temporary TCP and UDP servers on dynamically allocated local ports.

It performs communication using the loopback interface and runs flow-control validation scenarios.

### JavaScript

Requirements:

- Node.js 18 or later.
- Standard library.

The program uses asynchronous TCP and UDP sockets and Promise-based operations.

### C++17

Requirements:

- C++17-compatible compiler.
- Standard template library.

Compilation should enable C++17 support.

### Java 17

Requirements:

- Java Development Kit 17.

The program uses records, collections, enums and synchronized service methods.

### PostgreSQL

Requirements:

- PostgreSQL 14 or later.
- Permission to create schemas, tables, functions, triggers and indexes.

The SQL script creates the `transport_lab` schema, inserts sample network records, creates reporting views and executes validation queries.

The script uses a transaction to keep its database changes consistent.

## 19. Implementation Limitations

These implementations are educational engineering models, not replacements for operating-system networking stacks.

The following distinctions are important:

1. The Python and JavaScript socket examples use real operating-system TCP and UDP communication.
2. The Python, JavaScript, C++ and Java sliding-window examples simulate selected flow-control concepts.
3. The modeled connection handshakes do not construct or transmit actual TCP SYN, SYN-ACK and FIN packets.
4. The C++ and Java implementations do not create operating-system network sockets.
5. The PostgreSQL schema stores transport information but does not intercept packets or operate as a network stack.
6. The database's simplified sequence and acknowledgement calculations do not reproduce every TCP behavior.
7. Real TCP congestion control, retransmission timers, selective acknowledgements, window scaling and packet reassembly require additional protocol-specific mechanisms.

These distinctions prevent application-level simulations from being confused with actual TCP/IP protocol implementation.

## 20. Technical Terminology

| Term | Definition |
|---|---|
| Transport layer | Network layer responsible for process-to-process communication |
| TCP | Reliable, connection-oriented transport protocol |
| UDP | Connectionless, datagram-oriented transport protocol |
| Port | 16-bit application endpoint identifier |
| Socket | Programming interface and communication endpoint abstraction |
| Segment | TCP transport data unit |
| Datagram | UDP transport data unit |
| Handshake | Exchange used to establish a TCP connection |
| Sequence number | Identifies the position of data in a TCP byte stream |
| Acknowledgement | Identifies the next expected byte |
| Sliding window | Mechanism that controls outstanding transmitted data |
| Receive window | Advertised receiver capacity |
| Congestion window | Sender-side limit used for network congestion control |
| MSS | Maximum Segment Size |
| MTU | Maximum Transmission Unit |
| RTT | Round-Trip Time |
| RTO | Retransmission Timeout |
| SACK | Selective Acknowledgement |
| SYN | TCP connection establishment flag |
| ACK | TCP acknowledgement flag |
| FIN | TCP graceful termination flag |
| RST | TCP connection reset flag |
| TIME_WAIT | TCP state used during connection termination |
| Backpressure | Mechanism that prevents producers from overwhelming consumers |
| Multiplexing | Combining application communications over shared network infrastructure |
| Demultiplexing | Delivering received transport data to the appropriate application endpoint |

The transport layer provides the communication mechanisms that connect application processes across networked systems. TCP prioritizes reliable, ordered byte-stream delivery, while UDP provides a lightweight datagram service. Ports identify application endpoints, connection state manages TCP communication, and flow control protects receiving systems from excessive transmission rates.
