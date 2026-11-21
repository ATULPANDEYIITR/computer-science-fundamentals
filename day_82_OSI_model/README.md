# OSI Model: Seven-Layer Network Architecture

## 1. Introduction

The Open Systems Interconnection (OSI) model is a conceptual framework developed by the International Organization for Standardization (ISO) to describe how network communication functions across different systems.

It divides communication into seven logical layers. Each layer performs a distinct responsibility and provides services to the layer above it.

The model helps explain:

- How information moves between communicating systems.
- How application data becomes network-transmittable information.
- How addressing and routing operate.
- How reliable and unreliable transport mechanisms differ.
- How network protocols interact.
- How network failures can be isolated by function.

The seven layers are:

| Layer | Name | Primary responsibility | Protocol Data Unit |
|---|---|---|---|
| 7 | Application | Application-level network services | Data |
| 6 | Presentation | Encoding, compression and encryption | Data |
| 5 | Session | Communication session management | Data |
| 4 | Transport | End-to-end transport and port addressing | Segment or Datagram |
| 3 | Network | Logical addressing and routing | Packet |
| 2 | Data Link | Framing and MAC addressing | Frame |
| 1 | Physical | Transmission of raw bits | Bits |

The OSI model is a conceptual reference architecture. Real networking implementations do not always implement seven separately identifiable protocol layers.

## 2. Communication Architecture

Network communication involves two complementary processes:

**Encapsulation:** The sender processes application information down the protocol stack. Each layer adds information required for its communication responsibility.

**Decapsulation:** The receiver processes incoming information in the opposite direction, interpreting and removing the relevant protocol information.

The communication sequence is:

    SENDER                              RECEIVER

    Application (7)                     Application (7)
          |                                   ^
    Presentation (6)                   Presentation (6)
          |                                   ^
    Session (5)                        Session (5)
          |                                   ^
    Transport (4)                      Transport (4)
          |                                   ^
    Network (3)                        Network (3)
          |                                   ^
    Data Link (2)                      Data Link (2)
          |                                   ^
    Physical (1) ---- Transmission ---> Physical (1)

The sender's logical processing moves from Layer 7 toward Layer 1. The receiver's logical processing moves from Layer 1 toward Layer 7.

Intermediate network devices can process selected layers without processing the complete application communication.

## 3. Layer 1: Physical Layer

### Responsibilities

The Physical Layer handles the transmission and reception of raw bits through a communication medium.

It defines electrical, optical, radio-frequency and mechanical characteristics required for communication.

Its responsibilities include:

- Signal transmission and reception.
- Bit representation.
- Signal timing and synchronization.
- Physical connectors.
- Transmission frequency.
- Cable characteristics.
- Data transmission rates.
- Physical topology.
- Signal attenuation and interference.

### Transmission Media

| Medium | Characteristics |
|---|---|
| Twisted-pair cable | Electrical transmission through copper conductors |
| Coaxial cable | Shielded electrical transmission |
| Fiber-optic cable | Optical transmission using light |
| Radio waves | Wireless electromagnetic transmission |
| Microwave | Directional wireless transmission |

### Relevant Technologies

- Ethernet physical interfaces.
- IEEE 802.11 radio transmission.
- Fiber-optic transceivers.
- Repeaters.
- Hubs.
- Physical network adapters.

### Data Representation

The Layer 1 Protocol Data Unit is a bit.

For example:

    Character: A
    ASCII:     65
    Binary:    01000001

A transmission system represents bits using physical signals. The actual electrical or optical encoding depends on the physical technology.

### Implementation

The Python implementation converts byte sequences into bit strings and reconstructs bytes during reception.

The JavaScript implementation models physical transmission as the final processing stage in its event-driven pipeline.

The C++ implementation validates transmission input and records physical-layer processing metrics.

The Java implementation models physical transmission and records successful or failed operations.

The SQL implementation stores physical interfaces, transmission technologies and link characteristics.

### Failure Conditions

Typical physical-layer failures include:

