# Threads: Processes, Multithreading, Thread Models, and Thread Lifecycle

## Scope

This project studies threads as operating-system and programming-language execution units. It distinguishes processes from threads, explains how multiple threads execute within a process, examines historical and modern thread-mapping models, and models the lifecycle of a thread from creation through termination.

The implementations deliberately approach the subject from different perspectives:

- The Python program focuses on executable demonstrations of lifecycle tracking, process/thread identity, synchronization, producer-consumer coordination, thread pools, CPU-bound limitations, cancellation, failure handling, and deadlock prevention.
- The JavaScript program uses Node.js Worker Threads to demonstrate event-driven coordination, worker pools, message passing, shared memory, CPU-bound parallel work, worker failure, and lifecycle management.
- The C++ program presents a workload-scheduling case study using `std::thread`, atomics, condition variables, futures, a bounded queue, and a reusable worker pool.

The three central ideas are related but not interchangeable. A process is a resource and isolation boundary. A thread is an execution path within a process. Multithreading is the use of multiple threads within a process or execution environment.

## Processes and Threads

A process normally owns a separate virtual address space. Its executable code, global state, heap, stacks, file descriptors, and other operating-system resources belong to a process context. A separate process therefore provides a stronger isolation boundary than a thread.

Threads belonging to the same process share much of that process's address space. They normally share dynamically allocated objects, global variables, executable code, and process-level resources. Each thread nevertheless has its own execution context, including a stack, registers, scheduling state, and thread identifier.

This distinction creates an important trade-off.

A process can isolate failures and memory corruption more strongly, but communication between processes generally requires an explicit inter-process communication mechanism such as pipes, sockets, shared memory, or operating-system message facilities.

Threads can communicate through ordinary shared memory, which can be considerably faster and simpler for tightly coupled workloads. The cost is synchronization complexity. Two threads modifying the same state without appropriate synchronization can produce races, inconsistent invariants, deadlocks, or undefined behavior depending on the language and memory model.

The Python implementation demonstrates process and thread identity separately. The thread created in the same process retains the parent's process identity while receiving a distinct thread identity. The separate multiprocessing worker has a different process identity.

The C++ implementation makes the same distinction with `std::thread::id` and explains why a portable C++17 program should not assume that `std::thread` itself is a process abstraction.

## Why Multithreading Exists

A single execution path can perform only one sequence of instructions at a time. Multiple threads allow an application to divide independent work into concurrent execution paths.

The benefit depends strongly on the workload.

For I/O-bound work, a thread may spend substantial time waiting for a database, socket, filesystem, or external service. Other threads can perform useful work during those waits.

For CPU-bound work, several threads can execute computations simultaneously when the runtime and operating system permit true parallel execution across multiple processor cores. The scalability is limited by available cores, memory bandwidth, synchronization, cache behavior, and the amount of work that can actually run independently.

Concurrency and parallelism are related but distinct terms. Concurrency describes multiple tasks making progress during overlapping periods. Parallelism means multiple tasks are actually executing at the same time on separate execution resources.

The Python example is deliberately careful about this distinction because standard CPython has a Global Interpreter Lock. Ordinary Python threads are useful for many I/O-bound workloads, but they should not be treated as a general mechanism for parallel execution of CPU-intensive Python bytecode. The Python program therefore compares sequential computation, Python threads, and multiprocessing and explicitly identifies the machine-dependent nature of timing measurements.

The JavaScript implementation takes a different approach. Ordinary Node.js JavaScript executes through an event-driven model, while Worker Threads provide additional JavaScript execution contexts that can execute CPU-intensive JavaScript independently.

C++ exposes native operating-system threads through the standard library and can therefore use multiple threads for CPU-parallel work when the platform provides the corresponding scheduling resources.

## Thread Lifecycle

A useful conceptual lifecycle contains states such as:

`NEW` → `RUNNABLE` → `RUNNING` → `WAITING` → `RUNNING` → `TERMINATED`

These names describe application and scheduler concepts rather than a universal API exposed identically by every operating system.

A newly constructed thread has not yet started executing its target function. After it is started, it becomes eligible for scheduling. The scheduler may run it immediately or leave it waiting for processor time. During execution, it can block or wait for a timer, lock, condition, I/O operation, or another synchronization event. Eventually its target function returns or the thread otherwise terminates.

The Python program creates a `Thread` object, records an application-level `NEW` state, starts the thread, records runnable and running states, deliberately waits on a timer, and finally records termination. `join()` is then used to wait for completion.

