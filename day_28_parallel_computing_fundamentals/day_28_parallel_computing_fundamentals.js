/*
 * Parallel Computing Fundamentals
 *
 * Topics:
 *   - concurrency and parallelism
 *   - multicore processors
 *   - worker threads
 *   - SIMD concepts
 *   - MIMD concepts
 *   - task and data parallelism
 *   - synchronization
 *   - load balancing
 *   - Amdahl's Law
 *   - performance measurement
 *
 * Runtime:
 *   Node.js 18+ is recommended.
 *
 * JavaScript normally executes application code on an event-loop thread.
 * Node.js Worker Threads provide actual parallel execution on multiple
 * CPU cores for suitable CPU-bound workloads.
 */

"use strict";

const {
    Worker,
    isMainThread,
    parentPort,
    workerData
} = require("node:worker_threads");

const os = require("node:os");
const { performance } = require("node:perf_hooks");

// ============================================================================
// Worker implementation
// ============================================================================

if (!isMainThread) {
    /*
     * Each Worker has its own JavaScript execution context.
     * Worker threads can execute CPU-intensive work in parallel with other
     * workers because the work is performed by separate threads.
     */
    const { type, payload } = workerData;

    try {
        if (type === "prime-count") {
            parentPort.postMessage({
                type,
                result: countPrimes(payload.start, payload.end)
            });
        } else if (type === "vector-add") {
            parentPort.postMessage({
                type,
                result: vectorAdd(payload.left, payload.right)
            });
        } else if (type === "statistics") {
            parentPort.postMessage({
                type,
                result: calculateStatistics(payload.values)
            });
        } else {
            throw new Error(`Unknown worker task: ${type}`);
        }
    } catch (error) {
        parentPort.postMessage({
            type: "error",
            message: error.message
        });
    }

    process.exit(0);
}

// ============================================================================
// Basic terminology
// ============================================================================

function explainFundamentals() {
    console.log(`
Parallel computing:
  Divides work among execution resources so independent operations can
  progress simultaneously.

Concurrency:
  Multiple activities are in progress during overlapping periods.

Parallelism:
  Multiple operations actually execute at the same time on separate
  execution resources.

Multicore processor:
  A CPU containing multiple processing cores.

SIMD:
  Single Instruction, Multiple Data. One vector instruction operates on
  multiple data elements.

MIMD:
  Multiple Instruction, Multiple Data. Different processing units can
  execute different instruction streams on different data.

Task parallelism:
  Different workers perform different tasks.

Data parallelism:
  Multiple workers perform the same operation on different data partitions.
`);
}

// ============================================================================
// Sequential baseline
// ============================================================================

function sequentialSquareSum(values) {
    let total = 0;

    for (const value of values) {
        total += value * value;
    }

    return total;
}

// ============================================================================
// Event-loop concurrency
// ============================================================================

function simulatedAsyncTask(id, delayMilliseconds) {
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve(`task-${id} completed`);
        }, delayMilliseconds);
    });
}

async function demonstrateConcurrency() {
    console.log("\n=== Event-Loop Concurrency ===");

    const start = performance.now();

    /*
     * Promise.all starts the asynchronous operations without waiting for
     * each timer independently. This is concurrency, not CPU parallelism.
     */
    const results = await Promise.all(
        Array.from({ length: 8 }, (_, index) =>
            simulatedAsyncTask(index + 1, 50)
        )
    );

    console.log(results);
    console.log(
        `Concurrent asynchronous time: ${(performance.now() - start).toFixed(2)} ms`
    );
}

// ============================================================================
// Prime calculation
// ============================================================================

function isPrime(number) {
    if (number < 2) return false;
    if (number === 2) return true;
    if (number % 2 === 0) return false;

    for (let divisor = 3; divisor * divisor <= number; divisor += 2) {
        if (number % divisor === 0) {
            return false;
        }
    }

    return true;
}

function countPrimes(start, end) {
    let count = 0;

    for (let number = start; number < end; number++) {
        if (isPrime(number)) {
            count++;
        }
    }

    return count;
}

// ============================================================================
// Worker helper
// ============================================================================

function runWorker(type, payload) {
    return new Promise((resolve, reject) => {
        const worker = new Worker(__filename, {
            workerData: { type, payload }
        });

        worker.once("message", (message) => {
            if (message.type === "error") {
                reject(new Error(message.message));
            } else {
                resolve(message.result);
            }
        });

        worker.once("error", reject);

        worker.once("exit", (code) => {
            if (code !== 0) {
                reject(
                    new Error(`Worker stopped with exit code ${code}`)
                );
            }
        });
    });
}

// ============================================================================
// Worker-thread parallelism
// ============================================================================

function createRanges(start, end, workers) {
    if (workers <= 0) {
        throw new RangeError("workers must be positive");
    }

    const ranges = [];

    for (let index = 0; index < workers; index++) {
        const left =
            start + Math.floor(((end - start) * index) / workers);

        const right =
            start + Math.floor(((end - start) * (index + 1)) / workers);

        if (left < right) {
            ranges.push({ start: left, end: right });
        }
    }

    return ranges;
}

