"use strict";

/*
 * Graph Algorithms III
 *
 * Bellman-Ford, Floyd-Warshall, and negative-cycle analysis.
 *
 * Runtime: Node.js 18+
 *
 * Features:
 * - Event-driven graph updates.
 * - Asynchronous shortest-path execution.
 * - Bellman-Ford single-source analysis.
 * - Floyd-Warshall all-pairs analysis.
 * - Negative-cycle propagation.
 * - Path reconstruction.
 * - Graph snapshots and validation.
 * - Cross-algorithm verification.
 */

const { EventEmitter } = require("node:events");

class GraphError extends Error {}

class NegativeCycleError extends GraphError {}

const PathStatus = Object.freeze({
    FINITE: "finite",
    UNREACHABLE: "unreachable",
    NEGATIVE_INFINITY: "negative_infinity"
});

class WeightedGraph extends EventEmitter {
    constructor(vertexCount) {
        super();

        if (
            !Number.isSafeInteger(vertexCount) ||
            vertexCount <= 0
        ) {
            throw new GraphError(
                "Vertex count must be a positive safe integer."
            );
        }

        this.vertexCount = vertexCount;
        this.edges = [];
        this.adjacency = Array.from(
            { length: vertexCount },
            () => []
        );

        this.version = 0;
    }

    validateVertex(vertex) {
        if (
            !Number.isSafeInteger(vertex) ||
            vertex < 0 ||
            vertex >= this.vertexCount
        ) {
            throw new GraphError(`Invalid vertex: ${vertex}`);
        }
    }

    addEdge(source, destination, weight) {
        this.validateVertex(source);
        this.validateVertex(destination);

        if (
            typeof weight !== "number" ||
            !Number.isFinite(weight)
        ) {
            throw new GraphError("Weight must be a finite number.");
        }

        const edge = Object.freeze({
            source,
            destination,
            weight
        });

        this.edges.push(edge);
        this.adjacency[source].push(edge);
        this.version++;

        this.emit("edgeAdded", edge, this.version);

        return edge;
    }

    snapshot() {
        return Object.freeze({
            vertexCount: this.vertexCount,
            version: this.version,
            edges: Object.freeze([...this.edges])
        });
    }

    getStatus(distance, affected) {
        if (affected) {
            return PathStatus.NEGATIVE_INFINITY;
        }

        return distance === Infinity
            ? PathStatus.UNREACHABLE
            : PathStatus.FINITE;
    }

    bellmanFord(source, snapshot = this.snapshot()) {
        this.validateVertex(source);

        const n = snapshot.vertexCount;
        const distances = Array(n).fill(Infinity);
        const predecessors = Array(n).fill(null);
        const adjacency = Array.from({ length: n }, () => []);

        distances[source] = 0;

        for (const edge of snapshot.edges) {
            adjacency[edge.source].push(edge.destination);
        }

        for (let iteration = 0; iteration < n - 1; iteration++) {
            let changed = false;

            for (const edge of snapshot.edges) {
                if (distances[edge.source] === Infinity) {
                    continue;
                }

                const candidate =
                    distances[edge.source] + edge.weight;

                if (candidate < distances[edge.destination]) {
                    distances[edge.destination] = candidate;
                    predecessors[edge.destination] = edge.source;
                    changed = true;
                }
            }

            if (!changed) {
                break;
            }
        }

        const affected = new Set();
        let witness = null;

        for (const edge of snapshot.edges) {
            if (distances[edge.source] === Infinity) {
                continue;
            }

            const candidate =
                distances[edge.source] + edge.weight;

            if (candidate < distances[edge.destination]) {
                distances[edge.destination] = candidate;
                predecessors[edge.destination] = edge.source;
                affected.add(edge.destination);
                witness = edge.destination;
            }
        }

        // Every vertex reachable from a negative cycle is affected.
        const queue = [...affected];

        for (let index = 0; index < queue.length; index++) {
            const vertex = queue[index];

            for (const destination of adjacency[vertex]) {
                if (!affected.has(destination)) {
                    affected.add(destination);
                    queue.push(destination);
                }
            }
        }

        const negativeCycle = this.reconstructCycle(
            witness,
            predecessors
        );

        return Object.freeze({
            source,
            graphVersion: snapshot.version,
            distances: Object.freeze(distances),
            predecessors: Object.freeze(predecessors),
            affected: Object.freeze([...affected]),
            negativeCycle: Object.freeze(negativeCycle)
        });
    }

    reconstructCycle(vertex, predecessors) {
        if (vertex === null) {
            return [];
        }

        let current = vertex;

        for (let i = 0; i < this.vertexCount; i++) {
            current = predecessors[current];

            if (current === null) {
                return [];
            }
        }

        const cycle = [current];
        let next = predecessors[current];

        while (next !== null && next !== current) {
            if (cycle.length > this.vertexCount) {
                return [];
            }

            cycle.push(next);
            next = predecessors[next];
        }

        if (next === null) {
            return [];
        }

        cycle.push(current);
        return cycle.reverse();
    }

    reconstructPath(result, destination) {
        this.validateVertex(destination);

        const affected = new Set(result.affected);

        const status = this.getStatus(
            result.distances[destination],
            affected.has(destination)
        );

        if (status === PathStatus.NEGATIVE_INFINITY) {
            throw new NegativeCycleError(
                "No finite shortest path exists."
            );
        }

        if (status === PathStatus.UNREACHABLE) {
            return [];
        }

        const path = [];
        let current = destination;

        for (let i = 0; i <= this.vertexCount; i++) {
            path.push(current);

            if (current === result.source) {
                return path.reverse();
            }

            current = result.predecessors[current];

            if (current === null) {
                break;
            }
        }

        throw new GraphError("Invalid predecessor chain.");
    }

