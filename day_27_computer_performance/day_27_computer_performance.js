"use strict";

/*
 * Computer Performance:
 * Clock Speed, CPI, IPC, Latency, Throughput, and Benchmarks
 *
 * This file complements the Python study by emphasizing JavaScript runtime
 * behavior, high-resolution timing, event-loop scheduling, asynchronous
 * throughput, data processing, validation, and practical benchmarking.
 *
 * Run with:
 *     node computer_performance.js
 */

// ---------------------------------------------------------------------------
// 1. FUNDAMENTAL PERFORMANCE FORMULAS
// ---------------------------------------------------------------------------

function executionTime(instructionCount, cpi, clockRateHz) {
    if (!Number.isFinite(instructionCount) || instructionCount < 0) {
        throw new RangeError("instructionCount must be non-negative");
    }
    if (!Number.isFinite(cpi) || cpi <= 0) {
        throw new RangeError("CPI must be positive");
    }
    if (!Number.isFinite(clockRateHz) || clockRateHz <= 0) {
        throw new RangeError("clock rate must be positive");
    }

    return (instructionCount * cpi) / clockRateHz;
}

function cpiFromCounters(cycles, instructions) {
    if (!Number.isFinite(cycles) || cycles < 0) {
        throw new RangeError("cycles must be non-negative");
    }
    if (!Number.isFinite(instructions) || instructions <= 0) {
        throw new RangeError("instructions must be positive");
    }

    return cycles / instructions;
}

function ipcFromCounters(cycles, instructions) {
    if (!Number.isFinite(cycles) || cycles <= 0) {
        throw new RangeError("cycles must be positive");
    }
    if (!Number.isFinite(instructions) || instructions < 0) {
        throw new RangeError("instructions must be non-negative");
    }

    return instructions / cycles;
}

function simpleIpcFromCpi(cpi) {
    if (!Number.isFinite(cpi) || cpi <= 0) {
        throw new RangeError("CPI must be positive");
    }

    return 1 / cpi;
}

function amdahlSpeedup(improvedFraction, improvementFactor) {
    if (improvedFraction < 0 || improvedFraction > 1) {
        throw new RangeError("fraction must be between 0 and 1");
    }
    if (improvementFactor <= 0) {
        throw new RangeError("improvement factor must be positive");
    }

    return 1 / ((1 - improvedFraction) + improvedFraction / improvementFactor);
}

function speedup(oldTime, newTime) {
    if (oldTime <= 0 || newTime <= 0) {
        throw new RangeError("execution times must be positive");
    }

    return oldTime / newTime;
}


// ---------------------------------------------------------------------------
// 2. INSTRUCTION MIX
// ---------------------------------------------------------------------------

class InstructionClass {
    constructor(name, count, cpi) {
        if (!name || !Number.isInteger(count) || count < 0 || cpi <= 0) {
            throw new RangeError("invalid instruction class");
        }

        this.name = name;
        this.count = count;
        this.cpi = cpi;
    }
}

function analyzeInstructionMix(classes) {
    if (!Array.isArray(classes) || classes.length === 0) {
        throw new TypeError("classes must be a non-empty array");
    }

    const instructions = classes.reduce(
        (total, item) => total + item.count,
        0
    );

    const cycles = classes.reduce(
        (total, item) => total + item.count * item.cpi,
        0
    );

    if (instructions === 0) {
        throw new RangeError("instruction count cannot be zero");
    }

    return {
        instructions,
        cycles,
        cpi: cycles / instructions,
        ipc: instructions / cycles
    };
}


// ---------------------------------------------------------------------------
// 3. LATENCY AND THROUGHPUT
// ---------------------------------------------------------------------------

function sequentialCompletionTime(jobCount, latencyMs) {
    if (!Number.isInteger(jobCount) || jobCount < 0) {
        throw new RangeError("jobCount must be non-negative");
    }
    if (latencyMs < 0) {
        throw new RangeError("latency cannot be negative");
    }

    return jobCount * latencyMs;
}

