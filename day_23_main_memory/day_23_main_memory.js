/*
 * Main Memory: RAM, DRAM, SRAM, Memory Addressing, and Memory Allocation
 * ======================================================================
 *
 * A self-contained JavaScript study program.
 *
 * It uses typed arrays and explicit simulations to model memory concepts
 * that JavaScript normally hides behind its runtime and garbage collector.
 *
 * Run with:
 *     node main-memory.js
 */

"use strict";

// ============================================================================
// 1. MEMORY UNITS
// ============================================================================

const BYTES_PER_KIB = 1024;
const BYTES_PER_MIB = 1024 ** 2;
const BYTES_PER_GIB = 1024 ** 3;

function formatBytes(bytes) {
    if (!Number.isFinite(bytes) || bytes < 0) {
        throw new RangeError("Byte count must be a non-negative finite number.");
    }

    if (bytes < 1024) {
        return `${bytes} B`;
    }

    const units = ["KiB", "MiB", "GiB", "TiB"];
    let value = bytes;

    for (const unit of units) {
        value /= 1024;

        if (value < 1024 || unit === "TiB") {
            return `${value.toFixed(2)} ${unit}`;
        }
    }

    return `${bytes} B`;
}

function showMemoryUnits() {
    console.log("\n" + "=".repeat(78));
    console.log("1. MEMORY UNITS");
    console.log("=".repeat(78));

    console.log(`1 byte = 1 byte`);
    console.log(`1 KiB = ${BYTES_PER_KIB.toLocaleString()} bytes`);
    console.log(`1 MiB = ${BYTES_PER_MIB.toLocaleString()} bytes`);
    console.log(`1 GiB = ${BYTES_PER_GIB.toLocaleString()} bytes`);

    console.log("\nBinary and decimal units are different:");
    console.log("KB = 1,000 bytes in decimal notation.");
    console.log("KiB = 1,024 bytes in binary notation.");
}


// ============================================================================
// 2. BYTE-ADDRESSABLE MEMORY WITH TYPED ARRAYS
// ============================================================================

function demonstrateByteAddressing() {
    console.log("\n" + "=".repeat(78));
    console.log("2. BYTE ADDRESSING");
    console.log("=".repeat(78));

    // Uint8Array stores exactly one unsigned byte per element.
    const memory = new Uint8Array(16);

    for (let address = 0; address < memory.length; address++) {
        memory[address] = address * 3;
    }

    for (let address = 0; address < memory.length; address++) {
        console.log(
            `address=${address.toString().padStart(2, " ")} ` +
            `binary=${address.toString(2).padStart(4, "0")} ` +
            `value=${memory[address]}`
        );
    }

    console.log(
        "\nTyped arrays are useful for demonstrating contiguous binary data, " +
        "but they are still managed by the JavaScript runtime."
    );
}


// ============================================================================
// 3. SIMULATED RAM
// ============================================================================

class MemoryAccessError extends Error {
    constructor(message) {
        super(message);
        this.name = "MemoryAccessError";
    }
}

class SimulatedRAM {
    constructor(sizeBytes) {
        if (!Number.isInteger(sizeBytes) || sizeBytes <= 0) {
            throw new RangeError("RAM size must be a positive integer.");
        }

        this.memory = new Uint8Array(sizeBytes);
    }

    validateAddress(address, width = 1) {
        if (!Number.isInteger(address)) {
            throw new TypeError("Address must be an integer.");
        }

        if (address < 0 || width <= 0 || address + width > this.memory.length) {
            throw new MemoryAccessError(
                `Invalid access: address=${address}, width=${width}, ` +
                `RAM size=${this.memory.length}`
            );
        }
    }

    readByte(address) {
        this.validateAddress(address);
        return this.memory[address];
    }

    writeByte(address, value) {
        this.validateAddress(address);

        if (!Number.isInteger(value) || value < 0 || value > 255) {
            throw new RangeError("A byte must contain an integer from 0 to 255.");
        }

        this.memory[address] = value;
    }

