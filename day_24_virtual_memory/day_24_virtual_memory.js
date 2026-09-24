"use strict";

/*
 * Virtual Memory: Paging, Segmentation, Page Tables, TLB, and Page Faults
 *
 * This self-contained JavaScript program complements the Python simulator.
 * It emphasizes JavaScript data structures, classes, Maps, asynchronous
 * page-fault handling, validation, and trace-driven analysis.
 *
 * Run:
 *     node virtual-memory.js
 */

// ============================================================================
// 1. BASIC ADDRESS CALCULATIONS
// ============================================================================

function section(title) {
    console.log("\n" + "=".repeat(78));
    console.log(title);
    console.log("=".repeat(78));
}

function validatePowerOfTwo(value, name) {
    if (!Number.isInteger(value) || value <= 0 || (value & (value - 1)) !== 0) {
        throw new RangeError(`${name} must be a positive power of two`);
    }
}

function decomposeVirtualAddress(virtualAddress, pageSize, addressBits) {
    validatePowerOfTwo(pageSize, "pageSize");

    if (!Number.isSafeInteger(virtualAddress) || virtualAddress < 0) {
        throw new RangeError("Virtual address must be a non-negative safe integer");
    }

    const maximumAddress = 2 ** addressBits - 1;

    if (virtualAddress > maximumAddress) {
        throw new RangeError("Virtual address exceeds address space");
    }

    const offsetBits = Math.log2(pageSize);
    const pageNumber = Math.floor(virtualAddress / pageSize);
    const offset = virtualAddress % pageSize;

    return {
        pageNumber,
        offset,
        offsetBits,
        pageBits: addressBits - offsetBits
    };
}

function demonstrateAddressCalculation() {
    section("1. Virtual Address Decomposition");

    const address = 0x3a7b;
    const result = decomposeVirtualAddress(address, 4096, 16);

    console.log(`Virtual address : 0x${address.toString(16).toUpperCase()}`);
    console.log(`Page number     : ${result.pageNumber}`);
    console.log(`Offset          : ${result.offset}`);
    console.log(`Offset bits     : ${result.offsetBits}`);
    console.log(`Page-number bits: ${result.pageBits}`);
}

// ============================================================================
// 2. PAGE TABLE
// ============================================================================

class PageTableEntry {
    constructor({
        frameNumber = null,
        present = false,
        writable = true,
        executable = false,
        userAccessible = true,
        dirty = false,
        referenced = false
    } = {}) {
        this.frameNumber = frameNumber;
        this.present = present;
        this.writable = writable;
        this.executable = executable;
        this.userAccessible = userAccessible;
        this.dirty = dirty;
        this.referenced = referenced;
    }
}

class PageFault extends Error {
    constructor(pageNumber) {
        super(`Page fault on virtual page ${pageNumber}`);
        this.name = "PageFault";
        this.pageNumber = pageNumber;
    }
}

class SimplePageTable {
    constructor(virtualPages, physicalFrames) {
        if (virtualPages <= 0 || physicalFrames <= 0) {
            throw new RangeError("Memory dimensions must be positive");
        }

        this.entries = Array.from(
            { length: virtualPages },
            () => new PageTableEntry()
        );

        this.freeFrames = Array.from(
            { length: physicalFrames },
            (_, index) => index
        );
    }

    mapPage(pageNumber, options = {}) {
        this.validatePage(pageNumber);

        const entry = this.entries[pageNumber];

        if (entry.present) {
            return entry.frameNumber;
        }

        if (this.freeFrames.length === 0) {
            throw new Error("No physical frames available");
        }

        const frame = this.freeFrames.shift();

        entry.frameNumber = frame;
        entry.present = true;
        entry.writable = options.writable ?? true;
        entry.executable = options.executable ?? false;

        return frame;
    }

    translate(pageNumber, offset, pageSize) {
        this.validatePage(pageNumber);

        if (!Number.isInteger(offset) || offset < 0 || offset >= pageSize) {
            throw new RangeError("Invalid page offset");
        }

        const entry = this.entries[pageNumber];

        if (!entry.present) {
            throw new PageFault(pageNumber);
        }

        entry.referenced = true;
        return entry.frameNumber * pageSize + offset;
    }

