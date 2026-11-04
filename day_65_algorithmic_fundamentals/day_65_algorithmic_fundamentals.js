"use strict";

/*
 * Algorithm Fundamentals
 * Event-driven algorithm execution and correctness evaluation.
 *
 * Runtime: Node.js 18+
 */

const { EventEmitter } = require("node:events");
const { performance } = require("node:perf_hooks");
const crypto = require("node:crypto");

class AlgorithmError extends Error {}
class ValidationError extends AlgorithmError {}
class ContractViolationError extends AlgorithmError {}

const Complexity = Object.freeze({
    CONSTANT: "O(1)",
    LOGARITHMIC: "O(log n)",
    LINEAR: "O(n)",
    LINEARITHMIC: "O(n log n)",
    QUADRATIC: "O(n^2)",
    GRAPH: "O((V + E) log V)"
});

const AlgorithmState = Object.freeze({
    REGISTERED: "REGISTERED",
    RUNNING: "RUNNING",
    PASSED: "PASSED",
    FAILED: "FAILED"
});

function validateArray(values) {
    if (!Array.isArray(values)) {
        throw new ValidationError("Expected an array.");
    }

    if (!values.every(Number.isSafeInteger)) {
        throw new ValidationError(
            "All elements must be safe integers."
        );
    }
}

function assertSorted(values) {
    for (let i = 1; i < values.length; i++) {
        if (values[i - 1] > values[i]) {
            throw new ValidationError(
                "Binary search requires ascending order."
            );
        }
    }
}

function binarySearch(values, target) {
    validateArray(values);

    if (!Number.isSafeInteger(target)) {
        throw new ValidationError("Invalid search target.");
    }

    assertSorted(values);

    let low = 0;
    let high = values.length - 1;
    let comparisons = 0;

    while (low <= high) {
        const middle = low + Math.floor((high - low) / 2);
        comparisons++;

        if (values[middle] === target) {
            return {
                index: middle,
                comparisons
            };
        }

        comparisons++;

        if (values[middle] < target) {
            low = middle + 1;
        } else {
            high = middle - 1;
        }
    }

    return {
        index: -1,
        comparisons
    };
}

function quickSort(values) {
    validateArray(values);

    // Iterative three-way partitioning avoids recursion overflow
    // and handles repeated values efficiently.
    const result = values.slice();

    if (result.length < 2) {
        return result;
    }

    const stack = [[0, result.length - 1]];

    while (stack.length > 0) {
        const [left, right] = stack.pop();

        if (left >= right) continue;

        const pivot = result[
            left + Math.floor((right - left) / 2)
        ];

        let less = left;
        let current = left;
        let greater = right;

        while (current <= greater) {
            if (result[current] < pivot) {
                [result[less], result[current]] =
                    [result[current], result[less]];

                less++;
                current++;
            } else if (result[current] > pivot) {
                [result[current], result[greater]] =
                    [result[greater], result[current]];

                greater--;
            } else {
                current++;
            }
        }

        const leftSize = less - left;
        const rightSize = right - greater;

        // Process the smaller partition immediately.
        // The larger partition remains on the explicit stack.
        if (leftSize < rightSize) {
            if (greater + 1 < right) {
                stack.push([greater + 1, right]);
            }

            if (left < less - 1) {
                stack.push([left, less - 1]);
            }
        } else {
            if (left < less - 1) {
                stack.push([left, less - 1]);
            }

            if (greater + 1 < right) {
                stack.push([greater + 1, right]);
            }
        }
    }

    return result;
}

