# Minimum Spanning Trees: Kruskal, Prim and Union-Find

## 1. Problem Definition

A Minimum Spanning Tree (MST) is a subset of edges connecting every vertex in a connected, undirected, weighted graph with the minimum possible total edge weight.

Let a weighted graph be:

\[
G=(V,E)
\]

where:

- \(V\) represents the set of vertices.
- \(E\) represents the set of undirected edges.
- \(w(e)\) represents the weight associated with an edge.

A spanning tree must satisfy three conditions:

1. Every vertex belongs to the tree.
2. The tree is connected.
3. The tree contains no cycles.

A spanning tree containing \(V\) vertices always contains exactly:

\[
|V|-1
\]

edges.

The optimization objective is:

\[
MST(G)=\arg\min_{T\subseteq E}
\sum_{e\in T}w(e)
\]

subject to the spanning-tree conditions.

Typical applications include:

- Telecommunications infrastructure.
- Electrical distribution networks.
- Road and transportation planning.
- Computer network design.
- Pipeline connectivity.
- Data-center infrastructure.
- Clustering and graph analysis.

The implementations use an infrastructure-network scenario in which facilities must be connected while minimizing total connection cost.

## 2. Fundamental Graph Concepts

### 2.1 Vertices

Vertices represent the entities requiring connectivity.

Example:

| Vertex | Infrastructure entity |
|---|---|
| A | Warehouse |
| B | Factory |
| C | Office |
| D | Distribution center |
| E | Data center |

Each vertex must appear in the resulting spanning tree or spanning forest.

### 2.2 Edges

An edge represents a possible connection between two vertices.

An edge contains:

- Source vertex.
- Target vertex.
- Connection weight.

Example:

| Source | Target | Weight |
|---|---|---:|
| A | B | 4 |
| A | C | 3 |
| B | C | 1 |
| B | D | 2 |
| C | E | 5 |

An undirected edge has no preferred direction. Therefore, A-B and B-A represent the same connection.

The implementations reject duplicate undirected edges and self-loops.

### 2.3 Edge weights

Weights represent measurable connection costs.

They can represent:

- Construction expenses.
- Physical distance.
- Network installation costs.
- Transmission costs.
- Material requirements.

MST algorithms minimize the sum of the selected edge weights.

Negative edge weights are mathematically valid. The MST algorithms do not require all weights to be positive.

Non-finite weights, including infinity and NaN, are rejected because they do not provide meaningful finite optimization values.

### 2.4 Cycles

A cycle occurs when a sequence of connected edges returns to an already visited vertex.

For example:

A → B → C → A

Selecting all three connections creates a cycle.

An MST cannot contain cycles because a cycle contains at least one edge that can be removed without disconnecting the tree.

Cycle prevention is a central responsibility of Union-Find in Kruskal's algorithm.

## 3. Minimum Spanning Tree Properties

An MST has the following properties:

| Property | Explanation |
|---|---|
| Connectivity | Every vertex is reachable from every other vertex |
| Acyclicity | No cycles exist |
| Edge count | Exactly V - 1 edges |
| Minimum cost | Total selected weight is minimal |
| Undirected graph | Connections have no direction |
| Weighted graph | Every edge has a numerical weight |

An MST is not necessarily unique.

If multiple edges have equal weights, different valid spanning trees may have the same minimum total weight.

A deterministic tie-breaking rule can make the implementation produce repeatable results without changing the minimum-cost property.

## 4. Cut Property and Cycle Property

### 4.1 Cut property

A cut divides a graph's vertices into two non-empty groups.

An edge crossing the cut connects a vertex in one group to a vertex in the other.

A minimum-weight edge crossing a cut is safe to include in at least one MST.

This property provides the theoretical foundation for Prim's algorithm and helps explain Kruskal's greedy edge selection.

### 4.2 Cycle property

For a cycle containing a uniquely heaviest edge, that edge cannot belong to an MST.

Removing the heaviest edge preserves connectivity while reducing the total weight.

Both properties support the correctness of greedy MST algorithms.

## 5. Kruskal's Algorithm

Kruskal's algorithm constructs an MST by processing edges in ascending order of weight.

It initially treats every vertex as an independent component.

An edge is selected only when its endpoints belong to different components.

Union-Find efficiently maintains these components.

### 5.1 Processing workflow

1. Read the graph's vertices and edges.
2. Sort edges by ascending weight.
3. Initialize a separate Union-Find component for every vertex.
4. Select the next lightest edge.
5. Find the component containing each endpoint.
6. If both endpoints belong to different components, select the edge.
7. Merge the two components.
8. Reject an edge if its endpoints already belong to the same component.
9. Stop when V - 1 edges have been selected, provided the graph is connected.