    validatePage(pageNumber) {
        if (
            !Number.isInteger(pageNumber) ||
            pageNumber < 0 ||
            pageNumber >= this.entries.length
        ) {
            throw new RangeError("Invalid virtual page number");
        }
    }
}

function demonstratePageTable() {
    section("2. Single-Level Page Table");

    const pageTable = new SimplePageTable(8, 4);

    pageTable.mapPage(0, { writable: false, executable: true });
    pageTable.mapPage(2, { writable: true });
    pageTable.mapPage(5, { writable: true });

    pageTable.entries.forEach((entry, pageNumber) => {
        if (entry.present) {
            console.log(
                `VPN ${pageNumber} -> PFN ${entry.frameNumber}, ` +
                `writable=${entry.writable}, executable=${entry.executable}`
            );
        }
    });

    console.log(
        "VPN 2 + offset 17 -> physical address:",
        pageTable.translate(2, 17, 256)
    );

    try {
        pageTable.translate(4, 0, 256);
    } catch (error) {
        if (error instanceof PageFault) {
            console.log("Expected:", error.message);
        } else {
            throw error;
        }
    }
}

// ============================================================================
// 3. TLB
// ============================================================================

class LruTlb {
    constructor(capacity) {
        if (!Number.isInteger(capacity) || capacity <= 0) {
            throw new RangeError("TLB capacity must be positive");
        }

        this.capacity = capacity;
        this.entries = new Map();
        this.hits = 0;
        this.misses = 0;
    }

    lookup(pageNumber) {
        if (!this.entries.has(pageNumber)) {
            this.misses++;
            return null;
        }

        const entry = this.entries.get(pageNumber);

        // Map insertion order is used to model LRU order.
        this.entries.delete(pageNumber);
        this.entries.set(pageNumber, entry);

        this.hits++;
        return entry;
    }

    insert(pageNumber, entry) {
        this.entries.delete(pageNumber);
        this.entries.set(pageNumber, entry);

        if (this.entries.size > this.capacity) {
            const oldestKey = this.entries.keys().next().value;
            this.entries.delete(oldestKey);
        }
    }

    invalidate(pageNumber = null) {
        if (pageNumber === null) {
            this.entries.clear();
        } else {
            this.entries.delete(pageNumber);
        }
    }

    get hitRate() {
        const total = this.hits + this.misses;
        return total === 0 ? 0 : this.hits / total;
    }
}

function demonstrateTlb() {
    section("3. Translation Lookaside Buffer");

    const tlb = new LruTlb(2);

    const translations = new Map([
        [1, { frameNumber: 8, writable: true, executable: false }],
        [2, { frameNumber: 3, writable: true, executable: false }],
        [3, { frameNumber: 9, writable: false, executable: true }]
    ]);

    for (const pageNumber of [1, 2, 1, 3, 1, 2]) {
        const result = tlb.lookup(pageNumber);

        if (result) {
            console.log(
                `VPN ${pageNumber}: TLB HIT -> frame ${result.frameNumber}`
            );
        } else {
            console.log(`VPN ${pageNumber}: TLB MISS`);
            tlb.insert(pageNumber, translations.get(pageNumber));
        }
    }

    console.log(`Hits     : ${tlb.hits}`);
    console.log(`Misses   : ${tlb.misses}`);
    console.log(`Hit rate : ${(tlb.hitRate * 100).toFixed(2)}%`);
}

// ============================================================================
// 4. PHYSICAL FRAMES
// ============================================================================

class PhysicalFrame {
    constructor(frameNumber) {
        this.frameNumber = frameNumber;
        this.pageNumber = null;
        this.dirty = false;
        this.referenced = false;
    }
}

// ============================================================================
// 5. INTEGRATED PAGING SYSTEM
// ============================================================================

