# Heaps, Heap Operations, and Priority Queues

## Scope

This learning artifact treats heaps as array-backed tree structures that maintain a local ordering rule between each parent and its children.

The implementation distinguishes three related ideas:

- A **min heap** keeps the smallest element at the root.
- A **max heap** keeps the largest element at the root.
- A **priority queue** uses a priority ordering to determine which item should be processed next.

The five source files use the same conceptual foundation but apply it differently:

| File | Technical perspective | Main implementation |
|---|---|---|
| Python | Algorithmic simulation | Generic binary heap, stable priority queue, scheduler, heap sort, top-k |
| JavaScript | Event-driven processing | Binary heap, asynchronous scheduler, event emitter, top-k |
| C++17 | Systems-oriented implementation | Generic heap template, bounded top-k heap, scheduling engine |
| Java 17 | Enterprise domain model | Generic heap, `PriorityQueue`, records, policies, service layer |
| PostgreSQL | Relational workflow | Heap-operation records, priority jobs, queue extraction, reports, transactions |

## Core Heap Model

A binary heap is commonly represented using an array rather than explicit tree nodes.

For an element at index `i`:

- Parent index: `(i - 1) / 2`
- Left child index: `2i + 1`
- Right child index: `2i + 2`

The array representation is compact because a complete binary tree has no gaps between occupied levels.

A min heap satisfies:

`parent <= child`

A max heap satisfies:

`parent >= child`

The heap property does not require the complete array to be globally sorted. It only guarantees the ordering relationship required between parents and children.

Example min heap:

```text
          2
        /   \
       4     7
      / \   / \
     9   5 8   11
```

A valid heap may therefore contain values that are not sorted when read from left to right.

## Fundamental Heap Operations

### Insert

Insertion appends a new value at the end of the array.

The new value can violate the heap property with its parent. The implementation repeatedly exchanges the value with its parent until the ordering rule is restored.

This is called **sift-up** or **bubble-up**.

Complexity:

| Operation | Complexity |
|---|---|
| Insert | `O(log n)` |
| Peek root | `O(1)` |
| Extract root | `O(log n)` |
| Build heap | `O(n)` |
| Space | `O(n)` |

The logarithmic insertion and extraction bounds follow from the height of a complete binary tree.

### Extract Root

The root is the highest-priority element for the selected heap type.

Extraction removes the root, moves the last array element into the root position, and restores the heap property through **sift-down**.

For a min heap, the smaller child is selected during sift-down.

For a max heap, the larger child is selected.

### Heapify

Bottom-up heap construction starts from the last internal node and performs sift-down toward the root.

This method constructs a heap in `O(n)` time.

Repeatedly inserting all elements into an initially empty heap instead requires `O(n log n)` worst-case time.

This distinction is implemented directly in the Python, C++, and Java examples.

### Replace Root

Root replacement is useful when maintaining a bounded collection.

The old root is returned, the replacement becomes the new root, and one sift-down operation restores the heap.

This avoids removing and then inserting as two separate operations.

## Min Heaps

A min heap is appropriate when the smallest key must be retrieved efficiently.

Typical uses include:

- earliest deadline processing
- shortest-duration selection
- minimum-cost algorithms
- event simulation
- top-k algorithms using a bounded heap
- task scheduling with lower numeric priorities processed first

The Python implementation creates a reusable `BinaryHeap` class whose comparison behavior is controlled by `HeapType`.

The C++ implementation expresses the same concept through a generic comparator. This makes the ordering policy a compile-time type parameter rather than a runtime enum.

The Java implementation uses `Comparator.naturalOrder()` for its custom min heap and Java's standard `PriorityQueue` for the enterprise scheduling example.

## Max Heaps

A max heap places the largest value at the root.

Typical uses include:

- highest-score selection
- maximum-capacity selection
- largest-value retrieval
- ranking systems
- resource selection
- maintaining the largest values in a stream

The Python and C++ programs explicitly demonstrate max-heap extraction.

