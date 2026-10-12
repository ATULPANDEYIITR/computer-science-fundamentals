'use strict';

/*
 * File System Internals in JavaScript
 *
 * This Node.js program provides an event-driven simulation of filesystem
 * lifecycle events. It focuses on a different perspective from the Python
 * implementation: operations emit events, listeners observe lifecycle changes,
 * and policy code evaluates whether a mounted filesystem may safely proceed.
 *
 * The simulation covers:
 * - inode metadata
 * - directory name-to-inode mappings
 * - block allocation
 * - direct/indirect file block references
 * - journaling
 * - crash recovery
 * - mount validation
 * - event-driven observability
 */

const { EventEmitter } = require('events');
const crypto = require('crypto');

const FileType = Object.freeze({
    FILE: 'file',
    DIRECTORY: 'directory'
});

class FileSystemError extends Error {}
class AllocationError extends FileSystemError {}
class MountError extends FileSystemError {}

class Inode {
    constructor(number, type, mode, parent = null) {
        this.number = number;
        this.type = type;
        this.mode = mode;
        this.parent = parent;
        this.size = 0;
        this.linkCount = type === FileType.DIRECTORY ? 2 : 1;
        this.directBlocks = [];
        this.indirectBlock = null;
        this.indirectEntries = [];
        this.atime = Date.now();
        this.mtime = this.atime;
        this.ctime = this.atime;
    }

    get dataBlocks() {
        return [...this.directBlocks, ...this.indirectEntries];
    }
}

class JournalTransaction {
    constructor(id, description, snapshot) {
        this.id = id;
        this.description = description;
        this.snapshot = structuredClone(snapshot);
        this.committed = false;
        this.timestamp = new Date().toISOString();
    }
}

class FileSystem extends EventEmitter {
    static MAGIC = 'JS-FS-INTERNALS';
    static DIRECT_LIMIT = 4;

    constructor({
        blockSize = 64,
        totalBlocks = 100,
        inodeLimit = 30,
        journalCapacity = 20
    } = {}) {
        super();

        if (blockSize <= 0 || totalBlocks < 40 || inodeLimit < 4) {
            throw new RangeError('Filesystem geometry is too small or invalid');
        }

        this.blockSize = blockSize;
        this.totalBlocks = totalBlocks;
        this.inodeLimit = inodeLimit;
        this.journalCapacity = journalCapacity;
        this.journal = [];
        this.nextTransactionId = 1;
        this.nextInode = 1;
        this.mounted = false;
        this.clean = true;

        this.blocks = Array.from(
            { length: totalBlocks },
            () => Buffer.alloc(blockSize)
        );

        this.metadataBlocks = new Set(
            Array.from({ length: 12 }, (_, index) => index)
        );
        this.allocatedBlocks = new Set(this.metadataBlocks);

        this.inodes = new Map();
        this.directories = new Map();

        const root = this.allocateInode(FileType.DIRECTORY, 0o755, null);
        if (root.number !== 1) {
            throw new FileSystemError('Root inode allocation failed');
        }

        root.parent = root.number;
        this.directories.set(root.number, new Map([
            ['.', root.number],
            ['..', root.number]
        ]));

        this.superblock = {
            magic: FileSystem.MAGIC,
            blockSize,
            totalBlocks,
            inodeLimit,
            rootInode: root.number,
            journalStart: 8,
            journalBlocks: journalCapacity,
            generation: 1
        };
    }

    allocateInode(type, mode, parent) {
        if (this.inodes.size >= this.inodeLimit) {
            throw new AllocationError('Inode table is full');
        }

        const inode = new Inode(this.nextInode++, type, mode, parent);
        this.inodes.set(inode.number, inode);

        if (type === FileType.DIRECTORY) {
            this.directories.set(inode.number, new Map());
        }

        this.emit('inodeAllocated', {
            inode: inode.number,
            type
        });

        return inode;
    }

