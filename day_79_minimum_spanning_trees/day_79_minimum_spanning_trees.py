from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import heapq
import math
import random


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    weight: float

    def __post_init__(self):
        if not self.source or not self.target:
            raise ValueError("Vertex names cannot be empty.")
        if self.source == self.target:
            raise ValueError("Self-loops are not allowed.")
        if not math.isfinite(self.weight):
            raise ValueError("Edge weight must be finite.")


class DisjointSet:
    """Union-Find with path compression and union by rank."""

    def __init__(self, vertices: Iterable[str]):
        self.parent = {v: v for v in vertices}
        self.rank = {v: 0 for v in vertices}
        self.components = len(self.parent)

    def find(self, vertex: str) -> str:
        if vertex not in self.parent:
            raise KeyError(f"Unknown vertex: {vertex}")

        if self.parent[vertex] != vertex:
            self.parent[vertex] = self.find(self.parent[vertex])

        return self.parent[vertex]

    def union(self, a: str, b: str) -> bool:
        root_a = self.find(a)
        root_b = self.find(b)

        if root_a == root_b:
            return False

        if self.rank[root_a] < self.rank[root_b]:
            root_a, root_b = root_b, root_a

        self.parent[root_b] = root_a

        if self.rank[root_a] == self.rank[root_b]:
            self.rank[root_a] += 1

        self.components -= 1
        return True

    def connected(self, a: str, b: str) -> bool:
        return self.find(a) == self.find(b)


class WeightedGraph:
    """Undirected weighted graph supporting minimum spanning forests."""

    def __init__(self, vertices: Iterable[str]):
        self.vertices = set(vertices)

        if any(not isinstance(v, str) or not v for v in self.vertices):
            raise ValueError("Vertices must be non-empty strings.")

        self.edges: list[Edge] = []
        self.adjacency: dict[str, list[tuple[str, float]]] = {
            v: [] for v in self.vertices
        }
        self._edge_keys = set()

    def add_edge(self, source: str, target: str, weight: float) -> None:
        if source not in self.vertices or target not in self.vertices:
            raise ValueError("Both endpoints must exist in the graph.")

        edge = Edge(source, target, float(weight))
        key = tuple(sorted((source, target)))

        if key in self._edge_keys:
            raise ValueError(f"Duplicate undirected edge: {key}")

        self._edge_keys.add(key)
        self.edges.append(edge)

        self.adjacency[source].append((target, edge.weight))
        self.adjacency[target].append((source, edge.weight))

    def validate(self) -> None:
        if not self.vertices:
            raise ValueError("Graph must contain at least one vertex.")

        for edge in self.edges:
            if edge.source not in self.vertices:
                raise ValueError("Invalid edge source.")
            if edge.target not in self.vertices:
                raise ValueError("Invalid edge target.")
            if not math.isfinite(edge.weight):
                raise ValueError("Non-finite edge weight.")

    def kruskal(self) -> "MSTResult":
        """O(E log E) using sorting and Union-Find."""

        self.validate()
        dsu = DisjointSet(self.vertices)
        selected = []
        total_weight = 0.0

        for edge in sorted(
            self.edges,
            key=lambda e: (e.weight, e.source, e.target)
        ):
            if dsu.union(edge.source, edge.target):
                selected.append(edge)
                total_weight += edge.weight

                if len(selected) == len(self.vertices) - 1:
                    break

        return MSTResult(
            algorithm="Kruskal",
            edges=selected,
            total_weight=total_weight,
            components=dsu.components,
            vertices=len(self.vertices)
        )

    def prim(self, start: str | None = None) -> "MSTResult":
        """O((V + E) log V) using an adjacency list and binary heap.

        Disconnected graphs produce a minimum spanning forest.
        """

        self.validate()

        if start is not None and start not in self.vertices:
            raise ValueError(f"Unknown starting vertex: {start}")

        visited = set()
        selected = []
        total_weight = 0.0

        ordered_vertices = sorted(self.vertices)

        if start is not None:
            ordered_vertices.remove(start)
            ordered_vertices.insert(0, start)

        for root in ordered_vertices:
            if root in visited:
                continue

            visited.add(root)
            heap = []

            for neighbor, weight in self.adjacency[root]:
                heapq.heappush(
                    heap,
                    (weight, root, neighbor)
                )

            while heap:
                weight, source, target = heapq.heappop(heap)

                if target in visited:
                    continue

                visited.add(target)
                selected.append(Edge(source, target, weight))
                total_weight += weight

                for neighbor, next_weight in self.adjacency[target]:
                    if neighbor not in visited:
                        heapq.heappush(
                            heap,
                            (next_weight, target, neighbor)
                        )

        components = len(self.vertices) - len(selected)

        return MSTResult(
            algorithm="Prim",
            edges=selected,
            total_weight=total_weight,
            components=components,
            vertices=len(self.vertices)
        )

    def is_connected(self) -> bool:
        if not self.vertices:
            return False

        dsu = DisjointSet(self.vertices)

        for edge in self.edges:
            dsu.union(edge.source, edge.target)

        return dsu.components == 1


