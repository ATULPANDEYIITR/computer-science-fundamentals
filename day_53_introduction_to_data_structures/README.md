# Introduction to Data Structures

## Scope

This project introduces data structures through their abstract behavior, physical representation, access patterns, and algorithmic cost.

The central distinction is between an **abstract data type (ADT)** and a **data structure**.

An ADT specifies what operations mean and what behavior users can rely on. A data structure specifies how those operations are represented and implemented.

For example:

- A **stack ADT** exposes operations such as `push`, `pop`, and `peek`.
- A Python list, Java `ArrayDeque`, or C++ `vector` can be used to implement stack behavior.
- A **queue ADT** requires first-in-first-out behavior, while its implementation can use a linked structure, circular buffer, or deque.
- A **priority queue ADT** removes the element with the highest scheduling priority rather than simply the oldest element.

The five implementations use the same conceptual foundation but deliberately apply different programming techniques and use cases.

## Structural Classification

| Category | Examples | Main relationship | Typical operations |
|---|---|---|---|
| Linear | Stack, queue, linked list, array/list | Each element has a sequential position | Insert, remove, search, traverse |
| Non-linear | Tree, graph | Elements can have hierarchical or network relationships | Search, traversal, insertion, path analysis |
| Associative | Hash table/set | Values are accessed through keys or membership | Insert, lookup, remove |
| Priority-based | Heap/priority queue | Access is determined by priority | Insert, minimum/maximum removal |
| Ordered | Binary search tree | Ordering guides search | Insert, search, ordered traversal |

A structure should be selected according to the operations the application performs most frequently. Choosing a structure solely because it can store the required values ignores the cost of accessing those values.

## Abstract Data Types

An ADT defines behavior without requiring a particular representation.

### Stack

The stack follows **last-in-first-out (LIFO)** semantics.

If the values are inserted as:

`A → B → C`

the next removal is:

`C`

The Python implementation uses a list, Java uses `ArrayDeque`, and C++ uses `vector`. The representation differs, but the externally visible stack behavior remains the same.

Stacks are appropriate for:

- Undo operations
- Nested processing
- Expression evaluation
- Backtracking
- Function-call-like workflows

A stack does not provide efficient arbitrary access as its primary operation. Treating it as a general-purpose searchable collection weakens the abstraction.

### Queue

The queue follows **first-in-first-out (FIFO)** semantics.

If requests arrive as:

`A → B → C`

the removal order is:

`A → B → C`

The Python implementation uses `deque`, Java and C++ use double-ended queue abstractions, and the JavaScript implementation maintains a logical head index to avoid repeatedly shifting an array.

Queues are useful for:

- Request processing
- Breadth-first traversal
- Event processing
- Job scheduling
- Producer-consumer workflows

A queue is especially useful when fairness depends on arrival order.

### Priority Queue

A priority queue changes the removal rule. The next item is determined by priority rather than insertion time.

The JavaScript implementation uses a custom binary min-heap. Java uses `PriorityQueue`. The database represents priority explicitly and indexes pending work by priority.

The heap gives typical `O(log n)` insertion and removal while the best element can be inspected in `O(1)`.

## Linear Structures

Linear structures arrange elements around a sequential relationship.

### Arrays and Dynamic Arrays

A dynamic array provides contiguous storage and indexed access.

Typical characteristics are:

| Operation | Typical complexity |
|---|---:|
| Indexed read | `O(1)` |
| Append | Amortized `O(1)` |
| Insert at beginning | `O(n)` |
| Delete from beginning | `O(n)` |
| Linear search | `O(n)` |

Contiguous storage also tends to provide good cache locality.

The C++ implementation explicitly uses `vector` for a large sequential scan. The vector reserves capacity before inserting one million measurements, reducing repeated allocation and copying.

### Linked Lists

A linked list stores nodes connected through references or pointers.

For a singly linked list:

- Access by position is `O(n)`.
- Search is `O(n)`.
- Inserting after a known node can be `O(1)`.
- Each node requires additional reference storage.

The Python implementation uses an explicit node object with a `value` and `next` reference.

Linked lists are useful when structural insertion and removal are more important than random indexed access. They are not automatically faster than arrays. Sequential memory locality can make arrays faster for many workloads even when both approaches have superficially similar complexity for a particular operation.

## Non-Linear Structures

Non-linear structures represent relationships that cannot be reduced to one simple sequence.

### Trees

A tree is hierarchical.

A binary search tree maintains an ordering rule:

- Values smaller than a node belong in the left subtree.
- Values larger than a node belong in the right subtree.
- Duplicate handling must be explicitly defined.

For a reasonably balanced binary search tree:

- Search: approximately `O(log n)`
- Insert: approximately `O(log n)`
- Ordered traversal: `O(n)`

For a badly skewed tree, search and insertion can degrade to `O(n)`.

The implementations do not claim that an ordinary binary search tree is automatically balanced. This distinction matters when performance guarantees are required.

The Python, C++, and Java examples expose ordered traversal and membership operations while deliberately keeping the tree implementation small enough to show the underlying mechanism.

