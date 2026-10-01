# Processes: Process Concept, PCB, Process States, and Process Lifecycle

## Scope

A process is an executing instance of a program together with the execution state and operating-system resources required to manage it.

This project focuses on four tightly connected areas:

- the process concept and what makes a process different from a passive program;
- the Process Control Block, which stores the kernel's management information for a process;
- process states and the rules governing movement between those states;
- the process lifecycle from creation through scheduling, blocking, resumption, and termination.

The implementations use different perspectives rather than translating the same program three times. Python provides a detailed process-management simulator, JavaScript models the lifecycle with an event-driven design, and C++ builds a more structured process-management case study around a build-service environment.

The central relationship is:

`program -> process instance -> PCB -> state transitions -> scheduler/resource decisions -> termination`

The three implementation files model these mechanisms explicitly.

## Process Concept

A program stored on disk is passive. A process is an active execution entity created when the operating system establishes the execution context needed to run that program.

A process normally has information such as:

- a process identifier;
- an execution state;
- a program counter;
- processor register state;
- scheduling information;
- memory-management information;
- open resources;
- accounting information;
- relationships with other processes;
- information required to resume execution.

The exact organization is operating-system dependent, but the conceptual distinction is important: two processes may execute the same program while possessing different execution contexts, identifiers, resources, and lifecycle states.

For example, two instances of the same worker program can have different PIDs, different parent processes, different CPU progress, different resources, and different scheduling positions.

The Python simulator represents this distinction with `ProcessControlBlock`. The JavaScript implementation uses the `PCB` class. The C++ implementation uses the `ProcessControlBlock` structure.

## Process Identity

The process identifier, or PID, provides a kernel-visible identity for a process.

The implementations maintain PID-to-PCB mappings:

- Python uses a dictionary.
- JavaScript uses a `Map`.
- C++ uses a `std::map`.

The PID is deliberately independent of the process name. Names such as `build-worker-A` are descriptive, while the PID identifies a particular process instance.

This distinction matters when several instances have the same executable or service role.

## Process Control Block

The Process Control Block is the central process-management record represented in this project.

A real operating system may distribute process information across several kernel structures, and the exact PCB definition differs between operating systems. The educational PCB here combines representative fields into one explicit structure.

### Identity information

The implementations store:

- PID;
- parent PID;
- process name.

The parent PID establishes a process relationship without making the process name responsible for identifying its parent.

### Execution state

Each PCB contains one of:

`NEW`, `READY`, `RUNNING`, `BLOCKED`, or `TERMINATED`.

The state is changed through validated lifecycle operations rather than arbitrary assignment. This prevents impossible transitions from silently corrupting the scheduler model.

### CPU context

The CPU context contains representative execution information:

- program counter;
- stack pointer;
- base pointer;
- general-purpose registers;
- processor flags.

The simulator does not manipulate real CPU registers. Instead, it demonstrates the management principle that a process needs enough saved execution context to resume after a context switch.

For example, the Python simulator increments a simulated program counter and register value when a process runs. When another process receives the CPU, those values remain associated with the first process's PCB.

### Scheduling information

The PCB contains:

- priority;
- time-slice information;
- remaining CPU burst;
- CPU execution accounting;
- context-switch accounting.

The scheduling policy used by the examples is deliberately simple. Lower numerical priority values represent higher scheduling priority.

A production operating system can use considerably more sophisticated scheduling policies, including dynamic priorities, fairness mechanisms, per-CPU queues, real-time scheduling classes, and workload-specific policies.

### Parent and child information

The PCB stores child PIDs.

This supports lifecycle relationships such as a parent waiting for a child to terminate. The examples model a parent process entering a blocked state while waiting for a child and becoming ready again when the child's termination satisfies the wait.

### Resource ownership

The PCB records resources owned by the process.

The examples use resources such as terminal output, database connections, compiler slots, and storage devices. The purpose is not to implement a complete resource manager but to demonstrate why process metadata can be associated with resource ownership.

