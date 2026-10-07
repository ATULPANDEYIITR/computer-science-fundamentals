# Synchronization Mechanisms: Mutex, Semaphore, Monitors, Locks, and Condition Variables

## Scope

This learning set treats synchronization as the coordination of concurrent execution around shared state and finite resources.

The mechanisms are related, but they solve different problems:

| Mechanism | Primary purpose | Typical invariant |
|---|---|---|
| Mutex | Exclusive access to a critical section | At most one owner enters protected code |
| Lock | General abstraction for controlled mutual exclusion | Protected state is accessed under a defined ownership protocol |
| Semaphore | Control a quantity of concurrent access | The number of permit holders cannot exceed capacity |
| Condition variable | Wait for a state predicate to become true | A thread sleeps until protected state may satisfy its predicate |
| Monitor | Encapsulate shared state and its synchronization rules | State is accessed through synchronized operations |

A useful distinction is that a mutex answers **who may enter**, a semaphore answers **how many may enter**, and a condition variable answers **when a waiting participant should try again**. A monitor combines shared state, exclusive access, and condition-based waiting into a higher-level synchronization structure.

The implementations use realistic bounded work queues, resource pools, worker services, state transitions, and transactional database coordination rather than isolated syntax examples.

## Core synchronization model

Concurrent code becomes difficult when multiple execution contexts can observe or modify the same state.

Consider a shared integer counter:

`read -> calculate -> write`

The apparent simplicity hides a race. Two workers can read the same old value, calculate independently, and then overwrite each other's result.

A mutex makes the read-modify-write sequence one critical section:

`lock -> read -> calculate -> write -> unlock`

The protected region should be as small as practical. A large critical section reduces concurrency and can turn synchronization into a throughput bottleneck.

A synchronization primitive should protect an invariant rather than simply surround arbitrary code. For example, a bounded queue needs the invariant:

`0 <= queue_size <= capacity`

The queue's producer and consumer operations must preserve that invariant while allowing threads to sleep when the required state is unavailable.

## Mutexes and locks

A mutex provides mutual exclusion. Exactly one execution context can own it at a time.

Python's `threading.Lock`, C++'s `std::mutex`, and Java's `ReentrantLock` all support exclusive critical sections, although their APIs and ownership semantics differ.

The Python implementation uses `with lock:` so release is performed automatically when control leaves the protected block. This is particularly important when the protected operation raises an exception.

The C++ implementation demonstrates RAII with `std::lock_guard` and `std::scoped_lock`. The lock object's lifetime determines when the mutex is held. `std::scoped_lock` is particularly useful when multiple mutexes must be acquired together because it uses a deadlock-avoidance strategy.

The Java implementation uses `ReentrantLock` where explicit locking is useful. It also demonstrates Java's `synchronized` methods as monitor-style mutual exclusion.

A normal non-reentrant mutex should not be acquired twice by the same thread unless the API explicitly supports that behavior. Python's `RLock` and Java's `ReentrantLock` are reentrant. Reentrancy is useful when synchronized operations call other synchronized operations on the same object, but it should not be used to conceal unnecessarily complicated locking.

## Deadlock

A deadlock occurs when execution contexts wait indefinitely for one another.

The classic circular dependency is:

`Thread A holds Lock X and waits for Lock Y`

while:

`Thread B holds Lock Y and waits for Lock X`

Four conditions are commonly associated with deadlock:

- Mutual exclusion means a resource has exclusive ownership.
- Hold and wait means an execution context retains one resource while requesting another.
- No preemption means the resource is not forcibly taken away.
- Circular wait means the dependency chain forms a cycle.

The examples prevent circular wait by imposing a consistent lock acquisition order.

The C++ account example uses `std::scoped_lock` for simultaneous locking. The Java account example explicitly derives a stable ordering from account identifiers. The Python transfer example sorts accounts before acquiring either lock.

Lock ordering is a design rule, not a substitute for understanding the state model. A system with many independently acquired locks should document ownership and acquisition relationships.

## Semaphore

A semaphore maintains a permit count.

A mutex can be viewed conceptually as a special case where only one participant may own the protected resource. A counting semaphore allows several participants to proceed simultaneously while enforcing an upper bound.

The Python connection-pool example creates a semaphore with a capacity of three. Ten workers may request access, but no more than three can use the simulated resource concurrently.

