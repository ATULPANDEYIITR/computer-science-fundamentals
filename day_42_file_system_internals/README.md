# File System Internals: Inodes, File Allocation, Journaling, and Mounting

## Scope

This learning artifact models the internal structures and operations of a Unix-like file system through four closely related areas:

- **Inodes** identify files and hold metadata such as file type, permissions, ownership, size, timestamps, link count, and references to storage blocks.
- **File allocation** maps a file's logical blocks to physical blocks on a storage volume. The implementations use direct references for small files and an indirect reference structure when a file grows beyond the direct capacity.
- **Journaling** provides a transaction boundary for filesystem changes. Metadata changes are recorded as a recoverable operation before the filesystem treats the operation as durable.
- **Mounting** validates filesystem geometry and consistency before making the filesystem available. Unmounting provides the clean-shutdown boundary, while an unclean state causes recovery processing during the next mount.

The six files deliberately use different technical perspectives. Python provides a detailed executable simulator, JavaScript emphasizes event-driven filesystem lifecycle behavior, C++ presents a storage-engine case study, Java models an enterprise-oriented service with explicit domain abstractions, and PostgreSQL represents filesystem metadata and integrity rules relationally.

---

## Core filesystem model

A filesystem separates the human-readable name of an object from the metadata and storage that belong to that object.

A simplified relationship is:

    path
      |
      v
    directory entry
      |
      v
    inode
      |
      +---- metadata
      |
      +---- logical block 0 -> physical block
      |
      +---- logical block 1 -> physical block
      |
      +---- ...
      |
      +---- indirect block -> additional physical blocks

A directory therefore does not need to contain the contents of a regular file. It maps a name to an inode. The inode then describes the object and provides the information needed to locate its contents.

This distinction is central to filesystem internals. Renaming a file can change a directory entry without changing the file's data blocks. Reading the file requires resolving the directory path, locating its inode, translating the requested logical file offset into a logical block, and then locating the corresponding physical block.

---

## Inodes

An inode is the filesystem object that represents the metadata identity of a file or directory.

The implementations model fields such as:

- inode number
- file type
- permission mode
- owner identifiers
- parent relationship
- file size
- link count
- access, modification, and change timestamps
- direct data-block references
- an indirect-block reference
- additional indirect data-block references

The inode does not normally use the filename as its identity. The filename is maintained by a directory entry.

For example, a directory may conceptually contain:

    "report.txt" -> inode 42

The inode then contains information such as:

    inode 42
    type = regular file
    size = 18432
    direct blocks = [810, 811, 812, 813]
    indirect block = 814

This means a pathname lookup first finds inode 42 and then uses the inode's block mappings to access the file contents.

### Directory entries

Directories are represented as specialized filesystem objects. Their data describes name-to-inode relationships.

The implementations explicitly model the conventional `.` and `..` entries:

- `.` refers to the directory itself.
- `..` refers to its parent directory.

This makes directory traversal different from regular-file reading. A directory lookup searches its entries, while a regular-file read follows the inode's block mappings.

The Python, JavaScript, C++, and Java implementations all preserve these relationships in their in-memory directory structures. The SQL implementation represents them with the `directory_entry` table and foreign keys.

### Link counts

A link count tracks how many directory references contribute to an inode's name-based reachability.

A directory has special link behavior because subdirectories create relationships involving the parent directory. The simulations therefore increment parent directory link counts when subdirectories are created.

This is different from merely storing the number of filenames displayed to a user. Link accounting is an inode-level consistency property.

---

## File allocation

A file is logically a sequence of bytes, while a storage device is organized into blocks.

If the filesystem block size is 4096 bytes, byte offset 9000 belongs to:

    logical block = floor(9000 / 4096)

The offset within that logical block is:

    local offset = 9000 mod 4096

The inode then supplies the physical block corresponding to that logical block.

### Direct allocation

The programs reserve a small number of direct references in each inode.

The Python, JavaScript, C++, and Java implementations use four direct references for demonstration. A small file can therefore be represented without an additional level of block indirection.

The advantage is straightforward: locating the first blocks requires very little metadata traversal.

The limitation is capacity. Once all direct references are occupied, the inode needs another mechanism to represent additional blocks.