When a process terminates, the simulators clean up resources that it owns.

### Accounting information

The PCB records execution-related statistics such as:

- CPU ticks;
- ready time;
- blocked time;
- context-switch count;
- creation time;
- first execution time;
- termination time.

Accounting fields allow the simulator to distinguish lifecycle state from historical performance information.

## Process States

The five-state model used by the implementations is:

`NEW -> READY -> RUNNING -> BLOCKED -> READY`

with termination possible from appropriate states.

### NEW

`NEW` represents a process that has been created but has not yet been admitted to the ready queue.

Creation and scheduling admission are conceptually different operations.

The implementations create a PCB in `NEW`, record the creation event, establish parent-child relationships, and then move the process to `READY`.

### READY

A `READY` process is able to execute but is waiting for CPU allocation.

Being ready does not mean that the process is executing.

A single-CPU model can have many ready processes while only one process is running.

The ready queue therefore contains process identifiers rather than complete independent copies of process state.

The PCB remains the authoritative record, while the queue identifies which processes are candidates for dispatch.

### RUNNING

A `RUNNING` process currently owns the simulated CPU.

The single-CPU implementations enforce an important invariant:

`at most one PCB may be RUNNING`

When the scheduler dispatches a process, its state changes from `READY` to `RUNNING` and the scheduler records it as the current process.

### BLOCKED

A `BLOCKED` process cannot continue execution until an external event occurs.

Typical reasons include:

- waiting for disk I/O;
- waiting for a network event;
- waiting for a child process;
- waiting for a synchronization condition;
- waiting for another kernel-managed event.

The examples model I/O blocking using an event such as `disk` or `artifact-disk`.

A blocked process is removed from the CPU and associated with a wait queue. Completion of the event moves it back to `READY`.

### TERMINATED

A `TERMINATED` process has finished execution and cannot return to a runnable state.

The PCB retains lifecycle information such as its exit code and termination timestamp for accounting and parent-child coordination.

The examples prevent transitions out of `TERMINATED`.

## Legal State Transitions

The simulator deliberately enforces legal transitions.

The main paths are:

`NEW -> READY`

`READY -> RUNNING`

`RUNNING -> READY`

`RUNNING -> BLOCKED`

`BLOCKED -> READY`

`RUNNING -> TERMINATED`

The model also permits termination from states where cleanup is meaningful, while refusing transitions out of `TERMINATED`.

A transition is not merely a label change. It affects scheduler data structures and lifecycle metadata.

For example, moving `READY -> RUNNING` removes the PID from the ready queue and records it as the current CPU owner.

Moving `RUNNING -> BLOCKED` removes CPU ownership and adds the process to an appropriate wait queue.

Moving `BLOCKED -> READY` places the process back into a runnable queue.

This relationship between state and supporting data structures is essential to maintaining process-management consistency.

## Process Lifecycle

A typical lifecycle represented by the project is:

`creation -> admission -> ready -> dispatch -> execution -> preemption/blocking -> resumption -> termination`

A process does not necessarily visit every state only once.

A CPU-intensive process may repeatedly move between:

`READY -> RUNNING -> READY -> RUNNING`

A process performing I/O can repeatedly move through:

`RUNNING -> BLOCKED -> READY -> RUNNING`

A process eventually reaches `TERMINATED` when its execution completes or the process is explicitly terminated.

## Process Creation

Process creation establishes a new process identity and PCB.

The examples validate:

- process name;
- priority;
- CPU workload;
- parent existence;
- parent lifecycle state.

The new PID is inserted into the process table.

If a parent PID is supplied, the child PID is also recorded in the parent's child set.

This creates a bidirectional conceptual relationship:

`child.parentPid -> parent`

and

`parent.children -> child`

The examples do not attempt to reproduce a particular operating system's system-call interface. They model the process-management consequences of creation.

## Parent and Child Processes

The parent-child relationship is important to process lifecycle management.

