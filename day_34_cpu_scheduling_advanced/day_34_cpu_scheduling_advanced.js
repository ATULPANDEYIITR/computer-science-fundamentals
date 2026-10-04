/**
 * Advanced CPU Scheduling Model
 *
 * Focus:
 * - Multilevel Queue Scheduling
 * - Multilevel Feedback Queue Scheduling
 * - Context switching
 * - Event-driven process state transitions
 * - Reviewable scheduling decisions and metrics
 *
 * Runtime:
 *   Node.js 18+
 *
 * No external packages are required.
 */

"use strict";

const ProcessState = Object.freeze({
    NEW: "NEW",
    READY: "READY",
    RUNNING: "RUNNING",
    BLOCKED: "BLOCKED",
    TERMINATED: "TERMINATED"
});

const QueuePolicy = Object.freeze({
    FCFS: "FCFS",
    ROUND_ROBIN: "ROUND_ROBIN",
    PRIORITY: "PRIORITY"
});

class Process {
    constructor({
        pid,
        arrivalTime,
        bursts,
        basePriority,
        queueLevel = 0
    }) {
        if (!pid) throw new Error("Process ID is required.");
        if (arrivalTime < 0) {
            throw new Error("Arrival time cannot be negative.");
        }
        if (!Array.isArray(bursts) || bursts.length === 0) {
            throw new Error(`Process ${pid} needs CPU bursts.`);
        }

        for (const burst of bursts) {
            if (!Number.isInteger(burst.cpu) || burst.cpu <= 0) {
                throw new Error(
                    `CPU burst for ${pid} must be a positive integer.`
                );
            }

            if (!Number.isInteger(burst.io) || burst.io < 0) {
                throw new Error(
                    `I/O duration for ${pid} must be a non-negative integer.`
                );
            }
        }

        this.pid = pid;
        this.arrivalTime = arrivalTime;
        this.bursts = bursts;
        this.basePriority = basePriority;

        this.queueLevel = queueLevel;
        this.state = ProcessState.NEW;
        this.burstIndex = 0;
        this.remainingCpu = bursts[0].cpu;

        this.firstRunTime = null;
        this.completionTime = null;
        this.responseTime = null;
        this.waitingTime = 0;
        this.readySince = null;
        this.cpuTime = 0;
        this.preemptions = 0;
        this.demotions = 0;
        this.promotions = 0;
    }

    get currentBurst() {
        return this.bursts[this.burstIndex];
    }

    get completed() {
        return this.state === ProcessState.TERMINATED;
    }

    beginWaiting(now) {
        if (this.readySince === null) {
            this.readySince = now;
        }
    }

    endWaiting(now) {
        if (this.readySince !== null) {
            this.waitingTime += now - this.readySince;
            this.readySince = null;
        }
    }
}

class EventLog {
    constructor() {
        this.events = [];
    }

    append(start, end, type, pid = null, metadata = {}) {
        if (end <= start) return;

        this.events.push({
            start,
            end,
            type,
            pid,
            metadata
        });
    }

    print() {
        console.log("\nCPU EVENT TIMELINE");
        console.log("-".repeat(82));

        for (const event of this.events) {
            const subject = event.pid ?? "";
            const queue =
                event.metadata.queue !== undefined
                    ? `Q${event.metadata.queue}`
                    : "";

            console.log(
                `[${String(event.start).padStart(3)} -> ` +
                `${String(event.end).padStart(3)}] ` +
                `${event.type.padEnd(16)} ` +
                `${subject.padEnd(12)} ${queue}`
            );
        }
    }
}

class MLFQScheduler {
    constructor({
        processes,
        queues,
        contextSwitchCost = 1,
        boostInterval = 15
    }) {
        if (!queues.length) {
            throw new Error("MLFQ requires at least one queue.");
        }

        this.processes = new Map(
            processes.map(process => [process.pid, process])
        );

        this.queues = queues;
        this.readyQueues = queues.map(() => []);
        this.contextSwitchCost = contextSwitchCost;
        this.boostInterval = boostInterval;

        this.blocked = new Map();
        this.running = null;
        this.time = 0;
        this.quantumUsed = 0;

        this.contextSwitches = 0;
        this.contextSwitchTime = 0;

        this.events = new EventLog();
    }

    enqueue(process, now, front = false) {
        process.state = ProcessState.READY;
        process.beginWaiting(now);

        const queue = this.readyQueues[process.queueLevel];

        if (front) {
            queue.unshift(process);
        } else {
            queue.push(process);
        }
    }

    admitArrivals() {
        for (const process of this.processes.values()) {
            if (
                process.state === ProcessState.NEW &&
                process.arrivalTime <= this.time
            ) {
                this.enqueue(process, this.time);
            }
        }
    }

