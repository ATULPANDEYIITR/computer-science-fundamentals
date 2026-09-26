/*
 * STORAGE SYSTEMS
 *
 * HDD, SSD, flash storage, file storage, and block storage.
 *
 * This self-contained JavaScript file demonstrates storage concepts through
 * executable examples. It is intentionally written without external packages.
 *
 * Compatible with modern Node.js.
 */

"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");
const crypto = require("crypto");

// ============================================================================
// 1. BASIC STORAGE UNITS
// ============================================================================

function humanBytes(bytes) {
    if (bytes < 1024) return `${bytes} B`;

    const units = ["KiB", "MiB", "GiB", "TiB", "PiB"];
    let value = bytes;

    for (const unit of units) {
        value /= 1024;
        if (value < 1024) {
            return `${value.toFixed(2)} ${unit}`;
        }
    }

    return `${value.toFixed(2)} EiB`;
}

function section(title) {
    console.log(`\n${"=".repeat(78)}\n${title}\n${"=".repeat(78)}`);
}

function subsection(title) {
    console.log(`\n--- ${title} ---`);
}

function demonstrateUnits() {
    section("1. STORAGE UNITS");

    const values = [
        512,
        4096,
        1024 * 1024,
        10 * 1024 * 1024,
        5 * 1024 ** 3
    ];

    for (const value of values) {
        console.log(`${value.toLocaleString()} bytes = ${humanBytes(value)}`);
    }

    console.log(`
Storage is persistent or semi-persistent capacity used to retain data.

Important concepts:
- bit: binary value, 0 or 1.
- byte: normally 8 bits.
- sector: low-level storage unit associated with disk media.
- block: logical addressable unit exposed by a block device.
- file: named data managed through a filesystem.
- filesystem: software that organizes files, metadata, allocation and access.
- latency: time required for an I/O operation.
- throughput: amount of data transferred per unit of time.
- IOPS: input/output operations per second.
`);
}


// ============================================================================
// 2. MEDIA TECHNOLOGIES
// ============================================================================

const storageProfiles = {
    HDD: {
        movingParts: true,
        latencyUs: 5000,
        iops: 150,
        sequentialReadMBps: 180,
        sequentialWriteMBps: 160
    },
    SSD: {
        movingParts: false,
        latencyUs: 100,
        iops: 100000,
        sequentialReadMBps: 550,
        sequentialWriteMBps: 500
    },
    FLASH: {
        movingParts: false,
        latencyUs: 80,
        iops: 80000,
        sequentialReadMBps: 400,
        sequentialWriteMBps: 350
    }
};

function compareMedia() {
    section("2. HDD, SSD, AND FLASH STORAGE");

    for (const [name, profile] of Object.entries(storageProfiles)) {
        console.log(`\n${name}`);
        console.log(`  Moving parts: ${profile.movingParts}`);
        console.log(`  Illustrative latency: ${profile.latencyUs} microseconds`);
        console.log(`  Illustrative IOPS: ${profile.iops.toLocaleString()}`);
        console.log(`  Sequential read: ${profile.sequentialReadMBps} MB/s`);
        console.log(`  Sequential write: ${profile.sequentialWriteMBps} MB/s`);
    }

    console.log(`
HDD uses rotating magnetic platters and mechanical heads.
SSD uses non-volatile semiconductor storage and has no moving head.
Flash is a semiconductor storage technology commonly used by SSDs,
memory cards, USB devices, and embedded storage.

The values above are educational examples rather than universal specifications.
`);
}


// ============================================================================
// 3. HDD ACCESS SIMULATION
// ============================================================================

class HDDModel {
    constructor(tracks, sectorsPerTrack, bytesPerSector, rpm) {
        if (tracks <= 0 || sectorsPerTrack <= 0 || bytesPerSector <= 0 || rpm <= 0) {
            throw new RangeError("HDD parameters must be positive");
        }

        this.tracks = tracks;
        this.sectorsPerTrack = sectorsPerTrack;
        this.bytesPerSector = bytesPerSector;
        this.rpm = rpm;
    }

    get capacityBytes() {
        return this.tracks *
            this.sectorsPerTrack *
            this.bytesPerSector;
    }

