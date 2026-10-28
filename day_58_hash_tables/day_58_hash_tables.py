from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Generic, Iterator, Optional, TypeVar


K = TypeVar("K")
V = TypeVar("V")


class SlotState(Enum):
    EMPTY = "empty"
    OCCUPIED = "occupied"
    DELETED = "deleted"


@dataclass
class Entry(Generic[K, V]):
    key: K
    value: V


class HashTableError(Exception):
    """Base exception for hash-table failures."""


class DuplicateKeyError(HashTableError):
    pass


class KeyNotFoundError(HashTableError):
    pass


class HashTable(Generic[K, V]):
    """
    Hash table using separate chaining.

    Average-case lookup, insertion, and deletion are O(1) when the
    hash distribution is reasonable. Resizing keeps the load factor
    bounded so long chains do not grow unnecessarily.
    """

    def __init__(self, capacity: int = 8, max_load_factor: float = 0.75):
        if capacity < 2:
            raise ValueError("capacity must be at least 2")
        if not 0.1 <= max_load_factor <= 0.95:
            raise ValueError("max_load_factor must be between 0.1 and 0.95")

        self._buckets: list[list[Entry[K, V]]] = [
            [] for _ in range(capacity)
        ]
        self._size = 0
        self._max_load_factor = max_load_factor
        self._collisions = 0
        self._rehashes = 0

    @staticmethod
    def _validate_key(key: K) -> None:
        try:
            hash(key)
        except TypeError as exc:
            raise TypeError("key must be hashable") from exc

    def _index(self, key: K) -> int:
        return hash(key) % len(self._buckets)

    def _resize(self, new_capacity: int) -> None:
        old_entries = [entry for bucket in self._buckets for entry in bucket]
        self._buckets = [[] for _ in range(new_capacity)]
        self._collisions = 0

        for entry in old_entries:
            index = self._index(entry.key)
            if self._buckets[index]:
                self._collisions += 1
            self._buckets[index].append(entry)

        self._rehashes += 1

    def _ensure_capacity(self) -> None:
        if (self._size + 1) / len(self._buckets) > self._max_load_factor:
            self._resize(len(self._buckets) * 2)

    def put(self, key: K, value: V) -> None:
        self._validate_key(key)
        self._ensure_capacity()

        index = self._index(key)
        bucket = self._buckets[index]

        for entry in bucket:
            if entry.key == key:
                entry.value = value
                return

        if bucket:
            self._collisions += 1

        bucket.append(Entry(key, value))
        self._size += 1

    def add(self, key: K, value: V) -> None:
        self._validate_key(key)
        if self.contains(key):
            raise DuplicateKeyError(f"key already exists: {key!r}")
        self.put(key, value)

    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        self._validate_key(key)
        bucket = self._buckets[self._index(key)]

        for entry in bucket:
            if entry.key == key:
                return entry.value

        return default

    def require(self, key: K) -> V:
        value = self.get(key)
        if value is None:
            # None is allowed as a stored value, so perform an explicit search.
            bucket = self._buckets[self._index(key)]
            for entry in bucket:
                if entry.key == key:
                    return entry.value
            raise KeyNotFoundError(f"key not found: {key!r}")
        return value

    def remove(self, key: K) -> V:
        self._validate_key(key)
        index = self._index(key)
        bucket = self._buckets[index]

        for position, entry in enumerate(bucket):
            if entry.key == key:
                removed = bucket.pop(position)
                self._size -= 1
                return removed.value

        raise KeyNotFoundError(f"key not found: {key!r}")

    def contains(self, key: K) -> bool:
        return self.get(key) is not None or any(
            entry.key == key for entry in self._buckets[self._index(key)]
        )

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[K]:
        for bucket in self._buckets:
            for entry in bucket:
                yield entry.key

    @property
    def load_factor(self) -> float:
        return self._size / len(self._buckets)

    @property
    def capacity(self) -> int:
        return len(self._buckets)

    @property
    def collision_count(self) -> int:
        return self._collisions

    @property
    def rehash_count(self) -> int:
        return self._rehashes

    def bucket_distribution(self) -> list[int]:
        return [len(bucket) for bucket in self._buckets]

    def debug_report(self) -> dict[str, object]:
        distribution = self.bucket_distribution()
        return {
            "size": self._size,
            "capacity": self.capacity,
            "load_factor": round(self.load_factor, 3),
            "collisions": self._collisions,
            "rehashes": self._rehashes,
            "longest_chain": max(distribution, default=0),
            "distribution": distribution,
        }