- Disconnected cables.
- Damaged connectors.
- Power failures.
- Radio interference.
- Signal attenuation.
- Faulty transceivers.
- Incorrect physical media.

**Troubleshooting principle:** Verify physical connectivity, interface state, signal availability and transmission-medium integrity before investigating higher-layer failures.

## 4. Layer 2: Data Link Layer

### Responsibilities

The Data Link Layer provides communication between devices on the same local network link.

It organizes network-layer packets into frames and uses physical addresses to identify local-link destinations.

Its responsibilities include:

- Framing.
- MAC addressing.
- Media access control.
- Frame transmission.
- Link-level error detection.
- Local network delivery.
- Frame synchronization.

### Sublayers

The IEEE 802 architecture distinguishes two Data Link sublayers.

| Sublayer | Responsibility |
|---|---|
| Logical Link Control (LLC) | Provides logical link services and multiplexing |
| Media Access Control (MAC) | Handles media access and MAC addressing |

### MAC Addressing

A conventional Ethernet MAC address is 48 bits long.

Example:

    00:11:22:33:44:55

It identifies a network interface at the Data Link level.

A MAC address is used for local-link delivery. It does not replace an IP address and is not normally the address used for end-to-end routing across different IP networks.

### Ethernet Frame

A conventional Ethernet II frame contains:

| Field | Size |
|---|---:|
| Destination MAC | 6 bytes |
| Source MAC | 6 bytes |
| EtherType | 2 bytes |
| Payload | Variable |
| Frame Check Sequence | 4 bytes |

The Frame Check Sequence (FCS) uses CRC-32 to detect accidental frame corruption.

A standard Ethernet frame has a minimum size of 64 bytes and a maximum size of 1518 bytes without a VLAN tag, measured from destination MAC through FCS.

Preamble and Start Frame Delimiter are transmitted separately from this frame-size measurement.

### Switching

An Ethernet switch forwards frames using a MAC address table.

A typical switching operation is:

1. Receive an Ethernet frame.
2. Learn the source MAC address on the incoming port.
3. Examine the destination MAC address.
4. Forward the frame to the appropriate port.
5. Flood unknown unicast frames within the applicable VLAN.

Switches generally operate at Layer 2, although multilayer switches can also perform Layer 3 routing.

### VLANs

Virtual Local Area Networks divide a physical switching infrastructure into separate logical broadcast domains.

IEEE 802.1Q adds VLAN tagging information to Ethernet frames.

VLAN separation improves traffic organization and network segmentation but does not independently provide complete security isolation.

### Implementation

The Python implementation constructs an Ethernet-like frame containing source MAC, destination MAC and EtherType information. It calculates and verifies an FCS using CRC-32.

The C++ implementation models Ethernet frames as structured objects.

The Java implementation validates MAC address representations and creates immutable Ethernet frame records.

The SQL implementation stores network interfaces, MAC addresses and link characteristics.

### Failure Conditions

- Incorrect MAC addressing.
- Switching loops.
- VLAN configuration errors.
- Frame corruption.
- Port security violations.
- Interface shutdown.
- Incorrect duplex configuration.

**Troubleshooting principle:** Examine interface status, MAC address learning, VLAN membership, frame counters and switching behavior.

## 5. Layer 3: Network Layer

### Responsibilities

The Network Layer provides logical addressing and forwarding between different networks.

It enables packets to travel beyond the local broadcast domain.

Its responsibilities include:

- Logical addressing.
- Routing.
- Packet forwarding.
- Network identification.
- Path selection.
- Packet fragmentation where supported.
- Hop-limit or TTL processing.

### IP Addressing

Internet Protocol addresses identify network interfaces logically.

Two major IP versions are:

| Feature | IPv4 | IPv6 |
|---|---|---|
| Address size | 32 bits | 128 bits |
| Representation | Dotted decimal | Colon-separated hexadecimal |
| Example | 192.168.1.10 | 2001:db8::10 |
| Header size | Variable, minimum 20 bytes | Fixed 40 bytes |
| Broadcast | Supported | Not supported |

### IPv4 Packet

