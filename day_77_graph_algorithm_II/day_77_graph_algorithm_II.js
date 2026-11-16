"use strict";

/*
 * Graph Algorithms II
 * Dijkstra's Shortest Path Engine
 *
 * Node.js 18+
 *
 * Engineering perspective:
 * - Event-driven graph updates
 * - Asynchronous shortest-path requests
 * - Binary min-heap
 * - Map and Set based graph representation
 * - Versioned graph snapshots
 * - Request cancellation
 * - Path reconstruction
 * - Multi-source routing
 * - Structured execution diagnostics
 *
 * Run:
 * node dijkstra.js
 */

const { EventEmitter } = require("node:events");
const assert = require("node:assert/strict");

class GraphError extends Error {}
class NegativeWeightError extends GraphError {}
class UnknownVertexError extends GraphError {}
class ConcurrentModificationError extends GraphError {}

/*
 * Binary min-heap.
 *
 * Push and pop both require O(log V) time.
 * This avoids repeatedly sorting the entire priority queue.
 */
class MinHeap {
    constructor() {
        this.items = [];
        this.sequence = 0;
    }

    get size() {
        return this.items.length;
    }

    push(distance, vertex) {
        const entry = {
            distance,
            vertex,
            sequence: this.sequence++
        };

        this.items.push(entry);

        let index = this.items.length - 1;

        while (index > 0) {
            const parent = Math.floor((index - 1) / 2);

            if (!this.less(this.items[index], this.items[parent])) {
                break;
            }

            [this.items[index], this.items[parent]] =
                [this.items[parent], this.items[index]];

            index = parent;
        }
    }

    less(a, b) {
        if (a.distance !== b.distance) {
            return a.distance < b.distance;
        }

        return a.sequence < b.sequence;
    }

    pop() {
        if (this.items.length === 0) {
            return null;
        }

        const minimum = this.items[0];
        const last = this.items.pop();

        if (this.items.length > 0) {
            this.items[0] = last;

            let index = 0;

            while (true) {
                const left = index * 2 + 1;
                const right = left + 1;
                let smallest = index;

                if (
                    left < this.items.length &&
                    this.less(
                        this.items[left],
                        this.items[smallest]
                    )
                ) {
                    smallest = left;
                }

                if (
                    right < this.items.length &&
                    this.less(
                        this.items[right],
                        this.items[smallest]
                    )
                ) {
                    smallest = right;
                }

                if (smallest === index) {
                    break;
                }

                [this.items[index], this.items[smallest]] =
                    [this.items[smallest], this.items[index]];

                index = smallest;
            }
        }

        return minimum;
    }
}

class WeightedGraph extends EventEmitter {
    constructor({ directed = true } = {}) {
        super();

        this.directed = directed;
        this.adjacency = new Map();
        this.version = 0;
    }

    addVertex(vertex) {
        if (
            typeof vertex !== "string" ||
            vertex.trim().length === 0
        ) {
            throw new GraphError(
                "Vertex must be a nonempty string"
            );
        }

        if (!this.adjacency.has(vertex)) {
            this.adjacency.set(vertex, []);
            this.version++;

            this.emit("vertexAdded", {
                vertex,
                version: this.version
            });
        }
    }

    addEdge(source, destination, weight) {
        if (
            typeof weight !== "number" ||
            !Number.isFinite(weight)
        ) {
            throw new GraphError(
                "Weight must be a finite number"
            );
        }

        if (weight < 0) {
            throw new NegativeWeightError(
                "Negative edge weights are incompatible with Dijkstra"
            );
        }

        this.addVertex(source);
        this.addVertex(destination);

        this.adjacency.get(source).push({
            destination,
            weight
        });

        if (!this.directed) {
            this.adjacency.get(destination).push({
                destination: source,
                weight
            });
        }

        this.version++;

        this.emit("edgeAdded", {
            source,
            destination,
            weight,
            version: this.version
        });
    }

    hasVertex(vertex) {
        return this.adjacency.has(vertex);
    }

