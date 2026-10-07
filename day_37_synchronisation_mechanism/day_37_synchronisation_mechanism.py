"""
Synchronization Mechanisms in Python
====================================

Demonstrates mutexes, semaphores, monitors, locks, and condition variables
through progressively more realistic concurrent systems.

The examples use only Python's standard library and are executable as-is.
"""

from __future__ import annotations

import random
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional


def section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


# ---------------------------------------------------------------------------
# Mutex: protect a critical section
# ---------------------------------------------------------------------------

class SafeCounter:
    """A counter whose shared state is protected by a mutex."""

    def __init__(self) -> None:
        self._value = 0
        self._mutex = threading.Lock()

    def increment(self) -> None:
        with self._mutex:
            current = self._value
            time.sleep(0.0001)
            self._value = current + 1

    @property
    def value(self) -> int:
        with self._mutex:
            return self._value


def demonstrate_mutex() -> None:
    section("Mutex: protecting a shared counter")

    counter = SafeCounter()

    def worker() -> None:
        for _ in range(500):
            counter.increment()

    threads = [threading.Thread(target=worker) for _ in range(8)]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    print("Expected:", 8 * 500)
    print("Actual:  ", counter.value)


# ---------------------------------------------------------------------------
# Lock ownership and try-acquire behavior
# ---------------------------------------------------------------------------

def demonstrate_lock_operations() -> None:
    section("Lock operations: blocking and non-blocking acquisition")

    lock = threading.Lock()

    if lock.acquire(blocking=False):
        try:
            print("Main thread acquired the lock without blocking.")
        finally:
            lock.release()

    acquired = lock.acquire(timeout=0.05)
    try:
        print("Timed acquisition succeeded:", acquired)
    finally:
        if acquired:
            lock.release()

    print(
        "A Python Lock is a mutual-exclusion primitive: at most one thread "
        "can own the protected critical section at a time."
    )


# ---------------------------------------------------------------------------
# Semaphore: limit concurrent access to a finite resource
# ---------------------------------------------------------------------------

class ConnectionPool:
    """
    A semaphore models a finite number of simultaneously usable resources.

    The semaphore does not protect one piece of mutable state in the same
    way as a mutex. It controls how many workers may enter a region.
    """

    def __init__(self, capacity: int) -> None:
        self._capacity = capacity
        self._available = threading.Semaphore(capacity)
        self._active = 0
        self._peak = 0
        self._state_lock = threading.Lock()

    def use_connection(self, worker_id: int) -> None:
        acquired = self._available.acquire(timeout=1.0)
        if not acquired:
            raise TimeoutError(f"Worker {worker_id} could not obtain a connection")

        try:
            with self._state_lock:
                self._active += 1
                self._peak = max(self._peak, self._active)

            print(f"Worker {worker_id} acquired a connection")
            time.sleep(random.uniform(0.01, 0.04))
        finally:
            with self._state_lock:
                self._active -= 1
            self._available.release()
            print(f"Worker {worker_id} released a connection")

    @property
    def peak_usage(self) -> int:
        with self._state_lock:
            return self._peak


def demonstrate_semaphore() -> None:
    section("Semaphore: bounding concurrent resource usage")

    pool = ConnectionPool(capacity=3)

    threads = [
        threading.Thread(target=pool.use_connection, args=(worker_id,))
        for worker_id in range(10)
    ]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    print("Configured capacity:", 3)
    print("Observed peak usage:", pool.peak_usage)


# ---------------------------------------------------------------------------
# Condition variable: wait until a state predicate becomes true
# ---------------------------------------------------------------------------

class JobQueue:
    """
    A monitor-style queue using a mutex plus condition variables.

    Producers notify consumers after adding work. Consumers wait while the
    queue is empty instead of repeatedly polling it.
    """

    def __init__(self, maximum_size: int) -> None:
        self._queue: deque[str] = deque()
        self._maximum_size = maximum_size
        self._condition = threading.Condition()

    def put(self, job: str) -> None:
        with self._condition:
            while len(self._queue) >= self._maximum_size:
                self._condition.wait()

            self._queue.append(job)
            self._condition.notify()

    def get(self) -> Optional[str]:
        with self._condition:
            while not self._queue:
                self._condition.wait()

            job = self._queue.popleft()
            self._condition.notify()
            return job