### Indirect allocation

The simulated inode allocates an indirect metadata block once the direct capacity is exceeded.

The relationship becomes:

    inode
      |
      +-- direct block
      +-- direct block
      +-- direct block
      +-- direct block
      |
      +-- indirect block
             |
             +-- data block
             +-- data block
             +-- data block
             +-- ...

The indirect block is not itself ordinary file content. It is allocation metadata that contains references to additional data blocks.

This creates an important distinction:

- a **data block** contains file contents;
- an **indirect block** contains allocation references;
- an **inode** contains file metadata and the first level of block references.

The C++ case study makes this distinction visible when `pack.data` crosses the direct-block threshold.

### Logical versus physical blocks

A logical block belongs to the file's address space.

A physical block belongs to the filesystem's storage space.

For example:

    logical block 0 -> physical block 200
    logical block 1 -> physical block 201
    logical block 2 -> physical block 315

The file remains logically contiguous even when the physical blocks are separated.

This separation is important when discussing fragmentation. Fragmentation is primarily a property of the physical allocation pattern, not of the logical byte sequence exposed by the file interface.

### Allocation and truncation

Growing a file requires allocating enough physical blocks for the new logical size.

Shrinking a file requires releasing blocks that no longer belong to its logical range. When an indirect structure becomes empty, the indirect metadata block itself can also be released.

The Python, JavaScript, and Java implementations explicitly perform this cleanup. The C++ program demonstrates it with the repository `pack.data` case study.

---

## Journaling

Filesystem metadata operations can involve several related updates.

Creating a file can require:

    allocate inode
    create directory entry
    update directory timestamps
    update inode allocation state

If a crash occurs after only some of those changes reach persistent storage, the filesystem can contain contradictory structures.

For example, a directory could reference an inode that was never completely initialized, or an inode could claim a block that the allocation structure considers free.

Journaling addresses this consistency problem by establishing a durable record of an operation before considering the operation complete.

The simulated transaction lifecycle is:

    prepare transaction
          |
          v
    record affected metadata
          |
          v
    perform filesystem change
          |
          v
    commit transaction
          |
          v
    checkpoint/remove journal record

The Python `JournalRecord`, JavaScript `JournalTransaction`, C++ `JournalRecord`, Java `JournalTransaction`, and PostgreSQL `journal_transaction` table represent this idea differently.

### What journaling protects

The emphasis in these implementations is metadata consistency.

Journaling does not automatically mean that every user-data byte is synchronously copied into a journal. Filesystems differ in their journaling modes and ordering guarantees.

A metadata-journaling design can make the filesystem structure recoverable while allowing ordinary file data to follow different persistence rules.

The important concept is the ordering relationship between:

    journal durability
    filesystem metadata durability
    recovery

A production filesystem must define these ordering rules precisely.

### Prepared versus committed state

The SQL implementation explicitly distinguishes `prepared`, `committed`, and `aborted` journal states.

A prepared transaction records an intended operation that has not reached its final commit state.

A committed transaction represents a completed durability boundary.

The Python and JavaScript simulations use transaction objects to make the same conceptual boundary visible.

### Crash recovery

An unclean filesystem mount indicates that the previous lifecycle did not finish normally.

The Python implementation sets the filesystem clean flag to false during `simulate_crash()` and performs recovery during the next `mount()`.

The JavaScript implementation exposes the crash through an event-driven lifecycle. This is useful for observing the difference between normal unmounting and abrupt process termination.

The SQL implementation represents recovery state through `clean_shutdown` and `mount_status`.

A production journal recovery engine would also need durable sequence numbers, journal checksums, transaction ordering, checkpointing, handling of partial writes, and clearly defined replay semantics.

---

## Mounting

Mounting is the operation that makes a filesystem's namespace available to the operating system.

A simplified lifecycle is:

    storage device
          |
          v
    read superblock
          |
          v
    validate geometry
          |
          v
    inspect clean/recovery state
          |
          v
    recover journal if required
          |
          v
    verify critical consistency
          |
          v
    expose mounted filesystem

The implementations model a superblock containing values such as:

- filesystem magic
- block size
- total block count
- inode capacity
- root inode
- journal capacity
- generation number
- clean-shutdown state

