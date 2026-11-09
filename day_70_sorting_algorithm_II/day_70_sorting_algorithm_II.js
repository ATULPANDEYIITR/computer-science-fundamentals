"use strict";

/*
 * Sorting Algorithms II
 * Merge Sort, Quick Sort and Heap Sort
 *
 * Node.js 18+ compatible.
 *
 * Includes:
 * - Generic comparator-based sorting
 * - Stable merge sort
 * - Iterative three-way quicksort
 * - In-place heap operations on copied arrays
 * - Asynchronous benchmarking
 * - AbortSignal support
 * - Operation metrics
 * - Input validation and automated assertions
 * - JSON benchmark reporting
 */

const fs = require("node:fs/promises");
const assert = require("node:assert/strict");
const { performance } = require("node:perf_hooks");

class SortError extends Error {
    constructor(message) {
        super(message);
        this.name = "SortError";
    }
}

class Metrics {
    constructor(algorithm) {
        this.algorithm = algorithm;
        this.comparisons = 0;
        this.swaps = 0;
        this.writes = 0;
        this.partitions = 0;
        this.elapsedMs = 0;
    }

    snapshot() {
        return Object.freeze({
            algorithm: this.algorithm,
            comparisons: this.comparisons,
            swaps: this.swaps,
            writes: this.writes,
            partitions: this.partitions,
            elapsedMs: Number(this.elapsedMs.toFixed(4))
        });
    }
}

function defaultComparator(a, b) {
    if (a === b) return 0;
    if (a === undefined || b === undefined) {
        throw new SortError("Undefined values are not supported");
    }

    if (a < b) return -1;
    if (a > b) return 1;

    throw new SortError(
        "Values are not comparable. Supply a valid comparator."
    );
}

function validateOptions(options = {}) {
    if (typeof options !== "object" || options === null) {
        throw new SortError("Options must be an object");
    }

    const comparator = options.comparator ?? defaultComparator;

    if (typeof comparator !== "function") {
        throw new SortError("Comparator must be a function");
    }

    return {
        comparator,
        reverse: options.reverse === true
    };
}

function createContext(algorithm, options) {
    const config = validateOptions(options);
    const metrics = new Metrics(algorithm);

    function compare(a, b) {
        metrics.comparisons++;

        const result = config.comparator(a, b);

        if (typeof result !== "number" || Number.isNaN(result)) {
            throw new SortError(
                "Comparator must return a valid number"
            );
        }

        const normalized = Math.sign(result);

        return config.reverse ? -normalized : normalized;
    }

    return { metrics, compare };
}

function swap(data, i, j, metrics) {
    if (i === j) return;

    [data[i], data[j]] = [data[j], data[i]];
    metrics.swaps++;
    metrics.writes += 2;
}

function mergeSort(input, options = {}) {
    if (!Array.isArray(input)) {
        throw new SortError("Input must be an array");
    }

    const data = input.slice();
    const { metrics, compare } = createContext(
        "merge_sort",
        options
    );

    const start = performance.now();

    if (data.length < 2) {
        metrics.elapsedMs = performance.now() - start;
        return { result: data, metrics: metrics.snapshot() };
    }

    let source = data;
    let destination = new Array(data.length);

    // Bottom-up merge sort avoids recursion depth limitations.
    for (let width = 1; width < data.length; width *= 2) {
        for (let left = 0; left < data.length; left += 2 * width) {
            const middle = Math.min(left + width, data.length);
            const right = Math.min(left + 2 * width, data.length);

            let i = left;
            let j = middle;
            let k = left;

            while (i < middle && j < right) {
                // Left-first selection preserves stability.
                if (compare(source[i], source[j]) <= 0) {
                    destination[k++] = source[i++];
                } else {
                    destination[k++] = source[j++];
                }

                metrics.writes++;
            }

            while (i < middle) {
                destination[k++] = source[i++];
                metrics.writes++;
            }

            while (j < right) {
                destination[k++] = source[j++];
                metrics.writes++;
            }
        }

        [source, destination] = [destination, source];
    }

    metrics.elapsedMs = performance.now() - start;

    return {
        result: source,
        metrics: metrics.snapshot()
    };
}

