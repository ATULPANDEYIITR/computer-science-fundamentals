from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable
import json
import logging
import unittest

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("graph_algorithms")


class GraphError(Exception):
    """Base exception for graph operations."""


class VertexNotFoundError(GraphError):
    pass


class GraphType(Enum):
    DIRECTED = "directed"
    UNDIRECTED = "undirected"


@dataclass
class BFSResult:
    source: str
    distances: dict[str, int]
    parents: dict[str, str | None]

    def path_to(self, target: str) -> list[str] | None:
        if target not in self.distances:
            return None

        path = []
        current: str | None = target

        while current is not None:
            path.append(current)
            current = self.parents[current]

        return list(reversed(path))


@dataclass
class DFSResult:
    discovery_order: list[str]
    finish_order: list[str]
    has_cycle: bool
    topological_order: list[str] | None


class Graph:
    """
    Adjacency-list graph implementation.

    BFS: O(V + E)
    DFS: O(V + E)
    Connected components: O(V + E)
    """

    def __init__(self, graph_type: GraphType = GraphType.UNDIRECTED):
        self.graph_type = graph_type
        self.adjacency: dict[str, set[str]] = defaultdict(set)
        self.edge_count = 0

    def add_vertex(self, vertex: str) -> None:
        if not isinstance(vertex, str) or not vertex.strip():
            raise ValueError("Vertex must be a non-empty string.")
        self.adjacency[vertex]

    def add_edge(self, source: str, target: str) -> None:
        self.add_vertex(source)
        self.add_vertex(target)

        if target in self.adjacency[source]:
            return

        self.adjacency[source].add(target)
        self.edge_count += 1

        if self.graph_type == GraphType.UNDIRECTED:
            self.adjacency[target].add(source)

    def remove_vertex(self, vertex: str) -> None:
        if vertex not in self.adjacency:
            raise VertexNotFoundError(vertex)

        del self.adjacency[vertex]

        for neighbors in self.adjacency.values():
            neighbors.discard(vertex)

        self._recount_edges()

    def _recount_edges(self) -> None:
        total = sum(len(v) for v in self.adjacency.values())
        self.edge_count = (
            total // 2
            if self.graph_type == GraphType.UNDIRECTED
            else total
        )

    def validate_vertex(self, vertex: str) -> None:
        if vertex not in self.adjacency:
            raise VertexNotFoundError(f"Unknown vertex: {vertex}")

    def vertices(self) -> list[str]:
        return sorted(self.adjacency)

    def neighbors(self, vertex: str) -> list[str]:
        self.validate_vertex(vertex)
        return sorted(self.adjacency[vertex])

    # ---------------------------------------------------------
    # 1. BREADTH-FIRST SEARCH
    # ---------------------------------------------------------

    def bfs(self, source: str) -> BFSResult:
        self.validate_vertex(source)

        queue = deque([source])
        distances = {source: 0}
        parents: dict[str, str | None] = {source: None}

        while queue:
            current = queue.popleft()

            for neighbor in self.adjacency[current]:
                if neighbor not in distances:
                    distances[neighbor] = distances[current] + 1
                    parents[neighbor] = current
                    queue.append(neighbor)

        return BFSResult(source, distances, parents)

    def multi_source_bfs(self, sources: Iterable[str]) -> dict[str, int]:
        """Find minimum distance from any supplied source."""
        sources = list(dict.fromkeys(sources))

        if not sources:
            return {}

        for source in sources:
            self.validate_vertex(source)

        queue = deque(sources)
        distances = {source: 0 for source in sources}

        while queue:
            current = queue.popleft()

            for neighbor in self.adjacency[current]:
                if neighbor not in distances:
                    distances[neighbor] = distances[current] + 1
                    queue.append(neighbor)

        return distances

    def shortest_path(self, source: str, target: str) -> list[str] | None:
        self.validate_vertex(source)
        self.validate_vertex(target)
        return self.bfs(source).path_to(target)

    def levels(self, source: str) -> dict[int, list[str]]:
        """Group reachable vertices by BFS distance."""
        result = self.bfs(source)
        grouped: dict[int, list[str]] = defaultdict(list)

        for vertex, distance in result.distances.items():
            grouped[distance].append(vertex)

        return {
            level: sorted(vertices)
            for level, vertices in sorted(grouped.items())
        }

    # ---------------------------------------------------------
    # 2. DEPTH-FIRST SEARCH
    # ---------------------------------------------------------

    def dfs(self, source: str | None = None) -> DFSResult:
        if source is not None:
            self.validate_vertex(source)

        visited = set()
        discovery = []
        finish = []
        active = set()
        has_cycle = False

        def visit(vertex: str, parent: str | None) -> None:
            nonlocal has_cycle

            visited.add(vertex)
            active.add(vertex)
            discovery.append(vertex)

            for neighbor in sorted(self.adjacency[vertex]):
                if neighbor not in visited:
                    visit(neighbor, vertex)
                elif self.graph_type == GraphType.DIRECTED:
                    if neighbor in active:
                        has_cycle = True
                elif neighbor != parent:
                    has_cycle = True

            active.remove(vertex)
            finish.append(vertex)

        roots = [source] if source is not None else self.vertices()

        for vertex in roots:
            if vertex not in visited:
                visit(vertex, None)

        topological = None

        if self.graph_type == GraphType.DIRECTED and not has_cycle:
            topological = list(reversed(finish))

        return DFSResult(discovery, finish, has_cycle, topological)

    def has_path_dfs(self, source: str, target: str) -> bool:
        self.validate_vertex(source)
        self.validate_vertex(target)

        stack = [source]
        visited = set()

        while stack:
            current = stack.pop()

            if current == target:
                return True

            if current in visited:
                continue

            visited.add(current)
            stack.extend(
                neighbor
                for neighbor in self.adjacency[current]
                if neighbor not in visited
            )

        return False

    # ---------------------------------------------------------
    # 3. CONNECTED COMPONENTS
    # ---------------------------------------------------------

    def connected_components(self) -> list[list[str]]:
        if self.graph_type != GraphType.UNDIRECTED:
            raise GraphError(
                "Connected components require an undirected graph."
            )

        visited = set()
        components = []

        for vertex in self.vertices():
            if vertex in visited:
                continue

            component = []
            queue = deque([vertex])
            visited.add(vertex)

            while queue:
                current = queue.popleft()
                component.append(current)

                for neighbor in self.adjacency[current]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)

            components.append(sorted(component))

        return components

    def component_summary(self) -> dict:
        components = self.connected_components()

        return {
            "component_count": len(components),
            "components": components,
            "largest_component_size": max(
                (len(c) for c in components), default=0
            ),
            "isolated_vertices": [
                vertex for vertex in self.vertices()
                if not self.adjacency[vertex]
            ],
        }

    # ---------------------------------------------------------
    # 4. GRAPH PERSISTENCE
    # ---------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "type": self.graph_type.value,
            "vertices": self.vertices(),
            "edges": [
                [source, target]
                for source in self.vertices()
                for target in self.neighbors(source)
                if (
                    self.graph_type == GraphType.DIRECTED
                    or source < target
                )
            ],
        }

    def save(self, filename: str) -> None:
        data = self.to_dict()
        path = Path(filename)

        # Avoid accidental writes outside the current working directory.
        if path.name != filename:
            raise ValueError("Use a filename without directory traversal.")

        path.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8"
        )

    @classmethod
    def load(cls, filename: str) -> Graph:
        path = Path(filename)

        if path.name != filename:
            raise ValueError("Invalid filename.")

        data = json.loads(path.read_text(encoding="utf-8"))

        if not isinstance(data, dict):
            raise ValueError("Invalid graph document.")

        graph = cls(GraphType(data["type"]))

        for vertex in data["vertices"]:
            graph.add_vertex(vertex)

        for edge in data["edges"]:
            if not isinstance(edge, list) or len(edge) != 2:
                raise ValueError("Invalid edge record.")
            graph.add_edge(edge[0], edge[1])

        return graph


