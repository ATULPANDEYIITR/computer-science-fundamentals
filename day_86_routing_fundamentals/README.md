# Routing Fundamentals: Static Routing, Dynamic Routing, Routing Tables and Routing Algorithms

## 1. Technical Scope

Routing is the process of determining how network packets travel from a source network to a destination network across interconnected routers.

A router examines the destination IP address in a packet, consults its forwarding information, selects an appropriate next hop or outgoing interface, and forwards the packet.

Routing is concerned with determining and maintaining paths. Forwarding is the actual process of moving packets through a router.

This project implements four connected areas:

- Static routing and manually configured routes.
- Dynamic routing and automatic route calculation.
- Routing tables and route-selection rules.
- Routing algorithms and network topology evaluation.

The implementations model an enterprise network containing four routers, interconnected links, different link costs, network prefixes, and changing link availability.

## 2. Network Architecture

The example network contains four routers.

    R1 --------2-------- R2
     \                   | \
      \5                 1  \7
       \                 |   \
        R3 -------2----- R4

The numerical values represent link costs.

The network provides multiple paths between routers. This allows shortest-path calculation, route selection, and link-failure testing.

| Link | Cost |
|---|---:|
| R1 to R2 | 2 |
| R1 to R3 | 5 |
| R2 to R3 | 1 |
| R2 to R4 | 7 |
| R3 to R4 | 2 |

The shortest route from R1 to R4 is:

`R1 → R2 → R3 → R4`

Total cost:

`2 + 1 + 2 = 5`

The alternative direct route through R1 and R3 has a cost of 7.

The topology is represented as an adjacency list. Each router maintains information about its directly connected neighbors and link costs.

## 3. Static Routing

Static routing uses manually configured routing entries.

A network administrator specifies:

- Destination network.
- Next-hop IP address or router.
- Outgoing interface.
- Route metric.
- Route preference.

A static route does not automatically discover alternative paths when the network topology changes.

### 3.1 Static route example

Consider router R1 with the following configuration:

| Parameter | Value |
|---|---|
| Router | R1 |
| Destination | 192.168.10.0/24 |
| Next hop | R2 |
| Interface | eth0 |
| Metric | 1 |
| Administrative distance | 1 |

A packet addressed to `192.168.10.25` matches this route and is forwarded through R2.

### 3.2 Default routing

A default route provides a forwarding path when no more specific destination route exists.

The IPv4 default route is:

`0.0.0.0/0`

It matches every IPv4 destination.

A more specific matching route takes precedence over the default route.

### 3.3 Advantages

- Predictable forwarding decisions.
- No dynamic routing update traffic.
- Administrative control over route configuration.
- Suitable for small and stable networks.
- Useful for default routes and specific traffic paths.

### 3.4 Limitations

- Manual configuration and maintenance.
- Limited adaptability to network failures.
- Increased operational effort in large networks.
- Potential for configuration errors.
- Alternative paths require additional configuration or another routing mechanism.

## 4. Dynamic Routing

Dynamic routing allows routers to exchange network information and calculate routes automatically.

Instead of requiring every destination route to be manually configured, routers use routing protocols and algorithms to learn available paths.

Dynamic routing can respond to:

- Link failures.
- Changes in network topology.
- New network advertisements.
- Changes in routing metrics.
- Loss of previously available paths.

The project implements two algorithmic approaches: shortest-path calculation and distance-vector calculation.

### 4.1 OSPF and link-state routing

Open Shortest Path First (OSPF) is a link-state interior gateway routing protocol.

Routers participating in OSPF exchange link-state information and construct a representation of network topology within their OSPF area.

Each router independently calculates shortest paths using Dijkstra's algorithm.

Important OSPF characteristics include:

- Link-state advertisements.
- Link-state database.
- Neighbor discovery.
- Adjacency formation.
- Shortest Path First calculation.
- Area-based network organization.
- Cost-based route selection.

The Python, JavaScript, C++17, and Java implementations use Dijkstra's algorithm to demonstrate the central shortest-path calculation.

