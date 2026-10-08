"use strict";

/*
 * Deadlocks: conditions, prevention, avoidance, detection, and recovery.
 *
 * This Node.js program uses an event-driven resource manager to model
 * concurrent work. It intentionally uses JavaScript-specific mechanisms:
 * classes, Maps/Sets, promises, async functions, events, and immutable
 * snapshots for diagnostics.
 *
 * Run with:
 *   node deadlocks.js
 */

const { EventEmitter } = require("node:events");

class ResourcePool {
    constructor(capacities) {
        this.capacity = new Map(Object.entries(capacities));
        this.available = new Map(this.capacity);

        for (const [name, count] of this.capacity) {
            if (!Number.isInteger(count) || count <= 0) {
                throw new Error(`Invalid capacity for ${name}`);
            }
        }
    }

    canAllocate(request) {
        return [...request.entries()].every(
            ([resource, amount]) =>
                this.available.has(resource) &&
                amount >= 0 &&
                amount <= this.available.get(resource)
        );
    }

    allocate(request) {
        if (!this.canAllocate(request)) {
            return false;
        }

        for (const [resource, amount] of request) {
            this.available.set(
                resource,
                this.available.get(resource) - amount
            );
        }

        return true;
    }

    release(allocation) {
        for (const [resource, amount] of allocation) {
            if (!this.capacity.has(resource)) {
                throw new Error(`Unknown resource: ${resource}`);
            }

            const next = this.available.get(resource) + amount;

            if (next > this.capacity.get(resource)) {
                throw new Error(`Release exceeds capacity for ${resource}`);
            }

            this.available.set(resource, next);
        }
    }

    snapshot() {
        return Object.fromEntries(this.available);
    }
}

class Job {
    constructor(name, maximum) {
        if (!name.trim()) {
            throw new Error("Job name cannot be empty");
        }

        this.name = name;
        this.maximum = new Map(Object.entries(maximum));
        this.allocation = new Map();
        this.state = "READY";

        for (const [resource, amount] of this.maximum) {
            if (!Number.isInteger(amount) || amount < 0) {
                throw new Error(`Invalid maximum claim: ${resource}`);
            }

            this.allocation.set(resource, 0);
        }
    }

    remainingNeed() {
        const need = new Map();

        for (const [resource, maximum] of this.maximum) {
            need.set(
                resource,
                maximum - (this.allocation.get(resource) || 0)
            );
        }

        return need;
    }

    addAllocation(request) {
        for (const [resource, amount] of request) {
            const current = this.allocation.get(resource) || 0;
            const maximum = this.maximum.get(resource);

            if (maximum === undefined || current + amount > maximum) {
                throw new Error(
                    `${this.name} exceeds maximum claim for ${resource}`
                );
            }

            this.allocation.set(resource, current + amount);
        }
    }

    removeAllocation() {
        const released = new Map(this.allocation);

        for (const resource of this.allocation.keys()) {
            this.allocation.set(resource, 0);
        }

        return released;
    }
}

class DeadlockManager extends EventEmitter {
    constructor(capacities) {
        super();
        this.pool = new ResourcePool(capacities);
        this.jobs = new Map();
        this.waitingRequests = new Map();
    }

    addJob(job) {
        if (this.jobs.has(job.name)) {
            throw new Error(`Duplicate job: ${job.name}`);
        }

        for (const resource of job.maximum.keys()) {
            if (!this.pool.capacity.has(resource)) {
                throw new Error(`Unknown resource: ${resource}`);
            }
        }

        this.jobs.set(job.name, job);
    }

    request(jobName, request, { avoid = false } = {}) {
        const job = this.jobs.get(jobName);

        if (!job) {
            throw new Error(`Unknown job: ${jobName}`);
        }

        const requested = new Map(Object.entries(request));

        for (const [resource, amount] of requested) {
            if (!Number.isInteger(amount) || amount < 0) {
                throw new Error(`Invalid request amount for ${resource}`);
            }

            const need = job.remainingNeed().get(resource) ?? 0;

            if (amount > need) {
                throw new Error(
                    `${jobName} requested more ${resource} than its remaining need`
                );
            }
        }

        if (!this.pool.canAllocate(requested)) {
            job.state = "WAITING";
            this.waitingRequests.set(jobName, requested);
            this.emit("waiting", {
                job: jobName,
                request: Object.fromEntries(requested),
            });
            return false;
        }

        if (avoid && !this.isSafeAfter(jobName, requested)) {
            job.state = "WAITING";
            this.waitingRequests.set(jobName, requested);
            this.emit("unsafe-request", {
                job: jobName,
                request: Object.fromEntries(requested),
            });
            return false;
        }

        this.pool.allocate(requested);
        job.addAllocation(requested);
        job.state = "RUNNING";
        this.waitingRequests.delete(jobName);

        this.emit("allocated", {
            job: jobName,
            request: Object.fromEntries(requested),
        });

        return true;
    }

