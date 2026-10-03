'use strict';

/*
 * Threads in JavaScript are represented by Node.js Worker Threads.
 *
 * This file deliberately uses a different perspective from the Python example:
 * it models an event-driven service coordinator that creates workers on demand,
 * communicates through message passing, supports worker failure detection,
 * and compares shared-memory communication with message-based communication.
 *
 * Run with:
 *   node threads-case-study.js
 *
 * Worker Threads execute this same file when workerData.mode === "worker".
 */

const {
    Worker,
    isMainThread,
    parentPort,
    workerData,
    MessageChannel,
    SHARE_ENV
} = require('node:worker_threads');

const os = require('node:os');
const { performance } = require('node:perf_hooks');


// -----------------------------------------------------------------------------
// Worker-side execution
// -----------------------------------------------------------------------------

if (!isMainThread) {
    runWorker();
    return;
}


async function runWorker() {
    const { mode, workerId, workload } = workerData;

    if (mode === 'prime') {
        const started = performance.now();

        try {
            const count = countPrimes(workload.limit);

            parentPort.postMessage({
                type: 'completed',
                workerId,
                result: count,
                elapsedMs: performance.now() - started
            });
        } catch (error) {
            parentPort.postMessage({
                type: 'failed',
                workerId,
                error: error.message
            });
        }

        return;
    }

    if (mode === 'event-worker') {
        parentPort.on('message', async (message) => {
            if (message.type === 'process') {
                try {
                    const result = await processEvent(message.event);

                    parentPort.postMessage({
                        type: 'event-result',
                        requestId: message.requestId,
                        result
                    });
                } catch (error) {
                    parentPort.postMessage({
                        type: 'event-failed',
                        requestId: message.requestId,
                        error: error.message
                    });
                }
            }

            if (message.type === 'shutdown') {
                parentPort.close();
            }
        });

        parentPort.postMessage({
            type: 'ready',
            workerId
        });

        return;
    }

    throw new Error(`Unknown worker mode: ${mode}`);
}


// -----------------------------------------------------------------------------
// Event-driven worker pool
// -----------------------------------------------------------------------------

class EventWorkerPool {
    constructor(size) {
        if (!Number.isInteger(size) || size < 1) {
            throw new RangeError('Worker pool size must be a positive integer');
        }

        this.size = size;
        this.workers = [];
        this.pending = new Map();
        this.nextWorker = 0;
        this.nextRequestId = 1;
        this.closed = false;
    }

    async start() {
        const startupPromises = [];

        for (let index = 0; index < this.size; index += 1) {
            startupPromises.push(this.createWorker(index));
        }

        await Promise.all(startupPromises);
    }

    createWorker(workerId) {
        return new Promise((resolve, reject) => {
            const worker = new Worker(__filename, {
                workerData: {
                    mode: 'event-worker',
                    workerId
                },
                env: SHARE_ENV
            });

            const workerRecord = {
                worker,
                workerId,
                ready: false,
                busy: false
            };

            const onInitialMessage = (message) => {
                if (message.type === 'ready') {
                    workerRecord.ready = true;
                    worker.off('message', onInitialMessage);
                    this.attachWorkerListeners(workerRecord);
                    resolve();
                }
            };

            worker.on('message', onInitialMessage);

            worker.once('error', (error) => {
                reject(error);
            });

            worker.once('exit', (code) => {
                if (code !== 0 && !this.closed) {
                    this.failPendingForWorker(workerRecord, new Error(
                        `Worker ${workerId} exited with code ${code}`
                    ));
                }
            });

            this.workers.push(workerRecord);
        });
    }

    attachWorkerListeners(workerRecord) {
        const { worker } = workerRecord;

        worker.on('message', (message) => {
            if (message.type === 'event-result') {
                this.resolveRequest(message.requestId, message.result);
            }

            if (message.type === 'event-failed') {
                this.rejectRequest(
                    message.requestId,
                    new Error(message.error)
                );
            }
        });

        worker.on('error', (error) => {
            this.failPendingForWorker(workerRecord, error);
        });
    }

    submit(event) {
        if (this.closed) {
            return Promise.reject(new Error('Worker pool is closed'));
        }

        validateEvent(event);

        const availableWorkers = this.workers.filter(
            (record) => record.ready && !record.busy
        );

        if (availableWorkers.length === 0) {
            return Promise.reject(
                new Error('No worker is currently available')
            );
        }

        const record = availableWorkers[this.nextWorker % availableWorkers.length];
        this.nextWorker += 1;

        const requestId = this.nextRequestId++;
        record.busy = true;

        return new Promise((resolve, reject) => {
            this.pending.set(requestId, {
                resolve,
                reject,
                workerRecord: record
            });

            record.worker.postMessage({
                type: 'process',
                requestId,
                event
            });
        });
    }

