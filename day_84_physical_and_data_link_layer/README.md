# Physical and Data Link Layer: Signals, Frames, MAC Addresses, Ethernet and Switching

## 1. Introduction

The Physical Layer and Data Link Layer form the foundation of network communication. They operate at the lower two layers of the OSI reference model and establish how information is transmitted through a physical medium and delivered between directly connected network devices.

The Physical Layer represents information as signals. The Data Link Layer organizes transmitted information into frames, identifies devices using MAC addresses, detects transmission errors, and controls access to the communication medium.

This project implements these mechanisms through four complementary areas:

| Area | Primary responsibility |
|---|---|
| Physical Layer | Signal representation and transmission |
| Data Link Layer | Framing, addressing and error detection |
| Ethernet | Wired LAN frame format and communication |
| Switching | MAC learning and frame forwarding |

The implementations use Python for network simulation, JavaScript for event-driven processing, C++17 for efficient switching, Java 17 for enterprise-oriented network services, and PostgreSQL for persistent network data and operational reporting.

## 2. OSI Layer Relationship

The OSI reference model contains seven layers.

| Layer | Name | Main responsibility |
|---|---|---|
| 7 | Application | Network applications and services |
| 6 | Presentation | Data representation and transformation |
| 5 | Session | Session establishment and management |
| 4 | Transport | End-to-end transport and segmentation |
| 3 | Network | Logical addressing and routing |
| 2 | Data Link | Framing, MAC addressing and link-level delivery |
| 1 | Physical | Electrical, optical or radio signal transmission |

The Physical Layer delivers bits across a transmission medium. The Data Link Layer organizes those bits into frames and manages communication over an individual link.

An Ethernet switch normally operates at Layer 2. A router primarily operates at Layer 3.

A switch can forward Ethernet frames without examining the application-level content carried inside them.

## 3. Physical Layer

### 3.1 Signals and binary representation

Computers process information as binary data. A binary sequence contains two possible logical values:

- `0`
- `1`

The Physical Layer represents these values using physical signal characteristics.

Depending on the communication technology, signals can be represented through:

- Voltage levels
- Optical intensity
- Radio frequency characteristics
- Signal phase
- Signal frequency
- Amplitude variations

A logical bit is not itself an electrical signal. Encoding rules define how bits correspond to physical signal states.

### 3.2 Signal characteristics

| Characteristic | Meaning |
|---|---|
| Amplitude | Signal strength |
| Frequency | Number of cycles per second |
| Phase | Relative position within a waveform cycle |
| Bit rate | Number of transmitted bits per second |
| Bandwidth | Frequency range available to a communication channel |
| Noise | Unwanted signal disturbance |
| Attenuation | Reduction in signal strength |
| Latency | Time required for transmission or propagation |

Bit rate and bandwidth are related but are not interchangeable.

A transmission channel's capacity depends on its available bandwidth, noise conditions and modulation or encoding technique.

### 3.3 NRZ encoding

Non-Return-to-Zero encoding represents binary values through signal levels.

In the simplified implementation:

| Binary value | Signal level |
|---|---|
| 0 | Low |
| 1 | High |

For the binary sequence `10110010`, the signal levels are:

`1 0 1 1 0 0 1 0`

NRZ is straightforward to implement, but long sequences of identical bits can create synchronization difficulties depending on the specific NRZ variant and receiver design.

### 3.4 Manchester encoding

Manchester encoding represents each bit using two signal intervals.

The convention implemented in this project is:

| Bit | First half | Second half |
|---|---|---|
| 0 | Low | High |
| 1 | High | Low |

For example:

`1010`

Becomes:

`10 01 10 01`

Each bit contains a mandatory mid-bit transition. This assists clock recovery and synchronization.

The cost is additional signaling transitions and a higher signal-element rate relative to the original bit sequence.

The implementation validates the required transition during decoding. Invalid signal pairs raise an error rather than being silently accepted.

The encoding is an educational representation and should not be interpreted as the encoding used by every modern Ethernet standard.

### 3.5 Transmission duration

For a bit stream containing \(N\) bits and a bit rate of \(R\) bits per second:

\[
T = \frac{N}{R}
\]

For 1,024 bits transmitted at 1 Gbit/s:

\[
T = \frac{1024}{1,000,000,000}
\]

\[
T = 1.024 \times 10^{-6}\text{ seconds}
\]