    get rotationPeriodMs() {
        return 60000 / this.rpm;
    }

    estimateAccess(currentTrack, requestedTrack) {
        if (
            currentTrack < 0 ||
            requestedTrack < 0 ||
            currentTrack >= this.tracks ||
            requestedTrack >= this.tracks
        ) {
            throw new RangeError("Track outside HDD geometry");
        }

        const distance = Math.abs(requestedTrack - currentTrack);

        // Simplified educational seek model.
        const seekMs = 2 + distance * 0.02;
        const rotationalLatencyMs = this.rotationPeriodMs / 2;

        const transferMs =
            this.rotationPeriodMs / this.sectorsPerTrack;

        return {
            seekMs,
            rotationalLatencyMs,
            transferMs,
            totalMs: seekMs + rotationalLatencyMs + transferMs
        };
    }
}

function demonstrateHDD() {
    section("3. HDD MECHANICAL ACCESS");

    const disk = new HDDModel(10000, 512, 512, 7200);
    const estimate = disk.estimateAccess(100, 4100);

    console.log(`Capacity: ${humanBytes(disk.capacityBytes)}`);
    console.log(`Rotation period: ${disk.rotationPeriodMs.toFixed(3)} ms`);
    console.table(estimate);

    console.log(`
An HDD request can involve:
1. Seek time.
2. Rotational latency.
3. Data transfer.

This mechanical process makes random small I/O substantially different from
large sequential transfers.
`);
}


// ============================================================================
// 4. FLASH CELL TYPES
// ============================================================================

const flashCellTypes = [
    { name: "SLC", bitsPerCell: 1 },
    { name: "MLC", bitsPerCell: 2 },
    { name: "TLC", bitsPerCell: 3 },
    { name: "QLC", bitsPerCell: 4 }
];

function demonstrateFlash() {
    section("4. NAND FLASH");

    for (const cell of flashCellTypes) {
        console.log(`${cell.name}: ${cell.bitsPerCell} bit(s) per cell`);
    }

    console.log(`
Important SSD/flash mechanisms:
- FTL: Flash Translation Layer.
- Wear leveling: distributes writes across physical cells.
- Garbage collection: reclaims blocks containing obsolete pages.
- TRIM/deallocate: informs storage that logical ranges are no longer needed.
- ECC: error correction.
- Over-provisioning: reserved physical capacity.
- Write caching: absorbs or reorganizes writes.

Flash commonly programs pages but erases larger erase blocks. This mismatch
is one reason SSD controllers perform substantial internal management.
`);
}


// ============================================================================
// 5. BLOCK DEVICE
// ============================================================================

class BlockDevice {
    constructor(blockSize, blockCount) {
        if (!Number.isInteger(blockSize) || blockSize <= 0) {
            throw new RangeError("Block size must be a positive integer");
        }

        if (!Number.isInteger(blockCount) || blockCount <= 0) {
            throw new RangeError("Block count must be a positive integer");
        }

        this.blockSize = blockSize;
        this.blockCount = blockCount;
        this.storage = Buffer.alloc(blockSize * blockCount);
    }

    get capacity() {
        return this.storage.length;
    }

    validateBlock(blockNumber) {
        if (
            !Number.isInteger(blockNumber) ||
            blockNumber < 0 ||
            blockNumber >= this.blockCount
        ) {
            throw new RangeError("Block number outside device range");
        }
    }

    readBlock(blockNumber) {
        this.validateBlock(blockNumber);

        const start = blockNumber * this.blockSize;
        return Buffer.from(
            this.storage.subarray(start, start + this.blockSize)
        );
    }

    writeBlock(blockNumber, data) {
        this.validateBlock(blockNumber);

        if (!Buffer.isBuffer(data)) {
            throw new TypeError("Data must be a Buffer");
        }

        if (data.length !== this.blockSize) {
            throw new RangeError(
                `Expected ${this.blockSize} bytes, received ${data.length}`
            );
        }

        const start = blockNumber * this.blockSize;
        data.copy(this.storage, start);
    }
}

