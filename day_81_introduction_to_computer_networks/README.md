# Introduction to Computer Networks

## 1. Network Fundamentals

A computer network is a collection of interconnected devices that communicate and share resources through wired or wireless communication links.

A network enables:
- Communication between computers and servers.
- Sharing of files, printers and applications.
- Access to remote systems.
- Internet connectivity.
- Centralized administration and security.
- Distributed computing and information exchange.

A network requires devices, communication media, addressing, communication protocols and mechanisms for forwarding information.

### Main network components

| Component | Function |
|---|---|
| Host | Sends and receives network information |
| Network interface card | Connects a device to a network |
| Switch | Forwards Ethernet frames within a LAN |
| Router | Connects different IP networks |
| Firewall | Controls network traffic according to security rules |
| Transmission medium | Carries electrical, optical or radio signals |
| Protocol | Defines communication rules |
| IP address | Identifies a network interface logically |
| MAC address | Identifies a network interface at the data-link layer |

## 2. LAN and WAN

### Local Area Network (LAN)

A LAN connects devices within a limited geographical area, such as an office, laboratory, campus building or home.

Characteristics:
- Usually privately managed.
- Supports high-speed local communication.
- Commonly uses Ethernet or Wi-Fi.
- Uses switches to connect devices.
- Can use routers to communicate with other networks.

Example:

Development Computer → Ethernet Switch → Office Router

A computer can communicate with another computer or server within the same LAN without requiring traffic to travel across the public Internet.

### Wide Area Network (WAN)

A WAN connects geographically separated networks.

Examples include:
- Communication between headquarters and branch offices.
- Banking networks connecting multiple cities.
- Enterprise connectivity between data centres.
- Internet service provider infrastructure.

Characteristics:
- Covers large geographical areas.
- Uses routers and telecommunications infrastructure.
- May use leased lines, fibre, MPLS, cellular connectivity or VPN tunnels.
- Usually introduces more latency than local network links.

Example:

Head Office LAN → Office Router → WAN Link → Remote Router → Branch LAN

### LAN and WAN comparison

| Feature | LAN | WAN |
|---|---|---|
| Coverage | Limited geographical area | Large geographical area |
| Ownership | Often privately managed | May involve multiple providers |
| Typical devices | Switches and routers | Routers and provider infrastructure |
| Latency | Generally low | Generally higher |
| Communication | Local devices | Geographically separated networks |
| Example | Office network | Bank branch connectivity |

LAN and WAN describe network scope. They are not different versions of the OSI or TCP/IP models.

## 3. Network Topologies

Network topology describes how devices and communication links are arranged.

### Common topologies

| Topology | Structure | Main characteristic |
|---|---|---|
| Bus | Shared communication medium | Multiple devices use one backbone |
| Star | Devices connect to a central device | Common in Ethernet LANs |
| Ring | Devices form a closed loop | Traffic follows ring connections |
| Mesh | Multiple interconnected paths | Provides alternative communication routes |
| Tree | Hierarchical arrangement | Supports structured expansion |
| Hybrid | Combination of topologies | Used in complex enterprise networks |

A star topology is commonly used in modern office LANs.

Its central switch forwards frames between connected devices.

A mesh topology can provide multiple paths, improving resilience when a link fails.

## 4. Network Communication Models

Network models divide communication into layers.

Each layer has specific responsibilities and interacts with adjacent layers.

The two major reference models are:
- OSI model.
- TCP/IP model.

### 4.1 OSI Model

The Open Systems Interconnection model defines seven conceptual layers.

| Layer | Name | Main responsibility | Examples |
|---|---|---|---|
| 7 | Application | Application-level network services | HTTP, DNS |
| 6 | Presentation | Data representation and encryption | Encoding, TLS-related functions |
| 5 | Session | Session management | Session establishment |
| 4 | Transport | End-to-end transport | TCP, UDP |
| 3 | Network | Logical addressing and routing | IPv4, IPv6, ICMP |
| 2 | Data Link | Frames and local delivery | Ethernet, MAC |
| 1 | Physical | Transmission of bits | Copper, fibre, radio |

**Physical Layer**

Transmits raw bits over a physical or wireless medium.

It deals with:
- Electrical signals.
- Optical signals.
- Radio signals.
- Connectors.
- Transmission rates.
- Physical communication characteristics.

**Data Link Layer**

Provides communication over a directly connected network segment.

Its responsibilities include:
- Frame creation.
- MAC addressing.
- Frame delivery.
- Error detection.
- Media access control.

Ethernet switches primarily operate at this layer.

**Network Layer**

Handles logical addressing and routing between networks.

Its responsibilities include:
- IP addressing.
- Packet forwarding.
- Route selection.
- Fragmentation in applicable protocols.