### Superblock validation

The filesystem must not blindly interpret arbitrary storage as its own structures.

The magic value distinguishes the expected filesystem format from incompatible data.

Block size and total block count must agree with the structures used to interpret storage. An inconsistency here can make all subsequent block calculations invalid.

The Python and JavaScript mount methods explicitly reject incompatible geometry. The C++ and Java implementations perform equivalent checks.

### Root inode

A mounted filesystem requires a starting point for pathname resolution.

The superblock stores the root inode reference. Path resolution begins from that inode and follows directory entries.

The SQL schema stores the root through `filesystem.root_inode`, while the in-memory implementations use the root inode as the initial path-resolution point.

### Clean and unclean states

A clean unmount establishes that the filesystem completed its expected shutdown procedure.

An unclean state indicates that recovery may be required.

This is why mounting and journaling are related but not interchangeable:

- journaling records recoverable operations;
- mounting decides whether the filesystem can safely become active;
- recovery processes durable journal state when the previous shutdown was incomplete.

---

## Python implementation

The Python program is the most detailed general-purpose simulator.

Its `FileSystem` class maintains:

- a simulated block-addressable disk;
- inode objects;
- directory entries;
- an allocation set;
- a superblock;
- a journal;
- simulated timestamps;
- mount state.

`create_file()` demonstrates inode creation and directory-entry insertion.

`mkdir()` demonstrates directory-specific inode state and parent link accounting.

`write_file()` translates byte ranges into logical blocks and allocates additional physical blocks when the file grows.

`read_file()` performs the reverse operation by translating a byte range into physical block reads.

`truncate()` releases blocks and removes an empty indirect allocation block.

`check_consistency()` performs filesystem-level validation rather than assuming that internal data structures are correct.

The consistency checker catches conditions such as:

- missing root inode;
- missing `.` or `..` directory entries;
- dangling directory references;
- duplicate physical block ownership;
- data references into metadata regions;
- insufficient blocks for a file's declared size;
- mismatch between inode references and the allocation set.

`fragmentation_report()` also demonstrates how the set of allocated physical blocks can be inspected for contiguous runs.

---

## JavaScript implementation

The JavaScript program takes an event-driven perspective.

The filesystem extends Node.js's `EventEmitter`, so important lifecycle operations emit observable events.

Examples include:

- inode allocation;
- block allocation;
- block release;
- journal preparation;
- journal commit;
- journal replay;
- mount;
- unmount;
- crash;
- file writes.

This representation is useful because filesystem operations are not isolated functions in a larger storage service. They produce observable state transitions that monitoring and auditing systems can consume.

The JavaScript `writeFile()` implementation uses `Buffer` objects to model block-oriented binary data. It translates UTF-8 input into bytes before placing those bytes into simulated storage blocks.

The event-driven design is intentionally different from the Python program. The focus is not just allocation correctness but the observable lifecycle surrounding storage operations.

The `allocationDigest()` method uses SHA-256 to produce a deterministic fingerprint of the current allocation set. It does not replace a filesystem integrity checksum; it demonstrates how storage-state observations can be turned into a stable diagnostic value.

---

## C++ storage-engine case study

The C++ program models a repository storage engine.

The scenario contains a repository tree with:

    /repositories
        /kernel
            /objects
                pack.index
                pack.data

The important technical behavior is storage-oriented rather than a generic C++ demonstration.

`pack.index` contains relatively small metadata and stays within the direct allocation range.

`pack.data` receives a much larger payload. Once four direct blocks are insufficient, the inode obtains an indirect metadata block and additional data blocks.

The `RepositoryStorageEngine` separates:

- superblock state;
- simulated disk blocks;
- metadata block reservations;
- allocation state;
- inode objects;
- directory objects;
- journal records.

The `consistencyCheck()` function verifies that a physical block cannot simultaneously be treated as independently owned by multiple inode mappings.

It also checks that regular files have enough physical mappings for their declared sizes.

The case study demonstrates why storage-engine code needs explicit invariants. Allocation is not just a loop that finds an unused integer. Every allocated block must have a valid owner, metadata blocks must not be mistaken for ordinary file blocks, and inode mappings must agree with allocation state.

