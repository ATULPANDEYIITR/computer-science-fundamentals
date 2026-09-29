/*
 * Introduction to Operating Systems
 *
 * This standalone JavaScript file demonstrates operating-system concepts
 * through an educational simulation:
 *   - OS responsibilities
 *   - user mode and kernel mode
 *   - system calls
 *   - processes
 *   - scheduling
 *   - memory management
 *   - virtual memory
 *   - interrupts
 *   - file systems
 *   - access control
 *   - operating-system classifications
 *
 * Run with:
 *   node operating_systems.js
 */

"use strict";

// ---------------------------------------------------------------------------
// 1. Basic operating-system concepts
// ---------------------------------------------------------------------------

const PrivilegeMode = Object.freeze({
    USER: "user",
    KERNEL: "kernel"
});

const ProcessState = Object.freeze({
    NEW: "NEW",
    READY: "READY",
    RUNNING: "RUNNING",
    WAITING: "WAITING",
    TERMINATED: "TERMINATED"
});

class Process {
    constructor(pid, name, priority = 5, cpuBurst = 1, memoryKB = 512) {
        if (!Number.isInteger(pid) || pid <= 0) {
            throw new Error("PID must be a positive integer.");
        }

        if (!name) {
            throw new Error("Process name cannot be empty.");
        }

        if (cpuBurst <= 0 || memoryKB <= 0) {
            throw new Error("CPU burst and memory must be positive.");
        }

        this.pid = pid;
        this.name = name;
        this.priority = priority;
        this.cpuBurst = cpuBurst;
        this.remainingCPU = cpuBurst;
        this.memoryKB = memoryKB;
        this.state = ProcessState.NEW;
        this.registers = {};
    }
}

// ---------------------------------------------------------------------------
// 2. Educational operating-system kernel
// ---------------------------------------------------------------------------

class OperatingSystem {
    constructor(name, version, totalMemoryKB = 8192) {
        this.name = name;
        this.version = version;
        this.mode = PrivilegeMode.USER;
        this.totalMemoryKB = totalMemoryKB;
        this.usedMemoryKB = 0;
        this.nextPID = 1;
        this.processTable = new Map();
        this.fileSystem = new Map();
    }

    createProcess(name, options = {}) {
        const memoryKB = options.memoryKB ?? 512;
        const priority = options.priority ?? 5;
        const cpuBurst = options.cpuBurst ?? 1;

        if (this.usedMemoryKB + memoryKB > this.totalMemoryKB) {
            throw new Error("Insufficient simulated memory.");
        }

        const process = new Process(
            this.nextPID++,
            name,
            priority,
            cpuBurst,
            memoryKB
        );

        process.state = ProcessState.READY;

        this.processTable.set(process.pid, process);
        this.usedMemoryKB += memoryKB;

        return process;
    }

    terminateProcess(pid) {
        const process = this.processTable.get(pid);

        if (!process) {
            throw new Error(`Process ${pid} does not exist.`);
        }

        process.state = ProcessState.TERMINATED;
        this.usedMemoryKB -= process.memoryKB;
        this.processTable.delete(pid);
    }

    enterKernel(reason) {
        if (this.mode === PrivilegeMode.KERNEL) {
            throw new Error("Already in kernel mode.");
        }

        console.log(`[MODE] USER -> KERNEL: ${reason}`);
        this.mode = PrivilegeMode.KERNEL;
    }

    leaveKernel() {
        if (this.mode !== PrivilegeMode.KERNEL) {
            throw new Error("Cannot leave kernel mode when not in kernel mode.");
        }

        console.log("[MODE] KERNEL -> USER");
        this.mode = PrivilegeMode.USER;
    }

    /*
     * A system call is a controlled boundary between an application and
     * privileged operating-system functionality.
     */
    systemCall(process, serviceName, serviceFunction) {
        if (!this.processTable.has(process.pid)) {
            throw new Error("Calling process is not managed by this OS.");
        }

        console.log(`\nSystem call: ${serviceName} by PID ${process.pid}`);

        this.enterKernel(serviceName);

        try {
            return serviceFunction();
        } finally {
            // Returning to user mode must happen even if the service fails.
            this.leaveKernel();
        }
    }

    createFile(process, fileName, contents = "") {
        return this.systemCall(process, "create_file", () => {
            if (!fileName || fileName.includes("/")) {
                throw new Error("Invalid file name.");
            }

            if (this.fileSystem.has(fileName)) {
                throw new Error(`File already exists: ${fileName}`);
            }

            this.fileSystem.set(fileName, {
                contents,
                owner: "user",
                permissions: "rw-r--r--"
            });

            return true;
        });
    }

    readFile(process, fileName) {
        return this.systemCall(process, "read_file", () => {
            const file = this.fileSystem.get(fileName);

            if (!file) {
                throw new Error(`File not found: ${fileName}`);
            }

            return file.contents;
        });
    }