The IPv4 header contains:

- Version.
- Internet Header Length.
- Differentiated Services field.
- Total Length.
- Identification.
- Flags.
- Fragment Offset.
- Time To Live.
- Protocol.
- Header Checksum.
- Source IP address.
- Destination IP address.

The Protocol field identifies the transport or other upper-layer protocol carried by IPv4.

Common values include:

| Protocol | IPv4 Protocol Number |
|---|---:|
| ICMP | 1 |
| TCP | 6 |
| UDP | 17 |

### Routing

Routers make forwarding decisions using routing tables.

A routing entry typically contains:

- Destination network.
- Prefix length.
- Next-hop address.
- Outgoing interface.
- Metric or administrative preference.

Routers generally use longest-prefix matching to select the most specific applicable route.

Example:

    Destination: 192.168.1.20
    Network:     192.168.1.0/24
    Gateway:     192.168.1.1

If the destination belongs to the local subnet, a host normally resolves the destination's local-link address and sends directly.

If the destination belongs to another network, the host forwards the packet to its configured next-hop router.

### TTL

IPv4 Time To Live prevents packets from circulating indefinitely.

A router decreases TTL when forwarding a packet. A packet whose TTL expires is discarded.

IPv6 uses Hop Limit for the corresponding purpose.

### Implementation

The Python implementation constructs IPv4 headers, calculates the header checksum and validates packet length.

The C++ implementation includes subnet membership testing through bitwise address and subnet-mask operations.

The Java implementation models IPv4 packet fields as immutable records.

The SQL implementation stores IP addresses using PostgreSQL's `INET` type and maintains device and interface relationships.

### Failure Conditions

- Incorrect IP configuration.
- Missing routes.
- Incorrect subnet masks.
- Duplicate addresses.
- Routing loops.
- TTL expiration.
- Packet filtering.
- MTU-related fragmentation or packet-size problems.

**Troubleshooting principle:** Examine IP addressing, subnet boundaries, gateway configuration, routing tables and packet forwarding.

## 6. Layer 4: Transport Layer

### Responsibilities

The Transport Layer provides communication between application processes running on different systems.

It uses port numbers to distinguish application endpoints.

Its responsibilities can include:

- Segmentation and reassembly.
- Multiplexing.
- Process-to-process delivery.
- Flow control.
- Error recovery.
- Reliability.
- Connection management.
- Congestion control.

The exact services depend on the transport protocol.

### TCP

Transmission Control Protocol is connection-oriented.

Its major mechanisms include:

- Connection establishment.
- Sequence numbers.
- Acknowledgments.
- Retransmission.
- Ordered delivery.
- Flow control.
- Congestion control.
- Connection termination.

TCP connection establishment normally uses a three-way handshake:

    CLIENT                  SERVER

      | ---- SYN ------------> |
      | <--- SYN-ACK ---------- |
      | ---- ACK ------------> |
      |                         |
      | Connection established |

TCP provides an ordered byte stream rather than preserving application message boundaries.

### UDP

User Datagram Protocol is connectionless.

Its characteristics include:

- No transport-level connection establishment.
- No guaranteed delivery.
- No guaranteed ordering.
- No built-in retransmission.
- Low header overhead.
- Datagram-oriented communication.

UDP is commonly used by DNS, real-time applications and other services that implement their own reliability mechanisms or do not require retransmission.

### TCP and UDP Comparison

| Characteristic | TCP | UDP |
|---|---|---|
| Connection-oriented | Yes | No |
| Reliable delivery | Yes | Not guaranteed |
| Ordered delivery | Yes | Not guaranteed |
| Retransmission | Built in | Application-dependent |
| Header size | Minimum 20 bytes | 8 bytes |
| Data model | Byte stream | Datagrams |
| Typical use | Web sessions, SSH, file transfer | DNS, streaming, real-time traffic |

### Port Numbers

Port numbers range from 0 to 65535.

| Port | Common service |
|---:|---|
| 20/21 | FTP |
| 22 | SSH |
| 25 | SMTP |
| 53 | DNS |
| 80 | HTTP |
| 443 | HTTPS |

