# Network Layer Engineering: IP Addressing, Subnetting and Routing

## 1. Network Layer Fundamentals

The network layer is responsible for delivering packets between devices across interconnected networks. It provides logical addressing, routing, packet forwarding and communication between different network segments.

In the OSI reference model, the network layer is Layer 3. In the TCP/IP architecture, its responsibilities are primarily associated with the Internet layer.

The central engineering problem is determining how a packet travels from its source network to its destination network.

The implementations cover five connected areas:

- IP addressing and address representation.
- IPv4 and IPv6 addressing.
- Subnetting and CIDR.
- Routing tables and route selection.
- Packet forwarding and interface management.

## 2. IP Addressing

An IP address identifies a network-layer endpoint within an IP network.

An address contains two logical components:

| Component | Purpose |
|---|---|
| Network portion | Identifies the network or subnet |
| Host portion | Identifies an address within that network |

The prefix length determines how many bits belong to the network portion.

For example, `192.168.10.20/24` has a 24-bit network prefix and an 8-bit host portion.

Its corresponding network is `192.168.10.0/24`.

IP addresses are logical addresses. They are different from MAC addresses, which identify interfaces at the data-link layer.

### 2.1 IPv4

IPv4 uses 32-bit addresses, normally represented as four decimal octets.

Example:

`192.168.10.20`

Each octet contains eight bits and has a decimal range of 0 to 255.

IPv4 provides approximately 4.29 billion possible address values.

Important IPv4 characteristics:

- 32-bit addressing.
- Dotted-decimal representation.
- Subnet masks.
- Broadcast addressing.
- Private and public address spaces.
- Variable-length subnet prefixes.
- Network Address Translation commonly used in private networks.

Private IPv4 ranges include:

| Private network | Address range |
|---|---|
| Class A private | `10.0.0.0/8` |
| Class B private | `172.16.0.0/12` |
| Class C private | `192.168.0.0/16` |

These ranges are reserved for private network use and are not globally routed as public Internet destinations.

The historical class-based addressing system is largely replaced by Classless Inter-Domain Routing.

### 2.2 IPv6

IPv6 uses 128-bit addresses.

Example:

`2001:db8:100::10`

An IPv6 address contains eight hexadecimal groups, each representing 16 bits. Consecutive zero groups can be compressed using `::`.

IPv6 provides a substantially larger address space than IPv4.

Important characteristics:

- 128-bit addressing.
- Hexadecimal notation.
- Prefix-based network identification.
- No broadcast addressing.
- Multicast and anycast communication.
- Neighbor Discovery Protocol.
- Stateless Address Autoconfiguration support.
- Extension headers.
- Improved support for large-scale address allocation.

IPv6 does not use IPv4-style broadcast addresses. Multicast provides group communication.

The documentation prefix `2001:db8::/32` is used for examples and documentation.

### 2.3 IPv4 and IPv6 Comparison

| Property | IPv4 | IPv6 |
|---|---|---|
| Address size | 32 bits | 128 bits |
| Representation | Decimal | Hexadecimal |
| Address separation | Dots | Colons |
| Header size | Variable, minimum 20 bytes | Fixed 40-byte base header |
| Broadcast | Supported | Not supported |
| Address resolution | ARP | Neighbor Discovery |
| Fragmentation | Routers and source hosts | Source host |
| Header checksum | Present | Absent |
| Address configuration | Manual, DHCP | Manual, SLAAC, DHCPv6 |
| Typical prefix | `/24` | `/64` |

Dual-stack networking allows IPv4 and IPv6 to operate on the same infrastructure.

The Python, JavaScript, Java and PostgreSQL implementations support both address families in their respective network models.

The C++ implementation concentrates on IPv4 routing and uses a 32-bit address representation.

## 3. Subnetting

Subnetting divides a larger IP network into smaller logical networks.

It improves address allocation, network organization, traffic separation and routing administration.

Consider:

`192.168.10.0/24`

The prefix `/24` means that the first 24 bits identify the network.

The remaining eight bits identify addresses within the subnet.

<text/>

### 3.1 Subnet mask

The subnet mask for `/24` is:

`255.255.255.0`

Binary representation:

`11111111.11111111.11111111.00000000`

A logical AND operation between an IP address and its subnet mask identifies the network address.

Example:

| Property | Value |
|---|---|
| IP address | `192.168.10.20` |
| Prefix | `/24` |
| Network | `192.168.10.0` |
| Broadcast | `192.168.10.255` |
| First traditional usable host | `192.168.10.1` |
| Last traditional usable host | `192.168.10.254` |
| Total addresses | 256 |
| Traditional usable hosts | 254 |

