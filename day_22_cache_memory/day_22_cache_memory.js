/*
 * Cache Memory and Cache Simulator
 * =================================
 *
 * Topics demonstrated:
 * - Cache levels
 * - Cache lines and blocks
 * - Tags, indexes, and offsets
 * - Cache hits and misses
 * - Temporal and spatial locality
 * - Direct mapping
 * - Set associativity
 * - Fully associative mapping
 * - LRU and FIFO replacement
 * - Write-back and write-through
 * - Write-allocate and no-write-allocate
 * - Cache statistics
 * - Multi-level cache simulation
 * - AMAT
 * - Memory-access traces
 * - Edge cases
 *
 * This file uses standard JavaScript and can run with:
 *
 *     node cache_simulator.js
 *
 * No external packages are required.
 */

"use strict";

// ---------------------------------------------------------------------------
// Utility functions
// ---------------------------------------------------------------------------

function isPowerOfTwo(value) {
    return Number.isInteger(value) && value > 0 && (value & (value - 1)) === 0;
}

function integerLog2(value) {
    if (!isPowerOfTwo(value)) {
        throw new Error(`${value} must be a positive power of two.`);
    }

    return Math.log2(value);
}

function validateOperation(operation) {
    if (operation !== "read" && operation !== "write") {
        throw new Error('Operation must be "read" or "write".');
    }
}

// ---------------------------------------------------------------------------
// Address decomposition
// ---------------------------------------------------------------------------
//
// A byte address is interpreted as:
//
//     [ tag | set index | block offset ]
//
// blockNumber = floor(address / blockSize)
// offset      = address % blockSize
// setIndex    = blockNumber % numberOfSets
// tag         = floor(blockNumber / numberOfSets)
// ---------------------------------------------------------------------------

function decomposeAddress(address, blockSize, numberOfSets) {
    if (!Number.isInteger(address) || address < 0) {
        throw new Error("Address must be a non-negative integer.");
    }

    const blockNumber = Math.floor(address / blockSize);
    const offset = address % blockSize;
    const setIndex = blockNumber % numberOfSets;
    const tag = Math.floor(blockNumber / numberOfSets);

    return {
        blockNumber,
        offset,
        setIndex,
        tag
    };
}

function explainAddress(address, cacheSize, blockSize, associativity) {
    if (
        cacheSize <= 0 ||
        blockSize <= 0 ||
        associativity <= 0
    ) {
        throw new Error("Cache parameters must be positive.");
    }

    if (
        !isPowerOfTwo(cacheSize) ||
        !isPowerOfTwo(blockSize) ||
        !isPowerOfTwo(associativity)
    ) {
        throw new Error(
            "Cache size, block size, and associativity must be powers of two."
        );
    }

    const numberOfLines = cacheSize / blockSize;
    const numberOfSets = numberOfLines / associativity;

    if (!Number.isInteger(numberOfSets) || numberOfSets <= 0) {
        throw new Error("Invalid cache geometry.");
    }

    const fields = decomposeAddress(
        address,
        blockSize,
        numberOfSets
    );

    console.log("\nADDRESS DECOMPOSITION");
    console.log("---------------------");
    console.log(`Address:       ${address}`);
    console.log(`Block number:  ${fields.blockNumber}`);
    console.log(`Offset:        ${fields.offset}`);
    console.log(`Set index:     ${fields.setIndex}`);
    console.log(`Tag:           ${fields.tag}`);
    console.log(`Offset bits:   ${integerLog2(blockSize)}`);
    console.log(
        `Index bits:    ${numberOfSets === 1 ? 0 : integerLog2(numberOfSets)}`
    );
}

// ---------------------------------------------------------------------------
// Cache line
// ---------------------------------------------------------------------------

class CacheLine {
    constructor() {
        this.valid = false;
        this.tag = 0;
        this.dirty = false;
        this.lastUsed = 0;
        this.insertedAt = 0;
    }
}

// ---------------------------------------------------------------------------
// Cache statistics
// ---------------------------------------------------------------------------