# -------------------------------------------------------------
# 5. APPLICATION: SOCIAL NETWORK AND NETWORK REACHABILITY
# -------------------------------------------------------------

def build_social_network() -> Graph:
    graph = Graph(GraphType.UNDIRECTED)

    relationships = [
        ("Alice", "Bob"),
        ("Alice", "Charlie"),
        ("Bob", "David"),
        ("Charlie", "David"),
        ("David", "Eva"),
        ("Frank", "Grace"),
        ("Grace", "Helen"),
        ("Ivan", "Julia"),
    ]

    for first, second in relationships:
        graph.add_edge(first, second)

    graph.add_vertex("Kevin")
    return graph


def demonstrate_bfs(graph: Graph) -> None:
    print("\n=== BREADTH-FIRST SEARCH ===")

    result = graph.bfs("Alice")

    print("Distances:", result.distances)
    print("Shortest path Alice -> Eva:",
          result.path_to("Eva"))
    print("Unreachable path Alice -> Ivan:",
          result.path_to("Ivan"))

    print("BFS levels:", graph.levels("Alice"))

    distances = graph.multi_source_bfs(["Alice", "Frank"])
    print("Multi-source distances:", distances)


def demonstrate_dfs() -> None:
    print("\n=== DEPTH-FIRST SEARCH ===")

    graph = Graph(GraphType.DIRECTED)

    edges = [
        ("Requirements", "Design"),
        ("Design", "Implementation"),
        ("Implementation", "Testing"),
        ("Testing", "Deployment"),
        ("Requirements", "Documentation"),
    ]

    for source, target in edges:
        graph.add_edge(source, target)

    result = graph.dfs()

    print("Discovery:", result.discovery_order)
    print("Finish:", result.finish_order)
    print("Cycle detected:", result.has_cycle)
    print("Topological order:", result.topological_order)

    cyclic = Graph(GraphType.DIRECTED)
    cyclic.add_edge("A", "B")
    cyclic.add_edge("B", "C")
    cyclic.add_edge("C", "A")

    print("Cyclic graph detected:", cyclic.dfs().has_cycle)


