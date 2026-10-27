"use strict";

/*
 * Queue data structures implemented as a small Node.js job-processing system.
 * The implementations intentionally use JavaScript-specific Map, Set,
 * generators, Promises, and event-driven behavior.
 */

const { EventEmitter } = require("node:events");

class QueueError extends Error {
    constructor(message) {
        super(message);
        this.name = "QueueError";
    }
}

class QueueEmptyError extends QueueError {
    constructor(message = "queue is empty") {
        super(message);
        this.name = "QueueEmptyError";
    }
}

class QueueFullError extends QueueError {
    constructor(message = "queue is full") {
        super(message);
        this.name = "QueueFullError";
    }
}

class Queue {
    constructor(values = []) {
        this.items = [];
        this.head = 0;

        for (const value of values) {
            this.enqueue(value);
        }
    }

    enqueue(value) {
        this.items.push(value);
    }

    dequeue() {
        if (this.isEmpty()) {
            throw new QueueEmptyError();
        }

        const value = this.items[this.head];
        this.items[this.head] = undefined;
        this.head++;

        // Periodic compaction prevents an indefinitely growing backing array.
        if (this.head > 64 && this.head * 2 > this.items.length) {
            this.items = this.items.slice(this.head);
            this.head = 0;
        }

        return value;
    }

    peek() {
        if (this.isEmpty()) {
            throw new QueueEmptyError();
        }
        return this.items[this.head];
    }

    isEmpty() {
        return this.head >= this.items.length;
    }

    get size() {
        return this.items.length - this.head;
    }
}

class CircularQueue {
    constructor(capacity) {
        if (!Number.isInteger(capacity) || capacity <= 0) {
            throw new RangeError("capacity must be a positive integer");
        }

        this.data = new Array(capacity);
        this.capacity = capacity;
        this.head = 0;
        this.tail = 0;
        this.size = 0;
    }

    enqueue(value) {
        if (this.isFull()) {
            throw new QueueFullError();
        }

        this.data[this.tail] = value;
        this.tail = (this.tail + 1) % this.capacity;
        this.size++;
    }

    dequeue() {
        if (this.isEmpty()) {
            throw new QueueEmptyError();
        }

        const value = this.data[this.head];
        this.data[this.head] = undefined;
        this.head = (this.head + 1) % this.capacity;
        this.size--;
        return value;
    }

    isEmpty() {
        return this.size === 0;
    }

    isFull() {
        return this.size === this.capacity;
    }

    toArray() {
        return Array.from(
            { length: this.size },
            (_, index) => this.data[(this.head + index) % this.capacity]
        );
    }
}

class Deque {
    constructor(values = []) {
        this.data = new Map();
        this.frontIndex = 0;
        this.backIndex = 0;

        for (const value of values) {
            this.pushBack(value);
        }
    }

    pushFront(value) {
        this.frontIndex--;
        this.data.set(this.frontIndex, value);
    }

    pushBack(value) {
        this.data.set(this.backIndex, value);
        this.backIndex++;
    }

    popFront() {
        if (this.isEmpty()) {
            throw new QueueEmptyError("deque is empty");
        }

        const value = this.data.get(this.frontIndex);
        this.data.delete(this.frontIndex);
        this.frontIndex++;
        return value;
    }

    popBack() {
        if (this.isEmpty()) {
            throw new QueueEmptyError("deque is empty");
        }

        this.backIndex--;
        const value = this.data.get(this.backIndex);
        this.data.delete(this.backIndex);
        return value;
    }

    peekFront() {
        if (this.isEmpty()) {
            throw new QueueEmptyError("deque is empty");
        }
        return this.data.get(this.frontIndex);
    }

    peekBack() {
        if (this.isEmpty()) {
            throw new QueueEmptyError("deque is empty");
        }
        return this.data.get(this.backIndex - 1);
    }

    isEmpty() {
        return this.data.size === 0;
    }

    get size() {
        return this.data.size;
    }
}

class PriorityQueue {
    constructor() {
        this.heap = [];
        this.sequence = 0;
    }

    enqueue(value, priority) {
        if (!Number.isFinite(priority)) {
            throw new TypeError("priority must be finite");
        }

        const item = {
            value,
            priority,
            sequence: this.sequence++
        };

        this.heap.push(item);
        this.#bubbleUp(this.heap.length - 1);
    }

    dequeue() {
        if (this.heap.length === 0) {
            throw new QueueEmptyError("priority queue is empty");
        }

        const root = this.heap[0];
        const last = this.heap.pop();

        if (this.heap.length > 0) {
            this.heap[0] = last;
            this.#bubbleDown(0);
        }

        return root;
    }

    peek() {
        if (this.heap.length === 0) {
            throw new QueueEmptyError("priority queue is empty");
        }
        return this.heap[0];
    }

    get size() {
        return this.heap.length;
    }

    #less(a, b) {
        if (a.priority !== b.priority) {
            return a.priority < b.priority;
        }
        return a.sequence < b.sequence;
    }

    #bubbleUp(index) {
        while (index > 0) {
            const parent = Math.floor((index - 1) / 2);

            if (!this.#less(this.heap[index], this.heap[parent])) {
                break;
            }

            [this.heap[index], this.heap[parent]] =
                [this.heap[parent], this.heap[index]];

            index = parent;
        }
    }

    #bubbleDown(index) {
        while (true) {
            const left = index * 2 + 1;
            const right = left + 1;
            let smallest = index;

            if (
                left < this.heap.length &&
                this.#less(this.heap[left], this.heap[smallest])
            ) {
                smallest = left;
            }

            if (
                right < this.heap.length &&
                this.#less(this.heap[right], this.heap[smallest])
            ) {
                smallest = right;
            }

            if (smallest === index) {
                break;
            }

            [this.heap[index], this.heap[smallest]] =
                [this.heap[smallest], this.heap[index]];

            index = smallest;
        }
    }
}