Port assignments identify services conventionally. A port number alone does not establish that a particular service is actually operating.

### Implementation

The Python implementation constructs simplified TCP and UDP headers and validates transport ports and header lengths.

The JavaScript implementation uses a protocol registry and Map-based configuration.

The C++ implementation uses an enumeration to distinguish TCP and UDP and stores their transport metadata separately.

The Java implementation represents transport segments through immutable records and explicit protocol types.

The SQL implementation associates transport protocols and ports with communication sessions.

### Failure Conditions

- Port conflicts.
- Connection timeouts.
- TCP retransmission.
- Firewall restrictions.
- Connection resets.
- UDP packet loss.
- Congestion.
- Incorrect transport configuration.

**Troubleshooting principle:** Examine port accessibility, connection establishment, retransmissions, transport errors and firewall rules.

## 7. Layer 5: Session Layer

### Responsibilities

The Session Layer manages logical communication sessions between applications.

Its conceptual responsibilities include:

- Session establishment.
- Session maintenance.
- Session termination.
- Dialog management.
- Synchronization.
- Recovery points.
- Communication coordination.

It helps explain how applications maintain structured communication over time.

### Dialog Control

Communication may operate through:

- Simplex: communication in one direction.
- Half-duplex: communication in both directions, but not simultaneously.
- Full-duplex: simultaneous communication in both directions.

### Synchronization

Long-running communication can use synchronization points to support recovery after interruptions.

These mechanisms are especially relevant to conceptual session management and application workflows.

### Session Versus Transport

A session is not necessarily equivalent to a TCP connection.

A single TCP connection can support multiple logical application operations. Conversely, an application session may involve multiple underlying transport connections.

Examples include authenticated web sessions and application-level conversation identifiers.

### Implementation

The Python implementation creates UUID-based session identifiers and manages active-session membership using a set.

The JavaScript implementation models session creation and termination through explicit state transitions and events.

The C++ implementation maintains session records using a map and rejects operations on closed sessions.

The Java implementation defines a dedicated session class with controlled state transitions.

The SQL implementation stores session identifiers, endpoint references, protocol information, state and timestamps.

### Failure Conditions

- Session expiration.
- Unexpected termination.
- Lost synchronization.
- Invalid session identifiers.
- Authentication expiration.
- Session state inconsistencies.

**Troubleshooting principle:** Investigate session establishment, lifecycle, application state and synchronization rather than assuming every session problem originates in TCP.

## 8. Layer 6: Presentation Layer

### Responsibilities

The Presentation Layer defines how information is represented so that communicating applications can interpret it consistently.

Its responsibilities include:

- Character encoding.
- Data representation.
- Serialization.
- Compression.
- Encryption and decryption.
- Format conversion.

### Character Encoding

Different systems must agree on how characters are represented.

Common encodings include:

- ASCII.
- UTF-8.
- UTF-16.

UTF-8 is widely used for modern network applications because it supports Unicode and is compatible with ASCII for the ASCII character range.

Example:

    Character: A
    Unicode:   U+0041
    UTF-8:     41

Incorrect encoding assumptions can produce corrupted text even when lower network layers successfully deliver the data.

### Serialization

Serialization converts structured data into a transferable representation.

Examples include:

- JSON.
- XML.
- Protocol Buffers.
- ASN.1.

Deserialization reconstructs structured information at the receiving endpoint.

### Compression

Compression reduces data size.

Common approaches include:

- Lossless compression.
- Lossy compression.

Lossless compression preserves the original data. Lossy compression sacrifices selected information to achieve greater size reduction.

### Encryption

Encryption protects information confidentiality.

TLS provides cryptographic protection for application communication. In the practical TCP/IP stack, TLS is generally implemented above the transport layer and below or alongside application protocols.

The OSI model's Presentation Layer is a useful conceptual location for discussing encryption and representation, but modern protocol implementations do not always map cleanly to individual OSI layers.

### Implementation

The Python implementation supports UTF-8 encoding, decoding and SHA-256 integrity fingerprints.

