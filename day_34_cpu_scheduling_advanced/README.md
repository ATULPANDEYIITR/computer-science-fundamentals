# Advanced CPU Scheduling: Multilevel Queues, Multilevel Feedback Queues, and Context Switching

## Scope

This project studies advanced CPU scheduling through three closely related mechanisms:

- **Multilevel Queue Scheduling (MLQ)** separates processes into fixed scheduling classes.
- **Multilevel Feedback Queue Scheduling (MLFQ)** allows processes to move between queues according to observed CPU behavior.
- **Context switching** represents the dispatcher cost of changing the CPU from one execution context to another.

The three mechanisms solve different parts of the scheduling problem. A multilevel queue establishes classification. A multilevel feedback queue makes that classification adaptive. Context switching represents the execution cost of changing the selected process and therefore affects the real performance of otherwise identical scheduling policies.

The implementations model process arrival, CPU bursts, I/O blocking, ready queues, preemption, time quanta, queue transitions, priority boosts, dispatcher overhead, and standard scheduling metrics.

---

## Core Scheduling Model

A process moves through scheduler-visible states:

`NEW -> READY -> RUNNING -> BLOCKED -> READY -> RUNNING -> TERMINATED`

The exact path depends on its workload.

A CPU-bound process may remain ready for long periods and consume repeated time quanta. An I/O-bound process commonly executes a short CPU burst, blocks for I/O, and later returns to a ready queue. An interactive workload benefits from rapid response and therefore usually receives preferential treatment in an appropriately configured high-priority queue.

The scheduler repeatedly performs four important activities:

- Admit processes whose arrival time has been reached.
- Select a process from the highest eligible ready queue.
- Execute the selected process for the policy-defined amount of CPU time.
- React to completion, blocking, preemption, queue expiration, or a priority event.

The implementations represent CPU execution as discrete time units. This makes preemption and context-switch overhead explicit and makes the resulting scheduling timeline easy to inspect.

---

## Multilevel Queue Scheduling

Multilevel Queue Scheduling divides the ready workload into separate queues with different policies or priorities.

A typical configuration might contain:

| Queue | Workload | Scheduling policy |
|---|---|---|
| System | Kernel or highly important work | Priority scheduling |
| Interactive | User-facing processes | Round robin |
| Batch | Long-running background work | FCFS |

The important property is **static queue membership**.

A process assigned to the batch queue does not become an interactive process simply because it has consumed a large amount of CPU. The scheduler may use a different policy inside each queue, but the classification itself remains fixed.

This creates a strong distinction between queue-level priority and process-level scheduling.

If queue 0 has higher precedence than queue 1, the scheduler examines queue 0 before queue 1. A process in a lower queue may therefore experience significant waiting when a higher queue remains continuously populated.

### MLQ trade-off

MLQ is useful when workload classes are known in advance and organizational policy requires explicit separation. For example, a system may intentionally separate latency-sensitive services from batch workloads.

Its weakness is that static classification can become inaccurate. A process initially classified as interactive may later become CPU-intensive, while a batch process may suddenly become latency-sensitive. MLQ does not automatically learn from those behavioral changes.

---

## Multilevel Feedback Queue Scheduling

MLFQ adds adaptation to the multilevel queue model.

Instead of permanently assigning a process to one queue, the scheduler observes execution behavior and changes the process's queue level.

The project uses this configuration:

| Queue | Policy | Quantum | Intended behavior |
|---|---|---:|---|
| Q0 | Round robin | 2 | Interactive and latency-sensitive work |
| Q1 | Round robin | 4 | General-purpose work |
| Q2 | FCFS | None | CPU-heavy or batch work |

A CPU-intensive process that repeatedly consumes an entire quantum is demoted. This gradually moves sustained CPU consumers toward lower queues.

An I/O-bound process often gives up the CPU before consuming a complete quantum. The model can promote such a process when it returns from blocking because short CPU bursts are characteristic of interactive behavior.

This creates a behavioral distinction:

`CPU-intensive -> consumes quantum -> demotion`

versus:

`I/O-bound -> blocks early -> promotion or retention at a higher level`

The exact rules used by a real operating system can differ. MLFQ is a family of scheduling policies rather than one universally fixed algorithm.

---

## Why Queue Movement Matters

Queue movement allows MLFQ to approximate different goals at the same time.

