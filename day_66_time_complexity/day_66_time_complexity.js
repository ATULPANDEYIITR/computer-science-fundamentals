"use strict";

/*
 * Time Complexity Analysis Engine
 *
 * Demonstrates:
 * - Big-O, Big-Omega and Big-Theta.
 * - Growth functions.
 * - Event-driven complexity measurements.
 * - Search and sorting strategies.
 * - Asynchronous workload execution.
 * - Input validation and performance limits.
 *
 * Runtime: Node.js 18+
 */

const { performance } = require("node:perf_hooks");
const EventEmitter = require("node:events");

class ComplexityError extends Error {
    constructor(message) {
        super(message);
        this.name = "ComplexityError";
    }
}

const Complexity = Object.freeze({
    CONSTANT: "O(1)",
    LOGARITHMIC: "O(log n)",
    LINEAR: "O(n)",
    LINEARITHMIC: "O(n log n)",
    QUADRATIC: "O(n²)",
    CUBIC: "O(n³)",
    EXPONENTIAL: "O(2ⁿ)"
});

class ComplexityBound {
    constructor(name, bigO, bigOmega, bigTheta, description) {
        this.name = name;
        this.bigO = bigO;
        this.bigOmega = bigOmega;
        this.bigTheta = bigTheta;
        this.description = description;

        Object.freeze(this);
    }
}

class ComplexityRegistry {
    #bounds = new Map();

    register(bound) {
        if (!(bound instanceof ComplexityBound)) {
            throw new ComplexityError("Invalid complexity definition.");
        }

        if (this.#bounds.has(bound.name)) {
            throw new ComplexityError("Complexity class already registered.");
        }

        this.#bounds.set(bound.name, bound);
    }

    get(name) {
        const result = this.#bounds.get(name);

        if (!result) {
            throw new ComplexityError(`Unknown complexity class: ${name}`);
        }

        return result;
    }

    getAll() {
        return [...this.#bounds.values()];
    }
}

class OperationCounter {
    #count = 0;

    increment(amount = 1) {
        if (!Number.isSafeInteger(amount) || amount < 0) {
            throw new ComplexityError("Invalid operation increment.");
        }

        this.#count += amount;

        if (!Number.isSafeInteger(this.#count)) {
            throw new ComplexityError("Operation count exceeded safe integer range.");
        }
    }

    get value() {
        return this.#count;
    }

    reset() {
        this.#count = 0;
    }
}

class GrowthAnalyzer {
    static validate(n) {
        if (!Number.isSafeInteger(n) || n < 0) {
            throw new ComplexityError("n must be a non-negative safe integer.");
        }
    }

    static evaluate(n) {
        this.validate(n);

        const log = n > 0 ? Math.log2(n) : 0;

        return {
            constant: 1,
            logarithmic: log,
            linear: n,
            linearithmic: n * log,
            quadratic: n ** 2,
            cubic: n ** 3
        };
    }

    static compare(n) {
        const values = this.evaluate(n);

        return Object.entries(values)
            .sort((a, b) => a[1] - b[1])
            .map(([name, value]) => ({
                name,
                value: Number(value.toFixed(3))
            }));
    }

    // A bound comparison is valid only for positive inputs.
    static upperBound(value, reference, constant) {
        if (
            !Number.isFinite(value) ||
            !Number.isFinite(reference) ||
            !Number.isFinite(constant) ||
            reference <= 0 ||
            constant <= 0
        ) {
            throw new ComplexityError("Invalid asymptotic comparison.");
        }

        return value <= constant * reference;
    }
}

class SearchService {
    static linearSearch(values, target) {
        const counter = new OperationCounter();

        for (let i = 0; i < values.length; i++) {
            counter.increment();

            if (values[i] === target) {
                return {
                    index: i,
                    operations: counter.value,
                    complexity: Complexity.LINEAR
                };
            }
        }

        return {
            index: -1,
            operations: counter.value,
            complexity: Complexity.LINEAR
        };
    }