    resolveRequest(requestId, result) {
        const request = this.pending.get(requestId);

        if (!request) {
            return;
        }

        request.workerRecord.busy = false;
        this.pending.delete(requestId);
        request.resolve(result);
    }

    rejectRequest(requestId, error) {
        const request = this.pending.get(requestId);

        if (!request) {
            return;
        }

        request.workerRecord.busy = false;
        this.pending.delete(requestId);
        request.reject(error);
    }

    failPendingForWorker(workerRecord, error) {
        for (const [requestId, request] of this.pending.entries()) {
            if (request.workerRecord === workerRecord) {
                this.pending.delete(requestId);
                request.reject(error);
            }
        }

        workerRecord.busy = false;
    }

    async close() {
        this.closed = true;

        const terminationPromises = this.workers.map(
            (record) => record.worker.terminate()
        );

        await Promise.all(terminationPromises);
    }
}


// -----------------------------------------------------------------------------
// Event validation and processing
// -----------------------------------------------------------------------------

function validateEvent(event) {
    if (!event || typeof event !== 'object') {
        throw new TypeError('Event must be an object');
    }

    if (typeof event.service !== 'string' || event.service.trim() === '') {
        throw new TypeError('Event service must be a non-empty string');
    }

    if (!['INFO', 'WARNING', 'ERROR'].includes(event.level)) {
        throw new RangeError(
            'Event level must be INFO, WARNING, or ERROR'
        );
    }

    if (typeof event.message !== 'string' || event.message.length > 500) {
        throw new RangeError(
            'Event message must be a string of at most 500 characters'
        );
    }
}


function processEvent(event) {
    validateEvent(event);

    return new Promise((resolve) => {
        /*
         * JavaScript's event loop remains available while this timer represents
         * an I/O-like delay. The actual CPU-intensive part can be moved to a
         * Worker Thread when it becomes expensive enough to block the event loop.
         */
        setTimeout(() => {
            resolve({
                service: event.service,
                level: event.level,
                accepted: true,
                messageLength: event.message.length
            });
        }, 15);
    });
}


// -----------------------------------------------------------------------------
// Shared memory
// -----------------------------------------------------------------------------

function demonstrateSharedArrayBuffer() {
    console.log('\n=== Shared memory with SharedArrayBuffer ===');

    const shared = new SharedArrayBuffer(Int32Array.BYTES_PER_ELEMENT);
    const counter = new Int32Array(shared);

    const worker = new Worker(__filename, {
        workerData: {
            mode: 'shared-counter',
            shared
        }
    });

    return new Promise((resolve, reject) => {
        worker.on('message', (message) => {
            if (message.type === 'shared-complete') {
                console.log(`Worker incremented shared counter to ${message.value}`);
                resolve();
            }
        });

        worker.on('error', reject);
    });
}


// Handle the shared-memory worker without affecting the normal worker branch.
if (!isMainThread && workerData.mode === 'shared-counter') {
    const counter = new Int32Array(workerData.shared);

    for (let index = 0; index < 10000; index += 1) {
        /*
         * Atomics.add prevents a lost update when multiple agents access the
         * same shared memory location.
         */
        Atomics.add(counter, 0, 1);
    }

    parentPort.postMessage({
        type: 'shared-complete',
        value: Atomics.load(counter, 0)
    });
    return;
}


// -----------------------------------------------------------------------------
// CPU-bound workload
// -----------------------------------------------------------------------------

function countPrimes(limit) {
    if (!Number.isInteger(limit) || limit < 2) {
        return 0;
    }

    let count = 0;

    for (let number = 2; number <= limit; number += 1) {
        let prime = true;

        for (
            let divisor = 2;
            divisor * divisor <= number;
            divisor += 1
        ) {
            if (number % divisor === 0) {
                prime = false;
                break;
            }
        }

        if (prime) {
            count += 1;
        }
    }

    return count;
}


