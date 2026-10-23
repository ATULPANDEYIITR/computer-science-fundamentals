from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable, Iterator, Optional, TypeVar
import heapq
import time


T = TypeVar("T")


# A data structure stores data and defines how that data is accessed.
# The same values can behave very differently depending on the structure.


class Stack:
    """LIFO abstract data type backed by a Python list."""

    def __init__(self, values: Iterable[T] = ()) -> None:
        self._items = list(values)

    def push(self, value: T) -> None:
        self._items.append(value)

    def pop(self) -> T:
        if not self._items:
            raise IndexError("cannot pop from an empty stack")
        return self._items.pop()

    def peek(self) -> T:
        if not self._items:
            raise IndexError("cannot peek at an empty stack")
        return self._items[-1]

    def is_empty(self) -> bool:
        return not self._items

    def __len__(self) -> int:
        return len(self._items)


class Queue:
    """FIFO abstract data type using deque for O(1) endpoint operations."""

    def __init__(self, values: Iterable[T] = ()) -> None:
        self._items = deque(values)

    def enqueue(self, value: T) -> None:
        self._items.append(value)

    def dequeue(self) -> T:
        if not self._items:
            raise IndexError("cannot dequeue from an empty queue")
        return self._items.popleft()

    def peek(self) -> T:
        if not self._items:
            raise IndexError("cannot peek at an empty queue")
        return self._items[0]

    def is_empty(self) -> bool:
        return not self._items

    def __len__(self) -> int:
        return len(self._items)


class SinglyLinkedList:
    """Linear structure where each node points to the next node."""

    @dataclass
    class Node:
        value: T
        next: Optional["SinglyLinkedList.Node"] = None

    def __init__(self) -> None:
        self.head: Optional[SinglyLinkedList.Node] = None
        self._size = 0

    def append(self, value: T) -> None:
        node = self.Node(value)

        if self.head is None:
            self.head = node
        else:
            current = self.head
            while current.next is not None:
                current = current.next
            current.next = node

        self._size += 1

    def find(self, value: T) -> Optional[int]:
        current = self.head
        index = 0

        while current is not None:
            if current.value == value:
                return index
            current = current.next
            index += 1

        return None

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[T]:
        current = self.head
        while current is not None:
            yield current.value
            current = current.next


class BinarySearchTree:
    """Non-linear ordered structure supporting recursive search and insertion."""

    @dataclass
    class Node:
        value: int
        left: Optional["BinarySearchTree.Node"] = None
        right: Optional["BinarySearchTree.Node"] = None

    def __init__(self) -> None:
        self.root: Optional[BinarySearchTree.Node] = None

    def insert(self, value: int) -> None:
        if self.root is None:
            self.root = self.Node(value)
            return

        current = self.root

        while True:
            if value == current.value:
                return

            if value < current.value:
                if current.left is None:
                    current.left = self.Node(value)
                    return
                current = current.left
            else:
                if current.right is None:
                    current.right = self.Node(value)
                    return
                current = current.right

    def contains(self, value: int) -> bool:
        current = self.root

        while current is not None:
            if value == current.value:
                return True
            current = current.left if value < current.value else current.right

        return False

    def inorder(self) -> list[int]:
        result: list[int] = []

        def visit(node: Optional[BinarySearchTree.Node]) -> None:
            if node is None:
                return
            visit(node.left)
            result.append(node.value)
            visit(node.right)

        visit(self.root)
        return result


class Graph:
    """Non-linear adjacency-list graph."""

    def __init__(self, vertices: Iterable[str]) -> None:
        self.adjacency: dict[str, list[str]] = {vertex: [] for vertex in vertices}

    def add_edge(self, source: str, target: str) -> None:
        if source not in self.adjacency or target not in self.adjacency:
            raise ValueError("both vertices must exist")
        self.adjacency[source].append(target)

    def breadth_first_search(self, start: str) -> list[str]:
        if start not in self.adjacency:
            raise KeyError(f"unknown vertex: {start}")

        visited = {start}
        queue = deque([start])
        order = []

        while queue:
            vertex = queue.popleft()
            order.append(vertex)

            for neighbor in self.adjacency[vertex]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return order

    def depth_first_search(self, start: str) -> list[str]:
        if start not in self.adjacency:
            raise KeyError(f"unknown vertex: {start}")

        visited: set[str] = set()
        order: list[str] = []

        def visit(vertex: str) -> None:
            visited.add(vertex)
            order.append(vertex)

            for neighbor in self.adjacency[vertex]:
                if neighbor not in visited:
                    visit(neighbor)

        visit(start)
        return order