The Java build service uses a `Semaphore` to model compiler licenses. Four worker threads can exist, but only two can compile simultaneously because only two licenses are available.

The Java semaphore is configured as fair. Fairness can reduce starvation in workloads where requests should receive permits in approximately arrival order, although fairness can introduce scheduling overhead and reduce throughput.

The C++17 program cannot use `std::counting_semaphore`, because that standard facility belongs to C++20. It therefore implements semaphore semantics with a mutex, condition variable, and integer permit count.

The SQL implementation models permits as rows. A worker locks an available permit row and assigns it to a task. `FOR UPDATE SKIP LOCKED` allows competing workers to search for different available permits without waiting behind rows another worker has already claimed.

A semaphore is appropriate for:

- database connection limits
- compiler or license capacity
- API concurrency limits
- worker pool capacity
- bounded access to expensive hardware
- a limited number of simultaneous file-processing operations

A semaphore is not automatically a replacement for a mutex. If the purpose is protecting one mutable object, a mutex expresses the intent more clearly.

## Condition variables

A condition variable allows an execution context to sleep until shared state may have changed.

The important relationship is:

`mutex + condition variable + predicate`

A condition variable by itself does not describe correctness.

For a consumer waiting for a queue item, the predicate is:

`queue is not empty`

The consumer should wait while the predicate is false.

The Python implementation uses:

`while not self._queue: self._condition.wait()`

The Java implementation uses a `Condition` associated with a `ReentrantLock` and separately maintains `notEmpty` and `notFull` conditions.

The C++ build queue uses `std::condition_variable` with predicates passed to `wait`.

The predicate must be checked again after waking because notification does not guarantee that the desired state remains true. Another thread may consume the resource first, or a spurious wakeup may occur.

This is why condition waits should normally use a loop rather than a single `if`.

## Monitors

A monitor is a higher-level synchronization abstraction in which shared state and the operations that protect that state are encapsulated together.

A bounded buffer is a natural monitor example.

The buffer owns:

- its queue
- its capacity
- its mutex
- its waiting conditions
- its producer operation
- its consumer operation

External callers do not manipulate the internal queue while separately deciding which lock to acquire. They call `put` or `take`, and the monitor owns the synchronization protocol.

Python's `BoundedBufferMonitor` follows this model using `threading.Condition`.

Java has direct language-level monitor semantics through `synchronized`. The `BuildJob` class uses synchronized methods to protect its state transition logic.

C++ does not have a language-level monitor keyword, so the `BuildQueueMonitor` class explicitly combines a mutex, condition variables, protected state, and synchronized operations.

The monitor design is especially valuable when an invariant depends on several fields. Keeping synchronization next to the invariant reduces the number of places where incorrect access can occur.

## Python implementation

The Python program progresses from a simple mutex-protected counter to more advanced synchronization structures.

`SafeCounter` demonstrates why a read-modify-write sequence needs exclusion.

`ConnectionPool` uses a semaphore to bound concurrent resource use. A separate mutex protects metrics because the semaphore's purpose is capacity control, not metric consistency.

`JobQueue` uses a condition variable for producer-consumer coordination.

`BoundedBufferMonitor` packages queue state, capacity, locking, and waiting behavior into one monitor-like abstraction.

`transfer` demonstrates deterministic lock ordering to avoid circular wait.

`InventoryMonitor` demonstrates `RLock`, where nested synchronized operations are legitimate because the same thread can acquire the reentrant lock more than once.

`ReadWriteLock` demonstrates a more advanced synchronization protocol in which several readers may enter simultaneously while writers receive exclusive access. Waiting writers prevent an endless stream of new readers from starving a writer.

`RateLimitedService` combines a semaphore and mutex because they solve different problems: the semaphore limits concurrent expensive operations while the mutex protects service metrics.

## JavaScript implementation

JavaScript running in a conventional single-threaded event loop has a different concurrency model from native multithreaded C++ or Java.

Node.js Worker Threads introduce genuine parallel execution contexts. `SharedArrayBuffer` allows workers to share memory, and `Atomics` provides atomic operations on that memory.

`AtomicMutex` uses `Atomics.compareExchange` to acquire ownership. `Atomics.wait` and `Atomics.notify` provide efficient coordination for worker threads.

`CountingSemaphore` uses an atomic permit count. A worker decrements a positive count atomically to acquire a permit and increments it to release one.

