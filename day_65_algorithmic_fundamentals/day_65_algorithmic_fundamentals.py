from __future__ import annotations

import heapq
import random
import time
import unittest
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class AlgorithmError(Exception):
    """Base exception for algorithm execution errors."""


class InvalidInputError(AlgorithmError):
    """Raised when algorithm input violates its contract."""


class AlgorithmNotFoundError(AlgorithmError):
    """Raised when an algorithm is not registered."""


class AlgorithmCategory(Enum):
    SEARCHING = "Searching"
    SORTING = "Sorting"
    GRAPH = "Graph"


@dataclass
class AlgorithmMetrics:
    comparisons: int = 0
    operations: int = 0
    elapsed_seconds: float = 0.0
    input_size: int = 0

    def report(self) -> dict:
        return {
            "input_size": self.input_size,
            "comparisons": self.comparisons,
            "operations": self.operations,
            "elapsed_seconds": round(self.elapsed_seconds, 8),
        }


@dataclass
class Algorithm:
    name: str
    category: AlgorithmCategory
    time_complexity: str
    space_complexity: str
    description: str
    function: Callable


class AlgorithmRegistry:
    def __init__(self):
        self.algorithms: dict[str, Algorithm] = {}

    def register(self, algorithm: Algorithm):
        if algorithm.name in self.algorithms:
            raise InvalidInputError(
                f"Algorithm already registered: {algorithm.name}"
            )
        self.algorithms[algorithm.name] = algorithm

    def get(self, name: str) -> Algorithm:
        if name not in self.algorithms:
            raise AlgorithmNotFoundError(name)
        return self.algorithms[name]

    def list_algorithms(self) -> list[dict]:
        return [
            {
                "name": algorithm.name,
                "category": algorithm.category.value,
                "time_complexity": algorithm.time_complexity,
                "space_complexity": algorithm.space_complexity,
                "description": algorithm.description,
            }
            for algorithm in self.algorithms.values()
        ]


def binary_search(
    values: list[int],
    target: int,
    metrics: AlgorithmMetrics | None = None,
) -> int:
    """
    Find target in an ascending sorted list.

    Precondition: values is sorted in ascending order.
    Postcondition: return a matching index or -1.
    Time: O(log n).
    Auxiliary space: O(1).
    """

    if not isinstance(values, list):
        raise InvalidInputError("Input must be a list.")

    if any(not isinstance(value, int) for value in values):
        raise InvalidInputError("All elements must be integers.")

    if not isinstance(target, int):
        raise InvalidInputError("Target must be an integer.")

    if any(values[i] > values[i + 1] for i in range(len(values) - 1)):
        raise InvalidInputError("Input must be sorted.")

    left = 0
    right = len(values) - 1

    while left <= right:
        middle = left + (right - left) // 2

        if metrics:
            metrics.comparisons += 1

        if values[middle] == target:
            return middle

        if metrics:
            metrics.comparisons += 1

        if values[middle] < target:
            left = middle + 1
        else:
            right = middle - 1

    return -1


def merge_sort(
    values: list[int],
    metrics: AlgorithmMetrics | None = None,
) -> list[int]:
    """
    Stable divide-and-conquer sorting algorithm.

    Time: O(n log n).
    Auxiliary space: O(n).
    """

    if not isinstance(values, list):
        raise InvalidInputError("Input must be a list.")

    if any(not isinstance(value, int) for value in values):
        raise InvalidInputError("All elements must be integers.")

    def sort(items: list[int]) -> list[int]:
        if len(items) <= 1:
            return items.copy()

        middle = len(items) // 2
        left = sort(items[:middle])
        right = sort(items[middle:])

        result = []
        i = j = 0

        while i < len(left) and j < len(right):
            if metrics:
                metrics.comparisons += 1
                metrics.operations += 1

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


def insertion_sort(
    values: list[int],
    metrics: AlgorithmMetrics | None = None,
) -> list[int]:
    """
    Stable in-place insertion sort.

    Best time: O(n).
    Average and worst time: O(n^2).
    Auxiliary space: O(1).
    """

    if not isinstance(values, list):
        raise InvalidInputError("Input must be a list.")

    if any(not isinstance(value, int) for value in values):
        raise InvalidInputError("All elements must be integers.")

    result = values.copy()

    for i in range(1, len(result)):
        current = result[i]
        j = i - 1

        while j >= 0:
            if metrics:
                metrics.comparisons += 1

            if result[j] <= current:
                break

            result[j + 1] = result[j]
            j -= 1

            if metrics:
                metrics.operations += 1

        result[j + 1] = current

    return result


def dijkstra(
    graph: dict[str, dict[str, float]],
    source: str,
) -> dict[str, float]:
    """
    Calculate shortest paths in a graph with nonnegative edge weights.

    Time: O((V + E) log V) with a binary heap.
    Space: O(V + E).

    Precondition: every edge weight is nonnegative.
    """

    if not isinstance(graph, dict) or source not in graph:
        raise InvalidInputError("Source must exist in the graph.")

    for vertex, edges in graph.items():
        if not isinstance(vertex, str) or not isinstance(edges, dict):
            raise InvalidInputError("Invalid graph representation.")

        for neighbor, weight in edges.items():
            if neighbor not in graph:
                raise InvalidInputError(
                    f"Unknown neighboring vertex: {neighbor}"
                )

            if (
                isinstance(weight, bool)
                or not isinstance(weight, (int, float))
                or weight < 0
                or not float(weight) < float("inf")
            ):
                raise InvalidInputError(
                    "Edge weights must be finite and nonnegative."
                )

    distances = {vertex: float("inf") for vertex in graph}
    distances[source] = 0

    priority_queue = [(0, source)]

    while priority_queue:
        current_distance, current_vertex = heapq.heappop(
            priority_queue
        )

        if current_distance != distances[current_vertex]:
            continue

        for neighbor, weight in graph[current_vertex].items():
            new_distance = current_distance + weight

            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance

                heapq.heappush(
                    priority_queue,
                    (new_distance, neighbor),
                )

    return distances


