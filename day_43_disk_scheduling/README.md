# Disk Scheduling: FCFS, SSTF, SCAN, C-SCAN, LOOK, and C-LOOK

## Scope

Disk scheduling determines the order in which pending disk-cylinder requests are serviced. The central cost is physical head movement. A scheduling algorithm therefore does more than rearrange integers: it determines how the disk head travels through the cylinder space, how often it changes direction, whether it reaches a physical boundary, and how fairly different requests are treated.

This learning artifact treats six classical policies as distinct mechanisms:

- **FCFS** preserves arrival order and does not optimize head movement.
- **SSTF** repeatedly selects the pending request closest to the current head.
- **SCAN** moves in one direction until reaching the physical boundary, then reverses.
- **C-SCAN** services requests in one direction and returns through the boundary to restart the sweep.
- **LOOK** behaves like SCAN but reverses at the last pending request instead of traveling to the physical boundary.
- **C-LOOK** behaves like C-SCAN but wraps between the lowest and highest pending requests instead of using the physical disk boundaries.

The implementations use the same conceptual workload while deliberately presenting different engineering perspectives in Python, JavaScript, C++, Java, and PostgreSQL.

## Disk Head and Seek Movement

A disk with cylinders `0` through `199` has 200 possible cylinder positions. If the head starts at cylinder `53` and the next request is cylinder `98`, the movement is:

`|98 - 53| = 45`

If the following request is cylinder `183`, the additional movement is:

`|183 - 98| = 85`

The total movement is therefore cumulative rather than based only on the first and final positions.

For a service path `p1, p2, ..., pn` and initial head position `h`, the total movement is:

`|p1 - h| + |p2 - p1| + ... + |pn - p(n-1)|`

Average seek movement in these implementations is calculated as total movement divided by the number of serviced requests.

This metric is useful for comparing the movement characteristics of algorithms, but it does not by itself measure every operational concern. Real storage systems also care about queueing delay, request priority, device internals, caching, parallelism, workload distribution, and fairness.

## FCFS

First-Come, First-Served preserves the order in which requests entered the queue.

For the workload:

`98, 183, 37, 122, 14, 124, 65, 67`

with an initial head at `53`, FCFS services exactly that sequence.

Its important property is predictability rather than movement optimization. A request that arrives first does not lose its place because another request happens to be closer to the current head.

The Python implementation uses the original list directly after validation. The C++ implementation models the same behavior as a storage-controller operation. The SQL implementation represents the arrival order using `request_id`, allowing a relational query to reconstruct the queue order.

FCFS can generate large movements when consecutive requests are far apart. It can still be useful when preserving arrival order or simple fairness is more important than minimizing physical movement.

## SSTF

Shortest Seek Time First selects the pending request with the smallest distance from the current head.

At every decision point, the algorithm evaluates:

`abs(request_cylinder - current_head)`

The selected request becomes the new current head position, so the next decision is based on a different reference point.

The Python, JavaScript, C++, and Java implementations explicitly maintain a pending collection and repeatedly select the closest cylinder. They also use cylinder position as a deterministic tie breaker when two candidates have equal distance.

That tie-breaking rule matters. Without it, two executions can choose different requests when distances are equal, producing different service orders and potentially different downstream movement.

SSTF often reduces immediate seek distance compared with FCFS, but its local optimization can create unfairness. Requests that remain farther from the current head can wait while nearby requests repeatedly arrive.

This is a form of starvation risk. The algorithm therefore demonstrates why minimum immediate movement is not equivalent to globally optimal or fair scheduling.

## SCAN

SCAN is commonly described as an elevator-style algorithm.

The disk head moves in one direction and services requests encountered along that path. When the head reaches the physical end of the disk, it reverses direction.

For a disk containing cylinders `0..199`, a rightward SCAN operation can physically reach cylinder `199` before servicing requests on the left side of the original head position.

This physical-boundary behavior is the defining distinction between SCAN and LOOK.

The implementations keep two request groups:

- requests below the initial head position
- requests at or above the initial head position

The rightward sweep sorts the right-side requests in ascending order. After those requests, SCAN reaches the physical boundary when a reverse sweep is required, then processes the left-side requests in descending order.

