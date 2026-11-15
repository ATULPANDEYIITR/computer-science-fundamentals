"use strict";

/*
 * GRAPH ALGORITHMS I
 * BFS applications, DFS applications and connected components.
 *
 * Runtime: Node.js 18+
 * Dependencies: Node.js standard library only.
 */

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");
const assert = require("node:assert/strict");

class GraphError extends Error {}

class VertexNotFoundError extends GraphError {}

class Graph {
    constructor({ directed = false } = {}) {
        this.directed = directed;
        this.adjacency = new Map();
        this.edgeCount = 0;
    }

    addVertex(vertex) {
        if (
            typeof vertex !== "string" ||
            vertex.trim().length === 0
        ) {
            throw new TypeError("Vertex must be a non-empty string.");
        }

        if (!this.adjacency.has(vertex)) {
            this.adjacency.set(vertex, new Set());
        }

        return this;
    }

    addEdge(source, target) {
        this.addVertex(source);
        this.addVertex(target);

        if (this.adjacency.get(source).has(target)) {
            return this;
        }

        this.adjacency.get(source).add(target);

        if (!this.directed) {
            this.adjacency.get(target).add(source);
        }

        this.edgeCount++;
        return this;
    }

    hasVertex(vertex) {
        return this.adjacency.has(vertex);
    }

    validateVertex(vertex) {
        if (!this.hasVertex(vertex)) {
            throw new VertexNotFoundError(
                `Unknown vertex: ${vertex}`
            );
        }
    }

    vertices() {
        return [...this.adjacency.keys()].sort();
    }

    neighbors(vertex) {
        this.validateVertex(vertex);
        return [...this.adjacency.get(vertex)].sort();
    }

    // ---------------------------------------------------------
    // BFS: shortest unweighted paths
    // ---------------------------------------------------------

    bfs(source) {
        this.validateVertex(source);

        const queue = [source];
        let head = 0;

        const distances = new Map([[source, 0]]);
        const parents = new Map([[source, null]]);

        while (head < queue.length) {
            const current = queue[head++];

            for (const neighbor of this.adjacency.get(current)) {
                if (!distances.has(neighbor)) {
                    distances.set(
                        neighbor,
                        distances.get(current) + 1
                    );

                    parents.set(neighbor, current);
                    queue.push(neighbor);
                }
            }
        }

        return {
            distances,
            parents,
            pathTo(target) {
                if (!distances.has(target)) return null;

                const path = [];
                let current = target;

                while (current !== null) {
                    path.push(current);
                    current = parents.get(current);
                }

                return path.reverse();
            }
        };
    }

    multiSourceBfs(sources) {
        const uniqueSources = [...new Set(sources)];

        if (uniqueSources.length === 0) {
            return new Map();
        }

        const queue = [];
        const distances = new Map();

        for (const source of uniqueSources) {
            this.validateVertex(source);
            distances.set(source, 0);
            queue.push(source);
        }

        let head = 0;

        while (head < queue.length) {
            const current = queue[head++];

            for (const neighbor of this.adjacency.get(current)) {
                if (!distances.has(neighbor)) {
                    distances.set(
                        neighbor,
                        distances.get(current) + 1
                    );
                    queue.push(neighbor);
                }
            }
        }

        return distances;
    }

    shortestPath(source, target) {
        this.validateVertex(source);
        this.validateVertex(target);
        return this.bfs(source).pathTo(target);
    }

    // ---------------------------------------------------------
    // DFS: iterative traversal and cycle detection
    // ---------------------------------------------------------

