"use strict";

/*
 * Recursion Engineering Laboratory
 *
 * Demonstrates:
 * - Recursive problem decomposition
 * - Recursion trees
 * - Base and termination cases
 * - Memoization
 * - Divide-and-conquer algorithms
 * - Tree traversal
 * - Recursive dependency evaluation
 * - Asynchronous recursive execution
 * - Event-driven execution metrics
 * - Input validation and failure handling
 *
 * Runtime: Node.js 18+
 * Dependencies: None
 */

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");
const path = require("node:path");
const { performance } = require("node:perf_hooks");

class RecursionError extends Error {
    constructor(message) {
        super(message);
        this.name = "RecursionError";
    }
}

class InputValidationError extends RecursionError {
    constructor(message) {
        super(message);
        this.name = "InputValidationError";
    }
}

class RecursionBudgetError extends RecursionError {
    constructor(message) {
        super(message);
        this.name = "RecursionBudgetError";
    }
}

class CycleDetectedError extends RecursionError {
    constructor(message) {
        super(message);
        this.name = "CycleDetectedError";
    }
}

class ExecutionMonitor extends EventEmitter {
    constructor(maxDepth = 500) {
        super();

        if (!Number.isInteger(maxDepth) || maxDepth < 1) {
            throw new InputValidationError(
                "Maximum recursion depth must be positive."
            );
        }

        this.maxDepth = maxDepth;
        this.reset();
    }

    reset() {
        this.metrics = {
            calls: 0,
            maximumDepth: 0,
            cacheHits: 0,
            comparisons: 0
        };
    }

    enter(depth, operation) {
        if (depth > this.maxDepth) {
            throw new RecursionBudgetError(
                `Depth ${depth} exceeds ${this.maxDepth}.`
            );
        }

        this.metrics.calls++;
        this.metrics.maximumDepth = Math.max(
            this.metrics.maximumDepth,
            depth
        );

        this.emit("recursive-call", {
            operation,
            depth,
            totalCalls: this.metrics.calls
        });
    }

    cacheHit(key) {
        this.metrics.cacheHits++;
        this.emit("cache-hit", { key });
    }

    snapshot() {
        return Object.freeze({ ...this.metrics });
    }
}

function validateInteger(value, name, minimum = 0) {
    if (!Number.isSafeInteger(value) || value < minimum) {
        throw new InputValidationError(
            `${name} must be a safe integer >= ${minimum}.`
        );
    }
}

function factorial(n, monitor = new ExecutionMonitor()) {
    validateInteger(n, "n");

    if (n > 170) {
        throw new InputValidationError(
            "Factorial exceeds the finite Number range."
        );
    }

    function solve(value, depth) {
        monitor.enter(depth, "factorial");

        if (value <= 1) {
            return 1;
        }

        return value * solve(value - 1, depth + 1);
    }

    return solve(n, 0);
}

function fibonacciMemoized(n, monitor = new ExecutionMonitor()) {
    validateInteger(n, "n");

    if (n > 78) {
        throw new InputValidationError(
            "Fibonacci result exceeds Number.MAX_SAFE_INTEGER."
        );
    }

    const cache = new Map();

    function solve(value, depth) {
        monitor.enter(depth, "fibonacci");

        if (value <= 1) {
            return BigInt(value);
        }

        if (cache.has(value)) {
            monitor.cacheHit(value);
            return cache.get(value);
        }

        const result =
            solve(value - 1, depth + 1) +
            solve(value - 2, depth + 1);

        cache.set(value, result);
        return result;
    }

    return solve(n, 0);
}

function fibonacciBigInt(n) {
    validateInteger(n, "n");

    if (n > 10000) {
        throw new InputValidationError(
            "Input exceeds the configured Fibonacci limit."
        );
    }

    const memo = new Map([
        [0, 0n],
        [1, 1n]
    ]);

    function solve(value) {
        if (memo.has(value)) {
            return memo.get(value);
        }

        const result = solve(value - 1) + solve(value - 2);
        memo.set(value, result);
        return result;
    }

    return solve(n);
}

function binarySearch(values, target, monitor = new ExecutionMonitor()) {
    if (!Array.isArray(values)) {
        throw new InputValidationError("Expected an array.");
    }

    if (!values.every(Number.isSafeInteger)) {
        throw new InputValidationError(
            "Array must contain safe integers."
        );
    }

    if (!Number.isSafeInteger(target)) {
        throw new InputValidationError("Target must be a safe integer.");
    }

    for (let i = 1; i < values.length; i++) {
        if (values[i] < values[i - 1]) {
            throw new InputValidationError("Array must be sorted.");
        }
    }

    function search(left, right, depth) {
        monitor.enter(depth, "binary-search");

        if (left > right) {
            return -1;
        }

        const middle = left + Math.floor((right - left) / 2);
        monitor.metrics.comparisons++;

        if (values[middle] === target) {
            return middle;
        }

        if (target < values[middle]) {
            return search(left, middle - 1, depth + 1);
        }

        return search(middle + 1, right, depth + 1);
    }

    return search(0, values.length - 1, 0);
}

