"""
STORAGE SYSTEMS: HDD, SSD, FLASH STORAGE, FILE STORAGE, AND BLOCK STORAGE

A self-contained study and demonstration program covering storage media,
storage abstractions, performance characteristics, reliability, validation,
caching, allocation, file storage, block storage, and practical system design.

Run with:
    python storage_systems.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from collections import OrderedDict
import hashlib
import math
import os
import random
import tempfile
import time
from typing import Dict, Iterable, List, Optional, Tuple


# ============================================================================
# 1. FUNDAMENTAL STORAGE TERMINOLOGY
# ============================================================================

def print_section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def print_subsection(title: str) -> None:
    print("\n--- " + title + " ---")


def human_bytes(value: int) -> str:
    """Convert a byte count into a readable IEC-style value."""
    if value < 1024:
        return f"{value} B"

    units = ["KiB", "MiB", "GiB", "TiB", "PiB"]
    number = float(value)

    for unit in units:
        number /= 1024
        if number < 1024:
            return f"{number:.2f} {unit}"

    return f"{number:.2f} EiB"


def demonstrate_storage_units() -> None:
    print_section("1. STORAGE FUNDAMENTALS")

    values = [
        512,
        4096,
        1024 * 1024,
        10 * 1024 * 1024,
        5 * 1024**3,
    ]

    for value in values:
        print(f"{value:,} bytes = {human_bytes(value)}")

    print(
        """
Storage is persistent or semi-persistent capacity used to retain digital data.

Important terms:
- bit: smallest binary information unit, 0 or 1.
- byte: normally 8 bits.
- sector: a low-level addressable unit traditionally associated with disks.
- block: a logical storage unit exposed by many block devices.
- file: named data managed through a filesystem.
- filesystem: software structure that organizes files, directories, metadata,
  permissions, allocation, and recovery.
- storage medium: physical technology that retains data.
- storage interface: mechanism through which a host communicates with storage.
- latency: time required to begin or complete an operation.
- throughput: amount of data transferred per unit time.
- IOPS: input/output operations per second.
- capacity: amount of data that can be stored.
- durability: ability to retain data after power loss or failures.
- availability: ability to access the storage when required.

A critical distinction is that storage media and storage abstractions are
different layers. An SSD is a physical storage technology, while a filesystem
is a software abstraction that can operate on a block device backed by an SSD.
"""
    )


# ============================================================================
# 2. STORAGE MEDIA MODEL
# ============================================================================

class StorageTechnology(Enum):
    HDD = "Hard Disk Drive"
    SSD = "Solid State Drive"
    FLASH = "Flash Storage"


@dataclass
class TechnologyProfile:
    technology: StorageTechnology
    moving_parts: bool
    typical_latency_us: float
    relative_iops: int
    sequential_read_mb_s: float
    sequential_write_mb_s: float
    endurance_description: str


TECHNOLOGY_PROFILES = {
    StorageTechnology.HDD: TechnologyProfile(
        StorageTechnology.HDD,
        moving_parts=True,
        typical_latency_us=5000,
        relative_iops=150,
        sequential_read_mb_s=180,
        sequential_write_mb_s=160,
        endurance_description="Mechanical wear and head/platter failure are relevant.",
    ),
    StorageTechnology.SSD: TechnologyProfile(
        StorageTechnology.SSD,
        moving_parts=False,
        typical_latency_us=100,
        relative_iops=100_000,
        sequential_read_mb_s=550,
        sequential_write_mb_s=500,
        endurance_description="NAND program/erase cycles and controller behavior matter.",
    ),
    StorageTechnology.FLASH: TechnologyProfile(
        StorageTechnology.FLASH,
        moving_parts=False,
        typical_latency_us=80,
        relative_iops=80_000,
        sequential_read_mb_s=400,
        sequential_write_mb_s=350,
        endurance_description="Flash cells have finite program/erase endurance.",
    ),
}


def compare_storage_media() -> None:
    print_section("2. HDD, SSD, AND FLASH STORAGE")

    for technology, profile in TECHNOLOGY_PROFILES.items():
        print(f"\n{technology.value}")
        print(f"  Moving parts: {profile.moving_parts}")
        print(f"  Illustrative latency: {profile.typical_latency_us} us")
        print(f"  Illustrative IOPS: {profile.relative_iops:,}")
        print(f"  Sequential read: {profile.sequential_read_mb_s} MB/s")
        print(f"  Sequential write: {profile.sequential_write_mb_s} MB/s")
        print(f"  Endurance: {profile.endurance_description}")

    print(
        """
HDD:
A hard disk drive stores data magnetically on rotating platters. A mechanical
actuator positions read/write heads. Performance depends strongly on seek
distance, rotational position, request size, queueing, and access pattern.

SSD:
A solid-state drive has no rotating platter or moving read/write head. It
normally uses NAND flash plus a controller, firmware, mapping structures,
error correction, garbage collection, and often a DRAM or host-memory cache.

Flash storage:
Flash is a non-volatile semiconductor storage technology. NAND flash is used
in SSDs, USB drives, memory cards, and embedded storage. An SSD is therefore
one important product built around flash, but "flash storage" and "SSD" are
not perfectly interchangeable terms.

