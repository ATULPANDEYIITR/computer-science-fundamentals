# Graph Algorithms III: Bellman-Ford, Floyd-Warshall and Negative Cycles

## 1. Introduction

This project implements two fundamental shortest-path algorithms for weighted directed graphs:

- Bellman-Ford for single-source shortest paths.
- Floyd-Warshall for all-pairs shortest paths.

It also examines negative edge weights, negative cycles, unreachable vertices, shortest-path reconstruction, and the distinction between a finite shortest distance and an undefined shortest distance.

The five implementations provide different engineering perspectives:

| File | Implementation focus |
|---|---|
| Python | Graph simulation, algorithm execution, validation and testing |
| JavaScript | Event-driven graph updates and asynchronous analysis |
| C++17 | Efficient graph representation and algorithmic processing |
| Java 17 | Enterprise domain modeling and route-governance decisions |
| PostgreSQL | Relational graph storage, analysis execution and reporting |

All implementations use directed graphs. An edge from vertex `u` to vertex `v` does not imply an edge from `v` to `u`.

## 2. Mathematical Foundations

### 2.1 Weighted directed graphs

A weighted directed graph is represented as:

\[
G=(V,E,w)
\]

Where:

- \(V\) is the set of vertices.
- \(E\) is the set of directed edges.
- \(w(u,v)\) is the weight assigned to an edge from \(u\) to \(v\).

An edge weight can represent distance, travel cost, processing time, financial cost, or another numerical quantity.

For example:

\[
A \xrightarrow{4} B
\]

\[
B \xrightarrow{-2} C
\]

The total weight of a path is the sum of the weights of its edges.

\[
W(P)=\sum_{e\in P}w(e)
\]

A shortest path is a path with the minimum total weight among all available paths between two vertices.

A graph may contain positive, zero, and negative edge weights.

### 2.2 Negative edge weights

A negative edge has a weight smaller than zero.

For example:

\[
A \xrightarrow{-5} B
\]

Negative edges are useful when modeling credits, discounts, gains, adjustments, or systems where an operation reduces total cost.

Negative edge weights create a limitation for Dijkstra's algorithm. Its usual greedy selection rule assumes that extending a path cannot later produce a smaller distance through a negative edge.

Bellman-Ford and Floyd-Warshall can handle negative edge weights, provided the requested shortest distance is not made undefined by a reachable negative cycle.

### 2.3 Three possible shortest-path states

The implementations distinguish three outcomes.

| State | Meaning | Representation |
|---|---|---|
| Finite | A valid minimum distance exists | Numeric distance |
| Unreachable | No directed path exists | Infinity or SQL `NULL` with status |
| Negative infinity | A reachable negative cycle can reduce the path cost without limit | Explicit negative-infinity status |

These states must not be treated as interchangeable.

An unreachable vertex has no available path. A vertex affected by a negative cycle has paths whose costs can decrease indefinitely.

For example:

\[
A \xrightarrow{2} B
\]

\[
B \xrightarrow{-4} C
\]

\[
C \xrightarrow{1} B
\]

The cycle has total weight:

\[
-4+1=-3
\]

Traversing this cycle repeatedly decreases the total cost.

There is consequently no finite shortest distance for destinations reachable from this cycle.

## 3. Bellman-Ford Algorithm

### 3.1 Purpose

Bellman-Ford calculates shortest distances from one selected source vertex to all other vertices.

It supports:

- Positive edge weights.
- Zero-weight edges.
- Negative edge weights.
- Disconnected graphs.
- Detection of reachable negative cycles.

Its principal advantage is the ability to identify negative cycles that can affect the source's shortest-path calculations.

### 3.2 Relaxation

Relaxation is the central operation.

For an edge:

\[
u \rightarrow v
\]

with weight \(w(u,v)\), the algorithm checks:

\[
d[v] > d[u]+w(u,v)
\]

If the condition is true, the distance is improved:

\[
d[v]=d[u]+w(u,v)
\]

The predecessor of \(v\) is also updated to \(u\).

The predecessor information allows the actual route to be reconstructed after the algorithm finishes.

### 3.3 Initialization

For a graph containing \(V\) vertices:

\[
d[source]=0
\]

For all other vertices:

\[
d[v]=\infty
\]

The source has zero distance from itself. All other vertices initially have unknown or unreachable distances.

### 3.4 Repeated relaxation