function demonstrateBlockStorage() {
    section("5. BLOCK STORAGE");

    const device = new BlockDevice(512, 100);

    console.log(`Capacity: ${humanBytes(device.capacity)}`);

    const payload = Buffer.alloc(512);
    Buffer.from("BLOCK-DEVICE-RECORD").copy(payload);

    device.writeBlock(7, payload);

    console.log(
        `Block 7: ${device.readBlock(7).subarray(0, 20).toString()}`
    );

    for (const invalidBlock of [-1, 100]) {
        try {
            device.readBlock(invalidBlock);
        } catch (error) {
            console.log(
                `Rejected invalid block ${invalidBlock}: ${error.message}`
            );
        }
    }
}


// ============================================================================
// 6. SIMPLE FILESYSTEM OVER BLOCK STORAGE
// ============================================================================

class SimpleFileSystem {
    constructor(blockDevice) {
        this.device = blockDevice;
        this.freeBlocks = new Set(
            Array.from(
                { length: blockDevice.blockCount },
                (_, index) => index
            )
        );
        this.files = new Map();
    }

    createFile(name, data) {
        if (typeof name !== "string" || name.length === 0 || name.includes("/")) {
            throw new TypeError("Invalid file name");
        }

        if (!Buffer.isBuffer(data)) {
            throw new TypeError("File data must be a Buffer");
        }

        if (this.files.has(name)) {
            throw new Error(`File already exists: ${name}`);
        }

        const requiredBlocks = Math.max(
            1,
            Math.ceil(data.length / this.device.blockSize)
        );

        if (requiredBlocks > this.freeBlocks.size) {
            throw new Error("Insufficient free blocks");
        }

        const allocated = [...this.freeBlocks]
            .sort((a, b) => a - b)
            .slice(0, requiredBlocks);

        for (const block of allocated) {
            this.freeBlocks.delete(block);
        }

        this.files.set(name, allocated);

        const padded = Buffer.alloc(
            requiredBlocks * this.device.blockSize
        );

        data.copy(padded);

        for (let index = 0; index < allocated.length; index++) {
            const start = index * this.device.blockSize;
            const blockData = padded.subarray(
                start,
                start + this.device.blockSize
            );

            this.device.writeBlock(allocated[index], blockData);
        }
    }

    readFile(name) {
        if (!this.files.has(name)) {
            throw new Error(`File not found: ${name}`);
        }

        const blocks = this.files.get(name);

        const result = Buffer.concat(
            blocks.map(block => this.device.readBlock(block))
        );

        // This simple teaching filesystem has no explicit file length metadata,
        // so trailing zero bytes are removed.
        return result.subarray(0, result.length).toString().replace(/\0+$/, "");
    }

    deleteFile(name) {
        if (!this.files.has(name)) {
            throw new Error(`File not found: ${name}`);
        }

        for (const block of this.files.get(name)) {
            this.freeBlocks.add(block);
        }

        this.files.delete(name);
    }

    report() {
        return {
            totalBlocks: this.device.blockCount,
            freeBlocks: this.freeBlocks.size,
            allocatedBlocks:
                this.device.blockCount - this.freeBlocks.size,
            files: this.files.size
        };
    }
}

function demonstrateSimpleFileSystem() {
    section("6. FILESYSTEM BUILT ON BLOCK STORAGE");

    const device = new BlockDevice(128, 32);
    const fileSystem = new SimpleFileSystem(device);

    const content = Buffer.from(
        "Filesystem metadata maps file names to storage blocks."
    );

    fileSystem.createFile("document.txt", content);

    console.log(fileSystem.report());
    console.log(`Read: ${fileSystem.readFile("document.txt")}`);

    fileSystem.deleteFile("document.txt");

    console.log(`After deletion:`);
    console.log(fileSystem.report());
}


// ============================================================================
// 7. REAL FILE STORAGE
// ============================================================================

class SafeFileStorage {
    constructor(rootDirectory) {
        this.root = path.resolve(rootDirectory);
        fs.mkdirSync(this.root, { recursive: true });
    }

    safePath(relativePath) {
        const target = path.resolve(this.root, relativePath);

        // Prevent path traversal outside the storage root.
        const relative = path.relative(this.root, target);

        if (relative.startsWith("..") || path.isAbsolute(relative)) {
            throw new Error("Path escapes storage root");
        }

        return target;
    }

