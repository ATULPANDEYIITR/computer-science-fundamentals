# Interprocess Communication: Pipes, Message Queues, Shared Memory, and Sockets

## Scope

Interprocess communication (IPC) is the collection of operating-system and application mechanisms that allow independently executing processes to exchange data, coordinate work, expose services, or share state.

This repository treats four IPC mechanisms as distinct technical abstractions:

- **Pipes** provide stream-oriented communication, commonly between related processes or processes whose file descriptors are explicitly connected.
- **Message queues** preserve discrete application messages and are useful when producers and consumers exchange independent work items.
- **Shared memory** allows multiple processes to access the same memory region, reducing copying for large or high-frequency data exchange but introducing synchronization and ownership problems.
- **Sockets** provide a general communication interface that can operate locally, through Unix-domain sockets, or across machines using network transports.

The central architectural distinction is not simply how bytes move. It is the abstraction presented to the application, the lifetime of the communication endpoint, how message boundaries are represented, how failures appear, and how synchronization is enforced.

## IPC Architecture

A useful mental model is:

`Process A → IPC transport → Process B`

For a pipe, the transport behaves primarily as a stream. For a message queue, the transport preserves message units. For shared memory, the transport is a common memory region rather than a sequence of copied messages. For sockets, the transport can expose either stream or datagram semantics and can remain local or cross a machine boundary.

The applications in this repository deliberately use different workloads so that the mechanisms are not interchangeable examples with only syntax changed.

| Mechanism | Primary abstraction | Typical scope | Main engineering concern |
|---|---|---|---|
| Pipe | Byte stream | Related or explicitly connected local processes | Stream framing, blocking, endpoint lifetime |
| Message queue | Discrete messages | Local producer/consumer systems | Capacity, ordering, retries, consumer coordination |
| Shared memory | Common memory | Processes on the same host | Synchronization, ownership, races, cleanup |
| Socket | Stream or datagram endpoint | Local host or network | Framing, connection failure, access control |

## Pipes

A pipe normally exposes two endpoints: one used for writing and one used for reading. The operating system maintains a kernel-managed buffer between them.

A fundamental property is that a pipe is generally a **stream of bytes**. An application should not assume that a single read operation corresponds to one logical application message.

For example, if a producer intends to send:

`temperature=24.5`

followed by:

`temperature=25.1`

the reader may receive both records together, one record in several pieces, or a combination of these depending on buffering and scheduling.

The Python implementation uses `multiprocessing.Pipe()`, which provides connection objects capable of serializing Python objects. This gives the example a high-level point-to-point abstraction rather than requiring a custom byte protocol.

The C++ case study demonstrates a lower-level Unix pipe created with `pipe()`. It uses fixed-size records so the example can concentrate on the operating-system pipe itself. The implementation also contains `read_all()` and `write_all()` because partial I/O and interrupted system calls are important concerns when working directly with file descriptors.

The Java implementation uses `ProcessBuilder` to create a separate JVM process and communicates through the child's standard streams. The stream is wrapped in a length-prefixed protocol so the receiver can distinguish complete application messages from arbitrary stream fragments.

### Pipe lifecycle

A typical pipe workflow is:

`create pipe → create/connect processes → close unused endpoints → write/read → close endpoints → detect EOF`

Closing unused descriptors is important. If a process keeps a duplicate write endpoint open, a reader may continue waiting because the kernel still considers the write side open.

A producer also has to account for backpressure. If the consumer does not read quickly enough, the kernel pipe buffer can fill and a blocking writer may stop until space becomes available.

### Pipe failure behavior

Relevant failures include:

- The writer exits or closes its endpoint, causing the reader eventually to observe end-of-stream.
- A writer attempts to communicate with an unavailable endpoint.
- A process blocks because the pipe buffer is full.
- A reader blocks because no data is currently available and the writer has not closed the channel.
- A protocol built on top of the pipe becomes corrupted because it assumes write boundaries are application message boundaries.

Pipes are especially effective when communication is relatively simple and local. They become less attractive when many independent consumers, durable work queues, complex routing, or remote communication are required.

## Message Queues

A message queue differs from a stream because the application submits **complete messages** rather than an undifferentiated byte sequence.

A work-distribution system can therefore model communication as:

`producer → queue → consumer`

A producer can submit:

`{ job_id: 101, operation: "square", value: 9 }`

and the consumer receives that object as one work item.

The Python implementation uses `multiprocessing.Queue`. It submits structured `Job` objects and deliberately includes an invalid operation so the consumer demonstrates a failed message without terminating the entire worker.

The C++ implementation uses a bounded `MessageQueue` abstraction backed by a condition-variable-protected queue. This keeps the example portable across Linux environments while demonstrating the important message-queue properties: complete work items, bounded capacity, producer/consumer coordination, blocking, and explicit shutdown messages.

The Java implementation uses `LinkedBlockingQueue<DocumentJob>`. A `DocumentJob` is a typed domain record rather than an arbitrary byte sequence. The bounded queue creates backpressure when consumers cannot keep up.

### Queue capacity and backpressure

Capacity is an operational property, not merely a configuration number.

If producers generate work at a sustained rate of 2,000 messages per second while consumers process only 1,500 messages per second, backlog grows over time. A bounded queue eventually forces producers to wait or reject work.

That behavior can be preferable to an unbounded queue because memory usage remains controlled.

The relevant design question is therefore:

`What should happen when consumers are slower than producers?`

Possible policies include blocking producers, rejecting new work, applying priorities, persisting messages, delaying retries, or moving exhausted messages to a dead-letter mechanism.

### Consumer coordination

Multiple consumers require a mechanism that prevents the same work item from being processed incorrectly by competing workers.

The SQL implementation models this through message state and transactional row locking. Its `FOR UPDATE SKIP LOCKED` query allows one worker to claim a queued record without forcing another worker to wait behind an already claimed record.

This database pattern is not a replacement for an operating-system message queue. It demonstrates how durable message coordination can be implemented when the database itself becomes part of the IPC service's control plane.

## Shared Memory

Shared memory is fundamentally different from message passing.

Instead of:

`process A → copy message → process B`

the design becomes:

`process A ↘`
  
`shared memory region`

`process B ↗`

Both processes can access the same physical memory mapping.

This can significantly reduce copying for large datasets, but the reduction in copying creates a new responsibility: the application must coordinate access.

### Race conditions

Consider:

`counter = counter + 1`

At machine level this is not necessarily one indivisible operation. It can involve:

`read → modify → write`

If two processes perform the operation simultaneously, both may read the same old value and one update can overwrite the other.

The Python shared-memory demonstration uses a `multiprocessing.Lock` around the read-modify-write operation.

The C++ shared-memory example uses `mmap(..., MAP_SHARED, ...)` and process-shared atomic counters. The shared mapping is visible to child processes created after the mapping exists.

The Java example intentionally distinguishes JVM-shared memory from cross-process shared memory. `AtomicInteger` provides safe shared state among Java threads inside one JVM, but another JVM cannot directly see that object. The program uses this distinction to avoid incorrectly presenting ordinary Java heap memory as operating-system shared memory.

For genuine cross-process shared memory in Java, a memory-mapped file or another OS-backed memory facility is required.

### Shared-memory design responsibilities

Shared memory usually requires explicit answers to:

- Who creates the segment?
- Which processes may attach?
- Who owns the data structure?
- What synchronization primitive protects each region?
- What happens if a process terminates while holding a lock?
- How is memory initialized?
- How is version compatibility handled?
- How is stale or corrupted state detected?
- Who removes the shared segment?
- How are permissions enforced?

The memory region itself does not automatically provide these policies.

### When shared memory is appropriate

Shared memory is attractive for large local datasets, high-frequency telemetry, image buffers, packet-processing pipelines, and other workloads where copying the same data through repeated messages becomes expensive.

It is a poor fit when the main requirement is simple request/response communication and the amount of transferred data is small. The synchronization and lifecycle complexity can outweigh the performance benefit.

## Sockets

Sockets generalize IPC beyond a single process relationship.

A socket can provide local communication through a Unix-domain socket or communication between machines through network sockets.

A Unix-domain socket can be represented conceptually as:

`client process → local socket endpoint → server process`

A TCP socket can become:

`client process → network → server process`

The programming interface can look similar even though the failure model is very different.

### Stream framing

TCP and Unix stream sockets provide ordered byte streams. They do not inherently preserve application message boundaries.

If a client sends:

`MESSAGE_A`

and:

