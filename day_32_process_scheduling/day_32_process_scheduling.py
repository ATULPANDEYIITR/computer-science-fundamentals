#!/usr/bin/env python3
"""
Process Scheduling Simulator
============================

A self-contained study and simulation program for:

- FCFS  : First-Come, First-Served
- SJF   : Shortest Job First, non-preemptive
- SRTF  : Shortest Remaining Time First, preemptive SJF
- Priority Scheduling, both non-preemptive and preemptive
- Round Robin, time-sliced preemptive scheduling

The simulator calculates:
    - Completion time
    - Turnaround time
    - Waiting time
    - Response time
    - CPU utilization
    - Throughput
    - Context-switch count

It also produces an execution timeline and compares algorithms
on the same workload.

The implementation intentionally keeps scheduling policy separate
from process data so that the behavior of each algorithm can be
examined without unrelated operating-system machinery.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections import deque
from typing import Callable, Iterable, Optional


@dataclass(frozen=True)
class Process:
    pid: str
    arrival: int
    burst: int
    priority: int = 0

    def __post_init__(self) -> None:
        if not self.pid.strip():
            raise ValueError("Process ID cannot be empty.")
        if self.arrival < 0:
            raise ValueError("Arrival time cannot be negative.")
        if self.burst <= 0:
            raise ValueError("Burst time must be positive.")

    @property
    def name(self) -> str:
        return self.pid


@dataclass
class Result:
    algorithm: str
    processes: list[Process]
    completion: dict[str, int]
    first_start: dict[str, int]
    timeline: list[tuple[int, int, Optional[str]]]
    context_switches: int = 0

    def metrics(self) -> list[dict[str, float | int | str]]:
        rows = []

        for process in self.processes:
            completion = self.completion[process.pid]
            turnaround = completion - process.arrival
            waiting = turnaround - process.burst
            response = self.first_start[process.pid] - process.arrival

            rows.append(
                {
                    "PID": process.pid,
                    "Arrival": process.arrival,
                    "Burst": process.burst,
                    "Priority": process.priority,
                    "Completion": completion,
                    "Turnaround": turnaround,
                    "Waiting": waiting,
                    "Response": response,
                }
            )

        return rows

    def average(self, field: str) -> float:
        rows = self.metrics()
        return sum(float(row[field]) for row in rows) / len(rows)

    def makespan(self) -> int:
        return max(self.completion.values(), default=0)

    def busy_time(self) -> int:
        return sum(p.burst for p in self.processes)

    def cpu_utilization(self) -> float:
        total_time = self.makespan()
        if total_time == 0:
            return 0.0
        return self.busy_time() / total_time * 100.0

    def throughput(self) -> float:
        total_time = self.makespan()
        if total_time == 0:
            return 0.0
        return len(self.processes) / total_time

    def print_timeline(self) -> None:
        print(f"\n{self.algorithm} execution timeline")
        print("-" * 72)

        if not self.timeline:
            print("No execution intervals.")
            return

        for start, end, pid in self.timeline:
            label = pid if pid is not None else "IDLE"
            print(f"[{start:>3}, {end:>3}) {label}")

    def print_metrics(self) -> None:
        print(f"\n{self.algorithm} metrics")
        print("-" * 100)

        headers = (
            "PID",
            "AT",
            "BT",
            "PR",
            "CT",
            "TAT",
            "WT",
            "RT",
        )
        print(
            f"{headers[0]:<8}{headers[1]:>5}{headers[2]:>5}"
            f"{headers[3]:>5}{headers[4]:>5}{headers[5]:>6}"
            f"{headers[6]:>6}{headers[7]:>6}"
        )

        for row in self.metrics():
            print(
                f"{row['PID']:<8}"
                f"{row['Arrival']:>5}"
                f"{row['Burst']:>5}"
                f"{row['Priority']:>5}"
                f"{row['Completion']:>5}"
                f"{row['Turnaround']:>6}"
                f"{row['Waiting']:>6}"
                f"{row['Response']:>6}"
            )

        print("-" * 100)
        print(f"Average waiting time   : {self.average('Waiting'):.2f}")
        print(f"Average turnaround     : {self.average('Turnaround'):.2f}")
        print(f"Average response       : {self.average('Response'):.2f}")
        print(f"CPU utilization        : {self.cpu_utilization():.2f}%")
        print(f"Throughput             : {self.throughput():.4f} processes/unit")
        print(f"Context switches       : {self.context_switches}")


def add_interval(
    timeline: list[tuple[int, int, Optional[str]]],
    start: int,
    end: int,
    pid: Optional[str],
) -> None:
    """Merge adjacent intervals belonging to the same execution state."""
    if end <= start:
        return

    if timeline and timeline[-1][2] == pid and timeline[-1][1] == start:
        old_start, _, old_pid = timeline[-1]
        timeline[-1] = (old_start, end, old_pid)
    else:
        timeline.append((start, end, pid))


def finalize_result(
    algorithm: str,
    processes: list[Process],
    completion: dict[str, int],
    first_start: dict[str, int],
    timeline: list[tuple[int, int, Optional[str]]],
) -> Result:
    """Count actual changes between CPU execution states."""
    context_switches = 0
    previous: Optional[str] = None

    for _, _, pid in timeline:
        if pid is None:
            previous = None
            continue

        if previous is not None and previous != pid:
            context_switches += 1

        previous = pid

    return Result(
        algorithm=algorithm,
        processes=processes,
        completion=completion,
        first_start=first_start,
        timeline=timeline,
        context_switches=context_switches,
    )


def validate_workload(processes: Iterable[Process]) -> list[Process]:
    items = list(processes)

    if not items:
        raise ValueError("At least one process is required.")

    identifiers = [p.pid for p in items]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("Process IDs must be unique.")

    return sorted(items, key=lambda p: (p.arrival, p.pid))


def fcfs(processes: Iterable[Process]) -> Result:
    """
    First-Come, First-Served.

    The ready process with the earliest arrival is executed completely.
    FCFS is non-preemptive, so a newly arrived process cannot interrupt
    the process currently using the CPU.
    """
    jobs = validate_workload(processes)
    time = 0
    completion: dict[str, int] = {}
    first_start: dict[str, int] = {}
    timeline: list[tuple[int, int, Optional[str]]] = []

    for process in jobs:
        if time < process.arrival:
            add_interval(timeline, time, process.arrival, None)
            time = process.arrival

        first_start.setdefault(process.pid, time)
        end = time + process.burst
        add_interval(timeline, time, end, process.pid)
        time = end
        completion[process.pid] = time

    return finalize_result(
        "FCFS",
        jobs,
        completion,
        first_start,
        timeline,
    )


def sjf(processes: Iterable[Process]) -> Result:
    """
    Non-preemptive Shortest Job First.

    Whenever the CPU becomes free, select the arrived process with
    the smallest total CPU burst. Ties use arrival time and PID.
    """
    jobs = validate_workload(processes)
    remaining = jobs.copy()
    time = 0
    completion: dict[str, int] = {}
    first_start: dict[str, int] = {}
    timeline: list[tuple[int, int, Optional[str]]] = []

    while remaining:
        available = [p for p in remaining if p.arrival <= time]

        if not available:
            next_arrival = min(p.arrival for p in remaining)
            add_interval(timeline, time, next_arrival, None)
            time = next_arrival
            continue

        process = min(
            available,
            key=lambda p: (p.burst, p.arrival, p.pid),
        )

        remaining.remove(process)
        first_start.setdefault(process.pid, time)
        end = time + process.burst
        add_interval(timeline, time, end, process.pid)
        time = end
        completion[process.pid] = time

    return finalize_result(
        "SJF",
        jobs,
        completion,
        first_start,
        timeline,
    )


def srtf(processes: Iterable[Process]) -> Result:
    """
    Shortest Remaining Time First.

    This is the preemptive form of SJF. At each scheduling event,
    the process with the smallest remaining CPU time executes.

    An event occurs when:
        - a process arrives, or
        - the currently running process finishes.
    """
    jobs = validate_workload(processes)
    remaining = {p.pid: p.burst for p in jobs}
    by_id = {p.pid: p for p in jobs}
    completion: dict[str, int] = {}
    first_start: dict[str, int] = {}
    timeline: list[tuple[int, int, Optional[str]]] = []

    time = 0
    completed = 0

    while completed < len(jobs):
        available = [
            p
            for p in jobs
            if p.arrival <= time
            and remaining[p.pid] > 0
        ]

        if not available:
            next_arrival = min(
                p.arrival
                for p in jobs
                if remaining[p.pid] > 0 and p.arrival > time
            )
            add_interval(timeline, time, next_arrival, None)
            time = next_arrival
            continue

        process = min(
            available,
            key=lambda p: (
                remaining[p.pid],
                p.arrival,
                p.pid,
            ),
        )

        first_start.setdefault(process.pid, time)

        future_arrivals = [
            p.arrival
            for p in jobs
            if p.arrival > time and remaining[p.pid] > 0
        ]

        next_arrival = min(future_arrivals) if future_arrivals else None
        finish_time = time + remaining[process.pid]

        if next_arrival is not None and next_arrival < finish_time:
            run_until = next_arrival
        else:
            run_until = finish_time

        elapsed = run_until - time
        remaining[process.pid] -= elapsed
        add_interval(timeline, time, run_until, process.pid)
        time = run_until

        if remaining[process.pid] == 0:
            completion[process.pid] = time
            completed += 1

    return finalize_result(
        "SRTF",
        jobs,
        completion,
        first_start,
        timeline,
    )


def priority_non_preemptive(processes: Iterable[Process]) -> Result:
    """
    Non-preemptive priority scheduling.

    Lower numeric priority values represent higher scheduling priority.
    A process runs until its burst completes once selected.
    """
    jobs = validate_workload(processes)
    remaining = jobs.copy()
    time = 0
    completion: dict[str, int] = {}
    first_start: dict[str, int] = {}
    timeline: list[tuple[int, int, Optional[str]]] = []

    while remaining:
        available = [p for p in remaining if p.arrival <= time]

        if not available:
            next_arrival = min(p.arrival for p in remaining)
            add_interval(timeline, time, next_arrival, None)
            time = next_arrival
            continue

        process = min(
            available,
            key=lambda p: (p.priority, p.arrival, p.pid),
        )

        remaining.remove(process)
        first_start.setdefault(process.pid, time)
        end = time + process.burst
        add_interval(timeline, time, end, process.pid)
        time = end
        completion[process.pid] = time

    return finalize_result(
        "Priority (Non-Preemptive)",
        jobs,
        completion,
        first_start,
        timeline,
    )


def priority_preemptive(processes: Iterable[Process]) -> Result:
    """
    Preemptive priority scheduling.

    Lower numeric priority values represent higher priority.
    A newly arrived higher-priority process can interrupt the
    currently running process.
    """
    jobs = validate_workload(processes)
    remaining = {p.pid: p.burst for p in jobs}
    completion: dict[str, int] = {}
    first_start: dict[str, int] = {}
    timeline: list[tuple[int, int, Optional[str]]] = []

    time = 0
    completed = 0

    while completed < len(jobs):
        available = [
            p
            for p in jobs
            if p.arrival <= time and remaining[p.pid] > 0
        ]

        if not available:
            next_arrival = min(
                p.arrival
                for p in jobs
                if remaining[p.pid] > 0 and p.arrival > time
            )
            add_interval(timeline, time, next_arrival, None)
            time = next_arrival
            continue

        process = min(
            available,
            key=lambda p: (
                p.priority,
                p.arrival,
                p.pid,
            ),
        )

        first_start.setdefault(process.pid, time)

        future_arrivals = [
            p.arrival
            for p in jobs
            if p.arrival > time and remaining[p.pid] > 0
        ]
        next_arrival = min(future_arrivals) if future_arrivals else None
        finish_time = time + remaining[process.pid]

        if next_arrival is not None and next_arrival < finish_time:
            run_until = next_arrival
        else:
            run_until = finish_time

        elapsed = run_until - time
        remaining[process.pid] -= elapsed
        add_interval(timeline, time, run_until, process.pid)
        time = run_until

        if remaining[process.pid] == 0:
            completion[process.pid] = time
            completed += 1

    return finalize_result(
        "Priority (Preemptive)",
        jobs,
        completion,
        first_start,
        timeline,
    )


def round_robin(
    processes: Iterable[Process],
    quantum: int,
) -> Result:
    """
    Round Robin scheduling.

    Each ready process receives at most `quantum` units before being
    returned to the ready queue if it still has CPU work remaining.

    The implementation explicitly handles arrivals that occur while
    another process is consuming its time slice.
    """
    if quantum <= 0:
        raise ValueError("Round Robin quantum must be positive.")

    jobs = validate_workload(processes)
    remaining = {p.pid: p.burst for p in jobs}
    completion: dict[str, int] = {}
    first_start: dict[str, int] = {}
    timeline: list[tuple[int, int, Optional[str]]] = []

    queue: deque[Process] = deque()
    index = 0
    time = 0
    completed = 0

    while completed < len(jobs):
        while index < len(jobs) and jobs[index].arrival <= time:
            queue.append(jobs[index])
            index += 1

        if not queue:
            if index >= len(jobs):
                break

            next_arrival = jobs[index].arrival
            add_interval(timeline, time, next_arrival, None)
            time = next_arrival
            continue

        process = queue.popleft()

        if remaining[process.pid] <= 0:
            continue

        first_start.setdefault(process.pid, time)

        run_time = min(quantum, remaining[process.pid])
        end = time + run_time

        add_interval(timeline, time, end, process.pid)

        while index < len(jobs) and jobs[index].arrival <= end:
            queue.append(jobs[index])
            index += 1

        remaining[process.pid] -= run_time
        time = end

        if remaining[process.pid] == 0:
            completion[process.pid] = time
            completed += 1
        else:
            queue.append(process)

    return finalize_result(
        f"Round Robin (q={quantum})",
        jobs,
        completion,
        first_start,
        timeline,
    )


def print_comparison(results: list[Result]) -> None:
    """Display comparable scheduling metrics without declaring one universal winner."""
    print("\nAlgorithm comparison")
    print("-" * 108)
    print(
        f"{'Algorithm':<27}"
        f"{'Avg WT':>10}"
        f"{'Avg TAT':>11}"
        f"{'Avg RT':>10}"
        f"{'CPU %':>10}"
        f"{'Throughput':>13}"
        f"{'Switches':>10}"
    )

    for result in results:
        print(
            f"{result.algorithm:<27}"
            f"{result.average('Waiting'):>10.2f}"
            f"{result.average('Turnaround'):>11.2f}"
            f"{result.average('Response'):>10.2f}"
            f"{result.cpu_utilization():>10.2f}"
            f"{result.throughput():>13.4f}"
            f"{result.context_switches:>10}"
        )


def demonstrate_single_algorithm_details(
    result: Result,
) -> None:
    result.print_timeline()
    result.print_metrics()


def demonstrate_edge_case() -> None:
    """
    Show why arrival time matters.

    The CPU is idle initially, so a scheduler must advance time to
    the first process arrival instead of treating the workload as if
    every process existed at time zero.
    """
    workload = [
        Process("LATE-A", 5, 3, 2),
        Process("LATE-B", 7, 2, 1),
    ]

    result = fcfs(workload)
    demonstrate_single_algorithm_details(result)


def demonstrate_round_robin_behavior() -> None:
    """
    Show time slicing with several short processes.

    A small quantum increases opportunities for response but can
    increase context-switch overhead.
    """
    workload = [
        Process("WEB", 0, 7, 2),
        Process("API", 0, 4, 1),
        Process("DB", 1, 5, 3),
    ]

    result = round_robin(workload, quantum=2)
    demonstrate_single_algorithm_details(result)


def demonstrate_preemption() -> None:
    """
    Demonstrate the defining difference between non-preemptive and
    preemptive scheduling.

    A short process arriving during a long process can take the CPU
    under SRTF, while SJF allows the current process to finish.
    """
    workload = [
        Process("LONG", 0, 9, 3),
        Process("SHORT", 2, 2, 2),
        Process("MEDIUM", 3, 4, 1),
    ]

    print("\nSJF versus SRTF preemption example")
    print("=" * 72)

    sjf_result = sjf(workload)
    srtf_result = srtf(workload)

    sjf_result.print_timeline()
    srtf_result.print_timeline()


def demonstrate_validation() -> None:
    """Show that invalid scheduling parameters are rejected early."""
    invalid_cases: list[Callable[[], object]] = [
        lambda: Process("BAD", -1, 3),
        lambda: Process("BAD", 0, 0),
        lambda: round_robin(
            [Process("P1", 0, 3)],
            quantum=0,
        ),
    ]

    print("\nValidation behavior")
    print("-" * 72)

    for case in invalid_cases:
        try:
            case()
        except ValueError as exc:
            print(f"Rejected invalid input: {exc}")


def main() -> None:
    workload = [
        Process("P1", arrival=0, burst=8, priority=2),
        Process("P2", arrival=1, burst=4, priority=1),
        Process("P3", arrival=2, burst=2, priority=3),
        Process("P4", arrival=3, burst=6, priority=2),
        Process("P5", arrival=5, burst=3, priority=1),
    ]

    print("PROCESS SCHEDULING SIMULATOR")
    print("=" * 72)
    print("Workload:")
    print("PID       Arrival   Burst   Priority")

    for process in workload:
        print(
            f"{process.pid:<10}"
            f"{process.arrival:>7}"
            f"{process.burst:>8}"
            f"{process.priority:>10}"
        )

    results = [
        fcfs(workload),
        sjf(workload),
        srtf(workload),
        priority_non_preemptive(workload),
        priority_preemptive(workload),
        round_robin(workload, quantum=3),
    ]

    for result in results:
        result.print_timeline()
        result.print_metrics()

    print_comparison(results)

    demonstrate_preemption()
    demonstrate_round_robin_behavior()
    demonstrate_edge_case()
    demonstrate_validation()

    print("\nScheduling terminology")
    print("-" * 72)
    print(
        "Waiting time = Turnaround time - CPU burst time.\n"
        "Turnaround time = Completion time - Arrival time.\n"
        "Response time = First CPU start - Arrival time.\n"
        "SJF is non-preemptive; SRTF is its preemptive counterpart.\n"
        "Priority scheduling can be implemented in either preemptive or "
        "non-preemptive form.\n"
        "Round Robin uses a fixed time quantum and a cyclic ready queue."
    )


if __name__ == "__main__":
    main()
