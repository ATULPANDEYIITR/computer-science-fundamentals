from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from heapq import heappop, heappush
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class GraphType(Enum):
    DIRECTED = "directed"
    UNDIRECTED = "undirected"


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    weight: float = 1.0


class GraphError(Exception):
    """Raised for invalid graph operations."""


class Graph:
    def __init__(self, graph_type: GraphType = GraphType.DIRECTED):
        self.graph_type = graph_type
        self._adjacency: Dict[str, Dict[str, float]] = {}

    def add_vertex(self, vertex: str) -> None:
        vertex = vertex.strip()
        if not vertex:
            raise GraphError("Vertex name cannot be empty.")
        self._adjacency.setdefault(vertex, {})

    def add_edge(self, source: str, target: str, weight: float = 1.0) -> None:
        if not source.strip() or not target.strip():
            raise GraphError("Edge endpoints cannot be empty.")
        if weight < 0:
            raise GraphError("This graph implementation requires non-negative weights.")

        self.add_vertex(source)
        self.add_vertex(target)
        self._adjacency[source][target] = float(weight)

        if self.graph_type == GraphType.UNDIRECTED:
            self._adjacency[target][source] = float(weight)

    def remove_edge(self, source: str, target: str) -> None:
        self._adjacency.get(source, {}).pop(target, None)
        if self.graph_type == GraphType.UNDIRECTED:
            self._adjacency.get(target, {}).pop(source, None)

    def neighbors(self, vertex: str) -> Dict[str, float]:
        if vertex not in self._adjacency:
            raise GraphError(f"Unknown vertex: {vertex}")
        return dict(self._adjacency[vertex])

    def vertices(self) -> List[str]:
        return sorted(self._adjacency)

    def edges(self) -> List[Edge]:
        result: List[Edge] = []
        seen: Set[Tuple[str, str]] = set()

        for source, targets in self._adjacency.items():
            for target, weight in targets.items():
                key = tuple(sorted((source, target))) if self.graph_type == GraphType.UNDIRECTED else (source, target)
                if key not in seen:
                    result.append(Edge(source, target, weight))
                    seen.add(key)

        return sorted(result, key=lambda e: (e.source, e.target))

    def adjacency_list(self) -> Dict[str, Dict[str, float]]:
        return {vertex: dict(targets) for vertex, targets in self._adjacency.items()}

    def adjacency_matrix(self) -> Tuple[List[str], List[List[Optional[float]]]]:
        vertices = self.vertices()
        index = {vertex: i for i, vertex in enumerate(vertices)}
        matrix: List[List[Optional[float]]] = [
            [None for _ in vertices] for _ in vertices
        ]

        for source, targets in self._adjacency.items():
            for target, weight in targets.items():
                matrix[index[source]][index[target]] = weight

        return vertices, matrix

    def bfs(self, start: str) -> List[str]:
        if start not in self._adjacency:
            raise GraphError(f"Unknown vertex: {start}")

        queue = [start]
        visited = {start}
        order = []

        while queue:
            current = queue.pop(0)
            order.append(current)

            for neighbor in sorted(self._adjacency[current]):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return order

    def dfs(self, start: str) -> List[str]:
        if start not in self._adjacency:
            raise GraphError(f"Unknown vertex: {start}")

        order: List[str] = []
        visited: Set[str] = set()

        def visit(vertex: str) -> None:
            visited.add(vertex)
            order.append(vertex)
            for neighbor in sorted(self._adjacency[vertex]):
                if neighbor not in visited:
                    visit(neighbor)

        visit(start)
        return order

    def dijkstra(self, start: str) -> Tuple[Dict[str, float], Dict[str, Optional[str]]]:
        if start not in self._adjacency:
            raise GraphError(f"Unknown vertex: {start}")

        distances = {vertex: float("inf") for vertex in self._adjacency}
        previous: Dict[str, Optional[str]] = {
            vertex: None for vertex in self._adjacency
        }
        distances[start] = 0.0

        heap = [(0.0, start)]

        while heap:
            current_distance, current = heappop(heap)

            if current_distance != distances[current]:
                continue

            for neighbor, weight in self._adjacency[current].items():
                candidate = current_distance + weight
                if candidate < distances[neighbor]:
                    distances[neighbor] = candidate
                    previous[neighbor] = current
                    heappush(heap, (candidate, neighbor))

        return distances, previous

    def shortest_path(self, start: str, target: str) -> Tuple[List[str], float]:
        distances, previous = self.dijkstra(start)

        if target not in distances:
            raise GraphError(f"Unknown target vertex: {target}")

        if distances[target] == float("inf"):
            return [], float("inf")

        path = []
        current: Optional[str] = target

        while current is not None:
            path.append(current)
            current = previous[current]

        path.reverse()
        return path, distances[target]

    def topological_sort(self) -> List[str]:
        if self.graph_type != GraphType.DIRECTED:
            raise GraphError("Topological sorting requires a directed graph.")

        indegree = {vertex: 0 for vertex in self._adjacency}

        for targets in self._adjacency.values():
            for target in targets:
                indegree[target] += 1

        queue = sorted(vertex for vertex, degree in indegree.items() if degree == 0)
        order = []

        while queue:
            current = queue.pop(0)
            order.append(current)

            for neighbor in sorted(self._adjacency[current]):
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    queue.append(neighbor)
                    queue.sort()

        if len(order) != len(self._adjacency):
            raise GraphError("The directed graph contains a cycle.")

        return order

    def has_cycle(self) -> bool:
        if self.graph_type == GraphType.UNDIRECTED:
            visited: Set[str] = set()

            def visit(vertex: str, parent: Optional[str]) -> bool:
                visited.add(vertex)
                for neighbor in self._adjacency[vertex]:
                    if neighbor not in visited:
                        if visit(neighbor, vertex):
                            return True
                    elif neighbor != parent:
                        return True
                return False

            return any(
                vertex not in visited and visit(vertex, None)
                for vertex in self._adjacency
            )

        visiting: Set[str] = set()
        visited: Set[str] = set()

        def visit(vertex: str) -> bool:
            if vertex in visiting:
                return True
            if vertex in visited:
                return False

            visiting.add(vertex)
            for neighbor in self._adjacency[vertex]:
                if visit(neighbor):
                    return True

            visiting.remove(vertex)
            visited.add(vertex)
            return False

        return any(vertex not in visited and visit(vertex) for vertex in self._adjacency)