function topologicalSort(vertices, edges) {
    if (!Array.isArray(vertices) || !Array.isArray(edges)) {
        throw new ValidationError("Invalid graph input.");
    }

    const adjacency = new Map();
    const indegree = new Map();

    for (const vertex of vertices) {
        if (typeof vertex !== "string" || vertex.length === 0) {
            throw new ValidationError("Invalid vertex.");
        }

        if (adjacency.has(vertex)) {
            throw new ValidationError("Duplicate vertex.");
        }

        adjacency.set(vertex, []);
        indegree.set(vertex, 0);
    }

    for (const [from, to] of edges) {
        if (
            !adjacency.has(from) ||
            !adjacency.has(to) ||
            from === to
        ) {
            throw new ValidationError("Invalid directed edge.");
        }

        adjacency.get(from).push(to);
        indegree.set(to, indegree.get(to) + 1);
    }

    const queue = [];

    for (const [vertex, degree] of indegree) {
        if (degree === 0) queue.push(vertex);
    }

    // A moving head avoids the repeated cost of Array.shift().
    let head = 0;
    const order = [];

    while (head < queue.length) {
        const current = queue[head++];
        order.push(current);

        for (const neighbor of adjacency.get(current)) {
            const updated = indegree.get(neighbor) - 1;
            indegree.set(neighbor, updated);

            if (updated === 0) {
                queue.push(neighbor);
            }
        }
    }

    if (order.length !== vertices.length) {
        throw new ContractViolationError(
            "Graph contains a directed cycle."
        );
    }

    return order;
}

function hashInput(value) {
    return crypto
        .createHash("sha256")
        .update(JSON.stringify(value))
        .digest("hex");
}

class AlgorithmDefinition {
    constructor({
        name,
        category,
        complexity,
        spaceComplexity,
        execute,
        validateOutput
    }) {
        if (
            !name ||
            typeof name !== "string" ||
            typeof execute !== "function" ||
            typeof validateOutput !== "function"
        ) {
            throw new ValidationError(
                "Incomplete algorithm definition."
            );
        }

        this.name = name;
        this.category = category;
        this.complexity = complexity;
        this.spaceComplexity = spaceComplexity;
        this.execute = execute;
        this.validateOutput = validateOutput;
        Object.freeze(this);
    }
}

class AlgorithmEngine extends EventEmitter {
    constructor() {
        super();

        this.registry = new Map();
        this.executionHistory = [];
        this.maximumHistory = 1000;
    }

    register(definition) {
        if (!(definition instanceof AlgorithmDefinition)) {
            throw new ValidationError(
                "Expected an AlgorithmDefinition."
            );
        }

        if (this.registry.has(definition.name)) {
            throw new ValidationError(
                "Algorithm name already exists."
            );
        }

        this.registry.set(definition.name, {
            definition,
            state: AlgorithmState.REGISTERED
        });

        this.emit("registered", definition.name);
    }

    async execute(name, input) {
        const entry = this.registry.get(name);

        if (!entry) {
            throw new ValidationError(
                `Unknown algorithm: ${name}`
            );
        }

        if (entry.state === AlgorithmState.RUNNING) {
            throw new ContractViolationError(
                "Algorithm is already running."
            );
        }

        const { definition } = entry;
        const inputHash = hashInput(input);

        entry.state = AlgorithmState.RUNNING;

        this.emit("started", {
            name,
            inputHash
        });

        const start = performance.now();

        try {
            // Yield execution to allow other event-loop work.
            await new Promise(resolve => setImmediate(resolve));

            const output = definition.execute(input);

            const valid = definition.validateOutput(
                input,
                output
            );

            if (!valid) {
                throw new ContractViolationError(
                    "Output failed correctness validation."
                );
            }

            const duration = performance.now() - start;

            const record = Object.freeze({
                id: crypto.randomUUID(),
                name,
                inputHash,
                outputHash: hashInput(output),
                state: AlgorithmState.PASSED,
                durationMilliseconds: Number(duration.toFixed(4)),
                executedAt: new Date().toISOString()
            });

            entry.state = AlgorithmState.PASSED;
            this.record(record);
            this.emit("completed", record);

            return {
                output,
                metrics: record
            };
        } catch (error) {
            entry.state = AlgorithmState.FAILED;

            const record = Object.freeze({
                id: crypto.randomUUID(),
                name,
                inputHash,
                state: AlgorithmState.FAILED,
                error: error.message,
                executedAt: new Date().toISOString()
            });

            this.record(record);
            this.emit("failed", record);

            throw error;
        }
    }

    record(record) {
        this.executionHistory.push(record);

        if (
            this.executionHistory.length >
            this.maximumHistory
        ) {
            this.executionHistory.shift();
        }
    }

    getHistory() {
        return this.executionHistory.slice();
    }

    getStatus(name) {
        const entry = this.registry.get(name);

        if (!entry) {
            throw new ValidationError("Unknown algorithm.");
        }

        return entry.state;
    }
}