class VirtualMemorySystem {
    constructor({
        virtualPages,
        physicalFrames,
        pageSize = 256,
        tlbCapacity = 4,
        replacementPolicy = "LRU"
    }) {
        if (virtualPages <= 0 || physicalFrames <= 0) {
            throw new RangeError("Memory dimensions must be positive");
        }

        validatePowerOfTwo(pageSize, "pageSize");

        const policy = replacementPolicy.toUpperCase();

        if (!["FIFO", "LRU", "CLOCK"].includes(policy)) {
            throw new RangeError("Unsupported replacement policy");
        }

        this.virtualPages = virtualPages;
        this.physicalFrames = physicalFrames;
        this.pageSize = pageSize;
        this.replacementPolicy = policy;

        this.pageTable = Array.from(
            { length: virtualPages },
            () => new PageTableEntry()
        );

        this.frames = Array.from(
            { length: physicalFrames },
            (_, index) => new PhysicalFrame(index)
        );

        this.tlb = new LruTlb(tlbCapacity);

        this.fifoQueue = [];
        this.lruOrder = new Map();
        this.clockHand = 0;

        this.statistics = {
            accesses: 0,
            pageFaults: 0,
            diskReads: 0,
            diskWrites: 0
        };
    }

    async access(virtualAddress, {
        write = false,
        execute = false,
        simulateFaultDelay = false
    } = {}) {
        this.statistics.accesses++;

        const pageNumber = Math.floor(virtualAddress / this.pageSize);
        const offset = virtualAddress % this.pageSize;

        if (
            !Number.isSafeInteger(virtualAddress) ||
            virtualAddress < 0 ||
            pageNumber >= this.virtualPages
        ) {
            throw new RangeError("Virtual address is outside the address space");
        }

        const tlbEntry = this.tlb.lookup(pageNumber);

        if (tlbEntry !== null) {
            this.checkPermissions(tlbEntry, write, execute);

            const frame = this.frames[tlbEntry.frameNumber];
            frame.referenced = true;
            this.touch(pageNumber);

            if (write) {
                this.pageTable[pageNumber].dirty = true;
                frame.dirty = true;
            }

            return {
                virtualAddress,
                physicalAddress:
                    tlbEntry.frameNumber * this.pageSize + offset,
                pageNumber,
                offset,
                tlbHit: true,
                pageFault: false,
                evictedPage: null
            };
        }

        let pageEntry = this.pageTable[pageNumber];

        if (!pageEntry.present) {
            this.statistics.pageFaults++;

            if (simulateFaultDelay) {
                // Real page faults can involve storage I/O. This delay only
                // illustrates asynchronous event handling and is not a
                // representation of actual hardware timing.
                await new Promise(resolve => setTimeout(resolve, 5));
            }

            const evictedPage = this.handlePageFault(pageNumber);

            pageEntry = this.pageTable[pageNumber];

            this.tlb.insert(pageNumber, {
                frameNumber: pageEntry.frameNumber,
                writable: pageEntry.writable,
                executable: pageEntry.executable
            });

            this.checkPermissions(pageEntry, write, execute);

            if (write) {
                pageEntry.dirty = true;
                this.frames[pageEntry.frameNumber].dirty = true;
            }

            return {
                virtualAddress,
                physicalAddress:
                    pageEntry.frameNumber * this.pageSize + offset,
                pageNumber,
                offset,
                tlbHit: false,
                pageFault: true,
                evictedPage
            };
        }

        this.checkPermissions(pageEntry, write, execute);

        if (write) {
            pageEntry.dirty = true;
            this.frames[pageEntry.frameNumber].dirty = true;
        }

        pageEntry.referenced = true;

        this.tlb.insert(pageNumber, {
            frameNumber: pageEntry.frameNumber,
            writable: pageEntry.writable,
            executable: pageEntry.executable
        });

        this.touch(pageNumber);

        return {
            virtualAddress,
            physicalAddress:
                pageEntry.frameNumber * this.pageSize + offset,
            pageNumber,
            offset,
            tlbHit: false,
            pageFault: false,
            evictedPage: null
        };
    }

    checkPermissions(entry, write, execute) {
        if (write && !entry.writable) {
            throw new Error("Write access denied");
        }

        if (execute && !entry.executable) {
            throw new Error("Execute access denied");
        }
    }