For conventional IPv4 subnets with prefixes from `/0` through `/30`, the network and broadcast addresses are generally excluded from ordinary host assignment.

A `/31` is useful for point-to-point links, while `/32` identifies a single IPv4 address.

IPv6 does not have an IPv4-style broadcast address.

### 3.2 Subnet capacity

The total number of addresses in an IP network is:

`2^(address_bits - prefix_length)`

For IPv4:

`2^(32 - prefix)`

For IPv6:

`2^(128 - prefix)`

For example:

`192.168.10.0/26`

Total addresses:

`2^(32 - 26) = 64`

Traditional usable IPv4 host addresses:

`64 - 2 = 62`

### 3.3 Subnet division

A `/24` network can be divided into four `/26` subnets.

| Subnet | Address range | Prefix |
|---|---|---|
| 1 | `192.168.10.0` to `192.168.10.63` | `/26` |
| 2 | `192.168.10.64` to `192.168.10.127` | `/26` |
| 3 | `192.168.10.128` to `192.168.10.191` | `/26` |
| 4 | `192.168.10.192` to `192.168.10.255` | `/26` |

Each subnet has 64 addresses and 62 traditionally usable host addresses.

The Python implementation uses `ipaddress` to calculate subnet boundaries, enumerate subnets and summarize address ranges.

JavaScript uses `BigInt` to perform address arithmetic without losing precision for 128-bit IPv6 values.

Java uses `BigInteger` for the same reason.

The C++ implementation uses unsigned 32-bit integers for IPv4 calculations.

## 4. CIDR: Classless Inter-Domain Routing

CIDR represents network prefixes using slash notation.

Examples:

- `10.0.0.0/8`
- `172.16.0.0/16`
- `192.168.10.0/24`
- `192.168.10.64/26`
- `2001:db8:100::/64`

CIDR replaced the limitations of historical fixed network classes.

Its principal benefits are:

- Flexible network allocation.
- Efficient address utilization.
- Route aggregation.
- Reduced routing-table growth.
- Support for variable-length subnet masks.

### 4.1 Route aggregation

Several adjacent networks can sometimes be represented by one larger prefix.

For example:

- `192.168.0.0/24`
- `192.168.1.0/24`
- `192.168.2.0/24`
- `192.168.3.0/24`

These networks can be represented by:

`192.168.0.0/22`

Aggregation is possible because the four networks share the same first 22 bits.

The Python implementation uses `ipaddress.collapse_addresses()` for aggregation.

## 5. Routing

Routing determines the path used to transport IP packets between networks.

A router maintains routing information and selects an outgoing interface and, where necessary, a next-hop router.

A routing table typically contains:

| Field | Purpose |
|---|---|
| Destination | Target network |
| Prefix | Destination network size |
| Next hop | Gateway receiving the packet |
| Interface | Outgoing network interface |
| Metric | Preference among otherwise comparable routes |
| State | Whether the route is active |

### 5.1 Directly connected routes

A directly connected route represents a network attached to a router interface.

For example:

`192.168.10.0/24`

A router with interface `192.168.10.1/24` can communicate directly with destinations on that subnet, subject to local network and address-resolution behavior.

A next-hop gateway is not necessary for such a route.

### 5.2 Static routes

Static routes are manually configured.

Example:

`172.16.10.0/24 via 10.0.0.3`

The router sends packets for that destination network to the specified next-hop address.

Static routes are useful for:

- Small networks.
- Controlled network topologies.
- Default gateways.
- Specific administrative paths.
- Networks with predictable connectivity.

Their limitation is that network changes may require manual route updates.

### 5.3 Default routes

A default route is used when no more-specific route matches a destination.

IPv4:

`0.0.0.0/0`

IPv6:

`::/0`

A default route provides a fallback forwarding path.

It does not override a more-specific matching route.

## 6. Longest-Prefix Matching

Longest-Prefix Matching is a central routing mechanism.

When multiple routing entries match a destination, the router chooses the route with the longest matching network prefix.

Consider this routing table:

| Destination | Next hop | Metric |
|---|---|---:|
| `0.0.0.0/0` | `10.0.0.254` | 200 |
| `172.16.0.0/16` | `10.0.0.2` | 50 |
| `172.16.10.0/24` | `10.0.0.3` | 10 |

Destination:

`172.16.10.50`

All three entries match the destination.

The selected route is:

`172.16.10.0/24`

The `/24` route is more specific than `/16` and `/0`.

The metric is considered when routes have the same prefix length and otherwise satisfy the routing selection criteria.

The metric does not replace longest-prefix matching.

### 6.1 Routing lookup workflow

The implemented routing engines follow this logical process:

1. Validate the destination address.
2. Determine its address family.
3. Identify active routes matching that family.
4. Test destination membership in each network.
5. Exclude routes with unavailable interfaces.
6. Select the longest prefix.
7. Use the lowest metric to break equal-prefix ties.
8. Determine the next hop.
9. Check forwarding constraints.
10. Produce a forwarding decision or failure.

For a simple routing table containing `R` entries, a linear lookup requires O(R) route examinations.

Production routers commonly use optimized forwarding structures, including trie-based lookup and specialized hardware tables.

## 7. Packet Forwarding

Routing and forwarding are related but distinct operations.

Routing determines the appropriate path and builds or maintains routing information.

Forwarding applies a selected route to an individual packet.

The forwarding process includes:

- Receiving a packet.
- Validating relevant packet information.
- Inspecting the destination address.
- Performing a routing-table lookup.
- Selecting an outgoing interface.
- Determining the next-hop address.
- Checking interface availability.
- Applying packet-size and MTU constraints.
- Sending the packet towards the next hop.

The implementations simulate forwarding decisions. They do not transmit actual network packets.

### 7.1 Next-hop selection

For directly connected routes, the destination is normally the next-hop address.

For indirect routes, the routing table identifies a gateway.

The outgoing interface determines the link through which the packet is transmitted.

### 7.2 MTU

Maximum Transmission Unit specifies the maximum packet size supported by an interface at the relevant network-layer boundary.

The implementations check packet size against the configured MTU.

IPv4 and IPv6 have different fragmentation behavior.

IPv4 routers may fragment packets when permitted by the packet's fragmentation settings.

IPv6 routers do not fragment packets. Source nodes perform fragmentation using the appropriate extension header when required.

The programs deliberately reject packets exceeding the configured MTU instead of simulating fragmentation or Path MTU Discovery.

The packet-size checks are simplified models and do not implement all header options, extension headers or encapsulation overhead.

## 8. Python Implementation

The Python program provides a network-management model using the standard-library `ipaddress` module.

### 8.1 Main components

| Component | Responsibility |
|---|---|
| `Interface` | Represents an IPv4 or IPv6 interface |
| `Route` | Stores a destination, gateway, metric and state |
| `RoutingTable` | Stores routes and performs route lookup |
| `NetworkManager` | Coordinates interfaces and packet forwarding |
| `subnet_analysis()` | Calculates subnet properties |
| `split_subnets()` | Divides a network into smaller networks |
| `summarize_addresses()` | Aggregates adjacent addresses |
| `save_report()` | Writes a JSON network inventory |

### 8.2 Design decisions

Python's `ipaddress` module handles address parsing, CIDR validation, subnet membership and address arithmetic.

Dataclasses provide structured domain objects.

Enums distinguish routing states and address families.

Custom exceptions separate invalid addresses from missing routes and other network failures.

The routing engine uses longest-prefix matching followed by metric comparison.

The JSON report provides a persistent record of configured interfaces and routes.

### 8.3 Failure conditions

The script handles:

- Invalid IPv4 addresses.
- Invalid IPv6 addresses.
- Invalid CIDR prefixes.
- Mixed address families.
- Duplicate interfaces.
- Missing interfaces.
- Disabled interfaces.
- Unavailable routes.
- Invalid gateways.
- Invalid MTU values.

The implementation does not implement dynamic routing protocols or actual packet transmission.

## 9. JavaScript Implementation

The JavaScript program uses Node.js capabilities to implement an event-driven router.

### 9.1 Main components

| Component | Responsibility |
|---|---|
| `Router` | Manages interfaces and routes |
| `NetworkInterface` | Represents an outgoing interface |
| `parseCIDR()` | Validates CIDR notation |
| `ipv4ToBigInt()` | Converts IPv4 addresses into numeric values |
| `ipv6ToBigInt()` | Converts IPv6 addresses into numeric values |
| `findRoute()` | Performs longest-prefix matching |
| `forwardPacket()` | Processes asynchronous forwarding requests |

### 9.2 BigInt address representation

JavaScript's ordinary `Number` type cannot represent all 128-bit IPv6 values precisely.