class CacheStatistics {
    constructor() {
        this.accesses = 0;
        this.hits = 0;
        this.misses = 0;
        this.compulsoryMisses = 0;
        this.conflictMisses = 0;
        this.capacityMisses = 0;
        this.writeHits = 0;
        this.writeMisses = 0;
        this.writeBacks = 0;
    }

    get hitRate() {
        return this.accesses === 0 ? 0 : this.hits / this.accesses;
    }

    get missRate() {
        return this.accesses === 0 ? 0 : this.misses / this.accesses;
    }

    print(name) {
        console.log(`\n${name}`);
        console.log("-".repeat(name.length));
        console.log(`Accesses:           ${this.accesses}`);
        console.log(`Hits:               ${this.hits}`);
        console.log(`Misses:             ${this.misses}`);
        console.log(`Hit rate:           ${(this.hitRate * 100).toFixed(2)}%`);
        console.log(`Miss rate:          ${(this.missRate * 100).toFixed(2)}%`);
        console.log(`Compulsory misses:  ${this.compulsoryMisses}`);
        console.log(`Conflict misses:    ${this.conflictMisses}`);
        console.log(`Capacity misses:    ${this.capacityMisses}`);
        console.log(`Write hits:         ${this.writeHits}`);
        console.log(`Write misses:       ${this.writeMisses}`);
        console.log(`Write-backs:        ${this.writeBacks}`);
    }
}

// ---------------------------------------------------------------------------
// Cache simulator
// ---------------------------------------------------------------------------

class CacheSimulator {
    constructor({
        cacheSize,
        blockSize,
        associativity = 1,
        hitLatency = 1,
        missLatency = 50,
        replacementPolicy = "LRU",
        writePolicy = "write-back",
        allocationPolicy = "write-allocate"
    }) {
        if (!Number.isInteger(cacheSize) || cacheSize <= 0) {
            throw new Error("cacheSize must be a positive integer.");
        }

        if (!Number.isInteger(blockSize) || blockSize <= 0) {
            throw new Error("blockSize must be a positive integer.");
        }

        if (!isPowerOfTwo(cacheSize) || !isPowerOfTwo(blockSize)) {
            throw new Error("cacheSize and blockSize must be powers of two.");
        }

        if (cacheSize < blockSize) {
            throw new Error("cacheSize cannot be smaller than blockSize.");
        }

        const numberOfLines = cacheSize / blockSize;

        if (!Number.isInteger(associativity) || associativity <= 0) {
            throw new Error("associativity must be positive.");
        }

        if (
            !isPowerOfTwo(associativity) ||
            associativity > numberOfLines ||
            numberOfLines % associativity !== 0
        ) {
            throw new Error("Invalid associativity.");
        }

        if (!["LRU", "FIFO"].includes(replacementPolicy)) {
            throw new Error("Replacement policy must be LRU or FIFO.");
        }

        if (!["write-back", "write-through"].includes(writePolicy)) {
            throw new Error(
                "Write policy must be write-back or write-through."
            );
        }

        if (
            !["write-allocate", "no-write-allocate"].includes(
                allocationPolicy
            )
        ) {
            throw new Error(
                "Allocation policy must be write-allocate or no-write-allocate."
            );
        }

        this.cacheSize = cacheSize;
        this.blockSize = blockSize;
        this.associativity = associativity;
        this.numberOfLines = numberOfLines;
        this.numberOfSets = numberOfLines / associativity;
        this.hitLatency = hitLatency;
        this.missLatency = missLatency;
        this.replacementPolicy = replacementPolicy;
        this.writePolicy = writePolicy;
        this.allocationPolicy = allocationPolicy;

        this.reset();
    }

    reset() {
        this.sets = Array.from(
            { length: this.numberOfSets },
            () =>
                Array.from(
                    { length: this.associativity },
                    () => new CacheLine()
                )
        );

        this.statistics = new CacheStatistics();
        this.clock = 0;
        this.seenBlocks = new Set();
        this.evictedBlocks = new Set();
    }