function pipelinedCompletionTime(jobCount, latencyMs, initiationIntervalMs) {
    if (!Number.isInteger(jobCount) || jobCount < 0) {
        throw new RangeError("jobCount must be non-negative");
    }
    if (latencyMs < 0 || initiationIntervalMs < 0) {
        throw new RangeError("timing values cannot be negative");
    }

    if (jobCount === 0) {
        return 0;
    }

    return latencyMs + (jobCount - 1) * initiationIntervalMs;
}

function throughputFromInterval(intervalMs) {
    if (intervalMs <= 0) {
        throw new RangeError("interval must be positive");
    }

    return 1000 / intervalMs;
}


// ---------------------------------------------------------------------------
// 4. HIGH-RESOLUTION JAVASCRIPT TIMING
// ---------------------------------------------------------------------------

function nowNanoseconds() {
    /*
     * process.hrtime.bigint() is a monotonic high-resolution timer in Node.js.
     * It is preferable to Date.now() for short benchmark intervals because
     * Date.now() has lower resolution and represents wall-clock time.
     */
    return process.hrtime.bigint();
}

function elapsedMilliseconds(start, end) {
    return Number(end - start) / 1_000_000;
}


// ---------------------------------------------------------------------------
// 5. BENCHMARK ENGINE
// ---------------------------------------------------------------------------

function benchmark(name, operation, options = {}) {
    const warmupRuns = options.warmupRuns ?? 3;
    const repetitions = options.repetitions ?? 7;

    if (warmupRuns < 0 || repetitions <= 0) {
        throw new RangeError("invalid benchmark configuration");
    }

    // Warm-up helps avoid interpreting initialization effects as steady-state
    // performance. JavaScript engines may also optimize frequently executed
    // code dynamically.
    for (let i = 0; i < warmupRuns; i++) {
        operation();
    }

    const samples = [];

    for (let i = 0; i < repetitions; i++) {
        const start = nowNanoseconds();
        operation();
        const end = nowNanoseconds();

        samples.push(elapsedMilliseconds(start, end));
    }

    return {
        name,
        samples,
        mean: mean(samples),
        median: median(samples),
        minimum: Math.min(...samples),
        maximum: Math.max(...samples),
        standardDeviation: standardDeviation(samples)
    };
}


// ---------------------------------------------------------------------------
// 6. STATISTICS
// ---------------------------------------------------------------------------