async function parallelPrimeCount(start, end, workers) {
    const ranges = createRanges(start, end, workers);

    /*
     * Each worker receives an independent data partition.
     * This is data parallelism and, on a multicore machine, can execute
     * on multiple CPU cores.
     */
    const promises = ranges.map((range) =>
        runWorker("prime-count", range)
    );

    const counts = await Promise.all(promises);

    return counts.reduce((total, count) => total + count, 0);
}

async function demonstrateMulticoreParallelism() {
    console.log("\n=== Multicore Parallelism ===");

    const startNumber = 10000;
    const endNumber = 40000;
    const workers = Math.max(
        1,
        Math.min(os.availableParallelism(), 4)
    );

    let start = performance.now();
    const sequentialResult = countPrimes(startNumber, endNumber);
    const sequentialTime = performance.now() - start;

    start = performance.now();
    const parallelResult = await parallelPrimeCount(
        startNumber,
        endNumber,
        workers
    );
    const parallelTime = performance.now() - start;

    console.log(`Available logical processors: ${os.availableParallelism()}`);
    console.log(`Workers: ${workers}`);
    console.log(`Sequential result: ${sequentialResult}`);
    console.log(`Parallel result:   ${parallelResult}`);
    console.log(`Sequential time: ${sequentialTime.toFixed(2)} ms`);
    console.log(`Parallel time:   ${parallelTime.toFixed(2)} ms`);

    if (parallelTime > 0) {
        console.log(
            `Observed speedup: ${(sequentialTime / parallelTime).toFixed(2)}x`
        );
    }
}

// ============================================================================
// SIMD conceptual demonstration
// ============================================================================

function scalarVectorAdd(left, right) {
    if (left.length !== right.length) {
        throw new Error("Vectors must have equal lengths.");
    }

    const result = [];

    for (let index = 0; index < left.length; index++) {
        result.push(left[index] + right[index]);
    }

    return result;
}

function conceptualSimdVectorAdd(left, right, laneCount = 4) {
    if (left.length !== right.length) {
        throw new Error("Vectors must have equal lengths.");
    }

    if (laneCount <= 0) {
        throw new Error("laneCount must be positive.");
    }

    const result = [];

    /*
     * This groups values into conceptual SIMD vectors.
     * JavaScript array processing here does not guarantee actual hardware
     * SIMD instructions. A JavaScript engine may optimize numeric code
     * internally, but the programmer does not directly control CPU
     * instruction selection through this function.
     */
    for (let start = 0; start < left.length; start += laneCount) {
        const end = Math.min(start + laneCount, left.length);

        for (let index = start; index < end; index++) {
            result.push(left[index] + right[index]);
        }
    }

    return result;
}

async function demonstrateSIMD() {
    console.log("\n=== SIMD Concept ===");

    const left = [10, 20, 30, 40, 50, 60];
    const right = [1, 2, 3, 4, 5, 6];

    console.log("Scalar:", scalarVectorAdd(left, right));
    console.log(
        "Conceptual SIMD:",
        conceptualSimdVectorAdd(left, right, 4)
    );
}

// ============================================================================
// MIMD example
// ============================================================================

async function demonstrateMIMD() {
    console.log("\n=== MIMD Concept ===");

    const values = Array.from({ length: 100 }, (_, index) => index + 1);

    /*
     * These are different algorithms. The workers therefore demonstrate the
     * MIMD idea: separate execution units can perform different operations.
     */
    const [sum, maximum, statistics] = await Promise.all([
        runWorker("statistics", values).then((result) => result.sum),
        Promise.resolve(Math.max(...values)),
        runWorker("statistics", values)
    ]);

    console.log("Sum:", sum);
    console.log("Maximum:", maximum);
    console.log("Statistics:", statistics);
}

// ============================================================================
// Statistics worker
// ============================================================================

function calculateStatistics(values) {
    if (!Array.isArray(values)) {
        throw new TypeError("values must be an array");
    }

    if (values.length === 0) {
        return {
            count: 0,
            sum: 0,
            mean: null,
            minimum: null,
            maximum: null
        };
    }

    const sum = values.reduce((total, value) => total + value, 0);

    return {
        count: values.length,
        sum,
        mean: sum / values.length,
        minimum: Math.min(...values),
        maximum: Math.max(...values)
    };
}

// ============================================================================
// Data parallel vector addition using workers
// ============================================================================

function splitArray(values, parts) {
    if (parts <= 0) {
        throw new RangeError("parts must be positive");
    }

    const chunks = [];

    for (let index = 0; index < parts; index++) {
        const start = Math.floor((values.length * index) / parts);
        const end = Math.floor(
            (values.length * (index + 1)) / parts
        );

        if (start < end) {
            chunks.push(values.slice(start, end));
        }
    }

    return chunks;
}