Routers primarily operate at this layer.

**Transport Layer**

Provides communication between application processes.

TCP provides:
- Reliable delivery.
- Sequencing.
- Acknowledgements.
- Retransmission.
- Flow control.
- Congestion control.

UDP provides:
- Connectionless communication.
- Lower protocol overhead.
- Datagram delivery without built-in reliability guarantees.

**Session Layer**

Describes mechanisms for establishing, maintaining and managing communication sessions.

**Presentation Layer**

Describes data representation, encoding, compression and encryption functions.

**Application Layer**

Provides network services used by applications.

Examples include:
- HTTP for web communication.
- DNS for name resolution.
- SMTP for email transfer.
- DHCP for automatic network configuration.

### 4.2 TCP/IP Model

The TCP/IP model represents the architecture used by Internet communication.

| TCP/IP layer | Corresponding OSI layers | Responsibilities |
|---|---|---|
| Application | 5, 6, 7 | Application protocols and data representation |
| Transport | 4 | Process-to-process communication |
| Internet | 3 | IP addressing and routing |
| Network Access | 1, 2 | Local delivery and physical transmission |

### OSI and TCP/IP distinction

The OSI model is primarily a conceptual reference framework.

The TCP/IP model describes the practical protocol architecture used for Internet communication.

They are related but are not interchangeable.

## 5. Encapsulation and Decapsulation

Encapsulation occurs when data moves down the network layers before transmission.

Each layer adds information required for communication.

Typical encapsulation:

Application Data  
↓  
Transport Segment or Datagram  
↓  
Network Packet  
↓  
Data Link Frame  
↓  
Physical Bits

The reverse process is called decapsulation.

At the receiving device:
- The physical layer receives signals.
- The data-link layer processes frames.
- The network layer examines IP information.
- The transport layer processes TCP or UDP information.
- The application receives the reconstructed data.

### Important terminology

| Term | Meaning |
|---|---|
| Data | Information generated by an application |
| Segment | TCP transport-layer data unit |
| Datagram | Common term for UDP or IP data units |
| Packet | Network-layer data unit |
| Frame | Data-link-layer data unit |
| Bits | Physical representation of information |

## 6. IP Addressing and Subnetting

An IP address identifies a network interface logically for communication.

IPv4 addresses contain 32 bits and are normally represented using four decimal octets.

Example:

`192.168.1.10`

Each octet has a range of 0 to 255.

### Subnet masks

A subnet mask identifies the network and host portions of an IPv4 address.

Example:

`192.168.1.0/24`

The `/24` prefix indicates that the first 24 bits identify the network.

| Property | Value |
|---|---|
| Network address | 192.168.1.0 |
| Subnet mask | 255.255.255.0 |
| Broadcast address | 192.168.1.255 |
| Total addresses | 256 |
| Usable host addresses | 254 |

For an ordinary IPv4 subnet, the number of usable host addresses is:

\(2^{32-p}-2\)

where \(p\) represents the prefix length.

The subtraction accounts for the network and broadcast addresses. This conventional calculation does not apply to every special-purpose prefix, such as `/31` point-to-point networks and `/32` host routes.

### Private IPv4 ranges

| Range | CIDR |
|---|---|
| 10.0.0.0 to 10.255.255.255 | 10.0.0.0/8 |
| 172.16.0.0 to 172.31.255.255 | 172.16.0.0/12 |
| 192.168.0.0 to 192.168.255.255 | 192.168.0.0/16 |

Private addresses are commonly used inside organizations and home networks.

They are not directly globally routable on the public Internet.

## 7. Packet Switching

Packet switching is a communication technique in which information is divided into smaller units called packets.

Packets are transmitted through network devices and communication links.

Each packet carries addressing information needed for delivery.

### Packet-switching workflow

1. An application generates data.
2. The transport layer prepares the data.
3. The network layer creates IP packets.
4. The data-link layer creates frames.
5. Frames are transmitted over a communication link.
6. Switches forward frames within local network segments.
7. Routers inspect IP destinations and select forwarding paths.
8. The destination receives and processes the packets.
9. Transport-layer mechanisms reconstruct the application data when required.

### Store-and-forward switching

A switch receives a complete frame, checks it and forwards it through an appropriate outgoing interface.

### Router forwarding

A router examines the destination IP address and consults its forwarding information.

The router uses the most specific matching route through longest-prefix matching.

For example:

| Destination network | Next hop |
|---|---|
| 10.0.0.0/8 | Router R1 |
| 10.1.0.0/16 | Router R2 |
| 0.0.0.0/0 | Default gateway |

For destination `10.1.2.3`, the `/16` entry is preferred over the `/8` entry because it is more specific.

### Packet switching and circuit switching

