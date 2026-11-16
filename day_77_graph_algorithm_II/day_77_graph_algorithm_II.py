#!/usr/bin/env python3
"""
Graph Algorithms II: Dijkstra's Shortest Path Algorithm

Features:
- Weighted directed and undirected graphs
- Adjacency-list representation
- Min-priority queue using heapq
- Dijkstra's shortest path algorithm
- Path reconstruction
- Single-source shortest paths
- Multi-source shortest paths
- Early termination for destination queries
- Negative-weight validation
- Unreachable vertices
- Zero-weight edges
- Graph statistics and performance analysis
- JSON file export
- Automated correctness tests

Run:
    python dijkstra.py
"""

from __future__ import annotations

import heapq
import json
import math
import unittest

from dataclasses import dataclass
from pathlib import Path
from typing import Hashable, Optional


Vertex = Hashable


class GraphError(Exception):
    """Base exception for graph operations."""


class NegativeWeightError(GraphError):
    """Raised when Dijkstra receives a negative edge weight."""


class UnknownVertexError(GraphError):
    """Raised when a requested vertex does not exist."""


@dataclass(frozen=True)
class Edge:
    source: Vertex
    destination: Vertex
    weight: float


@dataclass
class ShortestPathResult:
    source: Vertex
    distances: dict[Vertex, float]
    predecessors: dict[Vertex, Optional[Vertex]]
    settled_vertices: list[Vertex]
    examined_edges: int
    relaxations: int

    def path_to(self, destination: Vertex) -> Optional[list[Vertex]]:
        if destination not in self.distances:
            raise UnknownVertexError(
                f"Unknown destination: {destination}"
            )

        if math.isinf(self.distances[destination]):
            return None

        path = []
        current = destination

        while current is not None:
            path.append(current)

            if current == self.source:
                break

            current = self.predecessors[current]

        if not path or path[-1] != self.source:
            return None

        return list(reversed(path))

    def distance_to(self, destination: Vertex) -> float:
        if destination not in self.distances:
            raise UnknownVertexError(destination)

        return self.distances[destination]

    def formatted_distance(self, destination: Vertex) -> str:
        distance = self.distance_to(destination)

        return "UNREACHABLE" if math.isinf(distance) else str(distance)


