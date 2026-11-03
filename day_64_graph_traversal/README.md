# Graph Traversal

## 1. Purpose and Scope

Graph traversal is the systematic process of visiting vertices in a graph while following its edges. It is used to discover reachable entities, examine relationships, find paths, analyze connected regions, and identify dependency structures.

The implementations use adjacency lists and cover two principal traversal algorithms:

- Breadth First Search (BFS)
- Depth First Search (DFS)

They also demonstrate practical applications: shortest paths in unweighted graphs, connected components, directed dependency analysis, cycle detection, and network impact assessment.

## 2. Graph Terminology

A graph is represented by \(G = (V, E)\), where:

- \(V\) is the set of vertices.
- \(E\) is the set of edges connecting vertices.
- A vertex represents an entity, location, service, task, or other identifiable object.
- An edge represents a relationship or connection between two vertices.
- An adjacent vertex is directly connected to another vertex.
- A path is a sequence of vertices connected by edges.
- A cycle is a path that returns to a previously visited vertex.
- A connected component is a maximal group of mutually reachable vertices in an undirected graph.
- A directed graph gives each edge a direction.
- An undirected graph represents relationships without direction.

An adjacency list stores the neighbors of each vertex. It is generally efficient for sparse graphs because it stores existing relationships rather than reserving space for every possible vertex pair.

### Directed and undirected edges

An undirected edge between A and B allows traversal in both directions:

`A -- B`

A directed edge from A to B allows traversal only from A to B:

`A -> B`

The meaning of an edge depends on the domain. In a dependency graph, an edge can represent a prerequisite or impact relationship. In a road network, an edge represents an available connection between locations.

## 3. Breadth First Search

Breadth First Search explores a graph level by level. It visits the starting vertex, then its immediate neighbors, then vertices two edges away, and continues until no undiscovered reachable vertices remain.

BFS uses a queue with First In, First Out behavior.

### BFS workflow

1. Validate the starting vertex.
2. Mark the starting vertex as discovered.
3. Insert it into the queue.
4. Remove the earliest queued vertex.
5. Inspect its adjacent vertices.
6. Mark each newly discovered vertex and record its predecessor.
7. Insert each new vertex into the queue.
8. Continue until the queue is empty.

A vertex must be marked when it is inserted into the queue, not when it is removed. This prevents multiple queue entries for the same vertex.

### BFS traversal tree

BFS records a predecessor for each discovered vertex. These predecessor relationships form a traversal tree rooted at the starting vertex.

The depth of a vertex is the number of edges in its BFS tree path from the root. In an unweighted graph, that depth is the minimum number of edges required to reach the vertex.

### BFS applications

**Shortest paths in unweighted graphs:** BFS discovers vertices in nondecreasing distance from the source. Its predecessor map can reconstruct a path with the minimum number of edges.

**Network reachability:** BFS determines which locations or services can be reached from a starting point.

**Service outage impact:** A directed edge from a dependency to a dependent service allows BFS to identify downstream services that may be affected by a failure.

**Level-based analysis:** The depth associated with each vertex provides a natural grouping by distance from the starting point.

BFS does not calculate minimum travel time when edges have different weights. Weighted shortest-path problems require algorithms that account for edge costs.

## 4. Depth First Search

Depth First Search explores one branch as far as possible before returning to inspect another branch.

DFS uses a stack or recursive function calls. The implementations use explicit stacks to avoid depending on programming-language recursion limits.

### DFS workflow

1. Validate and mark the starting vertex.
2. Place it on the stack.
3. Inspect an undiscovered adjacent vertex.
4. Record its predecessor and depth.
5. Continue from that vertex.
6. Return to an earlier vertex when no undiscovered neighbor remains.
7. Stop when the stack is empty.

The predecessor relationships form a DFS tree.

A stack of vertex-and-neighbor-iterator frames is used in Python, JavaScript, and Java. This preserves recursive DFS exploration order without requiring recursive calls. The C++ implementation uses explicit frames containing a vertex and its next neighbor position.

### DFS applications

**Dependency inspection:** DFS follows a chain of relationships deeply before exploring alternative branches.

**Reachability:** DFS determines which vertices are accessible from a starting vertex.

**Cycle-related analysis:** DFS-based graph methods can detect back edges and support cycle detection.

**Connected-region inspection:** DFS can enumerate the members of a component in an undirected graph.

**Topological analysis:** Directed acyclic graphs can be ordered so that prerequisites appear before dependent vertices.

