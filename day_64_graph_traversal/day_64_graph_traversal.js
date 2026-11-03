"use strict";

/*
 * Graph Traversal: event-driven BFS, DFS, and traversal applications.
 *
 * Runtime: Node.js 18 or later.
 *
 * Features:
 * - Directed and undirected adjacency-list graphs
 * - Asynchronous BFS and DFS
 * - EventEmitter-based traversal notifications
 * - AbortSignal cancellation
 * - Traversal limits
 * - Shortest-hop path reconstruction
 * - Dependency and outage-impact analysis
 * - Input validation and failure handling
 */

const { EventEmitter } = require("node:events");
const assert = require("node:assert/strict");

class GraphError extends Error {
    constructor(message) {
        super(message);
        this.name = "GraphError";
    }
}

class VertexNotFoundError extends GraphError {
    constructor(vertex) {
        super(`Vertex does not exist: ${vertex}`);
        this.name = "VertexNotFoundError";
    }
}

class TraversalLimitError extends GraphError {
    constructor(limit) {
        super(`Traversal exceeded the limit of ${limit} vertices.`);
        this.name = "TraversalLimitError";
    }
}

class TraversalCancelledError extends GraphError {
    constructor() {
        super("Traversal was cancelled.");
        this.name = "AbortError";
    }
}

class Graph {
    #adjacency = new Map();

    constructor({ directed = true } = {}) {
        this.directed = Boolean(directed);
    }

    static validateVertex(vertex) {
        if (
            typeof vertex !== "string" ||
            vertex.length === 0 ||
            vertex.trim() !== vertex ||
            vertex.length > 128
        ) {
            throw new TypeError(
                "Vertex identifiers must be non-empty, trimmed strings " +
                "of at most 128 characters."
            );
        }
    }

    addVertex(vertex) {
        Graph.validateVertex(vertex);

        if (!this.#adjacency.has(vertex)) {
            this.#adjacency.set(vertex, new Set());
        }

        return this;
    }

    addEdge(source, target) {
        Graph.validateVertex(source);
        Graph.validateVertex(target);

        this.addVertex(source);
        this.addVertex(target);

        this.#adjacency.get(source).add(target);

        if (!this.directed) {
            this.#adjacency.get(target).add(source);
        }

        return this;
    }

    hasVertex(vertex) {
        return this.#adjacency.has(vertex);
    }

    get size() {
        return this.#adjacency.size;
    }

    vertices() {
        return [...this.#adjacency.keys()].sort();
    }

    neighbors(vertex) {
        const adjacent = this.#adjacency.get(vertex);

        if (adjacent === undefined) {
            throw new VertexNotFoundError(vertex);
        }

        return [...adjacent].sort();
    }

    assertVertex(vertex) {
        if (!this.hasVertex(vertex)) {
            throw new VertexNotFoundError(vertex);
        }
    }
}

class TraversalEngine extends EventEmitter {
    constructor(graph) {
        super();

        if (!(graph instanceof Graph)) {
            throw new TypeError("TraversalEngine requires a Graph instance.");
        }

        this.graph = graph;
    }

    #validateOptions({ signal, maxVisited }) {
        if (
            !Number.isSafeInteger(maxVisited) ||
            maxVisited < 1
        ) {
            throw new RangeError("maxVisited must be a positive safe integer.");
        }

        if (
            signal !== undefined &&
            (
                typeof signal.aborted !== "boolean" ||
                typeof signal.addEventListener !== "function"
            )
        ) {
            throw new TypeError("signal must be an AbortSignal.");
        }
    }

