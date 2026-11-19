#!/usr/bin/env python3
"""
Advanced Algorithm Analysis
Topics:
1. Amortized Analysis
2. Randomized Algorithms
3. Probabilistic Analysis

Python 3.10+
Standard library only.
"""

from __future__ import annotations

import math
import random
import statistics
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Generic, TypeVar


T = TypeVar("T")


class AnalysisError(Exception):
    """Raised when an algorithm experiment receives invalid input."""


class AnalysisMethod(Enum):
    AGGREGATE = "Aggregate Analysis"
    ACCOUNTING = "Accounting Method"
    POTENTIAL = "Potential Method"
    RANDOMIZED = "Randomized Analysis"
    PROBABILISTIC = "Probabilistic Analysis"


@dataclass
class OperationResult:
    name: str
    operations: int
    theoretical_bound: float
    actual_cost: int
    details: dict = field(default_factory=dict)

    def display(self) -> None:
        print(f"\n{self.name}")
        print(f"Actual cost: {self.actual_cost}")
        print(f"Operations: {self.operations}")
        print(f"Theoretical bound: {self.theoretical_bound:.4f}")
        print(f"Details: {self.details}")


class DynamicArray(Generic[T]):
    """
    Dynamic array with doubling capacity.

    A resize copies all existing elements.
    Although an individual append can cost O(n),
    the amortized append cost is O(1).
    """

    def __init__(self, initial_capacity: int = 1):
        if initial_capacity < 1:
            raise AnalysisError("Initial capacity must be positive.")

        self.capacity = initial_capacity
        self.size = 0
        self.data: list[T | None] = [None] * initial_capacity
        self.total_writes = 0
        self.resize_count = 0

    def append(self, value: T) -> int:
        cost = 1

        if self.size == self.capacity:
            new_capacity = self.capacity * 2
            new_data: list[T | None] = [None] * new_capacity

            for index in range(self.size):
                new_data[index] = self.data[index]
                cost += 1

            self.data = new_data
            self.capacity = new_capacity
            self.resize_count += 1

        self.data[self.size] = value
        self.size += 1
        self.total_writes += cost

        return cost

    def get(self, index: int) -> T:
        if not 0 <= index < self.size:
            raise IndexError("Dynamic array index out of range.")

        value = self.data[index]

        if value is None:
            return value  # type: ignore[return-value]

        return value

    def values(self) -> list[T]:
        return self.data[:self.size]  # type: ignore[return-value]


def analyze_dynamic_array(n: int) -> OperationResult:
    if n <= 0:
        raise AnalysisError("Number of insertions must be positive.")

    array: DynamicArray[int] = DynamicArray()
    for value in range(n):
        array.append(value)

    # For doubling arrays, total writes are bounded by approximately 3n.
    return OperationResult(
        name="Dynamic Array: Amortized Analysis",
        operations=n,
        theoretical_bound=3 * n,
        actual_cost=array.total_writes,
        details={
            "size": array.size,
            "capacity": array.capacity,
            "resizes": array.resize_count,
            "actual_amortized_cost": array.total_writes / n,
            "individual_append_complexity": "O(n) worst case",
            "amortized_append_complexity": "O(1)",
        },
    )


def analyze_accounting_method(n: int) -> OperationResult:
    """
    Assign three credits to each insertion.
    One credit pays for the insertion.
    Remaining credits help pay for future resizing.
    """

    if n <= 0:
        raise AnalysisError("Number of operations must be positive.")

    array: DynamicArray[int] = DynamicArray()
    credits = 0
    charged_cost = 0

    for value in range(n):
        credits += 3
        charged_cost += 3

        actual_cost = array.append(value)
        credits -= actual_cost

        if credits < 0:
            raise RuntimeError("Accounting invariant violated.")

    return OperationResult(
        name="Accounting Method",
        operations=n,
        theoretical_bound=3 * n,
        actual_cost=array.total_writes,
        details={
            "charged_cost": charged_cost,
            "remaining_credits": credits,
            "credit_invariant": "Nonnegative",
        },
    )


def analyze_potential_method(n: int) -> OperationResult:
    """
    Potential function:
        Phi = 2 * size - capacity

    For a doubling array, the potential is nonnegative
    after each completed insertion.
    """

    if n <= 0:
        raise AnalysisError("Number of operations must be positive.")

    array: DynamicArray[int] = DynamicArray()
    potential = 0
    amortized_total = 0
    history = []

    for value in range(n):
        old_potential = potential
        actual_cost = array.append(value)

        potential = 2 * array.size - array.capacity

        amortized_cost = actual_cost + potential - old_potential
        amortized_total += amortized_cost

        if potential < 0:
            raise RuntimeError("Potential invariant violated.")

        history.append({
            "operation": value + 1,
            "actual_cost": actual_cost,
            "potential": potential,
            "amortized_cost": amortized_cost,
        })

    return OperationResult(
        name="Potential Method",
        operations=n,
        theoretical_bound=3 * n,
        actual_cost=array.total_writes,
        details={
            "total_amortized_cost": amortized_total,
            "final_potential": potential,
            "last_operation": history[-1],
        },
    )


@dataclass
class SortStatistics:
    comparisons: int = 0
    swaps: int = 0
    partitions: int = 0