The examples demonstrate a parent waiting for a child:

`parent RUNNING -> BLOCKED`

The child continues independently.

When the child terminates, the process manager checks whether the parent is waiting for that child. If the wait condition is satisfied, the parent becomes:

`BLOCKED -> READY`

This illustrates that process state can depend on events generated by other processes.

A production operating system may implement more elaborate child-reaping, orphan handling, supervision, exit-status collection, and process-group semantics.

## Scheduling and Dispatch

The scheduler decides which `READY` process should receive the CPU.

The educational scheduler uses priority and creation time as selection criteria.

A simplified decision is:

`select READY process with highest scheduling priority`

The scheduler then:

- removes the process from the ready queue;
- changes its state to `RUNNING`;
- records the current PID;
- initializes its first-start timestamp if necessary;
- increments context-switch accounting.

The scheduler is separate from the PCB itself. The PCB contains scheduling information, while scheduler structures determine which runnable process receives execution.

## Preemption

Preemption occurs when the scheduler removes a running process from the CPU even though the process has not terminated.

The simulator uses a time slice.

When the time slice expires:

`RUNNING -> READY`

The process is returned to the ready queue.

Its CPU context remains associated with its PCB, so a future dispatch can resume from the saved execution state.

Preemption demonstrates why a process is more than a program counter. The kernel must preserve enough execution information to resume the process correctly.

## Context Switching

A context switch changes CPU ownership from one process to another.

Conceptually, the operating system must preserve the outgoing process's execution context and restore the incoming process's context.

The educational implementations represent this using `CPUContext`.

The context includes a simulated:

- program counter;
- stack pointer;
- base pointer;
- general-purpose registers;
- flags.

The C++ case study makes the preservation principle explicit: execution modifies the context stored inside the PCB rather than maintaining a single permanent context for the process.

Real context switching can involve considerably more state and architecture-specific operations. Depending on the operating system and processor, memory-management state, floating-point state, vector registers, security state, kernel stack state, and other information may also be involved.

Context switching is not free. It can introduce scheduling overhead and can affect cache and translation lookaside buffer behavior.

## Blocking and I/O

A process blocks when it cannot make useful forward progress until an external event occurs.

The Python and JavaScript simulations associate blocked processes with an I/O name.

The C++ case study uses `artifact-disk` for simulated build-artifact storage.

The lifecycle is:

`RUNNING -> BLOCKED`

The process is removed from CPU ownership and placed on a wait queue.

When the device or event completes:

`BLOCKED -> READY`

The process becomes eligible for dispatch again.

This differs fundamentally from preemption.

With preemption, the process is ready to continue but the scheduler has temporarily selected another process.

With blocking, the process cannot continue until a required event occurs.

## Wait Queues

The blocked queue is keyed by the event being awaited.

For example:

`artifact-disk -> {PID 2, PID 5}`

means those processes are waiting for the simulated artifact disk.

When the event completes, the relevant PIDs are moved from the wait queue to the ready queue.

This structure demonstrates an important scheduler principle: runnable and non-runnable processes need different queueing structures because their eligibility for CPU execution differs.

## Termination

Termination changes the process into a non-runnable terminal state.

The examples perform cleanup such as:

- removing the PID from the ready queue;
- removing it from blocked queues;
- releasing resources owned by the process;
- recording the exit code;
- recording termination time;
- notifying a waiting parent when appropriate.

A terminated process cannot be dispatched again.

The PCB may remain available for accounting and lifecycle inspection even though the process itself no longer executes.

This distinction is useful when reasoning about process termination versus immediate destruction of every associated data structure.

## Python Implementation

The Python implementation is a complete process-management simulator built around `ProcessControlBlock` and `ProcessManager`.

### PCB representation

The Python `ProcessControlBlock` uses a dataclass so that process-management state is represented explicitly.

It contains identity, scheduling information, CPU context, relationships, resource ownership, accounting information, and lifecycle history.