Java's standard `PriorityQueue` is naturally a min-priority queue, so the example uses `Comparator.reverseOrder()` when maximum-first behavior is required.

JavaScript uses a comparator-driven heap, allowing the same binary-heap structure to represent either ordering.

## Priority Queues

A priority queue is an abstract data structure in which removal is determined by priority rather than insertion order.

A heap is one of the most common implementations of a priority queue because it provides efficient insertion and root extraction.

The distinction is important:

- A heap is a concrete data structure.
- A priority queue is an abstract behavior.
- A priority queue can be implemented with a heap.
- A heap can also be used for operations that are not exposed as a general-purpose priority queue.

The Python scheduler uses a stable priority queue. Equal priorities preserve submission order by storing a monotonically increasing sequence number.

The JavaScript scheduler uses the same principle while adding asynchronous execution and events.

The C++ scheduler stores jobs in a generic heap with a comparator that first evaluates priority and then sequence number.

The Java enterprise service uses `PriorityQueue<Job>` with a comparator over priority and sequence.

## Stable Priority Ordering

Two jobs may have the same priority.

If deterministic FIFO behavior is required for equal priorities, priority alone is insufficient.

The implementations therefore use a secondary sequence key:

`(priority, sequence)`

Lower priority is processed first. If priorities are equal, the smaller sequence number wins.

Example:

| Job | Priority | Sequence |
|---|---|---|
| Cache refresh | 2 | 0 |
| Database backup | 2 | 1 |
| Report generation | 3 | 2 |

The cache refresh is processed before the database backup even though both have priority `2`.

This prevents arbitrary ordering among equal-priority records.

## Python Implementation

The Python file defines a generic `BinaryHeap` with explicit min and max semantics.

Important mechanisms include:

- `dataclass` for domain objects
- `Enum` for heap type
- generic type variables
- list-based heap storage
- sift-up and sift-down
- bottom-up heap construction
- root replacement
- validation of heap invariants
- stable priority scheduling
- bounded top-k extraction
- heap sort
- edge-case validation
- performance measurement

The `StablePriorityQueue` uses Python's `heapq` module with `(priority, sequence, value)` tuples.

The `JobScheduler` turns the data structure into a concrete workload where security-related work receives a higher scheduling priority than ordinary reporting work.

The script also measures bottom-up heap construction and repeated extraction on 20,000 generated values.

## JavaScript Implementation

The JavaScript file uses a comparator-driven `BinaryHeap`.

The comparator determines whether the heap behaves as a min heap or max heap without duplicating the data structure.

The JavaScript implementation focuses on asynchronous and event-driven processing.

`PriorityScheduler` extends `EventEmitter` and emits:

- `submitted`
- `started`
- `completed`

The scheduler uses `Promise` and `setTimeout` to represent asynchronous task execution.

A sequence number provides deterministic ordering for equal priorities.

The `topK` function uses a bounded min heap. Once the heap reaches size `k`, a new value replaces the root only when it is larger than the current smallest member of the top-k set.

This produces `O(n log k)` behavior instead of sorting the entire input with `O(n log n)` work.

## C++17 Implementation

The C++ implementation uses a template-based `BinaryHeap`.

The heap is parameterized by a comparator, which separates storage and heap mechanics from ordering policy.

`std::less<int>` produces min-heap behavior.

`std::greater<int>` produces max-heap behavior.

The implementation also demonstrates move operations and `std::vector` storage to keep the structure efficient without external libraries.

`GovernanceScheduler` applies a job-specific comparator:

1. lower numeric priority first
2. lower sequence number for ties

The C++ `topK` implementation uses a bounded min heap. The root represents the smallest member of the current candidate set, so it can be replaced when a larger input value arrives.

The performance example measures bottom-up heap construction using `std::chrono`.

## Java 17 Implementation

The Java implementation separates data structure behavior from enterprise scheduling behavior.

The custom `BinaryHeap<T>` uses a supplied `Comparator<? super T>`.

