"use strict";

/*
 * Minimum Spanning Tree Engine
 *
 * Engineering perspective:
 * - Event-driven network construction.
 * - Kruskal and Prim algorithm selection.
 * - Union-Find with path compression and union by rank.
 * - Immutable snapshots of calculated results.
 * - Validation and disconnected-network handling.
 */

const assert = require("node:assert/strict");
const { EventEmitter } = require("node:events");

class GraphError extends Error {
    constructor(message) {
        super(message);
        this.name = "GraphError";
    }
}

class DisjointSet {
    constructor(vertices) {
        this.parent = new Map();
        this.rank = new Map();
        this.components = vertices.length;

        for (const vertex of vertices) {
            this.parent.set(vertex, vertex);
            this.rank.set(vertex, 0);
        }
    }

    find(vertex) {
        if (!this.parent.has(vertex)) {
            throw new GraphError(`Unknown vertex: ${vertex}`);
        }

        let root = vertex;

        while (this.parent.get(root) !== root) {
            root = this.parent.get(root);
        }

        // Iterative path compression avoids recursive stack growth.
        let current = vertex;

        while (current !== root) {
            const next = this.parent.get(current);
            this.parent.set(current, root);
            current = next;
        }

        return root;
    }

    union(a, b) {
        let rootA = this.find(a);
        let rootB = this.find(b);

        if (rootA === rootB) {
            return false;
        }

        if (this.rank.get(rootA) < this.rank.get(rootB)) {
            [rootA, rootB] = [rootB, rootA];
        }

        this.parent.set(rootB, rootA);

        if (this.rank.get(rootA) === this.rank.get(rootB)) {
            this.rank.set(rootA, this.rank.get(rootA) + 1);
        }

        this.components--;
        return true;
    }

    connected(a, b) {
        return this.find(a) === this.find(b);
    }
}

class MinHeap {
    constructor(compare) {
        this.items = [];
        this.compare = compare;
    }

    get size() {
        return this.items.length;
    }

    push(value) {
        const items = this.items;
        items.push(value);

        let index = items.length - 1;

        while (index > 0) {
            const parent = Math.floor((index - 1) / 2);

            if (this.compare(items[parent], items[index]) <= 0) {
                break;
            }

            [items[parent], items[index]] =
                [items[index], items[parent]];

            index = parent;
        }
    }

    pop() {
        if (this.items.length === 0) {
            return undefined;
        }

        const result = this.items[0];
        const last = this.items.pop();

        if (this.items.length > 0) {
            this.items[0] = last;
            this.siftDown(0);
        }

        return result;
    }

    siftDown(index) {
        const items = this.items;
        const size = items.length;

        while (true) {
            let smallest = index;
            const left = 2 * index + 1;
            const right = 2 * index + 2;

            if (
                left < size &&
                this.compare(items[left], items[smallest]) < 0
            ) {
                smallest = left;
            }

            if (
                right < size &&
                this.compare(items[right], items[smallest]) < 0
            ) {
                smallest = right;
            }

            if (smallest === index) {
                break;
            }

            [items[index], items[smallest]] =
                [items[smallest], items[index]];

            index = smallest;
        }
    }
}

class NetworkGraph extends EventEmitter {
    constructor(vertices) {
        super();

        if (!Array.isArray(vertices) || vertices.length === 0) {
            throw new GraphError("At least one vertex is required.");
        }

        this.vertices = new Set();

        for (const vertex of vertices) {
            if (typeof vertex !== "string" || vertex.trim() === "") {
                throw new GraphError("Invalid vertex identifier.");
            }

            if (this.vertices.has(vertex)) {
                throw new GraphError(`Duplicate vertex: ${vertex}`);
            }

            this.vertices.add(vertex);
        }

        this.edges = [];
        this.adjacency = new Map(
            [...this.vertices].map(v => [v, []])
        );

        this.edgeKeys = new Set();
        this.revision = 0;
    }