    allocateBlock() {
        for (let block = 0; block < this.totalBlocks; block++) {
            if (!this.allocatedBlocks.has(block)) {
                this.allocatedBlocks.add(block);
                this.emit('blockAllocated', { block });
                return block;
            }
        }

        throw new AllocationError('No free blocks remain');
    }

    freeBlock(block) {
        if (this.metadataBlocks.has(block)) {
            throw new FileSystemError(
                `Metadata block ${block} cannot be returned to the data allocator`
            );
        }

        this.allocatedBlocks.delete(block);
        this.emit('blockFreed', { block });
    }

    beginTransaction(description) {
        if (this.journal.length >= this.journalCapacity) {
            throw new FileSystemError('Journal capacity exhausted');
        }

        const transaction = new JournalTransaction(
            this.nextTransactionId++,
            description,
            this.snapshot()
        );

        this.journal.push(transaction);
        this.clean = false;
        this.emit('journalBegin', {
            id: transaction.id,
            description
        });

        return transaction;
    }

    commit(transaction) {
        transaction.committed = true;
        this.clean = true;

        this.emit('journalCommit', {
            id: transaction.id,
            description: transaction.description
        });

        this.journal = this.journal.filter(
            record => record.id !== transaction.id
        );
    }

    snapshot() {
        return {
            inodes: structuredClone(
                Array.from(this.inodes.entries()).map(([id, inode]) => [id, inode])
            ),
            directories: structuredClone(
                Array.from(this.directories.entries()).map(
                    ([id, directory]) => [id, Array.from(directory.entries())]
                )
            ),
            blocks: this.blocks.map(block => Buffer.from(block).toString('base64')),
            allocatedBlocks: [...this.allocatedBlocks],
            nextInode: this.nextInode,
            superblock: structuredClone(this.superblock)
        };
    }

    restoreSnapshot(snapshot) {
        this.inodes = new Map(snapshot.inodes);
        this.directories = new Map(
            snapshot.directories.map(
                ([id, entries]) => [id, new Map(entries)]
            )
        );
        this.blocks = snapshot.blocks.map(
            value => Buffer.from(value, 'base64')
        );
        this.allocatedBlocks = new Set(snapshot.allocatedBlocks);
        this.nextInode = snapshot.nextInode;
        this.superblock = structuredClone(snapshot.superblock);
    }

    recover() {
        const pending = this.journal.filter(record => record.committed);

        for (const transaction of pending) {
            this.restoreSnapshot(transaction.snapshot);
            this.emit('journalReplay', {
                id: transaction.id,
                description: transaction.description
            });
        }

        this.journal = [];
        this.clean = true;
    }

    mount() {
        if (this.mounted) {
            return;
        }

        if (this.superblock.magic !== FileSystem.MAGIC) {
            throw new MountError('Invalid filesystem magic');
        }

        if (this.superblock.blockSize !== this.blockSize) {
            throw new MountError('Block-size mismatch');
        }

        if (this.superblock.totalBlocks !== this.totalBlocks) {
            throw new MountError('Filesystem size mismatch');
        }

        if (!this.clean) {
            this.recover();
        }

        this.verifyConsistency();
        this.mounted = true;

        this.emit('mounted', {
            generation: this.superblock.generation
        });
    }

    unmount() {
        if (!this.mounted) {
            return;
        }

        this.verifyConsistency();
        this.mounted = false;
        this.clean = true;
        this.emit('unmounted');
    }

    crash() {
        this.mounted = false;
        this.clean = false;
        this.emit('crash');

        /*
         * A real crash does not execute normal shutdown code. Journal records
         * are intentionally retained because they represent durable recovery
         * information rather than ordinary process memory.
         */
    }

    resolve(path) {
        this.requireMounted();

        if (!path.startsWith('/')) {
            throw new FileSystemError('Only absolute paths are accepted');
        }

        const components = path.split('/').filter(Boolean);
        let current = this.superblock.rootInode;

        for (const component of components) {
            if (component === '.') {
                continue;
            }

            if (component === '..') {
                current = this.inodes.get(current).parent ?? current;
                continue;
            }

            const directory = this.directories.get(current);
            if (!directory) {
                throw new FileSystemError(`Inode ${current} is not a directory`);
            }

            if (!directory.has(component)) {
                throw new FileSystemError(`Path does not exist: ${path}`);
            }

            current = directory.get(component);
        }

        return current;
    }

