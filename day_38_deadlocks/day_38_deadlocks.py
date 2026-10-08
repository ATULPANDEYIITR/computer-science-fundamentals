"""
Deadlocks: conditions, prevention, avoidance, detection, and recovery.

This self-contained program models deadlocks in resource-allocation systems.
It demonstrates:
- The four Coffman conditions.
- A concrete circular-wait deadlock.
- Prevention by breaking one necessary condition.
- Banker's algorithm for deadlock avoidance.
- Wait-for-graph based deadlock detection.
- Recovery by aborting a selected process and releasing its resources.
- Validation, safety analysis, and practical diagnostics.

The examples use ordinary Python data structures and require no external packages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Optional, Set, Tuple


class ProcessState(Enum):
    RUNNING = "running"
    WAITING = "waiting"
    ABORTED = "aborted"
    COMPLETED = "completed"


class DeadlockError(RuntimeError):
    """Raised when an operation would intentionally create a modeled deadlock."""


@dataclass
class Resource:
    name: str
    instances: int

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Resource name cannot be empty.")
        if self.instances <= 0:
            raise ValueError("Resource instances must be positive.")


@dataclass
class Process:
    name: str
    maximum: Dict[str, int]
    allocation: Dict[str, int] = field(default_factory=dict)
    state: ProcessState = ProcessState.RUNNING

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Process name cannot be empty.")

        for resource, amount in self.maximum.items():
            if amount < 0:
                raise ValueError(f"Maximum claim cannot be negative: {resource}")
            self.allocation.setdefault(resource, 0)

        for resource, amount in self.allocation.items():
            if amount < 0:
                raise ValueError(f"Allocation cannot be negative: {resource}")
            self.maximum.setdefault(resource, amount)

        for resource in self.maximum:
            if self.allocation.get(resource, 0) > self.maximum[resource]:
                raise ValueError(
                    f"Allocation exceeds maximum claim for {self.name}: {resource}"
                )

    def need(self) -> Dict[str, int]:
        return {
            resource: self.maximum[resource] - self.allocation.get(resource, 0)
            for resource in self.maximum
        }


class ResourceSystem:
    """
    Small resource-allocation model.

    The model deliberately separates:
    - allocation: resources already held;
    - maximum: maximum resources a process may eventually need;
    - available: resources currently free;
    - request: resources a process is currently waiting for.

    This separation is essential because deadlock avoidance asks whether a
    hypothetical allocation keeps the system in a safe state.
    """

    def __init__(self, resources: Iterable[Resource]) -> None:
        self.resources: Dict[str, Resource] = {r.name: r for r in resources}
        self.processes: Dict[str, Process] = {}
        self.waiting_for: Dict[str, Set[str]] = {}

    def add_process(self, process: Process) -> None:
        if process.name in self.processes:
            raise ValueError(f"Duplicate process: {process.name}")

        unknown = set(process.maximum) - set(self.resources)
        if unknown:
            raise ValueError(
                f"Process {process.name} references unknown resources: {unknown}"
            )

        self.processes[process.name] = process
        self.waiting_for[process.name] = set()

        self._validate_total_allocation()

    def _validate_total_allocation(self) -> None:
        totals = {name: 0 for name in self.resources}

        for process in self.processes.values():
            if process.state == ProcessState.ABORTED:
                continue
            for resource, amount in process.allocation.items():
                totals[resource] = totals.get(resource, 0) + amount

        for resource, total in totals.items():
            capacity = self.resources[resource].instances
            if total > capacity:
                raise ValueError(
                    f"Allocated {total} instances of {resource}, "
                    f"but capacity is {capacity}."
                )

    def available(self) -> Dict[str, int]:
        available = {
            name: resource.instances for name, resource in self.resources.items()
        }

        for process in self.processes.values():
            if process.state == ProcessState.ABORTED:
                continue
            for resource, amount in process.allocation.items():
                available[resource] -= amount

        return available

    def request(
        self,
        process_name: str,
        request: Dict[str, int],
        enforce_safety: bool = False,
    ) -> bool:
        """
        Request resources.

        If enforce_safety is True, the allocation is tentatively applied and
        Banker's safety test decides whether the request is allowed.
        """

        if process_name not in self.processes:
            raise KeyError(f"Unknown process: {process_name}")

        process = self.processes[process_name]

        if process.state in {ProcessState.ABORTED, ProcessState.COMPLETED}:
            raise ValueError(f"Process {process_name} is not active.")

        for resource, amount in request.items():
            if resource not in self.resources:
                raise ValueError(f"Unknown resource: {resource}")
            if amount < 0:
                raise ValueError("Resource requests cannot be negative.")
            if amount > process.need().get(resource, 0):
                raise ValueError(
                    f"{process_name} requested more {resource} than its remaining need."
                )

        available = self.available()
        immediately_available = all(
            amount <= available.get(resource, 0)
            for resource, amount in request.items()
        )

        if not immediately_available:
            process.state = ProcessState.WAITING
            self.waiting_for[process_name] = {
                resource
                for resource, amount in request.items()
                if amount > available.get(resource, 0)
            }
            return False

        if enforce_safety:
            if not self._safe_after_tentative_allocation(process_name, request):
                process.state = ProcessState.WAITING
                self.waiting_for[process_name] = set(request)
                return False

        for resource, amount in request.items():
            process.allocation[resource] = (
                process.allocation.get(resource, 0) + amount
            )

        process.state = ProcessState.RUNNING
        self.waiting_for[process_name].clear()
        return True

    def _safe_after_tentative_allocation(
        self, process_name: str, request: Dict[str, int]
    ) -> bool:
        process = self.processes[process_name]

        for resource, amount in request.items():
            process.allocation[resource] = (
                process.allocation.get(resource, 0) + amount
            )

        safe = self.is_safe_state()

        for resource, amount in request.items():
            process.allocation[resource] -= amount

        return safe

    def release(self, process_name: str, release: Dict[str, int]) -> None:
        if process_name not in self.processes:
            raise KeyError(process_name)

        process = self.processes[process_name]

        for resource, amount in release.items():
            held = process.allocation.get(resource, 0)
            if amount < 0 or amount > held:
                raise ValueError(
                    f"Invalid release of {resource} by {process_name}: {amount}"
                )
            process.allocation[resource] = held - amount

        self._validate_total_allocation()

    def complete(self, process_name: str) -> None:
        if process_name not in self.processes:
            raise KeyError(process_name)

        process = self.processes[process_name]

        # Completion returns all resources held by the process.
        process.allocation = {resource: 0 for resource in process.allocation}
        process.state = ProcessState.COMPLETED
        self.waiting_for[process_name].clear()

    def abort(self, process_name: str) -> None:
        if process_name not in self.processes:
            raise KeyError(process_name)

        process = self.processes[process_name]

        # Aborting a process is a common recovery mechanism. Its held
        # resources become available immediately to other processes.
        process.allocation = {resource: 0 for resource in process.allocation}
        process.state = ProcessState.ABORTED
        self.waiting_for[process_name].clear()

        for waiting in self.waiting_for.values():
            waiting.discard(process_name)

    def is_safe_state(self) -> bool:
        """
        Banker's safety test.

        Work begins as the currently available resources. A process can
        finish when its remaining need is <= Work. Once it finishes, its
        allocated resources are returned to Work.

        A state is safe if every active process can be placed in a completion
        sequence. Safe does not mean that a deadlock is currently present;
        it means the system has at least one future completion sequence.
        """

        work = self.available()

        active = {
            name: process
            for name, process in self.processes.items()
            if process.state not in {ProcessState.ABORTED, ProcessState.COMPLETED}
        }

        finish = {name: False for name in active}

        changed = True
        while changed:
            changed = False

            for name, process in active.items():
                if finish[name]:
                    continue

                need = process.need()

                if all(need.get(resource, 0) <= work.get(resource, 0)
                       for resource in self.resources):
                    for resource, amount in process.allocation.items():
                        work[resource] = work.get(resource, 0) + amount

                    finish[name] = True
                    changed = True

        return all(finish.values())

    def safe_sequence(self) -> List[str]:
        work = self.available()

        active = {
            name: process
            for name, process in self.processes.items()
            if process.state not in {ProcessState.ABORTED, ProcessState.COMPLETED}
        }

        sequence: List[str] = []
        remaining = set(active)

        while remaining:
            candidate = None

            for name in remaining:
                need = active[name].need()
                if all(
                    need.get(resource, 0) <= work.get(resource, 0)
                    for resource in self.resources
                ):
                    candidate = name
                    break

            if candidate is None:
                return []

            process = active[candidate]
            for resource, amount in process.allocation.items():
                work[resource] = work.get(resource, 0) + amount

            sequence.append(candidate)
            remaining.remove(candidate)

        return sequence

    def detect_deadlock(self) -> Set[str]:
        """
        Detect cycles in the wait-for graph.

        A wait-for edge P -> Q means P is waiting for a resource currently
        held by Q. A cycle means the involved processes form a deadlock in
        this single-instance resource model.
        """

        graph = self._build_wait_for_graph()
        visiting: Set[str] = set()
        visited: Set[str] = set()
        cycle_nodes: Set[str] = set()

        def dfs(node: str, path: List[str]) -> None:
            if node in visiting:
                if node in path:
                    index = path.index(node)
                    cycle_nodes.update(path[index:])
                return

            if node in visited:
                return

            visiting.add(node)
            path.append(node)

            for neighbor in graph.get(node, set()):
                dfs(neighbor, path)

            path.pop()
            visiting.remove(node)
            visited.add(node)

        for node in graph:
            dfs(node, [])

        return cycle_nodes

    def _build_wait_for_graph(self) -> Dict[str, Set[str]]:
        holders: Dict[str, Set[str]] = {resource: set() for resource in self.resources}

        for process in self.processes.values():
            if process.state == ProcessState.ABORTED:
                continue

            for resource, amount in process.allocation.items():
                if amount > 0:
                    holders[resource].add(process.name)

        graph: Dict[str, Set[str]] = {
            process: set() for process in self.processes
        }

        for waiting_process, resources in self.waiting_for.items():
            for resource in resources:
                graph[waiting_process].update(holders.get(resource, set()))

        return graph

    def print_state(self) -> None:
        print("\nResource state")
        print("-" * 60)
        print(f"Available: {self.available()}")

        for process in self.processes.values():
            print(
                f"{process.name:10} "
                f"state={process.state.value:9} "
                f"allocation={process.allocation} "
                f"need={process.need()}"
            )


def demonstrate_deadlock_conditions() -> None:
    print("\n=== Four Coffman Conditions ===")

    conditions = {
        "Mutual exclusion":
            "At least one resource is non-shareable; only one process can hold it.",
        "Hold and wait":
            "A process holds resources while waiting for additional resources.",
        "No preemption":
            "A resource cannot simply be taken away from its holder.",
        "Circular wait":
            "Processes form a cycle in which each waits for a resource held by another.",
    }

    for name, description in conditions.items():
        print(f"{name}: {description}")

    print(
        "\nAll four conditions are necessary for a classic resource deadlock. "
        "Removing any one of them prevents that class of deadlock."
    )


def create_single_instance_deadlock() -> ResourceSystem:
    """
    Create P1 -> R2 and P2 -> R1.

    R1 and R2 each have one instance, so:
    P1 holds R1 and waits for R2.
    P2 holds R2 and waits for R1.

    This is the canonical circular-wait structure.
    """

    system = ResourceSystem([
        Resource("R1", 1),
        Resource("R2", 1),
    ])

    system.add_process(
        Process(
            "P1",
            maximum={"R1": 1, "R2": 1},
            allocation={"R1": 1, "R2": 0},
        )
    )

    system.add_process(
        Process(
            "P2",
            maximum={"R1": 1, "R2": 1},
            allocation={"R1": 0, "R2": 1},
        )
    )

    system.request("P1", {"R2": 1})
    system.request("P2", {"R1": 1})

    return system


def demonstrate_deadlock() -> None:
    print("\n=== Concrete Deadlock ===")

    system = create_single_instance_deadlock()
    system.print_state()

    deadlocked = system.detect_deadlock()

    print(f"\nDetected deadlocked processes: {sorted(deadlocked)}")
    print(
        "The system cannot make progress because each process owns one "
        "resource required by the other."
    )


def demonstrate_prevention() -> None:
    print("\n=== Deadlock Prevention ===")

    print("\nPrevention by resource ordering:")
    print(
        "Assign every resource a global order and require processes to acquire "
        "resources only in increasing order."
    )

    # P1 acquires R1 then R2. P2 follows the same order instead of acquiring R2
    # first. The circular-wait condition therefore cannot form.
    ordered = ResourceSystem([
        Resource("R1", 1),
        Resource("R2", 1),
    ])

    ordered.add_process(
        Process(
            "P1",
            maximum={"R1": 1, "R2": 1},
            allocation={"R1": 1, "R2": 0},
        )
    )
    ordered.add_process(
        Process(
            "P2",
            maximum={"R1": 1, "R2": 1},
            allocation={"R1": 0, "R2": 0},
        )
    )

    print(f"Initial availability: {ordered.available()}")

    accepted = ordered.request("P2", {"R1": 1})
    print(f"P2 requests R1 using the global order: accepted={accepted}")

    waiting = ordered.request("P2", {"R2": 1})
    print(f"P2 then requests R2: accepted={waiting}")

    ordered.complete("P1")
    print(f"After P1 completes, availability: {ordered.available()}")

    # The key prevention rule is acquisition order. No process is allowed to
    # hold a higher-ordered resource while requesting a lower-ordered one.
    print(
        "The ordering rule removes circular wait rather than detecting a cycle "
        "after it has formed."
    )


def demonstrate_avoidance() -> None:
    print("\n=== Deadlock Avoidance with Banker's Algorithm ===")

    system = ResourceSystem([
        Resource("A", 10),
        Resource("B", 5),
        Resource("C", 7),
    ])

    system.add_process(
        Process(
            "P0",
            maximum={"A": 7, "B": 5, "C": 3},
            allocation={"A": 0, "B": 1, "C": 0},
        )
    )
    system.add_process(
        Process(
            "P1",
            maximum={"A": 3, "B": 2, "C": 2},
            allocation={"A": 2, "B": 0, "C": 0},
        )
    )
    system.add_process(
        Process(
            "P2",
            maximum={"A": 9, "B": 0, "C": 2},
            allocation={"A": 3, "B": 0, "C": 2},
        )
    )
    system.add_process(
        Process(
            "P3",
            maximum={"A": 2, "B": 2, "C": 2},
            allocation={"A": 2, "B": 1, "C": 1},
        )
    )
    system.add_process(
        Process(
            "P4",
            maximum={"A": 4, "B": 3, "C": 3},
            allocation={"A": 0, "B": 0, "C": 2},
        )
    )

    system.print_state()

    print(f"\nSafe state: {system.is_safe_state()}")
    print(f"One safe sequence: {system.safe_sequence()}")

    # This request is not accepted merely because resources happen to be
    # available. The safety test checks whether granting it preserves at least
    # one possible completion sequence.
    result = system.request(
        "P1",
        {"A": 1, "B": 1, "C": 2},
        enforce_safety=True,
    )

    print(f"\nP1 request under safety checking: {result}")
    print(f"Safe state after request: {system.is_safe_state()}")
    system.print_state()


def demonstrate_detection_and_recovery() -> None:
    print("\n=== Detection and Recovery ===")

    system = create_single_instance_deadlock()
    system.print_state()

    deadlocked = system.detect_deadlock()
    print(f"\nDetected cycle: {sorted(deadlocked)}")

    # Recovery policy: abort the process holding fewer resources. This is only
    # an example policy; real systems may consider transaction cost, priority,
    # work already performed, restart cost, and starvation.
    victim = min(
        deadlocked,
        key=lambda name: sum(system.processes[name].allocation.values()),
    )

    print(f"Recovery selects victim: {victim}")
    system.abort(victim)

    print(f"Deadlock after abort: {sorted(system.detect_deadlock())}")
    system.print_state()

    remaining = next(
        name for name in deadlocked if name != victim
    )

    acquired = system.request(remaining, {"R1": 1, "R2": 1})
    print(
        f"\nRemaining process can request resources after recovery: "
        f"{acquired}"
    )
    system.print_state()


def demonstrate_edge_cases() -> None:
    print("\n=== Validation and Edge Cases ===")

    try:
        Resource("invalid", 0)
    except ValueError as exc:
        print(f"Rejected invalid resource capacity: {exc}")

    system = ResourceSystem([Resource("CPU", 2)])

    system.add_process(
        Process(
            "Worker",
            maximum={"CPU": 2},
            allocation={"CPU": 1},
        )
    )

    try:
        system.request("Worker", {"CPU": 2})
    except ValueError as exc:
        print(f"Rejected request beyond remaining need: {exc}")

    try:
        system.release("Worker", {"CPU": 5})
    except ValueError as exc:
        print(f"Rejected release beyond allocation: {exc}")

    print(
        "\nA safe state is not identical to an absence of waiting. A process "
        "can legitimately wait while the system still has a safe completion "
        "sequence."
    )


def explain_prevention_vs_avoidance() -> None:
    print("\n=== Prevention vs Avoidance ===")
    print(
        "Prevention changes the rules so at least one necessary deadlock "
        "condition cannot occur. Resource ordering is an example."
    )
    print(
        "Avoidance permits resource requests dynamically but evaluates whether "
        "granting each request would preserve a safe state. Banker's algorithm "
        "requires maximum claims and current allocations."
    )
    print(
        "Detection allows the system to enter an unsafe or deadlocked state and "
        "periodically searches for deadlocks. Recovery then attempts to restore "
        "progress."
    )


def main() -> None:
    print("DEADLOCKS: MODEL, PREVENTION, AVOIDANCE, DETECTION, RECOVERY")
    demonstrate_deadlock_conditions()
    demonstrate_deadlock()
    demonstrate_prevention()
    demonstrate_avoidance()
    demonstrate_detection_and_recovery()
    demonstrate_edge_cases()
    explain_prevention_vs_avoidance()


if __name__ == "__main__":
    main()
