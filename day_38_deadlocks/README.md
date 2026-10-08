# Deadlocks: Conditions, Prevention, Avoidance, Detection, and Recovery

## Topic scope

A deadlock is a state in which a set of concurrent processes cannot make progress because every member of the set is waiting for a resource or condition that depends on another member of the same set.

The important distinction is between **deadlock**, **ordinary waiting**, and an **unsafe state**.

Ordinary waiting can resolve when another process releases a resource. An unsafe state means the system no longer has a guaranteed completion sequence under the assumptions used by a deadlock-avoidance algorithm. A deadlocked state is an actual progress failure in which the relevant dependency cycle prevents the involved processes from completing.

This repository models the classical resource-allocation problem and separates four related mechanisms:

- **Prevention** changes resource-acquisition rules so at least one necessary deadlock condition cannot occur.
- **Avoidance** evaluates a proposed allocation before granting it and permits the allocation only when the resulting state remains safe.
- **Detection** allows resource dependencies to develop and periodically determines whether the current dependency structure contains a deadlock.
- **Recovery** restores progress after detection by releasing resources, aborting work, rolling back work, or using another system-specific recovery policy.

The implementations use the same conceptual foundation but deliberately approach it from different programming perspectives.

## Core deadlock conditions

The classical Coffman conditions identify four conditions that must coexist for a traditional resource deadlock.

### Mutual exclusion

A mutually exclusive resource can be held by only one process at a time.

A database connection represented as a single logical resource, an exclusive file lock, or a single device reservation can create this condition. If several processes require the same non-shareable resource, one process can hold it while another waits.

Removing mutual exclusion is possible only when the resource can safely be shared. Read-only data is often shareable, while a resource that requires exclusive modification is not.

### Hold and wait

A process is holding at least one resource while waiting for another resource.

For example, `BillingTransaction` may hold `DatabaseConnection` while waiting for `AuditLock`. If another transaction holds `AuditLock` and waits for the database connection, the two allocations become mutually dependent.

A prevention policy can remove hold and wait by requiring a process to request all required resources before beginning execution, or by requiring a process to release currently held resources before requesting additional resources. These policies can reduce concurrency and resource utilization, so they are design trade-offs rather than universally optimal solutions.

### No preemption

The system cannot simply take a resource away from its current holder.

Preemption is straightforward for some resources and unsafe or impossible for others. CPU time is routinely preempted by operating systems, while forcibly taking a partially updated application-level lock may corrupt a logical transaction.

A recovery strategy therefore needs to understand the resource type. Releasing an ordinary memory buffer may be different from rolling back a transaction that owns a database lock.

### Circular wait

Processes form a cycle of dependencies.

A simple cycle is:

`P1 -> P2 -> P1`

where `P1` waits for a resource held by `P2`, while `P2` waits for a resource held by `P1`.

Longer cycles are possible:

`P1 -> P2 -> P3 -> P1`

Circular wait is particularly useful for detection because a wait-for graph can represent processes as vertices and waiting dependencies as directed edges.

## Resource-allocation model

The implementations distinguish three important quantities.

| Quantity | Meaning |
|---|---|
| Capacity | Total instances of a resource owned by the system |
| Allocation | Instances currently assigned to a process |
| Maximum claim | Maximum number of instances the process may require |
| Remaining need | Maximum claim minus current allocation |
| Available | Capacity minus active allocations |

The distinction between maximum claim and current allocation is essential for Banker's algorithm.

For example, if a process has a maximum claim of five database connections and currently owns two, its remaining need is three. An avoidance algorithm evaluates whether granting additional resources still permits all active processes to reach completion.

## Pulling the conditions together

Consider two single-instance resources:

`DatabaseConnection`

`AuditLock`

Suppose:

`BillingTransaction` holds `DatabaseConnection` and waits for `AuditLock`.

`AuditTransaction` holds `AuditLock` and waits for `DatabaseConnection`.

Both resources are exclusive. Each transaction holds one resource while waiting for another. Neither resource is forcibly reclaimed. The wait-for graph contains a cycle.