The numerical values above are illustrative, not universal specifications.
Real performance depends on hardware, workload, queue depth, thermal state,
capacity, controller, firmware, interface, and data locality.
"""
    )


# ============================================================================
# 3. HDD ACCESS MODEL
# ============================================================================

@dataclass
class HDDGeometry:
    tracks: int
    sectors_per_track: int
    bytes_per_sector: int
    rotations_per_minute: int

    @property
    def capacity_bytes(self) -> int:
        return (
            self.tracks
            * self.sectors_per_track
            * self.bytes_per_sector
        )

    @property
    def rotation_period_ms(self) -> float:
        return 60_000 / self.rotations_per_minute


def simulate_hdd_access(
    geometry: HDDGeometry,
    current_track: int,
    requested_track: int,
) -> Dict[str, float]:
    """Estimate mechanical components of a simplified HDD access."""
    distance = abs(requested_track - current_track)

    # This is deliberately a simplified educational seek model.
    seek_ms = 2.0 + distance * 0.02
    average_rotational_latency_ms = geometry.rotation_period_ms / 2
    transfer_ms = geometry.bytes_per_sector / (
        geometry.sectors_per_track
        * geometry.bytes_per_sector
        / geometry.rotation_period_ms
    )

    return {
        "seek_ms": seek_ms,
        "rotational_latency_ms": average_rotational_latency_ms,
        "transfer_ms": transfer_ms,
        "estimated_total_ms": (
            seek_ms + average_rotational_latency_ms + transfer_ms
        ),
    }


def demonstrate_hdd() -> None:
    print_section("3. HDD MECHANICAL ACCESS")

    disk = HDDGeometry(
        tracks=10_000,
        sectors_per_track=512,
        bytes_per_sector=512,
        rotations_per_minute=7200,
    )

    estimate = simulate_hdd_access(disk, current_track=100, requested_track=4100)

    print(f"Illustrative capacity: {human_bytes(disk.capacity_bytes)}")
    print(f"Rotation period: {disk.rotation_period_ms:.2f} ms")

    for key, value in estimate.items():
        print(f"{key}: {value:.3f} ms")

    print(
        """
HDD access commonly involves:
1. Seek: moving the actuator to the target track.
2. Rotational latency: waiting for the desired sector to rotate underneath
   the head.
3. Transfer: reading or writing the requested bytes.

This explains why random small I/O can be dramatically slower on HDDs than
large sequential I/O.
"""
    )


# ============================================================================
# 4. FLASH AND SSD INTERNAL CONCEPTS
# ============================================================================

class FlashCellType(Enum):
    SLC = ("SLC", 1)
    MLC = ("MLC", 2)
    TLC = ("TLC", 3)
    QLC = ("QLC", 4)


def explain_flash_cells() -> None:
    print_section("4. NAND FLASH CELL TYPES")

    for cell_type in FlashCellType:
        name, bits = cell_type.value
        print(f"{name}: approximately {bits} bit(s) represented per cell")

    print(
        """
Common NAND terminology:
- SLC: Single-Level Cell.
- MLC: Multi-Level Cell.
- TLC: Triple-Level Cell.
- QLC: Quad-Level Cell.

Increasing bits per cell can improve density and reduce cost per stored bit,
but it can also introduce more demanding voltage-state management and may
affect write performance and endurance.

Modern SSD controllers use several techniques:
- Flash Translation Layer (FTL): maps logical block addresses to NAND pages.
- Wear leveling: distributes writes across flash cells.
- Garbage collection: relocates live data so obsolete pages can be erased.
- TRIM/deallocate: lets the device learn which logical ranges are no longer
  needed by the host.
- ECC: detects and corrects storage errors.
- Over-provisioning: reserves capacity for management and replacement.
- Write caching: temporarily absorbs writes to improve responsiveness.

NAND commonly has pages as read/program units and erase blocks as erase units.
Because erase is larger-grained than programming, the controller must manage
data movement carefully.
"""
    )


# ============================================================================
# 5. STORAGE HIERARCHY AND PERFORMANCE
# ============================================================================

@dataclass
class StorageLayer:
    name: str
    capacity: str
    approximate_latency: str
    persistence: str


def show_storage_hierarchy() -> None:
    print_section("5. STORAGE HIERARCHY")

    layers = [
        StorageLayer("CPU registers", "Tiny", "Sub-nanosecond scale", "Volatile"),
        StorageLayer("CPU cache", "Small", "Very low", "Volatile"),
        StorageLayer("RAM", "GB scale", "Nanosecond scale", "Volatile"),
        StorageLayer("NVMe SSD", "GB-TB scale", "Microsecond scale", "Non-volatile"),
        StorageLayer("SATA SSD", "GB-TB scale", "Microsecond scale", "Non-volatile"),
        StorageLayer("HDD", "TB scale", "Millisecond scale", "Non-volatile"),
        StorageLayer("Archive/object media", "TB-PB+ scale", "Higher", "Non-volatile"),
    ]

    for layer in layers:
        print(
            f"{layer.name:25} | "
            f"Capacity: {layer.capacity:10} | "
            f"Latency: {layer.approximate_latency:22} | "
            f"{layer.persistence}"
        )

    print(
        """