def demonstrate_components(graph: Graph) -> None:
    print("\n=== CONNECTED COMPONENTS ===")

    summary = graph.component_summary()

    print("Components:", summary["components"])
    print("Component count:", summary["component_count"])
    print("Largest component:", summary["largest_component_size"])
    print("Isolated vertices:", summary["isolated_vertices"])


# -------------------------------------------------------------
# 6. TESTING
# -------------------------------------------------------------

class GraphTests(unittest.TestCase):

    def setUp(self):
        self.graph = Graph()
        self.graph.add_edge("A", "B")
        self.graph.add_edge("B", "C")
        self.graph.add_vertex("D")

    def test_bfs_shortest_path(self):
        self.assertEqual(
            self.graph.shortest_path("A", "C"),
            ["A", "B", "C"]
        )

    def test_unreachable_vertex(self):
        self.assertIsNone(self.graph.shortest_path("A", "D"))

    def test_connected_components(self):
        self.assertEqual(
            len(self.graph.connected_components()), 2
        )

    def test_isolated_vertex(self):
        self.assertEqual(
            self.graph.component_summary()["isolated_vertices"],
            ["D"]
        )

    def test_cycle_detection(self):
        cyclic = Graph(GraphType.DIRECTED)
        cyclic.add_edge("A", "B")
        cyclic.add_edge("B", "C")
        cyclic.add_edge("C", "A")
        self.assertTrue(cyclic.dfs().has_cycle)

    def test_topological_sort(self):
        directed = Graph(GraphType.DIRECTED)
        directed.add_edge("A", "B")
        directed.add_edge("B", "C")

        order = directed.dfs().topological_order
        self.assertIsNotNone(order)

        positions = {vertex: i for i, vertex in enumerate(order)}
        self.assertLess(positions["A"], positions["B"])
        self.assertLess(positions["B"], positions["C"])

    def test_invalid_vertex(self):
        with self.assertRaises(VertexNotFoundError):
            self.graph.bfs("UNKNOWN")

    def test_duplicate_edge(self):
        count = self.graph.edge_count
        self.graph.add_edge("A", "B")
        self.assertEqual(count, self.graph.edge_count)

    def test_directed_components_rejected(self):
        directed = Graph(GraphType.DIRECTED)
        directed.add_vertex("A")
        with self.assertRaises(GraphError):
            directed.connected_components()


def main() -> None:
    print("GRAPH ALGORITHMS I")
    print("=" * 50)

    social_graph = build_social_network()

    print("Vertices:", social_graph.vertices())
    print("Edges:", social_graph.edge_count)

    demonstrate_bfs(social_graph)
    demonstrate_dfs()
    demonstrate_components(social_graph)

    print("\n=== GRAPH TESTS ===")
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(GraphTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    logger.info("All graph algorithm tests passed.")


if __name__ == "__main__":
    main()