The implementation uses `BigInt` to perform exact address arithmetic.

This supports:

- IPv4 network calculations.
- IPv6 network calculations.
- Prefix masks.
- Subnet membership.
- Address ranges.
- Subnet division.

The `net` module validates literal addresses without relying on DNS resolution.

### 9.3 Event-driven behavior

The router extends Node.js `EventEmitter`.

It emits events when:

- Interfaces are added.
- Routes are added.
- Interface states change.
- Packets are forwarded.

The asynchronous forwarding operation uses a Promise and `setImmediate()` to simulate an asynchronous processing boundary.

This is a simulation, not a real network transport mechanism.

### 9.4 Operational considerations

The implementation limits subnet enumeration to 4,096 networks.

This prevents accidental creation of excessively large result arrays.

It also records forwarding statistics and writes a JSON report.

## 10. C++17 Implementation

The C++ program implements an IPv4 routing engine with explicit address and network representations.

### 10.1 Main components

| Component | Responsibility |
|---|---|
| `IPv4Address` | Parses and represents IPv4 addresses |
| `IPv4Network` | Represents CIDR networks |
| `NetworkInterface` | Models interface configuration |
| `Route` | Stores route information |
| `Router` | Evaluates routing and forwarding |
| `ForwardingResult` | Represents the selected forwarding decision |

### 10.2 Binary address representation

An IPv4 address fits inside an unsigned 32-bit integer.

For example:

`192.168.10.1`

is represented by combining its four octets using bit shifting.

This makes subnet operations efficient.

The implementation uses:

- Bitwise AND for network identification.
- Bitwise OR for broadcast calculations.
- Bit shifting for subnet masks.
- Unsigned arithmetic for address ranges.
- STL containers for interfaces and routes.

### 10.3 Route-selection algorithm

The routing engine scans available routes.

For each route, it:

1. Checks whether the route is active.
2. Checks whether the destination belongs to the route.
3. Checks whether the outgoing interface is operational.
4. Compares prefix lengths.
5. Uses metric values for equal-prefix candidates.

The route lookup uses O(R) time, where R is the number of configured routes.

The program uses no third-party libraries.

### 10.4 Scope limitation

This C++ implementation focuses on IPv4.

It does not implement IPv6 parsing, dynamic routing, packet capture, actual packet transmission, ARP, Neighbor Discovery or fragmentation.

## 11. Java 17 Implementation

The Java program models an enterprise-oriented dual-stack network service.

It uses Java records, enums, collections, interfaces and service classes.

### 11.1 Domain model

| Type | Responsibility |
|---|---|
| `IpAddress` | Represents a validated IP address |
| `CidrNetwork` | Stores network and prefix information |
| `NetworkInterface` | Models interface configuration and state |
| `Route` | Represents a routing-table entry |
| `ForwardingDecision` | Stores the forwarding result |
| `RoutingPolicy` | Defines route eligibility |
| `ActiveInterfacePolicy` | Implements the active-interface policy |
| `RouterService` | Manages routing and forwarding |

### 11.2 BigInteger

Java's `BigInteger` provides arbitrary-precision integer arithmetic.

This is important for IPv6 because an IPv6 address requires 128 bits.

A signed 32-bit or 64-bit integer cannot represent the complete address space.

The implementation converts address bytes into positive `BigInteger` values and performs exact mask operations.

### 11.3 Policy-based design

The `RoutingPolicy` interface separates route-selection eligibility from the routing service.

`ActiveInterfacePolicy` checks:

- Route state.
- Interface state.
- Address-family compatibility.

This makes routing-policy behavior explicit and easier to test.

### 11.4 State management

Interfaces can transition between:

- `UP`
- `DOWN`

A route is eligible only when it is active and its outgoing interface is operational.

The implementation checks the policy during route creation and lookup.

### 11.5 Enterprise considerations

The design uses immutable records for addresses, networks, routes and forwarding decisions.

The service class owns mutable interface and routing collections.

The model validates gateway reachability through the outgoing interface subnet.

It does not implement concurrent configuration transactions, distributed routing control planes or real network I/O.

## 12. PostgreSQL Implementation

The PostgreSQL script provides a relational model for managing network infrastructure and forwarding decisions.

PostgreSQL provides native network data types that are particularly useful for this domain.

### 12.1 Network data types

| Type | Purpose |
|---|---|
| `INET` | Stores IPv4 or IPv6 host addresses |
| `CIDR` | Stores IPv4 or IPv6 network prefixes |
| `MACADDR` | Stores hardware addresses |

