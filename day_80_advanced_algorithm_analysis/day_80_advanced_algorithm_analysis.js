"use strict";

/*
 * Advanced Algorithm Analysis
 *
 * JavaScript implementation emphasizing:
 * - Asynchronous Monte Carlo experiments
 * - Event-driven experiment monitoring
 * - Randomized quicksort
 * - Probabilistic load distribution
 * - Statistical estimation and confidence intervals
 *
 * Runtime: Node.js 18+
 * Dependencies: Node.js standard library only
 */

const { EventEmitter } = require("node:events");
const { performance } = require("node:perf_hooks");
const assert = require("node:assert/strict");


class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "ValidationError";
    }
}


function validatePositiveInteger(value, name) {
    if (!Number.isSafeInteger(value) || value <= 0) {
        throw new ValidationError(
            `${name} must be a positive safe integer.`
        );
    }
}


class SeededRandom {
    constructor(seed = 42) {
        if (!Number.isInteger(seed)) {
            throw new ValidationError("Seed must be an integer.");
        }

        this.state = seed >>> 0;
    }

    next() {
        let x = this.state;

        x ^= x << 13;
        x ^= x >>> 17;
        x ^= x << 5;

        this.state = x >>> 0;

        return this.state / 0x100000000;
    }

    integer(min, max) {
        if (!Number.isInteger(min) ||
            !Number.isInteger(max) ||
            min > max) {
            throw new ValidationError("Invalid integer range.");
        }

        return min + Math.floor(
            this.next() * (max - min + 1)
        );
    }
}


class ExperimentMonitor extends EventEmitter {
    constructor() {
        super();
        this.completed = 0;
        this.failed = 0;
        this.startedAt = null;
    }

    start(name) {
        this.startedAt = performance.now();
        this.emit("experimentStarted", { name });
    }

    complete(result) {
        this.completed++;

        this.emit("experimentCompleted", {
            completed: this.completed,
            result
        });
    }

    fail(error) {
        this.failed++;

        this.emit("experimentFailed", {
            failed: this.failed,
            message: error.message
        });
    }

    getReport() {
        return {
            completed: this.completed,
            failed: this.failed,
            elapsedMilliseconds: this.startedAt === null
                ? 0
                : performance.now() - this.startedAt
        };
    }
}


/*
 * Dynamic array with geometric growth.
 *
 * The total number of copied elements over n appends
 * is O(n), although a resize operation is O(n).
 */

class DynamicArray {
    constructor(capacity = 1) {
        validatePositiveInteger(capacity, "capacity");

        this.capacity = capacity;
        this.size = 0;
        this.data = new Array(capacity);
        this.totalWrites = 0;
        this.resizes = 0;
    }

    append(value) {
        let cost = 1;

        if (this.size === this.capacity) {
            const newCapacity = this.capacity * 2;
            const newData = new Array(newCapacity);

            for (let i = 0; i < this.size; i++) {
                newData[i] = this.data[i];
                cost++;
            }

            this.data = newData;
            this.capacity = newCapacity;
            this.resizes++;
        }

        this.data[this.size++] = value;
        this.totalWrites += cost;

        return cost;
    }

    get(index) {
        if (!Number.isInteger(index) ||
            index < 0 ||
            index >= this.size) {
            throw new RangeError("Invalid array index.");
        }

        return this.data[index];
    }

    report() {
        return {
            size: this.size,
            capacity: this.capacity,
            resizes: this.resizes,
            totalWrites: this.totalWrites,
            amortizedCost: this.totalWrites / Math.max(1, this.size)
        };
    }
}


/*
 * Iterative randomized quicksort.
 *
 * An explicit stack avoids call-stack overflow on
 * adversarial inputs. Randomized pivots reduce the
 * likelihood of consistently poor partitions.
 */