Bellman-Ford performs at most:

\[
V-1
\]

relaxation rounds.

Why are there \(V-1\) rounds?

A shortest simple path in a graph without relevant negative cycles cannot require more than \(V-1\) edges. A simple path does not repeat a vertex.

Each complete round allows shortest-path information to propagate through additional edges.

The implementation also stops early if an entire round makes no changes.

This optimization improves practical performance for graphs that converge before all rounds are necessary.

### 3.5 Negative-cycle detection

After the relaxation rounds, the algorithm performs another pass through the edges.

If an edge can still reduce a distance, a reachable negative cycle exists.

The condition is:

\[
d[v]>d[u]+w(u,v)
\]

This test must ignore edges whose source is unreachable.

An unreachable negative cycle does not affect the shortest paths from the selected source.

### 3.6 Identifying affected vertices

Detecting one negative cycle is not sufficient.

The algorithm must also identify all vertices whose shortest distances are undefined because they are reachable from that cycle.

The implementations perform a graph traversal from the vertices identified during the additional relaxation pass.

A breadth-first traversal or equivalent stack traversal marks every downstream reachable vertex.

The resulting set represents vertices with negative-infinity shortest distances.

Vertices outside this set retain their independently valid shortest-path results or remain unreachable.

### 3.7 Negative-cycle reconstruction

The implementations maintain predecessor information.

When an additional relaxation identifies a negative cycle, predecessor links are followed repeatedly.

Following predecessors for \(V\) steps moves the reconstruction position into a cycle.

The cycle is then extracted by following predecessor links until the starting vertex is encountered again.

This produces a witness showing the cycle's vertices.

The witness is useful for debugging, graph validation, and identifying problematic cost relationships.

### 3.8 Complexity

| Operation | Complexity |
|---|---|
| Initialization | \(O(V)\) |
| Relaxation | \(O(VE)\) |
| Negative-cycle detection | \(O(E)\) |
| Affected-vertex traversal | \(O(V+E)\) |
| Path reconstruction | \(O(V)\) |
| Total time | \(O(VE)\) |
| Auxiliary storage | \(O(V)\), excluding graph storage |

Bellman-Ford is particularly suitable for sparse graphs and applications requiring negative-edge support from one source.

## 4. Floyd-Warshall Algorithm

### 4.1 Purpose

Floyd-Warshall calculates shortest distances between every pair of vertices.

Unlike Bellman-Ford, which begins with one source, Floyd-Warshall evaluates all source-destination combinations.

It is particularly useful when an application needs repeated queries between many different pairs of vertices.

### 4.2 Distance matrix

The algorithm uses a two-dimensional matrix:

\[
D[i][j]
\]

Each element represents the current shortest known distance from vertex \(i\) to vertex \(j\).

Initialization rules:

\[
D[i][i]=0
\]

For a direct edge:

\[
D[i][j]=w(i,j)
\]

For vertices without a direct connection:

\[
D[i][j]=\infty
\]

If multiple direct edges connect the same ordered pair, the smallest weight is selected.

### 4.3 Intermediate vertices

The algorithm considers each vertex as a possible intermediate point.

The update rule is:

\[
D[i][j]=\min(D[i][j],D[i][k]+D[k][j])
\]

Where:

- \(i\) is the source.
- \(j\) is the destination.
- \(k\) is the intermediate vertex.

The algorithm compares the current route from \(i\) to \(j\) with a route passing through \(k\).

If the route through \(k\) is cheaper, the distance matrix is updated.

### 4.4 Processing order

The intermediate vertex must be the outermost loop.

The logical processing order is:

1. Select an intermediate vertex.
2. Examine every source vertex.
3. Examine every destination vertex.
4. Update the shortest known distance.

This order maintains the intended dynamic-programming interpretation.

### 4.5 Negative-cycle detection

After processing all intermediate vertices, examine the diagonal entries.

If:

\[
D[i][i]<0
\]

then a negative cycle exists that is reachable from vertex \(i\) and returns to it.

A normal path from a vertex to itself has distance zero because no edge needs to be traversed.

A negative diagonal value therefore indicates that a negative-cost cycle has been discovered.

### 4.6 Pair-specific negative-infinity classification

A negative cycle does not automatically make every pair's shortest distance undefined.

A pair \((i,j)\) is affected only if there is:

