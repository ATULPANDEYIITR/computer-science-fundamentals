#!/usr/bin/env python3
"""
Graph Traversal: Breadth First Search, Depth First Search, and Applications.

Demonstrates:
- Directed and undirected adjacency-list graphs
- Breadth First Search (BFS)
- Depth First Search (DFS) without recursion
- Shortest paths in unweighted graphs
- Connected components
- Topological sorting and cycle detection
- Input validation and traversal limits

Run: python graph_traversal.py
"""

from __future__ import annotations

import heapq
from collections import deque
from dataclasses import dataclass
from typing import Iterator


class GraphError(Exception):
    """Base exception for graph-related errors."""


class VertexNotFoundError(GraphError):
    """Raised when an operation references an unknown vertex."""


class TraversalLimitError(GraphError):
    """Raised when a traversal exceeds its configured vertex limit."""


class CycleDetectedError(GraphError):
    """Raised when a directed graph contains a cycle."""


@dataclass(frozen=True)
class TraversalResult:
    """Stores the vertices discovered by a traversal and its traversal tree."""

    start: str
    order: tuple[str, ...]
    parent: dict[str, str | None]
    depth: dict[str, int]

    def path_to(self, target: str) -> list[str] | None:
        """Reconstruct a path from the starting vertex to a discovered vertex."""
        if target not in self.parent:
            return None

        path: list[str] = []
        current: str | None = target

        while current is not None:
            path.append(current)
            current = self.parent[current]

        path.reverse()
        return path


