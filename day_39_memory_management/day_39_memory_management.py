from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional
import random


class AllocationError(Exception):
    """Raised when a memory allocation request cannot be satisfied."""


class Strategy(Enum):
    FIRST_FIT = "first-fit"
    BEST_FIT = "best-fit"
    WORST_FIT = "worst-fit"


@dataclass
class Block:
    start: int
    size: int
    allocated: bool = False
    owner: Optional[str] = None

    @property
    def end(self) -> int:
        return self.start + self.size

    def label(self) -> str:
        if self.allocated:
            return f"{self.owner}:{self.size}"
        return f"FREE:{self.size}"


class ContiguousMemory:
    """
    A variable-partition contiguous memory allocator.

    Each allocation receives one physically contiguous region. Free regions
    are represented explicitly and are merged when adjacent free blocks meet.
    """

    def __init__(self, total_size: int, strategy: Strategy = Strategy.FIRST_FIT):
        if total_size <= 0:
            raise ValueError("total_size must be positive")
        self.total_size = total_size
        self.strategy = strategy
        self.blocks = [Block(0, total_size)]

    def _validate_request(self, owner: str, size: int) -> None:
        if not owner or not owner.strip():
            raise ValueError("owner must be a non-empty identifier")
        if size <= 0:
            raise ValueError("allocation size must be positive")
        if any(block.allocated and block.owner == owner for block in self.blocks):
            raise AllocationError(f"{owner} already owns an allocation")

    def _candidate_indexes(self, size: int) -> list[int]:
        return [
            index
            for index, block in enumerate(self.blocks)
            if not block.allocated and block.size >= size
        ]

    def _select_candidate(self, size: int) -> int:
        candidates = self._candidate_indexes(size)
        if not candidates:
            raise AllocationError(
                f"no contiguous free block can satisfy {size} units"
            )

        if self.strategy == Strategy.FIRST_FIT:
            return candidates[0]

        if self.strategy == Strategy.BEST_FIT:
            return min(candidates, key=lambda i: self.blocks[i].size)

        return max(candidates, key=lambda i: self.blocks[i].size)

    def allocate(self, owner: str, size: int) -> int:
        self._validate_request(owner, size)
        index = self._select_candidate(size)
        block = self.blocks[index]

        if block.size == size:
            block.allocated = True
            block.owner = owner
            return block.start

        allocated = Block(block.start, size, True, owner)
        remainder = Block(block.start + size, block.size - size)
        self.blocks[index:index + 1] = [allocated, remainder]
        return allocated.start

    def free(self, owner: str) -> None:
        for block in self.blocks:
            if block.allocated and block.owner == owner:
                block.allocated = False
                block.owner = None
                self._coalesce()
                return
        raise AllocationError(f"no allocation exists for {owner}")

    def _coalesce(self) -> None:
        merged: list[Block] = []

        for block in self.blocks:
            if (
                merged
                and not merged[-1].allocated
                and not block.allocated
                and merged[-1].end == block.start
            ):
                merged[-1].size += block.size
            else:
                merged.append(block)

        self.blocks = merged

    def compact(self) -> None:
        """
        Move allocated blocks toward address zero.

        Compaction eliminates external fragmentation but requires relocation
        of allocated objects and therefore represents a costly operation in a
        real memory-management system.
        """
        allocated = [block for block in self.blocks if block.allocated]
        new_blocks: list[Block] = []
        cursor = 0

        for block in allocated:
            new_blocks.append(Block(cursor, block.size, True, block.owner))
            cursor += block.size

        if cursor < self.total_size:
            new_blocks.append(Block(cursor, self.total_size - cursor))

        self.blocks = new_blocks

    def free_space(self) -> int:
        return sum(block.size for block in self.blocks if not block.allocated)

    def largest_free_block(self) -> int:
        free_blocks = [block.size for block in self.blocks if not block.allocated]
        return max(free_blocks, default=0)

    def external_fragmentation(self) -> int:
        """
        Free space that is unusable for an allocation of the largest
        contiguous free region.

        A common practical indicator is:
            total_free - largest_free_block
        """
        return self.free_space() - self.largest_free_block()

    def internal_fragmentation(self) -> int:
        """
        Variable-sized exact allocation creates no intentional padding here.
        The method is included to make the distinction explicit.

        Fixed-size allocation schemes can have internal fragmentation because
        an allocated unit may exceed the requested object size.
        """
        return 0

    def visualize(self, width: int = 70) -> str:
        if width <= 0:
            raise ValueError("width must be positive")

        line = [" "] * width
        for block in self.blocks:
            left = round(block.start / self.total_size * width)
            right = round(block.end / self.total_size * width)
            right = max(left + 1, min(width, right))
            marker = "#" if block.allocated else "."
            for position in range(left, right):
                line[position] = marker

        return "".join(line)

    def report(self) -> str:
        rows = [
            f"Strategy: {self.strategy.value}",
            f"Total memory: {self.total_size}",
            f"Free memory: {self.free_space()}",
            f"Largest free block: {self.largest_free_block()}",
            f"External fragmentation: {self.external_fragmentation()}",
            f"Internal fragmentation: {self.internal_fragmentation()}",
            f"Layout: {self.visualize()}",
            "",
            "Address range      State",
            "--------------------------",
        ]

        for block in self.blocks:
            state = "ALLOCATED" if block.allocated else "FREE"
            owner = block.owner or "-"
            rows.append(
                f"{block.start:5d}..{block.end - 1:<5d}      "
                f"{state:<9} {owner}"
            )

        return "\n".join(rows)


