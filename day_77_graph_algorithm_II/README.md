# Graph Algorithms II: Dijkstra's Algorithm and Shortest Path Problems

## 1. Problem Domain

Shortest path algorithms determine the minimum-cost route between vertices in a weighted graph.

They are used in:

- Road and transportation networks.
- Internet routing.
- Telecommunications.
- Network infrastructure analysis.
- Logistics and distribution.
- Resource allocation.
- Dependency and infrastructure analysis.
- Navigation and geographic information systems.

This implementation studies Dijkstra's algorithm through five independent engineering perspectives: Python graph simulation, JavaScript event-driven routing, C++17 algorithm engineering, Java 17 enterprise service design, and PostgreSQL relational graph processing.

The implementations use nonnegative edge weights and support both directed and undirected graph representations.

## 2. Mathematical Foundation

A weighted graph is represented as:

\[
G=(V,E,w)
\]

Where:

- \(V\) is the set of vertices.
- \(E\) is the set of edges.
- \(w(u,v)\) is the weight associated with an edge from \(u\) to \(v\).

An edge weight represents a measurable cost, such as travel time, distance, monetary expense, or transmission latency.

For a path containing vertices:

\[
P=(v_0,v_1,\ldots,v_k)
\]

Its total weight is:

\[
W(P)=\sum_{i=0}^{k-1}w(v_i,v_{i+1})
\]

The shortest path from source \(s\) to destination \(t\) is:

\[
\delta(s,t)=\min_{P:s\leadsto t}W(P)
\]

If no valid path exists, the destination is unreachable and its shortest distance is represented as infinity.

## 3. Graph Representation

### 3.1 Vertices

A vertex represents an identifiable entity in a network.

Examples include:

- A city in a transportation network.
- A router in a communication network.
- A warehouse in a distribution network.
- A server in an infrastructure network.

Each vertex has an identifier used by graph operations.

### 3.2 Edges

An edge establishes a connection between two vertices.

An edge contains:

| Attribute | Meaning |
|---|---|
| Source | Starting vertex |
| Destination | Ending vertex |
| Weight | Cost of traversing the edge |
| Active state | Whether the connection participates in routing |

A directed edge from A to B does not automatically establish a connection from B to A.

An undirected edge represents a connection usable in both directions.

### 3.3 Adjacency Lists

All five implementations use adjacency-list concepts.

An adjacency list associates each vertex with its outgoing edges.

For example:

- A → B (4)
- A → C (1)
- C → B (2)
- B → D (1)

This representation stores only existing connections.

Its space complexity is:

\[
O(V+E)
\]

An adjacency matrix instead requires:

\[
O(V^2)
\]

Adjacency lists are suitable for sparse transportation and infrastructure networks where the number of actual connections is significantly smaller than the number of possible connections.

## 4. Dijkstra's Algorithm

### 4.1 Core Principle

Dijkstra's algorithm is a greedy shortest-path algorithm.

It repeatedly selects the unsettled vertex with the smallest tentative distance and uses that vertex to improve the distance estimates of its outgoing neighbors.

The algorithm maintains three important structures:

| Structure | Purpose |
|---|---|
| Distance map | Stores the best known distance from the source |
| Predecessor map | Records the previous vertex on the best known path |
| Priority queue | Selects the next minimum-distance vertex |

### 4.2 Initialization

For a source vertex \(s\):

\[
dist(s)=0
\]

For all other vertices:

\[
dist(v)=\infty
\]

Initially, no predecessor is assigned.

The source is inserted into a minimum-priority queue with distance zero.

### 4.3 Relaxation

Suppose the algorithm processes an edge from \(u\) to \(v\).

The candidate distance is:

\[
candidate=dist(u)+w(u,v)
\]

If:

\[
candidate<dist(v)
\]

the distance and predecessor are updated:

\[
dist(v)=candidate
\]

\[
pred(v)=u
\]

The improved distance is inserted into the priority queue.

This operation is called edge relaxation.

