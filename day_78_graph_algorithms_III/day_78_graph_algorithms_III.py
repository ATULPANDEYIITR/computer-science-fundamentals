#!/usr/bin/env python3
"""
Graph Algorithms III: Bellman-Ford, Floyd-Warshall, and Negative Cycles.

Features:
- Directed weighted graph representation.
- Bellman-Ford single-source shortest paths.
- Negative-cycle detection and affected-vertex identification.
- Negative-cycle witness reconstruction.
- Floyd-Warshall all-pairs shortest paths.
- Path reconstruction.
- Cross-validation between algorithms.
- Disconnected graph handling.
- Input validation and complexity reporting.

Run:
    python graph_algorithms_iii.py
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import inf
from typing import Optional


class GraphError(Exception):
    """Base exception for graph-related errors."""


class NegativeCycleError(GraphError):
    """Raised when a finite shortest path cannot be established."""


class PathStatus(Enum):
    FINITE = "finite"
    UNREACHABLE = "unreachable"
    NEGATIVE_INFINITY = "negative_infinity"


@dataclass(frozen=True)
class Edge:
    source: int
    destination: int
    weight: float


@dataclass
class BellmanFordResult:
    distances: list[float]
    predecessors: list[Optional[int]]
    negative_cycle_vertices: set[int]
    negative_cycle_witness: list[int]

    def status(self, vertex: int) -> PathStatus:
        if vertex in self.negative_cycle_vertices:
            return PathStatus.NEGATIVE_INFINITY
        if self.distances[vertex] == inf:
            return PathStatus.UNREACHABLE
        return PathStatus.FINITE


@dataclass
class FloydWarshallResult:
    distances: list[list[float]]
    next_vertices: list[list[Optional[int]]]
    negative_cycle_vertices: set[int]

    def status(self, source: int, destination: int) -> PathStatus:
        if any(
            self.distances[source][cycle] != inf
            and self.distances[cycle][cycle] < 0
            and self.distances[cycle][destination] != inf
            for cycle in self.negative_cycle_vertices
        ):
            return PathStatus.NEGATIVE_INFINITY

        if self.distances[source][destination] == inf:
            return PathStatus.UNREACHABLE

        return PathStatus.FINITE


class WeightedDirectedGraph:
    """Directed weighted graph using an edge list and adjacency list."""

    def __init__(self, vertex_count: int):
        if not isinstance(vertex_count, int) or isinstance(vertex_count, bool):
            raise GraphError("Vertex count must be an integer.")

        if vertex_count <= 0:
            raise GraphError("Vertex count must be positive.")

        self.vertex_count = vertex_count
        self.edges: list[Edge] = []
        self.adjacency: list[list[Edge]] = [
            [] for _ in range(vertex_count)
        ]

    def _validate_vertex(self, vertex: int) -> None:
        if (
            not isinstance(vertex, int)
            or isinstance(vertex, bool)
            or not 0 <= vertex < self.vertex_count
        ):
            raise GraphError(f"Invalid vertex: {vertex}")

    def add_edge(self, source: int, destination: int, weight: float) -> None:
        self._validate_vertex(source)
        self._validate_vertex(destination)

        if not isinstance(weight, (int, float)) or isinstance(weight, bool):
            raise GraphError("Edge weight must be numeric.")

        if weight != weight or weight in (inf, -inf):
            raise GraphError("Edge weight must be finite.")

        edge = Edge(source, destination, float(weight))
        self.edges.append(edge)
        self.adjacency[source].append(edge)

    def bellman_ford(self, source: int) -> BellmanFordResult:
        """
        Single-source shortest paths.

        Complexity: O(VE).
        Identifies all vertices reachable from a reachable negative cycle.
        """
        self._validate_vertex(source)

        n = self.vertex_count
        distances = [inf] * n
        predecessors: list[Optional[int]] = [None] * n
        distances[source] = 0.0

        # Relax all edges at most V-1 times.
        for _ in range(n - 1):
            changed = False

            for edge in self.edges:
                if distances[edge.source] == inf:
                    continue

                candidate = distances[edge.source] + edge.weight

                if candidate < distances[edge.destination]:
                    distances[edge.destination] = candidate
                    predecessors[edge.destination] = edge.source
                    changed = True

            if not changed:
                break

        # A further relaxation indicates a reachable negative cycle.
        affected = set()
        witness_vertex = None

        for edge in self.edges:
            if distances[edge.source] == inf:
                continue

            candidate = distances[edge.source] + edge.weight

            if candidate < distances[edge.destination]:
                distances[edge.destination] = candidate
                predecessors[edge.destination] = edge.source
                affected.add(edge.destination)
                witness_vertex = edge.destination

        # Propagate negative-infinity status to every reachable vertex.
        stack = list(affected)

        while stack:
            vertex = stack.pop()

            for edge in self.adjacency[vertex]:
                if edge.destination not in affected:
                    affected.add(edge.destination)
                    stack.append(edge.destination)

        witness = self._reconstruct_negative_cycle(
            witness_vertex, predecessors
        )

        return BellmanFordResult(
            distances,
            predecessors,
            affected,
            witness
        )

    def _reconstruct_negative_cycle(
        self,
        vertex: Optional[int],
        predecessors: list[Optional[int]]
    ) -> list[int]:
        if vertex is None:
            return []

        current = vertex

        # Move V times to enter the cycle.
        for _ in range(self.vertex_count):
            previous = predecessors[current]
            if previous is None:
                return []
            current = previous

        cycle = [current]
        next_vertex = predecessors[current]

        while next_vertex is not None and next_vertex != current:
            if len(cycle) > self.vertex_count:
                return []
            cycle.append(next_vertex)
            next_vertex = predecessors[next_vertex]

        if next_vertex is None:
            return []

        cycle.append(current)
        cycle.reverse()
        return cycle

    def reconstruct_bellman_path(
        self,
        result: BellmanFordResult,
        source: int,
        destination: int
    ) -> list[int]:
        self._validate_vertex(source)
        self._validate_vertex(destination)

        status = result.status(destination)

        if status == PathStatus.NEGATIVE_INFINITY:
            raise NegativeCycleError(
                "Shortest path is undefined due to a reachable negative cycle."
            )

        if status == PathStatus.UNREACHABLE:
            return []

        path = []
        current: Optional[int] = destination

        for _ in range(self.vertex_count + 1):
            if current is None:
                break

            path.append(current)

            if current == source:
                path.reverse()
                return path

            current = result.predecessors[current]

        raise GraphError("Predecessor chain is invalid.")

    def floyd_warshall(self) -> FloydWarshallResult:
        """
        All-pairs shortest paths.

        Complexity: O(V^3) time and O(V^2) space.
        Negative cycles are identified using diagonal entries.
        """
        n = self.vertex_count

        distances = [[inf] * n for _ in range(n)]
        next_vertices: list[list[Optional[int]]] = [
            [None] * n for _ in range(n)
        ]

        for vertex in range(n):
            distances[vertex][vertex] = 0.0
            next_vertices[vertex][vertex] = vertex

        # Preserve the minimum weight among parallel edges.
        for edge in self.edges:
            if edge.weight < distances[edge.source][edge.destination]:
                distances[edge.source][edge.destination] = edge.weight
                next_vertices[edge.source][edge.destination] = (
                    edge.destination
                )

        # Consider every vertex as an intermediate vertex.
        for intermediate in range(n):
            for source in range(n):
                if distances[source][intermediate] == inf:
                    continue

                for destination in range(n):
                    if distances[intermediate][destination] == inf:
                        continue

                    candidate = (
                        distances[source][intermediate]
                        + distances[intermediate][destination]
                    )

                    if candidate < distances[source][destination]:
                        distances[source][destination] = candidate
                        next_vertices[source][destination] = (
                            next_vertices[source][intermediate]
                        )

        negative_cycles = {
            vertex
            for vertex in range(n)
            if distances[vertex][vertex] < 0
        }

        return FloydWarshallResult(
            distances,
            next_vertices,
            negative_cycles
        )

    def reconstruct_floyd_path(
        self,
        result: FloydWarshallResult,
        source: int,
        destination: int
    ) -> list[int]:
        self._validate_vertex(source)
        self._validate_vertex(destination)

        status = result.status(source, destination)

        if status == PathStatus.NEGATIVE_INFINITY:
            raise NegativeCycleError(
                "Path is undefined because a negative cycle is reachable."
            )

        if status == PathStatus.UNREACHABLE:
            return []

        if source == destination:
            return [source]

        path = [source]
        current = source

        for _ in range(self.vertex_count):
            next_vertex = result.next_vertices[current][destination]

            if next_vertex is None:
                return []

            current = next_vertex
            path.append(current)

            if current == destination:
                return path

        raise GraphError("Path reconstruction exceeded vertex limit.")


def demonstrate_bellman_ford() -> None:
    print("\n=== BELLMAN-FORD ===")

    graph = WeightedDirectedGraph(6)

    edges = [
        (0, 1, 4),
        (0, 2, 5),
        (1, 2, -2),
        (1, 3, 6),
        (2, 3, 3),
        (3, 4, 2),
        (4, 5, 1),
    ]

    for edge in edges:
        graph.add_edge(*edge)

    result = graph.bellman_ford(0)

    for vertex, distance in enumerate(result.distances):
        print(
            f"Vertex {vertex}: "
            f"distance={distance}, status={result.status(vertex).value}"
        )

    print(
        "Shortest path 0 -> 5:",
        graph.reconstruct_bellman_path(result, 0, 5)
    )

    assert result.distances[5] == 8


def demonstrate_negative_cycle() -> None:
    print("\n=== NEGATIVE CYCLE DETECTION ===")

    graph = WeightedDirectedGraph(6)

    edges = [
        (0, 1, 2),
        (1, 2, 2),
        (2, 3, -5),
        (3, 1, 1),
        (3, 4, 4),
        (0, 5, 10),
    ]

    for edge in edges:
        graph.add_edge(*edge)

    result = graph.bellman_ford(0)

    print("Negative-cycle witness:", result.negative_cycle_witness)
    print("Affected vertices:", sorted(result.negative_cycle_vertices))

    assert 1 in result.negative_cycle_vertices
    assert 2 in result.negative_cycle_vertices
    assert 3 in result.negative_cycle_vertices
    assert 4 in result.negative_cycle_vertices
    assert 5 not in result.negative_cycle_vertices


def demonstrate_floyd_warshall() -> None:
    print("\n=== FLOYD-WARSHALL ===")

    graph = WeightedDirectedGraph(5)

    edges = [
        (0, 1, 3),
        (0, 2, 10),
        (1, 2, -2),
        (1, 3, 7),
        (2, 3, 2),
        (3, 4, 1),
        (4, 1, 8),
    ]

    for edge in edges:
        graph.add_edge(*edge)

    result = graph.floyd_warshall()

    print("All-pairs distance matrix:")

    for row in result.distances:
        print([
            "INF" if value == inf else round(value, 2)
            for value in row
        ])

    print(
        "Shortest path 0 -> 4:",
        graph.reconstruct_floyd_path(result, 0, 4)
    )

    assert result.distances[0][4] == 4
    assert not result.negative_cycle_vertices


def demonstrate_disconnected_graph() -> None:
    print("\n=== DISCONNECTED GRAPH ===")

    graph = WeightedDirectedGraph(4)
    graph.add_edge(0, 1, 7)
    graph.add_edge(2, 3, -2)

    bellman = graph.bellman_ford(0)
    floyd = graph.floyd_warshall()

    print("Bellman-Ford distance to vertex 3:", bellman.distances[3])
    print("Floyd-Warshall distance 0 -> 3:", floyd.distances[0][3])

    assert bellman.status(3) == PathStatus.UNREACHABLE
    assert floyd.status(0, 3) == PathStatus.UNREACHABLE


def demonstrate_cross_validation() -> None:
    print("\n=== CROSS-VALIDATION ===")

    graph = WeightedDirectedGraph(5)

    edges = [
        (0, 1, 6),
        (0, 2, 7),
        (1, 2, 8),
        (1, 3, 5),
        (1, 4, -4),
        (2, 3, -3),
        (2, 4, 9),
        (3, 1, -2),
        (4, 0, 2),
        (4, 3, 7),
    ]

    for edge in edges:
        graph.add_edge(*edge)

    floyd = graph.floyd_warshall()

    for source in range(graph.vertex_count):
        bellman = graph.bellman_ford(source)

        for destination in range(graph.vertex_count):
            if bellman.status(destination) == PathStatus.FINITE:
                assert floyd.status(source, destination) == PathStatus.FINITE
                assert (
                    bellman.distances[destination]
                    == floyd.distances[source][destination]
                )

    print("Bellman-Ford and Floyd-Warshall results agree.")


def demonstrate_validation() -> None:
    print("\n=== INPUT VALIDATION ===")

    graph = WeightedDirectedGraph(3)

    invalid_inputs = [
        (-1, 1, 5),
        (0, 3, 2),
        (0, 1, float("nan")),
        (0, 1, float("inf")),
    ]

    for edge in invalid_inputs:
        try:
            graph.add_edge(*edge)
        except GraphError as error:
            print("Rejected:", error)


def main() -> None:
    print("GRAPH ALGORITHMS III")
    print("Bellman-Ford | Floyd-Warshall | Negative Cycles")

    demonstrate_bellman_ford()
    demonstrate_negative_cycle()
    demonstrate_floyd_warshall()
    demonstrate_disconnected_graph()
    demonstrate_cross_validation()
    demonstrate_validation()

    print("\nAll assertions passed.")


if __name__ == "__main__":
    main()