A boundary cylinder is a physical movement event, not a disk request unless a request actually exists at that cylinder.

## C-SCAN

Circular SCAN maintains a preferred sweep direction.

A rightward C-SCAN sweep services requests from the current position toward the high end of the disk. It reaches the physical maximum, moves to cylinder `0`, and continues servicing requests in ascending order.

The return movement is part of the physical path even though it does not represent ordinary service in the reverse direction.

This creates a more uniform directional service pattern than ordinary SCAN in workloads where requests are continuously arriving.

The implementation therefore distinguishes between:

- the **service order**, which identifies cylinders serviced as requests
- the **physical path**, which also contains boundary and wrap movements

This distinction is particularly important when calculating total movement.

## LOOK

LOOK removes unnecessary travel to physical boundaries.

If the final request in the current direction is cylinder `183`, LOOK does not travel from `183` to `199` merely because `199` is the end of the disk. It reverses when the current direction has no more pending requests.

This can reduce movement compared with SCAN.

The critical distinction is:

`SCAN -> physical disk boundary`

`LOOK -> last pending request`

Both algorithms use directional sweeps, but their stopping conditions are different.

## C-LOOK

C-LOOK combines circular service with request-aware stopping.

A rightward C-LOOK operation services the highest pending request in the current sweep, then wraps to the lowest pending request rather than traveling to the physical maximum and minimum merely because those boundaries exist.

The physical movement associated with the circular relocation is still counted.

The distinction is:

`C-SCAN -> wrap using physical boundaries`

`C-LOOK -> wrap using request extremes`

This makes C-LOOK particularly useful for understanding why an algorithm's logical service order and physical head path should be modeled separately.

## Python Implementation

The Python program defines a `DiskScheduler` class around a validated disk geometry and initial head position.

`ScheduleResult` is an immutable data structure containing:

- algorithm name
- service order
- total movement
- average seek
- number of serviced requests

The class provides separate methods for `fcfs`, `sstf`, `scan`, `c_scan`, `look`, and `c_look`.

Validation rejects empty queues, cylinders outside the disk, invalid directions, and invalid disk configurations.

The implementation also exposes a comparison operation that evaluates all six algorithms against the same workload. This makes the movement results directly comparable without mixing algorithm-specific logic.

The Python implementation includes an interactive path, although the default execution uses a deterministic example so that the file can be run without user input.

The edge-case demonstrations explicitly exercise invalid disk size, invalid request positions, empty queues, and invalid sweep directions.

## JavaScript Implementation

The JavaScript implementation treats disk scheduling as an event-driven service.

`DiskScheduler` contains the scheduling algorithms and movement calculations. `DiskSchedulingService` adds a lightweight event layer with events such as `requests.received` and `schedule.completed`.

This structure is useful because JavaScript applications often process scheduling decisions as part of asynchronous services rather than as a single procedural calculation.

The service uses `async` behavior to create a clear asynchronous boundary without introducing an external dependency.

The implementation also separates `physicalPath` from `order`. This is important for SCAN and C-SCAN because a boundary or wrap movement can affect physical seek cost without being an ordinary request.

Validation errors are handled explicitly and propagated to the top-level `main` function.

## C++ Case Study

The C++ implementation models a storage controller.

`DiskDevice` owns disk geometry, validates requests, calculates physical movement, and implements the scheduling algorithms.

`ScheduleResult` separates service requests from the physical path. This allows SCAN and C-SCAN to include boundary movements in their movement calculation while still reporting the actual service sequence separately.

The C++ implementation uses `std::vector` for pending requests and service paths, sorting operations for directional sweeps, and a `std::map` to expose all algorithm results through a common interface.

`StoragePolicyEngine` represents a higher-level decision layer. It selects the lowest-movement result rather than embedding selection policy into an individual scheduling algorithm.

This separation is important architecturally. A scheduling algorithm should calculate its behavior. A policy engine can decide which result should be preferred under a particular operational objective.

The case study also handles invalid cylinder requests with exceptions and returns a non-zero process status for fatal failures.

## Java Enterprise Model

The Java implementation uses explicit domain types for disk scheduling.

