"use strict";

/*
 * DYNAMIC PROGRAMMING
 *
 * JavaScript implementation focused on:
 * - Memoization with Map
 * - Promise-based asynchronous memoization
 * - Bottom-up tabulation
 * - Event-driven computation
 * - Weighted interval scheduling
 * - Dynamic programming policy evaluation
 *
 * Runtime: Node.js 18+
 */

const { EventEmitter } = require("node:events");
const assert = require("node:assert/strict");

// ============================================================
// VALIDATION
// ============================================================

function requireNonNegativeInteger(value, name) {
    if (!Number.isSafeInteger(value) || value < 0) {
        throw new RangeError(`${name} must be a non-negative safe integer.`);
    }
}

function requirePositiveInteger(value, name) {
    if (!Number.isSafeInteger(value) || value <= 0) {
        throw new RangeError(`${name} must be a positive safe integer.`);
    }
}

// ============================================================
// 1. GENERIC MEMOIZATION
// ============================================================

function memoize(fn, keyFunction = (...args) => JSON.stringify(args)) {
    const cache = new Map();

    function wrapped(...args) {
        const key = keyFunction(...args);

        if (cache.has(key)) {
            return cache.get(key);
        }

        const result = fn(...args);
        cache.set(key, result);

        return result;
    }

    wrapped.clear = () => cache.clear();
    wrapped.cacheSize = () => cache.size;

    return wrapped;
}

// ============================================================
// 2. ASYNCHRONOUS MEMOIZATION
// ============================================================

function memoizeAsync(fn) {
    const cache = new Map();

    return async function (...args) {
        const key = JSON.stringify(args);

        if (cache.has(key)) {
            return cache.get(key);
        }

        // Store the pending Promise so concurrent callers share work.
        const pending = Promise.resolve().then(() => fn(...args));

        cache.set(key, pending);

        try {
            return await pending;
        } catch (error) {
            // Failed operations must not remain permanently cached.
            if (cache.get(key) === pending) {
                cache.delete(key);
            }

            throw error;
        }
    };
}

// ============================================================
// 3. FIBONACCI
// ============================================================

const fibonacciMemoized = memoize(function fibonacci(n) {
    requireNonNegativeInteger(n, "n");

    if (n <= 1) {
        return BigInt(n);
    }

    return fibonacciMemoized(n - 1) + fibonacciMemoized(n - 2);
});

function fibonacciTabulated(n) {
    requireNonNegativeInteger(n, "n");

    if (n <= 1) {
        return BigInt(n);
    }

    let previous = 0n;
    let current = 1n;

    for (let i = 2; i <= n; i++) {
        [previous, current] = [
            current,
            previous + current
        ];
    }

    return current;
}

// ============================================================
// 4. GRID PATH COUNTING
// ============================================================

function gridPathCount(rows, columns, blockedCells = []) {
    requirePositiveInteger(rows, "rows");
    requirePositiveInteger(columns, "columns");

    const blocked = new Set();

    for (const cell of blockedCells) {
        if (
            !Array.isArray(cell) ||
            cell.length !== 2 ||
            !Number.isInteger(cell[0]) ||
            !Number.isInteger(cell[1])
        ) {
            throw new TypeError("Each obstacle must be [row, column].");
        }

        const [r, c] = cell;

        if (r < 0 || r >= rows || c < 0 || c >= columns) {
            throw new RangeError("Obstacle outside grid.");
        }

        blocked.add(`${r},${c}`);
    }

    const dp = Array(columns).fill(0n);

    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < columns; c++) {

            if (blocked.has(`${r},${c}`)) {
                dp[c] = 0n;
                continue;
            }

            if (r === 0 && c === 0) {
                dp[c] = 1n;
                continue;
            }

            const above = dp[c];
            const left = c > 0 ? dp[c - 1] : 0n;

            dp[c] = above + left;
        }
    }

    return dp[columns - 1];
}

// ============================================================
// 5. WEIGHTED INTERVAL SCHEDULING
// ============================================================

class Job {
    constructor(id, start, end, profit) {

        if (typeof id !== "string" || !id.trim()) {
            throw new TypeError("Job ID must be a non-empty string.");
        }

        if (
            !Number.isFinite(start) ||
            !Number.isFinite(end) ||
            start >= end
        ) {
            throw new RangeError("Invalid job interval.");
        }

        if (!Number.isFinite(profit) || profit < 0) {
            throw new RangeError("Profit must be non-negative.");
        }

        this.id = id;
        this.start = start;
        this.end = end;
        this.profit = profit;

        Object.freeze(this);
    }
}