    #checkCancellation(signal) {
        if (signal?.aborted) {
            throw new TraversalCancelledError();
        }
    }

    #discover(vertex, parent, depth, maxVisited) {
        if (parent.has(vertex)) {
            return false;
        }

        if (parent.size >= maxVisited) {
            throw new TraversalLimitError(maxVisited);
        }

        return true;
    }

    async #yieldToEventLoop(signal) {
        this.#checkCancellation(signal);
        await new Promise((resolve) => setImmediate(resolve));
        this.#checkCancellation(signal);
    }

    async breadthFirst(start, options = {}) {
        const {
            signal,
            maxVisited = 100_000
        } = options;

        this.graph.assertVertex(start);
        this.#validateOptions({ signal, maxVisited });
        this.#checkCancellation(signal);

        const queue = [start];
        let head = 0;

        const parent = new Map([[start, null]]);
        const depth = new Map([[start, 0]]);
        const order = [];

        this.emit("start", {
            algorithm: "BFS",
            start
        });

        try {
            this.emit("discover", {
                algorithm: "BFS",
                vertex: start,
                parent: null,
                depth: 0
            });

            while (head < queue.length) {
                this.#checkCancellation(signal);

                const current = queue[head++];
                order.push(current);

                this.emit("visit", {
                    algorithm: "BFS",
                    vertex: current,
                    depth: depth.get(current)
                });

                for (const neighbor of this.graph.neighbors(current)) {
                    if (!this.#discover(neighbor, parent, depth, maxVisited)) {
                        continue;
                    }

                    parent.set(neighbor, current);
                    depth.set(neighbor, depth.get(current) + 1);
                    queue.push(neighbor);

                    this.emit("discover", {
                        algorithm: "BFS",
                        vertex: neighbor,
                        parent: current,
                        depth: depth.get(neighbor)
                    });
                }

                await this.#yieldToEventLoop(signal);
            }

            const result = Object.freeze({
                algorithm: "BFS",
                start,
                order: Object.freeze(order.slice()),
                parent,
                depth
            });

            this.emit("finish", result);
            return result;
        } catch (error) {
            this.emit("failure", {
                algorithm: "BFS",
                start,
                error
            });

            throw error;
        }
    }

    async depthFirst(start, options = {}) {
        const {
            signal,
            maxVisited = 100_000
        } = options;

        this.graph.assertVertex(start);
        this.#validateOptions({ signal, maxVisited });
        this.#checkCancellation(signal);

        const parent = new Map([[start, null]]);
        const depth = new Map([[start, 0]]);
        const order = [];

        this.emit("start", {
            algorithm: "DFS",
            start
        });

        try {
            const stack = [{
                vertex: start,
                neighbors: this.graph.neighbors(start),
                nextIndex: 0
            }];

            order.push(start);

            this.emit("discover", {
                algorithm: "DFS",
                vertex: start,
                parent: null,
                depth: 0
            });

            this.emit("visit", {
                algorithm: "DFS",
                vertex: start,
                depth: 0
            });

            await this.#yieldToEventLoop(signal);

            /*
             * Each frame stores its own neighbor position.
             * This reproduces recursive DFS ordering without recursion.
             */
            while (stack.length > 0) {
                this.#checkCancellation(signal);

                const frame = stack[stack.length - 1];

                if (frame.nextIndex >= frame.neighbors.length) {
                    stack.pop();
                    continue;
                }

                const neighbor = frame.neighbors[frame.nextIndex++];

                if (!this.#discover(neighbor, parent, depth, maxVisited)) {
                    continue;
                }

                const nextDepth = depth.get(frame.vertex) + 1;

                parent.set(neighbor, frame.vertex);
                depth.set(neighbor, nextDepth);
                order.push(neighbor);

                this.emit("discover", {
                    algorithm: "DFS",
                    vertex: neighbor,
                    parent: frame.vertex,
                    depth: nextDepth
                });

                this.emit("visit", {
                    algorithm: "DFS",
                    vertex: neighbor,
                    depth: nextDepth
                });

                stack.push({
                    vertex: neighbor,
                    neighbors: this.graph.neighbors(neighbor),
                    nextIndex: 0
                });

                await this.#yieldToEventLoop(signal);
            }

            const result = Object.freeze({
                algorithm: "DFS",
                start,
                order: Object.freeze(order.slice()),
                parent,
                depth
            });

            this.emit("finish", result);
            return result;
        } catch (error) {
            this.emit("failure", {
                algorithm: "DFS",
                start,
                error
            });

            throw error;
        }
    }
}

function reconstructPath(result, target) {
    if (!(result.parent instanceof Map)) {
        throw new TypeError("A traversal result with a parent Map is required.");
    }

    if (!result.parent.has(target)) {
        return null;
    }

    const path = [];
    let current = target;

    while (current !== null) {
        path.push(current);
        current = result.parent.get(current);
    }

    return path.reverse();
}