A storage system is usually a hierarchy rather than one device.

Applications may interact with a file, which is translated by a filesystem
into blocks, which are sent through an operating-system I/O stack to a block
device, which may be an SSD. The SSD controller then translates logical
addresses into physical flash locations.

This layering allows the same application-level file interface to work with
very different physical media.
"""
    )


# ============================================================================
# 6. FILE STORAGE
# ============================================================================

@dataclass
class FileMetadata:
    path: str
    size: int
    checksum: str
    created_at: float
    modified_at: float


class SimpleFileStorage:
    """
    Educational file-storage layer.

    Real filesystems are much more sophisticated. They manage metadata,
    allocation, permissions, journaling or copy-on-write behavior, caching,
    concurrency, crash recovery, and many other concerns.
    """

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, relative_path: str) -> Path:
        candidate = (self.root / relative_path).resolve()

        # Prevent path traversal outside the storage root.
        if candidate != self.root and self.root not in candidate.parents:
            raise ValueError("Path escapes the storage root")

        return candidate

    def write(self, relative_path: str, data: bytes) -> FileMetadata:
        target = self._safe_path(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        with target.open("wb") as handle:
            handle.write(data)

        return self.metadata(relative_path)

    def read(self, relative_path: str) -> bytes:
        target = self._safe_path(relative_path)

        if not target.is_file():
            raise FileNotFoundError(relative_path)

        return target.read_bytes()

    def delete(self, relative_path: str) -> None:
        target = self._safe_path(relative_path)

        if target.is_file():
            target.unlink()

    def metadata(self, relative_path: str) -> FileMetadata:
        target = self._safe_path(relative_path)

        if not target.is_file():
            raise FileNotFoundError(relative_path)

        stat = target.stat()
        checksum = hashlib.sha256(target.read_bytes()).hexdigest()

        return FileMetadata(
            path=relative_path,
            size=stat.st_size,
            checksum=checksum,
            created_at=getattr(stat, "st_birthtime", stat.st_ctime),
            modified_at=stat.st_mtime,
        )


def demonstrate_file_storage() -> None:
    print_section("6. FILE STORAGE")

    with tempfile.TemporaryDirectory() as directory:
        storage = SimpleFileStorage(Path(directory))

        payload = b"Storage systems preserve information across application runs."
        metadata = storage.write("documents/example.txt", payload)

        print(f"Stored file: {metadata.path}")
        print(f"Size: {metadata.size} bytes")
        print(f"SHA-256: {metadata.checksum}")
        print(f"Read result: {storage.read('documents/example.txt').decode()}")

        try:
            storage.read("../outside.txt")
        except ValueError as error:
            print(f"Security validation worked: {error}")

    print(
        """
File storage organizes information using names, directories and metadata.
Applications normally ask for operations such as open, read, write, rename,
and delete rather than addressing raw physical sectors.

Advantages:
- Natural application interface.
- Hierarchical organization.
- Rich metadata and permissions.
- Convenient sharing and management.

Limitations:
- Filesystem metadata introduces overhead.
- Small-file workloads can generate many metadata operations.
- Application behavior depends on filesystem semantics.
"""
    )


# ============================================================================
# 7. BLOCK STORAGE
# ============================================================================

@dataclass
class BlockDevice:
    block_size: int
    block_count: int
    storage: bytearray = field(init=False)

    def __post_init__(self) -> None:
        if self.block_size <= 0:
            raise ValueError("Block size must be positive")
        if self.block_count <= 0:
            raise ValueError("Block count must be positive")

        self.storage = bytearray(self.block_size * self.block_count)

    @property
    def capacity(self) -> int:
        return self.block_size * self.block_count

    def _validate_range(self, block_number: int) -> None:
        if not 0 <= block_number < self.block_count:
            raise IndexError("Block number is outside device range")

    def read_block(self, block_number: int) -> bytes:
        self._validate_range(block_number)
        start = block_number * self.block_size
        end = start + self.block_size
        return bytes(self.storage[start:end])

    def write_block(self, block_number: int, data: bytes) -> None:
        self._validate_range(block_number)

        if len(data) != self.block_size:
            raise ValueError(
                f"Expected exactly {self.block_size} bytes"
            )

        start = block_number * self.block_size
        self.storage[start:start + self.block_size] = data


def demonstrate_block_storage() -> None:
    print_section("7. BLOCK STORAGE")

    device = BlockDevice(block_size=512, block_count=100)

    print(f"Capacity: {human_bytes(device.capacity)}")

    record = b"BLOCK-DEVICE-RECORD".ljust(device.block_size, b"\0")
    device.write_block(7, record)

    result = device.read_block(7)
    print(f"Block 7 begins with: {result[:20]!r}")

    for invalid_block in (-1, 100):
        try:
            device.read_block(invalid_block)
        except IndexError as error:
            print(f"Invalid block {invalid_block}: {error}")

    print(
        """
Block storage exposes a sequence of fixed-addressable logical blocks.

A block storage consumer may build a filesystem, database, virtual disk, or
other structure on top of it. The block device itself does not need to
understand filenames such as "report.pdf".

