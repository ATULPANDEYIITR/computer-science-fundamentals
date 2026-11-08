"use strict";

/**
 * Sorting Algorithms I
 * Bubble Sort, Selection Sort, and Insertion Sort.
 *
 * Runtime: Node.js 18+
 *
 * Features:
 * - Generic comparator-based sorting
 * - Event-driven sorting service
 * - Sorting metrics
 * - Inventory prioritization
 * - Stability demonstrations
 * - Asynchronous benchmark execution
 * - JSON report export
 * - Input validation
 * - Automated tests
 */

const fs = require("node:fs/promises");
const { performance } = require("node:perf_hooks");
const EventEmitter = require("node:events");

const ALGORITHMS = Object.freeze({
    BUBBLE: "bubble",
    SELECTION: "selection",
    INSERTION: "insertion"
});

class SortingError extends Error {
    constructor(message) {
        super(message);
        this.name = "SortingError";
    }
}

function validateInput(data, comparator) {
    if (!Array.isArray(data)) {
        throw new SortingError("Input must be an array.");
    }

    if (typeof comparator !== "function") {
        throw new SortingError("Comparator must be a function.");
    }

    if (data.some(value => value === undefined)) {
        throw new SortingError("Undefined values are not supported.");
    }

    return [...data];
}

function numericComparator(a, b) {
    if (
        typeof a !== "number" ||
        typeof b !== "number" ||
        !Number.isFinite(a) ||
        !Number.isFinite(b)
    ) {
        throw new SortingError(
            "Numeric sorting requires finite numbers."
        );
    }

    return a - b;
}

class SortingMetrics {
    constructor(algorithm) {
        this.algorithm = algorithm;
        this.comparisons = 0;
        this.swaps = 0;
        this.shifts = 0;
        this.passes = 0;
        this.durationMs = 0;
    }
}

class SortingService extends EventEmitter {
    constructor() {
        super();
        this.history = [];
    }

    execute(data, algorithm, options = {}) {
        const comparator =
            options.comparator || numericComparator;

        const reverse = options.reverse === true;

        if (!Object.values(ALGORITHMS).includes(algorithm)) {
            throw new SortingError(
                `Unsupported algorithm: ${algorithm}`
            );
        }

        const values = validateInput(data, comparator);
        const metrics = new SortingMetrics(algorithm);

        const compare = (a, b) => {
            metrics.comparisons++;

            const result = comparator(a, b);

            if (
                typeof result !== "number" ||
                !Number.isFinite(result)
            ) {
                throw new SortingError(
                    "Comparator must return a finite number."
                );
            }

            return reverse ? -result : result;
        };

        const start = performance.now();

        try {
            if (algorithm === ALGORITHMS.BUBBLE) {
                this.bubble(values, compare, metrics);
            } else if (algorithm === ALGORITHMS.SELECTION) {
                this.selection(values, compare, metrics);
            } else {
                this.insertion(values, compare, metrics);
            }
        } catch (error) {
            this.emit("sortError", {
                algorithm,
                message: error.message
            });

            throw error;
        }

        metrics.durationMs = performance.now() - start;

        const result = {
            algorithm,
            values,
            metrics: { ...metrics }
        };

        this.history.push(result);

        this.emit("sortCompleted", result);

        return result;
    }

    bubble(values, compare, metrics) {
        for (let i = 0; i < values.length - 1; i++) {
            let swapped = false;
            metrics.passes++;

            for (
                let j = 0;
                j < values.length - i - 1;
                j++
            ) {
                if (compare(values[j], values[j + 1]) > 0) {
                    [values[j], values[j + 1]] = [
                        values[j + 1],
                        values[j]
                    ];

                    metrics.swaps++;
                    swapped = true;
                }
            }

            if (!swapped) break;
        }
    }

    selection(values, compare, metrics) {
        for (let i = 0; i < values.length - 1; i++) {
            metrics.passes++;

            let minimum = i;

            for (let j = i + 1; j < values.length; j++) {
                if (compare(values[j], values[minimum]) < 0) {
                    minimum = j;
                }
            }

            if (minimum !== i) {
                [values[i], values[minimum]] = [
                    values[minimum],
                    values[i]
                ];

                metrics.swaps++;
            }
        }
    }

    insertion(values, compare, metrics) {
        for (let i = 1; i < values.length; i++) {
            metrics.passes++;

            const current = values[i];
            let j = i - 1;

            while (
                j >= 0 &&
                compare(values[j], current) > 0
            ) {
                values[j + 1] = values[j];
                metrics.shifts++;
                j--;
            }

            values[j + 1] = current;
        }
    }

    async executeAsync(data, algorithm, options = {}) {
        // Yield before execution so callers can coordinate asynchronous work.
        await new Promise(resolve => setImmediate(resolve));

        return this.execute(data, algorithm, options);
    }

    getHistory() {
        return this.history.map(result => ({
            ...result,
            values: [...result.values],
            metrics: { ...result.metrics }
        }));
    }
}

class InventoryManager {
    constructor(products) {
        if (!Array.isArray(products)) {
            throw new SortingError(
                "Products must be supplied as an array."
            );
        }

        const identifiers = new Set();

        for (const product of products) {
            if (
                !product ||
                typeof product.id !== "string" ||
                product.id.trim() === "" ||
                typeof product.name !== "string" ||
                !Number.isInteger(product.stock) ||
                product.stock < 0 ||
                typeof product.price !== "number" ||
                !Number.isFinite(product.price) ||
                product.price < 0
            ) {
                throw new SortingError(
                    "Invalid inventory product."
                );
            }

            if (identifiers.has(product.id)) {
                throw new SortingError(
                    `Duplicate product ID: ${product.id}`
                );
            }

            identifiers.add(product.id);
        }

        this.products = products.map(product =>
            Object.freeze({ ...product })
        );
    }