1. A path from \(i\) to a negative-cycle vertex \(k\).
2. A negative cycle involving or reachable from \(k\).
3. A path from \(k\) to \(j\).

The classification condition is:

\[
D[i][k]<\infty
\]

\[
D[k][k]<0
\]

\[
D[k][j]<\infty
\]

If these conditions hold, the shortest distance from \(i\) to \(j\) is negative infinity.

This pair-specific evaluation is implemented in the Python, JavaScript, Java, C++17 and PostgreSQL solutions.

### 4.7 Path reconstruction

Floyd-Warshall can maintain a next-vertex matrix.

\[
Next[i][j]
\]

This matrix stores the first vertex to visit after leaving \(i\) when traveling toward \(j\).

When a better route through \(k\) is discovered:

\[
Next[i][j]=Next[i][k]
\]

Path reconstruction starts at the source and repeatedly follows the next-vertex matrix until the destination is reached.

A path must not be reconstructed when its status is negative infinity.

### 4.8 Complexity

| Operation | Complexity |
|---|---|
| Matrix initialization | \(O(V^2)\) |
| Direct-edge insertion | \(O(E)\) |
| Dynamic-programming updates | \(O(V^3)\) |
| Negative-cycle detection | \(O(V)\) |
| Pair classification | \(O(V^3)\) |
| Distance storage | \(O(V^2)\) |
| Next-vertex storage | \(O(V^2)\) |

Floyd-Warshall is practical for relatively small or medium-sized dense graphs where all-pairs results are required.

## 5. Bellman-Ford and Floyd-Warshall: Technical Distinctions

| Property | Bellman-Ford | Floyd-Warshall |
|---|---|---|
| Main purpose | Single-source shortest paths | All-pairs shortest paths |
| Negative edges | Supported | Supported |
| Negative cycles | Detects reachable cycles | Detects cycles through diagonal values |
| Disconnected graphs | Supported | Supported |
| Primary structure | Edge list | Distance matrix |
| Path tracking | Predecessor array | Next-vertex matrix |
| Time complexity | \(O(VE)\) | \(O(V^3)\) |
| Auxiliary storage | \(O(V)\) | \(O(V^2)\) |
| Typical use | One-source routing | Repeated all-pairs queries |

Neither algorithm should report an ordinary finite shortest path when the relevant source-destination pair can be affected by a reachable negative cycle.

The algorithms solve related but different problems.

Bellman-Ford is generally preferable when only a small number of source vertices require analysis.

Floyd-Warshall is preferable when a complete shortest-distance matrix is required and the graph size makes cubic processing practical.

## 6. Python Implementation

File: `graph_algorithms_iii.py`

The Python implementation uses an object-oriented graph model and standard-library data structures.

### 6.1 Domain model

The main types are:

| Type | Responsibility |
|---|---|
| `Edge` | Stores a directed weighted edge |
| `WeightedDirectedGraph` | Maintains graph structure |
| `BellmanFordResult` | Stores single-source analysis |
| `FloydWarshallResult` | Stores all-pairs analysis |
| `PathStatus` | Distinguishes finite, unreachable and negative-infinity states |
| `GraphError` | Represents graph validation failures |
| `NegativeCycleError` | Represents undefined shortest-path requests |

The edge representation uses a frozen dataclass.

This prevents accidental modification of an edge after insertion.

### 6.2 Graph storage

The graph maintains:

- An edge list for efficient Bellman-Ford processing.
- An adjacency list for affected-vertex traversal.

The edge list makes it possible to examine every edge during each relaxation round.

The adjacency list supports efficient traversal of outgoing edges without repeatedly scanning the complete edge collection.

### 6.3 Validation

The implementation rejects:

- Non-positive vertex counts.
- Invalid vertex identifiers.
- Non-numeric weights.
- NaN values.
- Infinite edge weights.

Rejecting non-finite weights prevents invalid arithmetic from entering the algorithms.

### 6.4 Demonstrations

The Python script includes:

- A graph containing negative edges but no negative cycle.
- A graph containing a reachable negative cycle.
- An all-pairs shortest-path example.
- A disconnected graph.
- Cross-validation between Bellman-Ford and Floyd-Warshall.
- Invalid edge-input tests.

Assertions verify expected distances and negative-cycle propagation.

### 6.5 Practical considerations

Python lists and dictionaries provide convenient graph storage, although their memory overhead can be higher than compact array-based structures.