    releaseIO() {
        for (const [pid, readyAt] of this.blocked) {
            if (readyAt <= this.time) {
                const process = this.processes.get(pid);

                this.blocked.delete(pid);
                process.burstIndex += 1;
                process.remainingCpu =
                    process.currentBurst.cpu;

                this.enqueue(process, this.time);
            }
        }
    }

    highestReadyQueue() {
        for (let index = 0; index < this.readyQueues.length; index++) {
            if (this.readyQueues[index].length > 0) {
                return index;
            }
        }

        return null;
    }

    chooseProcess() {
        for (let level = 0; level < this.readyQueues.length; level++) {
            const queue = this.readyQueues[level];

            if (queue.length === 0) continue;

            const configuration = this.queues[level];

            if (configuration.policy === QueuePolicy.PRIORITY) {
                let selectedIndex = 0;

                for (let i = 1; i < queue.length; i++) {
                    if (
                        queue[i].basePriority <
                        queue[selectedIndex].basePriority
                    ) {
                        selectedIndex = i;
                    }
                }

                return queue.splice(selectedIndex, 1)[0];
            }

            return queue.shift();
        }

        return null;
    }

    priorityBoost() {
        if (
            this.boostInterval === null ||
            this.time === 0 ||
            this.time % this.boostInterval !== 0
        ) {
            return;
        }

        for (let level = 1; level < this.readyQueues.length; level++) {
            const oldQueue = this.readyQueues[level];

            while (oldQueue.length > 0) {
                const process = oldQueue.shift();
                process.queueLevel = 0;
                process.promotions += 1;
                this.readyQueues[0].push(process);
            }
        }

        this.events.append(
            this.time,
            this.time,
            "PRIORITY_BOOST"
        );
    }

    preemptForHigherQueue() {
        if (!this.running) return;

        const highest = this.highestReadyQueue();

        if (
            highest !== null &&
            highest < this.running.queueLevel
        ) {
            const process = this.running;

            process.preemptions += 1;
            this.enqueue(process, this.time);

            this.running = null;
            this.quantumUsed = 0;

            this.events.append(
                this.time,
                this.time,
                "HIGHER_QUEUE_PREEMPT",
                process.pid,
                { queue: process.queueLevel }
            );
        }
    }

    dispatch(process) {
        process.endWaiting(this.time);

        if (process.firstRunTime === null) {
            process.firstRunTime = this.time;
            process.responseTime =
                this.time - process.arrivalTime;
        }

        process.state = ProcessState.RUNNING;
        this.running = process;
        this.quantumUsed = 0;

        this.contextSwitches += 1;

        if (this.contextSwitchCost > 0) {
            const start = this.time;
            this.time += this.contextSwitchCost;
            this.contextSwitchTime += this.contextSwitchCost;

            this.events.append(
                start,
                this.time,
                "CONTEXT_SWITCH",
                process.pid,
                { queue: process.queueLevel }
            );
        }
    }

    completeCpuBurst() {
        const process = this.running;

        process.burstIndex += 1;

        if (process.burstIndex >= process.bursts.length) {
            process.state = ProcessState.TERMINATED;
            process.completionTime = this.time;
            this.running = null;
            this.quantumUsed = 0;

            return;
        }

        const ioDuration =
            process.bursts[process.burstIndex - 1].io;

        if (ioDuration > 0) {
            process.state = ProcessState.BLOCKED;

            this.blocked.set(
                process.pid,
                this.time + ioDuration
            );

            // I/O-bound behavior indicates that the process yielded the CPU
            // voluntarily. Moving it upward favors interactive responsiveness.
            if (process.queueLevel > 0) {
                process.queueLevel -= 1;
                process.promotions += 1;
            }
        } else {
            process.remainingCpu =
                process.currentBurst.cpu;

            this.enqueue(process, this.time);
        }

        this.running = null;
        this.quantumUsed = 0;
    }

    executeTick() {
        if (!this.running) return;

        const process = this.running;
        process.remainingCpu -= 1;
        process.cpuTime += 1;
        this.quantumUsed += 1;

        this.events.append(
            this.time,
            this.time + 1,
            "CPU",
            process.pid,
            { queue: process.queueLevel }
        );

        this.time += 1;

        if (process.remainingCpu === 0) {
            this.completeCpuBurst();
            return;
        }

        const configuration =
            this.queues[process.queueLevel];

        if (
            configuration.policy === QueuePolicy.ROUND_ROBIN &&
            this.quantumUsed >= configuration.quantum
        ) {
            if (
                process.queueLevel <
                this.queues.length - 1
            ) {
                process.queueLevel += 1;
                process.demotions += 1;
            }

            process.preemptions += 1;
            this.enqueue(process, this.time);

            this.running = null;
            this.quantumUsed = 0;
        }
    }