class WeightedGraph:
    """
    Weighted graph implemented using adjacency lists.

    The adjacency list provides efficient access to outgoing edges.

    For V vertices and E edges:
        Storage: O(V + E)
        Neighbor traversal: O(degree(vertex))
    """

    def __init__(self, directed: bool = True):
        self.directed = directed
        self.adjacency: dict[Vertex, list[tuple[Vertex, float]]] = {}
        self.edges: list[Edge] = {}

    def add_vertex(self, vertex: Vertex) -> None:
        try:
            hash(vertex)
        except TypeError as exc:
            raise GraphError("Vertices must be hashable") from exc

        self.adjacency.setdefault(vertex, [])

    def add_edge(
        self,
        source: Vertex,
        destination: Vertex,
        weight: float
    ) -> None:
        if isinstance(weight, bool):
            raise GraphError("Boolean values are not valid weights")

        if not isinstance(weight, (int, float)):
            raise GraphError("Edge weight must be numeric")

        weight = float(weight)

        if not math.isfinite(weight):
            raise GraphError("Edge weight must be finite")

        if weight < 0:
            raise NegativeWeightError(
                "Dijkstra's algorithm requires nonnegative weights"
            )

        self.add_vertex(source)
        self.add_vertex(destination)

        self.adjacency[source].append((destination, weight))

        if not self.directed:
            self.adjacency[destination].append((source, weight))

    def vertices(self) -> list[Vertex]:
        return list(self.adjacency)

    def vertex_count(self) -> int:
        return len(self.adjacency)

    def edge_count(self) -> int:
        return sum(map(len, self.adjacency.values()))

    def shortest_paths(
        self,
        source: Vertex,
        target: Optional[Vertex] = None
    ) -> ShortestPathResult:
        """
        Computes shortest distances from source.

        A min-heap selects the unsettled vertex with the
        smallest tentative distance.

        Stale heap entries are ignored because a vertex can
        receive multiple improved distance estimates.
        """

        if source not in self.adjacency:
            raise UnknownVertexError(source)

        if target is not None and target not in self.adjacency:
            raise UnknownVertexError(target)

        distances = {
            vertex: math.inf
            for vertex in self.adjacency
        }

        predecessors = {
            vertex: None
            for vertex in self.adjacency
        }

        distances[source] = 0.0

        # Heap entries contain (distance, insertion sequence, vertex).
        # The sequence prevents comparison of arbitrary vertex objects.
        sequence = 0
        priority_queue = [(0.0, sequence, source)]

        settled = []
        settled_set = set()

        examined_edges = 0
        relaxations = 0

        while priority_queue:
            current_distance, _, current = heapq.heappop(
                priority_queue
            )

            if current in settled_set:
                continue

            if current_distance != distances[current]:
                continue

            settled_set.add(current)
            settled.append(current)

            if target is not None and current == target:
                break

            for neighbor, weight in self.adjacency[current]:
                examined_edges += 1

                if neighbor in settled_set:
                    continue

                candidate = current_distance + weight

                if candidate < distances[neighbor]:
                    distances[neighbor] = candidate
                    predecessors[neighbor] = current

                    sequence += 1

                    heapq.heappush(
                        priority_queue,
                        (candidate, sequence, neighbor)
                    )

                    relaxations += 1

        return ShortestPathResult(
            source=source,
            distances=distances,
            predecessors=predecessors,
            settled_vertices=settled,
            examined_edges=examined_edges,
            relaxations=relaxations
        )

    def multi_source_shortest_paths(
        self,
        sources: list[Vertex]
    ) -> ShortestPathResult:
        """
        Computes distance from the nearest source.

        This is equivalent to connecting a virtual source
        to every supplied source using zero-weight edges.
        """

        if not sources:
            raise GraphError("At least one source is required")

        if len(set(sources)) != len(sources):
            raise GraphError("Duplicate sources are not allowed")

        for source in sources:
            if source not in self.adjacency:
                raise UnknownVertexError(source)

        distances = {
            vertex: math.inf
            for vertex in self.adjacency
        }

        predecessors = {
            vertex: None
            for vertex in self.adjacency
        }

        queue = []
        sequence = 0

        for source in sources:
            distances[source] = 0.0
            heapq.heappush(queue, (0.0, sequence, source))
            sequence += 1

        settled = []
        settled_set = set()
        examined_edges = 0
        relaxations = 0

        while queue:
            distance, _, current = heapq.heappop(queue)

            if current in settled_set:
                continue

            if distance != distances[current]:
                continue

            settled_set.add(current)
            settled.append(current)

            for neighbor, weight in self.adjacency[current]:
                examined_edges += 1

                if neighbor in settled_set:
                    continue

                candidate = distance + weight

                if candidate < distances[neighbor]:
                    distances[neighbor] = candidate
                    predecessors[neighbor] = current

                    heapq.heappush(
                        queue,
                        (candidate, sequence, neighbor)
                    )

                    sequence += 1
                    relaxations += 1

        # Multi-source reconstruction uses any one of the sources.
        return ShortestPathResult(
            source=sources[0],
            distances=distances,
            predecessors=predecessors,
            settled_vertices=settled,
            examined_edges=examined_edges,
            relaxations=relaxations
        )

    def export_json(self, filename: str) -> None:
        data = {
            "directed": self.directed,
            "vertices": [
                {
                    "id": vertex,
                    "edges": [
                        {
                            "destination": neighbor,
                            "weight": weight
                        }
                        for neighbor, weight in neighbors
                    ]
                }
                for vertex, neighbors in self.adjacency.items()
            ]
        }

        path = Path(filename)

        # Restrict exports to a single local filename.
        if path.name != filename or path.name in {"", ".", ".."}:
            raise GraphError("Use a local filename without directory paths")

        path.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8"
        )


def build_transport_network() -> WeightedGraph:
    """
    Construct a directed transportation network.

    Edge weights represent travel time in minutes.
    """

    graph = WeightedGraph(directed=True)

    routes = [
        ("Lucknow", "Kanpur", 90),
        ("Lucknow", "Ayodhya", 135),
        ("Lucknow", "Varanasi", 300),
        ("Kanpur", "Agra", 210),
        ("Kanpur", "Prayagraj", 180),
        ("Ayodhya", "Gorakhpur", 150),
        ("Ayodhya", "Varanasi", 190),
        ("Gorakhpur", "Patna", 240),
        ("Varanasi", "Patna", 200),
        ("Varanasi", "Prayagraj", 130),
        ("Prayagraj", "Patna", 260),
        ("Agra", "Delhi", 150),
        ("Prayagraj", "Delhi", 500),
        ("Patna", "Delhi", 600),
        ("Lucknow", "Lucknow_Express", 0),
        ("Lucknow_Express", "Kanpur", 70)
    ]

    for source, destination, weight in routes:
        graph.add_edge(source, destination, weight)

    graph.add_vertex("Mumbai")
    graph.add_vertex("Chennai")

    return graph