For large graphs, repeated Python-level edge iteration can become expensive.

The implementation uses early termination in Bellman-Ford to avoid unnecessary relaxation rounds.

## 7. JavaScript Implementation

File: `graph_algorithms_iii.js`

The JavaScript implementation emphasizes event-driven graph changes, immutable snapshots and asynchronous execution.

### 7.1 Event-driven graph management

The `WeightedGraph` class extends Node.js `EventEmitter`.

When an edge is inserted, the graph emits an `edgeAdded` event.

Listeners receive:

- The inserted edge.
- The current graph version.

This allows an application to observe graph changes without coupling graph storage directly to reporting or monitoring components.

### 7.2 Graph snapshots

A graph snapshot captures:

- Vertex count.
- Graph version.
- Edge collection.

Shortest-path analysis operates on a snapshot rather than repeatedly accessing the mutable graph.

This provides a consistent logical input during analysis.

The graph version helps identify which graph state produced a result.

The snapshot is a shallow immutable representation. Edge objects are frozen, and the edge collection is copied.

### 7.3 Asynchronous execution

The methods `analyzeFrom()` and `analyzeAllPairs()` return promises.

They allow analysis to participate in asynchronous Node.js workflows.

The example executes the two analyses using `Promise.all()`.

The use of `setImmediate()` yields to the event loop before starting the synchronous computation.

It does not make the shortest-path algorithm CPU-parallel. Large computations should be moved to worker threads or another execution service when responsiveness is important.

### 7.4 Negative-cycle management

The implementation uses JavaScript `Set` objects to maintain affected vertices.

An array-based queue performs breadth-first propagation.

The resulting analysis object exposes:

- Source vertex.
- Graph version.
- Distance array.
- Predecessor array.
- Affected vertices.
- Negative-cycle witness.

### 7.5 Failure handling

The implementation explicitly rejects invalid graph inputs and undefined shortest-path reconstruction.

The top-level promise rejection handler reports execution failures and sets a non-zero process exit code.

## 8. C++17 Implementation

File: `graph_algorithms_iii.cpp`

The C++17 implementation emphasizes explicit graph structures, predictable memory ownership and standard-library algorithms.

### 8.1 Data structures

| Structure | Purpose |
|---|---|
| `Edge` | Stores source, destination and weight |
| `WeightedGraph` | Owns graph edges and adjacency lists |
| `BellmanFordResult` | Stores distances, predecessors and affected states |
| `FloydWarshallResult` | Stores matrices and negative-cycle vertices |
| `PathStatus` | Represents shortest-path classification |
| `GraphError` | Handles invalid graph operations |

The graph owns its edge collection and adjacency lists.

Result structures are returned by value using move semantics where appropriate.

### 8.2 STL usage

The implementation uses:

- `std::vector` for graph and result storage.
- `std::queue` for breadth-first traversal.
- `std::reverse` for route reconstruction.
- `std::numeric_limits` for infinity.
- `std::isfinite` for numeric validation.
- `std::runtime_error` for exception handling.

### 8.3 Memory and performance

The edge list provides sequential access during Bellman-Ford relaxation.

The adjacency list provides efficient outgoing-edge traversal.

Floyd-Warshall uses contiguous row-based vectors for its matrices.

This design is suitable for compact graph-processing applications without third-party dependencies.

The use of `double` is convenient for general numerical examples. Applications requiring exact financial or decimal calculations should use an appropriate fixed-point or decimal representation.

## 9. Java 17 Implementation

File: `GraphAlgorithmsIII.java`

The Java implementation models graph analysis as an enterprise-oriented service workflow.

### 9.1 Domain types

| Type | Responsibility |
|---|---|
| `Edge` | Immutable weighted edge |
| `GraphSnapshot` | Versioned graph representation |
| `WeightedGraph` | Graph lifecycle and storage |
| `BellmanFordResult` | Single-source result |
| `FloydWarshallResult` | All-pairs result |
| `ShortestPathService` | Shortest-path service contract |
| `BellmanFordService` | Bellman-Ford implementation |
| `FloydWarshallService` | All-pairs implementation |
| `AnalysisPolicy` | Defines route acceptance conditions |
| `RouteDecision` | Represents a route-governance decision |
| `RouteGovernanceService` | Evaluates whether a finite route is permitted |