These types support native network operations and address-family-aware comparisons.

Examples of useful operators include:

| Operation | Purpose |
|---|---|
| `<<=` | Tests whether an address or network is contained by another network |
| `>>=` | Tests the reverse containment relationship |
| `&&` | Tests network overlap |
| `network()` | Calculates the network address |
| `broadcast()` | Calculates an IPv4 broadcast address |
| `family()` | Identifies the address family |
| `masklen()` | Returns the prefix length |
| `host()` | Extracts the host address |

### 12.2 Relational schema

The database contains the following principal tables:

| Table | Responsibility |
|---|---|
| `routers` | Network-device inventory |
| `network_interfaces` | Physical or logical interfaces |
| `interface_addresses` | IPv4 and IPv6 interface addresses |
| `routes` | Static routing entries |
| `forwarding_logs` | Packet forwarding decisions and failures |

Foreign keys preserve relationships between routers, interfaces, addresses and routes.

Check constraints enforce valid MTU values, nonnegative metrics, matching address families and valid packet sizes.

### 12.3 Route integrity

The `validate_route()` trigger checks:

- The selected router exists.
- The outgoing interface belongs to that router.
- The router is enabled.
- The interface is operational when activating a route.
- The gateway uses the correct address family.
- The gateway is reachable through an enabled interface address.

The interface-state trigger deactivates active routes when an interface becomes unavailable.

This is an explicit integrity policy for the database model.

### 12.4 Longest-prefix matching in SQL

The `lookup_route()` function selects a matching destination using:

1. Router identity.
2. Active route state.
3. Active interface state.
4. Address-family compatibility.
5. Network containment.
6. Descending prefix length.
7. Ascending metric.

The central ordering rule is:

`ORDER BY masklen(destination) DESC, metric ASC`

This models longest-prefix matching and metric-based tie-breaking.

### 12.5 Forwarding procedure

The `forward_packet()` procedure records successful and unsuccessful forwarding decisions.

Possible outcomes include:

- `FORWARDED`
- `NO_ROUTE`
- `INTERFACE_DOWN`
- `MTU_EXCEEDED`
- `INVALID_SOURCE`

The forwarding log makes network failures available for investigation and reporting.

### 12.6 Database performance

The script creates:

- A GiST index on interface network addresses.
- A GiST index on route destinations.
- A partial B-tree index for active route lookup.
- A router-and-state index.
- Time-based forwarding-log indexes.
- A partial index for forwarding failures.

GiST indexes support network containment operations.

B-tree indexes support filtering and ordering operations.

Actual index effectiveness depends on table size, query selectivity, PostgreSQL statistics and execution plans. Production workloads should be evaluated using `EXPLAIN (ANALYZE, BUFFERS)`.

### 12.7 Transaction handling

The SQL script uses an explicit transaction.

The route-management example uses a savepoint to demonstrate a reversible configuration boundary.

For production systems, route updates should be performed with appropriate transaction isolation and concurrency controls.

## 13. Network Layer Workflow

The implementations represent the following logical workflow:

    IP Address
        |
        v
    Address Validation
        |
        v
    Network and Prefix Identification
        |
        v
    Subnet Membership
        |
        v
    Routing Table Lookup
        |
        v
    Longest-Prefix Matching
        |
        v
    Metric-Based Tie Breaking
        |
        v
    Interface Availability Check
        |
        v
    Next-Hop Selection
        |
        v
    MTU Validation
        |
        v
    Forwarding Decision
        |
        v
    Operational Logging

The workflow separates address validation, routing decisions and forwarding checks.

These are different responsibilities and should not be treated as a single operation.

## 14. Important Network Layer Distinctions

| Concept | Meaning |
|---|---|
| IP address | Logical endpoint address |
| Network address | Identifier of an IP subnet |
| Prefix length | Number of network bits |
| Subnet mask | IPv4 representation of the network prefix |
| CIDR | Classless network-prefix notation |
| Subnetting | Dividing a network into smaller networks |
| Aggregation | Combining adjacent prefixes into a larger route |
| Routing | Determining a forwarding path |
| Forwarding | Applying a selected route to a packet |
| Next hop | The next router or destination on the selected path |
| Metric | Route preference value |
| MTU | Maximum supported packet size at an interface |
| Default route | Fallback route for otherwise unmatched destinations |

### Routing versus forwarding

Routing concerns path determination and routing information.

