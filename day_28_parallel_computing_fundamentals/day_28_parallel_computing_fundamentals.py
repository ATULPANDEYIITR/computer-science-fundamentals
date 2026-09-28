"""
Parallel Computing Fundamentals
Topics: parallelism, concurrency, multicore processors, SIMD, MIMD.

This standalone study program progresses from basic concepts to practical
parallel programming techniques using only the Python standard library.

Python's Global Interpreter Lock (GIL) means CPU-bound threads generally do
not execute Python bytecode simultaneously in standard CPython. Therefore,
ThreadPoolExecutor is demonstrated for concurrency/I/O-style work, while
ProcessPoolExecutor is used for CPU-bound parallel work.
"""

from __future__ import annotations

import math
import os
import statistics
import threading
import time
from concurrent.futures import (
    ThreadPoolExecutor,
    ProcessPoolExecutor,
    as_completed,
)
from dataclasses import dataclass
from functools import reduce
from multiprocessing import cpu_count
from typing import Iterable, Sequence


# ============================================================================
# 1. FUNDAMENTAL TERMINOLOGY
# ============================================================================

def print_section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def explain_fundamentals() -> None:
    print_section("1. Parallel Computing Fundamentals")

    print(
        """
Parallel computing divides work so that multiple computational resources
can make progress during overlapping time periods.

Concurrency and parallelism are related but different:

  Concurrency:
      Multiple tasks are in progress during overlapping periods.
      They do not necessarily execute simultaneously.

  Parallelism:
      Multiple units of work execute simultaneously on different execution
      resources, such as CPU cores.

A multicore CPU contains multiple processing cores. A program can exploit
those cores through multiple processes or suitable native/runtime mechanisms.

SIMD means Single Instruction, Multiple Data:
    one instruction operates on multiple data elements.

MIMD means Multiple Instruction, Multiple Data:
    different processing units may execute different instructions on
    different data.

Important distinction:
    A program can be concurrent without being parallel, and a parallel
    program is normally also concurrent because multiple activities overlap.
"""
    )


# ============================================================================
# 2. A SIMPLE SEQUENTIAL COMPUTATION
# ============================================================================

def sum_of_squares_sequential(values: Sequence[int]) -> int:
    """Sequential baseline used for comparison with parallel approaches."""
    total = 0
    for value in values:
        total += value * value
    return total


# ============================================================================
# 3. CONCURRENCY WITH THREADS
# ============================================================================

def simulated_io_task(task_id: int, delay: float = 0.05) -> str:
    """
    Simulate an I/O-bound task.

    While this thread sleeps, another thread can execute. This illustrates
    concurrency without requiring an external service.
    """
    time.sleep(delay)
    return f"task-{task_id} completed"


def demonstrate_concurrency() -> None:
    print_section("2. Concurrency with Threads")

    start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(simulated_io_task, task_id)
            for task_id in range(8)
        ]

        results = [future.result() for future in futures]

    elapsed = time.perf_counter() - start

    print("Concurrent results:", results)
    print(f"Elapsed time: {elapsed:.4f} seconds")
    print(
        "Threads are particularly useful for overlapping I/O-bound operations "
        "in standard CPython."
    )


# ============================================================================
# 4. RACE CONDITIONS AND SYNCHRONIZATION
# ============================================================================

@dataclass
class SharedCounter:
    value: int = 0