### 9.2 Records and immutability

Java records provide concise definitions for data-oriented types.

The graph snapshot stores an immutable copy of the edge list.

Analysis results copy their collections before exposing them.

The matrix result also copies its arrays during construction.

This reduces accidental modification of previously calculated results.

The arrays returned through the matrix record remain directly accessible to package-level consumers through the generated accessors, so a production API should expose defensive-copy accessors or a dedicated immutable matrix abstraction.

### 9.3 Service separation

The `ShortestPathService` interface separates the algorithm contract from its implementation.

The Bellman-Ford service implements single-source analysis.

The Floyd-Warshall service handles all-pairs analysis.

The route-governance service evaluates analysis results against policy objects.

This separation makes it possible to add other route-selection rules without embedding them inside the graph algorithms.

### 9.4 Policy evaluation

A route decision includes:

- Whether the route is permitted.
- The reason for the decision.
- The reconstructed path.
- The route distance.

The example policy requires a reachable destination and rejects negative-cycle-affected routes.

This demonstrates an important distinction between calculating a mathematical result and making an application-level decision based on that result.

### 9.5 Versioning and consistency

The graph snapshot includes a version number.

This provides traceability between the graph state and its analysis results.

In a concurrent enterprise application, graph mutation and snapshot creation should be protected by appropriate synchronization or implemented using immutable versioned graph objects.

## 10. PostgreSQL Implementation

File: `graph_algorithms_iii.sql`

The SQL implementation models the graph as a relational data structure and executes both shortest-path algorithms through stored procedures.

It requires PostgreSQL 15 or later.

### 10.1 Relational schema

The principal relationships are:

Graph:

\[
1 \rightarrow N
\]

Graph to vertices:

\[
1 \rightarrow N
\]

Graph to edges:

\[
1 \rightarrow N
\]

Analysis run:

\[
1 \rightarrow N
\]

Analysis run to shortest-path results:

\[
1 \rightarrow N
\]

Analysis run to negative-cycle reports:

\[
1 \rightarrow N
\]

The database uses composite foreign keys to ensure that edge endpoints belong to the same graph.

### 10.2 Tables

| Table | Purpose |
|---|---|
| `graph` | Stores graph metadata and vertex count |
| `graph_vertex` | Stores graph vertices |
| `graph_edge` | Stores directed weighted edges |
| `analysis_run` | Tracks algorithm execution |
| `shortest_path_result` | Stores source-destination results |
| `negative_cycle` | Stores negative-cycle reports |

The `graph_edge` table does not impose a uniqueness constraint on source and destination.

This permits parallel edges.

The algorithms select the minimum direct edge weight when initializing their calculations.

### 10.3 Integrity enforcement

The schema uses:

- Primary keys.
- Composite foreign keys.
- Unique constraints.
- Check constraints.
- Validation triggers.
- Performance-oriented indexes.

The vertex-validation trigger prevents identifiers outside the configured graph size.

The edge-validation trigger checks that both endpoints fall within the graph's vertex range.

Foreign keys independently ensure that both endpoint records exist.

### 10.4 Bellman-Ford stored procedure

The `execute_bellman_ford()` procedure:

1. Loads the graph and analysis configuration.
2. Initializes distance and predecessor arrays.
3. Performs up to \(V-1\) relaxation rounds.
4. Detects additional relaxations.
5. Identifies affected vertices.
6. Propagates affected status using a queue.
7. Attempts negative-cycle reconstruction.
8. Stores shortest-path classifications.
9. Marks the analysis as completed.

PostgreSQL arrays provide indexed storage for distances, predecessors and affected-state flags.

The implementation uses `NUMERIC` values for edge weights and distances.

### 10.5 Floyd-Warshall stored procedure

The `execute_floyd_warshall()` procedure maintains:

- A two-dimensional distance array.
- A two-dimensional next-vertex array.

It applies the standard intermediate-vertex update.

After the computation, it identifies negative diagonal entries.

It then classifies every source-destination pair independently.

This prevents a negative cycle in one disconnected region from incorrectly invalidating unrelated routes.

### 10.6 Analysis tracking

The `analysis_run` table records:

- Algorithm selection.
- Source vertex when required.
- Execution status.
- Graph version.
- Negative-cycle detection.
- Execution timestamps.
- Execution messages.

The analysis initialization function distinguishes Bellman-Ford from Floyd-Warshall.

