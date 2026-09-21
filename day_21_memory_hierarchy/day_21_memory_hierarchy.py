"""
MEMORY HIERARCHY
================
Registers, cache, RAM, secondary storage, locality, cache mapping,
replacement policies, write policies, virtual memory, TLBs, paging,
performance modeling, and practical system simulations.

This file is designed as a standalone executable study program.
It starts with simple concepts and gradually builds a small memory
hierarchy simulator.

No third-party packages are required.
"""

from __future__ import annotations

from collections import OrderedDict, deque
from dataclasses import dataclass
from enum import Enum
import math
import random
import statistics
import time
from typing import Iterable, Optional


# ============================================================================
# 1. FUNDAMENTAL IDEA
# ============================================================================

def section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def explain_basics() -> None:
    section("1. Memory hierarchy fundamentals")

    print(
        """
A computer does not normally store every piece of data in one identical
memory technology. Instead, it uses multiple levels.

A simplified hierarchy is:

    CPU registers
        ↓
    L1 cache
        ↓
    L2 cache
        ↓
    L3 cache
        ↓
    Main memory (RAM)
        ↓
    SSD / HDD
        ↓
    Long-term or remote storage

The general pattern is:

    Higher in the hierarchy:
        - smaller capacity
        - lower access latency
        - higher cost per byte
        - closer to the processor

    Lower in the hierarchy:
        - larger capacity
        - higher latency
        - lower cost per byte
        - farther from the processor

The hierarchy works because programs tend to reuse data and instructions.

Two central locality principles are:

1. Temporal locality:
   Data used recently is likely to be used again soon.

2. Spatial locality:
   Data located near recently accessed data is likely to be accessed soon.

A cache attempts to exploit both forms of locality.
"""
    )


# ============================================================================
# 2. UNITS, LATENCY, CAPACITY AND BANDWIDTH
# ============================================================================

def demonstrate_memory_metrics() -> None:
    section("2. Capacity, latency and bandwidth")

    capacities = {
        "4 KiB": 4 * 1024,
        "1 MiB": 1024**2,
        "1 GiB": 1024**3,
        "1 TiB": 1024**4,
    }

    print("Capacity conversions:")
    for label, bytes_value in capacities.items():
        print(f"  {label:8s} = {bytes_value:,} bytes")

    print(
        """
Latency and bandwidth are different concepts.

Latency answers:
    "How long before an access begins producing useful data?"

Bandwidth answers:
    "How much data can be transferred per unit of time?"

A memory system may have high bandwidth but still have significant latency.
This distinction matters for sequential versus random workloads.
"""
    )

    access_times_ns = {
        "Register": 0.3,
        "L1 cache": 1.0,
        "L2 cache": 4.0,
        "L3 cache": 12.0,
        "RAM": 80.0,
        "SSD": 100_000.0,
        "HDD": 5_000_000.0,
    }

    print("Illustrative access latencies:")
    for level, latency in access_times_ns.items():
        print(f"  {level:12s}: approximately {latency:,.1f} ns")

    print(
        "\nThese numbers are illustrative rather than universal hardware specifications."
    )


# ============================================================================
# 3. REGISTERS
# ============================================================================

def demonstrate_register_concept() -> None:
    section("3. CPU registers")

    print(
        """
Registers are tiny storage locations directly available to CPU instructions.

Typical categories include:

    - General-purpose registers
    - Program counter / instruction pointer
    - Stack pointer
    - Status or flags register
    - Control registers
    - Vector/SIMD registers
    - Architecture-specific special-purpose registers

Register names and exact behavior depend on the processor architecture.

Python does not expose physical CPU registers directly, so the example below
models the conceptual behavior.
"""
    )

    registers = {
        "R0": 10,
        "R1": 25,
        "R2": 0,
    }

    registers["R2"] = registers["R0"] + registers["R1"]

    print("Conceptual register state:")
    for name, value in registers.items():
        print(f"  {name} = {value}")

    print("The important point is that registers are the processor's fastest")
    print("working storage, but their number and capacity are very limited.")


# ============================================================================
# 4. CACHE LINES
# ============================================================================

@dataclass
class CacheLine:
    valid: bool = False
    tag: int = 0
    data: Optional[int] = None
    dirty: bool = False


class DirectMappedCache:
    """
    A simple direct-mapped cache.

    Memory is divided into blocks.
    Each block can occupy exactly one cache line.

    line_index = block_number % number_of_lines
    tag        = block_number // number_of_lines

    This demonstrates the mapping mechanism without modeling every hardware
    detail of a real processor cache.
    """

    def __init__(self, number_of_lines: int = 4):
        if number_of_lines <= 0:
            raise ValueError("number_of_lines must be positive")
        self.lines = [CacheLine() for _ in range(number_of_lines)]
        self.number_of_lines = number_of_lines
        self.hits = 0
        self.misses = 0

    def access(self, address: int) -> tuple[bool, int, int]:
        if address < 0:
            raise ValueError("address must be non-negative")

        block_number = address
        index = block_number % self.number_of_lines
        tag = block_number // self.number_of_lines

        line = self.lines[index]

        if line.valid and line.tag == tag:
            self.hits += 1
            return True, index, tag

        self.misses += 1
        line.valid = True
        line.tag = tag
        line.data = address
        line.dirty = False

        return False, index, tag

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total else 0.0

    def display(self) -> None:
        print("Index | Valid | Tag | Data")
        print("-" * 28)
        for index, line in enumerate(self.lines):
            print(
                f"{index:5d} | {str(line.valid):5s} | "
                f"{line.tag:3d} | {str(line.data):4s}"
            )


