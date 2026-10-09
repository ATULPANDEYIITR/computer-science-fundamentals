'use strict';

/*
 * Memory allocation simulator for contiguous variable-size partitions.
 *
 * This file focuses on JavaScript-specific modeling of allocator state,
 * event-driven allocation requests, asynchronous status reporting, and
 * policy evaluation. It does not depend on browser APIs or npm packages.
 */

class AllocationError extends Error {
    constructor(message) {
        super(message);
        this.name = 'AllocationError';
    }
}

const Strategy = Object.freeze({
    FIRST_FIT: 'first-fit',
    BEST_FIT: 'best-fit',
    WORST_FIT: 'worst-fit'
});

class MemoryBlock {
    constructor(start, size, allocated = false, owner = null) {
        this.start = start;
        this.size = size;
        this.allocated = allocated;
        this.owner = owner;
    }

    get end() {
        return this.start + this.size;
    }
}

class MemoryManager {
    constructor(totalSize, strategy = Strategy.FIRST_FIT) {
        if (!Number.isInteger(totalSize) || totalSize <= 0) {
            throw new TypeError('totalSize must be a positive integer');
        }

        this.totalSize = totalSize;
        this.strategy = strategy;
        this.blocks = [new MemoryBlock(0, totalSize)];
        this.listeners = new Set();
    }

    subscribe(listener) {
        if (typeof listener !== 'function') {
            throw new TypeError('listener must be a function');
        }

        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }

    emit(event) {
        for (const listener of this.listeners) {
            try {
                listener(Object.freeze({ ...event }));
            } catch (error) {
                // A monitoring listener must not break memory allocation.
                console.error('Memory event listener failed:', error.message);
            }
        }
    }

    validateRequest(owner, size) {
        if (typeof owner !== 'string' || owner.trim() === '') {
            throw new TypeError('owner must be a non-empty string');
        }

        if (!Number.isInteger(size) || size <= 0) {
            throw new TypeError('size must be a positive integer');
        }

        if (this.blocks.some(block => block.allocated && block.owner === owner)) {
            throw new AllocationError(`owner ${owner} already has memory`);
        }
    }

    candidates(size) {
        return this.blocks
            .map((block, index) => ({ block, index }))
            .filter(({ block }) => !block.allocated && block.size >= size);
    }

    chooseBlock(size) {
        const candidates = this.candidates(size);

        if (candidates.length === 0) {
            throw new AllocationError(
                `no contiguous region can satisfy ${size} units`
            );
        }

        if (this.strategy === Strategy.FIRST_FIT) {
            return candidates[0].index;
        }

        if (this.strategy === Strategy.BEST_FIT) {
            return candidates.reduce(
                (best, current) =>
                    current.block.size < best.block.size ? current : best
            ).index;
        }

        if (this.strategy === Strategy.WORST_FIT) {
            return candidates.reduce(
                (best, current) =>
                    current.block.size > best.block.size ? current : best
            ).index;
        }

        throw new Error(`unknown allocation strategy: ${this.strategy}`);
    }

    allocate(owner, size) {
        this.validateRequest(owner, size);

        const index = this.chooseBlock(size);
        const block = this.blocks[index];
        const address = block.start;

        if (block.size === size) {
            block.allocated = true;
            block.owner = owner;
        } else {
            this.blocks.splice(
                index,
                1,
                new MemoryBlock(address, size, true, owner),
                new MemoryBlock(address + size, block.size - size)
            );
        }

        this.emit({
            type: 'allocation',
            owner,
            size,
            address,
            strategy: this.strategy
        });

        return address;
    }

    release(owner) {
        const block = this.blocks.find(
            candidate => candidate.allocated && candidate.owner === owner
        );

        if (!block) {
            throw new AllocationError(`allocation ${owner} does not exist`);
        }

        block.allocated = false;
        block.owner = null;
        this.coalesce();

        this.emit({
            type: 'release',
            owner
        });
    }

    coalesce() {
        const merged = [];

        for (const block of this.blocks) {
            const previous = merged.at(-1);

            if (
                previous &&
                !previous.allocated &&
                !block.allocated &&
                previous.end === block.start
            ) {
                previous.size += block.size;
            } else {
                merged.push(block);
            }
        }

        this.blocks = merged;
    }

    compact() {
        const allocated = this.blocks.filter(block => block.allocated);
        const compacted = [];
        let cursor = 0;

        for (const oldBlock of allocated) {
            compacted.push(
                new MemoryBlock(cursor, oldBlock.size, true, oldBlock.owner)
            );
            cursor += oldBlock.size;
        }

        if (cursor < this.totalSize) {
            compacted.push(new MemoryBlock(cursor, this.totalSize - cursor));
        }

        this.blocks = compacted;

        this.emit({
            type: 'compaction',
            relocatedBlocks: allocated.length
        });
    }