The C++ implementation uses a similar lifecycle tracker around `std::thread`. The tracker is intentionally separate from the standard library's actual internal scheduler state because C++17 does not provide a portable API that exposes the complete operating-system thread state machine.

Node.js Worker Threads expose worker creation, messages, errors, exit events, and termination rather than a universal operating-system scheduler-state enumeration. The JavaScript implementation therefore models lifecycle using observable Worker events.

## Thread Creation and Joining

Creating a thread transfers or schedules a callable unit of work.

In Python, `threading.Thread` accepts a target function and arguments. Calling `start()` begins execution in a new thread. Calling the target function directly would not create another thread.

In C++, constructing a `std::thread` with a callable starts a new execution thread. A thread object must eventually be joined or detached before it is destroyed. The case study consistently uses `join()` for controlled ownership.

In Node.js, `new Worker(...)` creates a Worker Thread. Communication is normally performed using `postMessage()` and message events rather than directly sharing ordinary JavaScript objects.

Joining or otherwise waiting for completion matters because application shutdown, resource lifetime, and result collection must be coordinated with thread termination.

## Thread Models

Thread models describe the relationship between user-level execution contexts and kernel-managed schedulable threads.

### Many-to-One

In a many-to-one model, multiple user-level threads are mapped onto one kernel thread.

The runtime can provide many logical execution contexts while the operating system sees only one kernel-schedulable execution entity for that group. A blocking kernel operation can therefore prevent other user-level threads in the same group from progressing. The model also cannot obtain true CPU parallelism from multiple kernel execution resources.

The Python, JavaScript, and C++ APIs in this project do not allow the programmer to select a many-to-one operating-system mapping. It is presented as a thread-model concept rather than as an API configuration.

### One-to-One

In a one-to-one model, each user-visible thread corresponds to a kernel-schedulable thread.

This allows the operating system to schedule different threads on different processor cores when sufficient independent work exists. It also means that creating very large numbers of threads can impose real operating-system resource costs.

The C++ `std::thread` implementation represents this style of native threaded execution from the application programmer's perspective, although the exact implementation remains platform-dependent.

### Many-to-Many

A many-to-many model allows many user-level execution contexts to be multiplexed over a pool of kernel threads.

The runtime can provide a large number of logical execution contexts without requiring a dedicated kernel thread for every logical task. This design can improve scalability for certain workloads but requires sophisticated scheduling between the user-level runtime and the kernel.

Modern language runtimes frequently implement abstractions that differ from these historical textbook models, so the three models should be treated as architectural concepts rather than as a complete classification of every contemporary runtime.

## Python Implementation

The Python program is structured as an executable progression from basic thread behavior to realistic concurrency design.

### Lifecycle tracing

`LifecycleTracer` records application-level state transitions. The worker deliberately waits on a timer so the `WAITING` state has observable meaning rather than being a label attached to a purely computational function.

The use of `join()` demonstrates controlled thread ownership. The main thread waits until the worker has completed instead of allowing the worker's lifetime to become an unmanaged background activity.

### Process and thread identity

The process/thread demonstration records process IDs and thread IDs. The child thread shares the main process identity, whereas the multiprocessing worker runs in a separate process.

This directly demonstrates why process isolation and thread concurrency should not be treated as equivalent concepts.

### Shared state and locks

`UnsafeCounter` shows the structure of a read-modify-write operation:

`read → modify → write`

If several threads perform this sequence without synchronization, one thread can overwrite another thread's update.

`SafeCounter` surrounds the critical section with `threading.Lock`. The lock establishes exclusive access to the shared state during the operation.

The important principle is not that every threaded operation needs a lock. A lock is needed when concurrent execution can violate an invariant or otherwise create an unsafe access pattern.

### Events and conditions

`threading.Event` provides one-way notification for a state change such as "configuration is ready." A waiting thread can block until the event becomes set.

`threading.Condition` provides coordination around a predicate associated with shared state. The bounded producer-consumer example waits while the queue is full or empty and wakes other participants when the predicate may have changed.

The condition-variable pattern uses a `while` loop rather than an `if` statement because a wake-up does not itself guarantee that the desired predicate is still true.

### Producer-consumer processing

`LogProcessor` uses a bounded `queue.Queue` and multiple worker threads.

The bounded queue creates backpressure. A producer cannot create unlimited pending work because `put()` blocks when the queue reaches its capacity.