class OpenAddressingHashTable(Generic[K, V]):
    """
    Hash table using linear probing.

    EMPTY and DELETED are distinct states. DELETED slots must remain
    searchable so that a probe sequence is not accidentally terminated.
    """

    def __init__(
        self,
        capacity: int = 8,
        max_load_factor: float = 0.65,
    ):
        if capacity < 3:
            raise ValueError("capacity must be at least 3")
        if not 0.2 <= max_load_factor <= 0.9:
            raise ValueError("invalid load factor")

        self._keys: list[Optional[K]] = [None] * capacity
        self._values: list[Optional[V]] = [None] * capacity
        self._states: list[SlotState] = [SlotState.EMPTY] * capacity
        self._size = 0
        self._max_load_factor = max_load_factor
        self._deleted = 0
        self._probes = 0
        self._rehashes = 0

    def _index(self, key: K) -> int:
        return hash(key) % len(self._keys)

    def _find(self, key: K) -> tuple[Optional[int], int]:
        start = self._index(key)
        probes = 0

        for offset in range(len(self._keys)):
            index = (start + offset) % len(self._keys)
            probes += 1
            state = self._states[index]

            if state == SlotState.EMPTY:
                self._probes += probes
                return None, probes

            if state == SlotState.OCCUPIED and self._keys[index] == key:
                self._probes += probes
                return index, probes

        self._probes += probes
        return None, probes

    def _resize(self, new_capacity: int) -> None:
        old_items = [
            (self._keys[i], self._values[i])
            for i, state in enumerate(self._states)
            if state == SlotState.OCCUPIED
        ]

        self._keys = [None] * new_capacity
        self._values = [None] * new_capacity
        self._states = [SlotState.EMPTY] * new_capacity
        self._size = 0
        self._deleted = 0
        self._rehashes += 1

        for key, value in old_items:
            self._insert_without_resize(key, value)

    def _insert_without_resize(self, key: K, value: V) -> None:
        start = self._index(key)

        for offset in range(len(self._keys)):
            index = (start + offset) % len(self._keys)
            if self._states[index] != SlotState.OCCUPIED:
                self._keys[index] = key
                self._values[index] = value
                self._states[index] = SlotState.OCCUPIED
                self._size += 1
                return

        raise HashTableError("hash table is full")

    def put(self, key: K, value: V) -> None:
        if not hasattr(key, "__hash__") or hash(key) is None:
            raise TypeError("key must be hashable")

        existing, _ = self._find(key)
        if existing is not None:
            self._values[existing] = value
            return

        if (self._size + self._deleted + 1) / len(self._keys) > self._max_load_factor:
            self._resize(len(self._keys) * 2)

        self._insert_without_resize(key, value)

    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        index, _ = self._find(key)
        return default if index is None else self._values[index]

    def remove(self, key: K) -> V:
        index, _ = self._find(key)
        if index is None:
            raise KeyNotFoundError(f"key not found: {key!r}")

        value = self._values[index]
        self._keys[index] = None
        self._values[index] = None
        self._states[index] = SlotState.DELETED
        self._size -= 1
        self._deleted += 1
        return value  # type: ignore[return-value]

    @property
    def load_factor(self) -> float:
        return self._size / len(self._keys)

    def debug_report(self) -> dict[str, object]:
        return {
            "size": self._size,
            "capacity": len(self._keys),
            "load_factor": round(self.load_factor, 3),
            "deleted_slots": self._deleted,
            "total_probes": self._probes,
            "rehashes": self._rehashes,
        }


@dataclass(frozen=True)
class User:
    user_id: int
    name: str
    role: str


def run_examples() -> None:
    chained = HashTable[str, User](capacity=4)

    users = [
        User(101, "Asha", "developer"),
        User(102, "Ravi", "reviewer"),
        User(103, "Meera", "administrator"),
        User(104, "Karan", "developer"),
        User(105, "Nisha", "auditor"),
    ]

    for user in users:
        chained.put(str(user.user_id), user)

    print("Separate chaining")
    print(chained.debug_report())
    print(chained.require("103"))

    chained.put("103", User(103, "Meera", "security-admin"))
    print(chained.require("103"))

    removed = chained.remove("105")
    print("Removed:", removed)
    print("Contains 105:", chained.contains("105"))

    open_table = OpenAddressingHashTable[str, int](capacity=7)

    # These values deliberately create a small probing workload.
    for key, value in [
        ("A", 10),
        ("B", 20),
        ("C", 30),
        ("D", 40),
        ("E", 50),
    ]:
        open_table.put(key, value)

    print("\nLinear probing")
    print(open_table.debug_report())
    print("C =", open_table.get("C"))

    open_table.remove("C")
    print("C after deletion =", open_table.get("C", "missing"))
    open_table.put("C", 300)
    print("C after reinsertion =", open_table.get("C"))

    # Validation and failure handling.
    try:
        chained.add("103", users[2])
    except DuplicateKeyError as exc:
        print("Expected error:", exc)

    try:
        chained.require("999")
    except KeyNotFoundError as exc:
        print("Expected error:", exc)

    try:
        HashTable[list[int], int]().put([1, 2], 3)
    except TypeError as exc:
        print("Expected error:", exc)

    # Basic executable assertions.
    assert chained.require("101").name == "Asha"
    assert chained.require("103").role == "security-admin"
    assert not chained.contains("105")
    assert open_table.get("C") == 300
    assert open_table.get("missing") is None

    print("\nAssertions passed.")


if __name__ == "__main__":
    run_examples()