File storage and block storage therefore represent different abstraction
levels:

File storage:
    application -> file API -> filesystem -> block device -> physical media

Block storage:
    application/database/filesystem -> logical blocks -> storage device
"""
    )


# ============================================================================
# 8. BLOCK ALLOCATION AND SIMPLE FILESYSTEM
# ============================================================================

class SimpleFileSystem:
    """Small educational filesystem built on top of a block device."""

    def __init__(self, device: BlockDevice):
        self.device = device
        self.free_blocks = set(range(device.block_count))
        self.files: Dict[str, List[int]] = {}

    def create_file(self, name: str, data: bytes) -> None:
        if not name or "/" in name:
            raise ValueError("File name must be non-empty and contain no '/'")

        if name in self.files:
            raise FileExistsError(name)

        required = max(
            1,
            math.ceil(len(data) / self.device.block_size),
        )

        if required > len(self.free_blocks):
            raise OSError("Insufficient free blocks")

        allocated = sorted(self.free_blocks)[:required]

        for block in allocated:
            self.free_blocks.remove(block)

        self.files[name] = allocated

        padded = data.ljust(
            required * self.device.block_size,
            b"\0",
        )

        for index, block in enumerate(allocated):
            start = index * self.device.block_size
            end = start + self.device.block_size
            self.device.write_block(block, padded[start:end])

    def read_file(self, name: str) -> bytes:
        if name not in self.files:
            raise FileNotFoundError(name)

        chunks = [
            self.device.read_block(block)
            for block in self.files[name]
        ]

        return b"".join(chunks).rstrip(b"\0")

    def delete_file(self, name: str) -> None:
        if name not in self.files:
            raise FileNotFoundError(name)

        for block in self.files.pop(name):
            self.free_blocks.add(block)

    def report(self) -> Dict[str, int]:
        return {
            "total_blocks": self.device.block_count,
            "free_blocks": len(self.free_blocks),
            "allocated_blocks": (
                self.device.block_count - len(self.free_blocks)
            ),
            "files": len(self.files),
        }


def demonstrate_filesystem() -> None:
    print_section("8. FILESYSTEM BUILT ON BLOCK STORAGE")

    device = BlockDevice(block_size=128, block_count=32)
    filesystem = SimpleFileSystem(device)

    document = (
        b"Filesystem metadata maps human-friendly file names "
        b"to storage blocks."
    )

    filesystem.create_file("document.txt", document)

    print("Filesystem report:", filesystem.report())
    print("Read:", filesystem.read_file("document.txt").decode())

    filesystem.delete_file("document.txt")
    print("After deletion:", filesystem.report())

    try:
        filesystem.read_file("document.txt")
    except FileNotFoundError:
        print("Deleted file correctly reports FileNotFoundError.")


# ============================================================================
# 9. I/O PATTERNS
# ============================================================================

def benchmark_memory_io() -> None:
    print_section("9. I/O PATTERNS AND WORKLOADS")

    dataset = bytearray(8 * 1024 * 1024)

    sequential_start = time.perf_counter()
    checksum = 0

    for value in dataset:
        checksum ^= value

    sequential_elapsed = time.perf_counter() - sequential_start

    random_start = time.perf_counter()
    random_checksum = 0

    random_generator = random.Random(42)

    for _ in range(100_000):
        index = random_generator.randrange(len(dataset))
        random_checksum ^= dataset[index]

    random_elapsed = time.perf_counter() - random_start

    print(f"Sequential scan checksum: {checksum}")
    print(f"Sequential scan time: {sequential_elapsed:.6f} seconds")
    print(f"Random access checksum: {random_checksum}")
    print(f"Random access time: {random_elapsed:.6f} seconds")

    print(
        """
Common workloads:
- Sequential read: scanning a large media file.
- Sequential write: producing a large backup.
- Random read: database indexes or metadata-heavy workloads.
- Random write: transaction-heavy databases.
- Small I/O: many tiny records.
- Large I/O: large contiguous transfers.
- Mixed I/O: simultaneous reads and writes.

Do not interpret this Python memory benchmark as a benchmark of HDD or SSD
hardware. It demonstrates workload shape, not physical-device performance.
"""
    )


# ============================================================================
# 10. IOPS, THROUGHPUT, LATENCY, AND QUEUE DEPTH
# ============================================================================

def demonstrate_performance_metrics() -> None:
    print_section("10. STORAGE PERFORMANCE METRICS")

    io_size = 4096
    iops = 100_000
    throughput_bytes_per_second = io_size * iops

    print(f"I/O size: {io_size} bytes")
    print(f"IOPS: {iops:,}")
    print(
        "Theoretical transfer rate at that workload: "
        f"{throughput_bytes_per_second / 1024**2:.2f} MiB/s"
    )

    latency_ms = 0.1
    print(f"Illustrative average latency: {latency_ms} ms")

    print(
        """
IOPS and throughput answer different questions.

Throughput is especially important for large sequential transfers.
IOPS is especially useful for workloads consisting of many small operations.
Latency describes how long an operation takes and is critical for interactive
applications.