    findLine(setIndex, tag) {
        return this.sets[setIndex].find(
            line => line.valid && line.tag === tag
        ) || null;
    }

    chooseVictim(setIndex) {
        const currentSet = this.sets[setIndex];

        const invalidLine = currentSet.find(line => !line.valid);

        if (invalidLine) {
            return invalidLine;
        }

        if (this.replacementPolicy === "LRU") {
            return currentSet.reduce(
                (oldest, line) =>
                    line.lastUsed < oldest.lastUsed ? line : oldest,
                currentSet[0]
            );
        }

        return currentSet.reduce(
            (oldest, line) =>
                line.insertedAt < oldest.insertedAt ? line : oldest,
            currentSet[0]
        );
    }

    classifyMiss(blockNumber) {
        if (!this.seenBlocks.has(blockNumber)) {
            return "compulsory";
        }

        if (this.evictedBlocks.has(blockNumber)) {
            return this.associativity === 1
                ? "conflict"
                : "capacity-or-conflict";
        }

        return "unknown";
    }

    recordMissClassification(classification) {
        if (classification === "compulsory") {
            this.statistics.compulsoryMisses++;
        } else if (classification === "conflict") {
            this.statistics.conflictMisses++;
        } else if (classification === "capacity-or-conflict") {
            this.statistics.capacityMisses++;
        }
    }

    access(address, operation = "read", verbose = false) {
        validateOperation(operation);

        if (!Number.isInteger(address) || address < 0) {
            throw new Error("Address must be a non-negative integer.");
        }

        this.clock++;
        this.statistics.accesses++;

        const fields = decomposeAddress(
            address,
            this.blockSize,
            this.numberOfSets
        );

        const {
            blockNumber,
            setIndex,
            tag
        } = fields;

        const line = this.findLine(setIndex, tag);

        if (line) {
            this.statistics.hits++;

            if (operation === "write") {
                this.statistics.writeHits++;

                if (this.writePolicy === "write-back") {
                    line.dirty = true;
                } else {
                    line.dirty = false;
                }
            }

            line.lastUsed = this.clock;

            const result = {
                address,
                blockNumber,
                setIndex,
                tag,
                hit: true,
                latency: this.hitLatency,
                evictedTag: null,
                dirtyEviction: false
            };

            if (verbose) {
                this.printAccess(result, operation);
            }

            return result;
        }

        this.statistics.misses++;

        if (operation === "write") {
            this.statistics.writeMisses++;
        }

        const classification = this.classifyMiss(blockNumber);

        this.recordMissClassification(classification);
        this.seenBlocks.add(blockNumber);

        // A no-write-allocate write miss bypasses the cache.
        if (
            operation === "write" &&
            this.allocationPolicy === "no-write-allocate"
        ) {
            const result = {
                address,
                blockNumber,
                setIndex,
                tag,
                hit: false,
                latency: this.missLatency,
                evictedTag: null,
                dirtyEviction: false
            };

            if (verbose) {
                this.printAccess(result, operation);
            }

            return result;
        }

        const victim = this.chooseVictim(setIndex);

        let evictedTag = null;
        let dirtyEviction = false;

        if (victim.valid) {
            evictedTag = victim.tag;
            dirtyEviction = victim.dirty;

            const evictedBlock =
                victim.tag * this.numberOfSets + setIndex;

            this.evictedBlocks.add(evictedBlock);

            if (
                victim.dirty &&
                this.writePolicy === "write-back"
            ) {
                this.statistics.writeBacks++;
            }
        }

        victim.valid = true;
        victim.tag = tag;
        victim.lastUsed = this.clock;
        victim.insertedAt = this.clock;

        victim.dirty =
            operation === "write" &&
            this.writePolicy === "write-back";

        const result = {
            address,
            blockNumber,
            setIndex,
            tag,
            hit: false,
            latency: this.hitLatency + this.missLatency,
            evictedTag,
            dirtyEviction
        };

        if (verbose) {
            this.printAccess(result, operation);
        }

        return result;
    }