    handlePageFault(pageNumber) {
        let frame = this.frames.find(candidate => candidate.pageNumber === null);
        let evictedPage = null;

        if (!frame) {
            frame = this.selectVictim();
            evictedPage = frame.pageNumber;

            if (evictedPage !== null) {
                const victimEntry = this.pageTable[evictedPage];

                if (victimEntry.dirty) {
                    this.statistics.diskWrites++;
                }

                victimEntry.present = false;
                victimEntry.frameNumber = null;
                victimEntry.dirty = false;
                victimEntry.referenced = false;

                this.tlb.invalidate(evictedPage);
                this.lruOrder.delete(evictedPage);
            }
        }

        this.statistics.diskReads++;

        frame.pageNumber = pageNumber;
        frame.dirty = false;
        frame.referenced = true;

        const entry = this.pageTable[pageNumber];
        entry.present = true;
        entry.frameNumber = frame.frameNumber;
        entry.referenced = true;
        entry.dirty = false;

        this.fifoQueue.push(frame.frameNumber);
        this.touch(pageNumber);

        return evictedPage;
    }

    selectVictim() {
        if (this.replacementPolicy === "FIFO") {
            const frameNumber = this.fifoQueue.shift();
            return this.frames[frameNumber];
        }

        if (this.replacementPolicy === "LRU") {
            const oldestPage = this.lruOrder.keys().next().value;

            if (oldestPage === undefined) {
                throw new Error("LRU state is inconsistent");
            }

            const frameNumber = this.pageTable[oldestPage].frameNumber;
            this.lruOrder.delete(oldestPage);

            return this.frames[frameNumber];
        }

        while (true) {
            const frame = this.frames[this.clockHand];

            if (!frame.referenced) {
                this.clockHand =
                    (this.clockHand + 1) % this.frames.length;
                return frame;
            }

            frame.referenced = false;

            if (frame.pageNumber !== null) {
                this.pageTable[frame.pageNumber].referenced = false;
            }

            this.clockHand =
                (this.clockHand + 1) % this.frames.length;
        }
    }

    touch(pageNumber) {
        if (this.replacementPolicy !== "LRU") {
            return;
        }

        this.lruOrder.delete(pageNumber);
        this.lruOrder.set(pageNumber, true);

        const entry = this.pageTable[pageNumber];

        if (entry.present) {
            this.frames[entry.frameNumber].referenced = true;
        }
    }

    get tlbHitRate() {
        return this.tlb.hitRate;
    }

    get pageFaultRate() {
        const { accesses, pageFaults } = this.statistics;
        return accesses === 0 ? 0 : pageFaults / accesses;
    }

    printState() {
        console.log("\nPage table:");

        this.pageTable.forEach((entry, page) => {
            if (entry.present) {
                console.log(
                    `VPN ${page}: frame=${entry.frameNumber}, ` +
                    `dirty=${entry.dirty}, referenced=${entry.referenced}`
                );
            } else {
                console.log(`VPN ${page}: not resident`);
            }
        });

        console.log("\nPhysical frames:");

        this.frames.forEach(frame => {
            console.log(
                `Frame ${frame.frameNumber}: ` +
                `VPN=${frame.pageNumber}, ` +
                `dirty=${frame.dirty}, ` +
                `referenced=${frame.referenced}`
            );
        });
    }
}

async function demonstrateIntegratedSystem() {
    section("4. Integrated Paging, TLB, and Page Faults");

    const memory = new VirtualMemorySystem({
        virtualPages: 8,
        physicalFrames: 3,
        pageSize: 256,
        tlbCapacity: 2,
        replacementPolicy: "LRU"
    });

    const accesses = [
        [10, false],
        [266, false],
        [522, true],
        [10, false],
        [778, false],
        [266, false],
        [522, true],
        [1030, false]
    ];

    for (const [address, write] of accesses) {
        try {
            const result = await memory.access(address, {
                write,
                simulateFaultDelay: true
            });

            console.log(
                `VA=${address.toString().padStart(4)} ` +
                `VPN=${result.pageNumber} ` +
                `offset=${result.offset.toString().padStart(3)} ` +
                `PA=${result.physicalAddress.toString().padStart(4)} ` +
                `TLB=${result.tlbHit ? "HIT " : "MISS"} ` +
                `PF=${result.pageFault ? "YES" : "NO "} ` +
                `evicted=${result.evictedPage}`
            );
        } catch (error) {
            console.log(`VA=${address}: ERROR: ${error.message}`);
        }
    }

    memory.printState();

    console.log("\nStatistics:");
    console.log(memory.statistics);
    console.log(`TLB hit rate  : ${(memory.tlbHitRate * 100).toFixed(2)}%`);
    console.log(`Page fault rate: ${(memory.pageFaultRate * 100).toFixed(2)}%`);
}