    createSnapshot() {
        const snapshot = new Map();

        for (const [vertex, edges] of this.adjacency) {
            snapshot.set(
                vertex,
                edges.map(edge => Object.freeze({ ...edge }))
            );
        }

        return Object.freeze({
            version: this.version,
            adjacency: snapshot
        });
    }

    async shortestPath(
        source,
        destination,
        {
            signal,
            verifyVersion = true
        } = {}
    ) {
        const snapshot = this.createSnapshot();

        if (!snapshot.adjacency.has(source)) {
            throw new UnknownVertexError(
                `Unknown source: ${source}`
            );
        }

        if (!snapshot.adjacency.has(destination)) {
            throw new UnknownVertexError(
                `Unknown destination: ${destination}`
            );
        }

        const result = await this.runDijkstra(
            snapshot,
            source,
            destination,
            signal
        );

        /*
         * The calculation uses an immutable snapshot.
         * The result remains internally consistent even if the live
         * graph changes during asynchronous execution.
         *
         * Strict callers may reject results from an outdated snapshot.
         */
        if (
            verifyVersion &&
            snapshot.version !== this.version
        ) {
            throw new ConcurrentModificationError(
                "Graph changed during route calculation"
            );
        }

        return result;
    }

    async runDijkstra(
        snapshot,
        source,
        destination,
        signal
    ) {
        const adjacency = snapshot.adjacency;

        const distances = new Map();
        const predecessors = new Map();
        const settled = new Set();

        for (const vertex of adjacency.keys()) {
            distances.set(vertex, Infinity);
            predecessors.set(vertex, null);
        }

        distances.set(source, 0);

        const heap = new MinHeap();
        heap.push(0, source);

        let examinedEdges = 0;
        let relaxations = 0;

        while (heap.size > 0) {
            if (signal?.aborted) {
                throw new DOMException(
                    "Route calculation cancelled",
                    "AbortError"
                );
            }

            const current = heap.pop();

            if (settled.has(current.vertex)) {
                continue;
            }

            if (
                current.distance !==
                distances.get(current.vertex)
            ) {
                continue;
            }

            settled.add(current.vertex);

            if (current.vertex === destination) {
                break;
            }

            for (const edge of adjacency.get(current.vertex)) {
                examinedEdges++;

                if (settled.has(edge.destination)) {
                    continue;
                }

                const candidate =
                    current.distance + edge.weight;

                if (candidate < distances.get(edge.destination)) {
                    distances.set(edge.destination, candidate);

                    predecessors.set(
                        edge.destination,
                        current.vertex
                    );

                    heap.push(candidate, edge.destination);
                    relaxations++;
                }
            }

            /*
             * Yield periodically so cancellation and other
             * event-loop operations can execute.
             */
            if (examinedEdges % 1024 === 0) {
                await new Promise(resolve => setImmediate(resolve));
            }
        }

        const distance = distances.get(destination);

        const path = this.reconstructPath(
            source,
            destination,
            predecessors,
            distance
        );

        return Object.freeze({
            source,
            destination,
            distance,
            path,
            reachable: Number.isFinite(distance),
            graphVersion: snapshot.version,
            settledVertices: settled.size,
            examinedEdges,
            relaxations
        });
    }

    reconstructPath(
        source,
        destination,
        predecessors,
        distance
    ) {
        if (!Number.isFinite(distance)) {
            return null;
        }

        const path = [];
        let current = destination;

        while (current !== null) {
            path.push(current);

            if (current === source) {
                break;
            }

            current = predecessors.get(current);
        }

        if (path[path.length - 1] !== source) {
            return null;
        }

        return path.reverse();
    }

