#!/usr/bin/env python3
"""
File Systems: files, directories, metadata, file operations, and permissions.

Self-contained demonstration using only the Python standard library.
Designed for Windows, Linux, and macOS. POSIX permission behavior is
demonstrated when supported by the host operating system.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


def heading(title: str) -> None:
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")


def safe_write_text(path: Path, content: str) -> None:
    """Write UTF-8 text and make the failure explicit."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def demonstrate_paths(root: Path) -> None:
    heading("Path objects and filesystem navigation")

    documents = root / "documents"
    reports = documents / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    report = reports / "quarterly.txt"
    safe_write_text(report, "Revenue: 125000\nOperating cost: 73000\n")

    print("Absolute path:", report.resolve())
    print("Name:", report.name)
    print("Suffix:", report.suffix)
    print("Parent:", report.parent)
    print("Exists:", report.exists())
    print("Is file:", report.is_file())
    print("Is directory:", report.is_dir())

    print("\nDirectory tree:")
    for item in root.rglob("*"):
        kind = "DIR " if item.is_dir() else "FILE"
        print(f"{kind:4} {item.relative_to(root)}")


def demonstrate_file_operations(root: Path) -> None:
    heading("File creation, reading, appending, copying, moving, and deletion")

    source = root / "operations" / "source.txt"
    backup = root / "operations" / "backup.txt"
    moved = root / "archive" / "source-moved.txt"

    safe_write_text(source, "Line one\n")
    with source.open("a", encoding="utf-8") as handle:
        handle.write("Line two\n")

    print("Read content:")
    print(source.read_text(encoding="utf-8"), end="")

    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, backup)
    print("Backup created:", backup.exists())

    moved.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(moved))
    print("Moved source exists:", moved.exists())
    print("Original source exists:", source.exists())

    backup.unlink()
    print("Backup removed:", not backup.exists())

    try:
        backup.unlink()
    except FileNotFoundError as exc:
        print("Expected deletion failure:", exc.__class__.__name__)


def metadata(path: Path) -> dict[str, object]:
    info = path.stat()
    return {
        "name": path.name,
        "size_bytes": info.st_size,
        "mode_octal": oct(stat.S_IMODE(info.st_mode)),
        "permissions": stat.filemode(info.st_mode),
        "modified": time.ctime(info.st_mtime),
        "accessed": time.ctime(info.st_atime),
        "created_or_changed": time.ctime(info.st_ctime),
        "inode": getattr(info, "st_ino", None),
        "device": getattr(info, "st_dev", None),
        "owner_uid": getattr(info, "st_uid", None),
        "group_gid": getattr(info, "st_gid", None),
    }


def demonstrate_metadata(root: Path) -> None:
    heading("Filesystem metadata")

    target = root / "metadata.txt"
    safe_write_text(target, "Metadata inspection example\n")

    for key, value in metadata(target).items():
        print(f"{key:20}: {value}")

    print("Filesystem space:")
    usage = shutil.disk_usage(root)
    print(f"total={usage.total:,} bytes")
    print(f"used ={usage.used:,} bytes")
    print(f"free ={usage.free:,} bytes")


def permission_text(mode: int) -> str:
    return stat.filemode(mode)


def demonstrate_permissions(root: Path) -> None:
    heading("File permissions and access checks")

    target = root / "permissions.txt"
    safe_write_text(target, "Controlled access\n")

    before = target.stat().st_mode
    print("Initial:", permission_text(before))

    # chmod uses POSIX permission bits where the platform honors them.
    # Windows may expose only a subset of these semantics.
    if os.name == "posix":
        target.chmod(0o640)
        after = target.stat().st_mode
        print("After chmod(640):", permission_text(after))
        print("Owner read:", bool(after & stat.S_IRUSR))
        print("Owner write:", bool(after & stat.S_IWUSR))
        print("Owner execute:", bool(after & stat.S_IXUSR))
        print("Group read:", bool(after & stat.S_IRGRP))
        print("Others read:", bool(after & stat.S_IROTH))
    else:
        print("POSIX permission bits are limited on this platform.")
        print("Readable:", os.access(target, os.R_OK))
        print("Writable:", os.access(target, os.W_OK))

    try:
        with target.open("r", encoding="utf-8") as handle:
            print("Read succeeded:", handle.readline().strip())
    except PermissionError as exc:
        print("Permission denied:", exc)


def hash_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def demonstrate_binary_and_integrity(root: Path) -> None:
    heading("Binary files, streaming I/O, and integrity")

    source = root / "binary.bin"
    with source.open("wb") as handle:
        handle.write(bytes(range(256)) * 100)

    print("Size:", source.stat().st_size)
    print("SHA-256:", hash_file(source))

    destination = root / "binary-copy.bin"
    shutil.copyfile(source, destination)

    print("Copy hash matches:", hash_file(source) == hash_file(destination))