def save_graph(graph: Graph, path: str) -> None:
    """Persist the graph as a simple CSV-like edge list."""
    output = Path(path)
    with output.open("w", encoding="utf-8") as file:
        file.write("source,target,weight\n")
        for edge in graph.edges():
            file.write(f"{edge.source},{edge.target},{edge.weight}\n")


def build_delivery_network() -> Graph:
    network = Graph(GraphType.DIRECTED)

    routes = [
        ("Lucknow", "Kanpur", 1.5),
        ("Lucknow", "Ayodhya", 2.0),
        ("Kanpur", "Agra", 3.0),
        ("Ayodhya", "Varanasi", 2.5),
        ("Agra", "Delhi", 2.0),
        ("Varanasi", "Patna", 4.0),
        ("Delhi", "Jaipur", 3.0),
        ("Delhi", "Patna", 5.0),
        ("Jaipur", "Ahmedabad", 4.0),
        ("Patna", "Kolkata", 5.0),
        ("Ahmedabad", "Mumbai", 6.0),
        ("Kolkata", "Guwahati", 7.0),
        ("Mumbai", "Bengaluru", 7.0),
    ]

    for source, target, weight in routes:
        network.add_edge(source, target, weight)

    return network


def demonstrate() -> None:
    graph = build_delivery_network()

    print("DIRECTED WEIGHTED GRAPH")
    print("=======================")
    print("Vertices:", graph.vertices())
    print("\nEdges:")
    for edge in graph.edges():
        print(f"  {edge.source} -> {edge.target} ({edge.weight:.1f} hours)")

    print("\nAdjacency List:")
    for vertex, neighbors in graph.adjacency_list().items():
        print(f"  {vertex}: {neighbors}")

    vertices, matrix = graph.adjacency_matrix()
    print("\nAdjacency Matrix:")
    print("      " + " ".join(f"{v:>10}" for v in vertices))
    for vertex, row in zip(vertices, matrix):
        values = " ".join(
            f"{('-' if value is None else value):>10}" for value in row
        )
        print(f"{vertex:>10} {values}")

    print("\nBFS from Lucknow:")
    print(" -> ".join(graph.bfs("Lucknow")))

    print("\nDFS from Lucknow:")
    print(" -> ".join(graph.dfs("Lucknow")))

    path, distance = graph.shortest_path("Lucknow", "Mumbai")
    print("\nShortest route from Lucknow to Mumbai:")
    print(" -> ".join(path))
    print(f"Travel time: {distance:.1f} hours")

    print("\nCycle:", graph.has_cycle())

    workflow = Graph(GraphType.DIRECTED)
    workflow.add_edge("Design", "Implement")
    workflow.add_edge("Implement", "Test")
    workflow.add_edge("Test", "Deploy")
    print("\nDAG topological order:")
    print(" -> ".join(workflow.topological_sort()))

    try:
        workflow.add_edge("Deploy", "Design")
        workflow.topological_sort()
    except GraphError as exc:
        print("Cycle validation:", exc)
        workflow.remove_edge("Deploy", "Design")

    try:
        graph.add_edge("Delhi", "Mumbai", -2)
    except GraphError as exc:
        print("Weight validation:", exc)

    assert graph.shortest_path("Lucknow", "Mumbai")[1] == 18.5
    assert not graph.has_cycle()
    assert workflow.topological_sort() == ["Design", "Implement", "Test", "Deploy"]

    output_file = "delivery_network_edges.csv"
    save_graph(graph, output_file)
    print(f"\nGraph exported to {output_file}")

    print("\nComplexity:")
    print("  Adjacency-list storage: O(V + E)")
    print("  BFS/DFS: O(V + E)")
    print("  Dijkstra with binary heap: O((V + E) log V)")
    print("  Topological sort: O(V + E)")


if __name__ == "__main__":
    demonstrate()