    printAccess(result, operation) {
        const status = result.hit ? "HIT " : "MISS";

        let extra = "";

        if (result.evictedTag !== null) {
            extra += ` evictedTag=${result.evictedTag}`;
        }

        if (result.dirtyEviction) {
            extra += " dirtyWriteback=true";
        }

        console.log(
            `${operation.toUpperCase().padEnd(5)} ` +
            `address=${String(result.address).padStart(4)} ` +
            `block=${String(result.blockNumber).padStart(3)} ` +
            `set=${String(result.setIndex).padStart(2)} ` +
            `tag=${String(result.tag).padStart(3)} ` +
            `${status} latency=${String(result.latency).padStart(3)}` +
            extra
        );
    }

    run(addresses, operation = "read", verbose = false) {
        return addresses.map(
            address => this.access(address, operation, verbose)
        );
    }

    describe() {
        const mapping =
            this.associativity === 1
                ? "direct-mapped"
                : this.associativity === this.numberOfLines
                    ? "fully-associative"
                    : "set-associative";

        console.log("\nCACHE CONFIGURATION");
        console.log("-------------------");
        console.log(`Capacity:           ${this.cacheSize} bytes`);
        console.log(`Block size:         ${this.blockSize} bytes`);
        console.log(`Lines:              ${this.numberOfLines}`);
        console.log(`Sets:               ${this.numberOfSets}`);
        console.log(`Associativity:      ${this.associativity}-way`);
        console.log(`Mapping:            ${mapping}`);
        console.log(`Replacement:        ${this.replacementPolicy}`);
        console.log(`Write policy:       ${this.writePolicy}`);
        console.log(`Allocation policy:  ${this.allocationPolicy}`);
        console.log(`Hit latency:        ${this.hitLatency}`);
        console.log(`Miss penalty:       ${this.missLatency}`);
    }

    dump() {
        console.log("\nCACHE CONTENTS");
        console.log("--------------");

        this.sets.forEach((currentSet, setIndex) => {
            const entries = currentSet.map((line, way) => {
                if (!line.valid) {
                    return `way ${way}: EMPTY`;
                }

                const dirty = line.dirty ? "*" : "";

                return `way ${way}: tag=${line.tag}${dirty}`;
            });

            console.log(`Set ${setIndex}: ${entries.join(" | ")}`);
        });
    }
}

// ---------------------------------------------------------------------------
// Locality demonstrations
// ---------------------------------------------------------------------------

function demonstrateLocality() {
    console.log("\nLOCALITY");
    console.log("========");

    const cache = new CacheSimulator({
        cacheSize: 64,
        blockSize: 16,
        associativity: 2,
        missLatency: 20
    });

    const sequential = [];

    for (let address = 0; address < 64; address += 4) {
        sequential.push(address);
    }

    cache.run(sequential, "read", true);
    cache.statistics.print("Sequential access");

    cache.reset();

    const temporal = [
        0, 4, 8, 0, 4, 8,
        0, 4, 8, 0, 4, 8
    ];

    cache.run(temporal);
    cache.statistics.print("Temporal locality");
}

// ---------------------------------------------------------------------------
// Mapping comparison
// ---------------------------------------------------------------------------

function compareMappingTechniques() {
    console.log("\nMAPPING TECHNIQUES");
    console.log("==================");

    const addresses = [
        0, 32, 64, 96,
        0, 32, 64, 96,
        0, 32, 64, 96
    ];

    const configurations = [
        ["Direct mapped", 1],
        ["2-way set associative", 2],
        ["Fully associative", 8]
    ];

    for (const [name, associativity] of configurations) {
        const cache = new CacheSimulator({
            cacheSize: 64,
            blockSize: 8,
            associativity
        });

        cache.run(addresses);

        console.log(
            `${name.padEnd(28)} ` +
            `hits=${String(cache.statistics.hits).padStart(2)} ` +
            `misses=${String(cache.statistics.misses).padStart(2)} ` +
            `hitRate=${(cache.statistics.hitRate * 100).toFixed(2)}%`
        );
    }
}