function formatPath(path) {
    return path === null ? "unreachable" : path.join(" -> ");
}

async function demonstrateServiceDependencies() {
    /*
     * An edge dependency -> consumer represents impact propagation.
     * If a dependency fails, BFS discovers downstream services that
     * may become unavailable.
     */
    const graph = new Graph({ directed: true });

    const dependencies = [
        ["customer-database", "orders-api"],
        ["customer-database", "billing-api"],
        ["orders-api", "checkout-api"],
        ["billing-api", "checkout-api"],
        ["checkout-api", "web-frontend"],
        ["billing-api", "finance-report"],
        ["identity-service", "checkout-api"]
    ];

    for (const [source, target] of dependencies) {
        graph.addEdge(source, target);
    }

    const engine = new TraversalEngine(graph);
    const events = [];

    engine.on("discover", ({ algorithm, vertex, depth }) => {
        events.push({
            type: "discover",
            algorithm,
            vertex,
            depth
        });
    });

    engine.on("visit", ({ algorithm, vertex }) => {
        events.push({
            type: "visit",
            algorithm,
            vertex
        });
    });

    engine.on("finish", ({ algorithm, order }) => {
        console.log(`\n${algorithm} completed: ${order.length} vertices.`);
    });

    console.log("SERVICE DEPENDENCY GRAPH");

    const bfs = await engine.breadthFirst("customer-database");

    console.log("BFS impact order:", bfs.order);
    console.log(
        "Checkout dependency chain:",
        formatPath(reconstructPath(bfs, "web-frontend"))
    );

    const dfs = await engine.depthFirst("customer-database");

    console.log("DFS inspection order:", dfs.order);
    console.log("Event count:", events.length);

    assert.equal(bfs.depth.get("web-frontend"), 3);
    assert.deepEqual(
        reconstructPath(bfs, "web-frontend"),
        [
            "customer-database",
            "billing-api",
            "checkout-api",
            "web-frontend"
        ]
    );

    assert.equal(reconstructPath(bfs, "unknown-service"), null);
    assert.ok(dfs.order.includes("finance-report"));
}

async function demonstrateCancellation() {
    const graph = new Graph({ directed: false });

    graph
        .addEdge("A", "B")
        .addEdge("B", "C")
        .addEdge("C", "D");

    const engine = new TraversalEngine(graph);
    const controller = new AbortController();

    engine.once("visit", () => {
        controller.abort();
    });

    try {
        await engine.breadthFirst("A", {
            signal: controller.signal
        });

        throw new Error("Expected cancellation did not occur.");
    } catch (error) {
        if (error.name !== "AbortError") {
            throw error;
        }

        console.log("\nTraversal cancellation handled:", error.message);
    }
}

async function demonstrateLimitsAndValidation() {
    const graph = new Graph({ directed: false });

    graph
        .addEdge("A", "B")
        .addEdge("B", "C")
        .addEdge("C", "D");

    const engine = new TraversalEngine(graph);

    try {
        await engine.breadthFirst("A", { maxVisited: 2 });
        throw new Error("Expected traversal limit failure did not occur.");
    } catch (error) {
        if (!(error instanceof TraversalLimitError)) {
            throw error;
        }

        console.log("\nTraversal limit handled:", error.message);
    }

    try {
        await engine.breadthFirst("missing");
        throw new Error("Expected unknown vertex failure did not occur.");
    } catch (error) {
        if (!(error instanceof VertexNotFoundError)) {
            throw error;
        }

        console.log("Unknown vertex handled:", error.message);
    }

    try {
        graph.addVertex(" invalid ");
        throw new Error("Expected invalid identifier failure did not occur.");
    } catch (error) {
        if (!(error instanceof TypeError)) {
            throw error;
        }

        console.log("Invalid identifier handled:", error.message);
    }
}

async function main() {
    await demonstrateServiceDependencies();
    await demonstrateCancellation();
    await demonstrateLimitsAndValidation();

    console.log("\nAll JavaScript graph traversal checks passed.");
}

main().catch((error) => {
    console.error("Graph traversal failed:", error);
    process.exitCode = 1;
});