    freeSpace() {
        return this.blocks
            .filter(block => !block.allocated)
            .reduce((total, block) => total + block.size, 0);
    }

    largestFreeBlock() {
        return Math.max(
            0,
            ...this.blocks
                .filter(block => !block.allocated)
                .map(block => block.size)
        );
    }

    externalFragmentation() {
        return this.freeSpace() - this.largestFreeBlock();
    }

    allocationSnapshot() {
        return this.blocks.map(block => ({
            start: block.start,
            end: block.end,
            size: block.size,
            state: block.allocated ? 'allocated' : 'free',
            owner: block.owner
        }));
    }
}

function printState(manager, title) {
    console.log(`\n${title}`);

    for (const block of manager.allocationSnapshot()) {
        console.log(
            `[${String(block.start).padStart(3)}-${String(block.end - 1).padStart(3)}]`,
            block.state.padEnd(9),
            block.owner ?? ''
        );
    }

    console.log(
        `free=${manager.freeSpace()} ` +
        `largest=${manager.largestFreeBlock()} ` +
        `external-fragmentation=${manager.externalFragmentation()}`
    );
}

function demonstrateEventDrivenAllocation() {
    console.log('=== Event-driven contiguous allocation ===');

    const manager = new MemoryManager(128, Strategy.BEST_FIT);

    manager.subscribe(event => {
        if (event.type === 'allocation') {
            console.log(
                `ALLOCATE ${event.owner} -> address ${event.address}, ` +
                `${event.size} units`
            );
        }

        if (event.type === 'release') {
            console.log(`RELEASE ${event.owner}`);
        }

        if (event.type === 'compaction') {
            console.log(
                `COMPACTION relocated ${event.relocatedBlocks} allocated blocks`
            );
        }
    });

    manager.allocate('WebWorker', 24);
    manager.allocate('ImageProcessor', 36);
    manager.allocate('ReportGenerator', 18);
    printState(manager, 'Initial allocation');

    manager.release('ImageProcessor');
    printState(manager, 'After release');

    try {
        manager.allocate('LargeCache', 45);
    } catch (error) {
        console.log(`Large allocation rejected: ${error.message}`);
    }

    manager.compact();
    manager.allocate('LargeCache', 45);
    printState(manager, 'After compaction and retry');
}

function comparePolicies() {
    console.log('\n=== Allocation policy comparison ===');

    for (const strategy of Object.values(Strategy)) {
        const manager = new MemoryManager(100, strategy);

        manager.allocate('A', 20);
        manager.allocate('B', 30);
        manager.allocate('C', 10);
        manager.allocate('D', 15);

        manager.release('B');
        manager.release('D');

        let result = 'failed';

        try {
            manager.allocate('X', 12);
            result = 'allocated';
        } catch {
            // The comparison intentionally records policy behavior.
        }

        console.log(
            `${strategy.padEnd(10)} -> ${result}, ` +
            `largest-free=${manager.largestFreeBlock()}, ` +
            `fragmentation=${manager.externalFragmentation()}`
        );
    }
}

function demonstrateFixedPartitionWaste() {
    console.log('\n=== Fixed partition internal fragmentation ===');

    const partitionSize = 32;
    const requests = [3, 17, 25, 31];

    let waste = 0;

    for (const request of requests) {
        waste += partitionSize - request;
    }

    console.log(`partition-size=${partitionSize}`);
    console.log(`requested=${requests.reduce((a, b) => a + b, 0)}`);
    console.log(`internal-fragmentation=${waste}`);
}

async function asynchronousWorkload() {
    console.log('\n=== Asynchronous workload ===');

    const manager = new MemoryManager(256, Strategy.FIRST_FIT);

    const operations = [
        { delay: 20, type: 'allocate', owner: 'API', size: 40 },
        { delay: 40, type: 'allocate', owner: 'Search', size: 70 },
        { delay: 60, type: 'allocate', owner: 'Analytics', size: 50 },
        { delay: 80, type: 'release', owner: 'Search' },
        { delay: 100, type: 'allocate', owner: 'Batch', size: 60 }
    ];

    for (const operation of operations) {
        await new Promise(resolve => setTimeout(resolve, operation.delay));

        try {
            if (operation.type === 'allocate') {
                manager.allocate(operation.owner, operation.size);
            } else {
                manager.release(operation.owner);
            }
        } catch (error) {
            console.log(`Operation rejected: ${error.message}`);
        }
    }

    printState(manager, 'Final asynchronous state');
}

function main() {
    demonstrateEventDrivenAllocation();
    comparePolicies();
    demonstrateFixedPartitionWaste();

    asynchronousWorkload().catch(error => {
        console.error('Workload failed:', error);
        process.exitCode = 1;
    });
}

main();