function runCpuWorkers(limits) {
    return new Promise((resolve, reject) => {
        const results = [];
        let completed = 0;
        let settled = false;

        limits.forEach((limit, index) => {
            const worker = new Worker(__filename, {
                workerData: {
                    mode: 'prime',
                    workerId: index,
                    workload: { limit }
                }
            });

            worker.on('message', (message) => {
                if (message.type === 'completed') {
                    results[index] = {
                        limit,
                        count: message.result,
                        elapsedMs: message.elapsedMs
                    };

                    completed += 1;

                    if (completed === limits.length && !settled) {
                        settled = true;
                        resolve(results);
                    }
                }

                if (message.type === 'failed' && !settled) {
                    settled = true;
                    reject(new Error(message.error));
                }
            });

            worker.on('error', (error) => {
                if (!settled) {
                    settled = true;
                    reject(error);
                }
            });
        });
    });
}


// -----------------------------------------------------------------------------
// Thread lifecycle
// -----------------------------------------------------------------------------

async function demonstrateLifecycle() {
    console.log('\n=== Worker thread lifecycle ===');

    const worker = new Worker(__filename, {
        workerData: {
            mode: 'event-worker',
            workerId: 'lifecycle'
        }
    });

    await new Promise((resolve, reject) => {
        worker.once('message', (message) => {
            if (message.type === 'ready') {
                console.log('Worker transitioned from construction to ready state.');
                resolve();
            }
        });

        worker.once('error', reject);
    });

    console.log(`Worker thread identifier: ${worker.threadId}`);

    const exitCode = await worker.terminate();
    console.log(`Worker termination completed with code: ${exitCode}`);

    /*
     * Node does not expose operating-system scheduler states such as RUNNING
     * and BLOCKED directly through Worker. Application-level lifecycle states
     * should therefore be modeled explicitly when an application needs them.
     */
}


// -----------------------------------------------------------------------------
// Process versus worker-thread architecture
// -----------------------------------------------------------------------------

function demonstrateArchitecture() {
    console.log('\n=== Processes versus threads ===');

    console.log(
        'Node.js uses one main JavaScript execution thread for its event loop.'
    );

    console.log(
        'Worker Threads create additional JavaScript execution contexts inside the process.'
    );

    console.log(
        'Child processes provide stronger address-space isolation and independent process failure domains.'
    );

    console.log(
        'Worker Threads can share memory through SharedArrayBuffer, while ordinary messages are copied or transferred.'
    );
}


// -----------------------------------------------------------------------------
// Main case study
// -----------------------------------------------------------------------------

async function main() {
    console.log('THREADS CASE STUDY');
    console.log('==================');

    demonstrateArchitecture();

    await demonstrateLifecycle();

    console.log('\n=== Event-driven worker pool ===');

    const pool = new EventWorkerPool(
        Math.max(2, Math.min(4, os.cpus().length))
    );

    await pool.start();

    const events = [
        {
            service: 'api',
            level: 'INFO',
            message: 'request completed'
        },
        {
            service: 'payments',
            level: 'WARNING',
            message: 'payment retry scheduled'
        },
        {
            service: 'users',
            level: 'ERROR',
            message: 'database timeout'
        },
        {
            service: 'search',
            level: 'INFO',
            message: 'index refresh completed'
        }
    ];

    /*
     * Promise.all demonstrates fan-out/fan-in: several independent worker
     * operations are started, then their results are collected as one operation.
     */
    const results = await Promise.all(
        events.map((event) => pool.submit(event))
    );

    for (const result of results) {
        console.log(result);
    }

    await pool.close();

    console.log('\n=== CPU-bound worker threads ===');

    const limits = [9000, 9100, 9200, 9300];
    const started = performance.now();

    const primeResults = await runCpuWorkers(limits);

    console.log(`Parallel worker elapsed time: ${(performance.now() - started).toFixed(2)} ms`);

    for (const result of primeResults) {
        console.log(
            `limit=${result.limit}, primes=${result.count}, ` +
            `workerTime=${result.elapsedMs.toFixed(2)} ms`
        );
    }

    await demonstrateSharedArrayBuffer();

    console.log('\n=== JavaScript thread-model implications ===');

    console.log(
        'The event loop behaves like a single logical execution stream for ordinary JavaScript callbacks.'
    );
    console.log(
        'Worker Threads provide parallel JavaScript execution for CPU-intensive tasks.'
    );
    console.log(
        'A worker pool avoids creating an unbounded number of operating-system threads.'
    );
    console.log(
        'Shared memory increases coordination performance but introduces synchronization responsibilities.'
    );
    console.log(
        'Message passing isolates mutable state and is often simpler to reason about.'
    );

    console.log('\nCase study completed.');
}


main().catch((error) => {
    console.error(`Fatal error: ${error.message}`);
    process.exitCode = 1;
});