@dataclass
class MSTResult:
    algorithm: str
    edges: list[Edge]
    total_weight: float
    components: int
    vertices: int

    @property
    def is_spanning_tree(self) -> bool:
        return (
            self.vertices > 0
            and self.components == 1
            and len(self.edges) == self.vertices - 1
        )

    @property
    def is_spanning_forest(self) -> bool:
        return len(self.edges) == self.vertices - self.components

    def display(self) -> None:
        print(f"\n{self.algorithm} result")
        print("-" * 45)

        for edge in self.edges:
            print(
                f"{edge.source} -- {edge.target} "
                f"(weight={edge.weight:g})"
            )

        print(f"Total weight: {self.total_weight:g}")
        print(f"Vertices: {self.vertices}")
        print(f"Components: {self.components}")
        print(f"Edges selected: {len(self.edges)}")
        print(f"Spanning tree: {self.is_spanning_tree}")
        print(f"Spanning forest: {self.is_spanning_forest}")


def verify_result(graph: WeightedGraph, result: MSTResult) -> bool:
    """Verify acyclicity, edge count and component preservation."""

    dsu = DisjointSet(graph.vertices)

    for edge in result.edges:
        if not dsu.union(edge.source, edge.target):
            return False

    original = DisjointSet(graph.vertices)

    for edge in graph.edges:
        original.union(edge.source, edge.target)

    if dsu.components != original.components:
        return False

    if len(result.edges) != len(graph.vertices) - dsu.components:
        return False

    calculated_weight = sum(e.weight for e in result.edges)

    return (
        math.isclose(
            calculated_weight,
            result.total_weight,
            rel_tol=1e-9,
            abs_tol=1e-9
        )
        and dsu.components == result.components
    )


def build_network() -> WeightedGraph:
    """Example: designing a low-cost network between facilities."""

    graph = WeightedGraph(
        ["A", "B", "C", "D", "E", "F"]
    )

    connections = [
        ("A", "B", 4),
        ("A", "C", 3),
        ("B", "C", 1),
        ("B", "D", 2),
        ("C", "D", 4),
        ("C", "E", 5),
        ("D", "E", 2),
        ("D", "F", 6),
        ("E", "F", 3),
    ]

    for source, target, weight in connections:
        graph.add_edge(source, target, weight)

    return graph


def demonstrate_union_find() -> None:
    print("\nUnion-Find demonstration")

    dsu = DisjointSet(["A", "B", "C", "D"])

    print("A connected to B:", dsu.connected("A", "B"))

    dsu.union("A", "B")
    dsu.union("C", "D")

    print("A connected to B:", dsu.connected("A", "B"))
    print("A connected to C:", dsu.connected("A", "C"))

    dsu.union("B", "C")

    print("A connected to D:", dsu.connected("A", "D"))
    print("Remaining components:", dsu.components)