def binary_search(values: list[int], target: int) -> Optional[int]:
    """O(log n) search on a sorted list."""
    left, right = 0, len(values) - 1

    while left <= right:
        middle = (left + right) // 2

        if values[middle] == target:
            return middle
        if values[middle] < target:
            left = middle + 1
        else:
            right = middle - 1

    return None


def bfs_shortest_path(graph: dict[str, list[str]], start: str, target: str) -> Optional[list[str]]:
    """BFS finds a shortest path in an unweighted graph."""
    if start not in graph or target not in graph:
        raise KeyError("start and target must exist")

    queue = deque([start])
    parent: dict[str, Optional[str]] = {start: None}

    while queue:
        current = queue.popleft()

        if current == target:
            path = []
            while current is not None:
                path.append(current)
                current = parent[current]
            return list(reversed(path))

        for neighbor in graph[current]:
            if neighbor not in parent:
                parent[neighbor] = current
                queue.append(neighbor)

    return None


def dijkstra(graph: dict[str, list[tuple[str, int]]], start: str) -> dict[str, int]:
    """Dijkstra's algorithm for non-negative weighted edges."""
    distances = {vertex: float("inf") for vertex in graph}
    distances[start] = 0

    heap: list[tuple[int, str]] = [(0, start)]

    while heap:
        distance, vertex = heapq.heappop(heap)

        if distance != distances[vertex]:
            continue

        for neighbor, weight in graph[vertex]:
            if weight < 0:
                raise ValueError("Dijkstra requires non-negative edge weights")

            candidate = distance + weight
            if candidate < distances[neighbor]:
                distances[neighbor] = candidate
                heapq.heappush(heap, (candidate, neighbor))

    return distances


def demonstrate_complexity() -> None:
    """Compare linear search and binary search on the same sorted data."""
    values = list(range(1_000_000))
    target = 999_999

    start = time.perf_counter()
    linear_index = next((i for i, value in enumerate(values) if value == target), None)
    linear_time = time.perf_counter() - start

    start = time.perf_counter()
    binary_index = binary_search(values, target)
    binary_time = time.perf_counter() - start

    print("\nComplexity experiment")
    print(f"Linear search index: {linear_index}, time: {linear_time:.6f}s")
    print(f"Binary search index: {binary_index}, time: {binary_time:.6f}s")


def main() -> None:
    stack = Stack(["read", "process"])
    stack.push("write")
    print("Stack:", stack.pop(), stack.peek())

    queue = Queue(["request-1", "request-2"])
    queue.enqueue("request-3")
    print("Queue:", queue.dequeue(), queue.peek())

    linked = SinglyLinkedList()
    for value in ["A", "B", "C", "D"]:
        linked.append(value)
    print("Linked list:", list(linked))
    print("Linked-list search:", linked.find("C"))

    tree = BinarySearchTree()
    for value in [50, 30, 70, 20, 40, 60, 80]:
        tree.insert(value)
    print("BST inorder:", tree.inorder())
    print("BST contains 60:", tree.contains(60))

    graph = Graph(["A", "B", "C", "D", "E"])
    graph.add_edge("A", "B")
    graph.add_edge("A", "C")
    graph.add_edge("B", "D")
    graph.add_edge("C", "E")
    print("Graph BFS:", graph.breadth_first_search("A"))
    print("Graph DFS:", graph.depth_first_search("A"))

    unweighted = {
        "A": ["B", "C"],
        "B": ["D"],
        "C": ["D"],
        "D": ["E"],
        "E": [],
    }
    print("Shortest path:", bfs_shortest_path(unweighted, "A", "E"))

    weighted = {
        "A": [("B", 4), ("C", 2)],
        "B": [("C", 5), ("D", 10)],
        "C": [("D", 3)],
        "D": [],
    }
    print("Dijkstra distances:", dijkstra(weighted, "A"))

    print("Binary search:", binary_search([10, 20, 30, 40, 50], 40))
    demonstrate_complexity()


if __name__ == "__main__":
    main()