def randomized_quicksort(
    values: list[int],
    seed: int = 42
) -> tuple[list[int], SortStatistics]:
    """
    Randomized quicksort.

    Expected comparisons for distinct elements:
        2(n + 1)H_n - 4n

    Expected time: O(n log n)
    Worst-case time: O(n^2)
    Auxiliary recursion space: O(n) worst case.
    """

    result = values.copy()
    rng = random.Random(seed)
    stats = SortStatistics()

    def partition(low: int, high: int) -> int:
        stats.partitions += 1

        pivot_index = rng.randint(low, high)
        result[pivot_index], result[high] = (
            result[high],
            result[pivot_index],
        )
        stats.swaps += 1

        pivot = result[high]
        boundary = low - 1

        for index in range(low, high):
            stats.comparisons += 1

            if result[index] <= pivot:
                boundary += 1
                result[boundary], result[index] = (
                    result[index],
                    result[boundary],
                )
                stats.swaps += 1

        result[boundary + 1], result[high] = (
            result[high],
            result[boundary + 1],
        )
        stats.swaps += 1

        return boundary + 1

    def sort(low: int, high: int) -> None:
        if low >= high:
            return

        pivot = partition(low, high)
        sort(low, pivot - 1)
        sort(pivot + 1, high)

    sort(0, len(result) - 1)
    return result, stats


def harmonic_number(n: int) -> float:
    if n < 0:
        raise AnalysisError("Input cannot be negative.")

    return sum(1.0 / index for index in range(1, n + 1))


def expected_quicksort_comparisons(n: int) -> float:
    if n < 0:
        raise AnalysisError("Input cannot be negative.")

    if n <= 1:
        return 0.0

    return 2 * (n + 1) * harmonic_number(n) - 4 * n


def run_randomized_sort_experiment(
    n: int,
    trials: int = 100,
    seed: int = 42
) -> dict:
    if n < 0 or trials <= 0:
        raise AnalysisError("Invalid experiment parameters.")

    master_rng = random.Random(seed)
    comparison_counts = []

    for _ in range(trials):
        values = list(range(n))
        master_rng.shuffle(values)

        _, stats = randomized_quicksort(
            values,
            seed=master_rng.randrange(1_000_000_000),
        )
        comparison_counts.append(stats.comparisons)

    return {
        "algorithm": "Randomized Quicksort",
        "input_size": n,
        "trials": trials,
        "mean_comparisons": statistics.mean(comparison_counts),
        "minimum_comparisons": min(comparison_counts),
        "maximum_comparisons": max(comparison_counts),
        "theoretical_expected_comparisons":
            expected_quicksort_comparisons(n),
        "standard_deviation":
            statistics.pstdev(comparison_counts),
    }


def coupon_collector_experiment(
    coupon_types: int,
    trials: int = 1000,
    seed: int = 42,
) -> dict:
    """
    Simulate the coupon collector problem.

    Expected draws to collect all n coupon types:
        E[T] = n * H_n

    The simulation demonstrates probabilistic analysis.
    """

    if coupon_types <= 0 or trials <= 0:
        raise AnalysisError("Coupon types and trials must be positive.")

    rng = random.Random(seed)
    observations = []

    for _ in range(trials):
        collected: set[int] = set()
        draws = 0

        while len(collected) < coupon_types:
            collected.add(rng.randrange(coupon_types))
            draws += 1

        observations.append(draws)

    theoretical = coupon_types * harmonic_number(coupon_types)

    return {
        "experiment": "Coupon Collector",
        "coupon_types": coupon_types,
        "trials": trials,
        "mean_draws": statistics.mean(observations),
        "theoretical_expected_draws": theoretical,
        "minimum_draws": min(observations),
        "maximum_draws": max(observations),
        "standard_deviation": statistics.pstdev(observations),
    }


def demonstrate_probability() -> dict:
    """
    Estimate the probability of a randomly selected
    integer in [1, 100] being prime.
    """

    def is_prime(number: int) -> bool:
        if number < 2:
            return False

        if number == 2:
            return True

        if number % 2 == 0:
            return False

        divisor = 3
        while divisor * divisor <= number:
            if number % divisor == 0:
                return False
            divisor += 2

        return True

    rng = random.Random(123)
    samples = 10000
    prime_count = sum(
        is_prime(rng.randint(1, 100))
        for _ in range(samples)
    )

    exact_probability = sum(
        is_prime(number) for number in range(1, 101)
    ) / 100

    return {
        "experiment": "Prime Sampling",
        "samples": samples,
        "estimated_probability": prime_count / samples,
        "exact_probability": exact_probability,
    }


def run_validation_tests() -> None:
    result = analyze_dynamic_array(1000)
    assert result.actual_cost <= result.theoretical_bound

    sorted_values, stats = randomized_quicksort(
        [8, 3, 7, 1, 9, 2, 5, 4, 6]
    )
    assert sorted_values == list(range(1, 10))
    assert stats.comparisons > 0

    assert randomized_quicksort([])[0] == []
    assert randomized_quicksort([5])[0] == [5]

    assert abs(
        expected_quicksort_comparisons(2) - 1
    ) < 1e-9

    assert coupon_collector_experiment(
        1, 10
    )["mean_draws"] == 1

    try:
        analyze_dynamic_array(0)
        raise AssertionError("Invalid input was accepted.")
    except AnalysisError:
        pass


def main() -> None:
    print("=" * 65)
    print("ADVANCED ALGORITHM ANALYSIS")
    print("=" * 65)

    start = time.perf_counter()

    analyze_dynamic_array(10000).display()
    analyze_accounting_method(10000).display()
    analyze_potential_method(10000).display()

    print("\nRANDOMIZED ALGORITHM EXPERIMENT")
    print(run_randomized_sort_experiment(100, 200))

    print("\nPROBABILISTIC ANALYSIS")
    print(coupon_collector_experiment(20, 2000))

    print("\nPROBABILITY ESTIMATION")
    print(demonstrate_probability())

    run_validation_tests()

    elapsed = time.perf_counter() - start

    print("\nVALIDATION")
    print("All assertions passed.")
    print(f"Execution time: {elapsed:.6f} seconds")


if __name__ == "__main__":
    main()