    read(address, length) {
        this.validateAddress(address, length);
        return this.memory.slice(address, address + length);
    }

    write(address, data) {
        if (!(data instanceof Uint8Array)) {
            throw new TypeError("Data must be a Uint8Array.");
        }

        this.validateAddress(address, data.length);
        this.memory.set(data, address);
    }

    dump(start = 0, length = this.memory.length) {
        this.validateAddress(start, length);

        const data = this.memory.slice(start, start + length);

        for (let offset = 0; offset < data.length; offset += 8) {
            const chunk = Array.from(data.slice(offset, offset + 8))
                .map(byte => byte.toString(16).padStart(2, "0").toUpperCase())
                .join(" ");

            console.log(
                `${(start + offset).toString(16).padStart(4, "0").toUpperCase()}: ${chunk}`
            );
        }
    }
}

function demonstrateSimulatedRAM() {
    console.log("\n" + "=".repeat(78));
    console.log("3. SIMULATED RAM");
    console.log("=".repeat(78));

    const ram = new SimulatedRAM(64);

    ram.writeByte(10, 255);
    ram.write(20, new TextEncoder().encode("HELLO"));

    console.log("Byte at address 10:", ram.readByte(10));
    console.log(
        "Bytes at address 20:",
        Array.from(ram.read(20, 5))
    );

    console.log("\nMemory dump:");
    ram.dump(0, 32);

    try {
        ram.readByte(64);
    } catch (error) {
        console.log("\nInvalid access handled:", error.message);
    }
}


// ============================================================================
// 4. DRAM AND SRAM CONCEPTUAL MODEL
// ============================================================================

class MemoryCell {
    constructor(technology, bit = 0) {
        if (!["DRAM", "SRAM"].includes(technology)) {
            throw new RangeError("Technology must be DRAM or SRAM.");
        }

        if (![0, 1].includes(bit)) {
            throw new RangeError("A memory cell stores one bit: 0 or 1.");
        }

        this.technology = technology;
        this.bit = bit;
        this.refreshCount = 0;
    }

    refresh() {
        if (this.technology === "DRAM") {
            this.refreshCount++;
        }
    }

    read() {
        return this.bit;
    }

    write(bit) {
        if (![0, 1].includes(bit)) {
            throw new RangeError("Bit must be 0 or 1.");
        }

        this.bit = bit;
    }
}

function demonstrateDRAMAndSRAM() {
    console.log("\n" + "=".repeat(78));
    console.log("4. DRAM AND SRAM");
    console.log("=".repeat(78));

    const dram = new MemoryCell("DRAM", 1);
    const sram = new MemoryCell("SRAM", 1);

    for (let i = 0; i < 5; i++) {
        dram.refresh();
        sram.refresh();
    }

    console.log(
        `DRAM: bit=${dram.read()}, refreshes=${dram.refreshCount}`
    );

    console.log(
        `SRAM: bit=${sram.read()}, refreshes=${sram.refreshCount}`
    );

    console.log("\nDRAM is designed around dense storage and periodic refresh.");
    console.log("SRAM uses a stable circuit state and does not require DRAM-style refresh.");
}


// ============================================================================
// 5. MEMORY HIERARCHY
// ============================================================================

function showMemoryHierarchy() {
    console.log("\n" + "=".repeat(78));
    console.log("5. MEMORY HIERARCHY");
    console.log("=".repeat(78));

    const levels = [
        ["Registers", "CPU register structures", "Extremely fast"],
        ["L1 cache", "SRAM", "Very fast"],
        ["L2 cache", "SRAM", "Very fast"],
        ["L3 cache", "SRAM", "Fast"],
        ["Main memory", "DRAM", "Slower than cache"],
        ["SSD", "Flash", "Much slower than RAM"]
    ];

    for (const [level, technology, speed] of levels) {
        console.log(
            `${level.padEnd(16)} | ` +
            `${technology.padEnd(28)} | ${speed}`
        );
    }

    console.log(
        "\nThe hierarchy balances speed, capacity, density, persistence, and cost."
    );
}