    parentAndName(path) {
        const components = path.split('/').filter(Boolean);

        if (components.length === 0) {
            throw new FileSystemError('Root has no parent entry');
        }

        const name = components.pop();
        const parentPath = components.length
            ? `/${components.join('/')}`
            : '/';

        return {
            parent: this.resolve(parentPath),
            name
        };
    }

    createFile(path, mode = 0o644) {
        this.requireMounted();

        const { parent, name } = this.parentAndName(path);
        this.validateName(name);

        const directory = this.directories.get(parent);
        if (directory.has(name)) {
            throw new FileSystemError(`Entry already exists: ${path}`);
        }

        const transaction = this.beginTransaction(`create ${path}`);

        const inode = this.allocateInode(FileType.FILE, mode, parent);
        directory.set(name, inode.number);

        this.inodes.get(parent).mtime = Date.now();
        this.inodes.get(parent).ctime = Date.now();

        this.commit(transaction);
        return inode.number;
    }

    mkdir(path, mode = 0o755) {
        this.requireMounted();

        const { parent, name } = this.parentAndName(path);
        this.validateName(name);

        const parentDirectory = this.directories.get(parent);
        if (parentDirectory.has(name)) {
            throw new FileSystemError(`Entry already exists: ${path}`);
        }

        const transaction = this.beginTransaction(`mkdir ${path}`);
        const inode = this.allocateInode(FileType.DIRECTORY, mode, parent);

        this.directories.set(inode.number, new Map([
            ['.', inode.number],
            ['..', parent]
        ]));

        parentDirectory.set(name, inode.number);
        this.inodes.get(parent).linkCount++;
        this.inodes.get(parent).mtime = Date.now();

        this.commit(transaction);
        return inode.number;
    }

    writeFile(path, text, offset = 0) {
        this.requireMounted();

        if (!Number.isInteger(offset) || offset < 0) {
            throw new RangeError('Offset must be a non-negative integer');
        }

        const inode = this.inodes.get(this.resolve(path));
        if (!inode || inode.type !== FileType.FILE) {
            throw new FileSystemError('Path is not a regular file');
        }

        const payload = Buffer.from(text, 'utf8');
        if (payload.length === 0) {
            return 0;
        }

        const end = offset + payload.length;
        const neededBlocks = Math.ceil(end / this.blockSize);

        const transaction = this.beginTransaction(
            `write ${payload.length} bytes to ${path}`
        );

        while (inode.dataBlocks.length < neededBlocks) {
            const dataBlock = this.allocateBlock();

            if (inode.directBlocks.length < FileSystem.DIRECT_LIMIT) {
                inode.directBlocks.push(dataBlock);
            } else {
                if (inode.indirectBlock === null) {
                    inode.indirectBlock = this.allocateBlock();
                }
                inode.indirectEntries.push(dataBlock);
            }
        }

        for (let logical = 0; logical < neededBlocks; logical++) {
            const physical = inode.dataBlocks[logical];
            const block = Buffer.from(this.blocks[physical]);

            const blockStart = logical * this.blockSize;
            const start = Math.max(offset, blockStart);
            const endOfWrite = Math.min(end, blockStart + this.blockSize);

            if (start < endOfWrite) {
                const sourceStart = start - offset;
                const sourceEnd = endOfWrite - offset;
                const targetStart = start - blockStart;

                payload.copy(
                    block,
                    targetStart,
                    sourceStart,
                    sourceEnd
                );
            }

            this.blocks[physical] = block;
        }

        inode.size = Math.max(inode.size, end);
        inode.mtime = Date.now();
        inode.ctime = Date.now();

        this.commit(transaction);
        this.emit('fileWritten', {
            path,
            inode: inode.number,
            bytes: payload.length
        });

        return payload.length;
    }

