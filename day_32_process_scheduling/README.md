# Process Scheduling: FCFS, SJF, SRTF, Priority Scheduling, and Round Robin

## Scope

This project models CPU process scheduling through five major scheduling families:

- **FCFS (First-Come, First-Served)**: selects the earliest arriving ready process and executes it to completion.
- **SJF (Shortest Job First)**: selects the ready process with the smallest total CPU burst and executes it without preemption.
- **SRTF (Shortest Remaining Time First)**: the preemptive form of SJF, where the process with the smallest remaining CPU time receives the CPU.
- **Priority Scheduling**: selects work according to priority and can be implemented as either non-preemptive or preemptive scheduling.
- **Round Robin**: gives each ready process a bounded CPU time slice and cycles through the ready queue.

The three implementations approach the same operating-system subject from different perspectives. Python provides a complete scheduling simulator, JavaScript models scheduling through data structures and event-oriented behavior, and C++ presents a repository build-farm case study in which scheduling policies are implemented as a reusable systems component.

## Core Scheduling Model

A process is represented by at least four attributes:

| Attribute | Meaning |
|---|---|
| Arrival Time | The first time at which the process can enter the ready state |
| Burst Time | The amount of CPU service required |
| Priority | A policy-specific ordering value |
| Process ID | A unique identifier used to track execution |

A scheduler does not execute every process immediately. The process first becomes eligible at its arrival time. When the CPU becomes available, the scheduling policy examines the ready processes and chooses one according to its selection rule.

The implementations model an idle CPU explicitly. If no process has arrived, the simulated clock advances to the next arrival rather than executing nonexistent work.

## Scheduling Metrics

The programs calculate the standard metrics used to evaluate scheduling behavior.

### Completion Time

Completion time is the clock value at which a process finishes its required CPU service.

### Turnaround Time

Turnaround time measures the complete elapsed time spent in the system:

`Turnaround Time = Completion Time - Arrival Time`

A process that arrives at time 4 and completes at time 15 therefore has a turnaround time of 11.

### Waiting Time

Waiting time represents time spent ready but not executing:

`Waiting Time = Turnaround Time - Burst Time`

This definition works for both preemptive and non-preemptive policies because the total burst time is the actual CPU service requirement.

### Response Time

Response time measures how long a process waits before receiving CPU time for the first time:

`Response Time = First CPU Start Time - Arrival Time`

Response time is particularly important for interactive workloads because a process can have a reasonable completion time while still experiencing a poor initial response.

### CPU Utilization

The simulator estimates CPU utilization over the simulated makespan:

`CPU Utilization = Total CPU Busy Time / Total Simulated Time × 100`

This exposes idle periods that would otherwise be hidden by a simple list of completion times.

### Throughput

Throughput is modeled as:

`Throughput = Number of Completed Processes / Total Simulated Time`

The value depends on the workload as well as the scheduling policy.

## FCFS

FCFS uses arrival order as its scheduling rule. Once a process is selected, it keeps the CPU until its burst finishes.

The important property is **non-preemption**. A process arriving during the execution of another process does not interrupt the current process.

For example, if a long compilation begins at time 0 and a short test arrives at time 1, FCFS allows the compilation to finish before selecting the test.

This creates the classic **convoy effect**. A long CPU-bound process at the front of the queue can make several short processes wait even when those short processes would require very little CPU time.

The Python implementation represents FCFS through the `fcfs()` function. It walks the arrival-sorted workload, advances the clock when the CPU is idle, records the first start time, and executes each process for its complete burst.

The JavaScript implementation uses the same policy but emphasizes JavaScript arrays, `Map`, object-based intervals, and validation through class construction.

The C++ case study uses a vector of processes and creates a concrete interpretation in which jobs represent compilation, testing, packaging, and deployment work.

## SJF

SJF is non-preemptive but changes the selection rule.

When the CPU becomes free, the scheduler examines processes that have already arrived and selects the one with the smallest **total burst time**.

The process is not interrupted after selection.

This distinction is important:

- SJF compares complete burst lengths.
- SRTF compares remaining burst lengths while execution is in progress.

If several ready processes have equal burst times, the implementations use deterministic tie-breaking based on arrival time and process identifier. Deterministic tie-breaking prevents otherwise identical simulations from producing inconsistent timelines.

