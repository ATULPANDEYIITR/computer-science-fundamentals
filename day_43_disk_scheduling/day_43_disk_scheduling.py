"""
Disk Scheduling: FCFS, SSTF, SCAN, C-SCAN, LOOK, and C-LOOK

A self-contained implementation that models disk-head scheduling, compares
algorithms, validates requests, calculates seek movement, and demonstrates
direction-sensitive behavior and boundary handling.

Run with:
    python disk_scheduling.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable


@dataclass(frozen=True)
class ScheduleResult:
    algorithm: str
    order: list[int]
    movement: int
    average_seek: float
    service_count: int


class DiskScheduler:
    def __init__(self, disk_size: int, initial_head: int) -> None:
        if disk_size < 2:
            raise ValueError("disk_size must be at least 2")
        if not 0 <= initial_head < disk_size:
            raise ValueError("initial_head must be within the disk")
        self.disk_size = disk_size
        self.initial_head = initial_head

    def validate_requests(self, requests: Iterable[int]) -> list[int]:
        result = list(requests)
        if not result:
            raise ValueError("At least one disk request is required")
        invalid = [r for r in result if not 0 <= r < self.disk_size]
        if invalid:
            raise ValueError(
                f"Requests outside disk range 0..{self.disk_size - 1}: {invalid}"
            )
        return result

    @staticmethod
    def movement(start: int, order: Iterable[int]) -> int:
        current = start
        total = 0
        for cylinder in order:
            total += abs(cylinder - current)
            current = cylinder
        return total

    def result(self, name: str, order: list[int]) -> ScheduleResult:
        total = self.movement(self.initial_head, order)
        average = total / len(order) if order else 0.0
        return ScheduleResult(name, order, total, average, len(order))

    def fcfs(self, requests: Iterable[int]) -> ScheduleResult:
        requests = self.validate_requests(requests)
        return self.result("FCFS", requests.copy())

    def sstf(self, requests: Iterable[int]) -> ScheduleResult:
        remaining = self.validate_requests(requests).copy()
        current = self.initial_head
        order: list[int] = []

        # SSTF repeatedly chooses the pending request with the smallest
        # absolute seek distance from the current head position.
        while remaining:
            nearest = min(
                remaining,
                key=lambda cylinder: (abs(cylinder - current), cylinder),
            )
            order.append(nearest)
            remaining.remove(nearest)
            current = nearest

        return self.result("SSTF", order)

    def scan(
        self,
        requests: Iterable[int],
        direction: str = "right",
    ) -> ScheduleResult:
        requests = self.validate_requests(requests)
        direction = direction.lower()
        if direction not in {"left", "right"}:
            raise ValueError("direction must be 'left' or 'right'")

        left = sorted({r for r in requests if r < self.initial_head}, reverse=True)
        right = sorted({r for r in requests if r >= self.initial_head})

        order: list[int] = []

        if direction == "right":
            order.extend(right)
            if left:
                # SCAN physically reaches the disk boundary before reversing.
                if not order or order[-1] != self.disk_size - 1:
                    order.append(self.disk_size - 1)
                order.extend(left)
        else:
            order.extend(left)
            if right:
                if not order or order[-1] != 0:
                    order.append(0)
                order.extend(right)

        # A boundary is a movement event, not a service request.
        service_order = [r for r in order if r in requests]
        return self.result("SCAN", service_order) if not left or not right else (
            self.result_with_path("SCAN", order, requests)
        )

    def result_with_path(
        self,
        name: str,
        path: list[int],
        requests: Iterable[int],
    ) -> ScheduleResult:
        requests = list(requests)
        total = self.movement(self.initial_head, path)
        serviced = [p for p in path if p in requests]
        return ScheduleResult(
            name,
            serviced,
            total,
            total / len(serviced) if serviced else 0.0,
            len(serviced),
        )

    def c_scan(
        self,
        requests: Iterable[int],
        direction: str = "right",
    ) -> ScheduleResult:
        requests = self.validate_requests(requests)
        direction = direction.lower()
        if direction not in {"left", "right"}:
            raise ValueError("direction must be 'left' or 'right'")

        left = sorted({r for r in requests if r < self.initial_head})
        right = sorted({r for r in requests if r >= self.initial_head})

        path: list[int] = []

        if direction == "right":
            path.extend(right)
            if left:
                path.append(self.disk_size - 1)
                path.append(0)
                path.extend(left)
        else:
            left_desc = sorted({r for r in requests if r < self.initial_head}, reverse=True)
            right_desc = sorted({r for r in requests if r >= self.initial_head}, reverse=True)
            path.extend(left_desc)
            if right_desc:
                path.append(0)
                path.append(self.disk_size - 1)
                path.extend(right_desc)

        return self.result_with_path("C-SCAN", path, requests)

    def look(
        self,
        requests: Iterable[int],
        direction: str = "right",
    ) -> ScheduleResult:
        requests = self.validate_requests(requests)
        direction = direction.lower()
        if direction not in {"left", "right"}:
            raise ValueError("direction must be 'left' or 'right'")

        left = sorted({r for r in requests if r < self.initial_head}, reverse=True)
        right = sorted({r for r in requests if r >= self.initial_head})

        if direction == "right":
            order = right + left
        else:
            order = left + right

        return self.result("LOOK", order)

    def c_look(
        self,
        requests: Iterable[int],
        direction: str = "right",
    ) -> ScheduleResult:
        requests = self.validate_requests(requests)
        direction = direction.lower()
        if direction not in {"left", "right"}:
            raise ValueError("direction must be 'left' or 'right'")

        left = sorted({r for r in requests if r < self.initial_head})
        right = sorted({r for r in requests if r >= self.initial_head})

        if direction == "right":
            order = right + left
        else:
            order = list(reversed(left)) + list(reversed(right))

        # C-LOOK wraps from one request extreme to the other, rather than
        # traveling to the physical disk boundary.
        return self.result("C-LOOK", order)

    def all_algorithms(
        self,
        requests: Iterable[int],
        direction: str = "right",
    ) -> list[ScheduleResult]:
        return [
            self.fcfs(requests),
            self.sstf(requests),
            self.scan(requests, direction),
            self.c_scan(requests, direction),
            self.look(requests, direction),
            self.c_look(requests, direction),
        ]


def print_result(result: ScheduleResult) -> None:
    print(f"\n{result.algorithm}")
    print("-" * len(result.algorithm))
    print("Service order :", " -> ".join(map(str, result.order)))
    print("Total movement:", result.movement, "cylinders")
    print(f"Average seek  : {result.average_seek:.2f} cylinders")


def compare(results: list[ScheduleResult]) -> None:
    print("\nComparison")
    print("=" * 72)
    print(f"{'Algorithm':<12}{'Movement':>14}{'Average':>14}{'Requests':>14}")
    print("-" * 72)
    for result in sorted(results, key=lambda r: r.movement):
        print(
            f"{result.algorithm:<12}"
            f"{result.movement:>14}"
            f"{result.average_seek:>14.2f}"
            f"{result.service_count:>14}"
        )


def demonstrate_edge_cases() -> None:
    print("\nValidation and edge cases")
    print("=" * 72)

    scheduler = DiskScheduler(200, 50)

    cases = [
        ("invalid head", lambda: DiskScheduler(200, 250)),
        ("invalid request", lambda: scheduler.fcfs([10, 220])),
        ("empty request list", lambda: scheduler.fcfs([])),
        ("invalid direction", lambda: scheduler.look([10, 80], "up")),
    ]

    for name, operation in cases:
        try:
            operation()
        except ValueError as exc:
            print(f"{name}: correctly rejected -> {exc}")


def interactive_example() -> None:
    print("\nInteractive calculation")
    print("=" * 72)

    raw = input(
        "Enter request cylinders separated by spaces "
        "(press Enter to use the built-in example): "
    ).strip()

    if raw:
        try:
            requests = [int(value) for value in raw.split()]
        except ValueError:
            print("Requests must contain integers.")
            return
    else:
        requests = [98, 183, 37, 122, 14, 124, 65, 67]

    direction = input("Initial direction [right/left] (right): ").strip().lower()
    direction = direction or "right"

    try:
        scheduler = DiskScheduler(200, 53)
        results = scheduler.all_algorithms(requests, direction)
    except ValueError as exc:
        print(f"Input error: {exc}")
        return

    for result in results:
        print_result(result)
    compare(results)


def main() -> None:
    print("DISK SCHEDULING LAB")
    print("=" * 72)
    print("Disk cylinders: 0..199")
    print("Initial head  : 53")
    print("Requests      : 98, 183, 37, 122, 14, 124, 65, 67")
    print("Direction     : right")

    scheduler = DiskScheduler(200, 53)
    requests = [98, 183, 37, 122, 14, 124, 65, 67]

    for result in scheduler.all_algorithms(requests, "right"):
        print_result(result)

    compare(scheduler.all_algorithms(requests, "right"))
    demonstrate_edge_cases()

    # Set RUN_INTERACTIVE = True to enter requests manually.
    RUN_INTERACTIVE = False
    if RUN_INTERACTIVE:
        interactive_example()


if __name__ == "__main__":
    main()