function quickSort(input, options = {}) {
    if (!Array.isArray(input)) {
        throw new SortError("Input must be an array");
    }

    const data = input.slice();
    const { metrics, compare } = createContext(
        "quick_sort",
        options
    );

    const start = performance.now();

    function median(a, b, c) {
        if (compare(a, b) > 0) [a, b] = [b, a];
        if (compare(b, c) > 0) [b, c] = [c, b];
        if (compare(a, b) > 0) [a, b] = [b, a];
        return b;
    }

    const stack = [];

    if (data.length > 1) {
        stack.push([0, data.length - 1]);

        while (stack.length > 0) {
            const [low, high] = stack.pop();

            if (low >= high) continue;

            const pivot = median(
                data[low],
                data[Math.floor((low + high) / 2)],
                data[high]
            );

            let less = low;
            let current = low;
            let greater = high;

            metrics.partitions++;

            // Dutch National Flag partitioning.
            while (current <= greater) {
                const order = compare(data[current], pivot);

                if (order < 0) {
                    swap(data, less++, current++, metrics);
                } else if (order > 0) {
                    swap(data, current, greater--, metrics);
                } else {
                    current++;
                }
            }

            const leftSize = less - low;
            const rightSize = high - greater;

            // Push the larger side and process the smaller side.
            // This controls auxiliary stack growth.
            if (leftSize < rightSize) {
                if (greater + 1 < high) {
                    stack.push([greater + 1, high]);
                }

                if (low < less - 1) {
                    stack.push([low, less - 1]);
                }
            } else {
                if (low < less - 1) {
                    stack.push([low, less - 1]);
                }

                if (greater + 1 < high) {
                    stack.push([greater + 1, high]);
                }
            }
        }
    }

    metrics.elapsedMs = performance.now() - start;

    return {
        result: data,
        metrics: metrics.snapshot()
    };
}

function heapSort(input, options = {}) {
    if (!Array.isArray(input)) {
        throw new SortError("Input must be an array");
    }

    const data = input.slice();
    const { metrics, compare } = createContext(
        "heap_sort",
        options
    );

    const start = performance.now();

    function siftDown(root, end) {
        while (true) {
            let child = 2 * root + 1;

            if (child >= end) return;

            if (
                child + 1 < end &&
                compare(data[child], data[child + 1]) < 0
            ) {
                child++;
            }

            if (compare(data[root], data[child]) >= 0) {
                return;
            }

            swap(data, root, child, metrics);
            root = child;
        }
    }

    // Construct a max heap.
    for (let root = Math.floor(data.length / 2) - 1;
         root >= 0;
         root--) {
        siftDown(root, data.length);
    }

    // Extract maximum elements into their final positions.
    for (let end = data.length - 1; end > 0; end--) {
        swap(data, 0, end, metrics);
        siftDown(0, end);
    }

    metrics.elapsedMs = performance.now() - start;

    return {
        result: data,
        metrics: metrics.snapshot()
    };
}

const SORTERS = Object.freeze({
    merge_sort: mergeSort,
    quick_sort: quickSort,
    heap_sort: heapSort
});

function sort(input, algorithm, options = {}) {
    const sorter = SORTERS[algorithm];

    if (!sorter) {
        throw new SortError(`Unknown algorithm: ${algorithm}`);
    }

    return sorter(input, options);
}

function verifyResult(original, result, comparator = defaultComparator) {
    if (original.length !== result.length) {
        throw new SortError("Sorted output has incorrect length");
    }

    // Compare frequency maps rather than relying on string conversion.
    const remaining = new Map();

    for (const value of original) {
        remaining.set(value, (remaining.get(value) ?? 0) + 1);
    }

    for (const value of result) {
        const count = remaining.get(value) ?? 0;

        if (count === 0) {
            throw new SortError("Sorting changed the input elements");
        }

        remaining.set(value, count - 1);
    }

    for (let i = 1; i < result.length; i++) {
        if (comparator(result[i - 1], result[i]) > 0) {
            throw new SortError("Output is not sorted");
        }
    }

    return true;
}

