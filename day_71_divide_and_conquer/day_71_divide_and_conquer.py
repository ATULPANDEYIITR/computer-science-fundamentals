#!/usr/bin/env python3
"""
Divide and Conquer
Fundamentals, recursive algorithms, recurrence relations, and performance analysis.

Algorithms:
- Binary Search
- Merge Sort
- Quick Sort
- Maximum Subarray
- Karatsuba Multiplication
- Recurrence relation analysis
- Complexity measurement and validation
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional, TypeVar

T = TypeVar("T")


class AlgorithmCategory(Enum):
    SEARCHING = "Searching"
    SORTING = "Sorting"
    OPTIMIZATION = "Optimization"
    MULTIPLICATION = "Multiplication"


@dataclass(frozen=True)
class AlgorithmResult:
    name: str
    category: AlgorithmCategory
    input_size: int
    result: object
    execution_seconds: float
    recursive_calls: int
    description: str


@dataclass(frozen=True)
class Recurrence:
    name: str
    a: int
    b: int
    exponent: float
    description: str

    def __post_init__(self):
        if self.a < 1 or self.b < 2:
            raise ValueError("a must be positive and b must be >= 2.")
        if self.exponent < 0:
            raise ValueError("Exponent cannot be negative.")

    @property
    def critical_exponent(self) -> float:
        import math
        return math.log(self.a, self.b)

    def complexity(self) -> str:
        """
        Analyze T(n) = aT(n/b) + Theta(n^d).

        Assumes regularity conditions for the third case.
        """
        import math

        critical = self.critical_exponent
        epsilon = 1e-10

        if self.exponent < critical - epsilon:
            return f"Theta(n^{critical:.3f})"

        if abs(self.exponent - critical) <= epsilon:
            return f"Theta(n^{critical:.3f} log n)"

        return f"Theta(n^{self.exponent:.3f})"


class DivideAndConquer:
    def __init__(self):
        self.calls = 0

    def binary_search(self, values: list[T], target: T) -> int:
        """Iterative binary search on sorted input."""
        if any(values[i] > values[i + 1]
               for i in range(len(values) - 1)):
            raise ValueError("Binary search requires sorted input.")

        left, right = 0, len(values) - 1

        while left <= right:
            mid = left + (right - left) // 2

            if values[mid] == target:
                return mid
            if values[mid] < target:
                left = mid + 1
            else:
                right = mid - 1

        return -1

    def merge_sort(self, values: list[T]) -> list[T]:
        """Stable recursive merge sort."""
        self.calls = 0

        def sort(items: list[T]) -> list[T]:
            self.calls += 1

            if len(items) <= 1:
                return items.copy()

            mid = len(items) // 2
            left = sort(items[:mid])
            right = sort(items[mid:])

            return merge(left, right)

        def merge(left: list[T], right: list[T]) -> list[T]:
            result = []
            i = j = 0

            while i < len(left) and j < len(right):
                if left[i] <= right[j]:
                    result.append(left[i])
                    i += 1
                else:
                    result.append(right[j])
                    j += 1

            result.extend(left[i:])
            result.extend(right[j:])
            return result

        return sort(values)

    def quick_sort(self, values: list[int]) -> list[int]:
        """
        Three-way quicksort.
        Randomized pivots reduce the likelihood of consistently
        unbalanced partitions on adversarial input.
        """
        self.calls = 0

        def sort(items: list[int]) -> list[int]:
            self.calls += 1

            if len(items) <= 1:
                return items

            pivot = random.choice(items)
            lower = [x for x in items if x < pivot]
            equal = [x for x in items if x == pivot]
            higher = [x for x in items if x > pivot]

            return sort(lower) + equal + sort(higher)

        return sort(values)

    def maximum_subarray(
        self, values: list[int]
    ) -> tuple[int, int, int]:
        """
        Return (maximum_sum, start_index, end_index).
        Uses divide and conquer in O(n log n).
        """
        if not values:
            raise ValueError("Input cannot be empty.")

        self.calls = 0

        def solve(left: int, right: int) -> tuple[int, int, int]:
            self.calls += 1

            if left == right:
                return values[left], left, right

            mid = (left + right) // 2

            left_result = solve(left, mid)
            right_result = solve(mid + 1, right)

            total = 0
            best_left = float("-inf")
            cross_start = mid

            for i in range(mid, left - 1, -1):
                total += values[i]
                if total > best_left:
                    best_left = total
                    cross_start = i

            total = 0
            best_right = float("-inf")
            cross_end = mid + 1

            for i in range(mid + 1, right + 1):
                total += values[i]
                if total > best_right:
                    best_right = total
                    cross_end = i

            cross = (
                best_left + best_right,
                cross_start,
                cross_end
            )

            return max(
                left_result,
                right_result,
                cross,
                key=lambda item: item[0]
            )

        return solve(0, len(values) - 1)

    def karatsuba(self, x: int, y: int) -> int:
        """Recursive integer multiplication using Karatsuba."""
        if x < 0 or y < 0:
            raise ValueError("Inputs must be non-negative.")

        self.calls = 0

        def multiply(a: int, b: int) -> int:
            self.calls += 1

            if a < 10 or b < 10:
                return a * b

            digits = max(len(str(a)), len(str(b)))
            half = digits // 2
            power = 10 ** half

            high_a, low_a = divmod(a, power)
            high_b, low_b = divmod(b, power)

            z0 = multiply(low_a, low_b)
            z2 = multiply(high_a, high_b)
            z1 = multiply(low_a + high_a, low_b + high_b)

            return (
                z2 * power * power
                + (z1 - z2 - z0) * power
                + z0
            )

        return multiply(x, y)


def benchmark(
    name: str,
    category: AlgorithmCategory,
    size: int,
    operation: Callable[[], object],
    calls: int,
    description: str
) -> AlgorithmResult:
    start = time.perf_counter()
    result = operation()
    elapsed = time.perf_counter() - start

    return AlgorithmResult(
        name=name,
        category=category,
        input_size=size,
        result=result,
        execution_seconds=elapsed,
        recursive_calls=calls,
        description=description
    )


def demonstrate_recurrences():
    examples = [
        Recurrence(
            "Binary Search", 1, 2, 0,
            "T(n) = T(n/2) + O(1)"
        ),
        Recurrence(
            "Merge Sort", 2, 2, 1,
            "T(n) = 2T(n/2) + O(n)"
        ),
        Recurrence(
            "Karatsuba", 3, 2, 1,
            "T(n) = 3T(n/2) + O(n)"
        ),
        Recurrence(
            "Strassen-like recurrence", 7, 2, 2,
            "T(n) = 7T(n/2) + O(n^2)"
        ),
        Recurrence(
            "Quadratic combine", 2, 2, 2,
            "T(n) = 2T(n/2) + O(n^2)"
        )
    ]

    print("\nRECURRENCE ANALYSIS")
    print("-" * 75)

    for item in examples:
        print(f"{item.name:25} {item.description:35} "
              f"{item.complexity()}")


def run_demonstration():
    engine = DivideAndConquer()

    print("=" * 75)
    print("DIVIDE AND CONQUER ALGORITHM LAB")
    print("=" * 75)

    original = [38, 27, 43, 3, 9, 82, 10, 27]

    sorted_values = engine.merge_sort(original)

    print("\n1. MERGE SORT")
    print("Input:", original)
    print("Output:", sorted_values)
    print("Recursive calls:", engine.calls)

    assert sorted_values == sorted(original)

    print("\n2. BINARY SEARCH")
    position = engine.binary_search(sorted_values, 27)
    print("Target: 27")
    print("Position:", position)
    assert position != -1
    assert sorted_values[position] == 27

    print("\n3. QUICK SORT")
    random_values = [random.randint(-100, 100) for _ in range(20)]
    quick_sorted = engine.quick_sort(random_values)
    print("Input:", random_values)
    print("Output:", quick_sorted)
    print("Recursive calls:", engine.calls)
    assert quick_sorted == sorted(random_values)

    print("\n4. MAXIMUM SUBARRAY")
    sequence = [-2, 1, -3, 4, -1, 2, 1, -5, 4]
    maximum = engine.maximum_subarray(sequence)
    print("Input:", sequence)
    print("Maximum sum and indices:", maximum)
    print("Subarray:", sequence[maximum[1]:maximum[2] + 1])
    assert maximum[0] == 6

    print("\n5. KARATSUBA MULTIPLICATION")
    x = 123456789012345
    y = 987654321098765
    product = engine.karatsuba(x, y)
    print("First operand:", x)
    print("Second operand:", y)
    print("Product:", product)
    print("Recursive calls:", engine.calls)
    assert product == x * y

    demonstrate_recurrences()

    print("\n6. EDGE CASE VALIDATION")
    assert engine.merge_sort([]) == []
    assert engine.merge_sort([5]) == [5]
    assert engine.merge_sort([4, 4, 4]) == [4, 4, 4]
    assert engine.binary_search([], 10) == -1
    assert engine.maximum_subarray([-5, -2, -8])[0] == -2

    try:
        engine.binary_search([3, 1, 2], 1)
    except ValueError as error:
        print("Expected validation error:", error)

    try:
        engine.maximum_subarray([])
    except ValueError as error:
        print("Expected validation error:", error)

    try:
        engine.karatsuba(-10, 20)
    except ValueError as error:
        print("Expected validation error:", error)

    print("\nAll algorithm assertions passed.")


if __name__ == "__main__":
    run_demonstration()
