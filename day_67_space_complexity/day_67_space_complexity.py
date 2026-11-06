"""
SPACE COMPLEXITY
Auxiliary Space, Memory Analysis, and Algorithmic Trade-offs

Demonstrates:
- O(1), O(n), O(n²), and O(log n) space
- Auxiliary space versus total space
- In-place algorithms
- Recursive stack consumption
- Hash-based storage
- Dynamic programming memory optimization
- Streaming algorithms
- Memory estimation and budget validation
- Empirical memory profiling with tracemalloc
"""

from __future__ import annotations

import sys
import tracemalloc
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Any


class SpaceClass(Enum):
    CONSTANT = "O(1)"
    LOGARITHMIC = "O(log n)"
    LINEAR = "O(n)"
    QUADRATIC = "O(n^2)"


@dataclass(frozen=True)
class MemoryReport:
    algorithm: str
    input_size: int
    auxiliary_bytes: int
    complexity: SpaceClass
    description: str

    def display(self) -> None:
        print(f"\nAlgorithm: {self.algorithm}")
        print(f"Input size: {self.input_size}")
        print(f"Estimated auxiliary memory: {self.auxiliary_bytes:,} bytes")
        print(f"Space complexity: {self.complexity.value}")
        print(f"Description: {self.description}")


class MemoryBudgetExceeded(Exception):
    pass


def validate_input(values: list[int]) -> None:
    if not isinstance(values, list):
        raise TypeError("Input must be a list.")

    if not all(type(value) is int for value in values):
        raise ValueError("All elements must be integers.")


def constant_space_sum(values: list[int]) -> int:
    """Uses a fixed number of variables: O(1) auxiliary space."""
    validate_input(values)

    total = 0

    for value in values:
        total += value

    return total


def linear_space_copy(values: list[int]) -> list[int]:
    """Creates another collection proportional to input size: O(n)."""
    validate_input(values)

    result = []

    for value in values:
        result.append(value)

    return result


def in_place_reverse(values: list[int]) -> list[int]:
    """Reverses a list without allocating another proportional list."""
    validate_input(values)

    left = 0
    right = len(values) - 1

    while left < right:
        values[left], values[right] = values[right], values[left]
        left += 1
        right -= 1

    return values


def recursive_binary_search(
    values: list[int],
    target: int,
    left: int = 0,
    right: int | None = None
) -> int:
    """
    Recursive binary search.

    Auxiliary space: O(log n) because of recursive call frames.
    The input must already be sorted.
    """
    if right is None:
        right = len(values) - 1

    if left > right:
        return -1

    middle = left + (right - left) // 2

    if values[middle] == target:
        return middle

    if values[middle] > target:
        return recursive_binary_search(
            values, target, left, middle - 1
        )

    return recursive_binary_search(
        values, target, middle + 1, right
    )


def iterative_binary_search(values: list[int], target: int) -> int:
    """Uses constant auxiliary space: O(1)."""
    left = 0
    right = len(values) - 1

    while left <= right:
        middle = left + (right - left) // 2

        if values[middle] == target:
            return middle

        if values[middle] < target:
            left = middle + 1
        else:
            right = middle - 1

    return -1


def unique_values_with_set(values: list[int]) -> list[int]:
    """
    Uses a set for duplicate detection.

    Auxiliary space: O(n).
    """
    validate_input(values)

    seen = set()
    result = []

    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)

    return result


def matrix_creation(rows: int, columns: int) -> list[list[int]]:
    """Creates a matrix requiring O(rows * columns) space."""
    if rows < 0 or columns < 0:
        raise ValueError("Dimensions cannot be negative.")

    return [
        [0 for _ in range(columns)]
        for _ in range(rows)
    ]


def fibonacci_full_table(n: int) -> int:
    """Stores all computed Fibonacci values: O(n) space."""
    if n < 0:
        raise ValueError("n cannot be negative.")

    if n == 0:
        return 0

    table = [0] * (n + 1)
    table[1] = 1

    for index in range(2, n + 1):
        table[index] = table[index - 1] + table[index - 2]

    return table[n]


def fibonacci_optimized(n: int) -> int:
    """
    Uses only two previous values.

    Auxiliary space: O(1).
    """
    if n < 0:
        raise ValueError("n cannot be negative.")

    previous = 0
    current = 1

    for _ in range(n):
        previous, current = current, previous + current

    return previous


def zero_one_knapsack_full(
    weights: list[int],
    values: list[int],
    capacity: int
) -> int:
    """Full dynamic programming table: O(n * capacity) space."""
    validate_knapsack(weights, values, capacity)

    count = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(count + 1)]

    for i in range(1, count + 1):
        weight = weights[i - 1]
        value = values[i - 1]

        for current_capacity in range(capacity + 1):
            dp[i][current_capacity] = dp[i - 1][current_capacity]

            if weight <= current_capacity:
                dp[i][current_capacity] = max(
                    dp[i][current_capacity],
                    value + dp[i - 1][current_capacity - weight]
                )

    return dp[count][capacity]


def zero_one_knapsack_optimized(
    weights: list[int],
    values: list[int],
    capacity: int
) -> int:
    """
    One-dimensional dynamic programming.

    Auxiliary space: O(capacity).
    Reverse iteration prevents reusing an item.
    """
    validate_knapsack(weights, values, capacity)

    dp = [0] * (capacity + 1)

    for weight, value in zip(weights, values):
        for current_capacity in range(capacity, weight - 1, -1):
            dp[current_capacity] = max(
                dp[current_capacity],
                value + dp[current_capacity - weight]
            )

    return dp[capacity]


