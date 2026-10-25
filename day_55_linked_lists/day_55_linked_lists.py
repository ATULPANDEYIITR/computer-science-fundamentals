from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Generic, Iterable, Iterator, Optional, TypeVar


T = TypeVar("T")


class ListType(Enum):
    SINGLY = "singly"
    DOUBLY = "doubly"
    CIRCULAR = "circular"


class LinkedListError(Exception):
    """Base exception for linked-list operations."""


class EmptyListError(LinkedListError):
    """Raised when an operation requires at least one node."""


class IndexOutOfBoundsError(LinkedListError):
    """Raised for an invalid linked-list index."""


@dataclass
class SinglyNode(Generic[T]):
    value: T
    next: Optional["SinglyNode[T]"] = None


@dataclass
class DoublyNode(Generic[T]):
    value: T
    previous: Optional["DoublyNode[T]"] = None
    next: Optional["DoublyNode[T]"] = None


class SinglyLinkedList(Generic[T]):
    """Forward-only linked list."""

    def __init__(self, values: Iterable[T] = ()) -> None:
        self.head: Optional[SinglyNode[T]] = None
        self.tail: Optional[SinglyNode[T]] = None
        self.size = 0

        for value in values:
            self.append(value)

    def append(self, value: T) -> None:
        node = SinglyNode(value)

        if self.head is None:
            self.head = self.tail = node
        else:
            assert self.tail is not None
            self.tail.next = node
            self.tail = node

        self.size += 1

    def prepend(self, value: T) -> None:
        node = SinglyNode(value, self.head)
        self.head = node

        if self.tail is None:
            self.tail = node

        self.size += 1

    def insert(self, index: int, value: T) -> None:
        if index < 0 or index > self.size:
            raise IndexOutOfBoundsError(index)

        if index == 0:
            self.prepend(value)
            return

        if index == self.size:
            self.append(value)
            return

        previous = self.node_at(index - 1)
        previous.next = SinglyNode(value, previous.next)
        self.size += 1

    def node_at(self, index: int) -> SinglyNode[T]:
        if index < 0 or index >= self.size:
            raise IndexOutOfBoundsError(index)

        current = self.head
        for _ in range(index):
            assert current is not None
            current = current.next

        assert current is not None
        return current

    def get(self, index: int) -> T:
        return self.node_at(index).value

    def remove(self, index: int) -> T:
        if index < 0 or index >= self.size:
            raise IndexOutOfBoundsError(index)

        if index == 0:
            assert self.head is not None
            removed = self.head
            self.head = removed.next
            self.size -= 1

            if self.size == 0:
                self.tail = None

            return removed.value

        previous = self.node_at(index - 1)
        assert previous.next is not None
        removed = previous.next
        previous.next = removed.next

        if removed is self.tail:
            self.tail = previous

        self.size -= 1
        return removed.value

    def reverse(self) -> None:
        previous = None
        current = self.head
        self.tail = self.head

        while current is not None:
            following = current.next
            current.next = previous
            previous = current
            current = following

        self.head = previous

    def find(self, value: T) -> int:
        current = self.head
        index = 0

        while current is not None:
            if current.value == value:
                return index
            current = current.next
            index += 1

        return -1

    def __iter__(self) -> Iterator[T]:
        current = self.head

        while current is not None:
            yield current.value
            current = current.next

    def __len__(self) -> int:
        return self.size

    def __repr__(self) -> str:
        return " -> ".join(map(str, self))