Worker threads retrieve log records, process them, record failures, and call `task_done()`. The processor waits for all queued work with `queue.join()` before sending sentinel objects that cause workers to terminate.

This is a practical thread architecture because producers and consumers have different responsibilities and the queue decouples their rates.

### Thread pools and futures

`ThreadPoolExecutor` manages reusable worker threads. The example submits simulated remote lookups and uses `Future` objects to retrieve either successful results or exceptions.

This model is preferable to creating a new thread for every small task because thread creation, stack allocation, scheduling, and teardown have costs. A pool also provides a natural place to bound concurrency.

### CPU-bound limitation

The prime-counting example contrasts sequential computation, threads, and multiprocessing.

The measurements are deliberately treated as observational rather than as fixed benchmarks. Operating-system scheduling, CPU architecture, Python version, process startup cost, machine load, and input size can all change the results.

The important architectural lesson is that Python's standard CPython thread implementation is not equivalent to native CPU parallelism for ordinary CPU-bound Python bytecode.

### Cancellation and failure handling

A running Python thread cannot safely be killed arbitrarily through the standard `threading` API.

The cancellation demonstration therefore uses a shared `threading.Event`. The worker periodically checks the event and exits cooperatively.

The failure demonstration shows that exceptions from executor tasks are retrieved through their corresponding `Future`. This prevents worker failures from disappearing silently.

### Deadlock prevention

The deadlock discussion uses two locks to describe the classic circular-wait condition:

`Thread A: holds A → waits for B`

`Thread B: holds B → waits for A`

The implementation demonstrates a consistent lock-ordering strategy. If all participants acquire locks in the same global order, circular wait can be eliminated.

Other designs can reduce deadlock risk by shortening critical sections, avoiding unnecessary shared state, using higher-level synchronization structures, applying timeouts where appropriate, or redesigning ownership.

## JavaScript Implementation

The JavaScript program uses Node.js Worker Threads rather than translating the Python examples line by line.

### Worker execution contexts

The same JavaScript file acts as both the main coordinator and the worker implementation. `isMainThread` distinguishes the coordinator from worker execution.

`workerData` supplies initialization information to a worker, while `parentPort` provides the message channel between the worker and its parent.

This structure demonstrates how Worker Threads create additional JavaScript execution contexts while retaining an event-driven communication model.

### Event-driven worker pool

`EventWorkerPool` maintains a collection of workers and distributes requests to workers that are not currently busy.

Each submitted request receives a unique request ID. The pool stores its `resolve` and `reject` functions in a `Map`. When the worker returns a result, the request ID identifies the corresponding promise.

This creates an explicit request-response protocol:

`submit event → assign request ID → send message → worker processes event → worker sends result → resolve matching promise`

The protocol is more important than simply creating multiple workers because real applications need to associate asynchronous results with the operations that initiated them.

### Message passing

The event-processing workers receive structured messages rather than directly manipulating the main thread's ordinary JavaScript objects.

Message passing provides clear ownership boundaries. The worker receives an input, performs its operation, and sends back a result.

This model reduces shared-state complexity compared with exposing mutable application structures to every worker.

### Shared memory

`SharedArrayBuffer` demonstrates a different concurrency mechanism.

The counter is visible to both execution contexts. `Atomics.add()` is used to perform an atomic increment, and `Atomics.load()` retrieves the value.

Shared memory can be useful for high-performance coordination, but it changes the synchronization model. Once multiple workers can directly observe the same memory, the application must reason about atomicity and memory ordering rather than relying exclusively on message ownership.

### CPU-bound worker execution

The prime-counting workload runs in separate Worker Threads. This prevents the expensive computation from monopolizing the main event-loop execution context.

The example is intentionally different from the Python CPU-bound demonstration. It focuses on how Node.js can move CPU-intensive JavaScript to Worker Threads rather than on comparing process and thread timings.

### Worker failures and termination

The pool listens for worker errors and exit events. Pending requests associated with a failed worker are rejected instead of being left unresolved.

This is a critical production concern. A concurrent system must define what happens when the execution resource responsible for a request disappears.

## C++ Case Study: Workload Scheduler

The C++ implementation models a workload scheduler that accepts two broad classes of work:

- CPU-bound jobs perform prime-number analysis.
- I/O-like jobs spend time waiting, representing operations such as remote configuration, database, or object-store access.

The scheduler creates a fixed worker set and feeds it through a bounded queue.