def demonstrate_lock() -> None:
    print_section("3. Shared State and Synchronization")

    counter = SharedCounter()
    lock = threading.Lock()

    def increment_many_times() -> None:
        for _ in range(10_000):
            # The lock protects the critical section.
            with lock:
                counter.value += 1

    threads = [
        threading.Thread(target=increment_many_times)
        for _ in range(8)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    print("Expected counter:", 80_000)
    print("Actual counter:  ", counter.value)
    print(
        "A lock establishes mutual exclusion: only one thread at a time "
        "enters the protected critical section."
    )


# ============================================================================
# 5. CPU-BOUND WORK
# ============================================================================

def is_prime(number: int) -> bool:
    """Efficient enough primality test for this educational example."""
    if number < 2:
        return False
    if number == 2:
        return True
    if number % 2 == 0:
        return False

    limit = math.isqrt(number)
    divisor = 3

    while divisor <= limit:
        if number % divisor == 0:
            return False
        divisor += 2

    return True


def count_primes_in_range(bounds: tuple[int, int]) -> int:
    """Count primes in [start, stop). Suitable for process parallelism."""
    start, stop = bounds
    return sum(1 for number in range(start, stop) if is_prime(number))


def split_range(start: int, stop: int, parts: int) -> list[tuple[int, int]]:
    """Divide an interval into approximately equal chunks."""
    if parts <= 0:
        raise ValueError("parts must be positive")

    length = stop - start
    chunks: list[tuple[int, int]] = []

    for index in range(parts):
        left = start + (length * index) // parts
        right = start + (length * (index + 1)) // parts
        if left < right:
            chunks.append((left, right))

    return chunks


def demonstrate_process_parallelism() -> None:
    print_section("4. Multicore CPU Parallelism")

    lower = 10_000
    upper = 40_000
    workers = max(1, min(cpu_count(), 4))
    chunks = split_range(lower, upper, workers)

    sequential_start = time.perf_counter()
    sequential_count = count_primes_in_range((lower, upper))
    sequential_time = time.perf_counter() - sequential_start

    parallel_start = time.perf_counter()

    # Processes can execute Python CPU-bound work on multiple CPU cores.
    with ProcessPoolExecutor(max_workers=workers) as executor:
        counts = list(executor.map(count_primes_in_range, chunks))

    parallel_count = sum(counts)
    parallel_time = time.perf_counter() - parallel_start

    print(f"Logical CPUs reported by the operating system: {cpu_count()}")
    print(f"Workers used: {workers}")
    print(f"Sequential prime count: {sequential_count}")
    print(f"Parallel prime count:   {parallel_count}")
    print(f"Sequential time: {sequential_time:.4f}s")
    print(f"Parallel time:   {parallel_time:.4f}s")

    if parallel_time > 0:
        print(f"Observed speedup: {sequential_time / parallel_time:.2f}x")

    print(
        "Measured speedups depend on CPU topology, process startup, "
        "serialization, workload size, operating-system scheduling, and "
        "other running programs."
    )


# ============================================================================
# 6. DATA PARALLELISM
# ============================================================================

def transform_chunk(values: Sequence[int]) -> list[int]:
    """
    Data-parallel transformation.

    Each worker receives an independent section of the input and applies the
    same operation to every element.
    """
    return [value * value + 2 * value + 1 for value in values]


def chunk_sequence(values: Sequence[int], size: int) -> list[Sequence[int]]:
    if size <= 0:
        raise ValueError("chunk size must be positive")
    return [values[index:index + size] for index in range(0, len(values), size)]


def demonstrate_data_parallelism() -> None:
    print_section("5. Data Parallelism")

    values = list(range(1, 17))
    chunks = chunk_sequence(values, 4)

    with ProcessPoolExecutor(max_workers=4) as executor:
        transformed_chunks = list(executor.map(transform_chunk, chunks))

    transformed = [
        item
        for chunk in transformed_chunks
        for item in chunk
    ]

    print("Input:      ", values)
    print("Transformed:", transformed)
    print(
        "This is data parallelism: the same operation is applied to separate "
        "partitions of a larger dataset."
    )


# ============================================================================
# 7. SIMD CONCEPTUAL MODEL
# ============================================================================

def scalar_add(left: Sequence[int], right: Sequence[int]) -> list[int]:
    """Scalar model: one pair of values is processed per iteration."""
    if len(left) != len(right):
        raise ValueError("vectors must have equal length")

    result = []
    for a, b in zip(left, right):
        result.append(a + b)
    return result


def conceptual_simd_add(
    left: Sequence[int],
    right: Sequence[int],
    lane_count: int = 4,
) -> list[int]:
    """
    Model SIMD at the algorithmic level.

    A real CPU may use vector instructions such as AVX2/AVX-512. This pure
    Python function groups elements into conceptual vector lanes; it does not
    itself force hardware SIMD instructions.
    """
    if len(left) != len(right):
        raise ValueError("vectors must have equal length")
    if lane_count <= 0:
        raise ValueError("lane_count must be positive")

    result: list[int] = []

    for start in range(0, len(left), lane_count):
        left_vector = left[start:start + lane_count]
        right_vector = right[start:start + lane_count]

        # Conceptually: one vector instruction handles these lanes together.
        result.extend(
            a + b for a, b in zip(left_vector, right_vector)
        )

    return result


def demonstrate_simd() -> None:
    print_section("6. SIMD: Single Instruction, Multiple Data")

    left = [10, 20, 30, 40, 50, 60]
    right = [1, 2, 3, 4, 5, 6]

    print("Scalar result:", scalar_add(left, right))
    print("SIMD model:   ", conceptual_simd_add(left, right, lane_count=4))
    print(
        "Real SIMD is normally implemented by compiler-generated vector "
        "instructions, CPU intrinsics, or vectorized numerical libraries."
    )


# ============================================================================
# 8. MIMD CONCEPT
# ============================================================================

def mimd_task(task_name: str, values: Sequence[int]) -> tuple[str, int]:
    """Different tasks can execute different algorithms concurrently."""
    if task_name == "sum":
        result = sum(values)
    elif task_name == "max":
        result = max(values) if values else 0
    elif task_name == "squares":
        result = sum(value * value for value in values)
    else:
        raise ValueError(f"Unknown task: {task_name}")

    return task_name, result


def demonstrate_mimd() -> None:
    print_section("7. MIMD: Multiple Instruction, Multiple Data")

    values = list(range(1, 101))
    jobs = [
        ("sum", values),
        ("max", values),
        ("squares", values),
    ]

    # Different workers perform different operations on the same dataset.
    with ProcessPoolExecutor(max_workers=3) as executor:
        results = list(
            executor.map(
                lambda_job,
                jobs,
            )
        )

    for name, result in results:
        print(f"{name:8s}: {result}")


def lambda_job(job: tuple[str, Sequence[int]]) -> tuple[str, int]:
    """
    Top-level wrapper is process-pool friendly.

    It delegates to mimd_task instead of using an anonymous lambda as the
    submitted process function.
    """
    return mimd_task(*job)


# ============================================================================
# 9. MAP/REDUCE PARALLEL PATTERN
# ============================================================================

def partial_sum(values: Sequence[int]) -> int:
    return sum(values)


def parallel_sum(values: Sequence[int], workers: int = 4) -> int:
    """Map partial sums to workers and reduce them into one total."""
    chunks = chunk_sequence(values, max(1, math.ceil(len(values) / workers)))

    with ProcessPoolExecutor(max_workers=workers) as executor:
        partials = list(executor.map(partial_sum, chunks))

    return reduce(lambda a, b: a + b, partials, 0)


def demonstrate_map_reduce() -> None:
    print_section("8. Map-Reduce Parallel Pattern")

    values = list(range(1, 100_001))
    result = parallel_sum(values, workers=4)

    print("Parallel sum:", result)
    print("Expected:    ", sum(values))


# ============================================================================
# 10. AMDAHL'S LAW
# ============================================================================

def amdahl_speedup(serial_fraction: float, processors: int) -> float:
    """
    Amdahl's Law:

        speedup = 1 / (S + P/N)

    S = serial fraction
    P = parallel fraction = 1 - S
    N = number of processors

    The formula models the theoretical speedup limit for a fixed workload.
    """
    if not 0 <= serial_fraction <= 1:
        raise ValueError("serial_fraction must be between 0 and 1")
    if processors <= 0:
        raise ValueError("processors must be positive")

    parallel_fraction = 1 - serial_fraction
    return 1 / (serial_fraction + parallel_fraction / processors)


def demonstrate_amdahl() -> None:
    print_section("9. Amdahl's Law")

    serial_fraction = 0.10

    for processors in (1, 2, 4, 8, 16, 32, 64):
        speedup = amdahl_speedup(serial_fraction, processors)
        print(
            f"processors={processors:2d}, "
            f"theoretical speedup={speedup:6.2f}x"
        )

    print(
        "Even infinitely many processors cannot eliminate the serial portion. "
        "With a 10% serial fraction, the theoretical upper bound is 10x."
    )


# ============================================================================
# 11. GUSTAFSON'S LAW
# ============================================================================

def gustafson_scaled_speedup(serial_fraction: float, processors: int) -> float:
    """Gustafson's scaled-speedup model."""
    if not 0 <= serial_fraction <= 1:
        raise ValueError("serial_fraction must be between 0 and 1")
    if processors <= 0:
        raise ValueError("processors must be positive")

    return processors - serial_fraction * (processors - 1)


def demonstrate_gustafson() -> None:
    print_section("10. Gustafson's Law")

    for processors in (1, 2, 4, 8, 16):
        print(
            f"processors={processors:2d}, "
            f"scaled speedup={gustafson_scaled_speedup(0.10, processors):.2f}x"
        )

    print(
        "Gustafson's perspective is useful when larger processor counts are "
        "used to solve proportionally larger problems."
    )


# ============================================================================
# 12. LOAD BALANCING
# ============================================================================

def static_partition(values: Sequence[int], workers: int) -> list[Sequence[int]]:
    return chunk_sequence(
        values,
        max(1, math.ceil(len(values) / workers)),
    )


def demonstrate_load_balancing() -> None:
    print_section("11. Load Balancing")

    workload = [1, 1, 1, 20, 1, 1, 30, 1, 1, 1, 25, 1]

    print("Uneven task costs:", workload)

    partitions = static_partition(workload, 3)

    for index, partition in enumerate(partitions):
        print(
            f"Worker {index}: tasks={list(partition)}, "
            f"estimated work={sum(partition)}"
        )

    print(
        "Static partitioning is simple, but unequal task costs can leave some "
        "workers idle while another worker remains busy."
    )


# ============================================================================
# 13. PARALLEL OVERHEAD
# ============================================================================

def benchmark_sum(values: Sequence[int], workers: int) -> None:
    sequential_start = time.perf_counter()
    sequential = sum(values)
    sequential_time = time.perf_counter() - sequential_start

    parallel_start = time.perf_counter()
    parallel = parallel_sum(values, workers)
    parallel_time = time.perf_counter() - parallel_start

    print(f"Sequential result: {sequential}")
    print(f"Parallel result:   {parallel}")
    print(f"Sequential: {sequential_time:.6f}s")
    print(f"Parallel:   {parallel_time:.6f}s")

    print(
        "For small workloads, parallel execution may be slower because "
        "creating workers, partitioning data, communicating, and combining "
        "results introduce overhead."
    )


# ============================================================================
# 14. ERROR HANDLING IN PARALLEL PROGRAMS
# ============================================================================

def risky_operation(value: int) -> float:
    if value == 0:
        raise ZeroDivisionError("division by zero")
    return 100 / value


def demonstrate_parallel_errors() -> None:
    print_section("12. Error Handling")

    values = [10, 5, 0, 2]

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(risky_operation, value): value
            for value in values
        }

        for future in as_completed(futures):
            value = futures[future]
            try:
                print(f"value={value}, result={future.result():.2f}")
            except Exception as exc:
                print(f"value={value}, error={type(exc).__name__}: {exc}")