Queue depth represents outstanding I/O requests. Higher queue depth can allow
a device to exploit parallelism, but increasing queue depth does not
automatically improve every workload and may increase latency.
"""
    )


# ============================================================================
# 11. CACHE SIMULATION
# ============================================================================

class LRUBlockCache:
    """Small LRU cache illustrating locality and cache eviction."""

    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("Cache capacity must be positive")

        self.capacity = capacity
        self.cache: OrderedDict[int, bytes] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, block_number: int) -> Optional[bytes]:
        if block_number not in self.cache:
            self.misses += 1
            return None

        self.hits += 1
        value = self.cache.pop(block_number)
        self.cache[block_number] = value
        return value

    def put(self, block_number: int, data: bytes) -> None:
        if block_number in self.cache:
            self.cache.pop(block_number)

        self.cache[block_number] = data

        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total else 0.0


def demonstrate_cache() -> None:
    print_section("11. STORAGE CACHING")

    cache = LRUBlockCache(capacity=3)

    access_pattern = [1, 2, 3, 1, 2, 4, 1, 5, 1]

    for block in access_pattern:
        data = cache.get(block)

        if data is None:
            data = f"block-{block}".encode()
            cache.put(block, data)
            print(f"MISS block {block}")
        else:
            print(f"HIT  block {block}")

    print(f"Hits: {cache.hits}")
    print(f"Misses: {cache.misses}")
    print(f"Hit rate: {cache.hit_rate:.2%}")

    print(
        """
Caching exploits temporal and spatial locality.

Temporal locality:
Recently used data may be used again.

Spatial locality:
Nearby data may be used soon.

Caches can significantly reduce effective latency, but cached data creates
consistency and durability questions. A successful application write does not
necessarily mean data has reached persistent media unless the relevant
durability semantics have been satisfied.
"""
    )


# ============================================================================
# 12. DATA INTEGRITY AND CHECKSUMS
# ============================================================================

def demonstrate_integrity() -> None:
    print_section("12. DATA INTEGRITY")

    original = b"Important storage record"
    original_hash = hashlib.sha256(original).hexdigest()

    transmitted = bytearray(original)
    transmitted[5] ^= 1
    corrupted_hash = hashlib.sha256(bytes(transmitted)).hexdigest()

    print(f"Original SHA-256:  {original_hash}")
    print(f"Changed SHA-256:   {corrupted_hash}")
    print(f"Integrity matches: {original_hash == corrupted_hash}")

    print(
        """
Checksums and cryptographic hashes can detect accidental or intentional data
changes.

Storage systems may also use:
- ECC for correcting bit errors.
- End-to-end checksums.
- Scrubbing to discover latent corruption.
- Redundancy such as RAID or replication.
- Versioning and immutable backups.

A checksum detects a mismatch; it does not automatically recover the original
data. Recovery requires another trustworthy copy or error-correction mechanism.
"""
    )


# ============================================================================
# 13. RELIABILITY AND REDUNDANCY
# ============================================================================

@dataclass
class StorageFailureModel:
    component: str
    failure_effect: str
    mitigation: str


def demonstrate_reliability() -> None:
    print_section("13. RELIABILITY, REDUNDANCY, AND DURABILITY")

    models = [
        StorageFailureModel(
            "Single HDD",
            "Mechanical or electronic failure can make stored data inaccessible.",
            "Independent backup and monitoring.",
        ),
        StorageFailureModel(
            "Single SSD",
            "Controller, NAND, firmware, power, or electronic failure can cause loss.",
            "Backup, monitoring, and appropriate redundancy.",
        ),
        StorageFailureModel(
            "RAID array",
            "Some device failures may be tolerated depending on RAID level.",
            "Choose RAID according to failure tolerance and workload.",
        ),
        StorageFailureModel(
            "Replicated storage",
            "One copy may fail while another remains available.",
            "Independent replicas and tested recovery.",
        ),
    ]

    for model in models:
        print(f"\n{model.component}")
        print(f"  Failure effect: {model.failure_effect}")
        print(f"  Mitigation: {model.mitigation}")

    print(
        """
RAID is not a substitute for backup.

Important distinctions:
- Availability: can the service continue operating?
- Durability: will data survive failures over time?
- Recoverability: can lost or corrupted data be restored?
- Redundancy: are multiple copies or parity representations available?

A robust design normally considers failure domains, not only the number of
copies. Copies on the same controller, host, rack, or power domain may fail
together.
"""
    )


# ============================================================================
# 14. RAID CONCEPTUAL SIMULATION
# ============================================================================

def raid0_stripe(data_blocks: List[str], disk_count: int) -> List[List[str]]:
    if disk_count <= 0:
        raise ValueError("Disk count must be positive")

    disks = [[] for _ in range(disk_count)]

    for index, block in enumerate(data_blocks):
        disks[index % disk_count].append(block)

    return disks


def demonstrate_raid0() -> None:
    print_section("14. RAID 0 STRIPING CONCEPT")

    blocks = ["A", "B", "C", "D", "E", "F", "G", "H"]
    layout = raid0_stripe(blocks, disk_count=4)

    for index, disk in enumerate(layout):
        print(f"Disk {index}: {disk}")

    print(
        """
