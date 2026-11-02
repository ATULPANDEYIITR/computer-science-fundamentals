# Graphs: Directed and Weighted Graph Engineering

## Scope

This project implements graph representation and graph algorithms across Python, JavaScript, C++17, Java 17, and PostgreSQL.

The central model is a weighted graph in which vertices represent entities and edges represent relationships. The implementations distinguish directed graphs from undirected graphs and distinguish graph structure from edge cost.

The four core representations are:

| Representation | Stored relationship | Typical strength | Main cost |
|---|---|---|---|
| Adjacency list | Vertex to neighboring vertices | Sparse graphs | Neighbor lookup requires traversing a list/map |
| Adjacency matrix | Vertex pair to edge value | Dense graphs and constant-time pair lookup | O(V²) storage |
| Directed graph | Source-to-target relationship | Dependency, workflow, routing models | Reachability is asymmetric |
| Weighted graph | Edge plus numeric cost | Routing and optimization | Algorithms must account for edge weights |

The implementations use adjacency-list structures as the primary representation because the realistic examples are sparse. The Python, JavaScript, C++17, and Java implementations also expose traversal and shortest-path operations. The PostgreSQL implementation stores vertices and edges relationally.

## Domain Model

The examples use a transportation network because direction and weight have clear meanings.

A route such as:

`Lucknow -> Kanpur (1.5 hours)`

contains three independent pieces of information:

- `Lucknow` is the source vertex.
- `Kanpur` is the target vertex.
- `1.5` is the edge weight.

Because the graph is directed, the existence of `Lucknow -> Kanpur` does not imply the existence of `Kanpur -> Lucknow`.

The graph therefore models:

`Vertex -> directed weighted edge -> Vertex`

A second graph represents a workflow:

`Design -> Implement -> Test -> Deploy`

This graph is useful for topological ordering because each directed edge represents a dependency.

## Graph Representation

### Adjacency Lists

The Python implementation uses a dictionary containing dictionaries. Each source vertex maps to its outgoing neighbors and their weights.

The JavaScript implementation uses `Map<string, Map<string, number>>`, which gives explicit key-value semantics and preserves efficient neighbor lookup.

The C++ implementation uses `unordered_map<string, vector<pair<string, double>>>`. This exposes the lower-level storage characteristics of a sparse graph and uses STL containers directly.

The Java implementation uses `Map<String, Map<String, Double>>`, separating graph-domain behavior from the algorithms that operate on it.

The PostgreSQL implementation normalizes the representation into:

`graph -> vertex -> edge`

This avoids storing a variable-length adjacency structure inside one relational row and allows SQL constraints and indexes to enforce graph integrity.

### Adjacency Matrix

The Python implementation also provides an adjacency matrix conversion. A matrix entry represents the weight of an edge between two vertices. An absent edge is represented by `None`.

For `V` vertices, the matrix requires O(V²) storage regardless of the number of actual edges. This makes it appropriate for dense graphs or applications that repeatedly need direct pair lookup, but inefficient for sparse networks.

## Directed Graphs

A directed graph treats each edge as an ordered pair.

For example:

`A -> B`

and:

`B -> A`

are different edges.

The implementations therefore store only the specified direction when operating as directed graphs.

The Python implementation also supports undirected graphs. For an undirected edge, adding `A -> B` automatically creates the reverse adjacency relationship. The C++ and JavaScript models make the directed behavior explicit, while the Java implementation supports both graph types through the `GraphType` enum.

Direction matters for:

- dependency graphs
- workflow ordering
- network routing
- state transitions
- reachability
- prerequisite analysis

## Weighted Graphs

An edge weight represents a measurable cost. In the transportation examples, the value is travel time in hours.

The shortest-path calculation therefore minimizes total accumulated weight rather than the number of edges.

For example, a route containing three edges can be better than a route containing two edges if the three-edge route has a smaller total weight.

The implementations restrict Dijkstra-compatible graphs to non-negative weights. This validation is important because Dijkstra's algorithm is not correct for graphs containing negative-weight edges.

The Python, JavaScript, C++17, and Java implementations reject negative weights before adding them to the graph. PostgreSQL reinforces the same rule using the `CHECK (weight >= 0)` constraint.

## Breadth-First Search

Breadth-first search explores vertices level by level.

The traversal begins with a starting vertex, places it into a queue, and repeatedly processes the earliest queued vertex. Unvisited neighbors are added to the queue.

The implementation records visited vertices using a set so that cycles do not cause repeated traversal.

For an unweighted graph, BFS can determine the minimum number of edges between vertices.

Its complexity with an adjacency list is:

`O(V + E)`

where `V` is the number of vertices and `E` is the number of edges.

The weighted examples use Dijkstra rather than BFS when the objective is minimum total cost.

## Depth-First Search

Depth-first search follows one branch as far as possible before returning to another branch.