    static binarySearch(values, target) {
        for (let i = 1; i < values.length; i++) {
            if (values[i - 1] > values[i]) {
                throw new ComplexityError("Input must be sorted.");
            }
        }

        let left = 0;
        let right = values.length - 1;
        const counter = new OperationCounter();

        while (left <= right) {
            const middle = left + Math.floor((right - left) / 2);
            counter.increment();

            if (values[middle] === target) {
                return {
                    index: middle,
                    operations: counter.value,
                    complexity: Complexity.LOGARITHMIC
                };
            }

            if (values[middle] < target) {
                left = middle + 1;
            } else {
                right = middle - 1;
            }
        }

        return {
            index: -1,
            operations: counter.value,
            complexity: Complexity.LOGARITHMIC
        };
    }
}

class SortingService {
    static mergeSort(values) {
        let comparisons = 0;

        function sort(array) {
            if (array.length <= 1) {
                return array;
            }

            const middle = Math.floor(array.length / 2);
            const left = sort(array.slice(0, middle));
            const right = sort(array.slice(middle));

            const result = [];
            let i = 0;
            let j = 0;

            while (i < left.length && j < right.length) {
                comparisons++;

                if (left[i] <= right[j]) {
                    result.push(left[i++]);
                } else {
                    result.push(right[j++]);
                }
            }

            return result.concat(left.slice(i), right.slice(j));
        }

        return {
            result: sort(values),
            comparisons,
            complexity: Complexity.LINEARITHMIC
        };
    }

    static bubbleSort(values) {
        const result = [...values];
        let comparisons = 0;

        for (let i = 0; i < result.length; i++) {
            let swapped = false;

            for (let j = 0; j < result.length - i - 1; j++) {
                comparisons++;

                if (result[j] > result[j + 1]) {
                    [result[j], result[j + 1]] =
                        [result[j + 1], result[j]];

                    swapped = true;
                }
            }

            if (!swapped) break;
        }

        return {
            result,
            comparisons,
            complexity: Complexity.QUADRATIC
        };
    }
}

class PerformanceMonitor extends EventEmitter {
    #records = [];

    record(result) {
        this.#records.push(Object.freeze({ ...result }));
        this.emit("measurement", result);
    }

    getRecords() {
        return [...this.#records];
    }

    clear() {
        this.#records = [];
    }
}

class WorkloadRunner {
    constructor(monitor) {
        this.monitor = monitor;
    }