// ---------------------------------------------------------------------------
// Replacement policy comparison
// ---------------------------------------------------------------------------

function compareReplacementPolicies() {
    console.log("\nREPLACEMENT POLICIES");
    console.log("====================");

    const trace = [0, 8, 16, 0, 8, 24, 0, 8];

    for (const policy of ["LRU", "FIFO"]) {
        const cache = new CacheSimulator({
            cacheSize: 16,
            blockSize: 8,
            associativity: 2,
            replacementPolicy: policy
        });

        cache.run(trace);

        console.log(
            `${policy}: ` +
            `hits=${cache.statistics.hits}, ` +
            `misses=${cache.statistics.misses}, ` +
            `hitRate=${(cache.statistics.hitRate * 100).toFixed(2)}%`
        );
    }
}

// ---------------------------------------------------------------------------
// Write policy demonstration
// ---------------------------------------------------------------------------

function demonstrateWritePolicies() {
    console.log("\nWRITE POLICIES");
    console.log("==============");

    const trace = [
        ["write", 0],
        ["read", 0],
        ["write", 0],
        ["write", 16],
        ["read", 0]
    ];

    for (const writePolicy of ["write-back", "write-through"]) {
        const cache = new CacheSimulator({
            cacheSize: 16,
            blockSize: 8,
            associativity: 1,
            writePolicy,
            allocationPolicy: "write-allocate"
        });

        console.log(`\n${writePolicy}`);

        for (const [operation, address] of trace) {
            cache.access(address, operation, true);
        }

        cache.statistics.print(writePolicy);
    }
}

// ---------------------------------------------------------------------------
// Multi-level cache
// ---------------------------------------------------------------------------

function demonstrateMultiLevelCache() {
    console.log("\nMULTI-LEVEL CACHE");
    console.log("=================");

    const l1 = new CacheSimulator({
        cacheSize: 32,
        blockSize: 8,
        associativity: 2,
        hitLatency: 1,
        missLatency: 4
    });

    const l2 = new CacheSimulator({
        cacheSize: 128,
        blockSize: 8,
        associativity: 4,
        hitLatency: 8,
        missLatency: 40
    });

    const trace = [
        0, 8, 16, 24,
        0, 8, 64, 72,
        0, 8
    ];

    let totalCycles = 0;

    for (const address of trace) {
        const l1Result = l1.access(address);

        if (l1Result.hit) {
            totalCycles += l1.hitLatency;
            console.log(`address=${address} -> L1 HIT`);
            continue;
        }

        const l2Result = l2.access(address);

        if (l2Result.hit) {
            totalCycles += l1.missLatency + l2.hitLatency;
            console.log(
                `address=${address} -> L1 MISS, L2 HIT`
            );
        } else {
            totalCycles +=
                l1.missLatency +
                l2.missLatency;

            console.log(
                `address=${address} -> L1 MISS, L2 MISS, RAM`
            );
        }
    }

    console.log(`Estimated cycles: ${totalCycles}`);

    l1.statistics.print("L1");
    l2.statistics.print("L2");
}

// ---------------------------------------------------------------------------
// AMAT
// ---------------------------------------------------------------------------

function calculateAMAT(hitTime, missRate, missPenalty) {
    if (
        hitTime < 0 ||
        missRate < 0 ||
        missRate > 1 ||
        missPenalty < 0
    ) {
        throw new Error("Invalid AMAT inputs.");
    }

    return hitTime + missRate * missPenalty;
}

function demonstrateAMAT() {
    console.log("\nAVERAGE MEMORY ACCESS TIME");
    console.log("==========================");

    const examples = [
        [1, 0.05, 50],
        [1, 0.10, 50],
        [2, 0.02, 80]
    ];

    for (const [hitTime, missRate, penalty] of examples) {
        const amat = calculateAMAT(
            hitTime,
            missRate,
            penalty
        );

        console.log(
            `hit=${hitTime}, ` +
            `missRate=${(missRate * 100).toFixed(1)}%, ` +
            `penalty=${penalty} ` +
            `=> AMAT=${amat.toFixed(2)}`
        );
    }
}

