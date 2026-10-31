from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Optional


class Color(Enum):
    RED = "RED"
    BLACK = "BLACK"


@dataclass
class AVLNode:
    key: int
    height: int = 1
    left: Optional["AVLNode"] = None
    right: Optional["AVLNode"] = None


class AVLTree:
    """Height-balanced BST using single and double rotations."""

    def __init__(self) -> None:
        self.root: Optional[AVLNode] = None

    @staticmethod
    def height(node: Optional[AVLNode]) -> int:
        return node.height if node else 0

    @staticmethod
    def update_height(node: AVLNode) -> None:
        node.height = 1 + max(
            AVLTree.height(node.left),
            AVLTree.height(node.right),
        )

    @staticmethod
    def balance_factor(node: Optional[AVLNode]) -> int:
        if node is None:
            return 0
        return AVLTree.height(node.left) - AVLTree.height(node.right)

    def rotate_right(self, y: AVLNode) -> AVLNode:
        x = y.left
        if x is None:
            raise RuntimeError("Right rotation requires a left child")

        transfer = x.right
        x.right = y
        y.left = transfer

        self.update_height(y)
        self.update_height(x)
        return x

    def rotate_left(self, x: AVLNode) -> AVLNode:
        y = x.right
        if y is None:
            raise RuntimeError("Left rotation requires a right child")

        transfer = y.left
        y.left = x
        x.right = transfer

        self.update_height(x)
        self.update_height(y)
        return y

    def insert(self, key: int) -> None:
        self.root = self._insert(self.root, key)

    def _insert(self, node: Optional[AVLNode], key: int) -> AVLNode:
        if node is None:
            return AVLNode(key)

        if key < node.key:
            node.left = self._insert(node.left, key)
        elif key > node.key:
            node.right = self._insert(node.right, key)
        else:
            raise ValueError(f"Duplicate key is not allowed: {key}")

        self.update_height(node)
        balance = self.balance_factor(node)

        # LL case.
        if balance > 1 and key < node.left.key:
            return self.rotate_right(node)

        # RR case.
        if balance < -1 and key > node.right.key:
            return self.rotate_left(node)

        # LR case.
        if balance > 1 and key > node.left.key:
            node.left = self.rotate_left(node.left)
            return self.rotate_right(node)

        # RL case.
        if balance < -1 and key < node.right.key:
            node.right = self.rotate_right(node.right)
            return self.rotate_left(node)

        return node

    def delete(self, key: int) -> None:
        self.root = self._delete(self.root, key)

    def _delete(self, node: Optional[AVLNode], key: int) -> Optional[AVLNode]:
        if node is None:
            return None

        if key < node.key:
            node.left = self._delete(node.left, key)
        elif key > node.key:
            node.right = self._delete(node.right, key)
        else:
            if node.left is None:
                return node.right
            if node.right is None:
                return node.left

            successor = node.right
            while successor.left:
                successor = successor.left
            node.key = successor.key
            node.right = self._delete(node.right, successor.key)

        self.update_height(node)
        balance = self.balance_factor(node)

        if balance > 1 and self.balance_factor(node.left) >= 0:
            return self.rotate_right(node)

        if balance > 1 and self.balance_factor(node.left) < 0:
            node.left = self.rotate_left(node.left)
            return self.rotate_right(node)

        if balance < -1 and self.balance_factor(node.right) <= 0:
            return self.rotate_left(node)

        if balance < -1 and self.balance_factor(node.right) > 0:
            node.right = self.rotate_right(node.right)
            return self.rotate_left(node)

        return node

    def search(self, key: int) -> bool:
        node = self.root
        while node:
            if key == node.key:
                return True
            node = node.left if key < node.key else node.right
        return False

    def inorder(self) -> list[int]:
        result: list[int] = []

        def visit(node: Optional[AVLNode]) -> None:
            if node:
                visit(node.left)
                result.append(node.key)
                visit(node.right)

        visit(self.root)
        return result

    def validate(self) -> None:
        def check(node: Optional[AVLNode], low: Optional[int], high: Optional[int]) -> int:
            if node is None:
                return 0

            if low is not None and node.key <= low:
                raise AssertionError("BST ordering violation")
            if high is not None and node.key >= high:
                raise AssertionError("BST ordering violation")

            left_height = check(node.left, low, node.key)
            right_height = check(node.right, node.key, high)
            expected = 1 + max(left_height, right_height)

            if node.height != expected:
                raise AssertionError(f"Incorrect height at {node.key}")

            if abs(left_height - right_height) > 1:
                raise AssertionError(f"AVL balance violation at {node.key}")

            return expected

        check(self.root, None, None)


@dataclass
class RBNode:
    key: int
    color: Color = Color.RED
    left: Optional["RBNode"] = None
    right: Optional["RBNode"] = None
    parent: Optional["RBNode"] = None