def demonstrate_direct_mapping() -> None:
    section("4. Direct-mapped cache")

    cache = DirectMappedCache(number_of_lines=4)
    addresses = [0, 4, 0, 8, 4, 0, 12, 0, 16]

    print("Access sequence:", addresses)

    for address in addresses:
        hit, index, tag = cache.access(address)
        print(
            f"Address {address:2d} -> line {index}, tag {tag:2d}, "
            f"{'HIT' if hit else 'MISS'}"
        )

    cache.display()
    print(f"Hit rate: {cache.hit_rate:.2%}")

    print(
        """
Notice that addresses 0, 4, 8, 12 and 16 all map to line 0 when there
are four lines. This can cause conflict misses even if other cache lines
are unused.
"""
    )


# ============================================================================
# 5. SET-ASSOCIATIVE CACHE
# ============================================================================

@dataclass
class SetLine:
    tag: int
    last_used: int


class SetAssociativeCache:
    """
    Simplified set-associative cache using LRU replacement.

    A block maps to one set but may occupy any way in that set.
    """

    def __init__(self, number_of_sets: int = 4, ways: int = 2):
        if number_of_sets <= 0 or ways <= 0:
            raise ValueError("number_of_sets and ways must be positive")

        self.number_of_sets = number_of_sets
        self.ways = ways
        self.sets: list[list[SetLine]] = [[] for _ in range(number_of_sets)]
        self.clock = 0
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def access(self, block_number: int) -> bool:
        if block_number < 0:
            raise ValueError("block_number must be non-negative")

        self.clock += 1
        set_index = block_number % self.number_of_sets
        tag = block_number // self.number_of_sets

        current_set = self.sets[set_index]

        for line in current_set:
            if line.tag == tag:
                self.hits += 1
                line.last_used = self.clock
                return True

        self.misses += 1

        if len(current_set) >= self.ways:
            oldest = min(current_set, key=lambda line: line.last_used)
            current_set.remove(oldest)
            self.evictions += 1

        current_set.append(SetLine(tag=tag, last_used=self.clock))
        return False

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total else 0.0


def demonstrate_associativity() -> None:
    section("5. Set associativity and LRU")

    cache = SetAssociativeCache(number_of_sets=2, ways=2)
    accesses = [0, 2, 4, 0, 2, 4, 0]

    print("Two sets, two ways per set")
    print("Access sequence:", accesses)

    for block in accesses:
        result = cache.access(block)
        print(f"Block {block}: {'HIT' if result else 'MISS'}")

    print(f"Hits: {cache.hits}")
    print(f"Misses: {cache.misses}")
    print(f"Evictions: {cache.evictions}")
    print(f"Hit rate: {cache.hit_rate:.2%}")


# ============================================================================
# 6. CACHE MISS CLASSIFICATION
# ============================================================================

def explain_cache_misses() -> None:
    section("6. Types of cache misses")

    print(
        """
The classic three C classification is:

Compulsory miss:
    The first access to a block must miss because the block has not
    previously been brought into the cache.

Capacity miss:
    The working data exceeds the available cache capacity, causing
    useful blocks to be displaced.

Conflict miss:
    Multiple blocks compete for the same cache location in a direct-mapped
    or limited-associativity cache.

Modern analyses can use additional classifications, but the three-C model
is useful for understanding cache behavior.
"""
    )


# ============================================================================
# 7. LOCALITY WITH REAL DATA ACCESS PATTERNS
# ============================================================================

def sequential_sum(data: list[int]) -> int:
    total = 0
    for value in data:
        total += value
    return total


def strided_sum(data: list[int], stride: int) -> int:
    total = 0
    for index in range(0, len(data), stride):
        total += data[index]
    return total


def random_sum(data: list[int], seed: int = 42) -> int:
    generator = random.Random(seed)
    indices = list(range(len(data)))
    generator.shuffle(indices)

    total = 0
    for index in indices:
        total += data[index]
    return total


def demonstrate_locality() -> None:
    section("7. Temporal and spatial locality")

    data = list(range(100_000))

    start = time.perf_counter()
    sequential_result = sequential_sum(data)
    sequential_time = time.perf_counter() - start

    start = time.perf_counter()
    strided_result = strided_sum(data, 16)
    strided_time = time.perf_counter() - start

    start = time.perf_counter()
    random_result = random_sum(data)
    random_time = time.perf_counter() - start

    print(f"Sequential result: {sequential_result}")
    print(f"Stride-16 result:  {strided_result}")
    print(f"Random result:     {random_result}")

    print("\nPython-level timings:")
    print(f"  Sequential: {sequential_time:.6f} seconds")
    print(f"  Strided:    {strided_time:.6f} seconds")
    print(f"  Random:     {random_time:.6f} seconds")

    print(
        """
The exact timings depend heavily on Python implementation, operating system,
CPU, cache state and interpreter behavior. The conceptual lesson is that
sequential access provides strong spatial locality.
"""
    )