// ============================================================================
// 6. MEMORY ALLOCATION
// ============================================================================

class AllocationError extends Error {
    constructor(message) {
        super(message);
        this.name = "AllocationError";
    }
}

class FirstFitAllocator {
    constructor(capacity) {
        if (!Number.isInteger(capacity) || capacity <= 0) {
            throw new RangeError("Capacity must be positive.");
        }

        this.capacity = capacity;
        this.freeBlocks = [[0, capacity]];
        this.allocations = new Map();
        this.nextAllocationId = 1;
    }

    coalesce() {
        this.freeBlocks.sort((a, b) => a[0] - b[0]);

        const merged = [];

        for (const [start, size] of this.freeBlocks) {
            if (merged.length === 0) {
                merged.push([start, size]);
                continue;
            }

            const previous = merged[merged.length - 1];
            const previousEnd = previous[0] + previous[1];

            if (start <= previousEnd) {
                const newEnd = Math.max(previousEnd, start + size);
                previous[1] = newEnd - previous[0];
            } else {
                merged.push([start, size]);
            }
        }

        this.freeBlocks = merged;
    }

    allocate(size, owner) {
        if (!Number.isInteger(size) || size <= 0) {
            throw new AllocationError("Allocation size must be positive.");
        }

        for (let index = 0; index < this.freeBlocks.length; index++) {
            const [start, freeSize] = this.freeBlocks[index];

            if (freeSize >= size) {
                const id = this.nextAllocationId++;

                this.allocations.set(id, {
                    id,
                    address: start,
                    size,
                    owner
                });

                if (freeSize === size) {
                    this.freeBlocks.splice(index, 1);
                } else {
                    this.freeBlocks[index] = [
                        start + size,
                        freeSize - size
                    ];
                }

                return id;
            }
        }

        throw new AllocationError(
            `Unable to allocate ${size} bytes. Free=${this.totalFree()} bytes.`
        );
    }

    free(id) {
        const allocation = this.allocations.get(id);

        if (!allocation) {
            throw new AllocationError(
                `Allocation ${id} does not exist or was already freed.`
            );
        }

        this.allocations.delete(id);
        this.freeBlocks.push([allocation.address, allocation.size]);
        this.coalesce();
    }

    totalFree() {
        return this.freeBlocks.reduce(
            (total, [, size]) => total + size,
            0
        );
    }

    totalAllocated() {
        let total = 0;

        for (const allocation of this.allocations.values()) {
            total += allocation.size;
        }

        return total;
    }

    largestFreeBlock() {
        return Math.max(
            0,
            ...this.freeBlocks.map(([, size]) => size)
        );
    }

    fragmentationRatio() {
        const totalFree = this.totalFree();

        if (totalFree === 0) {
            return 0;
        }

        return 1 - this.largestFreeBlock() / totalFree;
    }

    printState() {
        console.log("\nAllocator state:");
        console.log(`Capacity: ${this.capacity} bytes`);
        console.log(`Allocated: ${this.totalAllocated()} bytes`);
        console.log(`Free: ${this.totalFree()} bytes`);

        console.log("\nAllocated blocks:");

        for (const allocation of this.allocations.values()) {
            console.log(
                `  id=${allocation.id} ` +
                `address=${allocation.address} ` +
                `size=${allocation.size} ` +
                `owner=${allocation.owner}`
            );
        }

        console.log("Free blocks:");

        for (const [start, size] of this.freeBlocks) {
            console.log(`  address=${start} size=${size}`);
        }

        console.log(
            `Fragmentation ratio: ${(this.fragmentationRatio() * 100).toFixed(2)}%`
        );
    }
}