    release(jobName, release) {
        const job = this.jobs.get(jobName);

        if (!job) {
            throw new Error(`Unknown job: ${jobName}`);
        }

        const released = new Map(Object.entries(release));

        for (const [resource, amount] of released) {
            const held = job.allocation.get(resource) || 0;

            if (!Number.isInteger(amount) || amount < 0 || amount > held) {
                throw new Error(`Invalid release by ${jobName}: ${resource}`);
            }

            job.allocation.set(resource, held - amount);
        }

        this.pool.release(released);
        this.emit("released", {
            job: jobName,
            resources: Object.fromEntries(released),
        });
    }

    isSafeAfter(jobName, request) {
        const job = this.jobs.get(jobName);

        const originalAllocation = new Map(job.allocation);

        try {
            this.pool.allocate(request);
            job.addAllocation(request);

            const result = this.isSafeState();

            this.pool.release(request);

            for (const [resource, amount] of originalAllocation) {
                job.allocation.set(resource, amount);
            }

            return result;
        } catch (error) {
            for (const [resource, amount] of job.allocation) {
                const original = originalAllocation.get(resource) || 0;
                job.allocation.set(resource, original);
                const temporary = amount - original;

                if (temporary > 0) {
                    this.pool.release(new Map([[resource, temporary]]));
                }
            }

            throw error;
        }
    }

    isSafeState() {
        const work = new Map(this.pool.available);

        const active = [...this.jobs.values()].filter(
            job => !["ABORTED", "COMPLETED"].includes(job.state)
        );

        const finished = new Set();

        let changed = true;

        while (changed) {
            changed = false;

            for (const job of active) {
                if (finished.has(job.name)) {
                    continue;
                }

                const need = job.remainingNeed();

                const canFinish = [...need.entries()].every(
                    ([resource, amount]) =>
                        amount <= (work.get(resource) || 0)
                );

                if (canFinish) {
                    for (const [resource, amount] of job.allocation) {
                        work.set(
                            resource,
                            (work.get(resource) || 0) + amount
                        );
                    }

                    finished.add(job.name);
                    changed = true;
                }
            }
        }

        return finished.size === active.length;
    }

    waitForGraph() {
        const holders = new Map();

        for (const resource of this.pool.capacity.keys()) {
            holders.set(resource, new Set());
        }

        for (const job of this.jobs.values()) {
            if (job.state === "ABORTED") {
                continue;
            }

            for (const [resource, amount] of job.allocation) {
                if (amount > 0) {
                    holders.get(resource).add(job.name);
                }
            }
        }

        const graph = new Map();

        for (const jobName of this.jobs.keys()) {
            graph.set(jobName, new Set());
        }

        for (const [jobName, request] of this.waitingRequests) {
            for (const [resource, amount] of request) {
                const available = this.pool.available.get(resource) || 0;

                if (amount > available) {
                    for (const holder of holders.get(resource) || []) {
                        graph.get(jobName).add(holder);
                    }
                }
            }
        }

        return graph;
    }

    detectDeadlock() {
        const graph = this.waitForGraph();
        const visited = new Set();
        const activePath = new Set();
        const deadlocked = new Set();

        const visit = (node, path) => {
            if (activePath.has(node)) {
                const index = path.indexOf(node);

                for (let i = index; i < path.length; i++) {
                    deadlocked.add(path[i]);
                }

                return;
            }

            if (visited.has(node)) {
                return;
            }

            visited.add(node);
            activePath.add(node);
            path.push(node);

            for (const next of graph.get(node) || []) {
                visit(next, path);
            }

            path.pop();
            activePath.delete(node);
        };

        for (const node of graph.keys()) {
            visit(node, []);
        }

        return deadlocked;
    }

    recover(victimName) {
        const victim = this.jobs.get(victimName);

        if (!victim) {
            throw new Error(`Unknown recovery victim: ${victimName}`);
        }

        const released = victim.removeAllocation();

        this.pool.release(released);
        victim.state = "ABORTED";
        this.waitingRequests.delete(victimName);

        this.emit("recovered", {
            victim: victimName,
            released: Object.fromEntries(released),
        });
    }

    complete(jobName) {
        const job = this.jobs.get(jobName);

        if (!job) {
            throw new Error(`Unknown job: ${jobName}`);
        }

        const released = job.removeAllocation();
        this.pool.release(released);
        job.state = "COMPLETED";

        this.emit("completed", { job: jobName });
    }

    snapshot() {
        return {
            available: this.pool.snapshot(),
            jobs: [...this.jobs.values()].map(job => ({
                name: job.name,
                state: job.state,
                allocation: Object.fromEntries(job.allocation),
                need: Object.fromEntries(job.remainingNeed()),
            })),
            waitFor: Object.fromEntries(
                [...this.waitForGraph()].map(
                    ([job, dependencies]) => [job, [...dependencies]]
                )
            ),
        };
    }
}

function wireDiagnostics(manager) {
    manager.on("allocated", event =>
        console.log("ALLOCATED:", event)
    );

    manager.on("waiting", event =>
        console.log("WAITING:", event)
    );

    manager.on("unsafe-request", event =>
        console.log("REJECTED FOR SAFETY:", event)
    );

    manager.on("released", event =>
        console.log("RELEASED:", event)
    );

    manager.on("recovered", event =>
        console.log("RECOVERY:", event)
    );
}