The `CPUContext` class separates processor state from broader process-management metadata.

### State validation

`ProcessManager.VALID_TRANSITIONS` defines the legal state graph.

The `transition()` and `transition_without_queue()` methods reject invalid transitions.

This is important because changing a state without updating the scheduler queues can produce an internally inconsistent system.

### Scheduler structures

The Python implementation maintains:

- `pcbs` for process identity and PCB lookup;
- `ready_queue` for runnable processes;
- `blocked` for event-specific waiting processes;
- `resources` for resource ownership;
- `current_pid` for the running process.

The `validate_invariants()` method checks that these structures agree.

### Lifecycle simulation

`cpu_step()` advances one simulated CPU tick.

It updates CPU accounting and simulated register state, then determines whether the process:

- finishes;
- blocks for I/O;
- gets preempted;
- continues running.

The `run()` method repeatedly advances the simulation and periodically completes simulated disk I/O.

### Parent-child waiting

`wait_for_child()` models a parent waiting for a specific child or any child.

Child termination can wake the parent and return it to the ready queue.

### Resource handling

Resources are represented explicitly through the `Resource` class.

A process can acquire a free resource and the resource records its owner PID.

The PCB simultaneously records the resource identifier in `owned_resources`.

The invariant checker verifies that both representations agree.

### Error handling

The simulator rejects conditions such as:

- empty process names;
- invalid priorities;
- non-positive CPU bursts;
- unknown PIDs;
- unknown resources;
- illegal state transitions;
- invalid parent-child relationships;
- attempts to release resources not owned by a process.

These failures illustrate why kernel process management cannot safely treat lifecycle state as unrestricted application data.

## JavaScript Implementation

The JavaScript implementation provides an event-driven representation of the same process-management concepts while using mechanisms natural to Node.js.

### Map and Set based process management

The PCB table is a `Map`, child relationships use `Set`, and blocked resources use sets of PIDs.

This makes JavaScript's collection model directly visible in the process-management structures.

### Event-driven lifecycle

`ProcessManager` extends `EventTarget`.

Lifecycle operations dispatch `process-event` events.

The example listener observes creation and termination events without being embedded inside the process-management operation itself.

This provides a useful representation of event-driven operating-system behavior.

A real operating system uses kernel event mechanisms, interrupts, wait queues, and scheduler interactions rather than JavaScript `EventTarget`, but the architectural idea of state changes producing observable events is relevant.

### JavaScript-specific validation

The implementation validates types and values with checks such as:

- `typeof`;
- `Number.isInteger`;
- range validation;
- explicit `Error`, `TypeError`, and `RangeError` handling.

The code avoids assuming that JavaScript objects automatically enforce process-state invariants.

### Asynchronous application boundary

The top-level `main()` function is asynchronous and handles failure with a rejected-promise catch.

The process simulator itself remains deterministic and synchronous because the purpose is to model lifecycle behavior rather than depend on wall-clock timing.

This separation prevents actual JavaScript event-loop timing from being confused with simulated CPU scheduling time.

## C++ Case Study

The C++ implementation models a build-service system.

A parent `build-service` process creates child processes such as:

- `build-worker-A`;
- `build-worker-B`;
- `monitor`.

Each build worker has its own PCB, CPU context, priority, lifecycle history, and resource ownership.

### Scenario architecture

The case study contains:

`ProcessManager`

which manages:

`PCB table -> scheduler -> ready queue -> blocked queues -> resources -> lifecycle events`

The build service acts as a parent process.

Build workers represent independent processing tasks.

The simulated `artifact-disk` causes build workers to block periodically, allowing the example to demonstrate I/O-related lifecycle transitions.

### Data structures

The C++ implementation uses:

- `std::map` for PID-to-PCB lookup;
- `std::deque` for the ready queue;
- `std::map<std::string, std::set<int>>` for event-specific blocked queues;
- `std::set` for child relationships;
- `std::set<std::string>` for PCB resource ownership;
- `std::optional` for values that may legitimately be absent;
- `std::vector` for lifecycle history and event logs.