`DiskRequest` represents an individual workload request with an external identifier, cylinder, and workload class.

`Direction` and `Algorithm` are enums rather than unrestricted strings. This prevents invalid algorithm and direction values from silently entering the domain model.

`ScheduleResult` is a record that captures the immutable result of a scheduling calculation.

`SchedulingPolicy` represents an operational movement budget. The policy contains a maximum permitted movement and a deterministic tie-breaking requirement.

`DiskController` performs scheduling and physical movement calculations.

`MergeEligibilityService` is deliberately separated from `DiskController`. It determines whether a calculated scheduling strategy satisfies the configured movement policy and then selects the lowest-movement eligible strategy.

The model therefore separates algorithm behavior from policy evaluation:

`DiskController -> calculates scheduling behavior`

`SchedulingPolicy -> defines an operational constraint`

`MergeEligibilityService -> evaluates and selects under that constraint`

This separation makes the domain easier to test and prevents policy rules from being scattered through individual algorithms.

## PostgreSQL Data Model

The SQL implementation models disk scheduling as a relational workflow.

`disks` stores physical geometry and the current head position.

`workloads` groups related requests.

`disk_requests` stores individual cylinder requests and their workload priority.

`scheduling_policies` stores movement budgets and deterministic scheduling requirements.

`scheduling_runs` records an execution of a scheduling evaluation against a workload, disk, policy, and direction.

`scheduling_results` stores the calculated outcome for each algorithm.

`scheduling_request_service` provides a normalized representation of request positions when individual service events need to be stored.

Foreign keys maintain relationships between the entities. Unique constraints prevent duplicate external request identifiers within a workload.

The `valid_head_position` constraint ensures that a disk head cannot be initialized outside the physical disk.

The request-validation trigger demonstrates a database-level integrity rule that compares incoming cylinder values with the configured disk geometry.

Indexes are applied to workload/cylinder lookup and scheduling-result movement ordering because those operations naturally support analysis of scheduling workloads.

## SQL Integrity and Transactions

The database is not treated merely as passive storage.

Constraints reject structurally invalid states. The request trigger rejects cylinder positions outside the configured disk range.

A policy update is demonstrated inside a transaction. The example performs an update and rolls it back, illustrating that policy configuration changes can be controlled atomically.

The selection query filters eligible scheduling results and chooses the lowest movement under the configured policy.

The database therefore provides three distinct responsibilities:

- store the scheduling domain
- enforce relational and numeric integrity
- support policy-oriented analysis and selection

The application implementations can perform the scheduling calculations, while PostgreSQL provides durable representation and integrity enforcement.

## Physical Path Versus Service Order

This distinction is essential for SCAN and C-SCAN.

Suppose a rightward SCAN operation has serviced its final right-side request at cylinder `183`, while there are requests on the left.

The physical path may include:

`... -> 183 -> 199 -> 122 -> 98 -> ...`

The service order should not treat `199` as a serviced request unless a request exists there. It is present because the head must reach the physical boundary before reversing.

C-SCAN can contain an even more explicit wrap:

`... -> 199 -> 0 -> 14 -> 37 -> ...`

The head physically travels through the wrap even though cylinders `199` and `0` may not themselves have been requested.

LOOK and C-LOOK remove this unnecessary boundary travel.

This is why a correct implementation should not calculate movement solely from a list containing service requests when physical boundary behavior is part of the algorithm.

## Algorithmic Characteristics

| Algorithm | Directional sweep | Uses physical boundaries | Wraps | Main characteristic |
|---|---|---:|---:|---|
| FCFS | No | No | No | Preserves arrival order |
| SSTF | Dynamic | No | No | Chooses nearest pending request |
| SCAN | Yes | Yes | No | Reverses at disk boundary |
| C-SCAN | One-way | Yes | Yes | Circular sweep using boundaries |
| LOOK | Yes | No | No | Reverses at last request |
| C-LOOK | One-way | No | Yes | Circular sweep between request extremes |

The distinction between LOOK and SCAN is boundary policy.

The distinction between C-LOOK and C-SCAN is wrap policy.

The distinction between FCFS and SSTF is request-selection policy.