async function demonstrateEventDrivenDeadlock() {
    console.log("\n=== Event-driven circular wait ===");

    const manager = new DeadlockManager({
        DatabaseConnection: 1,
        ReportLock: 1,
    });

    wireDiagnostics(manager);

    manager.addJob(
        new Job("ReportGenerator", {
            DatabaseConnection: 1,
            ReportLock: 1,
        })
    );

    manager.addJob(
        new Job("DataArchiver", {
            DatabaseConnection: 1,
            ReportLock: 1,
        })
    );

    manager.request("ReportGenerator", {
        DatabaseConnection: 1,
    });

    manager.request("DataArchiver", {
        ReportLock: 1,
    });

    // Promise scheduling makes the example resemble independent asynchronous
    // work units. The manager still owns the resource state synchronously.
    await Promise.resolve();

    manager.request("ReportGenerator", {
        ReportLock: 1,
    });

    manager.request("DataArchiver", {
        DatabaseConnection: 1,
    });

    console.log("Wait-for graph:", manager.snapshot().waitFor);

    const deadlocked = manager.detectDeadlock();
    console.log("Deadlocked jobs:", [...deadlocked]);

    if (deadlocked.size > 0) {
        // Recovery policy chooses the job with the smallest amount of completed
        // resource work. Real systems can use priority, rollback cost, age,
        // transaction size, or business criticality instead.
        const victim = [...deadlocked].sort((a, b) => {
            const aAllocation =
                [...manager.jobs.get(a).allocation.values()]
                    .reduce((sum, value) => sum + value, 0);

            const bAllocation =
                [...manager.jobs.get(b).allocation.values()]
                    .reduce((sum, value) => sum + value, 0);

            return aAllocation - bAllocation;
        })[0];

        console.log("Selected recovery victim:", victim);
        manager.recover(victim);
    }

    console.log("After recovery:", JSON.stringify(manager.snapshot(), null, 2));
}

function demonstratePreventionByOrdering() {
    console.log("\n=== Prevention by global resource ordering ===");

    const order = new Map([
        ["DatabaseConnection", 1],
        ["ReportLock", 2],
    ]);

    function validateAcquisitionOrder(currentResources, requestedResource) {
        const requestedRank = order.get(requestedResource);

        for (const resource of currentResources) {
            if (order.get(resource) > requestedRank) {
                throw new Error(
                    `Ordering violation: cannot request ${requestedResource} ` +
                    `after holding ${resource}`
                );
            }
        }
    }

    validateAcquisitionOrder(
        ["DatabaseConnection"],
        "ReportLock"
    );

    console.log(
        "The acquisition-order rule prevents a process from holding a "
        + "higher-ranked resource while requesting a lower-ranked resource."
    );
}

function demonstrateBankerSafety() {
    console.log("\n=== Avoidance with a safety check ===");

    const manager = new DeadlockManager({
        A: 10,
        B: 5,
        C: 7,
    });

    manager.addJob(new Job("P0", { A: 7, B: 5, C: 3 }));
    manager.addJob(new Job("P1", { A: 3, B: 2, C: 2 }));
    manager.addJob(new Job("P2", { A: 9, B: 0, C: 2 }));
    manager.addJob(new Job("P3", { A: 2, B: 2, C: 2 }));
    manager.addJob(new Job("P4", { A: 4, B: 3, C: 3 }));

    manager.request("P0", { A: 0, B: 1, C: 0 });
    manager.request("P1", { A: 2, B: 0, C: 0 });
    manager.request("P2", { A: 3, B: 0, C: 2 });
    manager.request("P3", { A: 2, B: 1, C: 1 });
    manager.request("P4", { A: 0, B: 0, C: 2 });

    console.log("Current state is safe:", manager.isSafeState());

    const accepted = manager.request(
        "P1",
        { A: 1, B: 1, C: 2 },
        { avoid: true }
    );

    console.log("Safety-checked request accepted:", accepted);
}

async function main() {
    console.log("DEADLOCKS IN CONCURRENT RESOURCE SYSTEMS");

    console.log("\n=== Coffman conditions ===");
    console.log(
        "Mutual exclusion: a non-shareable resource can have only one holder."
    );
    console.log(
        "Hold and wait: a job holds resources while requesting additional ones."
    );
    console.log(
        "No preemption: resources are not forcibly removed from a holder."
    );
    console.log(
        "Circular wait: each member of a cycle waits for another member."
    );

    await demonstrateEventDrivenDeadlock();
    demonstratePreventionByOrdering();
    demonstrateBankerSafety();

    console.log(
        "\nPrevention changes acquisition rules. Avoidance evaluates future "
        + "safety before granting requests. Detection searches for cycles after "
        + "the system is allowed to proceed. Recovery changes process state and "
        + "releases resources so progress can resume."
    );
}

main().catch(error => {
    console.error("Fatal error:", error.message);
    process.exitCode = 1;
});
