"""
Processes: Process Concept, PCB, Process States, and Process Lifecycle
=======================================================================

A self-contained operating-system process simulator.

This program models:
- Process creation and termination
- Process Control Blocks (PCBs)
- Process states and legal state transitions
- Parent/child relationships
- Ready and blocked queues
- CPU dispatch and preemption
- Blocking for I/O and subsequent wake-up
- Context switching
- Process lifecycle events
- Resource ownership
- Waiting for child processes
- Process statistics and lifecycle tracing

The simulator is intentionally implemented without operating-system-specific
packages so that the mechanisms can be inspected and executed directly.

It models operating-system concepts rather than attempting to replace the
actual process scheduler of the host operating system.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Deque, Dict, Iterable, List, Optional, Set, Tuple


class ProcessState(Enum):
    """States used by the process lifecycle model."""

    NEW = "NEW"
    READY = "READY"
    RUNNING = "RUNNING"
    BLOCKED = "BLOCKED"
    TERMINATED = "TERMINATED"


class EventType(Enum):
    """Events that can change process lifecycle state."""

    CREATE = "CREATE"
    DISPATCH = "DISPATCH"
    PREEMPT = "PREEMPT"
    BLOCK = "BLOCK"
    WAKE = "WAKE"
    EXIT = "EXIT"
    WAIT = "WAIT"
    SIGNAL = "SIGNAL"


@dataclass
class CPUContext:
    """
    Represents the CPU-related portion of a process's saved execution context.

    A real operating system saves architecture-specific registers and control
    information. The simulator keeps representative values instead of actual
    machine registers.
    """

    program_counter: int = 0
    stack_pointer: int = 0
    base_pointer: int = 0
    general_registers: Dict[str, int] = field(
        default_factory=lambda: {"R0": 0, "R1": 0, "R2": 0, "R3": 0}
    )
    flags: int = 0

    def snapshot(self) -> Dict[str, object]:
        """Return a serializable representation of the CPU context."""
        return {
            "PC": self.program_counter,
            "SP": self.stack_pointer,
            "BP": self.base_pointer,
            "registers": dict(self.general_registers),
            "flags": self.flags,
        }


@dataclass
class Resource:
    """Represents a resource that can be owned by a process."""

    resource_id: str
    resource_type: str
    owner_pid: Optional[int] = None


@dataclass
class ProcessControlBlock:
    """
    Process Control Block (PCB).

    The PCB is the kernel's process-management record. A real PCB contains
    considerably more architecture- and kernel-specific information. This
    model includes representative fields needed to explain process identity,
    state, scheduling, context, resources, relationships, and accounting.
    """

    pid: int
    parent_pid: Optional[int]
    name: str
    state: ProcessState = ProcessState.NEW

    priority: int = 5
    time_slice: int = 3
    remaining_burst: int = 1

    cpu: CPUContext = field(default_factory=CPUContext)

    children: Set[int] = field(default_factory=set)
    exit_code: Optional[int] = None

    pending_io: Optional[str] = None
    waiting_for_child: Optional[int] = None

    owned_resources: Set[str] = field(default_factory=set)

    cpu_ticks: int = 0
    ready_ticks: int = 0
    blocked_ticks: int = 0
    context_switches: int = 0

    created_at: int = 0
    started_at: Optional[int] = None
    terminated_at: Optional[int] = None

    state_history: List[Tuple[int, ProcessState]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.state_history.append((self.created_at, self.state))

    def record_state(self, tick: int, new_state: ProcessState) -> None:
        """Record a lifecycle transition."""
        self.state = new_state
        self.state_history.append((tick, new_state))

    def summary(self) -> str:
        """Return a concise PCB representation."""
        return (
            f"PID={self.pid} name={self.name!r} parent={self.parent_pid} "
            f"state={self.state.value} priority={self.priority} "
            f"cpu_ticks={self.cpu_ticks} owned={sorted(self.owned_resources)}"
        )


@dataclass
class LifecycleEvent:
    """A timestamped event in the simulated process lifecycle."""

    tick: int
    event_type: EventType
    pid: int
    detail: str


class ProcessManager:
    """
    Simulated kernel process manager.

    The manager owns the PCB table and implements lifecycle transitions.
    It deliberately validates transitions instead of allowing arbitrary state
    mutation, because operating-system process states have defined semantics.
    """

    VALID_TRANSITIONS = {
        ProcessState.NEW: {ProcessState.READY, ProcessState.TERMINATED},
        ProcessState.READY: {ProcessState.RUNNING, ProcessState.TERMINATED},
        ProcessState.RUNNING: {
            ProcessState.READY,
            ProcessState.BLOCKED,
            ProcessState.TERMINATED,
        },
        ProcessState.BLOCKED: {ProcessState.READY, ProcessState.TERMINATED},
        ProcessState.TERMINATED: set(),
    }

    def __init__(self) -> None:
        self.pcbs: Dict[int, ProcessControlBlock] = {}
        self.ready_queue: Deque[int] = deque()
        self.blocked: Dict[str, Set[int]] = defaultdict(set)
        self.resources: Dict[str, Resource] = {}

        self.current_pid: Optional[int] = None
        self.next_pid = 1
        self.tick = 0

        self.events: List[LifecycleEvent] = []
        self.context_switch_count = 0

    def log(self, event_type: EventType, pid: int, detail: str) -> None:
        """Record a kernel-like lifecycle event."""
        self.events.append(
            LifecycleEvent(
                tick=self.tick,
                event_type=event_type,
                pid=pid,
                detail=detail,
            )
        )

    def create_process(
        self,
        name: str,
        parent_pid: Optional[int] = None,
        priority: int = 5,
        cpu_burst: int = 5,
    ) -> int:
        """
        Create a process and its PCB.

        A newly created process starts in NEW and is then admitted into READY.
        This models the distinction between creation and scheduler admission.
        """
        if parent_pid is not None:
            parent = self.pcbs.get(parent_pid)
            if parent is None:
                raise ValueError(f"Parent PID {parent_pid} does not exist.")
            if parent.state == ProcessState.TERMINATED:
                raise ValueError("A terminated process cannot create a child.")

        if not name.strip():
            raise ValueError("Process name cannot be empty.")

        if not 1 <= priority <= 10:
            raise ValueError("Priority must be between 1 and 10.")

        if cpu_burst <= 0:
            raise ValueError("CPU burst must be positive.")

        pid = self.next_pid
        self.next_pid += 1

        pcb = ProcessControlBlock(
            pid=pid,
            parent_pid=parent_pid,
            name=name,
            priority=priority,
            time_slice=3,
            remaining_burst=cpu_burst,
            created_at=self.tick,
        )

        self.pcbs[pid] = pcb
        self.log(EventType.CREATE, pid, f"created process {name!r}")

        if parent_pid is not None:
            self.pcbs[parent_pid].children.add(pid)

        self.transition(pid, ProcessState.READY, "admitted to ready queue")

        return pid

    def transition(
        self,
        pid: int,
        new_state: ProcessState,
        reason: str,
    ) -> None:
        """Perform and validate a process-state transition."""
        pcb = self.get_pcb(pid)
        old_state = pcb.state

        if new_state not in self.VALID_TRANSITIONS[old_state]:
            raise RuntimeError(
                f"Illegal transition for PID {pid}: "
                f"{old_state.value} -> {new_state.value}"
            )

        pcb.record_state(self.tick, new_state)

        if new_state == ProcessState.READY:
            self.ready_queue.append(pid)

        if new_state == ProcessState.TERMINATED:
            pcb.terminated_at = self.tick

        self.log(
            EventType.SIGNAL,
            pid,
            f"{old_state.value} -> {new_state.value}: {reason}",
        )

    def get_pcb(self, pid: int) -> ProcessControlBlock:
        """Retrieve a PCB or raise a clear error."""
        try:
            return self.pcbs[pid]
        except KeyError as exc:
            raise KeyError(f"Unknown PID {pid}.") from exc

    def dispatch(self) -> Optional[int]:
        """
        Select a ready process.

        A priority-aware selection is used. Lower numerical priority values
        represent more urgent processes in this simulator.
        """
        if self.current_pid is not None:
            return self.current_pid

        if not self.ready_queue:
            return None

        candidates = list(self.ready_queue)
        selected = min(
            candidates,
            key=lambda pid: (
                self.pcbs[pid].priority,
                self.pcbs[pid].created_at,
            ),
        )

        self.ready_queue.remove(selected)

        pcb = self.get_pcb(selected)
        self.current_pid = selected

        if pcb.started_at is None:
            pcb.started_at = self.tick

        self.transition_without_queue(pid=selected, new_state=ProcessState.RUNNING)

        pcb.context_switches += 1
        self.context_switch_count += 1

        self.log(
            EventType.DISPATCH,
            selected,
            f"dispatched {pcb.name!r} to CPU",
        )

        return selected

    def transition_without_queue(
        self,
        pid: int,
        new_state: ProcessState,
    ) -> None:
        """Change state without automatically adding to the ready queue."""
        pcb = self.get_pcb(pid)
        old_state = pcb.state

        if new_state not in self.VALID_TRANSITIONS[old_state]:
            raise RuntimeError(
                f"Illegal transition for PID {pid}: "
                f"{old_state.value} -> {new_state.value}"
            )

        pcb.record_state(self.tick, new_state)

    def preempt_current(self, reason: str = "time slice expired") -> None:
        """Move the running process back to READY."""
        if self.current_pid is None:
            return

        pid = self.current_pid
        pcb = self.get_pcb(pid)

        self.transition_without_queue(pid, ProcessState.READY)
        self.ready_queue.append(pid)

        self.current_pid = None

        self.log(EventType.PREEMPT, pid, reason)

    def block_current(self, io_device: str) -> None:
        """
        Block the running process because it cannot continue until an external
        event, normally I/O completion, occurs.
        """
        if self.current_pid is None:
            raise RuntimeError("No process is running.")

        if not io_device.strip():
            raise ValueError("I/O device name cannot be empty.")

        pid = self.current_pid
        pcb = self.get_pcb(pid)

        self.transition_without_queue(pid, ProcessState.BLOCKED)

        pcb.pending_io = io_device
        self.blocked[io_device].add(pid)

        self.current_pid = None

        self.log(
            EventType.BLOCK,
            pid,
            f"blocked waiting for {io_device}",
        )

    def complete_io(self, io_device: str) -> List[int]:
        """
        Wake every process waiting for the specified I/O event.

        In an actual OS, device completion and wake-up are coordinated by
        interrupt handlers and kernel scheduling structures.
        """
        if io_device not in self.blocked:
            return []

        awakened: List[int] = []

        for pid in sorted(self.blocked[io_device]):
            pcb = self.get_pcb(pid)

            if pcb.state != ProcessState.BLOCKED:
                continue

            pcb.pending_io = None
            self.transition_without_queue(pid, ProcessState.READY)
            self.ready_queue.append(pid)

            self.log(
                EventType.WAKE,
                pid,
                f"I/O completed on {io_device}",
            )

            awakened.append(pid)

        self.blocked.pop(io_device, None)
        return awakened

    def acquire_resource(self, pid: int, resource_id: str) -> bool:
        """
        Acquire a resource if it is free.

        A real kernel may block a process rather than simply returning False.
        The explicit result makes contention visible in this educational model.
        """
        pcb = self.get_pcb(pid)

        if resource_id not in self.resources:
            raise KeyError(f"Unknown resource {resource_id}.")

        resource = self.resources[resource_id]

        if resource.owner_pid is None:
            resource.owner_pid = pid
            pcb.owned_resources.add(resource_id)
            return True

        return resource.owner_pid == pid

    def release_resource(self, pid: int, resource_id: str) -> None:
        """Release a resource only if the specified process owns it."""
        pcb = self.get_pcb(pid)

        if resource_id not in self.resources:
            raise KeyError(f"Unknown resource {resource_id}.")

        resource = self.resources[resource_id]

        if resource.owner_pid != pid:
            raise PermissionError(
                f"PID {pid} does not own resource {resource_id}."
            )

        resource.owner_pid = None
        pcb.owned_resources.discard(resource_id)

    def add_resource(self, resource_id: str, resource_type: str) -> None:
        """Register a resource managed by the simulator."""
        if resource_id in self.resources:
            raise ValueError(f"Resource {resource_id} already exists.")

        self.resources[resource_id] = Resource(
            resource_id=resource_id,
            resource_type=resource_type,
        )

    def wait_for_child(self, parent_pid: int, child_pid: Optional[int] = None) -> None:
        """
        Model a parent waiting for child termination.

        If the requested child has already terminated, the wait returns
        immediately. Otherwise the parent is blocked in a waiting state.
        """
        parent = self.get_pcb(parent_pid)

        if parent.state == ProcessState.TERMINATED:
            raise RuntimeError("A terminated process cannot wait.")

        if child_pid is not None:
            if child_pid not in parent.children:
                raise ValueError(
                    f"PID {child_pid} is not a child of PID {parent_pid}."
                )

            child = self.get_pcb(child_pid)
            if child.state == ProcessState.TERMINATED:
                return

        parent.waiting_for_child = child_pid

        if self.current_pid == parent_pid:
            self.transition_without_queue(
                parent_pid,
                ProcessState.BLOCKED,
            )
            self.current_pid = None

        self.log(
            EventType.WAIT,
            parent_pid,
            f"waiting for child {child_pid if child_pid else 'any child'}",
        )

    def terminate_process(self, pid: int, exit_code: int = 0) -> None:
        """
        Terminate a process and clean up simulator bookkeeping.

        Child processes are not automatically terminated. Real systems vary:
        some process models reparent surviving children while others provide
        supervision-specific behavior.
        """
        pcb = self.get_pcb(pid)

        if pcb.state == ProcessState.TERMINATED:
            return

        if self.current_pid == pid:
            self.current_pid = None

        if pid in self.ready_queue:
            self.ready_queue.remove(pid)

        for waiting_set in self.blocked.values():
            waiting_set.discard(pid)

        for resource_id in list(pcb.owned_resources):
            self.release_resource(pid, resource_id)

        old_state = pcb.state

        if ProcessState.TERMINATED not in self.VALID_TRANSITIONS[old_state]:
            raise RuntimeError(
                f"Cannot terminate PID {pid} from {old_state.value}."
            )

        pcb.exit_code = exit_code
        pcb.record_state(self.tick, ProcessState.TERMINATED)
        pcb.terminated_at = self.tick

        self.log(
            EventType.EXIT,
            pid,
            f"process exited with code {exit_code}",
        )

        parent_pid = pcb.parent_pid

        if parent_pid is not None and parent_pid in self.pcbs:
            parent = self.pcbs[parent_pid]

            if (
                parent.state == ProcessState.BLOCKED
                and (
                    parent.waiting_for_child is None
                    or parent.waiting_for_child == pid
                )
            ):
                parent.waiting_for_child = None
                self.transition_without_queue(
                    parent_pid,
                    ProcessState.READY,
                )
                self.ready_queue.append(parent_pid)

                self.log(
                    EventType.WAKE,
                    parent_pid,
                    f"child PID {pid} terminated",
                )

    def cpu_step(self) -> Optional[int]:
        """
        Execute one simulated CPU tick.

        The process either continues, blocks, terminates, or is preempted.
        """
        if self.current_pid is None:
            self.dispatch()

        if self.current_pid is None:
            self.tick += 1
            self.account_idle_tick()
            return None

        pid = self.current_pid
        pcb = self.get_pcb(pid)

        pcb.cpu_ticks += 1
        pcb.remaining_burst -= 1
        pcb.cpu.program_counter += 4
        pcb.cpu.general_registers["R0"] += 1

        self.tick += 1

        if pcb.remaining_burst <= 0:
            self.terminate_process(pid, exit_code=0)
            return pid

        if pcb.cpu_ticks % 4 == 0 and pcb.name.lower().find("io") >= 0:
            self.block_current("disk")
            return pid

        if pcb.cpu_ticks % pcb.time_slice == 0:
            self.preempt_current()
            return pid

        return pid

    def account_idle_tick(self) -> None:
        """Account one tick for processes waiting in non-running states."""
        for pcb in self.pcbs.values():
            if pcb.state == ProcessState.READY:
                pcb.ready_ticks += 1
            elif pcb.state == ProcessState.BLOCKED:
                pcb.blocked_ticks += 1

    def run(self, max_ticks: int = 100) -> None:
        """Run the scheduler until no runnable work remains or the limit expires."""
        if max_ticks <= 0:
            raise ValueError("max_ticks must be positive.")

        for _ in range(max_ticks):
            active_before = [
                pcb
                for pcb in self.pcbs.values()
                if pcb.state != ProcessState.TERMINATED
            ]

            if not active_before:
                break

            self.cpu_step()

            # Simulate periodic device completion for blocked I/O.
            if self.tick % 3 == 0:
                self.complete_io("disk")

    def process_tree(self, pid: int, depth: int = 0) -> List[str]:
        """Return a textual parent/child process tree."""
        pcb = self.get_pcb(pid)
        lines = [
            f"{'  ' * depth}{pcb.pid} {pcb.name} [{pcb.state.value}]"
        ]

        for child_pid in sorted(pcb.children):
            if child_pid in self.pcbs:
                lines.extend(self.process_tree(child_pid, depth + 1))

        return lines

    def lifecycle_trace(self, pid: int) -> List[str]:
        """Return the recorded state path for one process."""
        pcb = self.get_pcb(pid)

        return [
            f"t={tick}: {state.value}"
            for tick, state in pcb.state_history
        ]

    def validate_invariants(self) -> None:
        """
        Check internal invariants.

        These checks demonstrate an important systems principle: state
        transitions should preserve consistency between the PCB table and
        scheduler queues.
        """
        running = [
            pcb.pid
            for pcb in self.pcbs.values()
            if pcb.state == ProcessState.RUNNING
        ]

        if len(running) > 1:
            raise AssertionError("Single-CPU model has multiple RUNNING processes.")

        if self.current_pid != (running[0] if running else None):
            raise AssertionError("current_pid disagrees with PCB state.")

        ready_members = set(self.ready_queue)

        for pcb in self.pcbs.values():
            if pcb.state == ProcessState.READY and pcb.pid not in ready_members:
                raise AssertionError(
                    f"READY process {pcb.pid} missing from ready queue."
                )

            if pcb.state != ProcessState.READY and pcb.pid in ready_members:
                raise AssertionError(
                    f"Non-READY process {pcb.pid} appears in ready queue."
                )

            if pcb.state == ProcessState.TERMINATED:
                if pcb.pid in self.ready_queue:
                    raise AssertionError(
                        f"Terminated process {pcb.pid} remains runnable."
                    )

        for resource in self.resources.values():
            if resource.owner_pid is not None:
                owner = self.get_pcb(resource.owner_pid)
                if resource.resource_id not in owner.owned_resources:
                    raise AssertionError(
                        "Resource ownership differs between Resource and PCB."
                    )


def print_pcb(pcb: ProcessControlBlock) -> None:
    """Display important PCB fields."""
    print(f"PID:                 {pcb.pid}")
    print(f"Name:                {pcb.name}")
    print(f"Parent PID:          {pcb.parent_pid}")
    print(f"State:               {pcb.state.value}")
    print(f"Priority:            {pcb.priority}")
    print(f"Remaining CPU burst: {pcb.remaining_burst}")
    print(f"CPU ticks:           {pcb.cpu_ticks}")
    print(f"Ready ticks:         {pcb.ready_ticks}")
    print(f"Blocked ticks:       {pcb.blocked_ticks}")
    print(f"Context switches:    {pcb.context_switches}")
    print(f"Program counter:     {pcb.cpu.program_counter}")
    print(f"Owned resources:     {sorted(pcb.owned_resources)}")


def demonstrate_process_states() -> None:
    """Show the canonical process-state model."""
    print("\n=== Process States ===")
    print("NEW       : process is being created/admitted")
    print("READY     : process can execute but is waiting for CPU time")
    print("RUNNING   : process currently owns the CPU")
    print("BLOCKED   : process cannot continue until an event occurs")
    print("TERMINATED: process has finished and no longer executes")

    print("\nTypical transitions:")
    print("NEW -> READY -> RUNNING -> READY")
    print("RUNNING -> BLOCKED -> READY")
    print("RUNNING -> TERMINATED")


def demonstrate_pcb(manager: ProcessManager, pid: int) -> None:
    """Display how the PCB represents process-management information."""
    print("\n=== Process Control Block ===")
    print_pcb(manager.get_pcb(pid))


def demonstrate_scheduler() -> None:
    """Run a realistic multi-process lifecycle simulation."""
    print("\n=== Process Lifecycle Simulation ===")

    manager = ProcessManager()
    manager.add_resource("stdout", "terminal")
    manager.add_resource("db-connection-1", "database connection")

    init_pid = manager.create_process(
        "init",
        priority=2,
        cpu_burst=7,
    )

    worker_pid = manager.create_process(
        "io-worker",
        parent_pid=init_pid,
        priority=4,
        cpu_burst=9,
    )

    service_pid = manager.create_process(
        "service",
        parent_pid=init_pid,
        priority=3,
        cpu_burst=6,
    )

    print("\nInitial process tree:")
    print("\n".join(manager.process_tree(init_pid)))

    print("\nResource acquisition:")
    print(
        f"PID {service_pid} acquires stdout:",
        manager.acquire_resource(service_pid, "stdout"),
    )
    print(
        f"PID {worker_pid} attempts stdout:",
        manager.acquire_resource(worker_pid, "stdout"),
    )

    print("\nScheduler execution:")
    manager.run(max_ticks=30)

    manager.validate_invariants()

    print("\nFinal process states:")
    for pcb in manager.pcbs.values():
        print(pcb.summary())

    print("\nLifecycle traces:")
    for pid in sorted(manager.pcbs):
        print(f"PID {pid}: {' -> '.join(manager.lifecycle_trace(pid))}")

    print("\nKernel event trace:")
    for event in manager.events:
        print(
            f"t={event.tick:02d} "
            f"{event.event_type.value:10s} "
            f"PID={event.pid:02d} "
            f"{event.detail}"
        )

    print("\nContext switches:", manager.context_switch_count)


def demonstrate_parent_wait() -> None:
    """Demonstrate parent-child lifecycle coordination."""
    print("\n=== Parent/Child Wait ===")

    manager = ProcessManager()

    parent = manager.create_process(
        "parent",
        priority=2,
        cpu_burst=10,
    )
    child = manager.create_process(
        "child",
        parent_pid=parent,
        priority=3,
        cpu_burst=2,
    )

    manager.dispatch()

    if manager.current_pid != parent:
        manager.preempt_current("prepare parent wait demonstration")
        manager.dispatch()

    if manager.current_pid == parent:
        manager.wait_for_child(parent, child)

    print("Parent after wait:", manager.get_pcb(parent).state.value)

    manager.dispatch()
    while manager.get_pcb(child).state != ProcessState.TERMINATED:
        manager.cpu_step()

    manager.validate_invariants()

    print("Child after exit:", manager.get_pcb(child).state.value)
    print("Parent after child exit:", manager.get_pcb(parent).state.value)


def demonstrate_invalid_transition() -> None:
    """Show why direct arbitrary state mutation should be prevented."""
    print("\n=== Invalid State Transition Handling ===")

    manager = ProcessManager()
    pid = manager.create_process("validation-demo", cpu_burst=2)

    try:
        manager.transition(pid, ProcessState.BLOCKED, "invalid direct block")
    except RuntimeError as exc:
        print("Rejected invalid transition:", exc)

    manager.validate_invariants()


def demonstrate_context_switch() -> None:
    """
    Demonstrate why a PCB must retain enough CPU context to resume execution.

    The simulation modifies the program counter and registers as the process
    runs. A context switch leaves those values associated with the PCB rather
    than with the CPU globally.
    """
    print("\n=== Context Switching ===")

    manager = ProcessManager()

    first = manager.create_process(
        "compute-A",
        priority=4,
        cpu_burst=5,
    )
    second = manager.create_process(
        "compute-B",
        priority=4,
        cpu_burst=5,
    )

    manager.dispatch()
    manager.cpu_step()

    first_pcb = manager.get_pcb(first)
    print(
        f"After PID {first} runs: "
        f"PC={first_pcb.cpu.program_counter}, "
        f"R0={first_pcb.cpu.general_registers['R0']}"
    )

    manager.preempt_current("explicit context switch")

    manager.dispatch()
    manager.cpu_step()

    second_pcb = manager.get_pcb(second)
    print(
        f"After PID {second} runs: "
        f"PC={second_pcb.cpu.program_counter}, "
        f"R0={second_pcb.cpu.general_registers['R0']}"
    )

    manager.dispatch()
    resumed_first = manager.get_pcb(first)

    print(
        f"PID {first} retained its saved context: "
        f"PC={resumed_first.cpu.program_counter}, "
        f"R0={resumed_first.cpu.general_registers['R0']}"
    )

    manager.validate_invariants()


def demonstrate_edge_cases() -> None:
    """Exercise important process-management validation rules."""
    print("\n=== Edge Cases and Validation ===")

    manager = ProcessManager()

    try:
        manager.create_process("", cpu_burst=2)
    except ValueError as exc:
        print("Empty process name rejected:", exc)

    try:
        manager.create_process("invalid-priority", priority=99, cpu_burst=2)
    except ValueError as exc:
        print("Invalid priority rejected:", exc)

    pid = manager.create_process("resource-owner", cpu_burst=2)
    manager.add_resource("device-1", "exclusive-device")

    manager.dispatch()

    print(
        "Resource acquisition:",
        manager.acquire_resource(pid, "device-1"),
    )

    try:
        manager.release_resource(pid + 999, "device-1")
    except KeyError as exc:
        print("Unknown PID rejected:", exc)

    manager.validate_invariants()


def main() -> None:
    print("PROCESS MANAGEMENT AND LIFECYCLE SIMULATOR")
    print("=" * 50)

    demonstrate_process_states()

    manager = ProcessManager()
    demo_pid = manager.create_process(
        "pcb-demo",
        priority=3,
        cpu_burst=4,
    )
    demonstrate_pcb(manager, demo_pid)

    demonstrate_context_switch()
    demonstrate_scheduler()
    demonstrate_parent_wait()
    demonstrate_invalid_transition()
    demonstrate_edge_cases()

    print("\n=== Demonstration Complete ===")
    print(
        "The simulator separates process identity, process state, CPU context, "
        "scheduler queues, resources, and parent-child lifecycle information."
    )


if __name__ == "__main__":
    main()