SJF can substantially reduce average waiting time for workloads containing many short jobs, but a long job can wait for repeated short jobs depending on the arrival pattern.

The Python implementation repeatedly constructs the ready set and selects the minimum burst. The JavaScript implementation uses array filtering and sorting to express the same policy. The C++ implementation explicitly maintains the remaining candidate vector and compares burst, arrival time, and process ID.

## SRTF

SRTF is the preemptive counterpart of SJF.

The scheduler does not ask only:

> Which ready process has the smallest original burst?

It asks:

> Which ready process currently has the smallest remaining CPU requirement?

This difference creates preemption.

Suppose a process with nine units of remaining work is executing. A new process arrives with two units of work. SRTF can interrupt the nine-unit process and execute the two-unit process first.

The Python implementation treats process arrivals and completions as scheduling events. It calculates the next future arrival and executes the current process only until that event or its own completion.

The JavaScript implementation uses `Map` to maintain mutable remaining CPU time independently from the immutable `Process` object.

The C++ implementation uses a `map<string, int>` for remaining work and searches the ready set at each scheduling event.

SRTF therefore introduces more scheduling decisions than SJF. In a real operating system, preemption is not free: saving and restoring execution state introduces overhead that a simple mathematical simulation may not completely capture.

## Priority Scheduling

Priority scheduling changes the selection criterion from CPU duration to priority.

The implementations use the convention that a **smaller numeric priority value means higher priority**.

For example:

| Priority | Interpretation |
|---:|---|
| 1 | Higher priority |
| 2 | Medium priority |
| 5 | Lower priority |

The convention is a design decision. A different system can define larger numbers as higher priority, but the scheduler must apply one consistent ordering rule.

### Non-Preemptive Priority

The non-preemptive version chooses the highest-priority ready process when the CPU becomes available.

Once selected, that process runs until its burst completes.

A higher-priority process arriving during execution does not immediately take the CPU.

This makes non-preemptive priority scheduling structurally similar to SJF, but the selection attribute is priority rather than burst duration.

### Preemptive Priority

The preemptive version reevaluates the ready set when new work arrives.

If a newly arriving process has a higher priority than the currently executing process, the current process can be interrupted.

The C++ program includes a specific priority-preemption scenario with a long lower-priority job and later urgent jobs. This demonstrates how repeated high-priority arrivals can delay lower-priority work.

A production scheduler may address this behavior through mechanisms such as aging, where waiting processes gradually receive increased effective priority. Aging is not automatically applied by the provided simulations because doing so would change the policy being demonstrated.

## Round Robin

Round Robin is designed around time slicing.

A ready queue is maintained in FIFO order. The scheduler gives the process at the front of the queue at most a fixed **time quantum**.

If the process finishes before the quantum expires, it leaves the system.

If it still has remaining CPU work when the quantum expires, it is placed at the back of the ready queue.

For a quantum of three units, a process with eight units of CPU demand may execute in slices such as:

`3 + 3 + 2`

The exact sequence depends on other processes arriving during those slices.

The Python implementation uses `collections.deque`, which provides efficient queue operations appropriate for FIFO ready-queue behavior.

The JavaScript implementation uses an array as a queue and explicitly appends newly arrived processes before returning an unfinished process to the back of the queue.

The C++ implementation uses `std::queue`, making the ready queue a direct representation of the scheduling structure.

The quantum is a policy parameter rather than a universal constant. A very small quantum can increase scheduling and context-switch activity, while a very large quantum makes Round Robin increasingly resemble FCFS for many workloads.

## Preemption and Non-Preemption

The distinction between preemptive and non-preemptive scheduling is central to the project.

A non-preemptive policy lets the selected process retain the CPU until it finishes its current CPU burst.

A preemptive policy permits the scheduler to interrupt the current process when a scheduling event changes the selection decision.

The implementations demonstrate this difference directly:

| Policy | Preemptive | Primary Selection Rule |
|---|---|---|
| FCFS | No | Earliest arrival |
| SJF | No | Smallest burst |
| SRTF | Yes | Smallest remaining burst |
| Priority | Configurable | Highest priority |
| Round Robin | Yes | Ready-queue rotation |

The word "preemptive" does not mean that a process is discarded. Its remaining CPU requirement is preserved and it can return to the ready queue or remain eligible for another scheduling decision.

