# Graph Algorithms I: BFS, DFS and Connected Components

## 1. Technical Scope

This project implements three fundamental graph algorithm categories:

- Breadth-First Search (BFS)
- Depth-First Search (DFS)
- Connected Components

The implementations demonstrate graph representation, traversal, reachability, shortest paths in unweighted graphs, dependency analysis, cycle detection, and network partitioning.

The five source files provide independent implementations using Python, JavaScript, C++17, Java 17, and PostgreSQL.

The central domain scenario is enterprise infrastructure and software dependency analysis.

## 2. Graph Fundamentals

A graph is a mathematical structure:

\[
G=(V,E)
\]

Where:

- \(V\) represents vertices.
- \(E\) represents edges connecting vertices.
- An edge represents a relationship between two vertices.

A vertex may represent a computer, service, person, application, database, or deployment component.

An edge represents connectivity or dependency.

### Graph classifications

| Graph type | Description |
|---|---|
| Undirected | Relationships operate in both directions |
| Directed | Relationships have a defined direction |
| Weighted | Edges carry numerical costs |
| Unweighted | Edges represent equal-cost transitions |
| Connected | Every pair of vertices has a path between them |
| Disconnected | At least two vertices cannot reach one another |
| Cyclic | At least one cycle exists |
| Acyclic | No cycle exists |

The implementations use adjacency lists as their primary representation.

An adjacency list stores the neighbors of each vertex.

For a graph with \(V\) vertices and \(E\) edges, its storage complexity is:

\[
O(V+E)
\]

This representation is suitable for sparse infrastructure networks and dependency graphs.

## 3. Breadth-First Search (BFS)

### 3.1 Concept

Breadth-First Search explores a graph in increasing order of distance from a starting vertex.

It uses a FIFO queue.

The algorithm processes all immediately reachable neighbors before processing vertices at greater distances.

### 3.2 Mechanism

The traversal maintains:

- A queue of discovered vertices.
- A visited structure.
- A distance map.
- A parent map.

The parent map records the vertex through which another vertex was first discovered.

The shortest path can be reconstructed by following parent references backward from the destination.

### 3.3 Algorithm workflow

    Start vertex
         |
         v
    Initialize queue
         |
         v
    Mark source visited
         |
         v
    Remove front vertex
         |
         v
    Examine unvisited neighbors
         |
         v
    Record distance and parent
         |
         v
    Add neighbors to queue
         |
         v
    Queue empty?
       /     \
     No       Yes
     |         |
     v         v
    Repeat   Return results

### 3.4 Shortest paths

BFS finds shortest paths in terms of the number of edges for unweighted graphs.

For example:

    API -> Gateway -> Orders -> Database

The shortest path contains three edges.

Its distance is:

\[
d(API,Database)=3
\]

BFS does not automatically find minimum total edge weight in a weighted graph. Algorithms such as Dijkstra's algorithm are required for non-negative weighted shortest paths.

### 3.5 Multi-source BFS

Multi-source BFS begins from multiple source vertices simultaneously.

Every source receives distance zero.

The algorithm calculates the minimum number of edges from any supplied source to each reachable vertex.

Applications include:

- Nearest available server.
- Nearest emergency facility.
- Multiple network monitoring points.
- Nearest service endpoint.
- Distributed resource discovery.

### 3.6 BFS implementation decisions

| Language | Implementation |
|---|---|
| Python | `collections.deque` |
| JavaScript | Array with a moving head index |
| C++17 | `std::queue` |
| Java 17 | `ArrayDeque` |
| PostgreSQL | Recursive CTE with path tracking |

The JavaScript and C++ implementations use queue-based traversal rather than repeatedly removing the first element of a dynamically growing array.

### 3.7 Complexity

| Operation | Time complexity |
|---|---|
| BFS traversal | \(O(V+E)\) |
| Shortest path reconstruction | \(O(V)\) maximum |
| Multi-source BFS | \(O(V+E)\) |
| Adjacency-list storage | \(O(V+E)\) |

The actual traversal examines only the vertices reachable from the selected source.

## 4. Depth-First Search (DFS)

### 4.1 Concept

Depth-First Search explores one path as deeply as possible before returning to explore alternative paths.

DFS uses a stack, either explicitly or through recursion.

Unlike BFS, DFS does not guarantee shortest paths.

Its primary strength is structural graph analysis.

### 4.2 Mechanism

DFS maintains:

- A visited set.
- A discovery order.
- A finishing order.
- An active recursion-path set when detecting directed cycles.

The discovery order records when a vertex is first visited.

The finishing order records when all its outgoing traversal paths have been processed.

### 4.3 Applications

**Dependency analysis**

A directed edge:

    Core -> Authentication

means that the Core component must precede Authentication in the dependency ordering used by this project.

A topological ordering can establish a valid processing sequence when the directed graph is acyclic.

**Cycle detection**

A directed cycle such as:

    Core -> API -> Frontend -> Core

indicates a circular dependency.

Such a dependency prevents a valid topological ordering.

**Path exploration**

DFS can establish whether a path exists between two vertices.

It is useful for structural analysis where finding the minimum number of edges is not required.

### 4.4 Cycle detection distinction

For directed graphs, an edge leading to a vertex currently on the active DFS path indicates a back edge and therefore a directed cycle.

For undirected graphs, the edge leading back to the immediate parent is not a cycle.

The C++ and Java implementations use the appropriate distinction.

The Python implementation uses recursive traversal with parent tracking.

The JavaScript implementation uses iterative DFS to avoid dependence on the JavaScript call-stack limit.

### 4.5 Topological sorting

Topological sorting produces a linear ordering of vertices in a directed acyclic graph (DAG).

For every directed edge:

\[
u \rightarrow v
\]

The resulting order must place \(u\) before \(v\).

The implementations derive this ordering by reversing DFS finishing order.

A cyclic directed graph has no valid topological ordering.

### 4.6 Complexity

| Operation | Complexity |
|---|---|
| DFS traversal | \(O(V+E)\) |
| Directed cycle detection | \(O(V+E)\) |
| Topological sorting | \(O(V+E)\) |
| Discovery and finish storage | \(O(V)\) |

Recursive DFS may exhaust the call stack on very deep graphs.

For large production graphs, iterative DFS is generally preferable unless recursion depth is controlled.

## 5. Connected Components

### 5.1 Concept

A connected component is a maximal set of vertices in an undirected graph where every vertex can reach every other vertex in that set.

A graph can contain multiple independent components.

Consider:

    Component 1:
    API -- Gateway -- Orders -- Database

    Component 2:
    Monitoring -- Logging

    Component 3:
    Backup -- Storage

    Component 4:
    OfflineNode

The graph contains four connected components.

`OfflineNode` is an isolated vertex.

### 5.2 Algorithm

1. Initialize an empty visited set.
2. Select an unvisited vertex.
3. Run BFS from that vertex.
4. Collect every discovered vertex.
5. Mark the resulting set as one component.
6. Select another unvisited vertex.
7. Continue until every vertex has been visited.

Each vertex is assigned to exactly one component.

### 5.3 Applications

- Network segmentation.
- Identification of disconnected infrastructure.
- Social network communities at the connectivity level.
- Service availability analysis.
- Dependency isolation.
- Communication network analysis.

Connected components are different from strongly connected components.

For directed graphs, strongly connected components require directed reachability in both directions between every pair of vertices.

The connected-components implementations deliberately reject directed graphs rather than treating directed reachability as undirected connectivity.

### 5.4 Complexity

\[
O(V+E)
\]

Each vertex and edge is processed a bounded number of times.

## 6. Distinguishing the Three Algorithms

| Characteristic | BFS | DFS | Connected Components |
|---|---|---|---|
| Primary purpose | Layered traversal | Deep exploration | Network partitioning |
| Main structure | Queue | Stack or recursion | BFS or DFS |
| Shortest unweighted paths | Yes | No guarantee | Not its primary purpose |
| Cycle detection | Not implemented as its primary operation | Yes | Not its primary operation |
| Topological ordering | No | Yes, for DAGs | No |
| Disconnected graph handling | Reachable subgraph | Can cover entire graph | Entire undirected graph |
| Complexity | \(O(V+E)\) | \(O(V+E)\) | \(O(V+E)\) |

## 7. Implementation Architecture

### Python

File purpose: graph modeling and algorithm simulation.

Implemented capabilities:

- `Graph` class.
- Directed and undirected graph types.
- Adjacency-list storage.
- BFS shortest paths.
- Multi-source BFS.
- BFS level grouping.
- DFS discovery and finishing orders.
- Directed and undirected cycle detection.
- Topological sorting.
- Connected components.
- Isolated vertex detection.
- JSON graph persistence.
- Unit tests and exception handling.

