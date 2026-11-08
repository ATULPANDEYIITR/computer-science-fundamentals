#!/usr/bin/env python3
"""
Sorting Algorithms I
Bubble Sort, Selection Sort, and Insertion Sort.

Demonstrates:
- In-place sorting
- Stable and unstable sorting
- Ascending and descending order
- Comparison and swap statistics
- Early termination
- Custom keys
- Input validation
- Performance measurement
- Unit-style assertions
- CSV export
"""

from __future__ import annotations

import csv
import random
import time
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Callable, Iterable, TypeVar, Any

T = TypeVar("T")


class Algorithm(Enum):
    BUBBLE = "bubble"
    SELECTION = "selection"
    INSERTION = "insertion"


@dataclass
class SortMetrics:
    algorithm: str
    comparisons: int = 0
    swaps: int = 0
    shifts: int = 0
    passes: int = 0
    duration_ms: float = 0.0

    def display(self) -> None:
        print(
            f"{self.algorithm:12} "
            f"comparisons={self.comparisons:6} "
            f"swaps={self.swaps:6} "
            f"shifts={self.shifts:6} "
            f"passes={self.passes:5} "
            f"time={self.duration_ms:.4f} ms"
        )


@dataclass
class SortResult:
    values: list[Any]
    metrics: SortMetrics


class SortingError(ValueError):
    """Raised when sorting input is invalid."""


class SortingEngine:
    """Provides three elementary comparison-based sorting algorithms."""

    @staticmethod
    def validate(data: Iterable[T]) -> list[T]:
        if isinstance(data, (str, bytes)):
            raise SortingError("Input must be an iterable of sortable elements.")

        try:
            values = list(data)
        except TypeError as exc:
            raise SortingError("Input must be iterable.") from exc

        return values

    @staticmethod
    def bubble_sort(
        data: Iterable[T],
        reverse: bool = False,
        key: Callable[[T], Any] | None = None,
    ) -> SortResult:
        values = SortingEngine.validate(data)
        key_fn = key or (lambda item: item)

        metrics = SortMetrics(Algorithm.BUBBLE.value)
        start = time.perf_counter()

        n = len(values)

        for i in range(n - 1):
            swapped = False
            metrics.passes += 1

            for j in range(n - i - 1):
                metrics.comparisons += 1

                left = key_fn(values[j])
                right = key_fn(values[j + 1])

                should_swap = (
                    left < right if reverse else left > right
                )

                if should_swap:
                    values[j], values[j + 1] = (
                        values[j + 1],
                        values[j],
                    )
                    metrics.swaps += 1
                    swapped = True

            # No swaps means the list is already sorted.
            if not swapped:
                break

        metrics.duration_ms = (
            time.perf_counter() - start
        ) * 1000

        return SortResult(values, metrics)

    @staticmethod
    def selection_sort(
        data: Iterable[T],
        reverse: bool = False,
        key: Callable[[T], Any] | None = None,
    ) -> SortResult:
        values = SortingEngine.validate(data)
        key_fn = key or (lambda item: item)

        metrics = SortMetrics(Algorithm.SELECTION.value)
        start = time.perf_counter()

        n = len(values)

        for i in range(n - 1):
            metrics.passes += 1
            selected = i

            for j in range(i + 1, n):
                metrics.comparisons += 1

                candidate = key_fn(values[j])
                current = key_fn(values[selected])

                if (
                    candidate > current
                    if reverse
                    else candidate < current
                ):
                    selected = j

            if selected != i:
                values[i], values[selected] = (
                    values[selected],
                    values[i],
                )
                metrics.swaps += 1

        metrics.duration_ms = (
            time.perf_counter() - start
        ) * 1000

        return SortResult(values, metrics)

    @staticmethod
    def insertion_sort(
        data: Iterable[T],
        reverse: bool = False,
        key: Callable[[T], Any] | None = None,
    ) -> SortResult:
        values = SortingEngine.validate(data)
        key_fn = key or (lambda item: item)

        metrics = SortMetrics(Algorithm.INSERTION.value)
        start = time.perf_counter()

        for i in range(1, len(values)):
            metrics.passes += 1

            current = values[i]
            current_key = key_fn(current)
            j = i - 1

            while j >= 0:
                metrics.comparisons += 1
                previous_key = key_fn(values[j])

                should_shift = (
                    previous_key < current_key
                    if reverse
                    else previous_key > current_key
                )

                if not should_shift:
                    break

                values[j + 1] = values[j]
                metrics.shifts += 1
                j -= 1

            values[j + 1] = current

        metrics.duration_ms = (
            time.perf_counter() - start
        ) * 1000

        return SortResult(values, metrics)

    @classmethod
    def sort(
        cls,
        data: Iterable[T],
        algorithm: Algorithm,
        reverse: bool = False,
        key: Callable[[T], Any] | None = None,
    ) -> SortResult:
        algorithms = {
            Algorithm.BUBBLE: cls.bubble_sort,
            Algorithm.SELECTION: cls.selection_sort,
            Algorithm.INSERTION: cls.insertion_sort,
        }

        if not isinstance(algorithm, Algorithm):
            raise SortingError("Unsupported sorting algorithm.")

        return algorithms[algorithm](
            data,
            reverse=reverse,
            key=key,
        )