These are educational topology models, not complete OSPF protocol implementations. They do not implement actual OSPF packet formats, adjacency state machines, LSA flooding, or area management.

### 4.2 RIP and distance-vector routing

Routing Information Protocol (RIP) is a distance-vector routing protocol.

Routers exchange information about reachable destinations and their associated metrics.

RIP uses hop count as its routing metric.

Important characteristics include:

- Periodic routing updates.
- Neighbor-based route information.
- Bellman-Ford-style distance calculations.
- A maximum usable hop count of 15.
- Hop count 16 representing an unreachable destination.
- Convergence and routing-loop considerations.

The implementations use weighted link costs to demonstrate the underlying distance-vector relaxation mechanism.

This is a generalized distance-vector simulation rather than a complete RIP implementation. Production RIP uses its defined hop-count metric and protocol-specific update and timer behavior.

## 5. Routing Tables

A routing table stores information that helps a router determine where packets should be forwarded.

A route normally contains:

| Field | Description |
|---|---|
| Destination network | Network prefix being matched |
| Next hop | Router to which the packet is forwarded |
| Outgoing interface | Interface used for transmission |
| Metric | Cost associated with the route |
| Protocol | Source of the route |
| Administrative distance | Preference between route sources |
| Status | Whether the route is active |

### 5.1 Example routing table

| Destination | Next hop | Interface | Protocol | Metric |
|---|---|---|---|---:|
| 192.168.10.0/24 | R2 | eth0 | Static | 1 |
| 10.0.2.0/24 | R2 | eth-R2 | OSPF | 2 |
| 10.0.3.0/24 | R2 | eth-R2 | OSPF | 3 |
| 10.0.4.0/24 | R2 | eth-R2 | OSPF | 5 |

The next hop for a destination is not necessarily the final destination router. It is the immediate forwarding destination.

### 5.2 Longest Prefix Matching

Longest Prefix Matching (LPM) is the principal IPv4 forwarding selection rule.

When multiple routes match a destination, the router selects the matching route with the longest network prefix.

Consider these entries:

| Network | Prefix length |
|---|---:|
| 192.168.0.0/16 | 16 |
| 192.168.10.0/24 | 24 |
| 192.168.10.128/25 | 25 |

For destination `192.168.10.150`, all three prefixes match.

The `/25` route is selected because it is the most specific matching route.

The implementations use prefix length as the first route-selection criterion.

### 5.3 Administrative Distance

Administrative distance represents the relative preference of route sources.

Common default values are:

| Route source | Administrative distance |
|---|---:|
| Directly connected | 0 |
| Static | 1 |
| eBGP | 20 |
| EIGRP internal | 90 |
| OSPF | 110 |
| IS-IS | 115 |
| RIP | 120 |
| Unknown | 255 |

A lower administrative distance is preferred when competing routes refer to the same destination prefix.

Administrative distance is a local router preference, not a routing protocol metric.

Metric and administrative distance serve different purposes:

- Administrative distance compares route sources.
- Metric compares paths within a routing protocol or route source.

The code implementations use administrative distance and metric as secondary selection criteria after longest prefix matching.

## 6. Routing Algorithms

### 6.1 Dijkstra's Shortest-Path Algorithm

Dijkstra's algorithm calculates minimum-cost paths in a graph with non-negative edge weights.

It is the foundation of OSPF's Shortest Path First calculation.

The algorithm operates on:

- Vertices representing routers.
- Edges representing network links.
- Edge weights representing link costs.
- A distance value for each router.
- A predecessor or next-hop relationship.

Processing sequence:

1. Assign zero distance to the source.
2. Assign infinity to other routers.
3. Select the unvisited router with the smallest known distance.
4. Examine its available outgoing links.
5. Calculate candidate distances.
6. Update shorter paths.
7. Repeat until all reachable routers have been processed.

For the example network:

| Destination | Shortest path | Cost |
|---|---|---:|
| R1 | R1 | 0 |
| R2 | R1 → R2 | 2 |
| R3 | R1 → R2 → R3 | 3 |
| R4 | R1 → R2 → R3 → R4 | 5 |

**Complexity**

Using an adjacency list and binary heap:

- Time: `O((V + E) log V)`
- Space: `O(V + E)`

Where:

- `V` represents the number of routers.
- `E` represents the number of links.

The C++17 and Java implementations use priority queues for efficient minimum-distance selection.

The Python implementation uses the standard-library heap.

The JavaScript implementation uses a sorted array for its small demonstration topology, so its queue operations are less efficient than a binary heap.

### 6.2 Bellman-Ford and Distance-Vector Routing

Bellman-Ford-style relaxation calculates shortest paths by repeatedly evaluating network edges.

The fundamental relationship is:

`D(x, y) = min(c(x, v) + D(v, y))`

Where:

- `D(x, y)` is the estimated cost from router x to destination y.
- `c(x, v)` is the link cost between routers x and v.
- `D(v, y)` is the distance advertised by neighbor v.

Each iteration attempts to improve the known distance to a destination.

The educational implementations use synchronous distance snapshots to avoid allowing update order to affect a single iteration.

For a graph with non-negative edge weights, up to `V - 1` relaxation rounds are sufficient to calculate shortest paths in the absence of topology changes during calculation.

**Complexity**

- Time: `O(VE)`
- Space: `O(V)`

This implementation models a centralized distance-vector calculation. Actual RIP routers exchange routing information with neighboring routers independently.

### 6.3 Comparison

| Characteristic | Dijkstra | Bellman-Ford |
|---|---|---|
| Routing approach | Link-state calculation | Distance-vector calculation |
| Main protocol association | OSPF | RIP |
| Information model | Network topology | Neighbor distance information |
| Edge weights | Non-negative | Non-negative for this implementation |
| Calculation | Greedy shortest path | Repeated relaxation |
| Typical complexity | O((V+E) log V) | O(VE) |
| Main operational concern | Topology database and recalculation | Convergence and routing loops |

## 7. Static and Dynamic Routing Comparison

| Characteristic | Static routing | Dynamic routing |
|---|---|---|
| Configuration | Manual | Protocol-based |
| Route discovery | Administrator | Routing protocol |
| Topology changes | Manual adjustment | Automatic recalculation |
| Control traffic | Minimal | Protocol updates |
| Scalability | Limited | Better for larger networks |
| Failure adaptation | Depends on configured alternatives | Protocol-dependent |
| Operational complexity | Low for small networks | Higher protocol complexity |

A practical enterprise network can combine both approaches.

Examples include:

- Static routes for predictable remote networks.
- Default static routes toward an upstream provider.
- OSPF for internal enterprise connectivity.
- RIP in small legacy environments.

## 8. Link Failure and Network Convergence

A network link may become unavailable because of:

- Physical cable disconnection.
- Interface failure.
- Hardware malfunction.
- Network congestion or operational intervention.
- Loss of neighbor connectivity.

When a link fails, previously calculated routes may no longer be valid.

The demonstration disables the R2-to-R3 connection.

The original shortest path from R1 to R4 costs 5:

`R1 → R2 → R3 → R4`

After the failure, the alternative path is:

`R1 → R3 → R4`

Its cost is:

`5 + 2 = 7`

Another available path is:

`R1 → R2 → R4`

Its cost is:

`2 + 7 = 9`

The new shortest-path cost is therefore 7.

The implementations recalculate the topology and show the changed route.

In a production routing environment, route convergence also depends on failure detection, protocol timers, update propagation, route installation, and forwarding-plane synchronization.

A centralized calculation alone does not reproduce these operational processes.

## 9. Python Implementation

The Python script provides a reusable routing simulation.

### Main components