# ============================================================================
# 15. VALIDATION AND EDGE CASES
# ============================================================================

def demonstrate_edge_cases() -> None:
    print_section("13. Edge Cases and Validation")

    test_cases = [
        ("empty input", []),
        ("single value", [7]),
        ("negative values", [-5, -2, 3]),
    ]

    for name, values in test_cases:
        print(
            f"{name:16s}: "
            f"sum_of_squares={sum_of_squares_sequential(values)}"
        )

    try:
        split_range(0, 10, 0)
    except ValueError as exc:
        print("Invalid worker count handled:", exc)

    try:
        conceptual_simd_add([1], [1, 2])
    except ValueError as exc:
        print("Mismatched vector lengths handled:", exc)


# ============================================================================
# 16. PERFORMANCE AND DESIGN PRINCIPLES
# ============================================================================

def print_design_principles() -> None:
    print_section("14. Parallel Program Design Principles")

    principles = [
        "Identify independent work before introducing parallelism.",
        "Measure a sequential baseline before optimizing.",
        "Choose task parallelism or data parallelism according to the workload.",
        "Minimize shared mutable state.",
        "Reduce synchronization and communication.",
        "Use sufficiently large tasks to amortize scheduling overhead.",
        "Balance work among workers.",
        "Consider memory bandwidth, cache locality, and false sharing.",
        "Account for process/thread startup and data-transfer costs.",
        "Use deterministic reduction operations when reproducibility matters.",
        "Test race conditions, deadlocks, failures, and partial results.",
        "Treat parallel speedup as an empirical property, not an assumption.",
    ]

    for index, principle in enumerate(principles, 1):
        print(f"{index:2d}. {principle}")


