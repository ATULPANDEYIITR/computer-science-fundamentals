"""
Paging and Segmentation: page tables, segmentation, address translation,
and memory protection.

Self-contained executable teaching simulator. It models a simplified 32-bit
virtual address space with paging, segmentation, permissions, TLB behavior,
page faults, and combined segmentation-plus-paging translation.

The simulator deliberately uses software data structures rather than real
OS page tables so that every translation and protection decision is visible.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple


class MemoryFault(Exception):
    """Base class for simulated memory-management faults."""


class PageFault(MemoryFault):
    pass


class ProtectionFault(MemoryFault):
    pass


class SegmentFault(MemoryFault):
    pass


class AccessType(Enum):
    READ = auto()
    WRITE = auto()
    EXECUTE = auto()


@dataclass
class PageTableEntry:
    frame: int
    present: bool = True
    readable: bool = True
    writable: bool = False
    executable: bool = False
    user: bool = True
    accessed: bool = False
    dirty: bool = False


@dataclass
class SegmentDescriptor:
    name: str
    base: int
    limit: int
    readable: bool
    writable: bool
    executable: bool


@dataclass
class Translation:
    virtual_address: int
    physical_address: int
    page_number: int
    offset: int
    frame: int
    segment: Optional[str] = None
    tlb_hit: bool = False


class TLB:
    """Small fully-associative software TLB with FIFO replacement."""

    def __init__(self, capacity: int = 4):
        if capacity <= 0:
            raise ValueError("TLB capacity must be positive")
        self.capacity = capacity
        self.entries: Dict[int, int] = {}
        self.order: List[int] = []
        self.hits = 0
        self.misses = 0

    def lookup(self, page: int) -> Optional[int]:
        if page in self.entries:
            self.hits += 1
            return self.entries[page]
        self.misses += 1
        return None

    def insert(self, page: int, frame: int) -> None:
        if page in self.entries:
            self.entries[page] = frame
            return

        if len(self.entries) >= self.capacity:
            victim = self.order.pop(0)
            del self.entries[victim]

        self.entries[page] = frame
        self.order.append(page)

    def invalidate(self, page: Optional[int] = None) -> None:
        if page is None:
            self.entries.clear()
            self.order.clear()
        elif page in self.entries:
            del self.entries[page]
            self.order.remove(page)

    def statistics(self) -> Tuple[int, int]:
        return self.hits, self.misses


class PagedMemory:
    """A simplified single-level page-table system."""

    def __init__(
        self,
        virtual_bits: int = 16,
        physical_bits: int = 16,
        page_bits: int = 8,
        tlb_capacity: int = 4,
    ):
        if page_bits >= virtual_bits:
            raise ValueError("Page size must be smaller than virtual address width")
        self.virtual_bits = virtual_bits
        self.physical_bits = physical_bits
        self.page_bits = page_bits
        self.page_size = 1 << page_bits
        self.virtual_size = 1 << virtual_bits
        self.physical_size = 1 << physical_bits
        self.frame_count = self.physical_size // self.page_size
        self.page_count = self.virtual_size // self.page_size

        self.page_table: Dict[int, PageTableEntry] = {}
        self.physical_memory = bytearray(self.physical_size)
        self.tlb = TLB(tlb_capacity)
        self.next_free_frame = 0

    def map_page(
        self,
        page: int,
        readable: bool = True,
        writable: bool = False,
        executable: bool = False,
        user: bool = True,
        frame: Optional[int] = None,
    ) -> None:
        if not 0 <= page < self.page_count:
            raise ValueError("Virtual page is outside the address space")
        if frame is None:
            if self.next_free_frame >= self.frame_count:
                raise MemoryError("No physical frames available")
            frame = self.next_free_frame
            self.next_free_frame += 1
        if not 0 <= frame < self.frame_count:
            raise ValueError("Physical frame is outside physical memory")

        self.page_table[page] = PageTableEntry(
            frame=frame,
            readable=readable,
            writable=writable,
            executable=executable,
            user=user,
        )
        self.tlb.invalidate(page)

    def unmap_page(self, page: int) -> None:
        self.page_table.pop(page, None)
        self.tlb.invalidate(page)

    def _check_permission(self, entry: PageTableEntry, access: AccessType) -> None:
        allowed = {
            AccessType.READ: entry.readable,
            AccessType.WRITE: entry.writable,
            AccessType.EXECUTE: entry.executable,
        }[access]
        if not allowed:
            raise ProtectionFault(f"{access.name} access denied by page permissions")

    def translate(self, virtual_address: int, access: AccessType) -> Translation:
        if not 0 <= virtual_address < self.virtual_size:
            raise MemoryFault("Virtual address is outside the address space")

        page = virtual_address >> self.page_bits
        offset = virtual_address & (self.page_size - 1)

        frame = self.tlb.lookup(page)
        tlb_hit = frame is not None

        if frame is None:
            entry = self.page_table.get(page)
            if entry is None or not entry.present:
                raise PageFault(f"Page fault: virtual page {page} is not mapped")
            frame = entry.frame
            self.tlb.insert(page, frame)
        else:
            entry = self.page_table.get(page)
            if entry is None or not entry.present:
                self.tlb.invalidate(page)
                raise PageFault("Stale TLB entry references an unmapped page")

        self._check_permission(entry, access)

        entry.accessed = True
        if access == AccessType.WRITE:
            entry.dirty = True

        physical_address = frame * self.page_size + offset
        return Translation(
            virtual_address=virtual_address,
            physical_address=physical_address,
            page_number=page,
            offset=offset,
            frame=frame,
            tlb_hit=tlb_hit,
        )

    def read(self, virtual_address: int, size: int = 1) -> bytes:
        if size < 0:
            raise ValueError("Read size cannot be negative")
        result = bytearray()
        for address in range(virtual_address, virtual_address + size):
            translation = self.translate(address, AccessType.READ)
            result.append(self.physical_memory[translation.physical_address])
        return bytes(result)

    def write(self, virtual_address: int, data: bytes) -> None:
        for index, value in enumerate(data):
            translation = self.translate(virtual_address + index, AccessType.WRITE)
            self.physical_memory[translation.physical_address] = value

    def execute(self, virtual_address: int) -> int:
        translation = self.translate(virtual_address, AccessType.EXECUTE)
        return self.physical_memory[translation.physical_address]


class SegmentedMemory:
    """
    Segmentation performs logical-address validation before paging.

    A logical address is represented as (segment name, offset). The segment
    descriptor supplies a base and limit. Only after the segment check succeeds
    is the resulting linear address sent through the paging subsystem.
    """

    def __init__(self, pager: PagedMemory):
        self.pager = pager
        self.segments: Dict[str, SegmentDescriptor] = {}

    def add_segment(
        self,
        name: str,
        base: int,
        limit: int,
        readable: bool,
        writable: bool,
        executable: bool,
    ) -> None:
        if base < 0 or limit < 0:
            raise ValueError("Segment base and limit must be non-negative")
        if base + limit >= self.pager.virtual_size:
            raise ValueError("Segment exceeds the linear address space")

        self.segments[name] = SegmentDescriptor(
            name=name,
            base=base,
            limit=limit,
            readable=readable,
            writable=writable,
            executable=executable,
        )

    def translate(
        self,
        segment_name: str,
        offset: int,
        access: AccessType,
    ) -> Translation:
        segment = self.segments.get(segment_name)
        if segment is None:
            raise SegmentFault(f"Unknown segment: {segment_name}")

        if not 0 <= offset <= segment.limit:
            raise SegmentFault(
                f"Offset {offset} exceeds segment '{segment_name}' limit "
                f"{segment.limit}"
            )

        permission = {
            AccessType.READ: segment.readable,
            AccessType.WRITE: segment.writable,
            AccessType.EXECUTE: segment.executable,
        }[access]
        if not permission:
            raise ProtectionFault(
                f"{access.name} access denied by segment '{segment_name}'"
            )

        linear_address = segment.base + offset
        translation = self.pager.translate(linear_address, access)
        translation.segment = segment_name
        return translation


def demonstrate_basic_paging() -> None:
    print("\n=== Basic paging and address translation ===")
    memory = PagedMemory(virtual_bits=16, physical_bits=16, page_bits=8)

    # Virtual page 2 is backed by physical frame 7. The physical location
    # therefore has a different page number while preserving the offset.
    memory.map_page(2, readable=True, writable=True, executable=False, frame=7)

    virtual_address = (2 << 8) | 37
    translation = memory.translate(virtual_address, AccessType.READ)

    print(f"Virtual address:  {virtual_address}")
    print(f"Virtual page:     {translation.page_number}")
    print(f"Page offset:      {translation.offset}")
    print(f"Physical frame:   {translation.frame}")
    print(f"Physical address: {translation.physical_address}")
    print(f"TLB hit:           {translation.tlb_hit}")

    memory.write(virtual_address, b"A")
    print("Stored byte:", memory.read(virtual_address, 1).decode())


def demonstrate_protection() -> None:
    print("\n=== Page-level memory protection ===")
    memory = PagedMemory()
    memory.map_page(4, readable=True, writable=False, executable=False)

    address = (4 << 8) + 10
    print("Reading a read-only page is valid:", memory.read(address))

    try:
        memory.write(address, b"X")
    except ProtectionFault as error:
        print("Write rejected:", error)

    try:
        memory.execute(address)
    except ProtectionFault as error:
        print("Execution rejected:", error)


def demonstrate_page_faults() -> None:
    print("\n=== Page faults ===")
    memory = PagedMemory()
    memory.map_page(1, readable=True)

    valid = (1 << 8) + 3
    invalid = (9 << 8) + 3

    print("Mapped read:", memory.read(valid))
    try:
        memory.read(invalid)
    except PageFault as error:
        print("Expected fault:", error)


def demonstrate_cross_page_access() -> None:
    print("\n=== Cross-page access ===")
    memory = PagedMemory()
    memory.map_page(3, readable=True, writable=True, frame=1)
    memory.map_page(4, readable=True, writable=True, frame=8)

    # This write begins near the end of page 3 and continues into page 4.
    start = (3 << 8) + 254
    memory.write(start, b"ABCD")
    print("Cross-page bytes:", memory.read(start, 4))


def demonstrate_tlb() -> None:
    print("\n=== TLB behavior ===")
    memory = PagedMemory(tlb_capacity=2)
    for page, frame in ((1, 5), (2, 6), (3, 7)):
        memory.map_page(page, readable=True, frame=frame)

    addresses = [
        1 << 8,
        (1 << 8) + 1,
        2 << 8,
        (1 << 8) + 2,
        3 << 8,
        2 << 8,
    ]

    for address in addresses:
        translation = memory.translate(address, AccessType.READ)
        print(
            f"VA {address:04x} -> PA {translation.physical_address:04x}; "
            f"{'TLB hit' if translation.tlb_hit else 'page-table lookup'}"
        )

    hits, misses = memory.tlb.statistics()
    print(f"TLB hits={hits}, misses={misses}")


def demonstrate_segmentation() -> None:
    print("\n=== Segmentation followed by paging ===")
    memory = PagedMemory()
    segmented = SegmentedMemory(memory)

    # The code segment is executable and readable but not writable.
    segmented.add_segment(
        "code",
        base=0x1000,
        limit=0x01FF,
        readable=True,
        writable=False,
        executable=True,
    )

    # The data segment permits reads and writes.
    segmented.add_segment(
        "data",
        base=0x3000,
        limit=0x02FF,
        readable=True,
        writable=True,
        executable=False,
    )

    for page in range(0x10, 0x13):
        memory.map_page(page, readable=True, writable=False, executable=True)

    for page in range(0x30, 0x33):
        memory.map_page(page, readable=True, writable=True, executable=False)

    code_translation = segmented.translate("code", 0x20, AccessType.EXECUTE)
    print(
        f"code:0x20 -> linear 0x{code_translation.virtual_address:04x} "
        f"-> physical 0x{code_translation.physical_address:04x}"
    )

    data_translation = segmented.translate("data", 0x40, AccessType.WRITE)
    print(
        f"data:0x40 -> linear 0x{data_translation.virtual_address:04x} "
        f"-> physical 0x{data_translation.physical_address:04x}"
    )

    try:
        segmented.translate("code", 0x20, AccessType.WRITE)
    except ProtectionFault as error:
        print("Segment protection rejected write:", error)

    try:
        segmented.translate("code", 0x200, AccessType.EXECUTE)
    except SegmentFault as error:
        print("Segment limit rejected access:", error)


def demonstrate_multilevel_page_table_concept() -> None:
    print("\n=== Two-level page-table calculation ===")
    virtual_address = 0xCAFEBABE
    offset_bits = 12
    second_level_bits = 10
    offset_mask = (1 << offset_bits) - 1
    second_mask = (1 << second_level_bits) - 1

    offset = virtual_address & offset_mask
    second_index = (virtual_address >> offset_bits) & second_mask
    first_index = virtual_address >> (offset_bits + second_level_bits)

    print(f"Virtual address: 0x{virtual_address:08x}")
    print(f"First-level index: {first_index}")
    print(f"Second-level index: {second_index}")
    print(f"Offset: {offset}")

    # The upper-level index selects a page-table page. The second-level
    # index selects the PTE inside that page-table page.
    print(
        "Translation path: page-directory entry -> page-table entry -> "
        "physical frame + offset"
    )


def demonstrate_replacement_and_dirty_bits() -> None:
    print("\n=== Accessed and dirty state ===")
    memory = PagedMemory()
    memory.map_page(6, readable=True, writable=True, frame=2)

    address = (6 << 8) + 11
    memory.read(address)
    entry = memory.page_table[6]
    print("After read: accessed=", entry.accessed, "dirty=", entry.dirty)

    memory.write(address, b"Z")
    print("After write: accessed=", entry.accessed, "dirty=", entry.dirty)


def run() -> None:
    print("PAGING AND SEGMENTATION MEMORY-MANAGEMENT LAB")
    demonstrate_basic_paging()
    demonstrate_protection()
    demonstrate_page_faults()
    demonstrate_cross_page_access()
    demonstrate_tlb()
    demonstrate_segmentation()
    demonstrate_multilevel_page_table_concept()
    demonstrate_replacement_and_dirty_bits()

    print("\n=== Key relationship ===")
    print(
        "Segmentation validates a logical address against a segment descriptor. "
        "Paging maps the resulting linear address to a physical frame. "
        "Protection can therefore be enforced at both stages."
    )


if __name__ == "__main__":
    run()