This represents the ideal serialization time. Actual communication also involves propagation delay, processing, protocol overhead and medium-specific effects.

## 4. Data Link Layer

The Data Link Layer provides communication between devices over a directly connected network link.

Its principal responsibilities include:

- Framing
- Physical addressing
- Error detection
- Medium access control
- Link-level delivery
- Frame handling

The IEEE 802 architecture distinguishes the Logical Link Control (LLC) and Media Access Control (MAC) sublayers.

### 4.1 Logical Link Control

The LLC sublayer provides a logical interface between network-layer protocols and MAC-level communication.

It is associated with protocol identification and certain link-control functions.

### 4.2 Media Access Control

The MAC sublayer handles media access and hardware addressing.

In Ethernet, MAC addresses identify source and destination interfaces within the Layer 2 communication domain.

The MAC sublayer also participates in frame formatting and error detection.

## 5. MAC Addresses

### 5.1 MAC address structure

A conventional Ethernet MAC address contains 48 bits.

It is represented using six hexadecimal octets.

Example:

`00:11:22:33:44:AA`

Each hexadecimal octet represents eight bits.

\[
48 = 6 \times 8
\]

A MAC address is associated with a network interface rather than necessarily identifying an entire physical computer.

### 5.2 MAC address categories

| Category | Description | Example |
|---|---|---|
| Unicast | Identifies one destination interface | `00:11:22:33:44:AA` |
| Multicast | Identifies a group of destinations | `01:00:5E:00:00:01` |
| Broadcast | Identifies all devices in the Layer 2 broadcast domain | `FF:FF:FF:FF:FF:FF` |

The least significant bit of the first octet identifies whether the address is individual or group-oriented.

- Bit value 0: Individual address
- Bit value 1: Group address

The next least significant bit of the first octet indicates whether an address is universally or locally administered.

A locally administered MAC address can be configured by software or network administration.

### 5.3 MAC address learning

Ethernet switches dynamically learn MAC addresses by examining the source address of incoming frames.

For example:

| Source MAC | Incoming port |
|---|---|
| `00:11:22:33:44:AA` | eth0 |
| `00:11:22:33:44:BB` | eth1 |
| `00:11:22:33:44:CC` | eth2 |

The switch records these associations in its MAC address table.

When a source MAC address appears on a different port, the switch updates its learned location. This behavior supports devices that move between network connections.

## 6. Ethernet

Ethernet is a widely deployed family of wired LAN technologies standardized primarily through IEEE 802.3.

It defines physical and MAC-layer communication mechanisms.

### 6.1 Ethernet II frame format

The Ethernet II frame contains the following fields:

| Field | Size | Purpose |
|---|---:|---|
| Destination MAC | 6 bytes | Identifies destination |
| Source MAC | 6 bytes | Identifies sender |
| EtherType | 2 bytes | Identifies encapsulated protocol |
| Payload | 46–1500 bytes | Carries upper-layer information |
| FCS | 4 bytes | Detects transmission errors |

The basic frame structure is:

`Destination MAC → Source MAC → EtherType → Payload → FCS`

The standard Ethernet frame size is:

- Minimum: 64 bytes
- Maximum: 1518 bytes

These sizes exclude the preamble and Start Frame Delimiter.

The minimum payload requirement is 46 bytes. Shorter payloads are padded to meet the minimum frame size.

The maximum payload of 1500 bytes corresponds to the conventional Ethernet MTU.

Jumbo frames are supported by some network environments but are not part of the conventional 1518-byte maximum Ethernet frame size.

### 6.2 EtherType

EtherType identifies the protocol encapsulated in the Ethernet payload.

| EtherType | Protocol |
|---|---|
| `0x0800` | IPv4 |
| `0x0806` | ARP |
| `0x86DD` | IPv6 |
| `0x8100` | IEEE 802.1Q VLAN tagging |

An Ethernet frame carrying IPv4 uses EtherType `0x0800`.

### 6.3 Frame Check Sequence

The Ethernet Frame Check Sequence uses CRC-32.

Its purpose is to detect corruption introduced during transmission.

The checksum is calculated over the Ethernet frame header and payload, including padding.

The receiving system recalculates the checksum and compares it with the received FCS.

If the values differ, the frame is considered corrupted and is normally discarded.