# ============================================================================
# 17. CACHE LOCALITY AND FALSE SHARING: CONCEPTUAL DEMONSTRATION
# ============================================================================

def cache_locality_example(size: int = 100_000) -> tuple[int, int]:
    """
    Demonstrate two access patterns conceptually.

    Python does not expose direct control over CPU cache lines here, so this
    function illustrates the principle rather than guaranteeing a hardware
    cache experiment.
    """
    matrix = [list(range(size)) for _ in range(2)]

    contiguous_sum = sum(matrix[0])

    strided_sum = sum(matrix[row][0] for row in range(2))

    return contiguous_sum, strided_sum


def demonstrate_memory_concepts() -> None:
    print_section("15. Memory, Cache Locality, and False Sharing")

    contiguous, strided = cache_locality_example(1_000)

    print("Contiguous-access result:", contiguous)
    print("Strided-access result:   ", strided)

    print(
        """
Cache locality:
    CPUs move data between memory and caches in cache lines. Algorithms that
    access nearby data can often exploit spatial locality.

False sharing:
    Two threads may update different variables that happen to occupy the same
    cache line. Cache-coherence traffic can then reduce performance even
    though the logical variables are independent.

Python does not provide direct cache-line placement in ordinary code, but
these considerations are important in native multicore systems programming.
"""
    )


