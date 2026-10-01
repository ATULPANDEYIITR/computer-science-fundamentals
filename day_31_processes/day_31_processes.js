"use strict";

/*
 * Processes: Process Concept, PCB, Process States, and Process Lifecycle
 *
 * This Node.js program models operating-system process-management concepts
 * using JavaScript classes, Maps, Sets, queues, events, and asynchronous
 * event-driven behavior.
 *
 * It deliberately models the kernel's process-management logic rather than
 * creating real operating-system processes.
 */

const ProcessState = Object.freeze({
    NEW: "NEW",
    READY: "READY",
    RUNNING: "RUNNING",
    BLOCKED: "BLOCKED",
    TERMINATED: "TERMINATED"
});

const EventType = Object.freeze({
    CREATE: "CREATE",
    DISPATCH: "DISPATCH",
    PREEMPT: "PREEMPT",
    BLOCK: "BLOCK",
    WAKE: "WAKE",
    EXIT: "EXIT",
    WAIT: "WAIT"
});

const VALID_TRANSITIONS = Object.freeze({
    [ProcessState.NEW]: new Set([
        ProcessState.READY,
        ProcessState.TERMINATED
    ]),
    [ProcessState.READY]: new Set([
        ProcessState.RUNNING,
        ProcessState.TERMINATED
    ]),
    [ProcessState.RUNNING]: new Set([
        ProcessState.READY,
        ProcessState.BLOCKED,
        ProcessState.TERMINATED
    ]),
    [ProcessState.BLOCKED]: new Set([
        ProcessState.READY,
        ProcessState.TERMINATED
    ]),
    [ProcessState.TERMINATED]: new Set()
});

class CPUContext {
    constructor() {
        this.programCounter = 0;
        this.stackPointer = 1000;
        this.basePointer = 1000;
        this.registers = {
            R0: 0,
            R1: 0,
            R2: 0,
            R3: 0
        };
        this.flags = 0;
    }

    snapshot() {
        return {
            programCounter: this.programCounter,
            stackPointer: this.stackPointer,
            basePointer: this.basePointer,
            registers: { ...this.registers },
            flags: this.flags
        };
    }
}

class PCB {
    constructor({
        pid,
        parentPid = null,
        name,
        priority = 5,
        cpuBurst = 5,
        createdAt
    }) {
        this.pid = pid;
        this.parentPid = parentPid;
        this.name = name;
        this.state = ProcessState.NEW;

        this.priority = priority;
        this.timeSlice = 3;
        this.remainingBurst = cpuBurst;

        this.cpu = new CPUContext();

        this.children = new Set();
        this.exitCode = null;

        this.pendingIO = null;
        this.waitingForChild = null;

        this.ownedResources = new Set();

        this.cpuTicks = 0;
        this.readyTicks = 0;
        this.blockedTicks = 0;
        this.contextSwitches = 0;

        this.createdAt = createdAt;
        this.startedAt = null;
        this.terminatedAt = null;

        this.stateHistory = [
            {
                tick: createdAt,
                state: ProcessState.NEW
            }
        ];
    }

    recordState(tick, newState) {
        this.state = newState;
        this.stateHistory.push({
            tick,
            state: newState
        });
    }
}

class ProcessManager extends EventTarget {
    constructor() {
        super();

        this.pcbs = new Map();
        this.readyQueue = [];
        this.blocked = new Map();
        this.resources = new Map();

        this.currentPid = null;
        this.nextPid = 1;
        this.tick = 0;
        this.contextSwitchCount = 0;
        this.events = [];
    }

    log(type, pid, detail) {
        const event = {
            tick: this.tick,
            type,
            pid,
            detail
        };

        this.events.push(event);

        // EventTarget provides a JavaScript-specific event-driven view of
        // process lifecycle changes without requiring external packages.
        this.dispatchEvent(
            new CustomEvent("process-event", {
                detail: event
            })
        );
    }

    getPCB(pid) {
        const pcb = this.pcbs.get(pid);

        if (!pcb) {
            throw new Error(`Unknown PID ${pid}`);
        }

        return pcb;
    }