    run(maxTime = 10000) {
        while (this.time <= maxTime) {
            const finished = [...this.processes.values()]
                .every(process => process.completed);

            if (finished) break;

            this.admitArrivals();
            this.releaseIO();
            this.priorityBoost();
            this.preemptForHigherQueue();

            if (!this.running) {
                const selected = this.chooseProcess();

                if (selected) {
                    this.dispatch(selected);
                    continue;
                }

                this.events.append(
                    this.time,
                    this.time + 1,
                    "IDLE"
                );

                this.time += 1;
                continue;
            }

            this.executeTick();
        }

        if (this.time > maxTime) {
            throw new Error(
                "Scheduler exceeded its safety time limit."
            );
        }

        return this;
    }

    metrics() {
        const processes = [...this.processes.values()];
        const completed = processes.filter(
            process => process.completionTime !== null
        );

        if (!completed.length) {
            return {};
        }

        const average = values =>
            values.reduce((sum, value) => sum + value, 0) /
            values.length;

        const turnaround = completed.map(
            process =>
                process.completionTime -
                process.arrivalTime
        );

        const response = completed.map(
            process => process.responseTime ?? 0
        );

        return {
            averageWaitingTime: average(
                completed.map(process => process.waitingTime)
            ),
            averageTurnaroundTime: average(turnaround),
            averageResponseTime: average(response),
            cpuUtilizationPercent:
                (
                    completed.reduce(
                        (sum, process) =>
                            sum + process.cpuTime,
                        0
                    ) / Math.max(1, this.time)
                ) * 100,
            contextSwitches: this.contextSwitches,
            contextSwitchTime: this.contextSwitchTime
        };
    }
}

class MLQScheduler {
    /**
     * MLQ differs from MLFQ because queue membership is static.
     * A CPU-intensive process does not automatically move to a lower queue.
     */
    constructor({ processes, queues }) {
        this.processes = processes;
        this.queues = queues;
        this.readyQueues = queues.map(() => []);
        this.time = 0;
        this.running = null;
        this.events = new EventLog();
    }

    addArrivals() {
        for (const process of this.processes) {
            if (
                process.state === ProcessState.NEW &&
                process.arrivalTime <= this.time
            ) {
                process.state = ProcessState.READY;
                process.beginWaiting(this.time);
                this.readyQueues[process.queueLevel].push(process);
            }
        }
    }

    choose() {
        for (let level = 0; level < this.readyQueues.length; level++) {
            const queue = this.readyQueues[level];

            if (!queue.length) continue;

            const configuration = this.queues[level];

            if (configuration.policy === QueuePolicy.PRIORITY) {
                queue.sort(
                    (a, b) =>
                        a.basePriority - b.basePriority
                );
            }

            return queue.shift();
        }

        return null;
    }

    run() {
        while (
            this.processes.some(
                process => !process.completed
            )
        ) {
            this.addArrivals();

            if (!this.running) {
                this.running = this.choose();

                if (!this.running) {
                    this.events.append(
                        this.time,
                        this.time + 1,
                        "IDLE"
                    );
                    this.time += 1;
                    continue;
                }

                this.running.endWaiting(this.time);
                this.running.state = ProcessState.RUNNING;

                if (this.running.firstRunTime === null) {
                    this.running.firstRunTime = this.time;
                    this.running.responseTime =
                        this.time -
                        this.running.arrivalTime;
                }
            }

            this.running.remainingCpu -= 1;
            this.running.cpuTime += 1;

            this.events.append(
                this.time,
                this.time + 1,
                "CPU",
                this.running.pid,
                { queue: this.running.queueLevel }
            );

            this.time += 1;

            if (this.running.remainingCpu === 0) {
                this.running.state =
                    ProcessState.TERMINATED;

                this.running.completionTime =
                    this.time;

                this.running = null;
            }
        }

        return this;
    }
}