For disconnected graphs, processing continues until all available edges have been considered.

The result is then a minimum spanning forest.

### 5.2 Example

Consider the following edges:

| Edge | Weight |
|---|---:|
| B-C | 1 |
| B-D | 2 |
| D-E | 2 |
| A-C | 3 |
| E-F | 3 |
| A-B | 4 |
| C-D | 4 |
| C-E | 5 |
| D-F | 6 |

Kruskal processes the edges in ascending order.

| Edge | Decision | Reason |
|---|---|---|
| B-C | Select | Different components |
| B-D | Select | Different components |
| D-E | Select | Different components |
| A-C | Select | Different components |
| E-F | Select | Different components |
| A-B | Reject | Creates a cycle |
| C-D | Reject | Creates a cycle |
| C-E | Reject | Creates a cycle |
| D-F | Reject | Creates a cycle |

The resulting spanning tree is:

A-C, B-C, B-D, D-E, E-F

Its total weight is:

\[
3+1+2+2+3=11
\]

The graph contains six vertices and five selected edges.

### 5.3 Complexity

Let V represent the number of vertices and E the number of edges.

| Operation | Complexity |
|---|---|
| Edge sorting | O(E log E) |
| Union-Find initialization | O(V) |
| Find operation | Amortized O(α(V)) |
| Union operation | Amortized O(α(V)) |
| Processing edges | O(E α(V)) |
| Total | O(E log E) |

Here, α(V) is the inverse Ackermann function, which grows extremely slowly.

For practical graph sizes, Union-Find operations are nearly constant time.

### 5.4 When Kruskal is appropriate

Kruskal is particularly useful when:

- The graph is sparse.
- The edge list is readily available.
- Edges must be processed in sorted order.
- Components must be maintained efficiently.
- A minimum spanning forest is required.

Its principal storage requirements are the edge list and Union-Find structures.

## 6. Prim's Algorithm

Prim's algorithm constructs a minimum spanning tree by expanding a growing connected component.

Unlike Kruskal, which selects edges globally, Prim maintains a frontier of candidate edges connecting the current tree to unvisited vertices.

### 6.1 Processing workflow

1. Choose a starting vertex.
2. Mark it as visited.
3. Insert its outgoing edges into a minimum-priority queue.
4. Extract the lowest-weight edge.
5. Ignore it if its destination is already visited.
6. Otherwise, add the edge to the tree.
7. Mark its destination as visited.
8. Insert the new vertex's eligible outgoing edges.
9. Continue until all reachable vertices have been visited.
10. Start another component if the graph is disconnected.

The algorithm uses a priority queue to identify the lowest-weight frontier edge efficiently.

### 6.2 Example

Using the same infrastructure network, begin at vertex A.

A possible sequence is:

| Selected edge | Weight |
|---|---:|
| A-C | 3 |
| C-B | 1 |
| B-D | 2 |
| D-E | 2 |
| E-F | 3 |

The resulting total is:

\[
3+1+2+2+3=11
\]

The selection order can differ from Kruskal's order, but both algorithms produce a minimum total weight.

### 6.3 Complexity

Using an adjacency list and binary min-heap:

| Operation | Complexity |
|---|---|
| Adjacency-list construction | O(V + E) |
| Priority-queue insertion | O(log E) |
| Priority-queue extraction | O(log E) |
| Edge processing | O(E) |
| Total | O((V + E) log E) |

For a connected simple graph, this is commonly expressed as:

\[
O(E\log V)
\]

An adjacency matrix implementation has a different complexity profile, commonly O(V²), and can be useful for dense graphs.

### 6.4 When Prim is appropriate

Prim is particularly suitable when:

- The graph is represented by adjacency lists.
- The graph is relatively dense.
- A connected tree must grow from a chosen starting point.
- Priority-queue-based frontier management is convenient.

## 7. Kruskal and Prim: Technical Comparison

| Characteristic | Kruskal | Prim |
|---|---|---|
| Main approach | Global edge selection | Tree expansion |
| Starting vertex | Not required | Required for initial component |
| Primary structure | Union-Find | Priority queue |
| Edge ordering | Sort all edges | Extract minimum frontier edge |
| Cycle prevention | Union-Find | Visited vertices |
| Graph representation | Edge list | Adjacency list |
| Typical complexity | O(E log E) | O(E log V) |
| Sparse graphs | Very suitable | Suitable |
| Dense graphs | Can require extensive sorting | Often advantageous |
| Disconnected graphs | Minimum spanning forest | Minimum spanning forest |

Neither algorithm is universally superior.

