"use strict";

/*
 * Divide and Conquer: Asynchronous Algorithm Execution Engine
 *
 * Demonstrates:
 * - Recursive decomposition
 * - Promise-based parallel execution
 * - Merge sort with bounded parallelism
 * - Binary search
 * - Quick sort
 * - Maximum subarray
 * - Recurrence analysis
 * - Cancellation and input validation
 *
 * Runtime: Node.js 18+
 */

const { performance } = require("node:perf_hooks");
const { EventEmitter } = require("node:events");
const crypto = require("node:crypto");

class AlgorithmError extends Error {
    constructor(message, code = "ALGORITHM_ERROR") {
        super(message);
        this.name = "AlgorithmError";
        this.code = code;
    }
}

function validateArray(values, name = "values") {
    if (!Array.isArray(values)) {
        throw new AlgorithmError(`${name} must be an array.`, "INVALID_INPUT");
    }

    if (values.length > 1_000_000) {
        throw new AlgorithmError("Input exceeds configured limit.", "INPUT_LIMIT");
    }

    return values;
}

function validateNumbers(values) {
    validateArray(values);

    if (!values.every(Number.isSafeInteger)) {
        throw new AlgorithmError(
            "All elements must be safe integers.",
            "INVALID_NUMBER"
        );
    }
}

class AlgorithmMonitor extends EventEmitter {
    constructor() {
        super();
        this.history = [];
    }

    record(event) {
        const entry = Object.freeze({
            id: crypto.randomUUID(),
            timestamp: new Date().toISOString(),
            ...event
        });

        this.history.push(entry);
        this.emit("algorithm-event", entry);
    }

    report() {
        return this.history.map(event => ({ ...event }));
    }
}

class DivideAndConquerEngine {
    constructor({ parallelThreshold = 2048, maxDepth = 64 } = {}) {
        if (!Number.isInteger(parallelThreshold) || parallelThreshold < 2) {
            throw new AlgorithmError("Invalid parallel threshold.");
        }

        this.parallelThreshold = parallelThreshold;
        this.maxDepth = maxDepth;
        this.monitor = new AlgorithmMonitor();
    }

    merge(left, right) {
        const output = [];
        let i = 0;
        let j = 0;

        while (i < left.length && j < right.length) {
            if (left[i] <= right[j]) {
                output.push(left[i++]);
            } else {
                output.push(right[j++]);
            }
        }

        return output.concat(left.slice(i), right.slice(j));
    }

    mergeSort(values) {
        validateNumbers(values);

        const sort = items => {
            if (items.length <= 1) return items.slice();

            const middle = Math.floor(items.length / 2);

            return this.merge(
                sort(items.slice(0, middle)),
                sort(items.slice(middle))
            );
        };

        return sort(values);
    }

    async parallelMergeSort(values, options = {}) {
        validateNumbers(values);

        const signal = options.signal;
        const threshold = options.threshold ?? this.parallelThreshold;
        const maxDepth = options.maxDepth ?? this.maxDepth;

        if (!Number.isInteger(threshold) || threshold < 2) {
            throw new AlgorithmError("Threshold must be an integer >= 2.");
        }

        if (!Number.isInteger(maxDepth) || maxDepth < 0) {
            throw new AlgorithmError("Maximum depth must be non-negative.");
        }

        const checkCancellation = () => {
            if (signal?.aborted) {
                throw new AlgorithmError(
                    "Algorithm execution cancelled.",
                    "CANCELLED"
                );
            }
        };

        const sort = async (items, depth) => {
            checkCancellation();

            if (items.length <= 1) return items.slice();

            const middle = Math.floor(items.length / 2);
            const left = items.slice(0, middle);
            const right = items.slice(middle);

            let sortedLeft;
            let sortedRight;

            if (items.length >= threshold && depth < maxDepth) {
                // Both branches are independent and can execute concurrently.
                [sortedLeft, sortedRight] = await Promise.all([
                    sort(left, depth + 1),
                    sort(right, depth + 1)
                ]);
            } else {
                sortedLeft = await sort(left, depth + 1);
                sortedRight = await sort(right, depth + 1);
            }

            checkCancellation();
            return this.merge(sortedLeft, sortedRight);
        };

        const started = performance.now();

        this.monitor.record({
            algorithm: "parallel-merge-sort",
            state: "started",
            inputSize: values.length
        });

        try {
            const result = await sort(values, 0);

            this.monitor.record({
                algorithm: "parallel-merge-sort",
                state: "completed",
                elapsedMs: performance.now() - started
            });

            return result;
        } catch (error) {
            this.monitor.record({
                algorithm: "parallel-merge-sort",
                state: "failed",
                error: error.message
            });

            throw error;
        }
    }

    binarySearch(values, target) {
        validateNumbers(values);

        if (!Number.isSafeInteger(target)) {
            throw new AlgorithmError("Target must be a safe integer.");
        }

        for (let i = 1; i < values.length; i++) {
            if (values[i - 1] > values[i]) {
                throw new AlgorithmError("Array must be sorted.");
            }
        }

        let low = 0;
        let high = values.length - 1;

        while (low <= high) {
            const middle = low + Math.floor((high - low) / 2);

            if (values[middle] === target) return middle;
            if (values[middle] < target) low = middle + 1;
            else high = middle - 1;
        }

        return -1;
    }

