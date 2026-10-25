# Linked Lists: Singly, Doubly, and Circular Structures

## Scope

This project implements three linked-list variants as distinct data structures:

| Structure | Node links | Terminal condition | Main strength |
|---|---|---|---|
| Singly linked list | `next` | Final node points to `null` | Low pointer overhead and simple forward traversal |
| Doubly linked list | `previous`, `next` | Ends contain `null` links | Bidirectional traversal and local deletion |
| Circular linked list | `next` | Final node points back to the head | Repeated traversal without a terminal node |

The implementations model the same fundamental idea, a sequence of nodes connected through references, while preserving the different invariants that make each structure useful.

The five source files provide complementary perspectives:

- Python models the structures directly and emphasizes validation, generic behavior, and executable integrity checks.
- JavaScript uses object references and runtime validation to model pointer operations.
- C++17 uses ownership-oriented memory management and explicit resource lifetime.
- Java 17 models the structures as typed domain objects and service operations.
- PostgreSQL represents node relationships relationally and validates structural rules with constraints, functions, recursive queries, and transactions.

## Core Model

A linked list separates the logical sequence from the physical storage arrangement.

A conceptual singly linked list looks like:

    [10 | next] -> [20 | next] -> [30 | null]

A doubly linked list adds backward references:

    null <- [10] <-> [20] <-> [30] -> null

A circular linked list removes the terminal `null` relationship:

    [10] -> [20] -> [30]
      ^                 |
      |_________________|

The value stored by a node is independent from the reference that connects it to another node.

This distinction is important when inserting or deleting elements. The operation normally changes a small number of links rather than moving all subsequent values.

## Singly Linked Lists

A singly linked list stores one outgoing link per node.

Each node contains:

- a value
- a reference to the next node

The list normally maintains a `head` reference and may maintain a `tail` reference.

The Python implementation uses `SinglyNode` and `SinglyLinkedList`. It supports:

- append
- prepend
- indexed lookup
- indexed insertion
- indexed removal
- search
- reversal
- iteration

The JavaScript implementation provides the same structural behavior while using JavaScript objects as nodes.

The C++ implementation uses `std::unique_ptr` for node ownership. This makes node lifetime explicit and avoids manually deleting nodes during normal singly-list mutation.

The Java implementation uses generic `SinglyNode<T>` objects and exposes the structure through the `LinkedSequence<T>` interface.

### Pointer behavior

Appending to a list with a maintained tail pointer can be constant time:

    tail.next = new_node
    tail = new_node

Prepending is also constant time:

    new_node.next = head
    head = new_node

Indexed lookup remains linear because the list has no direct address calculation for an arbitrary position.

For index `k`, traversal follows approximately `k` links.

## Doubly Linked Lists

A doubly linked list stores two references in each node:

- `previous`
- `next`

The local relationship is:

    previous <-> current <-> next

The Python and Java implementations exploit this structure when locating a node. They select the closer end of the list, reducing traversal distance for indexed access.

The C++ implementation explicitly updates both directions during deletion:

    previous.next = current.next
    next.previous = current.previous

The JavaScript implementation performs equivalent object-reference updates.

The database representation stores the two relationships as `prev_node_id` and `next_node_id`.

### Why the second pointer matters

The additional pointer increases memory usage, but it provides an important operational benefit: traversal can proceed in either direction.

For a known node, removal can be performed locally without searching for its predecessor.

A doubly linked structure is useful for domains such as:

- browser history
- bidirectional navigation
- deque-like workflows
- undo and redo chains
- local sequence editing

The second pointer also introduces an integrity requirement. If node A points forward to node B, node B should point backward to node A.

The PostgreSQL validation function explicitly checks this reciprocal relationship.

## Circular Linked Lists

A circular linked list has no terminal `next = null` link.

Instead, the final node points to the first node:

    tail.next = head

The Python, JavaScript, and Java implementations maintain both `head` and `tail`.

The circular invariant is:

    tail.next == head

For a non-empty circular list, traversing exactly `size` nodes returns to the starting node.

This makes circular lists useful for repeated cycles such as:

- round-robin scheduling
- cyclic buffers
- repeated turn allocation
- rotating task ownership

The `rotate` operation demonstrates the natural relationship between the structure and cyclic traversal. Moving the head and tail together changes the logical starting point without rebuilding the nodes.

## Comparison of Operations

