# Synchronization Fundamentals

## Scope

This module focuses on three closely related but distinct concurrency concepts:

- **Race conditions** describe incorrect behavior caused by timing or interleaving between concurrent operations that access shared state.
- **Critical sections** are regions of execution in which shared state is read, validated, or modified and therefore requires coordinated access.
- **Mutual exclusion** is the synchronization property that prevents competing execution contexts from entering the same protected critical section at the same time.

The relationship is causal rather than synonymous. A race condition is a failure mode. A critical section identifies the sensitive operation. Mutual exclusion is one mechanism for preventing competing executions from simultaneously entering that operation.

The implementations use realistic shared-resource scenarios such as counters, reservations, job queues, account transfers, and database inventory.

---

## Core Distinction

A shared operation is dangerous when its correctness depends on several steps being treated as one indivisible operation.

Consider an inventory reservation:

`if stock >= requested_quantity: stock = stock - requested_quantity`

The logical operation contains both a **check** and a **state transition**. If two workers can perform the check independently before either performs the update, both workers can believe that enough inventory exists.

The important unit is therefore not an individual assignment. It is the complete invariant-preserving operation.

### Race condition

A race condition occurs when the result depends on an uncontrolled ordering of concurrent operations.

For a shared counter, the operation:

`counter = counter + 1`

is logically a read-modify-write sequence. Conceptually:

`old_value = counter`

`new_value = old_value + 1`

`counter = new_value`

Two workers can read the same `old_value`. Both calculate the same `new_value`, and one update can overwrite the other.

### Critical section

A critical section is the portion of execution that accesses shared state under a synchronization requirement.

For an inventory system, a critical section may include:

`read available stock -> verify requested quantity -> decrement stock -> record reservation`

Moving only the decrement behind a lock is insufficient if another worker can perform the validation outside the protected region.

### Mutual exclusion

Mutual exclusion ensures that only one execution context at a time enters a particular protected region.

A mutex, lock, monitor, or equivalent synchronization primitive can provide this property.

Mutual exclusion does not automatically make an entire program correct. The protected region must cover the right state transitions, locks must be acquired and released correctly, and multiple locks require a strategy that avoids deadlock.

---

## Python Implementation

The Python program uses `threading` to model concurrent workers.

The unsafe counter intentionally separates the read and write operations and inserts a scheduling opportunity between them. The resulting lost updates illustrate a race condition.

The protected counter uses `threading.Lock` with a `with` statement. The context manager is important because it releases the lock even when an exception occurs inside the critical section.

The inventory example moves the complete check-and-update operation behind the lock. This preserves the invariant that the quantity cannot become negative because of competing reservations.

The `RLock` example demonstrates reentrant mutual exclusion. A normal `Lock` cannot be acquired twice by the same thread without first being released. `RLock` is appropriate when nested calls legitimately need to enter the same synchronization boundary.

The bank example introduces multiple locks. Transfers acquire both account locks in a deterministic order. Without a consistent ordering strategy, opposing transfers can create a circular wait:

`A locked -> waiting for B`

while another thread has:

`B locked -> waiting for A`

The Python program also demonstrates lock acquisition timeouts and the performance cost of protecting shared work.

### Python-specific design choices

`threading.Lock` is appropriate for protecting shared mutable state between Python threads.

The `with lock:` form is preferred over manually calling `acquire()` and `release()` because exception-safe release is built into the context manager.

A lock should normally protect the smallest complete critical section that preserves the required invariant. Making the critical section unnecessarily large increases contention.

---

## JavaScript Implementation

JavaScript requires a different synchronization perspective.

Normal JavaScript execution in Node.js uses an event loop. JavaScript callbacks are not simultaneously executing on multiple event-loop threads, but asynchronous operations can still interleave logically.

The asynchronous withdrawal example demonstrates this distinction:

`check balance -> await -> update balance`

The `await` yields execution. Another operation can run between the check and the update. Consequently, single-threaded JavaScript can still experience a logical race condition.

The custom `AsyncMutex` serializes asynchronous critical sections. A waiting operation is represented by a promise resolver rather than by blocking an operating-system thread.

The implementation uses `finally` when releasing the mutex. This prevents an exception from leaving the mutex permanently locked.

The JavaScript implementation also uses Node.js `worker_threads` and `SharedArrayBuffer` to demonstrate actual shared-memory concurrency. `Atomics.add()` provides an atomic read-modify-write operation for the shared counter.

This creates an important distinction:

- Event-loop concurrency can create logical races through asynchronous interleaving.
- Worker threads can introduce actual concurrent access to shared memory.
- `Atomics` provide synchronization primitives for selected shared-memory operations.

