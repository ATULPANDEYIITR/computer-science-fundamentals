"""
Advanced CPU Scheduling Simulator
=================================

Topics:
- Multilevel Queue Scheduling (MLQ)
- Multilevel Feedback Queue Scheduling (MLFQ)
- Context switching
- Queue-specific scheduling policies
- Priority and starvation behavior
- Aging and priority boosts
- Preemption
- CPU bursts and I/O bursts
- Scheduling metrics
- Timeline generation
- Context-switch overhead
- Dispatcher behavior
- Workload comparison

The simulator is intentionally self-contained and uses only the Python standard
library. It models CPU scheduling at discrete time units so that scheduling
decisions, preemptions, context switches, I/O blocking, and queue movement can
be inspected directly.

The model is educational rather than a kernel implementation. Real operating
systems use timer interrupts, hardware-supported context management, kernel
queues, synchronization primitives, and more detailed process states.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import deque
from enum import Enum
from typing import Deque, Dict, List, Optional, Tuple
import statistics


class ProcessState(Enum):
    NEW = "NEW"
    READY = "READY"
    RUNNING = "RUNNING"
    BLOCKED = "BLOCKED"
    TERMINATED = "TERMINATED"


class QueuePolicy(Enum):
    FCFS = "FCFS"
    ROUND_ROBIN = "ROUND_ROBIN"
    PRIORITY = "PRIORITY"


@dataclass
class Burst:
    """
    Alternating CPU and I/O burst description.

    Example:
        CPU 4 -> I/O 3 -> CPU 5

    A process begins with a CPU burst. After the CPU burst completes, the
    process can block for I/O before returning to the ready queues.
    """

    cpu: int
    io: int = 0

    def __post_init__(self) -> None:
        if self.cpu <= 0:
            raise ValueError("CPU burst duration must be positive.")
        if self.io < 0:
            raise ValueError("I/O duration cannot be negative.")


@dataclass
class Process:
    pid: str
    arrival_time: int
    bursts: List[Burst]
    base_priority: int
    queue_level: int = 0

    state: ProcessState = ProcessState.NEW
    burst_index: int = 0
    remaining_cpu: int = 0
    remaining_io: int = 0
    completion_time: Optional[int] = None
    first_run_time: Optional[int] = None
    waiting_time: int = 0
    response_time: Optional[int] = None
    turnaround_time: Optional[int] = None
    cpu_time: int = 0
    context_switches: int = 0
    preemptions: int = 0
    demotions: int = 0
    promotions: int = 0
    ready_since: Optional[int] = None
    total_ready_wait: int = 0

    def __post_init__(self) -> None:
        if not self.pid:
            raise ValueError("Process ID cannot be empty.")
        if self.arrival_time < 0:
            raise ValueError("Arrival time cannot be negative.")
        if not self.bursts:
            raise ValueError(f"{self.pid} must contain at least one CPU burst.")
        if self.base_priority < 0:
            raise ValueError("Priority must be non-negative.")

        self.remaining_cpu = self.bursts[0].cpu

    @property
    def is_complete(self) -> bool:
        return self.burst_index >= len(self.bursts)

    @property
    def current_burst(self) -> Burst:
        return self.bursts[self.burst_index]

    def start_waiting(self, now: int) -> None:
        if self.ready_since is None:
            self.ready_since = now

    def stop_waiting(self, now: int) -> None:
        if self.ready_since is not None:
            waited = max(0, now - self.ready_since)
            self.waiting_time += waited
            self.total_ready_wait += waited
            self.ready_since = None


@dataclass
class QueueConfig:
    name: str
    policy: QueuePolicy
    time_quantum: Optional[int] = None
    priority_order: int = 0

    def __post_init__(self) -> None:
        if self.policy == QueuePolicy.ROUND_ROBIN:
            if self.time_quantum is None or self.time_quantum <= 0:
                raise ValueError(
                    f"Round-robin queue {self.name} requires a positive quantum."
                )


@dataclass
class TimelineEntry:
    start: int
    end: int
    label: str
    kind: str

    @property
    def duration(self) -> int:
        return self.end - self.start


class MLFQScheduler:
    """
    Multilevel Feedback Queue scheduler.

    Queue 0 is the highest-priority queue.

    Example configuration:
        Q0: RR, quantum 2
        Q1: RR, quantum 4
        Q2: FCFS

    Processes that consume an entire time quantum without blocking are
    demoted. Processes that block for I/O keep or regain an interactive
    position depending on the configured policy.

    The implementation also supports periodic priority boosts to prevent
    starvation in lower queues.
    """

    def __init__(
        self,
        processes: List[Process],
        queues: List[QueueConfig],
        context_switch_cost: int = 1,
        boost_interval: Optional[int] = 20,
    ) -> None:
        if not queues:
            raise ValueError("At least one ready queue is required.")
        if context_switch_cost < 0:
            raise ValueError("Context-switch cost cannot be negative.")

        self.processes = {p.pid: p for p in processes}
        self.queues = queues
        self.context_switch_cost = context_switch_cost
        self.boost_interval = boost_interval

        self.ready_queues: List[Deque[str]] = [
            deque() for _ in queues
        ]
        self.blocked: Dict[str, int] = {}
        self.running_pid: Optional[str] = None
        self.current_quantum_used = 0
        self.current_time = 0
        self.last_cpu_pid: Optional[str] = None
        self.timeline: List[TimelineEntry] = []

        self.total_context_switches = 0
        self.total_context_switch_time = 0

    def add_timeline(self, start: int, end: int, label: str, kind: str) -> None:
        if end <= start:
            return

        if (
            self.timeline
            and self.timeline[-1].end == start
            and self.timeline[-1].label == label
            and self.timeline[-1].kind == kind
        ):
            self.timeline[-1].end = end
        else:
            self.timeline.append(
                TimelineEntry(start, end, label, kind)
            )

    def enqueue(self, process: Process, now: int, front: bool = False) -> None:
        process.state = ProcessState.READY
        process.start_waiting(now)

        queue_index = max(0, min(process.queue_level, len(self.ready_queues) - 1))

        if front:
            self.ready_queues[queue_index].appendleft(process.pid)
        else:
            self.ready_queues[queue_index].append(process.pid)

    def admit_arrivals(self, now: int) -> None:
        for process in self.processes.values():
            if process.state == ProcessState.NEW and process.arrival_time <= now:
                self.enqueue(process, now)

    def update_blocked_processes(self, now: int) -> None:
        completed_io = [
            pid for pid, ready_at in self.blocked.items()
            if ready_at <= now
        ]

        for pid in completed_io:
            process = self.processes[pid]
            del self.blocked[pid]

            process.remaining_io = 0

            if process.burst_index + 1 < len(process.bursts):
                process.burst_index += 1
                process.remaining_cpu = process.current_burst.cpu
                self.enqueue(process, now)

    def choose_process(self) -> Optional[Process]:
        for queue_index, queue in enumerate(self.ready_queues):
            if not queue:
                continue

            config = self.queues[queue_index]

            if config.policy in (
                QueuePolicy.FCFS,
                QueuePolicy.ROUND_ROBIN,
            ):
                pid = queue.popleft()
                return self.processes[pid]

            if config.policy == QueuePolicy.PRIORITY:
                candidates = [self.processes[pid] for pid in queue]
                selected = min(
                    candidates,
                    key=lambda p: (p.base_priority, p.ready_since or 0),
                )
                queue.remove(selected.pid)
                return selected

        return None

    def highest_ready_level(self) -> Optional[int]:
        for index, queue in enumerate(self.ready_queues):
            if queue:
                return index
        return None

    def perform_priority_boost(self, now: int) -> None:
        """
        Periodically move waiting processes to the highest queue.

        This addresses starvation that can occur when a lower-priority queue
        is repeatedly denied CPU time by active higher queues.
        """
        if self.boost_interval is None:
            return
        if now == 0 or now % self.boost_interval != 0:
            return

        for queue_index in range(1, len(self.ready_queues)):
            while self.ready_queues[queue_index]:
                pid = self.ready_queues[queue_index].popleft()
                process = self.processes[pid]

                process.queue_level = 0
                process.promotions += 1
                self.ready_queues[0].append(pid)

    def preempt_for_higher_queue(self, now: int) -> None:
        """
        MLFQ is priority-based across queues.

        A process running in Q2 must yield if a process becomes ready in Q0.
        The same applies between Q1 and Q2.
        """
        if self.running_pid is None:
            return

        running = self.processes[self.running_pid]
        highest = self.highest_ready_level()

        if highest is None:
            return

        if highest < running.queue_level:
            running.preemptions += 1
            self.enqueue(running, now, front=False)
            self.running_pid = None
            self.current_quantum_used = 0

    def start_process(self, process: Process, now: int) -> None:
        process.stop_waiting(now)

        if process.first_run_time is None:
            process.first_run_time = now
            process.response_time = now - process.arrival_time

        process.state = ProcessState.RUNNING
        self.running_pid = process.pid
        self.current_quantum_used = 0

        if self.last_cpu_pid != process.pid:
            process.context_switches += 1
            self.total_context_switches += 1

            if self.context_switch_cost:
                self.add_timeline(
                    now,
                    now + self.context_switch_cost,
                    "CONTEXT_SWITCH",
                    "context-switch",
                )
                self.total_context_switch_time += self.context_switch_cost

                # Context-switch time advances the clock in this simulator.
                self.current_time += self.context_switch_cost

        self.last_cpu_pid = process.pid

    def finish_cpu_burst(self, process: Process, now: int) -> None:
        """
        A CPU burst has ended.

        If another burst exists, the process blocks for I/O. Otherwise the
        process terminates.
        """
        process.burst_index += 1

        if process.burst_index >= len(process.bursts):
            process.state = ProcessState.TERMINATED
            process.completion_time = now
            process.turnaround_time = now - process.arrival_time
            self.running_pid = None
            self.current_quantum_used = 0
            return

        io_duration = process.bursts[process.burst_index - 1].io

        if io_duration > 0:
            process.state = ProcessState.BLOCKED
            process.remaining_io = io_duration
            self.blocked[process.pid] = now + io_duration
            self.running_pid = None
            self.current_quantum_used = 0

            # Interactive/I/O-bound behavior is favored by resetting its
            # queue level when it gives up the CPU before consuming a full
            # quantum.
            if process.queue_level > 0:
                process.queue_level -= 1
                process.promotions += 1
        else:
            process.remaining_cpu = process.current_burst.cpu
            self.enqueue(process, now)
            self.running_pid = None
            self.current_quantum_used = 0

    def execute_one_tick(self, now: int) -> None:
        if self.running_pid is None:
            return

        process = self.processes[self.running_pid]
        process.remaining_cpu -= 1
        process.cpu_time += 1
        self.current_quantum_used += 1

        if process.remaining_cpu == 0:
            self.finish_cpu_burst(process, now + 1)
            return

        queue = self.queues[process.queue_level]

        if (
            queue.policy == QueuePolicy.ROUND_ROBIN
            and self.current_quantum_used >= queue.time_quantum
        ):
            if process.queue_level < len(self.queues) - 1:
                process.queue_level += 1
                process.demotions += 1

            process.preemptions += 1
            self.enqueue(process, now + 1)
            self.running_pid = None
            self.current_quantum_used = 0

    def run(self, max_time: int = 10_000) -> None:
        """
        Execute the scheduler until every process terminates.

        max_time protects the simulation from accidental infinite loops.
        """
        if not self.processes:
            return

        while self.current_time <= max_time:
            if all(
                process.state == ProcessState.TERMINATED
                for process in self.processes.values()
            ):
                break

            self.admit_arrivals(self.current_time)
            self.update_blocked_processes(self.current_time)
            self.perform_priority_boost(self.current_time)
            self.preempt_for_higher_queue(self.current_time)

            if self.running_pid is None:
                selected = self.choose_process()

                if selected is not None:
                    previous_time = self.current_time
                    self.start_process(selected, self.current_time)

                    if self.current_time > previous_time:
                        continue

            if self.running_pid is not None:
                pid = self.running_pid
                self.add_timeline(
                    self.current_time,
                    self.current_time + 1,
                    pid,
                    f"queue-{self.processes[pid].queue_level}",
                )
                self.execute_one_tick(self.current_time)
                self.current_time += 1
            else:
                # No process can execute. This represents idle CPU time.
                self.add_timeline(
                    self.current_time,
                    self.current_time + 1,
                    "IDLE",
                    "idle",
                )
                self.current_time += 1
        else:
            raise RuntimeError(
                "Simulation exceeded max_time. Check workload or scheduler configuration."
            )

    def metrics(self) -> Dict[str, float]:
        completed = [
            p for p in self.processes.values()
            if p.completion_time is not None
        ]

        if not completed:
            return {}

        turnaround = [
            p.turnaround_time
            for p in completed
            if p.turnaround_time is not None
        ]

        waiting = [p.waiting_time for p in completed]

        response = [
            p.response_time
            for p in completed
            if p.response_time is not None
        ]

        total_cpu = sum(p.cpu_time for p in completed)
        total_elapsed = max(
            p.completion_time for p in completed
        ) - min(p.arrival_time for p in completed)

        return {
            "average_waiting_time": statistics.mean(waiting),
            "average_turnaround_time": statistics.mean(turnaround),
            "average_response_time": statistics.mean(response),
            "throughput": len(completed) / max(1, total_elapsed),
            "cpu_utilization_percent": (
                100.0 * total_cpu / max(1, self.current_time)
            ),
            "context_switches": float(self.total_context_switches),
            "context_switch_time": float(self.total_context_switch_time),
        }

    def print_timeline(self) -> None:
        print("\nCPU TIMELINE")
        print("-" * 78)

        for entry in self.timeline:
            print(
                f"[{entry.start:>3} -> {entry.end:>3}] "
                f"{entry.label:<16} "
                f"{entry.kind}"
            )

    def print_process_report(self) -> None:
        print("\nPROCESS REPORT")
        print("-" * 100)

        header = (
            f"{'PID':<8}"
            f"{'Queue':<8}"
            f"{'State':<13}"
            f"{'CPU':<7}"
            f"{'Wait':<7}"
            f"{'Turn':<7}"
            f"{'Resp':<7}"
            f"{'Preempt':<9}"
            f"{'Demote':<8}"
            f"{'Promote':<9}"
        )
        print(header)
        print("-" * 100)

        for process in self.processes.values():
            print(
                f"{process.pid:<8}"
                f"Q{process.queue_level:<7}"
                f"{process.state.value:<13}"
                f"{process.cpu_time:<7}"
                f"{process.waiting_time:<7}"
                f"{str(process.turnaround_time):<7}"
                f"{str(process.response_time):<7}"
                f"{process.preemptions:<9}"
                f"{process.demotions:<8}"
                f"{process.promotions:<9}"
            )

    def print_metrics(self) -> None:
        print("\nSCHEDULING METRICS")
        print("-" * 40)

        for name, value in self.metrics().items():
            if "percent" in name:
                print(f"{name:<30}: {value:.2f}%")
            elif "throughput" in name:
                print(f"{name:<30}: {value:.4f}")
            else:
                print(f"{name:<30}: {value:.2f}")


class SimpleMLQScheduler:
    """
    Multilevel Queue scheduler.

    Unlike MLFQ, queue assignment is static. A process does not move between
    queues because of observed CPU behavior.

    Example:
        System queue: priority / FCFS
        Interactive queue: round-robin
        Batch queue: FCFS

    Higher queue levels always receive CPU preference.
    """

    def __init__(
        self,
        processes: List[Process],
        queues: List[QueueConfig],
        context_switch_cost: int = 1,
    ) -> None:
        self.processes = {p.pid: p for p in processes}
        self.queues = queues
        self.context_switch_cost = context_switch_cost
        self.ready: List[Deque[str]] = [deque() for _ in queues]
        self.running: Optional[str] = None
        self.time = 0
        self.timeline: List[TimelineEntry] = []
        self.switches = 0

    def add(self, process: Process) -> None:
        process.state = ProcessState.READY
        self.ready[process.queue_level].append(process.pid)

    def choose(self) -> Optional[Process]:
        for index, queue in enumerate(self.ready):
            if not queue:
                continue

            config = self.queues[index]

            if config.policy == QueuePolicy.PRIORITY:
                candidates = [self.processes[pid] for pid in queue]
                selected = min(
                    candidates,
                    key=lambda p: p.base_priority,
                )
                queue.remove(selected.pid)
                return selected

            pid = queue.popleft()
            return self.processes[pid]

        return None

    def run(self) -> None:
        """
        Simplified MLQ model for CPU-only bursts.

        Static queue membership is the defining distinction from MLFQ.
        """
        while any(p.state != ProcessState.TERMINATED for p in self.processes.values()):
            for process in self.processes.values():
                if (
                    process.state == ProcessState.NEW
                    and process.arrival_time <= self.time
                ):
                    self.add(process)

            if self.running is None:
                process = self.choose()

                if process is None:
                    self.timeline.append(
                        TimelineEntry(
                            self.time,
                            self.time + 1,
                            "IDLE",
                            "idle",
                        )
                    )
                    self.time += 1
                    continue

                process.state = ProcessState.RUNNING
                if process.first_run_time is None:
                    process.first_run_time = self.time
                    process.response_time = (
                        self.time - process.arrival_time
                    )

                process.waiting_time += (
                    self.time - (process.ready_since or self.time)
                )
                process.ready_since = None

                self.running = process.pid
                self.switches += 1

                if self.context_switch_cost:
                    self.timeline.append(
                        TimelineEntry(
                            self.time,
                            self.time + self.context_switch_cost,
                            "CONTEXT_SWITCH",
                            "context-switch",
                        )
                    )
                    self.time += self.context_switch_cost

            process = self.processes[self.running]
            process.remaining_cpu -= 1
            process.cpu_time += 1

            self.timeline.append(
                TimelineEntry(
                    self.time,
                    self.time + 1,
                    process.pid,
                    f"queue-{process.queue_level}",
                )
            )

            self.time += 1

            if process.remaining_cpu == 0:
                process.state = ProcessState.TERMINATED
                process.completion_time = self.time
                process.turnaround_time = (
                    self.time - process.arrival_time
                )
                self.running = None


def make_workload() -> List[Process]:
    """
    Realistic mixed workload:

    - SHELL behaves interactively and performs short CPU bursts.
    - API is a latency-sensitive service process with I/O waits.
    - COMPILER is CPU-heavy and therefore experiences MLFQ demotion.
    - BACKUP is a long batch job and naturally remains in a lower queue.
    - LOGGER produces periodic short bursts.
    """

    return [
        Process(
            pid="SHELL",
            arrival_time=0,
            bursts=[
                Burst(cpu=2, io=5),
                Burst(cpu=1, io=4),
                Burst(cpu=2),
            ],
            base_priority=1,
        ),
        Process(
            pid="API",
            arrival_time=1,
            bursts=[
                Burst(cpu=3, io=3),
                Burst(cpu=2, io=4),
                Burst(cpu=2),
            ],
            base_priority=2,
        ),
        Process(
            pid="COMPILER",
            arrival_time=0,
            bursts=[
                Burst(cpu=10),
            ],
            base_priority=5,
        ),
        Process(
            pid="BACKUP",
            arrival_time=2,
            bursts=[
                Burst(cpu=14),
            ],
            base_priority=8,
        ),
        Process(
            pid="LOGGER",
            arrival_time=4,
            bursts=[
                Burst(cpu=1, io=6),
                Burst(cpu=1, io=5),
                Burst(cpu=1),
            ],
            base_priority=3,
        ),
    ]


def clone_workload(processes: List[Process]) -> List[Process]:
    """
    Build independent process objects for comparing scheduler configurations.
    """
    return [
        Process(
            pid=p.pid,
            arrival_time=p.arrival_time,
            bursts=[
                Burst(cpu=b.cpu, io=b.io)
                for b in p.bursts
            ],
            base_priority=p.base_priority,
            queue_level=p.queue_level,
        )
        for p in processes
    ]


def run_mlfq_demo() -> None:
    print("=" * 78)
    print("MULTILEVEL FEEDBACK QUEUE SIMULATION")
    print("=" * 78)

    processes = make_workload()

    queues = [
        QueueConfig(
            name="Interactive",
            policy=QueuePolicy.ROUND_ROBIN,
            time_quantum=2,
            priority_order=0,
        ),
        QueueConfig(
            name="Standard",
            policy=QueuePolicy.ROUND_ROBIN,
            time_quantum=4,
            priority_order=1,
        ),
        QueueConfig(
            name="Batch",
            policy=QueuePolicy.FCFS,
            priority_order=2,
        ),
    ]

    scheduler = MLFQScheduler(
        processes=processes,
        queues=queues,
        context_switch_cost=1,
        boost_interval=15,
    )

    scheduler.run()
    scheduler.print_timeline()
    scheduler.print_process_report()
    scheduler.print_metrics()


def run_mlq_demo() -> None:
    print("\n")
    print("=" * 78)
    print("MULTILEVEL QUEUE SIMULATION")
    print("=" * 78)

    processes = [
        Process(
            pid="SYSTEM",
            arrival_time=0,
            bursts=[Burst(cpu=4)],
            base_priority=0,
            queue_level=0,
        ),
        Process(
            pid="UI",
            arrival_time=0,
            bursts=[Burst(cpu=5)],
            base_priority=1,
            queue_level=1,
        ),
        Process(
            pid="BATCH",
            arrival_time=0,
            bursts=[Burst(cpu=9)],
            base_priority=2,
            queue_level=2,
        ),
    ]

    queues = [
        QueueConfig(
            name="System",
            policy=QueuePolicy.PRIORITY,
            priority_order=0,
        ),
        QueueConfig(
            name="Interactive",
            policy=QueuePolicy.ROUND_ROBIN,
            time_quantum=2,
            priority_order=1,
        ),
        QueueConfig(
            name="Batch",
            policy=QueuePolicy.FCFS,
            priority_order=2,
        ),
    ]

    scheduler = SimpleMLQScheduler(
        processes=processes,
        queues=queues,
        context_switch_cost=1,
    )

    scheduler.run()

    for entry in scheduler.timeline:
        print(
            f"[{entry.start:>3} -> {entry.end:>3}] "
            f"{entry.label:<16} {entry.kind}"
        )

    print(f"\nContext switches: {scheduler.switches}")


def explain_context_switch_cost() -> None:
    print("\n")
    print("=" * 78)
    print("CONTEXT-SWITCH OVERHEAD")
    print("=" * 78)

    print(
        """