| Feature | Packet Switching | Circuit Switching |
|---|---|---|
| Communication | Divided into packets | Dedicated circuit |
| Resource allocation | Shared dynamically | Reserved for connection |
| Routing | May use different paths | Uses established circuit |
| Efficiency | Suitable for bursty traffic | Suitable for continuous reserved communication |
| Example | Internet communication | Traditional telephone circuit networks |

Packet switching is fundamental to modern IP networks.

## 8. Routing and Forwarding

Routing determines suitable paths through a network.

Forwarding moves packets from an incoming interface to an outgoing interface.

These are related but distinct operations.

### Routing

Routing uses routing information to determine reachable networks and preferred paths.

Routing can involve:
- Static routes.
- Dynamic routing.
- Route metrics.
- Administrative distance.
- Routing protocols.

Examples of routing protocols include OSPF, BGP and RIP.

### Forwarding

Forwarding uses the forwarding information base to select the outgoing interface and next hop for an individual packet.

A forwarding decision commonly considers:
- Destination IP address.
- Longest-prefix match.
- Next-hop address.
- Outgoing interface.
- Route availability.

### TTL

IPv4 includes a Time to Live field.

Routers decrement TTL when forwarding a packet.

If TTL reaches zero, the packet is discarded.

This mechanism helps prevent packets from circulating indefinitely because of routing loops.

## 9. Network Performance

Network performance is influenced by several measurements.

| Metric | Meaning |
|---|---|
| Bandwidth | Maximum supported data-transfer capacity |
| Throughput | Actual achieved data-transfer rate |
| Latency | Time taken for information to travel |
| Jitter | Variation in packet delay |
| Packet loss | Percentage of packets that fail to reach the destination |
| Availability | Proportion of time a service is operational |

Bandwidth and throughput are not equivalent.

A 1 Gbps network interface does not guarantee 1 Gbps application throughput.

Actual throughput can be affected by:
- Congestion.
- Protocol overhead.
- Packet loss.
- Hardware limitations.
- Application behaviour.
- Network configuration.

## 10. Implementation Architecture

The five source files provide complementary implementations of the same networking concepts.

| File | Engineering perspective | Main implementation |
|---|---|---|
| Python | Network simulation | Device modelling, topology, packets and path discovery |
| JavaScript | Event-driven networking | Asynchronous transmission and network events |
| C++17 | Packet-switching engine | Domain modelling, routing and forwarding |
| Java 17 | Enterprise network model | Immutable packet objects, services and validation |
| PostgreSQL | Network information management | Relational inventory, packet records and reporting |

### 10.1 Python implementation

The Python program models a network using dataclasses and enumerations.

Important components:

- `NetworkDevice`: Represents hosts, switches and routers.
- `NetworkInterface`: Stores IPv4 and MAC addressing information.
- `NetworkTopology`: Maintains devices and communication links.
- `Packet`: Represents a network packet.
- `RoutingTable`: Implements longest-prefix matching.
- `PacketSwitch`: Simulates packet delivery and network failures.

Breadth-first search is used to find a route with the smallest number of links.

The implementation also evaluates TTL expiration, link availability, bottleneck bandwidth and packet-delivery statistics.

### 10.2 JavaScript implementation

The JavaScript program uses Node.js capabilities.

Important components:

- `EventEmitter` for network events.
- `Map` for device and link storage.
- `Set` for tracking visited devices.
- `Promise` for asynchronous transmission.
- `Packet` for packet validation and metadata.
- `RoutingTable` for forwarding decisions.

Events include:
- `deviceAdded`
- `linkConnected`
- `linkStatusChanged`
- `packetCreated`
- `packetDelivered`
- `packetDropped`
- `transmissionCompleted`

This structure separates network state from event handling.

### 10.3 C++17 implementation

The C++ implementation emphasizes explicit domain types and controlled state management.

Important components:
- `IPv4` for address parsing.
- `Subnet` for address-range validation.
- `NetworkDevice` for network infrastructure.
- `NetworkTopology` for connectivity.
- `RoutingTable` for route selection.
- `PacketSwitch` for packet forwarding.

The topology uses hash-based device lookup and adjacency lists.

Breadth-first search provides route discovery.

Exceptions handle invalid addresses, unavailable links and failed transmissions.

### 10.4 Java 17 implementation

The Java program uses an enterprise-oriented service architecture.

Important components:
- Records for immutable network data.
- Enums for controlled domain states.
- Collections for topology and routing information.
- `NetworkTopology` for network management.
- `RoutingTable` for route selection.
- `PacketSwitch` for transmission processing.
- `TransmissionResult` for delivery outcomes.

Immutable packet records prevent accidental modification of packet identity and addressing information.

Packet forwarding creates updated packet states rather than modifying the original record.