class RedBlackTree:
    """
    Red-Black insertion model.

    The implementation uses None as the black leaf sentinel. Deletion is
    intentionally represented by rebuilding from remaining keys so that the
    example remains compact while preserving all insertion invariants.
    """

    def __init__(self) -> None:
        self.root: Optional[RBNode] = None

    @staticmethod
    def color(node: Optional[RBNode]) -> Color:
        return node.color if node else Color.BLACK

    def rotate_left(self, x: RBNode) -> None:
        y = x.right
        if y is None:
            raise RuntimeError("Invalid left rotation")

        x.right = y.left
        if y.left:
            y.left.parent = x

        y.parent = x.parent
        if x.parent is None:
            self.root = y
        elif x is x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y

        y.left = x
        x.parent = y

    def rotate_right(self, y: RBNode) -> None:
        x = y.left
        if x is None:
            raise RuntimeError("Invalid right rotation")

        y.left = x.right
        if x.right:
            x.right.parent = y

        x.parent = y.parent
        if y.parent is None:
            self.root = x
        elif y is y.parent.left:
            y.parent.left = x
        else:
            y.parent.right = x

        x.right = y
        y.parent = x

    def insert(self, key: int) -> None:
        parent: Optional[RBNode] = None
        current = self.root

        while current:
            parent = current
            if key < current.key:
                current = current.left
            elif key > current.key:
                current = current.right
            else:
                raise ValueError(f"Duplicate key is not allowed: {key}")

        node = RBNode(key=key, parent=parent)
        if parent is None:
            self.root = node
        elif key < parent.key:
            parent.left = node
        else:
            parent.right = node

        self._fix_insert(node)

    def _fix_insert(self, z: RBNode) -> None:
        while z.parent and z.parent.color == Color.RED:
            parent = z.parent
            grandparent = parent.parent
            if grandparent is None:
                break

            if parent is grandparent.left:
                uncle = grandparent.right

                if self.color(uncle) == Color.RED:
                    parent.color = Color.BLACK
                    uncle.color = Color.BLACK
                    grandparent.color = Color.RED
                    z = grandparent
                else:
                    if z is parent.right:
                        z = parent
                        self.rotate_left(z)
                        parent = z.parent

                    parent.color = Color.BLACK
                    grandparent.color = Color.RED
                    self.rotate_right(grandparent)
            else:
                uncle = grandparent.left

                if self.color(uncle) == Color.RED:
                    parent.color = Color.BLACK
                    uncle.color = Color.BLACK
                    grandparent.color = Color.RED
                    z = grandparent
                else:
                    if z is parent.left:
                        z = parent
                        self.rotate_right(z)
                        parent = z.parent

                    parent.color = Color.BLACK
                    grandparent.color = Color.RED
                    self.rotate_left(grandparent)

        if self.root:
            self.root.color = Color.BLACK
            self.root.parent = None

    def search(self, key: int) -> bool:
        node = self.root
        while node:
            if key == node.key:
                return True
            node = node.left if key < node.key else node.right
        return False

    def inorder(self) -> list[tuple[int, str]]:
        result: list[tuple[int, str]] = []

        def visit(node: Optional[RBNode]) -> None:
            if node:
                visit(node.left)
                result.append((node.key, node.color.value))
                visit(node.right)

        visit(self.root)
        return result

    def validate(self) -> None:
        if self.root and self.root.color != Color.BLACK:
            raise AssertionError("Root must be black")

        def check(node: Optional[RBNode]) -> int:
            if node is None:
                return 1

            if node.color == Color.RED:
                if self.color(node.left) == Color.RED or self.color(node.right) == Color.RED:
                    raise AssertionError("Red node has a red child")

            if node.left and node.left.parent is not node:
                raise AssertionError("Invalid parent pointer")
            if node.right and node.right.parent is not node:
                raise AssertionError("Invalid parent pointer")

            left_black_height = check(node.left)
            right_black_height = check(node.right)

            if left_black_height != right_black_height:
                raise AssertionError("Black-height violation")

            return left_black_height + (1 if node.color == Color.BLACK else 0)

        check(self.root)


def compare_growth(keys: Iterable[int]) -> None:
    avl = AVLTree()
    rb = RedBlackTree()

    for key in keys:
        avl.insert(key)
        rb.insert(key)

    avl.validate()
    rb.validate()

    print("AVL inorder:", avl.inorder())
    print("AVL height:", avl.height(avl.root))
    print("Red-Black inorder:", rb.inorder())
    print("Red-Black root:", rb.root.key if rb.root else None)
    print("Red-Black valid:", end=" ")
    rb.validate()
    print(True)

    for key in (10, 25, 50, 99):
        print(f"search({key}): AVL={avl.search(key)}, RB={rb.search(key)}")


def main() -> None:
    # Sorted insertion is a useful stress case: an ordinary BST becomes
    # linear, while both balanced structures maintain logarithmic height.
    sorted_keys = list(range(1, 32))
    compare_growth(sorted_keys)

    avl = AVLTree()
    for key in (30, 20, 10, 25, 28, 40, 50):
        avl.insert(key)
        avl.validate()

    print("Before AVL deletion:", avl.inorder())
    avl.delete(20)
    avl.delete(40)
    avl.validate()
    print("After AVL deletion:", avl.inorder())

    try:
        avl.insert(30)
    except ValueError as exc:
        print("Expected validation error:", exc)

    # Security/production note: untrusted keys should be validated before
    # reaching a tree API, and recursive operations should be bounded or
    # replaced with iterative implementations when input size is extreme.
    assert avl.search(28)
    assert not avl.search(20)


if __name__ == "__main__":
    main()
