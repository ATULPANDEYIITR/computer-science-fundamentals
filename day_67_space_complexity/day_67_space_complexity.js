"use strict";

/*
 * SPACE COMPLEXITY
 * Memory analysis, auxiliary space, and algorithmic trade-offs.
 *
 * Node.js implementation featuring:
 * - Memory-aware algorithm selection
 * - Iterative and recursive algorithms
 * - Buffer allocation and memory limits
 * - Map and Set storage
 * - Streaming aggregation
 * - Dynamic programming optimization
 * - Event-driven memory monitoring
 * - Asynchronous batch processing
 */

const { EventEmitter } = require("node:events");
const os = require("node:os");

class MemoryBudgetError extends Error {
    constructor(required, available) {
        super(
            `Memory budget exceeded: required ${required} bytes, available ${available} bytes`
        );
        this.name = "MemoryBudgetError";
        this.required = required;
        this.available = available;
    }
}

class MemoryPolicy {
    constructor(limitBytes) {
        if (!Number.isSafeInteger(limitBytes) || limitBytes < 0) {
            throw new RangeError("Memory limit must be a non-negative safe integer.");
        }

        this.limitBytes = limitBytes;
    }

    validate(requiredBytes) {
        if (!Number.isSafeInteger(requiredBytes) || requiredBytes < 0) {
            throw new RangeError("Invalid memory estimate.");
        }

        if (requiredBytes > this.limitBytes) {
            throw new MemoryBudgetError(requiredBytes, this.limitBytes);
        }

        return true;
    }
}

class MemoryMonitor extends EventEmitter {
    constructor(policy) {
        super();

        this.policy = policy;
        this.history = [];
    }

    record(label) {
        const usage = process.memoryUsage();

        const snapshot = Object.freeze({
            label,
            heapUsed: usage.heapUsed,
            heapTotal: usage.heapTotal,
            external: usage.external,
            arrayBuffers: usage.arrayBuffers,
            rss: usage.rss,
            timestamp: Date.now()
        });

        this.history.push(snapshot);
        this.emit("memory", snapshot);

        return snapshot;
    }

    getLatest() {
        return this.history.length
            ? this.history[this.history.length - 1]
            : null;
    }
}

function validateArray(values) {
    if (!Array.isArray(values)) {
        throw new TypeError("Expected an array.");
    }

    for (const value of values) {
        if (!Number.isFinite(value)) {
            throw new TypeError("All elements must be finite numbers.");
        }
    }
}

function sumInPlace(values) {
    validateArray(values);

    let total = 0;

    for (const value of values) {
        total += value;
    }

    return total;
}

function copyArray(values) {
    validateArray(values);
    return Array.from(values);
}

function reverseInPlace(values) {
    validateArray(values);

    let left = 0;
    let right = values.length - 1;

    while (left < right) {
        [values[left], values[right]] = [
            values[right],
            values[left]
        ];

        left++;
        right--;
    }

    return values;
}

function iterativeBinarySearch(values, target) {
    let left = 0;
    let right = values.length - 1;

    while (left <= right) {
        const middle = left + Math.floor((right - left) / 2);

        if (values[middle] === target) {
            return middle;
        }

        if (values[middle] < target) {
            left = middle + 1;
        } else {
            right = middle - 1;
        }
    }

    return -1;
}

function uniqueElements(values) {
    validateArray(values);

    const seen = new Set();
    const result = [];

    for (const value of values) {
        if (!seen.has(value)) {
            seen.add(value);
            result.push(value);
        }
    }

    return result;
}

function fibonacciTable(n) {
    validateN(n);

    if (n === 0) return 0;

    const dp = new Array(n + 1).fill(0);
    dp[1] = 1;

    for (let i = 2; i <= n; i++) {
        dp[i] = dp[i - 1] + dp[i - 2];
    }

    return dp[n];
}

function fibonacciConstantSpace(n) {
    validateN(n);

    let previous = 0;
    let current = 1;

    for (let i = 0; i < n; i++) {
        [previous, current] = [
            current,
            previous + current
        ];
    }

    return previous;
}

function validateN(n) {
    if (!Number.isSafeInteger(n) || n < 0 || n > 1000000) {
        throw new RangeError("n must be between 0 and 1,000,000.");
    }
}

function validateKnapsack(weights, values, capacity) {
    if (!Array.isArray(weights) || !Array.isArray(values)) {
        throw new TypeError("Weights and values must be arrays.");
    }

    if (weights.length !== values.length) {
        throw new RangeError("Weights and values must have equal lengths.");
    }

    if (!Number.isSafeInteger(capacity) || capacity < 0 || capacity > 1000000) {
        throw new RangeError("Invalid capacity.");
    }

    for (const weight of weights) {
        if (!Number.isSafeInteger(weight) || weight <= 0) {
            throw new RangeError("Weights must be positive integers.");
        }
    }

    for (const value of values) {
        if (!Number.isSafeInteger(value) || value < 0) {
            throw new RangeError("Values must be non-negative integers.");
        }
    }
}

function knapsackOptimized(weights, values, capacity) {
    validateKnapsack(weights, values, capacity);

    const dp = new Float64Array(capacity + 1);

    for (let i = 0; i < weights.length; i++) {
        const weight = weights[i];
        const value = values[i];

        // Descending iteration prevents using an item more than once.
        for (let current = capacity; current >= weight; current--) {
            dp[current] = Math.max(
                dp[current],
                value + dp[current - weight]
            );
        }
    }

    return dp[capacity];
}