@dataclass
class Product:
    product_id: str
    product_name: str
    stock_quantity: int
    unit_price: float


def demonstrate_basic_sorting() -> None:
    print("\n=== BASIC SORTING EXAMPLES ===")

    data = [64, 34, 25, 12, 22, 11, 90]

    print("Original:", data)

    for algorithm in Algorithm:
        result = SortingEngine.sort(data, algorithm)
        print(f"\n{algorithm.value.title()} Sort:")
        print("Sorted:", result.values)
        result.metrics.display()


def demonstrate_ordering() -> None:
    print("\n=== ASCENDING AND DESCENDING ===")

    values = [8, 3, 7, 1, 9, 2]

    ascending = SortingEngine.insertion_sort(values)
    descending = SortingEngine.insertion_sort(
        values,
        reverse=True,
    )

    print("Original:", values)
    print("Ascending:", ascending.values)
    print("Descending:", descending.values)


def demonstrate_custom_objects() -> None:
    print("\n=== INVENTORY SORTING ===")

    products = [
        Product("P101", "Keyboard", 45, 1200.00),
        Product("P102", "Monitor", 12, 9500.00),
        Product("P103", "Mouse", 80, 650.00),
        Product("P104", "Laptop", 8, 55000.00),
        Product("P105", "Headphones", 25, 1800.00),
    ]

    result = SortingEngine.insertion_sort(
        products,
        key=lambda product: product.stock_quantity,
    )

    print("Products ordered by stock quantity:")

    for product in result.values:
        print(
            f"{product.product_id} | "
            f"{product.product_name:12} | "
            f"Stock: {product.stock_quantity:3} | "
            f"Price: {product.unit_price:.2f}"
        )

    result.metrics.display()


def demonstrate_stability() -> None:
    print("\n=== STABILITY TEST ===")

    records = [
        ("Alice", 85),
        ("Bob", 70),
        ("Charlie", 85),
        ("David", 70),
        ("Eve", 85),
    ]

    print("Original:", records)

    for algorithm in (
        Algorithm.BUBBLE,
        Algorithm.SELECTION,
        Algorithm.INSERTION,
    ):
        result = SortingEngine.sort(
            records,
            algorithm,
            key=lambda item: item[1],
        )
        print(f"{algorithm.value}: {result.values}")

    print("Bubble and insertion sort preserve equal-key order.")
    print("Standard selection sort is not stable.")


def benchmark() -> list[dict[str, Any]]:
    print("\n=== PERFORMANCE BENCHMARK ===")

    random.seed(42)

    sizes = [20, 100, 300]
    results: list[dict[str, Any]] = []

    for size in sizes:
        original = [
            random.randint(1, 10000)
            for _ in range(size)
        ]

        print(f"\nDataset size: {size}")

        for algorithm in Algorithm:
            result = SortingEngine.sort(
                original,
                algorithm,
            )

            assert result.values == sorted(original)

            result.metrics.display()

            results.append({
                "size": size,
                **asdict(result.metrics),
            })

    return results


def export_benchmark(
    results: list[dict[str, Any]],
    filename: str = "sorting_benchmark.csv",
) -> None:
    if not results:
        raise SortingError("No benchmark records to export.")

    path = Path(filename)

    try:
        with path.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=list(results[0].keys()),
            )
            writer.writeheader()
            writer.writerows(results)

        print(f"\nBenchmark exported to: {path.resolve()}")

    except OSError as exc:
        print(f"CSV export failed: {exc}")


def run_tests() -> None:
    print("\n=== VALIDATION TESTS ===")

    test_cases = [
        [],
        [1],
        [5, 4, 3, 2, 1],
        [1, 2, 3, 4, 5],
        [3, 3, 3, 3],
        [-5, 0, 10, -20, 7],
        [2.5, 1.1, 3.7, 0.5],
    ]

    for case in test_cases:
        expected = sorted(case)

        for algorithm in Algorithm:
            result = SortingEngine.sort(case, algorithm)
            assert result.values == expected

    descending = SortingEngine.selection_sort(
        [1, 5, 3, 2],
        reverse=True,
    )

    assert descending.values == [5, 3, 2, 1]

    assert SortingEngine.insertion_sort([]).values == []

    try:
        SortingEngine.sort([3, 2, 1], "bubble")
    except SortingError:
        pass
    else:
        raise AssertionError("Invalid algorithm was accepted.")

    try:
        SortingEngine.bubble_sort(123)
    except SortingError:
        pass
    else:
        raise AssertionError("Non-iterable input was accepted.")

    print("All validation tests passed.")


def main() -> None:
    print("=" * 60)
    print("SORTING ALGORITHMS I")
    print("=" * 60)

    demonstrate_basic_sorting()
    demonstrate_ordering()
    demonstrate_custom_objects()
    demonstrate_stability()

    results = benchmark()
    export_benchmark(results)

    run_tests()

    print("\n=== COMPLEXITY REFERENCE ===")
    print("Bubble Sort:    O(n²), best O(n), stable")
    print("Selection Sort: O(n²), best O(n²), unstable")
    print("Insertion Sort: O(n²), best O(n), stable")
    print("Auxiliary space: O(1) for all three algorithms")


if __name__ == "__main__":
    main()