// ---------------------------------------------------------------------------
// Matrix traversal
// ---------------------------------------------------------------------------

function rowMajorMatrixAccess(rows, columns) {
    const trace = [];

    for (let row = 0; row < rows; row++) {
        for (let column = 0; column < columns; column++) {
            trace.push(row * columns + column);
        }
    }

    return trace;
}

function columnWiseMatrixAccess(rows, columns) {
    const trace = [];

    for (let column = 0; column < columns; column++) {
        for (let row = 0; row < rows; row++) {
            trace.push(row * columns + column);
        }
    }

    return trace;
}

function demonstrateMatrixTraversal() {
    console.log("\nMATRIX TRAVERSAL");
    console.log("================");

    const rowTrace = rowMajorMatrixAccess(16, 16);
    const columnTrace = columnWiseMatrixAccess(16, 16);

    for (const [name, trace] of [
        ["Row-major", rowTrace],
        ["Column-wise", columnTrace]
    ]) {
        const cache = new CacheSimulator({
            cacheSize: 128,
            blockSize: 16,
            associativity: 4
        });

        cache.run(trace);

        console.log(
            `${name.padEnd(14)} ` +
            `hits=${String(cache.statistics.hits).padStart(3)} ` +
            `misses=${String(cache.statistics.misses).padStart(3)} ` +
            `hitRate=${(cache.statistics.hitRate * 100).toFixed(2)}%`
        );
    }
}

// ---------------------------------------------------------------------------
// Edge cases
// ---------------------------------------------------------------------------

function demonstrateEdgeCases() {
    console.log("\nEDGE CASES");
    console.log("==========");

    const cache = new CacheSimulator({
        cacheSize: 16,
        blockSize: 4,
        associativity: 2
    });

    for (const address of [0, 3, 4, 7, 8, 12, 15, 16]) {
        const result = cache.access(address);

        console.log(
            `address=${String(address).padStart(2)} ` +
            `block=${String(result.blockNumber).padStart(2)} ` +
            `set=${result.setIndex} ` +
            `tag=${result.tag} ` +
            `hit=${result.hit}`
        );
    }

    try {
        new CacheSimulator({
            cacheSize: 16,
            blockSize: 3,
            associativity: 1
        });
    } catch (error) {
        console.log(`Rejected invalid block size: ${error.message}`);
    }

    try {
        cache.access(-1);
    } catch (error) {
        console.log(`Rejected invalid address: ${error.message}`);
    }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function main() {
    console.log("=".repeat(72));
    console.log("CACHE MEMORY AND CACHE SIMULATOR");
    console.log("=".repeat(72));

    console.log("\nCACHE LEVELS");
    console.log("============");
    console.log("L1: smallest and fastest cache level.");
    console.log("L2: larger and slower than L1.");
    console.log("L3: larger and commonly shared across CPU cores.");
    console.log("RAM: much larger but substantially slower than cache.");

    explainAddress(
        37,
        64,
        8,
        1
    );

    demonstrateLocality();
    compareMappingTechniques();
    compareReplacementPolicies();
    demonstrateWritePolicies();
    demonstrateMultiLevelCache();
    demonstrateAMAT();
    demonstrateMatrixTraversal();
    demonstrateEdgeCases();

    console.log("\nKEY FORMULAS");
    console.log("============");
    console.log("lines = cacheSize / blockSize");
    console.log("sets = lines / associativity");
    console.log("block = floor(address / blockSize)");
    console.log("offset = address % blockSize");
    console.log("set = block % sets");
    console.log("tag = floor(block / sets)");
    console.log("hitRate = hits / accesses");
    console.log("missRate = misses / accesses");
    console.log("AMAT = hitTime + missRate * missPenalty");

    console.log("\nSIMULATION COMPLETE");
}

main();