| Component | Responsibility |
|---|---|
| `Link` | Represents a network connection |
| `Route` | Stores a route and its attributes |
| `RoutingTable` | Stores routes and performs prefix matching |
| `Network` | Maintains router connectivity |
| `DijkstraRouter` | Calculates shortest paths |
| `DistanceVectorRouter` | Calculates distance vectors |
| `RoutingSimulator` | Coordinates routing operations |

### Technical mechanisms

- Dataclasses model links and routes.
- Enumerations define routing protocols.
- Dictionaries represent adjacency lists.
- Heap-based priority queues implement Dijkstra.
- IP address utilities validate IPv4 prefixes.
- Custom exceptions handle invalid routing operations.
- Assertions validate algorithm results.

The implementation also demonstrates the difference between installing a route and calculating a route.

A manually installed static route is independent of the dynamic shortest-path calculation.

## 10. JavaScript Implementation

The JavaScript implementation emphasizes event-driven topology management.

### Main components

| Component | Responsibility |
|---|---|
| `RoutingTable` | Route storage and forwarding lookup |
| `NetworkTopology` | Network graph and link state |
| `ShortestPathEngine` | Routing algorithm execution |
| `Router` | Router-specific configuration |
| `RoutingController` | Coordinates network operations |

### Event-driven behavior

The topology extends Node.js `EventEmitter`.

Important events include:

- `routerAdded`
- `topologyChanged`
- `linkStateChanged`
- `recalculationRequired`

A link-state change emits an event so other application components can respond to the topology update.

The implementation uses private class fields, immutable route objects, Maps, Sets, asynchronous file operations, and custom error classes.

The route export uses exclusive file creation and restrictive file permissions to avoid silently overwriting an existing file.

The JavaScript Dijkstra implementation uses an array-based priority queue for simplicity. A binary heap would be more appropriate for larger networks.

## 11. C++17 Implementation

The C++ program provides a network-oriented routing engine using the Standard Template Library.

### Main components

| Component | Responsibility |
|---|---|
| `IPv4Network` | IPv4 address and CIDR processing |
| `Link` | Network connection representation |
| `Route` | Routing entry |
| `RoutingTable` | Forwarding lookup |
| `NetworkTopology` | Adjacency-list graph |
| `RoutingEngine` | Dijkstra and distance-vector algorithms |
| `Router` | Route installation and packet forwarding |

### Engineering decisions

- `unordered_map` stores network adjacency information.
- `priority_queue` supports efficient shortest-path selection.
- `optional` represents a missing next hop.
- `enum class` prevents accidental protocol-value mixing.
- `vector` stores routes and links.
- `remove_if` supports route deletion.
- Exceptions handle invalid configurations and missing routes.

The implementation uses unsigned 32-bit values for IPv4 address representation.

It avoids external libraries and compiles using the C++17 standard.

## 12. Java 17 Implementation

The Java implementation uses an enterprise-oriented service structure.

### Main components

| Component | Responsibility |
|---|---|
| `IPv4Network` | Immutable network representation |
| `Link` | Immutable link state |
| `Route` | Immutable route definition |
| `NetworkTopology` | Router and link management |
| `RoutingTable` | Route lookup and management |
| `RoutingAlgorithms` | Shortest-path calculations |
| `RouterService` | Route installation and forwarding |

### Java 17 features

- Records represent immutable domain objects.
- Enums define protocol and link states.
- Streams filter and sort routing entries.
- `PriorityQueue` supports Dijkstra.
- `HashMap` stores distance and next-hop information.
- `ConcurrentHashMap` maintains router routing-table references.
- Custom exceptions distinguish validation failures from missing routes.

The service layer separates network topology management from routing-table operations.

This separation makes it easier to introduce configuration persistence, management APIs, monitoring, and network automation in a larger application.

## 13. PostgreSQL Implementation

The PostgreSQL script models a relational routing-management system.

The database stores network configuration, topology information, routing protocols, routes, and forwarding decisions.

### 13.1 Database entities

