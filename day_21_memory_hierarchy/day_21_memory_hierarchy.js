/*
 * MEMORY HIERARCHY
 * JavaScript companion implementation
 *
 * This file demonstrates memory-hierarchy concepts through executable
 * examples, including locality, cache simulation, LRU replacement,
 * asynchronous storage behavior, typed arrays, memory usage, and a
 * practical data-processing workload.
 *
 * Run with:
 *     node memory-hierarchy.js
 *
 * No external npm packages are required.
 */

"use strict";

const { performance } = require("node:perf_hooks");

// ============================================================================
// 1. BASIC CONCEPTS
// ============================================================================

function section(title) {
    console.log("\n" + "=".repeat(78));
    console.log(title);
    console.log("=".repeat(78));
}

function explainHierarchy() {
    section("1. Memory hierarchy in a JavaScript runtime");

    console.log(`
A processor normally accesses several levels of storage:

    Registers
       ↓
    CPU caches
       ↓
    RAM
       ↓
    SSD/HDD

JavaScript programs do not normally access physical registers or CPU cache
lines directly. The JavaScript engine, operating system, and CPU cooperate
to execute the program.

JavaScript nevertheless provides useful ways to study memory behavior:

    - arrays and typed arrays
    - object references
    - contiguous binary storage
    - allocation and garbage collection
    - data locality
    - asynchronous file or network I/O
    - high-level data structures

The CPU cache remains below the language abstraction.
`);
}


// ============================================================================
// 2. LOCALITY
// ============================================================================

function sequentialSum(array) {
    let total = 0;

    for (let index = 0; index < array.length; index++) {
        total += array[index];
    }

    return total;
}

function stridedSum(array, stride) {
    let total = 0;

    for (let index = 0; index < array.length; index += stride) {
        total += array[index];
    }

    return total;
}

function randomSum(array, seed = 12345) {
    // A deterministic pseudo-random generator makes the experiment repeatable.
    let state = seed >>> 0;

    function nextRandom() {
        state = (1664525 * state + 1013904223) >>> 0;
        return state / 0x100000000;
    }

    const indexes = Array.from({ length: array.length }, (_, index) => index);

    // Fisher-Yates shuffle.
    for (let index = indexes.length - 1; index > 0; index--) {
        const randomIndex = Math.floor(nextRandom() * (index + 1));
        [indexes[index], indexes[randomIndex]] =
            [indexes[randomIndex], indexes[index]];
    }

    let total = 0;

    for (const index of indexes) {
        total += array[index];
    }

    return total;
}

function demonstrateLocality() {
    section("2. Temporal and spatial locality");

    const data = new Float64Array(200_000);

    for (let index = 0; index < data.length; index++) {
        data[index] = index;
    }

    let start = performance.now();
    const sequentialResult = sequentialSum(data);
    const sequentialTime = performance.now() - start;

    start = performance.now();
    const stridedResult = stridedSum(data, 16);
    const stridedTime = performance.now() - start;

    start = performance.now();
    const randomResult = randomSum(data);
    const randomTime = performance.now() - start;

    console.log(`Sequential result: ${sequentialResult}`);
    console.log(`Stride-16 result:  ${stridedResult}`);
    console.log(`Random result:     ${randomResult}`);

    console.log(`Sequential time: ${sequentialTime.toFixed(3)} ms`);
    console.log(`Stride-16 time:  ${stridedTime.toFixed(3)} ms`);
    console.log(`Random time:     ${randomTime.toFixed(3)} ms`);

    console.log(`
Typed arrays provide compact binary storage, but JavaScript timing is
influenced by the JavaScript engine, JIT compilation, garbage collection,
CPU caches, operating-system scheduling, and other factors.

The experiment demonstrates why access patterns matter, not a universal
hardware-cache latency measurement.
`);
}


// ============================================================================
// 3. CACHE LINE CONCEPT
// ============================================================================

class DirectMappedCache {
    constructor(lineCount) {
        if (!Number.isInteger(lineCount) || lineCount <= 0) {
            throw new RangeError("lineCount must be a positive integer");
        }

        this.lineCount = lineCount;
        this.lines = Array.from(
            { length: lineCount },
            () => ({ valid: false, tag: null, block: null })
        );

        this.hits = 0;
        this.misses = 0;
    }

    access(blockNumber) {
        if (!Number.isInteger(blockNumber) || blockNumber < 0) {
            throw new RangeError("blockNumber must be a non-negative integer");
        }

        const index = blockNumber % this.lineCount;
        const tag = Math.floor(blockNumber / this.lineCount);
        const line = this.lines[index];

        if (line.valid && line.tag === tag) {
            this.hits++;
            return {
                hit: true,
                index,
                tag
            };
        }

        this.misses++;

        line.valid = true;
        line.tag = tag;
        line.block = blockNumber;

        return {
            hit: false,
            index,
            tag
        };
    }