The enterprise domain uses the immutable `Job` record:

`Job(String name, int priority, int duration, long sequence)`

Validation occurs when the record is constructed, preventing invalid jobs from entering the scheduling system.

`SchedulingPolicy` defines an explicit policy boundary.

`ProductionSchedulingPolicy` rejects jobs whose duration exceeds the configured maximum.

`SchedulerService` owns the scheduling queue and applies the policy before accepting work.

This structure demonstrates an important enterprise distinction:

- the heap determines ordering
- the queue manages pending work
- the policy determines eligibility
- the service coordinates domain behavior

The Java example also uses the standard `PriorityQueue`, streams-related collection operations, immutable `List` creation, records, interfaces, and custom validation.

## PostgreSQL Model

The PostgreSQL implementation represents heap-related operations and priority scheduling as relational data.

The main relationships are:

```text
Repository
   |
   +-- Branches
   |
   +-- Priority Jobs
   |
   +-- Heap Profiles
          |
          +-- Heap Operations
          |
          +-- Heap Metrics
```

`repositories` identifies logical systems.

`branches` records branch state and protection status as a supporting repository-domain model.

`heap_profiles` distinguishes min and max heap configurations.

`heap_operations` records operations such as `INSERT`, `PEEK`, `EXTRACT`, `HEAPIFY`, and `REPLACE_ROOT`.

`priority_jobs` models queueable work with a numeric priority and explicit state.

## Database Constraints

The database uses constraints to prevent invalid state.

Examples include:

- unique repository names
- unique branch names within a repository
- non-negative priorities
- positive job durations
- valid job states
- valid heap types
- valid heap operation names

Foreign keys preserve relationships between repositories, branches, jobs, heap profiles, and operations.

Indexes are applied to queue-oriented access patterns rather than every column.

The queue index supports retrieval by repository, state, priority, and submission time.

The heap-operation index supports ordered retrieval within a heap profile.

## PostgreSQL Queue Extraction

`extract_min_job` demonstrates database-level priority selection.

The query selects a queued job ordered by:

1. priority
2. submission time
3. job identifier

`FOR UPDATE SKIP LOCKED` allows concurrent workers to avoid selecting the same locked job.

The selected row transitions to `RUNNING` as part of the update.

This is a database implementation of priority-queue semantics rather than an in-memory binary heap.

The database therefore provides a useful distinction between two concepts:

- an in-memory heap provides efficient structural priority operations
- a relational queue provides durable, transactional priority selection

## Heap Operations and Persistence

The database records operations rather than attempting to reproduce an in-memory array representation.

For example:

| Sequence | Operation | Value |
|---|---|---|
| 1 | `INSERT` | 42 |
| 2 | `INSERT` | 17 |
| 3 | `INSERT` | 8 |
| 4 | `HEAPIFY` | 8 |
| 5 | `PEEK` | 8 |
| 6 | `EXTRACT` | 8 |

This preserves an operational history suitable for reporting and analysis.

The database does not claim that relational rows themselves form a binary heap. The heap structure remains an algorithmic concept, while the database records its operations and provides an independent persistent priority-queue workflow.

## Top-K Selection

Top-k selection is an important practical heap application.

Given `n` values and a requested `k`, maintaining a heap of only `k` elements reduces memory usage.

For largest-value selection:

1. create a min heap of size `k`
2. insert the first `k` values
3. inspect each remaining value
4. compare it with the heap root
5. replace the root when the new value is larger
6. extract the final candidates

Complexity is approximately:

`O(n log k)`

Space complexity is:

`O(k)`

This is useful when `k` is much smaller than `n`.

## Heap Sort

Heap sort repeatedly extracts the root from a heap.

A min heap produces ascending output.

A max heap produces descending output.

The Python example exposes this directly through `heapify_sort`.

Heap sort has `O(n log n)` time complexity and does not require the auxiliary structures associated with comparison-based sorting approaches that create separate output containers.