The Python and JavaScript implementations use recursive traversal. The C++ implementation also uses a recursive visitor function, while Java expresses the traversal through a private recursive method.

A visited set is essential because directed graphs can contain cycles.

DFS is useful for:

- connectivity exploration
- cycle detection
- dependency analysis
- graph decomposition
- structural inspection

With an adjacency list, traversal is O(V + E).

## Dijkstra's Algorithm

The weighted examples use Dijkstra's algorithm for minimum-cost paths.

The algorithm maintains:

- a distance for every vertex
- a predecessor for reconstructing the route
- a priority queue containing the next lowest-cost candidate

The starting vertex has distance zero. Every other vertex begins at infinity.

When an edge produces a cheaper route to a neighbor, the neighbor's distance and predecessor are updated.

The route from `Lucknow` to `Mumbai` is reconstructed by following predecessors backward from `Mumbai` and reversing the resulting sequence.

The example produces a minimum cost of 18.5 hours.

With an adjacency list and binary heap, the implementation has approximately:

`O((V + E) log V)`

time complexity.

Dijkstra is not suitable for negative edge weights. The implementations deliberately validate weights rather than silently accepting invalid input.

## Topological Ordering

A topological ordering exists only for a directed acyclic graph.

The workflow:

`Design -> Implement -> Test -> Deploy`

can therefore be ordered as:

`Design -> Implement -> Test -> Deploy`

The implementations calculate indegrees and repeatedly select vertices whose indegree is zero.

If the algorithm processes fewer vertices than exist in the graph, a cycle is present.

Adding:

`Deploy -> Design`

creates a cycle and makes a topological ordering impossible.

This is a distinct property from shortest-path optimization. Topological sorting evaluates dependency structure, while Dijkstra evaluates weighted route cost.

## Cycle Detection

Directed cycle detection uses three logical states:

- unvisited
- currently being explored
- completely explored

Encountering a vertex that is already in the current exploration set indicates a directed cycle.

The Python, JavaScript, C++17, and Java implementations use this approach.

The Python implementation also supports cycle detection for undirected graphs using the parent vertex to distinguish a legitimate reverse traversal from a true cycle.

## Python Implementation

The Python source models a reusable `Graph` class with:

- directed and undirected modes
- adjacency-list storage
- adjacency-matrix conversion
- BFS
- DFS
- Dijkstra
- shortest-path reconstruction
- topological sorting
- cycle detection
- CSV edge-list export
- validation exceptions
- assertions

`dataclass` is used for immutable edge records, while `Enum` expresses graph type explicitly.

The executable demonstration builds a delivery network, performs traversal, computes a weighted route, tests cycle handling, rejects a negative weight, validates expected output, and exports the edge list.

The file uses only Python standard-library modules.

## JavaScript Implementation

The JavaScript source treats graph processing as a Node.js event-driven application.

`Map` and `Set` provide explicit graph collections. A custom binary min-heap supports Dijkstra without requiring an external package.

The implementation also demonstrates asynchronous file output using `fs.promises`.

The workflow is intentionally different from the Python representation. The JavaScript version emphasizes:

- object-oriented graph state
- `Map` and `Set`
- asynchronous persistence
- Promise-based error propagation
- a custom heap
- deterministic neighbor ordering

A failed validation is propagated as a `GraphError`, while the top-level `main()` function handles asynchronous failure.

## C++17 Implementation

The C++ implementation emphasizes explicit resource and type management.

The graph uses:

- `enum class`
- `struct`
- `unordered_map`
- `vector`
- `unordered_set`
- `priority_queue`
- lambdas
- exceptions
- STL algorithms

The priority queue uses `std::greater` to implement a minimum-oriented heap.

The class separates graph storage, validation, traversal, shortest-path computation, and topological analysis.

The C++ implementation demonstrates how graph algorithms can be expressed with STL containers while retaining direct control over the data representation.

## Java 17 Implementation

The Java implementation uses an enterprise-style separation between domain structures and services.

The graph is exposed through the `GraphAnalyzer` interface. `WeightedGraph` implements the graph operations, while `RouteService` handles route-oriented presentation.

Java records represent immutable value objects:

- `Edge`
- `ShortestPath`

The Dijkstra queue uses a local record for its priority-queue entries.

Streams are used for deterministic vertex ordering and selected traversal operations. Collections remain mutable internally while the public result values are exposed as immutable list results where appropriate.

Validation is represented by a domain-specific `GraphException`.

This design separates:

`graph state -> algorithms -> route service`

rather than putting every responsibility into the application entry point.

## PostgreSQL Implementation

The PostgreSQL implementation stores the graph relationally.

The main entities are:

| Table | Purpose |
|---|---|
| `graph` | Graph identity and direction |
| `vertex` | Individual graph vertices |
| `edge` | Directed weighted relationships |
| `graph_policy` | Graph-level operational constraints |