# ============================================================================
# 8. TWO-DIMENSIONAL DATA AND ACCESS ORDER
# ============================================================================

def row_major_sum(matrix: list[list[int]]) -> int:
    total = 0
    for row in matrix:
        for value in row:
            total += value
    return total


def column_major_sum(matrix: list[list[int]]) -> int:
    if not matrix:
        return 0

    rows = len(matrix)
    columns = len(matrix[0])
    total = 0

    for column in range(columns):
        for row in range(rows):
            total += matrix[row][column]

    return total


def demonstrate_matrix_locality() -> None:
    section("8. Spatial locality in matrix traversal")

    size = 500
    matrix = [[row + column for column in range(size)] for row in range(size)]

    start = time.perf_counter()
    row_result = row_major_sum(matrix)
    row_time = time.perf_counter() - start

    start = time.perf_counter()
    column_result = column_major_sum(matrix)
    column_time = time.perf_counter() - start

    print(f"Row-major result:    {row_result}")
    print(f"Column-major result: {column_result}")
    print(f"Row-major time:      {row_time:.6f} seconds")
    print(f"Column-major time:   {column_time:.6f} seconds")

    print(
        """
Python lists are themselves collections of references, so this is not a
perfect hardware-cache benchmark. In a contiguous row-major data layout,
row-wise traversal normally provides better spatial locality because
neighboring elements are physically closer in memory.
"""
    )


# ============================================================================
# 9. WRITE POLICIES
# ============================================================================

class WritePolicy(Enum):
    WRITE_THROUGH = "write-through"
    WRITE_BACK = "write-back"


@dataclass
class WriteCacheEntry:
    value: int
    dirty: bool = False


class TinyWriteCache:
    """
    Demonstrates the conceptual difference between write-through and
    write-back caching.
    """

    def __init__(self, policy: WritePolicy):
        self.policy = policy
        self.cache: dict[int, WriteCacheEntry] = {}
        self.memory: dict[int, int] = {}
        self.memory_writes = 0

    def write(self, address: int, value: int) -> None:
        self.cache[address] = WriteCacheEntry(
            value=value,
            dirty=self.policy == WritePolicy.WRITE_BACK,
        )

        if self.policy == WritePolicy.WRITE_THROUGH:
            self.memory[address] = value
            self.memory_writes += 1

    def evict(self, address: int) -> None:
        entry = self.cache.pop(address, None)
        if entry is None:
            return

        if self.policy == WritePolicy.WRITE_BACK and entry.dirty:
            self.memory[address] = entry.value
            self.memory_writes += 1

    def read_memory(self, address: int) -> int:
        return self.memory.get(address, 0)


def demonstrate_write_policies() -> None:
    section("9. Write-through versus write-back")

    for policy in WritePolicy:
        cache = TinyWriteCache(policy)
        cache.write(10, 100)
        cache.write(10, 200)

        before_eviction = cache.memory_writes
        cache.evict(10)
        after_eviction = cache.memory_writes

        print(f"\nPolicy: {policy.value}")
        print(f"Memory writes before eviction: {before_eviction}")
        print(f"Memory writes after eviction:  {after_eviction}")
        print(f"Final memory value: {cache.read_memory(10)}")

    print(
        """
Write-through:
    Every cache write is immediately propagated to the next level.
    This can simplify consistency but may generate more write traffic.

Write-back:
    Modified data remains in cache until eviction or another required event.
    A dirty bit identifies modified cache lines.
"""
    )


# ============================================================================
# 10. WRITE ALLOCATION
# ============================================================================

def explain_write_allocation() -> None:
    section("10. Write allocation")

    print(
        """
Write-allocate:
    On a write miss, bring the block into cache and then modify it.

No-write-allocate:
    On a write miss, write directly to the lower memory level without
    loading the block into the cache.

Write allocation and write policy are separate design choices.

Common combinations include:

    write-back + write-allocate
    write-through + no-write-allocate

Actual processor designs may use more specialized policies.
"""
    )


# ============================================================================
# 11. AVERAGE MEMORY ACCESS TIME
# ============================================================================

def average_memory_access_time(
    hit_time: float,
    miss_rate: float,
    miss_penalty: float,
) -> float:
    if hit_time < 0 or miss_rate < 0 or miss_rate > 1 or miss_penalty < 0:
        raise ValueError("Invalid memory timing parameters")

    return hit_time + miss_rate * miss_penalty


def demonstrate_amat() -> None:
    section("11. Average Memory Access Time")

    l1_hit_time = 1.0
    l1_miss_rate = 0.05
    l2_penalty = 10.0

    amat = average_memory_access_time(
        hit_time=l1_hit_time,
        miss_rate=l1_miss_rate,
        miss_penalty=l2_penalty,
    )

    print(f"L1 hit time:  {l1_hit_time} ns")
    print(f"L1 miss rate: {l1_miss_rate:.2%}")
    print(f"Miss penalty: {l2_penalty} ns")
    print(f"AMAT:         {amat:.2f} ns")

    print(
        """
For multiple levels, the penalty itself can contain another lookup.

For example:

AMAT =
    L1 hit time
    + L1 miss rate ×
      (L2 hit time
       + L2 miss rate ×
         (L3 hit time
          + L3 miss rate × RAM penalty))
"""
    )