class Graph:
    """Adjacency-list graph supporting directed and undirected edges."""

    MAX_VERTEX_ID_LENGTH = 128

    def __init__(self, directed: bool = False) -> None:
        self.directed = directed
        self._adjacency: dict[str, set[str]] = {}

    @staticmethod
    def _validate_vertex_id(vertex: str) -> None:
        if not isinstance(vertex, str):
            raise TypeError("Vertex identifiers must be strings.")

        if not vertex or vertex != vertex.strip():
            raise ValueError("Vertex identifiers cannot be empty or padded.")

        if len(vertex) > Graph.MAX_VERTEX_ID_LENGTH:
            raise ValueError("Vertex identifier exceeds the maximum length.")

    def add_vertex(self, vertex: str) -> None:
        self._validate_vertex_id(vertex)
        self._adjacency.setdefault(vertex, set())

    def add_edge(self, source: str, target: str) -> None:
        """Add an edge, creating its endpoints when necessary."""
        self._validate_vertex_id(source)
        self._validate_vertex_id(target)

        self.add_vertex(source)
        self.add_vertex(target)

        self._adjacency[source].add(target)

        if not self.directed:
            self._adjacency[target].add(source)

    def has_vertex(self, vertex: str) -> bool:
        return vertex in self._adjacency

    def vertices(self) -> tuple[str, ...]:
        return tuple(sorted(self._adjacency))

    def neighbors(self, vertex: str) -> tuple[str, ...]:
        if vertex not in self._adjacency:
            raise VertexNotFoundError(f"Unknown vertex: {vertex}")

        return tuple(sorted(self._adjacency[vertex]))

    def _validate_start(self, start: str) -> None:
        if start not in self._adjacency:
            raise VertexNotFoundError(f"Starting vertex does not exist: {start}")

    @staticmethod
    def _validate_limit(max_visited: int) -> None:
        if isinstance(max_visited, bool) or not isinstance(max_visited, int):
            raise TypeError("max_visited must be an integer.")

        if max_visited < 1:
            raise ValueError("max_visited must be at least 1.")

    def breadth_first_search(
        self,
        start: str,
        max_visited: int = 100_000,
    ) -> TraversalResult:
        """
        Visit vertices level by level.

        A vertex is marked as discovered when it enters the queue.
        This prevents duplicate queue entries and produces shortest-hop
        distances in an unweighted graph.
        """
        self._validate_start(start)
        self._validate_limit(max_visited)

        queue: deque[str] = deque([start])
        parent: dict[str, str | None] = {start: None}
        depth: dict[str, int] = {start: 0}
        order: list[str] = []

        while queue:
            current = queue.popleft()
            order.append(current)

            for neighbor in self.neighbors(current):
                if neighbor in parent:
                    continue

                if len(parent) >= max_visited:
                    raise TraversalLimitError(
                        f"BFS exceeded the limit of {max_visited} vertices."
                    )

                parent[neighbor] = current
                depth[neighbor] = depth[current] + 1
                queue.append(neighbor)

        return TraversalResult(
            start=start,
            order=tuple(order),
            parent=parent,
            depth=depth,
        )

    def depth_first_search(
        self,
        start: str,
        max_visited: int = 100_000,
    ) -> TraversalResult:
        """
        Explore one branch before returning to alternative branches.

        An explicit stack of neighbor iterators reproduces recursive DFS
        order without depending on Python's recursion limit.
        """
        self._validate_start(start)
        self._validate_limit(max_visited)

        parent: dict[str, str | None] = {start: None}
        depth: dict[str, int] = {start: 0}
        order: list[str] = [start]

        stack: list[tuple[str, Iterator[str]]] = [
            (start, iter(self.neighbors(start)))
        ]

        while stack:
            current, neighbor_iterator = stack[-1]

            try:
                neighbor = next(neighbor_iterator)
            except StopIteration:
                stack.pop()
                continue

            if neighbor in parent:
                continue

            if len(parent) >= max_visited:
                raise TraversalLimitError(
                    f"DFS exceeded the limit of {max_visited} vertices."
                )

            parent[neighbor] = current
            depth[neighbor] = depth[current] + 1
            order.append(neighbor)

            stack.append((neighbor, iter(self.neighbors(neighbor))))

        return TraversalResult(
            start=start,
            order=tuple(order),
            parent=parent,
            depth=depth,
        )

    def shortest_path(self, start: str, target: str) -> list[str] | None:
        """
        Return a path with the minimum number of edges.

        BFS is appropriate because this graph is unweighted.
        A missing target is an error; an unreachable target returns None.
        """
        self._validate_start(start)

        if target not in self._adjacency:
            raise VertexNotFoundError(f"Unknown target vertex: {target}")

        result = self.breadth_first_search(start)
        return result.path_to(target)

    def connected_components(self) -> list[list[str]]:
        """Find connected components in an undirected graph."""
        if self.directed:
            raise GraphError(
                "Connected components require an undirected graph. "
                "Directed graphs need a defined component convention."
            )

        remaining = set(self._adjacency)
        components: list[list[str]] = []

        while remaining:
            start = min(remaining)
            result = self.breadth_first_search(start)
            component = list(result.order)

            components.append(component)
            remaining.difference_update(component)

        return components

    def topological_order(self) -> list[str]:
        """
        Return a topological ordering using Kahn's algorithm.

        A topological order exists only when the directed graph is acyclic.
        A min-heap makes the result deterministic when several vertices
        are eligible at the same time.
        """
        if not self.directed:
            raise GraphError("Topological sorting requires a directed graph.")

        indegree = {vertex: 0 for vertex in self._adjacency}

        for source in self._adjacency:
            for target in self._adjacency[source]:
                indegree[target] += 1

        ready = [
            vertex
            for vertex, degree in indegree.items()
            if degree == 0
        ]
        heapq.heapify(ready)

        result: list[str] = []

        while ready:
            current = heapq.heappop(ready)
            result.append(current)

            for neighbor in self.neighbors(current):
                indegree[neighbor] -= 1

                if indegree[neighbor] == 0:
                    heapq.heappush(ready, neighbor)

        if len(result) != len(self._adjacency):
            blocked = sorted(
                vertex
                for vertex, degree in indegree.items()
                if degree > 0
            )
            raise CycleDetectedError(
                f"Topological ordering is impossible. Cycle-related vertices: "
                f"{blocked}"
            )

        return result


