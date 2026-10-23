"use strict";

/*
 * Introduction to Data Structures
 *
 * This Node.js program uses different structures for different access patterns.
 * The examples form a small task-processing and dependency-analysis system.
 */

class Stack {
    constructor(values = []) {
        this.items = [...values];
    }

    push(value) {
        this.items.push(value);
    }

    pop() {
        if (this.items.length === 0) {
            throw new Error("Cannot pop from an empty stack");
        }
        return this.items.pop();
    }

    peek() {
        if (this.items.length === 0) {
            throw new Error("Cannot inspect an empty stack");
        }
        return this.items[this.items.length - 1];
    }

    get size() {
        return this.items.length;
    }
}


class Queue {
    constructor(values = []) {
        this.items = [...values];
        this.head = 0;
    }

    enqueue(value) {
        this.items.push(value);
    }

    dequeue() {
        if (this.head >= this.items.length) {
            throw new Error("Cannot dequeue from an empty queue");
        }

        const value = this.items[this.head++];

        // Periodically release consumed array slots.
        if (this.head > 1024 && this.head * 2 > this.items.length) {
            this.items = this.items.slice(this.head);
            this.head = 0;
        }

        return value;
    }

    peek() {
        if (this.head >= this.items.length) {
            throw new Error("Cannot inspect an empty queue");
        }
        return this.items[this.head];
    }

    get size() {
        return this.items.length - this.head;
    }
}


class MinHeap {
    constructor() {
        this.heap = [];
    }

    push(item) {
        if (!item || typeof item.priority !== "number") {
            throw new TypeError("Heap entries require a numeric priority");
        }

        this.heap.push(item);
        this.#bubbleUp(this.heap.length - 1);
    }

    pop() {
        if (this.heap.length === 0) {
            return undefined;
        }

        const root = this.heap[0];
        const last = this.heap.pop();

        if (this.heap.length > 0) {
            this.heap[0] = last;
            this.#bubbleDown(0);
        }

        return root;
    }

    #bubbleUp(index) {
        while (index > 0) {
            const parent = Math.floor((index - 1) / 2);

            if (this.heap[parent].priority <= this.heap[index].priority) {
                break;
            }

            [this.heap[parent], this.heap[index]] =
                [this.heap[index], this.heap[parent]];

            index = parent;
        }
    }

    #bubbleDown(index) {
        while (true) {
            const left = index * 2 + 1;
            const right = index * 2 + 2;
            let smallest = index;

            if (
                left < this.heap.length &&
                this.heap[left].priority < this.heap[smallest].priority
            ) {
                smallest = left;
            }

            if (
                right < this.heap.length &&
                this.heap[right].priority < this.heap[smallest].priority
            ) {
                smallest = right;
            }

            if (smallest === index) {
                return;
            }

            [this.heap[index], this.heap[smallest]] =
                [this.heap[smallest], this.heap[index]];

            index = smallest;
        }
    }

    get size() {
        return this.heap.length;
    }
}


class BinarySearchTree {
    constructor() {
        this.root = null;
    }

    insert(value) {
        if (!Number.isInteger(value)) {
            throw new TypeError("BST values must be integers");
        }

        if (this.root === null) {
            this.root = { value, left: null, right: null };
            return;
        }

        let current = this.root;

        while (true) {
            if (value === current.value) {
                return;
            }

            if (value < current.value) {
                if (current.left === null) {
                    current.left = { value, left: null, right: null };
                    return;
                }
                current = current.left;
            } else {
                if (current.right === null) {
                    current.right = { value, left: null, right: null };
                    return;
                }
                current = current.right;
            }
        }
    }

    contains(value) {
        let current = this.root;

        while (current !== null) {
            if (current.value === value) {
                return true;
            }

            current = value < current.value
                ? current.left
                : current.right;
        }

        return false;
    }

    inOrder() {
        const result = [];

        const visit = (node) => {
            if (node === null) {
                return;
            }

            visit(node.left);
            result.push(node.value);
            visit(node.right);
        };

        visit(this.root);
        return result;
    }
}


class DependencyGraph {
    constructor(nodes) {
        this.adjacency = new Map();

        for (const node of nodes) {
            if (typeof node !== "string" || node.length === 0) {
                throw new TypeError("Graph nodes must be non-empty strings");
            }

            this.adjacency.set(node, new Set());
        }
    }

    addDependency(task, prerequisite) {
        if (!this.adjacency.has(task) || !this.adjacency.has(prerequisite)) {
            throw new Error("Both graph nodes must exist");
        }

        this.adjacency.get(prerequisite).add(task);
    }