Forwarding concerns the actual decision applied to an individual packet.

A routing table can contain a valid route while forwarding still fails because an interface is unavailable or the packet exceeds an interface constraint.

### IPv4 versus IPv6 subnetting

Both address families use prefix-based subnetting.

The fundamental difference is address width.

IPv4 uses 32 bits, whereas IPv6 uses 128 bits.

The same CIDR concepts apply to both, but address representation, broadcast behavior, address resolution and fragmentation rules differ.

## 15. Security and Operational Considerations

Network-layer engineering must consider security and reliability.

Important controls include:

- Rejecting malformed IP addresses.
- Validating address-family compatibility.
- Preventing invalid gateway assignments.
- Restricting route configuration permissions.
- Monitoring interface-state changes.
- Recording forwarding failures.
- Validating packet-size constraints.
- Protecting management interfaces.
- Preventing unauthorized route modifications.
- Monitoring unexpected route changes.
- Using authenticated and encrypted management protocols.
- Applying ingress and egress filtering where appropriate.

A production routing system must also address routing-protocol authentication, control-plane protection, route filtering, redundancy, failover and network segmentation.

A database containing routing information should not automatically be treated as an authoritative forwarding plane.

Actual routers maintain operational forwarding state independently and use routing software or hardware to process packets.

## 16. Limitations and Engineering Trade-offs

The implementations are educational network-management and routing simulations.

They do not replace operating-system routing stacks or hardware routers.

| Capability | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| IPv4 validation | Yes | Yes | Yes | Yes | Yes |
| IPv6 validation | Yes | Yes | No | Yes | Yes |
| CIDR calculations | Yes | Yes | Yes | Yes | Yes |
| Subnet division | Yes | Yes | Yes | Yes | Native types |
| Route lookup | Yes | Yes | Yes | Yes | Yes |
| Longest-prefix matching | Yes | Yes | Yes | Yes | Yes |
| Interface state | Yes | Yes | Yes | Yes | Yes |
| Metric comparison | Yes | Yes | Yes | Yes | Yes |
| Forwarding simulation | Yes | Yes | Yes | Yes | Yes |
| Actual packet transmission | No | No | No | No | No |
| Dynamic routing protocols | No | No | No | No | No |

Other limitations include:

- No OSPF, BGP, RIP or IS-IS implementation.
- No actual ARP or Neighbor Discovery exchange.
- No packet capture.
- No live interface discovery.
- No complete fragmentation implementation.
- No Path MTU Discovery implementation.
- No routing convergence simulation.
- No real-time forwarding hardware integration.

The routing algorithms use linear route searches in the in-memory implementations. This is suitable for understandable demonstrations but is not the most efficient approach for very large routing tables.

## 17. Execution Requirements

| Deliverable | Runtime | External dependencies |
|---|---|---|
| Python | Python 3.10+ | None |
| JavaScript | Node.js 18+ | None |
| C++ | C++17 compiler | None |
| Java | Java 17 | None |
| PostgreSQL | PostgreSQL 15+ | None |

### Python

Run the script with Python 3:

`python network_layer.py`

The program creates `network_report.json` in the current working directory.

### JavaScript

Run:

`node network_layer.js`

The program creates `network_report.json` in the current working directory.

### C++17

Compile and run:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic network_layer.cpp -o network_layer`

`./network_layer`

### Java 17

Compile:

`javac NetworkLayer.java`

Run:

`java NetworkLayer`

### PostgreSQL

Execute the SQL file using a PostgreSQL client connected to a database in which the executing role has permission to create schemas, tables, types, functions, procedures and triggers.

The script creates its own `network_layer` schema and commits the sample configuration and forwarding records.

The schema creation statement uses `IF NOT EXISTS`, but the script is intended as a fresh-install demonstration rather than a fully repeatable migration system.

## 18. Technical Learning Outcomes

The five implementations demonstrate how network-layer concepts can be represented using different engineering approaches:

- Python emphasizes address manipulation, validation and network simulation.
- JavaScript emphasizes asynchronous processing and event-driven routing.
- C++17 emphasizes efficient IPv4 address arithmetic and explicit route selection.
- Java 17 emphasizes enterprise domain modeling and policy-based routing.
- PostgreSQL emphasizes relational integrity, native network data types, routing queries and operational reporting.

The central technical relationship remains consistent:

**IP addressing identifies network endpoints, subnetting organizes address spaces, CIDR represents network prefixes, routing selects paths, and forwarding applies routing decisions to individual packets.**