### 10.5 PostgreSQL implementation

The SQL implementation maintains a relational network inventory and packet-processing history.

Its principal entities include:

| Table | Purpose |
|---|---|
| `network_models` | OSI and TCP/IP reference models |
| `network_layers` | Layer definitions |
| `layer_protocols` | Protocol information |
| `networks` | LAN and WAN records |
| `subnets` | IPv4 subnet information |
| `devices` | Hosts, switches, routers and firewalls |
| `network_interfaces` | Interface addresses and MAC addresses |
| `network_links` | Connections between devices |
| `routing_entries` | Routing information |
| `packets` | Packet metadata and delivery states |
| `packet_transmissions` | Packet forwarding history |
| `network_metrics` | Network performance measurements |

The database uses:
- Primary and foreign keys.
- Unique constraints.
- Check constraints.
- Subnet-validation triggers.
- Packet-state transition triggers.
- Routing functions.
- Packet-processing functions.
- Transmission procedures.
- Reporting views.
- Indexes for frequently queried fields.

The database stores packet metadata and simulated transmission records. It does not capture or transmit real network traffic.

## 11. Integrated Network Scenario

The implementations use a small enterprise network containing a head office and a remote office.

### Network topology

PC1  
↓  
SW1  
↓  
R1  
↓  
WAN Link  
↓  
R2  
↓  
SW2  
↓  
SRV1

### Device responsibilities

| Device | Role |
|---|---|
| PC1 | Generates application data |
| SW1 | Forwards local Ethernet frames |
| R1 | Routes traffic from the head office |
| R2 | Routes traffic toward the remote network |
| SW2 | Connects remote local devices |
| SRV1 | Receives application communication |

### Example addressing

| Device | IP address |
|---|---|
| PC1 | 192.168.1.10 |
| R1 | 192.168.1.1 |
| R2 | 10.0.0.1 |
| SRV1 | 10.0.0.10 |

The head office uses `192.168.1.0/24`.

The remote office uses `10.0.0.0/24`.

The WAN connects the two network environments.

### Successful communication

A packet generated by PC1 travels through SW1 and R1, crosses the WAN connection, reaches R2, passes through SW2 and arrives at SRV1.

The simulation calculates:
- Route.
- Remaining TTL.
- Total link latency.
- Bottleneck bandwidth.
- Packet size.
- Delivery status.

### Failure scenarios

The implementations demonstrate two important failure conditions.

**TTL expiration**

A packet with insufficient TTL cannot complete the required forwarding operations.

The packet is discarded.

**WAN link failure**

When the connection between R1 and R2 becomes unavailable, the network cannot find an available path to SRV1.

The transmission is recorded as dropped.

## 12. Performance and Complexity

The implementations use adjacency lists to represent network topology.

For a graph containing \(V\) devices and \(E\) links:

| Operation | Complexity |
|---|---|
| Device lookup using hash maps | Average O(1) |
| Breadth-first search | O(V + E) |
| Routing table linear lookup | O(R) |
| Routing lookup with sorted prefixes | O(R) in the supplied implementations |
| Packet transmission | O(V + E) including route discovery |
| Packet statistics | O(1) per update |

Here, \(R\) represents the number of routing entries.

The supplied simulations prioritize clarity and correctness over production-scale routing performance.

A production routing system would generally maintain optimized forwarding structures, such as prefix tries, and use more sophisticated routing algorithms.

The simulations also use simplified transmission timing. They do not reproduce physical serialization delays, real congestion queues, retransmission timers or operating-system network stacks.

## 13. Security and Reliability Considerations

Network infrastructure requires security controls at multiple levels.

Important considerations include:

- Restricting access to routers and switches.
- Using authenticated network administration.
- Applying firewall rules.
- Separating networks using VLANs and subnet boundaries.
- Monitoring abnormal traffic.
- Protecting routing information.
- Encrypting sensitive communication.
- Validating packet and interface information.
- Maintaining network configuration backups.
- Monitoring link failures and packet loss.

IP addresses and MAC addresses are network identifiers, not authentication credentials.

A valid IP address does not establish that a device is trusted.

Network segmentation and access-control policies should be used to limit unauthorized communication.

## 14. Practical Learning Outcomes

The implementations demonstrate the relationships between:

- Network devices and communication links.
- LAN and WAN architecture.
- OSI and TCP/IP reference models.
- IP addressing and subnetting.
- Encapsulation and decapsulation.
- Switch-based frame forwarding.
- Router-based packet forwarding.
- Routing tables and longest-prefix matching.
- Packet switching and TTL.
- Network availability and performance.
- Event-driven communication.
- Relational network inventory management.

These concepts provide the foundation for understanding how local networks, enterprise infrastructure and the Internet communicate.