## Scheduling Timeline

Each implementation records execution intervals in a form equivalent to:

`[start, end) PROCESS`

The half-open interval notation means that execution includes the beginning time and stops immediately before the ending time.

For example:

`[4, 7) P2`

represents three units of CPU service.

Idle intervals are represented explicitly. This matters because a workload such as:

- P1 arrives at 4
- P2 arrives at 8

cannot have CPU utilization calculated correctly unless the idle interval from time 0 to 4 is represented.

Adjacent intervals belonging to the same process are merged. This keeps the timeline readable without changing the scheduling result.

## Python Implementation

The Python program is a complete simulator centered on the `Process` and `Result` data classes.

`Process` validates identifiers, arrival times, burst times, and priorities at construction. This prevents invalid process state from entering the scheduling algorithms.

`Result` centralizes derived metrics such as waiting time, turnaround time, response time, CPU utilization, throughput, and context-switch counts. The scheduling functions therefore concentrate on policy behavior rather than duplicating metric calculations.

The implementation contains separate functions for:

- `fcfs()`
- `sjf()`
- `srtf()`
- `priority_non_preemptive()`
- `priority_preemptive()`
- `round_robin()`

The SRTF and preemptive-priority implementations maintain a separate remaining-time mapping. This is necessary because the original burst value is immutable process metadata while the remaining CPU requirement changes during execution.

The Round Robin implementation uses a `deque`, matching the FIFO semantics of a ready queue.

The script also demonstrates:

- CPU idle periods
- preemption
- Round Robin time slicing
- invalid arrival times
- invalid burst lengths
- invalid Round Robin quantum values
- deterministic tie-breaking
- context-switch counting
- cross-policy metric comparison

The program uses only Python's standard library.

## JavaScript Implementation

The JavaScript program is designed as a Node.js executable and takes a more event-oriented representation of scheduling state.

The `Process` class validates process construction. Runtime scheduling state is stored separately in `Map` instances. For preemptive algorithms, this separation is important because the process definition remains stable while the remaining CPU time changes.

The `appendInterval()` function consolidates adjacent timeline entries. This demonstrates a useful event-log technique: multiple internal scheduling events can still produce a compact externally visible timeline.

The JavaScript implementation also uses:

- arrays for ordered workloads
- `Set` for duplicate process detection
- `Map` for remaining CPU state and completion records
- arrays as explicit FIFO queues for Round Robin
- structured result objects for metrics
- `console.table()` for readable scheduling output

The SRTF implementation repeatedly identifies the currently eligible process with the smallest remaining CPU time. The preemptive-priority implementation instead compares priority values.

The Round Robin implementation makes queue ordering explicit. New arrivals that occur during a time slice are inserted before the expired process is returned to the queue, reflecting the event sequence represented by the simulation.

## C++ Case Study: Repository Build Farm

The C++ program models a shared continuous-integration build worker.

The workload contains operations such as:

- compilation
- automated testing
- linting
- packaging
- deployment preparation

Each job is represented by the `Process` structure.

The scheduler is represented through policy functions rather than a single hard-coded ordering rule. This allows the same workload to be passed through FCFS, SJF, SRTF, both priority variants, and Round Robin.

The case study records:

- process arrival
- CPU burst
- priority
- first execution
- completion
- turnaround
- waiting
- response
- CPU utilization
- throughput
- context switches
- complete execution timeline

The `ScheduleResult` structure owns the common reporting and metric calculations. This prevents every scheduling algorithm from implementing its own independent interpretation of waiting or turnaround time.

The preemptive algorithms store remaining CPU time separately from the original process record. This is essential because preemption changes remaining work but does not change the original burst requirement.

The C++ implementation uses C++17 standard-library facilities such as `vector`, `map`, `queue`, `sort`, and exception classes. No external libraries are required.

## Why SJF and SRTF Are Different

SJF and SRTF are often confused because both are based on job length.

Their selection state is different.

SJF asks for the smallest **original burst among currently ready processes** and then commits to that process until completion.

SRTF asks for the smallest **remaining burst at every scheduling event** and can interrupt an existing process.

Consider:

| Process | Arrival | Burst |
|---|---:|---:|
| A | 0 | 9 |
| B | 2 | 2 |