---

## Java enterprise-oriented model

The Java program introduces an explicit policy abstraction through the `MergePolicy` interface.

The storage layer is represented by `FileSystemService`, while `RepositoryStoragePolicy` represents an external rule layer that can decide whether a storage operation is valid.

This separation matters in enterprise systems because filesystem mechanics and higher-level policy should not become inseparably coupled.

The domain types make different concepts explicit:

- `FileType` distinguishes files and directories;
- `InodeAttribute` identifies timestamp categories;
- `JournalState` distinguishes journal lifecycle state;
- `DirectoryEntry` models namespace relationships;
- `JournalTransaction` represents a storage transaction.

The Java `append()` operation demonstrates how a higher-level service operation can pass through a policy boundary before manipulating inode allocation.

The `truncate()` implementation shows the inverse allocation lifecycle. Blocks that fall outside the new logical file size are released, and an empty indirect allocation structure is removed.

The service also exposes `verifyConsistency()` and an allocation digest. The digest is useful for deterministic diagnostics but is not presented as a substitute for a filesystem's complete integrity system.

---

## PostgreSQL relational model

The SQL implementation represents filesystem state as relational metadata.

### `filesystem`

The `filesystem` table corresponds to superblock-level information.

It contains:

- filesystem identity;
- magic value;
- block size;
- total block count;
- inode capacity;
- root inode;
- journal capacity;
- generation;
- mount status;
- clean-shutdown state.

### `inode`

The `inode` table stores the identity and metadata of each filesystem object.

The composite uniqueness rule on `(filesystem_id, inode_number)` prevents two objects in the same filesystem from claiming the same inode number.

The foreign-key relationship to the filesystem ensures that an inode belongs to an existing volume.

### `directory_entry`

`directory_entry` represents pathname namespace relationships.

A directory inode and an entry name form the primary key. The target inode is a foreign key.

This makes dangling references detectable at the relational level.

### `storage_block`

`storage_block` represents physical block state.

The `allocated` flag and `is_metadata` flag distinguish free blocks, allocated data blocks, and reserved metadata blocks.

### `inode_block`

`inode_block` connects logical file blocks to physical blocks.

The `logical_block_number` represents a block position inside a file.

The `physical_block_number` represents its location on the volume.

`allocation_kind` records whether the mapping is direct or indirect.

This table is the relational equivalent of the block references maintained inside the in-memory inode models.

### Journal tables

`journal_transaction` represents transaction state and ordering.

`journal_inode_record` records inode-level changes.

`journal_directory_record` records namespace changes.

Separating these records allows recovery logic to identify which filesystem objects participated in a transaction.

---

## Database-level integrity

Some filesystem invariants are valuable at the database layer because application code should not be the only place that protects them.

The SQL script uses:

- primary keys;
- foreign keys;
- unique constraints;
- check constraints;
- indexes;
- triggers;
- deferred constraint triggers;
- transactional functions.

The `enforce_unique_physical_allocation()` trigger verifies that an inode mapping points to an existing allocated data block and rejects attempts to use a metadata block as ordinary file storage.

The `enforce_inode_size()` constraint trigger compares a regular file's declared size with its mapped physical blocks.

This illustrates an important distinction between application validation and structural integrity. Application code can reject an invalid operation before issuing SQL, but database constraints provide a second enforcement boundary.

---

## Important distinctions

| Area | Primary responsibility | Main state being managed |
|---|---|---|
| Inodes | Identify objects and store metadata | File metadata and block references |
| File allocation | Map logical file space to physical storage | Physical block ownership |
| Journaling | Preserve recoverable transaction intent | Metadata transaction state |
| Mounting | Validate and activate a filesystem | Filesystem lifecycle state |

These areas interact but should not be treated as synonyms.

A Pull-style namespace operation is not relevant here; the filesystem namespace is instead governed by directory entries and inode references.

Likewise, journaling is not equivalent to backup. A journal is primarily a mechanism for filesystem consistency and crash recovery, not a long-term copy of user data.

Mounting is not the same as opening a file. Mounting makes the filesystem namespace available, while opening a file operates on an individual filesystem object after path resolution.