CRC is an error-detection mechanism, not an encryption or authentication mechanism.

A valid CRC does not prove that the sender is trusted or that the payload is secure.

### 6.4 CRC-32 implementation

The implementations use the reflected CRC-32 polynomial:

\[
0xEDB88320
\]

The initial CRC register is:

\[
0xFFFFFFFF
\]

The final result is XORed with:

\[
0xFFFFFFFF
\]

The Ethernet FCS is transmitted least-significant byte first.

The Python and C++ implementations calculate CRC-32 directly. JavaScript uses a precomputed lookup table, while Java uses the standard library's CRC-32 implementation.

The PostgreSQL script stores FCS values for auditing but does not independently verify their correctness. Its frame-integrity checks cover structural properties.

## 7. Ethernet Switching

### 7.1 Switch operation

An Ethernet switch connects multiple network devices through separate interfaces.

It examines incoming Ethernet frames and makes forwarding decisions using destination MAC addresses.

The switch maintains a forwarding database, commonly called the MAC address table.

The fundamental workflow is:

`Incoming Frame → Source MAC Learning → Destination MAC Lookup → Forwarding Decision → Outgoing Port`

### 7.2 Unknown unicast flooding

When a switch receives a unicast frame whose destination MAC address is not present in its forwarding table, it does not initially know the correct output port.

It floods the frame through eligible ports in the same Layer 2 forwarding domain, excluding the incoming port.

When the destination device responds, the switch learns its source MAC address and incoming port.

Subsequent frames can then be forwarded selectively.

### 7.3 Known unicast forwarding

When the destination MAC address exists in the forwarding database, the switch forwards the frame through the associated output port.

It does not need to flood the frame to every connected device.

This reduces unnecessary traffic.

### 7.4 Broadcast forwarding

An Ethernet broadcast frame uses:

`FF:FF:FF:FF:FF:FF`

The switch forwards broadcast traffic through eligible ports within the relevant broadcast domain, excluding the ingress port.

Routers and Layer 3 boundaries normally separate broadcast domains.

### 7.5 Multicast forwarding

Multicast addresses identify groups of receivers.

A basic Ethernet switch can flood multicast traffic when it does not have more specific forwarding information.

More advanced switches can use IGMP snooping and multicast forwarding databases to reduce unnecessary multicast traffic.

### 7.6 MAC address aging

Learned MAC entries are not necessarily permanent.

Switches remove entries that have not been refreshed within the configured aging interval.

For example, if the aging interval is 300 seconds, an entry that remains inactive for the configured period becomes eligible for removal.

Aging prevents outdated mappings from remaining indefinitely in the forwarding database.

## 8. Switching Versus Routing

| Characteristic | Layer 2 Switching | Layer 3 Routing |
|---|---|---|
| Primary address | MAC address | IP address |
| Primary data unit | Frame | Packet |
| Main decision | MAC lookup | IP route lookup |
| Main device | Ethernet switch | Router |
| Communication scope | Layer 2 forwarding domain | Between IP networks |
| Main forwarding information | MAC table | Routing table |

A switch and a router solve different forwarding problems.

A Layer 2 switch forwards frames within its Layer 2 domain. A router determines how packets move between IP networks.

Multilayer switches can perform both functions.

## 9. Physical Layer and Data Link Layer Relationship

The two layers work together but have different responsibilities.

| Physical Layer | Data Link Layer |
|---|---|
| Transmits signals | Organizes bits into frames |
| Defines physical characteristics | Defines link-level addressing |
| Handles signal encoding | Handles frame formatting |
| Concerns transmission media | Concerns link-level delivery |
| Deals with signal quality | Detects frame corruption |

The relationship can be represented as:

`Application Data`

`↓`

`Transport and Network Encapsulation`

`↓`

`Ethernet Frame Construction`

`↓`

`Binary Bit Stream`

`↓`

`Physical Signal Encoding`

`↓`

`Transmission Medium`

The receiving device performs the reverse operations.

## 10. Python Implementation

**File:** `physical_data_link.py`

The Python implementation provides an integrated network simulator.

### Main components

| Component | Responsibility |
|---|---|
| `MACAddress` | Validates and normalizes MAC addresses |
| `LineEncoder` | Implements NRZ and Manchester encoding |
| `Signal` | Models transmission characteristics and noise |
| `EthernetFrame` | Builds and validates Ethernet frames |
| `NetworkInterface` | Maintains interface state and counters |
| `EthernetSwitch` | Learns MAC addresses and forwards frames |
| `NetworkTests` | Validates important network behavior |