function demonstrateAllocation() {
    console.log("\n" + "=".repeat(78));
    console.log("6. MEMORY ALLOCATION AND FRAGMENTATION");
    console.log("=".repeat(78));

    const allocator = new FirstFitAllocator(128);

    const processA = allocator.allocate(20, "Process A");
    const processB = allocator.allocate(30, "Process B");
    const processC = allocator.allocate(25, "Process C");

    allocator.printState();

    console.log("\nFreeing Process B...");
    allocator.free(processB);
    allocator.printState();

    console.log("\nAllocating 15 bytes...");
    const processD = allocator.allocate(15, "Process D");

    allocator.printState();

    console.log("\nFreeing all allocations...");
    allocator.free(processA);
    allocator.free(processC);
    allocator.free(processD);

    allocator.printState();
}


// ============================================================================
// 7. ALLOCATION STRATEGIES
// ============================================================================

function allocationStrategy(blocks, requests, mode) {
    const remaining = [...blocks];
    const placements = [];

    for (const request of requests) {
        const candidates = [];

        for (let index = 0; index < remaining.length; index++) {
            if (remaining[index] >= request) {
                candidates.push({
                    index,
                    available: remaining[index]
                });

                if (mode === "first") {
                    break;
                }
            }
        }

        if (candidates.length === 0) {
            placements.push(null);
            continue;
        }

        let selected;

        if (mode === "first") {
            selected = candidates[0];
        } else if (mode === "best") {
            selected = candidates.reduce(
                (smallest, current) =>
                    current.available < smallest.available
                        ? current
                        : smallest
            );
        } else if (mode === "worst") {
            selected = candidates.reduce(
                (largest, current) =>
                    current.available > largest.available
                        ? current
                        : largest
            );
        } else {
            throw new RangeError("Unknown allocation strategy.");
        }

        placements.push(selected.index);
        remaining[selected.index] -= request;
    }

    return placements;
}

function demonstrateAllocationStrategies() {
    console.log("\n" + "=".repeat(78));
    console.log("7. FIRST-FIT, BEST-FIT, AND WORST-FIT");
    console.log("=".repeat(78));

    const blocks = [100, 500, 200, 300, 600];
    const requests = [212, 417, 112, 426];

    console.log("Blocks:", blocks);
    console.log("Requests:", requests);

    for (const [name, mode] of [
        ["First-fit", "first"],
        ["Best-fit", "best"],
        ["Worst-fit", "worst"]
    ]) {
        console.log(`${name}:`, allocationStrategy(blocks, requests, mode));
    }

    console.log(
        "\nDifferent allocation policies can produce different fragmentation patterns."
    );
}


// ============================================================================
// 8. MEMORY ALIGNMENT
// ============================================================================

function alignUp(address, alignment) {
    if (!Number.isInteger(address) || address < 0) {
        throw new RangeError("Address must be a non-negative integer.");
    }

    if (
        !Number.isInteger(alignment) ||
        alignment <= 0 ||
        (alignment & (alignment - 1)) !== 0
    ) {
        throw new RangeError("Alignment must be a positive power of two.");
    }

    return Math.ceil(address / alignment) * alignment;
}

function demonstrateAlignment() {
    console.log("\n" + "=".repeat(78));
    console.log("8. MEMORY ALIGNMENT");
    console.log("=".repeat(78));

    for (const address of [0, 1, 7, 8, 9, 15, 16, 17]) {
        console.log(
            `address=${address.toString().padStart(2)} -> ` +
            `aligned=${alignUp(address, 8)}`
        );
    }

    console.log(
        "\nAlignment can reduce inefficient accesses but can introduce padding."
    );
}


// ============================================================================
// 9. REFERENCES, IDENTITY, AND SHALLOW COPIES
// ============================================================================