function mergeSort(values) {
    if (!Array.isArray(values)) {
        throw new InputValidationError("Expected an array.");
    }

    if (!values.every(Number.isSafeInteger)) {
        throw new InputValidationError(
            "Merge sort accepts safe integers only."
        );
    }

    function sort(items) {
        if (items.length <= 1) {
            return items.slice();
        }

        const middle = Math.floor(items.length / 2);

        const left = sort(items.slice(0, middle));
        const right = sort(items.slice(middle));

        return merge(left, right);
    }

    function merge(left, right) {
        const result = [];
        let i = 0;
        let j = 0;

        while (i < left.length && j < right.length) {
            if (left[i] <= right[j]) {
                result.push(left[i++]);
            } else {
                result.push(right[j++]);
            }
        }

        return result.concat(left.slice(i), right.slice(j));
    }

    return sort(values);
}

class BinaryTreeNode {
    constructor(value, left = null, right = null) {
        if (!Number.isSafeInteger(value)) {
            throw new InputValidationError(
                "Tree values must be safe integers."
            );
        }

        this.value = value;
        this.left = left;
        this.right = right;
    }
}

function traverseTree(root, order = "inorder") {
    const supported = new Set([
        "preorder",
        "inorder",
        "postorder"
    ]);

    if (!supported.has(order)) {
        throw new InputValidationError("Invalid traversal order.");
    }

    const visited = new WeakSet();
    const output = [];

    function visit(node, depth) {
        if (node === null) {
            return;
        }

        if (!(node instanceof BinaryTreeNode)) {
            throw new InputValidationError("Invalid tree node.");
        }

        if (visited.has(node)) {
            throw new CycleDetectedError(
                "Tree contains a cycle or shared child node."
            );
        }

        visited.add(node);

        if (order === "preorder") {
            output.push(node.value);
        }

        visit(node.left, depth + 1);

        if (order === "inorder") {
            output.push(node.value);
        }

        visit(node.right, depth + 1);

        if (order === "postorder") {
            output.push(node.value);
        }
    }

    visit(root, 0);
    return output;
}

/*
 * Recursive dependency evaluator.
 *
 * A dependency must be evaluated before its parent.
 * The active set detects cycles.
 * The completed map avoids repeated computation.
 */
class DependencyEngine {
    constructor(graph) {
        this.graph = new Map();

        for (const [task, dependencies] of Object.entries(graph)) {
            if (
                !Array.isArray(dependencies) ||
                typeof task !== "string" ||
                task.trim() === ""
            ) {
                throw new InputValidationError(
                    "Invalid dependency graph."
                );
            }

            this.graph.set(task, [...new Set(dependencies)]);
        }

        for (const dependencies of this.graph.values()) {
            for (const dependency of dependencies) {
                if (!this.graph.has(dependency)) {
                    throw new InputValidationError(
                        `Unknown dependency: ${dependency}`
                    );
                }
            }
        }
    }

    executionOrder() {
        const active = new Set();
        const completed = new Set();
        const result = [];

        function visit(task, graph) {
            if (completed.has(task)) {
                return;
            }

            if (active.has(task)) {
                throw new CycleDetectedError(
                    `Circular dependency at ${task}.`
                );
            }

            active.add(task);

            for (const dependency of graph.get(task)) {
                visit(dependency, graph);
            }

            active.delete(task);
            completed.add(task);
            result.push(task);
        }

        for (const task of this.graph.keys()) {
            visit(task, this.graph);
        }

        return result;
    }
}

/*
 * Asynchronous recursive traversal.
 *
 * Sequential awaits preserve dependency ordering.
 * An explicit depth budget prevents unbounded recursion.
 */
async function asyncTreeSum(node, maxDepth = 100) {
    if (!Number.isInteger(maxDepth) || maxDepth < 0) {
        throw new InputValidationError("Invalid depth budget.");
    }

    async function sum(current, depth) {
        if (depth > maxDepth) {
            throw new RecursionBudgetError(
                "Asynchronous tree depth exceeded."
            );
        }

        if (current === null) {
            return 0;
        }

        if (!(current instanceof BinaryTreeNode)) {
            throw new InputValidationError("Invalid tree node.");
        }

        const left = await sum(current.left, depth + 1);
        const right = await sum(current.right, depth + 1);

        return current.value + left + right;
    }

    return sum(node, 0);
}

/*
 * Safe recursive directory-size inspection.
 * Symlinks are excluded and filesystem errors are propagated.
 */
async function directorySize(directory, maxDepth = 20) {
    const root = await fs.realpath(directory);
    const rootStat = await fs.lstat(root);

    if (!rootStat.isDirectory()) {
        throw new InputValidationError(
            "Path must identify a directory."
        );
    }

    async function calculate(current, depth) {
        if (depth > maxDepth) {
            throw new RecursionBudgetError(
                "Directory depth exceeded."
            );
        }

        const entries = await fs.readdir(current, {
            withFileTypes: true
        });

        let total = 0;

        for (const entry of entries) {
            const child = path.join(current, entry.name);

            if (entry.isSymbolicLink()) {
                continue;
            }

            if (entry.isDirectory()) {
                total += await calculate(child, depth + 1);
            } else if (entry.isFile()) {
                const stat = await fs.stat(child);
                total += stat.size;
            }
        }

        return total;
    }

    return calculate(root, 0);
}