function isSortedAscending(values) {
    return values.every(
        (value, index) =>
            index === 0 || values[index - 1] <= value
    );
}

function testSorting() {
    const cases = [
        [],
        [1],
        [9, 3, 7, 2, 5],
        [4, 4, 4, 1],
        [-10, 0, 8, -3],
        Array.from(
            { length: 10000 },
            (_, index) => 10000 - index
        )
    ];

    for (const input of cases) {
        const output = quickSort(input);
        const expected = input.slice().sort((a, b) => a - b);

        if (JSON.stringify(output) !== JSON.stringify(expected)) {
            throw new ContractViolationError(
                "Sorting correctness test failed."
            );
        }

        if (!isSortedAscending(output)) {
            throw new ContractViolationError(
                "Sorted-order postcondition failed."
            );
        }

        if (input.length !== output.length) {
            throw new ContractViolationError(
                "Sorting changed the number of elements."
            );
        }
    }
}

function testTopologicalSort() {
    const vertices = ["Design", "Code", "Test", "Deploy"];

    const edges = [
        ["Design", "Code"],
        ["Code", "Test"],
        ["Test", "Deploy"]
    ];

    const result = topologicalSort(vertices, edges);
    const positions = new Map(
        result.map((vertex, index) => [vertex, index])
    );

    for (const [from, to] of edges) {
        if (positions.get(from) >= positions.get(to)) {
            throw new ContractViolationError(
                "Topological ordering is invalid."
            );
        }
    }

    return result;
}

async function main() {
    const engine = new AlgorithmEngine();

    engine.on("registered", name => {
        console.log(`Registered: ${name}`);
    });

    engine.on("completed", record => {
        console.log(
            `Completed ${record.name}: ` +
            `${record.durationMilliseconds} ms`
        );
    });

    engine.on("failed", record => {
        console.error(
            `Failed ${record.name}: ${record.error}`
        );
    });

    engine.register(
        new AlgorithmDefinition({
            name: "quick_sort",
            category: "SORTING",
            complexity: "Average O(n log n), worst O(n^2)",
            spaceComplexity: "O(log n) typical stack usage",
            execute: quickSort,
            validateOutput: (input, output) =>
                output.length === input.length &&
                isSortedAscending(output) &&
                input.every(value => output.includes(value))
        })
    );

    engine.register(
        new AlgorithmDefinition({
            name: "topological_sort",
            category: "GRAPH",
            complexity: "O(V + E)",
            spaceComplexity: "O(V + E)",
            execute: ({ vertices, edges }) =>
                topologicalSort(vertices, edges),
            validateOutput: ({ vertices, edges }, output) => {
                if (output.length !== vertices.length) {
                    return false;
                }

                const positions = new Map(
                    output.map((vertex, index) => [vertex, index])
                );

                return edges.every(
                    ([from, to]) =>
                        positions.get(from) < positions.get(to)
                );
            }
        })
    );

    testSorting();

    const sorting = await engine.execute(
        "quick_sort",
        [40, 10, 30, 20, 50, 10]
    );

    console.log("\nSorted output:", sorting.output);
    console.log("Execution record:", sorting.metrics);

    const graphResult = await engine.execute(
        "topological_sort",
        {
            vertices: ["Database", "API", "Frontend", "Testing"],
            edges: [
                ["Database", "API"],
                ["API", "Frontend"],
                ["Frontend", "Testing"]
            ]
        }
    );

    console.log("\nDependency order:", graphResult.output);

    console.log("\nBinary search:", binarySearch(
        [2, 4, 6, 8, 10, 12],
        8
    ));

    console.log("\nExecution history:", engine.getHistory());

    try {
        await engine.execute("unknown_algorithm", []);
    } catch (error) {
        console.log("\nExpected failure:", error.message);
    }

    try {
        topologicalSort(
            ["A", "B"],
            [["A", "B"], ["B", "A"]]
        );
    } catch (error) {
        console.log("Cycle detection:", error.message);
    }

    console.log("\nAll algorithm tests completed.");
}

main().catch(error => {
    console.error("Application failure:", error.message);
    process.exitCode = 1;
});