Bellman-Ford requires a source vertex.

Floyd-Warshall does not.

### 10.7 Reporting

The script includes views and queries for:

- Graph inventory.
- Vertex and edge counts.
- Negative-edge counts.
- Analysis summaries.
- Finite routes.
- Unreachable destinations.
- Negative-infinity classifications.
- Negative-cycle reports.
- Route eligibility.
- Aggregated analysis statistics.

The `evaluate_route()` function translates stored mathematical results into a simple application-level decision.

### 10.8 Transaction management

The script uses an explicit transaction for schema creation, sample data and analysis execution.

This ensures that the initial setup is committed as one logical operation.

The analysis procedures also use database-level row locking when obtaining their execution records.

The graph-version check compares the recorded edge count with the current edge count.

This detects some forms of graph modification, but edge counts alone are not a reliable versioning mechanism because an update or replacement can leave the count unchanged.

A production implementation should use an explicit graph-version counter, incremented transactionally for every graph mutation, and should prevent concurrent mutations while an analysis is executing.

## 11. Important Edge Cases

### 11.1 Negative edges without negative cycles

Consider:

\[
A \xrightarrow{4} B
\]

\[
B \xrightarrow{-2} C
\]

The path from \(A\) to \(C\) has cost:

\[
4-2=2
\]

This is a valid finite shortest distance.

The existence of a negative edge alone does not indicate a negative cycle.

### 11.2 Negative cycle that cannot be reached from the source

Suppose a graph contains two disconnected components.

The first contains the selected source.

The second contains a negative cycle.

Bellman-Ford must not report that the source's shortest-path calculations are affected by the disconnected cycle.

The implementation checks source reachability before considering a relaxation.

### 11.3 Negative cycle affecting only some destinations

A negative cycle may affect a subset of destinations.

For example:

\[
A \rightarrow B
\]

\[
B \rightarrow C
\]

\[
C \rightarrow B
\]

\[
C \rightarrow D
\]

The cycle between \(B\) and \(C\) also affects \(D\), because \(D\) can be reached from the cycle.

A separate vertex that cannot be reached from the cycle retains its independent shortest-path state.

### 11.4 Self-loops

A negative self-loop is a negative cycle containing one vertex.

For example:

\[
A \xrightarrow{-3} A
\]

A zero-weight self-loop does not produce a negative cycle.

A positive self-loop does not improve the distance from a vertex to itself.

### 11.5 Parallel edges

Two directed edges may connect the same ordered pair.

For example:

\[
A \xrightarrow{8} B
\]

\[
A \xrightarrow{3} B
\]

The algorithms must initialize the direct distance using the smaller weight.

### 11.6 Zero-weight edges

Zero-weight edges are valid.

They can represent free transitions or relationships that do not add to the total cost.

### 11.7 Empty connectivity

A graph may contain vertices without any connecting edges.

These vertices remain unreachable from unrelated sources.

### 11.8 Source equals destination

For a graph without a relevant negative cycle, the shortest distance from a vertex to itself is zero.

If the vertex can reach a negative cycle that can return to it, the corresponding shortest distance is negative infinity instead.

## 12. Numerical Accuracy and Implementation Limitations

The shortest-path algorithms rely on numerical comparisons.

Floating-point arithmetic can introduce rounding errors when edge weights have decimal representations.

For example, repeated additions of decimal values may not produce an exact mathematical result in binary floating-point arithmetic.

The implementations use different numerical representations:

| Language | Numeric representation |
|---|---|
| Python | Floating-point `float` |
| JavaScript | IEEE 754 `Number` |
| C++17 | `double` |
| Java 17 | `double` |
| PostgreSQL | `NUMERIC` |

For applications involving financial values, exact monetary amounts should use integer minor units or decimal arithmetic.

For extremely large graphs or weights, additional safeguards are required.

These include:

- Bounds on vertex and edge counts.
- Bounds on maximum edge weights.
- Overflow checks where applicable.
- Explicit numerical tolerances for floating-point comparisons.
- Memory limits for all-pairs matrices.
- Validation of intermediate arithmetic.

The current implementations use exact comparisons for their selected sample values.

Floating-point applications with noisy or approximate data may require a carefully defined comparison tolerance. Such a tolerance must be applied consistently because it can change which path is considered shortest.

## 13. Security and Reliability Considerations