@dataclass(frozen=True)
class FileRecord:
    path: str
    size: int
    suffix: str
    permissions: str
    modified_epoch: float


def inventory_directory(root: Path) -> list[FileRecord]:
    records: list[FileRecord] = []

    for path in root.rglob("*"):
        if path.is_file():
            info = path.stat()
            records.append(
                FileRecord(
                    path=str(path.relative_to(root)),
                    size=info.st_size,
                    suffix=path.suffix.lower(),
                    permissions=stat.filemode(info.st_mode),
                    modified_epoch=info.st_mtime,
                )
            )

    return sorted(records, key=lambda record: record.path)


def demonstrate_inventory(root: Path) -> None:
    heading("Filesystem inventory")

    records = inventory_directory(root)
    for record in records:
        print(
            f"{record.path:35} "
            f"{record.size:8} bytes "
            f"{record.suffix or '[none]':8} "
            f"{record.permissions}"
        )

    inventory_file = root / "inventory.json"
    payload = [record.__dict__ for record in records]
    inventory_file.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    print("Inventory exported to:", inventory_file)


def demonstrate_safe_recursive_operations(root: Path) -> None:
    heading("Recursive operations and safety checks")

    source = root / "project"
    source.mkdir()
    safe_write_text(source / "README.md", "# Project\n")
    safe_write_text(source / "config.ini", "mode=production\n")
    (source / "data").mkdir()
    safe_write_text(source / "data" / "records.csv", "id,value\n1,42\n")

    destination = root / "project-backup"
    shutil.copytree(source, destination)

    print("Backup tree:")
    for item in destination.rglob("*"):
        print(item.relative_to(root))

    # Never construct deletion targets from unchecked external input.
    # Resolve paths and verify that they remain below an approved root.
    approved_root = root.resolve()
    requested = (approved_root / "project-backup").resolve()

    if requested != approved_root and approved_root in requested.parents:
        shutil.rmtree(requested)
        print("Validated backup removal completed.")
    else:
        raise RuntimeError("Refusing unsafe recursive deletion.")


def demonstrate_links(root: Path) -> None:
    heading("Symbolic links and filesystem references")

    target = root / "link-target.txt"
    link = root / "link.txt"
    safe_write_text(target, "Target content\n")

    if hasattr(os, "symlink"):
        try:
            link.symlink_to(target.name)
            print("Link created:", link)
            print("is_symlink:", link.is_symlink())
            print("Resolved target:", link.resolve())
            print("Link content:", link.read_text(encoding="utf-8").strip())
        except (OSError, NotImplementedError) as exc:
            print("Symbolic link unavailable:", exc)
    else:
        print("Symbolic links are unsupported by this Python build.")


def demonstrate_error_handling(root: Path) -> None:
    heading("Failure conditions")

    missing = root / "does-not-exist.txt"

    try:
        missing.read_text(encoding="utf-8")
    except FileNotFoundError:
        print("Missing file handled explicitly.")

    directory = root / "existing-directory"
    directory.mkdir(exist_ok=True)

    try:
        directory.read_text(encoding="utf-8")
    except IsADirectoryError:
        print("Directory-versus-file error handled explicitly.")

    try:
        safe_write_text(root / "invalid" / "nested.txt", "Created safely\n")
        print("Missing parent directories were created.")
    except OSError as exc:
        print("Filesystem error:", exc)


def demonstrate_atomic_update(root: Path) -> None:
    heading("Atomic-style replacement")

    destination = root / "configuration.json"
    temporary = root / "configuration.json.tmp"

    configuration = {
        "environment": "production",
        "max_connections": 40,
        "audit_logging": True,
    }

    temporary.write_text(
        json.dumps(configuration, indent=2),
        encoding="utf-8",
    )

    # os.replace gives a single replacement operation rather than exposing
    # a partially written destination to another reader.
    os.replace(temporary, destination)
    print(destination.read_text(encoding="utf-8"))


def main() -> None:
    heading("File Systems: Practical Python Laboratory")

    with tempfile.TemporaryDirectory(prefix="filesystem_lab_") as temporary:
        root = Path(temporary)
        print("Working root:", root)

        demonstrate_paths(root)
        demonstrate_file_operations(root)
        demonstrate_metadata(root)
        demonstrate_permissions(root)
        demonstrate_binary_and_integrity(root)
        demonstrate_inventory(root)
        demonstrate_safe_recursive_operations(root)
        demonstrate_links(root)
        demonstrate_error_handling(root)
        demonstrate_atomic_update(root)

        heading("Final filesystem state")
        for item in sorted(root.rglob("*")):
            kind = "DIR " if item.is_dir() else "FILE"
            print(f"{kind:4} {item.relative_to(root)}")

    print("\nTemporary laboratory removed automatically.")


if __name__ == "__main__":
    main()