function mean(values) {
    if (!values.length) {
        throw new RangeError("values cannot be empty");
    }

    return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function median(values) {
    if (!values.length) {
        throw new RangeError("values cannot be empty");
    }

    const sorted = [...values].sort((a, b) => a - b);
    const middle = Math.floor(sorted.length / 2);

    return sorted.length % 2 === 0
        ? (sorted[middle - 1] + sorted[middle]) / 2
        : sorted[middle];
}

function standardDeviation(values) {
    if (values.length < 2) {
        return 0;
    }

    const average = mean(values);
    const squaredDifferences = values.map(
        value => (value - average) ** 2
    );

    return Math.sqrt(
        mean(squaredDifferences)
    );
}

function percentile(values, percentileValue) {
    if (!values.length) {
        throw new RangeError("values cannot be empty");
    }
    if (percentileValue < 0 || percentileValue > 100) {
        throw new RangeError("percentile must be between 0 and 100");
    }

    const sorted = [...values].sort((a, b) => a - b);

    if (sorted.length === 1) {
        return sorted[0];
    }

    const position =
        (sorted.length - 1) * percentileValue / 100;

    const lower = Math.floor(position);
    const upper = Math.ceil(position);

    if (lower === upper) {
        return sorted[lower];
    }

    const fraction = position - lower;

    return sorted[lower] +
        fraction * (sorted[upper] - sorted[lower]);
}


// ---------------------------------------------------------------------------
// 7. DATA-PROCESSING BENCHMARKS
// ---------------------------------------------------------------------------

function createDataset(size) {
    const values = new Array(size);

    for (let i = 0; i < size; i++) {
        values[i] = i;
    }

    return values;
}

function loopSum(values) {
    let total = 0;

    for (let i = 0; i < values.length; i++) {
        total += values[i];
    }

    return total;
}

function reduceSum(values) {
    return values.reduce(
        (total, value) => total + value,
        0
    );
}

function loopMapFilterSum(values) {
    let total = 0;

    for (let i = 0; i < values.length; i++) {
        const value = values[i];

        if (value % 2 === 0) {
            total += value * 2;
        }
    }

    return total;
}

function functionalMapFilterSum(values) {
    return values
        .filter(value => value % 2 === 0)
        .map(value => value * 2)
        .reduce((total, value) => total + value, 0);
}


// ---------------------------------------------------------------------------
// 8. CPU MODEL
// ---------------------------------------------------------------------------

class CpuModel {
    constructor(name, frequencyHz, cpi) {
        if (!name) {
            throw new TypeError("CPU name is required");
        }
        if (frequencyHz <= 0 || cpi <= 0) {
            throw new RangeError("frequency and CPI must be positive");
        }

        this.name = name;
        this.frequencyHz = frequencyHz;
        this.cpi = cpi;
    }

    executionTime(instructions) {
        return executionTime(
            instructions,
            this.cpi,
            this.frequencyHz
        );
    }

    effectiveIpc() {
        return simpleIpcFromCpi(this.cpi);
    }
}


// ---------------------------------------------------------------------------
// 9. ASYNCHRONOUS THROUGHPUT
// ---------------------------------------------------------------------------

function simulatedAsyncOperation(delayMs) {
    /*
     * setTimeout demonstrates an important distinction:
     * asynchronous concurrency can increase throughput without making the
     * latency of an individual operation smaller.
     */
    return new Promise(resolve => {
        setTimeout(() => resolve(delayMs), delayMs);
    });
}

async function runSequentialAsyncJobs(jobCount, delayMs) {
    const start = nowNanoseconds();

    for (let i = 0; i < jobCount; i++) {
        await simulatedAsyncOperation(delayMs);
    }

    const end = nowNanoseconds();

    return elapsedMilliseconds(start, end);
}

async function runConcurrentAsyncJobs(jobCount, delayMs) {
    const start = nowNanoseconds();

    const jobs = Array.from(
        { length: jobCount },
        () => simulatedAsyncOperation(delayMs)
    );

    await Promise.all(jobs);

    const end = nowNanoseconds();

    return elapsedMilliseconds(start, end);
}


// ---------------------------------------------------------------------------
// 10. EVENT-LOOP DEMONSTRATION
// ---------------------------------------------------------------------------

function demonstrateEventLoop() {
    /*
     * JavaScript uses an event loop for asynchronous callbacks.
     * A CPU-heavy synchronous loop blocks the main thread in a browser and
     * blocks the Node.js event loop in a Node process.
     */
    const events = [];

    events.push("synchronous start");

    queueMicrotask(() => {
        events.push("microtask");
    });

    setTimeout(() => {
        events.push("timer callback");
        console.log("\nEVENT LOOP ORDER");
        console.log(events.join(" -> "));
    }, 0);

    events.push("synchronous end");
}


// ---------------------------------------------------------------------------
// 11. MEMORY-ACCESS MODEL
// ---------------------------------------------------------------------------

function memoryAccessCycles({
    computeInstructions,
    baseCpi,
    memoryAccesses,
    cacheHitRate,
    hitPenalty,
    missPenalty
}) {
    if (
        computeInstructions <= 0 ||
        baseCpi <= 0 ||
        memoryAccesses < 0 ||
        cacheHitRate < 0 ||
        cacheHitRate > 1
    ) {
        throw new RangeError("invalid memory model");
    }

    const hits = memoryAccesses * cacheHitRate;
    const misses = memoryAccesses - hits;

    return (
        computeInstructions * baseCpi +
        hits * hitPenalty +
        misses * missPenalty
    );
}


// ---------------------------------------------------------------------------
// 12. VALIDATION AND ERROR HANDLING
// ---------------------------------------------------------------------------

function demonstrateValidation() {
    console.log("\nVALIDATION");

    const invalidOperations = [
        () => executionTime(1000, 1, 0),
        () => simpleIpcFromCpi(-1),
        () => percentile([], 50)
    ];

    for (const operation of invalidOperations) {
        try {
            operation();
        } catch (error) {
            console.log(`${error.constructor.name}: ${error.message}`);
        }
    }
}


// ---------------------------------------------------------------------------
// 13. MAIN PROGRAM
// ---------------------------------------------------------------------------

async function main() {
    console.log("=".repeat(78));
    console.log("COMPUTER PERFORMANCE STUDY");
    console.log("Clock Speed | CPI | IPC | Latency | Throughput | Benchmarks");
    console.log("=".repeat(78));

    console.log("\n1. CLOCK SPEED");

    const frequency = 3.5e9;

    console.log(`Frequency: ${(frequency / 1e9).toFixed(2)} GHz`);
    console.log(`Clock period: ${(1e9 / frequency).toFixed(3)} ns`);

    console.log("\n2. CPU EXECUTION TIME");

    const instructions = 1_000_000_000;
    const cpi = 1.5;
    const cpuTime = executionTime(
        instructions,
        cpi,
        frequency
    );

    console.log(`Instructions: ${instructions.toLocaleString()}`);
    console.log(`CPI: ${cpi}`);
    console.log(`Execution time: ${(cpuTime * 1000).toFixed(3)} ms`);

    console.log("\n3. CPI AND IPC");

    const cycles = instructions * cpi;

    console.log(`Cycles: ${cycles.toLocaleString()}`);
    console.log(`CPI from counters: ${cpiFromCounters(cycles, instructions).toFixed(3)}`);
    console.log(`IPC from counters: ${ipcFromCounters(cycles, instructions).toFixed(3)}`);

    console.log("\n4. INSTRUCTION MIX");

    const instructionMix = [
        new InstructionClass("integer", 500_000, 1.0),
        new InstructionClass("load/store", 300_000, 2.0),
        new InstructionClass("branch", 100_000, 4.0),
        new InstructionClass("floating point", 100_000, 3.0)
    ];

    const mixResult = analyzeInstructionMix(instructionMix);

    console.table(mixResult);

    console.log("\n5. CPU COMPARISON");

    const cpuModels = [
        new CpuModel("CPU A", 3.0e9, 1.0),
        new CpuModel("CPU B", 4.0e9, 1.5),
        new CpuModel("CPU C", 3.2e9, 0.8)
    ];

    for (const cpu of cpuModels) {
        const time = cpu.executionTime(2_000_000_000);

        console.log(
            `${cpu.name}: ` +
            `${(time * 1000).toFixed(3)} ms, ` +
            `effective IPC ${cpu.effectiveIpc().toFixed(3)}`
        );
    }

    console.log("\n6. LATENCY AND THROUGHPUT");

    const jobs = 100;
    const latencyMs = 10;
    const intervalMs = 2;

    console.log(
        `Sequential: ${sequentialCompletionTime(jobs, latencyMs).toFixed(1)} ms`
    );

    console.log(
        `Pipelined: ${pipelinedCompletionTime(
            jobs,
            latencyMs,
            intervalMs
        ).toFixed(1)} ms`
    );

    console.log(
        `Ideal throughput: ${throughputFromInterval(intervalMs).toFixed(1)} jobs/s`
    );

    console.log("\n7. AMDAHL'S LAW");

    const amdahl = amdahlSpeedup(0.80, 5);

    console.log(`Speedup: ${amdahl.toFixed(3)}x`);
    console.log(
        `Infinite improvement limit: ${(1 / (1 - 0.80)).toFixed(3)}x`
    );

    console.log("\n8. CACHE/MEMORY MODEL");

    const memoryCycles = memoryAccessCycles({
        computeInstructions: 1_000_000,
        baseCpi: 1,
        memoryAccesses: 200_000,
        cacheHitRate: 0.95,
        hitPenalty: 2,
        missPenalty: 100
    });

    console.log(`Modeled cycles: ${memoryCycles.toLocaleString()}`);
    console.log(
        `Effective CPI: ${(memoryCycles / 1_000_000).toFixed(3)}`
    );

    console.log("\n9. JAVASCRIPT MICRO-BENCHMARK");

    const dataset = createDataset(100_000);

    // Execute once before measuring to reduce first-use effects.
    loopSum(dataset);
    reduceSum(dataset);
    loopMapFilterSum(dataset);
    functionalMapFilterSum(dataset);

    const benchmarkResults = [
        benchmark("for-loop sum", () => loopSum(dataset)),
        benchmark("reduce sum", () => reduceSum(dataset)),
        benchmark(
            "loop map/filter/sum",
            () => loopMapFilterSum(dataset)
        ),
        benchmark(
            "functional map/filter/sum",
            () => functionalMapFilterSum(dataset)
        )
    ];

    for (const result of benchmarkResults) {
        console.log(
            `${result.name.padEnd(28)} ` +
            `mean=${result.mean.toFixed(4)} ms ` +
            `median=${result.median.toFixed(4)} ms ` +
            `min=${result.minimum.toFixed(4)} ms ` +
            `max=${result.maximum.toFixed(4)} ms`
        );
    }

    console.log("\n10. PERCENTILES");

    const loopResult = benchmarkResults[0];

    console.log(`P50: ${percentile(loopResult.samples, 50).toFixed(4)} ms`);
    console.log(`P95: ${percentile(loopResult.samples, 95).toFixed(4)} ms`);
    console.log(`P99: ${percentile(loopResult.samples, 99).toFixed(4)} ms`);

    console.log("\n11. ASYNCHRONOUS LATENCY VERSUS THROUGHPUT");

    const asyncJobCount = 10;
    const asyncLatency = 20;

    const sequentialAsyncTime =
        await runSequentialAsyncJobs(
            asyncJobCount,
            asyncLatency
        );

    const concurrentAsyncTime =
        await runConcurrentAsyncJobs(
            asyncJobCount,
            asyncLatency
        );

    console.log(
        `Sequential async jobs: ${sequentialAsyncTime.toFixed(2)} ms`
    );

    console.log(
        `Concurrent async jobs: ${concurrentAsyncTime.toFixed(2)} ms`
    );

    console.log(
        "Concurrency improves completion throughput here because the simulated " +
        "operations spend time waiting rather than consuming the CPU."
    );

    console.log("\n12. EVENT LOOP");

    demonstrateEventLoop();

    console.log("\n13. SPEEDUP");

    const baseline = benchmarkResults[2].median;
    const optimized = benchmarkResults[3].median;

    console.log(
        `Functional versus loop speed ratio: ${speedup(
            baseline,
            optimized
        ).toFixed(3)}x`
    );

    console.log("\n14. VALIDATION");

    demonstrateValidation();

    console.log("\n" + "=".repeat(78));
    console.log("KEY RELATIONSHIPS");
    console.log("=".repeat(78));
    console.log("CPU time = Instruction Count × CPI / Clock Rate");
    console.log("CPI = Cycles / Instructions");
    console.log("IPC = Instructions / Cycles");
    console.log("Latency = time for one operation/result");
    console.log("Throughput = completed work per unit time");
    console.log("Speedup = old execution time / new execution time");
    console.log("Amdahl = 1 / ((1-p) + p/s)");
    console.log(
        "Benchmark results describe the measured program and environment, " +
        "not an abstract CPU speed independent of workload."
    );
}

main().catch(error => {
    console.error("Fatal error:", error);
    process.exitCode = 1;
});
