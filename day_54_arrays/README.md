# Arrays: Array Operations, Indexing, Traversal, Insertion, and Deletion

## Scope

An array is an ordered collection whose elements are associated with positions. The defining operational property is direct positional access: when an array uses contiguous indexing, the address of an element can be calculated from its base location and index.

This project treats arrays as an operational data structure rather than as a collection of syntax examples. The implementations cover:

- indexed access
- traversal
- updates
- linear search
- binary search on sorted data
- insertion
- deletion
- dynamic capacity growth
- validation
- failure handling
- operation tracking
- database-backed ordered storage

The central distinction is between operations that use the index directly and operations that must inspect or move multiple elements.

## Core Array Model

A conceptual array can be represented as:

    index:    0     1     2     3     4
             +-----+-----+-----+-----+-----+
    value:   | 10  | 20  | 30  | 40  | 50  |
             +-----+-----+-----+-----+-----+

The index identifies the position, while the stored value represents the element at that position.

For a zero-based array:

    first index = 0
    last index  = size - 1

The position is part of the data structure's organization. Inserting or deleting an element in the middle therefore affects the positions of later elements.

## Fundamental Operations

| Operation | Typical complexity | Reason |
|---|---:|---|
| Indexed access | O(1) | The position directly identifies the element |
| Update by index | O(1) | Only one known position changes |
| Traversal | O(n) | Every element is visited |
| Linear search | O(n) | Elements may need to be inspected sequentially |
| Binary search | O(log n) | The search space is repeatedly halved |
| Insert at end | Amortized O(1) | Dynamic storage can append without shifting existing elements |
| Insert at arbitrary position | O(n) | The suffix must move |
| Delete at end | O(1) | No suffix needs to move |
| Delete at arbitrary position | O(n) | Later elements must move left |

Binary search has a stronger prerequisite than linear search: the data must be ordered according to the search rule.

## Array Indexing

Indexed access is the defining strength of an array.

The Python implementation exposes `access(index)`, JavaScript uses `get(index)`, C++ uses `access(index)`, and Java uses `access(index)`. Each implementation validates the requested position before returning the element.

The validation is important because an invalid index should not silently become a valid operation.

The Python implementation raises `ArrayError`. JavaScript raises `ArrayOperationError`. C++ uses `ArrayError`, and Java uses `ArrayOperationException`.

The PostgreSQL implementation represents the index explicitly with the `position` column. The composite primary key `(array_id, position)` prevents two elements from occupying the same position within one logical array.

## Traversal

Traversal visits elements in index order.

The Python implementation exposes `traverse()` as an iterator, allowing callers to consume values without requiring a second collection.

The JavaScript implementation uses a callback so that traversal can participate naturally in an event-driven program.

C++ uses the underlying vector's contiguous iteration model through its data representation, while Java stores elements in an `ArrayList` and exposes immutable snapshots.

Traversal is O(n) because an operation that needs to inspect every element cannot generally avoid visiting every relevant position.

## Searching

Two different search strategies are implemented.

### Linear Search

Linear search checks positions sequentially:

    index 0 -> index 1 -> index 2 -> ... -> index n-1

It works on both sorted and unsorted data.

The implementations return the first matching position and `-1` when the value is absent.

The worst-case complexity is O(n).

### Binary Search

Binary search requires sorted data.

The search repeatedly selects the middle position:

    [10, 20, 30, 40, 50, 60, 70]
             ^
           middle

If the target is larger, the lower part can be discarded. If it is smaller, the upper part can be discarded.

The implementations explicitly reject unsorted data rather than silently returning an unreliable result.

The complexity is O(log n).

## Insertion

Insertion changes both the array contents and the positions of subsequent elements.

For example:

    Before:
    [10, 20, 30, 40]

    Insert 25 at index 2:

    [10, 20, 25, 30, 40]

The original `30` and `40` move one position to the right.

The Python implementation models this shift explicitly with a loop.

The JavaScript implementation uses `splice`, which provides the indexed insertion behavior.

The C++ implementation uses `std::vector::insert`.

The Java implementation uses `ArrayList.add(index, value)`.

The PostgreSQL function `insert_array_value` performs an equivalent suffix shift by updating positions before inserting the new row.

An arbitrary-position insertion is O(n) because the suffix can contain O(n) elements.

## Deletion

Deletion performs the opposite movement.

    Before:
    [10, 20, 30, 40]

    Delete index 1:

    [10, 30, 40]

The elements after the deleted position move left.

The Python implementation manually shifts the suffix and removes the final duplicate position.

JavaScript uses `splice`.

C++ uses `std::vector::erase`.

Java uses `ArrayList.remove`.