    breadthFirstSearch(start) {
        this.#validateNode(start);

        const visited = new Set([start]);
        const queue = new Queue([start]);
        const result = [];

        while (queue.size > 0) {
            const current = queue.dequeue();
            result.push(current);

            for (const neighbor of this.adjacency.get(current)) {
                if (!visited.has(neighbor)) {
                    visited.add(neighbor);
                    queue.enqueue(neighbor);
                }
            }
        }

        return result;
    }

    topologicalOrder() {
        const indegree = new Map();

        for (const node of this.adjacency.keys()) {
            indegree.set(node, 0);
        }

        for (const neighbors of this.adjacency.values()) {
            for (const neighbor of neighbors) {
                indegree.set(neighbor, indegree.get(neighbor) + 1);
            }
        }

        const queue = new Queue(
            [...indegree.entries()]
                .filter(([, degree]) => degree === 0)
                .map(([node]) => node)
        );

        const result = [];

        while (queue.size > 0) {
            const current = queue.dequeue();
            result.push(current);

            for (const neighbor of this.adjacency.get(current)) {
                const degree = indegree.get(neighbor) - 1;
                indegree.set(neighbor, degree);

                if (degree === 0) {
                    queue.enqueue(neighbor);
                }
            }
        }

        if (result.length !== this.adjacency.size) {
            throw new Error("Dependency graph contains a cycle");
        }

        return result;
    }

    #validateNode(node) {
        if (!this.adjacency.has(node)) {
            throw new Error(`Unknown graph node: ${node}`);
        }
    }
}


function binarySearch(values, target) {
    if (!Array.isArray(values)) {
        throw new TypeError("values must be an array");
    }

    let left = 0;
    let right = values.length - 1;

    while (left <= right) {
        const middle = Math.floor((left + right) / 2);

        if (values[middle] === target) {
            return middle;
        }

        if (values[middle] < target) {
            left = middle + 1;
        } else {
            right = middle - 1;
        }
    }

    return -1;
}


async function processTasks(tasks) {
    if (!Array.isArray(tasks)) {
        throw new TypeError("tasks must be an array");
    }

    // Promise scheduling illustrates event-driven processing without
    // introducing external dependencies.
    const queue = new Queue(tasks);
    const completed = [];

    while (queue.size > 0) {
        const task = queue.dequeue();

        if (!task || typeof task.name !== "string") {
            throw new TypeError("Each task requires a name");
        }

        await new Promise((resolve) => setImmediate(resolve));
        completed.push(task.name);
    }

    return completed;
}


async function main() {
    const stack = new Stack(["parse", "validate"]);
    stack.push("execute");
    console.log("Stack:", stack.pop(), stack.peek());

    const queue = new Queue(["request-1", "request-2"]);
    queue.enqueue("request-3");
    console.log("Queue:", queue.dequeue(), queue.peek());

    const heap = new MinHeap();
    heap.push({ priority: 30, task: "low" });
    heap.push({ priority: 10, task: "urgent" });
    heap.push({ priority: 20, task: "normal" });
    console.log("Priority queue:", heap.pop(), heap.pop(), heap.pop());

    const tree = new BinarySearchTree();
    [50, 30, 70, 20, 40, 60, 80].forEach((value) => tree.insert(value));
    console.log("BST:", tree.inOrder());
    console.log("BST contains 60:", tree.contains(60));

    const graph = new DependencyGraph([
        "compile",
        "test",
        "package",
        "deploy"
    ]);

    graph.addDependency("test", "compile");
    graph.addDependency("package", "test");
    graph.addDependency("deploy", "package");

    console.log("Dependency BFS:", graph.breadthFirstSearch("compile"));
    console.log("Dependency order:", graph.topologicalOrder());

    console.log(
        "Binary search:",
        binarySearch([10, 20, 30, 40, 50], 40)
    );

    const completed = await processTasks([
        { name: "validate-input" },
        { name: "build-index" },
        { name: "persist-result" }
    ]);

    console.log("Asynchronous processing:", completed);

    // Set provides average O(1) membership checks for duplicate detection.
    const identifiers = ["A-101", "A-102", "A-101", "A-103"];
    const uniqueIdentifiers = new Set(identifiers);
    console.log("Unique identifiers:", [...uniqueIdentifiers]);
}


main().catch((error) => {
    console.error("Processing failed:", error.message);
    process.exitCode = 1;
});
