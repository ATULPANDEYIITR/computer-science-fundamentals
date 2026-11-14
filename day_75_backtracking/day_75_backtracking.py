"""
BACKTRACKING: STATE SPACE TREES, PERMUTATIONS, COMBINATIONS, AND N-QUEENS

Python 3.10+
Standard-library only.

Demonstrates:
1. Recursive backtracking and state-space exploration.
2. Permutations with duplicate elimination.
3. Combinations with pruning.
4. N-Queens with column and diagonal constraints.
5. Search statistics, limits, validation, and tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Generator, Iterable, Optional
import json
import logging
import time


logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger("backtracking")


class SearchError(Exception):
    """Base exception for search operations."""


class SearchLimitExceeded(SearchError):
    """Raised when a configured search limit is reached."""


class SearchMode(Enum):
    PERMUTATIONS = "permutations"
    COMBINATIONS = "combinations"
    N_QUEENS = "n_queens"


@dataclass
class SearchStatistics:
    nodes_visited: int = 0
    solutions_found: int = 0
    pruned_branches: int = 0
    maximum_depth: int = 0
    elapsed_seconds: float = 0.0

    def report(self) -> dict:
        return {
            "nodes_visited": self.nodes_visited,
            "solutions_found": self.solutions_found,
            "pruned_branches": self.pruned_branches,
            "maximum_depth": self.maximum_depth,
            "elapsed_seconds": round(self.elapsed_seconds, 6),
        }


@dataclass
class SearchConfiguration:
    max_nodes: Optional[int] = 1_000_000
    max_solutions: Optional[int] = 100_000

    def __post_init__(self):
        for name, value in (
            ("max_nodes", self.max_nodes),
            ("max_solutions", self.max_solutions),
        ):
            if value is not None and value < 1:
                raise ValueError(f"{name} must be positive or None")


class BacktrackingEngine:
    """
    Generic state-space traversal.

    Each recursive call represents one state-space-tree node.
    The path contains the current partial solution.
    """

    def __init__(
        self,
        configuration: Optional[SearchConfiguration] = None
    ):
        self.configuration = configuration or SearchConfiguration()
        self.statistics = SearchStatistics()
        self._start_time = 0.0

    def reset(self):
        self.statistics = SearchStatistics()
        self._start_time = time.perf_counter()

    def visit_node(self, depth: int):
        self.statistics.nodes_visited += 1
        self.statistics.maximum_depth = max(
            self.statistics.maximum_depth,
            depth
        )

        limit = self.configuration.max_nodes

        if limit is not None and self.statistics.nodes_visited > limit:
            raise SearchLimitExceeded(
                f"Node limit exceeded: {limit}"
            )

    def record_solution(self):
        limit = self.configuration.max_solutions

        if (
            limit is not None
            and self.statistics.solutions_found >= limit
        ):
            raise SearchLimitExceeded(
                f"Solution limit exceeded: {limit}"
            )

        self.statistics.solutions_found += 1

    def finish(self):
        self.statistics.elapsed_seconds = (
            time.perf_counter() - self._start_time
        )


class PermutationSolver:
    """Generate distinct permutations using duplicate-aware backtracking."""

    def __init__(
        self,
        values: Iterable,
        configuration: Optional[SearchConfiguration] = None
    ):
        self.values = list(values)
        self.engine = BacktrackingEngine(configuration)

    def solve(self) -> list[list]:
        self.engine.reset()

        ordered = sorted(self.values)
        path = []
        used = [False] * len(ordered)
        results = []

        def backtrack():
            self.engine.visit_node(len(path))

            if len(path) == len(ordered):
                self.engine.record_solution()
                results.append(path.copy())
                return

            for index, value in enumerate(ordered):
                if used[index]:
                    continue

                # Equal values at the same decision depth produce
                # duplicate branches. Only the first unused copy is used.
                if (
                    index > 0
                    and ordered[index] == ordered[index - 1]
                    and not used[index - 1]
                ):
                    self.engine.statistics.pruned_branches += 1
                    continue

                used[index] = True
                path.append(value)

                backtrack()

                path.pop()
                used[index] = False

        try:
            backtrack()
        finally:
            self.engine.finish()

        return results


class CombinationSolver:
    """
    Generate combinations without considering order.

    A sorted input and increasing indices ensure that each
    combination is generated once.
    """

    def __init__(
        self,
        values: Iterable,
        selection_size: int,
        configuration: Optional[SearchConfiguration] = None
    ):
        self.values = list(values)

        if not isinstance(selection_size, int):
            raise TypeError("selection_size must be an integer")

        if not 0 <= selection_size <= len(self.values):
            raise ValueError(
                "selection_size must be between zero and input length"
            )

        self.selection_size = selection_size
        self.engine = BacktrackingEngine(configuration)

    def solve(self) -> list[list]:
        self.engine.reset()

        values = sorted(self.values)
        results = []
        path = []
        n = len(values)
        k = self.selection_size

        def backtrack(start: int):
            self.engine.visit_node(len(path))

            if len(path) == k:
                self.engine.record_solution()
                results.append(path.copy())
                return

            remaining = k - len(path)

            # No valid completion exists if too few elements remain.
            last_start = n - remaining

            for index in range(start, last_start + 1):
                # Remove duplicate combinations at the same depth.
                if (
                    index > start
                    and values[index] == values[index - 1]
                ):
                    self.engine.statistics.pruned_branches += 1
                    continue

                path.append(values[index])
                backtrack(index + 1)
                path.pop()

        try:
            backtrack(0)
        finally:
            self.engine.finish()

        return results


@dataclass
class NQueensSolution:
    positions: tuple[int, ...]

    def board(self) -> list[str]:
        n = len(self.positions)
        result = []

        for column in self.positions:
            row = ["."] * n
            row[column] = "Q"
            result.append("".join(row))

        return result


class NQueensSolver:
    """
    Place one queen in each row.

    Three sets enforce:
    - Unique columns.
    - Unique row-column diagonals.
    - Unique row+column diagonals.
    """

    def __init__(
        self,
        n: int,
        configuration: Optional[SearchConfiguration] = None
    ):
        if not isinstance(n, int) or isinstance(n, bool):
            raise TypeError("Board size must be an integer")

        if not 1 <= n <= 15:
            raise ValueError("Board size must be between 1 and 15")

        self.n = n
        self.engine = BacktrackingEngine(configuration)

    def solve(self) -> list[NQueensSolution]:
        self.engine.reset()

        positions = [-1] * self.n
        columns = set()
        descending_diagonals = set()
        ascending_diagonals = set()

        results = []

        def backtrack(row: int):
            self.engine.visit_node(row)

            if row == self.n:
                self.engine.record_solution()
                results.append(
                    NQueensSolution(tuple(positions))
                )
                return

            for column in range(self.n):
                descending = row - column
                ascending = row + column

                if (
                    column in columns
                    or descending in descending_diagonals
                    or ascending in ascending_diagonals
                ):
                    self.engine.statistics.pruned_branches += 1
                    continue

                positions[row] = column
                columns.add(column)
                descending_diagonals.add(descending)
                ascending_diagonals.add(ascending)

                backtrack(row + 1)

                # Undo every state modification before exploring
                # the next candidate.
                positions[row] = -1
                columns.remove(column)
                descending_diagonals.remove(descending)
                ascending_diagonals.remove(ascending)

        try:
            backtrack(0)
        finally:
            self.engine.finish()

        return results


class NQueensBitmaskSolver:
    """
    Optimized N-Queens using integer bitmasks.

    A bit represents an occupied column or diagonal.
    """

    def __init__(self, n: int):
        if not isinstance(n, int) or isinstance(n, bool):
            raise TypeError("Board size must be an integer")

        if not 1 <= n <= 15:
            raise ValueError("Board size must be between 1 and 15")

        self.n = n
        self.full_mask = (1 << n) - 1
        self.nodes_visited = 0
        self.solutions = []

    def solve(self) -> list[NQueensSolution]:
        self.nodes_visited = 0
        self.solutions = []

        positions = [-1] * self.n

        def search(row, columns, left_diagonals, right_diagonals):
            self.nodes_visited += 1

            if row == self.n:
                self.solutions.append(
                    NQueensSolution(tuple(positions))
                )
                return

            available = self.full_mask & ~(
                columns | left_diagonals | right_diagonals
            )

            while available:
                # Extract the least significant available bit.
                bit = available & -available
                available ^= bit

                column = bit.bit_length() - 1
                positions[row] = column

                search(
                    row + 1,
                    columns | bit,
                    ((left_diagonals | bit) << 1) & self.full_mask,
                    (right_diagonals | bit) >> 1,
                )

                positions[row] = -1

        search(0, 0, 0, 0)
        return self.solutions


def display_solutions(title: str, solutions: list):
    print(f"\n{title}")
    print("=" * len(title))

    for index, solution in enumerate(solutions, 1):
        if isinstance(solution, NQueensSolution):
            print(f"Solution {index}:")
            print("\n".join(solution.board()))
        else:
            print(f"{index}: {solution}")

        print()


def demonstrate_permutations():
    solver = PermutationSolver([1, 2, 2])
    results = solver.solve()

    display_solutions("Distinct Permutations of [1, 2, 2]", results)
    print("Statistics:", solver.engine.statistics.report())

    assert len(results) == 3
    assert len({tuple(item) for item in results}) == 3


def demonstrate_combinations():
    solver = CombinationSolver([1, 2, 3, 4], 2)
    results = solver.solve()

    display_solutions("Combinations of [1, 2, 3, 4], k=2", results)
    print("Statistics:", solver.engine.statistics.report())

    assert len(results) == 6


def demonstrate_n_queens():
    solver = NQueensSolver(4)
    solutions = solver.solve()

    display_solutions("N-Queens: Board Size 4", solutions)
    print("Statistics:", solver.engine.statistics.report())

    assert len(solutions) == 2

    optimized = NQueensBitmaskSolver(4)
    optimized_results = optimized.solve()

    assert len(optimized_results) == 2

    print("Bitmask search nodes:", optimized.nodes_visited)


def demonstrate_edge_cases():
    assert PermutationSolver([]).solve() == [[]]

    assert CombinationSolver([], 0).solve() == [[]]

    assert CombinationSolver([1, 2, 3], 0).solve() == [[]]

    assert CombinationSolver([1, 2, 3], 3).solve() == [
        [1, 2, 3]
    ]

    assert len(NQueensSolver(1).solve()) == 1

    assert len(NQueensSolver(2).solve()) == 0
    assert len(NQueensSolver(3).solve()) == 0

    assert len(NQueensSolver(5).solve()) == 10

    try:
        NQueensSolver(0)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid board size was accepted")

    print("\nAll edge-case assertions passed.")


def demonstrate_search_limits():
    solver = PermutationSolver(
        [1, 2, 3, 4, 5],
        SearchConfiguration(
            max_nodes=5,
            max_solutions=100
        )
    )

    try:
        solver.solve()
    except SearchLimitExceeded as error:
        print("\nControlled search termination:", error)


def export_results(filename: str, solutions: list):
    """
    Write results as JSON.

    The destination is explicitly supplied by the caller.
    Production applications should restrict writable directories.
    """

    data = []

    for solution in solutions:
        if isinstance(solution, NQueensSolution):
            data.append({
                "positions": solution.positions,
                "board": solution.board(),
            })
        else:
            data.append(solution)

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def main():
    print("BACKTRACKING ALGORITHM LABORATORY")
    print("--------------------------------")

    demonstrate_permutations()
    demonstrate_combinations()
    demonstrate_n_queens()
    demonstrate_edge_cases()
    demonstrate_search_limits()

    print("\nExecution completed successfully.")


if __name__ == "__main__":
    main()