    readFile(path, offset = 0, length = null) {
        this.requireMounted();

        const inode = this.inodes.get(this.resolve(path));
        if (!inode || inode.type !== FileType.FILE) {
            throw new FileSystemError('Path is not a regular file');
        }

        if (offset < 0 || !Number.isInteger(offset)) {
            throw new RangeError('Invalid read offset');
        }

        if (offset >= inode.size) {
            return '';
        }

        const actualLength = length === null
            ? inode.size - offset
            : Math.min(length, inode.size - offset);

        if (actualLength < 0) {
            throw new RangeError('Invalid read length');
        }

        const result = Buffer.alloc(actualLength);
        let copied = 0;

        while (copied < actualLength) {
            const absoluteOffset = offset + copied;
            const logicalBlock = Math.floor(
                absoluteOffset / this.blockSize
            );
            const physicalBlock = inode.dataBlocks[logicalBlock];
            const source = this.blocks[physicalBlock];

            const sourceOffset = absoluteOffset % this.blockSize;
            const amount = Math.min(
                source.length - sourceOffset,
                actualLength - copied
            );

            source.copy(result, copied, sourceOffset, sourceOffset + amount);
            copied += amount;
        }

        inode.atime = Date.now();
        return result.toString('utf8');
    }

    truncate(path, newSize) {
        this.requireMounted();

        if (!Number.isInteger(newSize) || newSize < 0) {
            throw new RangeError('newSize must be non-negative');
        }

        const inode = this.inodes.get(this.resolve(path));
        if (!inode || inode.type !== FileType.FILE) {
            throw new FileSystemError('Path is not a regular file');
        }

        const requiredBlocks = Math.ceil(newSize / this.blockSize);
        const transaction = this.beginTransaction(
            `truncate ${path} to ${newSize}`
        );

        while (inode.dataBlocks.length > requiredBlocks) {
            if (inode.indirectEntries.length > 0) {
                const block = inode.indirectEntries.pop();
                this.freeBlock(block);
            } else {
                const block = inode.directBlocks.pop();
                this.freeBlock(block);
            }
        }

        if (
            inode.indirectEntries.length === 0 &&
            inode.indirectBlock !== null
        ) {
            this.freeBlock(inode.indirectBlock);
            inode.indirectBlock = null;
        }

        inode.size = newSize;
        inode.mtime = Date.now();
        inode.ctime = Date.now();

        this.commit(transaction);
    }

    listDirectory(path = '/') {
        const inodeNumber = this.resolve(path);
        const directory = this.directories.get(inodeNumber);

        if (!directory) {
            throw new FileSystemError('Not a directory');
        }

        return Object.fromEntries(directory.entries());
    }

    stat(path) {
        const inode = this.inodes.get(this.resolve(path));
        return {
            number: inode.number,
            type: inode.type,
            mode: `0${inode.mode.toString(8)}`,
            size: inode.size,
            linkCount: inode.linkCount,
            directBlocks: [...inode.directBlocks],
            indirectBlock: inode.indirectBlock,
            indirectEntries: [...inode.indirectEntries]
        };
    }