| Table | Purpose |
|---|---|
| `networks` | Network ownership and identification |
| `routers` | Router configuration |
| `interfaces` | Router interface addresses and subnets |
| `network_links` | Connections and link costs |
| `routing_protocols` | Protocol configuration |
| `routing_tables` | Router routing-table records |
| `routes` | Individual route entries |
| `routing_events` | Link-state change history |
| `forwarding_decisions` | Packet-forwarding results |

### 13.2 Data integrity

The schema uses:

- Primary keys for entity identification.
- Foreign keys for relational consistency.
- Unique constraints for router and interface identifiers.
- Check constraints for IP address families and metrics.
- Enumerated types for routing states.
- Triggers for route and link-state validation.
- Indexes for route and topology retrieval.

The route-validation trigger ensures that an outgoing interface belongs to the router owning the routing table.

When a next hop is configured, the trigger verifies that the next-hop address belongs to a subnet accessible through an enabled interface on that router.

### 13.3 PostgreSQL routing functions

| Function | Purpose |
|---|---|
| `lookup_route` | Performs longest-prefix route selection |
| `calculate_dijkstra` | Calculates shortest paths |
| `calculate_distance_vector` | Performs distance-vector relaxation |
| `record_forwarding_decision` | Stores packet-forwarding outcomes |

The SQL implementation uses temporary tables for intermediate shortest-path calculations.

This separates calculation state from persistent routing configuration.

### 13.4 Database indexing

Important indexes include:

- Router and interface lookup indexes.
- Link source and destination indexes.
- Routing-table and status indexes.
- GIST indexing for network containment operations.
- Partial indexes for active routes.

The destination-network GIST index supports efficient CIDR containment queries.

The partial active-route index reduces unnecessary index entries when inactive routes are retained for operational history.

### 13.5 Transactions

The script demonstrates savepoints and rollback.

A link failure can be recorded, evaluated, and then rolled back when the example needs to restore the original topology.

This is important when testing configuration changes without permanently modifying the baseline network.

## 14. Route Selection Workflow

The overall forwarding process can be represented as follows:

    Packet arrives at router
              |
              v
    Read destination IP address
              |
              v
    Validate destination address
              |
              v
    Search active routing entries
              |
              v
    Apply longest prefix matching
              |
              v
    Compare administrative distance
              |
              v
    Compare metric where necessary
              |
              v
    Select next hop and interface
              |
         +----+----+
         |         |
         v         v
      Route      No route
      found      found
         |         |
         v         v
    Forward     Report or
    packet      handle failure

This model represents the logical routing decision. Actual packet transmission also requires a valid forwarding entry, neighbor resolution, an operational outgoing interface, and applicable forwarding policies.

## 15. Important Technical Distinctions

| Concept | Meaning |
|---|---|
| Routing | Determining available paths through a network |
| Forwarding | Moving packets to the selected next hop |
| Routing table | Collection of network route entries |
| Routing metric | Cost used to compare paths |
| Administrative distance | Preference between route sources |
| Next hop | Immediate forwarding destination |
| Network prefix | Destination address range |
| Longest prefix matching | Selection of the most specific matching route |
| Link-state routing | Routing based on network topology information |
| Distance-vector routing | Routing based on neighbor-advertised distances |
| Convergence | Process through which routers reach consistent routing information |

## 16. Failure Conditions and Edge Cases

The implementations account for several important routing conditions.

| Condition | Expected behavior |
|---|---|
| Unknown router | Reject topology or routing operation |
| Invalid IPv4 address | Raise validation error |
| Invalid CIDR prefix | Reject network configuration |
| Negative link cost | Reject link |
| Negative route metric | Reject route |
| Missing route | Report route-not-found condition |
| Disabled link | Exclude link from path calculation |
| Unreachable destination | Represent distance as infinity |
| Multiple matching prefixes | Select longest prefix |
| Equal prefix lengths | Compare administrative distance and metric |
| Direct destination | Represent next hop as local or direct |

### 16.1 Routing loops

Distance-vector protocols can experience routing loops when routers retain incorrect information about unreachable destinations.

RIP uses mechanisms such as:

- Split horizon.
- Route poisoning.
- Poison reverse.
- Hold-down timers.
- Triggered updates.

The educational distance-vector algorithms do not implement these complete protocol mechanisms.

### 16.2 Equal-cost paths

Equal-cost paths may allow traffic distribution across multiple next hops.

This behavior is known as Equal-Cost Multi-Path (ECMP).

The current implementations select one deterministic route when costs are equal. They do not implement ECMP forwarding.

### 16.3 Route redistribution

Route redistribution transfers routing information between different routing protocols.

For example, static routes may be redistributed into OSPF.

Redistribution requires careful metric handling, route filtering, and loop prevention.

The project models multiple route sources but does not implement full protocol redistribution.

## 17. Security and Operational Considerations

Routing configuration directly affects network reachability and traffic paths.

Important controls include:

- Restricting routing configuration to authorized administrators.
- Authenticating routing protocol neighbors.
- Validating route advertisements.
- Protecting routing-management interfaces.
- Monitoring unexpected route changes.
- Preventing unauthorized route installation.
- Maintaining configuration backups.
- Logging topology changes.
- Applying route filtering and prefix restrictions.
- Monitoring routing convergence and interface health.

A production implementation should also distinguish between the Routing Information Base (RIB) and the Forwarding Information Base (FIB).

The RIB contains routing information from connected networks, static configuration, and routing protocols.

The FIB contains the selected forwarding information used by the packet-forwarding plane.

The educational implementations primarily model routing-table selection and do not implement hardware forwarding, ARP, Neighbor Discovery, or complete router control-plane behavior.

## 18. Performance Considerations

| Component | Complexity or consideration |
|---|---|
| Adjacency-list storage | O(V + E) |
| Dijkstra with binary heap | O((V + E) log V) |
| Bellman-Ford relaxation | O(VE) |
| Routing-table linear lookup | O(R) |
| Route sorting | O(R log R) |
| Longest-prefix lookup | Depends on route lookup structure |
| PostgreSQL CIDR index | GIST-assisted network matching |

Where:

- `V` is the number of routers.
- `E` is the number of network links.
- `R` is the number of routing entries.

For large routing tables, prefix tries or specialized IP lookup structures can improve forwarding lookup performance.

For large network topologies, efficient priority queues, incremental recalculation, and optimized topology-change processing become important.

The SQL implementation is intended for routing configuration management and educational calculations, not line-rate packet forwarding.

## 19. Execution

### Python

Save the first implementation as `routing_fundamentals.py`.

Run:

`python routing_fundamentals.py`

### JavaScript

Save the second implementation as `routing_fundamentals.js`.

Run:

`node routing_fundamentals.js`

### C++17

Save the third implementation as `routing_fundamentals.cpp`.

Compile:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic routing_fundamentals.cpp -o routing_fundamentals`

Run:

`./routing_fundamentals`

On Windows:

`routing_fundamentals.exe`

### Java 17

Save the fourth implementation as `RoutingEnterprise.java`.

Compile:

`javac RoutingEnterprise.java`

Run:

`java RoutingEnterprise`

### PostgreSQL

Save the fifth implementation as `routing_fundamentals.sql`.

Execute using:

`psql -U postgres -d postgres -f routing_fundamentals.sql`

The executing database user needs permission to create the schema, types, tables, functions, triggers, and temporary tables.

The script uses PostgreSQL-specific networking types and operators.

## 20. Practical Learning Outcomes

The implementations establish the relationship between network topology, routing algorithms, route selection, and packet forwarding.

The key technical distinction is that static routing installs administrator-defined paths, while dynamic routing calculates and maintains paths from network information.

Routing tables provide the information required for forwarding decisions. Longest prefix matching selects the most specific destination network, administrative distance compares competing route sources, and routing metrics compare alternative paths within a routing mechanism.

The four programming implementations demonstrate these mechanisms through different software-engineering approaches, while PostgreSQL provides a persistent relational model for network configuration, route management, and forwarding history.