### Implementation decisions

The `MACAddress` class is immutable through a frozen dataclass. This prevents accidental modification of addresses used as dictionary keys.

The Ethernet frame class separates header construction, payload padding, serialization and FCS calculation.

The switch uses a dictionary-backed MAC table, providing average constant-time address lookup.

The MAC aging operation removes entries whose inactivity exceeds the configured interval.

The simulator demonstrates:

1. Signal encoding and decoding.
2. Ethernet frame construction.
3. FCS calculation.
4. Unknown unicast flooding.
5. Dynamic MAC learning.
6. Known unicast forwarding.
7. Broadcast forwarding.
8. Corrupted frame rejection.
9. Automated validation.

The tests cover address normalization, signal decoding, frame integrity and switching behavior.

## 11. JavaScript Implementation

**File:** `physical_data_link.js`

The JavaScript implementation emphasizes event-driven network operations.

### Main components

| Component | Responsibility |
|---|---|
| `MACAddress` | Address validation |
| `SignalEncoder` | Physical encoding and decoding |
| `CRC32` | Lookup-table checksum calculation |
| `EthernetFrame` | Buffer-based frame processing |
| `EthernetSwitch` | Event-driven switching engine |

### Event-driven architecture

The switch extends Node.js `EventEmitter`.

It publishes events for:

- MAC address learning
- MAC address expiration
- Frame forwarding
- Frame processing
- Port-state changes

This design separates network operations from monitoring and reporting.

For example, a monitoring component can subscribe to `macLearned` without modifying the switching algorithm.

JavaScript `Map` provides efficient MAC address lookup, while `Buffer` handles binary Ethernet frame data.

The implementation uses assertions to verify signal round trips, checksum rejection and network forwarding.

The code also handles disabled interfaces, invalid frames and unavailable ports.

## 12. C++17 Implementation

**File:** `physical_data_link.cpp`

The C++ implementation focuses on efficient domain modeling and a self-contained switching engine.

### Main components

| Component | Responsibility |
|---|---|
| `MACAddress` | Six-byte hardware address |
| `PhysicalLayer` | Signal encoding and decoding |
| `CRC32` | Checksum calculation |
| `EthernetFrame` | Frame serialization and FCS validation |
| `SwitchPort` | Port state and counters |
| `MACEntry` | Learned forwarding information |
| `EthernetSwitch` | Forwarding decisions and MAC aging |

### Design decisions

The MAC address uses `std::array<Byte, 6>` because its size is fixed.

The switch uses `std::map` for its forwarding table. This provides ordered storage and logarithmic lookup.

The frame uses `std::vector` for variable-length payload and serialized data.

The implementation uses exceptions for invalid addresses, malformed signals, frame corruption and unavailable ports.

Its switching algorithm distinguishes:

- Known unicast traffic
- Unknown unicast traffic
- Multicast traffic
- Broadcast traffic
- Disabled ports

The switch also maintains counters for received, forwarded, flooded and dropped traffic.

## 13. Java 17 Implementation

**File:** `NetworkLayerSimulation.java`

The Java implementation models an enterprise network switch through explicit domain types and a service-oriented structure.

### Main components

| Component | Responsibility |
|---|---|
| `MacAddress` | Immutable MAC address record |
| `PhysicalLayer` | Signal encoding and decoding |
| `EthernetFrame` | Validated Ethernet frame |
| `SwitchPolicy` | Network forwarding restrictions |
| `SwitchPort` | Interface state and operational counters |
| `MACLearningEntry` | Dynamic forwarding information |
| `EthernetSwitchService` | Switching and forwarding operations |
| `SwitchReport` | Operational statistics |

### Enterprise policy evaluation

The `SwitchPolicy` record controls:

- Broadcast forwarding
- Multicast forwarding
- Maximum interface count

The switching service checks the applicable policy before processing traffic.

A disabled port cannot participate in normal forwarding.

The `EthernetFrame` class protects its internal payload by cloning arrays during construction and retrieval.

The implementation uses immutable records for MAC addresses, learned entries and reports.

This reduces accidental state changes and makes the domain model easier to reason about.