RAID 0 stripes data across multiple devices.

Potential benefit:
- Parallelism and aggregate throughput.

Major limitation:
- There is no redundancy. Failure of one member can make the logical array
  unusable.

Other RAID concepts include:
- RAID 1: mirroring.
- RAID 5: distributed parity.
- RAID 6: dual distributed parity.
- RAID 10: mirrored sets combined with striping.

Actual performance and failure behavior depend on implementation and workload.
"""


# ============================================================================
# 15. STORAGE CAPACITY AND DECIMAL VS BINARY UNITS
# ============================================================================

def demonstrate_capacity_units() -> None:
    print_section("15. DECIMAL AND BINARY CAPACITY")

    decimal_tb = 1_000_000_000_000
    binary_tib = 1024**4

    print(f"1 TB decimal: {decimal_tb:,} bytes")
    print(f"1 TiB binary: {binary_tib:,} bytes")
    print(
        f"1,000,000,000,000 bytes = "
        f"{decimal_tb / binary_tib:.4f} TiB"
    )

    print(
        """
Storage manufacturers commonly use decimal units:
1 KB = 1,000 bytes
1 MB = 1,000,000 bytes
1 GB = 1,000,000,000 bytes
1 TB = 1,000,000,000,000 bytes

Binary units use powers of 1024:
1 KiB = 1,024 bytes
1 MiB = 1,048,576 bytes
1 GiB = 1,073,741,824 bytes
1 TiB = 1,099,511,627,776 bytes

This difference explains why an advertised decimal capacity can appear
smaller when reported using binary units.
"""
    )


# ============================================================================
# 16. THIN PROVISIONING AND VIRTUAL STORAGE
# ============================================================================

@dataclass
class VirtualDisk:
    logical_capacity: int
    physical_limit: int
    allocated: bytearray = field(default_factory=bytearray)

    def __post_init__(self) -> None:
        if self.logical_capacity <= 0:
            raise ValueError("Logical capacity must be positive")
        if self.physical_limit <= 0:
            raise ValueError("Physical limit must be positive")
        if self.physical_limit > self.logical_capacity:
            raise ValueError("Physical limit cannot exceed logical capacity")

        self.allocated = bytearray(self.physical_limit)

    def write(self, offset: int, data: bytes) -> None:
        if offset < 0 or offset + len(data) > self.logical_capacity:
            raise ValueError("Write exceeds logical capacity")

        # Educational model: only offsets within the simulated physical
        # allocation can actually be represented.
        if offset + len(data) > self.physical_limit:
            raise OSError(
                "Virtual disk has logical capacity remaining but no physical "
                "space in this simplified simulation"
            )

        self.allocated[offset:offset + len(data)] = data


def demonstrate_virtual_storage() -> None:
    print_section("16. VIRTUAL AND THIN-PROVISIONED STORAGE")

    disk = VirtualDisk(
        logical_capacity=1024 * 1024 * 1024,
        physical_limit=128 * 1024 * 1024,
    )

    print(f"Logical capacity:  {human_bytes(disk.logical_capacity)}")
    print(f"Physical capacity: {human_bytes(disk.physical_limit)}")

    print(
        """
Virtual storage can present a logical capacity different from immediately
allocated physical capacity.

Thin provisioning can improve utilization because physical capacity is
allocated as data is written. It also introduces operational risk if logical
consumption grows beyond available physical capacity.

Production systems therefore monitor both logical consumption and physical
capacity.
"""
    )


# ============================================================================
# 17. SECURITY CONSIDERATIONS
# ============================================================================

def demonstrate_storage_security() -> None:
    print_section("17. STORAGE SECURITY")

    secret = b"Confidential information"
    digest = hashlib.sha256(secret).hexdigest()

    print(f"Integrity digest: {digest}")

    print(
        """
Important storage-security controls include:

1. Access control
   Restrict which users and processes can read or modify data.

2. Encryption at rest
   Protect stored information if physical media is stolen or improperly
   accessed.

3. Encryption in transit
   Protect data while moving between hosts and storage services.

4. Key management
   Protect encryption keys separately from the encrypted data.

5. Secure deletion
   Understand that simply deleting a filesystem name may not physically erase
   every historical representation, especially with SSDs, snapshots,
   replication, and backups.

6. Path validation
   Applications handling user-controlled filenames must prevent path
   traversal.

7. Backup protection
   Backups contain the same sensitive information as primary storage and must
   receive appropriate access control and encryption.

8. Auditability
   Important access and administrative operations should be logged.

A cryptographic hash is not encryption. A hash can help detect changes, while
encryption is designed to protect confidentiality.
"""
    )


# ============================================================================
# 18. FILESYSTEM SEMANTICS
# ============================================================================

def demonstrate_filesystem_semantics() -> None:
    print_section("18. FILESYSTEM SEMANTICS")

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)

        file_path = root / "atomic-example.txt"
        temporary_path = root / "atomic-example.tmp"

        temporary_path.write_text("complete new content", encoding="utf-8")

        # Rename-based replacement is a common pattern for reducing the
        # window in which readers can observe partially written content.
        temporary_path.replace(file_path)

        print(file_path.read_text(encoding="utf-8"))

    print(
        """