# ============================================================================
# 12. MULTI-LEVEL CACHE SIMULATION
# ============================================================================

@dataclass
class CacheLevelResult:
    level: str
    hit: bool
    latency: float


class SimpleCacheLevel:
    def __init__(self, name: str, capacity_blocks: int, latency: float):
        if capacity_blocks <= 0:
            raise ValueError("capacity_blocks must be positive")

        self.name = name
        self.capacity_blocks = capacity_blocks
        self.latency = latency
        self.entries: OrderedDict[int, None] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def access(self, block: int) -> bool:
        if block in self.entries:
            self.hits += 1
            self.entries.move_to_end(block)
            return True

        self.misses += 1

        if len(self.entries) >= self.capacity_blocks:
            self.entries.popitem(last=False)

        self.entries[block] = None
        return False


class MultiLevelMemory:
    """
    A teaching model of:

        L1 -> L2 -> L3 -> RAM

    Real CPUs have additional details such as instruction/data caches,
    coherence protocols, prefetchers, nonblocking caches and multiple
    simultaneous outstanding requests.
    """

    def __init__(self):
        self.levels = [
            SimpleCacheLevel("L1", capacity_blocks=4, latency=1),
            SimpleCacheLevel("L2", capacity_blocks=8, latency=4),
            SimpleCacheLevel("L3", capacity_blocks=16, latency=12),
        ]
        self.ram_latency = 80

    def access(self, block: int) -> CacheLevelResult:
        total_latency = 0

        for level in self.levels:
            total_latency += level.latency

            if level.access(block):
                return CacheLevelResult(level.name, True, total_latency)

        total_latency += self.ram_latency
        return CacheLevelResult("RAM", False, total_latency)

    def statistics(self) -> None:
        for level in self.levels:
            accesses = level.hits + level.misses
            hit_rate = level.hits / accesses if accesses else 0
            print(
                f"{level.name}: hits={level.hits}, misses={level.misses}, "
                f"hit_rate={hit_rate:.2%}"
            )


def demonstrate_multilevel_cache() -> None:
    section("12. Multi-level cache simulation")

    memory = MultiLevelMemory()

    access_pattern = [1, 2, 3, 4, 1, 2, 3, 4, 20, 21, 1, 2, 20, 21]

    for block in access_pattern:
        result = memory.access(block)
        print(
            f"Block {block:2d}: {result.level:3s}, "
            f"{'hit' if result.hit else 'lower-level access'}, "
            f"modeled latency={result.latency:3.0f} ns"
        )

    print("\nStatistics:")
    memory.statistics()


# ============================================================================
# 13. PREFETCHING
# ============================================================================

class SequentialPrefetcher:
    """
    A conceptual next-block prefetcher.

    Prefetching attempts to move data into a nearer level before the CPU
    explicitly requests it.
    """

    def __init__(self):
        self.prefetched: set[int] = set()

    def observe(self, block: int) -> None:
        self.prefetched.add(block + 1)

    def consume(self, block: int) -> bool:
        if block in self.prefetched:
            self.prefetched.remove(block)
            return True
        return False


def demonstrate_prefetching() -> None:
    section("13. Hardware prefetching concept")

    prefetcher = SequentialPrefetcher()

    accesses = [100, 101, 102, 103, 104]
    useful_prefetches = 0

    for block in accesses:
        if prefetcher.consume(block):
            useful_prefetches += 1
            print(f"Block {block}: supplied by conceptual prefetch")
        else:
            print(f"Block {block}: normal access")

        prefetcher.observe(block)

    print(f"Useful prefetches: {useful_prefetches}")

    print(
        """
Prefetching can reduce effective latency when access patterns are predictable.

It can also hurt performance when predictions are wrong because:

    - bandwidth is consumed
    - cache capacity is consumed
    - useful data may be displaced
    - energy consumption increases

Therefore, prefetching is a trade-off rather than a universally beneficial
operation.
"""
    )


# ============================================================================
# 14. VIRTUAL MEMORY AND PAGING
# ============================================================================

@dataclass
class PageTableEntry:
    frame_number: int
    present: bool = True
    writable: bool = True
    executable: bool = False


class PageTable:
    def __init__(self, page_size: int = 4096):
        if page_size <= 0 or page_size & (page_size - 1):
            raise ValueError("page_size must be a positive power of two")

        self.page_size = page_size
        self.entries: dict[int, PageTableEntry] = {}

    def map_page(
        self,
        virtual_page: int,
        frame_number: int,
        writable: bool = True,
        executable: bool = False,
    ) -> None:
        self.entries[virtual_page] = PageTableEntry(
            frame_number=frame_number,
            writable=writable,
            executable=executable,
        )

    def translate(self, virtual_address: int) -> int:
        if virtual_address < 0:
            raise ValueError("virtual address must be non-negative")

        virtual_page = virtual_address // self.page_size
        offset = virtual_address % self.page_size

        entry = self.entries.get(virtual_page)

        if entry is None or not entry.present:
            raise MemoryError(f"Page fault for virtual page {virtual_page}")

        return entry.frame_number * self.page_size + offset