The JavaScript implementation uses Node.js Buffer and crypto facilities.

The C++ implementation models presentation processing through byte-compatible strings.

The Java implementation uses StandardCharsets.UTF_8 and MessageDigest.

The examples do not implement actual encryption. A SHA-256 digest provides integrity-related fingerprinting but does not provide confidentiality, authentication or encryption.

### Failure Conditions

- Character encoding mismatch.
- Malformed serialized data.
- Unsupported compression format.
- Invalid decryption parameters.
- Certificate validation failures.
- Incompatible data representations.

**Troubleshooting principle:** Check character encoding, serialization formats, cryptographic configuration and data transformation boundaries.

## 9. Layer 7: Application Layer

### Responsibilities

The Application Layer provides network services directly to application software.

It defines application-level communication rules and message structures.

Its responsibilities include:

- Request and response formats.
- Application protocol operations.
- Resource access.
- Application-level error handling.
- Service identification.
- Communication semantics.

### Common Protocols

| Protocol | Purpose |
|---|---|
| HTTP | Web communication |
| HTTPS | HTTP protected using TLS |
| DNS | Domain name resolution |
| FTP | File transfer |
| SSH | Secure remote access |
| SMTP | Email transmission |
| DHCP | Dynamic host configuration |
| SNMP | Network monitoring and management |

### HTTP Communication

HTTP uses request and response messages.

An HTTP request commonly includes:

- Request method.
- Resource path.
- HTTP version.
- Headers.
- Optional message body.

Common methods include:

| Method | Purpose |
|---|---|
| GET | Retrieve a resource |
| POST | Submit information |
| PUT | Replace or create a resource |
| PATCH | Partially modify a resource |
| DELETE | Remove a resource |

An HTTP response contains a status code, headers and potentially a message body.

### DNS

The Domain Name System translates domain names into network information.

For example:

    example.com
        |
        v
    DNS Resolver
        |
        v
    DNS Response
        |
        v
    IP Address

DNS commonly uses UDP port 53, although TCP is also used for certain operations and circumstances.

### Implementation

The Python implementation constructs a simplified HTTP request and validates its method and resource path.

The JavaScript implementation maintains a protocol registry using a Map.

The C++ implementation validates application protocol support through a set.

The Java implementation applies an explicit application protocol policy.

The SQL implementation records application protocols and associates them with communication sessions.

### Failure Conditions

- Application service unavailable.
- Invalid request.
- Authentication failure.
- Authorization failure.
- Incorrect resource path.
- Unsupported protocol.
- Application timeout.

**Troubleshooting principle:** Examine service availability, request formatting, application logs, authentication and application-specific errors.

## 10. Protocol Data Units and Encapsulation

A Protocol Data Unit (PDU) is the data representation associated with communication at a particular layer.

| Layer | PDU | Typical addressing or identification |
|---|---|---|
| Physical | Bits | Physical signal representation |
| Data Link | Frame | MAC addresses |
| Network | Packet | IP addresses |
| Transport | Segment or Datagram | Port numbers |
| Session | Data | Session identifier |
| Presentation | Data | Encoding and representation |
| Application | Data | Application protocol and resource |

### Encapsulation Example

Suppose a workstation sends an HTTPS request to a server.

    Application:
        HTTP request

    Presentation:
        Encoded application data

    Session:
        Logical session association

    Transport:
        TCP header + application data

    Network:
        IPv4 header + TCP segment

    Data Link:
        Ethernet header + IPv4 packet + FCS

    Physical:
        Transmitted bits

Each layer has a different responsibility. The headers are not interchangeable.

### Important Distinction

An IP packet retains its logical source and destination addresses while being forwarded across routers.

The Ethernet frame is normally replaced at each routed link with a new link-layer frame appropriate for the next hop.

Therefore:

- IP addressing supports communication across networks.
- MAC addressing supports local-link delivery.
- Port addressing identifies transport endpoints.
- Application identifiers determine application-level operations.

## 11. Network Devices and OSI Layers