| Operation | Singly | Doubly | Circular |
|---|---:|---:|---:|
| Access by index | O(n) | O(n), optimized from nearest end | O(n) |
| Insert at head | O(1) | O(1) | O(1) |
| Insert at tail with tail pointer | O(1) | O(1) | O(1) |
| Remove head | O(1) | O(1) | O(1) |
| Remove known node | Requires predecessor | O(1) | Requires predecessor in this implementation |
| Forward traversal | O(n) | O(n) | O(n) |
| Backward traversal | Not supported directly | O(n) | Not supported directly |
| Extra pointer overhead | Low | Higher | Low |
| Terminal node | `next = null` | `next = null` | `next = head` |

The asymptotic access complexity remains linear for all three structures because nodes are not stored at predictable contiguous indexes.

## Python Implementation

The Python source uses dataclasses for node definitions:

- `SinglyNode`
- `DoublyNode`

The list classes maintain explicit size counters, which prevents repeated traversal merely to determine the number of elements.

Custom exceptions distinguish invalid linked-list operations from ordinary runtime failures.

The Python implementation also includes Floyd's cycle-detection algorithm:

    slow moves one node at a time
    fast moves two nodes at a time

If the two references meet, a cycle exists.

This algorithm uses O(1) additional space.

The `merge_sorted` function demonstrates a linked-list operation that exploits already sorted input. It performs a linear merge instead of sorting the combined values.

Integrity validation checks:

- empty-list head and tail state
- singly-list terminal links
- doubly-list boundary pointers
- circular tail-to-head relationship
- recorded size against traversal behavior

## JavaScript Implementation

The JavaScript source uses classes for nodes and lists.

`SinglyNode` and `DoublyNode` expose explicit reference fields. The circular structure reuses the singly-node shape because its nodes require only one outgoing reference.

JavaScript-specific behavior includes:

- runtime index validation
- `Object.is` for value comparison
- array conversion for observable traversal results
- normalized rotation using modulo arithmetic
- exception-based failure reporting

The implementation is executable directly in a Node.js environment without third-party packages.

The circular implementation deliberately bounds traversal by the stored size. Without such a boundary, an ordinary traversal loop could continue indefinitely because there is no `null` terminator.

## C++17 Implementation

The C++ implementation emphasizes ownership and resource lifetime.

The singly linked list uses `std::unique_ptr<Node>` for ownership. This gives a clear ownership chain:

    list -> head -> next -> next -> ...

When a node is removed, ownership of the remaining suffix is transferred through `std::unique_ptr`.

The doubly linked list uses raw non-owning pointers for neighboring nodes while the list itself owns the allocated nodes and releases them in `clear()` and the destructor.

This distinction is deliberate:

- ownership determines who destroys a node
- neighbor pointers describe structural relationships

The circular implementation requires special cleanup because a cycle cannot be destroyed by recursively following `next` until `null`. Its `clear()` function explicitly walks exactly the stored number of nodes before releasing the head.

Bounds violations use `std::out_of_range`.

## Java 17 Implementation

The Java implementation models the lists through the generic `LinkedSequence<T>` interface.

This provides a common operational contract:

- `addFirst`
- `addLast`
- `get`
- `remove`
- `size`
- `toList`

The concrete classes retain different structural invariants.

Java-specific design features include:

- generic node types
- interfaces
- records
- immutable `List.copyOf` results
- `Objects.requireNonNull`
- custom runtime exceptions
- `Comparator<T>`
- switch expressions

`LinkedListService` contains operations that can work against the interface rather than a particular concrete list.

The `ListReport` record separates structural inspection from mutable list state.

The doubly linked implementation selects the closest endpoint when locating a node. This reduces expected traversal distance compared with always beginning at the head.

## PostgreSQL Representation

The PostgreSQL implementation represents each node as a row.

The central tables are:

| Table | Purpose |
|---|---|
| `linked_list` | Defines the logical list and its type |
| `list_node` | Stores node values and relationships |
| `list_operation` | Records operations and their outcomes |

A node's links are represented using foreign keys:

- `next_node_id`
- `prev_node_id`

The list type is represented with a PostgreSQL enum:

    singly
    doubly
    circular

The relational model makes the difference between logical ordering and physical references explicit.

## Database Integrity

Several constraints protect the relational representation.

`PRIMARY KEY` constraints uniquely identify lists and nodes.

`FOREIGN KEY` constraints prevent references to nonexistent nodes.