Foreign keys ensure that an edge cannot reference nonexistent vertices.

The `edge` table has:

- primary key
- graph foreign key
- source vertex foreign key
- target vertex foreign key
- non-negative weight check
- uniqueness constraint for a directed source-target pair

Indexes support common graph operations involving graph identity and source or target vertices.

## Database Integrity

The database enforces several rules independently of application code.

Vertex names cannot be empty.

Edge weights cannot be negative.

An edge's source and target must belong to the same graph.

Self-loops are rejected by the edge constraint.

Graph policies limit the number of vertices and edges.

A trigger validates graph membership before an edge is inserted or updated.

This means invalid graph structure is rejected at the database boundary rather than relying only on client-side validation.

## Recursive SQL Traversal

PostgreSQL recursive CTEs provide graph traversal without moving the graph into an external algorithm implementation.

`reachable_vertices()` performs unweighted reachability and records the traversal depth.

`weighted_reachability()` explores paths while maintaining an accumulated cost and a visited-vertex array. The visited array prevents the recursive query from repeatedly traversing a vertex already present in the current path.

The weighted SQL function is intended as relational path exploration rather than a replacement for a specialized Dijkstra implementation. For large weighted graphs, an application-level priority queue is generally a better fit for shortest-path computation.

## Transactional Workflow

The PostgreSQL script creates the schema and inserts the delivery network inside a transaction.

A later transaction demonstrates inserting or updating a route with `ON CONFLICT`.

This provides an atomic change boundary for graph mutations.

The database also contains an intentionally documented invalid negative-weight operation. It is commented out so that the complete script remains executable while showing the database-level failure condition.

## Relationship Between Concepts

The project keeps the graph concepts separate:

`Graph representation`
→ describes how vertices and edges are stored.

`Directed graph`
→ determines whether edge direction matters.

`Weighted graph`
→ assigns numerical cost to relationships.

`Traversal`
→ explores graph structure.

`Shortest path`
→ optimizes accumulated edge weight.

`Topological ordering`
→ orders dependencies in an acyclic directed graph.

`Cycle detection`
→ determines whether graph structure contains a circular dependency.

These mechanisms can interact, but they solve different problems.

## Edge Cases and Failure Conditions

The implementations explicitly address:

- empty vertex names
- unknown start vertices
- unknown target vertices
- negative edge weights
- unreachable vertices
- directed cycles
- duplicate edge updates
- invalid graph types for topological sorting
- self-loops in the relational model
- edges referencing vertices from another graph
- graph-size policy limits

An unreachable shortest-path query returns an empty path with infinite cost in the language implementations.

A cyclic directed graph causes topological sorting to fail rather than returning an invalid partial order.

## Security and Integrity Considerations

Graph input should be validated before it is accepted into application state.

Negative weights are rejected because they invalidate the assumptions of the selected shortest-path algorithm.

The PostgreSQL model uses foreign keys and constraints instead of trusting application code to maintain referential integrity.

SQL functions use typed parameters rather than dynamically constructed SQL statements.

For production systems, graph data should also be subject to authorization controls at the application and database roles, especially when graph vertices or edges represent sensitive infrastructure, users, assets, or operational dependencies.

The examples deliberately avoid executing arbitrary external commands or accepting unvalidated SQL fragments.

## Performance Characteristics

| Operation | Adjacency-list complexity |
|---|---:|
| Storage | O(V + E) |
| BFS | O(V + E) |
| DFS | O(V + E) |
| Dijkstra with binary heap | O((V + E) log V) |
| Topological sort | O(V + E) |
| Adjacency matrix storage | O(V²) |

For sparse graphs, adjacency lists generally use substantially less memory than matrices.

For dense graphs or applications requiring frequent direct edge-existence checks, an adjacency matrix can be appropriate.

Dijkstra requires non-negative weights. If negative weights are a genuine domain requirement, a different shortest-path algorithm must be selected rather than weakening the validation rule.

## File Structure

The six artifacts correspond to:

| File | Role |
|---|---|
| `graph.py` | Python graph model and algorithms |
| `graph.js` | JavaScript graph model with asynchronous persistence |
| `GraphGovernanceDemo.cpp` | C++17 graph case study |
| `GraphGovernanceDemo.java` | Java 17 domain and service model |
| `graph.sql` | PostgreSQL relational graph model and queries |
| `README.md` | Technical explanation of the implemented mechanisms |

## Execution Model

The Python program runs with the Python standard library.

The JavaScript program runs under Node.js and uses only Node.js built-in modules.

The C++ source requires a C++17-compatible compiler.

The Java source requires Java 17 or later.

The SQL script requires PostgreSQL with support for schemas, enums, recursive CTEs, triggers, functions, and standard relational constraints.

Each implementation is independently executable and does not depend on the runtime state of another implementation.