def demonstrate_virtual_memory() -> None:
    section("14. Virtual memory and address translation")

    page_table = PageTable(page_size=4096)

    page_table.map_page(0, 10)
    page_table.map_page(1, 11)
    page_table.map_page(2, 20)

    virtual_addresses = [0, 100, 4095, 4096, 8192, 9000]

    for address in virtual_addresses:
        try:
            physical = page_table.translate(address)
            print(f"Virtual address {address:5d} -> physical address {physical:6d}")
        except MemoryError as error:
            print(f"Virtual address {address:5d} -> {error}")

    print(
        """
Virtual memory separates the addresses used by a process from physical
memory locations.

Paging divides virtual memory into fixed-size pages and physical memory
into frames.

A page table maps virtual pages to physical frames.

The offset inside a page remains unchanged during translation.

Virtual memory enables:

    - process isolation
    - flexible memory allocation
    - protection permissions
    - sharing of selected pages
    - demand paging
    - memory overcommit strategies in some systems
"""
    )


# ============================================================================
# 15. TLB
# ============================================================================

class TLB:
    """
    Translation Lookaside Buffer.

    A TLB caches recent virtual-page -> physical-frame translations so that
    the processor does not have to walk the page table for every access.
    """

    def __init__(self, capacity: int = 4):
        if capacity <= 0:
            raise ValueError("capacity must be positive")

        self.capacity = capacity
        self.entries: OrderedDict[int, int] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def lookup(self, virtual_page: int) -> Optional[int]:
        if virtual_page in self.entries:
            self.hits += 1
            frame = self.entries.pop(virtual_page)
            self.entries[virtual_page] = frame
            return frame

        self.misses += 1
        return None

    def insert(self, virtual_page: int, frame: int) -> None:
        if virtual_page in self.entries:
            self.entries.pop(virtual_page)

        elif len(self.entries) >= self.capacity:
            self.entries.popitem(last=False)

        self.entries[virtual_page] = frame


def demonstrate_tlb() -> None:
    section("15. Translation Lookaside Buffer")

    page_table = PageTable()
    page_table.map_page(1, 100)
    page_table.map_page(2, 200)
    page_table.map_page(3, 300)

    tlb = TLB(capacity=2)

    for virtual_page in [1, 1, 2, 1, 3, 1, 2, 3]:
        frame = tlb.lookup(virtual_page)

        if frame is None:
            frame = page_table.entries[virtual_page].frame_number
            tlb.insert(virtual_page, frame)
            source = "page table"
        else:
            source = "TLB"

        print(
            f"Virtual page {virtual_page}: frame {frame}, source={source}"
        )

    print(f"TLB hits:   {tlb.hits}")
    print(f"TLB misses: {tlb.misses}")


# ============================================================================
# 16. PAGE FAULT CONCEPT
# ============================================================================

class DemandPagedMemory:
    """
    Simplified demand-paging model.

    A page is not necessarily resident in physical memory. When accessed
    while absent, a page fault occurs and the operating system would normally
    arrange for the page to be loaded.
    """

    def __init__(self, number_of_frames: int = 3):
        self.number_of_frames = number_of_frames
        self.frames: OrderedDict[int, int] = OrderedDict()
        self.page_faults = 0
        self.accesses = 0

    def access_page(self, virtual_page: int) -> bool:
        self.accesses += 1

        if virtual_page in self.frames:
            self.frames.move_to_end(virtual_page)
            return True

        self.page_faults += 1

        if len(self.frames) >= self.number_of_frames:
            self.frames.popitem(last=False)

        self.frames[virtual_page] = len(self.frames)
        return False

    @property
    def fault_rate(self) -> float:
        return self.page_faults / self.accesses if self.accesses else 0


def demonstrate_page_faults() -> None:
    section("16. Demand paging and page faults")

    memory = DemandPagedMemory(number_of_frames=3)
    sequence = [1, 2, 3, 1, 4, 1, 2, 5, 1, 2, 3]

    for page in sequence:
        hit = memory.access_page(page)
        print(
            f"Page {page}: {'resident' if hit else 'PAGE FAULT'}, "
            f"resident pages={list(memory.frames.keys())}"
        )

    print(f"Page fault rate: {memory.fault_rate:.2%}")


# ============================================================================
# 17. MEMORY-MAPPED FILE CONCEPT
# ============================================================================

class MemoryMappedFileModel:
    """
    Conceptual model of memory mapping.

    A real memory-mapped file is provided by an operating system API.
    Here, a bytearray models a file-backed memory region.
    """

    def __init__(self, content: bytes):
        self.storage = bytearray(content)

    def read(self, offset: int, length: int) -> bytes:
        if offset < 0 or length < 0:
            raise ValueError("offset and length must be non-negative")

        if offset + length > len(self.storage):
            raise IndexError("read exceeds mapped region")

        return bytes(self.storage[offset:offset + length])

    def write(self, offset: int, content: bytes) -> None:
        if offset < 0:
            raise ValueError("offset must be non-negative")

        end = offset + len(content)

        if end > len(self.storage):
            raise IndexError("write exceeds mapped region")

        self.storage[offset:end] = content