The JavaScript `Monitor` combines protected state with an atomic wakeup word. The queue predicate is still checked after waking, which is essential because a notification is only a reason to re-evaluate state.

The worker-thread example creates four workers that increment one shared counter. Without atomic coordination, independent read-modify-write operations could lose updates.

This implementation demonstrates why JavaScript's normal event-loop model and shared-memory worker model should not be treated as identical concurrency environments.

## C++ case study

The C++ program models a build service.

A bounded build queue receives compilation jobs from producers and feeds worker threads.

`BuildQueueMonitor` is the central monitor. Its mutex protects the queue and stopping state. `not_empty_` wakes consumers when work exists, while `not_full_` wakes producers when capacity becomes available.

`LicenseSemaphore` models a scarce compiler-license pool. Since the program targets C++17, it implements counting semaphore semantics with a condition variable rather than using the C++20 `std::counting_semaphore`.

`BuildMetrics` uses a mutex to protect counters and peak concurrency.

The worker pipeline therefore uses several synchronization mechanisms simultaneously:

`queue monitor -> semaphore acquisition -> build execution -> metrics update -> permit release`

This separation is important. The queue's synchronization answers whether work is available. The semaphore answers whether scarce compiler capacity is available. The metrics mutex answers whether one thread can safely update shared statistics.

The account-transfer portion demonstrates multiple-lock synchronization and deadlock prevention.

## Java implementation

The Java program models an enterprise repository build service.

`BuildJob` owns a state machine:

`QUEUED -> RUNNING -> SUCCEEDED`

or:

`QUEUED -> RUNNING -> FAILED`

The synchronized transition methods prevent invalid concurrent state modifications.

`BoundedBuildQueue` uses `ReentrantLock` and two `Condition` instances. `notEmpty` represents the predicate that consumers require, while `notFull` represents the predicate that producers require.

This separation is clearer than using one undifferentiated condition when different categories of waiters exist.

`CompilerLicensePool` uses `Semaphore` to constrain concurrent builds.

`BuildMetrics` uses atomic counters because the operations are simple numeric state updates and do not require a multi-field transaction.

`TransferService` uses explicit lock ordering to protect two accounts simultaneously without creating a circular acquisition dependency.

The Java example also demonstrates interruption. A worker that is interrupted while waiting or sleeping restores its interrupted status after handling the interruption. Interruption should be treated as a control signal rather than silently swallowed.

## SQL implementation

Database synchronization differs from in-memory thread synchronization because PostgreSQL coordinates concurrent database sessions and transactions.

The SQL model represents a worker pool, individual permits, tasks, synchronization events, and lock audits.

`SELECT ... FOR UPDATE` provides row-level locking. A transaction that locks a task row can safely validate and transition that task without another transaction simultaneously changing the same row.

`pg_advisory_xact_lock` provides application-defined transactional locking. It is useful when the logical resource being protected is not naturally represented by one database row.

The permit table models a counting semaphore. Each row is one available permit. A worker locks an available permit with `FOR UPDATE SKIP LOCKED` and assigns it to a task.

`SKIP LOCKED` is useful for work queues because workers can move past rows currently locked by another worker instead of blocking behind them.

The SQL script also demonstrates `SERIALIZABLE` transactions. Serializable isolation can detect conflicts that would violate serial execution, but applications must be prepared to retry transactions that PostgreSQL aborts because of serialization conflicts.

Database locks should be kept short. Holding a transaction open while performing slow external work can unnecessarily block other database sessions.

## Relationship between the mechanisms

A realistic concurrent system commonly uses more than one synchronization mechanism.

A worker service may need:

`mutex` to protect metrics

`condition variable` to wait for work

`semaphore` to limit external capacity

`monitor` to encapsulate a bounded queue

`lock ordering` to coordinate multiple protected objects

These mechanisms should not be collapsed into one generic concept.

A mutex does not inherently express resource capacity.

A semaphore does not inherently describe ownership of one mutable object.

A condition variable does not protect state by itself.

A monitor is an architectural structure built from synchronization primitives and protected state.

A lock is a broader term that can describe the synchronization mechanism used to establish exclusive access, while a mutex is a specific mutual-exclusion concept.

## Edge cases and failure conditions

### Lost updates

A shared counter can lose increments when a read-modify-write operation occurs without synchronization.

Atomic increment operations or a mutex-protected critical section solve this specific problem.

### Spurious wakeups

Condition-variable waits can return even though the desired condition is not satisfied. Always re-evaluate the predicate.