def demonstrate_condition_variable() -> None:
    section("Condition variable: producer-consumer coordination")

    queue = JobQueue(maximum_size=2)
    processed: list[str] = []
    result_lock = threading.Lock()

    def producer() -> None:
        for number in range(6):
            job = f"job-{number}"
            queue.put(job)
            print("Produced:", job)
            time.sleep(0.01)

    def consumer() -> None:
        for _ in range(6):
            job = queue.get()
            time.sleep(0.02)
            with result_lock:
                processed.append(job)
            print("Consumed:", job)

    producer_thread = threading.Thread(target=producer)
    consumer_thread = threading.Thread(target=consumer)

    consumer_thread.start()
    producer_thread.start()

    producer_thread.join()
    consumer_thread.join()

    print("Processed jobs:", processed)


# ---------------------------------------------------------------------------
# Monitor: combine shared state, mutual exclusion, and waiting conditions
# ---------------------------------------------------------------------------

class BoundedBufferMonitor:
    """
    A monitor encapsulates both the protected state and the synchronization
    protocol required to manipulate it.

    The condition variable uses the monitor's lock. Both producer and
    consumer predicates are checked in loops because waking does not itself
    guarantee that the desired state remains true.
    """

    def __init__(self, capacity: int) -> None:
        self._items: deque[int] = deque()
        self._capacity = capacity
        self._condition = threading.Condition(threading.RLock())

    def produce(self, item: int) -> None:
        with self._condition:
            while len(self._items) == self._capacity:
                self._condition.wait()

            self._items.append(item)
            self._condition.notify_all()

    def consume(self) -> int:
        with self._condition:
            while not self._items:
                self._condition.wait()

            item = self._items.popleft()
            self._condition.notify_all()
            return item

    def snapshot(self) -> list[int]:
        with self._condition:
            return list(self._items)


def demonstrate_monitor() -> None:
    section("Monitor: encapsulated shared state and synchronization")

    buffer = BoundedBufferMonitor(capacity=3)
    consumed: list[int] = []
    consumed_lock = threading.Lock()

    def producer(start: int) -> None:
        for value in range(start, start + 5):
            buffer.produce(value)
            time.sleep(0.005)

    def consumer() -> None:
        for _ in range(5):
            value = buffer.consume()
            with consumed_lock:
                consumed.append(value)
            time.sleep(0.008)

    producers = [
        threading.Thread(target=producer, args=(0,)),
        threading.Thread(target=producer, args=(100,)),
    ]
    consumers = [
        threading.Thread(target=consumer),
        threading.Thread(target=consumer),
    ]

    for thread in consumers + producers:
        thread.start()
    for thread in consumers + producers:
        thread.join()

    print("Consumed values:", sorted(consumed))
    print("Remaining buffer:", buffer.snapshot())


# ---------------------------------------------------------------------------
# Deadlock avoidance through consistent lock ordering
# ---------------------------------------------------------------------------

class Account:
    def __init__(self, account_id: str, balance: int) -> None:
        self.account_id = account_id
        self.balance = balance
        self.lock = threading.Lock()


def transfer(first: Account, second: Account, amount: int) -> None:
    """
    Acquire accounts in deterministic ID order.

    Without a global ordering, one thread could lock A then wait for B while
    another locks B then waits for A. Deterministic ordering prevents that
    circular-wait condition.
    """
    if amount <= 0:
        raise ValueError("Transfer amount must be positive")

    if first.account_id == second.account_id:
        raise ValueError("Source and destination must differ")

    first_lock_account, second_lock_account = sorted(
        (first, second), key=lambda account: account.account_id
    )

    with first_lock_account.lock:
        with second_lock_account.lock:
            if first.balance < amount:
                raise ValueError("Insufficient funds")

            first.balance -= amount
            second.balance += amount