    async multiSourceShortestPaths(sources) {
        if (!Array.isArray(sources) || sources.length === 0) {
            throw new GraphError(
                "At least one source is required"
            );
        }

        if (new Set(sources).size !== sources.length) {
            throw new GraphError("Duplicate sources are invalid");
        }

        const snapshot = this.createSnapshot();
        const distances = new Map();
        const predecessors = new Map();
        const heap = new MinHeap();
        const settled = new Set();

        for (const vertex of snapshot.adjacency.keys()) {
            distances.set(vertex, Infinity);
            predecessors.set(vertex, null);
        }

        for (const source of sources) {
            if (!snapshot.adjacency.has(source)) {
                throw new UnknownVertexError(source);
            }

            distances.set(source, 0);
            heap.push(0, source);
        }

        while (heap.size > 0) {
            const current = heap.pop();

            if (settled.has(current.vertex)) {
                continue;
            }

            if (current.distance !== distances.get(current.vertex)) {
                continue;
            }

            settled.add(current.vertex);

            for (const edge of snapshot.adjacency.get(current.vertex)) {
                if (settled.has(edge.destination)) {
                    continue;
                }

                const candidate =
                    current.distance + edge.weight;

                if (candidate < distances.get(edge.destination)) {
                    distances.set(edge.destination, candidate);

                    predecessors.set(
                        edge.destination,
                        current.vertex
                    );

                    heap.push(candidate, edge.destination);
                }
            }
        }

        return {
            distances,
            predecessors,
            graphVersion: snapshot.version
        };
    }
}

function buildNetwork() {
    const graph = new WeightedGraph();

    graph.on("edgeAdded", event => {
        console.log(
            `[EVENT] ${event.source} -> ${event.destination}, ` +
            `weight=${event.weight}`
        );
    });

    const edges = [
        ["Lucknow", "Kanpur", 90],
        ["Lucknow", "Ayodhya", 135],
        ["Kanpur", "Delhi", 210],
        ["Kanpur", "Prayagraj", 180],
        ["Ayodhya", "Varanasi", 190],
        ["Varanasi", "Delhi", 350],
        ["Prayagraj", "Delhi", 500],
        ["Ayodhya", "Gorakhpur", 150],
        ["Gorakhpur", "Patna", 240],
        ["Lucknow", "Express", 0],
        ["Express", "Kanpur", 70]
    ];

    for (const [source, destination, weight] of edges) {
        graph.addEdge(source, destination, weight);
    }

    graph.addVertex("Mumbai");

    return graph;
}

async function runTests() {
    const graph = new WeightedGraph();

    graph.addEdge("A", "B", 4);
    graph.addEdge("A", "C", 1);
    graph.addEdge("C", "B", 2);
    graph.addEdge("B", "D", 1);
    graph.addVertex("Z");

    const result = await graph.shortestPath("A", "D");

    assert.equal(result.distance, 4);
    assert.deepEqual(result.path, ["A", "C", "B", "D"]);

    const unreachable = await graph.shortestPath("A", "Z");

    assert.equal(unreachable.reachable, false);
    assert.equal(unreachable.path, null);

    assert.throws(
        () => graph.addEdge("A", "B", -5),
        NegativeWeightError
    );

    assert.throws(
        () => graph.addEdge("A", "B", Infinity),
        GraphError
    );

    const multi = await graph.multiSourceShortestPaths(["A", "D"]);

    assert.equal(multi.distances.get("B"), 2);

    const undirected = new WeightedGraph({ directed: false });
    undirected.addEdge("X", "Y", 8);

    const reverse = await undirected.shortestPath("Y", "X");

    assert.equal(reverse.distance, 8);

    console.log("[TEST] All tests passed");
}

async function main() {
    console.log("\nDIJKSTRA SHORTEST PATH ENGINE\n");

    const graph = buildNetwork();

    const result = await graph.shortestPath(
        "Lucknow",
        "Delhi"
    );

    console.log("\nShortest route result");

    console.log(JSON.stringify(result, null, 2));

    const multi = await graph.multiSourceShortestPaths([
        "Lucknow",
        "Patna"
    ]);

    console.log("\nMulti-source distances");

    for (const [vertex, distance] of multi.distances) {
        console.log(
            `${vertex.padEnd(15)} ${distance}`
        );
    }

    console.log("\nRunning correctness tests");

    await runTests();

    console.log("\nComplexity");
    console.log("Adjacency-list storage: O(V + E)");
    console.log("Binary heap Dijkstra: O((V + E) log V)");
    console.log("Path reconstruction: O(V)");
    console.log("Auxiliary space: O(V)");
    console.log("Graph snapshot creation: O(V + E)");
}

main().catch(error => {
    console.error("Execution failed:", error.message);
    process.exitCode = 1;
});