function demonstrateReferences() {
    console.log("\n" + "=".repeat(78));
    console.log("9. JAVASCRIPT REFERENCES AND OBJECT IDENTITY");
    console.log("=".repeat(78));

    const first = [10, 20, 30];
    const second = first;

    console.log("first === second:", first === second);

    second.push(40);

    console.log("first:", first);
    console.log("second:", second);

    // Spread syntax creates a new outer array.
    const independent = [...first];
    independent.push(50);

    console.log("\nIndependent outer copy:");
    console.log("first:", first);
    console.log("independent:", independent);
    console.log("first === independent:", first === independent);

    const nested = [[1, 2], [3, 4]];
    const shallow = [...nested];

    nested[0].push(99);

    console.log("\nNested shallow-copy behavior:");
    console.log("nested:", nested);
    console.log("shallow:", shallow);

    console.log(
        "\nA shallow copy duplicates the outer container while preserving " +
        "references to nested objects."
    );
}


// ============================================================================
// 10. GARBAGE COLLECTION AND MEMORY RETENTION
// ============================================================================

function demonstrateMemoryRetention() {
    console.log("\n" + "=".repeat(78));
    console.log("10. MEMORY RETENTION AND GARBAGE COLLECTION");
    console.log("=".repeat(78));

    const retainedObjects = [];

    for (let i = 0; i < 10; i++) {
        retainedObjects.push(new Array(10_000).fill(i));
    }

    console.log("Objects still intentionally reachable:", retainedObjects.length);

    retainedObjects.length = 0;

    console.log(
        "References released. The JavaScript runtime may reclaim the objects "
        + "during a later garbage-collection cycle."
    );

    console.log(
        "\nA JavaScript program normally does not explicitly free individual "
        + "objects. Memory is reclaimed when objects become unreachable."
    );
}


// ============================================================================
// 11. VIRTUAL MEMORY ADDRESS TRANSLATION
// ============================================================================

class VirtualMemorySimulator {
    constructor(pageSize, physicalFrameCount) {
        if (
            !Number.isInteger(pageSize) ||
            pageSize <= 0 ||
            (pageSize & (pageSize - 1)) !== 0
        ) {
            throw new RangeError("Page size must be a positive power of two.");
        }

        this.pageSize = pageSize;
        this.physicalFrameCount = physicalFrameCount;
        this.pageTable = new Map();
    }

    mapPage(virtualPage, physicalFrame) {
        if (virtualPage < 0 || !Number.isInteger(virtualPage)) {
            throw new RangeError("Virtual page must be a non-negative integer.");
        }

        if (
            physicalFrame < 0 ||
            physicalFrame >= this.physicalFrameCount
        ) {
            throw new RangeError("Invalid physical frame.");
        }

        this.pageTable.set(virtualPage, physicalFrame);
    }

    translate(virtualAddress) {
        if (!Number.isInteger(virtualAddress) || virtualAddress < 0) {
            throw new RangeError("Virtual address must be non-negative.");
        }

        const virtualPage = Math.floor(
            virtualAddress / this.pageSize
        );

        const offset = virtualAddress % this.pageSize;

        if (!this.pageTable.has(virtualPage)) {
            throw new MemoryAccessError(
                `Page fault for virtual page ${virtualPage}.`
            );
        }

        const physicalFrame = this.pageTable.get(virtualPage);

        return {
            virtualPage,
            offset,
            physicalFrame,
            physicalAddress:
                physicalFrame * this.pageSize + offset
        };
    }
}

function demonstrateVirtualMemory() {
    console.log("\n" + "=".repeat(78));
    console.log("11. VIRTUAL MEMORY ADDRESS TRANSLATION");
    console.log("=".repeat(78));

    const virtualMemory = new VirtualMemorySimulator(256, 8);

    virtualMemory.mapPage(0, 3);
    virtualMemory.mapPage(1, 7);
    virtualMemory.mapPage(2, 1);

    for (const virtualAddress of [0, 10, 255, 256, 300, 512, 700]) {
        try {
            const result = virtualMemory.translate(virtualAddress);

            console.log(
                `virtual=${virtualAddress} -> ` +
                `page=${result.virtualPage}, ` +
                `offset=${result.offset}, ` +
                `frame=${result.physicalFrame}, ` +
                `physical=${result.physicalAddress}`
            );
        } catch (error) {
            console.log(
                `virtual=${virtualAddress} -> ${error.message}`
            );
        }
    }
}


