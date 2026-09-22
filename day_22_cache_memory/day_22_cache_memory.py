"""
Cache Memory and Cache Simulator
================================

A comprehensive executable study of:

- Cache memory fundamentals
- Cache levels: L1, L2, L3
- Cache hits and misses
- Spatial and temporal locality
- Direct-mapped, fully associative, and set-associative caches
- Tag, index, and offset fields
- Replacement policies
- Write-through and write-back behavior
- Write-allocate and no-write-allocate behavior
- Cache statistics
- Address tracing
- Sequential and strided access patterns
- Conflict, capacity, and compulsory misses
- Multi-level cache simulation
- LRU replacement
- Performance estimation
- Edge cases and validation
- A practical cache simulator

The program uses only the Python standard library.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum
from math import log2
from typing import Iterable, Optional


# ---------------------------------------------------------------------------
# Fundamental terminology
# ---------------------------------------------------------------------------
#
# A CPU is much faster than main memory. Cache memory reduces the effective
# memory-access time by keeping recently or frequently accessed data close to
# the CPU.
#
# A cache is divided into cache lines (also called blocks). A cache line stores:
#
#   - valid bit
#   - tag
#   - data block
#   - optionally dirty bit and metadata such as LRU information
#
# For a byte address:
#
#   address = [ tag | index | block offset ]
#
# The block offset identifies a byte inside a cache block.
# The index identifies a cache set.
# The tag distinguishes different memory blocks that can map to the same set.
#
# Important locality principles:
#
# Temporal locality:
#     Recently accessed data is likely to be accessed again.
#
# Spatial locality:
#     Addresses near a recently accessed address are likely to be accessed.
#
# Sequential array traversal generally demonstrates strong spatial locality.
#
# Repeated access to the same array elements demonstrates temporal locality.
# ---------------------------------------------------------------------------


class ReplacementPolicy(Enum):
    LRU = "LRU"
    FIFO = "FIFO"


class WritePolicy(Enum):
    WRITE_BACK = "write-back"
    WRITE_THROUGH = "write-through"


class AllocationPolicy(Enum):
    WRITE_ALLOCATE = "write-allocate"
    NO_WRITE_ALLOCATE = "no-write-allocate"


class AssociativityType(Enum):
    DIRECT_MAPPED = "direct-mapped"
    FULLY_ASSOCIATIVE = "fully-associative"
    SET_ASSOCIATIVE = "set-associative"


@dataclass
class CacheLine:
    valid: bool = False
    tag: int = 0
    dirty: bool = False
    last_used: int = 0
    inserted_at: int = 0


@dataclass
class AccessResult:
    address: int
    block_number: int
    set_index: int
    tag: int
    hit: bool
    latency: int
    evicted_tag: Optional[int] = None
    dirty_eviction: bool = False


@dataclass
class CacheStatistics:
    accesses: int = 0
    hits: int = 0
    misses: int = 0
    compulsory_misses: int = 0
    conflict_misses: int = 0
    capacity_misses: int = 0
    write_hits: int = 0
    write_misses: int = 0
    write_backs: int = 0

    @property
    def hit_rate(self) -> float:
        return self.hits / self.accesses if self.accesses else 0.0

    @property
    def miss_rate(self) -> float:
        return self.misses / self.accesses if self.accesses else 0.0

    def print_report(self, name: str) -> None:
        print(f"\n{name}")
        print("-" * len(name))
        print(f"Accesses:            {self.accesses}")
        print(f"Hits:                {self.hits}")
        print(f"Misses:              {self.misses}")
        print(f"Hit rate:            {self.hit_rate:.2%}")
        print(f"Miss rate:           {self.miss_rate:.2%}")
        print(f"Compulsory misses:   {self.compulsory_misses}")
        print(f"Conflict misses:     {self.conflict_misses}")
        print(f"Capacity misses:     {self.capacity_misses}")
        print(f"Write hits:          {self.write_hits}")
        print(f"Write misses:        {self.write_misses}")
        print(f"Write-backs:         {self.write_backs}")


# ---------------------------------------------------------------------------
# Utility functions for cache address decomposition
# ---------------------------------------------------------------------------

def is_power_of_two(value: int) -> bool:
    """Return True only when value is a positive power of two."""
    return value > 0 and (value & (value - 1)) == 0


def log2_integer(value: int) -> int:
    """Return integer log2 for a power-of-two value."""
    if not is_power_of_two(value):
        raise ValueError(f"{value} must be a positive power of two.")
    return value.bit_length() - 1


def address_fields(
    address: int,
    block_size: int,
    number_of_sets: int,
) -> tuple[int, int, int, int]:
    """
    Split a byte address into:
        block_number, offset, set_index, tag

    block_number = address // block_size
    offset       = address % block_size
    set_index    = block_number % number_of_sets
    tag          = block_number // number_of_sets
    """
    if address < 0:
        raise ValueError("Memory addresses cannot be negative.")
    if not is_power_of_two(block_size):
        raise ValueError("Block size must be a power of two.")
    if not is_power_of_two(number_of_sets):
        raise ValueError("Number of sets must be a power of two.")

    block_number = address // block_size
    offset = address % block_size
    set_index = block_number % number_of_sets
    tag = block_number // number_of_sets

    return block_number, offset, set_index, tag


def explain_address(
    address: int,
    cache_size: int,
    block_size: int,
    associativity: int,
) -> None:
    """Print the tag/index/offset decomposition for one address."""
    if cache_size <= 0 or block_size <= 0 or associativity <= 0:
        raise ValueError("Cache parameters must be positive.")

    if cache_size % (block_size * associativity) != 0:
        raise ValueError(
            "Cache size must be divisible by block_size * associativity."
        )

    number_of_lines = cache_size // block_size
    number_of_sets = number_of_lines // associativity

    block_number, offset, set_index, tag = address_fields(
        address,
        block_size,
        number_of_sets,
    )

    offset_bits = log2_integer(block_size)
    index_bits = log2_integer(number_of_sets) if number_of_sets > 1 else 0

    print("\nAddress decomposition")
    print("---------------------")
    print(f"Address:             {address}")
    print(f"Binary address:      {address:016b}")
    print(f"Block number:        {block_number}")
    print(f"Offset:              {offset}")
    print(f"Set index:           {set_index}")
    print(f"Tag:                 {tag}")
    print(f"Offset bits:         {offset_bits}")
    print(f"Index bits:          {index_bits}")
    print(
        "Interpretation:     "
        f"[tag={tag}] [index={set_index}] [offset={offset}]"
    )


# ---------------------------------------------------------------------------
# Single-level cache simulator
# ---------------------------------------------------------------------------

class CacheSimulator:
    """
    A configurable cache simulator.

    Parameters:
        cache_size:
            Total cache capacity in bytes.

        block_size:
            Bytes stored in each cache line.

        associativity:
            Number of lines per set.
            1 means direct mapped.
            number_of_lines means fully associative.

        hit_latency:
            Simulated access latency when the cache hits.

        miss_latency:
            Additional latency associated with a miss.

        replacement_policy:
            LRU or FIFO.

        write_policy:
            Write-back or write-through.

        allocation_policy:
            Write-allocate or no-write-allocate.
    """

    def __init__(
        self,
        cache_size: int,
        block_size: int,
        associativity: int = 1,
        hit_latency: int = 1,
        miss_latency: int = 50,
        replacement_policy: ReplacementPolicy = ReplacementPolicy.LRU,
        write_policy: WritePolicy = WritePolicy.WRITE_BACK,
        allocation_policy: AllocationPolicy = AllocationPolicy.WRITE_ALLOCATE,
    ) -> None:
        if cache_size <= 0:
            raise ValueError("cache_size must be positive.")
        if block_size <= 0:
            raise ValueError("block_size must be positive.")
        if not is_power_of_two(cache_size):
            raise ValueError("cache_size must be a power of two.")
        if not is_power_of_two(block_size):
            raise ValueError("block_size must be a power of two.")
        if cache_size < block_size:
            raise ValueError("cache_size cannot be smaller than block_size.")
        if cache_size % block_size != 0:
            raise ValueError("cache_size must be divisible by block_size.")

        number_of_lines = cache_size // block_size

        if associativity <= 0:
            raise ValueError("associativity must be positive.")
        if not is_power_of_two(associativity):
            raise ValueError("associativity must be a power of two.")
        if associativity > number_of_lines:
            raise ValueError(
                "associativity cannot exceed the number of cache lines."
            )
        if number_of_lines % associativity != 0:
            raise ValueError(
                "number of lines must be divisible by associativity."
            )

        self.cache_size = cache_size
        self.block_size = block_size
        self.associativity = associativity
        self.number_of_lines = number_of_lines
        self.number_of_sets = number_of_lines // associativity
        self.hit_latency = hit_latency
        self.miss_latency = miss_latency
        self.replacement_policy = replacement_policy
        self.write_policy = write_policy
        self.allocation_policy = allocation_policy

        self.sets: list[list[CacheLine]] = [
            [CacheLine() for _ in range(associativity)]
            for _ in range(self.number_of_sets)
        ]

        self.statistics = CacheStatistics()
        self.clock = 0

        # Used to classify first-reference misses.
        self.seen_blocks: set[int] = set()

        # A set of all blocks that have been evicted at least once helps
        # distinguish some recurring misses in this educational simulator.
        self.evicted_blocks: set[int] = set()

    def reset(self) -> None:
        """Clear cache contents and all simulation statistics."""
        self.sets = [
            [CacheLine() for _ in range(self.associativity)]
            for _ in range(self.number_of_sets)
        ]
        self.statistics = CacheStatistics()
        self.clock = 0
        self.seen_blocks.clear()
        self.evicted_blocks.clear()

    def _find_line(
        self,
        set_index: int,
        tag: int,
    ) -> Optional[CacheLine]:
        for line in self.sets[set_index]:
            if line.valid and line.tag == tag:
                return line
        return None

    def _choose_victim(self, set_index: int) -> CacheLine:
        """
        Choose an invalid line first.

        If all lines are valid, choose according to the configured policy.
        """
        current_set = self.sets[set_index]

        for line in current_set:
            if not line.valid:
                return line

        if self.replacement_policy == ReplacementPolicy.LRU:
            return min(current_set, key=lambda line: line.last_used)

        if self.replacement_policy == ReplacementPolicy.FIFO:
            return min(current_set, key=lambda line: line.inserted_at)

        raise RuntimeError("Unsupported replacement policy.")

    def _classify_miss(self, block_number: int) -> str:
        """
        Educational miss classification.

        A first reference is classified as compulsory.

        For later misses, this simulator uses cache occupancy and previous
        eviction information to provide an approximate classification.

        Exact hardware miss classification can require a parallel reference
        model, especially when several miss causes overlap.
        """
        if block_number not in self.seen_blocks:
            return "compulsory"

        if block_number in self.evicted_blocks:
            if self.associativity == 1:
                return "conflict"

            return "capacity_or_conflict"

        return "unknown"

    def _record_miss_classification(self, classification: str) -> None:
        if classification == "compulsory":
            self.statistics.compulsory_misses += 1
        elif classification == "conflict":
            self.statistics.conflict_misses += 1
        elif classification == "capacity_or_conflict":
            # We assign this to capacity for the summary while documenting
            # that real classification can require a reference-model study.
            self.statistics.capacity_misses += 1

    def access(
        self,
        address: int,
        operation: str = "read",
        verbose: bool = False,
    ) -> AccessResult:
        """
        Access one byte address.

        operation:
            "read" or "write"

        The simulator models cache tags and replacement behavior. It does not
        model actual data bytes; the objective is cache behavior.
        """
        operation = operation.lower()

        if operation not in {"read", "write"}:
            raise ValueError("operation must be 'read' or 'write'.")

        if address < 0:
            raise ValueError("address cannot be negative.")

        self.clock += 1
        self.statistics.accesses += 1

        block_number, offset, set_index, tag = address_fields(
            address,
            self.block_size,
            self.number_of_sets,
        )

        line = self._find_line(set_index, tag)

        if line is not None:
            # Cache hit.
            self.statistics.hits += 1

            if operation == "write":
                self.statistics.write_hits += 1

                if self.write_policy == WritePolicy.WRITE_BACK:
                    line.dirty = True
                else:
                    # Write-through sends the update to lower memory.
                    line.dirty = False

            line.last_used = self.clock

            result = AccessResult(
                address=address,
                block_number=block_number,
                set_index=set_index,
                tag=tag,
                hit=True,
                latency=self.hit_latency,
            )

            if verbose:
                self._print_access(result, operation)

            return result

        # Cache miss.
        self.statistics.misses += 1

        if operation == "write":
            self.statistics.write_misses += 1

        classification = self._classify_miss(block_number)
        self._record_miss_classification(classification)

        self.seen_blocks.add(block_number)

        # No-write-allocate means a write miss bypasses the cache.
        if (
            operation == "write"
            and self.allocation_policy == AllocationPolicy.NO_WRITE_ALLOCATE
        ):
            result = AccessResult(
                address=address,
                block_number=block_number,
                set_index=set_index,
                tag=tag,
                hit=False,
                latency=self.miss_latency,
            )

            if verbose:
                self._print_access(result, operation)

            return result

        victim = self._choose_victim(set_index)

        evicted_tag: Optional[int] = None
        dirty_eviction = False

        if victim.valid:
            evicted_tag = victim.tag
            dirty_eviction = victim.dirty

            evicted_block = (
                victim.tag * self.number_of_sets + set_index
            )

            self.evicted_blocks.add(evicted_block)

            if victim.dirty and self.write_policy == WritePolicy.WRITE_BACK:
                self.statistics.write_backs += 1

        # Fill the cache line with the requested memory block.
        victim.valid = True
        victim.tag = tag
        victim.last_used = self.clock
        victim.inserted_at = self.clock

        # A write miss with write-allocate modifies the newly allocated line.
        if operation == "write":
            victim.dirty = (
                self.write_policy == WritePolicy.WRITE_BACK
            )
        else:
            victim.dirty = False

        result = AccessResult(
            address=address,
            block_number=block_number,
            set_index=set_index,
            tag=tag,
            hit=False,
            latency=self.hit_latency + self.miss_latency,
            evicted_tag=evicted_tag,
            dirty_eviction=dirty_eviction,
        )

        if verbose:
            self._print_access(result, operation)

        return result

    def _print_access(
        self,
        result: AccessResult,
        operation: str,
    ) -> None:
        status = "HIT " if result.hit else "MISS"
        eviction = ""

        if result.evicted_tag is not None:
            eviction = f", evicted_tag={result.evicted_tag}"

        if result.dirty_eviction:
            eviction += ", dirty_writeback=True"

        print(
            f"{operation.upper():5} address={result.address:4} "
            f"block={result.block_number:3} "
            f"set={result.set_index:2} "
            f"tag={result.tag:3} "
            f"{status} latency={result.latency:3}{eviction}"
        )

    def run(
        self,
        addresses: Iterable[int],
        operation: str = "read",
        verbose: bool = False,
    ) -> list[AccessResult]:
        """Run a sequence of addresses."""
        return [
            self.access(address, operation=operation, verbose=verbose)
            for address in addresses
        ]

    def describe(self) -> None:
        """Print cache geometry and configuration."""
        cache_type = (
            AssociativityType.DIRECT_MAPPED.value
            if self.associativity == 1
            else (
                AssociativityType.FULLY_ASSOCIATIVE.value
                if self.associativity == self.number_of_lines
                else AssociativityType.SET_ASSOCIATIVE.value
            )
        )

        print("\nCache configuration")
        print("-------------------")
        print(f"Capacity:            {self.cache_size} bytes")
        print(f"Block size:          {self.block_size} bytes")
        print(f"Lines:               {self.number_of_lines}")
        print(f"Sets:                {self.number_of_sets}")
        print(f"Associativity:       {self.associativity}-way")
        print(f"Mapping:             {cache_type}")
        print(f"Replacement:         {self.replacement_policy.value}")
        print(f"Write policy:        {self.write_policy.value}")
        print(f"Allocation policy:   {self.allocation_policy.value}")
        print(f"Hit latency:         {self.hit_latency}")
        print(f"Miss penalty:        {self.miss_latency}")

    def dump(self) -> None:
        """Display the current tag state of the cache."""
        print("\nCache contents")
        print("--------------")

        for set_index, current_set in enumerate(self.sets):
            print(f"Set {set_index:2}: ", end="")

            entries = []
            for way, line in enumerate(current_set):
                if line.valid:
                    dirty = "*" if line.dirty else " "
                    entries.append(
                        f"way {way}: tag={line.tag:<4}{dirty}"
                    )
                else:
                    entries.append(f"way {way}: EMPTY")

            print(" | ".join(entries))


# ---------------------------------------------------------------------------
# Educational demonstrations
# ---------------------------------------------------------------------------

def demonstrate_cache_levels() -> None:
    """
    Explain the usual hierarchy.

    Actual hardware values differ by CPU architecture. The values below are
    illustrative rather than specifications for a particular processor.
    """
    print("\nCACHE LEVELS")
    print("============")
    levels = [
        ("L1", "smallest", "fastest", "usually private to a core"),
        ("L2", "larger", "slower than L1", "often private to a core"),
        ("L3", "larger again", "slower than L2", "often shared by cores"),
        ("RAM", "much larger", "much slower", "main memory"),
    ]

    for name, size, speed, role in levels:
        print(
            f"{name:4} size={size:12} speed={speed:18} role={role}"
        )

    print(
        "\nThe hierarchy works because programs frequently reuse data "
        "and often access nearby memory addresses."
    )


def demonstrate_address_mapping() -> None:
    """Show tag/index/offset calculations."""
    print("\nADDRESS MAPPING")
    print("===============")

    explain_address(
        address=37,
        cache_size=64,
        block_size=8,
        associativity=1,
    )

    print("\nFor this example:")
    print("  cache size = 64 bytes")
    print("  block size = 8 bytes")
    print("  number of lines = 8")
    print("  number of sets = 8")
    print("  direct mapping means one possible line per set")


def demonstrate_locality() -> None:
    """Compare sequential and strided access patterns."""
    print("\nLOCALITY")
    print("========")

    cache = CacheSimulator(
        cache_size=64,
        block_size=16,
        associativity=2,
        miss_latency=20,
    )

    sequential = list(range(0, 64, 4))

    print("\nSequential access:")
    cache.run(sequential, verbose=True)
    cache.statistics.print_report("Sequential pattern")

    cache.reset()

    print("\nRepeated temporal-locality pattern:")
    temporal = [0, 4, 8, 0, 4, 8, 0, 4, 8]
    cache.run(temporal, verbose=True)
    cache.statistics.print_report("Temporal locality pattern")

    cache.reset()

    print("\nStrided pattern:")
    strided = list(range(0, 128, 32))
    cache.run(strided, verbose=True)
    cache.statistics.print_report("Strided pattern")


def compare_mapping_techniques() -> None:
    """Compare direct mapping, set associativity, and full associativity."""
    print("\nMAPPING TECHNIQUES")
    print("==================")

    addresses = [
        0, 32, 64, 96,
        0, 32, 64, 96,
        0, 32, 64, 96,
    ]

    configurations = [
        ("Direct mapped", 1),
        ("2-way set associative", 2),
        ("Fully associative", 8),
    ]

    for name, associativity in configurations:
        cache = CacheSimulator(
            cache_size=64,
            block_size=8,
            associativity=associativity,
        )

        cache.run(addresses)

        print(
            f"{name:28} "
            f"hits={cache.statistics.hits:2} "
            f"misses={cache.statistics.misses:2} "
            f"hit_rate={cache.statistics.hit_rate:.2%}"
        )


def demonstrate_replacement_policies() -> None:
    """Show the effect of LRU and FIFO."""
    print("\nREPLACEMENT POLICIES")
    print("====================")

    sequence = [0, 8, 16, 0, 8, 24, 0, 8]

    for policy in (
        ReplacementPolicy.LRU,
        ReplacementPolicy.FIFO,
    ):
        cache = CacheSimulator(
            cache_size=16,
            block_size=8,
            associativity=2,
            replacement_policy=policy,
        )

        cache.run(sequence)

        print(
            f"{policy.value:5} "
            f"hits={cache.statistics.hits} "
            f"misses={cache.statistics.misses} "
            f"hit_rate={cache.statistics.hit_rate:.2%}"
        )


def demonstrate_write_policies() -> None:
    """Compare write-back and write-through behavior."""
    print("\nWRITE POLICIES")
    print("==============")

    sequence = [
        ("write", 0),
        ("read", 0),
        ("write", 0),
        ("write", 16),
        ("read", 0),
    ]

    for policy in (
        WritePolicy.WRITE_BACK,
        WritePolicy.WRITE_THROUGH,
    ):
        cache = CacheSimulator(
            cache_size=16,
            block_size=8,
            associativity=1,
            write_policy=policy,
            allocation_policy=AllocationPolicy.WRITE_ALLOCATE,
        )

        print(f"\n{policy.value}")
        for operation, address in sequence:
            cache.access(address, operation, verbose=True)

        cache.statistics.print_report(
            f"Statistics for {policy.value}"
        )


def demonstrate_multilevel_cache() -> None:
    """
    Model a simple L1/L2/RAM hierarchy.

    On an L1 miss, L2 is checked. On an L2 miss, main memory is assumed to
    satisfy the request. This example focuses on hit/miss behavior rather
    than implementing coherence or inclusive/exclusive cache policies.
    """
    print("\nMULTI-LEVEL CACHE")
    print("=================")

    l1 = CacheSimulator(
        cache_size=32,
        block_size=8,
        associativity=2,
        hit_latency=1,
        miss_latency=4,
    )

    l2 = CacheSimulator(
        cache_size=128,
        block_size=8,
        associativity=4,
        hit_latency=8,
        miss_latency=40,
    )

    accesses = [0, 8, 16, 24, 0, 8, 64, 72, 0, 8]

    total_cycles = 0

    for address in accesses:
        l1_result = l1.access(address)

        if l1_result.hit:
            total_cycles += l1.hit_latency
            print(
                f"address={address:3} -> L1 HIT, "
                f"latency={l1.hit_latency}"
            )
            continue

        l2_result = l2.access(address)

        if l2_result.hit:
            total_cycles += l1.miss_latency + l2.hit_latency
            print(
                f"address={address:3} -> L1 MISS, L2 HIT, "
                f"latency={l1.miss_latency + l2.hit_latency}"
            )
        else:
            total_cycles += (
                l1.miss_latency
                + l2.miss_latency
            )
            print(
                f"address={address:3} -> L1 MISS, L2 MISS, RAM, "
                f"latency={l1.miss_latency + l2.miss_latency}"
            )

    print(f"\nEstimated total cycles: {total_cycles}")

    l1.statistics.print_report("L1")
    l2.statistics.print_report("L2")


def demonstrate_edge_cases() -> None:
    """Exercise important validation and boundary conditions."""
    print("\nEDGE CASES")
    print("==========")

    cache = CacheSimulator(
        cache_size=16,
        block_size=4,
        associativity=2,
    )

    addresses = [0, 3, 4, 7, 8, 12, 15, 16]

    for address in addresses:
        result = cache.access(address)
        print(
            f"address={address:2}, "
            f"block={result.block_number:2}, "
            f"set={result.set_index}, "
            f"tag={result.tag}, "
            f"hit={result.hit}"
        )

    invalid_values = [
        (-1, 4, 1),
        (16, 3, 1),
        (16, 4, 3),
    ]

    for cache_size, block_size, associativity in invalid_values:
        try:
            CacheSimulator(
                cache_size=cache_size,
                block_size=block_size,
                associativity=associativity,
            )
        except ValueError as error:
            print(f"Rejected invalid configuration: {error}")


def calculate_average_memory_access_time(
    hit_time: float,
    miss_rate: float,
    miss_penalty: float,
) -> float:
    """
    AMAT = hit time + miss rate * miss penalty

    This is the classic single-level approximation.
    """
    return hit_time + miss_rate * miss_penalty


def demonstrate_amat() -> None:
    """Calculate effective memory access time."""
    print("\nAVERAGE MEMORY ACCESS TIME")
    print("==========================")

    examples = [
        (1.0, 0.05, 50.0),
        (1.0, 0.10, 50.0),
        (2.0, 0.02, 80.0),
    ]

    for hit_time, miss_rate, miss_penalty in examples:
        amat = calculate_average_memory_access_time(
            hit_time,
            miss_rate,
            miss_penalty,
        )

        print(
            f"hit={hit_time:.1f}, "
            f"miss_rate={miss_rate:.2%}, "
            f"penalty={miss_penalty:.1f} "
            f"=> AMAT={amat:.2f}"
        )


def run_custom_trace() -> None:
    """
    A more realistic trace containing reads and writes.

    This demonstrates how a simulator can consume a memory-reference trace.
    """
    print("\nCUSTOM MEMORY TRACE")
    print("===================")

    cache = CacheSimulator(
        cache_size=128,
        block_size=16,
        associativity=4,
        replacement_policy=ReplacementPolicy.LRU,
        write_policy=WritePolicy.WRITE_BACK,
        allocation_policy=AllocationPolicy.WRITE_ALLOCATE,
        hit_latency=1,
        miss_latency=30,
    )

    trace = [
        ("read", 0),
        ("read", 4),
        ("read", 8),
        ("read", 16),
        ("write", 20),
        ("read", 64),
        ("read", 68),
        ("write", 0),
        ("read", 128),
        ("read", 0),
        ("write", 64),
        ("read", 64),
    ]

    for operation, address in trace:
        cache.access(
            address,
            operation=operation,
            verbose=True,
        )

    cache.describe()
    cache.dump()
    cache.statistics.print_report("Trace statistics")


def compare_block_sizes() -> None:
    """
    Larger blocks can exploit spatial locality but may waste bandwidth and
    cache capacity when accesses are sparse.
    """
    print("\nBLOCK SIZE COMPARISON")
    print("=====================")

    trace = list(range(0, 256, 4))

    for block_size in (4, 8, 16, 32):
        cache = CacheSimulator(
            cache_size=64,
            block_size=block_size,
            associativity=2,
        )

        cache.run(trace)

        print(
            f"block={block_size:2} bytes "
            f"hits={cache.statistics.hits:3} "
            f"misses={cache.statistics.misses:3} "
            f"hit_rate={cache.statistics.hit_rate:.2%}"
        )


def compare_workload_patterns() -> None:
    """Compare common memory access patterns."""
    print("\nWORKLOAD PATTERN COMPARISON")
    print("===========================")

    patterns = {
        "sequential": list(range(0, 256, 4)),
        "reverse sequential": list(range(252, -1, -4)),
        "repeated": [0, 4, 8, 12] * 16,
        "stride 16": list(range(0, 256, 16)),
        "stride 64": list(range(0, 256, 64)),
    }

    for name, trace in patterns.items():
        cache = CacheSimulator(
            cache_size=64,
            block_size=16,
            associativity=2,
        )

        cache.run(trace)

        print(
            f"{name:20} "
            f"accesses={len(trace):3} "
            f"hits={cache.statistics.hits:3} "
            f"misses={cache.statistics.misses:3} "
            f"hit_rate={cache.statistics.hit_rate:.2%}"
        )


# ---------------------------------------------------------------------------
# Practical cache-aware algorithms
# ---------------------------------------------------------------------------

def row_major_matrix_access(rows: int, columns: int) -> list[int]:
    """
    Return addresses for row-major traversal.

    In a row-major layout, adjacent columns occupy adjacent memory locations,
    so traversing rows normally has strong spatial locality.
    """
    return [
        row * columns + column
        for row in range(rows)
        for column in range(columns)
    ]


def column_major_like_access(rows: int, columns: int) -> list[int]:
    """
    Access a row-major matrix column by column.

    The address jumps by an entire row, which can reduce spatial locality.
    """
    return [
        row * columns + column
        for column in range(columns)
        for row in range(rows)
    ]


def compare_matrix_traversals() -> None:
    """Demonstrate why memory layout and traversal order matter."""
    print("\nMATRIX TRAVERSAL AND CACHE LOCALITY")
    print("===================================")

    rows = 16
    columns = 16

    row_trace = row_major_matrix_access(rows, columns)
    column_trace = column_major_like_access(rows, columns)

    for name, trace in (
        ("Row-major traversal", row_trace),
        ("Column-wise traversal", column_trace),
    ):
        cache = CacheSimulator(
            cache_size=128,
            block_size=16,
            associativity=4,
        )

        cache.run(trace)

        print(
            f"{name:24} "
            f"hits={cache.statistics.hits:3} "
            f"misses={cache.statistics.misses:3} "
            f"hit_rate={cache.statistics.hit_rate:.2%}"
        )


# ---------------------------------------------------------------------------
# Main educational driver
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 72)
    print("CACHE MEMORY AND CACHE SIMULATOR")
    print("=" * 72)

    demonstrate_cache_levels()
    demonstrate_address_mapping()
    demonstrate_locality()
    compare_mapping_techniques()
    demonstrate_replacement_policies()
    demonstrate_write_policies()
    demonstrate_multilevel_cache()
    demonstrate_edge_cases()
    demonstrate_amat()
    run_custom_trace()
    compare_block_sizes()
    compare_workload_patterns()
    compare_matrix_traversals()

    print("\nKEY FORMULAS")
    print("============")
    print("Number of cache lines = cache size / block size")
    print("Number of sets = number of lines / associativity")
    print("Block number = address // block size")
    print("Offset = address % block size")
    print("Set index = block number % number of sets")
    print("Tag = block number // number of sets")
    print("Hit rate = hits / total accesses")
    print("Miss rate = misses / total accesses")
    print("AMAT = hit time + miss rate * miss penalty")

    print("\nSIMULATION COMPLETE")


if __name__ == "__main__":
    main()