    addEdge(source, target, weight) {
        if (!this.vertices.has(source) || !this.vertices.has(target)) {
            throw new GraphError("Edge endpoint does not exist.");
        }

        if (source === target) {
            throw new GraphError("Self-loops are not supported.");
        }

        if (typeof weight !== "number" || !Number.isFinite(weight)) {
            throw new GraphError("Weight must be a finite number.");
        }

        const [a, b] = [source, target].sort();
        const key = JSON.stringify([a, b]);

        if (this.edgeKeys.has(key)) {
            throw new GraphError("Duplicate undirected edge.");
        }

        const edge = Object.freeze({ source, target, weight });

        this.edgeKeys.add(key);
        this.edges.push(edge);

        this.adjacency.get(source).push({
            vertex: target,
            weight
        });

        this.adjacency.get(target).push({
            vertex: source,
            weight
        });

        this.revision++;

        this.emit("edgeAdded", {
            edge,
            revision: this.revision
        });

        return this;
    }

    compareEdges(a, b) {
        return (
            a.weight - b.weight ||
            a.source.localeCompare(b.source) ||
            a.target.localeCompare(b.target)
        );
    }

    kruskal() {
        const dsu = new DisjointSet([...this.vertices]);
        const sorted = [...this.edges].sort(
            (a, b) => this.compareEdges(a, b)
        );

        const selected = [];
        let totalWeight = 0;

        for (const edge of sorted) {
            if (dsu.union(edge.source, edge.target)) {
                selected.push(edge);
                totalWeight += edge.weight;

                if (selected.length === this.vertices.size - 1) {
                    break;
                }
            }
        }

        return this.createResult("Kruskal", selected, totalWeight,
            dsu.components);
    }

    prim(start) {
        if (start === undefined) {
            start = [...this.vertices].sort()[0];
        }

        if (!this.vertices.has(start)) {
            throw new GraphError("Starting vertex does not exist.");
        }

        const visited = new Set();
        const selected = [];
        let totalWeight = 0;

        const compare = (a, b) =>
            a.weight - b.weight ||
            a.source.localeCompare(b.source) ||
            a.target.localeCompare(b.target);

        const heap = new MinHeap(compare);

        const roots = [start, ...[...this.vertices]
            .filter(v => v !== start).sort()];

        for (const root of roots) {
            if (visited.has(root)) {
                continue;
            }

            visited.add(root);

            for (const edge of this.adjacency.get(root)) {
                heap.push({
                    source: root,
                    target: edge.vertex,
                    weight: edge.weight
                });
            }

            while (heap.size > 0) {
                const edge = heap.pop();

                if (visited.has(edge.target)) {
                    continue;
                }

                visited.add(edge.target);
                selected.push(Object.freeze(edge));
                totalWeight += edge.weight;

                for (const next of this.adjacency.get(edge.target)) {
                    if (!visited.has(next.vertex)) {
                        heap.push({
                            source: edge.target,
                            target: next.vertex,
                            weight: next.weight
                        });
                    }
                }
            }
        }

        return this.createResult(
            "Prim",
            selected,
            totalWeight,
            this.vertices.size - selected.length
        );
    }

    createResult(algorithm, edges, totalWeight, components) {
        const result = Object.freeze({
            algorithm,
            edges: Object.freeze([...edges]),
            totalWeight,
            components,
            vertexCount: this.vertices.size,
            edgeCount: edges.length,
            isSpanningTree:
                this.vertices.size > 0 &&
                components === 1 &&
                edges.length === this.vertices.size - 1,
            isSpanningForest:
                edges.length === this.vertices.size - components,
            graphRevision: this.revision
        });

        this.emit("mstCalculated", result);
        return result;
    }

    async calculate(algorithm, options = {}) {
        // Promise-based interface for application integration.
        await Promise.resolve();

        if (algorithm === "kruskal") {
            return this.kruskal();
        }

        if (algorithm === "prim") {
            return this.prim(options.start);
        }

        throw new GraphError(`Unsupported algorithm: ${algorithm}`);
    }
}

function displayResult(result) {
    console.log(`\n${result.algorithm}`);
    console.log("-".repeat(40));

    for (const edge of result.edges) {
        console.log(
            `${edge.source} -- ${edge.target}: ${edge.weight}`
        );
    }

    console.log("Total weight:", result.totalWeight);
    console.log("Components:", result.components);
    console.log("Spanning tree:", result.isSpanningTree);
    console.log("Spanning forest:", result.isSpanningForest);
}