    write(relativePath, data) {
        const target = this.safePath(relativePath);

        fs.mkdirSync(path.dirname(target), { recursive: true });
        fs.writeFileSync(target, data);

        return this.metadata(relativePath);
    }

    read(relativePath) {
        const target = this.safePath(relativePath);
        return fs.readFileSync(target);
    }

    metadata(relativePath) {
        const target = this.safePath(relativePath);
        const stats = fs.statSync(target);

        const content = fs.readFileSync(target);
        const checksum = crypto
            .createHash("sha256")
            .update(content)
            .digest("hex");

        return {
            path: relativePath,
            size: stats.size,
            checksum,
            modifiedAt: stats.mtime.toISOString()
        };
    }

    delete(relativePath) {
        const target = this.safePath(relativePath);
        fs.unlinkSync(target);
    }
}

function demonstrateFileStorage() {
    section("7. FILE STORAGE");

    const directory = fs.mkdtempSync(
        path.join(os.tmpdir(), "storage-study-")
    );

    try {
        const storage = new SafeFileStorage(directory);
        const content = Buffer.from(
            "Persistent data managed through a filesystem."
        );

        const metadata = storage.write("documents/example.txt", content);

        console.log(metadata);
        console.log(`Read: ${storage.read("documents/example.txt").toString()}`);

        try {
            storage.read("../outside.txt");
        } catch (error) {
            console.log(`Path validation worked: ${error.message}`);
        }
    } finally {
        fs.rmSync(directory, { recursive: true, force: true });
    }
}


// ============================================================================
// 8. CACHE SIMULATION
// ============================================================================

class LRUCache {
    constructor(capacity) {
        if (!Number.isInteger(capacity) || capacity <= 0) {
            throw new RangeError("Cache capacity must be positive");
        }

        this.capacity = capacity;
        this.map = new Map();
        this.hits = 0;
        this.misses = 0;
    }

    get(key) {
        if (!this.map.has(key)) {
            this.misses++;
            return undefined;
        }

        const value = this.map.get(key);

        // Delete and reinsert so the key becomes most recently used.
        this.map.delete(key);
        this.map.set(key, value);

        this.hits++;
        return value;
    }

    set(key, value) {
        if (this.map.has(key)) {
            this.map.delete(key);
        }

        this.map.set(key, value);

        if (this.map.size > this.capacity) {
            const oldestKey = this.map.keys().next().value;
            this.map.delete(oldestKey);
        }
    }

    get hitRate() {
        const total = this.hits + this.misses;
        return total === 0 ? 0 : this.hits / total;
    }
}

function demonstrateCaching() {
    section("8. STORAGE CACHING");

    const cache = new LRUCache(3);
    const accesses = [1, 2, 3, 1, 2, 4, 1, 5, 1];

    for (const block of accesses) {
        const value = cache.get(block);

        if (value === undefined) {
            cache.set(block, `block-${block}`);
            console.log(`MISS ${block}`);
        } else {
            console.log(`HIT  ${block}`);
        }
    }

    console.log(`Hits: ${cache.hits}`);
    console.log(`Misses: ${cache.misses}`);
    console.log(`Hit rate: ${(cache.hitRate * 100).toFixed(2)}%`);

    console.log(`
Caching reduces storage latency by keeping frequently used data closer
to the application. It also introduces consistency and durability questions.
`);
}


// ============================================================================
// 9. HASH-BASED INTEGRITY
// ============================================================================

function demonstrateIntegrity() {
    section("9. DATA INTEGRITY");

    const original = Buffer.from("Important storage record");
    const originalHash = crypto
        .createHash("sha256")
        .update(original)
        .digest("hex");

    const changed = Buffer.from(original);
    changed[5] ^= 1;

    const changedHash = crypto
        .createHash("sha256")
        .update(changed)
        .digest("hex");

    console.log(`Original: ${originalHash}`);
    console.log(`Changed:  ${changedHash}`);
    console.log(`Match: ${originalHash === changedHash}`);

    console.log(`
Hashes can detect content changes. They do not recover corrupted data.
Recovery requires another valid copy, redundancy, or an error-correction
mechanism.
`);
}