    verifyConsistency() {
        if (!this.inodes.has(this.superblock.rootInode)) {
            throw new FileSystemError('Root inode is missing');
        }

        const referencedBlocks = new Set(this.metadataBlocks);

        for (const inode of this.inodes.values()) {
            if (inode.type === FileType.FILE) {
                const expected = Math.ceil(inode.size / this.blockSize);

                if (inode.dataBlocks.length < expected) {
                    throw new FileSystemError(
                        `Inode ${inode.number} does not contain enough blocks`
                    );
                }
            }

            for (const block of inode.dataBlocks) {
                if (this.metadataBlocks.has(block)) {
                    throw new FileSystemError(
                        `Data inode references metadata block ${block}`
                    );
                }

                if (referencedBlocks.has(block)) {
                    throw new FileSystemError(
                        `Block ${block} is multiply allocated`
                    );
                }

                referencedBlocks.add(block);
            }

            if (inode.indirectBlock !== null) {
                if (referencedBlocks.has(inode.indirectBlock)) {
                    throw new FileSystemError(
                        `Indirect block ${inode.indirectBlock} is multiply allocated`
                    );
                }
                referencedBlocks.add(inode.indirectBlock);
            }
        }

        for (const [inodeNumber, directory] of this.directories.entries()) {
            if (!directory.has('.') || !directory.has('..')) {
                if (inodeNumber !== this.superblock.rootInode) {
                    throw new FileSystemError(
                        `Directory ${inodeNumber} is missing dot entries`
                    );
                }
            }

            for (const [name, referencedInode] of directory.entries()) {
                if (!this.inodes.has(referencedInode)) {
                    throw new FileSystemError(
                        `${name} references missing inode ${referencedInode}`
                    );
                }
            }
        }

        return true;
    }

    freeSpace() {
        return this.totalBlocks - this.allocatedBlocks.size;
    }

    allocationDigest() {
        const hash = crypto.createHash('sha256');

        for (const block of [...this.allocatedBlocks].sort((a, b) => a - b)) {
            hash.update(`${block}:`);
        }

        return hash.digest('hex');
    }

    validateName(name) {
        if (
            !name ||
            name === '.' ||
            name === '..' ||
            name.includes('/') ||
            Buffer.byteLength(name, 'utf8') > 255
        ) {
            throw new FileSystemError('Invalid directory entry name');
        }
    }

    requireMounted() {
        if (!this.mounted) {
            throw new MountError('Filesystem is not mounted');
        }
    }
}

function attachAuditLog(fs) {
    fs.on('mounted', event => {
        console.log(`[mount] generation=${event.generation}`);
    });

    fs.on('journalBegin', event => {
        console.log(
            `[journal] begin #${event.id}: ${event.description}`
        );
    });

    fs.on('journalCommit', event => {
        console.log(
            `[journal] commit #${event.id}: ${event.description}`
        );
    });

    fs.on('journalReplay', event => {
        console.log(
            `[journal] replay #${event.id}: ${event.description}`
        );
    });

    fs.on('blockAllocated', event => {
        console.log(`[allocator] block ${event.block} allocated`);
    });

    fs.on('blockFreed', event => {
        console.log(`[allocator] block ${event.block} freed`);
    });
}

function main() {
    const fs = new FileSystem({
        blockSize: 32,
        totalBlocks: 90,
        inodeLimit: 20,
        journalCapacity: 10
    });

    attachAuditLog(fs);

    fs.mount();

    console.log('\n--- directory and inode lifecycle ---');
    fs.mkdir('/services');
    fs.mkdir('/services/api');
    fs.createFile('/services/api/request.log');

    fs.writeFile(
        '/services/api/request.log',
        'GET /orders 200\nPOST /orders 201\n'
    );

    console.log(fs.stat('/services/api/request.log'));
    console.log(fs.listDirectory('/services/api'));
    console.log(fs.readFile('/services/api/request.log'));

    console.log('\n--- indirect allocation ---');
    fs.writeFile(
        '/services/api/request.log',
        'X'.repeat(180),
        32
    );
    console.log(fs.stat('/services/api/request.log'));

    console.log('\n--- crash and journal recovery ---');
    fs.writeFile('/services/api/request.log', 'journal-visible-data');
    fs.crash();
    fs.mount();

    console.log(fs.readFile('/services/api/request.log'));
    console.log(`free blocks: ${fs.freeSpace()}`);
    console.log(`allocation digest: ${fs.allocationDigest()}`);

    console.log('\n--- truncation ---');
    fs.truncate('/services/api/request.log', 20);
    console.log(fs.stat('/services/api/request.log'));

    fs.verifyConsistency();
    console.log('\nFilesystem consistency check passed.');

    fs.unmount();
}

try {
    main();
} catch (error) {
    console.error(`${error.name}: ${error.message}`);
    process.exitCode = 1;
}