The appropriate choice depends on graph density, storage representation, available memory, and application requirements.

## 8. Union-Find Data Structure

Union-Find is also called Disjoint Set Union (DSU).

It maintains a collection of non-overlapping sets and supports two primary operations.

### 8.1 Find

Find identifies the representative or root of the set containing a given element.

If A, B and C belong to the same component, their Find operations return the same representative.

### 8.2 Union

Union combines two different sets.

If two vertices belong to different components, their components are merged.

If they already belong to the same component, Union returns false.

This prevents cycle creation during Kruskal's algorithm.

### 8.3 Path compression

Without path compression, parent references may form long chains.

Path compression changes the parent of visited elements to the root.

Example:

Before:

A → B → C → D

After Find(A):

A → D

B → D

C → D

D

This reduces the cost of subsequent Find operations.

### 8.4 Union by rank

Union by rank attaches the shorter tree beneath the taller tree.

Rank approximates tree height.

When both roots have equal rank, one becomes the parent and its rank increases.

### 8.5 Combined complexity

Path compression and union by rank provide amortized:

\[
O(\alpha(V))
\]

per operation.

This makes Union-Find highly efficient for connectivity tracking.

### 8.6 Important distinction

Union-Find does not calculate an MST by itself.

It provides an efficient component-management mechanism.

Kruskal uses it to determine whether selecting an edge would create a cycle.

## 9. Disconnected Graphs and Minimum Spanning Forests

A disconnected graph cannot have a spanning tree because there is no path connecting all vertices.

A minimum spanning forest contains one minimum spanning tree for each connected component.

For a graph with:

- V vertices.
- C connected components.

A minimum spanning forest contains:

\[
V-C
\]

edges.

Example:

Component 1:

A -- B -- C

Component 2:

D -- E

The graph has five vertices and two connected components.

The forest contains:

\[
5-2=3
\]

selected edges.

The implementations distinguish between:

- A spanning tree: one connected component.
- A spanning forest: potentially multiple connected components.

A disconnected graph must not be reported as having a valid spanning tree.

## 10. Python Implementation

The Python implementation provides a complete graph-processing environment.

### Main components

| Component | Responsibility |
|---|---|
| `Edge` | Immutable weighted-edge representation |
| `DisjointSet` | Union-Find implementation |
| `WeightedGraph` | Graph and adjacency-list management |
| `MSTResult` | Stores algorithm results |
| `verify_result()` | Checks structural invariants |
| `run_tests()` | Executes validation and algorithm tests |

### Design decisions

The implementation uses:

- Dataclasses for structured domain objects.
- Dictionaries for parent and rank management.
- Sets for unique vertices and undirected edge detection.
- Lists for edges and adjacency structures.
- `heapq` for Prim's priority queue.
- Exceptions for invalid graph operations.
- Assertions for correctness verification.

Both algorithms return the same result structure.

The result includes total weight, selected edges, component count and spanning-tree status.

### Validation

The test suite covers:

- Connected graphs.
- Disconnected graphs.
- Negative weights.
- Single-vertex graphs.
- Duplicate connections.
- Self-loops.
- Unknown starting vertices.
- Algorithm weight agreement.
- Randomized connected graph comparisons.

The randomized tests use a fixed seed for reproducibility.

## 11. JavaScript Implementation

The JavaScript implementation provides an event-driven network engine.

### Main components

| Component | Responsibility |
|---|---|
| `NetworkGraph` | Graph management and algorithm execution |
| `DisjointSet` | Component management |
| `MinHeap` | Priority-queue implementation |
| `GraphError` | Domain-specific validation errors |
| `calculate()` | Promise-based algorithm interface |
| `verifyResult()` | Result validation |

### Event-driven behavior

The graph extends Node.js `EventEmitter`.

Two events are supported:

- `edgeAdded`: emitted after a valid edge is registered.
- `mstCalculated`: emitted after an MST or forest is calculated.

This allows other application components to react to graph changes and calculations without coupling them directly to algorithm implementations.

### Asynchronous interface

The `calculate()` method provides a Promise-based interface.

It allows integration into asynchronous application workflows.

The underlying algorithms are synchronous. Wrapping them in a Promise does not make CPU-intensive calculations execute in a separate thread.

For very large graphs, worker threads or background processing would be appropriate.

### Data integrity

The implementation uses:

- `Map` for adjacency and Union-Find state.
- `Set` for visited vertices.
- Frozen edge objects.
- Frozen result snapshots.
- Explicit input validation.
- A custom binary min-heap.

## 12. C++17 Implementation

The C++17 implementation focuses on efficient graph processing and explicit domain modeling.

### Main components