def display_result(
    result: ShortestPathResult,
    destination: Vertex
) -> None:
    path = result.path_to(destination)
    distance = result.distance_to(destination)

    print(f"\nDestination: {destination}")

    if path is None:
        print("Route: Unreachable")
        return

    print("Route:", " -> ".join(map(str, path)))
    print(f"Shortest distance: {distance:g} minutes")


def demonstrate_dijkstra() -> None:
    graph = build_transport_network()

    print("=" * 65)
    print("DIJKSTRA SHORTEST PATH ENGINE")
    print("=" * 65)

    print(f"Vertices: {graph.vertex_count()}")
    print(f"Directed edges: {graph.edge_count()}")

    source = "Lucknow"
    destinations = [
        "Delhi",
        "Patna",
        "Gorakhpur",
        "Mumbai"
    ]

    result = graph.shortest_paths(source)

    print(f"\nSingle-source shortest paths from {source}")

    for destination in destinations:
        display_result(result, destination)

    print("\nAlgorithm diagnostics")
    print("Settled vertices:", len(result.settled_vertices))
    print("Examined edges:", result.examined_edges)
    print("Successful relaxations:", result.relaxations)

    print("\nEarly destination termination")

    optimized = graph.shortest_paths(
        source,
        target="Delhi"
    )

    display_result(optimized, "Delhi")

    print("\nMulti-source shortest paths")

    multi = graph.multi_source_shortest_paths(
        ["Lucknow", "Patna"]
    )

    for vertex in graph.vertices():
        print(
            f"{vertex:20} "
            f"{multi.formatted_distance(vertex)}"
        )

    print("\nGraph export")

    graph.export_json("dijkstra_network.json")
    print("Exported dijkstra_network.json")


class DijkstraTests(unittest.TestCase):

    def setUp(self):
        self.graph = WeightedGraph(directed=True)

        self.graph.add_edge("A", "B", 4)
        self.graph.add_edge("A", "C", 1)
        self.graph.add_edge("C", "B", 2)
        self.graph.add_edge("B", "D", 1)
        self.graph.add_edge("C", "D", 5)
        self.graph.add_vertex("Z")

    def test_shortest_distance(self):
        result = self.graph.shortest_paths("A")

        self.assertEqual(result.distance_to("D"), 4)

    def test_shortest_path(self):
        result = self.graph.shortest_paths("A")

        self.assertEqual(
            result.path_to("D"),
            ["A", "C", "B", "D"]
        )

    def test_unreachable_vertex(self):
        result = self.graph.shortest_paths("A")

        self.assertIsNone(result.path_to("Z"))
        self.assertTrue(math.isinf(result.distance_to("Z")))

    def test_zero_weight(self):
        graph = WeightedGraph()
        graph.add_edge("A", "B", 0)

        result = graph.shortest_paths("A")

        self.assertEqual(result.distance_to("B"), 0)

    def test_negative_weight(self):
        with self.assertRaises(NegativeWeightError):
            self.graph.add_edge("A", "Z", -1)

    def test_unknown_vertex(self):
        with self.assertRaises(UnknownVertexError):
            self.graph.shortest_paths("UNKNOWN")

    def test_undirected_graph(self):
        graph = WeightedGraph(directed=False)
        graph.add_edge("A", "B", 7)

        self.assertEqual(
            graph.shortest_paths("B").distance_to("A"),
            7
        )

    def test_multi_source(self):
        result = self.graph.multi_source_shortest_paths(
            ["A", "D"]
        )

        self.assertEqual(result.distance_to("B"), 2)

    def test_empty_sources(self):
        with self.assertRaises(GraphError):
            self.graph.multi_source_shortest_paths([])

    def test_nonfinite_weight(self):
        with self.assertRaises(GraphError):
            self.graph.add_edge("A", "B", math.inf)


def print_complexity() -> None:
    print("\nComplexity analysis")
    print("Graph storage: O(V + E)")
    print("Heap-based Dijkstra: O((V + E) log V)")
    print("Path reconstruction: O(V) worst case")
    print("Single-source result storage: O(V)")
    print("Multi-source execution: O((V + E) log V)")
    print("Negative weights: Unsupported")


if __name__ == "__main__":
    demonstrate_dijkstra()
    print_complexity()

    print("\nRunning automated tests")

    unittest.main(argv=["dijkstra.py"], exit=False, verbosity=2)