def demonstrate_deadlock_avoidance() -> None:
    section("Lock ordering: avoiding circular wait")

    account_a = Account("A", 1000)
    account_b = Account("B", 1000)

    operations = [
        (account_a, account_b),
        (account_b, account_a),
        (account_a, account_b),
        (account_b, account_a),
    ]

    threads = [
        threading.Thread(target=transfer, args=(source, target, 100))
        for source, target in operations
    ]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    print("Account A:", account_a.balance)
    print("Account B:", account_b.balance)
    print("Combined balance:", account_a.balance + account_b.balance)


# ---------------------------------------------------------------------------
# Reentrant lock: a monitor method can safely call another synchronized method
# ---------------------------------------------------------------------------

class InventoryMonitor:
    def __init__(self) -> None:
        self._stock: dict[str, int] = {"keyboard": 10, "mouse": 20}
        self._lock = threading.RLock()

    def _validate_product(self, product: str) -> None:
        if product not in self._stock:
            raise KeyError(f"Unknown product: {product}")

    def reserve(self, product: str, quantity: int) -> None:
        with self._lock:
            self._validate_product(product)
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
            if self._stock[product] < quantity:
                raise ValueError("Insufficient stock")
            self._stock[product] -= quantity

    def reserve_bundle(self, product: str, quantity: int) -> None:
        """
        RLock permits reserve_bundle() to call reserve() while the same
        thread already owns the monitor lock.
        """
        with self._lock:
            self.reserve(product, quantity)

    def stock(self) -> dict[str, int]:
        with self._lock:
            return dict(self._stock)


def demonstrate_reentrant_lock() -> None:
    section("Reentrant lock: nested monitor operations")

    inventory = InventoryMonitor()
    inventory.reserve_bundle("keyboard", 2)
    print("Inventory after reservation:", inventory.stock())


# ---------------------------------------------------------------------------
# Reader-writer pattern using a condition variable
# ---------------------------------------------------------------------------

class ReadWriteLock:
    """
    A compact reader-writer synchronization primitive.

    Multiple readers may enter simultaneously. Writers require exclusive
    access. New readers wait while a writer is active or waiting, which gives
    writers priority and prevents an endless writer starvation scenario.
    """

    def __init__(self) -> None:
        self._condition = threading.Condition()
        self._active_readers = 0
        self._active_writer = False
        self._waiting_writers = 0

    def acquire_read(self) -> None:
        with self._condition:
            while self._active_writer or self._waiting_writers > 0:
                self._condition.wait()
            self._active_readers += 1

    def release_read(self) -> None:
        with self._condition:
            if self._active_readers <= 0:
                raise RuntimeError("No read lock is held")
            self._active_readers -= 1
            if self._active_readers == 0:
                self._condition.notify_all()

    def acquire_write(self) -> None:
        with self._condition:
            self._waiting_writers += 1
            try:
                while self._active_writer or self._active_readers > 0:
                    self._condition.wait()
                self._active_writer = True
            finally:
                self._waiting_writers -= 1

    def release_write(self) -> None:
        with self._condition:
            if not self._active_writer:
                raise RuntimeError("No write lock is held")
            self._active_writer = False
            self._condition.notify_all()


class SharedConfiguration:
    def __init__(self) -> None:
        self._data = {"version": 1, "mode": "safe"}
        self._rw_lock = ReadWriteLock()

    def read(self) -> dict[str, object]:
        self._rw_lock.acquire_read()
        try:
            time.sleep(0.005)
            return dict(self._data)
        finally:
            self._rw_lock.release_read()

    def update(self, mode: str) -> None:
        if mode not in {"safe", "performance"}:
            raise ValueError("Unsupported configuration mode")

        self._rw_lock.acquire_write()
        try:
            self._data["version"] = int(self._data["version"]) + 1
            self._data["mode"] = mode
            time.sleep(0.01)
        finally:
            self._rw_lock.release_write()


