from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import Enum
import heapq
from typing import Deque, Generic, Iterable, Iterator, Optional, TypeVar


T = TypeVar("T")


class QueueError(Exception):
    """Base exception for queue-related failures."""


class QueueEmptyError(QueueError):
    """Raised when removing or inspecting an empty queue."""


class QueueFullError(QueueError):
    """Raised when inserting into a full bounded queue."""


class Queue:
    """FIFO queue with O(1) enqueue and dequeue operations."""

    def __init__(self, values: Iterable[T] = ()) -> None:
        self._items: Deque[T] = deque(values)

    def enqueue(self, value: T) -> None:
        self._items.append(value)

    def dequeue(self) -> T:
        if not self._items:
            raise QueueEmptyError("cannot dequeue from an empty queue")
        return self._items.popleft()

    def peek(self) -> T:
        if not self._items:
            raise QueueEmptyError("cannot peek at an empty queue")
        return self._items[0]

    def is_empty(self) -> bool:
        return not self._items

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)


class CircularQueue(Generic[T]):
    """Fixed-capacity FIFO queue backed by a circular array."""

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self._data: list[Optional[T]] = [None] * capacity
        self._capacity = capacity
        self._head = 0
        self._tail = 0
        self._size = 0

    def enqueue(self, value: T) -> None:
        if self.is_full():
            raise QueueFullError("circular queue is full")
        self._data[self._tail] = value
        self._tail = (self._tail + 1) % self._capacity
        self._size += 1

    def dequeue(self) -> T:
        if self.is_empty():
            raise QueueEmptyError("circular queue is empty")

        value = self._data[self._head]
        self._data[self._head] = None
        self._head = (self._head + 1) % self._capacity
        self._size -= 1

        if value is None:
            raise RuntimeError("internal circular queue invariant violated")
        return value

    def peek(self) -> T:
        if self.is_empty():
            raise QueueEmptyError("circular queue is empty")

        value = self._data[self._head]
        if value is None:
            raise RuntimeError("internal circular queue invariant violated")
        return value

    def is_empty(self) -> bool:
        return self._size == 0

    def is_full(self) -> bool:
        return self._size == self._capacity

    def __len__(self) -> int:
        return self._size

    def snapshot(self) -> list[T]:
        return [
            self._data[(self._head + offset) % self._capacity]  # type: ignore[misc]
            for offset in range(self._size)
        ]


class DequeModel(Generic[T]):
    """Double-ended queue supporting O(1) insertion/removal at both ends."""

    def __init__(self, values: Iterable[T] = ()) -> None:
        self._items: Deque[T] = deque(values)

    def push_front(self, value: T) -> None:
        self._items.appendleft(value)

    def push_back(self, value: T) -> None:
        self._items.append(value)

    def pop_front(self) -> T:
        if not self._items:
            raise QueueEmptyError("deque is empty")
        return self._items.popleft()

    def pop_back(self) -> T:
        if not self._items:
            raise QueueEmptyError("deque is empty")
        return self._items.pop()

    def peek_front(self) -> T:
        if not self._items:
            raise QueueEmptyError("deque is empty")
        return self._items[0]

    def peek_back(self) -> T:
        if not self._items:
            raise QueueEmptyError("deque is empty")
        return self._items[-1]

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)


@dataclass(frozen=True, order=True)
class PriorityItem:
    priority: int
    sequence: int
    task: str


class PriorityQueue:
    """Stable min-priority queue. Lower numeric priority is served first."""

    def __init__(self) -> None:
        self._heap: list[PriorityItem] = []
        self._sequence = 0

    def push(self, task: str, priority: int) -> None:
        if not task.strip():
            raise ValueError("task must contain non-whitespace characters")
        heapq.heappush(
            self._heap,
            PriorityItem(priority, self._sequence, task.strip()),
        )
        self._sequence += 1

    def pop(self) -> PriorityItem:
        if not self._heap:
            raise QueueEmptyError("priority queue is empty")
        return heapq.heappop(self._heap)

    def peek(self) -> PriorityItem:
        if not self._heap:
            raise QueueEmptyError("priority queue is empty")
        return self._heap[0]

    def __len__(self) -> int:
        return len(self._heap)