### Graphs

A graph represents relationships among vertices.

A graph can be:

- Directed or undirected
- Weighted or unweighted
- Cyclic or acyclic
- Sparse or dense

The Python graph uses an adjacency list. The JavaScript dependency graph uses a `Map` containing `Set` objects. The C++ implementation uses `unordered_map` and vectors. PostgreSQL stores vertices and edges as relational rows.

Adjacency lists are generally appropriate for sparse graphs because storage is proportional to the number of vertices and edges rather than the square of the number of vertices.

For a graph with `V` vertices and `E` edges, common traversal algorithms operate in approximately `O(V + E)` time when the graph is represented by adjacency lists.

## Searching

Searching demonstrates why data organization affects algorithmic complexity.

### Linear Search

Linear search examines elements sequentially until the target is found.

Its worst-case complexity is:

`O(n)`

It requires no ordering assumption.

### Binary Search

Binary search requires ordered data.

Each comparison eliminates roughly half of the remaining search range.

Its complexity is:

`O(log n)`

The Python, JavaScript, C++, and Java implementations all use an iterative binary-search mechanism, while the database models ordered access using relational indexes where appropriate.

The critical limitation is that binary search is not a general replacement for linear search. The data must satisfy the required ordering condition.

## Complexity Overview

Big-O notation describes how resource requirements grow as input size increases.

| Complexity | Typical interpretation | Example |
|---|---|---|
| `O(1)` | Constant work | Array index access |
| `O(log n)` | Repeatedly reduces the search space | Binary search |
| `O(n)` | Processes each element once | Linear search |
| `O(n log n)` | Divide-and-conquer sorting patterns | Efficient comparison sorting |
| `O(n²)` | Pairwise relationships | Simple nested comparison |
| `O(2ⁿ)` | Exponential growth | Some brute-force subset algorithms |

Big-O is not a timing measurement. A constant-time operation can still have a larger constant cost than another operation. Hardware, memory layout, cache behavior, allocation, input distribution, and implementation details affect actual execution time.

The Python implementation performs a simple linear-search versus binary-search timing experiment to show that practical timing and asymptotic analysis are related but different concepts.

## Python Implementation

The Python program presents the topic as an executable progression from simple ADTs to graph algorithms.

`Stack` demonstrates LIFO behavior using a list.

`Queue` uses `collections.deque`, which avoids the expensive front-removal behavior of repeatedly calling `pop(0)` on a list.

`SinglyLinkedList` explicitly models nodes and links. This exposes the structural cost that a built-in list normally hides.

`BinarySearchTree` maintains ordered nodes and provides membership testing and inorder traversal.

`Graph` uses a dictionary of adjacency lists. It provides breadth-first search and depth-first search.

The program then adds:

- Binary search
- Unweighted shortest-path discovery with BFS
- Dijkstra's algorithm for non-negative weighted graphs
- Complexity timing
- Validation of empty structures
- Validation of graph vertices
- Rejection of negative Dijkstra weights

Dijkstra's implementation explicitly rejects negative edges because the algorithm's correctness depends on non-negative edge weights.

## JavaScript Implementation

The JavaScript file takes a Node.js-oriented approach.

The queue implementation uses a head index rather than repeatedly removing the first array element. This avoids shifting the remaining elements on every dequeue.

The custom `MinHeap` demonstrates priority scheduling directly rather than relying entirely on a built-in abstraction.

The dependency graph uses:

- `Map` for adjacency relationships
- `Set` for duplicate-free neighbors
- A queue for breadth-first processing
- Indegree counts for topological ordering

The topological-order operation detects cycles by checking whether every vertex can be processed.

The asynchronous task processor uses `setImmediate` to model event-driven work without introducing an external package. The data structure remains responsible for ordering work while the event loop controls asynchronous execution.

This separates two concepts that are often confused: a data structure determines how work is organized, while asynchronous execution determines when callbacks or tasks receive processing time.

## C++ Implementation

The C++ program models a build system.

A `Stack<string>` represents operations that follow LIFO semantics.

A `Queue<string>` represents build requests that should be processed in arrival order.

`BinarySearchTree` uses `unique_ptr` for node ownership. This prevents manual memory management from becoming part of the tree's correctness requirements.

`BuildGraph` models build dependencies such as:

`compile → unit-test → package → security-scan → deploy`

Topological sorting converts these relationships into an executable order.

The implementation uses `unordered_map` for average constant-time key lookup and vectors for adjacency lists. It explicitly rejects missing graph nodes and dependency cycles.

The program also demonstrates `unordered_set` for duplicate elimination and `vector` for a large sequential workload.

## Java Implementation

The Java implementation uses an enterprise-oriented deployment model.

`DeploymentTask` is an immutable record containing:

- Task identifier
- Service name
- Priority
- State

The `TaskState` enum makes workflow states explicit rather than representing them with arbitrary strings.

`FifoWorkQueue` and `PriorityWorkQueue` implement the same `WorkQueue` interface with different access policies. This illustrates how an ADT can be represented by multiple concrete structures.

