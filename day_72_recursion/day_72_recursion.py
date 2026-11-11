#!/usr/bin/env python3
"""
Recursion: Recursive Thinking, Recursion Trees, Base Cases, and Algorithms.

Demonstrates:
- Recursive problem decomposition
- Base cases and recursive progress
- Recursion depth and call tracking
- Factorial and Fibonacci
- Memoization and dynamic programming
- Binary search
- Merge sort
- Recursive tree traversal
- Recursive directory-size calculation
- Recursion-tree analysis
- Validation, exceptions, and automated tests

Python 3.10+
Standard library only.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import sys
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger("recursion")

T = TypeVar("T")


class RecursionErrorType(Exception):
    """Base exception for recursion-related errors."""


class InvalidInputError(RecursionErrorType):
    """Raised when an algorithm receives invalid input."""


class RecursionLimitError(RecursionErrorType):
    """Raised when a configured recursion budget is exceeded."""


class Algorithm(Enum):
    FACTORIAL = "factorial"
    FIBONACCI = "fibonacci"
    BINARY_SEARCH = "binary_search"
    MERGE_SORT = "merge_sort"
    TREE_TRAVERSAL = "tree_traversal"


@dataclass
class RecursionMetrics:
    calls: int = 0
    maximum_depth: int = 0
    cache_hits: int = 0
    comparisons: int = 0

    def register_call(self, depth: int) -> None:
        self.calls += 1
        self.maximum_depth = max(self.maximum_depth, depth)


@dataclass
class RecursionNode:
    problem: str
    depth: int
    result: Optional[str] = None
    children: list["RecursionNode"] = field(default_factory=list)


@dataclass
class TreeNode:
    value: int
    left: Optional["TreeNode"] = None
    right: Optional["TreeNode"] = None


class RecursionEngine:
    """Collection of recursive algorithms with measurable execution."""

    def __init__(self, max_depth: int = 900):
        if max_depth < 1:
            raise InvalidInputError("Maximum depth must be positive.")

        self.max_depth = min(max_depth, sys.getrecursionlimit() - 50)
        self.metrics = RecursionMetrics()

    def reset_metrics(self) -> None:
        self.metrics = RecursionMetrics()

    def _check_depth(self, depth: int) -> None:
        if depth > self.max_depth:
            raise RecursionLimitError(
                f"Recursion depth {depth} exceeds limit {self.max_depth}."
            )

    def factorial(self, n: int, depth: int = 0) -> int:
        """Calculate n! using a direct recursive definition."""

        if isinstance(n, bool) or not isinstance(n, int) or n < 0:
            raise InvalidInputError("Factorial requires a non-negative integer.")

        self._check_depth(depth)
        self.metrics.register_call(depth)

        # Base cases: 0! = 1 and 1! = 1.
        if n <= 1:
            return 1

        # Every recursive call reduces n.
        return n * self.factorial(n - 1, depth + 1)

    def fibonacci(self, n: int, depth: int = 0) -> int:
        """Calculate Fibonacci using naive recursion."""

        if isinstance(n, bool) or not isinstance(n, int) or n < 0:
            raise InvalidInputError("Fibonacci requires a non-negative integer.")

        if n > 35:
            raise InvalidInputError(
                "Naive Fibonacci is restricted to n <= 35."
            )

        self._check_depth(depth)
        self.metrics.register_call(depth)

        # Two base cases are required.
        if n <= 1:
            return n

        return (
            self.fibonacci(n - 1, depth + 1)
            + self.fibonacci(n - 2, depth + 1)
        )

    def fibonacci_memoized(self, n: int) -> int:
        """Calculate Fibonacci with top-down memoization."""

        if isinstance(n, bool) or not isinstance(n, int) or n < 0:
            raise InvalidInputError("Invalid Fibonacci input.")

        if n > 10000:
            raise InvalidInputError("Input exceeds configured limit.")

        self.reset_metrics()
        cache: dict[int, int] = {}

        def solve(value: int, depth: int) -> int:
            self._check_depth(depth)
            self.metrics.register_call(depth)

            if value <= 1:
                return value

            if value in cache:
                self.metrics.cache_hits += 1
                return cache[value]

            cache[value] = solve(value - 1, depth + 1) + solve(
                value - 2, depth + 1
            )

            return cache[value]

        return solve(n, 0)

    def fibonacci_iterative(self, n: int) -> int:
        """Calculate Fibonacci without recursive stack usage."""

        if isinstance(n, bool) or not isinstance(n, int) or n < 0:
            raise InvalidInputError("Invalid Fibonacci input.")

        if n > 10000:
            raise InvalidInputError("Input exceeds configured limit.")

        previous, current = 0, 1

        for _ in range(n):
            previous, current = current, previous + current

        return previous

    def binary_search(
        self,
        values: list[int],
        target: int,
        left: int = 0,
        right: Optional[int] = None,
        depth: int = 0
    ) -> int:
        """Search a sorted list using recursive interval reduction."""

        if not all(isinstance(x, int) and not isinstance(x, bool) for x in values):
            raise InvalidInputError("Binary search requires integer elements.")

        if values != sorted(values):
            raise InvalidInputError("Input must be sorted.")

        if isinstance(target, bool) or not isinstance(target, int):
            raise InvalidInputError("Target must be an integer.")

        if right is None:
            right = len(values) - 1

        if left < 0 or right >= len(values):
            if not values and left == 0 and right == -1:
                return -1
            raise InvalidInputError("Invalid search boundaries.")

        self._check_depth(depth)
        self.metrics.register_call(depth)

        # Base case: the search interval is empty.
        if left > right:
            return -1

        middle = left + (right - left) // 2
        self.metrics.comparisons += 1

        if values[middle] == target:
            return middle

        if target < values[middle]:
            return self.binary_search(
                values, target, left, middle - 1, depth + 1
            )

        return self.binary_search(
            values, target, middle + 1, right, depth + 1
        )

    def merge_sort(self, values: list[int]) -> list[int]:
        """Sort integers using divide, conquer, and combine."""

        if not all(isinstance(x, int) and not isinstance(x, bool) for x in values):
            raise InvalidInputError("Merge sort requires integer elements.")

        self.reset_metrics()

        def sort(items: list[int], depth: int) -> list[int]:
            self._check_depth(depth)
            self.metrics.register_call(depth)

            # Base case: lists of zero or one elements are sorted.
            if len(items) <= 1:
                return items.copy()

            middle = len(items) // 2

            left = sort(items[:middle], depth + 1)
            right = sort(items[middle:], depth + 1)

            return merge(left, right)

        def merge(left: list[int], right: list[int]) -> list[int]:
            result: list[int] = []
            i = j = 0

            while i < len(left) and j < len(right):
                self.metrics.comparisons += 1

                if left[i] <= right[j]:
                    result.append(left[i])
                    i += 1
                else:
                    result.append(right[j])
                    j += 1

            result.extend(left[i:])
            result.extend(right[j:])

            return result

        return sort(values, 0)

    def traverse_tree(
        self,
        root: Optional[TreeNode],
        order: str = "inorder"
    ) -> list[int]:
        """Traverse a binary tree using recursive traversal."""

        if order not in {"preorder", "inorder", "postorder"}:
            raise InvalidInputError("Unsupported traversal order.")

        self.reset_metrics()
        visited: list[int] = set()

        def walk(node: Optional[TreeNode], depth: int) -> list[int]:
            self._check_depth(depth)

            if node is None:
                return []

            self.metrics.register_call(depth)

            # Detect accidental cycles or shared nodes.
            identity = id(node)

            if identity in visited:
                raise InvalidInputError(
                    "Tree contains a cycle or repeated node reference."
                )

            visited.add(identity)

            left = walk(node.left, depth + 1)
            right = walk(node.right, depth + 1)

            if order == "preorder":
                return [node.value] + left + right

            if order == "inorder":
                return left + [node.value] + right

            return left + right + [node.value]

        return walk(root, 0)

    def recursion_tree(
        self,
        n: int,
        branching: int = 2,
        max_display_depth: int = 5
    ) -> RecursionNode:
        """Construct a bounded illustrative recursion tree."""

        if n < 0 or branching < 1 or max_display_depth < 0:
            raise InvalidInputError("Invalid recursion-tree parameters.")

        def build(value: int, depth: int) -> RecursionNode:
            node = RecursionNode(
                problem=f"T({value})",
                depth=depth
            )

            if value <= 1 or depth >= max_display_depth:
                node.result = "base case" if value <= 1 else "display limit"
                return node

            child_value = max(0, value // 2)

            for _ in range(branching):
                node.children.append(build(child_value, depth + 1))

            return node

        return build(n, 0)


def directory_size(
    directory: Path,
    max_depth: int = 30
) -> int:
    """
    Calculate directory size recursively.

    Symbolic links are ignored to avoid following external paths
    or introducing filesystem cycles.
    """

    root = directory.resolve(strict=True)

    if not root.is_dir():
        raise InvalidInputError("The supplied path is not a directory.")

    def calculate(path: Path, depth: int) -> int:
        if depth > max_depth:
            raise RecursionLimitError("Directory nesting limit exceeded.")

        total = 0

        with os_scandir(path) as entries:
            for entry in entries:
                try:
                    if entry.is_symlink():
                        continue

                    if entry.is_file(follow_symlinks=False):
                        total += entry.stat(follow_symlinks=False).st_size

                    elif entry.is_dir(follow_symlinks=False):
                        total += calculate(Path(entry.path), depth + 1)

                except OSError as exc:
                    logger.warning(
                        "Unable to inspect %s: %s",
                        entry.path,
                        exc
                    )

        return total

    return calculate(root, 0)


def os_scandir(path: Path):
    """Open a directory iterator with deterministic resource cleanup."""
    import os
    return os.scandir(path)


def print_metrics(metrics: RecursionMetrics) -> None:
    print(json.dumps(asdict(metrics), indent=2))


def run_tests() -> None:
    engine = RecursionEngine()

    assert engine.factorial(0) == 1
    assert engine.factorial(5) == 120
    assert engine.fibonacci(10) == 55
    assert engine.fibonacci_memoized(40) == 102334155
    assert engine.fibonacci_iterative(40) == 102334155

    values = [2, 4, 6, 8, 10, 12]
    assert engine.binary_search(values, 8) == 3
    assert engine.binary_search(values, 7) == -1

    assert engine.merge_sort([9, 3, 5, 1, 8]) == [1, 3, 5, 8, 9]
    assert engine.merge_sort([]) == []

    root = TreeNode(
        10,
        TreeNode(5, TreeNode(2), TreeNode(7)),
        TreeNode(15, None, TreeNode(20))
    )

    assert engine.traverse_tree(root, "inorder") == [2, 5, 7, 10, 15, 20]
    assert engine.traverse_tree(root, "preorder") == [10, 5, 2, 7, 15, 20]
    assert engine.traverse_tree(root, "postorder") == [2, 7, 5, 20, 15, 10]

    try:
        engine.factorial(-1)
        raise AssertionError("Negative factorial should fail.")
    except InvalidInputError:
        pass

    try:
        engine.fibonacci(-1)
        raise AssertionError("Negative Fibonacci should fail.")
    except InvalidInputError:
        pass

    print("All tests passed.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Recursive algorithms and recursion analysis."
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON report path."
    )

    parser.add_argument(
        "--directory",
        type=Path,
        help="Optional directory for recursive size calculation."
    )

    parser.add_argument(
        "--tests",
        action="store_true",
        help="Run automated assertions."
    )

    args = parser.parse_args()

    engine = RecursionEngine()

    print("\n1. Factorial")
    print("5! =", engine.factorial(5))
    print_metrics(engine.metrics)

    print("\n2. Naive Fibonacci")
    engine.reset_metrics()
    print("F(10) =", engine.fibonacci(10))
    print_metrics(engine.metrics)

    print("\n3. Memoized Fibonacci")
    print("F(40) =", engine.fibonacci_memoized(40))
    print_metrics(engine.metrics)

    print("\n4. Recursive binary search")
    numbers = [3, 7, 11, 15, 19, 23, 27]
    print("Position of 19:", engine.binary_search(numbers, 19))
    print_metrics(engine.metrics)

    print("\n5. Merge sort")
    unsorted = [45, 12, 78, 3, 29, 18, 1]
    print("Sorted:", engine.merge_sort(unsorted))
    print_metrics(engine.metrics)

    print("\n6. Binary tree traversal")
    root = TreeNode(
        8,
        TreeNode(4, TreeNode(2), TreeNode(6)),
        TreeNode(12, TreeNode(10), TreeNode(14))
    )

    print("Inorder:", engine.traverse_tree(root, "inorder"))
    print_metrics(engine.metrics)

    print("\n7. Recursion tree")
    tree = engine.recursion_tree(16, branching=2)

    def display(node: RecursionNode, prefix: str = "") -> None:
        print(prefix + node.problem, node.result or "")
        for child in node.children:
            display(child, prefix + "  ")

    display(tree)

    report: dict[str, Any] = {
        "factorial_5": engine.factorial(5),
        "fibonacci_40": engine.fibonacci_memoized(40),
        "sorted_values": engine.merge_sort(unsorted),
        "binary_search_position": engine.binary_search(numbers, 19),
    }

    if args.directory:
        report["directory_size_bytes"] = directory_size(args.directory)

    if args.output:
        # Exclusive creation prevents accidental overwriting.
        with args.output.open("x", encoding="utf-8") as file:
            json.dump(report, file, indent=2)

        print(f"\nReport saved to {args.output}")

    if args.tests:
        run_tests()


if __name__ == "__main__":
    main()