The distinction between ordinary sweep algorithms and circular sweep algorithms is whether the head reverses or wraps when the current directional workload is exhausted.

## Fairness and Starvation

Movement minimization and fairness are separate objectives.

SSTF can favor requests near the current head repeatedly. If new nearby requests continuously arrive, a distant request may remain pending for a long time.

SCAN-style policies reduce this problem by giving the head a systematic directional sweep.

C-SCAN provides a more uniform directional service model because requests are considered during repeated circular sweeps rather than alternating physical directions.

No algorithm should therefore be selected solely from a single movement measurement when the production objective also includes latency or fairness.

## Tie Handling

Equal-distance SSTF candidates require a deterministic rule if repeatable results matter.

The implementations choose the lower cylinder when two candidates have equal seek distance.

Deterministic tie handling is useful for testing, reproducibility, auditing, and comparing results across implementations.

A production system could instead use request age, priority, arrival timestamp, or another explicit rule. That choice should be treated as policy rather than left to accidental collection ordering.

## Edge Cases

A correct implementation must account for situations where:

- the request queue is empty
- the initial head is at cylinder `0`
- the initial head is at the highest cylinder
- a request is exactly at the current head
- all requests lie on one side of the head
- all requests are on the other side
- duplicate cylinder positions appear
- two SSTF candidates have equal distance
- the disk contains only two cylinders
- a request lies outside the disk
- SCAN has no request on the side reached after the initial sweep
- C-SCAN requires a wrap
- LOOK can reverse without reaching a boundary
- C-LOOK must move between request extremes

A particularly important case is a request equal to the current head. Its seek contribution is zero, but it is still a valid service operation.

## Performance Considerations

FCFS can process the request list in linear time once validation is complete.

SSTF in the presented implementations performs a linear search over the remaining queue for every selection, producing approximately `O(n²)` selection work.

SCAN, C-SCAN, LOOK, and C-LOOK depend heavily on sorting. Their principal ordering work is generally `O(n log n)`.

The physical movement calculation itself is linear in the number of path elements.

The practical choice between algorithms should therefore consider both movement characteristics and implementation cost. For very large queues, data structures such as balanced trees, heaps, indexed queues, or device-specific scheduling structures can reduce selection overhead.

## Security and Reliability Considerations

Disk scheduling code should reject cylinder positions outside the configured geometry rather than allowing malformed values to reach lower layers.

Validation should occur before movement calculations.

Production systems should also protect scheduling configuration from unauthorized changes. A movement threshold, disk geometry, or algorithm selection can affect system behavior, so these values should be treated as controlled configuration.

Deterministic scheduling decisions are valuable when scheduling operations must be audited. A recorded workload, policy, algorithm, direction, and resulting movement provides a traceable decision record.

Database constraints should complement application validation rather than being treated as an optional replacement for it.

## Common Implementation Mistakes

A common error is treating SCAN as identical to LOOK. SCAN reaches the physical boundary when a reversal is required; LOOK stops at the final request in the current direction.

Another error is treating C-SCAN as merely sorted ascending requests. The physical wrap contributes movement even though the wrap itself does not represent normal request servicing.

C-LOOK is also frequently implemented incorrectly by traveling to cylinder `0` or the maximum cylinder. Its wrap is based on request extremes, not physical disk boundaries.

SSTF implementations can become nondeterministic when equal-distance candidates are not handled explicitly.

Another mistake is calculating average seek using physical-path elements rather than the number of serviced requests. Boundary positions used only for movement should not inflate the service count.

## Practical Interpretation

For the common workload with initial head `53` and requests `98, 183, 37, 122, 14, 124, 65, 67`, the six algorithms produce different movement because they make different decisions about ordering, boundaries, and direction changes.

The comparison output should be interpreted as a property of that workload, disk geometry, starting head, and direction. A lower movement result does not mean that the corresponding algorithm is universally superior.

The central engineering question is not simply:

`Which algorithm has the smallest number?`

It is:

`Which scheduling policy best satisfies the system's movement, fairness, latency, and operational constraints?`

The six implementations demonstrate that answer through different programming models while preserving the technical distinctions among FCFS, SSTF, SCAN, C-SCAN, LOOK, and C-LOOK.
