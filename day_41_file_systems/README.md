# File Systems: Files, Directories, Metadata, Operations, and Permissions

## Scope

A file system provides the persistent organization used by an operating system to store files, directories, and associated metadata. This implementation set treats five closely connected areas as distinct concerns:

- **Files** hold byte-oriented application data.
- **Directories** organize filesystem names into a hierarchy.
- **Metadata** describes objects without being part of their normal application content.
- **File operations** create, read, write, copy, move, rename, delete, and enumerate filesystem objects.
- **File permissions** determine which users or classes of users can perform operations.

The implementations use temporary workspaces so that demonstrations do not modify an existing project directory. The Python and JavaScript programs emphasize practical filesystem APIs, the C++ program models a controlled repository workspace, the Java program expresses filesystem rules through domain types and services, and the SQL script represents filesystem state and permission policy as relational data.

## Files and Directories

A regular file is fundamentally a sequence of bytes. Text files are one interpretation of those bytes using an encoding such as UTF-8. Binary files should normally be processed as bytes rather than decoded as text.

Directories provide hierarchical naming. A path such as `application/config/application.properties` identifies an object through successive directory components. The parent directory is not the same kind of object as the file it contains, and filesystem APIs expose different operations and metadata for each.

The Python implementation uses `pathlib.Path`, which provides explicit path composition instead of relying on string concatenation. It creates nested directories with `mkdir(parents=True, exist_ok=True)` and walks the resulting tree with `rglob()`.

The JavaScript implementation uses Node.js `path` functions and `fs/promises`. Its recursive inventory separates path manipulation from filesystem operations.

The C++ case study creates a repository-like workspace containing `src`, `docs`, and `build/logs`. This models a realistic development filesystem where source material, documentation, and generated operational logs occupy different directory regions.

The Java implementation uses `Path` and a `FileSystemService`. `resolveInsideRoot()` normalizes a requested path and verifies that it remains below the approved workspace root.

## Metadata

Metadata is information maintained about a filesystem object rather than the application's ordinary file content.

The Python program retrieves metadata with `Path.stat()`. It displays size, timestamps, permission bits, inode information when supplied by the platform, and ownership identifiers when available.

The JavaScript program obtains metadata through `fs.stat()` and reports file type, size, timestamps, and permission bits. It also distinguishes `stat()` from `lstat()` when examining symbolic links. `lstat()` describes the link itself rather than transparently following it.

The C++ implementation obtains object information through `std::filesystem::status()` and `file_size()`. It evaluates whether an object is a regular file or directory and inspects owner permission bits.

The Java implementation uses `BasicFileAttributes` with `NOFOLLOW_LINKS`. This matters when the application needs to distinguish a symbolic link from its target.

Metadata is platform-dependent. POSIX systems expose concepts such as user and group ownership, inode numbers, and explicit read/write/execute permission bits. Windows exposes a different security model, so an application should not assume that POSIX permission bits completely represent Windows access control.

## File Operations

File operations have different failure modes and should not be treated as interchangeable string manipulation.

Creating a file can fail because its parent does not exist, the path is invalid, storage is unavailable, or access is denied. Reading can fail because the object is missing, is a directory rather than a regular file, or cannot be opened with the required access.

The Python implementation demonstrates text creation, append mode, reading, copying, moving, and deletion. It catches `FileNotFoundError`, `IsADirectoryError`, and general operating-system failures at appropriate boundaries.

The JavaScript implementation uses asynchronous filesystem APIs. `fs/promises` prevents long synchronous filesystem operations from unnecessarily blocking the Node.js event loop. It also demonstrates `copyFile()`, `rename()`, `rm()`, and `appendFile()`.

The C++ case study uses `std::ofstream`, `std::filesystem::copy_file()`, directory creation, recursive traversal, and validated deletion.

The Java implementation uses `Files.writeString()`, `Files.readString()`, `Files.copy()`, `Files.move()`, and `Files.walk()`. Its service layer prevents callers from bypassing path validation.

## Streaming and Large Files

Reading a large file into memory is not always appropriate. Streaming processes data incrementally.

The Python implementation hashes a file using repeated fixed-size reads. The digest therefore does not require the complete file to be loaded into memory.

The JavaScript implementation creates a binary file and copies it through Node.js streams. The `pipeline()` API connects the streams while preserving asynchronous error handling.

For large production workloads, the appropriate buffer size depends on storage characteristics, workload concurrency, network latency, and application memory limits.

## Permissions

Permissions are an access-control mechanism attached to filesystem objects.

On POSIX systems, traditional permission bits distinguish:

- owner
- group
- other

Each class can have:

- read
- write
- execute

For a regular file, read permits reading content, write permits modifying content, and execute permits execution when the operating system supports executable files. Directory permissions have different semantics: read controls directory-entry listing, write controls creation/removal of entries, and execute permits traversal and access to entries when other conditions permit it.