The JavaScript program therefore does not simply translate the Python mutex example. It demonstrates the concurrency model specific to asynchronous JavaScript and Node.js shared memory.

---

## C++ Repository Job Scheduler Case Study

The C++ implementation models a repository-analysis job scheduler.

A scheduler contains shared resources such as:

- pending jobs
- shutdown state
- worker counters
- account-like resource balances
- shared service state

The `UnsafeCounter` demonstrates a classic unsynchronized read-modify-write race.

`SafeCounter` uses `std::mutex` and `std::lock_guard`. The guard follows RAII: acquiring the lock is associated with an object whose destructor releases it. This makes exception-safe synchronization a normal part of the C++ object lifetime model.

### Producer-consumer critical section

`JobQueue` contains:

- a shared queue
- a mutex protecting the queue
- a condition variable for worker coordination
- a shutdown state

A producer modifies the queue while holding the mutex and then notifies a consumer.

A consumer waits using `std::unique_lock` and `condition_variable::wait`.

The wait predicate checks:

`queue is not empty OR scheduler is shutting down`

The predicate is necessary because condition-variable wakeups do not themselves guarantee that the desired state is true when the waiting thread resumes.

### Multiple resources

The bank example models a transfer requiring two account locks.

`std::scoped_lock` is used to acquire both mutexes safely. The implementation does not manually lock account A and then account B in one location while another operation does the reverse.

The total balance remains invariant because the transfer protects both accounts during the state transition.

### Atomic operations

The atomic counter demonstrates a case where a full mutex is unnecessary.

`std::atomic<int>::fetch_add()` provides an atomic increment. Atomic operations are appropriate when the required synchronization is limited to a value-level operation.

An atomic counter does not replace a mutex for arbitrary multi-variable invariants. If an operation must update several related objects consistently, protecting the entire invariant may still require a lock or another transaction-like mechanism.

---

## Java Enterprise Reservation Model

The Java program models an enterprise reservation service.

The domain uses explicit types such as `ReservationStatus`, `ReservationService`, `JobQueue`, and `Account`.

`ReservationService` uses `ReentrantLock` to protect the critical section containing:

`capacity check -> capacity decrement`

This is a complete state transition. Releasing the lock between those operations would reintroduce the race condition.

The lock is released in a `finally` block. This is essential because an exception must not leave the service permanently locked.

### Condition-based coordination

`JobQueue` uses a `Condition` associated with a `ReentrantLock`.

A consumer waits while the queue is empty and the service is still running.

The state is checked in a loop rather than with a single conditional statement. This handles spurious wakeups and state changes caused by other threads.

Shutdown calls `signalAll()` so that waiting consumers can observe the new terminal state instead of remaining blocked.

### Multi-account synchronization

Account transfers require two locks.

The implementation orders the locks by account identifier before acquiring them. Every transfer therefore follows the same ordering rule.

This prevents the circular-wait pattern that commonly produces deadlocks.

### Timed acquisition

`tryLock` with a timeout gives the caller a bounded wait. This can be preferable in systems where indefinite blocking would prevent recovery or consume scarce worker capacity.

Timed acquisition does not eliminate the underlying contention. It changes the failure behavior from indefinite waiting to an explicit timeout path.

### Atomic state

`AtomicInteger` is used for a counter where the required operation is a single atomic increment.

This demonstrates an important design decision: use the least complicated synchronization mechanism that can actually preserve the required invariant.

---

## SQL Concurrency Model

The SQL implementation uses PostgreSQL because database synchronization has different semantics from in-process thread synchronization.

The relational model contains:

- `products` for shared inventory state
- `reservation_requests` for reservation attempts
- `reservation_events` for state history

The product's `stock_quantity` has a `CHECK` constraint preventing negative stored values.

The reservation request references its product through a foreign key, and status values are restricted to the supported lifecycle states.

### Atomic conditional update

The statement:

`UPDATE products SET stock_quantity = stock_quantity - 15 WHERE ... AND stock_quantity >= 15`

combines the eligibility predicate and state transition into one database operation.

This is fundamentally different from:

`SELECT stock_quantity`

followed later by an independent update.

The second pattern exposes a larger race window unless additional transaction synchronization is used.

### Row-level critical section

The `reserve_inventory` function uses:

`SELECT ... FOR UPDATE`

The selected product row becomes locked for the transaction.

The reservation workflow then performs:

`read stock -> validate quantity -> decrement stock -> create reservation -> create event`

while the product row is protected.

A competing transaction attempting to lock the same product must wait until the current transaction completes.

This is database-level mutual exclusion for the selected row.

### Transaction boundaries

