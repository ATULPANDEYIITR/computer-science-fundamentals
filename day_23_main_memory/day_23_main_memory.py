"""
Main Memory: RAM, DRAM, SRAM, Memory Addressing, and Memory Allocation Basics
===========================================================================

A self-contained study and demonstration program covering main-memory concepts
from beginner to advanced level.

The program is intentionally simulation-oriented. Python cannot directly expose
physical RAM addresses of ordinary Python objects, so the script models memory
management explicitly while also demonstrating real Python object allocation,
references, mutability, copying, memory measurement, and allocation behavior.

Run:
    python main_memory.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import OrderedDict
from copy import copy, deepcopy
from enum import Enum
import gc
import random
import sys
import time
import tracemalloc
from typing import Any, Iterable, Optional


# ============================================================================
# 1. FUNDAMENTAL MEMORY UNITS
# ============================================================================

BYTES_PER_KIB = 1024
BYTES_PER_MIB = 1024 ** 2
BYTES_PER_GIB = 1024 ** 3


def format_bytes(number_of_bytes: int) -> str:
    """Convert a byte count into a readable binary-unit representation."""
    if number_of_bytes < 0:
        raise ValueError("Byte count cannot be negative.")

    if number_of_bytes < 1024:
        return f"{number_of_bytes} B"

    value = float(number_of_bytes)
    for unit in ("KiB", "MiB", "GiB", "TiB"):
        value /= 1024
        if value < 1024 or unit == "TiB":
            return f"{value:.2f} {unit}"

    return f"{number_of_bytes} B"


def print_memory_units() -> None:
    print("\n" + "=" * 78)
    print("1. MEMORY UNITS")
    print("=" * 78)

    examples = [
        ("1 byte", 1),
        ("1 KiB", 1024),
        ("1 MiB", 1024 ** 2),
        ("1 GiB", 1024 ** 3),
        ("1 TiB", 1024 ** 4),
    ]

    for name, value in examples:
        print(f"{name:<12} = {value:,} bytes")

    print("\nImportant distinction:")
    print("  1 KB  = 1,000 bytes in decimal notation.")
    print("  1 KiB = 1,024 bytes in binary notation.")
    print("Modern storage and memory specifications often use decimal prefixes,")
    print("while operating-system tools frequently use binary-derived quantities.")


# ============================================================================
# 2. BIT, BYTE, WORD, AND ADDRESSING
# ============================================================================

def demonstrate_binary_addressing() -> None:
    print("\n" + "=" * 78)
    print("2. MEMORY ADDRESSING")
    print("=" * 78)

    # A byte-addressable memory assigns one unique address to every byte.
    memory = bytearray(16)

    for address in range(len(memory)):
        memory[address] = address * 3

    print("Simulated 16-byte memory:")
    for address, value in enumerate(memory):
        print(
            f"address={address:2d} "
            f"binary_address={address:04b} "
            f"value={value:3d}"
        )

    print("\nIf a system has N address bits, it can represent 2^N addresses.")
    for address_bits in (8, 16, 32, 64):
        addressable_bytes = 2 ** address_bits
        print(
            f"{address_bits:2d}-bit address space -> "
            f"{format_bytes(addressable_bytes)} addressable bytes "
            f"under a byte-addressable model"
        )

    print("\nImportant caveat:")
    print("The width of a CPU register and the practical usable virtual address")
    print("space are related but are not necessarily identical. Modern systems")
    print("may use fewer virtual-address bits than the CPU's architectural width.")


# ============================================================================
# 3. RAM CONCEPTUAL MODEL
# ============================================================================

class MemoryAccessError(Exception):
    """Raised when a simulated memory access is invalid."""


class SimulatedRAM:
    """
    Simple byte-addressable RAM model.

    This model intentionally exposes operations that resemble low-level
    memory access. Real DRAM includes rows, columns, banks, refresh cycles,
    sense amplifiers, timing parameters, and controllers that are not modeled
    here.
    """

    def __init__(self, size_bytes: int):
        if size_bytes <= 0:
            raise ValueError("RAM size must be positive.")
        self._memory = bytearray(size_bytes)

    @property
    def size(self) -> int:
        return len(self._memory)

    def _validate_address(self, address: int, width: int = 1) -> None:
        if not isinstance(address, int):
            raise TypeError("Address must be an integer.")
        if address < 0:
            raise MemoryAccessError("Negative memory addresses are invalid.")
        if width <= 0:
            raise ValueError("Access width must be positive.")
        if address + width > self.size:
            raise MemoryAccessError(
                f"Access [{address}, {address + width}) exceeds "
                f"RAM size {self.size}."
            )

    def read_byte(self, address: int) -> int:
        self._validate_address(address)
        return self._memory[address]

    def write_byte(self, address: int, value: int) -> None:
        self._validate_address(address)
        if not 0 <= value <= 255:
            raise ValueError("A byte must contain a value from 0 to 255.")
        self._memory[address] = value

    def read(self, address: int, width: int) -> bytes:
        self._validate_address(address, width)
        return bytes(self._memory[address:address + width])

    def write(self, address: int, data: bytes | bytearray) -> None:
        self._validate_address(address, len(data))
        self._memory[address:address + len(data)] = data

    def dump(self, start: int = 0, length: int = 16) -> None:
        self._validate_address(start, length)
        data = self._memory[start:start + length]

        for offset in range(0, len(data), 8):
            chunk = data[offset:offset + 8]
            hex_values = " ".join(f"{byte:02X}" for byte in chunk)
            print(f"{start + offset:04X}: {hex_values}")


def demonstrate_simulated_ram() -> None:
    print("\n" + "=" * 78)
    print("3. BYTE-ADDRESSABLE RAM SIMULATION")
    print("=" * 78)

    ram = SimulatedRAM(64)

    ram.write_byte(10, 255)
    ram.write(20, b"HELLO")

    print("Byte at address 10:", ram.read_byte(10))
    print("Bytes at address 20:", ram.read(20, 5))
    print("\nMemory dump:")
    ram.dump(0, 32)

    print("\nInvalid access demonstration:")
    try:
        ram.read_byte(64)
    except MemoryAccessError as error:
        print("Caught:", error)


# ============================================================================
# 4. DRAM AND SRAM
# ============================================================================

class MemoryTechnology(Enum):
    DRAM = "DRAM"
    SRAM = "SRAM"


@dataclass
class MemoryCell:
    """
    Abstract memory-cell model.

    DRAM:
        Conceptually stores a bit as charge and needs periodic refresh.

    SRAM:
        Conceptually uses a stable circuit state and does not require DRAM-style
        periodic refresh while powered.
    """

    technology: MemoryTechnology
    bit: int = 0
    refresh_count: int = 0

    def __post_init__(self) -> None:
        if self.bit not in (0, 1):
            raise ValueError("A memory cell stores either 0 or 1.")

    def refresh(self) -> None:
        if self.technology == MemoryTechnology.DRAM:
            self.refresh_count += 1

    def read(self) -> int:
        return self.bit

    def write(self, bit: int) -> None:
        if bit not in (0, 1):
            raise ValueError("A memory cell accepts only 0 or 1.")
        self.bit = bit


def compare_dram_sram() -> None:
    print("\n" + "=" * 78)
    print("4. DRAM VERSUS SRAM")
    print("=" * 78)

    dram = MemoryCell(MemoryTechnology.DRAM, 1)
    sram = MemoryCell(MemoryTechnology.SRAM, 1)

    for _ in range(5):
        dram.refresh()
        sram.refresh()

    print(f"DRAM bit={dram.read()}, refreshes={dram.refresh_count}")
    print(f"SRAM bit={sram.read()}, refreshes={sram.refresh_count}")

    print(
        "\nDRAM is commonly used for main system memory because it offers "
        "high density at relatively low cost per bit."
    )
    print(
        "SRAM is commonly used for CPU caches because its cell design can "
        "provide very fast access without DRAM-style refresh."
    )

    print("\nSimplified comparison:")
    print("  DRAM: dense, relatively inexpensive, requires refresh.")
    print("  SRAM:  fast, less dense, more expensive per bit.")
    print("  Neither statement means every implementation has identical latency.")
    print("  Actual performance depends on architecture, hierarchy, timing,")
    print("  controller behavior, cache state, and workload.")


# ============================================================================
# 5. MEMORY HIERARCHY
# ============================================================================

@dataclass
class MemoryLevel:
    name: str
    technology: str
    relative_speed: str
    typical_role: str


def show_memory_hierarchy() -> None:
    print("\n" + "=" * 78)
    print("5. MEMORY HIERARCHY")
    print("=" * 78)

    hierarchy = [
        MemoryLevel("CPU registers", "Flip-flop/register structures",
                    "Extremely fast", "Immediate CPU operands and state"),
        MemoryLevel("L1 cache", "SRAM", "Very fast",
                    "Frequently used instructions/data"),
        MemoryLevel("L2 cache", "SRAM", "Very fast",
                    "Larger cache close to CPU core"),
        MemoryLevel("L3 cache", "SRAM", "Fast",
                    "Larger shared or semi-shared cache"),
        MemoryLevel("Main memory", "DRAM", "Slower than cache",
                    "Active program and data storage"),
        MemoryLevel("SSD/storage", "Flash", "Much slower than RAM",
                    "Persistent data and programs"),
    ]

    for level in hierarchy:
        print(
            f"{level.name:<18} | {level.technology:<28} | "
            f"{level.relative_speed:<20} | {level.typical_role}"
        )

    print(
        "\nThe hierarchy exists because a single technology does not simultaneously "
        "maximize speed, capacity, persistence, density, and cost efficiency."
    )


# ============================================================================
# 6. MEMORY ALLOCATION BASICS
# ============================================================================

@dataclass
class Allocation:
    address: int
    size: int
    owner: str
    data: bytearray = field(repr=False)

    @property
    def end_address(self) -> int:
        return self.address + self.size


class AllocationError(Exception):
    """Raised for invalid simulated allocation operations."""


class FirstFitAllocator:
    """
    Educational variable-size allocator.

    Free memory is represented as a list of intervals. Allocation uses a
    first-fit policy: the first sufficiently large free block is selected.

    This demonstrates concepts related to:
      - contiguous allocation
      - free blocks
      - fragmentation
      - allocation and release
      - coalescing adjacent free blocks
    """

    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("Capacity must be positive.")

        self.capacity = capacity
        self.free_blocks: list[tuple[int, int]] = [(0, capacity)]
        self.allocations: dict[int, Allocation] = {}
        self.next_allocation_id = 1

    def _coalesce(self) -> None:
        self.free_blocks.sort()

        merged: list[tuple[int, int]] = []

        for start, size in self.free_blocks:
            if not merged:
                merged.append((start, size))
                continue

            previous_start, previous_size = merged[-1]
            previous_end = previous_start + previous_size

            if start <= previous_end:
                new_end = max(previous_end, start + size)
                merged[-1] = (previous_start, new_end - previous_start)
            else:
                merged.append((start, size))

        self.free_blocks = merged

    def allocate(self, size: int, owner: str) -> int:
        if size <= 0:
            raise AllocationError("Allocation size must be positive.")

        for index, (start, free_size) in enumerate(self.free_blocks):
            if free_size >= size:
                allocation_id = self.next_allocation_id
                self.next_allocation_id += 1

                allocation = Allocation(
                    address=start,
                    size=size,
                    owner=owner,
                    data=bytearray(size),
                )

                self.allocations[allocation_id] = allocation

                if free_size == size:
                    del self.free_blocks[index]
                else:
                    self.free_blocks[index] = (
                        start + size,
                        free_size - size,
                    )

                return allocation_id

        raise AllocationError(
            f"Unable to allocate {size} bytes. "
            f"Total free={self.total_free()} bytes."
        )

    def free(self, allocation_id: int) -> None:
        allocation = self.allocations.pop(allocation_id, None)

        if allocation is None:
            raise AllocationError(
                f"Allocation ID {allocation_id} does not exist or was already freed."
            )

        self.free_blocks.append((allocation.address, allocation.size))
        self._coalesce()

    def total_free(self) -> int:
        return sum(size for _, size in self.free_blocks)

    def total_allocated(self) -> int:
        return sum(allocation.size for allocation in self.allocations.values())

    def largest_free_block(self) -> int:
        return max((size for _, size in self.free_blocks), default=0)

    def fragmentation_report(self) -> dict[str, float | int]:
        total_free = self.total_free()
        largest = self.largest_free_block()

        if total_free == 0:
            external_fragmentation = 0.0
        else:
            external_fragmentation = 1 - (largest / total_free)

        return {
            "total_free": total_free,
            "free_blocks": len(self.free_blocks),
            "largest_free_block": largest,
            "external_fragmentation_ratio": external_fragmentation,
        }

    def print_state(self) -> None:
        print("\nAllocator state:")
        print(f"Capacity: {self.capacity} bytes")
        print(f"Allocated: {self.total_allocated()} bytes")
        print(f"Free: {self.total_free()} bytes")

        print("\nAllocated blocks:")
        for allocation_id, allocation in sorted(
            self.allocations.items(),
            key=lambda item: item[1].address,
        ):
            print(
                f"  id={allocation_id:<2} "
                f"address={allocation.address:<3} "
                f"size={allocation.size:<3} "
                f"owner={allocation.owner}"
            )

        print("Free blocks:")
        for start, size in self.free_blocks:
            print(f"  address={start:<3} size={size:<3}")

        report = self.fragmentation_report()
        print(
            "Fragmentation ratio: "
            f"{report['external_fragmentation_ratio']:.2%}"
        )


def demonstrate_memory_allocation() -> None:
    print("\n" + "=" * 78)
    print("6. MEMORY ALLOCATION AND FRAGMENTATION")
    print("=" * 78)

    allocator = FirstFitAllocator(128)

    process_a = allocator.allocate(20, "Process A")
    process_b = allocator.allocate(30, "Process B")
    process_c = allocator.allocate(25, "Process C")

    allocator.print_state()

    print("\nFreeing Process B...")
    allocator.free(process_b)
    allocator.print_state()

    print("\nAllocating 15 bytes into the newly available region...")
    process_d = allocator.allocate(15, "Process D")
    allocator.print_state()

    print("\nFreeing A, C, and D to demonstrate coalescing...")
    allocator.free(process_a)
    allocator.free(process_c)
    allocator.free(process_d)
    allocator.print_state()


# ============================================================================
# 7. STACK-LIKE AND HEAP-LIKE CONCEPTS
# ============================================================================

def recursive_stack_demo(depth: int, current: int = 0) -> int:
    """
    Demonstrates the conceptual idea of call-stack frames.

    Each recursive invocation creates another Python call frame. The exact
    physical layout is implementation-dependent and should not be interpreted
    as a direct map of Python objects onto hardware RAM.
    """
    if current >= depth:
        return current

    return recursive_stack_demo(depth, current + 1)


def demonstrate_stack_and_heap_concepts() -> None:
    print("\n" + "=" * 78)
    print("7. STACK-LIKE AND HEAP-LIKE CONCEPTS")
    print("=" * 78)

    local_number = 42
    local_text = "memory"
    dynamic_list = [1, 2, 3, 4, 5]

    print("Example local values:", local_number, local_text)
    print("Example dynamically created object:", dynamic_list)

    print("\nRecursive call depth result:", recursive_stack_demo(10))

    print(
        "\nConceptual model:"
        "\n  Call stack -> function calls, parameters, local execution state."
        "\n  Heap      -> dynamically managed objects and storage."
        "\n"
        "\nPython's implementation is more complicated than this simplified "
        "model. CPython manages Python objects on a managed heap, and Python "
        "variables generally hold references to objects rather than embedding "
        "the complete object directly in the variable."
    )


# ============================================================================
# 8. PYTHON REFERENCES, IDENTITY, MUTABILITY, AND COPYING
# ============================================================================

def demonstrate_python_object_memory() -> None:
    print("\n" + "=" * 78)
    print("8. PYTHON OBJECT REFERENCES AND COPYING")
    print("=" * 78)

    first = [10, 20, 30]
    second = first

    print("first is second:", first is second)
    print("first id:", id(first))
    print("second id:", id(second))

    second.append(40)
    print("After modifying second:")
    print("first:", first)
    print("second:", second)

    independent = first.copy()
    independent.append(50)

    print("\nShallow list copy:")
    print("first:", first)
    print("independent:", independent)
    print("first is independent:", first is independent)

    nested = [[1, 2], [3, 4]]
    shallow = copy(nested)
    deep = deepcopy(nested)

    nested[0].append(99)

    print("\nNested structures:")
    print("original:", nested)
    print("shallow :", shallow)
    print("deep    :", deep)

    print(
        "\nThe shallow copy creates a new outer container but keeps references "
        "to the original inner lists. Deep copy recursively duplicates nested "
        "objects where possible."
    )


# ============================================================================
# 9. PYTHON MEMORY MEASUREMENT
# ============================================================================

def demonstrate_memory_measurement() -> None:
    print("\n" + "=" * 78)
    print("9. PYTHON MEMORY MEASUREMENT")
    print("=" * 78)

    small_integer = 100
    large_list = list(range(10_000))

    print("sys.getsizeof(100):", sys.getsizeof(small_integer), "bytes")
    print("sys.getsizeof(large_list):", sys.getsizeof(large_list), "bytes")

    print(
        "\nsys.getsizeof() reports the size of the object itself and does not "
        "necessarily include all referenced objects."
    )

    tracemalloc.start()

    snapshot_before = tracemalloc.take_snapshot()

    temporary_data = [
        {"index": index, "value": index * index}
        for index in range(20_000)
    ]

    snapshot_after = tracemalloc.take_snapshot()

    differences = snapshot_after.compare_to(snapshot_before, "lineno")
    print("\nTop allocations observed by tracemalloc:")
    for statistic in differences[:5]:
        print(statistic)

    del temporary_data
    gc.collect()

    current, peak = tracemalloc.get_traced_memory()
    print(
        f"\nCurrent traced memory: {format_bytes(current)}"
        f"\nPeak traced memory:    {format_bytes(peak)}"
    )

    tracemalloc.stop()


# ============================================================================
# 10. ALLOCATION STRATEGIES
# ============================================================================

def simulate_first_fit(blocks: list[int], requests: list[int]) -> list[Optional[int]]:
    remaining = blocks.copy()
    placements: list[Optional[int]] = []

    for request in requests:
        selected_index = None

        for index, available in enumerate(remaining):
            if available >= request:
                selected_index = index
                break

        if selected_index is None:
            placements.append(None)
            continue

        placements.append(selected_index)
        remaining[selected_index] -= request

    return placements


def simulate_best_fit(blocks: list[int], requests: list[int]) -> list[Optional[int]]:
    remaining = blocks.copy()
    placements: list[Optional[int]] = []

    for request in requests:
        candidates = [
            (available, index)
            for index, available in enumerate(remaining)
            if available >= request
        ]

        if not candidates:
            placements.append(None)
            continue

        _, selected_index = min(candidates)
        placements.append(selected_index)
        remaining[selected_index] -= request

    return placements


def simulate_worst_fit(blocks: list[int], requests: list[int]) -> list[Optional[int]]:
    remaining = blocks.copy()
    placements: list[Optional[int]] = []

    for request in requests:
        candidates = [
            (available, index)
            for index, available in enumerate(remaining)
            if available >= request
        ]

        if not candidates:
            placements.append(None)
            continue

        _, selected_index = max(candidates)
        placements.append(selected_index)
        remaining[selected_index] -= request

    return placements


def demonstrate_allocation_policies() -> None:
    print("\n" + "=" * 78)
    print("10. FIRST-FIT, BEST-FIT, AND WORST-FIT")
    print("=" * 78)

    blocks = [100, 500, 200, 300, 600]
    requests = [212, 417, 112, 426]

    strategies = {
        "First-fit": simulate_first_fit,
        "Best-fit": simulate_best_fit,
        "Worst-fit": simulate_worst_fit,
    }

    print("Free blocks:", blocks)
    print("Requests:   ", requests)

    for name, strategy in strategies.items():
        placements = strategy(blocks, requests)
        print(f"{name:<10}: {placements}")

    print(
        "\nThese policies illustrate allocation decisions but are simplified "
        "models. Production allocators use more sophisticated data structures, "
        "alignment rules, size classes, caches, arenas, and concurrency controls."
    )


# ============================================================================
# 11. MEMORY ALIGNMENT
# ============================================================================

def align_up(address: int, alignment: int) -> int:
    if address < 0:
        raise ValueError("Address cannot be negative.")
    if alignment <= 0 or alignment & (alignment - 1):
        raise ValueError("Alignment must be a positive power of two.")

    return (address + alignment - 1) // alignment * alignment


def demonstrate_alignment() -> None:
    print("\n" + "=" * 78)
    print("11. MEMORY ALIGNMENT")
    print("=" * 78)

    addresses = [0, 1, 7, 8, 9, 15, 16, 17]
    alignment = 8

    for address in addresses:
        print(
            f"address={address:2d} -> aligned_address="
            f"{align_up(address, alignment):2d}"
        )

    print(
        "\nAlignment can improve access efficiency and may be required by "
        "hardware instructions or data types. Padding can increase memory use."
    )


# ============================================================================
# 12. CACHE LOCALITY
# ============================================================================

def row_major_sum(matrix: list[list[int]]) -> int:
    total = 0

    for row in matrix:
        for value in row:
            total += value

    return total


def column_major_sum(matrix: list[list[int]]) -> int:
    total = 0

    if not matrix:
        return 0

    rows = len(matrix)
    columns = len(matrix[0])

    for column in range(columns):
        for row in range(rows):
            total += matrix[row][column]

    return total


def demonstrate_locality() -> None:
    print("\n" + "=" * 78)
    print("12. LOCALITY AND CACHE BEHAVIOR")
    print("=" * 78)

    matrix = [[row * 500 + column for column in range(500)] for row in range(500)]

    start = time.perf_counter()
    first_result = row_major_sum(matrix)
    row_time = time.perf_counter() - start

    start = time.perf_counter()
    second_result = column_major_sum(matrix)
    column_time = time.perf_counter() - start

    print("Row-major result:   ", first_result)
    print("Column-major result:", second_result)
    print(f"Row traversal time: {row_time:.6f} seconds")
    print(f"Column traversal:   {column_time:.6f} seconds")

    print(
        "\nThe exact timing depends on Python implementation, hardware, and "
        "system load. The important principle is spatial locality: accessing "
        "nearby memory locations tends to work well with cache lines."
    )


# ============================================================================
# 13. PAGE-BASED VIRTUAL MEMORY MODEL
# ============================================================================

@dataclass
class PageTableEntry:
    virtual_page: int
    physical_frame: int
    present: bool = True
    writable: bool = True


class VirtualMemorySimulator:
    """
    Small virtual-memory translation model.

    A virtual address is divided into:
        virtual page number + page offset.

    The page table maps virtual pages to physical frames.
    """

    def __init__(self, page_size: int, physical_frames: int):
        if page_size <= 0 or page_size & (page_size - 1):
            raise ValueError("Page size must be a positive power of two.")
        if physical_frames <= 0:
            raise ValueError("Physical frame count must be positive.")

        self.page_size = page_size
        self.physical_frames = physical_frames
        self.page_table: dict[int, PageTableEntry] = {}

    def map_page(self, virtual_page: int, physical_frame: int) -> None:
        if virtual_page < 0:
            raise ValueError("Virtual page cannot be negative.")
        if not 0 <= physical_frame < self.physical_frames:
            raise ValueError("Physical frame is outside the simulated RAM.")

        self.page_table[virtual_page] = PageTableEntry(
            virtual_page,
            physical_frame,
        )

    def translate(self, virtual_address: int) -> int:
        if virtual_address < 0:
            raise MemoryAccessError("Virtual address cannot be negative.")

        virtual_page, offset = divmod(virtual_address, self.page_size)

        entry = self.page_table.get(virtual_page)

        if entry is None or not entry.present:
            raise MemoryAccessError(
                f"Page fault: virtual page {virtual_page} is not present."
            )

        return entry.physical_frame * self.page_size + offset


def demonstrate_virtual_memory() -> None:
    print("\n" + "=" * 78)
    print("13. VIRTUAL-TO-PHYSICAL ADDRESS TRANSLATION")
    print("=" * 78)

    vm = VirtualMemorySimulator(page_size=256, physical_frames=8)

    vm.map_page(0, 3)
    vm.map_page(1, 7)
    vm.map_page(2, 1)

    for virtual_address in (0, 10, 255, 256, 300, 512, 700):
        try:
            physical_address = vm.translate(virtual_address)
            print(
                f"virtual={virtual_address:3d} -> "
                f"physical={physical_address:4d}"
            )
        except MemoryAccessError as error:
            print(f"virtual={virtual_address:3d} -> {error}")

    print(
        "\nThis model demonstrates the conceptual role of page tables. "
        "Real CPUs use hardware translation mechanisms, TLBs, protection "
        "bits, multiple page-table levels, and operating-system page-fault handling."
    )


# ============================================================================
# 14. SIMPLE SYSTEM MONITOR
# ============================================================================

@dataclass
class MemorySnapshot:
    timestamp: float
    allocated_bytes: int
    process_count: int
    cache_simulated_bytes: int


class SystemMemoryMonitor:
    """
    Portable educational monitor.

    This class intentionally monitors memory statistics produced by the
    simulator instead of requiring operating-system-specific APIs.
    """

    def __init__(self):
        self.snapshots: list[MemorySnapshot] = []

    def record(
        self,
        allocated_bytes: int,
        process_count: int,
        cache_simulated_bytes: int,
    ) -> None:
        self.snapshots.append(
            MemorySnapshot(
                timestamp=time.time(),
                allocated_bytes=allocated_bytes,
                process_count=process_count,
                cache_simulated_bytes=cache_simulated_bytes,
            )
        )

    def report(self) -> None:
        print("\nSystem monitor report:")

        for index, snapshot in enumerate(self.snapshots, start=1):
            print(
                f"  sample={index:<2} "
                f"allocated={format_bytes(snapshot.allocated_bytes):>10} "
                f"processes={snapshot.process_count:<2} "
                f"cache={format_bytes(snapshot.cache_simulated_bytes):>10}"
            )

        if self.snapshots:
            latest = self.snapshots[-1]
            print(
                f"\nLatest allocated memory: "
                f"{format_bytes(latest.allocated_bytes)}"
            )


def demonstrate_system_monitor() -> None:
    print("\n" + "=" * 78)
    print("14. SYSTEM MEMORY MONITOR")
    print("=" * 78)

    monitor = SystemMemoryMonitor()

    for process_count in range(1, 6):
        simulated_allocated = process_count * 120 * 1024
        simulated_cache = min(process_count * 32 * 1024, 128 * 1024)

        monitor.record(
            allocated_bytes=simulated_allocated,
            process_count=process_count,
            cache_simulated_bytes=simulated_cache,
        )

    monitor.report()


# ============================================================================
# 15. ERROR CONDITIONS AND EDGE CASES
# ============================================================================

def demonstrate_edge_cases() -> None:
    print("\n" + "=" * 78)
    print("15. EDGE CASES AND FAILURE CONDITIONS")
    print("=" * 78)

    ram = SimulatedRAM(8)

    cases = [
        ("negative address", lambda: ram.read_byte(-1)),
        ("out-of-range address", lambda: ram.read_byte(8)),
        ("invalid byte value", lambda: ram.write_byte(0, 256)),
    ]

    for description, operation in cases:
        try:
            operation()
        except (MemoryAccessError, ValueError, TypeError) as error:
            print(f"{description:<24}: handled -> {error}")

    allocator = FirstFitAllocator(32)

    try:
        allocator.allocate(64, "Too Large")
    except AllocationError as error:
        print(f"{'oversized allocation':<24}: handled -> {error}")

    block = allocator.allocate(16, "Temporary")

    try:
        allocator.free(block)
        allocator.free(block)
    except AllocationError as error:
        print(f"{'double free':<24}: handled -> {error}")


# ============================================================================
# 16. MEMORY LEAK CONCEPT
# ============================================================================

class LeakSimulation:
    """
    Simulates a logical memory leak by retaining references.

    In a garbage-collected language, a true leak often means objects remain
    reachable through an unintended reference. The allocator itself is not
    necessarily the direct cause.
    """

    def __init__(self):
        self.retained_objects: list[list[int]] = []

    def create_retained_object(self, size: int) -> None:
        self.retained_objects.append([0] * size)

    def release_all(self) -> None:
        self.retained_objects.clear()


def demonstrate_logical_memory_leak() -> None:
    print("\n" + "=" * 78)
    print("16. MEMORY LEAK CONCEPT")
    print("=" * 78)

    tracemalloc.start()
    leak_simulation = LeakSimulation()

    for _ in range(10):
        leak_simulation.create_retained_object(10_000)

    current, peak = tracemalloc.get_traced_memory()

    print("Retained objects:", len(leak_simulation.retained_objects))
    print("Current traced memory:", format_bytes(current))
    print("Peak traced memory:", format_bytes(peak))

    leak_simulation.release_all()
    gc.collect()

    current_after, _ = tracemalloc.get_traced_memory()
    print("After releasing references:", format_bytes(current_after))

    tracemalloc.stop()

    print(
        "\nThe important concept is reachability. Garbage collection can reclaim "
        "objects only when they are no longer reachable according to the runtime's "
        "memory-management rules."
    )


# ============================================================================
# 17. PERFORMANCE AND ALGORITHM COMPLEXITY
# ============================================================================

def benchmark_allocation_search() -> None:
    print("\n" + "=" * 78)
    print("17. PERFORMANCE CONSIDERATIONS")
    print("=" * 78)

    blocks = [random.randint(64, 4096) for _ in range(20_000)]
    requests = [random.randint(32, 2048) for _ in range(5_000)]

    start = time.perf_counter()
    first_fit_results = simulate_first_fit(blocks, requests)
    elapsed = time.perf_counter() - start

    successful = sum(result is not None for result in first_fit_results)

    print(f"Requests processed: {len(requests):,}")
    print(f"Successful placements: {successful:,}")
    print(f"Elapsed time: {elapsed:.4f} seconds")

    print(
        "\nThe simple first-fit implementation can require scanning many free "
        "blocks. Its worst-case behavior is approximately O(B * R), where B "
        "is the number of blocks and R is the number of allocation requests."
    )
    print(
        "Production allocators use specialized structures to reduce search "
        "cost and improve locality, fragmentation behavior, and concurrency."
    )


# ============================================================================
# 18. PROTECTION CONCEPTS
# ============================================================================

@dataclass
class ProtectedRegion:
    start: int
    end: int
    readable: bool
    writable: bool
    executable: bool
    owner: str


class ProtectedMemory:
    """Educational model of memory permissions."""

    def __init__(self, size: int):
        if size <= 0:
            raise ValueError("Memory size must be positive.")

        self.size = size
        self.regions: list[ProtectedRegion] = []

    def add_region(
        self,
        start: int,
        end: int,
        *,
        readable: bool,
        writable: bool,
        executable: bool,
        owner: str,
    ) -> None:
        if not (0 <= start < end <= self.size):
            raise ValueError("Invalid region boundaries.")

        self.regions.append(
            ProtectedRegion(
                start,
                end,
                readable,
                writable,
                executable,
                owner,
            )
        )

    def check(self, address: int, operation: str) -> bool:
        for region in self.regions:
            if region.start <= address < region.end:
                permission = {
                    "read": region.readable,
                    "write": region.writable,
                    "execute": region.executable,
                }.get(operation)

                if permission is None:
                    raise ValueError("Unknown memory operation.")

                return permission

        return False


def demonstrate_memory_protection() -> None:
    print("\n" + "=" * 78)
    print("18. MEMORY PROTECTION")
    print("=" * 78)

    memory = ProtectedMemory(1024)

    memory.add_region(
        0,
        256,
        readable=True,
        writable=False,
        executable=True,
        owner="Code",
    )

    memory.add_region(
        256,
        768,
        readable=True,
        writable=True,
        executable=False,
        owner="Data",
    )

    memory.add_region(
        768,
        1024,
        readable=True,
        writable=False,
        executable=False,
        owner="Read-only data",
    )

    tests = [
        (100, "read"),
        (100, "write"),
        (100, "execute"),
        (500, "read"),
        (500, "write"),
        (500, "execute"),
        (900, "write"),
    ]

    for address, operation in tests:
        allowed = memory.check(address, operation)
        print(
            f"address={address:3d} operation={operation:<7} "
            f"allowed={allowed}"
        )

    print(
        "\nReal operating systems use hardware-supported page permissions and "
        "process isolation to prevent arbitrary access across protected regions."
    )


# ============================================================================
# 19. INTEGRATED MEMORY WORKLOAD
# ============================================================================

@dataclass
class Process:
    process_id: int
    name: str
    allocation_id: Optional[int] = None
    state: str = "created"


class MemoryManager:
    """Combines process tracking with the educational allocator."""

    def __init__(self, capacity: int):
        self.allocator = FirstFitAllocator(capacity)
        self.processes: dict[int, Process] = {}
        self.next_process_id = 1

    def create_process(self, name: str, memory_required: int) -> int:
        process_id = self.next_process_id
        self.next_process_id += 1

        allocation_id = self.allocator.allocate(
            memory_required,
            f"Process {process_id}: {name}",
        )

        self.processes[process_id] = Process(
            process_id=process_id,
            name=name,
            allocation_id=allocation_id,
            state="running",
        )

        return process_id

    def terminate_process(self, process_id: int) -> None:
        process = self.processes.get(process_id)

        if process is None:
            raise ValueError(f"Process {process_id} does not exist.")

        if process.state == "terminated":
            raise ValueError(f"Process {process_id} is already terminated.")

        if process.allocation_id is not None:
            self.allocator.free(process.allocation_id)

        process.state = "terminated"

    def report(self) -> None:
        print("\nProcess table:")

        for process in self.processes.values():
            print(
                f"  PID={process.process_id:<2} "
                f"name={process.name:<15} "
                f"state={process.state:<10} "
                f"allocation={process.allocation_id}"
            )

        self.allocator.print_state()


def demonstrate_integrated_workload() -> None:
    print("\n" + "=" * 78)
    print("19. INTEGRATED MEMORY WORKLOAD")
    print("=" * 78)

    manager = MemoryManager(1024)

    browser = manager.create_process("Browser", 300)
    editor = manager.create_process("Editor", 180)
    database = manager.create_process("Database", 350)

    manager.report()

    print("\nTerminating Editor...")
    manager.terminate_process(editor)
    manager.report()

    print("\nCreating Compiler...")
    compiler = manager.create_process("Compiler", 160)
    print("Compiler PID:", compiler)
    manager.report()

    print(
        "\nThis small model connects allocation, process lifetime, release, "
        "free-space management, and fragmentation into one workflow."
    )


# ============================================================================
# 20. KNOWLEDGE CHECK
# ============================================================================

def knowledge_check() -> None:
    print("\n" + "=" * 78)
    print("20. QUICK KNOWLEDGE CHECK")
    print("=" * 78)

    questions = [
        (
            "What does DRAM require that SRAM does not?",
            "Periodic refresh to preserve stored charge."
        ),
        (
            "What does a memory address identify in a byte-addressable system?",
            "A byte location in the address space."
        ),
        (
            "What is external fragmentation?",
            "Free memory divided into separate blocks that may be individually too small for a request."
        ),
        (
            "Why is cache locality important?",
            "Nearby or recently accessed data may be served efficiently by cache mechanisms."
        ),
        (
            "What is virtual memory?",
            "An address-space abstraction that maps virtual addresses to physical memory and other backing resources."
        ),
        (
            "What is a page fault?",
            "An exception or trap caused when a required virtual-memory page is not currently available in the required physical-memory state."
        ),
    ]

    for number, (question, answer) in enumerate(questions, start=1):
        print(f"\n{number}. {question}")
        print(f"   Answer: {answer}")


# ============================================================================
# 21. MAIN PROGRAM
# ============================================================================

def main() -> None:
    print("=" * 78)
    print("MAIN MEMORY STUDY PROGRAM")
    print("RAM | DRAM | SRAM | ADDRESSING | ALLOCATION | PROTECTION | MONITORING")
    print("=" * 78)

    print_memory_units()
    demonstrate_binary_addressing()
    demonstrate_simulated_ram()
    compare_dram_sram()
    show_memory_hierarchy()
    demonstrate_memory_allocation()
    demonstrate_stack_and_heap_concepts()
    demonstrate_python_object_memory()
    demonstrate_memory_measurement()
    demonstrate_allocation_policies()
    demonstrate_alignment()
    demonstrate_locality()
    demonstrate_virtual_memory()
    demonstrate_system_monitor()
    demonstrate_edge_cases()
    demonstrate_logical_memory_leak()
    benchmark_allocation_search()
    demonstrate_memory_protection()
    demonstrate_integrated_workload()
    knowledge_check()

    print("\n" + "=" * 78)
    print("END OF MAIN MEMORY STUDY PROGRAM")
    print("=" * 78)


if __name__ == "__main__":
    main()