    prioritizeByStock(service) {
        return service.execute(
            this.products,
            ALGORITHMS.INSERTION,
            {
                comparator: (a, b) => a.stock - b.stock
            }
        );
    }

    prioritizeByPrice(service) {
        return service.execute(
            this.products,
            ALGORITHMS.SELECTION,
            {
                comparator: (a, b) => a.price - b.price
            }
        );
    }
}

async function runBenchmark(service) {
    console.log("\n=== ASYNCHRONOUS BENCHMARK ===");

    const sizes = [20, 100, 300];
    const report = [];

    for (const size of sizes) {
        const original = Array.from(
            { length: size },
            () => Math.floor(Math.random() * 10000)
        );

        for (const algorithm of Object.values(ALGORITHMS)) {
            const result = await service.executeAsync(
                original,
                algorithm
            );

            const expected = [...original].sort(
                (a, b) => a - b
            );

            if (
                result.values.some(
                    (value, index) => value !== expected[index]
                )
            ) {
                throw new Error("Benchmark correctness failure.");
            }

            report.push({
                size,
                ...result.metrics
            });

            console.log(
                `${algorithm.padEnd(10)} ` +
                `n=${size} ` +
                `comparisons=${result.metrics.comparisons} ` +
                `swaps=${result.metrics.swaps} ` +
                `shifts=${result.metrics.shifts} ` +
                `time=${result.metrics.durationMs.toFixed(4)} ms`
            );
        }
    }

    await fs.writeFile(
        "sorting_benchmark.json",
        JSON.stringify(report, null, 2),
        { encoding: "utf8", flag: "w" }
    );

    console.log("Benchmark report saved.");

    return report;
}

function runStabilityTest(service) {
    console.log("\n=== STABILITY TEST ===");

    const records = [
        { name: "Alice", score: 85 },
        { name: "Bob", score: 70 },
        { name: "Charlie", score: 85 },
        { name: "David", score: 70 }
    ];

    for (const algorithm of Object.values(ALGORITHMS)) {
        const result = service.execute(
            records,
            algorithm,
            {
                comparator: (a, b) => a.score - b.score
            }
        );

        console.log(
            algorithm,
            result.values.map(
                record => `${record.name}:${record.score}`
            )
        );
    }
}

function runTests(service) {
    console.log("\n=== AUTOMATED TESTS ===");

    const testCases = [
        [],
        [1],
        [5, 4, 3, 2, 1],
        [1, 2, 3, 4, 5],
        [3, 3, 3, 3],
        [-5, 10, 0, -20],
        [2.5, 1.5, 3.5]
    ];

    for (const testCase of testCases) {
        const expected = [...testCase].sort(
            (a, b) => a - b
        );

        for (const algorithm of Object.values(ALGORITHMS)) {
            const result = service.execute(
                testCase,
                algorithm
            );

            if (
                JSON.stringify(result.values) !==
                JSON.stringify(expected)
            ) {
                throw new Error(
                    `${algorithm} failed: ${testCase}`
                );
            }
        }
    }

    const descending = service.execute(
        [1, 5, 3, 2],
        ALGORITHMS.INSERTION,
        { reverse: true }
    );

    if (
        JSON.stringify(descending.values) !==
        JSON.stringify([5, 3, 2, 1])
    ) {
        throw new Error("Descending order test failed.");
    }

    try {
        service.execute([1, 2], "unknown");
        throw new Error("Invalid algorithm was accepted.");
    } catch (error) {
        if (!(error instanceof SortingError)) {
            throw error;
        }
    }

    try {
        service.execute([1, NaN, 3], ALGORITHMS.BUBBLE);
        throw new Error("Invalid numeric input was accepted.");
    } catch (error) {
        if (!(error instanceof SortingError)) {
            throw error;
        }
    }

    console.log("All tests passed.");
}

async function main() {
    console.log("====================================");
    console.log("SORTING ALGORITHMS I");
    console.log("====================================");

    const service = new SortingService();

    service.on("sortCompleted", result => {
        console.log(
            `[EVENT] ${result.algorithm} completed.`
        );
    });

    service.on("sortError", error => {
        console.error(
            `[EVENT] Sorting failed: ${error.message}`
        );
    });

    const values = [64, 34, 25, 12, 22, 11, 90];

    console.log("\nOriginal:", values);

    for (const algorithm of Object.values(ALGORITHMS)) {
        const result = service.execute(
            values,
            algorithm
        );

        console.log(
            `${algorithm}:`,
            result.values,
            result.metrics
        );
    }

    console.log("\n=== INVENTORY MANAGEMENT ===");

    const inventory = new InventoryManager([
        { id: "P101", name: "Keyboard", stock: 45, price: 1200 },
        { id: "P102", name: "Monitor", stock: 12, price: 9500 },
        { id: "P103", name: "Mouse", stock: 80, price: 650 },
        { id: "P104", name: "Laptop", stock: 8, price: 55000 }
    ]);

    const priority = inventory.prioritizeByStock(service);

    for (const product of priority.values) {
        console.log(
            `${product.id} ${product.name} Stock=${product.stock}`
        );
    }

    runStabilityTest(service);
    runTests(service);
    await runBenchmark(service);

    console.log("\nSorting execution completed.");
}

main().catch(error => {
    console.error("Application failure:", error.message);
    process.exitCode = 1;
});
