'use strict';

const fs = require('node:fs');

class GraphError extends Error {}

class DirectedWeightedGraph {
    constructor() {
        this.adjacency = new Map();
    }

    addVertex(vertex) {
        if (typeof vertex !== 'string' || vertex.trim() === '') {
            throw new GraphError('Vertex name must be a non-empty string.');
        }
        if (!this.adjacency.has(vertex)) {
            this.adjacency.set(vertex, new Map());
        }
    }

    addEdge(source, target, weight) {
        if (!Number.isFinite(weight) || weight < 0) {
            throw new GraphError('Edge weight must be a finite non-negative number.');
        }

        this.addVertex(source);
        this.addVertex(target);
        this.adjacency.get(source).set(target, weight);
    }

    vertices() {
        return [...this.adjacency.keys()].sort();
    }

    edges() {
        const result = [];

        for (const [source, targets] of this.adjacency) {
            for (const [target, weight] of targets) {
                result.push({ source, target, weight });
            }
        }

        return result.sort((a, b) =>
            a.source.localeCompare(b.source) ||
            a.target.localeCompare(b.target)
        );
    }

    bfs(start) {
        this.requireVertex(start);

        const queue = [start];
        const visited = new Set([start]);
        const order = [];

        for (let index = 0; index < queue.length; index++) {
            const current = queue[index];
            order.push(current);

            const neighbors = [...this.adjacency.get(current).keys()].sort();

            for (const neighbor of neighbors) {
                if (!visited.has(neighbor)) {
                    visited.add(neighbor);
                    queue.push(neighbor);
                }
            }
        }

        return order;
    }

    dfs(start) {
        this.requireVertex(start);

        const visited = new Set();
        const order = [];

        const visit = (vertex) => {
            visited.add(vertex);
            order.push(vertex);

            const neighbors = [...this.adjacency.get(vertex).keys()].sort();

            for (const neighbor of neighbors) {
                if (!visited.has(neighbor)) {
                    visit(neighbor);
                }
            }
        };

        visit(start);
        return order;
    }

    dijkstra(start) {
        this.requireVertex(start);

        const distance = new Map();
        const previous = new Map();

        for (const vertex of this.vertices()) {
            distance.set(vertex, Infinity);
            previous.set(vertex, null);
        }

        distance.set(start, 0);

        // A small binary heap avoids repeatedly sorting all vertices.
        const heap = new MinHeap();
        heap.push({ vertex: start, distance: 0 });

        while (!heap.isEmpty()) {
            const current = heap.pop();

            if (current.distance !== distance.get(current.vertex)) {
                continue;
            }

            for (const [neighbor, weight] of this.adjacency.get(current.vertex)) {
                const candidate = current.distance + weight;

                if (candidate < distance.get(neighbor)) {
                    distance.set(neighbor, candidate);
                    previous.set(neighbor, current.vertex);
                    heap.push({ vertex: neighbor, distance: candidate });
                }
            }
        }

        return { distance, previous };
    }

    shortestPath(start, target) {
        const { distance, previous } = this.dijkstra(start);
        this.requireVertex(target);

        if (distance.get(target) === Infinity) {
            return { path: [], distance: Infinity };
        }

        const path = [];
        let current = target;

        while (current !== null) {
            path.push(current);
            current = previous.get(current);
        }

        path.reverse();

        return {
            path,
            distance: distance.get(target)
        };
    }

    topologicalSort() {
        const indegree = new Map();

        for (const vertex of this.adjacency.keys()) {
            indegree.set(vertex, 0);
        }

        for (const targets of this.adjacency.values()) {
            for (const target of targets.keys()) {
                indegree.set(target, indegree.get(target) + 1);
            }
        }

        const ready = [...indegree.entries()]
            .filter(([, degree]) => degree === 0)
            .map(([vertex]) => vertex)
            .sort();

        const order = [];

        while (ready.length > 0) {
            const current = ready.shift();
            order.push(current);

            for (const neighbor of this.adjacency.get(current).keys()) {
                indegree.set(neighbor, indegree.get(neighbor) - 1);

                if (indegree.get(neighbor) === 0) {
                    ready.push(neighbor);
                    ready.sort();
                }
            }
        }

        if (order.length !== this.adjacency.size) {
            throw new GraphError('Topological sorting failed because the graph has a cycle.');
        }

        return order;
    }

    hasCycle() {
        const visiting = new Set();
        const visited = new Set();

        const visit = (vertex) => {
            if (visiting.has(vertex)) {
                return true;
            }

            if (visited.has(vertex)) {
                return false;
            }

            visiting.add(vertex);

            for (const neighbor of this.adjacency.get(vertex).keys()) {
                if (visit(neighbor)) {
                    return true;
                }
            }

            visiting.delete(vertex);
            visited.add(vertex);
            return false;
        };

        for (const vertex of this.adjacency.keys()) {
            if (!visited.has(vertex) && visit(vertex)) {
                return true;
            }
        }

        return false;
    }