A high-priority queue with a short quantum improves response time because a newly runnable interactive process can receive CPU service quickly.

A lower queue with a longer quantum reduces scheduling frequency for CPU-intensive processes.

A bottom FCFS queue can execute long-running work without repeatedly applying short time slices.

The scheduler therefore trades:

- response time,
- waiting time,
- throughput,
- fairness,
- context-switch overhead,
- starvation risk,
- and CPU utilization.

Changing the quantum changes these trade-offs. A very small quantum can improve responsiveness but cause many preemptions and context switches. A very large quantum reduces switching overhead but makes the scheduler behave more like FCFS for processes sharing that queue.

---

## Priority Boosting and Starvation

MLFQ can create starvation.

Suppose Q0 continuously receives short interactive processes. If the scheduler always gives Q0 priority over Q1 and Q2, a long-running process in Q2 may receive little or no CPU time.

The Python, JavaScript, and C++ implementations address this with periodic priority boosting.

At a boost event, waiting processes in lower queues are moved toward the highest-priority queue.

Conceptually:

`Q2 waiting -> Q1/Q0`

and:

`Q1 waiting -> Q0`

The purpose is not to reward CPU-heavy work. The purpose is to place an upper bound on how long a waiting process can remain trapped in a lower-priority class under the configured policy.

Priority boosting is a policy choice. Its interval must be selected carefully. A very frequent boost can effectively destroy the distinction between queues, while an excessively long interval can allow poor response for lower-priority workloads.

---

## Context Switching

A context switch occurs when the CPU changes from one execution context to another.

A scheduler may need to preserve the outgoing context and restore the incoming context. At the operating-system level, the details depend on the processor architecture, operating-system design, process versus thread semantics, memory-management mechanisms, and kernel implementation.

This project models context switching as explicit elapsed time.

For example, with:

`contextSwitchCost = 1`

a dispatch transition consumes one time unit that does not execute the selected process's CPU burst.

This matters particularly in round-robin scheduling.

Consider a quantum of one CPU unit:

`A -> context switch -> B -> context switch -> A`

The scheduler may switch very frequently. If each switch has non-zero cost, useful application CPU time becomes a smaller fraction of elapsed time.

The C++ case study explicitly compares switch costs of zero, one, and two time units so that the effect can be observed rather than treated as an abstract concept.

---

## Python Implementation

The Python program is the most complete simulation-oriented implementation.

Its `Process` class stores:

- arrival time,
- CPU and I/O bursts,
- base priority,
- current queue level,
- remaining CPU time,
- process state,
- response time,
- waiting time,
- completion time,
- preemption count,
- demotion count,
- and promotion count.

The `Burst` class models an alternating CPU/I/O workload. This is important because CPU scheduling decisions change when a process blocks for I/O.

The `QueueConfig` class defines the policy and, when applicable, the round-robin quantum.

### Python MLFQ behavior

`MLFQScheduler` maintains independent ready queues.

The scheduler:

- admits newly arrived processes,
- releases processes whose I/O has completed,
- performs periodic priority boosts,
- preempts a running lower-queue process when a higher queue becomes ready,
- dispatches the next eligible process,
- executes CPU time,
- detects quantum expiration,
- demotes CPU-intensive processes,
- handles CPU burst completion,
- and terminates completed processes.

The timeline records CPU execution, idle periods, and context-switch intervals.

The implementation also separates `waiting_time`, `response_time`, `turnaround_time`, CPU utilization, context-switch count, and context-switch time. These metrics represent different performance dimensions and should not be treated as interchangeable.

### Python MLQ behavior

`SimpleMLQScheduler` deliberately uses static queue membership.

The example contains:

- a system queue using priority scheduling,
- an interactive queue using round robin,
- and a batch queue using FCFS.

Unlike the MLFQ implementation, the process does not change queues based on CPU consumption.

This makes the difference between MLQ and MLFQ observable in executable behavior rather than only in terminology.

---

## JavaScript Implementation

The JavaScript implementation uses an event-driven representation.

The `Process` class models process state and execution statistics. `EventLog` records scheduling events so the execution history can be inspected independently from the scheduler's internal queues.

The MLFQ implementation records events such as:

- CPU execution,
- context switching,
- higher-queue preemption,
- and priority boosts.