A row lock is meaningful within the transaction that acquired it.

`COMMIT` makes the transaction's changes durable and releases transaction-scoped locks. `ROLLBACK` abandons the transaction's changes and also releases its locks.

This is why database synchronization cannot be understood independently from transaction boundaries.

### Optimistic version validation

The `version_number` column demonstrates optimistic concurrency control.

A client can update a row only when its previously observed version is still current:

`WHERE version_number = expected_version`

If another transaction has already modified the row, the update affects zero rows.

This approach detects conflicts rather than blocking competing writers.

### Advisory locks

`pg_advisory_xact_lock` provides a synchronization mechanism for application-defined resources that may not correspond naturally to a database row.

The lock is transaction-scoped and is automatically released when the transaction ends.

Advisory locks require disciplined ownership of lock keys. If different application components assign unrelated meanings to the same key, the synchronization model becomes difficult to reason about.

---

## Critical-Section Boundaries

A useful way to identify a critical section is to ask which operations must observe one consistent state.

For an inventory reservation, this is not merely:

`stock = stock - quantity`

It is:

`read stock -> determine eligibility -> modify stock -> establish reservation state`

For an account transfer, the protected state includes both accounts because the invariant concerns their relationship.

For a producer-consumer queue, the protected state includes the queue and shutdown flag because consumers must make decisions using a consistent view of both.

For a database reservation, the protected resource is represented by a database row and the synchronization mechanism is implemented by transaction locking or an atomic statement.

---

## Race Conditions That the Implementations Address

### Lost update

Two workers read the same value and both write derived values. One update overwrites another.

The counter examples demonstrate this directly.

### Check-then-act race

A worker checks whether a resource is available and later consumes it. Another worker can change the resource between those operations.

The reservation examples treat the check and mutation as one critical section.

### Inconsistent multi-resource state

An operation updates multiple related resources. Another thread can observe or modify only part of the state while the operation is in progress.

The account transfer examples protect both accounts.

### Queue state race

A consumer checks an empty queue and goes to sleep while a producer modifies the queue. Condition variables coordinate this transition without requiring busy waiting.

### Asynchronous logical race

JavaScript's event loop avoids simultaneous execution of ordinary JavaScript callbacks, but `await` creates scheduling points. State can change before a continuation resumes.

The JavaScript async mutex addresses this specific form of race.

---

## Mutual Exclusion Mechanisms Used

| Environment | Mechanism | Protected behavior |
| --- | --- | --- |
| Python | `threading.Lock` | Shared counters, inventory, account state |
| Python | `threading.RLock` | Nested acquisition by one thread |
| JavaScript | Async mutex | Asynchronous check-and-update workflow |
| Node.js | `Atomics` | Shared-memory atomic increments |
| C++ | `std::mutex` | Shared object state |
| C++ | `std::scoped_lock` | Multiple mutexes |
| C++ | `std::condition_variable` | Coordinated queue access |
| Java | `synchronized` | Object-level mutual exclusion |
| Java | `ReentrantLock` | Explicit lock ownership and conditions |
| Java | `AtomicInteger` | Atomic counter mutation |
| PostgreSQL | `SELECT ... FOR UPDATE` | Row-level critical section |
| PostgreSQL | Atomic `UPDATE` | Conditional state transition |
| PostgreSQL | Advisory lock | Application-defined resource synchronization |

The mechanisms are not interchangeable. A database row lock coordinates transactions against database state, while an in-process mutex coordinates threads inside a process.

---

## Deadlock Considerations

Mutual exclusion can introduce a new class of failure: deadlock.

A deadlock can occur when operations hold resources while waiting for resources held by other operations.

The classic pattern is:

`Thread A: lock resource 1 -> wait for resource 2`

`Thread B: lock resource 2 -> wait for resource 1`

The C++ and Java account examples avoid this by imposing a deterministic lock ordering.

Other strategies include reducing lock scope, using combined lock acquisition facilities, using timed lock acquisition, or redesigning the shared-state model.

Mutual exclusion therefore solves one class of concurrency problem while potentially creating another if synchronization is poorly designed.

---

## Performance Implications

A lock has a cost.

Threads may contend for the same lock, and waiting threads may spend time blocked rather than doing useful work.

A large critical section also reduces concurrency. If expensive computation, network calls, or unrelated processing occurs while holding a lock, other workers may be unnecessarily prevented from accessing the protected resource.

The implementations therefore keep the synchronization boundary around the state transition that actually requires protection.

Atomic operations can be cheaper than a mutex for simple independent counters, but atomic operations do not automatically protect compound invariants.

A database row lock can also serialize transactions. Good relational design therefore combines appropriate indexes, short transactions, atomic statements, and carefully chosen isolation behavior.