Important filesystem semantics include:
- Naming and path resolution.
- Permissions.
- File ownership.
- Directory hierarchy.
- Timestamps.
- Links.
- Atomic operations.
- Buffering.
- Synchronization and durability.
- Crash recovery.

"Write returned successfully" and "data is guaranteed durable after sudden
power loss" are not necessarily identical statements. Applications with
strong durability requirements must use the correct operating-system and
filesystem mechanisms.
"""
    )


# ============================================================================
# 19. STORAGE DESIGN COMPARISON
# ============================================================================

def compare_file_and_block_storage() -> None:
    print_section("19. FILE STORAGE VS BLOCK STORAGE")

    comparison = [
        ("Primary abstraction", "Files/directories", "Addressable blocks"),
        ("Typical consumer", "Applications/users", "Filesystems/databases/VMs"),
        ("Naming", "Built into abstraction", "Usually provided by upper layer"),
        ("Flexibility", "High application convenience", "High low-level control"),
        ("Metadata", "Filesystem-managed", "Consumer-managed"),
        ("Typical use", "Documents, shared folders", "Databases, VM disks"),
    ]

    print(f"{'Characteristic':25} | {'File':28} | {'Block':28}")
    print("-" * 87)

    for characteristic, file_value, block_value in comparison:
        print(
            f"{characteristic:25} | "
            f"{file_value:28} | "
            f"{block_value:28}"
        )


# ============================================================================
# 20. SIMPLE STORAGE BENCHMARK MODEL
# ============================================================================

@dataclass
class Workload:
    name: str
    operation_size_bytes: int
    operations: int
    sequential: bool


def estimate_workload(
    workload: Workload,
    throughput_mb_s: float,
    iops: int,
) -> float:
    """
    Estimate workload time using a deliberately simplified model.

    For sequential workloads, throughput is emphasized.
    For random workloads, IOPS is emphasized.
    Real storage systems require substantially more detailed modeling.
    """
    if workload.operations <= 0:
        raise ValueError("Operations must be positive")

    if workload.sequential:
        total_bytes = workload.operation_size_bytes * workload.operations
        return total_bytes / (throughput_mb_s * 1024**2)

    return workload.operations / iops


def demonstrate_workload_model() -> None:
    print_section("20. WORKLOAD ESTIMATION")

    workloads = [
        Workload(
            "Large sequential backup",
            operation_size_bytes=1024 * 1024,
            operations=1000,
            sequential=True,
        ),
        Workload(
            "Small random database operations",
            operation_size_bytes=4096,
            operations=100_000,
            sequential=False,
        ),
    ]

    profile = TECHNOLOGY_PROFILES[StorageTechnology.SSD]

    for workload in workloads:
        seconds = estimate_workload(
            workload,
            throughput_mb_s=profile.sequential_read_mb_s,
            iops=profile.relative_iops,
        )
        print(f"{workload.name}: approximately {seconds:.3f} seconds")

    print(
        """
This model illustrates why a storage device should not be selected from a
single headline speed number. Workload shape, request size, concurrency,
latency, durability requirements, capacity, endurance, and cost all matter.
"""
    )


# ============================================================================
# 21. END-TO-END STORAGE ARCHITECTURE
# ============================================================================

def explain_end_to_end_stack() -> None:
    print_section("21. END-TO-END STORAGE STACK")

    stack = [
        "Application",
        "File API or database API",
        "Filesystem or database storage engine",
        "Operating-system I/O layer",
        "Block device interface",
        "Storage controller",
        "SSD/HDD firmware",
        "Physical storage medium",
    ]

    for number, layer in enumerate(stack, start=1):
        print(f"{number:2}. {layer}")

    print(
        """
A request can cross many layers.

For example:
    application write
        -> filesystem
        -> page/block allocation
        -> operating-system I/O
        -> device queue
        -> controller
        -> SSD FTL
        -> NAND programming

Performance or reliability behavior can therefore originate at different
layers. Troubleshooting requires identifying the layer responsible rather than
assuming that every storage problem is caused by the physical disk.
"""
    )


# ============================================================================
# 22. EDGE CASES AND FAILURE TESTS
# ============================================================================

def demonstrate_edge_cases() -> None:
    print_section("22. EDGE CASES AND FAILURE HANDLING")

    cases = [
        ("Zero block size", lambda: BlockDevice(0, 10)),
        ("Negative block count", lambda: BlockDevice(512, -1)),
        ("Invalid block write size", lambda: BlockDevice(512, 2).write_block(0, b"x")),
    ]

    for name, operation in cases:
        try:
            operation()
        except (ValueError, IndexError, OSError) as error:
            print(f"{name}: correctly rejected -> {error}")

    print(
        """
Storage software must handle:
- Out-of-range addresses.
- Full devices.
- Missing files.
- Permission failures.
- Corrupt metadata.
- Interrupted writes.
- Device disappearance.
- Invalid block sizes.
- Capacity exhaustion.
- Hardware errors.
- Concurrent access.
- Unexpected shutdown.
- Partial writes.