// ============================================================================
// 12. BUFFER AND BINARY DATA PROCESSING
// ============================================================================

function demonstrateBinaryData() {
    console.log("\n" + "=".repeat(78));
    console.log("12. BINARY DATA AND BUFFERS");
    console.log("=".repeat(78));

    const buffer = new ArrayBuffer(16);
    const bytes = new Uint8Array(buffer);
    const integers = new Uint32Array(buffer);

    bytes[0] = 0x78;
    bytes[1] = 0x56;
    bytes[2] = 0x34;
    bytes[3] = 0x12;

    console.log("Bytes:", Array.from(bytes.slice(0, 4)));
    console.log(
        "Uint32 interpretation depends on the machine's byte order:",
        integers[0]
    );

    console.log(
        "\nTyped arrays allow JavaScript programs to work with fixed-width "
        + "binary representations useful in files, networking, graphics, "
        + "WebAssembly interfaces, and systems-oriented programming."
    );
}


// ============================================================================
// 13. ASYNCHRONOUS MEMORY WORKLOAD
// ============================================================================

function delay(milliseconds) {
    return new Promise(resolve => setTimeout(resolve, milliseconds));
}

async function asynchronousMemoryWorkload() {
    console.log("\n" + "=".repeat(78));
    console.log("13. ASYNCHRONOUS APPLICATION MEMORY");
    console.log("=".repeat(78));

    const buffers = [];

    for (let iteration = 1; iteration <= 5; iteration++) {
        await delay(5);

        buffers.push(new Uint8Array(64 * 1024));

        console.log(
            `iteration=${iteration}, ` +
            `application buffer count=${buffers.length}, ` +
            `logical buffer memory=${formatBytes(buffers.length * 64 * 1024)}`
        );
    }

    buffers.length = 0;

    console.log(
        "\nReferences were released. Actual reclamation timing is controlled "
        + "by the JavaScript runtime and is not guaranteed to be immediate."
    );
}


// ============================================================================
// 14. NODE.JS SYSTEM MEMORY OBSERVATION
// ============================================================================

function showNodeMemoryStatistics() {
    console.log("\n" + "=".repeat(78));
    console.log("14. NODE.JS MEMORY STATISTICS");
    console.log("=".repeat(78));

    if (typeof process === "undefined" || !process.memoryUsage) {
        console.log("Node.js process memory APIs are unavailable.");
        return;
    }

    const usage = process.memoryUsage();

    for (const [name, value] of Object.entries(usage)) {
        console.log(`${name.padEnd(14)} ${formatBytes(value)}`);
    }

    console.log(
        "\nThese values describe memory associated with the Node.js process. "
        + "They are not a direct replacement for an operating system's complete "
        + "physical-RAM monitoring facilities."
    );
}


// ============================================================================
// 15. CACHE LOCALITY SIMULATION
// ============================================================================

function sequentialArrayAccess(size) {
    const data = new Int32Array(size);

    for (let i = 0; i < size; i++) {
        data[i] = i;
    }

    return data;
}

function sumSequential(data) {
    let total = 0;

    for (let i = 0; i < data.length; i++) {
        total += data[i];
    }

    return total;
}

function sumStrided(data, stride) {
    let total = 0;

    for (let offset = 0; offset < stride; offset++) {
        for (let index = offset; index < data.length; index += stride) {
            total += data[index];
        }
    }

    return total;
}