    validatePriority(priority) {
        if (!Number.isInteger(priority) || priority < 1 || priority > 10) {
            throw new RangeError("Priority must be an integer from 1 through 10.");
        }
    }

    createProcess({
        name,
        parentPid = null,
        priority = 5,
        cpuBurst = 5
    }) {
        if (typeof name !== "string" || name.trim() === "") {
            throw new TypeError("Process name must be a non-empty string.");
        }

        this.validatePriority(priority);

        if (!Number.isInteger(cpuBurst) || cpuBurst <= 0) {
            throw new RangeError("CPU burst must be a positive integer.");
        }

        if (parentPid !== null) {
            const parent = this.getPCB(parentPid);

            if (parent.state === ProcessState.TERMINATED) {
                throw new Error("A terminated process cannot create a child.");
            }
        }

        const pid = this.nextPid++;

        const pcb = new PCB({
            pid,
            parentPid,
            name,
            priority,
            cpuBurst,
            createdAt: this.tick
        });

        this.pcbs.set(pid, pcb);

        this.log(
            EventType.CREATE,
            pid,
            `Created process "${name}".`
        );

        if (parentPid !== null) {
            this.getPCB(parentPid).children.add(pid);
        }

        this.transition(pid, ProcessState.READY, "Process admitted.");

        return pid;
    }

    transition(pid, newState, reason) {
        const pcb = this.getPCB(pid);
        const oldState = pcb.state;

        if (!VALID_TRANSITIONS[oldState].has(newState)) {
            throw new Error(
                `Illegal transition: ${oldState} -> ${newState} for PID ${pid}.`
            );
        }

        pcb.recordState(this.tick, newState);

        if (newState === ProcessState.READY) {
            this.readyQueue.push(pid);
        }

        if (newState === ProcessState.TERMINATED) {
            pcb.terminatedAt = this.tick;
        }

        this.log(
            EventType.WAKE,
            pid,
            `${oldState} -> ${newState}: ${reason}`
        );
    }

    transitionWithoutQueue(pid, newState) {
        const pcb = this.getPCB(pid);
        const oldState = pcb.state;

        if (!VALID_TRANSITIONS[oldState].has(newState)) {
            throw new Error(
                `Illegal transition: ${oldState} -> ${newState} for PID ${pid}.`
            );
        }

        pcb.recordState(this.tick, newState);
    }

    dispatch() {
        if (this.currentPid !== null) {
            return this.currentPid;
        }

        if (this.readyQueue.length === 0) {
            return null;
        }

        // Sorting a small educational queue makes the scheduling policy
        // explicit. Lower priority numbers represent higher urgency here.
        this.readyQueue.sort((a, b) => {
            const left = this.getPCB(a);
            const right = this.getPCB(b);

            return (
                left.priority - right.priority ||
                left.createdAt - right.createdAt
            );
        });

        const pid = this.readyQueue.shift();
        const pcb = this.getPCB(pid);

        this.transitionWithoutQueue(pid, ProcessState.RUNNING);

        this.currentPid = pid;

        if (pcb.startedAt === null) {
            pcb.startedAt = this.tick;
        }

        pcb.contextSwitches += 1;
        this.contextSwitchCount += 1;

        this.log(
            EventType.DISPATCH,
            pid,
            `PID ${pid} is now running on the CPU.`
        );

        return pid;
    }

    preempt(reason = "time slice expired") {
        if (this.currentPid === null) {
            return;
        }

        const pid = this.currentPid;

        this.transitionWithoutQueue(pid, ProcessState.READY);
        this.readyQueue.push(pid);
        this.currentPid = null;

        this.log(EventType.PREEMPT, pid, reason);
    }

    blockCurrent(ioDevice) {
        if (this.currentPid === null) {
            throw new Error("There is no running process.");
        }

        if (typeof ioDevice !== "string" || ioDevice.trim() === "") {
            throw new TypeError("I/O device must be a non-empty string.");
        }

        const pid = this.currentPid;
        const pcb = this.getPCB(pid);

        this.transitionWithoutQueue(pid, ProcessState.BLOCKED);

        pcb.pendingIO = ioDevice;

        if (!this.blocked.has(ioDevice)) {
            this.blocked.set(ioDevice, new Set());
        }

        this.blocked.get(ioDevice).add(pid);
        this.currentPid = null;

        this.log(
            EventType.BLOCK,
            pid,
            `PID ${pid} is waiting for ${ioDevice}.`
        );
    }