`MESSAGE_B`

the server must use a protocol that determines where each message ends.

The Python, JavaScript, and Java examples therefore implement length-prefixed framing.

The protocol is conceptually:

`4-byte payload length + payload bytes`

The receiver first reads the fixed-size length and then reads exactly that many bytes.

This is stronger than assuming that one `recv()` or `read()` call returns one application message.

The JavaScript implementation demonstrates the same principle with a `FrameDecoder`. It accumulates chunks until an entire frame is available.

### Unix-domain sockets

Unix-domain sockets are useful for local services such as:

- local administrative APIs
- database clients
- service supervisors
- local worker services
- daemon control interfaces

They avoid TCP/IP routing when both endpoints reside on the same host.

Filesystem permissions can also provide an important access-control layer. The Python, JavaScript, and C++ examples restrict the local socket endpoint where the platform permits it.

A local socket should not automatically be considered secure. An attacker who can access the endpoint may still be able to issue valid protocol commands unless authentication and authorization are enforced.

## Relationship Between the Four Mechanisms

These mechanisms can appear together in one architecture.

A high-throughput local processing system might use a pipe for a simple parent-to-child control path, a message queue for work distribution, shared memory for large telemetry buffers, and a Unix socket for administrative requests.

The mechanisms serve different roles:

`control stream → pipe`

`work items → message queue`

`large shared dataset → shared memory`

`request/response API → socket`

The important design decision is therefore not to choose one IPC mechanism universally. It is to match the communication semantics to the workload.

## Python Implementation

The Python program uses `multiprocessing` to create independent operating-system processes.

The pipe example uses `multiprocessing.Pipe` and exchanges structured Python dictionaries. It demonstrates command handling, response generation, shutdown, and worker cleanup.

The message-queue example introduces a `Job` dataclass and a producer/consumer workflow. Queue capacity is bounded, and the worker explicitly reports unsupported operations rather than silently discarding them.

The shared-memory example creates a `SharedMemory` segment and exposes it as an integer buffer. Three processes modify the same array while a process-safe lock protects the update operation.

The socket example uses a Unix-domain stream socket. JSON provides the application representation, while a four-byte length prefix provides message framing.

The failure demonstration intentionally closes a pipe endpoint and reads from an empty queue. These cases show why IPC code needs explicit handling for endpoint closure, empty queues, process termination, timeouts, and protocol errors.

## JavaScript Implementation

The Node.js implementation uses several JavaScript-specific process facilities.

`child_process.fork()` provides a child process with Node's built-in process messaging channel. This is message-oriented and therefore differs from the byte stream used through child standard output.

`spawn()` demonstrates a stream-style process boundary. The pipe worker writes newline-delimited JSON, and the parent reconstructs messages from chunks. This shows why stream parsing is necessary even when the payload format is JSON.

`SharedArrayBuffer` provides a shared memory region between worker threads. `Atomics.add()` is used because ordinary read-modify-write updates are not sufficient when several workers modify the same shared integer.

The Unix-domain socket example uses Node's `net` module. Its `FrameDecoder` reconstructs length-prefixed JSON messages from arbitrary stream chunks.

The examples therefore expose a JavaScript-specific distinction between process messaging, process streams, shared memory between worker threads, and socket-based communication.

## C++ Case Study

The C++ program models a local telemetry-processing service.

Sensor records contain a sensor identifier, numeric value, and unit. The service must receive records, process them, maintain aggregate metrics, and expose an administrative interface.

The pipe portion creates a real Unix pipe and a child process. Fixed-size `PipeRecord` structures are transmitted through file descriptors. `read_all()` and `write_all()` handle partial system calls and interruptions.

The message-queue portion uses a bounded queue with condition variables. A `WorkMessage` can represent either a processing job or a shutdown request. Capacity creates backpressure rather than allowing uncontrolled queue growth.

The shared-memory portion uses `mmap` with `MAP_SHARED`. Multiple child processes update process-shared atomic counters. The example demonstrates why shared memory must be combined with synchronization rather than treated as automatically safe.

The socket portion uses a Unix-domain `SOCK_STREAM` endpoint. The administrative client sends `GET_METRICS`, and the server returns current aggregate metrics.

The case study intentionally combines IPC mechanisms because real systems often need more than one communication semantic.

## Java Implementation