function createWorkload() {
    return [
        new Process({
            pid: "TERMINAL",
            arrivalTime: 0,
            bursts: [
                { cpu: 2, io: 5 },
                { cpu: 1, io: 4 },
                { cpu: 2, io: 0 }
            ],
            basePriority: 1
        }),

        new Process({
            pid: "API",
            arrivalTime: 1,
            bursts: [
                { cpu: 3, io: 3 },
                { cpu: 2, io: 4 },
                { cpu: 2, io: 0 }
            ],
            basePriority: 2
        }),

        new Process({
            pid: "BUILD",
            arrivalTime: 0,
            bursts: [
                { cpu: 12, io: 0 }
            ],
            basePriority: 6
        }),

        new Process({
            pid: "BACKUP",
            arrivalTime: 2,
            bursts: [
                { cpu: 15, io: 0 }
            ],
            basePriority: 9
        }),

        new Process({
            pid: "LOGGER",
            arrivalTime: 4,
            bursts: [
                { cpu: 1, io: 6 },
                { cpu: 1, io: 5 },
                { cpu: 1, io: 0 }
            ],
            basePriority: 3
        })
    ];
}

function cloneProcesses(processes) {
    return processes.map(
        process =>
            new Process({
                pid: process.pid,
                arrivalTime: process.arrivalTime,
                bursts: process.bursts.map(
                    burst => ({ ...burst })
                ),
                basePriority: process.basePriority,
                queueLevel: process.queueLevel
            })
    );
}

function printMetrics(metrics) {
    console.log("\nSCHEDULING METRICS");
    console.log("-".repeat(42));

    for (const [name, value] of Object.entries(metrics)) {
        const formatted =
            typeof value === "number"
                ? value.toFixed(2)
                : value;

        console.log(
            `${name.padEnd(30)} ${formatted}`
        );
    }
}

function demonstrateMLFQ() {
    console.log("=".repeat(82));
    console.log("EVENT-DRIVEN MLFQ CPU SCHEDULER");
    console.log("=".repeat(82));

    const processes = createWorkload();

    const scheduler = new MLFQScheduler({
        processes,
        queues: [
            {
                name: "Interactive",
                policy: QueuePolicy.ROUND_ROBIN,
                quantum: 2
            },
            {
                name: "Standard",
                policy: QueuePolicy.ROUND_ROBIN,
                quantum: 4
            },
            {
                name: "Batch",
                policy: QueuePolicy.FCFS
            }
        ],
        contextSwitchCost: 1,
        boostInterval: 15
    });

    scheduler.run();
    scheduler.events.print();
    printMetrics(scheduler.metrics());

    console.log("\nPROCESS STATES");
    console.log("-".repeat(82));

    for (const process of processes) {
        console.log(
            `${process.pid.padEnd(12)}` +
            `state=${process.state.padEnd(11)} ` +
            `cpu=${String(process.cpuTime).padStart(3)} ` +
            `wait=${String(process.waitingTime).padStart(3)} ` +
            `preempt=${String(process.preemptions).padStart(2)} ` +
            `demote=${String(process.demotions).padStart(2)} ` +
            `promote=${String(process.promotions).padStart(2)}`
        );
    }
}

function demonstrateMLQ() {
    console.log("\n");
    console.log("=".repeat(82));
    console.log("STATIC MULTILEVEL QUEUE MODEL");
    console.log("=".repeat(82));

    const processes = [
        new Process({
            pid: "SYSTEM",
            arrivalTime: 0,
            bursts: [{ cpu: 4, io: 0 }],
            basePriority: 0,
            queueLevel: 0
        }),
        new Process({
            pid: "INTERACTIVE",
            arrivalTime: 0,
            bursts: [{ cpu: 6, io: 0 }],
            basePriority: 2,
            queueLevel: 1
        }),
        new Process({
            pid: "BATCH",
            arrivalTime: 0,
            bursts: [{ cpu: 10, io: 0 }],
            basePriority: 5,
            queueLevel: 2
        })
    ];

    const scheduler = new MLQScheduler({
        processes,
        queues: [
            {
                name: "System",
                policy: QueuePolicy.PRIORITY
            },
            {
                name: "Interactive",
                policy: QueuePolicy.ROUND_ROBIN,
                quantum: 2
            },
            {
                name: "Batch",
                policy: QueuePolicy.FCFS
            }
        ]
    });

    scheduler.run();
    scheduler.events.print();
}

function demonstrateValidation() {
    console.log("\n");
    console.log("=".repeat(82));
    console.log("VALIDATION");
    console.log("=".repeat(82));

    try {
        new Process({
            pid: "BAD",
            arrivalTime: -1,
            bursts: [{ cpu: 2, io: 0 }],
            basePriority: 1
        });
    } catch (error) {
        console.log(`Invalid arrival rejected: ${error.message}`);
    }

    try {
        new Process({
            pid: "BAD",
            arrivalTime: 0,
            bursts: [{ cpu: 0, io: 0 }],
            basePriority: 1
        });
    } catch (error) {
        console.log(`Invalid CPU burst rejected: ${error.message}`);
    }
}

function main() {
    demonstrateMLFQ();
    demonstrateMLQ();
    demonstrateValidation();
}

main();