// ============================================================================
// 10. ASYNCHRONOUS FILE I/O
// ============================================================================

async function demonstrateAsyncFileIO() {
    section("10. ASYNCHRONOUS FILE I/O");

    const directory = await fs.promises.mkdtemp(
        path.join(os.tmpdir(), "async-storage-study-")
    );

    const file = path.join(directory, "async.txt");

    try {
        await fs.promises.writeFile(
            file,
            "Asynchronous file I/O avoids blocking the JavaScript event loop."
        );

        const content = await fs.promises.readFile(file, "utf8");

        console.log(`Read asynchronously: ${content}`);

        console.log(`
Node.js exposes asynchronous filesystem APIs because application-level
programs often need to continue processing while I/O is pending.

Promises and async/await make asynchronous storage operations easier to
compose and handle than deeply nested callbacks.
`);
    } finally {
        await fs.promises.rm(directory, {
            recursive: true,
            force: true
        });
    }
}


// ============================================================================
// 11. WORKLOAD MODEL
// ============================================================================

function estimateWorkload({
    operationSizeBytes,
    operations,
    sequential,
    throughputMBps,
    iops
}) {
    if (operations <= 0) {
        throw new RangeError("Operations must be positive");
    }

    if (sequential) {
        const totalBytes = operationSizeBytes * operations;
        return totalBytes / (throughputMBps * 1024 * 1024);
    }

    return operations / iops;
}

function demonstrateWorkloads() {
    section("11. STORAGE WORKLOADS");

    const ssd = storageProfiles.SSD;

    const workloads = [
        {
            name: "Large sequential backup",
            operationSizeBytes: 1024 * 1024,
            operations: 1000,
            sequential: true
        },
        {
            name: "Small random database operations",
            operationSizeBytes: 4096,
            operations: 100000,
            sequential: false
        }
    ];

    for (const workload of workloads) {
        const seconds = estimateWorkload({
            ...workload,
            throughputMBps: ssd.sequentialReadMBps,
            iops: ssd.iops
        });

        console.log(`${workload.name}: ${seconds.toFixed(3)} seconds`);
    }

    console.log(`
Storage evaluation should consider:
- latency,
- throughput,
- IOPS,
- request size,
- queue depth,
- sequential versus random access,
- read/write ratio,
- concurrency,
- endurance,
- capacity,
- availability,
- durability,
- cost.
`);
}


// ============================================================================
// 12. RAID 0 STRIPING
// ============================================================================

function raid0Stripe(blocks, diskCount) {
    if (!Number.isInteger(diskCount) || diskCount <= 0) {
        throw new RangeError("Disk count must be positive");
    }

    const disks = Array.from({ length: diskCount }, () => []);

    blocks.forEach((block, index) => {
        disks[index % diskCount].push(block);
    });

    return disks;
}

function demonstrateRAID() {
    section("12. RAID 0 STRIPING");

    const blocks = ["A", "B", "C", "D", "E", "F", "G", "H"];
    const disks = raid0Stripe(blocks, 4);

    disks.forEach((disk, index) => {
        console.log(`Disk ${index}: ${disk.join(", ")}`);
    });

    console.log(`
RAID 0 distributes data across multiple devices.

Its main conceptual advantage is parallelism.
Its defining limitation is lack of redundancy.

RAID 1 uses mirroring.
RAID 5 uses distributed parity.
RAID 6 uses dual distributed parity.
RAID 10 combines mirroring and striping.

RAID improves selected availability or performance characteristics, but RAID
does not replace independent backups.
`);
}


// ============================================================================
// 13. FILESYSTEM SEMANTICS
// ============================================================================

function demonstrateAtomicReplacement() {
    section("13. FILESYSTEM ATOMIC REPLACEMENT PATTERN");

    const directory = fs.mkdtempSync(
        path.join(os.tmpdir(), "atomic-storage-study-")
    );

    const target = path.join(directory, "configuration.json");
    const temporary = path.join(directory, "configuration.tmp");

    try {
        fs.writeFileSync(
            temporary,
            JSON.stringify({
                version: 2,
                enabled: true
            })
        );

        // A same-filesystem rename is commonly used as part of an atomic
        // replacement pattern. Exact durability semantics depend on the
        // filesystem and required synchronization operations.
        fs.renameSync(temporary, target);

        console.log(fs.readFileSync(target, "utf8"));
    } finally {
        fs.rmSync(directory, { recursive: true, force: true });
    }
}