def demonstrate_memory_mapping() -> None:
    section("17. Memory-mapped storage concept")

    mapped = MemoryMappedFileModel(b"MEMORY-HIERARCHY-DATA")

    print(mapped.read(0, 6).decode())

    mapped.write(0, b"CPU")
    print(mapped.read(0, 12).decode())

    print(
        """
Memory mapping allows file-backed data to be accessed through a memory-like
interface. Operating systems can use virtual memory mechanisms to bring
needed portions into physical memory.

It is useful for large files, databases, indexes and shared-memory designs,
but it does not mean the entire file must be physically resident in RAM.
"""
    )


# ============================================================================
# 18. CACHE SIMULATION EXPERIMENT
# ============================================================================

def simulate_cache_workload(
    cache_size: int,
    accesses: Iterable[int],
) -> tuple[int, int]:
    cache: OrderedDict[int, None] = OrderedDict()
    hits = 0
    misses = 0

    for block in accesses:
        if block in cache:
            hits += 1
            cache.move_to_end(block)
        else:
            misses += 1

            if len(cache) >= cache_size:
                cache.popitem(last=False)

            cache[block] = None

    return hits, misses


def compare_workloads() -> None:
    section("18. Comparing workloads")

    sequential = list(range(100))
    repeated = [value for value in range(10) for _ in range(10)]

    generator = random.Random(123)
    random_workload = [generator.randrange(100) for _ in range(100)]

    workloads = {
        "Sequential": sequential,
        "Repeated": repeated,
        "Random": random_workload,
    }

    for cache_size in [4, 8, 16, 32]:
        print(f"\nCache capacity: {cache_size} blocks")

        for name, workload in workloads.items():
            hits, misses = simulate_cache_workload(cache_size, workload)
            total = hits + misses
            hit_rate = hits / total if total else 0
            print(
                f"  {name:10s}: hits={hits:3d}, misses={misses:3d}, "
                f"hit_rate={hit_rate:.2%}"
            )


# ============================================================================
# 19. MEMORY CONSISTENCY AND CACHE COHERENCE
# ============================================================================

def explain_coherence_and_consistency() -> None:
    section("19. Cache coherence and memory consistency")

    print(
        """
In a multicore processor, several cores may have private caches.

Cache coherence concerns whether different caches eventually agree about
the value of the same memory location.

Common coherence mechanisms use protocols such as MESI-family protocols,
with states conceptually including:

    Modified
    Exclusive
    Shared
    Invalid

Memory consistency is a broader question: what ordering of memory operations
is visible to different threads?

Coherence and consistency are related but not identical.

Concurrency introduces additional requirements such as:

    - atomic operations
    - locks
    - memory barriers/fences
    - acquire/release ordering
    - cache-line ownership
    - false sharing avoidance
"""
    )


# ============================================================================
# 20. FALSE SHARING
# ============================================================================

def explain_false_sharing() -> None:
    section("20. False sharing")

    print(
        """
A cache normally transfers data in cache-line-sized blocks rather than
individual variables.

Suppose two threads update two different variables:

    Thread A -> counter_a
    Thread B -> counter_b

If counter_a and counter_b occupy the same cache line, each thread may
invalidate or acquire ownership of the same cache line even though the
threads never access the same logical variable.

This is called false sharing.

Possible mitigations include:

    - padding
    - alignment
    - separating frequently modified variables
    - choosing appropriate data structures

False sharing is particularly important in high-performance concurrent
software.
"""
    )


# ============================================================================
# 21. STACK, HEAP AND MEMORY HIERARCHY
# ============================================================================

def stack_example(depth: int) -> int:
    if depth <= 0:
        return 0
    return 1 + stack_example(depth - 1)


def demonstrate_stack_and_heap() -> None:
    section("21. Stack, heap and physical memory")

    result = stack_example(5)
    dynamic_data = [index * index for index in range(10)]

    print(f"Recursive stack example result: {result}")
    print(f"Dynamic data: {dynamic_data}")

    print(
        """
Stack and heap are logical regions of a process's virtual address space.
They should not be confused with CPU cache levels.

A simplified relationship is:

    CPU registers
          ↓
    CPU caches
          ↓
    physical RAM
          ↓
    storage

while a process may organize its virtual address space into regions such as:

    code
    read-only data
    writable data
    heap
    shared mappings
    stack

The operating system and hardware translate virtual addresses to physical
memory and storage-backed pages as necessary.
"""
    )


# ============================================================================
# 22. ALIGNMENT
# ============================================================================

def is_aligned(address: int, alignment: int) -> bool:
    if alignment <= 0 or alignment & (alignment - 1):
        raise ValueError("alignment must be a positive power of two")

    return address % alignment == 0


def demonstrate_alignment() -> None:
    section("22. Memory alignment")

    addresses = [0, 8, 16, 24, 31, 32, 64]

    for address in addresses:
        print(
            f"Address {address:2d}: "
            f"8-byte aligned={is_aligned(address, 8)}, "
            f"64-byte aligned={is_aligned(address, 64)}"
        )

    print(
        """
Alignment can affect correctness on some architectures and can affect
performance because naturally aligned objects can be accessed efficiently.

Cache-line alignment is particularly useful when intentionally separating
independently updated data to avoid false sharing.
"""
    )


# ============================================================================
# 23. EDGE CASES AND COMMON ERRORS
# ============================================================================

