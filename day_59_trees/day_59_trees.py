from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Optional


class TraversalOrder(Enum):
    PREORDER = "preorder"
    INORDER = "inorder"
    POSTORDER = "postorder"
    LEVEL_ORDER = "level_order"


@dataclass
class TreeNode:
    value: int
    left: Optional["TreeNode"] = None
    right: Optional["TreeNode"] = None


class BinaryTree:
    """Binary tree with traversal, search, height, and structural validation."""

    def __init__(self, root: Optional[TreeNode] = None) -> None:
        self.root = root

    @staticmethod
    def from_level_order(values: Iterable[Optional[int]]) -> "BinaryTree":
        values = list(values)
        if not values or values[0] is None:
            return BinaryTree()

        root = TreeNode(values[0])
        queue: deque[TreeNode] = deque([root])
        index = 1

        while queue and index < len(values):
            node = queue.popleft()

            if index < len(values) and values[index] is not None:
                node.left = TreeNode(values[index])
                queue.append(node.left)
            index += 1

            if index < len(values) and values[index] is not None:
                node.right = TreeNode(values[index])
                queue.append(node.right)
            index += 1

        return BinaryTree(root)

    def preorder(self) -> list[int]:
        result: list[int] = []

        def visit(node: Optional[TreeNode]) -> None:
            if node is None:
                return
            result.append(node.value)
            visit(node.left)
            visit(node.right)

        visit(self.root)
        return result

    def inorder(self) -> list[int]:
        result: list[int] = []
        stack: list[TreeNode] = []
        current = self.root

        # Explicit stack avoids recursion-depth failures on deep trees.
        while current is not None or stack:
            while current is not None:
                stack.append(current)
                current = current.left

            current = stack.pop()
            result.append(current.value)
            current = current.right

        return result

    def postorder(self) -> list[int]:
        if self.root is None:
            return []

        result: list[int] = []
        stack: list[tuple[TreeNode, bool]] = [(self.root, False)]

        while stack:
            node, expanded = stack.pop()

            if expanded:
                result.append(node.value)
                continue

            stack.append((node, True))
            if node.right is not None:
                stack.append((node.right, False))
            if node.left is not None:
                stack.append((node.left, False))

        return result

    def level_order(self) -> list[int]:
        if self.root is None:
            return []

        result: list[int] = []
        queue: deque[TreeNode] = deque([self.root])

        while queue:
            node = queue.popleft()
            result.append(node.value)

            if node.left is not None:
                queue.append(node.left)
            if node.right is not None:
                queue.append(node.right)

        return result

    def traverse(self, order: TraversalOrder) -> list[int]:
        methods = {
            TraversalOrder.PREORDER: self.preorder,
            TraversalOrder.INORDER: self.inorder,
            TraversalOrder.POSTORDER: self.postorder,
            TraversalOrder.LEVEL_ORDER: self.level_order,
        }
        return methods[order]()

    def contains(self, value: int) -> bool:
        return value in self.level_order()

    def height(self) -> int:
        if self.root is None:
            return 0

        height = 0
        queue: deque[TreeNode] = deque([self.root])

        while queue:
            level_size = len(queue)
            height += 1

            for _ in range(level_size):
                node = queue.popleft()
                if node.left is not None:
                    queue.append(node.left)
                if node.right is not None:
                    queue.append(node.right)

        return height

    def leaf_count(self) -> int:
        if self.root is None:
            return 0

        count = 0
        queue: deque[TreeNode] = deque([self.root])

        while queue:
            node = queue.popleft()
            if node.left is None and node.right is None:
                count += 1
            else:
                if node.left is not None:
                    queue.append(node.left)
                if node.right is not None:
                    queue.append(node.right)

        return count


class BinarySearchTree(BinaryTree):
    """Binary search tree using the invariant left < node < right."""

    def insert(self, value: int) -> None:
        if self.root is None:
            self.root = TreeNode(value)
            return

        current = self.root

        while True:
            if value == current.value:
                raise ValueError(f"Duplicate value is not allowed: {value}")

            if value < current.value:
                if current.left is None:
                    current.left = TreeNode(value)
                    return
                current = current.left
            else:
                if current.right is None:
                    current.right = TreeNode(value)
                    return
                current = current.right

    def search(self, value: int) -> bool:
        current = self.root

        while current is not None:
            if value == current.value:
                return True
            current = current.left if value < current.value else current.right

        return False

    def validate_bst(self) -> bool:
        def validate(
            node: Optional[TreeNode],
            lower: Optional[int],
            upper: Optional[int],
        ) -> bool:
            if node is None:
                return True

            if lower is not None and node.value <= lower:
                return False
            if upper is not None and node.value >= upper:
                return False

            return (
                validate(node.left, lower, node.value)
                and validate(node.right, node.value, upper)
            )

        return validate(self.root, None, None)

    def min_value(self) -> int:
        if self.root is None:
            raise ValueError("Cannot find a minimum in an empty tree.")

        current = self.root
        while current.left is not None:
            current = current.left
        return current.value

    def max_value(self) -> int:
        if self.root is None:
            raise ValueError("Cannot find a maximum in an empty tree.")

        current = self.root
        while current.right is not None:
            current = current.right
        return current.value


def build_sample_bst() -> BinarySearchTree:
    tree = BinarySearchTree()
    for value in [50, 30, 70, 20, 40, 60, 80, 10, 25, 65]:
        tree.insert(value)
    return tree


def run_assertions() -> None:
    tree = build_sample_bst()

    assert tree.validate_bst()
    assert tree.search(65)
    assert not tree.search(999)
    assert tree.min_value() == 10
    assert tree.max_value() == 80
    assert tree.height() == 4
    assert tree.leaf_count() == 5
    assert tree.inorder() == [10, 20, 25, 30, 40, 50, 60, 65, 70, 80]

    ordinary = BinaryTree.from_level_order(
        [1, 2, 3, 4, 5, None, 6, None, None, 7]
    )
    assert ordinary.preorder() == [1, 2, 4, 5, 7, 3, 6]
    assert ordinary.inorder() == [4, 2, 7, 5, 1, 3, 6]
    assert ordinary.postorder() == [4, 7, 5, 2, 6, 3, 1]
    assert ordinary.level_order() == [1, 2, 3, 4, 5, 6, 7]

    empty = BinaryTree()
    assert empty.level_order() == []
    assert empty.height() == 0
    assert empty.leaf_count() == 0

    try:
        tree.insert(50)
    except ValueError:
        pass
    else:
        raise AssertionError("Duplicate insertion should fail.")


def main() -> None:
    run_assertions()

    tree = build_sample_bst()

    print("Binary Tree Traversals")
    for order in TraversalOrder:
        print(f"{order.value:12}: {tree.traverse(order)}")

    print("\nBinary Search Tree")
    print("Contains 65:", tree.search(65))
    print("Contains 99:", tree.search(99))
    print("Minimum:", tree.min_value())
    print("Maximum:", tree.max_value())
    print("Height:", tree.height())
    print("Leaves:", tree.leaf_count())
    print("Valid BST:", tree.validate_bst())

    # Operational considerations:
    # - Traversals are O(n) time.
    # - BFS uses O(w) auxiliary space, where w is maximum width.
    # - Recursive DFS can use O(h) call-stack space; iterative versions
    #   are preferable when arbitrary input depth is possible.
    # - BST search/insert are O(h), ranging from O(log n) for balanced trees
    #   to O(n) for a highly skewed tree.
    # - Values are validated before insertion and duplicate keys are rejected.


if __name__ == "__main__":
    main()