At time 0, A is the only available process. SJF starts A and continues running it.

At time 2, B has arrived. SRTF observes that A has seven units remaining while B requires only two, so SRTF can run B before continuing A.

The distinction is therefore not simply an implementation detail. It changes the execution timeline and the waiting and response metrics.

## Why Priority Scheduling Is Different from SJF

Priority scheduling can produce a completely different decision even when burst lengths are known.

Suppose two ready jobs have:

| Process | Burst | Priority |
|---|---:|---:|
| A | 2 | 5 |
| B | 8 | 1 |

SJF chooses A because it has the smaller burst.

Priority scheduling chooses B under the convention used by this project because priority `1` is higher than priority `5`.

This is why scheduling policy must be treated as a distinct decision rule rather than as a generic "choose the best process" operation.

## Round Robin and Time Quantum

Round Robin does not attempt to estimate which process will finish soonest or which process is most important.

Its central mechanism is bounded CPU ownership.

The time quantum controls how long a ready process can execute before the scheduler gives other ready processes an opportunity.

With:

- P1 requiring 7 units
- P2 requiring 4 units
- quantum = 2

the scheduler may produce a pattern such as:

`P1 → P2 → P1 → P2 → P1 → P1`

The exact sequence depends on arrival times.

A smaller quantum generally creates more opportunities for waiting processes to receive CPU time, but it can also produce more scheduling boundaries. The simulations expose this effect through the recorded execution timeline and context-switch count.

## Context Switches

The simulator counts a context switch when execution moves directly from one process to another.

Idle transitions are treated separately. Entering or leaving an idle CPU does not count as a process-to-process context switch in these implementations.

The count is therefore a simplified scheduling metric rather than a complete hardware measurement.

A real operating system may incur costs associated with:

- saving register state
- restoring another process's state
- changing address-space context
- cache effects
- branch-prediction effects
- scheduler execution itself

The educational simulations represent the scheduling decisions, not the complete microarchitectural cost of a context switch.

## Starvation

Starvation occurs when a process remains ready but repeatedly loses scheduling decisions to other processes.

Priority scheduling can exhibit starvation when higher-priority work continuously arrives.

SJF and SRTF can also produce long delays for large jobs when short jobs continually enter the system.

Round Robin provides a different fairness mechanism because ready processes receive recurring time slices, assuming the queue and scheduling assumptions remain valid.

The programs deliberately expose these behaviors rather than hiding them behind a single aggregate performance value.

## Tie-Breaking

Scheduling algorithms frequently encounter ties.

Two processes can have:

- identical arrival times
- identical burst times
- identical priority values
- identical remaining CPU requirements

The simulations use deterministic tie-breaking, generally based on arrival time followed by process ID.

Deterministic scheduling is valuable in an educational simulator because the same input should generate the same timeline on every run.

A production scheduler may use additional attributes such as CPU affinity, fairness state, task class, deadline, or dynamic priority.

## Edge Cases

The implementations explicitly address several important edge conditions.

### CPU Initially Idle

If the earliest process arrives after time zero, the scheduler inserts an idle interval and advances the clock to the arrival.

### Multiple Simultaneous Arrivals

When multiple processes arrive at the same time, the policy-specific comparison determines which process is selected.

### Process Completion at an Arrival Event

A process may finish at exactly the same time another process arrives. The implementation processes the completed process first and then evaluates the newly ready workload at the resulting scheduling event.

### Preemption During Execution

SRTF and preemptive priority scheduling calculate the next relevant arrival so that execution can stop when a new scheduling decision becomes necessary.

### Invalid Input

The implementations reject negative arrival times, non-positive burst lengths, duplicate identifiers, and invalid Round Robin quantum values.

### Empty Workloads

An empty workload is rejected rather than producing undefined averages or division-by-zero behavior.

## Performance Considerations

The project prioritizes transparency over high-performance scheduler implementation.

Several policies repeatedly scan the process collection to identify the next candidate. This makes the implementations easy to inspect but can be less efficient than production-ready priority queues or specialized scheduler data structures.

For `n` processes, repeated linear scans can approach quadratic behavior for some workloads.

A production implementation can use structures such as:

- a heap ordered by remaining time
- a heap ordered by priority
- an arrival-event queue
- a FIFO ready queue for Round Robin