    get hitRate() {
        const accesses = this.hits + this.misses;
        return accesses === 0 ? 0 : this.hits / accesses;
    }
}

function demonstrateDirectMappedCache() {
    section("3. Direct-mapped cache");

    const cache = new DirectMappedCache(4);
    const accesses = [0, 4, 0, 8, 4, 0, 12, 0, 16];

    for (const block of accesses) {
        const result = cache.access(block);

        console.log(
            `Block ${block.toString().padStart(2)} -> ` +
            `line ${result.index}, tag ${result.tag}, ` +
            `${result.hit ? "HIT" : "MISS"}`
        );
    }

    console.log(`Hits: ${cache.hits}`);
    console.log(`Misses: ${cache.misses}`);
    console.log(`Hit rate: ${(cache.hitRate * 100).toFixed(2)}%`);
}


// ============================================================================
// 4. SET-ASSOCIATIVE CACHE WITH LRU
// ============================================================================

class SetAssociativeCache {
    constructor(setCount, ways) {
        if (!Number.isInteger(setCount) || setCount <= 0) {
            throw new RangeError("setCount must be positive");
        }

        if (!Number.isInteger(ways) || ways <= 0) {
            throw new RangeError("ways must be positive");
        }

        this.setCount = setCount;
        this.ways = ways;
        this.sets = Array.from({ length: setCount }, () => []);
        this.clock = 0;
        this.hits = 0;
        this.misses = 0;
        this.evictions = 0;
    }

    access(blockNumber) {
        if (!Number.isInteger(blockNumber) || blockNumber < 0) {
            throw new RangeError("blockNumber must be non-negative");
        }

        this.clock++;

        const setIndex = blockNumber % this.setCount;
        const tag = Math.floor(blockNumber / this.setCount);
        const targetSet = this.sets[setIndex];

        const existing = targetSet.find(entry => entry.tag === tag);

        if (existing) {
            this.hits++;
            existing.lastUsed = this.clock;
            return true;
        }

        this.misses++;

        if (targetSet.length >= this.ways) {
            let oldestIndex = 0;

            for (let index = 1; index < targetSet.length; index++) {
                if (
                    targetSet[index].lastUsed <
                    targetSet[oldestIndex].lastUsed
                ) {
                    oldestIndex = index;
                }
            }

            targetSet.splice(oldestIndex, 1);
            this.evictions++;
        }

        targetSet.push({
            tag,
            lastUsed: this.clock
        });

        return false;
    }

    get hitRate() {
        const accesses = this.hits + this.misses;
        return accesses === 0 ? 0 : this.hits / accesses;
    }
}

function demonstrateAssociativity() {
    section("4. Set associativity and LRU replacement");

    const cache = new SetAssociativeCache(2, 2);
    const accesses = [0, 2, 4, 0, 2, 4, 0];

    for (const block of accesses) {
        console.log(
            `Block ${block}: ${cache.access(block) ? "HIT" : "MISS"}`
        );
    }

    console.log(`Hits: ${cache.hits}`);
    console.log(`Misses: ${cache.misses}`);
    console.log(`Evictions: ${cache.evictions}`);
    console.log(`Hit rate: ${(cache.hitRate * 100).toFixed(2)}%`);
}


// ============================================================================
// 5. LRU MEMORY CACHE
// ============================================================================

class LRUCache {
    constructor(capacity) {
        if (!Number.isInteger(capacity) || capacity <= 0) {
            throw new RangeError("capacity must be positive");
        }

        this.capacity = capacity;
        this.entries = new Map();
        this.hits = 0;
        this.misses = 0;
    }

    get(key) {
        if (!this.entries.has(key)) {
            this.misses++;
            return undefined;
        }

        const value = this.entries.get(key);

        // JavaScript Map preserves insertion order.
        // Delete + set moves the key to the newest position.
        this.entries.delete(key);
        this.entries.set(key, value);

        this.hits++;
        return value;
    }

    set(key, value) {
        if (this.entries.has(key)) {
            this.entries.delete(key);
        } else if (this.entries.size >= this.capacity) {
            const oldestKey = this.entries.keys().next().value;
            this.entries.delete(oldestKey);
        }

        this.entries.set(key, value);
    }

    get hitRate() {
        const total = this.hits + this.misses;
        return total === 0 ? 0 : this.hits / total;
    }
}