class JobState(Enum):
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Job:
    job_id: int
    name: str
    priority: int
    state: JobState = JobState.WAITING


class Scheduler:
    """Small scheduler using FIFO intake plus priority-based dispatch."""

    def __init__(self, capacity: int = 8) -> None:
        self._intake = CircularQueue[Job](capacity)
        self._ready = PriorityQueue()
        self._jobs: dict[int, Job] = {}

    def submit(self, job: Job) -> None:
        if job.job_id in self._jobs:
            raise ValueError(f"duplicate job id: {job.job_id}")
        if job.priority < 0:
            raise ValueError("priority cannot be negative")

        self._intake.enqueue(job)
        self._jobs[job.job_id] = job

    def stage_jobs(self) -> None:
        while not self._intake.is_empty():
            job = self._intake.dequeue()
            self._ready.push(job.name, job.priority)

    def dispatch(self) -> Optional[PriorityItem]:
        if len(self._ready) == 0:
            return None
        item = self._ready.pop()
        return item

    def pending_intake(self) -> list[Job]:
        return self._intake.snapshot()


def demonstrate() -> None:
    print("=== FIFO Queue ===")
    queue = Queue(["commit-101", "commit-102"])
    queue.enqueue("commit-103")
    print(queue.dequeue())
    print(queue.peek())
    print(list(queue))

    print("\n=== Circular Queue ===")
    circular = CircularQueue[str](3)
    circular.enqueue("build")
    circular.enqueue("test")
    circular.enqueue("deploy")
    print(circular.snapshot())

    print(circular.dequeue())
    circular.enqueue("monitor")
    print(circular.snapshot())

    try:
        circular.enqueue("overflow")
    except QueueFullError as exc:
        print(f"expected failure: {exc}")

    print("\n=== Deque ===")
    task_deque = DequeModel(["review", "merge"])
    task_deque.push_front("security-check")
    task_deque.push_back("audit")
    print(task_deque.pop_front())
    print(task_deque.pop_back())
    print(list(task_deque))

    print("\n=== Priority Queue ===")
    priority_queue = PriorityQueue()
    priority_queue.push("normal-build", 30)
    priority_queue.push("security-hotfix", 5)
    priority_queue.push("release", 10)
    priority_queue.push("documentation", 30)

    while len(priority_queue):
        item = priority_queue.pop()
        print(item.priority, item.task)

    print("\n=== Scheduler ===")
    scheduler = Scheduler(capacity=4)
    scheduler.submit(Job(1, "unit-tests", 20))
    scheduler.submit(Job(2, "security-scan", 5))
    scheduler.submit(Job(3, "release-build", 10))
    scheduler.stage_jobs()

    while True:
        dispatched = scheduler.dispatch()
        if dispatched is None:
            break
        print(f"dispatch priority={dispatched.priority}: {dispatched.task}")

    print("\n=== Validation ===")
    try:
        CircularQueue[int](0)
    except ValueError as exc:
        print(f"invalid capacity rejected: {exc}")

    try:
        Queue().dequeue()
    except QueueEmptyError as exc:
        print(f"empty queue rejected: {exc}")

    print("\nAll queue invariants passed.")

    # Basic executable assertions act as lightweight regression tests.
    fifo = Queue([1, 2, 3])
    assert [fifo.dequeue(), fifo.dequeue(), fifo.dequeue()] == [1, 2, 3]

    cq = CircularQueue[int](2)
    cq.enqueue(1)
    cq.enqueue(2)
    assert cq.dequeue() == 1
    cq.enqueue(3)
    assert cq.snapshot() == [2, 3]

    dq = DequeModel[int]()
    dq.push_front(2)
    dq.push_front(1)
    dq.push_back(3)
    assert [dq.pop_front(), dq.pop_back(), dq.pop_front()] == [1, 3, 2]

    pq = PriorityQueue()
    pq.push("low", 50)
    pq.push("urgent", 1)
    assert pq.pop().task == "urgent"


if __name__ == "__main__":
    demonstrate()