The four conditions therefore coexist, and the system has a deadlock.

This example is deliberately different from ordinary resource contention. If `BillingTransaction` simply waited for an available resource with no cycle, the condition would be waiting rather than deadlock.

# Python implementation

The Python program implements a reusable `ResourceSystem` with explicit resource capacity, process maximum claims, allocations, waiting requests, process states, safety testing, cycle detection, and recovery.

`Resource`, `Process`, and `ResourceSystem` separate domain data from resource-management behavior. The `Process.need()` method calculates remaining claims directly from maximum allocation and current allocation.

The `request()` method demonstrates an important distinction between immediate availability and safe allocation. A request can be immediately satisfiable yet still be rejected when safety checking is enabled because granting it could remove every future completion sequence.

The Banker's safety algorithm uses a working copy of available resources. It repeatedly finds a process whose remaining need can be satisfied by the current work vector. When that process is hypothetically completed, its allocated resources are returned to the work vector. If every active process can be placed into such a sequence, the state is safe.

The Python wait-for graph is derived from waiting resources and their current holders. Depth-first traversal identifies cycles. Recovery aborts a selected process, clears its allocations, and makes those resources available again.

The example recovery policy selects a victim with comparatively low allocation. This is intentionally only a policy example. Production systems may consider transaction priority, rollback cost, elapsed execution time, resource consumption, business criticality, or restart cost.

The validation logic also demonstrates failure handling for invalid capacities, excessive requests, unknown resources, allocations beyond maximum claims, and invalid releases.

## Python-specific implementation decisions

Python dictionaries represent resource vectors naturally because resource names are meaningful keys. Sets represent graph dependencies and detected cycle members efficiently.

Dataclasses make resource and process state explicit without introducing unnecessary framework dependencies.

The program uses only the standard library, making the simulation executable without installation of third-party packages.

# JavaScript implementation

The JavaScript implementation approaches the same domain as an event-driven resource manager.

`ResourcePool` owns resource capacity and availability. `Job` owns maximum claims, current allocation, and process state. `DeadlockManager` coordinates requests, safety evaluation, wait-for graph construction, detection, and recovery.

The event-emitter design is a deliberate JavaScript-specific choice. Allocation, waiting, unsafe-request rejection, resource release, completion, and recovery can be observed as domain events. This resembles an application service that emits operational events to logging, monitoring, or audit consumers.

`Map` and `Set` are used instead of ordinary objects for resource vectors and graph edges because they provide explicit key/value and membership semantics suitable for dynamic resource names.

The asynchronous demonstration uses a promise boundary to resemble independently scheduled work units while retaining deterministic resource ownership inside the manager.

The JavaScript program also demonstrates the distinction between a request being unavailable now and a request being rejected by avoidance. An unavailable request enters a waiting state. An avoidance rejection means the resources may exist now but granting them would make the resulting allocation unsafe.

The resource-ordering example demonstrates prevention. The safety evaluator demonstrates avoidance. The wait-for graph demonstrates detection. The recovery method demonstrates resource release after a detected cycle.

# C++ case study

The C++ program presents a resource-governance engine suitable for a system where concurrent transactions compete for scarce exclusive resources.

The `Process` structure stores a maximum claim, allocation, and lifecycle state. `GovernanceEngine` owns capacities, processes, waiting relationships, allocation validation, safety analysis, wait-for graph construction, cycle detection, and recovery.

The C++ implementation uses ordered associative containers so diagnostic output remains deterministic. `std::map` represents resource vectors, while `std::set` represents active process collections and dependency edges.

The `safeAfter()` method performs a hypothetical allocation and then evaluates the resulting state. This illustrates the central idea of avoidance: the system does not merely ask whether resources are available; it asks whether the proposed allocation preserves a future completion sequence.

The wait-for graph is derived from resource ownership and waiting relationships. A directed edge from one process to another means that the first process is blocked by a resource held by the second.

Depth-first traversal identifies cycles. A cycle is significant because each participant depends on another participant in the cycle.