function demonstrateLRUCache() {
    section("5. Application-level LRU cache");

    const cache = new LRUCache(3);

    cache.set("customer:1", { name: "Asha", balance: 5000 });
    cache.set("customer:2", { name: "Ravi", balance: 7000 });
    cache.set("customer:3", { name: "Meera", balance: 9000 });

    console.log("Lookup customer:1:", cache.get("customer:1"));

    cache.set("customer:4", { name: "Kabir", balance: 11000 });

    console.log(
        "Lookup customer:2 after eviction:",
        cache.get("customer:2")
    );

    console.log(`Hit rate: ${(cache.hitRate * 100).toFixed(2)}%`);
}


// ============================================================================
// 6. CACHE MISS TYPES
// ============================================================================

function explainCacheMisses() {
    section("6. Cache miss classification");

    console.log(`
Compulsory miss:
    The first access to a block has no cached copy.

Capacity miss:
    The working set is too large for the cache.

Conflict miss:
    Several blocks compete for the same cache location.

These categories help diagnose why a cache is not achieving a high hit rate.
`);
}


// ============================================================================
// 7. TYPED ARRAYS AND MEMORY REPRESENTATION
// ============================================================================

function demonstrateTypedArrays() {
    section("7. Typed arrays and compact data representation");

    const integerValues = new Int32Array([10, 20, 30, 40]);
    const bytes = new Uint8Array(integerValues.buffer);

    console.log("Int32 values:", Array.from(integerValues));
    console.log("Underlying bytes:", Array.from(bytes));

    console.log(`
A typed array gives JavaScript code a predictable element type and compact
binary representation.

The exact physical cache behavior remains controlled by the JavaScript engine
and hardware, but contiguous typed-array data is useful for data-intensive
workloads because it represents data more compactly than many object-heavy
structures.
`);
}


// ============================================================================
// 8. DATA LAYOUT
// ============================================================================

function sumObjectRecords(records) {
    let total = 0;

    for (const record of records) {
        total += record.value;
    }

    return total;
}

function sumTypedValues(values) {
    let total = 0;

    for (let index = 0; index < values.length; index++) {
        total += values[index];
    }

    return total;
}

function demonstrateDataLayout() {
    section("8. Data layout and locality");

    const count = 100_000;

    const objects = Array.from(
        { length: count },
        (_, index) => ({ value: index })
    );

    const typedValues = new Float64Array(count);

    for (let index = 0; index < count; index++) {
        typedValues[index] = index;
    }

    let start = performance.now();
    const objectResult = sumObjectRecords(objects);
    const objectTime = performance.now() - start;

    start = performance.now();
    const typedResult = sumTypedValues(typedValues);
    const typedTime = performance.now() - start;

    console.log(`Object result: ${objectResult}`);
    console.log(`Typed result:  ${typedResult}`);
    console.log(`Object time:   ${objectTime.toFixed(3)} ms`);
    console.log(`Typed time:    ${typedTime.toFixed(3)} ms`);

    console.log(`
The result is not a universal benchmark. Object layout depends on the
JavaScript engine. Typed arrays provide a more explicit compact binary layout.
`);
}


// ============================================================================
// 9. VIRTUAL MEMORY CONCEPT
// ============================================================================

class PageTable {
    constructor(pageSize = 4096) {
        if (
            !Number.isInteger(pageSize) ||
            pageSize <= 0 ||
            (pageSize & (pageSize - 1)) !== 0
        ) {
            throw new RangeError(
                "pageSize must be a positive power of two"
            );
        }

        this.pageSize = pageSize;
        this.entries = new Map();
    }

    mapPage(virtualPage, physicalFrame) {
        if (virtualPage < 0 || physicalFrame < 0) {
            throw new RangeError("page and frame must be non-negative");
        }

        this.entries.set(virtualPage, physicalFrame);
    }

    translate(virtualAddress) {
        if (!Number.isSafeInteger(virtualAddress) || virtualAddress < 0) {
            throw new RangeError("invalid virtual address");
        }

        const virtualPage = Math.floor(
            virtualAddress / this.pageSize
        );

        const offset = virtualAddress % this.pageSize;

        if (!this.entries.has(virtualPage)) {
            throw new Error(`Page fault for virtual page ${virtualPage}`);
        }

        const frame = this.entries.get(virtualPage);

        return frame * this.pageSize + offset;
    }
}