This representation is useful when scheduling data must later be consumed by a user interface, monitoring dashboard, timeline renderer, or event-processing system.

JavaScript's object-oriented model is used to keep process state and scheduler behavior separate. The implementation does not depend on browser APIs or npm packages, so it can run directly under Node.js.

The JavaScript MLFQ model also demonstrates that a scheduler can be treated as a state machine driven by events rather than as a collection of independent examples.

---

## C++ Case Study

The C++ implementation models a repository-build server workload.

The workload contains:

- `TERMINAL`, representing short interactive work with I/O waits.
- `API`, representing a latency-sensitive service process.
- `COMPILER`, representing sustained CPU-intensive work.
- `BACKUP`, representing a long batch operation.
- `LOGGER`, representing short periodic CPU bursts separated by I/O.

The scheduler uses three queues:

`Q0 -> interactive round robin`

`Q1 -> standard round robin`

`Q2 -> batch FCFS`

The compiler and backup workloads naturally consume complete CPU quanta and therefore move toward lower queues. The terminal, API, and logger workloads perform I/O and can regain higher scheduling priority.

### C++ architecture

The base `Scheduler` class owns common mechanisms:

- process storage,
- ready queues,
- blocked-process tracking,
- dispatching,
- event recording,
- CPU execution,
- burst completion,
- preemption,
- and metric reporting.

`MLFQScheduler` adds adaptive queue movement and priority boosting.

`MLQScheduler` retains static queue membership.

This separation is deliberate. The difference between the two scheduling algorithms is represented as an architectural distinction rather than a flag that merely changes printed text.

---

## CPU Scheduling Metrics

### Response time

Response time measures how long a process waits from arrival until its first CPU execution.

`response time = first CPU start - arrival time`

This metric is particularly important for interactive workloads.

A process can have low total waiting time while still having an undesirable first response, so response time should be analyzed separately.

### Waiting time

Waiting time measures time spent ready but not executing.

The implementation accumulates ready-queue waiting intervals.

Blocked I/O time is not treated as ready-queue waiting because a blocked process is not eligible to receive CPU service.

### Turnaround time

Turnaround time measures the total elapsed time from arrival to completion.

`turnaround time = completion time - arrival time`

It includes CPU execution, ready waiting, blocking, and other elapsed scheduler effects represented by the model.

### CPU utilization

CPU utilization compares useful process CPU execution against elapsed simulation time.

Context-switch intervals therefore reduce the modeled utilization when they consume explicit time.

### Throughput

Throughput describes completed work per unit of elapsed time.

A scheduler that produces excellent response times but excessive overhead can still have poor throughput.

---

## Time Quantum Selection

The time quantum is one of the most important MLFQ parameters.

A short quantum has several consequences:

- interactive processes receive frequent opportunities to run,
- CPU-bound processes are demoted faster,
- preemption frequency increases,
- context-switch overhead can increase,
- cache locality can be affected in a real system.

A long quantum has different consequences:

- fewer scheduling decisions occur,
- context-switch overhead is lower,
- CPU-bound work receives longer uninterrupted execution,
- interactive processes may wait longer behind a running process.

There is no universally optimal quantum. The correct value depends on workload characteristics, processor behavior, scheduling objectives, and the cost of switching.

---

## Preemption

Preemption means that the scheduler interrupts a currently running process before its current CPU burst has completed.

In the MLFQ model, preemption can occur when:

- a round-robin quantum expires,
- a higher-priority queue becomes ready,
- or another policy-specific scheduling condition is reached.

A quantum expiration generally represents scheduler-enforced preemption.

A process blocking for I/O is different. It voluntarily leaves the CPU because it cannot continue until an external operation progresses.

Distinguishing these mechanisms is important because their performance and policy implications differ.

---

## MLQ and MLFQ Comparison

| Property | Multilevel Queue | Multilevel Feedback Queue |
|---|---|---|
| Queue membership | Static | Dynamic |
| CPU behavior affects queue | Usually no | Yes |
| Demotion | Not intrinsic | Common |
| Promotion | Not intrinsic | Common |
| Priority boost | Optional policy mechanism | Common starvation-control mechanism |
| Workload classification | Explicit | Adaptive |
| Policy complexity | Lower | Higher |
| Starvation risk | Can be significant | Can be controlled with boosts |
| Scheduling flexibility | Lower | Higher |
| Tuning requirements | Queue assignments | Queue assignments, quanta, promotion and boost rules |

