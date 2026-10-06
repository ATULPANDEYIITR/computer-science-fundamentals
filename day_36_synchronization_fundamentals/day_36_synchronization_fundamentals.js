"use strict";

/*
 * Synchronization Fundamentals in JavaScript
 *
 * JavaScript normally executes JavaScript callbacks on a single event-loop
 * thread, but asynchronous operations can still create logical race conditions.
 * Node.js worker_threads additionally permit true shared-memory concurrency.
 *
 * Run:
 *     node synchronization_fundamentals.js
 */

const { Worker, isMainThread, parentPort, workerData } = require("node:worker_threads");

function delay(milliseconds) {
    return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

async function demonstrateAsyncRace() {
    console.log("\n=== Asynchronous Race Condition ===");

    let balance = 100;
    const withdrawalAmount = 80;

    async function withdraw(name) {
        if (balance < withdrawalAmount) {
            return `${name}: rejected`;
        }

        // The await yields control back to the event loop. Another withdrawal
        // can now pass the same check before this operation updates the balance.
        await delay(10);

        balance -= withdrawalAmount;
        return `${name}: approved`;
    }

    const results = await Promise.all([
        withdraw("request-A"),
        withdraw("request-B"),
    ]);

    console.log(results);
    console.log(`Final balance: ${balance}`);
    console.log(
        "Both requests can observe the same state because the check and update "
        + "were separated by an asynchronous yield."
    );
}

class AsyncMutex {
    constructor() {
        this.locked = false;
        this.waiters = [];
    }

    acquire() {
        return new Promise((resolve) => {
            if (!this.locked) {
                this.locked = true;
                resolve(this.release.bind(this));
                return;
            }

            this.waiters.push(resolve);
        });
    }

    release() {
        const next = this.waiters.shift();

        if (next) {
            next(this.release.bind(this));
            return;
        }

        this.locked = false;
    }

    async runExclusive(operation) {
        const release = await this.acquire();

        try {
            return await operation();
        } finally {
            // finally guarantees that an exception does not leave the mutex
            // permanently locked.
            release();
        }
    }
}

async function demonstrateAsyncMutex() {
    console.log("\n=== Mutual Exclusion with an Async Mutex ===");

    let balance = 100;
    const mutex = new AsyncMutex();

    async function withdraw(name) {
        return mutex.runExclusive(async () => {
            if (balance < 80) {
                return `${name}: rejected`;
            }

            await delay(10);
            balance -= 80;
            return `${name}: approved`;
        });
    }

    const results = await Promise.all([
        withdraw("request-A"),
        withdraw("request-B"),
    ]);

    console.log(results);
    console.log(`Final balance: ${balance}`);
}

class InventoryService {
    constructor(quantity) {
        if (!Number.isInteger(quantity) || quantity < 0) {
            throw new RangeError("Inventory quantity must be a non-negative integer.");
        }

        this.quantity = quantity;
        this.mutex = new AsyncMutex();
    }

    async reserve(quantity) {
        if (!Number.isInteger(quantity) || quantity <= 0) {
            throw new RangeError("Reservation quantity must be positive.");
        }

        return this.mutex.runExclusive(async () => {
            if (quantity > this.quantity) {
                return false;
            }

            // The invariant is protected for the entire check-and-update.
            this.quantity -= quantity;
            return true;
        });
    }
}

async function demonstrateProtectedResource() {
    console.log("\n=== Protected Resource ===");

    const inventory = new InventoryService(50);

    const requests = Array.from({ length: 20 }, (_, index) =>
        inventory.reserve((index % 4) + 1)
    );

    const results = await Promise.all(requests);

    console.log(`Successful reservations: ${results.filter(Boolean).length}`);
    console.log(`Remaining inventory: ${inventory.quantity}`);
}

function runSharedMemoryWorker() {
    const sharedCounter = new Int32Array(
        new SharedArrayBuffer(Int32Array.BYTES_PER_ELEMENT)
    );

    return new Promise((resolve, reject) => {
        const workerCount = 4;
        let completed = 0;

        const workers = Array.from({ length: workerCount }, () => {
            const worker = new Worker(__filename, {
                workerData: {
                    sharedCounter,
                    iterations: 100_000,
                },
            });

            worker.on("message", () => {
                completed += 1;

                if (completed === workerCount) {
                    resolve(sharedCounter[0]);
                }
            });

            worker.on("error", reject);
        });
    });
}

function demonstrateAtomicOperation() {
    console.log("\n=== Shared Memory and Atomic Increment ===");

    /*
     * Atomics.add is a hardware/runtime-supported atomic read-modify-write
     * operation. Multiple worker threads can update the same shared integer
     * without losing increments.
     */
    const sharedCounter = new Int32Array(
        new SharedArrayBuffer(Int32Array.BYTES_PER_ELEMENT)
    );

    const workerCount = 4;
    const iterations = 50_000;

    return new Promise((resolve, reject) => {
        let completed = 0;

        for (let index = 0; index < workerCount; index += 1) {
            const worker = new Worker(__filename, {
                workerData: {
                    sharedCounter,
                    iterations,
                    useAtomics: true,
                },
            });

            worker.on("message", () => {
                completed += 1;

                if (completed === workerCount) {
                    console.log(`Expected counter: ${workerCount * iterations}`);
                    console.log(`Actual counter:   ${sharedCounter[0]}`);
                    resolve();
                }
            });

            worker.on("error", reject);
        }
    });
}

async function demonstrateEventOrdering() {
    console.log("\n=== Event-Loop Ordering and Logical Critical Sections ===");

    const events = [];

    async function operation(name, pause) {
        events.push(`${name}: read`);

        await delay(pause);

        events.push(`${name}: write`);
    }

    await Promise.all([
        operation("operation-A", 15),
        operation("operation-B", 5),
    ]);

    console.log(events.join(" -> "));
    console.log(
        "An event-loop application avoids simultaneous JavaScript execution, "
        + "but asynchronous interleaving can still violate application invariants."
    );
}

async function main() {
    await demonstrateAsyncRace();
    await demonstrateAsyncMutex();
    await demonstrateProtectedResource();
    await demonstrateEventOrdering();
    await demonstrateAtomicOperation();

    // This helper intentionally exists to show that a SharedArrayBuffer can be
    // shared by workers. It is not needed by the primary demonstration.
    void runSharedMemoryWorker;
}

if (!isMainThread) {
    const { sharedCounter, iterations, useAtomics = false } = workerData;

    for (let index = 0; index < iterations; index += 1) {
        if (useAtomics) {
            Atomics.add(sharedCounter, 0, 1);
        } else {
            // This path illustrates a non-atomic read-modify-write. It should
            // not be used for shared counters when correctness matters.
            sharedCounter[0] = sharedCounter[0] + 1;
        }
    }

    parentPort.postMessage("complete");
} else {
    main().catch((error) => {
        console.error(error);
        process.exitCode = 1;
    });
}