### Bounded queue

`BoundedQueue<T>` uses:

- `std::mutex` to protect queue state.
- `std::condition_variable` to wait for space or data.
- A maximum capacity to provide backpressure.
- A close operation that wakes blocked producers and consumers.

The `push()` predicate waits until the queue has capacity or has been closed. The `pop()` predicate waits until data exists or the queue has been closed.

This design avoids busy waiting. A worker that has no work sleeps rather than repeatedly polling the queue.

### Worker pool

`WorkScheduler` creates a fixed number of worker threads. Each worker repeatedly obtains a work item from the queue and processes it.

The pool avoids repeated thread creation and gives the system a predictable concurrency limit.

A fixed pool also prevents an application from responding to increased input simply by creating an unbounded number of threads. Unbounded thread creation can exhaust memory and increase scheduler contention.

### Atomic state

`AtomicCounter` demonstrates an operation that can be safely incremented by multiple threads without a mutex.

The example uses `memory_order_relaxed` because the counter itself does not carry an additional ordering relationship with other data. The atomic operation guarantees safe modification of the counter, while stronger memory ordering would be appropriate when the atomic variable is also used to coordinate visibility of other shared objects.

This distinction is important: atomicity of one variable does not automatically make an entire multi-object algorithm thread-safe.

### Futures

The asynchronous task demonstration uses `std::async` and `std::future`.

An exception raised inside the asynchronous operation is captured by the future and rethrown when `get()` is called. This gives the calling thread a structured mechanism for receiving both successful results and asynchronous failures.

### Cancellation

The scheduler uses an atomic cancellation flag. Workers check the flag before executing pending work.

This is cooperative cancellation rather than forced thread termination. Forced termination can leave mutexes locked, partially updated data structures, open resources, or broken invariants.

The same principle applies across languages: reliable thread cancellation normally requires the work itself to cooperate with the cancellation protocol.

## Synchronization Mechanisms

Synchronization should be selected according to the state relationship being protected.

| Mechanism | Appropriate role | Important concern |
| --- | --- | --- |
| Mutex | Exclusive access to shared mutable state | Contention and deadlock |
| Atomic | Small independently synchronized state | Does not automatically protect related objects |
| Condition variable | Waiting for a state predicate | Predicate must be checked after wake-up |
| Event | Notification that a state transition occurred | Usually represents notification rather than arbitrary data transfer |
| Queue | Ownership transfer between producers and consumers | Capacity and shutdown behavior matter |
| Future | Result and exception propagation | Completion does not automatically solve shared-state safety |
| Message passing | Explicit communication between execution contexts | Serialization, transfer cost, and protocol design |

The best design often minimizes shared mutable state instead of adding more locks.

## Thread Lifecycle and Blocking

A thread can be active without continuously consuming CPU. It may wait for:

- a lock to become available;
- a condition-variable predicate;
- I/O completion;
- a timer;
- another thread's result;
- queue input;
- explicit synchronization.

Blocking is therefore an important part of thread design.

A worker pool with ten threads does not necessarily mean ten threads are executing instructions continuously. Several may be waiting for external resources while another performs computation.

Excessive blocking can nevertheless reduce throughput if the pool is too small. An excessively large pool introduces other costs such as memory usage, scheduling overhead, cache contention, and context switching.

## Common Concurrency Failures

### Race conditions

A race occurs when correctness depends on the relative timing of concurrent operations.

A typical pattern is:

`read shared value → calculate new value → write shared value`

Two workers can read the same old value and both write derived results, causing one update to disappear.

The solution is not always a mutex. Depending on the problem, ownership transfer, immutable data, queues, atomics, or a redesign can be more appropriate.

### Deadlocks

Deadlock requires a cycle in which participants wait indefinitely for resources held by one another.

Consistent lock ordering is a practical prevention technique. If every component acquires locks according to the same global ordering, circular wait can be prevented.

Long critical sections also increase contention. Work that does not require exclusive access should normally occur outside the protected region.

### Starvation

Starvation occurs when a thread repeatedly fails to obtain the resources or scheduling opportunities it needs.

Unfair lock usage, poorly designed priority systems, and overloaded queues can contribute to starvation.

### Livelock

In livelock, threads remain active and repeatedly respond to one another but fail to make useful progress. Retrying without backoff is a common pattern that can create this condition.

### Unbounded queues

An unlimited work queue can hide a throughput problem until memory usage becomes dangerous.