The recovery case aborts a selected process. Its allocations are removed, allowing the resources to return to the available pool. A real system would use a more sophisticated victim-selection policy because terminating arbitrary work can be expensive.

The C++ implementation uses no external library and is designed for C++17 or later.

# Java implementation

The Java program presents deadlock management as an enterprise domain service.

`ResourcePool` encapsulates resource capacity and available units. `Job` represents a managed execution unit with a maximum claim, allocation, and explicit `ProcessState`. `DeadlockEngine` implements request validation, safe-state evaluation, wait-for graph construction, cycle detection, completion, and abort-based recovery.

The domain state is represented explicitly rather than encoded through print statements. This makes invalid transitions easier to identify and provides a structure that can be adapted to service-layer applications.

The Java implementation uses `Map.copyOf()` when exposing snapshots so callers cannot directly mutate the internal resource maps through returned views.

`safeAfter()` demonstrates transactional-style reasoning at the application layer. The proposed allocation is temporarily applied, evaluated, and then restored. The real allocation is not committed unless the safety decision permits it.

The state model distinguishes `READY`, `RUNNING`, `WAITING`, `COMPLETED`, and `ABORTED`. This is useful because a process that is waiting is not automatically deadlocked, and an aborted process should no longer contribute its allocation to the active resource system.

The implementation also separates policy from mechanism. The engine provides detection and recovery mechanisms, while a production application could choose a victim based on business-specific rules.

# SQL data model

The PostgreSQL-compatible SQL script represents the logical deadlock domain relationally.

The principal entities are:

- `resources` stores resource capacities.
- `processes` stores execution units and their lifecycle states.
- `maximum_claims` stores maximum resource requirements.
- `allocations` stores resources currently held.
- `resource_requests` records outstanding resource requests.
- `wait_for_edges` represents process-to-process dependencies.
- `deadlock_events` records detected deadlocks.
- `recovery_actions` records the selected recovery action and victim.

Foreign keys prevent references to resources or processes that do not exist. Check constraints prevent negative capacities, negative allocations, invalid process states, and invalid request quantities.

The primary keys on allocation and maximum-claim tables prevent duplicate rows for the same process/resource relationship.

## Available-resource calculation

The `available_resources` view computes:

`available = capacity - active allocations`

Aborted processes are excluded from active allocation totals because recovery releases their resources.

This view allows the database to expose the current resource state without duplicating available counts as independently mutable data.

## Remaining-need calculation

The `remaining_need` view calculates:

`remaining need = maximum claim - current allocation`

This is the relational equivalent of the resource vector used by Banker's algorithm.

The view is useful for identifying processes that both hold resources and still require additional resources. Those processes are directly relevant to hold-and-wait analysis.

## Wait-for representation

`wait_for_edges` explicitly records relationships such as:

`BillingTransaction -> AuditTransaction`

The relationship means that `BillingTransaction` is waiting for a resource currently held by `AuditTransaction`.

This representation is distinct from a resource request itself. A request says what resource is wanted. A wait-for edge says which process currently blocks that request.

That distinction becomes important when a resource has multiple instances or when resource ownership changes.

## SQL cycle detection

The recursive common table expression traverses wait-for edges and carries the visited path in an array.

When a traversal encounters a process already present in its path, the dependency has returned to an earlier node. That provides relational evidence of a cycle.

The query is intentionally based on the wait-for graph rather than merely counting waiting processes. A large number of waiting processes does not prove deadlock. The dependency topology matters.

## Database-level integrity

The schema uses database constraints for rules that should remain true regardless of application behavior.

Negative allocations are rejected by `CHECK` constraints. Unknown processes and resources are rejected by foreign keys. Duplicate process/resource allocation records are rejected by composite primary keys.

Indexes on process, resource, request, and wait-for relationships support the principal investigation paths used by deadlock monitoring.

The script does not pretend that ordinary relational constraints can replace deadlock algorithms. Constraints preserve valid data; detection and avoidance require reasoning about relationships and future states.

# Prevention

Deadlock prevention works by ensuring that at least one Coffman condition cannot arise.