    writeFile(process, fileName, contents) {
        return this.systemCall(process, "write_file", () => {
            const file = this.fileSystem.get(fileName);

            if (!file) {
                throw new Error(`File not found: ${fileName}`);
            }

            file.contents = contents;
            return true;
        });
    }
}

// ---------------------------------------------------------------------------
// 3. System-call example
// ---------------------------------------------------------------------------

function demonstrateSystemCalls() {
    console.log("\n=== SYSTEM CALLS ===");

    const os = new OperatingSystem("WebEduOS", "1.0");
    const terminal = os.createProcess("terminal", {
        memoryKB: 512,
        cpuBurst: 2
    });

    os.createFile(
        terminal,
        "notes.txt",
        "An operating system provides controlled services."
    );

    const content = os.readFile(terminal, "notes.txt");
    console.log("File contents:", content);

    os.writeFile(
        terminal,
        "notes.txt",
        "System calls provide a controlled user-to-kernel boundary."
    );

    console.log("Updated contents:", os.readFile(terminal, "notes.txt"));
}

// ---------------------------------------------------------------------------
// 4. User mode and kernel mode
// ---------------------------------------------------------------------------

function demonstratePrivilegeSeparation() {
    console.log("\n=== USER MODE AND KERNEL MODE ===");

    const os = new OperatingSystem("WebEduOS", "1.0");

    console.log("Initial privilege mode:", os.mode);

    try {
        if (os.mode !== PrivilegeMode.KERNEL) {
            throw new Error(
                "A user-mode application cannot directly perform privileged hardware operations."
            );
        }
    } catch (error) {
        console.log("Protected operation rejected:", error.message);
    }

    const application = os.createProcess("application");

    os.systemCall(application, "privileged_service", () => {
        console.log("Kernel performs the protected operation.");
    });
}

// ---------------------------------------------------------------------------
// 5. CPU scheduling
// ---------------------------------------------------------------------------

function firstComeFirstServed(processes) {
    const timeline = [];

    for (const process of processes) {
        process.state = ProcessState.RUNNING;

        timeline.push({
            process: process.name,
            duration: process.cpuBurst
        });

        process.state = ProcessState.READY;
    }

    return timeline;
}

function roundRobin(processes, quantum = 2) {
    if (!Number.isInteger(quantum) || quantum <= 0) {
        throw new Error("Quantum must be a positive integer.");
    }

    const queue = [...processes];
    const timeline = [];

    while (queue.length > 0) {
        const process = queue.shift();

        process.state = ProcessState.RUNNING;

        const executionTime = Math.min(quantum, process.remainingCPU);
        process.remainingCPU -= executionTime;

        timeline.push({
            process: process.name,
            duration: executionTime
        });

        if (process.remainingCPU > 0) {
            process.state = ProcessState.READY;
            queue.push(process);
        } else {
            process.state = ProcessState.TERMINATED;
        }
    }

    return timeline;
}

function demonstrateScheduling() {
    console.log("\n=== CPU SCHEDULING ===");

    const fcfsProcesses = [
        new Process(1, "browser", 5, 5),
        new Process(2, "editor", 5, 2),
        new Process(3, "compiler", 5, 7)
    ];

    console.log("FCFS:");
    console.table(firstComeFirstServed(fcfsProcesses));

    const roundRobinProcesses = [
        new Process(1, "browser", 5, 5),
        new Process(2, "editor", 5, 2),
        new Process(3, "compiler", 5, 7)
    ];

    console.log("Round Robin, quantum=2:");
    console.table(roundRobin(roundRobinProcesses, 2));
}

// ---------------------------------------------------------------------------
// 6. Memory management
// ---------------------------------------------------------------------------

class MemoryManager {
    constructor(totalKB) {
        if (!Number.isInteger(totalKB) || totalKB <= 0) {
            throw new Error("Total memory must be positive.");
        }

        this.totalKB = totalKB;
        this.allocations = new Map();
        this.nextAddress = 0;
    }

    allocate(owner, sizeKB) {
        if (!Number.isInteger(sizeKB) || sizeKB <= 0) {
            throw new Error("Allocation size must be positive.");
        }

        const usedKB = [...this.allocations.values()]
            .reduce((sum, allocation) => sum + allocation.sizeKB, 0);

        if (usedKB + sizeKB > this.totalKB) {
            throw new Error("Not enough memory.");
        }

        const address = this.nextAddress;

        this.allocations.set(owner, {
            address,
            sizeKB
        });

        this.nextAddress += sizeKB;

        return address;
    }

    free(owner) {
        if (!this.allocations.has(owner)) {
            throw new Error(`No allocation for ${owner}`);
        }

        this.allocations.delete(owner);
    }