DFS does not generally produce shortest paths. Its first discovered path to a vertex can be longer than another available path.

## 5. BFS and DFS Compared

| Property | BFS | DFS |
|---|---|---|
| Primary structure | Queue | Stack or recursion |
| Exploration pattern | Level by level | Branch by branch |
| Discovery depth | Nondecreasing | May move deeper before returning |
| Unweighted shortest path | Yes | No general guarantee |
| Reachability | Yes | Yes |
| Connected components | Yes | Yes |
| Cycle analysis | Possible with additional state | Commonly used with additional state |
| Topological ordering | Kahn's algorithm uses a queue | DFS-based ordering is another option |
| Deep graph handling | Uses an iterative queue | Explicit stack avoids recursion limits |

Both algorithms take \(O(V + E)\) time with an adjacency-list representation when each vertex and edge is processed a constant number of times.

Their traversal order can differ even when they discover the same reachable vertices. The order also depends on how neighboring vertices are ordered.

## 6. Traversal State and Data Structures

The implementations maintain the following state:

| Structure | Purpose |
|---|---|
| Adjacency list | Stores vertex relationships |
| Queue | Maintains BFS processing order |
| Stack | Maintains DFS exploration state |
| Visited or discovered set | Prevents repeated discovery |
| Parent map or array | Records the traversal tree |
| Depth or distance map | Records the number of tree edges from the source |
| Traversal order | Records the sequence of visited vertices |

The discovered state is particularly important for graphs containing cycles. Without it, a traversal could repeatedly revisit vertices and fail to terminate.

### Parent-based path reconstruction

A predecessor is recorded when a vertex is first discovered. To reconstruct a path:

1. Start at the target vertex.
2. Follow its predecessor.
3. Continue until the starting vertex is reached.
4. Reverse the collected sequence.

If the target was not discovered, no path exists from the selected source within the traversed graph.

## 7. Practical Applications Implemented

### 7.1 Transport network analysis

The Python and C++ implementations model locations connected by road segments.

The C++ example also models road availability. A road can be open or closed, and closed roads are ignored during traversal.

This supports several operational questions:

- Which locations can emergency teams reach?
- What is the route with the fewest road segments?
- Which locations become separated after road closures?
- Which locations belong to the same connected component?

BFS provides the minimum-hop route. Connected-component analysis identifies regions separated by unavailable connections.

The route is based on the number of edges, not road distance, congestion, or travel time.

### 7.2 Service dependency impact analysis

The JavaScript and Java implementations use directed service relationships.

An edge from service A to service B means that B depends on A or may be affected by A's failure.

For example:

`customer-db -> orders-api -> checkout-api -> web-frontend`

A BFS starting at `customer-db` identifies reachable downstream services and records the number of dependency hops.

The result can support preliminary outage-impact analysis. It does not automatically establish the actual severity of an incident because real service behavior may also depend on redundancy, caching, failover, optional dependencies, and runtime configuration.

### 7.3 Task and deployment ordering

A directed acyclic graph (DAG) represents prerequisite relationships.

For example:

`Extract Data -> Validate Data -> Analyze Data -> Generate Report`

A valid topological ordering places each prerequisite before its dependent task.

The Python and Java implementations use Kahn's algorithm:

1. Calculate the indegree of every vertex.
2. Insert all zero-indegree vertices into a ready queue.
3. Remove one ready vertex and append it to the result.
4. Decrease the indegree of its outgoing neighbors.
5. Add newly eligible vertices to the ready queue.
6. Compare the number of processed vertices with the graph's vertex count.

If some vertices remain, the graph contains a cycle and cannot have a complete topological ordering.

## 8. Python Implementation

The Python file defines a reusable `Graph` class and a `TraversalResult` dataclass.

The graph can be directed or undirected. Neighbor sets prevent duplicate edges, and sorted neighbor access provides deterministic traversal results.

Its main mechanisms are:

- `breadth_first_search()` implements queue-based BFS.
- `depth_first_search()` implements iterative DFS with neighbor iterators.
- `shortest_path()` uses BFS and predecessor reconstruction.
- `connected_components()` identifies components in an undirected graph.
- `topological_order()` uses Kahn's algorithm with a minimum heap.

The implementation distinguishes an unknown vertex from a known but unreachable target. It also validates vertex identifiers and supports a maximum number of visited vertices.

A traversal limit protects against unexpectedly large traversals, although a fixed limit must be selected according to the application's memory and workload constraints.

## 9. JavaScript Implementation