| Device | Common OSI layer | Primary function |
|---|---|---|
| Repeater | Layer 1 | Regenerates physical signals |
| Hub | Layer 1 | Repeats signals to connected ports |
| Ethernet switch | Layer 2 | Forwards frames using MAC addresses |
| Bridge | Layer 2 | Connects local network segments |
| Router | Layer 3 | Forwards packets between networks |
| Firewall | Layers 3–7, depending on implementation | Enforces traffic policies |
| Gateway | Multiple layers | Connects systems using different protocols or architectures |

The classification is conceptual. Modern devices often operate across multiple layers.

For example, a next-generation firewall can inspect application-level information, while a multilayer switch can perform both Layer 2 switching and Layer 3 routing.

## 12. Practical Troubleshooting Using the OSI Model

The layered architecture supports systematic fault isolation.

| Layer | Example symptom | Investigation |
|---|---|---|
| Physical | No connectivity | Cable, signal, power and interface status |
| Data Link | Local communication failure | MAC learning, VLAN and frame errors |
| Network | Remote network unreachable | IP address, subnet and routing |
| Transport | Connection timeout | Ports, TCP handshake and firewall |
| Session | Session unexpectedly expires | Session state and lifecycle |
| Presentation | Corrupted information | Encoding, serialization and cryptography |
| Application | Service returns errors | Application logs and request validation |

### Example: HTTPS Connection Failure

Consider a workstation attempting to connect to a web server.

    Workstation: 192.168.1.10
    Server:      192.168.1.20
    Protocol:    HTTPS
    Port:        443

A structured investigation proceeds as follows:

1. Verify that the network interfaces are operational.
2. Check the Ethernet link and local MAC resolution.
3. Verify the workstation's IP address and routing information.
4. Check whether TCP port 443 is reachable.
5. Examine application session behavior.
6. Validate TLS negotiation and certificate handling.
7. Inspect the HTTP request and server response.

This sequence narrows the investigation by responsibility rather than treating every communication failure as an application problem.

## 13. Implementation Architecture

The five source files provide different engineering perspectives on the same network architecture.

### Python: Protocol Simulation

The Python implementation provides an executable encapsulation and decapsulation model.

| Component | Responsibility |
|---|---|
| `PhysicalLayer` | Converts bytes into bits |
| `DataLinkLayer` | Constructs Ethernet frames and verifies FCS |
| `NetworkLayer` | Creates and validates IPv4 headers |
| `TransportLayer` | Constructs TCP and UDP headers |
| `SessionLayer` | Manages session lifecycle |
| `PresentationLayer` | Encodes and decodes application data |
| `ApplicationLayer` | Constructs HTTP requests |
| `OSISimulator` | Coordinates transmission and reception |

Important mechanisms include:

- Dataclasses for protocol data.
- Enumerations for layer identification.
- Exceptions for invalid network operations.
- CRC-32 verification.
- IPv4 header checksums.
- UUID-based session identifiers.
- Assertions for functional verification.

The packet model is intentionally simplified. It does not implement complete TCP or UDP checksum processing, TCP connection establishment, retransmission, actual IP routing, Ethernet padding, VLAN tagging or physical signaling.

### JavaScript: Event-Driven Network Processing

The JavaScript implementation uses an event-driven architecture.

Its primary components are:

| Component | Responsibility |
|---|---|
| `ProtocolRegistry` | Application protocol lookup |
| `NetworkSession` | Session state management |
| `LayerProcessor` | Layer-specific processing |
| `NetworkSimulator` | Communication orchestration |

The EventEmitter interface provides events for:

- Session creation.
- Layer processing.
- Layer failures.
- Packet transmission.
- Packet reception.
- Session termination.

The implementation also uses:

- Maps for protocol and session management.
- Sets and structured validation rules where appropriate.
- Promises for asynchronous execution.
- Buffer for byte-oriented data handling.
- Crypto for UUID and SHA-256 operations.

The implementation emphasizes event propagation, operational observability and failure isolation.

### C++17: Structured Network Engine