    completeIO(ioDevice) {
        const waiting = this.blocked.get(ioDevice);

        if (!waiting) {
            return [];
        }

        const awakened = [];

        for (const pid of waiting) {
            const pcb = this.getPCB(pid);

            if (pcb.state !== ProcessState.BLOCKED) {
                continue;
            }

            pcb.pendingIO = null;

            this.transitionWithoutQueue(
                pid,
                ProcessState.READY
            );

            this.readyQueue.push(pid);
            awakened.push(pid);

            this.log(
                EventType.WAKE,
                pid,
                `${ioDevice} completed; process returned to READY.`
            );
        }

        this.blocked.delete(ioDevice);

        return awakened;
    }

    terminate(pid, exitCode = 0) {
        const pcb = this.getPCB(pid);

        if (pcb.state === ProcessState.TERMINATED) {
            return;
        }

        if (this.currentPid === pid) {
            this.currentPid = null;
        }

        this.readyQueue = this.readyQueue.filter(
            candidate => candidate !== pid
        );

        for (const waiting of this.blocked.values()) {
            waiting.delete(pid);
        }

        // Releasing resources before marking the process dead prevents the
        // resource table from retaining ownership by a terminated process.
        for (const resourceId of [...pcb.ownedResources]) {
            this.releaseResource(pid, resourceId);
        }

        this.transitionWithoutQueue(
            pid,
            ProcessState.TERMINATED
        );

        pcb.exitCode = exitCode;
        pcb.terminatedAt = this.tick;

        this.log(
            EventType.EXIT,
            pid,
            `Process terminated with exit code ${exitCode}.`
        );

        if (pcb.parentPid !== null) {
            const parent = this.pcbs.get(pcb.parentPid);

            if (
                parent &&
                parent.state === ProcessState.BLOCKED &&
                (
                    parent.waitingForChild === null ||
                    parent.waitingForChild === pid
                )
            ) {
                parent.waitingForChild = null;

                this.transitionWithoutQueue(
                    parent.pid,
                    ProcessState.READY
                );

                this.readyQueue.push(parent.pid);

                this.log(
                    EventType.WAKE,
                    parent.pid,
                    `Child PID ${pid} terminated.`
                );
            }
        }
    }

    waitForChild(parentPid, childPid = null) {
        const parent = this.getPCB(parentPid);

        if (parent.state === ProcessState.TERMINATED) {
            throw new Error("A terminated process cannot wait.");
        }

        if (childPid !== null) {
            if (!parent.children.has(childPid)) {
                throw new Error(
                    `PID ${childPid} is not a child of PID ${parentPid}.`
                );
            }

            if (this.getPCB(childPid).state === ProcessState.TERMINATED) {
                return;
            }
        }

        parent.waitingForChild = childPid;

        if (this.currentPid === parentPid) {
            this.transitionWithoutQueue(
                parentPid,
                ProcessState.BLOCKED
            );

            this.currentPid = null;
        }

        this.log(
            EventType.WAIT,
            parentPid,
            `Waiting for child ${childPid ?? "any child"}.`
        );
    }

    addResource(resourceId, resourceType) {
        if (this.resources.has(resourceId)) {
            throw new Error(`Resource ${resourceId} already exists.`);
        }

        this.resources.set(resourceId, {
            id: resourceId,
            type: resourceType,
            ownerPid: null
        });
    }

    acquireResource(pid, resourceId) {
        const pcb = this.getPCB(pid);
        const resource = this.resources.get(resourceId);

        if (!resource) {
            throw new Error(`Unknown resource ${resourceId}.`);
        }

        if (resource.ownerPid === null) {
            resource.ownerPid = pid;
            pcb.ownedResources.add(resourceId);
            return true;
        }

        return resource.ownerPid === pid;
    }