def demonstrate_reader_writer_lock() -> None:
    section("Reader-writer lock built from a condition variable")

    configuration = SharedConfiguration()
    observations: list[dict[str, object]] = []
    observation_lock = threading.Lock()

    def reader(reader_id: int) -> None:
        state = configuration.read()
        with observation_lock:
            observations.append({"reader": reader_id, **state})

    def writer() -> None:
        configuration.update("performance")

    readers = [threading.Thread(target=reader, args=(i,)) for i in range(5)]
    writer_thread = threading.Thread(target=writer)

    for thread in readers[:2]:
        thread.start()

    writer_thread.start()

    for thread in readers[2:]:
        thread.start()

    for thread in readers:
        thread.join()
    writer_thread.join()

    print("Read observations:", observations)
    print("Final configuration:", configuration.read())


# ---------------------------------------------------------------------------
# Production-oriented service combining multiple synchronization primitives
# ---------------------------------------------------------------------------

@dataclass
class RateLimitedService:
    """
    A small service model.

    The semaphore limits expensive concurrent operations while the mutex
    protects aggregate metrics. This illustrates that synchronization
    primitives often solve different problems and can legitimately coexist.
    """

    concurrency_limit: int
    _semaphore: threading.Semaphore = field(init=False)
    _metrics_lock: threading.Lock = field(default_factory=threading.Lock, init=False)
    _completed: int = field(default=0, init=False)
    _failed: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if self.concurrency_limit <= 0:
            raise ValueError("Concurrency limit must be positive")
        self._semaphore = threading.Semaphore(self.concurrency_limit)

    def process(self, request_id: int, fail: bool = False) -> None:
        if not self._semaphore.acquire(timeout=0.5):
            with self._metrics_lock:
                self._failed += 1
            raise TimeoutError(f"Request {request_id} exceeded concurrency wait")

        try:
            time.sleep(random.uniform(0.005, 0.02))
            if fail:
                raise RuntimeError("Simulated downstream failure")

            with self._metrics_lock:
                self._completed += 1
        except Exception:
            with self._metrics_lock:
                self._failed += 1
            raise
        finally:
            self._semaphore.release()

    def metrics(self) -> dict[str, int]:
        with self._metrics_lock:
            return {
                "completed": self._completed,
                "failed": self._failed,
            }


def demonstrate_combined_service() -> None:
    section("Combined synchronization: bounded service with protected metrics")

    service = RateLimitedService(concurrency_limit=3)

    def worker(request_id: int) -> None:
        try:
            service.process(request_id, fail=request_id in {3, 7})
        except RuntimeError as exc:
            print(f"Request {request_id} failed:", exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    print("Service metrics:", service.metrics())


# ---------------------------------------------------------------------------
# Failure demonstrations
# ---------------------------------------------------------------------------

def demonstrate_common_failure_rules() -> None:
    section("Failure rules and synchronization discipline")

    lock = threading.Lock()
    lock.acquire()

    try:
        acquired = lock.acquire(timeout=0.01)
        print("Second acquisition by the same thread on a normal Lock:", acquired)
        if acquired:
            lock.release()
    finally:
        lock.release()

    print("A normal Lock is not reentrant.")
    print("Use RLock when the same thread legitimately enters nested protected code.")
    print("Always release acquired resources with try/finally or a context manager.")
    print("Condition predicates should be checked in while loops.")
    print("A semaphore must be released exactly once for every successful acquire.")
    print("Keep critical sections short to reduce contention.")
    print("Lock ordering is a practical deadlock-prevention technique.")
    print("Synchronization protects concurrent access; it does not replace input validation.")


def main() -> None:
    demonstrate_mutex()
    demonstrate_lock_operations()
    demonstrate_semaphore()
    demonstrate_condition_variable()
    demonstrate_monitor()
    demonstrate_deadlock_avoidance()
    demonstrate_reentrant_lock()
    demonstrate_reader_writer_lock()
    demonstrate_combined_service()
    demonstrate_common_failure_rules()


if __name__ == "__main__":
    main()