`UNIQUE (list_id, node_position)` prevents duplicate logical positions within one list.

`CHECK` constraints prevent negative positions and invalid operation states.

The `validate_list_structure` function performs rules that cannot be expressed cleanly through simple row-level constraints.

For singly linked lists it verifies that predecessor references are absent.

For doubly linked lists it verifies reciprocal next and previous relationships.

For circular lists it verifies that the final logical node points back to the first node.

This separation is important because relational constraints enforce local validity while linked-list validation can require reasoning about multiple related rows.

## Transactional Mutation

The PostgreSQL script includes a transaction for appending a node to the singly linked structure.

The transaction:

1. Determines the next logical position.
2. Inserts the new node.
3. Updates the previous tail's `next_node_id`.
4. Commits the complete state.

If a mutation fails before `COMMIT`, PostgreSQL can roll the transaction back rather than leaving a partially updated relationship.

This is especially important for linked structures because inserting a node often requires changing more than one relationship.

## Recursive Traversal

The PostgreSQL script uses a recursive common table expression to traverse the circular list.

The recursive query follows:

    current node
        |
        v
    next_node_id
        |
        v
    next node

The recursion is bounded by the number of nodes. This prevents an intentionally or accidentally cyclic structure from causing an unbounded database traversal.

The result exposes the logical sequence and the successor relationship.

## Failure Handling

The implementations explicitly handle invalid operations.

Examples include:

- negative indexes
- indexes beyond the current size
- removal from an empty structure
- invalid circular traversal assumptions
- inconsistent doubly linked relationships
- orphaned database references

The failure strategy differs by language.

| Implementation | Failure mechanism |
|---|---|
| Python | Custom exceptions and assertions |
| JavaScript | Custom `Error` subclass |
| C++17 | `std::out_of_range` and assertions |
| Java 17 | Custom runtime exception and null validation |
| PostgreSQL | Constraints, validation functions, transaction boundaries |

## Security and Reliability Considerations

Linked lists are data structures rather than security controls, but implementations still require defensive design.

Important concerns include:

- validating indexes before dereferencing nodes
- preventing null-reference assumptions
- preventing accidental infinite traversal of circular structures
- maintaining reciprocal links in doubly linked structures
- preserving ownership during C++ mutations
- avoiding partial relational updates through transactions
- limiting recursive database traversal
- avoiding unchecked external input as an index

The C++ implementation uses ownership-aware memory management for singly linked nodes. The database uses foreign keys to reduce the risk of dangling references.

## Memory and Performance Trade-offs

Linked lists are not universally superior to arrays or dynamic arrays.

A linked list is useful when structural changes are frequent and node references are meaningful.

An array-like structure is generally better when:

- random indexed access dominates
- cache locality matters
- compact memory representation matters
- predictable iteration performance is important

Linked lists require pointer or reference storage for each node. Those references add memory overhead and can reduce cache locality.

Doubly linked lists require two relationship fields instead of one, increasing memory consumption and mutation complexity.

Circular lists eliminate the terminal null relationship but require special traversal termination logic.

## Engineering Distinctions

The three structures should not be treated as interchangeable implementations of the same abstraction.

A singly linked list optimizes for simple forward relationships.

A doubly linked list adds reverse navigation and simplifies local removal when the target node is known.

A circular linked list changes the termination model entirely. The absence of a terminal null pointer makes repeated traversal natural but requires explicit stopping conditions.

The correct structure depends on the access pattern and invariants required by the application.

## Implemented Workflow

The complete workflow represented by the source files is:

    Create structure
          |
          v
    Add nodes
          |
          v
    Maintain links
          |
          v
    Traverse / search
          |
          v
    Insert or remove
          |
          v
    Validate invariants
          |
          v
    Reverse / rotate where supported
          |
          v
    Report or persist structure

Each implementation keeps the core node relationships explicit so that mutation behavior can be inspected rather than hidden behind an unrelated collection abstraction.

## Practical Design Rules

Use a singly linked list when forward traversal and low structural overhead are the primary requirements.

Use a doubly linked list when both traversal directions or efficient local removal are important.

Use a circular linked list when the logical workflow naturally repeats from the last element to the first.

Regardless of the variant, maintain a clear invariant for `head`, `tail`, node count, and link relationships. Most linked-list defects arise from updating one side of a relationship while forgetting another or from using a traversal condition that does not match the structure's termination model.