The Python program changes a POSIX file to mode `640` when running on a POSIX platform. That means the owner receives read/write permission, the group receives read permission, and other users receive no traditional permission bits.

The JavaScript program reports and modifies POSIX-style permission bits when the runtime and operating system support them.

The Java program uses `PosixFilePermission` where available. It deliberately treats the absence of a POSIX permission provider as a platform limitation instead of pretending that Java's POSIX API represents Windows ACLs.

The SQL model stores logical permission policy separately from the actual operating-system filesystem. This distinction is important: a database row granting `read` does not itself grant the kernel permission to open a real operating-system file.

## Path Safety

Path handling becomes a security boundary when an application accepts filenames from users, APIs, archives, jobs, or configuration.

A dangerous operation is constructing a path from untrusted input and assuming that the resulting path remains inside an intended directory. A value such as `../../outside.txt` can escape the expected directory if it is resolved without validation.

The Python implementation resolves a deletion candidate and checks that it remains beneath the approved root before recursive removal.

The JavaScript implementation uses `path.resolve()` and `path.relative()` to reject candidates that escape the approved root.

The Java implementation normalizes the candidate with `Path.normalize()` and checks `startsWith(root)`.

The C++ implementation uses `weakly_canonical()` to compare the components of the approved root and candidate paths.

These checks protect the application boundary, but they do not eliminate every filesystem security problem. Symbolic links can introduce another layer of indirection, and race conditions can occur when an application checks a path and later operates on it after another process has changed the filesystem.

## Atomic Updates

Configuration files and other important state should not normally be replaced by writing an incomplete document directly to the final path.

The Python implementation writes a temporary configuration file and then uses `os.replace()`.

The JavaScript implementation writes a temporary file and renames it into the destination.

The Java implementation attempts `ATOMIC_MOVE` and falls back when the filesystem provider does not support atomic moves.

The objective is to reduce the period during which another reader can observe a partially written destination. Atomicity depends on filesystem and operating-system guarantees, so applications should still consider durability, crash recovery, and cross-filesystem moves separately.

## Symbolic Links

A symbolic link is a filesystem object that refers to another path.

The Python demonstration checks `is_symlink()` and resolves the target.

The JavaScript implementation uses `symlink()` and `lstat()` so that the link itself can be identified.

The Java program uses `NOFOLLOW_LINKS` when reading metadata to avoid silently replacing link metadata with target metadata.

Symbolic links are particularly important for security-sensitive path handling. A path that initially appears to remain inside an approved directory can resolve through a link to another location. Applications performing privileged filesystem operations therefore need stronger techniques than simple string prefix checks when hostile filesystem mutation is possible.

## Python Implementation

The Python program is a filesystem laboratory built around `pathlib`, `os`, `stat`, `shutil`, `tempfile`, and hashing from the standard library.

Its inventory uses a `FileRecord` dataclass to turn raw filesystem metadata into structured records. This makes the distinction between filesystem discovery and reporting explicit.

The file hashing implementation reads fixed-size chunks and computes SHA-256 incrementally. The recursive copy demonstration uses `shutil.copytree()` while the deletion path is explicitly validated before `rmtree()`.

The temporary workspace is removed automatically with `TemporaryDirectory`, preventing the laboratory from leaving test files in the user's working directory.

## JavaScript Implementation

The Node.js implementation emphasizes asynchronous filesystem behavior and event-driven I/O.

`fs/promises` is used for ordinary filesystem operations, while streams are used for large binary data. The binary demonstration creates a sizeable file and copies it with `pipeline()`, avoiding a design in which the complete file is first converted into one large in-memory buffer.

The program also demonstrates `stat()` versus symbolic-link inspection, SHA-256 hashing through a stream, recursive inventory, atomic-style replacement, and path validation.

The temporary directory is removed in a `finally` block, so cleanup remains active even if one demonstration raises an exception.

## C++ Case Study

The C++ program models a controlled development repository workspace.

The workspace contains source files, documentation, configuration, and build logs. `RepositoryWorkspace` owns operations on the approved root, while `FileSystemPolicy` contains permission and path-safety decisions.

`RepositoryFile` provides a structured representation of discovered regular files. The inventory uses `recursive_directory_iterator`, making directory traversal explicit.

The backup service rejects anything that is not a regular file before copying it. The deletion operation validates the requested path before calling `remove_all()`.

The case study demonstrates an important systems-design distinction: a filesystem service should not scatter path validation and policy decisions throughout unrelated application code. Centralizing those rules makes unsafe operations easier to detect and test.

## Java Implementation

The Java program models filesystem behavior through a `FileSystemService` rather than a collection of unrelated API calls.

`FileMetadata` is an immutable record containing path, resource type, size, timestamp, and POSIX permission information. `ResourceType` distinguishes regular files, directories, and symbolic links.

`AccessRight` provides a domain vocabulary for read, write, and execute access. The service translates those concepts to POSIX permissions when the platform exposes a POSIX filesystem provider.