PostgreSQL deletes the requested row and decrements positions for the remaining suffix.

Arbitrary-position deletion is O(n).

## Dynamic Capacity

A dynamically managed array separates logical size from allocated capacity.

For example:

    capacity = 4
    size     = 4

Appending another element requires additional storage.

The Python and JavaScript models grow capacity by doubling it. The C++ vector reserves additional capacity when its logical storage reaches the current capacity. The Java model tracks logical capacity while relying on `ArrayList` for physical storage management.

Doubling reduces the frequency of resizing operations. Although an individual resize can be O(n), repeated appends have amortized O(1) insertion cost at the end.

The distinction is:

- `size` describes the number of logical elements.
- `capacity` describes available storage before another growth operation is required.

## Python Implementation

The Python program uses a `DynamicArray` dataclass and maintains its own list of values.

Important mechanisms include:

- `ArrayStats` for operation accounting
- `Operation` for explicit operation types
- index validation
- capacity growth
- manual suffix shifting
- linear search
- sorted-data validation for binary search
- traversal through a generator
- assertions for behavioral verification
- explicit failure demonstrations

The implementation uses only the standard library.

The manual insertion and deletion loops make the movement of array elements visible instead of hiding it behind a collection method.

## JavaScript Implementation

The JavaScript implementation models an observable array.

`ObservableArray` maintains the values and emits structured events for operations such as:

- access
- update
- insertion
- deletion
- search
- capacity expansion
- reversal

This provides an event-driven perspective that is useful when array operations are part of a larger application workflow.

JavaScript's `Map` or `Set` is not required for this domain because the central data structure is deliberately a contiguous indexed collection. Using an ordinary array keeps the operational distinction clear.

Validation prevents invalid positions and non-integer values.

## C++17 Implementation

The C++ implementation uses `std::vector<int>` as the underlying contiguous storage.

The `RepositoryArray` class adds a domain layer around the STL container and records operation statistics.

The implementation demonstrates:

- explicit capacity management
- STL insertion and deletion
- exception-based validation
- linear search
- binary search
- reverse traversal behavior
- operation statistics
- assertions
- failure handling

`std::vector` is an appropriate representation because it provides contiguous storage, constant-time indexed access, and amortized constant-time append.

The trade-off is that inserting or deleting near the beginning or middle requires element movement.

## Java 17 Implementation

The Java implementation uses `ArrayList<Integer>` for dynamic indexed storage.

The domain model separates searching from the array itself through the `SearchStrategy` interface.

Two concrete policies are provided:

- `LinearSearch`
- `BinarySearch`

This makes the search algorithm replaceable without changing the array-management class.

The `OperationStats` record is immutable. Each operation produces a new statistics value rather than mutating an existing statistics object.

The enterprise-oriented design also uses:

- a domain-specific exception
- an enum for operation types
- a record for immutable statistics
- a strategy interface
- explicit validation
- immutable snapshots with `List.copyOf`

## PostgreSQL Representation

A relational database does not provide an array's in-memory address calculation model through ordinary rows. The PostgreSQL implementation therefore models a logical array explicitly.

The model is:

    integer_arrays
          |
          +---- array_elements
                    |
                    +---- position
                    +---- value

An array has a capacity, while each element has a position and value.

The primary key:

    (array_id, position)

ensures that one logical array cannot contain two elements at the same position.

A foreign key connects each element to its parent array.

## Database Constraints

The database enforces several invariants:

- array names are unique
- capacities are positive
- element positions cannot be negative
- each array-position pair is unique
- element rows must reference an existing array
- positions cannot exceed configured capacity

The `validate_array_position` trigger performs a capacity check before an element is inserted or updated.

This is important because application code should not be the only layer responsible for maintaining structural invariants.

## Database Insertion and Deletion

The `insert_array_value` function locks the target array before checking capacity.

It then:

1. Determines the current logical size.
2. Validates the requested insertion position.
3. Shifts the suffix one position to the right.
4. Inserts the new value.

The deletion function:

1. Locks and retrieves the requested element.
2. Deletes that element.
3. Shifts the remaining suffix left.
4. Returns the removed value.

These operations reproduce indexed array semantics in relational form.

The relational representation is useful for persistence and querying, but it is less efficient than native contiguous memory for repeated arbitrary-position shifts.

## Transactional Integrity

The PostgreSQL examples use explicit transactions around structural changes.

For example:

    BEGIN
    insert
    COMMIT

If a structural operation fails, the transaction can be rolled back so that a partial position shift does not remain in the database.

The final transaction intentionally demonstrates an invalid insertion and rolls the operation back.