    dfs(start = null) {
        if (start !== null) this.validateVertex(start);

        const roots = start === null
            ? this.vertices()
            : [start];

        const visited = new Set();
        const active = new Set();
        const discovery = [];
        const finish = [];
        let hasCycle = false;

        // Iterative DFS avoids call-stack overflow on deep graphs.
        for (const root of roots) {
            if (visited.has(root)) continue;

            const stack = [{
                vertex: root,
                neighbors: this.neighbors(root),
                index: 0,
                parent: null
            }];

            visited.add(root);
            active.add(root);
            discovery.push(root);

            while (stack.length > 0) {
                const frame = stack[stack.length - 1];

                if (frame.index < frame.neighbors.length) {
                    const neighbor = frame.neighbors[frame.index++];

                    if (!visited.has(neighbor)) {
                        visited.add(neighbor);
                        active.add(neighbor);
                        discovery.push(neighbor);

                        stack.push({
                            vertex: neighbor,
                            neighbors: this.neighbors(neighbor),
                            index: 0,
                            parent: frame.vertex
                        });
                    } else if (this.directed) {
                        if (active.has(neighbor)) {
                            hasCycle = true;
                        }
                    } else if (neighbor !== frame.parent) {
                        hasCycle = true;
                    }
                } else {
                    stack.pop();
                    active.delete(frame.vertex);
                    finish.push(frame.vertex);
                }
            }
        }

        return {
            discovery,
            finish,
            hasCycle,
            topologicalOrder:
                this.directed && !hasCycle
                    ? [...finish].reverse()
                    : null
        };
    }

    // ---------------------------------------------------------
    // Connected components: undirected graphs
    // ---------------------------------------------------------

    connectedComponents() {
        if (this.directed) {
            throw new GraphError(
                "Connected components require an undirected graph."
            );
        }

        const visited = new Set();
        const components = [];

        for (const root of this.vertices()) {
            if (visited.has(root)) continue;

            const component = [];
            const queue = [root];
            let head = 0;

            visited.add(root);

            while (head < queue.length) {
                const current = queue[head++];
                component.push(current);

                for (const neighbor of this.adjacency.get(current)) {
                    if (!visited.has(neighbor)) {
                        visited.add(neighbor);
                        queue.push(neighbor);
                    }
                }
            }

            components.push(component.sort());
        }

        return components;
    }

    componentStatistics() {
        const components = this.connectedComponents();

        return {
            count: components.length,
            largestSize: Math.max(
                0,
                ...components.map(c => c.length)
            ),
            components,
            isolated: this.vertices().filter(
                v => this.adjacency.get(v).size === 0
            )
        };
    }

    toJSON() {
        return {
            directed: this.directed,
            vertices: this.vertices(),
            edges: this.vertices().flatMap(source =>
                this.neighbors(source)
                    .filter(target =>
                        this.directed || source < target
                    )
                    .map(target => [source, target])
            )
        };
    }

    static fromJSON(data) {
        if (
            !data ||
            typeof data.directed !== "boolean" ||
            !Array.isArray(data.vertices) ||
            !Array.isArray(data.edges)
        ) {
            throw new TypeError("Invalid graph document.");
        }

        const graph = new Graph({ directed: data.directed });

        for (const vertex of data.vertices) {
            graph.addVertex(vertex);
        }

        for (const edge of data.edges) {
            if (!Array.isArray(edge) || edge.length !== 2) {
                throw new TypeError("Invalid edge.");
            }
            graph.addEdge(edge[0], edge[1]);
        }

        return graph;
    }
}

// -------------------------------------------------------------
// Event-driven graph processing
// -------------------------------------------------------------

class GraphMonitor extends EventEmitter {
    constructor(graph) {
        super();
        this.graph = graph;
    }

    async analyze(source) {
        this.emit("analysisStarted", { source });

        try {
            const result = await Promise.resolve(
                this.graph.bfs(source)
            );

            this.emit("vertexDiscovered", {
                source,
                count: result.distances.size
            });

            const statistics = this.graph.componentStatistics();

            const report = {
                source,
                reachable: result.distances.size,
                components: statistics.count,
                largestComponent: statistics.largestSize
            };

            this.emit("analysisCompleted", report);
            return report;
        } catch (error) {
            this.emit("analysisFailed", {
                message: error.message
            });
            throw error;
        }
    }
}

// -------------------------------------------------------------
// Application: dependency and infrastructure analysis
// -------------------------------------------------------------

function buildInfrastructureGraph() {
    const graph = new Graph();

    const connections = [
        ["API", "Gateway"],
        ["Gateway", "Auth"],
        ["Gateway", "Orders"],
        ["Orders", "Database"],
        ["Orders", "Cache"],
        ["Monitoring", "Logging"],
        ["Backup", "Storage"]
    ];

    for (const [source, target] of connections) {
        graph.addEdge(source, target);
    }

    graph.addVertex("OfflineNode");
    return graph;
}

