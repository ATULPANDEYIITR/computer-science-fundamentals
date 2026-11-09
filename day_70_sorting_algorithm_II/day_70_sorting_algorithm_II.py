#!/usr/bin/env python3
"""
Sorting Algorithms II
Merge Sort, Quick Sort, and Heap Sort

Features:
- Three complete sorting implementations
- Ascending and descending order
- Stable and unstable sorting behavior
- Custom key functions
- Comparison and operation metrics
- Duplicate and edge-case handling
- Benchmarking on different input distributions
- Correctness validation and automated tests
- CSV benchmark export
"""

from __future__ import annotations

import csv
import random
import statistics
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Iterable, TypeVar, Any

T = TypeVar("T")
K = TypeVar("K")


class Algorithm(Enum):
    MERGE = "merge_sort"
    QUICK = "quick_sort"
    HEAP = "heap_sort"


@dataclass
class SortMetrics:
    algorithm: str
    comparisons: int = 0
    swaps: int = 0
    writes: int = 0
    partitions: int = 0
    recursion_depth: int = 0
    elapsed_ms: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "comparisons": self.comparisons,
            "swaps": self.swaps,
            "writes": self.writes,
            "partitions": self.partitions,
            "recursion_depth": self.recursion_depth,
            "elapsed_ms": round(self.elapsed_ms, 4),
        }


def validate_input(values: Iterable[T]) -> list[T]:
    """Create a defensive copy without modifying the caller's collection."""
    if values is None:
        raise ValueError("Input cannot be None")

    try:
        result = list(values)
    except TypeError as exc:
        raise ValueError("Input must be iterable") from exc

    return result


def compare(
    left: T,
    right: T,
    reverse: bool,
    metrics: SortMetrics,
    key: Callable[[T], Any],
) -> int:
    metrics.comparisons += 1

    a = key(left)
    b = key(right)

    if a == b:
        return 0

    result = -1 if a < b else 1
    return -result if reverse else result


def merge_sort(
    values: Iterable[T],
    *,
    reverse: bool = False,
    key: Callable[[T], Any] | None = None,
) -> tuple[list[T], SortMetrics]:
    """
    Stable merge sort.

    Time: O(n log n)
    Auxiliary space: O(n)
    """
    data = validate_input(values)
    key_fn = key or (lambda item: item)
    metrics = SortMetrics(Algorithm.MERGE.value)

    if len(data) < 2:
        return data, metrics

    buffer = [None] * len(data)

    def sort(left: int, right: int, depth: int) -> None:
        metrics.recursion_depth = max(metrics.recursion_depth, depth)

        if right - left <= 1:
            return

        middle = (left + right) // 2

        sort(left, middle, depth + 1)
        sort(middle, right, depth + 1)

        i = left
        j = middle
        position = left

        while i < middle and j < right:
            # Selecting the left item on equality preserves stability.
            if compare(data[i], data[j], reverse, metrics, key_fn) <= 0:
                buffer[position] = data[i]
                i += 1
            else:
                buffer[position] = data[j]
                j += 1

            position += 1
            metrics.writes += 1

        while i < middle:
            buffer[position] = data[i]
            i += 1
            position += 1
            metrics.writes += 1

        while j < right:
            buffer[position] = data[j]
            j += 1
            position += 1
            metrics.writes += 1

        for position in range(left, right):
            data[position] = buffer[position]
            metrics.writes += 1

    started = time.perf_counter()
    sort(0, len(data), 1)
    metrics.elapsed_ms = (time.perf_counter() - started) * 1000

    return data, metrics


