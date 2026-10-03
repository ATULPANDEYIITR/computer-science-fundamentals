"""
Threads: processes vs threads, multithreading, thread models, and thread lifecycle.

This executable case study builds a small parallel log-processing service. It starts
with process/thread isolation, demonstrates thread lifecycle states, compares
single-threaded and multithreaded execution, models common thread architectures,
and finishes with synchronization, worker pools, failures, cancellation, and
performance measurements.

Python's threading module is particularly useful for I/O-bound concurrency.
CPython's Global Interpreter Lock (GIL) prevents multiple Python bytecode
instructions from executing simultaneously in ordinary CPU-bound threads, so
threads should not be presented as a universal CPU-parallelism mechanism.
"""

from __future__ import annotations

import concurrent.futures
import multiprocessing
import os
import queue
import random
import threading
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Iterable


# ---------------------------------------------------------------------------
# Thread lifecycle
# ---------------------------------------------------------------------------

class ThreadState(Enum):
    NEW = auto()
    RUNNABLE = auto()
    RUNNING = auto()
    WAITING = auto()
    TERMINATED = auto()


@dataclass
class LifecycleRecord:
    name: str
    state: ThreadState
    timestamp: float
    detail: str


class LifecycleTracer:
    """Records application-level lifecycle events.

    Python exposes limited internal thread-state information, so an application
    should model meaningful lifecycle transitions explicitly rather than trying
    to infer scheduler state from private interpreter internals.
    """

    def __init__(self) -> None:
        self._records: list[LifecycleRecord] = []
        self._lock = threading.Lock()

    def record(self, name: str, state: ThreadState, detail: str) -> None:
        with self._lock:
            self._records.append(
                LifecycleRecord(name, state, time.perf_counter(), detail)
            )

    def print_records(self) -> None:
        print("\nThread lifecycle trace")
        for record in self._records:
            print(
                f"  {record.name:<18} "
                f"{record.state.name:<10} "
                f"{record.detail}"
            )


def lifecycle_worker(
    tracer: LifecycleTracer,
    ready_event: threading.Event,
) -> None:
    name = threading.current_thread().name

    tracer.record(name, ThreadState.RUNNABLE, "worker entered scheduling domain")
    ready_event.set()

    tracer.record(name, ThreadState.RUNNING, "worker started useful work")
    time.sleep(0.03)

    tracer.record(name, ThreadState.WAITING, "worker waiting on a timer")
    time.sleep(0.03)

    tracer.record(name, ThreadState.RUNNING, "worker resumed")
    tracer.record(name, ThreadState.TERMINATED, "worker function returned")


def demonstrate_thread_lifecycle() -> None:
    print("\n=== Thread lifecycle ===")

    tracer = LifecycleTracer()
    ready = threading.Event()

    worker = threading.Thread(
        target=lifecycle_worker,
        args=(tracer, ready),
        name="lifecycle-worker",
    )

    tracer.record(worker.name, ThreadState.NEW, "Thread object created")
    print(f"Before start: alive={worker.is_alive()}")

    worker.start()
    tracer.record(worker.name, ThreadState.RUNNABLE, "Thread.start() returned")

    ready.wait(timeout=1.0)
    print(f"During execution: alive={worker.is_alive()}")

    worker.join(timeout=1.0)
    print(f"After join: alive={worker.is_alive()}")

    tracer.print_records()


# ---------------------------------------------------------------------------
# Process and thread identity
# ---------------------------------------------------------------------------

def identify_execution_context(label: str) -> dict[str, int | str]:
    return {
        "label": label,
        "process_id": os.getpid(),
        "thread_id": threading.get_ident(),
        "thread_name": threading.current_thread().name,
    }


def process_identity_worker(output_queue: multiprocessing.Queue) -> None:
    output_queue.put(identify_execution_context("child process"))


def demonstrate_process_vs_thread_identity() -> None:
    print("\n=== Processes versus threads ===")

    main_context = identify_execution_context("main thread")
    print(
        f"Main: process={main_context['process_id']}, "
        f"thread={main_context['thread_id']}"
    )

    thread_result: list[dict[str, int | str]] = []

    def thread_worker() -> None:
        thread_result.append(identify_execution_context("child thread"))

    thread = threading.Thread(target=thread_worker, name="identity-thread")
    thread.start()
    thread.join()

    print(
        f"Thread: process={thread_result[0]['process_id']}, "
        f"thread={thread_result[0]['thread_id']}"
    )
    print("A thread shares its process identity and address space with sibling threads.")

    output_queue: multiprocessing.Queue = multiprocessing.Queue()
    process = multiprocessing.Process(
        target=process_identity_worker,
        args=(output_queue,),
        name="identity-process",
    )
    process.start()
    process.join()

    child_context = output_queue.get(timeout=1.0)
    print(
        f"Process: process={child_context['process_id']}, "
        f"thread={child_context['thread_id']}"
    )
    print("A process has a separate virtual address space from the parent process.")