### 4.4 Settled Vertices

A vertex becomes settled when it is removed from the priority queue with its current minimum distance.

Under the nonnegative-weight condition, its shortest distance is final.

A settled vertex does not need to be processed again.

### 4.5 Stale Priority Queue Entries

A vertex can receive multiple improved distance estimates.

For example:

- Initial distance to B: 10.
- Improved distance to B: 6.
- Improved distance to B: 3.

The priority queue can contain multiple entries for B.

Older entries become stale.

The implementations discard stale entries by comparing the extracted distance with the current best distance.

This avoids unnecessary processing and supports an efficient implementation without requiring decrease-key operations.

### 4.6 Algorithm Workflow

    Initialize all distances to infinity
                |
                v
    Set source distance to zero
                |
                v
    Insert source into minimum heap
                |
                v
    Extract minimum-distance vertex
                |
                v
    Is vertex already settled?
           /          \
         Yes           No
          |             |
          v             v
        Skip       Settle vertex
                        |
                        v
                 Examine outgoing edges
                        |
                        v
                 Calculate candidate distance
                        |
                        v
                 Is candidate smaller?
                    /        \
                  Yes         No
                   |           |
                   v           v
              Update state    Continue
                   |
                   v
              Insert heap entry
                   |
                   v
              Queue empty?
                /       \
              No         Yes
              |           |
              v           v
          Repeat       Return results

## 5. Important Algorithm Constraints

### 5.1 Nonnegative Edge Weights

Dijkstra's algorithm requires:

\[
w(u,v)\geq 0
\]

Negative edge weights invalidate its greedy correctness guarantee.

The Python, JavaScript, C++17, Java 17, and PostgreSQL implementations validate this condition.

### 5.2 Zero-Weight Edges

Zero-weight edges are valid.

They represent connections that do not increase the measured path cost.

For example:

\[
w(A,B)=0
\]

A zero-weight edge must not be confused with an absent edge.

The implementations explicitly support zero-weight connections.

### 5.3 Unreachable Vertices

A vertex is unreachable when no valid path exists from the selected source.

Its distance remains:

\[
dist(v)=\infty
\]

The implementation does not invent a route for unreachable destinations.

### 5.4 Negative Cycles

Dijkstra does not solve shortest-path problems involving negative edge weights or negative cycles.

For such problems, Bellman-Ford is a more appropriate algorithm.

### 5.5 Floating-Point Precision

The Python, JavaScript, C++17, and Java implementations use numeric distance values.

Floating-point arithmetic can introduce small rounding differences.

For monetary routing, fixed-point arithmetic or integer values in the smallest currency unit may be preferable.

The PostgreSQL implementation uses `NUMERIC` to support decimal weights with controlled precision.

## 6. Shortest Path Reconstruction

Calculating the minimum distance does not automatically produce the complete route.

The predecessor map provides the information needed to reconstruct the path.

Suppose:

\[
pred(D)=B
\]

\[
pred(B)=C
\]

\[
pred(C)=A
\]

Starting from D and repeatedly following predecessors produces:

\[
D\rightarrow B\rightarrow C\rightarrow A
\]

Reversing the sequence produces:

\[
A\rightarrow C\rightarrow B\rightarrow D
\]

The path reconstruction operation requires at most:

\[
O(V)
\]

time for a simple shortest-path tree.

An unreachable destination has no reconstructable path.

## 7. Single-Source Shortest Paths

Single-source Dijkstra computes shortest distances from one selected source to every reachable vertex.

For example, selecting Lucknow as the source produces distances to:

- Kanpur.
- Ayodhya.
- Varanasi.
- Agra.
- Prayagraj.
- Gorakhpur.
- Patna.
- Delhi.

The result is a shortest-path tree.

The tree represents the predecessor relationships selected during the execution.

It does not require storing a separate complete path for every destination.

This reduces redundant storage.

## 8. Destination-Specific Shortest Paths

Sometimes the application requires a route between only two vertices.

For example:

\[
s=\text{Lucknow}
\]

\[
t=\text{Delhi}
\]

Dijkstra can terminate when the destination is extracted from the priority queue with its current minimum distance.

This is safe because the destination has then been settled.

The optimization avoids processing vertices that cannot improve the requested result.

It does not necessarily avoid examining every edge in the graph. Its actual benefit depends on graph structure and destination position.

## 9. Multi-Source Shortest Paths

Multi-source Dijkstra calculates the shortest distance from the nearest selected source.

For sources:

\[
S=\{s_1,s_2,\ldots,s_k\}
\]

Initialize:

\[
dist(s_i)=0
\]

for every selected source.

All sources enter the same priority queue.

The algorithm then proceeds normally.

This approach is equivalent to adding a virtual source connected to every original source by a zero-weight edge.

Applications include:

- Nearest warehouse assignment.
- Emergency-service accessibility.
- Nearest network gateway.
- Multi-depot delivery planning.
- Distributed infrastructure analysis.

The implementations provide multi-source functionality separately from ordinary single-source execution.

## 10. Complexity Analysis

For a graph represented using adjacency lists and a binary min-heap:

| Operation | Complexity |
|---|---|
| Graph initialization | \(O(V)\) |
| Add vertex | \(O(1)\) expected |
| Add edge | \(O(1)\) |
| Extract minimum | \(O(\log V)\) |
| Heap insertion | \(O(\log V)\) |
| Edge relaxation | \(O(\log V)\) including heap insertion |
| Path reconstruction | \(O(V)\) worst case |
| Graph storage | \(O(V+E)\) |

The standard binary-heap implementation has time complexity:

\[
O((V+E)\log V)
\]

For connected sparse graphs, this is commonly expressed as:

\[
O(E\log V)
\]

Auxiliary algorithm storage is:

\[
O(V)
\]

The graph itself requires:

\[
O(V+E)
\]

A binary heap is a practical choice because it provides predictable performance without introducing a complicated decrease-key implementation.

## 11. Python Implementation

**File:** `dijkstra.py`

The Python implementation focuses on algorithm simulation and correctness.

### Implemented mechanisms

- `WeightedGraph` models directed and undirected graphs.
- `Edge` provides immutable edge records.
- `ShortestPathResult` stores execution results.
- `heapq` implements the minimum-priority queue.
- Dictionaries maintain distance and predecessor state.
- Sets track settled vertices.
- Exceptions reject invalid graph operations.
- JSON export provides a persistent graph representation.
- `unittest` verifies algorithm behavior.

### Important design decisions

Python's `heapq` does not provide a built-in decrease-key operation.

The implementation therefore inserts improved entries and ignores outdated entries during extraction.

A sequence number is included in each heap entry to avoid comparing arbitrary vertex objects when distances are equal.

The graph supports arbitrary hashable vertex identifiers.

The multi-source method initializes multiple vertices at distance zero.

### Validation scenarios

The test suite covers:

- Ordinary shortest paths.
- Path reconstruction.
- Unreachable destinations.
- Zero-weight edges.
- Negative-weight rejection.
- Unknown vertices.
- Undirected graph traversal.
- Multi-source execution.
- Empty source collections.
- Non-finite weights.

The script uses only Python standard-library modules.

## 12. JavaScript Implementation

**File:** `dijkstra.js`

The JavaScript implementation emphasizes event-driven network updates and asynchronous routing requests.

### Implemented mechanisms

- `WeightedGraph` extends `EventEmitter`.
- `Map` stores graph adjacency lists.
- `Set` tracks settled vertices.
- `MinHeap` implements a binary minimum heap.
- `Promise` supports asynchronous route calculations.
- `AbortSignal` supports request cancellation.
- Graph snapshots preserve a consistent calculation state.
- Graph versions identify modifications.
- Assertions verify routing behavior.

### Event-driven graph updates

The graph emits events when vertices and edges are added.

Applications can use these events to trigger:

- Route recalculation.
- Cache invalidation.
- Monitoring.
- Network change notifications.
- Operational reporting.

### Asynchronous processing

The routing service periodically yields control to the Node.js event loop.

This permits cancellation checks and other scheduled operations to run during longer computations.

It does not make the calculation computationally parallel.

### Graph snapshot consistency

The implementation creates a snapshot before routing.

The algorithm operates on that snapshot rather than reading a changing adjacency structure throughout execution.

The snapshot carries a version number.

A strict caller can reject a result when the underlying graph changes before the calculation finishes.

This separates computational consistency from the current state of the live graph.

## 13. C++17 Implementation

**File:** `dijkstra.cpp`

The C++17 implementation emphasizes performance-oriented algorithm engineering and explicit memory structures.

### Implemented mechanisms

- `WeightedGraph` models the graph.
- `Edge` represents weighted connections.
- `PathResult` stores routing results.
- `unordered_map` stores adjacency and distance information.
- `unordered_set` tracks settled vertices.
- `priority_queue` implements minimum-distance selection.
- STL algorithms reverse reconstructed paths.
- Exceptions handle invalid graph operations.

### Priority queue design

The standard C++ `priority_queue` is a maximum-heap by default.

Using `greater<>` reverses the ordering.

This creates a minimum-priority queue.

The queue stores pairs:

\[
(distance,vertex)
\]

The implementation processes outdated entries using the same distance comparison used in the other implementations.

### Domain modeling

The graph distinguishes:

- Directed graph.
- Undirected graph.
- Source vertex.
- Destination vertex.
- Edge weight.
- Predecessor.
- Settled vertex.

The result object exposes path reconstruction independently of the graph traversal implementation.

### Engineering considerations

The use of `unordered_map` provides expected constant-time vertex lookup.

Its iteration order is not guaranteed, so the public vertex listing is sorted before display.

The implementation uses `double` for general-purpose travel costs and rejects non-finite edge weights.

Distance overflow is checked during relaxation.

## 14. Java 17 Implementation

**File:** `DijkstraEngine.java`

The Java implementation uses an enterprise-oriented service architecture.

### Domain types

| Type | Responsibility |
|---|---|
| `GraphType` | Distinguishes directed and undirected graphs |
| `Edge` | Represents a validated weighted edge |
| `QueueEntry` | Represents a priority queue entry |
| `RouteResult` | Represents a destination-specific result |
| `SingleSourceResult` | Represents single-source calculations |
| `GraphSnapshot` | Represents a consistent graph version |
| `RoutingService` | Defines the routing service contract |

### Service separation

The implementation separates graph management from routing calculations.

`WeightedGraph` manages graph construction and snapshots.

`DijkstraRoutingService` calculates destination-specific routes.

`MultiSourceRoutingService` calculates distances from multiple sources.

`RoutingApplication` provides the application-facing interface.

This separation permits different routing implementations to be introduced behind the same service contract.

### Immutable results

Java records represent structured results.

Collections are copied when result objects are constructed.

This prevents callers from modifying the internal result state through an exposed mutable collection.

### State consistency

The graph produces a snapshot before route execution.

The service calculates against that snapshot rather than repeatedly reading the mutable graph.

This supports predictable execution in applications where graph updates and route requests may occur concurrently.

The snapshot represents the state at the time it was created, not necessarily the latest state when the response is returned.

## 15. PostgreSQL Implementation

**File:** `dijkstra.sql`

The PostgreSQL implementation models graph data relationally and executes Dijkstra's algorithm through PL/pgSQL.

### Relational entities

| Table | Purpose |
|---|---|
| `graphs` | Stores graph definitions |
| `vertices` | Stores graph vertices |
| `edges` | Stores weighted connections |
| `route_runs` | Stores execution metadata |
| `route_results` | Stores distances and predecessors |
| `route_path` | Stores reconstructed path sequences |

### Referential integrity

The database uses:

- Primary keys.
- Foreign keys.
- Composite foreign keys.
- Unique constraints.
- Check constraints.
- Enumeration types.