def demonstrate_basic_contiguous_allocation() -> None:
    print("\n=== Contiguous allocation ===")

    memory = ContiguousMemory(100, Strategy.FIRST_FIT)
    memory.allocate("Process-A", 20)
    memory.allocate("Process-B", 30)
    memory.allocate("Process-C", 15)

    print(memory.report())

    memory.free("Process-B")
    print("\nAfter releasing Process-B:")
    print(memory.report())

    try:
        memory.allocate("Process-D", 35)
    except AllocationError as error:
        print(f"\nAllocation failed: {error}")
        print(
            "Although enough total memory may exist, the allocator requires "
            "one contiguous free region."
        )


def compare_allocation_strategies() -> None:
    print("\n=== Allocation strategy comparison ===")

    requests = [
        ("A", 18),
        ("B", 7),
        ("C", 25),
        ("D", 10),
        ("E", 14),
    ]

    for strategy in Strategy:
        memory = ContiguousMemory(100, strategy)

        for owner, size in requests:
            memory.allocate(owner, size)

        memory.free("B")
        memory.free("D")

        try:
            memory.allocate("F", 16)
            result = "allocated"
        except AllocationError:
            result = "failed"

        print(
            f"{strategy.value:10} -> allocation of 16 units: {result}, "
            f"largest free block={memory.largest_free_block()}, "
            f"external fragmentation={memory.external_fragmentation()}"
        )


def demonstrate_external_fragmentation() -> None:
    print("\n=== External fragmentation ===")

    memory = ContiguousMemory(120)

    memory.allocate("A", 20)
    memory.allocate("B", 20)
    memory.allocate("C", 20)
    memory.allocate("D", 20)
    memory.allocate("E", 20)

    memory.free("B")
    memory.free("D")

    print(memory.report())
    print(
        "\nTotal free space:",
        memory.free_space(),
        "| largest contiguous region:",
        memory.largest_free_block(),
    )

    try:
        memory.allocate("Large-Process", 30)
    except AllocationError:
        print(
            "30-unit allocation failed because free memory is split into "
            "separate regions."
        )

    memory.compact()
    print("\nAfter compaction:")
    print(memory.report())

    address = memory.allocate("Large-Process", 30)
    print(f"\nLarge-Process allocated after compaction at address {address}.")