    quickSort(values) {
        validateNumbers(values);

        const sort = items => {
            if (items.length <= 1) return items.slice();

            const pivot = items[Math.floor(items.length / 2)];
            const lower = [];
            const equal = [];
            const higher = [];

            for (const value of items) {
                if (value < pivot) lower.push(value);
                else if (value > pivot) higher.push(value);
                else equal.push(value);
            }

            return [...sort(lower), ...equal, ...sort(higher)];
        };

        return sort(values);
    }

    maximumSubarray(values) {
        validateNumbers(values);

        if (values.length === 0) {
            throw new AlgorithmError("Maximum subarray needs non-empty input.");
        }

        const solve = (left, right) => {
            if (left === right) {
                return {
                    sum: values[left],
                    start: left,
                    end: right
                };
            }

            const middle = Math.floor((left + right) / 2);

            const first = solve(left, middle);
            const second = solve(middle + 1, right);

            let sum = 0;
            let bestLeft = -Infinity;
            let start = middle;

            for (let i = middle; i >= left; i--) {
                sum += values[i];

                if (sum > bestLeft) {
                    bestLeft = sum;
                    start = i;
                }
            }

            sum = 0;
            let bestRight = -Infinity;
            let end = middle + 1;

            for (let i = middle + 1; i <= right; i++) {
                sum += values[i];

                if (sum > bestRight) {
                    bestRight = sum;
                    end = i;
                }
            }

            const cross = {
                sum: bestLeft + bestRight,
                start,
                end
            };

            return [first, second, cross].reduce(
                (best, current) =>
                    current.sum > best.sum ? current : best
            );
        };

        return solve(0, values.length - 1);
    }
}

class RecurrenceAnalyzer {
    static analyze({ a, b, d }) {
        if (
            !Number.isFinite(a) ||
            !Number.isFinite(b) ||
            !Number.isFinite(d) ||
            !Number.isInteger(a) ||
            !Number.isInteger(b) ||
            a < 1 ||
            b < 2 ||
            d < 0
        ) {
            throw new AlgorithmError("Invalid recurrence parameters.");
        }

        const critical = Math.log(a) / Math.log(b);
        const epsilon = 1e-10;

        let classification;

        if (d < critical - epsilon) {
            classification = `Theta(n^${critical.toFixed(3)})`;
        } else if (Math.abs(d - critical) <= epsilon) {
            classification = `Theta(n^${critical.toFixed(3)} log n)`;
        } else {
            classification = `Theta(n^${d.toFixed(3)})`;
        }

        return {
            recurrence: `T(n) = ${a}T(n/${b}) + Theta(n^${d})`,
            criticalExponent: critical,
            complexity: classification
        };
    }
}

async function main() {
    const engine = new DivideAndConquerEngine();

    engine.monitor.on("algorithm-event", event => {
        console.log("[EVENT]", event.algorithm, event.state);
    });

    const input = Array.from(
        { length: 2000 },
        () => Math.floor(Math.random() * 10000)
    );

    console.log("\n1. SYNCHRONOUS MERGE SORT");

    const sorted = engine.mergeSort(input);
    console.log("Sorted elements:", sorted.length);
    console.log("Correct:", sorted.every(
        (value, index) => index === 0 || sorted[index - 1] <= value
    ));

    console.log("\n2. ASYNCHRONOUS PARALLEL MERGE SORT");

    const parallel = await engine.parallelMergeSort(input, {
        threshold: 256,
        maxDepth: 4
    });

    console.log("Parallel output matches:", 
        JSON.stringify(sorted) === JSON.stringify(parallel));

    console.log("\n3. BINARY SEARCH");

    const target = sorted[500];
    console.log("Target:", target);
    console.log("Found at:", engine.binarySearch(sorted, target));

    console.log("\n4. QUICK SORT");

    const quick = engine.quickSort([9, 3, 7, 3, 1, 8, 2]);
    console.log(quick);

    console.log("\n5. MAXIMUM SUBARRAY");

    const maximum = engine.maximumSubarray([
        -2, 1, -3, 4, -1, 2, 1, -5, 4
    ]);

    console.log(maximum);

    console.log("\n6. RECURRENCE ANALYSIS");

    const recurrences = [
        { a: 1, b: 2, d: 0 },
        { a: 2, b: 2, d: 1 },
        { a: 3, b: 2, d: 1 },
        { a: 2, b: 2, d: 2 }
    ];

    for (const recurrence of recurrences) {
        console.log(RecurrenceAnalyzer.analyze(recurrence));
    }

    console.log("\n7. FAILURE HANDLING");

    try {
        engine.binarySearch([5, 2, 8], 5);
    } catch (error) {
        console.log(error.code, error.message);
    }

    try {
        engine.maximumSubarray([]);
    } catch (error) {
        console.log(error.code, error.message);
    }

    const controller = new AbortController();
    controller.abort();

    try {
        await engine.parallelMergeSort(input, {
            signal: controller.signal
        });
    } catch (error) {
        console.log(error.code, error.message);
    }

    console.log("\n8. EXECUTION HISTORY");
    console.log(engine.monitor.report());

    console.log("\nAll JavaScript demonstrations completed.");
}

main().catch(error => {
    console.error("Execution failed:", error);
    process.exitCode = 1;
});