Composite foreign keys ensure that an edge's source and destination vertices belong to the same graph.

Negative edge weights are prohibited through a database constraint and trigger validation.

### Graph versioning

Changes to vertices or edges increment the graph version.

The version provides a mechanism for identifying modifications between route calculations.

It is useful when building cache invalidation or route-result freshness checks.

### Temporary algorithm state

The PL/pgSQL function creates a session-scoped temporary table.

The table stores:

- Vertex identifier.
- Tentative distance.
- Predecessor identifier.
- Settled state.

The algorithm repeatedly selects the unsettled vertex having the smallest non-null distance.

It then relaxes outgoing edges through a set-based SQL update.

A `NULL` distance represents infinity.

### Path reconstruction

The database stores predecessor relationships.

The reconstruction function follows these relationships backward from the destination until it reaches the source.

It then returns the ordered path and cumulative distances.

A maximum-step check prevents an invalid predecessor chain from producing an infinite loop.

### Transaction handling

The SQL script uses a transaction for schema creation and sample data insertion.

A savepoint demonstrates how an individual graph modification can be rolled back without discarding the surrounding transaction.

### Performance considerations

The outgoing-edge index supports the most frequent graph traversal operation.

The incoming-edge index supports reverse relationship analysis.

The route-result distance index supports distance-based reporting.

The PL/pgSQL implementation uses ordered selection from a temporary table rather than a binary heap.

Consequently, it is a relational demonstration of Dijkstra's logic, not a performance-equivalent replacement for the heap-based implementations.

For very large graphs, a specialized in-memory graph engine or a database implementation with a priority queue would generally be more efficient.

## 16. Implementation Comparison

| Dimension | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| Graph storage | Dictionary | Map | unordered_map | Map | Relational tables |
| Priority queue | heapq | Custom binary heap | priority_queue | PriorityQueue | Ordered temporary-table selection |
| Settled tracking | Set | Set | unordered_set | HashSet | Boolean column |
| Predecessors | Dictionary | Map | unordered_map | Map | Foreign-key identifiers |
| Async processing | No | Yes | No | No | No |
| Multi-source | Yes | Yes | Yes | Yes | Yes |
| Persistence | JSON export | In-memory | In-memory | In-memory | Relational database |
| Testing | unittest | assert | Runtime assertions | Assertion checks | SQL validation queries |

## 17. Shortest Path Problem Variants

Dijkstra is one algorithm within a larger family of shortest-path techniques.

Different problem characteristics require different algorithms.

| Problem | Suitable algorithm |
|---|---|
| Single-source, nonnegative weights | Dijkstra |
| Single-source, negative weights | Bellman-Ford |
| All-pairs shortest paths | Floyd-Warshall |
| All-pairs on sparse graphs | Repeated Dijkstra, where weights are nonnegative |
| Unweighted shortest path | Breadth-First Search |
| Directed acyclic graph shortest path | Topological-order relaxation |
| Negative-cycle detection | Bellman-Ford |
| Shortest path with admissible heuristic | A* |

### Dijkstra versus BFS

Breadth-First Search minimizes the number of edges traversed.

Dijkstra minimizes total edge weight.

They produce equivalent shortest paths when every edge has the same positive weight, but their problem assumptions differ.

### Dijkstra versus Bellman-Ford

Dijkstra relies on nonnegative weights and uses greedy vertex settlement.

Bellman-Ford repeatedly relaxes all edges and can support negative weights when no reachable negative cycle prevents a finite shortest path.

### Dijkstra versus Floyd-Warshall

Dijkstra solves a single-source shortest-path problem.

Floyd-Warshall calculates shortest distances between every pair of vertices.

Its time complexity is:

\[
O(V^3)
\]

Its space complexity is:

\[
O(V^2)
\]

The appropriate choice depends on the number of required source-destination queries and the density of the graph.

## 18. Edge Cases and Failure Handling