The C++ implementation emphasizes typed network structures and explicit validation.

Its domain types include:

- `MACAddress`
- `IPv4Address`
- `Session`
- `TransportSegment`
- `IPv4Packet`
- `EthernetFrame`
- `NetworkInterface`

Its principal architectural decisions include:

- Fixed-size arrays for address storage.
- Enumerations for protocol and session state.
- Maps for session and metrics management.
- Sets for supported application protocols.
- Exceptions for layer-specific failures.
- Bitwise subnet calculations.

The address representations use fixed-size storage, avoiding unnecessary dynamic allocation for IP and MAC addresses.

### Java 17: Enterprise Network Architecture

The Java implementation emphasizes domain modeling, controlled state transitions and immutable data structures.

Important components include:

| Component | Responsibility |
|---|---|
| `Endpoint` | Network endpoint validation |
| `ApplicationData` | Application message representation |
| `TransportSegment` | Transport protocol representation |
| `IPv4Packet` | Logical network packet |
| `EthernetFrame` | Link-layer frame |
| `NetworkSession` | Session lifecycle |
| `ProtocolPolicy` | Application protocol authorization |
| `NetworkService` | Communication orchestration |
| `AuditEvent` | Operational audit record |

Java records enforce immutable data representations for packet structures.

The session class restricts state transitions and prevents operations on closed or failed sessions.

The protocol policy separates application protocol validation from packet processing.

The audit collection records layer-specific operational events.

### PostgreSQL: Relational Network Management

The SQL implementation models a network management environment using relational structures.

Its main entities are:

| Table | Purpose |
|---|---|
| `osi_layers` | Seven-layer reference information |
| `protocols` | Protocol classification |
| `network_devices` | Routers, switches, hosts and servers |
| `network_interfaces` | MAC and IP interface information |
| `network_links` | Physical and logical connectivity |
| `communication_sessions` | Communication endpoint and session state |
| `packet_observations` | Layer-specific packet processing records |
| `diagnostic_events` | Operational failures and warnings |

The database uses:

- Primary keys.
- Foreign keys.
- Unique constraints.
- Check constraints.
- PostgreSQL `INET` and `MACADDR` data types.
- Partial and composite indexes.
- Views.
- Common Table Expressions.
- PL/pgSQL functions.
- Triggers.
- Transactions and savepoints.

The `evaluate_session` function measures successful layer coverage and determines whether a session satisfies its defined observation criteria.

The observation trigger prevents new processing observations from being recorded against sessions that are already closed or failed.

## 14. Important Technical Distinctions

### OSI Model Versus TCP/IP Model

The OSI model defines seven conceptual layers. The TCP/IP model organizes practical Internet communication into fewer layers.

A commonly used four-layer TCP/IP representation is:

| TCP/IP layer | Approximate OSI correspondence |
|---|---|
| Application | Layers 5, 6 and 7 |
| Transport | Layer 4 |
| Internet | Layer 3 |
| Network Access | Layers 1 and 2 |

The mapping is approximate rather than an exact one-to-one correspondence.

### MAC Address Versus IP Address

| MAC address | IP address |
|---|---|
| Identifies a local network interface | Provides logical network addressing |
| Used for local-link delivery | Used for routing across networks |
| Layer 2 | Layer 3 |
| Commonly 48 bits in Ethernet | 32 bits in IPv4 and 128 bits in IPv6 |

### Segment Versus Packet Versus Frame

A segment or datagram belongs to the Transport Layer.

A packet belongs to the Network Layer.

A frame belongs to the Data Link Layer.

They represent different encapsulation stages and have different addressing and control information.

### Session Versus Connection

A TCP connection provides transport-level communication state.

An application session represents a logical application interaction.

They can have different lifecycles and should not be treated as equivalent.

### Encryption Versus Hashing

Encryption protects confidentiality and allows authorized recovery of the original information through decryption.

Hashing produces a fixed-length digest.

The SHA-256 examples in the source files provide integrity-related fingerprints. They do not implement encryption or authenticate the sender.

### Error Detection Versus Error Correction