def demonstrate_edge_cases() -> None:
    section("23. Edge cases and common programming errors")

    tests = [
        ("Negative address", lambda: DirectMappedCache(4).access(-1)),
        ("Zero cache lines", lambda: DirectMappedCache(0)),
        ("Invalid page size", lambda: PageTable(3000)),
        ("Negative virtual address", lambda: PageTable().translate(-1)),
        ("Out-of-range mapped read", lambda: MemoryMappedFileModel(b"abc").read(2, 5)),
    ]

    for name, operation in tests:
        try:
            operation()
            print(f"{name}: unexpectedly accepted")
        except (ValueError, MemoryError, IndexError) as error:
            print(f"{name}: correctly rejected -> {error}")

    print(
        """
Common mistakes include:

    - assuming cache latency is identical on every CPU
    - confusing bandwidth with latency
    - assuming RAM is the fastest memory
    - assuming a cache hit means zero time
    - ignoring spatial locality
    - ignoring data layout
    - treating virtual addresses as physical addresses
    - confusing cache coherence with memory consistency
    - assuming bigger caches always improve performance
    - ignoring cache-line effects in concurrent programs
    - assuming SSD latency is comparable to RAM latency
    """
    )


# ============================================================================
# 24. PERFORMANCE TRADE-OFFS
# ============================================================================

def demonstrate_tradeoffs() -> None:
    section("24. Memory hierarchy design trade-offs")

    designs = [
        ("Small cache", "Low capacity", "Low area and power", "More misses"),
        ("Large cache", "High capacity", "Fewer capacity misses", "More area/power"),
        ("Direct mapped", "Simple mapping", "Low lookup complexity", "More conflicts"),
        ("High associativity", "Flexible placement", "Fewer conflicts", "More comparison hardware"),
        ("Write-through", "Immediate propagation", "Simpler lower-level visibility", "More write traffic"),
        ("Write-back", "Delayed propagation", "Less lower-level traffic", "Dirty-state management"),
        ("Aggressive prefetch", "More data fetched early", "Can hide latency", "Can waste bandwidth"),
    ]

    for design, characteristic, advantage, disadvantage in designs:
        print(
            f"{design:22s} | {characteristic:30s} | "
            f"{advantage:34s} | {disadvantage}"
        )


# ============================================================================
# 25. MEMORY SECURITY
# ============================================================================

def explain_memory_security() -> None:
    section("25. Memory hierarchy and security")

    print(
        """
Memory architecture has security implications.

Important areas include:

1. Process isolation
   Virtual memory prevents ordinary user processes from directly accessing
   arbitrary physical memory.

2. Page permissions
   Pages can have read, write and execute permissions.

3. ASLR
   Address Space Layout Randomization changes virtual memory layouts to make
   some exploitation techniques harder.

4. NX / DEP
   Non-executable memory reduces the ability to execute injected data.

5. Cache side channels
   Cache timing can reveal information about another computation when an
   attacker can observe timing differences.

6. Speculative execution
   Modern CPUs may execute instructions speculatively. Microarchitectural
   state can sometimes expose information despite architectural permission
   checks.

7. Secure erasure
   Data may exist simultaneously in registers, caches, RAM, swap and storage.
   Removing one copy does not necessarily remove every physical copy.

Security therefore requires understanding both architectural behavior and
microarchitectural behavior.
"""
    )


# ============================================================================
# 26. PRODUCTION DESIGN PRINCIPLES
# ============================================================================

def explain_production_principles() -> None:
    section("26. Practical memory-hierarchy engineering")

    print(
        """
For performance-sensitive systems:

    1. Measure before optimizing.
    2. Understand the actual access pattern.
    3. Prefer contiguous data when appropriate.
    4. Reduce unnecessary pointer chasing.
    5. Improve temporal locality through reuse.
    6. Improve spatial locality through suitable layout.
    7. Keep hot data compact.
    8. Avoid unnecessary allocations.
    9. Consider cache-line boundaries.
   10. Consider concurrency and false sharing.
   11. Profile cache misses where hardware counters are available.
   12. Consider TLB behavior for large working sets.
   13. Distinguish CPU-cache effects from language-runtime effects.
   14. Validate performance on representative hardware.
   15. Treat security implications separately from raw performance.
"""
    )


# ============================================================================
# 27. SIMPLE MEMORY-HIERARCHY PERFORMANCE MODEL
# ============================================================================

@dataclass
class HierarchyModel:
    register_latency: float
    l1_latency: float
    l1_miss_rate: float
    l2_latency: float
    l2_miss_rate: float
    l3_latency: float
    l3_miss_rate: float
    ram_latency: float
    storage_latency: float

    def validate(self) -> None:
        latencies = [
            self.register_latency,
            self.l1_latency,
            self.l2_latency,
            self.l3_latency,
            self.ram_latency,
            self.storage_latency,
        ]

        if any(value < 0 for value in latencies):
            raise ValueError("Latencies cannot be negative")

        miss_rates = [
            self.l1_miss_rate,
            self.l2_miss_rate,
            self.l3_miss_rate,
        ]

        if any(rate < 0 or rate > 1 for rate in miss_rates):
            raise ValueError("Miss rates must be between 0 and 1")

    def expected_latency(self) -> float:
        self.validate()

        return (
            self.register_latency
            + self.l1_latency
            + self.l1_miss_rate
            * (
                self.l2_latency
                + self.l2_miss_rate
                * (
                    self.l3_latency
                    + self.l3_miss_rate
                    * (self.ram_latency)
                )
            )
        )


