'use strict';

/**
 * Heap and priority-queue case study.
 * The implementation uses an array-backed binary heap and event-driven
 * scheduling to show how heap operations support real workloads.
 */

class BinaryHeap {
    constructor(compare) {
        if (typeof compare !== 'function') {
            throw new TypeError('compare must be a function');
        }
        this.items = [];
        this.compare = compare;
    }

    get size() {
        return this.items.length;
    }

    isEmpty() {
        return this.items.length === 0;
    }

    parent(index) {
        return Math.floor((index - 1) / 2);
    }

    left(index) {
        return index * 2 + 1;
    }

    right(index) {
        return index * 2 + 2;
    }

    swap(a, b) {
        [this.items[a], this.items[b]] = [this.items[b], this.items[a]];
    }

    siftUp(index) {
        while (index > 0) {
            const parent = this.parent(index);

            if (this.compare(this.items[index], this.items[parent]) >= 0) {
                break;
            }

            this.swap(index, parent);
            index = parent;
        }
    }

    siftDown(index) {
        while (true) {
            const left = this.left(index);
            const right = this.right(index);
            let best = index;

            if (
                left < this.size &&
                this.compare(this.items[left], this.items[best]) < 0
            ) {
                best = left;
            }

            if (
                right < this.size &&
                this.compare(this.items[right], this.items[best]) < 0
            ) {
                best = right;
            }

            if (best === index) {
                return;
            }

            this.swap(index, best);
            index = best;
        }
    }

    push(value) {
        this.items.push(value);
        this.siftUp(this.size - 1);
    }

    peek() {
        if (this.isEmpty()) {
            throw new Error('Cannot peek an empty heap');
        }
        return this.items[0];
    }

    pop() {
        if (this.isEmpty()) {
            throw new Error('Cannot pop an empty heap');
        }

        const root = this.items[0];
        const last = this.items.pop();

        if (!this.isEmpty()) {
            this.items[0] = last;
            this.siftDown(0);
        }

        return root;
    }

    build(values) {
        if (!Array.isArray(values)) {
            throw new TypeError('values must be an array');
        }

        this.items = [...values];

        for (let i = Math.floor(this.size / 2) - 1; i >= 0; i--) {
            this.siftDown(i);
        }
    }

    replaceRoot(value) {
        if (this.isEmpty()) {
            throw new Error('Cannot replace root of an empty heap');
        }

        const old = this.items[0];
        this.items[0] = value;
        this.siftDown(0);
        return old;
    }

    validate() {
        for (let i = 1; i < this.size; i++) {
            const parent = this.parent(i);
            if (this.compare(this.items[i], this.items[parent]) < 0) {
                return false;
            }
        }
        return true;
    }
}

class MaxHeap extends BinaryHeap {
    constructor() {
        super((a, b) => b - a);
    }
}

class MinHeap extends BinaryHeap {
    constructor() {
        super((a, b) => a - b);
    }
}

class EventEmitter {
    constructor() {
        this.listeners = new Map();
    }

    on(event, handler) {
        if (typeof handler !== 'function') {
            throw new TypeError('handler must be a function');
        }

        if (!this.listeners.has(event)) {
            this.listeners.set(event, new Set());
        }

        this.listeners.get(event).add(handler);
        return () => this.off(event, handler);
    }

    off(event, handler) {
        this.listeners.get(event)?.delete(handler);
    }

    emit(event, payload) {
        const handlers = this.listeners.get(event);
        if (!handlers) return;

        for (const handler of handlers) {
            handler(payload);
        }
    }
}

class PriorityScheduler extends EventEmitter {
    constructor() {
        super();

        this.sequence = 0;
        this.queue = new BinaryHeap((a, b) => {
            if (a.priority !== b.priority) {
                return a.priority - b.priority;
            }
            return a.sequence - b.sequence;
        });
    }