## Resource ordering

The most explicit prevention strategy demonstrated by the programs is global resource ordering.

Suppose:

`DatabaseConnection < AuditLock`

Every process must acquire resources in ascending order.

A process may acquire `DatabaseConnection` and then request `AuditLock`, but it may not hold `AuditLock` and request `DatabaseConnection`.

If every process obeys the ordering rule, a cycle cannot exist because every dependency follows the same increasing direction. A hypothetical circular dependency would require resource ordering to eventually decrease, contradicting the acquisition rule.

The trade-off is that applications must know and consistently enforce the ordering. In a large system with dynamically discovered locks, maintaining a reliable global order can require careful architectural discipline.

## Eliminating hold and wait

Another prevention strategy is to acquire all required resources before beginning the critical operation.

This removes the situation in which a process holds one resource while waiting for another.

The cost is potentially poor resource utilization. A process may reserve resources it does not immediately need, preventing other processes from using them.

## Preemption

Where resource semantics permit safe preemption, a system can reclaim a resource from a waiting process or force a rollback.

This is more complicated for resources representing partially completed work. Preempting a CPU time slice is routine. Preempting a transaction that has modified shared state may require rollback and recovery.

## Avoidance

Avoidance does not prohibit all potentially dangerous allocation patterns.

Instead, it requires enough information to evaluate whether a proposed allocation leaves the system in a safe state.

Banker's algorithm relies on known maximum claims. A safety test does not predict exactly what the processes will do. It asks whether there exists at least one completion sequence under the declared maximum claims.

A safe sequence is therefore a proof of possible progress, not a prediction of actual execution order.

# Detection

Detection is appropriate when prevention is too restrictive or avoidance requires information that the system cannot reliably obtain.

A common detection representation is the wait-for graph.

Each node represents a process. An edge:

`P1 -> P2`

means that `P1` cannot proceed because it requires something currently held by `P2`.

For a system of single-instance resources, a directed cycle is sufficient to identify a deadlock.

For multiple-instance resource types, detection is more involved. A cycle in a generalized dependency graph can indicate a dependency problem without always proving that every process is permanently deadlocked. Algorithms therefore need to account for resource counts and outstanding requests.

The implementations focus on the single-instance wait-for interpretation for clear cycle demonstration and use Banker's safety reasoning for the multiple-resource avoidance case.

# Recovery

Detection answers whether a deadlock exists. Recovery answers how the system returns to progress.

## Process termination

The simplest modeled recovery method is to abort a selected process and release its resources.

The choice of victim matters. Useful policy inputs include:

- Amount of work already completed.
- Number and type of resources held.
- Estimated restart cost.
- Transaction priority.
- Business criticality.
- Rollback complexity.
- Number of other processes that become unblocked.
- Historical victim frequency.

Always selecting the same low-priority process can cause starvation, so production recovery policies should account for repeated victim selection.

## Resource release and rollback

A more controlled recovery strategy can roll back a transaction to a safe checkpoint, release resources, and retry it later.

This can preserve more completed work than terminating the process completely, but it requires checkpointing or transactional rollback semantics.

The SQL recovery example models process abortion and allocation release atomically in a transaction. The transaction ensures that the logical state change and recovery record are committed together.

# Prevention, avoidance, detection, and recovery compared

| Mechanism | Primary question | Typical information required | Main trade-off |
|---|---|---|---|
| Prevention | How can a necessary deadlock condition be made impossible? | Resource-acquisition rules | Can restrict concurrency |
| Avoidance | Is this allocation safe before granting it? | Current allocation, available resources, maximum claims | Requires accurate maximum-claim information |
| Detection | Is a deadlock present now? | Current wait/dependency state | Deadlock may already have stopped progress |
| Recovery | How can progress be restored? | Deadlock participants and recovery policy | Work may be lost or rolled back |

These mechanisms are complementary rather than interchangeable.

A system can use prevention for lock ordering, avoidance for scarce resources with known claims, detection for unexpected dependency cycles, and recovery for cases that still reach an unrecoverable state.