    floydWarshall(snapshot = this.snapshot()) {
        const n = snapshot.vertexCount;

        const distances = Array.from(
            { length: n },
            () => Array(n).fill(Infinity)
        );

        const next = Array.from(
            { length: n },
            () => Array(n).fill(null)
        );

        for (let i = 0; i < n; i++) {
            distances[i][i] = 0;
            next[i][i] = i;
        }

        for (const edge of snapshot.edges) {
            if (
                edge.weight <
                distances[edge.source][edge.destination]
            ) {
                distances[edge.source][edge.destination] = edge.weight;
                next[edge.source][edge.destination] =
                    edge.destination;
            }
        }

        for (let k = 0; k < n; k++) {
            for (let i = 0; i < n; i++) {
                if (distances[i][k] === Infinity) {
                    continue;
                }

                for (let j = 0; j < n; j++) {
                    if (distances[k][j] === Infinity) {
                        continue;
                    }

                    const candidate =
                        distances[i][k] + distances[k][j];

                    if (candidate < distances[i][j]) {
                        distances[i][j] = candidate;
                        next[i][j] = next[i][k];
                    }
                }
            }
        }

        const negativeCycles = [];

        for (let i = 0; i < n; i++) {
            if (distances[i][i] < 0) {
                negativeCycles.push(i);
            }
        }

        return Object.freeze({
            graphVersion: snapshot.version,
            distances: Object.freeze(
                distances.map(row => Object.freeze(row))
            ),
            next: Object.freeze(
                next.map(row => Object.freeze(row))
            ),
            negativeCycles: Object.freeze(negativeCycles)
        });
    }

    floydStatus(result, source, destination) {
        this.validateVertex(source);
        this.validateVertex(destination);

        for (const cycle of result.negativeCycles) {
            if (
                result.distances[source][cycle] !== Infinity &&
                result.distances[cycle][destination] !== Infinity
            ) {
                return PathStatus.NEGATIVE_INFINITY;
            }
        }

        return result.distances[source][destination] === Infinity
            ? PathStatus.UNREACHABLE
            : PathStatus.FINITE;
    }

    reconstructFloydPath(result, source, destination) {
        const status = this.floydStatus(
            result,
            source,
            destination
        );

        if (status === PathStatus.NEGATIVE_INFINITY) {
            throw new NegativeCycleError(
                "Path is undefined due to a reachable negative cycle."
            );
        }

        if (status === PathStatus.UNREACHABLE) {
            return [];
        }

        if (source === destination) {
            return [source];
        }

        const path = [source];
        let current = source;

        for (let i = 0; i < this.vertexCount; i++) {
            current = result.next[current][destination];

            if (current === null) {
                return [];
            }

            path.push(current);

            if (current === destination) {
                return path;
            }
        }

        throw new GraphError("Path reconstruction exceeded limit.");
    }

    async analyzeFrom(source) {
        // Yield to the event loop before running CPU-intensive analysis.
        await new Promise(resolve => setImmediate(resolve));

        const snapshot = this.snapshot();

        return this.bellmanFord(source, snapshot);
    }

    async analyzeAllPairs() {
        await new Promise(resolve => setImmediate(resolve));

        const snapshot = this.snapshot();

        return this.floydWarshall(snapshot);
    }
}

async function main() {
    console.log("GRAPH ALGORITHMS III");

    const graph = new WeightedGraph(6);

    graph.on("edgeAdded", (edge, version) => {
        console.log(
            `Graph update ${version}: ${edge.source} -> ` +
            `${edge.destination}, weight=${edge.weight}`
        );
    });

    const edges = [
        [0, 1, 4],
        [0, 2, 5],
        [1, 2, -2],
        [1, 3, 6],
        [2, 3, 3],
        [3, 4, 2],
        [4, 5, 1]
    ];

    for (const edge of edges) {
        graph.addEdge(...edge);
    }

    const [singleSource, allPairs] = await Promise.all([
        graph.analyzeFrom(0),
        graph.analyzeAllPairs()
    ]);

    console.log("\nBellman-Ford distances:");
    console.log(singleSource.distances);

    console.log(
        "Bellman-Ford path 0 -> 5:",
        graph.reconstructPath(singleSource, 5)
    );

    console.log("\nFloyd-Warshall matrix:");

    for (const row of allPairs.distances) {
        console.log(row.map(value =>
            value === Infinity ? "INF" : value
        ));
    }

    console.log(
        "Floyd-Warshall path 0 -> 5:",
        graph.reconstructFloydPath(allPairs, 0, 5)
    );

    if (singleSource.distances[5] !== allPairs.distances[0][5]) {
        throw new GraphError("Algorithm verification failed.");
    }

    const negative = new WeightedGraph(5);

    [
        [0, 1, 2],
        [1, 2, 2],
        [2, 3, -5],
        [3, 1, 1],
        [3, 4, 4]
    ].forEach(edge => negative.addEdge(...edge));

    const negativeResult = negative.bellmanFord(0);

    console.log("\nNegative cycle witness:");
    console.log(negativeResult.negativeCycle);

    console.log(
        "Affected vertices:",
        negativeResult.affected.sort((a, b) => a - b)
    );

    if (!negativeResult.affected.includes(4)) {
        throw new GraphError("Negative-cycle propagation failed.");
    }

    try {
        negative.reconstructPath(negativeResult, 4);
    } catch (error) {
        if (!(error instanceof NegativeCycleError)) {
            throw error;
        }

        console.log("Correctly rejected undefined shortest path.");
    }

    console.log("\nAll verification checks passed.");
}

main().catch(error => {
    console.error("Execution failed:", error.message);
    process.exitCode = 1;
});