function randomizedQuickSort(input, seed = 42) {
    const values = [...input];
    const random = new SeededRandom(seed);

    let comparisons = 0;
    let swaps = 0;
    let partitions = 0;

    const stack = [[0, values.length - 1]];

    function swap(i, j) {
        if (i !== j) {
            [values[i], values[j]] = [values[j], values[i]];
            swaps++;
        }
    }

    function partition(low, high) {
        partitions++;

        const pivotIndex = random.integer(low, high);
        swap(pivotIndex, high);

        const pivot = values[high];
        let boundary = low - 1;

        for (let i = low; i < high; i++) {
            comparisons++;

            if (values[i] <= pivot) {
                boundary++;
                swap(boundary, i);
            }
        }

        swap(boundary + 1, high);

        return boundary + 1;
    }

    while (stack.length > 0) {
        const [low, high] = stack.pop();

        if (low >= high) {
            continue;
        }

        const pivot = partition(low, high);

        const left = [low, pivot - 1];
        const right = [pivot + 1, high];

        // Process the smaller partition immediately.
        // This limits the maximum explicit stack size.
        const leftSize = left[1] - left[0];
        const rightSize = right[1] - right[0];

        if (leftSize > rightSize) {
            if (left[0] < left[1]) stack.push(left);
            if (right[0] < right[1]) stack.push(right);
        } else {
            if (right[0] < right[1]) stack.push(right);
            if (left[0] < left[1]) stack.push(left);
        }
    }

    return {
        values,
        comparisons,
        swaps,
        partitions
    };
}


function harmonicNumber(n) {
    if (!Number.isSafeInteger(n) || n < 0) {
        throw new ValidationError("Invalid harmonic number input.");
    }

    let result = 0;

    for (let i = 1; i <= n; i++) {
        result += 1 / i;
    }

    return result;
}


function expectedQuickSortComparisons(n) {
    if (!Number.isSafeInteger(n) || n < 0) {
        throw new ValidationError("Invalid input size.");
    }

    if (n <= 1) return 0;

    return 2 * (n + 1) * harmonicNumber(n) - 4 * n;
}


function mean(values) {
    if (values.length === 0) {
        throw new ValidationError("Cannot calculate empty mean.");
    }

    return values.reduce((a, b) => a + b, 0) / values.length;
}


function standardDeviation(values) {
    const average = mean(values);

    return Math.sqrt(
        mean(values.map(value => (value - average) ** 2))
    );
}


/*
 * Approximate 95% confidence interval using the normal
 * approximation. This is suitable for sufficiently large
 * Monte Carlo samples, not a universal guarantee.
 */

function confidenceInterval95(values) {
    const average = mean(values);
    const sd = standardDeviation(values);

    const margin = 1.96 * sd / Math.sqrt(values.length);

    return {
        lower: average - margin,
        upper: average + margin
    };
}


async function runMonteCarlo({
    trials,
    couponTypes,
    seed = 42,
    monitor = new ExperimentMonitor()
}) {
    validatePositiveInteger(trials, "trials");
    validatePositiveInteger(couponTypes, "couponTypes");

    if (trials > 1000000 || couponTypes > 1000000) {
        throw new ValidationError("Experiment size exceeds safety limit.");
    }

    const random = new SeededRandom(seed);
    const observations = [];

    monitor.start("Coupon Collector Monte Carlo");

    try {
        for (let trial = 0; trial < trials; trial++) {
            const collected = new Set();
            let draws = 0;

            while (collected.size < couponTypes) {
                collected.add(random.integer(0, couponTypes - 1));
                draws++;
            }

            observations.push(draws);

            if ((trial + 1) % 1000 === 0) {
                monitor.emit("progress", {
                    completedTrials: trial + 1,
                    totalTrials: trials
                });

                // Yield to the Node.js event loop.
                await new Promise(resolve => setImmediate(resolve));
            }
        }

        const result = {
            trials,
            couponTypes,
            observedMean: mean(observations),
            theoreticalMean:
                couponTypes * harmonicNumber(couponTypes),
            standardDeviation: standardDeviation(observations),
            confidenceInterval: confidenceInterval95(observations),
            minimum: Math.min(...observations),
            maximum: Math.max(...observations)
        };

        monitor.complete(result);

        return result;
    } catch (error) {
        monitor.fail(error);
        throw error;
    }
}


/*
 * Power of two choices:
 *
 * Each incoming request samples two servers and selects
 * the less-loaded server.
 *
 * This generally distributes work more evenly than
 * selecting one server uniformly at random.
 */