    async run(name, operation, size, complexity) {
        GrowthAnalyzer.validate(size);

        const start = performance.now();

        // Yield to the event loop before executing the workload.
        await new Promise(resolve => setImmediate(resolve));

        try {
            const operations = operation(size);
            const elapsed = performance.now() - start;

            const result = {
                name,
                size,
                operations,
                elapsedMilliseconds: Number(elapsed.toFixed(4)),
                complexity
            };

            this.monitor.record(result);
            return result;
        } catch (error) {
            throw new ComplexityError(
                `Workload ${name} failed: ${error.message}`
            );
        }
    }
}

function createRegistry() {
    const registry = new ComplexityRegistry();

    const definitions = [
        new ComplexityBound(
            "Constant", "O(1)", "Ω(1)", "Θ(1)",
            "Fixed number of operations."
        ),
        new ComplexityBound(
            "Logarithmic", "O(log n)", "Ω(log n)", "Θ(log n)",
            "Input decreases by a constant factor."
        ),
        new ComplexityBound(
            "Linear", "O(n)", "Ω(n)", "Θ(n)",
            "Operations grow proportionally to n."
        ),
        new ComplexityBound(
            "Linearithmic", "O(n log n)", "Ω(n log n)", "Θ(n log n)",
            "Common in efficient comparison sorting."
        ),
        new ComplexityBound(
            "Quadratic", "O(n²)", "Ω(n²)", "Θ(n²)",
            "Two complete nested loops."
        ),
        new ComplexityBound(
            "Cubic", "O(n³)", "Ω(n³)", "Θ(n³)",
            "Three complete nested loops."
        ),
        new ComplexityBound(
            "Exponential", "O(2ⁿ)", "Ω(2ⁿ)", "Θ(2ⁿ)",
            "Work grows exponentially."
        )
    ];

    definitions.forEach(item => registry.register(item));

    return registry;
}

function countLinear(n) {
    return n;
}

function countLogarithmic(n) {
    let count = 0;
    let value = 1;

    while (value < n) {
        value *= 2;
        count++;
    }

    return count;
}

function countQuadratic(n) {
    return n * n;
}

function countTriangular(n) {
    return n * (n + 1) / 2;
}

function countCubic(n) {
    return n * n * n;
}

async function main() {
    console.log("TIME COMPLEXITY ANALYSIS ENGINE");
    console.log("=".repeat(75));

    const registry = createRegistry();

    console.log("\nASYMPTOTIC DEFINITIONS");

    for (const item of registry.getAll()) {
        console.log(
            `${item.name}: Big-O=${item.bigO}, ` +
            `Big-Omega=${item.bigOmega}, Big-Theta=${item.bigTheta}`
        );
    }

    console.log("\nGROWTH COMPARISON");

    for (const size of [10, 100, 1000]) {
        console.log(`n=${size}`, GrowthAnalyzer.compare(size));
    }

    console.log("\nSEARCH");

    const values = Array.from({ length: 1000 }, (_, i) => i * 2);

    console.log("Linear:", SearchService.linearSearch(values, 800));
    console.log("Binary:", SearchService.binarySearch(values, 800));

    console.log("\nSORTING");

    const unsorted = [45, 12, 89, 3, 22, 67, 1, 9];

    console.log("Merge:", SortingService.mergeSort(unsorted));
    console.log("Bubble:", SortingService.bubbleSort(unsorted));

    console.log("\nEVENT-DRIVEN BENCHMARKING");

    const monitor = new PerformanceMonitor();

    monitor.on("measurement", result => {
        console.log(
            `Measured ${result.name}: ${result.operations} operations`
        );
    });

    const runner = new WorkloadRunner(monitor);

    const workloads = [
        ["Linear", countLinear, Complexity.LINEAR],
        ["Logarithmic", countLogarithmic, Complexity.LOGARITHMIC],
        ["Quadratic", countQuadratic, Complexity.QUADRATIC],
        ["Triangular", countTriangular, Complexity.QUADRATIC],
        ["Cubic", countCubic, Complexity.CUBIC]
    ];

    for (const [name, operation, complexity] of workloads) {
        for (const size of [10, 100, 500]) {
            await runner.run(name, operation, size, complexity);
        }
    }

    console.log("\nEDGE CASES");

    console.assert(
        SearchService.linearSearch([], 10).index === -1,
        "Empty linear search failed."
    );

    console.assert(
        SearchService.binarySearch([], 10).index === -1,
        "Empty binary search failed."
    );

    console.assert(
        SortingService.mergeSort([]).result.length === 0,
        "Empty merge sort failed."
    );

    console.assert(countTriangular(0) === 0);
    console.assert(countLogarithmic(1) === 0);

    try {
        SearchService.binarySearch([9, 2, 5], 2);
    } catch (error) {
        console.log("Expected error:", error.message);
    }

    try {
        GrowthAnalyzer.evaluate(-5);
    } catch (error) {
        console.log("Expected error:", error.message);
    }

    console.log("\nTOTAL RECORDED MEASUREMENTS:", monitor.getRecords().length);
    console.log("EXECUTION COMPLETED");
}

main().catch(error => {
    console.error("Execution failure:", error.message);
    process.exitCode = 1;
});