# Edge cases and failure modes

A process waiting for a resource is not automatically deadlocked.

For example, if `P1` waits for a resource held by `P2` and `P2` will complete without needing anything from `P1`, the wait can eventually resolve.

A dependency chain becomes a deadlock when progress is blocked by a closed dependency structure or by an equivalent resource-allocation condition.

Another important edge case is an unsafe state without an immediate deadlock. Banker's algorithm can reject an allocation because it would destroy every known safe completion sequence even though all processes are currently capable of continuing. Avoidance is deliberately conservative because it protects future progress rather than waiting for an actual cycle to form.

Resource counts also matter. With one instance of each resource, a cycle in the wait-for graph has a direct deadlock interpretation. With multiple instances, graph structure alone may be insufficient and available-unit accounting becomes important.

Recovery can create starvation. If a process is repeatedly selected as the victim, it may never complete. A production policy should track recovery history and incorporate fairness.

# Performance considerations

For a resource-allocation system with `P` processes and `R` resource types, a straightforward Banker's safety check repeatedly examines process needs against available resources. Its practical cost is approximately proportional to repeated `P × R` comparisons, with additional work for the completion sequence.

Wait-for graph cycle detection using depth-first traversal is approximately `O(V + E)` for `V` processes and `E` dependency edges.

The relational implementation adds indexing because detection workloads frequently filter by process and resource. Recursive SQL traversal can become expensive for large dependency graphs, so production systems may maintain a specialized dependency representation or perform graph analysis in an application or dedicated monitoring service.

Deadlock checks should also consider frequency. Continuous detection provides faster reaction but consumes more resources. Periodic detection reduces monitoring overhead but permits a deadlock to persist longer.

# Security and reliability considerations

Deadlock-management data can reveal operational information such as which processes own locks, which transactions are blocked, and which resources are scarce.

Access to diagnostic information should therefore be controlled. A wait-for graph can expose internal workload relationships that may be inappropriate for ordinary users.

Recovery operations should require stronger authorization than read-only detection. Aborting a process or releasing a logical allocation can cause data loss or transaction rollback.

Recovery actions should be auditable. The SQL model therefore records the deadlock event, selected victim, action, and execution time.

Application-level deadlock detection must not assume that its logical model is perfectly synchronized with the underlying operating system, database, distributed lock manager, or runtime. The source of truth for actual resource ownership must be clearly defined.

# Common mistakes

Confusing waiting with deadlock is a frequent modeling error. Waiting becomes deadlock only when the dependency structure prevents the involved processes from making progress.

Treating a safe state as a guaranteed execution schedule is also incorrect. A safe sequence proves that at least one completion sequence exists under the model. It does not dictate the actual scheduler's order.

Using resource ordering inconsistently defeats prevention. Every participant that can acquire the resources must obey the same ordering policy.

Assuming that a cycle always proves deadlock in a multiple-instance resource system can produce false positives. Resource counts and outstanding requests must be considered.

Detecting a deadlock without a recovery policy leaves the system unable to make progress. Detection and recovery should therefore be designed together when the system permits deadlocks by design.

Selecting recovery victims without fairness can create starvation.

# Production design considerations

A production implementation should establish clear ownership for resource state, define which resources are preemptible, record request and release events, and distinguish transient contention from permanent dependency cycles.

For avoidance, maximum claims must be meaningful. If a process declares an unrealistically high maximum, safe-state analysis may reject allocations unnecessarily. If it declares too low a maximum, the model cannot correctly represent the process's real behavior.

For prevention, resource ordering should be documented as a system invariant and enforced close to the resource-acquisition API rather than relying only on developer discipline.

For detection, the monitoring system should retain enough information to reconstruct why each process is waiting and which process currently holds the blocking resource.

For recovery, victim selection should be deterministic enough to audit but flexible enough to consider business impact and starvation.

The central engineering distinction remains:

**Prevention controls the rules before a deadlock can form. Avoidance evaluates future safety before granting resources. Detection identifies an existing dependency problem. Recovery restores progress after the problem has been detected.**