    submit(task) {
        if (!task || typeof task !== 'object') {
            throw new TypeError('task must be an object');
        }

        if (!String(task.name ?? '').trim()) {
            throw new Error('Task name is required');
        }

        if (!Number.isInteger(task.priority) || task.priority < 0) {
            throw new Error('Priority must be a non-negative integer');
        }

        if (!Number.isInteger(task.duration) || task.duration <= 0) {
            throw new Error('Duration must be a positive integer');
        }

        const entry = {
            ...task,
            sequence: this.sequence++
        };

        this.queue.push(entry);
        this.emit('submitted', entry);
    }

    async run() {
        const results = [];

        while (!this.queue.isEmpty()) {
            const task = this.queue.pop();

            this.emit('started', task);

            await new Promise(resolve => {
                setTimeout(resolve, Math.min(task.duration, 25));
            });

            results.push(task);
            this.emit('completed', task);
        }

        return results;
    }
}

function topK(values, k) {
    if (!Array.isArray(values) || values.length === 0) {
        return [];
    }

    if (!Number.isInteger(k) || k < 1 || k > values.length) {
        throw new RangeError('k must be between 1 and values.length');
    }

    // A min heap of size k keeps the smallest member of the current
    // top-k set at the root, making replacement O(log k).
    const heap = new MinHeap();

    for (const value of values) {
        if (!Number.isFinite(value)) {
            throw new TypeError('topK accepts only finite numbers');
        }

        if (heap.size < k) {
            heap.push(value);
        } else if (value > heap.peek()) {
            heap.replaceRoot(value);
        }
    }

    const result = [];
    while (!heap.isEmpty()) {
        result.push(heap.pop());
    }

    return result.reverse();
}

function heapSort(values) {
    const heap = new MinHeap();
    heap.build(values);

    const sorted = [];
    while (!heap.isEmpty()) {
        sorted.push(heap.pop());
    }

    return sorted;
}

async function main() {
    console.log('=== Min Heap ===');

    const minHeap = new MinHeap();
    [8, 2, 7, 1, 9, 3].forEach(value => minHeap.push(value));

    console.log('Heap:', minHeap.items);
    console.log('Valid:', minHeap.validate());
    console.log('Minimum:', minHeap.peek());

    const ascending = [];
    while (!minHeap.isEmpty()) {
        ascending.push(minHeap.pop());
    }

    console.log('Ascending:', ascending);

    console.log('\n=== Max Heap ===');

    const maxHeap = new MaxHeap();
    maxHeap.build([8, 2, 7, 1, 9, 3]);

    const descending = [];
    while (!maxHeap.isEmpty()) {
        descending.push(maxHeap.pop());
    }

    console.log('Descending:', descending);

    console.log('\n=== Top-K ===');
    console.log(topK([17, 4, 29, 11, 35, 8, 42, 19], 3));

    console.log('\n=== Heap Sort ===');
    console.log(heapSort([15, 3, 20, 7, 9, 1]));

    console.log('\n=== Event-Driven Priority Scheduler ===');

    const scheduler = new PriorityScheduler();

    scheduler.on('submitted', task => {
        console.log(`submitted: ${task.name}`);
    });

    scheduler.on('started', task => {
        console.log(`started: ${task.name}`);
    });

    scheduler.on('completed', task => {
        console.log(`completed: ${task.name}`);
    });

    scheduler.submit({
        name: 'cache-refresh',
        priority: 3,
        duration: 10
    });

    scheduler.submit({
        name: 'security-alert',
        priority: 0,
        duration: 5
    });

    scheduler.submit({
        name: 'report-generation',
        priority: 4,
        duration: 15
    });

    scheduler.submit({
        name: 'incident-analysis',
        priority: 1,
        duration: 10
    });

    const completed = await scheduler.run();

    console.log(
        'Completion order:',
        completed.map(task => task.name)
    );

    console.log('\n=== Edge Case ===');

    try {
        new MinHeap().pop();
    } catch (error) {
        console.log(`Expected failure: ${error.message}`);
    }
}

main().catch(error => {
    console.error(`Fatal error: ${error.message}`);
    process.exitCode = 1;
});