async function demonstrateDataParallelism() {
    console.log("\n=== Data Parallel Vector Processing ===");

    const left = Array.from({ length: 12 }, (_, index) => index + 1);
    const right = Array.from({ length: 12 }, (_, index) => (index + 1) * 10);

    const leftChunks = splitArray(left, 3);
    const rightChunks = splitArray(right, 3);

    const jobs = leftChunks.map((leftChunk, index) =>
        runWorker("vector-add", {
            left: leftChunk,
            right: rightChunks[index]
        })
    );

    const chunks = await Promise.all(jobs);
    const result = chunks.flat();

    console.log("Left:", left);
    console.log("Right:", right);
    console.log("Result:", result);
}

// ============================================================================
// Worker-side vector operation
// ============================================================================

function vectorAdd(left, right) {
    if (!Array.isArray(left) || !Array.isArray(right)) {
        throw new TypeError("Both inputs must be arrays.");
    }

    if (left.length !== right.length) {
        throw new Error("Vector lengths must match.");
    }

    return left.map((value, index) => value + right[index]);
}

// ============================================================================
// Amdahl's Law
// ============================================================================

function amdahlSpeedup(serialFraction, processors) {
    if (serialFraction < 0 || serialFraction > 1) {
        throw new RangeError(
            "serialFraction must be between 0 and 1."
        );
    }

    if (processors <= 0) {
        throw new RangeError("processors must be positive.");
    }

    return 1 / (
        serialFraction +
        (1 - serialFraction) / processors
    );
}

function demonstrateAmdahl() {
    console.log("\n=== Amdahl's Law ===");

    const serialFraction = 0.10;

    for (const processors of [1, 2, 4, 8, 16, 32]) {
        console.log(
            `${processors} processors -> ` +
            `${amdahlSpeedup(serialFraction, processors).toFixed(2)}x`
        );
    }
}

// ============================================================================
// Gustafson's Law
// ============================================================================

function gustafsonSpeedup(serialFraction, processors) {
    return processors -
        serialFraction * (processors - 1);
}

function demonstrateGustafson() {
    console.log("\n=== Gustafson's Law ===");

    for (const processors of [1, 2, 4, 8, 16]) {
        console.log(
            `${processors} processors -> ` +
            `${gustafsonSpeedup(0.10, processors).toFixed(2)}x`
        );
    }
}

// ============================================================================
// Performance considerations
// ============================================================================

function discussPerformance() {
    console.log(`
=== Performance Considerations ===

Parallel execution introduces overhead:
  - worker creation
  - scheduling
  - communication
  - copying or serialization
  - synchronization
  - reduction/aggregation
  - memory bandwidth pressure

A parallel implementation can therefore be slower than a sequential
implementation when the workload is too small.

Important metrics:
  Speedup    = T_sequential / T_parallel
  Efficiency = Speedup / number_of_processors

Important architectural considerations:
  - CPU core count
  - cache hierarchy
  - memory bandwidth
  - workload granularity
  - synchronization frequency
  - data locality
  - load balance
  - worker startup cost
`);
}

// ============================================================================
// Edge cases
// ============================================================================

function demonstrateEdgeCases() {
    console.log("\n=== Edge Cases ===");

    console.log("Empty statistics:", calculateStatistics([]));

    try {
        scalarVectorAdd([1], [1, 2]);
    } catch (error) {
        console.log(
            `Mismatched vectors handled: ${error.name}: ${error.message}`
        );
    }

    try {
        createRanges(0, 10, 0);
    } catch (error) {
        console.log(
            `Invalid worker count handled: ${error.name}: ${error.message}`
        );
    }

    console.log(
        "Negative-number primality:",
        isPrime(-7)
    );
}

// ============================================================================
// Main program
// ============================================================================

async function main() {
    console.log("Parallel Computing Fundamentals");

    explainFundamentals();

    console.log(
        "\nSequential square sum:",
        sequentialSquareSum([1, 2, 3, 4, 5])
    );

    await demonstrateConcurrency();
    await demonstrateMulticoreParallelism();
    await demonstrateSIMD();
    await demonstrateMIMD();
    await demonstrateDataParallelism();

    demonstrateAmdahl();
    demonstrateGustafson();
    demonstrateEdgeCases();
    discussPerformance();

    console.log(`
=== Key Distinctions ===

Concurrency:
  Multiple tasks can make progress during overlapping periods.

Parallelism:
  Multiple operations execute simultaneously.

SIMD:
  One instruction conceptually operates on multiple data elements.

MIMD:
  Different execution units can execute different instructions on
  different data.

Node.js event-loop concurrency is excellent for overlapping asynchronous
operations. Worker Threads are appropriate when CPU-bound work needs actual
parallel execution across CPU cores.
`);
}

main().catch((error) => {
    console.error("Fatal error:", error);
    process.exitCode = 1;
});