// ============================================================================
// 6. SEGMENTATION
// ============================================================================

class Segment {
    constructor(name, base, limit, {
        readable = true,
        writable = false,
        executable = false
    } = {}) {
        this.name = name;
        this.base = base;
        this.limit = limit;
        this.readable = readable;
        this.writable = writable;
        this.executable = executable;
    }

    translate(offset, { write = false, execute = false } = {}) {
        if (!Number.isInteger(offset) || offset < 0 || offset >= this.limit) {
            throw new RangeError(
                `Offset outside segment '${this.name}'`
            );
        }

        if (write && !this.writable) {
            throw new Error(`Write denied for segment '${this.name}'`);
        }

        if (execute && !this.executable) {
            throw new Error(`Execution denied for segment '${this.name}'`);
        }

        return this.base + offset;
    }
}

class SegmentedMemory {
    constructor() {
        this.segments = new Map();
    }

    addSegment(selector, segment) {
        if (!Number.isInteger(selector) || selector < 0) {
            throw new RangeError("Invalid segment selector");
        }

        this.segments.set(selector, segment);
    }

    translate(selector, offset, options = {}) {
        const segment = this.segments.get(selector);

        if (!segment) {
            throw new Error("Invalid segment selector");
        }

        return segment.translate(offset, options);
    }
}

function demonstrateSegmentation() {
    section("5. Segmentation");

    const memory = new SegmentedMemory();

    memory.addSegment(
        1,
        new Segment("code", 10000, 2000, {
            writable: false,
            executable: true
        })
    );

    memory.addSegment(
        2,
        new Segment("data", 20000, 3000, {
            writable: true,
            executable: false
        })
    );

    console.log(
        "Code offset 120 ->",
        memory.translate(1, 120, { execute: true })
    );

    console.log(
        "Data offset 500 ->",
        memory.translate(2, 500, { write: true })
    );

    try {
        memory.translate(1, 120, { write: true });
    } catch (error) {
        console.log("Expected protection failure:", error.message);
    }

    try {
        memory.translate(2, 3000);
    } catch (error) {
        console.log("Expected bounds failure:", error.message);
    }
}

// ============================================================================
// 7. MULTI-LEVEL PAGE TABLE
// ============================================================================

class TwoLevelPageTable {
    constructor(directoryEntries, tableEntries) {
        this.directoryEntries = directoryEntries;
        this.tableEntries = tableEntries;
        this.directory = new Map();
    }

    mapPage(virtualPage, frame) {
        const directoryIndex =
            Math.floor(virtualPage / this.tableEntries);
        const tableIndex = virtualPage % this.tableEntries;

        if (
            directoryIndex < 0 ||
            directoryIndex >= this.directoryEntries
        ) {
            throw new RangeError("Virtual page outside address space");
        }

        if (!this.directory.has(directoryIndex)) {
            this.directory.set(directoryIndex, new Map());
        }

        this.directory.get(directoryIndex).set(tableIndex, frame);
    }

    translate(virtualPage) {
        const directoryIndex =
            Math.floor(virtualPage / this.tableEntries);
        const tableIndex = virtualPage % this.tableEntries;

        const table = this.directory.get(directoryIndex);

        return table?.get(tableIndex) ?? null;
    }
}

function demonstrateMultiLevelPaging() {
    section("6. Multi-Level Page Tables");

    const table = new TwoLevelPageTable(4, 4);

    table.mapPage(0, 10);
    table.mapPage(1, 11);
    table.mapPage(8, 20);
    table.mapPage(15, 27);

    [0, 1, 2, 8, 15].forEach(page => {
        console.log(`VPN ${page} -> PFN ${table.translate(page)}`);
    });

    console.log(
        "A multi-level structure can avoid allocating lower-level tables "
        + "for completely unused regions."
    );
}

