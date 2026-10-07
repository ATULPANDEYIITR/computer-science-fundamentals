'use strict';

/*
 * Synchronization mechanisms in Node.js using worker_threads.
 *
 * JavaScript code running in one Node.js event loop normally avoids shared
 * memory races by serializing JavaScript execution. Once Worker threads use
 * SharedArrayBuffer, actual shared-memory synchronization becomes relevant.
 *
 * This program demonstrates:
 *   - Atomics as the low-level locking mechanism
 *   - a mutex built on an atomic state
 *   - a counting semaphore
 *   - a condition-variable-like wait/notify protocol
 *   - a monitor combining state, mutex behavior, and waiting
 *   - a bounded concurrent service
 */

const {
    Worker,
    isMainThread,
    parentPort,
    workerData
} = require('node:worker_threads');

const { promisify } = require('node:util');

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

class AtomicMutex {
    constructor(sharedState) {
        this.state = new Int32Array(sharedState);
    }

    lock(timeoutMs = 1000) {
        const deadline = Date.now() + timeoutMs;

        while (true) {
            if (Atomics.compareExchange(this.state, 0, 0, 1) === 0) {
                return true;
            }

            const remaining = deadline - Date.now();
            if (remaining <= 0) {
                return false;
            }

            Atomics.wait(this.state, 0, 1, Math.min(remaining, 20));
        }
    }

    unlock() {
        if (Atomics.exchange(this.state, 0, 0) !== 1) {
            throw new Error('Mutex was not locked');
        }

        Atomics.notify(this.state, 0, 1);
    }
}

class CountingSemaphore {
    /*
     * The integer represents available permits.
     *
     * Atomically decrementing the value only when it is positive prevents
     * more workers from entering than the configured capacity allows.
     */
    constructor(sharedState, initialPermits) {
        this.state = new Int32Array(sharedState);

        if (this.state[0] === 0) {
            Atomics.store(this.state, 0, initialPermits);
        }
    }

    acquire(timeoutMs = 1000) {
        const deadline = Date.now() + timeoutMs;

        while (true) {
            const available = Atomics.load(this.state, 0);

            if (available > 0 &&
                Atomics.compareExchange(
                    this.state,
                    0,
                    available,
                    available - 1
                ) === available) {
                return true;
            }

            const remaining = deadline - Date.now();
            if (remaining <= 0) {
                return false;
            }

            Atomics.wait(
                this.state,
                0,
                Atomics.load(this.state, 0),
                Math.min(remaining, 20)
            );
        }
    }

    release() {
        const previous = Atomics.add(this.state, 0, 1);

        if (previous < 0) {
            throw new Error('Semaphore state became invalid');
        }

        Atomics.notify(this.state, 0, 1);
    }
}

class Monitor {
    /*
     * A monitor owns state and exposes operations that acquire the mutex
     * before checking or changing that state.
     *
     * A condition is represented here by the same atomic wait/notify facility
     * provided by Atomics. The wait predicate is always rechecked after wakeup.
     */
    constructor(capacity) {
        this.capacity = capacity;
        this.buffer = [];
        this.mutex = new AtomicMutex(new SharedArrayBuffer(4));
        this.conditionWord = new Int32Array(new SharedArrayBuffer(4));
    }

    put(item) {
        while (true) {
            if (!this.mutex.lock()) {
                throw new Error('Unable to enter monitor');
            }

            if (this.buffer.length < this.capacity) {
                this.buffer.push(item);
                Atomics.add(this.conditionWord, 0, 1);
                Atomics.notify(this.conditionWord, 0);
                this.mutex.unlock();
                return;
            }

            this.mutex.unlock();

            /*
             * This monitor implementation is intentionally compact. The
             * condition word is used as a wakeup signal; the capacity
             * predicate remains authoritative and is checked again.
             */
            Atomics.wait(this.conditionWord, 0, Atomics.load(this.conditionWord, 0), 25);
        }
    }

    take() {
        while (true) {
            if (!this.mutex.lock()) {
                throw new Error('Unable to enter monitor');
            }

            if (this.buffer.length > 0) {
                const item = this.buffer.shift();
                Atomics.add(this.conditionWord, 0, 1);
                Atomics.notify(this.conditionWord, 0);
                this.mutex.unlock();
                return item;
            }

            this.mutex.unlock();
            Atomics.wait(this.conditionWord, 0, Atomics.load(this.conditionWord, 0), 25);
        }
    }
}

async function basicMutexExample() {
    console.log('\n=== Mutex with SharedArrayBuffer ===');

    const sharedCounter = new SharedArrayBuffer(4);
    const counter = new Int32Array(sharedCounter);
    const lock = new AtomicMutex(new SharedArrayBuffer(4));

    async function increment() {
        for (let i = 0; i < 1000; i++) {
            if (!lock.lock()) {
                throw new Error('Could not acquire mutex');
            }

            const current = Atomics.load(counter, 0);
            await sleep(0);
            Atomics.store(counter, 0, current + 1);

            lock.unlock();
        }
    }

    await Promise.all(
        Array.from({ length: 4 }, () => increment())
    );

    console.log('Expected:', 4000);
    console.log('Actual:  ', Atomics.load(counter, 0));
}