// ============================================================================
// 14. STORAGE SECURITY
// ============================================================================

function demonstrateSecurity() {
    section("14. STORAGE SECURITY");

    const secret = Buffer.from("Confidential storage record");

    const digest = crypto
        .createHash("sha256")
        .update(secret)
        .digest("hex");

    console.log(`Integrity digest: ${digest}`);

    console.log(`
Important controls:
- Authentication and authorization.
- Least-privilege permissions.
- Encryption at rest.
- Encryption in transit.
- Encryption-key management.
- Backup protection.
- Audit logging.
- Secure deletion policies.
- Path traversal prevention.
- Integrity verification.

A cryptographic hash is not encryption. Hashing helps detect content changes;
encryption protects confidentiality when correctly implemented.
`);
}


// ============================================================================
// 15. SIMPLE STORAGE SERVICE
// ============================================================================

class StorageService {
    constructor(rootDirectory) {
        this.storage = new SafeFileStorage(rootDirectory);
        this.index = new Map();
    }

    store(name, content) {
        if (typeof name !== "string" || name.trim() === "") {
            throw new TypeError("Object name cannot be empty");
        }

        if (!Buffer.isBuffer(content)) {
            throw new TypeError("Content must be a Buffer");
        }

        if (content.length > 10 * 1024 * 1024) {
            throw new RangeError("Object exceeds 10 MiB limit");
        }

        const metadata = this.storage.write(name, content);
        this.index.set(name, metadata.checksum);

        return metadata;
    }

    retrieve(name) {
        const content = this.storage.read(name);

        const actual = crypto
            .createHash("sha256")
            .update(content)
            .digest("hex");

        const expected = this.index.get(name);

        if (expected && expected !== actual) {
            throw new Error("Storage integrity verification failed");
        }

        return content;
    }

    delete(name) {
        this.storage.delete(name);
        this.index.delete(name);
    }
}

function demonstrateStorageService() {
    section("15. INTEGRATED STORAGE SERVICE");

    const directory = fs.mkdtempSync(
        path.join(os.tmpdir(), "storage-service-")
    );

    try {
        const service = new StorageService(directory);

        const metadata = service.store(
            "objects/record.bin",
            Buffer.from("Application-managed persistent data.")
        );

        console.log(metadata);
        console.log(
            `Verified content: ${service.retrieve(metadata.path).toString()}`
        );

        service.delete(metadata.path);

        try {
            service.retrieve(metadata.path);
        } catch (error) {
            console.log(`Deletion handled correctly: ${error.code || error.message}`);
        }
    } finally {
        fs.rmSync(directory, { recursive: true, force: true });
    }
}


// ============================================================================
// 16. MAIN
// ============================================================================

async function main() {
    demonstrateUnits();
    compareMedia();
    demonstrateHDD();
    demonstrateFlash();
    demonstrateBlockStorage();
    demonstrateSimpleFileSystem();
    demonstrateFileStorage();
    demonstrateCaching();
    demonstrateIntegrity();
    await demonstrateAsyncFileIO();
    demonstrateWorkloads();
    demonstrateRAID();
    demonstrateAtomicReplacement();
    demonstrateSecurity();
    demonstrateStorageService();

    section("17. KEY STORAGE DISTINCTIONS");

    console.log(`
HDD:
  Mechanical magnetic storage. Strong capacity-per-cost characteristics but
  comparatively high random-access latency.

SSD:
  Solid-state storage product using flash and a controller. Low latency and
  high parallelism compared with mechanical disks.

Flash:
  Non-volatile semiconductor technology. NAND flash is the dominant flash
  technology used in many mass-storage devices.

File storage:
  Named files and directories managed by a filesystem.

Block storage:
  Addressable logical blocks. A filesystem, database, or virtual-machine
  storage layer can consume those blocks.

The physical medium and logical storage abstraction are separate design layers.
`);
}

main().catch(error => {
    console.error("Storage demonstration failed:", error);
    process.exitCode = 1;
});