function weightedIntervalScheduling(jobs) {

    if (!Array.isArray(jobs)) {
        throw new TypeError("Jobs must be an array.");
    }

    const ids = new Set();

    for (const job of jobs) {

        if (!(job instanceof Job)) {
            throw new TypeError("Every entry must be a Job.");
        }

        if (ids.has(job.id)) {
            throw new Error(`Duplicate job ID: ${job.id}`);
        }

        ids.add(job.id);
    }

    const sorted = [...jobs].sort(
        (a, b) => a.end - b.end || a.start - b.start || a.id.localeCompare(b.id)
    );

    const n = sorted.length;

    // Find the latest job compatible with each job.
    const predecessor = Array(n).fill(-1);

    for (let i = 0; i < n; i++) {

        let low = 0;
        let high = i - 1;
        let answer = -1;

        while (low <= high) {

            const mid = Math.floor((low + high) / 2);

            if (sorted[mid].end <= sorted[i].start) {
                answer = mid;
                low = mid + 1;
            } else {
                high = mid - 1;
            }
        }

        predecessor[i] = answer;
    }

    // dp[i] represents the best profit from the first i jobs.
    const dp = Array(n + 1).fill(0);

    for (let i = 1; i <= n; i++) {

        const job = sorted[i - 1];

        const include =
            job.profit + dp[predecessor[i - 1] + 1];

        const exclude = dp[i - 1];

        dp[i] = Math.max(include, exclude);
    }

    const selected = [];
    let i = n;

    while (i > 0) {

        const job = sorted[i - 1];

        const include =
            job.profit + dp[predecessor[i - 1] + 1];

        if (include > dp[i - 1]) {

            selected.push(job);

            i = predecessor[i - 1] + 1;

        } else {
            i--;
        }
    }

    selected.reverse();

    return Object.freeze({
        maximumProfit: dp[n],
        selectedJobs: Object.freeze(selected),
        statesComputed: n + 1
    });
}

// ============================================================
// 6. EVENT-DRIVEN DP ENGINE
// ============================================================

class DynamicProgrammingEngine extends EventEmitter {

    constructor() {
        super();

        this.results = new Map();
        this.running = new Set();
    }

    async execute(taskId, computation) {

        if (typeof taskId !== "string" || !taskId.trim()) {
            throw new TypeError("Task ID is required.");
        }

        if (typeof computation !== "function") {
            throw new TypeError("Computation must be a function.");
        }

        if (this.running.has(taskId)) {
            throw new Error(`Task already running: ${taskId}`);
        }

        this.running.add(taskId);

        this.emit("started", { taskId });

        try {

            const result = await computation();

            this.results.set(taskId, result);

            this.emit("completed", {
                taskId,
                result
            });

            return result;

        } catch (error) {

            this.emit("failed", {
                taskId,
                error: error.message
            });

            throw error;

        } finally {
            this.running.delete(taskId);
        }
    }

    getResult(taskId) {
        return this.results.get(taskId);
    }
}

// ============================================================
// 7. DYNAMIC PROGRAMMING WITH CONSTRAINT POLICIES
// ============================================================

class BudgetOptimizer {

    constructor(budget) {
        requireNonNegativeInteger(budget, "budget");
        this.budget = budget;
    }

    optimize(projects) {

        const jobs = projects.map(project => {

            requirePositiveInteger(project.cost, "project cost");

            if (
                !Number.isSafeInteger(project.value) ||
                project.value < 0
            ) {
                throw new RangeError("Project value must be non-negative.");
            }

            return new Job(
                project.id,
                0,
                project.cost,
                project.value
            );
        });

        // Convert projects to a 0/1 knapsack problem.
        const n = jobs.length;

        const dp = Array(this.budget + 1).fill(0);
        const choices = Array.from(
            { length: n + 1 },
            () => Array(this.budget + 1).fill(false)
        );

        for (let i = 1; i <= n; i++) {

            const project = projects[i - 1];

            for (let capacity = this.budget; capacity >= 0; capacity--) {

                const exclude = dp[capacity];

                let include = -1;

                if (project.cost <= capacity) {
                    include =
                        dp[capacity - project.cost] + project.value;
                }

                if (include > exclude) {
                    dp[capacity] = include;
                    choices[i][capacity] = true;
                }
            }
        }

        // Reconstruct using a separate full table for correctness.
        const table = Array.from(
            { length: n + 1 },
            () => Array(this.budget + 1).fill(0)
        );

        for (let i = 1; i <= n; i++) {
            const project = projects[i - 1];

            for (let capacity = 0; capacity <= this.budget; capacity++) {

                table[i][capacity] = table[i - 1][capacity];

                if (project.cost <= capacity) {
                    table[i][capacity] = Math.max(
                        table[i][capacity],
                        project.value + table[i - 1][capacity - project.cost]
                    );
                }
            }
        }

        const selected = [];
        let remaining = this.budget;

        for (let i = n; i > 0; i--) {

            if (table[i][remaining] !== table[i - 1][remaining]) {
                selected.push(projects[i - 1].id);
                remaining -= projects[i - 1].cost;
            }
        }

        selected.reverse();

        return Object.freeze({
            maximumValue: table[n][this.budget],
            selectedProjects: Object.freeze(selected),
            budget: this.budget
        });
    }
}