| Component | Responsibility |
|---|---|
| `Edge` | Weighted connection |
| `MSTResult` | Calculation result |
| `DisjointSet` | Efficient component management |
| `WeightedGraph` | Graph operations |
| `Algorithm` | Algorithm identification |

### Engineering decisions

The implementation uses:

- `vector` for graph storage.
- `unordered_map` for vertex lookup.
- `unordered_set` for duplicate-edge detection.
- `priority_queue` for Prim's algorithm.
- `sort` for Kruskal's algorithm.
- `tuple` for priority-queue entries.
- Exceptions for invalid input.

Integer vertex identifiers are used internally to avoid repeated string comparisons during Union-Find operations.

The external interface retains readable vertex names.

### Memory considerations

The adjacency-list representation requires:

\[
O(V+E)
\]

memory.

Kruskal additionally requires a sorted edge collection.

Prim uses a priority queue containing candidate connections.

The implementation avoids unnecessary external dependencies and compiles with standard C++17.

## 13. Java 17 Enterprise Implementation

The Java implementation models network optimization as an enterprise service.

It separates graph data, calculation results, algorithms and policy evaluation.

### Domain types

| Type | Responsibility |
|---|---|
| `Edge` | Immutable connection |
| `NetworkPlan` | Immutable MST result |
| `InfrastructureNetwork` | Graph state |
| `DisjointSet` | Connectivity tracking |
| `NetworkPolicy` | Policy contract |
| `StandardNetworkPolicy` | Cost and connectivity validation |
| `NetworkService` | Calculation and approval workflow |

### Records

Java records provide concise immutable representations for edges and calculated network plans.

The selected-edge list is copied using `List.copyOf()` to prevent external modification.

### Policy evaluation

An algorithm can produce a mathematically valid minimum spanning tree that still fails an enterprise requirement.

For example:

- The resulting network exceeds the approved cost.
- The graph is disconnected.
- The network requires a single spanning tree.
- The calculation fails verification.

The `NetworkPolicy` interface separates these business requirements from the graph algorithms.

This distinction is important in enterprise systems because optimization correctness and business authorization are separate concerns.

## 14. PostgreSQL Database Implementation

The SQL implementation models weighted networks as relational data.

### Database relationship

Networks  
→ Vertices  
→ Edges  
→ Network Policies  
→ MST Calculations  
→ Selected MST Edges

Approvals are stored separately from calculation results.

### Main tables

| Table | Purpose |
|---|---|
| `networks` | Network master information |
| `vertices` | Network vertices |
| `edges` | Weighted undirected connections |
| `network_policies` | Optimization and validation policies |
| `network_approvals` | Approval records |
| `mst_calculations` | Calculation history |
| `mst_selected_edges` | Selected connections for each result |

### Referential integrity

Foreign keys prevent edges from referencing vertices belonging to another network.

The edge table uses canonical endpoint ordering:

\[
source\_vertex\_id < target\_vertex\_id
\]

This prevents reversed duplicate connections.

A unique constraint additionally protects against duplicate undirected edges.

Check constraints prevent self-loops and invalid numerical values.

### Database-level validation

The edge trigger checks:

- Network existence.
- Network archival status.
- Negative-weight policy.

The calculation procedure validates:

- Network status.
- Required algorithm.
- Vertex count.
- Connectivity.
- Maximum permitted weight.

### SQL implementation of Union-Find

The `calculate_mst_kruskal()` function implements component management using temporary tables.

Each vertex initially points to itself.

For every edge, the function:

1. Finds the source root.
2. Finds the target root.
3. Skips the edge if both roots match.
4. Compares root ranks.
5. Merges the components.
6. Returns the selected edge.

The temporary table stores parent references and rank values.

The implementation uses union by rank. Unlike the iterative application-language implementations, the SQL function does not perform explicit path compression.

### Transaction handling

The `execute_mst()` procedure:

1. Locks the network row.
2. Validates network state.
3. Loads the active policy.
4. Executes Kruskal.
5. Calculates the number of components.
6. Checks connectivity and cost limits.
7. Stores calculation history.
8. Persists selected edges.

The calling transaction controls whether the calculation and its associated records are committed.

A policy violation raises an exception, preventing a partially persisted calculation.

### Connectivity reporting

The `network_connectivity()` function uses a recursive CTE to identify connected components.

It reports the component membership of every vertex.

This is separate from the Kruskal calculation and provides an independent connectivity-reporting mechanism.

### Database performance

The implementation includes indexes for:

- Network-specific edge retrieval.
- Weight-ordered edge processing.
- Vertex lookup.
- Calculation history.
- Approval retrieval.