class DoublyLinkedList(Generic[T]):
    """Bidirectional linked list with head and tail references."""

    def __init__(self, values: Iterable[T] = ()) -> None:
        self.head: Optional[DoublyNode[T]] = None
        self.tail: Optional[DoublyNode[T]] = None
        self.size = 0

        for value in values:
            self.append(value)

    def append(self, value: T) -> None:
        node = DoublyNode(value, self.tail, None)

        if self.tail is None:
            self.head = self.tail = node
        else:
            self.tail.next = node
            self.tail = node

        self.size += 1

    def prepend(self, value: T) -> None:
        node = DoublyNode(value, None, self.head)

        if self.head is None:
            self.head = self.tail = node
        else:
            self.head.previous = node
            self.head = node

        self.size += 1

    def node_at(self, index: int) -> DoublyNode[T]:
        if index < 0 or index >= self.size:
            raise IndexOutOfBoundsError(index)

        # Start from whichever end is closer.
        if index <= self.size // 2:
            current = self.head
            for _ in range(index):
                assert current is not None
                current = current.next
        else:
            current = self.tail
            for _ in range(self.size - 1, index, -1):
                assert current is not None
                current = current.previous

        assert current is not None
        return current

    def insert(self, index: int, value: T) -> None:
        if index < 0 or index > self.size:
            raise IndexOutOfBoundsError(index)

        if index == 0:
            self.prepend(value)
            return

        if index == self.size:
            self.append(value)
            return

        target = self.node_at(index)
        previous = target.previous
        node = DoublyNode(value, previous, target)

        assert previous is not None
        previous.next = node
        target.previous = node
        self.size += 1

    def remove(self, index: int) -> T:
        target = self.node_at(index)

        if target.previous is None:
            self.head = target.next
        else:
            target.previous.next = target.next

        if target.next is None:
            self.tail = target.previous
        else:
            target.next.previous = target.previous

        self.size -= 1
        return target.value

    def reverse(self) -> None:
        current = self.head

        while current is not None:
            current.previous, current.next = current.next, current.previous
            current = current.previous

        self.head, self.tail = self.tail, self.head

    def forward(self) -> list[T]:
        return list(self)

    def backward(self) -> list[T]:
        result: list[T] = []
        current = self.tail

        while current is not None:
            result.append(current.value)
            current = current.previous

        return result

    def __iter__(self) -> Iterator[T]:
        current = self.head

        while current is not None:
            yield current.value
            current = current.next

    def __len__(self) -> int:
        return self.size


class CircularLinkedList(Generic[T]):
    """Circular singly linked list whose tail points back to head."""

    def __init__(self, values: Iterable[T] = ()) -> None:
        self.head: Optional[SinglyNode[T]] = None
        self.tail: Optional[SinglyNode[T]] = None
        self.size = 0

        for value in values:
            self.append(value)

    def append(self, value: T) -> None:
        node = SinglyNode(value)

        if self.head is None:
            self.head = self.tail = node
            node.next = node
        else:
            assert self.tail is not None
            node.next = self.head
            self.tail.next = node
            self.tail = node

        self.size += 1

    def prepend(self, value: T) -> None:
        if self.head is None:
            self.append(value)
            return

        assert self.tail is not None
        node = SinglyNode(value, self.head)
        self.tail.next = node
        self.head = node
        self.size += 1

    def node_at(self, index: int) -> SinglyNode[T]:
        if index < 0 or index >= self.size:
            raise IndexOutOfBoundsError(index)

        assert self.head is not None
        current = self.head

        for _ in range(index):
            assert current.next is not None
            current = current.next

        return current

    def remove(self, index: int) -> T:
        if index < 0 or index >= self.size:
            raise IndexOutOfBoundsError(index)

        assert self.head is not None
        assert self.tail is not None

        if self.size == 1:
            value = self.head.value
            self.head = self.tail = None
            self.size = 0
            return value

        if index == 0:
            value = self.head.value
            self.head = self.head.next
            self.tail.next = self.head
            self.size -= 1
            return value

        previous = self.node_at(index - 1)
        assert previous.next is not None
        removed = previous.next
        previous.next = removed.next

        if removed is self.tail:
            self.tail = previous

        self.size -= 1
        return removed.value

    def rotate(self, steps: int) -> None:
        if self.size == 0:
            return

        steps %= self.size
        for _ in range(steps):
            assert self.head is not None
            assert self.tail is not None
            self.head = self.head.next
            self.tail = self.tail.next

    def __iter__(self) -> Iterator[T]:
        if self.head is None:
            return

        current = self.head
        for _ in range(self.size):
            yield current.value
            assert current.next is not None
            current = current.next

    def __len__(self) -> int:
        return self.size

    def __repr__(self) -> str:
        if self.size == 0:
            return "empty circular list"
        return " -> ".join(map(str, self)) + " -> (head)"