# ============================================================================
# 18. MAIN STUDY PROGRAM
# ============================================================================

def main() -> None:
    print_section("Parallel Computing Fundamentals Study Program")

    explain_fundamentals()

    values = list(range(1, 11))
    print("Sequential sum of squares:", sum_of_squares_sequential(values))

    demonstrate_concurrency()
    demonstrate_lock()
    demonstrate_process_parallelism()
    demonstrate_data_parallelism()
    demonstrate_simd()
    demonstrate_mimd()
    demonstrate_map_reduce()
    demonstrate_amdahl()
    demonstrate_gustafson()
    demonstrate_load_balancing()

    print_section("16. Parallel Overhead Benchmark")
    benchmark_sum(list(range(1, 20_001)), workers=4)

    demonstrate_parallel_errors()
    demonstrate_edge_cases()
    demonstrate_memory_concepts()
    print_design_principles()

    print_section("17. Key Distinctions")
    print(
        """
Concurrency  -> structuring multiple activities so they can make progress.
Parallelism  -> executing multiple operations simultaneously.
Multicore    -> hardware with multiple CPU cores.
SIMD         -> one instruction, multiple data elements.
MIMD         -> multiple instruction streams, multiple data elements.
Thread       -> execution path sharing a process address space.
Process      -> independent execution context with separate memory.
Speedup      -> sequential execution time divided by parallel execution time.
Efficiency   -> speedup divided by number of processors.
Scalability  -> how performance changes as resources or workload increase.
Synchronization -> coordination that prevents unsafe or invalid interactions.
"""
    )

    print("Study program completed.")


if __name__ == "__main__":
    # ProcessPoolExecutor requires a protected entry point on platforms that
    # use process spawning, especially Windows.
    main()