# ---------------------------------------------------------------------------
# Race condition and synchronization
# ---------------------------------------------------------------------------

class UnsafeCounter:
    def __init__(self) -> None:
        self.value = 0

    def increment(self) -> None:
        current = self.value
        time.sleep(0)
        self.value = current + 1


class SafeCounter:
    def __init__(self) -> None:
        self.value = 0
        self._lock = threading.Lock()

    def increment(self) -> None:
        with self._lock:
            current = self.value
            time.sleep(0)
            self.value = current + 1


def run_counter(counter: UnsafeCounter | SafeCounter, increments: int) -> None:
    for _ in range(increments):
        counter.increment()


def demonstrate_synchronization() -> None:
    print("\n=== Shared state and synchronization ===")

    worker_count = 6
    increments_per_worker = 200

    unsafe = UnsafeCounter()
    threads = [
        threading.Thread(
            target=run_counter,
            args=(unsafe, increments_per_worker),
            name=f"unsafe-{i}",
        )
        for i in range(worker_count)
    ]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    expected = worker_count * increments_per_worker
    print(f"Unsafe counter: actual={unsafe.value}, expected={expected}")

    safe = SafeCounter()
    threads = [
        threading.Thread(
            target=run_counter,
            args=(safe, increments_per_worker),
            name=f"safe-{i}",
        )
        for i in range(worker_count)
    ]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    print(f"Locked counter: actual={safe.value}, expected={expected}")
    print(
        "The lock protects the read-modify-write critical section. "
        "The lock is not required merely because multiple threads exist."
    )


# ---------------------------------------------------------------------------
# Thread coordination primitives
# ---------------------------------------------------------------------------

def demonstrate_event_and_condition() -> None:
    print("\n=== Thread coordination ===")

    started = threading.Event()
    consumed = threading.Event()
    produced_item: list[str] = []

    def producer() -> None:
        time.sleep(0.03)
        produced_item.append("configuration-loaded")
        started.set()

    def consumer() -> None:
        if not started.wait(timeout=1.0):
            raise TimeoutError("consumer timed out waiting for producer")
        print(f"Consumer received: {produced_item[0]}")
        consumed.set()

    producer_thread = threading.Thread(target=producer, name="producer")
    consumer_thread = threading.Thread(target=consumer, name="consumer")

    consumer_thread.start()
    producer_thread.start()

    if not consumed.wait(timeout=1.0):
        raise TimeoutError("main thread timed out waiting for consumer")

    producer_thread.join()
    consumer_thread.join()

    condition = threading.Condition()
    buffer: queue.Queue[int] = queue.Queue(maxsize=2)
    consumed_values: list[int] = []

    def condition_producer() -> None:
        for value in range(4):
            with condition:
                while buffer.full():
                    condition.wait()
                buffer.put(value)
                condition.notify_all()

    def condition_consumer() -> None:
        for _ in range(4):
            with condition:
                while buffer.empty():
                    condition.wait()
                consumed_values.append(buffer.get())
                condition.notify_all()

    producer_thread = threading.Thread(
        target=condition_producer,
        name="condition-producer",
    )
    consumer_thread = threading.Thread(
        target=condition_consumer,
        name="condition-consumer",
    )

    producer_thread.start()
    consumer_thread.start()
    producer_thread.join()
    consumer_thread.join()

    print(f"Condition-controlled buffer values: {consumed_values}")


# ---------------------------------------------------------------------------
# Producer-consumer worker model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LogRecord:
    service: str
    level: str
    message: str


class LogProcessor:
    """Thread-safe producer-consumer processing pipeline."""

    SENTINEL = object()

    def __init__(self, worker_count: int = 3) -> None:
        if worker_count < 1:
            raise ValueError("worker_count must be at least one")

        self.worker_count = worker_count
        self._queue: queue.Queue[LogRecord | object] = queue.Queue(maxsize=4)
        self._results: list[str] = []
        self._results_lock = threading.Lock()
        self._threads: list[threading.Thread] = []

    def _process(self, record: LogRecord) -> str:
        # Simulate an I/O-bound operation such as sending an event to a remote
        # logging service. The sleep releases the GIL while waiting.
        time.sleep(0.005)

        if record.level not in {"INFO", "WARNING", "ERROR"}:
            raise ValueError(f"unsupported log level: {record.level}")

        return f"{record.level}:{record.service}:{record.message}"

    def _worker(self) -> None:
        while True:
            item = self._queue.get()
            try:
                if item is self.SENTINEL:
                    return

                try:
                    result = self._process(item)
                    with self._results_lock:
                        self._results.append(result)
                except Exception as exc:
                    with self._results_lock:
                        self._results.append(
                            f"FAILED:{item.service}:{type(exc).__name__}:{exc}"
                        )
            finally:
                self._queue.task_done()

    def start(self) -> None:
        for index in range(self.worker_count):
            thread = threading.Thread(
                target=self._worker,
                name=f"log-worker-{index}",
                daemon=False,
            )
            thread.start()
            self._threads.append(thread)

    def submit(self, record: LogRecord) -> None:
        if not isinstance(record, LogRecord):
            raise TypeError("submit expects LogRecord")
        self._queue.put(record)

    def close(self) -> None:
        self._queue.join()

        for _ in self._threads:
            self._queue.put(self.SENTINEL)

        for thread in self._threads:
            thread.join()

    @property
    def results(self) -> list[str]:
        with self._results_lock:
            return list(self._results)