Preemptive scheduling adds another consideration: the scheduler must respond to events that can change the selected process.

The mathematical complexity of a policy is therefore only part of the real scheduling cost. Event management, queue maintenance, preemption, synchronization, and context-switch overhead also matter.

## Common Modeling Errors

### Confusing Burst Time with Remaining Time

A preempted process keeps its original burst requirement as historical data, but its remaining CPU requirement decreases.

Replacing the original burst with the remaining value makes turnaround and waiting calculations incorrect.

### Treating SJF as Preemptive

SJF does not automatically interrupt the current process.

SRTF is the preemptive version.

### Ignoring Arrival Times

Selecting a process that has not yet arrived violates the scheduling model.

The simulators explicitly advance the clock through idle periods.

### Using Priority Without Defining Its Direction

A priority number has no universal meaning. The system must define whether smaller or larger values indicate higher priority.

This project explicitly uses smaller values as higher priority.

### Mishandling Round Robin Requeueing

An unfinished Round Robin process must return to the ready queue rather than continue indefinitely.

Newly arrived processes also have to enter the queue according to the simulator's event ordering.

### Calculating Waiting Time Directly from a Single Queue Interval

A preemptive process can wait multiple times. Waiting time should therefore be derived from turnaround and total CPU burst rather than assuming one continuous waiting interval.

## Policy Comparison

| Policy | Selection basis | Preemptive | Main characteristic |
|---|---|---|---|
| FCFS | Arrival order | No | Simple FIFO behavior; vulnerable to convoy effects |
| SJF | Smallest total burst | No | Short jobs are selected first |
| SRTF | Smallest remaining burst | Yes | Reconsiders execution when workload changes |
| Priority | Priority value | Optional | Allows workload importance to control selection |
| Round Robin | FIFO queue plus quantum | Yes | Time-sliced sharing of CPU |

No single metric completely describes scheduling behavior.

Average waiting time, average turnaround time, response time, CPU utilization, throughput, context-switch frequency, and fairness can point to different characteristics of the same workload.

The correct policy depends on the workload and system objective rather than on one universally optimal metric.

## Production Considerations

A real operating-system scheduler has responsibilities beyond the calculations represented here.

Production scheduling can involve:

- multiple CPU cores
- CPU affinity
- kernel and user processes
- interrupt handling
- synchronization
- dynamic priorities
- deadlines
- I/O blocking
- sleeping and waking
- cache locality
- power management
- real-time scheduling constraints
- scheduler implementation overhead

The provided programs intentionally isolate CPU scheduling policy so that the fundamental decision mechanisms remain visible.

A real scheduler also has to protect shared scheduler state against races and must interact correctly with hardware-supported process and thread context switching.

## Practical Interpretation of the Results

The simulator output should be interpreted as a workload-specific experiment.

A lower average waiting time does not automatically imply lower response time for every process.

A high CPU utilization percentage does not prove fairness.

A small number of context switches does not necessarily mean a better interactive experience.

A high-priority workload can improve response for urgent jobs while delaying lower-priority work.

A very small Round Robin quantum can improve scheduling granularity while increasing scheduling activity.

These are relationships between metrics and policy behavior, not independent properties of an algorithm.

## Execution

The Python program can be run directly with a Python 3 interpreter.

The JavaScript program is designed for a Node.js runtime.

The C++ program requires a compiler supporting C++17 or later. A typical compilation command is `g++ -std=c++17 -O2 scheduler.cpp -o scheduler`.

All three programs operate on deterministic in-memory workloads and require no external package or database.

## Implementation Relationship

The three programs deliberately do not function as line-for-line translations.

The Python implementation emphasizes reusable simulation functions, data classes, validation, metric calculation, and an educational scheduling laboratory.

The JavaScript implementation emphasizes object construction, `Map`-based mutable scheduler state, queue operations, structured result objects, and event-oriented preemption.

The C++ implementation treats scheduling as a systems case study. It separates process records, timeline records, scheduling policies, result calculation, and reporting so that the same workload can be evaluated by multiple policies.

Together, the implementations show that FCFS, SJF, SRTF, Priority Scheduling, and Round Robin are not merely formulas for calculating waiting time. They are different mechanisms for deciding which ready process receives CPU service, when that decision is reconsidered, and how process state is preserved between executions.