    releaseResource(pid, resourceId) {
        const pcb = this.getPCB(pid);
        const resource = this.resources.get(resourceId);

        if (!resource) {
            throw new Error(`Unknown resource ${resourceId}.`);
        }

        if (resource.ownerPid !== pid) {
            throw new Error(
                `PID ${pid} does not own resource ${resourceId}.`
            );
        }

        resource.ownerPid = null;
        pcb.ownedResources.delete(resourceId);
    }

    cpuTick() {
        if (this.currentPid === null) {
            this.dispatch();
        }

        if (this.currentPid === null) {
            this.tick += 1;
            return null;
        }

        const pid = this.currentPid;
        const pcb = this.getPCB(pid);

        pcb.cpuTicks += 1;
        pcb.remainingBurst -= 1;

        pcb.cpu.programCounter += 4;
        pcb.cpu.registers.R0 += 1;

        this.tick += 1;

        if (pcb.remainingBurst <= 0) {
            this.terminate(pid, 0);
            return pid;
        }

        if (
            pcb.name.toLowerCase().includes("io") &&
            pcb.cpuTicks % 4 === 0
        ) {
            this.blockCurrent("disk");
            return pid;
        }

        if (pcb.cpuTicks % pcb.timeSlice === 0) {
            this.preempt();
        }

        return pid;
    }

    run(maxTicks = 50) {
        if (!Number.isInteger(maxTicks) || maxTicks <= 0) {
            throw new RangeError("maxTicks must be positive.");
        }

        for (let i = 0; i < maxTicks; i += 1) {
            const active = [...this.pcbs.values()].some(
                pcb => pcb.state !== ProcessState.TERMINATED
            );

            if (!active) {
                break;
            }

            this.cpuTick();

            if (this.tick % 3 === 0) {
                this.completeIO("disk");
            }
        }
    }

    processTree(pid, depth = 0) {
        const pcb = this.getPCB(pid);
        const result = [
            `${"  ".repeat(depth)}${pcb.pid} ${pcb.name} [${pcb.state}]`
        ];

        for (const childPid of [...pcb.children].sort((a, b) => a - b)) {
            result.push(
                ...this.processTree(childPid, depth + 1)
            );
        }

        return result;
    }

    lifecycle(pid) {
        const pcb = this.getPCB(pid);

        return pcb.stateHistory.map(
            entry => `t=${entry.tick}: ${entry.state}`
        );
    }

    validateInvariants() {
        const running = [...this.pcbs.values()].filter(
            pcb => pcb.state === ProcessState.RUNNING
        );

        if (running.length > 1) {
            throw new Error(
                "Single-CPU scheduler cannot have multiple running processes."
            );
        }

        if (
            running.length === 0 &&
            this.currentPid !== null
        ) {
            throw new Error(
                "currentPid refers to no RUNNING process."
            );
        }

        if (
            running.length === 1 &&
            running[0].pid !== this.currentPid
        ) {
            throw new Error(
                "PCB running state disagrees with currentPid."
            );
        }

        const readySet = new Set(this.readyQueue);

        for (const pcb of this.pcbs.values()) {
            if (
                pcb.state === ProcessState.READY &&
                !readySet.has(pcb.pid)
            ) {
                throw new Error(
                    `READY PID ${pcb.pid} is missing from the ready queue.`
                );
            }

            if (
                pcb.state !== ProcessState.READY &&
                readySet.has(pcb.pid)
            ) {
                throw new Error(
                    `PID ${pcb.pid} is queued but not READY.`
                );
            }
        }

        for (const resource of this.resources.values()) {
            if (resource.ownerPid !== null) {
                const owner = this.getPCB(resource.ownerPid);

                if (!owner.ownedResources.has(resource.id)) {
                    throw new Error(
                        `Resource ${resource.id} has inconsistent ownership.`
                    );
                }
            }
        }
    }
}

function printPCB(pcb) {
    console.log({
        pid: pcb.pid,
        name: pcb.name,
        parentPid: pcb.parentPid,
        state: pcb.state,
        priority: pcb.priority,
        remainingBurst: pcb.remainingBurst,
        cpuTicks: pcb.cpuTicks,
        contextSwitches: pcb.contextSwitches,
        cpuContext: pcb.cpu.snapshot(),
        ownedResources: [...pcb.ownedResources]
    });
}