The implementation uses `defaultdict(set)` to prevent duplicate adjacency entries.

The `deque` implementation provides efficient queue operations.

The persistence layer validates graph structure during loading and restricts filenames to the current working directory.

### JavaScript

File purpose: event-driven graph analysis.

Implemented capabilities:

- `Map`-based adjacency storage.
- `Set`-based neighbor collections.
- BFS and multi-source BFS.
- Iterative DFS.
- Cycle detection.
- Topological ordering.
- Connected component statistics.
- JSON serialization.
- Event-driven analysis monitoring.
- Asynchronous processing.
- Runtime validation.
- Automated assertions.

`GraphMonitor` emits lifecycle events:

| Event | Meaning |
|---|---|
| `analysisStarted` | Graph analysis begins |
| `vertexDiscovered` | Reachable vertices have been identified |
| `analysisCompleted` | Analysis report is available |
| `analysisFailed` | Analysis encountered an error |

The asynchronous interface separates graph computation from monitoring and reporting.

### C++17

File purpose: efficient graph traversal and structural analysis.

Implemented capabilities:

- Strongly typed graph classification.
- STL adjacency containers.
- `std::map` and `std::set` graph representation.
- BFS shortest paths.
- Multi-source BFS.
- DFS.
- Directed and undirected cycle detection.
- Topological sorting.
- Connected components.
- Input validation.
- Exception-based error handling.
- Automated tests.

The implementation uses ordered containers for deterministic output.

This introduces additional lookup and insertion costs compared with hash-based containers, but makes execution results easier to inspect and test.

### Java 17

File purpose: enterprise-oriented graph analysis.

Implemented capabilities:

- Immutable result records.
- Explicit graph interfaces.
- Domain-specific exceptions.
- Directed and undirected graph types.
- BFS shortest paths.
- Multi-source traversal.
- DFS.
- Cycle detection.
- Topological dependency ordering.
- Connected components.
- Isolated vertex reporting.
- Dependency deployment service.
- Automated validation.

The `GraphAnalyzer` interface defines the analysis contract.

`DependencyService` separates dependency-order decisions from the underlying graph representation.

This design makes it possible to test deployment eligibility independently from traversal implementation.

### PostgreSQL

File purpose: relational graph storage and database-side traversal.

Implemented database objects:

| Object | Responsibility |
|---|---|
| `graphs` | Graph definitions and classifications |
| `graph_vertices` | Vertex records |
| `graph_edges` | Edge relationships |
| `graph_analysis` | Execution records |
| `traversal_log` | Traversal audit data |
| `bfs_traversal` | Recursive BFS-style reachability and minimum distances |
| `dfs_traversal` | Recursive path exploration |
| `connected_components` | Undirected component identification |
| `multi_source_bfs` | Multiple-source distance calculations |
| `component_summary` | Graph-level reporting |
| `graph_edge_details` | Human-readable edge information |

The schema uses composite foreign keys to ensure that edge endpoints belong to the same graph.

Undirected edges are stored in both directions through a database trigger.

The insertion procedure uses canonical endpoint ordering to prevent duplicate undirected relationships.

Indexes support graph-specific adjacency lookups and reverse traversal.

## 8. PostgreSQL Recursive Query Design

Recursive CTEs provide a relational mechanism for expressing graph traversal.

The general structure is:

    WITH RECURSIVE traversal AS (
        -- Initial vertices

        UNION ALL

        -- Expand through adjacent vertices
    )
    SELECT ...
    FROM traversal;

The anchor query identifies starting vertices.

The recursive query expands through edges.

Path arrays prevent revisiting vertices already present in the current traversal path.

The BFS implementation calculates minimum depth by grouping all discovered paths by vertex.

The DFS implementation preserves a traversal path for each reachable vertex and selects a representative shortest-depth path.

The connected-components implementation computes reachability from every vertex using recursive `UNION`, then groups mutually reachable vertices using their minimum vertex identifier.

### Database limitations

The PostgreSQL implementation is intended for educational and moderate-sized graph workloads.

Its recursive queries can generate many intermediate paths.

The path-enumeration approach is not equivalent to a queue-based BFS implementation in terms of execution cost.

For large graphs, consider a procedural frontier table, temporary visited table, iterative PL/pgSQL traversal, or a specialized graph-processing system.

The depth limit prevents unbounded recursive expansion but does not make path enumeration scalable for dense graphs.

