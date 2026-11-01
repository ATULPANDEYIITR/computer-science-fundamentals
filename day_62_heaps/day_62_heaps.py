from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, Iterable, TypeVar
import heapq
import itertools
import random
import time


T = TypeVar("T")


class HeapType(Enum):
    MIN = "min"
    MAX = "max"


@dataclass(order=True)
class PriorityItem(Generic[T]):
    priority: int
    sequence: int
    value: T = field(compare=False)


class BinaryHeap(Generic[T]):
    """Array-backed binary heap supporting min and max semantics."""

    def __init__(self, heap_type: HeapType = HeapType.MIN):
        self.heap_type = heap_type
        self._data: list[T] = []

    def _better(self, a: T, b: T) -> bool:
        if self.heap_type is HeapType.MIN:
            return a < b
        return a > b

    def _sift_up(self, index: int) -> None:
        while index > 0:
            parent = (index - 1) // 2
            if not self._better(self._data[index], self._data[parent]):
                break
            self._data[index], self._data[parent] = (
                self._data[parent],
                self._data[index],
            )
            index = parent

    def _sift_down(self, index: int) -> None:
        size = len(self._data)

        while True:
            left = 2 * index + 1
            right = left + 1
            best = index

            if left < size and self._better(self._data[left], self._data[best]):
                best = left

            if right < size and self._better(self._data[right], self._data[best]):
                best = right

            if best == index:
                break

            self._data[index], self._data[best] = (
                self._data[best],
                self._data[index],
            )
            index = best

    def push(self, value: T) -> None:
        self._data.append(value)
        self._sift_up(len(self._data) - 1)

    def peek(self) -> T:
        if not self._data:
            raise IndexError("peek from empty heap")
        return self._data[0]

    def pop(self) -> T:
        if not self._data:
            raise IndexError("pop from empty heap")

        root = self._data[0]
        last = self._data.pop()

        if self._data:
            self._data[0] = last
            self._sift_down(0)

        return root

    def replace_root(self, value: T) -> T:
        if not self._data:
            raise IndexError("replace_root on empty heap")

        old = self._data[0]
        self._data[0] = value
        self._sift_down(0)
        return old

    def build(self, values: Iterable[T]) -> None:
        self._data = list(values)

        for index in range(len(self._data) // 2 - 1, -1, -1):
            self._sift_down(index)

    def heapify_sort(self, values: Iterable[T]) -> list[T]:
        temporary = BinaryHeap[T](self.heap_type)
        temporary.build(values)
        return [temporary.pop() for _ in range(len(temporary))]

    def validate(self) -> bool:
        for child in range(1, len(self._data)):
            parent = (child - 1) // 2
            if self._better(self._data[child], self._data[parent]):
                return False
        return True

    def __len__(self) -> int:
        return len(self._data)

    def __bool__(self) -> bool:
        return bool(self._data)

    def __repr__(self) -> str:
        return f"{self.heap_type.value}-heap({self._data!r})"


class StablePriorityQueue(Generic[T]):
    """Priority queue with FIFO behavior for equal priorities."""

    def __init__(self) -> None:
        self._counter = itertools.count()
        self._heap: list[tuple[int, int, T]] = []

    def push(self, value: T, priority: int) -> None:
        sequence = next(self._counter)
        heapq.heappush(self._heap, (priority, sequence, value))

    def pop(self) -> T:
        if not self._heap:
            raise IndexError("pop from empty priority queue")
        return heapq.heappop(self._heap)[2]

    def peek(self) -> T:
        if not self._heap:
            raise IndexError("peek from empty priority queue")
        return self._heap[0][2]

    def __len__(self) -> int:
        return len(self._heap)


@dataclass(frozen=True)
class Job:
    name: str
    priority: int
    duration: int


class JobScheduler:
    """Small scheduling example using a priority queue."""

    def __init__(self) -> None:
        self.queue = StablePriorityQueue[Job]()

    def submit(self, job: Job) -> None:
        if not job.name.strip():
            raise ValueError("job name cannot be empty")
        if job.priority < 0:
            raise ValueError("priority cannot be negative")
        if job.duration <= 0:
            raise ValueError("duration must be positive")

        self.queue.push(job, job.priority)

    def run(self) -> list[str]:
        completed: list[str] = []

        while self.queue:
            job = self.queue.pop()
            completed.append(
                f"{job.name}: priority={job.priority}, duration={job.duration}"
            )

        return completed


def demo_basic_operations() -> None:
    print("=== Binary Min Heap ===")
    min_heap = BinaryHeap[int](HeapType.MIN)

    for value in [9, 4, 7, 1, 3, 8, 2]:
        min_heap.push(value)

    print("Heap:", min_heap)
    print("Valid:", min_heap.validate())
    print("Peek:", min_heap.peek())

    popped = []
    while min_heap:
        popped.append(min_heap.pop())

    print("Ascending order:", popped)

    print("\n=== Binary Max Heap ===")
    max_heap = BinaryHeap[int](HeapType.MAX)
    max_heap.build([9, 4, 7, 1, 3, 8, 2])

    print("Heap:", max_heap)
    print("Peek:", max_heap.peek())

    descending = []
    while max_heap:
        descending.append(max_heap.pop())

    print("Descending order:", descending)


def demo_heapify_and_replace() -> None:
    print("\n=== Heapify and Replace Root ===")

    heap = BinaryHeap[int](HeapType.MIN)
    heap.build([12, 5, 19, 2, 8, 14, 3])

    print("Initial:", heap)
    removed = heap.replace_root(6)
    print("Replaced root:", removed)
    print("After replacement:", heap)
    print("Valid:", heap.validate())


def demo_priority_queue() -> None:
    print("\n=== Stable Priority Queue ===")

    scheduler = JobScheduler()

    jobs = [
        Job("database-backup", 2, 15),
        Job("security-alert", 0, 3),
        Job("report-generation", 3, 20),
        Job("cache-refresh", 2, 5),
        Job("incident-analysis", 1, 10),
    ]

    for job in jobs:
        scheduler.submit(job)

    for result in scheduler.run():
        print(result)


def demo_top_k() -> None:
    print("\n=== Top-K Elements ===")

    values = [17, 4, 29, 11, 35, 8, 42, 19, 23]
    k = 3

    if not 0 < k <= len(values):
        raise ValueError("k must be between 1 and the number of values")

    top_k = heapq.nlargest(k, values)
    print("Values:", values)
    print(f"Top {k}:", top_k)


def demo_heap_sort() -> None:
    print("\n=== Heap Sort ===")

    values = [15, 3, 20, 7, 9, 1, 14]
    heap = BinaryHeap[int](HeapType.MIN)

    result = heap.heapify_sort(values)
    print("Input:", values)
    print("Sorted:", result)


def demo_edge_cases() -> None:
    print("\n=== Edge Cases ===")

    heap = BinaryHeap[int]()

    try:
        heap.peek()
    except IndexError as exc:
        print("Empty peek:", exc)

    try:
        heap.pop()
    except IndexError as exc:
        print("Empty pop:", exc)

    try:
        JobScheduler().submit(Job("", 1, 5))
    except ValueError as exc:
        print("Invalid job:", exc)

    try:
        JobScheduler().submit(Job("invalid-duration", 1, 0))
    except ValueError as exc:
        print("Invalid duration:", exc)


def demo_performance() -> None:
    print("\n=== Performance Measurement ===")

    rng = random.Random(42)
    values = [rng.randint(1, 1_000_000) for _ in range(20_000)]

    heap = BinaryHeap[int](HeapType.MIN)

    start = time.perf_counter()
    heap.build(values)
    build_time = time.perf_counter() - start

    start = time.perf_counter()
    while heap:
        heap.pop()
    pop_time = time.perf_counter() - start

    print(f"Heapify time: {build_time:.6f}s")
    print(f"Repeated pop time: {pop_time:.6f}s")
    print("Build complexity: O(n)")
    print("Push/pop complexity: O(log n)")
    print("Peek complexity: O(1)")
    print("Array storage: O(n)")


def main() -> None:
    demo_basic_operations()
    demo_heapify_and_replace()
    demo_priority_queue()
    demo_top_k()
    demo_heap_sort()
    demo_edge_cases()
    demo_performance()


if __name__ == "__main__":
    main()