The practical trade-off is that library sorting functions are often preferred for general-purpose application code because they can have better constant factors and optimized implementations.

## Failure Conditions

The implementations explicitly reject invalid states rather than silently accepting them.

Examples include:

- extracting from an empty heap
- peeking into an empty heap
- invalid top-k sizes
- null or missing values where prohibited
- negative priorities
- non-positive durations
- invalid job names
- policy-rejected jobs

These checks make failure behavior deterministic.

## Edge Cases

Important edge cases include:

- empty heap
- one-element heap
- duplicate values
- equal priorities
- `k = 1`
- `k = n`
- invalid `k`
- replacing the root
- heapifying an already sorted sequence
- heapifying reverse-sorted data
- large input collections
- jobs with identical priorities
- policy rejection before queue insertion

Duplicate values are valid heap members. A heap does not require unique keys.

Equal priorities require a secondary ordering rule when deterministic execution is important.

## Performance Considerations

The primary complexity characteristics are:

| Operation | Binary Heap |
|---|---|
| Access root | `O(1)` |
| Insert | `O(log n)` |
| Extract root | `O(log n)` |
| Replace root | `O(log n)` |
| Build by bottom-up heapify | `O(n)` |
| Search arbitrary value | `O(n)` |
| Top-k using bounded heap | `O(n log k)` |

A heap is not an ordered search tree.

Finding an arbitrary value generally requires scanning the underlying array because the heap property provides only parent-child ordering.

The best data structure therefore depends on the operation mix.

## Data-Structure Trade-Offs

A heap is well suited when the dominant requirement is repeated access to the minimum or maximum element.

It is less suitable when the application frequently needs:

- arbitrary-value lookup
- ordered iteration of all elements
- predecessor and successor queries
- direct lookup by key

For those requirements, other structures such as balanced search trees, hash tables, or sorted arrays may be more appropriate depending on the workload.

## Security and Reliability Considerations

Heap operations themselves do not provide application security.

Production systems still need controls around the data and workload using the heap.

Relevant controls include:

- validate externally supplied priorities
- reject invalid durations
- prevent unbounded queue growth
- use deterministic tie-breaking where auditability matters
- avoid trusting user-controlled scheduling metadata
- isolate queue workers from unsafe task execution
- use database transactions for durable queue state
- use row locking when multiple workers compete for jobs
- monitor queue depth and execution latency
- retain sufficient operational history for diagnosis

The PostgreSQL queue extraction uses row-level locking semantics so concurrent workers can coordinate safely.

## Relationship Between the Implementations

The implementations deliberately emphasize different engineering perspectives.

```text
                    HEAP
                     |
          +----------+----------+
          |                     |
       MIN HEAP             MAX HEAP
          |                     |
          +----------+----------+
                     |
              PRIORITY QUEUE
                     |
          +----------+----------+
          |          |          |
       Python   JavaScript   C++ / Java
          |          |          |
      scheduling   events    enterprise
                     |
                PostgreSQL
                     |
              durable queue
```

The common abstraction is priority ordering.

The implementation mechanism changes according to the environment.

Python emphasizes algorithmic clarity and reusable classes.

JavaScript emphasizes asynchronous and event-driven processing.

C++ emphasizes generic, low-level data-structure construction and performance.

Java emphasizes domain modeling, policies, immutable records, and service boundaries.

PostgreSQL emphasizes durable state, constraints, transactions, locking, and reporting.

## Practical Interpretation

A heap should be selected because its workload requires efficient minimum or maximum extraction.

A priority queue should be selected when the application needs to process items according to priority.

A min heap is appropriate when lower keys represent higher processing priority.

A max heap is appropriate when higher keys represent higher processing priority.

A bounded heap is useful when only the best `k` candidates matter and the complete sorted input is unnecessary.

A database-backed priority queue is appropriate when queued state must survive process failure and be coordinated between workers.

These are related uses of the same ordering principle, but they solve different operational problems.