    requireVertex(vertex) {
        if (!this.adjacency.has(vertex)) {
            throw new GraphError(`Unknown vertex: ${vertex}`);
        }
    }
}

class MinHeap {
    constructor() {
        this.items = [];
    }

    push(item) {
        this.items.push(item);
        this.#bubbleUp(this.items.length - 1);
    }

    pop() {
        if (this.items.length === 0) {
            return undefined;
        }

        const root = this.items[0];
        const last = this.items.pop();

        if (this.items.length > 0) {
            this.items[0] = last;
            this.#bubbleDown(0);
        }

        return root;
    }

    isEmpty() {
        return this.items.length === 0;
    }

    #bubbleUp(index) {
        while (index > 0) {
            const parent = Math.floor((index - 1) / 2);

            if (this.items[parent].distance <= this.items[index].distance) {
                break;
            }

            [this.items[parent], this.items[index]] =
                [this.items[index], this.items[parent]];

            index = parent;
        }
    }

    #bubbleDown(index) {
        while (true) {
            const left = index * 2 + 1;
            const right = index * 2 + 2;
            let smallest = index;

            if (
                left < this.items.length &&
                this.items[left].distance < this.items[smallest].distance
            ) {
                smallest = left;
            }

            if (
                right < this.items.length &&
                this.items[right].distance < this.items[smallest].distance
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
}

function buildNetwork() {
    const graph = new DirectedWeightedGraph();

    const routes = [
        ['Lucknow', 'Kanpur', 1.5],
        ['Lucknow', 'Ayodhya', 2.0],
        ['Kanpur', 'Agra', 3.0],
        ['Ayodhya', 'Varanasi', 2.5],
        ['Agra', 'Delhi', 2.0],
        ['Varanasi', 'Patna', 4.0],
        ['Delhi', 'Jaipur', 3.0],
        ['Delhi', 'Patna', 5.0],
        ['Jaipur', 'Ahmedabad', 4.0],
        ['Patna', 'Kolkata', 5.0],
        ['Ahmedabad', 'Mumbai', 6.0],
        ['Kolkata', 'Guwahati', 7.0],
        ['Mumbai', 'Bengaluru', 7.0]
    ];

    for (const [source, target, weight] of routes) {
        graph.addEdge(source, target, weight);
    }

    return graph;
}

async function writeEdgeList(graph, filename) {
    const lines = ['source,target,weight'];

    for (const edge of graph.edges()) {
        lines.push(`${edge.source},${edge.target},${edge.weight}`);
    }

    await fs.promises.writeFile(filename, lines.join('\n') + '\n', 'utf8');
}

async function main() {
    const graph = buildNetwork();

    console.log('DIRECTED WEIGHTED GRAPH');
    console.log('=======================');

    console.log('\nEdges:');
    for (const edge of graph.edges()) {
        console.log(`  ${edge.source} -> ${edge.target} (${edge.weight} hours)`);
    }

    console.log('\nBFS:', graph.bfs('Lucknow').join(' -> '));
    console.log('DFS:', graph.dfs('Lucknow').join(' -> '));

    const route = graph.shortestPath('Lucknow', 'Mumbai');
    console.log('\nShortest route:', route.path.join(' -> '));
    console.log(`Travel time: ${route.distance} hours`);

    console.log('\nContains cycle:', graph.hasCycle());

    const workflow = new DirectedWeightedGraph();
    workflow.addEdge('Collect Data', 'Validate Data', 1);
    workflow.addEdge('Validate Data', 'Transform Data', 1);
    workflow.addEdge('Transform Data', 'Publish Data', 1);

    console.log(
        'Workflow order:',
        workflow.topologicalSort().join(' -> ')
    );

    workflow.addEdge('Publish Data', 'Collect Data', 1);

    try {
        workflow.topologicalSort();
    } catch (error) {
        console.log('Cycle validation:', error.message);
    }

    try {
        graph.addEdge('Delhi', 'Mumbai', -3);
    } catch (error) {
        console.log('Weight validation:', error.message);
    }

    await writeEdgeList(graph, 'delivery_network_edges.csv');
    console.log('\nExported delivery_network_edges.csv');

    console.log('\nComplexity:');
    console.log('  Adjacency list: O(V + E) storage');
    console.log('  BFS/DFS: O(V + E)');
    console.log('  Dijkstra with binary heap: O((V + E) log V)');
    console.log('  Topological sort: O(V + E)');
}

main().catch((error) => {
    console.error('Fatal error:', error.message);
    process.exitCode = 1;
});