function demonstrateVirtualMemory() {
    section("9. Virtual address translation");

    const pageTable = new PageTable();

    pageTable.mapPage(0, 10);
    pageTable.mapPage(1, 11);
    pageTable.mapPage(2, 20);

    for (const address of [0, 100, 4095, 4096, 8192, 9000]) {
        try {
            console.log(
                `Virtual ${address} -> Physical ${pageTable.translate(address)}`
            );
        } catch (error) {
            console.log(`Virtual ${address} -> ${error.message}`);
        }
    }
}


// ============================================================================
// 10. TLB
// ============================================================================

class TLB {
    constructor(capacity) {
        this.capacity = capacity;
        this.entries = new Map();
        this.hits = 0;
        this.misses = 0;
    }

    lookup(virtualPage) {
        if (!this.entries.has(virtualPage)) {
            this.misses++;
            return undefined;
        }

        const frame = this.entries.get(virtualPage);

        this.entries.delete(virtualPage);
        this.entries.set(virtualPage, frame);

        this.hits++;
        return frame;
    }

    insert(virtualPage, frame) {
        if (this.entries.has(virtualPage)) {
            this.entries.delete(virtualPage);
        } else if (this.entries.size >= this.capacity) {
            const oldest = this.entries.keys().next().value;
            this.entries.delete(oldest);
        }

        this.entries.set(virtualPage, frame);
    }
}

function demonstrateTLB() {
    section("10. Translation Lookaside Buffer");

    const pageTable = new PageTable();

    pageTable.mapPage(1, 100);
    pageTable.mapPage(2, 200);
    pageTable.mapPage(3, 300);

    const tlb = new TLB(2);

    for (const page of [1, 1, 2, 1, 3, 1, 2, 3]) {
        let frame = tlb.lookup(page);
        let source = "TLB";

        if (frame === undefined) {
            frame = pageTable.entries.get(page);
            tlb.insert(page, frame);
            source = "page table";
        }

        console.log(`Page ${page} -> frame ${frame}, source=${source}`);
    }

    console.log(`TLB hits: ${tlb.hits}`);
    console.log(`TLB misses: ${tlb.misses}`);
}


// ============================================================================
// 11. WRITE-BACK CACHE
// ============================================================================

class WriteBackCache {
    constructor(capacity) {
        this.capacity = capacity;
        this.cache = new Map();
        this.memory = new Map();
        this.dirtyEvictions = 0;
    }

    write(address, value) {
        if (this.cache.has(address)) {
            this.cache.delete(address);
        } else if (this.cache.size >= this.capacity) {
            const oldestAddress = this.cache.keys().next().value;
            const oldEntry = this.cache.get(oldestAddress);

            if (oldEntry.dirty) {
                this.memory.set(oldestAddress, oldEntry.value);
                this.dirtyEvictions++;
            }

            this.cache.delete(oldestAddress);
        }

        this.cache.set(address, {
            value,
            dirty: true
        });
    }

    flush() {
        for (const [address, entry] of this.cache) {
            if (entry.dirty) {
                this.memory.set(address, entry.value);
                entry.dirty = false;
            }
        }
    }
}

function demonstrateWriteBack() {
    section("11. Write-back cache concept");

    const cache = new WriteBackCache(2);

    cache.write(10, 100);
    cache.write(20, 200);

    console.log("Memory before eviction:", Object.fromEntries(cache.memory));

    cache.write(30, 300);

    console.log("Memory after eviction:", Object.fromEntries(cache.memory));

    cache.flush();

    console.log("Memory after flush:", Object.fromEntries(cache.memory));
    console.log(`Dirty evictions: ${cache.dirtyEvictions}`);
}


// ============================================================================
// 12. ASYNCHRONOUS STORAGE
// ============================================================================

function simulatedStorageRead(key, latencyMilliseconds = 25) {
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve({
                key,
                value: `persistent-data-for-${key}`
            });
        }, latencyMilliseconds);
    });
}

async function demonstrateAsynchronousStorage() {
    section("12. Storage latency and asynchronous programming");

    console.log("Starting simulated storage read...");

    const start = performance.now();
    const result = await simulatedStorageRead("customer-42", 25);
    const elapsed = performance.now() - start;

    console.log("Storage result:", result);
    console.log(`Elapsed time: ${elapsed.toFixed(2)} ms`);

    console.log(`
A storage operation can have much higher latency than an in-memory CPU-cache
access. JavaScript uses promises and asynchronous APIs to avoid blocking the
main event loop during many I/O operations.

Asynchronous programming does not make storage physically faster. It changes
how the application manages waiting.
`);
}


// ============================================================================
// 13. CACHE-AWARE DATA PROCESSING
// ============================================================================