These choices make the ownership and lifecycle relationships explicit.

### Build compiler resource

`compiler-slot` represents an exclusive resource.

Build worker A can acquire it.

Build worker B cannot acquire it while A owns it.

The resource stores its owner PID while the PCB stores the corresponding resource identifier.

The invariant checker verifies that these two representations remain synchronized.

### Build artifact I/O

Build workers periodically request simulated artifact storage.

The transition is:

`RUNNING -> BLOCKED`

The worker enters the `artifact-disk` wait queue.

When the disk event completes, the worker moves to:

`BLOCKED -> READY`

The scheduler can then dispatch it again.

This makes I/O waiting distinct from scheduler preemption.

### Parent waiting

The service process waits for build worker A.

The service process becomes blocked.

When the child terminates, the process manager checks the parent's wait condition and moves the parent to the ready queue.

The example therefore connects process hierarchy and lifecycle state without treating parent-child relationships as merely descriptive metadata.

### C++ lifecycle safety

The `legalTransition()` function defines the allowed state graph.

`changeState()` is the controlled state-changing mechanism.

This design prevents individual operations from silently creating states that the scheduler does not understand.

The `validateInvariants()` function checks:

- single-CPU execution;
- agreement between `currentPid` and the running PCB;
- consistency of the ready queue;
- resource ownership consistency.

These checks represent the kind of consistency requirements that are essential in process-management code.

## Distinguishing the Core Mechanisms

| Mechanism | Primary responsibility | Example in this project |
|---|---|---|
| Process | Represents an active execution instance | `build-worker-A` |
| PCB | Stores management and execution metadata | `ProcessControlBlock` |
| Process state | Describes current lifecycle condition | `READY`, `RUNNING`, `BLOCKED` |
| Scheduler | Selects a runnable process | Priority-based dispatch |
| Ready queue | Holds processes eligible for CPU allocation | `readyQueue` |
| Blocked queue | Holds processes waiting for an event | `artifact-disk` wait queue |
| Context | Preserves resumable CPU state | Program counter and registers |
| Parent-child relationship | Connects process lifecycles | Build service and workers |
| Resource ownership | Associates kernel-managed resources with processes | `compiler-slot` |
| Termination | Ends execution and performs cleanup | Exit code and resource release |

These mechanisms overlap operationally but should not be treated as synonyms.

A PCB records state; it is not itself the state.

The scheduler uses state and scheduling metadata; it does not replace the PCB.

A blocked queue identifies processes waiting for a particular event; it is not another process state.

## Preemption Versus Blocking

Preemption and blocking both remove a process from the CPU, but their causes are different.

### Preemption

The process remains capable of executing.

The scheduler removes it because another process should receive CPU time.

The lifecycle is:

`RUNNING -> READY`

The process remains in the ready queue.

### Blocking

The process cannot proceed until an event occurs.

The lifecycle is:

`RUNNING -> BLOCKED`

The process is placed on an appropriate wait queue.

Only when the awaited event completes does it return to:

`BLOCKED -> READY`

This distinction is one of the most important concepts in process-state reasoning.

## Common Lifecycle Failure Modes

### Invalid state transitions

Allowing arbitrary state changes can produce impossible conditions such as a terminated process becoming runnable again.

The implementations prevent this through explicit transition tables.

### Stale ready-queue entries

A PID can remain in a ready queue after its PCB becomes running or terminated if queue management is not coordinated with state changes.

The invariant checks detect this inconsistency.

### Multiple running processes on a single CPU

A single-CPU scheduler should not simultaneously identify multiple processes as running.

The implementations explicitly validate this condition.

A multiprocessor operating system changes the rule to allow one running process per available CPU, but the educational model intentionally uses one CPU.

### Lost blocked processes

If a blocked PID is removed from all scheduler structures without being associated with a wake-up event, it may never return to execution.