This is a database-level difference from ordinary in-memory arrays: transaction boundaries can make a sequence of structural modifications atomic.

## Operation Logging

`array_operation_log` records operations such as:

- access
- search
- insert
- update
- delete

Triggers automatically record row-level modifications.

This creates an audit trail that can be used to examine operational behavior.

The reporting view groups activity by array and operation type.

The log is not part of the mathematical definition of an array. It is a governance and observability mechanism added around the data structure.

## Edge Cases

The implementations explicitly address several boundary conditions.

| Case | Expected behavior |
|---|---|
| Accessing an invalid index | Reject the operation |
| Negative index in the modeled API | Reject the operation |
| Insertion beyond the logical end | Reject the operation |
| Deleting a missing element | Reject the operation |
| Searching for an absent value | Return `-1` |
| Binary search on unsorted data | Reject the operation |
| Appending at capacity | Grow dynamic storage |
| Empty-array access | Reject the operation |
| Duplicate values | Permit them |
| Updating an existing position | Replace only that element |

Duplicate values are valid because an array's identity comes from position and order, not from value uniqueness.

## Failure Handling

Failure handling is deliberately explicit.

A robust array abstraction should distinguish between:

- invalid input
- invalid positions
- invalid algorithm preconditions
- capacity violations
- missing values
- internal operation failures

The implementations avoid silently correcting invalid indices. Silent correction can hide programming errors and make state corruption harder to diagnose.

## Security Considerations

Arrays themselves are not normally a security boundary, but array operations can participate in security-sensitive software.

Relevant controls include:

- validating externally supplied indices
- preventing integer overflow in index calculations
- limiting maximum capacity when input size is untrusted
- rejecting malformed values
- avoiding uncontrolled memory allocation
- preserving database transaction integrity
- using database constraints rather than relying only on application checks
- avoiding dynamic SQL for array values and positions
- recording important operations when auditability is required

For production systems, capacity limits should be chosen according to available memory and workload characteristics rather than allowing unrestricted growth.

## Performance Considerations

The most important performance distinction is between access and movement.

Direct access:

    array[index]

does not require inspecting earlier elements.

Insertion in the middle:

    [A B C D]
       insert X

requires movement:

    [A B X C D]

Deletion has the corresponding left-shift cost.

This makes arrays particularly effective when workloads contain many indexed reads and relatively few arbitrary-position modifications.

For workloads dominated by middle insertions or deletions, a different data structure may be more appropriate. The correct choice depends on the access pattern, memory behavior, ordering requirements, and workload size.

## Cross-Implementation Design

The five implementations use different mechanisms while preserving the same operational model.

| Implementation | Main representation | Distinct perspective |
|---|---|---|
| Python | `list` wrapped by `DynamicArray` | Explicit operations and validation |
| JavaScript | native array wrapped by `ObservableArray` | Event-driven operation tracking |
| C++17 | `std::vector<int>` | Contiguous storage and STL performance |
| Java 17 | `ArrayList<Integer>` | Domain modeling and search strategies |
| PostgreSQL | ordered relational rows | Persistent indexed state and transactions |

The implementations are deliberately not literal translations of one another.

## Relationship Between Operations

The operational flow can be represented as:

    Input
      |
      v
    Validate
      |
      +---- invalid ----> reject
      |
      v
    Select position
      |
      +---- access ------> return value
      |
      +---- update ------> replace value
      |
      +---- search ------> locate value
      |
      +---- insert ------> shift right -> store value
      |
      +---- delete ------> remove value -> shift left
      |
      v
    Updated array state

This model highlights why insertion and deletion are more expensive than indexed access.

## Practical Implications

Arrays are a strong choice when the application benefits from:

- predictable positional access
- compact ordered storage
- sequential traversal
- cache-friendly contiguous representation
- simple indexing
- frequent reads by known position

They become less attractive when the dominant workload requires frequent arbitrary-position insertion and deletion.

The same conceptual array operation also behaves differently depending on its implementation environment. An in-memory vector, a Java dynamic list, a JavaScript array, and a relational representation all preserve ordered elements but have different memory, persistence, transaction, and performance characteristics.

## Implemented Learning Model

The complete project connects the operations into one progression:

    Representation
         |
         v
    Indexing and Access
         |
         v
    Traversal
         |
         v
    Search
      /     \
     v       v
   Linear  Binary
             |
        sorted data
         required
         |
         v
    Insertion / Deletion
         |
         v
    Capacity and State
         |
         v
    Validation and Failure Handling
         |
         v
    Persistent Relational Model

The key technical lesson is that array behavior is determined not only by what operation is requested, but also by how the underlying storage represents order and position.