Bounded queues introduce backpressure. Once the queue is full, producers must wait, reject work, or apply another explicit overload policy.

## Thread Safety Versus Reentrancy

Thread safety means concurrent use does not violate correctness under the specified synchronization model.

Reentrancy concerns whether a function can safely be entered again before a previous invocation has completed, including cases involving callbacks or signals depending on the environment.

A function can be thread-safe without being reentrant in every possible execution context, and a reentrant function is not automatically a complete solution to every shared-state concurrency problem.

For application-level thread design, explicit ownership and clear synchronization boundaries are generally easier to reason about than relying on hidden global state.

## Performance Considerations

Threading introduces overhead as well as potential speedups.

Relevant costs include:

- thread creation and destruction;
- thread stack memory;
- scheduler operations;
- context switches;
- mutex contention;
- cache invalidation and cache-line contention;
- atomic operations;
- communication and serialization;
- worker startup time;
- queue contention.

The useful concurrency level is workload-dependent.

CPU-bound workloads generally scale only while additional workers can obtain useful processor resources. Creating more threads than the machine can efficiently schedule can reduce performance.

I/O-bound workloads can benefit from more concurrent operations because workers spend time waiting, but external limits such as database connection pools, socket limits, API rate limits, and service capacity still constrain useful concurrency.

Benchmark results should therefore be measured on representative workloads rather than inferred from thread count alone.

## Security and Reliability

Threads share process memory, so a memory-safety error or corrupted shared structure can affect other threads in the same process.

This makes process isolation valuable when stronger fault containment is required.

Concurrent applications should also consider:

- bounded work queues to limit memory growth;
- timeouts for operations that can block indefinitely;
- explicit worker failure handling;
- cooperative cancellation;
- safe ownership of resources;
- minimal shared mutable state;
- predictable shutdown behavior;
- lock-ordering rules;
- validation before work enters a shared queue.

A separate thread should not be treated as a security sandbox. A thread normally operates with the privileges and address-space access of its process.

## Debugging Concurrent Programs

Concurrency bugs are often timing-dependent. A program may work repeatedly and then fail under a different CPU load or scheduler decision.

Useful debugging observations include thread IDs, worker names, queue sizes, task IDs, state transitions, and timing information.

The examples record explicit lifecycle and worker information for this reason.

Logging from multiple threads also requires care. Log records should remain identifiable by operation and worker, and the logging mechanism itself must be safe for concurrent use.

A reproducible task ID and deterministic input set can make intermittent failures substantially easier to investigate.

## Relationship Between the Implementations

The three implementations intentionally demonstrate different concurrency abstractions.

Python emphasizes high-level thread coordination through `threading`, `queue`, `Event`, `Condition`, `ThreadPoolExecutor`, and `Future`.

JavaScript emphasizes an event-driven runtime where ordinary application work is coordinated through callbacks and promises, while Worker Threads are introduced when independent JavaScript execution is needed. It also demonstrates the important distinction between message-passing communication and explicitly shared memory.

C++ emphasizes lower-level execution control. `std::thread`, `std::mutex`, `std::condition_variable`, `std::atomic`, `std::future`, and the custom bounded queue expose the mechanisms used to build a reusable worker architecture.

The common architectural pattern is the same at a higher level:

`work arrives → work is assigned → execution proceeds concurrently → shared or transferred state is coordinated → result or failure is returned → workers shut down cleanly`

The implementation details differ because each runtime exposes different concurrency primitives and memory models.

## Practical Design Rules

Thread count should be chosen from workload characteristics and resource limits rather than from a desire to maximize the number of threads.

Shared state should have a clear owner and synchronization rule. If state can be transferred instead of shared, message passing or queue-based ownership transfer can reduce synchronization complexity.

Critical sections should be small enough to reduce contention but large enough to protect the complete invariant they are responsible for.

Every worker system should define startup, normal completion, failure, cancellation, and shutdown behavior. A design that specifies only the successful execution path is incomplete.

A thread should not be used merely because a task is logically separate. The cost of concurrency must be justified by overlapping useful work, latency requirements, isolation requirements, or throughput requirements.

The central distinction remains:

**Processes provide separate execution and memory-isolation boundaries; threads provide concurrent execution within a process; multithreading coordinates multiple such execution paths; thread models describe how those execution paths relate to user-level and kernel-level scheduling; and the thread lifecycle describes their progression from creation through completion.**