def quick_sort(
    values: Iterable[T],
    *,
    reverse: bool = False,
    key: Callable[[T], Any] | None = None,
) -> tuple[list[T], SortMetrics]:
    """
    Iterative three-way quicksort using median-of-three pivot selection.

    Average time: O(n log n)
    Worst-case time: O(n^2)
    Auxiliary space: O(log n) average stack usage.

    Three-way partitioning handles duplicate-heavy inputs efficiently.
    """
    data = validate_input(values)
    key_fn = key or (lambda item: item)
    metrics = SortMetrics(Algorithm.QUICK.value)

    def ordering(a: T, b: T) -> int:
        return compare(a, b, reverse, metrics, key_fn)

    def swap(i: int, j: int) -> None:
        if i != j:
            data[i], data[j] = data[j], data[i]
            metrics.swaps += 1
            metrics.writes += 2

    def median_value(a: T, b: T, c: T) -> T:
        if ordering(a, b) > 0:
            a, b = b, a
        if ordering(b, c) > 0:
            b, c = c, b
        if ordering(a, b) > 0:
            a, b = b, a
        return b

    started = time.perf_counter()

    if len(data) > 1:
        stack = [(0, len(data) - 1, 1)]

        while stack:
            low, high, depth = stack.pop()
            metrics.recursion_depth = max(
                metrics.recursion_depth, depth
            )

            while low < high:
                pivot = median_value(
                    data[low],
                    data[(low + high) // 2],
                    data[high],
                )

                lt = low
                current = low
                gt = high

                metrics.partitions += 1

                while current <= gt:
                    result = ordering(data[current], pivot)

                    if result < 0:
                        swap(lt, current)
                        lt += 1
                        current += 1
                    elif result > 0:
                        swap(current, gt)
                        gt -= 1
                    else:
                        current += 1

                # Process the smaller partition immediately.
                # This limits explicit stack growth.
                left_size = lt - low
                right_size = high - gt

                if left_size < right_size:
                    if gt + 1 < high:
                        stack.append((gt + 1, high, depth + 1))
                    high = lt - 1
                else:
                    if low < lt - 1:
                        stack.append((low, lt - 1, depth + 1))
                    low = gt + 1

    metrics.elapsed_ms = (time.perf_counter() - started) * 1000
    return data, metrics


def heap_sort(
    values: Iterable[T],
    *,
    reverse: bool = False,
    key: Callable[[T], Any] | None = None,
) -> tuple[list[T], SortMetrics]:
    """
    In-place heap sort on a defensive copy.

    Time: O(n log n)
    Auxiliary space: O(1), excluding the input copy.
    Stability: Not guaranteed.
    """
    data = validate_input(values)
    key_fn = key or (lambda item: item)
    metrics = SortMetrics(Algorithm.HEAP.value)
    size = len(data)

    def ordering(a: T, b: T) -> int:
        return compare(a, b, reverse, metrics, key_fn)

    def swap(i: int, j: int) -> None:
        if i != j:
            data[i], data[j] = data[j], data[i]
            metrics.swaps += 1
            metrics.writes += 2

    def sift_down(root: int, end: int) -> None:
        while True:
            child = 2 * root + 1

            if child >= end:
                return

            # Select the larger child for a max heap.
            if child + 1 < end:
                if ordering(data[child], data[child + 1]) < 0:
                    child += 1

            if ordering(data[root], data[child]) >= 0:
                return

            swap(root, child)
            root = child

    started = time.perf_counter()

    # Bottom-up heap construction takes O(n) time.
    for root in range(size // 2 - 1, -1, -1):
        sift_down(root, size)

    # Repeatedly move the heap maximum to its final position.
    for end in range(size - 1, 0, -1):
        swap(0, end)
        sift_down(0, end)

    if reverse:
        data.reverse()
        metrics.writes += size

    metrics.elapsed_ms = (time.perf_counter() - started) * 1000
    return data, metrics


SORTERS = {
    Algorithm.MERGE: merge_sort,
    Algorithm.QUICK: quick_sort,
    Algorithm.HEAP: heap_sort,
}


def sort_data(
    values: Iterable[T],
    algorithm: Algorithm,
    *,
    reverse: bool = False,
    key: Callable[[T], Any] | None = None,
) -> tuple[list[T], SortMetrics]:
    if not isinstance(algorithm, Algorithm):
        raise ValueError("Unsupported sorting algorithm")

    return SORTERS[algorithm](
        values,
        reverse=reverse,
        key=key,
    )


def verify_sort(
    original: list[T],
    result: list[T],
    *,
    reverse: bool = False,
    key: Callable[[T], Any] | None = None,
) -> None:
    """Verify ordering and preservation of all input elements."""
    key_fn = key or (lambda item: item)

    if len(original) != len(result):
        raise AssertionError("Element count changed")

    if sorted(original, key=key_fn) != sorted(result, key=key_fn):
        raise AssertionError("Elements were lost or modified")

    keys = [key_fn(item) for item in result]

    if reverse:
        if any(keys[i] < keys[i + 1] for i in range(len(keys) - 1)):
            raise AssertionError("Descending order validation failed")
    else:
        if any(keys[i] > keys[i + 1] for i in range(len(keys) - 1)):
            raise AssertionError("Ascending order validation failed")


def benchmark(
    size: int = 5000,
    seed: int = 42,
) -> list[dict[str, Any]]:
    if size < 0:
        raise ValueError("Size cannot be negative")

    rng = random.Random(seed)

    datasets = {
        "random": [rng.randint(-10000, 10000) for _ in range(size)],
        "sorted": list(range(size)),
        "reverse_sorted": list(range(size, 0, -1)),
        "duplicates": [rng.randint(0, 9) for _ in range(size)],
        "nearly_sorted": list(range(size)),
        "all_equal": [7] * size,
    }

    for index in range(0, size, max(1, size // 100)):
        if datasets["nearly_sorted"]:
            other = min(index + 1, size - 1)
            datasets["nearly_sorted"][index], \
                datasets["nearly_sorted"][other] = \
                datasets["nearly_sorted"][other], \
                datasets["nearly_sorted"][index]

    results = []

    for dataset_name, dataset in datasets.items():
        for algorithm in Algorithm:
            sorted_data, metrics = sort_data(dataset, algorithm)
            verify_sort(dataset, sorted_data)

            record = metrics.as_dict()
            record["dataset"] = dataset_name
            record["input_size"] = size
            results.append(record)

    return results


def export_benchmark(
    records: list[dict[str, Any]],
    filename: str = "sorting_benchmark.csv",
) -> None:
    if not records:
        raise ValueError("Cannot export an empty benchmark")

    path = Path(filename)

    if path.suffix.lower() != ".csv":
        raise ValueError("Benchmark output must use CSV format")

    fields = list(records[0].keys())

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def run_tests() -> None:
    test_cases = [
        [],
        [1],
        [2, 1],
        [5, 3, 8, 1, 2],
        [4, 4, 4, 4],
        [-5, -10, 0, 10],
        list(range(100, 0, -1)),
        [random.Random(10).randint(-100, 100) for _ in range(100)],
    ]

    for values in test_cases:
        expected = sorted(values)

        for algorithm in Algorithm:
            result, metrics = sort_data(values, algorithm)
            assert result == expected
            verify_sort(values, result)
            assert metrics.comparisons >= 0

            descending, _ = sort_data(
                values, algorithm, reverse=True
            )
            assert descending == sorted(values, reverse=True)

    # Verify stable ordering using records with equal keys.
    records = [
        {"name": "A", "score": 80},
        {"name": "B", "score": 70},
        {"name": "C", "score": 80},
        {"name": "D", "score": 70},
    ]

    stable_result, _ = merge_sort(
        records, key=lambda record: record["score"]
    )

    assert [r["name"] for r in stable_result] == [
        "B", "D", "A", "C"
    ]

    # Verify invalid input handling.
    try:
        merge_sort(None)
        raise AssertionError("None input should be rejected")
    except ValueError:
        pass

    print("All sorting tests passed.")


def main() -> None:
    run_tests()

    sample = [38, 27, 43, 3, 9, 82, 10, 3]

    print("\nSample sorting results")
    print("Original:", sample)

    for algorithm in Algorithm:
        result, metrics = sort_data(sample, algorithm)
        print(f"\n{algorithm.value}")
        print("Sorted:", result)
        print("Metrics:", metrics.as_dict())

    print("\nBenchmark execution")

    records = benchmark(size=5000)
    export_benchmark(records)

    for algorithm in Algorithm:
        times = [
            record["elapsed_ms"]
            for record in records
            if record["algorithm"] == algorithm.value
        ]

        print(
            f"{algorithm.value}: "
            f"mean={statistics.mean(times):.4f} ms"
        )

    print("\nBenchmark exported to sorting_benchmark.csv")


if __name__ == "__main__":
    main()