function processTransactions(transactions) {
    let total = 0;

    for (let index = 0; index < transactions.length; index++) {
        total += transactions[index];
    }

    return total;
}

function demonstratePracticalWorkload() {
    section("13. Practical transaction-processing workload");

    const transactionCount = 500_000;
    const transactions = new Float64Array(transactionCount);

    for (let index = 0; index < transactionCount; index++) {
        transactions[index] = (index % 100) * 1.5;
    }

    const start = performance.now();
    const total = processTransactions(transactions);
    const elapsed = performance.now() - start;

    console.log(`Transactions: ${transactionCount}`);
    console.log(`Total value: ${total.toFixed(2)}`);
    console.log(`Processing time: ${elapsed.toFixed(3)} ms`);

    console.log(`
A real production system may use batching, compact data layouts, indexes,
parallelism, and memory-aware algorithms. Cache behavior is one part of the
complete performance picture.
`);
}


// ============================================================================
// 14. CACHE PERFORMANCE MODEL
// ============================================================================

function averageMemoryAccessTime(
    hitTime,
    missRate,
    missPenalty
) {
    if (hitTime < 0 || missRate < 0 || missRate > 1 || missPenalty < 0) {
        throw new RangeError("Invalid AMAT parameters");
    }

    return hitTime + missRate * missPenalty;
}

function demonstrateAMAT() {
    section("14. Average Memory Access Time");

    const result = averageMemoryAccessTime(1, 0.05, 10);

    console.log(`AMAT: ${result.toFixed(2)} ns`);

    console.log(`
The simplified equation is:

    AMAT = hit time + miss rate × miss penalty

For multiple cache levels, the lower-level lookup becomes part of the
penalty associated with a miss at the upper level.
`);
}


// ============================================================================
// 15. EDGE CASES
// ============================================================================

function demonstrateErrors() {
    section("15. Edge cases and validation");

    const tests = [
        {
            name: "Negative cache block",
            operation: () => new DirectMappedCache(4).access(-1)
        },
        {
            name: "Zero cache capacity",
            operation: () => new LRUCache(0)
        },
        {
            name: "Invalid page size",
            operation: () => new PageTable(3000)
        },
        {
            name: "Unmapped virtual page",
            operation: () => new PageTable().translate(4096)
        }
    ];

    for (const test of tests) {
        try {
            test.operation();
            console.log(`${test.name}: unexpectedly accepted`);
        } catch (error) {
            console.log(`${test.name}: rejected -> ${error.message}`);
        }
    }
}


// ============================================================================
// 16. MEMORY USAGE OBSERVATION
// ============================================================================

function demonstrateMemoryUsage() {
    section("16. JavaScript memory usage");

    const before = process.memoryUsage();

    const data = new Float64Array(1_000_000);

    for (let index = 0; index < data.length; index++) {
        data[index] = index;
    }

    const after = process.memoryUsage();

    console.log("Heap used before:", before.heapUsed);
    console.log("Heap used after: ", after.heapUsed);
    console.log("Array-buffer bytes:", data.byteLength);

    console.log(`
Node.js exposes process-level memory statistics. These statistics describe
the JavaScript process, not a direct measurement of CPU-cache occupancy.

The operating system and processor manage physical memory and cache state.
`);
}


// ============================================================================
// 17. SECURITY
// ============================================================================

function explainSecurity() {
    section("17. Memory hierarchy and security");

    console.log(`
Relevant security topics include:

    - virtual-memory process isolation
    - page permissions
    - executable versus non-executable memory
    - address-space randomization
    - cache timing side channels
    - speculative execution side channels
    - sensitive data remaining in memory
    - secure handling of buffers

High-level JavaScript code normally cannot manipulate CPU cache state directly,
but JavaScript execution can still be affected by microarchitectural behavior.
Browser security models add additional isolation and timing restrictions.
`);
}


// ============================================================================
// 18. MAIN
// ============================================================================

async function main() {
    explainHierarchy();
    demonstrateLocality();
    demonstrateDirectMappedCache();
    demonstrateAssociativity();
    demonstrateLRUCache();
    explainCacheMisses();
    demonstrateTypedArrays();
    demonstrateDataLayout();
    demonstrateVirtualMemory();
    demonstrateTLB();
    demonstrateWriteBack();
    await demonstrateAsynchronousStorage();
    demonstratePracticalWorkload();
    demonstrateAMAT();
    demonstrateErrors();
    demonstrateMemoryUsage();
    explainSecurity();

    section("Completed");
    console.log("JavaScript memory-hierarchy study completed successfully.");
}

main().catch((error) => {
    console.error("Program failed:", error);
    process.exitCode = 1;
});