async function demonstrateEventDrivenLifecycle() {
    console.log("\n=== Event-Driven Process Lifecycle ===");

    const manager = new ProcessManager();

    manager.addEventListener("process-event", event => {
        const detail = event.detail;

        if (
            detail.type === EventType.CREATE ||
            detail.type === EventType.EXIT
        ) {
            console.log(
                `[event] t=${detail.tick} PID=${detail.pid} ` +
                `${detail.type}: ${detail.detail}`
            );
        }
    });

    const parent = manager.createProcess({
        name: "application",
        priority: 2,
        cpuBurst: 7
    });

    const ioWorker = manager.createProcess({
        name: "io-worker",
        parentPid: parent,
        priority: 4,
        cpuBurst: 9
    });

    const analytics = manager.createProcess({
        name: "analytics",
        parentPid: parent,
        priority: 3,
        cpuBurst: 5
    });

    console.log("\nInitial process tree:");
    console.log(manager.processTree(parent).join("\n"));

    manager.dispatch();

    if (manager.currentPid === parent) {
        manager.waitForChild(parent, ioWorker);
    }

    console.log(
        `\nParent state after waiting: ${manager.getPCB(parent).state}`
    );

    manager.dispatch();

    for (let i = 0; i < 20; i += 1) {
        manager.cpuTick();

        if (manager.tick % 3 === 0) {
            manager.completeIO("disk");
        }

        if (
            manager.getPCB(ioWorker).state === ProcessState.TERMINATED &&
            manager.getPCB(analytics).state === ProcessState.TERMINATED
        ) {
            break;
        }
    }

    manager.validateInvariants();

    console.log("\nFinal process tree:");
    console.log(manager.processTree(parent).join("\n"));

    console.log("\nPCB snapshots:");

    for (const pid of [parent, ioWorker, analytics]) {
        printPCB(manager.getPCB(pid));
    }

    console.log("\nLifecycle paths:");

    for (const pid of [parent, ioWorker, analytics]) {
        console.log(
            `PID ${pid}: ${manager.lifecycle(pid).join(" -> ")}`
        );
    }

    console.log(
        `\nContext switches: ${manager.contextSwitchCount}`
    );
}

function demonstrateResourceOwnership() {
    console.log("\n=== PCB Resource Ownership ===");

    const manager = new ProcessManager();

    manager.addResource("terminal", "exclusive-output");
    manager.addResource("database", "database-connection");

    const first = manager.createProcess({
        name: "terminal-service",
        priority: 3,
        cpuBurst: 3
    });

    const second = manager.createProcess({
        name: "database-service",
        priority: 4,
        cpuBurst: 3
    });

    console.log(
        "First process owns terminal:",
        manager.acquireResource(first, "terminal")
    );

    console.log(
        "Second process tries terminal:",
        manager.acquireResource(second, "terminal")
    );

    console.log(
        "Second process owns database:",
        manager.acquireResource(second, "database")
    );

    printPCB(manager.getPCB(first));
    printPCB(manager.getPCB(second));

    manager.releaseResource(first, "terminal");

    manager.validateInvariants();

    console.log(
        "Terminal owner after release:",
        manager.resources.get("terminal").ownerPid
    );
}

function demonstrateValidation() {
    console.log("\n=== Lifecycle Validation ===");

    const manager = new ProcessManager();

    const pid = manager.createProcess({
        name: "validation-process",
        priority: 5,
        cpuBurst: 2
    });

    try {
        manager.transition(
            pid,
            ProcessState.BLOCKED,
            "not legal directly from READY"
        );
    } catch (error) {
        console.log("Invalid transition rejected:", error.message);
    }

    manager.validateInvariants();
}

async function main() {
    console.log(
        "PROCESS CONCEPT, PCB, STATES, AND LIFECYCLE"
    );
    console.log("==========================================");

    await demonstrateEventDrivenLifecycle();
    demonstrateResourceOwnership();
    demonstrateValidation();

    console.log("\nSimulation complete.");
}

main().catch(error => {
    console.error("Fatal simulation error:", error.message);
    process.exitCode = 1;
});