function generateDatasets(size, seed = 42) {
    let state = seed >>> 0;

    function random() {
        state = (1664525 * state + 1013904223) >>> 0;
        return state / 4294967296;
    }

    const randomValues = Array.from(
        { length: size },
        () => Math.floor(random() * 20001) - 10000
    );

    return new Map([
        ["random", randomValues],
        ["sorted", Array.from({ length: size }, (_, i) => i)],
        ["reverse", Array.from({ length: size }, (_, i) => size - i)],
        ["duplicates", Array.from(
            { length: size },
            () => Math.floor(random() * 10)
        )],
        ["all_equal", Array(size).fill(5)]
    ]);
}

async function benchmark({
    size = 5000,
    seed = 42,
    signal
} = {}) {
    if (!Number.isSafeInteger(size) || size < 0) {
        throw new SortError("Size must be a non-negative safe integer");
    }

    const datasets = generateDatasets(size, seed);
    const results = [];

    for (const [datasetName, values] of datasets) {
        for (const algorithm of Object.keys(SORTERS)) {
            if (signal?.aborted) {
                throw new DOMException(
                    "Benchmark cancelled",
                    "AbortError"
                );
            }

            // Yield to the event loop between benchmark operations.
            await new Promise(resolve => setImmediate(resolve));

            const output = sort(values, algorithm);
            verifyResult(values, output.result);

            results.push({
                dataset: datasetName,
                inputSize: size,
                ...output.metrics
            });
        }
    }

    return results;
}

async function exportBenchmark(records, filename = "sorting_benchmark.json") {
    if (!Array.isArray(records) || records.length === 0) {
        throw new SortError("Benchmark records cannot be empty");
    }

    if (typeof filename !== "string" || filename.trim() === "") {
        throw new SortError("A valid output filename is required");
    }

    const content = JSON.stringify(records, null, 2);

    await fs.writeFile(filename, content, {
        encoding: "utf8",
        flag: "w"
    });
}

function runTests() {
    const cases = [
        [],
        [1],
        [2, 1],
        [5, 3, 8, 1, 2],
        [4, 4, 4, 4],
        [-10, 0, 10, -5],
        Array.from({ length: 100 }, (_, i) => 100 - i)
    ];

    for (const values of cases) {
        const expected = [...values].sort((a, b) => a - b);

        for (const algorithm of Object.keys(SORTERS)) {
            const output = sort(values, algorithm);

            assert.deepEqual(output.result, expected);
            verifyResult(values, output.result);

            const descending = sort(values, algorithm, {
                reverse: true
            });

            assert.deepEqual(
                descending.result,
                [...expected].reverse()
            );
        }
    }

    // Stable merge sort preserves the original order of equal keys.
    const records = [
        { id: "A", score: 80 },
        { id: "B", score: 70 },
        { id: "C", score: 80 },
        { id: "D", score: 70 }
    ];

    const stable = mergeSort(records, {
        comparator: (a, b) => a.score - b.score
    });

    assert.deepEqual(
        stable.result.map(record => record.id),
        ["B", "D", "A", "C"]
    );

    assert.throws(() => sort(null, "merge_sort"), SortError);
    assert.throws(() => sort([1, 2], "unknown"), SortError);

    console.log("All JavaScript sorting tests passed.");
}

async function main() {
    runTests();

    const sample = [38, 27, 43, 3, 9, 82, 10, 3];

    console.log("\nSample results");

    for (const algorithm of Object.keys(SORTERS)) {
        const output = sort(sample, algorithm);

        console.log(algorithm, {
            result: output.result,
            metrics: output.metrics
        });
    }

    const controller = new AbortController();

    const records = await benchmark({
        size: 5000,
        seed: 42,
        signal: controller.signal
    });

    await exportBenchmark(records);

    console.log("\nBenchmark exported to sorting_benchmark.json");
    console.log(`Benchmark records: ${records.length}`);
}

if (require.main === module) {
    main().catch(error => {
        console.error("Execution failed:", error.message);
        process.exitCode = 1;
    });
}

module.exports = {
    mergeSort,
    quickSort,
    heapSort,
    sort,
    benchmark,
    verifyResult,
    SortError
};