// ============================================================================
// 8. EFFECTIVE ACCESS TIME
// ============================================================================

function effectiveAccessTime(memoryNs, tlbNs, hitRate) {
    if (memoryNs < 0 || tlbNs < 0) {
        throw new RangeError("Timing values cannot be negative");
    }

    if (hitRate < 0 || hitRate > 1) {
        throw new RangeError("Hit rate must be between 0 and 1");
    }

    const hitCost = tlbNs + memoryNs;
    const missCost = tlbNs + 2 * memoryNs;

    return hitRate * hitCost + (1 - hitRate) * missCost;
}

function demonstrateEffectiveAccessTime() {
    section("7. Effective Access Time");

    [0.5, 0.8, 0.95, 0.99].forEach(hitRate => {
        const eat = effectiveAccessTime(100, 10, hitRate);

        console.log(
            `TLB hit rate ${(hitRate * 100).toFixed(0)}% -> ${eat.toFixed(1)} ns`
        );
    });

    console.log(
        "This simplified model assumes one memory access after a TLB hit "
        + "and two memory accesses after a TLB miss."
    );
}

// ============================================================================
// 9. PAGE REPLACEMENT ALGORITHMS
// ============================================================================

function fifoFaults(referenceString, frameCount) {
    if (frameCount <= 0) {
        throw new RangeError("Frame count must be positive");
    }

    const frames = [];
    const queue = [];
    let faults = 0;

    for (const page of referenceString) {
        if (frames.includes(page)) {
            continue;
        }

        faults++;

        if (frames.length < frameCount) {
            frames.push(page);
            queue.push(page);
        } else {
            const victim = queue.shift();
            frames[frames.indexOf(victim)] = page;
            queue.push(page);
        }
    }

    return faults;
}

function lruFaults(referenceString, frameCount) {
    if (frameCount <= 0) {
        throw new RangeError("Frame count must be positive");
    }

    const frames = new Map();
    let faults = 0;

    for (const page of referenceString) {
        if (frames.has(page)) {
            frames.delete(page);
            frames.set(page, true);
            continue;
        }

        faults++;

        if (frames.size === frameCount) {
            const victim = frames.keys().next().value;
            frames.delete(victim);
        }

        frames.set(page, true);
    }

    return faults;
}

function optimalFaults(referenceString, frameCount) {
    if (frameCount <= 0) {
        throw new RangeError("Frame count must be positive");
    }

    const frames = [];
    let faults = 0;

    for (let index = 0; index < referenceString.length; index++) {
        const page = referenceString[index];

        if (frames.includes(page)) {
            continue;
        }

        faults++;

        if (frames.length < frameCount) {
            frames.push(page);
            continue;
        }

        const future = referenceString.slice(index + 1);

        let victimIndex = 0;
        let farthest = -1;

        frames.forEach((resident, residentIndex) => {
            const nextUse = future.indexOf(resident);
            const distance = nextUse === -1 ? Infinity : nextUse;

            if (distance > farthest) {
                farthest = distance;
                victimIndex = residentIndex;
            }
        });

        frames[victimIndex] = page;
    }

    return faults;
}

function demonstrateReplacementAlgorithms() {
    section("8. Page Replacement Algorithms");

    const referenceString = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2];

    console.log("Reference:", referenceString.join(" "));

    [2, 3, 4].forEach(frameCount => {
        console.log(
            `Frames=${frameCount}: ` +
            `FIFO=${fifoFaults(referenceString, frameCount)}, ` +
            `LRU=${lruFaults(referenceString, frameCount)}, ` +
            `Optimal=${optimalFaults(referenceString, frameCount)}`
        );
    });
}

// ============================================================================
// 10. WORKING SET
// ============================================================================

function workingSetSizes(referenceString, windowSize) {
    if (windowSize <= 0) {
        throw new RangeError("Window size must be positive");
    }

    return referenceString.map((_, index) => {
        const start = Math.max(0, index - windowSize + 1);
        return new Set(referenceString.slice(start, index + 1)).size;
    });
}