function demonstrateLocality() {
    console.log("\n" + "=".repeat(78));
    console.log("15. CACHE LOCALITY");
    console.log("=".repeat(78));

    const data = sequentialArrayAccess(2_000_000);

    let start = process.hrtime.bigint();
    const sequentialResult = sumSequential(data);
    let sequentialTime = Number(process.hrtime.bigint() - start) / 1e6;

    start = process.hrtime.bigint();
    const stridedResult = sumStrided(data, 64);
    let stridedTime = Number(process.hrtime.bigint() - start) / 1e6;

    console.log("Sequential result:", sequentialResult);
    console.log("Strided result:   ", stridedResult);
    console.log(`Sequential time:   ${sequentialTime.toFixed(3)} ms`);
    console.log(`Strided time:      ${stridedTime.toFixed(3)} ms`);

    console.log(
        "\nTiming varies by CPU, runtime, operating-system load, and JIT behavior. "
        + "The conceptual principle is spatial locality: nearby memory addresses "
        + "are often transferred together into cache lines."
    );
}


// ============================================================================
// 16. MEMORY PROTECTION MODEL
// ============================================================================

class ProtectedRegion {
    constructor(start, end, permissions, owner) {
        this.start = start;
        this.end = end;
        this.permissions = new Set(permissions);
        this.owner = owner;
    }

    allows(operation) {
        return this.permissions.has(operation);
    }
}

class ProtectedMemory {
    constructor(size) {
        this.size = size;
        this.regions = [];
    }

    addRegion(start, end, permissions, owner) {
        if (
            start < 0 ||
            end <= start ||
            end > this.size
        ) {
            throw new RangeError("Invalid protected-memory region.");
        }

        this.regions.push(
            new ProtectedRegion(start, end, permissions, owner)
        );
    }

    check(address, operation) {
        const region = this.regions.find(
            candidate =>
                address >= candidate.start &&
                address < candidate.end
        );

        return region ? region.allows(operation) : false;
    }
}

function demonstrateProtection() {
    console.log("\n" + "=".repeat(78));
    console.log("16. MEMORY PROTECTION");
    console.log("=".repeat(78));

    const memory = new ProtectedMemory(1024);

    memory.addRegion(0, 256, ["read", "execute"], "Code");
    memory.addRegion(256, 768, ["read", "write"], "Data");
    memory.addRegion(768, 1024, ["read"], "Read-only data");

    const tests = [
        [100, "read"],
        [100, "write"],
        [100, "execute"],
        [500, "write"],
        [500, "execute"],
        [900, "write"]
    ];

    for (const [address, operation] of tests) {
        console.log(
            `address=${address}, operation=${operation}, ` +
            `allowed=${memory.check(address, operation)}`
        );
    }

    console.log(
        "\nActual process isolation and memory permissions are enforced by the "
        + "operating system and CPU memory-management hardware."
    );
}


// ============================================================================
// 17. ERROR HANDLING AND EDGE CASES
// ============================================================================

function demonstrateEdgeCases() {
    console.log("\n" + "=".repeat(78));
    console.log("17. EDGE CASES AND ERROR HANDLING");
    console.log("=".repeat(78));

    const ram = new SimulatedRAM(8);

    const tests = [
        ["negative address", () => ram.readByte(-1)],
        ["out-of-range address", () => ram.readByte(8)],
        ["invalid byte", () => ram.writeByte(0, 256)]
    ];

    for (const [name, operation] of tests) {
        try {
            operation();
        } catch (error) {
            console.log(`${name.padEnd(22)} -> handled: ${error.message}`);
        }
    }

    const allocator = new FirstFitAllocator(32);

    try {
        allocator.allocate(64, "Too Large");
    } catch (error) {
        console.log(`oversized allocation   -> handled: ${error.message}`);
    }

    const id = allocator.allocate(16, "Temporary");
    allocator.free(id);

    try {
        allocator.free(id);
    } catch (error) {
        console.log(`double free             -> handled: ${error.message}`);
    }
}


// ============================================================================
// 18. INTEGRATED PROCESS AND MEMORY MANAGER
// ============================================================================

class MemoryManager {
    constructor(capacity) {
        this.allocator = new FirstFitAllocator(capacity);
        this.processes = new Map();
        this.nextProcessId = 1;
    }

