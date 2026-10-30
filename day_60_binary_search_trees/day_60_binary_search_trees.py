from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import json
from typing import Optional


@dataclass(slots=True)
class Node:
    key: int
    value: str
    left: Optional["Node"] = None
    right: Optional["Node"] = None
    height: int = 1


class IndexBase:
    """Shared ordered-index operations for binary search tree implementations."""

    balanced = False

    def __init__(self) -> None:
        self.root: Optional[Node] = None
        self.size = 0

    @staticmethod
    def validate_key(key: int) -> None:
        if isinstance(key, bool) or not isinstance(key, int):
            raise TypeError("Tree keys must be integers")

    @staticmethod
    def validate_value(value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Values must be non-empty strings")
        if len(value) > 200:
            raise ValueError("Values cannot exceed 200 characters")

    def search(self, key: int) -> Optional[str]:
        self.validate_key(key)
        current = self.root

        while current is not None:
            if key == current.key:
                return current.value
            current = current.left if key < current.key else current.right

        return None

    def inorder(self) -> list[tuple[int, str]]:
        result: list[tuple[int, str]] = []
        stack: list[Node] = []
        current = self.root

        while current is not None or stack:
            while current is not None:
                stack.append(current)
                current = current.left

            current = stack.pop()
            result.append((current.key, current.value))
            current = current.right

        return result

    def range_query(self, lower: int, upper: int) -> list[tuple[int, str]]:
        self.validate_key(lower)
        self.validate_key(upper)

        if lower > upper:
            raise ValueError("Lower bound cannot exceed upper bound")

        result: list[tuple[int, str]] = []
        stack: list[Node] = []
        current = self.root

        # Skip subtrees that cannot contain a key in the requested interval.
        while current is not None or stack:
            while current is not None:
                if current.key >= lower:
                    stack.append(current)
                    current = current.left
                else:
                    current = current.right

            if not stack:
                break

            current = stack.pop()
            if current.key > upper:
                break

            result.append((current.key, current.value))
            current = current.right

        return result

    def kth_smallest(self, position: int) -> tuple[int, str]:
        if isinstance(position, bool) or not isinstance(position, int):
            raise TypeError("Position must be an integer")
        if position < 1 or position > self.size:
            raise IndexError("Position is outside the tree")

        stack: list[Node] = []
        current = self.root
        visited = 0

        while current is not None or stack:
            while current is not None:
                stack.append(current)
                current = current.left

            current = stack.pop()
            visited += 1

            if visited == position:
                return current.key, current.value

            current = current.right

        raise RuntimeError("Tree size and traversal results are inconsistent")

    def height(self) -> int:
        if self.root is None:
            return 0

        queue = deque([(self.root, 1)])
        maximum = 0

        while queue:
            node, depth = queue.popleft()
            maximum = max(maximum, depth)

            if node.left is not None:
                queue.append((node.left, depth + 1))
            if node.right is not None:
                queue.append((node.right, depth + 1))

        return maximum

    def validate(self) -> bool:
        """Check ordering, uniqueness, node count, and AVL metadata if applicable."""
        stack: list[tuple[Node, Optional[int], Optional[int]]] = []
        seen: set[int] = set()

        if self.root is not None:
            stack.append((self.root, None, None))

        count = 0

        while stack:
            node, lower, upper = stack.pop()
            identity = id(node)

            if identity in seen:
                return False
            seen.add(identity)

            if lower is not None and node.key <= lower:
                return False
            if upper is not None and node.key >= upper:
                return False

            count += 1

            if node.left is not None:
                stack.append((node.left, lower, node.key))
            if node.right is not None:
                stack.append((node.right, node.key, upper))

        if count != self.size:
            return False

        if self.balanced and self.root is not None:
            heights: dict[int, int] = {}
            postorder: list[tuple[Node, bool]] = [(self.root, False)]

            while postorder:
                node, visited = postorder.pop()

                if not visited:
                    postorder.append((node, True))
                    if node.right is not None:
                        postorder.append((node.right, False))
                    if node.left is not None:
                        postorder.append((node.left, False))
                    continue

                left_height = heights.get(id(node.left), 0)
                right_height = heights.get(id(node.right), 0)
                expected_height = 1 + max(left_height, right_height)

                if node.height != expected_height:
                    return False
                if abs(left_height - right_height) > 1:
                    return False

                heights[id(node)] = expected_height

        return True

    def __len__(self) -> int:
        return self.size


class BinarySearchTree(IndexBase):
    """
    Unbalanced binary search tree.

    Iterative insertion and deletion avoid recursion-depth failures when
    ordered input creates a degenerate tree.
    """

    def insert(self, key: int, value: str) -> bool:
        self.validate_key(key)
        self.validate_value(value)

        if self.root is None:
            self.root = Node(key, value)
            self.size = 1
            return True

        current = self.root

        while True:
            if key == current.key:
                current.value = value
                return False

            if key < current.key:
                if current.left is None:
                    current.left = Node(key, value)
                    self.size += 1
                    return True
                current = current.left
            else:
                if current.right is None:
                    current.right = Node(key, value)
                    self.size += 1
                    return True
                current = current.right

    def delete(self, key: int) -> bool:
        self.validate_key(key)

        parent: Optional[Node] = None
        current = self.root

        while current is not None and current.key != key:
            parent = current
            current = current.left if key < current.key else current.right

        if current is None:
            return False

        # For a node with two children, copy its inorder successor.
        # The successor has no left child, so its physical removal is simple.
        if current.left is not None and current.right is not None:
            successor_parent = current
            successor = current.right

            while successor.left is not None:
                successor_parent = successor
                successor = successor.left

            current.key = successor.key
            current.value = successor.value

            if successor_parent == current:
                successor_parent.right = successor.right
            else:
                successor_parent.left = successor.right

        else:
            replacement = current.left or current.right

            if parent is None:
                self.root = replacement
            elif parent.left is current:
                parent.left = replacement
            else:
                parent.right = replacement

        self.size -= 1
        return True


class AvlTree(IndexBase):
    """
    AVL tree.

    Every insertion and deletion restores the height-balance condition.
    Rotations keep search, insertion, and deletion logarithmic in height.
    """

    balanced = True

    @staticmethod
    def _node_height(node: Optional[Node]) -> int:
        return node.height if node is not None else 0

    @classmethod
    def _refresh(cls, node: Node) -> None:
        node.height = 1 + max(
            cls._node_height(node.left),
            cls._node_height(node.right),
        )

    @classmethod
    def _balance_factor(cls, node: Node) -> int:
        return cls._node_height(node.left) - cls._node_height(node.right)

    @classmethod
    def _rotate_right(cls, root: Node) -> Node:
        pivot = root.left
        if pivot is None:
            raise RuntimeError("Invalid right rotation")

        root.left = pivot.right
        pivot.right = root

        cls._refresh(root)
        cls._refresh(pivot)
        return pivot

    @classmethod
    def _rotate_left(cls, root: Node) -> Node:
        pivot = root.right
        if pivot is None:
            raise RuntimeError("Invalid left rotation")

        root.right = pivot.left
        pivot.left = root

        cls._refresh(root)
        cls._refresh(pivot)
        return pivot

    @classmethod
    def _rebalance(cls, node: Node) -> Node:
        cls._refresh(node)
        balance = cls._balance_factor(node)

        if balance > 1:
            if node.left is not None and cls._balance_factor(node.left) < 0:
                node.left = cls._rotate_left(node.left)
            return cls._rotate_right(node)

        if balance < -1:
            if node.right is not None and cls._balance_factor(node.right) > 0:
                node.right = cls._rotate_right(node.right)
            return cls._rotate_left(node)

        return node

    @classmethod
    def _insert(
        cls,
        node: Optional[Node],
        key: int,
        value: str,
    ) -> Node:
        if node is None:
            return Node(key, value)

        if key < node.key:
            node.left = cls._insert(node.left, key, value)
        elif key > node.key:
            node.right = cls._insert(node.right, key, value)
        else:
            node.value = value
            return node

        return cls._rebalance(node)

    def insert(self, key: int, value: str) -> bool:
        self.validate_key(key)
        self.validate_value(value)

        is_new = self.search(key) is None
        self.root = self._insert(self.root, key, value)

        if is_new:
            self.size += 1

        return is_new

    @classmethod
    def _minimum(cls, node: Node) -> Node:
        while node.left is not None:
            node = node.left
        return node

    @classmethod
    def _delete(cls, node: Optional[Node], key: int) -> Optional[Node]:
        if node is None:
            return None

        if key < node.key:
            node.left = cls._delete(node.left, key)
        elif key > node.key:
            node.right = cls._delete(node.right, key)
        else:
            if node.left is None:
                return node.right
            if node.right is None:
                return node.left

            successor = cls._minimum(node.right)
            node.key = successor.key
            node.value = successor.value
            node.right = cls._delete(node.right, successor.key)

        return cls._rebalance(node)

    def delete(self, key: int) -> bool:
        self.validate_key(key)

        if self.search(key) is None:
            return False

        self.root = self._delete(self.root, key)
        self.size -= 1
        return True


def exercise_tree(tree: IndexBase) -> dict:
    """Exercise updates, searches, all deletion shapes, and ordered queries."""
    initial_records = [
        (50, "gateway"),
        (30, "database"),
        (70, "monitor"),
        (20, "worker"),
        (40, "cache"),
        (60, "scheduler"),
        (80, "backup"),
        (65, "logger"),
    ]

    for key, value in initial_records:
        tree.insert(key, value)

    assert tree.search(50) == "gateway"
    assert tree.search(999) is None

    # Duplicate keys update values rather than creating duplicate nodes.
    assert tree.insert(50, "gateway-updated") is False
    assert tree.search(50) == "gateway-updated"
    assert len(tree) == len(initial_records)

    # Leaf, one-child, and two-child removal cases.
    assert tree.delete(20)
    assert tree.delete(60)
    assert tree.delete(70)
    assert not tree.delete(999)

    assert tree.validate()

    return {
        "remaining_records": tree.inorder(),
        "range_35_to_70": tree.range_query(35, 70),
        "first_record": tree.kth_smallest(1),
        "height": tree.height(),
        "node_count": len(tree),
        "valid": tree.validate(),
    }


def compare_tree_shapes() -> dict:
    unbalanced = BinarySearchTree()
    balanced = AvlTree()

    # Sorted input is a worst-case insertion order for an ordinary BST.
    for key in range(1, 1001):
        unbalanced.insert(key, f"asset-{key}")
        balanced.insert(key, f"asset-{key}")

    assert unbalanced.validate()
    assert balanced.validate()
    assert unbalanced.height() == 1000
    assert balanced.height() <= 11

    for tree in (unbalanced, balanced):
        assert tree.search(500) == "asset-500"
        assert tree.delete(500)
        assert tree.search(500) is None
        assert tree.validate()

    return {
        "input_records": 1000,
        "unbalanced_bst_height": unbalanced.height(),
        "avl_height": balanced.height(),
        "unbalanced_node_count": len(unbalanced),
        "avl_node_count": len(balanced),
        "both_valid_after_deletion": (
            unbalanced.validate() and balanced.validate()
        ),
    }


def main() -> None:
    # The same workload is run against two different tree structures.
    bst_result = exercise_tree(BinarySearchTree())
    avl_result = exercise_tree(AvlTree())
    comparison = compare_tree_shapes()

    report = {
        "unbalanced_bst": bst_result,
        "avl_tree": avl_result,
        "sorted_insertion_comparison": comparison,
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