def detect_cycle(head: Optional[SinglyNode[T]]) -> bool:
    """Floyd's tortoise-and-hare cycle detection."""
    slow = fast = head

    while fast is not None and fast.next is not None:
        assert slow is not None
        slow = slow.next
        fast = fast.next.next

        if slow is fast:
            return True

    return False


def merge_sorted(
    first: SinglyLinkedList[int],
    second: SinglyLinkedList[int],
) -> SinglyLinkedList[int]:
    """Merge two sorted singly linked lists without sorting the result."""
    result = SinglyLinkedList[int]()
    left = first.head
    right = second.head

    while left is not None and right is not None:
        if left.value <= right.value:
            result.append(left.value)
            left = left.next
        else:
            result.append(right.value)
            right = right.next

    while left is not None:
        result.append(left.value)
        left = left.next

    while right is not None:
        result.append(right.value)
        right = right.next

    return result


def validate_integrity(
    singly: SinglyLinkedList[T],
    doubly: DoublyLinkedList[T],
    circular: CircularLinkedList[T],
) -> None:
    if len(singly) == 0:
        assert singly.head is None and singly.tail is None
    else:
        assert singly.head is not None and singly.tail is not None
        assert singly.tail.next is None

    if len(doubly) == 0:
        assert doubly.head is None and doubly.tail is None
    else:
        assert doubly.head is not None and doubly.tail is not None
        assert doubly.head.previous is None
        assert doubly.tail.next is None

        current = doubly.head
        previous = None
        count = 0

        while current is not None:
            assert current.previous is previous
            previous = current
            current = current.next
            count += 1

        assert count == len(doubly)

    if len(circular) == 0:
        assert circular.head is None and circular.tail is None
    else:
        assert circular.head is not None and circular.tail is not None
        assert circular.tail.next is circular.head

        current = circular.head
        for _ in range(len(circular)):
            assert current is not None
            current = current.next

        assert current is circular.head


def main() -> None:
    singly = SinglyLinkedList([10, 20, 30])
    singly.prepend(5)
    singly.insert(2, 15)
    removed = singly.remove(1)

    print("Singly:", singly)
    print("Removed:", removed)
    print("Index of 30:", singly.find(30))
    print("Cycle detected:", detect_cycle(singly.head))

    singly.reverse()
    print("Reversed singly:", singly)

    first = SinglyLinkedList([1, 3, 5, 7])
    second = SinglyLinkedList([2, 4, 6, 8])
    print("Merged sorted:", merge_sorted(first, second))

    doubly = DoublyLinkedList(["A", "B", "C", "D"])
    doubly.insert(2, "X")
    print("Doubly forward:", doubly.forward())
    print("Doubly backward:", doubly.backward())
    print("Doubly remove:", doubly.remove(2))
    doubly.reverse()
    print("Doubly reversed:", doubly.forward())

    circular = CircularLinkedList([100, 200, 300, 400])
    circular.rotate(2)
    print("Circular after rotation:", circular)
    print("Circular remove:", circular.remove(1))
    print("Circular:", circular)

    validate_integrity(singly, doubly, circular)

    try:
        singly.get(100)
    except IndexOutOfBoundsError as exc:
        print("Expected validation failure:", exc)

    empty = SinglyLinkedList[int]()
    try:
        empty.remove(0)
    except IndexOutOfBoundsError as exc:
        print("Expected empty-list failure:", exc)

    print("All integrity checks passed.")


if __name__ == "__main__":
    main()