### Notification races

A notification is not a durable resource. The waiting thread must inspect shared state after waking rather than assuming that the notification guarantees the resource is still available.

### Semaphore leaks

Every successful semaphore acquisition needs exactly one release. `finally` in Python, `finally` in Java, and RAII-style scope management in C++ are effective ways to preserve this invariant.

### Deadlock

Multiple locks create dependency graphs. Stable acquisition ordering, combined lock acquisition, lock timeouts, and minimizing lock scope are practical prevention techniques.

### Starvation

A thread may wait indefinitely if other participants repeatedly acquire the same resource. Fair semaphore or lock policies can reduce starvation, but fairness can have a performance cost.

### Lock contention

Even correct synchronization can reduce throughput. Long database transactions, slow I/O inside critical sections, unnecessary shared state, and excessive lock granularity all increase contention.

### Exception paths

A synchronization resource must be released when an operation fails. Failure-safe release is part of synchronization correctness, not merely cleanup style.

## Common mistakes

A frequent mistake is protecting only part of an invariant.

For example, locking a queue during insertion but not during a size check creates a race between observing capacity and modifying the queue.

Another mistake is using a condition variable without protecting the predicate with the same synchronization mechanism.

A third mistake is treating a semaphore as a replacement for data protection. A semaphore can limit the number of participants while the shared data still requires a mutex.

Acquiring multiple locks in different orders is a common source of deadlock.

Holding locks while performing slow network or file operations increases contention and can create cascading delays.

Unlocking manually across many return paths makes exception-related leaks more likely. Scoped or context-managed ownership is generally safer.

## Performance considerations

Synchronization introduces costs:

- lock acquisition and release
- thread blocking and wakeups
- context switching
- cache-coherence traffic
- contention between workers
- database lock waits
- transaction retries under serializable isolation

The correct optimization is usually to reduce unnecessary shared mutable state before attempting sophisticated lock-free designs.

A short critical section can be more valuable than a faster lock.

A semaphore can increase throughput when expensive work has a natural capacity limit because it prevents an unbounded number of workers from competing for the same external resource.

A condition variable is generally preferable to busy-waiting when a worker has nothing useful to do.

Database `SKIP LOCKED` can improve queue throughput, but it changes ordering behavior because a locked row may be temporarily bypassed.

## Security and reliability considerations

Synchronization does not itself provide authorization or authentication.

A lock can ensure that two workers do not update the same record concurrently, but it does not determine whether a worker is allowed to update that record.

Database transactions should use the minimum privileges required by the application.

Advisory-lock keys should have a documented namespace so unrelated parts of an application do not accidentally coordinate through the same logical lock identifier.

Shared memory in JavaScript and native applications should be treated as trusted mutable state only when ownership and validation rules are clearly defined.

Timeouts are useful for detecting stalled synchronization, but a timeout should not be interpreted as proof that another participant is malfunctioning. The system should distinguish contention, cancellation, failure, and resource exhaustion.

## Debugging synchronized systems

Concurrency bugs are often nondeterministic. Reproducing the same schedule repeatedly can be difficult.

Useful diagnostic data includes:

- thread or worker identifier
- resource or lock identifier
- acquisition timestamp
- release timestamp
- wait duration
- current state
- operation name
- transaction identifier where applicable
- failure reason

The Python, C++, Java, and SQL examples record or expose enough state to reason about ownership, queue state, task state, and resource capacity.

A useful debugging question is not merely "which thread failed?" but "which synchronization invariant was violated, and which operation was allowed to observe or modify state without the required protection?"

## Production design principles

Keep ownership rules explicit.

Protect the smallest state that forms a coherent invariant.

Use the synchronization primitive whose semantics match the problem.

Prefer structured lock ownership such as Python context managers, C++ RAII, and Java `try/finally`.

Use condition predicates rather than notification counts as the source of correctness.

Bound scarce resources with semaphores or equivalent capacity controls.

Avoid holding locks during slow external operations whenever the invariant permits releasing the lock first.

For multiple locks, establish and enforce one acquisition order.

For database synchronization, keep transactions short and understand the selected isolation level.

Treat timeouts, interruption, cancellation, and failure as part of the synchronization design rather than exceptional afterthoughts.

The central design principle across all six implementations is that synchronization is correct only when the synchronization mechanism, protected state, and state-transition rules agree with one another.
