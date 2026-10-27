# Queue Data Structures

## Scope

This project implements four related but distinct queue structures:

| Structure | Ordering rule | Primary operations | Typical use |
|---|---|---|---|
| Queue | First In, First Out | Enqueue, dequeue, peek | Request processing |
| Circular Queue | FIFO over fixed storage | Enqueue, dequeue, peek | Bounded buffers and ring buffers |
| Deque | Both ends are active | Push/pop front and back | Work stealing and bidirectional processing |
| Priority Queue | Highest service priority first | Insert, extract, peek | Scheduling and urgent work |

The implementations use a common repository-development style domain in which requests, builds, scans, tests, and operational jobs enter processing pipelines. The data structures themselves remain general-purpose.

The central distinction is ordering policy:

`Queue → arrival order`

`Circular Queue → arrival order + bounded capacity`

`Deque → caller chooses either end`

`Priority Queue → priority order, with deterministic tie-breaking`

## Domain Model

The implementations progress from basic storage behavior to a small job-processing workflow.

    Job Submission
          |
          v
    +-------------+
    | Intake      |
    | Queue       |
    +-------------+
          |
          v
    +-------------------+
    | Ordering Policy   |
    | FIFO / Priority   |
    +-------------------+
          |
          v
    +-------------------+
    | Dispatch          |
    +-------------------+
          |
          +------> Running
          |
          +------> Completed
          |
          +------> Failed

A queue controls ordering. It does not inherently represent the full lifecycle of a job. State management is therefore kept separate from the data structure where appropriate.

## Queue

A standard queue follows First In, First Out ordering.

For elements `A`, `B`, and `C`:

`enqueue(A) → enqueue(B) → enqueue(C)`

The first removal returns `A`.

The Python implementation uses `collections.deque`, providing constant-time operations at both ends. The Java implementation uses `ArrayDeque`. The C++ implementation uses `std::queue`, while the PostgreSQL model represents ordering explicitly through `sequence_no`.

The main invariant is:

`dequeue()` returns the oldest element that has not already been removed.

Empty removal is treated as an explicit failure rather than returning an ambiguous value.

## Circular Queue

A circular queue uses a fixed-size array and two logical positions:

             tail
              |
              v
       +---+---+---+---+
       | A | B | C | D |
       +---+---+---+---+
           ^
          head

Logical order:

`head → B → C → D → tail`

The physical storage wraps around when the end of the array is reached.

The core index operation is:

`next = (index + 1) % capacity`

The implementations track:

- head position
- tail position
- current size
- fixed capacity

Using `size` distinguishes empty and full states without reserving a special array slot.

A circular queue rejects insertion when capacity has been reached. This makes capacity a correctness condition rather than merely a performance preference.

The PostgreSQL implementation enforces circular capacity through a trigger that locks the queue row before counting active entries. This illustrates the difference between an in-memory bounded data structure and a persistent relational representation.

## Deque

A deque, or double-ended queue, permits insertion and removal at both ends.

    front                           back
      |                               |
      v                               v
    +-----+-----+-----+-----+
    |  A  |  B  |  C  |  D  |
    +-----+-----+-----+-----+
      ^                       ^
    pop/push                pop/push

The operations are:

- `push_front`
- `push_back`
- `pop_front`
- `pop_back`
- `peek_front`
- `peek_back`

A deque can model FIFO behavior by using only one end for insertion and the opposite end for removal. It can also support more specialized workflows where urgent work is inserted at the front while ordinary work remains at the back.

The JavaScript implementation uses a `Map` with logical numeric positions. This avoids repeated array shifting when the front changes. Python and Java rely on their standard deque implementations, while the C++ implementation uses `std::deque`.

## Priority Queue

A priority queue does not preserve ordinary arrival order.

For example:

| Job | Priority |
|---|---:|
| Documentation | 30 |
| Release | 10 |
| Security scan | 5 |

If lower numbers represent greater urgency, the processing order becomes:

`Security scan → Release → Documentation`

The Python implementation uses `heapq`.

The JavaScript implementation contains an explicit binary heap so that heap behavior is visible in the implementation rather than hidden behind a third-party package.

The C++ implementation uses `std::priority_queue` with a custom comparator.

The Java implementation uses `PriorityQueue` with a domain-specific comparator.

Equal priorities require deterministic behavior. The Python and JavaScript implementations retain insertion sequence information where needed. The C++ and Java examples use job identifiers as a deterministic secondary ordering key.

## Python Implementation