`DeploymentService` controls state transitions:

`PENDING → RUNNING → COMPLETED`

Invalid transitions raise exceptions.

`DependencyGraph` represents deployment dependencies and uses topological ordering to produce a valid execution sequence. Cycles produce a failure instead of an invalid deployment order.

The implementation also uses:

- Records for immutable domain data
- Interfaces for interchangeable queue policies
- Generics for reusable collection behavior
- Streams for filtered service queries
- `HashSet` for membership checks
- `TreeSet` for unique ordered values
- `PriorityQueue` for priority scheduling

## PostgreSQL Implementation

The SQL model treats data structures as operational concepts rather than attempting to reproduce in-memory pointer structures literally.

The schema contains:

- `data_structures`
- `work_items`
- `graph_vertices`
- `graph_edges`
- `benchmark_runs`

`structure_kind` distinguishes stack, queue, linked list, tree, graph, hash-index, and priority-queue concepts.

`task_state` provides database-enforced state values.

Check constraints enforce valid priority ranges and consistency between completion timestamps and completed state.

The graph uses a normalized vertex-edge model:

`graph_vertices → graph_edges → graph_vertices`

This is a natural relational representation of graph relationships.

A recursive CTE traverses dependency paths. This demonstrates that relational databases can perform recursive graph-like queries when relationships are stored as rows.

The pending-work view orders items according to priority and insertion time.

The state/priority index supports queries that frequently select pending work and order it by priority.

The transaction demonstrates atomic changes to work items. The invalid priority example demonstrates that integrity rules should not depend exclusively on application code.

## Relationships Between Structure Choices

The most important design decision is not memorizing the names of structures. It is matching operations to representation.

Consider a deployment system:

    Incoming requests
           |
           v
       FIFO Queue
           |
           v
      Dependency Graph
           |
           v
      Topological Order
           |
           v
       Priority Queue
           |
           v
     Completed Task Set

Each stage requires a different access policy.

The queue preserves arrival order.

The graph expresses relationships between tasks.

Topological ordering converts dependency relationships into a valid processing sequence.

The priority queue selects urgent work.

The set provides efficient membership testing for completed identifiers.

Using one structure for all stages would make some operations unnecessarily expensive or semantically incorrect.

## Edge Cases and Failure Conditions

Empty structures are explicitly rejected when an operation requires an element.

Duplicate tree values are ignored in the binary search tree implementations.

Unknown graph vertices are rejected rather than silently creating malformed relationships.

Graph cycles prevent topological ordering because no valid dependency-first sequence exists.

Dijkstra's algorithm rejects negative edge weights.

Binary search is only valid when the input is sorted according to the expected ordering.

Priority values are constrained to an allowed range in the SQL model and Java domain model.

Java deployment tasks reject invalid state transitions.

The SQL schema rejects invalid priorities and inconsistent completion timestamps at the database layer.

These checks illustrate a broader principle: data structure correctness depends not only on storage but also on preserving the invariants that define the structure.

## Performance and Memory Considerations

A complexity estimate should be considered together with memory behavior.

An array can provide excellent cache locality because elements occupy contiguous storage.

A linked list requires node references and can suffer from poor cache locality.

A hash table normally provides average `O(1)` lookup but requires extra memory and does not inherently preserve sorted order.

A balanced tree can provide `O(log n)` ordered operations, while an unbalanced binary search tree can degrade to `O(n)`.

An adjacency matrix requires `O(V²)` storage and is useful when dense connectivity and constant-time edge existence checks are important.

An adjacency list requires `O(V + E)` storage and is usually more appropriate for sparse graphs.

A heap provides efficient priority updates and removal of the highest- or lowest-priority element, but it is not a general replacement for a sorted sequence.

## Security and Reliability Considerations

Data structures themselves do not provide complete application security.

External input should be validated before becoming a key, identifier, priority, or graph relationship.

Unbounded queues can become memory-exhaustion risks when producers generate work faster than consumers can process it.

Recursive algorithms can encounter excessive call depth on large or pathological structures. Iterative traversal may be preferable when input size is not tightly controlled.

Hash-based structures should be considered carefully when attackers can influence large numbers of keys. Runtime and implementation behavior can vary with collision patterns.

Database constraints provide a second enforcement boundary. Application validation is useful for user feedback, while database constraints protect persistent integrity when multiple clients or services can modify the same data.

## Educational Distinctions

The four main ideas can be separated clearly:

**Abstract data type** describes behavior and allowed operations.

**Linear structure** organizes elements around a sequential relationship.

**Non-linear structure** represents branching or network relationships.

**Complexity analysis** evaluates how computational or memory requirements grow as the input changes.

These concepts are related but are not interchangeable. A stack is an ADT whose common implementation is linear. A tree is a non-linear data structure. A binary search algorithm is an algorithm whose efficiency depends on an ordered representation. Big-O notation describes the growth of the algorithm's cost rather than defining the data structure itself.

The implementations therefore use different structures for different access requirements instead of treating data structures as interchangeable containers.
