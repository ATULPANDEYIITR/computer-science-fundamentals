#!/usr/bin/env python3
"""
Dynamic Programming: Memoization, Tabulation, Optimal Substructure,
and Overlapping Subproblems.

Executable with Python 3.10+.
Uses only the Python standard library.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Optional
import logging
import unittest


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# DOMAIN MODELS
# ============================================================

@dataclass(frozen=True)
class Item:
    name: str
    weight: int
    value: int

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("Item name cannot be empty.")
        if self.weight <= 0:
            raise ValueError("Weight must be positive.")
        if self.value < 0:
            raise ValueError("Value cannot be negative.")


@dataclass
class DPResult:
    value: int
    selected_items: list[str]
    states_computed: int
    algorithm: str


# ============================================================
# 1. FIBONACCI: RECURSION AND MEMOIZATION
# ============================================================

def fibonacci_recursive(n: int) -> int:
    """Basic recursive Fibonacci implementation."""

    if n < 0:
        raise ValueError("n cannot be negative.")

    if n <= 1:
        return n

    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)


def fibonacci_memoized(n: int) -> int:
    """
    Top-down dynamic programming.

    Memoization stores previously computed results.
    Each distinct state is calculated once.
    """

    if n < 0:
        raise ValueError("n cannot be negative.")

    @lru_cache(maxsize=None)
    def solve(state: int) -> int:
        if state <= 1:
            return state

        return solve(state - 1) + solve(state - 2)

    return solve(n)


# ============================================================
# 2. FIBONACCI: TABULATION
# ============================================================

def fibonacci_tabulated(n: int) -> int:
    """
    Bottom-up dynamic programming.

    Builds solutions from smaller states to larger states.
    Uses O(1) auxiliary space.
    """

    if n < 0:
        raise ValueError("n cannot be negative.")

    if n <= 1:
        return n

    previous = 0
    current = 1

    for _ in range(2, n + 1):
        previous, current = current, previous + current

    return current


# ============================================================
# 3. GRID PATHS: OVERLAPPING SUBPROBLEMS
# ============================================================

def count_grid_paths_memoized(
    rows: int,
    columns: int,
    obstacles: Optional[set[tuple[int, int]]] = None
) -> int:
    """
    Count paths from the top-left to the bottom-right.

    Allowed movements:
        Right
        Down

    Obstacles are represented by (row, column).
    """

    if rows <= 0 or columns <= 0:
        raise ValueError("Grid dimensions must be positive.")

    blocked = obstacles or set()

    for row, column in blocked:
        if not (0 <= row < rows and 0 <= column < columns):
            raise ValueError("Obstacle lies outside the grid.")

    @lru_cache(maxsize=None)
    def solve(row: int, column: int) -> int:

        if row >= rows or column >= columns:
            return 0

        if (row, column) in blocked:
            return 0

        if row == rows - 1 and column == columns - 1:
            return 1

        return (
            solve(row + 1, column)
            + solve(row, column + 1)
        )

    return solve(0, 0)


def count_grid_paths_tabulated(
    rows: int,
    columns: int,
    obstacles: Optional[set[tuple[int, int]]] = None
) -> int:
    """Bottom-up grid path calculation using O(columns) space."""

    if rows <= 0 or columns <= 0:
        raise ValueError("Grid dimensions must be positive.")

    blocked = obstacles or set()

    for row, column in blocked:
        if not (0 <= row < rows and 0 <= column < columns):
            raise ValueError("Obstacle lies outside the grid.")

    dp = [0] * columns

    for row in range(rows):
        for column in range(columns):

            if (row, column) in blocked:
                dp[column] = 0

            elif row == 0 and column == 0:
                dp[column] = 1

            else:
                above = dp[column]
                left = dp[column - 1] if column > 0 else 0
                dp[column] = above + left

    return dp[-1]


# ============================================================
# 4. 0/1 KNAPSACK: OPTIMAL SUBSTRUCTURE
# ============================================================

def knapsack_memoized(
    items: list[Item],
    capacity: int
) -> DPResult:
    """
    Top-down 0/1 knapsack.

    Each item can be selected at most once.

    State:
        solve(index, remaining_capacity)

    Decision:
        Exclude the current item.
        Include the current item when it fits.
    """

    if capacity < 0:
        raise ValueError("Capacity cannot be negative.")

    states = 0

    @lru_cache(maxsize=None)
    def solve(index: int, remaining: int) -> int:
        nonlocal states
        states += 1

        if index == len(items):
            return 0

        exclude = solve(index + 1, remaining)

        include = 0

        item = items[index]

        if item.weight <= remaining:
            include = (
                item.value
                + solve(index + 1, remaining - item.weight)
            )

        return max(include, exclude)

    best_value = solve(0, capacity)

    selected = []
    remaining = capacity

    for index, item in enumerate(items):

        if item.weight > remaining:
            continue

        current = solve(index, remaining)
        excluded = solve(index + 1, remaining)

        if (
            item.value
            + solve(index + 1, remaining - item.weight)
            > excluded
        ):
            selected.append(item.name)
            remaining -= item.weight

    return DPResult(
        value=best_value,
        selected_items=selected,
        states_computed=states,
        algorithm="Memoization"
    )


def knapsack_tabulated(
    items: list[Item],
    capacity: int
) -> DPResult:
    """
    Bottom-up 0/1 knapsack.

    The two-dimensional table supports reconstruction
    of the selected items.
    """

    if capacity < 0:
        raise ValueError("Capacity cannot be negative.")

    n = len(items)

    dp = [
        [0] * (capacity + 1)
        for _ in range(n + 1)
    ]

    for i in range(1, n + 1):

        item = items[i - 1]

        for weight in range(capacity + 1):

            exclude = dp[i - 1][weight]
            include = 0

            if item.weight <= weight:
                include = (
                    item.value
                    + dp[i - 1][weight - item.weight]
                )

            dp[i][weight] = max(include, exclude)

    selected = []
    remaining = capacity

    for i in range(n, 0, -1):

        if dp[i][remaining] != dp[i - 1][remaining]:

            item = items[i - 1]
            selected.append(item.name)
            remaining -= item.weight

    selected.reverse()

    return DPResult(
        value=dp[n][capacity],
        selected_items=selected,
        states_computed=(n + 1) * (capacity + 1),
        algorithm="Tabulation"
    )


# ============================================================
# 5. LONGEST COMMON SUBSEQUENCE
# ============================================================

def longest_common_subsequence(
    first: str,
    second: str
) -> tuple[int, str]:
    """
    Find the longest common subsequence.

    A subsequence preserves relative character order,
    but characters need not be consecutive.
    """

    if not isinstance(first, str) or not isinstance(second, str):
        raise TypeError("Inputs must be strings.")

    rows = len(first)
    columns = len(second)

    dp = [
        [0] * (columns + 1)
        for _ in range(rows + 1)
    ]

    for i in range(1, rows + 1):
        for j in range(1, columns + 1):

            if first[i - 1] == second[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1

            else:
                dp[i][j] = max(
                    dp[i - 1][j],
                    dp[i][j - 1]
                )

    sequence = []
    i, j = rows, columns

    while i > 0 and j > 0:

        if first[i - 1] == second[j - 1]:
            sequence.append(first[i - 1])
            i -= 1
            j -= 1

        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1

        else:
            j -= 1

    sequence.reverse()

    result = "".join(sequence)

    return dp[rows][columns], result


# ============================================================
# 6. DYNAMIC PROGRAMMING COMPARISON
# ============================================================

def compare_fibonacci(n: int) -> dict[str, int]:
    """Compare memoized and tabulated approaches."""

    return {
        "memoization": fibonacci_memoized(n),
        "tabulation": fibonacci_tabulated(n)
    }


# ============================================================
# 7. TESTING
# ============================================================

class DynamicProgrammingTests(unittest.TestCase):

    def test_fibonacci(self):
        for n in range(20):
            self.assertEqual(
                fibonacci_memoized(n),
                fibonacci_tabulated(n)
            )

        self.assertEqual(fibonacci_tabulated(100), 354224848179261915075)

    def test_fibonacci_invalid(self):
        with self.assertRaises(ValueError):
            fibonacci_tabulated(-1)

    def test_grid_paths(self):
        self.assertEqual(
            count_grid_paths_memoized(3, 3),
            6
        )

        self.assertEqual(
            count_grid_paths_tabulated(3, 3),
            6
        )

    def test_grid_obstacles(self):
        blocked = {(1, 1)}

        self.assertEqual(
            count_grid_paths_memoized(3, 3, blocked),
            2
        )

        self.assertEqual(
            count_grid_paths_tabulated(3, 3, blocked),
            2
        )

    def test_knapsack(self):
        items = [
            Item("Laptop", 3, 50),
            Item("Monitor", 4, 60),
            Item("Keyboard", 2, 30),
            Item("Mouse", 1, 20)
        ]

        memo = knapsack_memoized(items, 5)
        table = knapsack_tabulated(items, 5)

        self.assertEqual(memo.value, 80)
        self.assertEqual(table.value, 80)
        self.assertEqual(set(memo.selected_items), set(table.selected_items))

    def test_empty_knapsack(self):
        result = knapsack_tabulated([], 10)
        self.assertEqual(result.value, 0)
        self.assertEqual(result.selected_items, [])

    def test_lcs(self):
        length, sequence = longest_common_subsequence(
            "ABCBDAB",
            "BDCABA"
        )

        self.assertEqual(length, 4)
        self.assertEqual(len(sequence), 4)

    def test_zero_capacity(self):
        item = Item("Book", 2, 10)
        result = knapsack_tabulated([item], 0)

        self.assertEqual(result.value, 0)

    def test_invalid_item(self):
        with self.assertRaises(ValueError):
            Item("Invalid", 0, 10)


# ============================================================
# 8. EXECUTABLE EXAMPLES
# ============================================================

def run_demonstration() -> None:

    print("\nDYNAMIC PROGRAMMING DEMONSTRATION")
    print("=" * 55)

    n = 15

    print("\n1. Fibonacci")

    print("Memoization:", fibonacci_memoized(n))
    print("Tabulation:", fibonacci_tabulated(n))

    print("\n2. Grid Path Optimization")

    print(
        "Paths without obstacles:",
        count_grid_paths_tabulated(4, 4)
    )

    print(
        "Paths with obstacle:",
        count_grid_paths_tabulated(4, 4, {(1, 1), (2, 2)})
    )

    print("\n3. 0/1 Knapsack")

    items = [
        Item("Laptop", 3, 50),
        Item("Monitor", 4, 60),
        Item("Keyboard", 2, 30),
        Item("Mouse", 1, 20),
        Item("SSD", 2, 40)
    ]

    capacity = 7

    memo_result = knapsack_memoized(items, capacity)
    table_result = knapsack_tabulated(items, capacity)

    for result in (memo_result, table_result):

        print(f"\nAlgorithm: {result.algorithm}")
        print("Maximum value:", result.value)
        print("Selected items:", result.selected_items)
        print("Computed states:", result.states_computed)

    print("\n4. Longest Common Subsequence")

    length, sequence = longest_common_subsequence(
        "DYNAMICPROGRAMMING",
        "PROGRAMMING"
    )

    print("Length:", length)
    print("Sequence:", sequence)

    print("\n5. Method Comparison")

    print(compare_fibonacci(20))

    print("\n6. Automated Tests")

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        DynamicProgrammingTests
    )

    result = unittest.TextTestRunner(verbosity=2).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)


if __name__ == "__main__":
    run_demonstration()