def demonstrate_coalescing() -> None:
    print("\n=== Free-block coalescing ===")

    memory = ContiguousMemory(80)
    memory.allocate("A", 20)
    memory.allocate("B", 20)
    memory.allocate("C", 20)

    memory.free("B")
    print("After freeing B:")
    print(memory.report())

    memory.free("A")
    print("\nAfter freeing adjacent A and B:")
    print(memory.report())

    print(
        "\nCoalescing combines adjacent free blocks without moving allocated "
        "objects."
    )


def demonstrate_best_and_worst_fit() -> None:
    print("\n=== Best-fit and worst-fit behavior ===")

    for strategy in (Strategy.BEST_FIT, Strategy.WORST_FIT):
        memory = ContiguousMemory(100, strategy)
        memory.allocate("A", 20)
        memory.allocate("B", 35)
        memory.allocate("C", 15)
        memory.allocate("D", 10)

        memory.free("B")
        memory.free("D")

        print(f"\nBefore another allocation using {strategy.value}:")
        print(memory.report())

        memory.allocate("X", 8)
        print(f"\nAfter allocating X=8 using {strategy.value}:")
        print(memory.report())


def demonstrate_fixed_partition_internal_fragmentation() -> None:
    print("\n=== Fixed partition internal fragmentation ===")

    partition_size = 16
    requests = [5, 16, 7, 12]

    allocated = 0
    wasted = 0

    for request in requests:
        allocated += partition_size
        wasted += partition_size - request

    print(f"Partition size: {partition_size}")
    print(f"Requested memory: {sum(requests)}")
    print(f"Reserved memory: {allocated}")
    print(f"Internal fragmentation: {wasted}")

    print(
        "\nInternal fragmentation occurs inside allocated partitions. "
        "It is different from external fragmentation, which occurs between "
        "allocated regions."
    )


def simulate_random_workload(seed: int = 42) -> None:
    print("\n=== Random allocation workload ===")

    random.seed(seed)
    memory = ContiguousMemory(1000, Strategy.FIRST_FIT)
    active: dict[str, int] = {}

    for step in range(1, 101):
        if active and random.random() < 0.45:
            owner = random.choice(list(active))
            memory.free(owner)
            del active[owner]
        else:
            owner = f"P{step}"
            size = random.randint(10, 80)

            try:
                memory.allocate(owner, size)
                active[owner] = size
            except AllocationError:
                pass

    print(f"Active allocations: {len(active)}")
    print(f"Free memory: {memory.free_space()}")
    print(f"Largest free block: {memory.largest_free_block()}")
    print(f"External fragmentation: {memory.external_fragmentation()}")
    print(
        "A workload can have substantial total free memory while still "
        "having poor allocation success because the free memory is dispersed."
    )


def demonstrate_validation_and_failure_modes() -> None:
    print("\n=== Validation and failure handling ===")

    memory = ContiguousMemory(64)

    invalid_requests = [
        ("", 10),
        ("A", 0),
        ("B", -4),
    ]

    for owner, size in invalid_requests:
        try:
            memory.allocate(owner, size)
        except (ValueError, AllocationError) as error:
            print(f"Rejected {owner!r}, size={size}: {error}")

    memory.allocate("A", 20)

    try:
        memory.allocate("A", 10)
    except AllocationError as error:
        print(f"Duplicate allocation rejected: {error}")

    try:
        memory.free("Unknown")
    except AllocationError as error:
        print(f"Invalid release rejected: {error}")


def main() -> None:
    demonstrate_basic_contiguous_allocation()
    demonstrate_external_fragmentation()
    demonstrate_coalescing()
    compare_allocation_strategies()
    demonstrate_best_and_worst_fit()
    demonstrate_fixed_partition_internal_fragmentation()
    demonstrate_validation_and_failure_modes()
    simulate_random_workload()


if __name__ == "__main__":
    main()