The Python file provides four independent structures and a small scheduler.

### FIFO queue

`collections.deque` provides efficient front removal without the O(n) shifting associated with removing the first element of a normal list.

### Circular queue

The `CircularQueue` class explicitly manages:

- capacity
- head
- tail
- size
- full-state detection
- empty-state detection

Its `snapshot()` method exposes logical ordering without exposing physical storage layout.

### Deque

`DequeModel` exposes both ends while preserving constant-time operations through `collections.deque`.

### Priority queue

`PriorityQueue` uses a heap of immutable `PriorityItem` records. The sequence number makes equal-priority jobs stable.

### Scheduler

The scheduler separates intake from priority dispatch:

`CircularQueue[Job] → PriorityQueue → dispatch`

This demonstrates that different queue structures can be composed instead of forcing one structure to solve every ordering requirement.

The script also performs executable assertions for FIFO ordering, circular wraparound, deque behavior, priority ordering, and invalid operations.

## JavaScript Implementation

The JavaScript file uses Node.js standard-library facilities and introduces an event-driven processing model.

The `Queue` class uses an array with a moving head index. Periodic compaction prevents removed elements from causing the backing array to grow indefinitely.

The `CircularQueue` maintains the same logical state variables as the other implementations but uses JavaScript arrays.

The `Deque` uses `Map` and logical integer positions. This avoids repeated `Array.prototype.unshift()` operations, which would require shifting many elements.

The `PriorityQueue` contains an explicit binary heap with:

- `bubbleUp`
- `bubbleDown`
- stable sequence numbers
- priority comparison

The `JobProcessor` extends `EventEmitter` and adds asynchronous execution. It limits concurrent work and emits:

- `submitted`
- `started`
- `completed`
- `failed`

A failed asynchronous task is recorded without terminating processing of unrelated jobs.

## C++17 Implementation

The C++ program presents queues through STL containers and templates.

`FIFOQueue<T>` wraps `std::queue`.

`CircularQueue<T>` uses `std::vector<std::optional<T>>`. `std::optional` allows an unused storage slot to be represented without inventing a sentinel value that could conflict with legitimate data.

`DequeModel<T>` uses `std::deque`.

The priority scheduler uses `std::priority_queue` with a custom comparator. Because the standard container is normally a max-heap, the comparator reverses the ordering so that smaller numeric priorities are dispatched first.

The `GovernanceEngine` separates:

- intake storage
- priority scheduling
- registered identifiers
- job states

This creates a coherent stateful case study instead of four unrelated container demonstrations.

Invalid transitions such as completing an already completed job are rejected.

## Java 17 Implementation

The Java implementation uses explicit enterprise-style domain modeling.

Important types include:

- `QueueLike<T>` for a common queue contract
- `FifoQueue<T>`
- `CircularQueue<T>`
- `DequeModel<T>`
- `Job` as an immutable record
- `JobState` as an enum
- `JobStatus` as an immutable report record
- `DispatchPolicy` as a policy interface
- `PriorityDispatchPolicy`
- `EnterpriseJobService`

The service explicitly controls state transitions:

`QUEUED → RUNNING → COMPLETED`

or:

`QUEUED → RUNNING → FAILED`

Invalid transitions are rejected.

The policy object separates dispatch ordering from service orchestration. This makes it possible to replace ordering rules without rewriting job-state management.

The stream-based status report demonstrates immutable result production and collection processing without turning the application into a generic streams tutorial.

## PostgreSQL Implementation

The PostgreSQL script models persistent queue state.

The principal tables are:

| Table | Responsibility |
|---|---|
| `queue` | Queue identity, type, capacity, and priority configuration |
| `queue_item` | Persistent items, order, priority, payload, and lifecycle state |
| `queue_event` | Audit history of queue operations |

The relational relationship is:

`queue → queue_item → queue_event`

The `queue_kind` enum distinguishes:

- `FIFO`
- `CIRCULAR`
- `DEQUE`
- `PRIORITY`

The database does not pretend that all four structures have identical physical implementations. Instead, relational ordering fields and application/database functions represent their semantics.

## PostgreSQL Ordering

FIFO behavior is represented through `sequence_no`.

Priority behavior uses:

`priority + sequence_no`

This gives deterministic ordering among items with equal priority.

The `next_dispatch` view uses a window function to identify the next item for each queue.

The `dequeue_fifo()` function uses row locking and `SKIP LOCKED`, allowing concurrent workers to avoid selecting the same item.