def demonstrate_worker_model() -> None:
    print("\n=== Producer-consumer worker model ===")

    records = [
        LogRecord("api", "INFO", "request completed"),
        LogRecord("payments", "WARNING", "retry scheduled"),
        LogRecord("users", "ERROR", "database timeout"),
        LogRecord("search", "INFO", "index refreshed"),
        LogRecord("api", "INVALID", "bad severity"),
    ]

    processor = LogProcessor(worker_count=3)
    processor.start()

    for record in records:
        processor.submit(record)

    processor.close()

    for result in processor.results:
        print(f"  {result}")


# ---------------------------------------------------------------------------
# Thread pool and futures
# ---------------------------------------------------------------------------

def simulate_remote_lookup(host: str) -> str:
    if not host:
        raise ValueError("host cannot be empty")

    # A deterministic delay keeps the demonstration reproducible enough while
    # still modeling an operation dominated by waiting rather than computation.
    time.sleep(0.02)
    return f"{host}:reachable"


def demonstrate_thread_pool() -> None:
    print("\n=== Thread pool and futures ===")

    hosts = [
        "api.internal",
        "database.internal",
        "cache.internal",
        "queue.internal",
    ]

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=3,
        thread_name_prefix="lookup",
    ) as executor:
        futures = {
            executor.submit(simulate_remote_lookup, host): host
            for host in hosts
        }

        for future in concurrent.futures.as_completed(futures):
            host = futures[future]
            try:
                print(f"  {future.result()}")
            except Exception as exc:
                print(f"  {host}: failed: {exc}")

    print(
        "A Future represents the eventual result or failure of submitted work. "
        "The executor controls worker-thread reuse."
    )


# ---------------------------------------------------------------------------
# Thread model architecture
# ---------------------------------------------------------------------------

def demonstrate_thread_models() -> None:
    print("\n=== Thread models ===")

    model_descriptions = {
        "many-to-one": (
            "Many user-level threads map to one kernel thread. "
            "A blocking kernel operation can block the entire process, "
            "and the process cannot obtain parallel CPU execution from those threads."
        ),
        "one-to-one": (
            "Each user-visible thread maps to a kernel schedulable thread. "
            "Modern operating systems commonly use this model because independent "
            "threads can be scheduled on different CPU cores."
        ),
        "many-to-many": (
            "Many user-level threads are multiplexed over a pool of kernel threads. "
            "The runtime can expose many logical execution contexts while the OS "
            "schedules a bounded number of kernel threads."
        ),
    }

    for model, description in model_descriptions.items():
        print(f"\n{model}")
        print(f"  {description}")

    print(
        "\nThe Python Thread API does not expose a switch for selecting these "
        "OS-level mapping models. The actual mapping is determined by the "
        "runtime and operating-system implementation."
    )


# ---------------------------------------------------------------------------
# CPU-bound comparison
# ---------------------------------------------------------------------------

def count_primes(limit: int) -> int:
    if limit < 2:
        return 0

    count = 0
    for number in range(2, limit + 1):
        is_prime = True

        divisor = 2
        while divisor * divisor <= number:
            if number % divisor == 0:
                is_prime = False
                break
            divisor += 1

        if is_prime:
            count += 1

    return count


def threaded_prime_worker(limit: int, output: dict[int, int], index: int) -> None:
    output[index] = count_primes(limit)