def validate_knapsack(
    weights: list[int],
    values: list[int],
    capacity: int
) -> None:
    if len(weights) != len(values):
        raise ValueError("Weights and values must have equal lengths.")

    if capacity < 0:
        raise ValueError("Capacity cannot be negative.")

    if any(type(weight) is not int or weight <= 0 for weight in weights):
        raise ValueError("Weights must be positive integers.")

    if any(type(value) is not int or value < 0 for value in values):
        raise ValueError("Values must be non-negative integers.")


def streaming_unique_count(values: list[int]) -> int:
    """
    Counts distinct values using a set.

    O(k) auxiliary space, where k is the number of distinct values.
    """
    seen = set()

    for value in values:
        seen.add(value)

    return len(seen)


def estimate_memory(
    element_count: int,
    bytes_per_element: int,
    additional_bytes: int = 0
) -> int:
    """Estimates a simple linear memory requirement."""
    if element_count < 0:
        raise ValueError("Element count cannot be negative.")

    if bytes_per_element < 0 or additional_bytes < 0:
        raise ValueError("Memory values cannot be negative.")

    return element_count * bytes_per_element + additional_bytes


def enforce_memory_budget(
    estimated_bytes: int,
    budget_bytes: int
) -> None:
    if estimated_bytes < 0 or budget_bytes < 0:
        raise ValueError("Memory values cannot be negative.")

    if estimated_bytes > budget_bytes:
        raise MemoryBudgetExceeded(
            f"Required: {estimated_bytes:,} bytes; "
            f"Available: {budget_bytes:,} bytes."
        )


def measure_peak_memory(
    operation: Callable[..., Any],
    *args: Any
) -> tuple[Any, int]:
    """
    Measures Python-tracked peak allocations.

    This is an empirical measurement, not a proof of asymptotic complexity.
    """
    tracemalloc.start()

    try:
        tracemalloc.reset_peak()
        result = operation(*args)
        _, peak = tracemalloc.get_traced_memory()
        return result, peak
    finally:
        tracemalloc.stop()


def build_reports(n: int) -> list[MemoryReport]:
    return [
        MemoryReport(
            "Constant-space sum",
            n,
            sys.getsizeof(0),
            SpaceClass.CONSTANT,
            "Fixed number of variables."
        ),
        MemoryReport(
            "List copy",
            n,
            sys.getsizeof([None] * n),
            SpaceClass.LINEAR,
            "Additional list containing n references."
        ),
        MemoryReport(
            "Two-dimensional matrix",
            n,
            sys.getsizeof([[0] * n for _ in range(n)]),
            SpaceClass.QUADRATIC,
            "An n by n matrix."
        ),
        MemoryReport(
            "Binary search recursion",
            n,
            max(1, n.bit_length()) * 64,
            SpaceClass.LOGARITHMIC,
            "Approximate recursive call-frame storage."
        )
    ]


def run_tests() -> None:
    assert constant_space_sum([1, 2, 3]) == 6
    assert linear_space_copy([1, 2]) == [1, 2]

    data = [1, 2, 3, 4]
    assert in_place_reverse(data) == [4, 3, 2, 1]

    sorted_data = [1, 3, 5, 7, 9]
    assert iterative_binary_search(sorted_data, 7) == 3
    assert iterative_binary_search(sorted_data, 8) == -1
    assert recursive_binary_search(sorted_data, 5) == 2

    assert unique_values_with_set([1, 2, 2, 3]) == [1, 2, 3]

    assert len(matrix_creation(3, 4)) == 3

    assert fibonacci_full_table(10) == 55
    assert fibonacci_optimized(10) == 55

    weights = [2, 3, 4, 5]
    values = [3, 4, 5, 6]

    assert zero_one_knapsack_full(weights, values, 5) == 7
    assert zero_one_knapsack_optimized(weights, values, 5) == 7

    assert streaming_unique_count([1, 2, 2, 3]) == 3

    assert estimate_memory(100, 8, 16) == 816

    try:
        enforce_memory_budget(2048, 1024)
    except MemoryBudgetExceeded:
        pass
    else:
        raise AssertionError("Memory budget validation failed.")

    try:
        fibonacci_optimized(-1)
    except ValueError:
        pass
    else:
        raise AssertionError("Negative input validation failed.")

    print("All tests passed.")


def main() -> None:
    print("=" * 65)
    print("SPACE COMPLEXITY AND MEMORY ANALYSIS")
    print("=" * 65)

    run_tests()

    n = 1000

    print("\nMEMORY COMPLEXITY REPORTS")

    for report in build_reports(n):
        report.display()

    print("\nALGORITHM COMPARISON")

    print("Fibonacci using full table:", fibonacci_full_table(30))
    print("Fibonacci using two variables:", fibonacci_optimized(30))

    print(
        "Knapsack optimized result:",
        zero_one_knapsack_optimized(
            [2, 3, 4, 5],
            [3, 4, 5, 6],
            5
        )
    )

    print("\nEMPIRICAL MEMORY PROFILING")

    input_data = list(range(10000))

    _, copy_peak = measure_peak_memory(
        linear_space_copy,
        input_data
    )

    _, sum_peak = measure_peak_memory(
        constant_space_sum,
        input_data
    )

    print(f"List-copy peak: {copy_peak:,} bytes")
    print(f"Constant-space sum peak: {sum_peak:,} bytes")

    print("\nMEMORY BUDGET VALIDATION")

    try:
        estimated = estimate_memory(100000, 8, 1024)
        enforce_memory_budget(estimated, 1024 * 1024)
        print(f"Accepted memory estimate: {estimated:,} bytes")
    except MemoryBudgetExceeded as error:
        print("Rejected:", error)

    print("\nPROCESS COMPLETE")


if __name__ == "__main__":
    main()