    status() {
        const usedKB = [...this.allocations.values()]
            .reduce((sum, allocation) => sum + allocation.sizeKB, 0);

        return {
            usedKB,
            freeKB: this.totalKB - usedKB,
            allocations: [...this.allocations.entries()]
        };
    }
}

function demonstrateMemoryManagement() {
    console.log("\n=== MEMORY MANAGEMENT ===");

    const memory = new MemoryManager(4096);

    console.log("Browser address:", memory.allocate("browser", 1024));
    console.log("Compiler address:", memory.allocate("compiler", 2048));
    console.log(memory.status());

    memory.free("browser");

    console.log("After freeing browser memory:");
    console.log(memory.status());

    try {
        memory.allocate("large-job", 5000);
    } catch (error) {
        console.log("Expected failure:", error.message);
    }
}

// ---------------------------------------------------------------------------
// 7. Virtual memory and paging
// ---------------------------------------------------------------------------

class PageTable {
    constructor(pageSize = 4096) {
        if (!Number.isInteger(pageSize) || pageSize <= 0) {
            throw new Error("Page size must be positive.");
        }

        this.pageSize = pageSize;
        this.mapping = new Map();
    }

    map(virtualPage, physicalFrame) {
        if (virtualPage < 0 || physicalFrame < 0) {
            throw new Error("Page and frame numbers must not be negative.");
        }

        this.mapping.set(virtualPage, physicalFrame);
    }

    translate(virtualAddress) {
        if (!Number.isInteger(virtualAddress) || virtualAddress < 0) {
            throw new Error("Virtual address must be non-negative.");
        }

        const virtualPage = Math.floor(virtualAddress / this.pageSize);
        const offset = virtualAddress % this.pageSize;

        if (!this.mapping.has(virtualPage)) {
            throw new Error(`Page fault for virtual page ${virtualPage}.`);
        }

        const physicalFrame = this.mapping.get(virtualPage);

        return physicalFrame * this.pageSize + offset;
    }
}

function demonstrateVirtualMemory() {
    console.log("\n=== VIRTUAL MEMORY ===");

    const pageTable = new PageTable();

    pageTable.map(0, 5);
    pageTable.map(1, 8);

    const virtualAddress = 4096 + 123;

    console.log("Virtual address:", virtualAddress);
    console.log("Physical address:", pageTable.translate(virtualAddress));

    try {
        pageTable.translate(8192);
    } catch (error) {
        console.log("Expected page fault:", error.message);
    }
}

// ---------------------------------------------------------------------------
// 8. Interrupts
// ---------------------------------------------------------------------------

function simulateInterrupt(os, interruptName) {
    console.log(`\nInterrupt received: ${interruptName}`);

    const previousMode = os.mode;

    // Hardware causes execution to enter a privileged handler.
    os.mode = PrivilegeMode.KERNEL;

    console.log(`Interrupt handler running in ${os.mode} mode.`);
    console.log("Kernel processes the event.");

    os.mode = previousMode;

    console.log(`Execution returned to ${os.mode} mode.`);
}

// ---------------------------------------------------------------------------
// 9. Context switching
// ---------------------------------------------------------------------------

function contextSwitch(currentProcess, nextProcess) {
    currentProcess.registers = {
        instructionPointer: 1000,
        stackPointer: 8000,
        generalRegister: 42
    };

    console.log(
        `Saved ${currentProcess.name}:`,
        currentProcess.registers
    );

    nextProcess.registers = {
        instructionPointer: 2500,
        stackPointer: 9000,
        generalRegister: 7
    };

    console.log(
        `Restored ${nextProcess.name}:`,
        nextProcess.registers
    );
}

// ---------------------------------------------------------------------------
// 10. Asynchronous I/O
// ---------------------------------------------------------------------------

function simulatedDiskRead(fileName, delayMilliseconds = 50) {
    /*
     * Real device I/O can take substantially longer than CPU operations.
     * Asynchronous APIs allow other work to proceed while waiting.
     */
    return new Promise((resolve, reject) => {
        if (!fileName) {
            reject(new Error("File name is required."));
            return;
        }

        setTimeout(() => {
            resolve(`Data returned from ${fileName}`);
        }, delayMilliseconds);
    });
}

async function demonstrateAsynchronousIO() {
    console.log("\n=== ASYNCHRONOUS I/O ===");

    console.log("Starting disk read...");

    const readPromise = simulatedDiskRead("database.db");

    console.log("CPU can perform other work while I/O is pending.");

    const data = await readPromise;

    console.log("I/O completed:", data);

    try {
        await simulatedDiskRead("");
    } catch (error) {
        console.log("I/O validation error:", error.message);
    }
}

// ---------------------------------------------------------------------------
// 11. Access control
// ---------------------------------------------------------------------------

class AccessController {
    constructor() {
        this.permissions = new Map([
            ["alice", new Set(["read", "write"])],
            ["bob", new Set(["read"])],
            ["guest", new Set()]
        ]);
    }