async function semaphoreExample() {
    console.log('\n=== Counting semaphore ===');

    const semaphore = new CountingSemaphore(
        new SharedArrayBuffer(4),
        2
    );

    let active = 0;
    let peak = 0;

    async function expensiveOperation(id) {
        if (!semaphore.acquire(1000)) {
            throw new Error(`Worker ${id} timed out waiting for a permit`);
        }

        try {
            active++;
            peak = Math.max(peak, active);

            console.log(`Request ${id} entered; active=${active}`);
            await sleep(20 + Math.random() * 30);
        } finally {
            active--;
            semaphore.release();
            console.log(`Request ${id} left; active=${active}`);
        }
    }

    await Promise.all(
        Array.from({ length: 8 }, (_, id) => expensiveOperation(id))
    );

    console.log('Configured concurrency:', 2);
    console.log('Observed peak:', peak);
}

async function monitorExample() {
    console.log('\n=== Monitor-style bounded buffer ===');

    /*
     * This monitor is useful inside a single JavaScript agent as an
     * encapsulated synchronization design. Worker-based shared memory is
     * used elsewhere in this program for actual cross-thread coordination.
     */
    const monitor = new Monitor(2);
    const produced = [];
    const consumed = [];

    const producer = (async () => {
        for (let i = 0; i < 5; i++) {
            monitor.put(`job-${i}`);
            produced.push(`job-${i}`);
            await sleep(5);
        }
    })();

    const consumer = (async () => {
        for (let i = 0; i < 5; i++) {
            const item = monitor.take();
            consumed.push(item);
            await sleep(12);
        }
    })();

    await Promise.all([producer, consumer]);

    console.log('Produced:', produced);
    console.log('Consumed:', consumed);
}

async function conditionPredicateExample() {
    console.log('\n=== Condition-style predicate waiting ===');

    const state = {
        ready: false,
        value: null
    };

    /*
     * Promise-based condition waiting is natural when no SharedArrayBuffer
     * is required. The predicate is checked after every notification.
     */
    let notify;
    let notification = new Promise(resolve => {
        notify = resolve;
    });

    const waiter = (async () => {
        while (!state.ready) {
            await notification;
            notification = new Promise(resolve => {
                notify = resolve;
            });
        }

        return state.value;
    })();

    await sleep(30);

    state.value = {
        status: 'ready',
        timestamp: new Date().toISOString()
    };
    state.ready = true;
    notify();

    console.log('Condition result:', await waiter);
}

async function workerThreadDemo() {
    console.log('\n=== Worker-thread shared-memory synchronization ===');

    const sharedCounter = new SharedArrayBuffer(4);
    const mutexState = new SharedArrayBuffer(4);

    const workers = Array.from({ length: 4 }, (_, workerId) => {
        return new Promise((resolve, reject) => {
            const worker = new Worker(__filename, {
                workerData: {
                    workerId,
                    iterations: 1000,
                    sharedCounter,
                    mutexState
                }
            });

            worker.on('message', resolve);
            worker.on('error', reject);
        });
    });

    const results = await Promise.all(workers);

    console.log('Worker results:', results);
    console.log('Shared counter:', new Int32Array(sharedCounter)[0]);
}

async function run() {
    await basicMutexExample();
    await semaphoreExample();
    await monitorExample();
    await conditionPredicateExample();
    await workerThreadDemo();

    console.log('\n=== Synchronization rules ===');
    console.log('Mutex: one owner protects a critical section.');
    console.log('Semaphore: a permit count limits concurrent access.');
    console.log('Monitor: state and synchronization protocol are encapsulated together.');
    console.log('Condition variable: threads wait for a state predicate instead of polling.');
    console.log('Atomics: provide indivisible operations on shared memory.');
    console.log('Always release acquired locks and permits in finally blocks.');
}

if (!isMainThread) {
    const counter = new Int32Array(workerData.sharedCounter);
    const mutex = new AtomicMutex(workerData.mutexState);

    for (let i = 0; i < workerData.iterations; i++) {
        if (!mutex.lock(1000)) {
            throw new Error(`Worker ${workerData.workerId} timed out`);
        }

        try {
            Atomics.add(counter, 0, 1);
        } finally {
            mutex.unlock();
        }
    }

    parentPort.postMessage({
        workerId: workerData.workerId,
        iterations: workerData.iterations,
        completed: true
    });
} else {
    run().catch(error => {
        console.error(error);
        process.exitCode = 1;
    });
}