| Condition | Expected behavior |
|---|---|
| Unknown source | Reject the request |
| Unknown destination | Reject the request |
| Negative edge weight | Reject the graph modification |
| Zero-weight edge | Process normally |
| Disconnected destination | Return unreachable |
| Duplicate multi-source entries | Reject the request |
| Empty source collection | Reject the request |
| Self-loop with positive weight | Process without improving the current distance |
| Self-loop with zero weight | Process without creating an incorrect predecessor |
| Equal-cost alternatives | Preserve one valid shortest path |
| Non-finite edge weight | Reject the graph modification |
| Excessive path reconstruction | Detect invalid predecessor chains |
| Graph modification during asynchronous calculation | Use a snapshot and optionally reject stale results |

## 19. Security and Production Considerations

### Input validation

Graph identifiers and vertex names must be validated before use.

Edge weights must be finite and nonnegative.

Database functions should be called with validated parameters.

### Resource limits

Unrestricted graph construction can consume excessive memory and processing time.

Production systems should enforce limits on:

- Number of vertices.
- Number of edges.
- Maximum edge weight.
- Number of simultaneous routing requests.
- Request execution duration.
- Maximum retained route history.

### Database security

The PostgreSQL implementation should run with a dedicated database role.

Application roles should receive only the required permissions.

In particular:

- Avoid unrestricted schema modification privileges.
- Restrict graph deletion.
- Control access to temporary and persistent routing data.
- Use parameterized SQL calls.
- Audit important graph modifications.

The sample script establishes data integrity, but a production deployment still requires role-based permissions and operational access controls.

### Concurrency

A graph can change while another operation is calculating a route.

The JavaScript and Java implementations use snapshots.

The PostgreSQL implementation captures the graph version and uses database transaction mechanisms.

Production deployments should define a consistent isolation and update policy.

### Numerical stability

Distances should use an appropriate numeric representation for the application.

For integer distances, integer arithmetic can avoid floating-point rounding.

For fractional weights, fixed-point or decimal arithmetic can improve reproducibility.

Overflow and maximum supported distance should be explicitly controlled.

### Monitoring

Useful operational metrics include:

- Number of routing requests.
- Route calculation duration.
- Number of settled vertices.
- Number of examined edges.
- Number of successful relaxations.
- Unreachable destination count.
- Graph version.
- Graph update frequency.

These measurements help identify unusually dense graphs, excessive updates, and inefficient routing requests.

## 20. Practical Applications

### Transportation

Vertices represent cities and edges represent road connections.

Weights represent travel time or distance.

Dijkstra identifies the minimum-cost route from one city to another.

### Telecommunications

Vertices represent routers and edges represent communication links.

Weights may represent latency or transmission cost.

Shortest-path calculations help identify efficient network routes.

### Logistics

Vertices represent warehouses, distribution centers, and delivery locations.

Edges represent transportation links.

Multi-source Dijkstra can identify the nearest available distribution center.

### Infrastructure

Vertices represent servers, network components, or facilities.

Edges represent dependency or communication relationships.

Weighted paths help evaluate connectivity and infrastructure costs.

### Emergency Services

Vertices represent service locations and destinations.

Weights represent estimated response times.

Multi-source routing can calculate accessibility from multiple emergency-service locations.

Real-world deployment requires additional considerations such as changing traffic conditions, operational availability, access restrictions, and time-dependent edge weights.

## 21. Implementation Limitations

These implementations provide a deterministic shortest-path model using fixed edge weights.

They do not implement:

- Real-time traffic integration.
- Time-dependent edge weights.
- Vehicle routing with capacity constraints.
- Multiple simultaneous delivery objectives.
- Dynamic shortest-path maintenance.
- Turn restrictions.
- Geographic coordinate calculations.
- Distributed graph processing.
- Negative-weight shortest paths.
- Full graph transaction version history.

Dijkstra is appropriate when the network has nonnegative edge costs and the routing objective is to minimize their sum.

When the objective changes, the algorithm and graph model may also need to change.