The service also separates port registration, port administration, MAC learning, aging, forwarding and reporting.

## 14. PostgreSQL Implementation

**File:** `physical_data_link.sql`

The database models network infrastructure and records Ethernet operations for operational analysis.

### 14.1 Relational domain model

The primary relationships are:

`Network Devices → Network Interfaces → Signal Transmissions`

`Ethernet Frames → Frame Ingress → Network Interfaces`

`Ethernet Frames → Frame Egress → Network Interfaces`

`Network Devices → MAC Learning Table`

`Network Devices → Switching Policies`

`Ethernet Frames → Forwarding Decisions`

### 14.2 Database objects

| Database object | Purpose |
|---|---|
| `network_devices` | Network device inventory |
| `network_interfaces` | Interface configuration and MAC addresses |
| `signal_transmissions` | Physical transmission metadata |
| `ethernet_frames` | Frame metadata and payload |
| `frame_ingress` | Incoming frame records |
| `frame_egress` | Outgoing frame records |
| `mac_learning_table` | Learned MAC-to-interface mappings |
| `switching_policies` | Forwarding configuration |
| `forwarding_decisions` | Auditable forwarding decisions |

### 14.3 Integrity controls

The schema uses:

- Primary keys
- Foreign keys
- Unique constraints
- Check constraints
- Generated columns
- Validation triggers
- Indexes

The frame-validation trigger checks source and destination addresses and verifies payload-length consistency.

The ingress-validation trigger ensures that the interface exists, belongs to the expected device and is operational.

The database stores the FCS value but does not calculate CRC-32 itself.

### 14.4 MAC learning

The `learn_mac_address` function inserts a new MAC-to-interface mapping or updates an existing mapping.

PostgreSQL's `ON CONFLICT` mechanism handles an existing device/MAC combination.

This models address movement between switch ports.

### 14.5 MAC aging

The `expire_mac_entries` procedure removes stale MAC mappings according to the configured switching policy.

It uses timestamps to determine inactivity.

### 14.6 Forwarding evaluation

The `evaluate_frame_forwarding` function evaluates the destination MAC and applicable policy.

Possible outcomes include:

| Decision | Meaning |
|---|---|
| `UNICAST` | Forward to a learned destination interface |
| `FLOOD` | Forward unknown unicast traffic to eligible interfaces |
| `BROADCAST` | Distribute broadcast traffic |
| `MULTICAST` | Distribute multicast traffic |
| `DROP` | Reject traffic |
| `FILTERED` | Reject traffic due to policy |

### 14.7 Reporting

The SQL script provides reporting views for:

- Learned MAC addresses
- Ethernet frame information
- Forwarding decisions
- Interface utilization
- Unicast and flooding statistics
- Broadcast and multicast activity
- Policy configuration

The script includes transaction and savepoint handling to demonstrate controlled policy changes.

## 15. Important Technical Distinctions

### 15.1 MAC address versus IP address

A MAC address is used for link-level delivery. An IP address identifies a logical network-layer endpoint.

MAC addresses are relevant to local Layer 2 forwarding, whereas IP addresses are used for communication across IP networks.

### 15.2 Frame versus packet

A frame is the Data Link Layer data unit.

A packet is commonly associated with the Network Layer.

An Ethernet frame can carry an IP packet as its payload.

### 15.3 CRC versus encryption

CRC detects accidental transmission errors.

Encryption protects confidentiality, and cryptographic authentication mechanisms establish message integrity and authenticity.

CRC must not be treated as a security control.

### 15.4 Hub versus switch

A traditional Ethernet hub repeats incoming signals to its other ports.

A switch learns MAC addresses and selectively forwards frames.

A switch provides separate collision domains per port in conventional switched Ethernet. Modern full-duplex Ethernet does not use the traditional shared-medium collision behavior.

### 15.5 Collision detection and modern Ethernet

Traditional shared, half-duplex Ethernet used CSMA/CD:

1. Carrier sensing
2. Transmission
3. Collision detection
4. Backoff
5. Retransmission

Modern switched full-duplex Ethernet eliminates the need for CSMA/CD because devices have dedicated bidirectional links and do not share a collision domain.

## 16. Performance and Complexity

The following table describes the principal operations in the implementations.