def measure_algorithm(
    function: Callable,
    *args,
) -> tuple[object, AlgorithmMetrics]:
    metrics = AlgorithmMetrics()

    if args and hasattr(args[0], "__len__"):
        metrics.input_size = len(args[0])

    start = time.perf_counter()

    try:
        result = function(*args, metrics)
    except TypeError:
        result = function(*args)

    metrics.elapsed_seconds = time.perf_counter() - start

    return result, metrics


def verify_binary_search():
    values = [2, 5, 8, 12, 16, 23, 38]

    assert values[binary_search(values, 12)] == 12
    assert binary_search(values, 100) == -1
    assert binary_search([], 10) == -1
    assert binary_search([5], 5) == 0

    try:
        binary_search([5, 2, 8], 2)
        raise AssertionError("Unsorted input was accepted.")
    except InvalidInputError:
        pass


def verify_sorting():
    test_cases = [
        [],
        [1],
        [5, 4, 3, 2, 1],
        [1, 2, 3, 4, 5],
        [4, 4, 2, 2, 1],
        [0, -5, 10, -1],
    ]

    for values in test_cases:
        expected = sorted(values)

        assert merge_sort(values) == expected
        assert insertion_sort(values) == expected

        # Sorting must not modify the original input.
        assert values == values.copy()


def verify_dijkstra():
    graph = {
        "A": {"B": 4, "C": 1},
        "B": {"D": 1},
        "C": {"B": 2, "D": 5},
        "D": {},
        "E": {},
    }

    distances = dijkstra(graph, "A")

    assert distances["A"] == 0
    assert distances["B"] == 3
    assert distances["C"] == 1
    assert distances["D"] == 4
    assert distances["E"] == float("inf")

    try:
        dijkstra(
            {"A": {"B": -1}, "B": {}},
            "A",
        )
        raise AssertionError("Negative weight was accepted.")
    except InvalidInputError:
        pass


class AlgorithmTests(unittest.TestCase):
    def test_binary_search(self):
        verify_binary_search()

    def test_sorting(self):
        verify_sorting()

    def test_dijkstra(self):
        verify_dijkstra()

    def test_empty_input(self):
        self.assertEqual(merge_sort([]), [])
        self.assertEqual(insertion_sort([]), [])

    def test_registry(self):
        registry = AlgorithmRegistry()

        registry.register(
            Algorithm(
                name="merge_sort",
                category=AlgorithmCategory.SORTING,
                time_complexity="O(n log n)",
                space_complexity="O(n)",
                description="Stable divide-and-conquer sorting.",
                function=merge_sort,
            )
        )

        self.assertEqual(
            registry.get("merge_sort").name,
            "merge_sort",
        )


def demonstrate_algorithms():
    registry = AlgorithmRegistry()

    algorithms = [
        Algorithm(
            "binary_search",
            AlgorithmCategory.SEARCHING,
            "O(log n)",
            "O(1)",
            "Search an ordered collection.",
            binary_search,
        ),
        Algorithm(
            "merge_sort",
            AlgorithmCategory.SORTING,
            "O(n log n)",
            "O(n)",
            "Stable divide-and-conquer sorting.",
            merge_sort,
        ),
        Algorithm(
            "insertion_sort",
            AlgorithmCategory.SORTING,
            "O(n^2)",
            "O(1)",
            "Incremental in-place sorting.",
            insertion_sort,
        ),
        Algorithm(
            "dijkstra",
            AlgorithmCategory.GRAPH,
            "O((V+E) log V)",
            "O(V+E)",
            "Shortest paths with nonnegative weights.",
            dijkstra,
        ),
    ]

    for algorithm in algorithms:
        registry.register(algorithm)

    print("\nALGORITHM FUNDAMENTALS")
    print("=" * 65)

    for algorithm in registry.list_algorithms():
        print(algorithm)

    sample = [42, 12, 7, 31, 19, 3, 25]

    sorted_values, sorting_metrics = measure_algorithm(
        merge_sort,
        sample,
    )

    print("\nSorting")
    print("Original:", sample)
    print("Sorted:", sorted_values)
    print("Metrics:", sorting_metrics.report())

    search_metrics = AlgorithmMetrics(input_size=len(sorted_values))

    position = binary_search(
        sorted_values,
        19,
        search_metrics,
    )

    print("\nSearching")
    print("Target:", 19)
    print("Position:", position)
    print("Metrics:", search_metrics.report())

    graph = {
        "A": {"B": 6, "C": 2},
        "B": {"D": 1},
        "C": {"B": 3, "D": 7},
        "D": {},
    }

    print("\nShortest paths")
    print(dijkstra(graph, "A"))

    random.seed(42)
    large_input = [
        random.randint(0, 100000)
        for _ in range(5000)
    ]

    print("\nPerformance experiment")

    for function in (insertion_sort, merge_sort):
        result, metrics = measure_algorithm(
            function,
            large_input,
        )

        assert result == sorted(large_input)

        print(
            function.__name__,
            metrics.report(),
        )


if __name__ == "__main__":
    unittest.main(
        argv=["algorithm_fundamentals"],
        exit=False,
    )

    demonstrate_algorithms()