The Java program models an enterprise document-processing service.

`DocumentJob` is a validated immutable record representing work. `ProcessingResult` explicitly represents completion or failure. `JobState` prevents the workflow from being reduced to unstructured strings.

`LinkedBlockingQueue` supplies bounded message-oriented work distribution. The processing service maintains state transitions and uses atomic metrics for concurrent updates.

The process-pipe example launches another JVM through `ProcessBuilder`. The parent and child exchange length-prefixed messages through standard input and output.

The Unix-domain socket example uses Java's Unix-domain socket support and the same framing principle used by the other stream-oriented examples.

The shared-state demonstration uses `AtomicInteger` and explicitly labels the boundary: it is shared JVM memory, not cross-process shared memory. This distinction is important when designing Java systems because an ordinary Java heap belongs to one JVM process.

## SQL Data Model

The PostgreSQL script models the durable control plane surrounding an IPC service.

`ipc_service` identifies logical services.

`ipc_endpoint` describes the communication mechanism and its scope. The `transport_kind` enumeration prevents arbitrary transport names from being inserted.

`socket_endpoint` stores socket-specific protocol information such as Unix stream, TCP stream, or UDP datagram.

`ipc_process` records participating operating-system processes.

`ipc_message` represents durable application messages and records state, priority, retry count, availability time, and JSON payload.

`message_consumer` represents consumers and their retry policy.

`message_delivery` records delivery attempts separately from the message itself. This is important because one logical message may have multiple delivery attempts.

`shared_memory_segment` and `shared_memory_attachment` model shared-memory ownership and process attachment.

`ipc_failure` records transport-specific failure information so operational failures do not disappear into application logs alone.

### Database integrity

Several rules are enforced through constraints.

Message priorities are limited to a known range. Attempt counts cannot become negative. Socket ports must be valid TCP/UDP port numbers. Shared-memory sizes must be positive. Process stop times cannot precede process start times.

The `completion_time_consistent` constraint prevents a completed or terminal message from existing without a completion timestamp and prevents nonterminal messages from carrying a completion timestamp.

These rules belong at the database layer because they describe durable data invariants rather than temporary application state.

### Queue claiming

The SQL script uses:

`FOR UPDATE SKIP LOCKED`

inside a common table expression to demonstrate concurrent work claiming.

A worker locks one available message, changes its state to `PROCESSING`, and increments its attempt count. Another worker can skip already locked rows and search for other work.

This is useful for database-backed work queues because it reduces contention between concurrent consumers.

It is not identical to an operating-system message queue. A database-backed queue adds durability, transactional semantics, SQL querying, and persistence, but it also introduces database load and database-specific locking behavior.

## State and Failure Modeling

IPC systems have multiple states that should not be collapsed into one boolean.

A message can move through:

`QUEUED → DELIVERED → PROCESSING → COMPLETED`

or:

`QUEUED → PROCESSING → FAILED → RETRY`

and eventually:

`FAILED → DEAD_LETTERED`

A process can terminate while a message is being processed. A socket can disconnect after a request is transmitted but before the response arrives. A queue consumer can fail after receiving work but before recording completion. A shared-memory process can terminate while another process is reading a region.

These cases create an important distinction between **transport success** and **business success**.

Receiving bytes successfully does not mean the application processed the operation successfully.

## Ordering and Delivery Semantics

IPC mechanisms differ in the ordering guarantees they expose.

A stream generally preserves byte order, but it does not define application message boundaries.

A message queue preserves discrete messages and commonly provides ordering rules within its defined scope, but multiple consumers can make observed processing order differ from insertion order.

Shared memory has no inherent message ordering. The application must establish synchronization and visibility rules.

Sockets inherit their ordering and delivery behavior from the chosen socket type. TCP provides an ordered reliable byte stream, while UDP provides datagrams without TCP's reliability and ordering guarantees.

Therefore an application should explicitly document whether it needs:

- at-most-once processing
- at-least-once processing
- retryable delivery
- deduplication
- strict ordering
- bounded latency
- durable messages
- best-effort delivery

IPC transport alone does not automatically solve all of these requirements.

## Synchronization

Communication and synchronization are related but different.

A pipe can transmit data without guaranteeing that a larger application workflow is synchronized.

A queue can deliver a job without guaranteeing that two consumers cannot update the same external resource incorrectly.