The JavaScript file uses Node.js events to expose traversal progress.

`Graph` stores adjacency relationships in `Map` and `Set` objects. `TraversalEngine` extends `EventEmitter` and supports asynchronous BFS and DFS.

The engine emits:

| Event | Meaning |
|---|---|
| `start` | A traversal has begun |
| `discover` | A vertex has been discovered |
| `visit` | A vertex is being processed |
| `finish` | The traversal completed successfully |
| `failure` | The traversal ended because of an error |

The asynchronous implementation yields control to the Node.js event loop between processed vertices. This allows other scheduled tasks to execute during traversal.

An `AbortSignal` provides cancellation. A maximum-visited limit prevents unbounded traversal of unexpectedly large graphs.

The event model is useful for monitoring, visualization, progress reporting, and integration with event-driven applications. Event listeners should remain lightweight because synchronous event handlers execute as part of event emission.

## 10. C++17 Implementation

The C++ program models an emergency road network.

`RoadNetwork` manages location labels, adjacency lists, and a set of closed undirected roads. Each road is stored in both adjacency lists, while its closure state is stored once using a normalized vertex pair.

The program implements:

- BFS using `std::queue`.
- DFS using an explicit vector of stack frames.
- Shortest-route reconstruction with `std::optional`.
- Connected-component discovery after road closures.
- Validation of vertex identifiers and road operations.

Sorted adjacency lists make traversal output deterministic. The use of an explicit DFS stack avoids recursive call-stack growth.

The network model distinguishes a road that does not exist from a road that exists but is closed. Attempts to modify an unknown road produce an exception.

## 11. Java 17 Implementation

The Java program provides an enterprise-oriented service dependency model.

Its domain types include:

- `ServiceNode`: an immutable record identifying a service and its criticality.
- `Criticality`: an enum containing CRITICAL, HIGH, MEDIUM, and LOW.
- `DependencyGraph`: an immutable graph snapshot.
- `TraversalResult`: an immutable result containing order, parent relationships, and depth.
- `ImpactReport`: an immutable outage-impact assessment.

The `TraversalStrategy` interface separates traversal behavior from the domain model. BFS and DFS are implemented as separate strategy classes.

`ImpactAssessmentService` uses BFS to identify downstream services and groups affected services by criticality.

`TraversalService` also implements topological ordering for dependency-based deployment sequences. A `CycleDetectedException` identifies services that prevent a valid ordering.

The builder validates service identifiers and dependency endpoints before constructing an immutable graph. This supports safe concurrent reading of a completed graph snapshot, although graph updates require constructing a new snapshot.

## 12. PostgreSQL Implementation

The SQL file stores graph data using three principal tables.

| Table | Responsibility |
|---|---|
| `graph_model` | Graph metadata and directed/undirected configuration |
| `vertex` | Vertices belonging to a graph |
| `edge` | Relationships between vertices |

### Relational integrity

The vertex table uses a composite primary key containing `graph_id` and `vertex_id`.

The edge table uses composite foreign keys for both endpoints. This ensures that an edge cannot connect a vertex from a different graph.

The edge primary key prevents duplicate representations of the same directed edge.

For undirected graphs, a trigger enforces canonical edge orientation. Each relationship is stored once with the smaller vertex identifier as its source. Traversal interprets the relationship in both directions.

### Edge availability

The `is_open` field represents whether a transport connection is available.

A closed edge requires a closure reason and is excluded from traversal. This allows the network to retain its infrastructure records while changing the effective graph used for route analysis.

### Database traversal function

`graph_lab.traverse()` supports two algorithms:

- `BFS` selects the earliest discovered unexpanded vertex.
- `DFS` selects the latest discovered unexpanded vertex.

A temporary table stores discovery order, depth, predecessor, and expansion state.

For BFS, the oldest inserted unexpanded vertex is selected. For DFS, the newest inserted unexpanded vertex is selected. Descending neighbor insertion gives deterministic DFS exploration when the stack is processed in last-in, first-out order.

The unique vertex constraint in the temporary table ensures that each vertex is discovered once.

### Shortest paths

`graph_lab.shortest_path()` invokes BFS and uses a recursive CTE to follow predecessor links from the target back to the source.

The function returns a `BIGINT[]` containing the path. A null result indicates that the existing target is unreachable from the starting vertex.

`graph_lab.is_reachable()` exposes the same result as a Boolean.

### Reporting and indexes

The `vertex_degree_summary` view reports incoming and outgoing adjacency counts.