class JobProcessor extends EventEmitter {
    constructor(concurrency = 2) {
        super();

        if (!Number.isInteger(concurrency) || concurrency <= 0) {
            throw new RangeError("concurrency must be positive");
        }

        this.concurrency = concurrency;
        this.active = 0;
        this.pending = new PriorityQueue();
        this.completed = new Set();
        this.failed = new Map();
    }

    submit(job) {
        if (
            !job ||
            !Number.isInteger(job.id) ||
            typeof job.name !== "string" ||
            !job.name.trim()
        ) {
            throw new TypeError("job must contain a valid id and name");
        }

        this.pending.enqueue(job, job.priority ?? 100);
        this.emit("submitted", job);
        this.#drain();
    }

    async #run(job) {
        this.active++;
        this.emit("started", job);

        try {
            // A deterministic delay models asynchronous work without dependencies.
            await new Promise((resolve) =>
                setTimeout(resolve, Math.max(1, job.durationMs ?? 10))
            );

            if (job.shouldFail) {
                throw new Error(`job ${job.id} failed`);
            }

            this.completed.add(job.id);
            this.emit("completed", job);
        } catch (error) {
            this.failed.set(job.id, error.message);
            this.emit("failed", job, error);
        } finally {
            this.active--;
            this.#drain();
        }
    }

    #drain() {
        while (this.active < this.concurrency && this.pending.size > 0) {
            const { value: job } = this.pending.dequeue();
            void this.#run(job);
        }
    }

    async waitUntilIdle() {
        while (this.active > 0 || this.pending.size > 0) {
            await new Promise((resolve) => setTimeout(resolve, 5));
        }
    }
}

async function main() {
    console.log("=== FIFO Queue ===");
    const fifo = new Queue(["commit-1", "commit-2"]);
    fifo.enqueue("commit-3");
    console.log(fifo.dequeue(), fifo.peek(), fifo.size);

    console.log("\n=== Circular Queue ===");
    const circular = new CircularQueue(3);
    circular.enqueue("A");
    circular.enqueue("B");
    circular.enqueue("C");
    console.log(circular.toArray());

    circular.dequeue();
    circular.enqueue("D");
    console.log(circular.toArray());

    try {
        circular.enqueue("E");
        circular.enqueue("F");
    } catch (error) {
        console.log(`expected failure: ${error.message}`);
    }

    console.log("\n=== Deque ===");
    const deque = new Deque(["review", "merge"]);
    deque.pushFront("security");
    deque.pushBack("audit");
    console.log(deque.popFront(), deque.popBack(), deque.peekFront());

    console.log("\n=== Priority Queue ===");
    const priority = new PriorityQueue();
    priority.enqueue("normal", 20);
    priority.enqueue("urgent", 1);
    priority.enqueue("release", 10);

    while (priority.size > 0) {
        console.log(priority.dequeue());
    }

    console.log("\n=== Event-Driven Processor ===");
    const processor = new JobProcessor(2);

    processor.on("submitted", (job) =>
        console.log(`submitted: ${job.name}`)
    );
    processor.on("started", (job) =>
        console.log(`started: ${job.name}`)
    );
    processor.on("completed", (job) =>
        console.log(`completed: ${job.name}`)
    );
    processor.on("failed", (job, error) =>
        console.log(`failed: ${job.name}: ${error.message}`)
    );

    processor.submit({
        id: 101,
        name: "unit-tests",
        priority: 20,
        durationMs: 15
    });

    processor.submit({
        id: 102,
        name: "security-scan",
        priority: 5,
        durationMs: 5
    });

    processor.submit({
        id: 103,
        name: "release-build",
        priority: 10,
        durationMs: 10
    });

    processor.submit({
        id: 104,
        name: "deployment",
        priority: 1,
        durationMs: 5,
        shouldFail: true
    });

    await processor.waitUntilIdle();

    console.log("completed IDs:", [...processor.completed]);
    console.log("failed jobs:", [...processor.failed.entries()]);

    console.log("\n=== Assertions ===");
    const q = new Queue([1, 2, 3]);
    console.assert(q.dequeue() === 1);
    console.assert(q.dequeue() === 2);

    const cq = new CircularQueue(2);
    cq.enqueue(1);
    cq.enqueue(2);
    console.assert(cq.dequeue() === 1);
    cq.enqueue(3);
    console.assert(JSON.stringify(cq.toArray()) === JSON.stringify([2, 3]));

    const d = new Deque();
    d.pushBack(2);
    d.pushFront(1);
    d.pushBack(3);
    console.assert(d.popFront() === 1);
    console.assert(d.popBack() === 3);

    const pq = new PriorityQueue();
    pq.enqueue("later", 50);
    pq.enqueue("urgent", 1);
    console.assert(pq.dequeue().value === "urgent");

    console.log("queue invariants passed");
}

main().catch((error) => {
    console.error("fatal error:", error);
    process.exitCode = 1;
});