Graph algorithms are not inherently secure merely because their implementations use standard data structures.

Applications accepting external graph data should enforce:

- Vertex-count limits.
- Edge-count limits.
- Valid vertex identifiers.
- Finite numerical weights.
- Request timeouts.
- Memory limits.
- Controlled access to graph mutation.
- Safe database permissions.
- Transactional analysis storage.
- Audit records for graph changes.

### 13.1 Resource exhaustion

Floyd-Warshall uses quadratic memory and cubic processing time.

An attacker or malfunctioning client could submit an excessively large graph and consume substantial resources.

Input limits should be enforced before allocating matrices.

### 13.2 Negative-cycle abuse

Negative cycles may be legitimate in some mathematical models.

In other applications, they can indicate incorrect data or manipulation.

Systems that use shortest-path results for routing, pricing, or scheduling should define an explicit policy for negative-cycle-affected results.

### 13.3 Database access

Database users should receive only the permissions required for their responsibilities.

Graph creation, graph modification and analysis execution should be separated when different operational roles are involved.

Stored procedures should be executed using appropriately restricted database roles.

### 13.4 Auditability

For reproducible analysis, record:

- Graph identifier.
- Graph version.
- Algorithm.
- Source vertex, where applicable.
- Analysis timestamp.
- Execution status.
- Negative-cycle information.
- Result classification.

A result should not silently be reused after its underlying graph has changed.

## 14. Performance Comparison

| Graph characteristic | Bellman-Ford | Floyd-Warshall |
|---|---|---|
| Small sparse graph | Suitable | Suitable |
| Large sparse graph | Often more practical | Usually expensive |
| Dense graph | Depends on required sources | Suitable for relatively small graphs |
| One source | Preferred | Unnecessary extra work |
| Many source queries | Repeated execution required | One complete computation |
| Negative edge weights | Supported | Supported |
| Negative-cycle detection | Source-dependent | All-pairs diagonal analysis |
| Memory demand | Lower | Higher |

For a graph with \(V\) vertices and \(E\) edges:

Bellman-Ford:

\[
O(VE)
\]

Floyd-Warshall:

\[
O(V^3)
\]

The correct algorithm depends on the number of required queries, graph density, available memory and the need for all-pairs information.

## 15. Execution Instructions

### Python

Requirements: Python 3.10 or later.

File: `graph_algorithms_iii.py`

Run the script using Python. It uses only the standard library.

### JavaScript

Requirements: Node.js 18 or later.

File: `graph_algorithms_iii.js`

Run using the Node.js runtime. No external npm packages are required.

### C++17

Requirements: A C++17-compatible compiler.

Compile with:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic graph_algorithms_iii.cpp -o graph_algorithms_iii`

Run:

`./graph_algorithms_iii`

On Windows, run `graph_algorithms_iii.exe`.

### Java 17

Requirements: Java 17 JDK.

File: `GraphAlgorithmsIII.java`

Compile:

`javac GraphAlgorithmsIII.java`

Run:

`java GraphAlgorithmsIII`

### PostgreSQL

Requirements: PostgreSQL 15 or later.

File: `graph_algorithms_iii.sql`

Execute the complete SQL file using a PostgreSQL client with permission to create schemas, tables, procedures, functions and triggers.

The script recreates its dedicated `graph_algorithms` schema, so existing data in that schema will be removed.

## 16. Learning Outcomes

The implementations demonstrate the following technical concepts:

- Directed weighted graph representation.
- Edge relaxation.
- Single-source shortest paths.
- All-pairs shortest paths.
- Dynamic programming.
- Negative edge handling.
- Negative-cycle detection.
- Negative-cycle reconstruction.
- Reachability analysis.
- Negative-infinity propagation.
- Predecessor-based path reconstruction.
- Next-vertex matrix reconstruction.
- Graph snapshots and versioning.
- Event-driven programming.
- Asynchronous execution.
- Immutable result modeling.
- Policy-based decision-making.
- Relational graph representation.
- Stored procedures and triggers.
- Transaction handling.
- Cross-validation of independent algorithms.

The central distinction is that Bellman-Ford and Floyd-Warshall calculate shortest-path information, while negative-cycle analysis determines whether the requested minimum distance is mathematically well-defined. A reliable implementation must preserve that distinction throughout computation, result storage, reporting and application-level decisions. 