For undirected graphs, the view generates both traversal directions from each stored edge. For directed graphs, it retains the stored direction.

The indexes support graph-specific outgoing and incoming edge lookups. A partial index covers open outgoing edges, which are the relationships used by traversal.

The SQL examples demonstrate BFS, DFS, path reconstruction, reachability, graph-level counts, edge validation, degree aggregation, and closure reporting.

## 13. Complexity Analysis

Let \(V\) represent the number of vertices and \(E\) the number of edges.

| Operation | Typical time complexity | Explanation |
|---|---:|---|
| Add vertex | \(O(1)\) average | Adjacency entry creation |
| Add edge | \(O(1)\) average with hash-based adjacency | Insert relationship |
| BFS | \(O(V + E)\) | Each reachable vertex and adjacency relationship is processed |
| DFS | \(O(V + E)\) | Each reachable vertex and adjacency relationship is processed |
| Shortest path reconstruction | \(O(V)\) worst case | Follows predecessor links |
| Connected components | \(O(V + E)\) | Traverses each component |
| Kahn topological ordering | \(O(V + E)\) with a queue | Each vertex and edge is processed once |
| Kahn ordering with a heap | \(O(E + V \log V)\) | Heap operations maintain deterministic selection |

The listed bounds assume an adjacency-list representation and constant-time visited-state checks. Sorting neighbors introduces additional costs when deterministic ordering is required.

Memory complexity for a traversal is \(O(V)\) for its queue or stack, discovered state, parent relationships, and depth information. The graph itself requires \(O(V + E)\) storage.

## 14. Edge Cases and Failure Handling

The implementations account for the following conditions:

| Condition | Expected behavior |
|---|---|
| Unknown starting vertex | Validation error |
| Known but unreachable target | No path result |
| Isolated vertex | Traversal returns that vertex |
| Duplicate edge | Stored once or rejected, depending on implementation |
| Self-loop | Supported by the Python and JavaScript graph models; rejected by the C++ road model |
| Cycle in an undirected graph | Traversal terminates through discovered-state checks |
| Cycle in a directed dependency graph | Topological ordering fails |
| Closed road | Excluded from effective transport traversal |
| Directed edge | Traversal follows its direction |
| Traversal limit exceeded | Traversal fails explicitly |
| Cancelled asynchronous traversal | JavaScript raises an abort error |

An algorithm should not silently treat an invalid input as an unreachable vertex. Input errors and graph reachability are separate conditions.

## 15. Performance and Production Considerations

### Graph representation

Adjacency lists are appropriate when each vertex is connected to a relatively small number of other vertices. Dense graphs may justify an adjacency matrix for particular workloads, at the cost of \(O(V^2)\) storage.

### Neighbor ordering

Sorting neighbors makes results reproducible. This is useful for tests, reports, and debugging. If traversal order is not relevant, maintaining insertion order or using unsorted adjacency structures can reduce sorting overhead.

### Large graphs

A production traversal should consider:

- Maximum permitted vertices and edges.
- Memory consumption of queues, stacks, and predecessor structures.
- Traversal time limits.
- Cancellation requirements.
- Graph update frequency.
- Consistency of graph snapshots during traversal.
- Access restrictions for sensitive network relationships.

### Weighted relationships

BFS minimizes the number of edges, not the total edge weight. If roads have distance, cost, or travel-time values, a weighted shortest-path algorithm is required.

### Concurrent graph changes

Traversal results are based on the graph state observed during processing. Applications that update edges concurrently should use immutable snapshots, transactions, versioned graph data, or suitable synchronization.

### Security and validation

Vertex identifiers and graph membership must be validated before traversal. Database access should use parameterized statements rather than dynamically concatenated SQL. Application services should authorize access to sensitive graph data independently of the traversal algorithm.

## 16. Technical Distinctions

The following mechanisms solve different problems and should not be treated as interchangeable:

| Mechanism | Primary purpose |
|---|---|
| BFS | Level-by-level traversal |
| DFS | Branch-oriented traversal |
| Reachability | Determines whether a target can be discovered |
| Shortest path | Finds a minimum-edge path in an unweighted graph |
| Connected components | Partitions an undirected graph into connected groups |
| Topological ordering | Orders vertices in a directed acyclic graph |
| Cycle detection | Identifies cyclic relationships |
| Traversal cancellation | Stops an active traversal |
| Edge availability | Determines which relationships may currently be followed |

The choice of algorithm depends on graph direction, edge weights, data volume, the required result, and operational constraints.