| Operation | Typical complexity |
|---|---|
| MAC address validation | O(1) |
| NRZ encoding | O(n) |
| Manchester encoding | O(n) |
| CRC-32 calculation | O(n) |
| Frame serialization | O(n) |
| Hash-based MAC lookup | Average O(1) |
| Ordered MAC lookup | O(log n) |
| MAC table aging | O(m) |
| Unknown unicast flooding | O(p) |

Where:

- `n` is the number of bits or bytes processed.
- `m` is the number of learned MAC entries.
- `p` is the number of switch ports.

The Python and JavaScript implementations use hash-based lookup.

The C++ implementation uses an ordered map.

The Java implementation uses `HashMap` for learned MAC addresses.

The SQL implementation uses indexed relational lookups.

Hardware switches commonly use specialized forwarding hardware to perform high-speed MAC table lookups and frame processing.

## 17. Security Considerations

Ethernet switching introduces several security concerns.

### MAC spoofing

An attacker can transmit frames using a forged source MAC address.

A switch may learn the forged address and update its forwarding database.

Possible controls include:

- Port security
- MAC address limits
- Static MAC entries where appropriate
- Network access control
- Monitoring MAC address movement

### MAC flooding

An attacker can generate frames with numerous different source MAC addresses to exhaust the switch's forwarding-table capacity.

Potential controls include:

- MAC learning limits
- Rate limiting
- Port security
- Monitoring abnormal address learning

### Broadcast storms

Excessive broadcast traffic can consume network bandwidth and processing capacity.

Controls include:

- Broadcast storm control
- VLAN segmentation
- Spanning Tree Protocol
- Loop prevention
- Network monitoring

### VLAN security

VLANs separate Layer 2 broadcast domains logically.

Correct VLAN configuration is important because incorrect trunk or access-port settings can create unintended network access.

### Frame integrity

CRC detects accidental corruption but does not prevent malicious frame modification.

Security-sensitive environments require additional mechanisms such as authenticated access, secure network protocols and appropriate cryptographic protection.

## 18. Limitations of the Implementations

These programs are educational software simulations, not physical Ethernet drivers or hardware switch operating systems.

| Component | Limitation |
|---|---|
| Signal encoding | Uses simplified logical signal levels |
| Ethernet frame | Does not implement physical preamble or SFD transmission |
| CRC | Detects errors but does not provide authentication |
| Switching | Does not implement VLAN-aware forwarding |
| MAC learning | Does not implement full hardware switch behavior |
| Multicast | Does not implement IGMP snooping |
| Physical transmission | Does not model real electrical or optical waveforms |
| Database | Records forwarding decisions rather than performing hardware forwarding |

The simplified switch model assumes that each learned MAC address belongs to one forwarding domain.

A production VLAN-aware switch must incorporate the VLAN identifier into its forwarding-table key. Otherwise, identical MAC addresses in different VLANs can produce incorrect forwarding behavior.

The SQL implementation uses sample FCS values for demonstration. It does not establish that those values correspond to the stored frame payloads.

The implementations also do not provide a complete IEEE 802.3 conformance test suite.

## 19. Execution Requirements

| Deliverable | Runtime | Dependencies |
|---|---|---|
| Python | Python 3.10+ | Standard library |
| JavaScript | Node.js 18+ | Node.js standard library |
| C++17 | C++17 compiler | Standard library |
| Java | Java 17 | Standard library |
| PostgreSQL | PostgreSQL 15+ | PostgreSQL database |

The programs execute their own demonstrations and validation checks.

The PostgreSQL script creates the `network_lab` schema, its relational objects, sample data, functions, procedures, triggers, indexes and reporting views.

## 20. Learning Outcomes

The implementations establish practical understanding of the relationship between physical transmission and link-level communication.

The central technical relationships are:

- Signals represent binary information on a physical medium.
- Encoding determines how bits are represented as signal states.
- Ethernet organizes link-level information into frames.
- MAC addresses identify link-layer source and destination interfaces.
- CRC-32 detects accidental corruption.
- Switches learn source MAC addresses.
- Known unicast frames are forwarded selectively.
- Unknown unicast frames can be flooded.
- Broadcast and multicast traffic follow different forwarding rules.
- MAC aging removes stale forwarding information.
- Switching policies control which traffic is permitted.
- Database constraints and transactions support reliable network-operation records.

These concepts form the foundation for studying Ethernet networks, LAN architecture, network interface behavior, Layer 2 switching and enterprise network administration.
