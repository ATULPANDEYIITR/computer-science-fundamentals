#!/usr/bin/env python3
"""
Time Complexity: Big-O, Big-Omega, Big-Theta and Asymptotic Analysis.

Executable demonstrations:
- Formal asymptotic bounds.
- Growth-rate comparison.
- Operation counting.
- Linear search and binary search.
- Nested loops and logarithmic algorithms.
- Sorting algorithms.
- Empirical benchmarking.
- Complexity classification and validation.
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional


class ComplexityClass(Enum):
    CONSTANT = "O(1)"
    LOGARITHMIC = "O(log n)"
    LINEAR = "O(n)"
    LINEARITHMIC = "O(n log n)"
    QUADRATIC = "O(n^2)"
    CUBIC = "O(n^3)"
    EXPONENTIAL = "O(2^n)"


@dataclass(frozen=True)
class ComplexityBounds:
    """Represent upper, lower and tight asymptotic bounds."""

    upper: str
    lower: str
    tight: str
    explanation: str


@dataclass
class BenchmarkResult:
    algorithm: str
    input_size: int
    operations: int
    elapsed_seconds: float
    estimated_class: str


class ComplexityError(ValueError):
    pass


def validate_size(n: int, maximum: int = 100_000) -> None:
    if isinstance(n, bool) or not isinstance(n, int):
        raise ComplexityError("Input size must be an integer.")
    if n < 0 or n > maximum:
        raise ComplexityError(f"Input size must be between 0 and {maximum}.")


def constant_algorithm(n: int) -> int:
    validate_size(n)
    return 1


def linear_algorithm(n: int) -> int:
    validate_size(n)
    operations = 0

    for _ in range(n):
        operations += 1

    return operations


def logarithmic_algorithm(n: int) -> int:
    validate_size(n)
    operations = 0
    value = 1

    while value < n:
        value *= 2
        operations += 1

    return operations


def quadratic_algorithm(n: int) -> int:
    validate_size(n)
    operations = 0

    for i in range(n):
        for j in range(n):
            operations += 1

    return operations


def triangular_algorithm(n: int) -> int:
    validate_size(n)
    operations = 0

    for i in range(n):
        for _ in range(i + 1):
            operations += 1

    return operations


def linearithmic_algorithm(n: int) -> int:
    validate_size(n)
    if n <= 1:
        return n

    operations = 0
    width = 1

    while width < n:
        operations += n
        width *= 2

    return operations


def exponential_algorithm(n: int) -> int:
    validate_size(n, maximum=25)

    def fibonacci_calls(k: int) -> int:
        if k <= 1:
            return 1
        return 1 + fibonacci_calls(k - 1) + fibonacci_calls(k - 2)

    return fibonacci_calls(n)


def linear_search(values: list[int], target: int) -> tuple[Optional[int], int]:
    operations = 0

    for index, value in enumerate(values):
        operations += 1

        if value == target:
            return index, operations

    return None, operations


def binary_search(values: list[int], target: int) -> tuple[Optional[int], int]:
    """Requires sorted input. Runs in O(log n)."""

    if any(values[i] > values[i + 1] for i in range(len(values) - 1)):
        raise ComplexityError("Binary search requires sorted input.")

    left = 0
    right = len(values) - 1
    operations = 0

    while left <= right:
        middle = left + (right - left) // 2
        operations += 1

        if values[middle] == target:
            return middle, operations

        if values[middle] < target:
            left = middle + 1
        else:
            right = middle - 1

    return None, operations


def merge_sort(values: list[int]) -> tuple[list[int], int]:
    """Merge sort with comparison counting."""

    comparisons = 0

    def sort(items: list[int]) -> list[int]:
        nonlocal comparisons

        if len(items) <= 1:
            return items

        middle = len(items) // 2
        left = sort(items[:middle])
        right = sort(items[middle:])

        merged = []
        i = j = 0

        while i < len(left) and j < len(right):
            comparisons += 1

            if left[i] <= right[j]:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1

        merged.extend(left[i:])
        merged.extend(right[j:])

        return merged

    return sort(values), comparisons


def bubble_sort(values: list[int]) -> tuple[list[int], int]:
    """Bubble sort with early termination."""

    result = values.copy()
    comparisons = 0

    for i in range(len(result)):
        swapped = False

        for j in range(len(result) - i - 1):
            comparisons += 1

            if result[j] > result[j + 1]:
                result[j], result[j + 1] = result[j + 1], result[j]
                swapped = True

        if not swapped:
            break

    return result, comparisons


def get_complexity_catalog() -> dict[str, ComplexityBounds]:
    return {
        "Constant": ComplexityBounds(
            "O(1)", "Ω(1)", "Θ(1)",
            "A fixed number of operations."
        ),
        "Logarithmic": ComplexityBounds(
            "O(log n)", "Ω(log n)", "Θ(log n)",
            "Problem size is repeatedly reduced by a constant factor."
        ),
        "Linear": ComplexityBounds(
            "O(n)", "Ω(n)", "Θ(n)",
            "Operations grow proportionally to input size."
        ),
        "Linearithmic": ComplexityBounds(
            "O(n log n)", "Ω(n log n)", "Θ(n log n)",
            "Common in efficient comparison-based sorting."
        ),
        "Quadratic": ComplexityBounds(
            "O(n^2)", "Ω(n^2)", "Θ(n^2)",
            "Typical of two complete nested loops."
        ),
        "Cubic": ComplexityBounds(
            "O(n^3)", "Ω(n^3)", "Θ(n^3)",
            "Typical of three complete nested loops."
        ),
        "Exponential": ComplexityBounds(
            "O(2^n)", "Ω(2^n)", "Θ(2^n)",
            "Work doubles with each additional input element."
        ),
    }


def growth_values(n: int) -> dict[str, float]:
    validate_size(n)

    if n == 0:
        return {
            "1": 1,
            "log2(n)": 0,
            "n": 0,
            "n log2(n)": 0,
            "n^2": 0,
            "n^3": 0,
        }

    return {
        "1": 1,
        "log2(n)": math.log2(n),
        "n": n,
        "n log2(n)": n * math.log2(n),
        "n^2": n ** 2,
        "n^3": n ** 3,
    }


def benchmark(
    name: str,
    algorithm: Callable[[int], int],
    sizes: list[int],
    complexity: str,
) -> list[BenchmarkResult]:
    results = []

    for size in sizes:
        start = time.perf_counter()
        operations = algorithm(size)
        elapsed = time.perf_counter() - start

        results.append(
            BenchmarkResult(
                algorithm=name,
                input_size=size,
                operations=operations,
                elapsed_seconds=elapsed,
                estimated_class=complexity,
            )
        )

    return results


def demonstrate_searching() -> None:
    values = list(range(0, 200, 2))

    print("\nSEARCH ALGORITHMS")
    print("-" * 65)

    index, operations = linear_search(values, 120)
    print(f"Linear search: index={index}, comparisons={operations}")

    index, operations = binary_search(values, 120)
    print(f"Binary search: index={index}, comparisons={operations}")

    index, operations = linear_search(values, -1)
    print(f"Linear search, absent target: index={index}, comparisons={operations}")


def demonstrate_sorting() -> None:
    random.seed(42)
    values = random.sample(range(1000), 30)

    print("\nSORTING ALGORITHMS")
    print("-" * 65)

    bubble_result, bubble_operations = bubble_sort(values)
    merge_result, merge_operations = merge_sort(values)

    assert bubble_result == sorted(values)
    assert merge_result == sorted(values)

    print(f"Bubble sort comparisons: {bubble_operations}")
    print(f"Merge sort comparisons: {merge_operations}")
    print(f"Sorted output: {merge_result}")


def demonstrate_asymptotic_analysis() -> None:
    catalog = get_complexity_catalog()

    print("\nASYMPTOTIC COMPLEXITY CATALOG")
    print("-" * 85)

    for name, bounds in catalog.items():
        print(
            f"{name:15} "
            f"Big-O={bounds.upper:12} "
            f"Big-Omega={bounds.lower:12} "
            f"Big-Theta={bounds.tight}"
        )

    print("\nGROWTH COMPARISON")
    print("-" * 65)

    for size in (10, 100, 1000):
        values = growth_values(size)
        print(f"\nn = {size}")

        for function, result in values.items():
            print(f"{function:15}: {result:,.2f}")


def demonstrate_benchmarking() -> None:
    print("\nOPERATION-COUNT BENCHMARK")
    print("-" * 85)

    workloads = [
        ("Constant", constant_algorithm, "O(1)"),
        ("Logarithmic", logarithmic_algorithm, "O(log n)"),
        ("Linear", linear_algorithm, "O(n)"),
        ("Linearithmic", linearithmic_algorithm, "O(n log n)"),
        ("Quadratic", quadratic_algorithm, "O(n^2)"),
    ]

    sizes = [10, 100, 500]

    for name, algorithm, complexity in workloads:
        results = benchmark(name, algorithm, sizes, complexity)

        for result in results:
            print(
                f"{result.algorithm:15} "
                f"n={result.input_size:5} "
                f"operations={result.operations:12} "
                f"time={result.elapsed_seconds:.8f}s "
                f"class={result.estimated_class}"
            )


def demonstrate_edge_cases() -> None:
    print("\nEDGE CASE VALIDATION")
    print("-" * 65)

    assert linear_search([], 10) == (None, 0)
    assert binary_search([], 10) == (None, 0)
    assert linear_algorithm(0) == 0
    assert logarithmic_algorithm(1) == 0
    assert quadratic_algorithm(0) == 0
    assert merge_sort([]) == ([], 0)
    assert bubble_sort([5, 5, 5]) == ([5, 5, 5], 2)

    try:
        binary_search([5, 2, 9], 5)
    except ComplexityError as error:
        print(f"Expected validation error: {error}")

    try:
        linear_algorithm(-1)
    except ComplexityError as error:
        print(f"Expected validation error: {error}")

    print("All edge-case assertions passed.")


def main() -> None:
    print("=" * 85)
    print("TIME COMPLEXITY AND ASYMPTOTIC ANALYSIS")
    print("=" * 85)

    demonstrate_asymptotic_analysis()
    demonstrate_searching()
    demonstrate_sorting()
    demonstrate_benchmarking()
    demonstrate_edge_cases()

    print("\nEXECUTION COMPLETED")


if __name__ == "__main__":
    main()