function simulateLoadBalancing({
    requests,
    serverCount,
    seed = 42
}) {
    validatePositiveInteger(requests, "requests");
    validatePositiveInteger(serverCount, "serverCount");

    const random = new SeededRandom(seed);
    const loads = new Array(serverCount).fill(0);

    for (let request = 0; request < requests; request++) {
        const first = random.integer(0, serverCount - 1);
        const second = random.integer(0, serverCount - 1);

        const selected = loads[first] <= loads[second]
            ? first
            : second;

        loads[selected]++;
    }

    const average = requests / serverCount;

    return {
        requests,
        serverCount,
        loads,
        minimumLoad: Math.min(...loads),
        maximumLoad: Math.max(...loads),
        averageLoad: average,
        loadSpread: Math.max(...loads) - Math.min(...loads)
    };
}


function simulateSingleChoice({
    requests,
    serverCount,
    seed = 42
}) {
    validatePositiveInteger(requests, "requests");
    validatePositiveInteger(serverCount, "serverCount");

    const random = new SeededRandom(seed);
    const loads = new Array(serverCount).fill(0);

    for (let i = 0; i < requests; i++) {
        loads[random.integer(0, serverCount - 1)]++;
    }

    return {
        maximumLoad: Math.max(...loads),
        minimumLoad: Math.min(...loads),
        loadSpread: Math.max(...loads) - Math.min(...loads),
        loads
    };
}


function analyzeDynamicArray(n) {
    validatePositiveInteger(n, "n");

    const array = new DynamicArray();

    for (let i = 0; i < n; i++) {
        array.append(i);
    }

    const report = array.report();

    if (report.totalWrites > 3 * n) {
        throw new Error("Amortized complexity bound violated.");
    }

    return report;
}


async function runTests() {
    const array = new DynamicArray();

    for (let i = 0; i < 1000; i++) {
        array.append(i);
    }

    assert.equal(array.size, 1000);
    assert.ok(array.totalWrites <= 3000);

    const sorted = randomizedQuickSort(
        [8, 3, 1, 7, 2, 9, 4],
        123
    );

    assert.deepEqual(sorted.values, [1, 2, 3, 4, 7, 8, 9]);

    assert.deepEqual(
        randomizedQuickSort([], 10).values,
        []
    );

    assert.equal(expectedQuickSortComparisons(2), 1);

    const result = await runMonteCarlo({
        trials: 100,
        couponTypes: 1
    });

    assert.equal(result.observedMean, 1);

    const load = simulateLoadBalancing({
        requests: 10000,
        serverCount: 20
    });

    assert.equal(load.loads.reduce((a, b) => a + b, 0), 10000);

    console.log("\nAll validation tests passed.");
}


async function main() {
    const monitor = new ExperimentMonitor();

    monitor.on("experimentStarted", event => {
        console.log(`Started: ${event.name}`);
    });

    monitor.on("progress", event => {
        console.log(
            `Progress: ${event.completedTrials}/${event.totalTrials}`
        );
    });

    monitor.on("experimentCompleted", event => {
        console.log("Experiment completed.");
        console.log(event.result);
    });

    monitor.on("experimentFailed", event => {
        console.error("Experiment failed:", event.message);
    });

    console.log("ADVANCED ALGORITHM ANALYSIS");

    console.log("\nAMORTIZED ANALYSIS");
    console.log(analyzeDynamicArray(10000));

    console.log("\nRANDOMIZED QUICKSORT");

    const randomInput = Array.from(
        { length: 1000 },
        (_, index) => index
    );

    const shuffled = randomizedQuickSort(
        randomInput.reverse(),
        2026
    );

    console.log({
        comparisons: shuffled.comparisons,
        swaps: shuffled.swaps,
        partitions: shuffled.partitions,
        theoreticalExpectedComparisons:
            expectedQuickSortComparisons(1000)
    });

    console.log("\nPROBABILISTIC ANALYSIS");

    const probabilityResult = await runMonteCarlo({
        trials: 5000,
        couponTypes: 20,
        seed: 12345,
        monitor
    });

    console.log(probabilityResult);

    console.log("\nRANDOMIZED LOAD BALANCING");

    const singleChoice = simulateSingleChoice({
        requests: 10000,
        serverCount: 50
    });

    const twoChoices = simulateLoadBalancing({
        requests: 10000,
        serverCount: 50
    });

    console.log({
        singleChoiceSpread: singleChoice.loadSpread,
        twoChoiceSpread: twoChoices.loadSpread
    });

    console.log("\nMONITOR REPORT");
    console.log(monitor.getReport());

    await runTests();
}


main().catch(error => {
    console.error("Application failure:", error.message);
    process.exitCode = 1;
});