A context switch occurs when the dispatcher changes the CPU from one
process/thread to another. The scheduler may need to save register state,
program-counter information, scheduling metadata, and address-space-related
state, then restore the next execution context.

The switch consumes CPU time without advancing the useful CPU burst of the
selected application.

In this simulator, context-switch cost is modeled explicitly on the timeline.
A cost of one tick means each dispatch transition consumes one unit of elapsed
time. A real system may have costs affected by cache locality, TLB behavior,
address-space changes, kernel mechanisms, CPU architecture, and thread versus
process switching.
"""
    )

    workload = [
        Process(
            pid="A",
            arrival_time=0,
            bursts=[Burst(cpu=4)],
            base_priority=1,
        ),
        Process(
            pid="B",
            arrival_time=0,
            bursts=[Burst(cpu=4)],
            base_priority=2,
        ),
    ]

    for cost in (0, 1, 2):
        cloned = clone_workload(workload)

        scheduler = MLFQScheduler(
            processes=cloned,
            queues=[
                QueueConfig(
                    name="RR",
                    policy=QueuePolicy.ROUND_ROBIN,
                    time_quantum=1,
                ),
            ],
            context_switch_cost=cost,
            boost_interval=None,
        )

        scheduler.run()
        metrics = scheduler.metrics()

        print(
            f"Switch cost={cost}: "
            f"elapsed={scheduler.current_time}, "
            f"context switches={scheduler.total_context_switches}, "
            f"CPU utilization={metrics['cpu_utilization_percent']:.2f}%"
        )


def validate_configuration() -> None:
    print("\n")
    print("=" * 78)
    print("VALIDATION AND FAILURE CONDITIONS")
    print("=" * 78)

    invalid_cases = [
        lambda: QueueConfig(
            name="Invalid RR",
            policy=QueuePolicy.ROUND_ROBIN,
            time_quantum=0,
        ),
        lambda: Burst(cpu=0),
        lambda: Process(
            pid="",
            arrival_time=0,
            bursts=[Burst(cpu=1)],
            base_priority=1,
        ),
        lambda: MLFQScheduler(
            processes=[],
            queues=[],
        ),
    ]

    for index, create_invalid in enumerate(invalid_cases, start=1):
        try:
            create_invalid()
        except ValueError as exc:
            print(f"Validation case {index}: rejected -> {exc}")
        except Exception as exc:
            print(f"Validation case {index}: rejected -> {exc}")
        else:
            print(f"Validation case {index}: ERROR, invalid input accepted")


def compare_mlfq_policies() -> None:
    print("\n")
    print("=" * 78)
    print("MLFQ CONFIGURATION COMPARISON")
    print("=" * 78)

    base = make_workload()

    configurations = [
        ("Aggressive interactive", [2, 4]),
        ("Longer interactive quantum", [4, 8]),
    ]

    for label, quantums in configurations:
        processes = clone_workload(base)

        queues = [
            QueueConfig(
                name="Q0",
                policy=QueuePolicy.ROUND_ROBIN,
                time_quantum=quantums[0],
            ),
            QueueConfig(
                name="Q1",
                policy=QueuePolicy.ROUND_ROBIN,
                time_quantum=quantums[1],
            ),
            QueueConfig(
                name="Q2",
                policy=QueuePolicy.FCFS,
            ),
        ]

        scheduler = MLFQScheduler(
            processes=processes,
            queues=queues,
            context_switch_cost=1,
            boost_interval=15,
        )

        scheduler.run()
        metrics = scheduler.metrics()

        print(
            f"{label:<32} "
            f"wait={metrics['average_waiting_time']:.2f}, "
            f"response={metrics['average_response_time']:.2f}, "
            f"switches={metrics['context_switches']:.0f}, "
            f"utilization={metrics['cpu_utilization_percent']:.2f}%"
        )


def main() -> None:
    run_mlfq_demo()
    run_mlq_demo()
    explain_context_switch_cost()
    validate_configuration()
    compare_mlfq_policies()


if __name__ == "__main__":
    main()