The central distinction is queue membership.

MLQ asks:

> Which predefined class does this process belong to?

MLFQ asks:

> What does this process's recent CPU behavior suggest about the queue it should receive?

---

## Edge Cases

### CPU burst exactly equals the quantum

A process that finishes exactly when its quantum expires should normally be treated as having completed its CPU burst rather than unnecessarily requeued and immediately dispatched again.

The implementations check burst completion before applying quantum-expiration demotion.

### Process arrival during context switching

The simulation treats context-switch time as elapsed time. Processes whose arrival time falls during that interval become eligible when the scheduler next performs admission.

### Empty ready queues

When no process is ready and no process is running, the CPU is recorded as idle. The simulation advances until another process arrives or blocked I/O completes.

### All processes blocked

A blocked process cannot be scheduled. The scheduler advances through idle time until an I/O completion event makes a process ready.

### Lower queue starvation

Priority boosts provide an explicit mechanism for moving waiting processes upward.

### Invalid scheduling configuration

The implementations reject invalid input such as:

- zero or negative CPU bursts,
- negative arrival times,
- invalid round-robin quanta,
- empty process definitions,
- and invalid context-switch costs.

Failing early is preferable to allowing an invalid scheduler configuration to produce misleading metrics.

---

## Common Scheduling Mistakes

### Treating MLQ and MLFQ as synonyms

They are not interchangeable. Static queue membership is the defining characteristic of MLQ, while adaptive queue movement is central to MLFQ.

### Counting blocked time as ready waiting

A blocked process cannot compete for the CPU. I/O blocking therefore must be represented separately from ready-queue waiting.

### Ignoring context-switch overhead

A theoretical scheduling sequence may appear efficient while a real implementation spends substantial time switching between contexts.

### Using only average waiting time

Average waiting time can hide poor interactive responsiveness or severe outliers. Response time and turnaround time provide additional information.

### Forgetting starvation

Strict priority between queues can indefinitely delay lower-priority work. A scheduler intended for mixed workloads needs a fairness mechanism or an explicit acceptance of starvation.

### Treating every preemption as identical

Quantum expiration, arrival of higher-priority work, and voluntary blocking are different events. They should be represented separately when analyzing scheduler behavior.

---

## Performance Characteristics

With `n` processes and `q` scheduling queues, a simple simulator can incur additional search overhead when selecting processes from priority queues.

The educational implementations deliberately favor transparency over kernel-level optimization.

The most expensive conceptual operations include:

- searching a priority queue for the best candidate,
- scanning all processes for arrivals,
- scanning blocked processes for I/O completion,
- and moving lower-level ready queues during a priority boost.

A production scheduler would use specialized kernel data structures, timer facilities, run queues, per-CPU structures, synchronization mechanisms, and architecture-specific context-management code rather than repeatedly scanning all processes.

The simulation complexity should therefore not be confused with the complexity of an operating-system scheduler.

---

## Context-Switch Trade-offs

A scheduler with an extremely small time quantum can create a high number of context switches.

For a workload with many runnable processes:

`smaller quantum -> more preemptions -> more switches`

If:

`context switch cost > 0`

then:

`more switches -> more non-application CPU time`

The relationship becomes especially important for CPU-bound workloads.

For interactive workloads, some overhead may be justified because shorter scheduling intervals can improve responsiveness.

The correct engineering decision is therefore a trade-off rather than an attempt to minimize context switches absolutely.

---

## Practical Interpretation

The simulations model a mixed operating environment rather than a single homogeneous workload.

Interactive processes should receive rapid CPU access because users notice latency.

I/O-bound services should not be punished simply because they repeatedly leave the CPU for I/O. Their short CPU bursts are often exactly the behavior a responsive scheduler should recognize.

CPU-intensive compilation and backup operations can tolerate lower queue priority because they generally care more about throughput than immediate response.

MLFQ provides a mechanism for expressing these workload differences dynamically. Context-switch accounting prevents the analysis from treating scheduling decisions as free.

The resulting system illustrates why advanced CPU scheduling is a multi-objective optimization problem involving responsiveness, fairness, throughput, starvation control, and scheduling overhead.