Error detection identifies corrupted information.

Error correction attempts to reconstruct the original information.

Ethernet FCS provides error detection. It does not itself provide retransmission or general error correction.

TCP reliability operates through acknowledgments, retransmissions and related transport mechanisms.

## 15. Security Considerations

The seven-layer model also helps organize network security controls.

| Layer | Security considerations |
|---|---|
| Physical | Physical access, cable security and equipment protection |
| Data Link | VLAN separation, MAC spoofing and switching attacks |
| Network | IP spoofing, routing attacks and packet filtering |
| Transport | Port restrictions, connection abuse and denial of service |
| Session | Session hijacking, expiration and session fixation |
| Presentation | Encryption, certificate validation and serialization safety |
| Application | Authentication, authorization, input validation and application vulnerabilities |

Security controls frequently operate across multiple layers.

Examples include:

- Network segmentation through VLANs and routing policies.
- Stateful firewall inspection.
- TLS encryption.
- Secure application authentication.
- Session expiration.
- Input validation.
- Logging and monitoring.

No single OSI layer provides complete network security.

## 16. Performance Considerations

Network performance depends on several interacting factors.

### Bandwidth

Bandwidth describes the available transmission capacity of a communication link.

### Latency

Latency describes the time required for information to travel between endpoints or through a communication path.

### Throughput

Throughput measures the actual rate of successful data transfer.

### Packet Loss

Packet loss occurs when transmitted packets fail to reach their intended destination.

### MTU

Maximum Transmission Unit defines the maximum packet payload size supported by a network interface or link at the relevant networking layer.

An incorrect MTU configuration can result in fragmentation, packet drops or communication failures.

### Processing Overhead

Every protocol header consumes transmission capacity.

Encapsulation increases the total size of transmitted information.

For this reason, protocol overhead, MTU, packet size, buffering and retransmission behavior influence practical performance.

## 17. Limitations of the Implementations

The source files are educational protocol and network-management models rather than complete operating-system network stacks.

Their limitations are important when interpreting results.

| Area | Implementation limitation |
|---|---|
| Physical | Does not generate actual electrical, optical or radio signals |
| Data Link | Ethernet construction is simplified |
| Network | IPv4 processing does not implement complete routing or fragmentation |
| Transport | TCP and UDP headers are simplified and omit complete checksum processing |
| Session | Session management is modeled at application level |
| Presentation | Encoding is demonstrated without production encryption |
| Application | HTTP handling is illustrative rather than a complete HTTP implementation |

The Python IPv4 implementation uses a simplified IPv4 header and does not process incoming IPv4 fragmentation.

The Python Ethernet implementation calculates FCS, while the C++, Java and JavaScript implementations focus on structured packet metadata and processing behavior.

The JavaScript pipeline demonstrates event-driven layer processing rather than producing a standards-compliant Ethernet frame.

The Java and C++ programs model protocol metadata and communication behavior without implementing complete wire-format serialization.

The PostgreSQL database is a network inventory and operational observation model. It does not capture live network packets or independently verify actual transmission.

## 18. Execution and Verification

The source files are independent implementations.

| Deliverable | Runtime | Execution |
|---|---|---|
| Python | Python 3.10+ | `python osi_model.py` |
| JavaScript | Node.js 18+ | `node osi_model.js` |
| C++17 | C++17 compiler | `g++ -std=c++17 -O2 osi_model.cpp -o osi_model` followed by `./osi_model` |
| Java | Java 17 | `javac OSIEnterprise.java` followed by `java OSIEnterprise` |
| PostgreSQL | PostgreSQL 15+ | Execute the SQL script in a PostgreSQL database |

The Python implementation uses only the standard library.

The JavaScript implementation uses Node.js built-in modules.

The C++ implementation uses the C++ standard library.

The Java implementation uses the Java 17 standard library.

The PostgreSQL implementation uses native PostgreSQL data types, SQL and PL/pgSQL.

The programs demonstrate the separation of networking responsibilities, structured communication, protocol validation, session management and layer-specific diagnostics.