## 9. Realistic Enterprise Scenario

The sample infrastructure graph models:

    API
     |
    Gateway
     |
    Orders
    /    \
    DB    Cache

    Monitoring -- Logging

    Backup -- Storage

    OfflineNode

BFS from API identifies reachable infrastructure components and calculates minimum hop counts.

DFS over a deployment dependency graph identifies dependency cycles and derives a valid deployment order.

Connected components identify independent infrastructure groups.

These operations answer different operational questions:

| Operational question | Algorithm |
|---|---|
| What is the shortest route between two services? | BFS |
| Which services are reachable from multiple monitoring points? | Multi-source BFS |
| Is a deployment dependency cycle present? | DFS |
| What is a valid deployment sequence? | DFS-based topological sorting |
| Which infrastructure components are disconnected? | Connected Components |
| Which vertices have no connections? | Isolated vertex detection |

## 10. Validation and Edge Cases

The implementations account for the following conditions:

- Empty vertex identifiers.
- Duplicate edges.
- Unknown source vertices.
- Unknown destination vertices.
- Disconnected vertices.
- Isolated vertices.
- Empty multi-source input.
- Multiple BFS sources.
- Directed cycles.
- Undirected cycles.
- Directed graph component-analysis rejection.
- Invalid serialized graph structures.
- Invalid database edge endpoints.
- Duplicate database relationships.
- Negative edge weights.
- Self-loops.
- Database referential integrity.

An unreachable destination is represented as an absent path rather than an artificial path or distance.

A source and destination that are the same vertex have a shortest path containing that single vertex and distance zero.

## 11. Performance and Security Considerations

### Performance

Adjacency lists are preferable to adjacency matrices for sparse graphs.

An adjacency matrix requires:

\[
O(V^2)
\]

space, even when relatively few edges exist.

BFS and DFS require:

\[
O(V+E)
\]

time under adjacency-list traversal.

The database implementation uses indexes on graph identifiers and edge endpoints to reduce adjacency lookup costs.

The JavaScript implementation avoids expensive front-of-array removal.

The Java and C++ implementations use explicit graph models and structured traversal results.

### Security and integrity

Production graph systems should enforce:

- Validated vertex identifiers.
- Parameterized database operations.
- Referential integrity.
- Authorization for graph modifications.
- Restricted database privileges.
- Controlled metadata storage.
- Resource limits on traversal.
- Input-size restrictions.
- Audit records for graph changes.
- Transactional updates.

Recursive graph queries should not be exposed to unrestricted user-controlled graph sizes.

A traversal limit is a safety control, not a replacement for workload management.

## 12. Execution Requirements

| Implementation | Runtime | Dependencies |
|---|---|---|
| Python | Python 3.10+ | Standard library |
| JavaScript | Node.js 18+ | Standard library |
| C++17 | C++17 compiler | Standard library |
| Java | Java 17 | Standard library |
| PostgreSQL | PostgreSQL 15+ | PostgreSQL |

### Execution commands

| File | Command |
|---|---|
| Python | `python graph_algorithms.py` |
| JavaScript | `node graph_algorithms.js` |
| C++17 | `g++ -std=c++17 -O2 -Wall -Wextra -pedantic graph_algorithms.cpp -o graph_algorithms` followed by `./graph_algorithms` |
| Java 17 | `javac Main.java` followed by `java Main` |
| PostgreSQL | Execute `graph_algorithms.sql` using `psql` |

The PostgreSQL script creates the `graph_lab` schema, database objects, sample records, validation procedures, and reporting queries.

It should be executed against a database where the executing role has the required schema and table creation privileges.

## 13. Testing Expectations

The automated tests verify:

| Test | Expected behavior |
|---|---|
| BFS shortest path | Returns a minimum-edge path |
| Unreachable destination | Returns no path |
| Multi-source BFS | Uses the minimum source distance |
| Connected components | Identifies independent groups |
| Isolated vertex | Identifies a vertex without edges |
| Directed acyclic graph | Produces a topological ordering |
| Directed cycle | Rejects topological ordering |
| Unknown vertex | Raises a validation error |
| Directed component request | Rejects invalid graph operation |
| Graph serialization | Preserves vertices and relationships |

The expected sample infrastructure graph contains:

- 11 vertices.
- 7 logical undirected edges.
- 4 connected components.
- 1 isolated vertex.

These values provide a consistent reference for validating the five implementations.