def demonstrate_hierarchy_model() -> None:
    section("27. End-to-end hierarchy performance model")

    model = HierarchyModel(
        register_latency=0.3,
        l1_latency=1.0,
        l1_miss_rate=0.05,
        l2_latency=4.0,
        l2_miss_rate=0.10,
        l3_latency=12.0,
        l3_miss_rate=0.20,
        ram_latency=80.0,
        storage_latency=100_000.0,
    )

    print(f"Estimated expected latency: {model.expected_latency():.3f} ns")

    print(
        """
The storage latency is not included in every ordinary CPU cache miss.
Storage becomes relevant when virtual-memory or file-backed behavior
requires data beyond physical RAM.
"""
    )


# ============================================================================
# 28. MICROBENCHMARK WARNING
# ============================================================================

def explain_benchmarking() -> None:
    section("28. Benchmarking considerations")

    print(
        """
A short program timing one operation does not automatically measure
physical cache latency.

Results can be affected by:

    - compiler optimizations
    - interpreter overhead
    - CPU frequency scaling
    - operating-system scheduling
    - branch prediction
    - hardware prefetching
    - warm versus cold caches
    - TLB state
    - other processes
    - measurement overhead
    - NUMA placement
    - garbage collection in managed runtimes

Reliable performance analysis generally uses repeated measurements,
carefully controlled workloads, suitable timers and hardware performance
counters where available.
"""
    )


# ============================================================================
# 29. KNOWLEDGE CHECK
# ============================================================================

def knowledge_check() -> None:
    section("29. Knowledge check")

    questions = [
        (
            "Which locality principle says recently accessed data is likely "
            "to be accessed again?",
            "Temporal locality",
        ),
        (
            "Which locality principle says nearby addresses are likely "
            "to be accessed?",
            "Spatial locality",
        ),
        (
            "What is the small cache used for virtual-to-physical translations?",
            "TLB",
        ),
        (
            "What cache organization lets a block map to exactly one line?",
            "Direct-mapped cache",
        ),
        (
            "What is modified cache data commonly marked with in write-back caches?",
            "A dirty bit",
        ),
        (
            "What event occurs when a required virtual page is not resident?",
            "Page fault",
        ),
    ]

    for number, (question, answer) in enumerate(questions, start=1):
        print(f"{number}. {question}")
        print(f"   Answer: {answer}")


# ============================================================================
# 30. INTEGRATED DEMONSTRATION
# ============================================================================

def integrated_example() -> None:
    section("30. Integrated memory-hierarchy example")

    print(
        """
Imagine a database engine repeatedly processing customer records.

A simplified path can look like:

    CPU instruction
        ↓
    Registers
        ↓
    L1 cache
        ↓
    L2 cache
        ↓
    L3 cache
        ↓
    RAM
        ↓
    SSD-backed storage

The database tries to keep frequently used structures in RAM.
The CPU then relies on cache hierarchy to keep hot portions of those
structures close to execution units.

Good data layout can improve spatial locality.
Repeated access to the same records can improve temporal locality.
Prefetching may help predictable scans.
The operating system handles virtual memory and page residency.
The processor handles cache lookup and much of the cache-coherence machinery.

The application therefore interacts with the memory hierarchy at several
levels even when it does not explicitly manipulate hardware caches.
"""
    )

    database_records = [
        {"id": 1, "balance": 5000},
        {"id": 2, "balance": 10000},
        {"id": 3, "balance": 2500},
    ]

    query_ids = [1, 2, 1, 3, 1, 2, 1]

    lookup_count = 0
    for record_id in query_ids:
        lookup_count += 1
        record = next(
            record for record in database_records if record["id"] == record_id
        )
        print(
            f"Query {lookup_count}: customer={record_id}, "
            f"balance={record['balance']}"
        )

    print(
        """
The Python list and dictionaries above are software data structures.
Their physical placement and cache behavior are ultimately determined by
the Python runtime, operating system and processor.
"""
    )


# ============================================================================
# 31. MAIN
# ============================================================================

def main() -> None:
    explain_basics()
    demonstrate_memory_metrics()
    demonstrate_register_concept()
    demonstrate_direct_mapping()
    demonstrate_associativity()
    explain_cache_misses()
    demonstrate_locality()
    demonstrate_matrix_locality()
    demonstrate_write_policies()
    explain_write_allocation()
    demonstrate_amat()
    demonstrate_multilevel_cache()
    demonstrate_prefetching()
    demonstrate_virtual_memory()
    demonstrate_tlb()
    demonstrate_page_faults()
    demonstrate_memory_mapping()
    compare_workloads()
    explain_coherence_and_consistency()
    explain_false_sharing()
    demonstrate_stack_and_heap()
    demonstrate_alignment()
    demonstrate_edge_cases()
    demonstrate_tradeoffs()
    explain_memory_security()
    explain_production_principles()
    demonstrate_hierarchy_model()
    explain_benchmarking()
    knowledge_check()
    integrated_example()

    section("Completed")
    print("Memory hierarchy study program completed successfully.")


if __name__ == "__main__":
    main()