---

## Error Handling and Failure States

Synchronization must remain correct when operations fail.

Python uses context managers so locks are released automatically.

Java uses `finally` around explicit lock ownership.

C++ uses RAII lock objects whose destructors release locks.

JavaScript's async mutex releases its ownership from a `finally` block.

PostgreSQL transaction-scoped locks are released when the transaction commits or rolls back.

These patterns address an important failure mode: a lock acquired successfully but never released.

An exception-safe synchronization boundary is part of correctness, not merely a coding convenience.

---

## Common Mistakes

### Protecting only the write

Protecting `balance -= amount` while leaving the balance check outside the critical section does not protect the complete invariant.

### Locking unrelated work

A lock should not normally cover slow network operations, lengthy computation, or unrelated processing when that work does not require shared-state protection.

### Assuming single-threaded means race-free

Asynchronous JavaScript can still have logical races because execution can interleave at `await` points.

### Assuming atomics solve every concurrency problem

An atomic counter can protect one integer operation. It does not automatically make a sequence involving several objects atomic.

### Acquiring multiple locks inconsistently

Different lock orders can create circular wait and deadlock.

### Ignoring interruption and shutdown

Worker systems need explicit shutdown behavior. The C++ and Java queue examples make shutdown part of the synchronized state.

### Forgetting transaction scope

A PostgreSQL row lock does not remain indefinitely. Its lifetime is tied to the transaction.

---

## Debugging Synchronization Problems

Concurrency bugs can disappear when debugging changes timing.

Useful evidence includes:

- thread or worker identifiers
- timestamps around lock acquisition and release
- operation identifiers
- resource identifiers
- transaction identifiers
- expected and observed state
- lock wait durations
- failed optimistic version checks

A useful diagnostic record for an inventory operation is:

`request_id, product_id, worker_id, observed_stock, requested_quantity, lock_acquired_at, update_result`

The goal is to reconstruct the ordering of events rather than only inspect the final incorrect value.

Deterministic tests are difficult for concurrency bugs because scheduling is nondeterministic. Tests should therefore exercise shared invariants repeatedly and verify final state as well as individual operation outcomes.

---

## Database Integrity Versus Application Synchronization

A database constraint and a synchronization mechanism solve different problems.

A `CHECK (stock_quantity >= 0)` constraint says that a committed row cannot contain negative inventory.

It does not by itself define how two application transactions should coordinate a multi-step reservation workflow.

The synchronization strategy determines how competing transactions safely perform the transition.

The strongest design places important invariants at the database layer while also designing application workflows around correct transaction boundaries.

---

## Practical Invariants

The examples rely on explicit invariants.

For the counter:

`final_counter = initial_counter + successful_increments`

For inventory:

`stock_quantity >= 0`

For an account transfer:

`source_balance + target_balance` remains constant, assuming no external deposits or withdrawals.

For the job queue:

A job is removed only after it has actually been inserted, and shutdown must not strand consumers waiting for work that can no longer arrive.

Making invariants explicit makes it easier to identify the exact critical section that needs synchronization.

---

## Production Considerations

Synchronization should be designed around the ownership and lifetime of shared state.

For in-process state, the lock should have a clear owner and should protect a clearly defined invariant.

For asynchronous workflows, the synchronization abstraction should serialize the complete logical operation rather than merely individual callback statements.

For multi-threaded native or JVM systems, lock ordering, timeout behavior, interruption, and shutdown should be explicit architectural concerns.

For relational systems, transaction boundaries, row-level locking, atomic updates, constraints, isolation behavior, and indexes should be considered together.

The central design question is not simply whether a lock exists. It is whether every concurrent path that can violate an invariant is forced through the same synchronization boundary.

---

## Implementation Map

| File | Technical focus |
| --- | --- |
| Python | Threaded race-condition simulation, mutex-protected resources, reentrant locking, timeouts, multi-lock ordering |
| JavaScript | Event-loop races, asynchronous mutexes, `await` interleaving, worker threads, `SharedArrayBuffer`, `Atomics` |
| C++ | Threaded repository-job scheduler, mutexes, condition variables, RAII, atomic operations, multi-resource locking |
| Java | Enterprise reservation service, `synchronized`, `ReentrantLock`, `Condition`, explicit domain state, timed locking |
| SQL | PostgreSQL transactions, atomic updates, row-level locking, constraints, optimistic versioning, advisory locks |

The six artifacts treat race conditions, critical sections, and mutual exclusion as related mechanisms within a single concurrency model while preserving the technical distinction between a failure condition, a protected execution region, and the synchronization property used to protect that region.