The event-specific blocked queues prevent that class of bookkeeping error in the simulator.

### Resource ownership leaks

A terminated process must not retain an exclusive resource indefinitely.

The implementations release owned resources during termination.

### Parent-child wait errors

A parent should not wait for a PID that is not actually its child.

The examples validate the parent-child relationship before accepting a child-specific wait.

## Performance Considerations

The implementations are educational simulations rather than production schedulers.

Priority selection scans the ready queue.

If there are `n` ready processes, selecting the minimum priority process can require `O(n)` work.

A production scheduler can use more specialized data structures and policies depending on workload and operating-system requirements.

Lifecycle-history storage grows with the number of state transitions.

Event logs similarly consume memory as simulation duration increases.

Resource lookup is kept separate from scheduling lookup so that the process table does not need to encode every resource-management operation directly.

The C++ implementation uses ordered maps and sets, which provide predictable logarithmic lookup characteristics. Different production designs may use hash tables, intrusive lists, per-CPU structures, heaps, trees, or specialized scheduler queues.

## Security and Isolation Considerations

A process-management model must not treat process identity as a security boundary by itself.

A PID identifies a process, but authorization decisions normally require additional identity and credential information.

Real operating systems also enforce memory isolation so that one process cannot arbitrarily read or modify another process's address space.

Resource ownership must be validated against the actual process identity rather than trusting a caller-provided process name.

The examples demonstrate this principle by requiring a valid PID and checking ownership before releasing a resource.

Production process management also has to account for privilege boundaries, namespaces or equivalent isolation mechanisms, signal permissions, file-descriptor access, resource limits, and protection against denial-of-service conditions.

## Debugging the Lifecycle

A useful debugging strategy is to inspect three things together:

`PCB state + scheduler queue membership + lifecycle event`

For example, if a process is marked `READY` but does not appear in the ready queue, the process manager is inconsistent.

If a process is marked `BLOCKED` but has no associated wait event, the scheduler may have no mechanism to wake it.

If a process is marked `RUNNING` while `currentPid` identifies another process, the CPU ownership model is inconsistent.

The Python and C++ implementations provide explicit invariant validation for these conditions.

Lifecycle histories also make state transitions observable rather than forcing debugging to rely only on the final state.

## Production Considerations

A real operating-system process manager contains substantially more machinery than these simulations.

Important areas not fully reproduced here include:

- virtual-memory mappings;
- page tables and address-space identifiers;
- kernel stacks;
- file descriptor tables;
- credentials and security contexts;
- signal handling;
- interprocess communication;
- namespaces and isolation;
- process groups and sessions;
- multithreaded processes;
- symmetric multiprocessing;
- CPU affinity;
- real-time scheduling;
- accounting and resource limits;
- kernel synchronization;
- hardware interrupts;
- system calls;
- architecture-specific context switching.

The simplified model isolates the lifecycle concepts so that the relationship between process identity, PCB state, scheduling, blocking, and termination remains visible.

## Relationship Between the Three Implementations

The implementations intentionally emphasize different aspects of the same operating-system model.

The Python program is the most explicit simulator. It emphasizes lifecycle operations, PCB fields, resource ownership, parent-child relationships, state validation, and scheduler behavior.

The JavaScript program emphasizes event-driven lifecycle changes, JavaScript collection types, event dispatch, and application-style state management.

The C++ program presents a coherent build-service case study where process management is tied to compiler resources, artifact storage, parent-child coordination, CPU scheduling, and invariant validation.

The underlying lifecycle remains consistent:

`NEW -> READY -> RUNNING`

with execution-dependent transitions:

`RUNNING -> READY`

`RUNNING -> BLOCKED -> READY`

and eventual termination:

`RUNNING -> TERMINATED`

The important architectural boundary is that the PCB represents the process-management state, while scheduler queues, blocked queues, resources, and lifecycle events operate around that state to coordinate execution.