The partial edge index excludes disabled connections.

Index selection should be evaluated using actual production data and query plans.

## 15. Correctness and Validation

MST correctness depends on three principal invariants.

### Invariant 1: No cycles

Every selected edge must connect two previously separate components.

Union-Find enforces this condition in Kruskal's algorithm.

Prim enforces it by selecting edges that connect visited and unvisited vertices.

### Invariant 2: Component preservation

The selected edges must connect every pair of vertices that were originally connected in the input graph.

A disconnected graph must retain its original number of connected components.

### Invariant 3: Edge count

For a graph containing V vertices and C components:

\[
|E_{selected}|=V-C
\]

For a connected graph:

\[
|E_{selected}|=V-1
\]

The implementations verify these conditions.

### Additional test cases

| Test | Expected behavior |
|---|---|
| Empty graph | Rejected |
| Single vertex | Empty spanning tree |
| Negative edge weight | Accepted |
| Infinite weight | Rejected |
| Self-loop | Rejected |
| Duplicate undirected edge | Rejected |
| Unknown vertex | Rejected |
| Disconnected graph | Minimum spanning forest |
| Equal-weight edges | Valid minimum solution |
| Cycle-producing edge | Rejected during selection |

## 16. Performance Comparison

| Implementation | Kruskal | Prim |
|---|---|---|
| Python | O(E log E) | O((V + E) log V) |
| JavaScript | O(E log E) | O((V + E) log V) |
| C++17 | O(E log E) | O((V + E) log V) |
| Java 17 | O(E log E) | O((V + E) log V) |
| PostgreSQL | O(E log E) edge ordering, plus PL/pgSQL and temporary-table operations | Not implemented |

The SQL implementation uses Kruskal only.

Its database execution overhead is not equivalent to the asymptotic complexity of an in-memory Union-Find implementation. Temporary-table operations and repeated SQL statements add practical overhead.

For large production graphs, algorithm selection should consider graph size, database execution cost, memory requirements and data-transfer overhead.

## 17. Limitations and Practical Considerations

### Graph size

Large graphs can require substantial memory for adjacency lists, edge collections and priority queues.

For extremely large networks, partitioning, streaming edge processing or specialized graph storage may be necessary.

### Dynamic changes

An MST calculated for one graph version may become invalid after an edge is added, removed or modified.

The JavaScript and Java implementations retain graph revision information in calculated results.

Production systems should associate calculations with immutable graph snapshots or explicit graph-version identifiers.

### Equal weights

Multiple minimum spanning trees may exist when edge weights are equal.

Deterministic tie-breaking provides reproducible output, but does not establish that the resulting MST is unique.

### Changing edge weights

A change in an edge weight can change the optimal spanning tree.

The implementations recalculate the MST rather than implementing advanced dynamic MST algorithms.

### Security and integrity

Production implementations should also consider:

- Authorization to modify network definitions.
- Validation of imported graph data.
- Transaction isolation.
- Audit logging.
- Database access controls.
- Protection against unauthorized network modifications.
- Input-size restrictions.
- Consistent graph snapshots.

### Cost interpretation

An MST minimizes total edge weight, not necessarily the actual operational cost of an infrastructure project.

Real-world constraints such as capacity, reliability, geographic restrictions and installation dependencies may require a more advanced optimization model.

## 18. Execution

| Deliverable | Runtime | Execution |
|---|---|---|
| Python | Python 3.10+ | `python minimum_spanning_tree.py` |
| JavaScript | Node.js 18+ | `node minimum_spanning_tree.js` |
| C++17 | C++17 compiler | `g++ -std=c++17 -O2 minimum_spanning_tree.cpp -o mst` |
| Java | Java 17 | `javac Main.java` followed by `java -ea Main` |
| PostgreSQL | PostgreSQL 14+ | Execute the SQL script in a database |

The Java implementation uses assertions for additional test validation. Therefore, run it with `-ea`.

The SQL script creates a dedicated `mst` schema and replaces an existing schema with that name. It should be executed in a test database unless that replacement is intentional.

## 19. Conceptual Workflow

The relationship between the algorithms and their supporting data structures is:

Graph Input  
→ Vertex and Edge Validation  
→ Weighted Graph Representation  
→ Algorithm Selection  
→ Kruskal or Prim  
→ Union-Find or Priority Queue  
→ Minimum Spanning Tree / Forest  
→ Structural Verification  
→ Cost Evaluation  
→ Result Storage

The central distinction is that Kruskal and Prim are optimization algorithms, whereas Union-Find is a supporting data structure used to maintain connectivity efficiently.

Both algorithms solve the same minimum spanning tree problem through different greedy strategies.
