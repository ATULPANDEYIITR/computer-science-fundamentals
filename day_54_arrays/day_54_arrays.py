from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Optional


class Operation(Enum):
    ACCESS = "access"
    SEARCH = "search"
    INSERT = "insert"
    DELETE = "delete"
    UPDATE = "update"


class ArrayError(Exception):
    """Raised when an array operation violates a domain rule."""


@dataclass
class ArrayStats:
    accesses: int = 0
    searches: int = 0
    insertions: int = 0
    deletions: int = 0
    updates: int = 0

    def record(self, operation: Operation) -> None:
        if operation is Operation.ACCESS:
            self.accesses += 1
        elif operation is Operation.SEARCH:
            self.searches += 1
        elif operation is Operation.INSERT:
            self.insertions += 1
        elif operation is Operation.DELETE:
            self.deletions += 1
        elif operation is Operation.UPDATE:
            self.updates += 1


@dataclass
class DynamicArray:
    capacity: int = 4
    _data: list[int] = field(default_factory=list)
    stats: ArrayStats = field(default_factory=ArrayStats)

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError("Capacity must be positive.")

    @property
    def size(self) -> int:
        return len(self._data)

    def _validate_index(self, index: int, allow_end: bool = False) -> None:
        upper = self.size if allow_end else self.size - 1
        if index < 0 or index > upper:
            raise ArrayError(
                f"Index {index} is outside the valid range."
            )

    def _grow_if_required(self) -> None:
        if self.size >= self.capacity:
            self.capacity *= 2

    def access(self, index: int) -> int:
        self._validate_index(index)
        self.stats.record(Operation.ACCESS)
        return self._data[index]

    def update(self, index: int, value: int) -> None:
        self._validate_index(index)
        if not isinstance(value, int):
            raise TypeError("Only integers are supported.")
        self._data[index] = value
        self.stats.record(Operation.UPDATE)

    def linear_search(self, value: int) -> int:
        self.stats.record(Operation.SEARCH)
        for index, item in enumerate(self._data):
            if item == value:
                return index
        return -1

    def binary_search(self, value: int) -> int:
        """Binary search requires the array to be sorted."""
        if any(
            self._data[i] > self._data[i + 1]
            for i in range(self.size - 1)
        ):
            raise ArrayError("Binary search requires sorted data.")

        self.stats.record(Operation.SEARCH)
        left, right = 0, self.size - 1

        while left <= right:
            middle = left + (right - left) // 2
            current = self._data[middle]

            if current == value:
                return middle
            if current < value:
                left = middle + 1
            else:
                right = middle - 1

        return -1

    def insert(self, index: int, value: int) -> None:
        self._validate_index(index, allow_end=True)
        if not isinstance(value, int):
            raise TypeError("Only integers are supported.")

        self._grow_if_required()

        # Elements at and after index move one position to the right.
        self._data.append(0)
        for position in range(self.size - 1, index, -1):
            self._data[position] = self._data[position - 1]

        self._data[index] = value
        self.stats.record(Operation.INSERT)

    def append(self, value: int) -> None:
        self.insert(self.size, value)

    def delete(self, index: int) -> int:
        self._validate_index(index)
        removed = self._data[index]

        # Shift the suffix left to preserve contiguous array semantics.
        for position in range(index, self.size - 1):
            self._data[position] = self._data[position + 1]

        self._data.pop()
        self.stats.record(Operation.DELETE)
        return removed

    def reverse(self) -> None:
        left, right = 0, self.size - 1
        while left < right:
            self._data[left], self._data[right] = (
                self._data[right],
                self._data[left],
            )
            left += 1
            right -= 1

    def traverse(self) -> Iterable[int]:
        for value in self._data:
            yield value

    def snapshot(self) -> list[int]:
        return self._data.copy()


def validate_operations(array: DynamicArray) -> None:
    assert array.snapshot() == [10, 20, 30, 40]

    assert array.access(2) == 30
    assert array.linear_search(40) == 3
    assert array.linear_search(999) == -1

    array.update(1, 25)
    assert array.snapshot() == [10, 25, 30, 40]

    array.insert(2, 27)
    assert array.snapshot() == [10, 25, 27, 30, 40]

    removed = array.delete(1)
    assert removed == 25
    assert array.snapshot() == [10, 27, 30, 40]

    array.reverse()
    assert array.snapshot() == [40, 30, 27, 10]


def demonstrate_sorted_operations() -> None:
    array = DynamicArray(capacity=2)

    for value in [10, 20, 30, 40, 50]:
        array.append(value)

    assert array.capacity >= 8
    assert array.binary_search(30) == 2
    assert array.binary_search(99) == -1

    print("Sorted array:", array.snapshot())
    print("30 found at:", array.binary_search(30))
    print("Capacity after growth:", array.capacity)


def demonstrate_failures() -> None:
    array = DynamicArray()
    array.append(5)

    failure_cases = [
        ("invalid access", lambda: array.access(4)),
        ("invalid insertion", lambda: array.insert(3, 8)),
        ("invalid deletion", lambda: array.delete(-1)),
        ("binary search on unsorted data", lambda: (
            array.append(1),
            array.binary_search(1),
        )),
    ]

    for name, action in failure_cases:
        try:
            action()
        except (ArrayError, IndexError, TypeError, ValueError) as exc:
            print(f"{name}: rejected -> {exc}")


def main() -> None:
    array = DynamicArray(capacity=4)

    for value in [10, 20, 30, 40]:
        array.append(value)

    validate_operations(DynamicArray(capacity=4))
    # Rebuild the validation fixture because validation intentionally mutates it.
    validation_array = DynamicArray(capacity=4)
    for value in [10, 20, 30, 40]:
        validation_array.append(value)
    validate_operations(validation_array)

    print("Final validation array:", validation_array.snapshot())
    print("Traversal:", list(validation_array.traverse()))
    print("Statistics:", validation_array.stats)

    demonstrate_sorted_operations()
    demonstrate_failures()

    print("\nComplexity:")
    print("Indexed access: O(1)")
    print("Linear search: O(n)")
    print("Binary search on sorted data: O(log n)")
    print("Insertion/deletion at arbitrary position: O(n)")
    print("Append: amortized O(1)")
    print("Traversal: O(n)")


if __name__ == "__main__":
    main()