function buildRecursionTree(n, maxDepth = 5) {
    validateInteger(n, "n");

    if (!Number.isInteger(maxDepth) || maxDepth < 0) {
        throw new InputValidationError("Invalid display depth.");
    }

    function build(value, depth) {
        const node = {
            problem: `T(${value})`,
            depth,
            children: []
        };

        if (value <= 1 || depth >= maxDepth) {
            node.terminal =
                value <= 1 ? "base case" : "display limit";

            return node;
        }

        const next = Math.floor(value / 2);

        node.children.push(build(next, depth + 1));
        node.children.push(build(next, depth + 1));

        return node;
    }

    return build(n, 0);
}

function printRecursionTree(node, prefix = "") {
    console.log(`${prefix}${node.problem} ${node.terminal || ""}`);

    for (const child of node.children) {
        printRecursionTree(child, `${prefix}  `);
    }
}

function runAssertions() {
    const monitor = new ExecutionMonitor();

    console.assert(factorial(5, monitor) === 120);
    console.assert(factorial(0) === 1);
    console.assert(fibonacciMemoized(10) === 55n);
    console.assert(fibonacciBigInt(100) === 354224848179261915075n);

    console.assert(
        binarySearch([1, 3, 5, 7, 9], 7) === 3
    );

    console.assert(
        binarySearch([1, 3, 5, 7, 9], 8) === -1
    );

    console.assert(
        JSON.stringify(mergeSort([8, 2, 4, 1])) ===
        JSON.stringify([1, 2, 4, 8])
    );

    const root = new BinaryTreeNode(
        8,
        new BinaryTreeNode(4),
        new BinaryTreeNode(12)
    );

    console.assert(
        JSON.stringify(traverseTree(root)) ===
        JSON.stringify([4, 8, 12])
    );

    const graph = new DependencyEngine({
        deploy: ["test"],
        test: ["build"],
        build: ["compile"],
        compile: []
    });

    console.assert(
        JSON.stringify(graph.executionOrder()) ===
        JSON.stringify(["compile", "build", "test", "deploy"])
    );

    console.log("All synchronous assertions passed.");
}

async function main() {
    const monitor = new ExecutionMonitor(500);

    monitor.on("recursive-call", event => {
        if (event.depth <= 2) {
            console.log(
                `[TRACE] ${event.operation}, depth=${event.depth}`
            );
        }
    });

    monitor.on("cache-hit", event => {
        console.log(`[CACHE] Reused result for ${event.key}`);
    });

    console.log("\n1. Factorial");
    console.log("5! =", factorial(5, monitor));
    console.log("Metrics:", monitor.snapshot());

    monitor.reset();

    console.log("\n2. Memoized Fibonacci");
    console.log("F(40) =", fibonacciMemoized(40, monitor).toString());
    console.log("Metrics:", monitor.snapshot());

    console.log("\n3. Binary search");
    console.log(
        "Position:",
        binarySearch([2, 4, 6, 8, 10, 12], 8)
    );

    console.log("\n4. Merge sort");
    console.log(mergeSort([19, 4, 11, 2, 8, 1]));

    console.log("\n5. Binary tree");
    const root = new BinaryTreeNode(
        10,
        new BinaryTreeNode(
            5,
            new BinaryTreeNode(2),
            new BinaryTreeNode(7)
        ),
        new BinaryTreeNode(
            15,
            null,
            new BinaryTreeNode(20)
        )
    );

    console.log("Inorder:", traverseTree(root, "inorder"));
    console.log("Preorder:", traverseTree(root, "preorder"));
    console.log("Postorder:", traverseTree(root, "postorder"));

    console.log("\n6. Dependency evaluation");
    const dependencies = new DependencyEngine({
        deploy: ["integration-test"],
        "integration-test": ["unit-test"],
        "unit-test": ["build"],
        build: ["compile"],
        compile: []
    });

    console.log("Execution order:", dependencies.executionOrder());

    console.log("\n7. Asynchronous recursive sum");
    console.log("Tree sum:", await asyncTreeSum(root));

    console.log("\n8. Recursion tree");
    printRecursionTree(buildRecursionTree(16));

    console.log("\n9. Performance measurement");
    const start = performance.now();
    const sorted = mergeSort(
        Array.from({ length: 10000 }, (_, i) => 10000 - i)
    );
    const elapsed = performance.now() - start;

    console.log("Sorted elements:", sorted.length);
    console.log("Execution time (ms):", elapsed.toFixed(3));

    runAssertions();
}

main().catch(error => {
    console.error(`${error.name}: ${error.message}`);
    process.exitCode = 1;
});