function demonstrateWorkingSet() {
    section("9. Locality, Working Set, and Thrashing");

    const traces = {
        "Locality-heavy": [1, 2, 1, 2, 1, 2, 1, 2, 3, 2, 1, 2],
        "Locality-poor": Array.from({ length: 12 }, (_, index) => index)
    };

    for (const [name, trace] of Object.entries(traces)) {
        console.log(name);
        console.log("Trace:", trace.join(" "));
        console.log(
            "Working-set sizes:",
            workingSetSizes(trace, 4).join(" ")
        );
    }

    console.log(
        "Thrashing occurs when frequent page faults consume a substantial "
        + "fraction of execution time."
    );
}

// ============================================================================
// 11. COPY-ON-WRITE
// ============================================================================

class CopyOnWriteManager {
    constructor() {
        this.nextFrame = 0;
        this.pages = new Map();
    }

    allocate(processId, virtualPage) {
        this.pages.set(
            `${processId}:${virtualPage}`,
            {
                frameNumber: this.nextFrame++,
                referenceCount: 1
            }
        );
    }

    forkShare(parent, child, virtualPage) {
        const parentKey = `${parent}:${virtualPage}`;
        const parentPage = this.pages.get(parentKey);

        if (!parentPage) {
            throw new Error("Parent page does not exist");
        }

        parentPage.referenceCount++;

        this.pages.set(`${child}:${virtualPage}`, parentPage);
    }

    write(processId, virtualPage) {
        const key = `${processId}:${virtualPage}`;
        const page = this.pages.get(key);

        if (!page) {
            throw new Error("Process page does not exist");
        }

        if (page.referenceCount > 1) {
            page.referenceCount--;

            const privatePage = {
                frameNumber: this.nextFrame++,
                referenceCount: 1
            };

            this.pages.set(key, privatePage);
            return privatePage.frameNumber;
        }

        return page.frameNumber;
    }
}

function demonstrateCopyOnWrite() {
    section("10. Copy-on-Write");

    const manager = new CopyOnWriteManager();

    manager.allocate("parent", 0);
    manager.forkShare("parent", "child", 0);

    console.log(
        "Before child write:",
        manager.pages.get("parent:0").frameNumber,
        manager.pages.get("child:0").frameNumber
    );

    manager.write("child", 0);

    console.log(
        "After child write:",
        manager.pages.get("parent:0").frameNumber,
        manager.pages.get("child:0").frameNumber
    );
}

// ============================================================================
// 12. SECURITY AND PROTECTION
// ============================================================================

function demonstrateProtection() {
    section("11. Memory Protection");

    const code = new PageTableEntry({
        writable: false,
        executable: true
    });

    const data = new PageTableEntry({
        writable: true,
        executable: false
    });

    console.log(
        "Code page:",
        `writable=${code.writable}, executable=${code.executable}`
    );

    console.log(
        "Data page:",
        `writable=${data.writable}, executable=${data.executable}`
    );

    try {
        if (!code.writable) {
            throw new Error("Write denied by page permissions");
        }
    } catch (error) {
        console.log("Expected:", error.message);
    }

    console.log(
        "Modern memory protection can combine user/kernel permissions, "
        + "read/write/execute bits, ASLR, and other mechanisms."
    );
}

// ============================================================================
// 13. PERFORMANCE ANALYSIS
// ============================================================================

function benchmarkReplacementAlgorithms() {
    section("12. Trace-Based Performance Analysis");

    const referenceString = [];

    // Generate a workload with strong locality. This is intentionally
    // deterministic so repeated executions produce comparable results.
    for (let index = 0; index < 1000; index++) {
        const workingPage = Math.floor(index / 20) % 8;
        referenceString.push(
            index % 5 === 0
                ? (workingPage + 1) % 8
                : workingPage
        );
    }

    console.log(`Trace length: ${referenceString.length}`);

    [2, 4, 8].forEach(frameCount => {
        console.log(
            `Frames=${frameCount}, ` +
            `FIFO faults=${fifoFaults(referenceString, frameCount)}, ` +
            `LRU faults=${lruFaults(referenceString, frameCount)}, ` +
            `Optimal faults=${optimalFaults(referenceString, frameCount)}`
        );
    });

    console.log(
        "The optimal policy is a theoretical baseline because a real OS "
        + "does not know the exact future reference sequence."
    );
}