// ============================================================
// 8. TESTS AND DEMONSTRATION
// ============================================================

async function runTests() {

    assert.equal(fibonacciMemoized(20), 6765n);
    assert.equal(fibonacciTabulated(20), 6765n);

    assert.equal(gridPathCount(3, 3), 6n);

    assert.equal(
        gridPathCount(3, 3, [[1, 1]]),
        2n
    );

    assert.equal(
        gridPathCount(1, 1),
        1n
    );

    const jobs = [
        new Job("A", 1, 3, 50),
        new Job("B", 3, 5, 60),
        new Job("C", 2, 6, 80),
        new Job("D", 5, 7, 40)
    ];

    const schedule = weightedIntervalScheduling(jobs);

    assert.equal(schedule.maximumProfit, 150);

    const optimizer = new BudgetOptimizer(7);

    const result = optimizer.optimize([
        { id: "Database", cost: 4, value: 80 },
        { id: "Security", cost: 3, value: 60 },
        { id: "Monitoring", cost: 2, value: 40 },
        { id: "Backup", cost: 5, value: 90 }
    ]);

    assert.equal(result.maximumValue, 140);

    const asynchronousFibonacci = memoizeAsync(async n => {
        return fibonacciTabulated(n);
    });

    assert.equal(
        await asynchronousFibonacci(30),
        832040n
    );

    // Concurrent calls share the same pending computation.
    const engine = new DynamicProgrammingEngine();

    const events = [];

    engine.on("started", event => events.push(`started:${event.taskId}`));
    engine.on("completed", event => events.push(`completed:${event.taskId}`));

    const output = await engine.execute(
        "fibonacci-job",
        async () => fibonacciTabulated(25)
    );

    assert.equal(output, 75025n);

    assert.deepEqual(events, [
        "started:fibonacci-job",
        "completed:fibonacci-job"
    ]);

    await assert.rejects(
        engine.execute("failure", async () => {
            throw new Error("Computation failed.");
        }),
        /Computation failed/
    );

    console.log("All JavaScript tests passed.");
}

async function main() {

    console.log("\nDYNAMIC PROGRAMMING ENGINE");
    console.log("==========================");

    console.log("\n1. Fibonacci");
    console.log("Memoization:", fibonacciMemoized(40).toString());
    console.log("Tabulation:", fibonacciTabulated(40).toString());

    console.log("\n2. Grid Paths");
    console.log(
        "Available paths:",
        gridPathCount(5, 5, [[1, 2], [2, 2]]).toString()
    );

    console.log("\n3. Weighted Interval Scheduling");

    const jobs = [
        new Job("Development", 1, 4, 100),
        new Job("Testing", 4, 6, 80),
        new Job("Deployment", 6, 8, 120),
        new Job("Research", 2, 7, 150)
    ];

    const schedule = weightedIntervalScheduling(jobs);

    console.log("Maximum profit:", schedule.maximumProfit);
    console.log(
        "Selected jobs:",
        schedule.selectedJobs.map(job => job.id)
    );

    console.log("\n4. Budget Optimization");

    const optimizer = new BudgetOptimizer(10);

    console.log(
        optimizer.optimize([
            { id: "Infrastructure", cost: 5, value: 100 },
            { id: "Security", cost: 3, value: 80 },
            { id: "Monitoring", cost: 2, value: 50 },
            { id: "Backup", cost: 6, value: 120 }
        ])
    );

    console.log("\n5. Validation");

    await runTests();
}

if (require.main === module) {
    main().catch(error => {
        console.error("Execution failed:", error.message);
        process.exitCode = 1;
    });
}

module.exports = {
    memoize,
    memoizeAsync,
    fibonacciMemoized,
    fibonacciTabulated,
    gridPathCount,
    Job,
    weightedIntervalScheduling,
    DynamicProgrammingEngine,
    BudgetOptimizer
};