The `dequeue_priority()` function applies explicit priority ordering before transitioning the selected item to `RUNNING`.

## Database Validation

Database-level validation covers several important rules.

Circular queues must have a positive capacity.

Non-circular queues cannot accidentally receive circular capacity.

Priority values are restricted to the priority queue model.

Non-priority queues cannot assign non-normal priority.

Sequence numbers must be positive.

Active duplicate external keys are prevented with a partial unique index.

State changes generate audit events.

Completion and failure timestamps are assigned by triggers.

These controls prevent application code from being the only enforcement layer.

## Transactional Processing

The SQL script contains an explicit transaction that:

1. Locks a candidate priority item.
2. Changes it to `RUNNING`.
3. Selects the running item.
4. Changes it to `COMPLETED`.
5. Commits both operations atomically.

This is important when multiple workers operate against the same persistent queue.

`FOR UPDATE SKIP LOCKED` is particularly useful for work queues because workers can skip records already being processed instead of waiting unnecessarily.

## Complexity

| Structure | Insert | Remove | Peek | Storage |
|---|---:|---:|---:|---:|
| FIFO queue | O(1) | O(1) | O(1) | O(n) |
| Circular queue | O(1) | O(1) | O(1) | O(capacity) |
| Deque | O(1) | O(1) | O(1) | O(n) |
| Priority queue | O(log n) | O(log n) | O(1) | O(n) |

Priority queues require logarithmic insertion and extraction because heap order must be restored after changes.

A circular queue provides predictable bounded storage but cannot accept more active elements than its capacity.

## Failure Conditions

The implementations explicitly handle:

- dequeue from an empty queue
- peek from an empty queue
- insertion into a full circular queue
- invalid capacity
- invalid priorities
- duplicate identifiers
- blank job names
- invalid lifecycle transitions
- duplicate active persistent keys
- invalid database state combinations

Failure is represented as an exception or database constraint violation rather than an ambiguous return value.

## Performance Considerations

The primary performance decision is to avoid front-removal from ordinary dynamic arrays.

A naive array implementation of:

`remove first element`

may require shifting O(n) remaining elements.

Deque-backed structures avoid this cost.

Circular queues avoid dynamic resizing entirely when a fixed capacity is appropriate.

Priority queues avoid scanning all pending elements to find the next highest-priority item. Heap extraction requires O(log n) time.

The PostgreSQL implementation uses indexes specifically for pending FIFO ordering, priority ordering, and recent event retrieval. Partial indexes restrict index entries to operationally relevant states.

## Security and Reliability Considerations

Queue data can contain operational or application-sensitive information. The examples therefore avoid dynamic SQL construction and use typed relational constraints.

For production systems, payloads should be treated as untrusted input. Validation should occur before dispatch, and consumers should not execute payload values as commands without an explicit authorization boundary.

Persistent queues require attention to:

- transaction boundaries
- duplicate delivery
- idempotent processing
- worker crashes
- retry policy
- poison messages
- audit records
- bounded capacity
- concurrent consumers

A queue data structure by itself does not guarantee exactly-once processing. Application state and transaction design determine the effective delivery semantics.

## Edge Cases

### Empty queue

Every implementation rejects removal from an empty structure.

### Full circular queue

A bounded circular queue rejects insertion when the number of active elements equals capacity.

### Wraparound

Removing an element and then inserting another demonstrates reuse of storage at the beginning of the circular buffer.

### Equal priorities

Priority queues use deterministic secondary ordering so equal-priority jobs do not produce arbitrary output.

### Invalid state transition

A completed or failed job cannot be completed again.

### Duplicate work

The PostgreSQL partial unique index prevents multiple active entries with the same queue-specific external key.

## Distinguishing the Four Structures

These structures solve different ordering problems.

A **queue** answers:

`Which item arrived first?`

A **circular queue** answers:

`Which item arrived first while storage remains bounded and reusable?`

A **deque** answers:

`Which item should be manipulated from either end?`

A **priority queue** answers:

`Which item has the strongest service priority?`

They should not be treated as interchangeable implementations.

## Practical Workflow

A realistic processing pipeline can combine them:

`bounded intake → FIFO staging → priority dispatch → worker execution`

A deque can be introduced when urgent work must enter or leave from either end.

A circular queue is appropriate where a hard storage bound matters.

A priority queue is appropriate where service order is determined by urgency rather than arrival time.

The implementations demonstrate these differences through executable state transitions, validation, scheduling behavior, asynchronous events, and persistent SQL operations.