def demonstrate_cpu_bound_limit() -> None:
    print("\n=== CPU-bound threads versus processes ===")

    limits = [12_000, 12_100, 12_200, 12_300]

    start = time.perf_counter()
    sequential_results = [count_primes(limit) for limit in limits]
    sequential_time = time.perf_counter() - start

    threaded_results: dict[int, int] = {}
    start = time.perf_counter()

    threads = [
        threading.Thread(
            target=threaded_prime_worker,
            args=(limit, threaded_results, index),
            name=f"prime-thread-{index}",
        )
        for index, limit in enumerate(limits)
    ]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    threaded_time = time.perf_counter() - start

    process_workers = min(len(limits), os.cpu_count() or 1)
    start = time.perf_counter()

    with multiprocessing.Pool(processes=process_workers) as pool:
        process_results = pool.map(count_primes, limits)

    process_time = time.perf_counter() - start

    print(f"Sequential results: {sequential_results}")
    print(f"Threaded results:   {[threaded_results[i] for i in range(len(limits))]}")
    print(f"Process results:    {process_results}")
    print(f"Sequential time: {sequential_time:.4f}s")
    print(f"Threaded time:   {threaded_time:.4f}s")
    print(f"Process time:    {process_time:.4f}s")

    print(
        "These measurements are machine-dependent. In CPython, CPU-bound "
        "Python threads generally do not provide the same parallelism as "
        "multiple processes because of the GIL."
    )


# ---------------------------------------------------------------------------
# Failure propagation and cancellation
# ---------------------------------------------------------------------------

def unreliable_task(task_id: int) -> str:
    time.sleep(0.01)

    if task_id == 3:
        raise RuntimeError("simulated worker failure")

    return f"task-{task_id}:completed"


def demonstrate_failure_handling() -> None:
    print("\n=== Failure propagation and cancellation ===")

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(unreliable_task, task_id)
            for task_id in range(6)
        ]

        for future in concurrent.futures.as_completed(futures):
            try:
                print(f"  {future.result()}")
            except Exception as exc:
                print(f"  worker failure: {type(exc).__name__}: {exc}")

    cancel_event = threading.Event()

    def cancellable_worker() -> str:
        for _ in range(100):
            if cancel_event.is_set():
                return "cancelled cooperatively"

            time.sleep(0.005)

        return "completed"

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(cancellable_worker)
        time.sleep(0.03)
        cancel_event.set()
        print(f"  {future.result()}")

    print(
        "Calling Future.cancel() cannot stop a task that is already running. "
        "Long-running thread work should expose a cooperative cancellation mechanism."
    )


# ---------------------------------------------------------------------------
# Deadlock demonstration as a safe static model
# ---------------------------------------------------------------------------

def demonstrate_deadlock_prevention() -> None:
    print("\n=== Deadlock prevention ===")

    lock_a = threading.Lock()
    lock_b = threading.Lock()

    print(
        "A classic deadlock occurs when thread A holds lock A and waits for B "
        "while thread B holds lock B and waits for A."
    )

    print(
        "The prevention strategy demonstrated conceptually here is global "
        "lock ordering: every worker acquires lock A before lock B."
    )

    with lock_a:
        with lock_b:
            print("  acquired locks in a consistent order")

    print(
        "Using a consistent order avoids circular wait. Other solutions include "
        "reducing lock scope, using higher-level concurrent data structures, "
        "timeouts, and redesigning shared-state ownership."
    )


# ---------------------------------------------------------------------------
# Practical architecture comparison
# ---------------------------------------------------------------------------

def choose_execution_model(workload: str) -> str:
    normalized = workload.strip().lower()

    if normalized in {"network", "io", "network-io", "file-io"}:
        return "Threads or an asynchronous event loop are appropriate for waiting-heavy I/O."
    if normalized in {"cpu", "cpu-bound", "computation"}:
        return "Processes are generally appropriate for CPU-bound Python computation."
    if normalized in {"isolation", "untrusted"}:
        return "Separate processes provide stronger memory and failure isolation than threads."
    if normalized in {"shared-memory", "low-latency"}:
        return "Threads can share memory efficiently, but shared-state synchronization must be designed carefully."

    raise ValueError(
        "workload must describe network, CPU, isolation, or shared-memory work"
    )


def demonstrate_design_selection() -> None:
    print("\n=== Execution-model selection ===")

    for workload in ("network", "cpu-bound", "isolation", "shared-memory"):
        print(f"{workload:<15} -> {choose_execution_model(workload)}")


def main() -> None:
    print("THREADS CASE STUDY")
    print("==================")
    print(
        "Focus: process isolation, thread lifecycle, multithreading, "
        "thread models, synchronization, and practical execution choices."
    )

    demonstrate_thread_lifecycle()
    demonstrate_process_vs_thread_identity()
    demonstrate_synchronization()
    demonstrate_event_and_condition()
    demonstrate_worker_model()
    demonstrate_thread_pool()
    demonstrate_thread_models()
    demonstrate_cpu_bound_limit()
    demonstrate_failure_handling()
    demonstrate_deadlock_prevention()
    demonstrate_design_selection()

    print("\nCase study completed.")


if __name__ == "__main__":
    main()