function buildDependencyGraph() {
    const graph = new Graph({ directed: true });

    for (const [source, target] of [
        ["Core", "Authentication"],
        ["Authentication", "API"],
        ["API", "Frontend"],
        ["Core", "Reporting"]
    ]) {
        graph.addEdge(source, target);
    }

    return graph;
}

// -------------------------------------------------------------
// Validation and tests
// -------------------------------------------------------------

async function runTests() {
    const graph = buildInfrastructureGraph();

    assert.deepEqual(
        graph.shortestPath("API", "Database"),
        ["API", "Gateway", "Orders", "Database"]
    );

    assert.equal(
        graph.shortestPath("API", "OfflineNode"),
        null
    );

    assert.equal(graph.connectedComponents().length, 4);

    assert.equal(
        graph.multiSourceBfs(["API", "Monitoring"]).get("Logging"),
        1
    );

    const directed = buildDependencyGraph();
    const result = directed.dfs();

    assert.equal(result.hasCycle, false);
    assert.ok(result.topologicalOrder);

    const positions = new Map(
        result.topologicalOrder.map((v, i) => [v, i])
    );

    assert.ok(
        positions.get("Core") < positions.get("API")
    );

    directed.addEdge("Frontend", "Core");
    assert.equal(directed.dfs().hasCycle, true);

    assert.throws(
        () => graph.bfs("Unknown"),
        VertexNotFoundError
    );

    assert.throws(
        () => directed.connectedComponents(),
        GraphError
    );

    const serialized = graph.toJSON();
    const restored = Graph.fromJSON(serialized);

    assert.deepEqual(
        restored.connectedComponents(),
        graph.connectedComponents()
    );

    const monitor = new GraphMonitor(graph);

    const events = [];

    monitor.on("analysisStarted", () => events.push("started"));
    monitor.on("analysisCompleted", () => events.push("completed"));

    const report = await monitor.analyze("API");

    assert.deepEqual(events, ["started", "completed"]);
    assert.equal(report.reachable, 5);

    await assert.rejects(
        monitor.analyze("Missing"),
        VertexNotFoundError
    );

    console.log("All JavaScript tests passed.");
}

// -------------------------------------------------------------
// Execution
// -------------------------------------------------------------

async function main() {
    const infrastructure = buildInfrastructureGraph();

    console.log("=== BFS: SHORTEST PATH ===");
    const bfs = infrastructure.bfs("API");

    console.log(
        "API to Database:",
        bfs.pathTo("Database")
    );

    console.log(
        "Reachable distances:",
        Object.fromEntries(bfs.distances)
    );

    console.log("\n=== DFS: DEPENDENCY ORDER ===");

    const dependencies = buildDependencyGraph();
    const dfs = dependencies.dfs();

    console.log("Discovery:", dfs.discovery);
    console.log("Topological order:", dfs.topologicalOrder);

    console.log("\n=== CONNECTED COMPONENTS ===");
    console.log(infrastructure.componentStatistics());

    const monitor = new GraphMonitor(infrastructure);

    monitor.on("analysisCompleted", report => {
        console.log("Event report:", report);
    });

    await monitor.analyze("API");

    console.log("\n=== TESTS ===");
    await runTests();

    // Persistence demonstration uses a controlled temporary path.
    const filename = "graph_algorithms_sample.json";

    try {
        await fs.writeFile(
            filename,
            JSON.stringify(infrastructure.toJSON(), null, 2),
            { encoding: "utf8", mode: 0o600 }
        );

        const loaded = Graph.fromJSON(
            JSON.parse(await fs.readFile(filename, "utf8"))
        );

        assert.deepEqual(
            loaded.connectedComponents(),
            infrastructure.connectedComponents()
        );

        console.log("Graph persistence verified.");
    } finally {
        await fs.rm(filename, { force: true });
    }
}

main().catch(error => {
    console.error("Execution failed:", error.message);
    process.exitCode = 1;
});