def print_traversal(name: str, result: TraversalResult) -> None:
    print(f"\n{name}")
    print("Visit order:", " -> ".join(result.order))
    print("Depths:", result.depth)
    print("Parents:", result.parent)


def demonstrate_undirected_network() -> None:
    """
    Model an undirected transport network.

    BFS identifies minimum-hop routes.
    DFS inspects connected areas.
    Connected components identify isolated network sections.
    """
    network = Graph(directed=False)

    roads = [
        ("Dispatch", "West Junction"),
        ("Dispatch", "East Junction"),
        ("West Junction", "West Shelter"),
        ("West Junction", "Central Bridge"),
        ("East Junction", "Central Bridge"),
        ("Central Bridge", "South Shelter"),
        ("South Shelter", "Supply Depot"),
        ("East Junction", "Remote Outpost"),
    ]

    for source, target in roads:
        network.add_edge(source, target)

    bfs_result = network.breadth_first_search("Dispatch")
    dfs_result = network.depth_first_search("Dispatch")

    print("TRANSPORT NETWORK")
    print_traversal("Breadth First Search", bfs_result)
    print_traversal("Depth First Search", dfs_result)

    route = network.shortest_path("Dispatch", "South Shelter")
    print("\nShortest route to South Shelter:", route)

    components = network.connected_components()
    print("\nConnected components:", components)

    assert route is not None
    assert len(route) == 4
    assert len(components) == 1
    assert bfs_result.depth["South Shelter"] == 3

    print("\nTransport network checks passed.")


def demonstrate_directed_dependencies() -> None:
    """
    Model task dependencies.

    An edge A -> B means that A must be completed before B.
    Topological ordering identifies a valid execution sequence.
    """
    dependencies = Graph(directed=True)

    tasks = [
        ("Extract Data", "Validate Data"),
        ("Validate Data", "Analyze Data"),
        ("Analyze Data", "Generate Report"),
        ("Extract Data", "Check Data Quality"),
        ("Check Data Quality", "Analyze Data"),
    ]

    for source, target in tasks:
        dependencies.add_edge(source, target)

    print("\nDIRECTED TASK DEPENDENCIES")
    print("BFS from Extract Data:")
    print(
        dependencies.breadth_first_search("Extract Data").order
    )

    print("DFS from Extract Data:")
    print(
        dependencies.depth_first_search("Extract Data").order
    )

    print("Valid execution order:")
    print(" -> ".join(dependencies.topological_order()))

    assert dependencies.has_vertex("Generate Report")

    # A cycle makes a valid topological execution order impossible.
    dependencies.add_edge("Generate Report", "Extract Data")

    try:
        dependencies.topological_order()
    except CycleDetectedError as error:
        print("\nExpected cycle detection:", error)
    else:
        raise AssertionError("A directed cycle was not detected.")


def demonstrate_edge_cases() -> None:
    empty = Graph()

    try:
        empty.breadth_first_search("missing")
    except VertexNotFoundError:
        print("\nUnknown starting vertex handled correctly.")

    isolated = Graph()
    isolated.add_vertex("Only Vertex")

    result = isolated.breadth_first_search("Only Vertex")
    assert result.order == ("Only Vertex",)
    assert result.path_to("Only Vertex") == ["Only Vertex"]
    assert result.path_to("missing") is None

    try:
        isolated.breadth_first_search("Only Vertex", max_visited=0)
    except ValueError:
        print("Invalid traversal limit handled correctly.")

    try:
        isolated.add_vertex(" padded ")
    except ValueError:
        print("Invalid vertex identifier handled correctly.")


def main() -> None:
    demonstrate_undirected_network()
    demonstrate_directed_dependencies()
    demonstrate_edge_cases()

    print("\nAll graph traversal demonstrations completed successfully.")


if __name__ == "__main__":
    main()
