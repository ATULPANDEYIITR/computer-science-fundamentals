"""
Synchronization Fundamentals: Race Conditions, Critical Sections, and Mutual Exclusion

This executable program demonstrates how concurrent operations can corrupt shared
state, why a critical section needs protection, and how mutual exclusion prevents
two threads from entering that critical section simultaneously.

Run:
    python synchronization_fundamentals.py
"""

from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass
from typing import Callable


@dataclass
class Account:
    """A deliberately simple shared resource used by the concurrency examples."""
    balance: int


def unsafe_increment(shared: dict[str, int], iterations: int) -> None:
    """
    Perform a read-modify-write operation without synchronization.

    The expression conceptually looks like:
        value = shared["counter"]
        value = value + 1
        shared["counter"] = value

    The three operations form a critical section. Without mutual exclusion,
    another thread can read the same old value between the read and the write.
    """
    for _ in range(iterations):
        current = shared["counter"]

        # Sleeping here does not make the race possible in principle; it makes
        # the scheduling window easier to observe during this demonstration.
        time.sleep(0.00001)

        shared["counter"] = current + 1


def demonstrate_race_condition() -> None:
    """Show lost updates caused by unsynchronized read-modify-write operations."""
    print("\n=== Race Condition ===")

    shared = {"counter": 0}
    thread_count = 8
    iterations = 100

    threads = [
        threading.Thread(
            target=unsafe_increment,
            args=(shared, iterations),
            name=f"unsafe-worker-{index}",
        )
        for index in range(thread_count)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    expected = thread_count * iterations
    actual = shared["counter"]

    print(f"Expected counter: {expected}")
    print(f"Actual counter:   {actual}")
    print(f"Lost updates:     {expected - actual}")

    if actual != expected:
        print("Race condition observed: concurrent updates overwrote each other.")
    else:
        print(
            "This run did not expose the race. Scheduling can vary, "
            "but the operation remains logically unsafe."
        )


def safe_increment(
    shared: dict[str, int],
    iterations: int,
    lock: threading.Lock,
) -> None:
    """
    Protect the read-modify-write operation with a mutex.

    Lock acquisition and release establish mutual exclusion. Only the thread
    holding the lock can execute the protected critical section.
    """
    for _ in range(iterations):
        with lock:
            current = shared["counter"]
            time.sleep(0.00001)
            shared["counter"] = current + 1


def demonstrate_mutual_exclusion() -> None:
    """Show how a lock protects a shared critical section."""
    print("\n=== Mutual Exclusion ===")

    shared = {"counter": 0}
    lock = threading.Lock()

    thread_count = 8
    iterations = 100

    threads = [
        threading.Thread(
            target=safe_increment,
            args=(shared, iterations, lock),
            name=f"safe-worker-{index}",
        )
        for index in range(thread_count)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    expected = thread_count * iterations
    actual = shared["counter"]

    print(f"Expected counter: {expected}")
    print(f"Actual counter:   {actual}")
    print(f"Protected result: {actual == expected}")


def withdraw_without_lock(account: Account, amount: int) -> bool:
    """
    Unsafe withdrawal.

    The balance check and balance update belong to one logical critical section.
    If two threads perform this operation concurrently, both can observe the
    same balance and approve withdrawals that should not both succeed.
    """
    if account.balance < amount:
        return False

    time.sleep(0.001)
    account.balance -= amount
    return True


def withdraw_with_lock(
    account: Account,
    amount: int,
    lock: threading.Lock,
) -> bool:
    """Safely validate and modify the account inside one critical section."""
    with lock:
        if account.balance < amount:
            return False

        time.sleep(0.001)
        account.balance -= amount
        return True


def demonstrate_check_then_act_race() -> None:
    """
    Demonstrate why the validation and state change must be atomic with respect
    to competing threads.
    """
    print("\n=== Check-Then-Act Race ===")

    account = Account(balance=100)
    amount = 80
    results: list[bool] = []

    def worker() -> None:
        results.append(withdraw_without_lock(account, amount))

    threads = [threading.Thread(target=worker) for _ in range(2)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    print(f"Withdrawal results without lock: {results}")
    print(f"Final balance: {account.balance}")

    account = Account(balance=100)
    lock = threading.Lock()
    results.clear()

    def safe_worker() -> None:
        results.append(withdraw_with_lock(account, amount, lock))

    threads = [threading.Thread(target=safe_worker) for _ in range(2)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    print(f"Withdrawal results with lock:    {results}")
    print(f"Final balance: {account.balance}")


class Inventory:
    """
    Shared inventory with a protected critical section.

    The lock belongs to the resource whose invariants it protects. This makes
    it harder for callers to accidentally manipulate the inventory without
    synchronization.
    """

    def __init__(self, quantity: int) -> None:
        if quantity < 0:
            raise ValueError("Initial quantity cannot be negative.")

        self._quantity = quantity
        self._lock = threading.Lock()

    def reserve(self, amount: int) -> bool:
        if amount <= 0:
            raise ValueError("Reservation amount must be positive.")

        with self._lock:
            if amount > self._quantity:
                return False

            self._quantity -= amount
            return True

    @property
    def quantity(self) -> int:
        with self._lock:
            return self._quantity


def demonstrate_resource_encapsulation() -> None:
    """Demonstrate a thread-safe shared resource abstraction."""
    print("\n=== Thread-Safe Resource ===")

    inventory = Inventory(quantity=100)
    successful_reservations = 0
    result_lock = threading.Lock()

    def reserve_worker() -> None:
        nonlocal successful_reservations

        requested = random.randint(1, 8)
        if inventory.reserve(requested):
            with result_lock:
                successful_reservations += 1

    threads = [
        threading.Thread(target=reserve_worker)
        for _ in range(40)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    print(f"Successful reservations: {successful_reservations}")
    print(f"Remaining inventory:     {inventory.quantity}")


def demonstrate_lock_timeout() -> None:
    """
    Show a failure-handling pattern for lock acquisition.

    A timeout prevents a worker from waiting indefinitely when another operation
    holds the critical section for too long.
    """
    print("\n=== Lock Acquisition Timeout ===")

    lock = threading.Lock()
    lock.acquire()

    def blocked_worker() -> None:
        acquired = lock.acquire(timeout=0.05)

        if not acquired:
            print("Worker could not enter the critical section before timeout.")
            return

        try:
            print("Worker entered the critical section.")
        finally:
            lock.release()

    thread = threading.Thread(target=blocked_worker)
    thread.start()
    thread.join()

    lock.release()


def demonstrate_reentrant_lock() -> None:
    """
    Demonstrate RLock when the same thread legitimately needs to acquire the
    same lock through nested calls.

    A normal Lock would deadlock if the same thread attempted to acquire it
    again before releasing it.
    """
    print("\n=== Reentrant Lock ===")

    lock = threading.RLock()

    def outer_operation() -> None:
        with lock:
            inner_operation()

    def inner_operation() -> None:
        with lock:
            print("The same thread acquired the RLock twice safely.")

    outer_operation()


class Bank:
    """
    Two-account transfer system.

    Each account has its own lock. Lock ordering is used to avoid deadlock:
    both operations acquire account locks according to object identity order.
    """

    @dataclass
    class _Account:
        identifier: str
        balance: int
        lock: threading.Lock

    def __init__(self) -> None:
        self.accounts = {
            "A": self._Account("A", 1000, threading.Lock()),
            "B": self._Account("B", 1000, threading.Lock()),
        }

    def transfer(self, source_id: str, target_id: str, amount: int) -> bool:
        if source_id == target_id:
            raise ValueError("Source and target must be different.")

        if amount <= 0:
            raise ValueError("Transfer amount must be positive.")

        source = self.accounts[source_id]
        target = self.accounts[target_id]

        # Consistent ordering prevents A->B and B->A transfers from waiting
        # forever for each other's locks.
        first, second = sorted(
            (source, target),
            key=lambda account: account.identifier,
        )

        with first.lock:
            with second.lock:
                if source.balance < amount:
                    return False

                source.balance -= amount
                target.balance += amount
                return True

    def total_balance(self) -> int:
        accounts = sorted(
            self.accounts.values(),
            key=lambda account: account.identifier,
        )

        with accounts[0].lock:
            with accounts[1].lock:
                return sum(account.balance for account in accounts)


def demonstrate_deadlock_avoidance() -> None:
    """Run opposing transfers while maintaining a consistent lock order."""
    print("\n=== Multiple Locks and Deadlock Avoidance ===")

    bank = Bank()
    transfer_count = 500

    def transfer_forward() -> None:
        for _ in range(transfer_count):
            bank.transfer("A", "B", 1)

    def transfer_backward() -> None:
        for _ in range(transfer_count):
            bank.transfer("B", "A", 1)

    threads = [
        threading.Thread(target=transfer_forward),
        threading.Thread(target=transfer_backward),
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    print(f"Account A: {bank.accounts['A'].balance}")
    print(f"Account B: {bank.accounts['B'].balance}")
    print(f"Total:     {bank.total_balance()}")


def benchmark(
    name: str,
    operation: Callable[[dict[str, int], int], None],
    thread_count: int,
    iterations: int,
) -> None:
    """Measure an operation to illustrate synchronization overhead."""
    shared = {"counter": 0}

    start = time.perf_counter()

    threads = [
        threading.Thread(
            target=operation,
            args=(shared, iterations),
        )
        for _ in range(thread_count)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    elapsed = time.perf_counter() - start

    print(
        f"{name}: counter={shared['counter']}, "
        f"time={elapsed:.6f}s"
    )


def demonstrate_performance_tradeoff() -> None:
    """
    A lock adds overhead and can reduce parallelism around the protected region.

    Correctness must be established first. Performance optimization should then
    minimize the amount of work performed while holding the lock.
    """
    print("\n=== Synchronization Performance Trade-Off ===")

    lock = threading.Lock()

    def synchronized_operation(
        shared: dict[str, int],
        iterations: int,
    ) -> None:
        for _ in range(iterations):
            with lock:
                shared["counter"] += 1

    benchmark(
        "Protected increment",
        synchronized_operation,
        thread_count=4,
        iterations=10_000,
    )


def main() -> None:
    print("Synchronization Fundamentals")
    print("============================")
    print("Focus: race conditions, critical sections, and mutual exclusion.")

    demonstrate_race_condition()
    demonstrate_mutual_exclusion()
    demonstrate_check_then_act_race()
    demonstrate_resource_encapsulation()
    demonstrate_lock_timeout()
    demonstrate_reentrant_lock()
    demonstrate_deadlock_avoidance()
    demonstrate_performance_trade_off()


if __name__ == "__main__":
    main()