// ============================================================================
// 14. EDGE CASES
// ============================================================================

function demonstrateEdgeCases() {
    section("13. Edge Cases");

    const cases = [
        [
            "Negative virtual address",
            () => decomposeVirtualAddress(-1, 4096, 16)
        ],
        [
            "Invalid page size",
            () => decomposeVirtualAddress(100, 3000, 16)
        ],
        [
            "Address beyond address space",
            () => decomposeVirtualAddress(70000, 4096, 16)
        ],
        [
            "Zero TLB capacity",
            () => new LruTlb(0)
        ]
    ];

    cases.forEach(([name, operation]) => {
        try {
            operation();
            console.log(`${name}: unexpectedly succeeded`);
        } catch (error) {
            console.log(`${name}: correctly rejected -> ${error.message}`);
        }
    });
}

// ============================================================================
// 15. COMPARISON
// ============================================================================

function printComparison() {
    section("14. Paging and Segmentation Comparison");

    const rows = [
        ["Allocation", "Fixed-size pages", "Variable-size segments"],
        ["Address", "Page + offset", "Segment + offset"],
        ["Main strength", "Efficient physical allocation", "Logical organization"],
        ["Fragmentation", "Internal", "External"],
        ["Protection", "Page permissions", "Segment permissions"],
        ["Sharing", "Page-oriented", "Logical-region-oriented"]
    ];

    console.log(
        "Property".padEnd(18) +
        "Paging".padEnd(28) +
        "Segmentation"
    );

    console.log("-".repeat(70));

    rows.forEach(([property, paging, segmentation]) => {
        console.log(
            property.padEnd(18) +
            paging.padEnd(28) +
            segmentation
        );
    });
}

// ============================================================================
// 16. SELF-TESTS
// ============================================================================

function runTests() {
    section("15. Self-Tests");

    const decomposition =
        decomposeVirtualAddress(5000, 4096, 16);

    console.assert(
        decomposition.pageNumber === 1,
        "Incorrect page number"
    );

    console.assert(
        decomposition.offset === 904,
        "Incorrect offset"
    );

    const table = new SimplePageTable(4, 2);
    const frame = table.mapPage(1);

    console.assert(
        table.translate(1, 20, 256) === frame * 256 + 20,
        "Incorrect page-table translation"
    );

    console.assert(
        fifoFaults([1, 2, 1, 3], 2) === 3,
        "FIFO test failed"
    );

    console.assert(
        lruFaults([1, 2, 1, 3], 2) === 3,
        "LRU test failed"
    );

    const segment = new Segment(
        "test",
        100,
        50,
        { writable: true }
    );

    console.assert(
        segment.translate(10, { write: true }) === 110,
        "Segmentation test failed"
    );

    console.log("Self-tests completed.");
}

// ============================================================================
// 17. MAIN
// ============================================================================

async function main() {
    demonstrateAddressCalculation();
    demonstratePageTable();
    demonstrateTlb();
    await demonstrateIntegratedSystem();
    demonstrateSegmentation();
    demonstrateMultiLevelPaging();
    demonstrateEffectiveAccessTime();
    demonstrateReplacementAlgorithms();
    demonstrateWorkingSet();
    demonstrateCopyOnWrite();
    demonstrateProtection();
    benchmarkReplacementAlgorithms();
    demonstrateEdgeCases();
    printComparison();
    runTests();

    section("Study Checklist");

    [
        "Virtual and physical addresses",
        "Pages and frames",
        "Page tables",
        "Page-table entries",
        "TLB",
        "TLB hit and miss behavior",
        "Page faults",
        "Demand paging",
        "Page replacement",
        "FIFO, LRU, CLOCK, and optimal policies",
        "Segmentation",
        "Multi-level page tables",
        "Working sets",
        "Thrashing",
        "Copy-on-write",
        "Memory protection",
        "Effective access time",
        "Performance trade-offs"
    ].forEach(item => console.log(`[x] ${item}`));
}

main().catch(error => {
    console.error("Fatal error:", error);
    process.exitCode = 1;
});