    createProcess(name, memoryRequired) {
        const processId = this.nextProcessId++;

        const allocationId = this.allocator.allocate(
            memoryRequired,
            `Process ${processId}: ${name}`
        );

        this.processes.set(processId, {
            processId,
            name,
            allocationId,
            state: "running"
        });

        return processId;
    }

    terminateProcess(processId) {
        const process = this.processes.get(processId);

        if (!process) {
            throw new Error(`Process ${processId} does not exist.`);
        }

        if (process.state === "terminated") {
            throw new Error(`Process ${processId} is already terminated.`);
        }

        this.allocator.free(process.allocationId);
        process.state = "terminated";
    }

    report() {
        console.log("\nProcess table:");

        for (const process of this.processes.values()) {
            console.log(
                `PID=${process.processId} ` +
                `name=${process.name} ` +
                `state=${process.state} ` +
                `allocation=${process.allocationId}`
            );
        }

        this.allocator.printState();
    }
}

function demonstrateIntegratedSystem() {
    console.log("\n" + "=".repeat(78));
    console.log("18. INTEGRATED MEMORY MANAGEMENT CASE");
    console.log("=".repeat(78));

    const manager = new MemoryManager(1024);

    const browser = manager.createProcess("Browser", 300);
    const editor = manager.createProcess("Editor", 180);
    const database = manager.createProcess("Database", 350);

    console.log(
        `Created processes: ${browser}, ${editor}, ${database}`
    );

    manager.report();

    console.log("\nTerminating Editor...");
    manager.terminateProcess(editor);
    manager.report();

    console.log("\nCreating Compiler...");
    const compiler = manager.createProcess("Compiler", 160);

    console.log("Compiler PID:", compiler);
    manager.report();
}


// ============================================================================
// 19. KNOWLEDGE CHECK
// ============================================================================

function knowledgeCheck() {
    console.log("\n" + "=".repeat(78));
    console.log("19. KNOWLEDGE CHECK");
    console.log("=".repeat(78));

    const questions = [
        [
            "What is the key refresh property of DRAM?",
            "Stored charge must be periodically refreshed."
        ],
        [
            "What does a byte address identify?",
            "A byte location in a byte-addressable address space."
        ],
        [
            "What is external fragmentation?",
            "Free memory exists in separated blocks rather than one sufficiently large contiguous block."
        ],
        [
            "What is locality?",
            "Programs often access data and instructions with spatial or temporal patterns that cache systems can exploit."
        ],
        [
            "What is virtual address translation?",
            "Mapping a process-visible virtual address to a physical memory location or another backing resource."
        ]
    ];

    questions.forEach(([question, answer], index) => {
        console.log(`\n${index + 1}. ${question}`);
        console.log(`   Answer: ${answer}`);
    });
}


// ============================================================================
// 20. MAIN
// ============================================================================

async function main() {
    console.log("=".repeat(78));
    console.log("MAIN MEMORY STUDY PROGRAM");
    console.log("RAM | DRAM | SRAM | ADDRESSING | ALLOCATION | PROTECTION");
    console.log("=".repeat(78));

    showMemoryUnits();
    demonstrateByteAddressing();
    demonstrateSimulatedRAM();
    demonstrateDRAMAndSRAM();
    showMemoryHierarchy();
    demonstrateAllocation();
    demonstrateAllocationStrategies();
    demonstrateAlignment();
    demonstrateReferences();
    demonstrateMemoryRetention();
    demonstrateVirtualMemory();
    demonstrateBinaryData();
    await asynchronousMemoryWorkload();
    showNodeMemoryStatistics();
    demonstrateLocality();
    demonstrateProtection();
    demonstrateEdgeCases();
    demonstrateIntegratedSystem();
    knowledgeCheck();

    console.log("\n" + "=".repeat(78));
    console.log("END OF MAIN MEMORY STUDY PROGRAM");
    console.log("=".repeat(78));
}

main().catch(error => {
    console.error("\nFatal error:", error);
    process.exitCode = 1;
});