Failure handling should be explicit. Silent corruption is substantially more
dangerous than a visible error because it can remain undetected.
"""
    )


# ============================================================================
# 23. BEST PRACTICES
# ============================================================================

def demonstrate_best_practices() -> None:
    print_section("23. STORAGE BEST PRACTICES")

    practices = [
        "Define workload requirements before choosing media.",
        "Separate capacity, performance, endurance, availability, and durability.",
        "Use backups independently from primary storage.",
        "Test backup restoration instead of assuming backups work.",
        "Monitor capacity before the device becomes full.",
        "Monitor health indicators where supported.",
        "Use checksums or integrity mechanisms for important data.",
        "Protect storage credentials and encryption keys.",
        "Use least-privilege access.",
        "Understand filesystem and application durability semantics.",
        "Account for failure domains in redundant designs.",
        "Measure real workloads instead of relying only on vendor peak numbers.",
        "Consider write amplification and endurance for write-heavy flash workloads.",
        "Plan migration and replacement before storage reaches end of life.",
    ]

    for number, practice in enumerate(practices, start=1):
        print(f"{number:2}. {practice}")


# ============================================================================
# 24. INTEGRATED STORAGE SERVICE EXAMPLE
# ============================================================================

class StorageService:
    """
    A compact application-level storage service.

    It combines:
    - validation,
    - file persistence,
    - checksums,
    - metadata,
    - controlled access,
    - and integrity verification.

    It intentionally avoids pretending to be a production filesystem.
    """

    def __init__(self, root: Path):
        self.storage = SimpleFileStorage(root)
        self.index: Dict[str, str] = {}

    def store(self, object_name: str, content: bytes) -> FileMetadata:
        if not object_name.strip():
            raise ValueError("Object name cannot be empty")

        if len(content) > 10 * 1024 * 1024:
            raise ValueError("Object exceeds service size limit")

        metadata = self.storage.write(object_name, content)
        self.index[object_name] = metadata.checksum
        return metadata

    def retrieve(self, object_name: str) -> bytes:
        content = self.storage.read(object_name)

        expected = self.index.get(object_name)
        actual = hashlib.sha256(content).hexdigest()

        if expected is not None and expected != actual:
            raise IOError("Integrity verification failed")

        return content

    def delete(self, object_name: str) -> None:
        self.storage.delete(object_name)
        self.index.pop(object_name, None)


def demonstrate_integrated_service() -> None:
    print_section("24. INTEGRATED STORAGE SERVICE")

    with tempfile.TemporaryDirectory() as directory:
        service = StorageService(Path(directory))

        content = (
            b"An application can build higher-level semantics on top of "
            b"file or block storage."
        )

        metadata = service.store("objects/record.bin", content)

        print(f"Stored {metadata.path}")
        print(f"Verified read: {service.retrieve(metadata.path)!r}")

        service.delete(metadata.path)

        try:
            service.retrieve(metadata.path)
        except FileNotFoundError:
            print("Deletion and missing-object handling succeeded.")


# ============================================================================
# 25. STUDY QUESTIONS PRINTED BY THE PROGRAM
# ============================================================================

def print_study_questions() -> None:
    print_section("25. STUDY QUESTIONS")

    questions = [
        "Why is random small I/O generally more difficult for HDDs than SSDs?",
        "Why does an SSD require an FTL?",
        "What is the difference between NAND page programming and block erasure?",
        "Why can a filesystem be placed on block storage?",
        "Why is RAID not equivalent to backup?",
        "How do IOPS and throughput describe different workloads?",
        "What does TRIM communicate to an SSD?",
        "Why does flash require wear leveling?",
        "Why can deletion fail to guarantee physical erasure?",
        "Why should storage encryption keys be protected separately?",
        "What is the difference between durability and availability?",
        "How can caching reduce latency?",
        "Why can thin provisioning create capacity risks?",
        "Why should storage benchmarking use realistic workload patterns?",
    ]

    for number, question in enumerate(questions, start=1):
        print(f"{number:2}. {question}")


# ============================================================================
# MAIN PROGRAM
# ============================================================================

def main() -> None:
    demonstrate_storage_units()
    compare_storage_media()
    demonstrate_hdd()
    explain_flash_cells()
    show_storage_hierarchy()
    demonstrate_file_storage()
    demonstrate_block_storage()
    demonstrate_filesystem()
    benchmark_memory_io()
    demonstrate_performance_metrics()
    demonstrate_cache()
    demonstrate_integrity()
    demonstrate_reliability()
    demonstrate_raid0()
    demonstrate_capacity_units()
    demonstrate_virtual_storage()
    demonstrate_storage_security()
    demonstrate_filesystem_semantics()
    compare_file_and_block_storage()
    demonstrate_workload_model()
    explain_end_to_end_stack()
    demonstrate_edge_cases()
    demonstrate_best_practices()
    demonstrate_integrated_service()
    print_study_questions()

    print_section("STORAGE SYSTEMS STUDY PROGRAM COMPLETE")
    print(
        "The demonstrations covered physical storage media, logical storage "
        "abstractions, performance, reliability, security, and implementation."
    )


if __name__ == "__main__":
    main()