Shared memory requires synchronization almost immediately because simultaneous access can produce races.

Sockets provide communication but do not automatically make a multi-step request transaction atomic.

Locks, atomic operations, semaphores, condition variables, transactional state changes, sequence numbers, and acknowledgements can therefore be required above the basic transport.

## Performance Considerations

Pipes and queues normally involve kernel-managed buffering and data movement between address spaces.

Message-oriented IPC is often easier to reason about but can introduce serialization and copying costs.

Shared memory can avoid repeated copies for large data structures, but synchronization overhead and cache contention can become significant. False sharing can occur when independent counters occupy the same cache line and multiple CPUs repeatedly modify them.

Sockets add protocol and kernel overhead, with TCP also involving network-stack processing even when endpoints are on the same machine. Unix-domain sockets generally avoid the IP routing path and are useful for local service communication.

Performance should therefore be measured against the actual workload rather than inferred only from the IPC mechanism's name.

## Security Considerations

IPC endpoints are attack surfaces.

A local Unix socket should have controlled filesystem permissions. A process should not trust a peer merely because it is local.

Socket protocols should validate message lengths before allocating memory. The examples enforce maximum frame sizes.

JSON or other structured input should be validated against an expected schema before values influence sensitive operations.

Shared-memory regions require access-control policies because a process with permission to attach may potentially read or modify sensitive state.

Message queues require controls around who may publish, consume, acknowledge, or delete messages.

Pipes can expose sensitive information when inherited file descriptors are accidentally passed to processes that should not receive them.

Security therefore includes both transport access and application-level authorization.

## Debugging IPC Systems

IPC bugs frequently appear as timing-dependent failures.

Useful observations include:

- process identifiers
- endpoint creation and destruction
- queue depth
- message identifiers
- correlation identifiers
- delivery attempts
- timestamps
- state transitions
- socket connection events
- bytes or messages transmitted
- process termination status
- timeout causes

A correlation identifier is especially useful when one request generates several internal messages. The SQL model stores `correlation_id` separately from the message identifier so related operations can be traced without assuming that one request always equals one message.

Deadlocks and indefinite blocking should be diagnosed by determining which process owns each synchronization primitive and which process is waiting for data, capacity, or another lock.

## Common Design Errors

Treating a stream read as one complete message is a common protocol error. Pipes and stream sockets require framing when the application exchanges variable-length messages.

Using shared memory without synchronization creates race conditions. Adding a lock after the design is already running can also be insufficient if readers and writers do not agree on ownership and memory visibility.

Using an unbounded work queue can convert downstream slowdown into memory exhaustion.

Assuming local communication is automatically secure can expose administrative socket commands to unintended processes.

Ignoring process termination can leave queued work permanently stuck in a processing state.

Retrying every IPC failure blindly can produce duplicate side effects. Retries therefore need an idempotency or deduplication strategy when the operation is not naturally repeatable.

## Practical Selection Criteria

Use a **pipe** when the communication is simple, local, and naturally represented as a stream between known processes.

Use a **message queue** when work consists of independent messages and producer/consumer coordination is central to the design.

Use **shared memory** when processes on the same host need very high-throughput access to common data and the team can correctly implement synchronization, ownership, lifecycle, and recovery.

Use a **socket** when the service boundary should support a request/response interface, multiple clients, Unix-local communication, or network communication.

The correct mechanism follows the communication semantics rather than the programming language.

## Limitations Demonstrated by the Implementations

The examples are educational systems rather than replacements for production IPC frameworks.

The Python queue and pipe abstractions serialize Python objects and therefore have Python-specific interoperability characteristics.

The Node.js shared-memory example uses worker threads because `SharedArrayBuffer` is a JavaScript shared-memory facility within the Node process model. It should not be confused with an operating-system shared-memory segment visible to unrelated processes.

The C++ implementation uses Unix/POSIX APIs for the low-level pipe, memory mapping, and Unix-domain socket examples. Those APIs are not portable unchanged to every operating system.

The Java implementation uses standard Java 17 APIs and deliberately distinguishes JVM-shared state from true cross-process memory mapping.

The SQL implementation models durable IPC state rather than replacing the operating system's transport layer.

The four mechanisms therefore remain conceptually distinct even when a production architecture combines them.
