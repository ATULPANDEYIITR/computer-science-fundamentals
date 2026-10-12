#!/usr/bin/env python3
"""
File System Internals: inodes, file allocation, journaling, and mounting.

This executable simulation models a small Unix-like file system. It does not
attempt to manipulate the host operating system's real disk structures. Instead,
it makes the important mechanisms explicit:

- inode metadata and inode-to-block mappings
- direct and indirect block allocation
- directory entries
- free-block allocation
- file creation, reads, writes, truncation, and deletion
- mount-time superblock validation
- a write-ahead journal for metadata transactions
- crash simulation and journal recovery
- consistency checking
- allocation fragmentation and locality observations

The implementation intentionally keeps the simulated disk small enough that
allocation behavior can be inspected directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import copy
import math
import random
from typing import Dict, Iterable, List, Optional, Tuple


class FileType(str, Enum):
    FILE = "file"
    DIRECTORY = "directory"


class AllocationError(RuntimeError):
    pass


class FileSystemError(RuntimeError):
    pass


class MountError(FileSystemError):
    pass


@dataclass
class Superblock:
    magic: str
    block_size: int
    total_blocks: int
    inode_count: int
    root_inode: int
    journal_start: int
    journal_blocks: int
    clean: bool = True
    generation: int = 1


@dataclass
class Inode:
    number: int
    file_type: FileType
    mode: int
    uid: int
    gid: int
    size: int = 0
    link_count: int = 1
    direct_blocks: List[int] = field(default_factory=list)
    indirect_block: Optional[int] = None
    indirect_entries: List[int] = field(default_factory=list)
    parent: Optional[int] = None
    timestamps: Dict[str, int] = field(
        default_factory=lambda: {"atime": 0, "mtime": 0, "ctime": 0}
    )

    @property
    def data_blocks(self) -> List[int]:
        return self.direct_blocks + self.indirect_entries


@dataclass
class DirEntry:
    name: str
    inode: int


@dataclass
class JournalRecord:
    transaction_id: int
    description: str
    inode_updates: Dict[int, Inode]
    directory_updates: Dict[int, List[DirEntry]]
    block_updates: Dict[int, Optional[bytes]]
    superblock_update: Optional[Superblock]
    committed: bool = False


class Disk:
    """A block-addressable simulated disk."""

    def __init__(self, block_size: int, total_blocks: int):
        if block_size <= 0 or total_blocks <= 0:
            raise ValueError("block_size and total_blocks must be positive")
        self.block_size = block_size
        self.total_blocks = total_blocks
        self.blocks: Dict[int, bytes] = {
            number: bytes(block_size) for number in range(total_blocks)
        }

    def read(self, block_number: int) -> bytes:
        self._validate_block(block_number)
        return self.blocks[block_number]

    def write(self, block_number: int, data: bytes) -> None:
        self._validate_block(block_number)
        if len(data) != self.block_size:
            raise ValueError("A disk write must contain exactly one block")
        self.blocks[block_number] = data

    def _validate_block(self, block_number: int) -> None:
        if not 0 <= block_number < self.total_blocks:
            raise ValueError(f"Invalid disk block: {block_number}")


class Journal:
    """
    A compact write-ahead journal.

    A real filesystem journal normally records enough information to replay or
    undo metadata operations according to its journaling mode. This simulator
    uses complete before-commit snapshots of affected logical structures so the
    recovery behavior remains visible without implementing a real on-disk
    serialization format.
    """

    def __init__(self, capacity: int = 32):
        self.capacity = capacity
        self.records: List[JournalRecord] = []
        self.next_transaction_id = 1

    def begin(
        self,
        description: str,
        inode_updates: Dict[int, Inode],
        directory_updates: Dict[int, List[DirEntry]],
        block_updates: Dict[int, Optional[bytes]],
        superblock_update: Optional[Superblock],
    ) -> JournalRecord:
        if len(self.records) >= self.capacity:
            raise FileSystemError("Journal is full")
        record = JournalRecord(
            transaction_id=self.next_transaction_id,
            description=description,
            inode_updates=copy.deepcopy(inode_updates),
            directory_updates=copy.deepcopy(directory_updates),
            block_updates=copy.deepcopy(block_updates),
            superblock_update=copy.deepcopy(superblock_update),
        )
        self.next_transaction_id += 1
        self.records.append(record)
        return record

    def commit(self, transaction_id: int) -> None:
        record = self._find(transaction_id)
        record.committed = True

    def discard_committed(self) -> None:
        self.records = [r for r in self.records if not r.committed]

    def pending(self) -> List[JournalRecord]:
        return [r for r in self.records if not r.committed]

    def _find(self, transaction_id: int) -> JournalRecord:
        for record in self.records:
            if record.transaction_id == transaction_id:
                return record
        raise FileSystemError(f"Unknown journal transaction {transaction_id}")


class FileSystem:
    MAGIC = "FSI-SIM-1"
    DIRECT_LIMIT = 4

    def __init__(
        self,
        block_size: int = 64,
        total_blocks: int = 128,
        inode_count: int = 32,
        journal_blocks: int = 12,
    ):
        if total_blocks < 32:
            raise ValueError("The simulated disk needs at least 32 blocks")
        if inode_count < 4:
            raise ValueError("At least four inodes are required")

        self.disk = Disk(block_size, total_blocks)
        self.inodes: Dict[int, Inode] = {}
        self.directories: Dict[int, List[DirEntry]] = {}
        self.allocated_blocks: set[int] = set()
        self.allocated_inodes: set[int] = set()
        self.journal = Journal(capacity=journal_blocks)
        self.clock = 0
        self.mounted = False
        self.mount_generation = 0

        # Reserve low-numbered blocks for filesystem metadata. A real filesystem
        # uses concrete superblock, inode-table, bitmap, journal, and data areas.
        metadata_blocks = 8 + journal_blocks
        if metadata_blocks >= total_blocks:
            raise ValueError("Too many journal/metadata blocks for disk size")

        self.superblock = Superblock(
            magic=self.MAGIC,
            block_size=block_size,
            total_blocks=total_blocks,
            inode_count=inode_count,
            root_inode=1,
            journal_start=8,
            journal_blocks=journal_blocks,
        )

        self.metadata_blocks = set(range(metadata_blocks))
        self.allocated_blocks.update(self.metadata_blocks)

        root = self._allocate_inode(
            file_type=FileType.DIRECTORY,
            mode=0o755,
            uid=0,
            gid=0,
            parent=1,
        )
        if root.number != self.superblock.root_inode:
            raise AssertionError("Root inode allocation invariant failed")

        self.directories[root.number] = [
            DirEntry(".", root.number),
            DirEntry("..", root.number),
        ]

        self.mount()

    def _tick(self) -> int:
        self.clock += 1
        return self.clock

    def _allocate_inode(
        self,
        file_type: FileType,
        mode: int,
        uid: int,
        gid: int,
        parent: Optional[int],
    ) -> Inode:
        for number in range(1, self.superblock.inode_count + 1):
            if number not in self.allocated_inodes:
                inode = Inode(
                    number=number,
                    file_type=file_type,
                    mode=mode,
                    uid=uid,
                    gid=gid,
                    parent=parent,
                )
                now = self._tick()
                inode.timestamps = {"atime": now, "mtime": now, "ctime": now}
                self.inodes[number] = inode
                self.allocated_inodes.add(number)
                if file_type == FileType.DIRECTORY:
                    self.directories[number] = []
                return inode
        raise AllocationError("No free inodes remain")

    def _free_inode(self, inode_number: int) -> None:
        inode = self.inodes.pop(inode_number)
        self.directories.pop(inode_number, None)
        self.allocated_inodes.remove(inode_number)

    def _allocate_block(self) -> int:
        for block in range(0, self.disk.total_blocks):
            if block not in self.allocated_blocks:
                self.allocated_blocks.add(block)
                return block
        raise AllocationError("No free data blocks remain")

    def _free_block(self, block: int) -> None:
        if block in self.metadata_blocks:
            raise FileSystemError(f"Attempted to free metadata block {block}")
        self.allocated_blocks.discard(block)

    def _path_components(self, path: str) -> List[str]:
        if not path.startswith("/"):
            raise FileSystemError("Only absolute paths are supported")
        return [part for part in path.split("/") if part not in ("", ".")]

    def resolve(self, path: str) -> int:
        components = self._path_components(path)
        current = self.superblock.root_inode

        if not components:
            return current

        for component in components:
            if component == "..":
                current = self.inodes[current].parent or current
                continue

            if self.inodes[current].file_type != FileType.DIRECTORY:
                raise FileSystemError(f"{current} is not a directory")

            match = next(
                (entry for entry in self.directories[current] if entry.name == component),
                None,
            )
            if match is None:
                raise FileSystemError(f"Path does not exist: {path}")
            current = match.inode

        return current

    def _parent_and_name(self, path: str) -> Tuple[int, str]:
        components = self._path_components(path)
        if not components:
            raise FileSystemError("The root directory has no parent entry")

        name = components[-1]
        if len(components) == 1:
            return self.superblock.root_inode, name

        parent_path = "/" + "/".join(components[:-1])
        parent_inode = self.resolve(parent_path)
        return parent_inode, name

    def _record_transaction(
        self,
        description: str,
        affected_inodes: Iterable[int],
        affected_directories: Iterable[int],
        affected_blocks: Iterable[int],
    ) -> JournalRecord:
        inode_updates = {
            n: copy.deepcopy(self.inodes[n])
            for n in affected_inodes
            if n in self.inodes
        }
        directory_updates = {
            n: copy.deepcopy(self.directories[n])
            for n in affected_directories
            if n in self.directories
        }
        block_updates = {
            n: self.disk.read(n)
            for n in affected_blocks
            if 0 <= n < self.disk.total_blocks
        }
        return self.journal.begin(
            description,
            inode_updates,
            directory_updates,
            block_updates,
            self.superblock,
        )

    def _commit(self, record: JournalRecord) -> None:
        self.journal.commit(record.transaction_id)
        self.superblock.clean = True
        self.superblock.generation += 1
        self.journal.discard_committed()

    def create_file(
        self,
        path: str,
        mode: int = 0o644,
        uid: int = 1000,
        gid: int = 1000,
    ) -> int:
        self._require_mounted()
        parent_number, name = self._parent_and_name(path)
        parent = self.inodes[parent_number]

        if parent.file_type != FileType.DIRECTORY:
            raise FileSystemError("Parent is not a directory")
        self._validate_name(name)

        if any(entry.name == name for entry in self.directories[parent_number]):
            raise FileSystemError(f"Entry already exists: {path}")

        inode = self._allocate_inode(FileType.FILE, mode, uid, gid, parent_number)
        record = self._record_transaction(
            f"create file {path}",
            [parent_number, inode.number],
            [parent_number],
            [],
        )
        self.directories[parent_number].append(DirEntry(name, inode.number))
        self._touch(parent_number, "mtime")
        self._touch(parent_number, "ctime")
        self.superblock.clean = False
        self._commit(record)
        return inode.number

    def mkdir(
        self,
        path: str,
        mode: int = 0o755,
        uid: int = 1000,
        gid: int = 1000,
    ) -> int:
        self._require_mounted()
        parent_number, name = self._parent_and_name(path)
        parent = self.inodes[parent_number]

        if parent.file_type != FileType.DIRECTORY:
            raise FileSystemError("Parent is not a directory")
        self._validate_name(name)

        if any(entry.name == name for entry in self.directories[parent_number]):
            raise FileSystemError(f"Entry already exists: {path}")

        inode = self._allocate_inode(
            FileType.DIRECTORY, mode, uid, gid, parent_number
        )
        self.directories[inode.number] = [
            DirEntry(".", inode.number),
            DirEntry("..", parent_number),
        ]

        record = self._record_transaction(
            f"create directory {path}",
            [parent_number, inode.number],
            [parent_number, inode.number],
            [],
        )
        self.directories[parent_number].append(DirEntry(name, inode.number))
        parent.link_count += 1
        self._touch(parent_number, "mtime")
        self._touch(parent_number, "ctime")
        self.superblock.clean = False
        self._commit(record)
        return inode.number

    def write_file(self, path: str, data: bytes, offset: int = 0) -> int:
        self._require_mounted()
        if offset < 0:
            raise ValueError("offset cannot be negative")

        inode_number = self.resolve(path)
        inode = self.inodes[inode_number]

        if inode.file_type != FileType.FILE:
            raise FileSystemError("Only regular files can be written")

        if not data:
            return 0

        old_blocks = set(inode.data_blocks)
        required_end = offset + len(data)
        required_blocks = math.ceil(required_end / self.disk.block_size)

        if required_blocks > len(inode.data_blocks):
            self._extend_file_blocks(inode, required_blocks)

        affected_blocks = inode.data_blocks[:required_blocks]
        record = self._record_transaction(
            f"write {len(data)} bytes to {path}",
            [inode.number],
            [],
            affected_blocks,
        )

        for index in range(required_blocks):
            existing = (
                bytearray(self.disk.read(inode.data_blocks[index]))
                if index < len(old_blocks) or inode.data_blocks[index] in old_blocks
                else bytearray(self.disk.block_size)
            )

            block_start = index * self.disk.block_size
            write_start = max(offset, block_start)
            write_end = min(required_end, block_start + self.disk.block_size)

            if write_start < write_end:
                source_start = write_start - offset
                source_end = write_end - offset
                local_start = write_start - block_start
                local_end = write_end - block_start
                existing[local_start:local_end] = data[source_start:source_end]

            self.disk.write(inode.data_blocks[index], bytes(existing))

        inode.size = max(inode.size, required_end)
        self._touch(inode.number, "mtime")
        self._touch(inode.number, "ctime")
        self.superblock.clean = False
        self._commit(record)
        return len(data)

    def _extend_file_blocks(self, inode: Inode, required_blocks: int) -> None:
        while len(inode.data_blocks) < required_blocks:
            block = self._allocate_block()

            if len(inode.direct_blocks) < self.DIRECT_LIMIT:
                inode.direct_blocks.append(block)
            else:
                if inode.indirect_block is None:
                    inode.indirect_block = self._allocate_block()
                inode.indirect_entries.append(block)

    def read_file(self, path: str, offset: int = 0, length: Optional[int] = None) -> bytes:
        self._require_mounted()
        inode = self.inodes[self.resolve(path)]

        if inode.file_type != FileType.FILE:
            raise FileSystemError("Only regular files can be read")
        if offset < 0:
            raise ValueError("offset cannot be negative")
        if offset >= inode.size:
            return b""

        if length is None:
            length = inode.size - offset
        if length < 0:
            raise ValueError("length cannot be negative")

        length = min(length, inode.size - offset)
        result = bytearray()

        first_block = offset // self.disk.block_size
        last_block = (offset + length - 1) // self.disk.block_size

        for logical_index in range(first_block, last_block + 1):
            physical_block = inode.data_blocks[logical_index]
            result.extend(self.disk.read(physical_block))

        start_in_result = offset % self.disk.block_size
        self._touch(inode.number, "atime")
        return bytes(result[start_in_result : start_in_result + length])

    def truncate(self, path: str, new_size: int) -> None:
        self._require_mounted()
        if new_size < 0:
            raise ValueError("new_size cannot be negative")

        inode = self.inodes[self.resolve(path)]
        if inode.file_type != FileType.FILE:
            raise FileSystemError("Only regular files can be truncated")

        required_blocks = math.ceil(new_size / self.disk.block_size)
        record = self._record_transaction(
            f"truncate {path} to {new_size} bytes",
            [inode.number],
            [],
            inode.data_blocks,
        )

        while len(inode.data_blocks) > required_blocks:
            if inode.indirect_entries:
                block = inode.indirect_entries.pop()
                self._free_block(block)
            else:
                block = inode.direct_blocks.pop()
                self._free_block(block)

        if not inode.indirect_entries and inode.indirect_block is not None:
            self._free_block(inode.indirect_block)
            inode.indirect_block = None

        inode.size = new_size
        self._touch(inode.number, "mtime")
        self._touch(inode.number, "ctime")
        self.superblock.clean = False
        self._commit(record)

    def delete(self, path: str) -> None:
        self._require_mounted()
        parent_number, name = self._parent_and_name(path)
        entry = next(
            (entry for entry in self.directories[parent_number] if entry.name == name),
            None,
        )
        if entry is None:
            raise FileSystemError(f"Path does not exist: {path}")

        inode = self.inodes[entry.inode]
        if inode.file_type == FileType.DIRECTORY:
            visible_entries = [
                item for item in self.directories[inode.number]
                if item.name not in (".", "..")
            ]
            if visible_entries:
                raise FileSystemError("Directory is not empty")

        affected_blocks = inode.data_blocks[:]
        if inode.indirect_block is not None:
            affected_blocks.append(inode.indirect_block)

        record = self._record_transaction(
            f"delete {path}",
            [parent_number, inode.number],
            [parent_number, inode.number],
            affected_blocks,
        )

        self.directories[parent_number] = [
            item for item in self.directories[parent_number] if item.name != name
        ]
        self._touch(parent_number, "mtime")
        self._touch(parent_number, "ctime")

        for block in inode.data_blocks:
            self._free_block(block)
        if inode.indirect_block is not None:
            self._free_block(inode.indirect_block)

        if inode.file_type == FileType.DIRECTORY:
            self.inodes[parent_number].link_count -= 1

        self._free_inode(inode.number)
        self.superblock.clean = False
        self._commit(record)

    def list_directory(self, path: str = "/") -> List[Tuple[str, int, str]]:
        inode_number = self.resolve(path)
        inode = self.inodes[inode_number]
        if inode.file_type != FileType.DIRECTORY:
            raise FileSystemError("Not a directory")

        return [
            (entry.name, entry.inode, self.inodes[entry.inode].file_type.value)
            for entry in self.directories[inode_number]
        ]

    def stat(self, path: str) -> Dict[str, object]:
        inode = self.inodes[self.resolve(path)]
        return {
            "inode": inode.number,
            "type": inode.file_type.value,
            "mode": oct(inode.mode),
            "uid": inode.uid,
            "gid": inode.gid,
            "size": inode.size,
            "links": inode.link_count,
            "direct_blocks": list(inode.direct_blocks),
            "indirect_block": inode.indirect_block,
            "indirect_entries": list(inode.indirect_entries),
            "parent": inode.parent,
            "timestamps": dict(inode.timestamps),
        }

    def mount(self) -> None:
        if self.mounted:
            return

        if self.superblock.magic != self.MAGIC:
            raise MountError("Filesystem magic does not match")
        if self.superblock.block_size != self.disk.block_size:
            raise MountError("Block-size mismatch")
        if self.superblock.total_blocks != self.disk.total_blocks:
            raise MountError("Disk-size mismatch")

        self.mounted = True
        self.mount_generation += 1

        if not self.superblock.clean or self.journal.pending():
            self.recover_journal()

        self.check_consistency(raise_on_error=True)

    def unmount(self) -> None:
        if not self.mounted:
            return
        self.check_consistency(raise_on_error=True)
        self.superblock.clean = True
        self.mounted = False

    def recover_journal(self) -> None:
        """
        Replay committed metadata transactions that remain in the journal.

        In this simulator, committed records represent operations whose intent
        was durably recorded before the filesystem state was interrupted.
        """
        for record in list(self.journal.records):
            if not record.committed:
                continue

            for inode_number, inode in record.inode_updates.items():
                self.inodes[inode_number] = copy.deepcopy(inode)

            for directory_number, entries in record.directory_updates.items():
                self.directories[directory_number] = copy.deepcopy(entries)

            for block_number, data in record.block_updates.items():
                if data is not None:
                    self.disk.write(block_number, data)

            if record.superblock_update is not None:
                self.superblock = copy.deepcopy(record.superblock_update)

        self.journal.records.clear()
        self.superblock.clean = True
        self.superblock.generation += 1

    def simulate_crash(self) -> None:
        """
        Simulate abrupt power loss.

        Volatile mounted state is lost. Journal records survive because the
        journal is treated as durable storage. Uncommitted in-memory changes
        are intentionally not reconstructed.
        """
        self.mounted = False
        self.superblock.clean = False

        # Rebuilding allocator state from the persistent logical structures
        # models a remount after an interrupted operation.
        self._rebuild_allocation_state()

    def _rebuild_allocation_state(self) -> None:
        self.allocated_inodes = set(self.inodes.keys())
        self.allocated_blocks = set(self.metadata_blocks)

        for inode in self.inodes.values():
            self.allocated_blocks.update(inode.data_blocks)
            if inode.indirect_block is not None:
                self.allocated_blocks.add(inode.indirect_block)

    def check_consistency(self, raise_on_error: bool = False) -> List[str]:
        errors: List[str] = []

        if self.superblock.root_inode not in self.inodes:
            errors.append("Root inode is missing")

        for inode_number, inode in self.inodes.items():
            if inode.file_type == FileType.DIRECTORY:
                entries = self.directories.get(inode_number, [])
                names = [entry.name for entry in entries]

                if "." not in names or ".." not in names:
                    errors.append(f"Directory inode {inode_number} lacks . or ..")

                if len(names) != len(set(names)):
                    errors.append(f"Directory inode {inode_number} contains duplicates")

                for entry in entries:
                    if entry.inode not in self.inodes:
                        errors.append(
                            f"Directory {inode_number} references missing inode "
                            f"{entry.inode}"
                        )

            expected_blocks = math.ceil(inode.size / self.disk.block_size)
            if inode.file_type == FileType.FILE and len(inode.data_blocks) < expected_blocks:
                errors.append(
                    f"Inode {inode_number} has insufficient blocks for its size"
                )

            if inode.indirect_block is not None and not inode.indirect_entries:
                errors.append(
                    f"Inode {inode_number} has an empty indirect allocation block"
                )

            if len(inode.direct_blocks) > self.DIRECT_LIMIT:
                errors.append(f"Inode {inode_number} exceeds direct-block capacity")

            for block in inode.data_blocks:
                if block in self.metadata_blocks:
                    errors.append(
                        f"Inode {inode_number} points into metadata block {block}"
                    )

        seen_blocks: Dict[int, int] = {}
        for inode in self.inodes.values():
            for block in inode.data_blocks:
                seen_blocks[block] = seen_blocks.get(block, 0) + 1

        duplicate_blocks = [block for block, count in seen_blocks.items() if count > 1]
        if duplicate_blocks:
            errors.append(f"Data blocks shared unexpectedly: {duplicate_blocks}")

        expected_allocated = set(self.metadata_blocks)
        for inode in self.inodes.values():
            expected_allocated.update(inode.data_blocks)
            if inode.indirect_block is not None:
                expected_allocated.add(inode.indirect_block)

        if expected_allocated != self.allocated_blocks:
            errors.append("Block allocation bitmap does not match inode references")

        if errors and raise_on_error:
            raise FileSystemError("Filesystem consistency failure: " + "; ".join(errors))

        return errors

    def fragmentation_report(self) -> Dict[str, object]:
        data_blocks = sorted(
            block for block in self.allocated_blocks if block not in self.metadata_blocks
        )
        if not data_blocks:
            return {
                "allocated_data_blocks": [],
                "largest_contiguous_run": 0,
                "fragmentation_ratio": 0.0,
            }

        runs = []
        start = previous = data_blocks[0]

        for block in data_blocks[1:]:
            if block == previous + 1:
                previous = block
            else:
                runs.append((start, previous))
                start = previous = block

        runs.append((start, previous))
        lengths = [end - start + 1 for start, end in runs]
        largest = max(lengths)
        total = len(data_blocks)

        return {
            "allocated_data_blocks": data_blocks,
            "largest_contiguous_run": largest,
            "fragmentation_ratio": round(1 - largest / total, 3),
        }

    def _touch(self, inode_number: int, timestamp: str) -> None:
        self.inodes[inode_number].timestamps[timestamp] = self._tick()

    @staticmethod
    def _validate_name(name: str) -> None:
        if not name:
            raise FileSystemError("A directory entry requires a name")
        if name in (".", ".."):
            raise FileSystemError("Reserved directory name")
        if "/" in name:
            raise FileSystemError("A directory entry cannot contain '/'")
        if len(name.encode("utf-8")) > 255:
            raise FileSystemError("Name exceeds the simulated 255-byte limit")

    def _require_mounted(self) -> None:
        if not self.mounted:
            raise MountError("Filesystem is not mounted")


def demonstrate_inode_and_allocation() -> None:
    print("\n=== Inodes and block allocation ===")
    fs = FileSystem(block_size=32, total_blocks=80, inode_count=20, journal_blocks=8)

    fs.mkdir("/data")
    inode = fs.create_file("/data/report.txt")
    payload = (
        b"Quarterly storage report: "
        b"the file is intentionally longer than four blocks so the inode "
        b"must transition from direct references to an indirect reference."
    )
    fs.write_file("/data/report.txt", payload)

    print("Inode:", inode)
    print("Stat:", fs.stat("/data/report.txt"))
    print("Read:", fs.read_file("/data/report.txt").decode())
    print("Directory:", fs.list_directory("/data"))
    print("Allocation:", fs.fragmentation_report())


def demonstrate_mount_and_journal_recovery() -> None:
    print("\n=== Mounting and journaling ===")
    fs = FileSystem(block_size=32, total_blocks=80, inode_count=20, journal_blocks=8)
    fs.mkdir("/logs")
    fs.create_file("/logs/system.log")
    fs.write_file("/logs/system.log", b"boot completed\n")

    print("Before unmount:", fs.stat("/logs/system.log"))
    fs.unmount()
    fs.mount()
    print("After clean remount:", fs.read_file("/logs/system.log").decode().strip())

    fs.write_file("/logs/system.log", b"transaction boundary\n")
    fs.simulate_crash()
    fs.mount()

    print("After simulated crash:", fs.read_file("/logs/system.log").decode())
    print("Journal records:", len(fs.journal.records))
    print("Consistency errors:", fs.check_consistency())


def demonstrate_truncation_and_reuse() -> None:
    print("\n=== Truncation and block reuse ===")
    fs = FileSystem(block_size=16, total_blocks=64, inode_count=16, journal_blocks=6)
    fs.create_file("/alpha")
    fs.write_file("/alpha", b"A" * 90)

    before = fs.stat("/alpha")
    print("Before truncation:", before)

    fs.truncate("/alpha", 10)
    after = fs.stat("/alpha")
    print("After truncation:", after)

    fs.create_file("/beta")
    fs.write_file("/beta", b"B" * 48)
    print("Beta:", fs.stat("/beta"))
    print("Allocation:", fs.fragmentation_report())


def demonstrate_validation_failures() -> None:
    print("\n=== Validation and failure conditions ===")
    fs = FileSystem(block_size=32, total_blocks=48, inode_count=10, journal_blocks=6)

    fs.create_file("/config")
    fs.write_file("/config", b"mode=production")

    failures = []

    for operation in (
        lambda: fs.create_file("/config"),
        lambda: fs.write_file("/config", b"x", offset=-1),
        lambda: fs.read_file("/missing"),
        lambda: fs.mkdir("/config"),
        lambda: fs.delete("/missing"),
    ):
        try:
            operation()
        except (FileSystemError, ValueError) as exc:
            failures.append(str(exc))

    for failure in failures:
        print("Rejected:", failure)


def demonstrate_directory_links() -> None:
    print("\n=== Directory structure and link accounting ===")
    fs = FileSystem(block_size=32, total_blocks=64, inode_count=16, journal_blocks=6)

    fs.mkdir("/engineering")
    fs.mkdir("/engineering/kernel")
    fs.create_file("/engineering/kernel/fs.c")

    print("/:", fs.list_directory("/"))
    print("/engineering:", fs.list_directory("/engineering"))
    print("/engineering/kernel:", fs.list_directory("/engineering/kernel"))

    fs.delete("/engineering/kernel/fs.c")
    fs.delete("/engineering/kernel")
    print("After cleanup:", fs.list_directory("/engineering"))


def main() -> None:
    print("File System Internals Simulator")
    print("The simulation models logical filesystem structures, not a host disk.")

    demonstrate_inode_and_allocation()
    demonstrate_mount_and_journal_recovery()
    demonstrate_truncation_and_reuse()
    demonstrate_validation_failures()
    demonstrate_directory_links()

    print("\n=== Final design observations ===")
    print(
        "An inode identifies file metadata and block references; directories map "
        "names to inode numbers."
    )
    print(
        "Allocation translates logical file growth into physical block ownership. "
        "Direct references are fast for small files, while indirect references "
        "extend capacity."
    )
    print(
        "Journaling records transaction intent so recovery can restore filesystem "
        "metadata after an interrupted operation."
    )
    print(
        "Mounting validates filesystem geometry and consistency before exposing "
        "the filesystem to normal operations."
    )


if __name__ == "__main__":
    main()