The service also owns path validation. Every external relative path is resolved against the approved root, normalized, and checked before the operation proceeds.

The atomic configuration update first writes a temporary file and then attempts `ATOMIC_MOVE`. This gives the example a concrete failure-aware implementation rather than treating atomic replacement as a purely conceptual operation.

## SQL Data Model

The SQL script represents a logical filesystem hierarchy using `filesystem_nodes`.

A node has a parent, name, resource type, size, timestamps, and optional symbolic-link target. A foreign key connects children to their parent directories, while a trigger rejects a parent that is not a directory.

The sibling-name uniqueness index prevents two nodes in the same logical directory from having the same name.

`filesystem_permissions` separates permission policy from filesystem objects. Its composite primary key prevents duplicate permission records for the same node, scope, and access right.

`filesystem_users` represents users and their logical groups. `filesystem_audit` records operations, their success state, the actor, and the affected node.

The recursive common table expression reconstructs logical paths from parent-child relationships. This is the relational equivalent of traversing a directory tree.

## Database-Level Integrity

The SQL model places structural rules close to the data.

Negative file sizes are rejected by a `CHECK` constraint. A symbolic link without a target is rejected. A filesystem node cannot reference a nonexistent parent because of the foreign key. Duplicate sibling names are rejected by the unique index.

The parent-directory trigger handles a rule that cannot be expressed directly by a simple foreign key: the referenced parent must not merely exist, it must have `kind = 'directory'`.

The audit records demonstrate both successful and failed logical operations. The transaction around the rename updates the filesystem representation and audit record together.

## Permissions Versus Application Authorization

Filesystem permissions and application authorization are related but not identical.

An operating system may decide whether a process can open a file. An application may separately decide whether a particular authenticated user is allowed to request a particular operation.

The SQL function `has_access()` represents logical application policy. It should not be interpreted as a replacement for operating-system enforcement.

A production system may therefore have multiple authorization layers: operating-system permissions, service identity, application roles, directory ownership, and potentially additional policy controls.

## Common Failure Modes

**Confusing files and directories:** Reading a directory through a regular-file API can produce an `IsADirectoryError`, platform-specific error, or equivalent failure.

**Assuming paths are strings:** Path separators, normalization, drive letters, UNC paths, symbolic links, and filesystem providers make path handling more complex than concatenating strings.

**Loading large files into memory:** Whole-file reads can cause unnecessary memory pressure. Streaming or chunked processing is preferable for large data.

**Ignoring permissions:** An application can fail even when a path exists because the process lacks the required access.

**Using `stat()` when link metadata is required:** Following a symbolic link can return metadata for the target instead of the link.

**Unsafe recursive deletion:** Recursive deletion magnifies a path-validation mistake. The target should be validated before the operation and, for hostile environments, protected against filesystem races.

**Assuming POSIX permissions are universal:** Windows ACLs and other filesystem security models do not map perfectly onto Unix mode bits.

**Assuming successful writes imply durability:** A successful write does not automatically mean that data has survived every possible power-loss scenario.

## Performance Considerations

Directory traversal can become expensive when a tree contains millions of entries. Recursive traversal should avoid unnecessary metadata calls when only names are required.

Large-file processing should be streaming or chunked. Repeated small reads can increase system-call overhead, while extremely large buffers can increase memory pressure.

Indexes such as the SQL parent and kind indexes improve common inventory queries, but indexes have storage and update costs. The sibling-name index also enforces a correctness rule rather than existing solely for performance.

Metadata operations can be significantly more expensive on network filesystems than on local storage. Production code should avoid repeatedly querying the same metadata when a single traversal can collect the required attributes.

## Security Considerations

Filesystem applications should treat externally supplied paths as untrusted input.

Path traversal must be addressed before reading, writing, copying, extracting, or deleting data. Symbolic links require special attention because the apparent path and resolved target can differ.

Recursive deletion deserves particularly strict controls because an incorrect target can cause extensive data loss.

Permission changes should follow least privilege. Applications should avoid making files globally writable or executable merely to simplify deployment.

Temporary files can contain sensitive information. They should be created in controlled locations and removed after use. Where confidential data is involved, the application must also consider encryption, operating-system access controls, backup retention, and storage-media behavior.

## Production Design Considerations

A production filesystem service should define explicit boundaries around which directories it owns, which identities can modify them, and which operations are permitted.

Important operations should produce auditable records when traceability matters. Errors should preserve operating-system error information while avoiding accidental disclosure of sensitive paths to untrusted callers.

Configuration updates should use controlled replacement patterns. Backup and recovery behavior should be designed independently from ordinary file copying because copying a file does not by itself establish a reliable disaster-recovery process.

Filesystem behavior also varies by operating system, filesystem type, mount configuration, permissions model, case sensitivity, symbolic-link support, and network characteristics. Cross-platform applications should test these assumptions rather than treating one host's behavior as universal.