    canPerform(user, operation) {
        const permissions = this.permissions.get(user);

        if (!permissions) {
            return false;
        }

        return permissions.has(operation);
    }
}

function demonstrateAccessControl() {
    console.log("\n=== PROTECTION AND ACCESS CONTROL ===");

    const access = new AccessController();

    for (const user of ["alice", "bob", "guest"]) {
        console.log(
            `${user} write permission:`,
            access.canPerform(user, "write")
        );
    }
}

// ---------------------------------------------------------------------------
// 12. Operating-system classifications
// ---------------------------------------------------------------------------

function explainOperatingSystemTypes() {
    console.log("\n=== OPERATING-SYSTEM TYPES ===");

    const types = {
        Batch: "Executes groups of jobs with little interactive input.",
        Multiprogramming:
            "Keeps multiple programs available so CPU time can be used efficiently.",
        Multitasking:
            "Shares processor time among active tasks to provide interactive execution.",
        Multiprocessing:
            "Uses multiple processors or cores for parallel execution.",
        RealTime:
            "Targets workloads where response-time constraints are important.",
        Distributed:
            "Coordinates computation and resources across networked machines.",
        Network:
            "Provides communication and resource-sharing services.",
        Embedded:
            "Targets dedicated hardware with constrained resources.",
        Mobile:
            "Targets mobile devices with power, radio, sensor, and touch constraints.",
        Desktop:
            "Targets general-purpose interactive personal-computing workloads.",
        Server:
            "Targets long-running services, networking, concurrency, and shared resources."
    };

    for (const [type, description] of Object.entries(types)) {
        console.log(`${type}: ${description}`);
    }
}

// ---------------------------------------------------------------------------
// 13. Kernel architectures
// ---------------------------------------------------------------------------

function explainKernelArchitectures() {
    console.log("\n=== KERNEL ARCHITECTURES ===");

    const architectures = {
        "Monolithic kernel":
            "Many core services operate in kernel space, allowing efficient internal communication.",
        "Microkernel":
            "Keeps the privileged kernel core small and places more services outside it.",
        "Hybrid kernel":
            "Combines structural ideas associated with monolithic and microkernel designs.",
        "Modular kernel":
            "Supports separable kernel components that can be loaded or configured as modules.",
        "Layered design":
            "Organizes functionality into layers with defined responsibilities and interfaces."
    };

    for (const [name, description] of Object.entries(architectures)) {
        console.log(`${name}: ${description}`);
    }
}

// ---------------------------------------------------------------------------
// 14. Main end-to-end demonstration
// ---------------------------------------------------------------------------

async function main() {
    console.log("=".repeat(72));
    console.log("INTRODUCTION TO OPERATING SYSTEMS");
    console.log("=".repeat(72));

    console.log(
        "\nAn operating system manages hardware resources and provides " +
        "controlled services to application software."
    );

    demonstrateSystemCalls();
    demonstratePrivilegeSeparation();
    demonstrateScheduling();
    demonstrateMemoryManagement();
    demonstrateVirtualMemory();

    const os = new OperatingSystem("WebEduOS", "1.0");

    simulateInterrupt(os, "network packet received");

    const processA = new Process(100, "process-A", 5, 2);
    const processB = new Process(101, "process-B", 5, 3);

    contextSwitch(processA, processB);

    await demonstrateAsynchronousIO();

    demonstrateAccessControl();
    explainOperatingSystemTypes();
    explainKernelArchitectures();

    // -----------------------------------------------------------------------
    // A small complete workflow
    // -----------------------------------------------------------------------

    console.log("\n=== COMPLETE WORKFLOW ===");

    const system = new OperatingSystem("WebEduOS", "2.0", 4096);

    const browser = system.createProcess("browser", {
        memoryKB: 1024,
        cpuBurst: 5
    });

    const compiler = system.createProcess("compiler", {
        memoryKB: 1536,
        cpuBurst: 7
    });

    system.createFile(
        browser,
        "build.log",
        "Compilation started.\n"
    );

    system.writeFile(
        compiler,
        "build.log",
        "Compilation started.\nCompilation completed.\n"
    );

    console.log(system.readFile(browser, "build.log"));

    simulateInterrupt(system, "timer tick");

    console.log("Processes:", [...system.processTable.values()].map(
        process => ({
            pid: process.pid,
            name: process.name,
            state: process.state,
            memoryKB: process.memoryKB
        })
    ));

    system.terminateProcess(browser.pid);
    system.terminateProcess(compiler.pid);

    console.log("Used memory after termination:", system.usedMemoryKB);
    console.log("\nJavaScript operating-system demonstrations completed.");
}

main().catch(error => {
    console.error("Fatal demonstration error:", error.message);
    process.exitCode = 1;
});