---

## Edge cases represented by the implementations

### Empty files

A zero-byte regular file requires no data blocks. Its inode can still exist and be referenced by a directory.

### Files crossing the direct allocation boundary

A file larger than the direct capacity must acquire an indirect allocation structure. This is explicitly exercised by the Python, JavaScript, C++, and Java programs.

### Truncation to zero

Reducing a file to zero bytes should release all data blocks and any now-unused indirect metadata structure.

### Missing paths

Path resolution rejects nonexistent components instead of silently creating them.

### Duplicate names

Directory insertion rejects an entry when the same name already exists in the target directory.

### Invalid names

The implementations reject empty names, `.` and `..` as ordinary names, embedded path separators, and names beyond the modeled length limit.

### Metadata/data separation

Metadata blocks are reserved and cannot be returned to the ordinary data allocator.

### Unclean shutdown

An unclean filesystem state causes recovery processing during mount rather than treating the previous lifecycle as a successful clean shutdown.

---

## Performance considerations

Inode-based lookup introduces several layers of work.

A pathname lookup may require:

    path parsing
      -> directory lookup
      -> inode lookup
      -> logical block calculation
      -> physical block lookup
      -> block read

Real filesystems reduce the cost of these operations through caching.

The simulations intentionally use straightforward maps, lists, and sets so the underlying structures remain visible.

The SQL model adds indexes where query patterns justify them:

- filesystem/type filtering on inodes;
- reverse lookup of directory targets;
- physical-block lookup;
- journal recovery ordering;
- recent mount events.

An actual storage implementation must also consider locality, allocation-group design, cache behavior, I/O scheduling, metadata contention, and persistent storage latency.

---

## Security and integrity considerations

Filesystem metadata is privileged state.

A corrupted inode can redirect reads to unintended blocks. A corrupted allocation map can cause two objects to claim the same physical storage. A corrupted directory entry can create a namespace reference to an unexpected object.

The examples therefore enforce structural relationships rather than relying entirely on application assumptions.

Permission mode, UID, and GID are represented in the inode structures, but the simulators do not implement a complete operating-system authorization model. Real permission enforcement requires identity handling, access checks, ownership semantics, special permission bits, ACLs where supported, and operating-system integration.

Journal integrity also requires protection against partial or corrupted journal records. Production systems may use checksums, sequence numbers, barriers, durable flush semantics, redundant metadata, or copy-on-write techniques depending on filesystem architecture.

---

## Debugging and consistency checking

A filesystem consistency checker should reason from multiple independent structures.

Useful questions include:

- Does every directory reference an existing inode?
- Does every regular file have enough block mappings for its declared size?
- Is a physical data block owned by more than one inode?
- Is a data mapping accidentally pointing into a metadata region?
- Does the allocation map agree with inode block references?
- Does the root inode exist?
- Are required directory relationships present?
- Is the filesystem marked clean when it was actually shut down cleanly?

The `check_consistency()` routines in the Python and C++ implementations and `verifyConsistency()` in the JavaScript and Java programs make these checks executable.

The SQL queries perform analogous relational checks against stored metadata.

---

## Production considerations

A real filesystem is considerably more complex than these simulations.

Important production concerns include persistent serialization formats, crash-consistent superblock updates, block checksums, metadata checksums, allocation bitmaps, free-space trees, extent allocation, delayed allocation, write ordering, cache coherency, concurrent access, locking, sparse files, hard links, symbolic links, extended attributes, access-control lists, quotas, storage-device error handling, journal replay ordering, journal wraparound, and filesystem repair.

The allocation mechanism here is intentionally simple. Real filesystems commonly use structures such as extents or allocation trees to represent large contiguous ranges more efficiently than individual block pointers.

The journal model is also intentionally compact. A production journal needs a durable format and explicit recovery semantics for every point at which a crash can occur.

Mounting likewise involves more than checking a magic value. A real implementation must validate on-disk structures, establish the appropriate device mappings, perform recovery when required, initialize caches, and expose a consistent namespace to the operating system.

The central design principle remains the same across the implementations: **filesystem correctness comes from maintaining consistent relationships among namespace entries, inode metadata, physical allocation, journal state, and mount state.**