function verifyResult(graph, result) {
    const dsu = new DisjointSet([...graph.vertices]);

    for (const edge of result.edges) {
        if (!dsu.union(edge.source, edge.target)) {
            return false;
        }
    }

    const original = new DisjointSet([...graph.vertices]);

    for (const edge of graph.edges) {
        original.union(edge.source, edge.target);
    }

    const weight = result.edges.reduce(
        (sum, edge) => sum + edge.weight,
        0
    );

    return (
        dsu.components === original.components &&
        dsu.components === result.components &&
        result.edges.length === graph.vertices.size - dsu.components &&
        Math.abs(weight - result.totalWeight) < 1e-9
    );
}

async function runTests() {
    const graph = new NetworkGraph(["A", "B", "C", "D", "E", "F"]);

    let addedEvents = 0;
    let calculatedEvents = 0;

    graph.on("edgeAdded", () => addedEvents++);
    graph.on("mstCalculated", () => calculatedEvents++);

    const connections = [
        ["A", "B", 4],
        ["A", "C", 3],
        ["B", "C", 1],
        ["B", "D", 2],
        ["C", "D", 4],
        ["C", "E", 5],
        ["D", "E", 2],
        ["D", "F", 6],
        ["E", "F", 3]
    ];

    for (const connection of connections) {
        graph.addEdge(...connection);
    }

    const kruskal = graph.kruskal();
    const prim = graph.prim("A");

    assert.equal(kruskal.isSpanningTree, true);
    assert.equal(prim.isSpanningTree, true);
    assert.equal(kruskal.totalWeight, prim.totalWeight);
    assert.equal(verifyResult(graph, kruskal), true);
    assert.equal(verifyResult(graph, prim), true);
    assert.equal(addedEvents, connections.length);

    // Event-driven asynchronous execution.
    const asyncResult = await graph.calculate("kruskal");
    assert.equal(asyncResult.totalWeight, kruskal.totalWeight);

    // Negative weights.
    const negative = new NetworkGraph(["A", "B", "C"]);
    negative.addEdge("A", "B", -5);
    negative.addEdge("B", "C", 2);
    negative.addEdge("A", "C", 4);

    assert.equal(negative.kruskal().totalWeight, -3);

    // Disconnected network.
    const disconnected = new NetworkGraph(["A", "B", "C", "D"]);
    disconnected.addEdge("A", "B", 2);
    disconnected.addEdge("C", "D", 1);

    const forest = disconnected.kruskal();

    assert.equal(forest.components, 2);
    assert.equal(forest.isSpanningTree, false);
    assert.equal(forest.isSpanningForest, true);

    // Single vertex.
    const singleton = new NetworkGraph(["A"]);
    assert.equal(singleton.prim().totalWeight, 0);
    assert.equal(singleton.prim().isSpanningTree, true);

    // Validation.
    assert.throws(
        () => graph.addEdge("A", "B", 1),
        GraphError
    );

    assert.throws(
        () => graph.addEdge("A", "UNKNOWN", 1),
        GraphError
    );

    assert.throws(
        () => graph.addEdge("A", "A", 1),
        GraphError
    );

    assert.throws(
        () => graph.addEdge("A", "F", Infinity),
        GraphError
    );

    await assert.rejects(
        graph.calculate("unknown"),
        GraphError
    );

    assert.equal(calculatedEvents >= 4, true);

    displayResult(kruskal);
    displayResult(prim);

    console.log("\nAll JavaScript tests passed.");
}

async function main() {
    const graph = new NetworkGraph([
        "Warehouse",
        "Factory",
        "Office",
        "Distribution",
        "DataCenter"
    ]);

    graph.on("edgeAdded", event => {
        console.log(
            `Connection registered: ${event.edge.source} -> ` +
            `${event.edge.target}`
        );
    });

    const connections = [
        ["Warehouse", "Factory", 12],
        ["Warehouse", "Office", 8],
        ["Factory", "Office", 5],
        ["Factory", "Distribution", 7],
        ["Office", "Distribution", 9],
        ["Office", "DataCenter", 11],
        ["Distribution", "DataCenter", 4]
    ];

    for (const edge of connections) {
        graph.addEdge(...edge);
    }

    const result = await graph.calculate("kruskal");
    displayResult(result);

    await runTests();
}

main().catch(error => {
    console.error("Execution failed:", error.message);
    process.exitCode = 1;
});