def demonstrate_disconnected_graph() -> None:
    print("\nDisconnected graph demonstration")

    graph = WeightedGraph(["A", "B", "C", "D", "E"])

    graph.add_edge("A", "B", 2)
    graph.add_edge("B", "C", 3)
    graph.add_edge("D", "E", 1)

    graph.kruskal().display()
    graph.prim().display()


def run_tests() -> None:
    graph = build_network()

    kruskal = graph.kruskal()
    prim = graph.prim(start="A")

    assert kruskal.is_spanning_tree
    assert prim.is_spanning_tree

    assert verify_result(graph, kruskal)
    assert verify_result(graph, prim)

    assert math.isclose(
        kruskal.total_weight,
        prim.total_weight
    )

    # Negative edge weights are valid in MST problems.
    negative_graph = WeightedGraph(["A", "B", "C"])
    negative_graph.add_edge("A", "B", -5)
    negative_graph.add_edge("B", "C", 2)
    negative_graph.add_edge("A", "C", 4)

    assert negative_graph.kruskal().total_weight == -3

    # A single vertex has an empty spanning tree.
    singleton = WeightedGraph(["A"])
    assert singleton.kruskal().is_spanning_tree
    assert singleton.prim().total_weight == 0

    # Empty graphs are rejected.
    try:
        WeightedGraph([]).kruskal()
        raise AssertionError("Empty graph should fail validation.")
    except ValueError:
        pass

    # Duplicate undirected edges are rejected.
    try:
        duplicate = WeightedGraph(["A", "B"])
        duplicate.add_edge("A", "B", 1)
        duplicate.add_edge("B", "A", 2)
        raise AssertionError("Duplicate edge should be rejected.")
    except ValueError:
        pass

    # Self-loops are rejected.
    try:
        graph_with_loop = WeightedGraph(["A"])
        graph_with_loop.add_edge("A", "A", 1)
        raise AssertionError("Self-loop should be rejected.")
    except ValueError:
        pass

    # Deterministic randomized comparison of both algorithms.
    rng = random.Random(42)

    for _ in range(100):
        count = rng.randint(2, 12)
        vertices = [str(i) for i in range(count)]
        random_graph = WeightedGraph(vertices)

        # Generate a connected backbone.
        for i in range(1, count):
            random_graph.add_edge(
                vertices[i - 1],
                vertices[i],
                rng.randint(-10, 30)
            )

        # Add additional non-duplicate edges.
        candidates = [
            (i, j)
            for i in range(count)
            for j in range(i + 1, count)
        ]
        rng.shuffle(candidates)

        for i, j in candidates:
            key = tuple(sorted((vertices[i], vertices[j])))

            if key not in random_graph._edge_keys and rng.random() < 0.3:
                random_graph.add_edge(
                    vertices[i],
                    vertices[j],
                    rng.randint(-10, 30)
                )

        k = random_graph.kruskal()
        p = random_graph.prim()

        assert math.isclose(
            k.total_weight,
            p.total_weight,
            rel_tol=1e-9,
            abs_tol=1e-9
        )

        assert verify_result(random_graph, k)
        assert verify_result(random_graph, p)

    print("\nAll tests passed.")


def main() -> None:
    graph = build_network()

    print("MINIMUM SPANNING TREE")
    print("=====================")
    print("Network vertices:", sorted(graph.vertices))
    print("Available connections:", len(graph.edges))
    print("Graph connected:", graph.is_connected())

    kruskal = graph.kruskal()
    prim = graph.prim(start="A")

    kruskal.display()
    prim.display()

    print("\nAlgorithm comparison")
    print("--------------------")
    print("Kruskal weight:", kruskal.total_weight)
    print("Prim weight:", prim.total_weight)
    print("Both results verified:",
          verify_result(graph, kruskal)
          and verify_result(graph, prim))

    demonstrate_union_find()
    demonstrate_disconnected_graph()
    run_tests()


if __name__ == "__main__":
    main()