function knapsackFull(weights, values, capacity) {
    validateKnapsack(weights, values, capacity);

    const rows = weights.length + 1;
    const columns = capacity + 1;

    const dp = Array.from(
        { length: rows },
        () => new Float64Array(columns)
    );

    for (let i = 1; i < rows; i++) {
        const weight = weights[i - 1];
        const value = values[i - 1];

        for (let current = 0; current < columns; current++) {
            dp[i][current] = dp[i - 1][current];

            if (weight <= current) {
                dp[i][current] = Math.max(
                    dp[i][current],
                    value + dp[i - 1][current - weight]
                );
            }
        }
    }

    return dp[rows - 1][capacity];
}

function estimateLinearMemory(count, bytesPerElement) {
    if (
        !Number.isSafeInteger(count) ||
        !Number.isSafeInteger(bytesPerElement) ||
        count < 0 ||
        bytesPerElement < 0
    ) {
        throw new RangeError("Invalid memory estimation parameters.");
    }

    const estimate = BigInt(count) * BigInt(bytesPerElement);

    if (estimate > BigInt(Number.MAX_SAFE_INTEGER)) {
        throw new RangeError("Estimated memory exceeds safe integer range.");
    }

    return Number(estimate);
}

async function processBatches(
    source,
    batchSize,
    processor,
    policy
) {
    if (!Number.isSafeInteger(batchSize) || batchSize <= 0) {
        throw new RangeError("Batch size must be positive.");
    }

    if (typeof processor !== "function") {
        throw new TypeError("Processor must be a function.");
    }

    const results = [];
    let batch = [];

    async function flush() {
        if (batch.length === 0) return;

        const currentBatch = batch;
        batch = [];

        const estimate = estimateLinearMemory(
            currentBatch.length,
            8
        );

        policy.validate(estimate);

        const processed = await processor(currentBatch);

        results.push(processed);
    }

    for await (const item of source) {
        batch.push(item);

        if (batch.length >= batchSize) {
            await flush();
        }
    }

    await flush();

    return results;
}

async function* numberGenerator(count) {
    for (let i = 0; i < count; i++) {
        yield i;
    }
}

function runTests() {
    console.assert(sumInPlace([1, 2, 3]) === 6);

    console.assert(
        JSON.stringify(copyArray([1, 2])) === "[1,2]"
    );

    console.assert(
        JSON.stringify(reverseInPlace([1, 2, 3])) === "[3,2,1]"
    );

    console.assert(
        iterativeBinarySearch([1, 3, 5, 7], 5) === 2
    );

    console.assert(
        JSON.stringify(uniqueElements([1, 1, 2, 3])) === "[1,2,3]"
    );

    console.assert(fibonacciTable(10) === 55);
    console.assert(fibonacciConstantSpace(10) === 55);

    const weights = [2, 3, 4, 5];
    const values = [3, 4, 5, 6];

    console.assert(knapsackFull(weights, values, 5) === 7);
    console.assert(knapsackOptimized(weights, values, 5) === 7);

    console.assert(estimateLinearMemory(100, 8) === 800);

    const policy = new MemoryPolicy(1024);
    console.assert(policy.validate(512));

    let rejected = false;

    try {
        policy.validate(2048);
    } catch (error) {
        rejected = error instanceof MemoryBudgetError;
    }

    console.assert(rejected);

    console.log("All JavaScript tests passed.");
}

async function main() {
    console.log("SPACE COMPLEXITY ANALYSIS");
    console.log("=========================");

    runTests();

    const monitor = new MemoryMonitor(
        new MemoryPolicy(1024 * 1024)
    );

    monitor.on("memory", (snapshot) => {
        console.log(
            `[MEMORY] ${snapshot.label}:`,
            `${(snapshot.heapUsed / 1024 / 1024).toFixed(2)} MB heap`
        );
    });

    monitor.record("Initial state");

    const input = Array.from({ length: 100000 }, (_, index) => index);

    console.log("\nALGORITHM COMPARISON");

    console.log("Input sum:", sumInPlace(input));
    console.log("Copied elements:", copyArray(input.slice(0, 5)));
    console.log("Optimized Fibonacci:", fibonacciConstantSpace(30));

    console.log(
        "Knapsack result:",
        knapsackOptimized([2, 3, 4, 5], [3, 4, 5, 6], 5)
    );

    monitor.record("After algorithm execution");

    console.log("\nSTREAMING BATCH PROCESSING");

    const policy = new MemoryPolicy(64 * 1024);

    const batchResults = await processBatches(
        numberGenerator(1000),
        100,
        async (batch) => {
            return batch.reduce((sum, value) => sum + value, 0);
        },
        policy
    );

    console.log("Number of batches:", batchResults.length);
    console.log(
        "Combined result:",
        batchResults.reduce((sum, value) => sum + value, 0)
    );

    console.log("\nMEMORY ESTIMATION");

    console.log(
        "100,000 numeric slots at 8 bytes each:",
        estimateLinearMemory(100000, 8),
        "bytes"
    );

    console.log(
        "System free memory:",
        os.freemem(),
        "bytes"
    );

    monitor.record("Final state");

    console.log("\nMEMORY HISTORY:", monitor.history.length, "snapshots");
    console.log("PROCESS COMPLETE");
}

main().catch((error) => {
    console.error("Execution failed:", error.message);
    process.exitCode = 1;
});
