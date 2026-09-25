"use strict";

/*
 * Input and Output Systems
 * =========================
 *
 * Topic:
 *   I/O devices, controllers, interrupts, DMA, and buses
 *
 * This file demonstrates the topic using JavaScript classes, queues,
 * asynchronous execution, events, validation, buffering, and a complete
 * simulated I/O pipeline.
 *
 * It runs with a modern JavaScript runtime such as Node.js.
 */


// ============================================================================
// 1. BASIC INPUT/OUTPUT
// ============================================================================

const readline = require("readline");

function createInputInterface() {
    return readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });
}

function askQuestion(question) {
    const rl = createInputInterface();

    return new Promise((resolve) => {
        rl.question(question, (answer) => {
            rl.close();
            resolve(answer.trim());
        });
    });
}


// ============================================================================
// 2. DEVICE MODEL
// ============================================================================

const DeviceType = Object.freeze({
    INPUT: "INPUT",
    OUTPUT: "OUTPUT",
    STORAGE: "STORAGE",
    NETWORK: "NETWORK",
    MIXED: "MIXED"
});

class Device {
    constructor(name, type, transferRateMBps, latencyMs, blockSize = 4096) {
        if (!name) {
            throw new Error("Device name is required.");
        }

        if (transferRateMBps <= 0) {
            throw new Error("Transfer rate must be positive.");
        }

        if (latencyMs < 0) {
            throw new Error("Latency cannot be negative.");
        }

        this.name = name;
        this.type = type;
        this.transferRateMBps = transferRateMBps;
        this.latencyMs = latencyMs;
        this.blockSize = blockSize;
    }

    describe() {
        return {
            name: this.name,
            type: this.type,
            transferRateMBps: this.transferRateMBps,
            latencyMs: this.latencyMs,
            blockSize: this.blockSize
        };
    }
}


// ============================================================================
// 3. DEVICE CONTROLLER
// ============================================================================

class DeviceController {
    constructor(device) {
        this.device = device;
        this.command = null;
        this.status = "IDLE";
        this.dataRegister = null;
        this.error = null;
    }

    writeCommand(command) {
        const supportedCommands = ["READ", "WRITE"];

        if (!supportedCommands.includes(command)) {
            throw new Error(`Unsupported command: ${command}`);
        }

        this.command = command;
        this.status = "COMMAND_RECEIVED";
        this.error = null;
    }

    writeData(data) {
        if (!Buffer.isBuffer(data)) {
            throw new TypeError("Controller data must be a Buffer.");
        }

        this.dataRegister = data;
        this.status = "DATA_READY";
    }

    execute() {
        if (!this.command) {
            this.status = "ERROR";
            this.error = "No command configured.";
            return;
        }

        this.status = "BUSY";

        if (this.command === "READ") {
            this.dataRegister = Buffer.from("DEVICE-DATA");
            this.status = "COMPLETE";
            return;
        }

        if (this.command === "WRITE") {
            if (!this.dataRegister) {
                this.status = "ERROR";
                this.error = "No write data supplied.";
                return;
            }

            this.status = "COMPLETE";
        }
    }
}


// ============================================================================
// 4. INTERRUPT CONTROLLER
// ============================================================================

class InterruptController {
    constructor() {
        this.pendingInterrupts = [];
    }

    raise(source, priority = 10, metadata = {}) {
        this.pendingInterrupts.push({
            source,
            priority,
            metadata,
            timestamp: Date.now()
        });

        // Smaller numerical priority is treated as more urgent.
        this.pendingInterrupts.sort((a, b) => a.priority - b.priority);
    }

    hasPending() {
        return this.pendingInterrupts.length > 0;
    }

    acknowledge() {
        return this.pendingInterrupts.shift() || null;
    }

    pendingCount() {
        return this.pendingInterrupts.length;
    }
}


// ============================================================================
// 5. POLLING AND INTERRUPT EXAMPLES
// ============================================================================

function pollingSimulation(deviceReadyAfter = 4) {
    let checks = 0;
    let ready = false;

    while (!ready) {
        checks++;

        if (checks >= deviceReadyAfter) {
            ready = true;
        }
    }

    return {
        checks,
        ready
    };
}

function interruptSimulation() {
    const controller = new InterruptController();

    controller.raise("NETWORK_ADAPTER", 2, {
        reason: "packet-arrived"
    });

    return controller.acknowledge();
}


// ============================================================================
// 6. MEMORY MODEL
// ============================================================================

class Memory {
    constructor(size) {
        if (!Number.isInteger(size) || size <= 0) {
            throw new Error("Memory size must be a positive integer.");
        }

        this.data = Buffer.alloc(size);
    }

    validateRange(address, length) {
        if (!Number.isInteger(address) || !Number.isInteger(length)) {
            throw new TypeError("Address and length must be integers.");
        }

        if (address < 0 || length < 0 || address + length > this.data.length) {
            throw new RangeError("Memory access is outside the valid range.");
        }
    }

    write(address, source) {
        if (!Buffer.isBuffer(source)) {
            throw new TypeError("Source must be a Buffer.");
        }

        this.validateRange(address, source.length);
        source.copy(this.data, address);
    }

    read(address, length) {
        this.validateRange(address, length);
        return Buffer.from(this.data.subarray(address, address + length));
    }

    size() {
        return this.data.length;
    }
}


// ============================================================================
// 7. DMA CONTROLLER
// ============================================================================

class DMAController {
    constructor(memory, interruptController) {
        this.memory = memory;
        this.interruptController = interruptController;
        this.busy = false;
        this.bytesTransferred = 0;
    }

    deviceToMemory(deviceData, destinationAddress) {
        if (this.busy) {
            throw new Error("DMA controller is already busy.");
        }

        if (!Buffer.isBuffer(deviceData)) {
            throw new TypeError("Device data must be a Buffer.");
        }

        this.busy = true;

        try {
            this.memory.write(destinationAddress, deviceData);
            this.bytesTransferred = deviceData.length;
        } finally {
            this.busy = false;
        }

        this.interruptController.raise("DMA", 3, {
            bytesTransferred: this.bytesTransferred,
            direction: "DEVICE_TO_MEMORY"
        });
    }

    memoryToDevice(sourceAddress, length) {
        if (this.busy) {
            throw new Error("DMA controller is already busy.");
        }

        this.busy = true;

        let data;

        try {
            data = this.memory.read(sourceAddress, length);
            this.bytesTransferred = length;
        } finally {
            this.busy = false;
        }

        this.interruptController.raise("DMA", 3, {
            bytesTransferred: this.bytesTransferred,
            direction: "MEMORY_TO_DEVICE"
        });

        return data;
    }
}


// ============================================================================
// 8. BUS AND ARBITRATION
// ============================================================================

class Bus {
    constructor(name, bandwidthMBps) {
        if (bandwidthMBps <= 0) {
            throw new Error("Bus bandwidth must be positive.");
        }

        this.name = name;
        this.bandwidthMBps = bandwidthMBps;
        this.owner = null;
    }

    acquire(requester) {
        if (this.owner !== null) {
            return false;
        }

        this.owner = requester;
        return true;
    }

    release(requester) {
        if (this.owner !== requester) {
            throw new Error("Requester does not own this bus.");
        }

        this.owner = null;
    }

    transferTimeSeconds(sizeMB) {
        if (sizeMB < 0) {
            throw new Error("Transfer size cannot be negative.");
        }

        return sizeMB / this.bandwidthMBps;
    }
}


// ============================================================================
// 9. I/O QUEUE
// ============================================================================

class IORequest {
    constructor(id, operation, address, size) {
        if (!Number.isInteger(id) || id <= 0) {
            throw new Error("Request ID must be positive.");
        }

        if (!["READ", "WRITE"].includes(operation)) {
            throw new Error("Unsupported I/O operation.");
        }

        if (address < 0 || size <= 0) {
            throw new Error("Address and size are invalid.");
        }

        this.id = id;
        this.operation = operation;
        this.address = address;
        this.size = size;
    }
}

class IOQueue {
    constructor() {
        this.items = [];
    }

    submit(request) {
        this.items.push(request);
    }

    next() {
        return this.items.shift() || null;
    }

    get length() {
        return this.items.length;
    }
}


// ============================================================================
// 10. BUFFER
// ============================================================================

class IOBuffer {
    constructor(capacity) {
        if (!Number.isInteger(capacity) || capacity <= 0) {
            throw new Error("Buffer capacity must be positive.");
        }

        this.capacity = capacity;
        this.items = [];
    }

    write(data) {
        if (this.items.length >= this.capacity) {
            return false;
        }

        this.items.push(data);
        return true;
    }

    read() {
        return this.items.shift() ?? null;
    }

    get size() {
        return this.items.length;
    }
}


// ============================================================================
// 11. ASYNCHRONOUS I/O
// ============================================================================

function asynchronousIO(durationMs, operation) {
    return new Promise((resolve, reject) => {
        if (durationMs < 0) {
            reject(new Error("Duration cannot be negative."));
            return;
        }

        setTimeout(() => {
            try {
                const result = operation();
                resolve(result);
            } catch (error) {
                reject(error);
            }
        }, durationMs);
    });
}


// ============================================================================
// 12. DEVICE DRIVER
// ============================================================================

class DeviceDriver {
    constructor(controller) {
        this.controller = controller;
    }

    write(data) {
        if (!Buffer.isBuffer(data)) {
            throw new TypeError("Driver expects Buffer data.");
        }

        this.controller.writeCommand("WRITE");
        this.controller.writeData(data);
        this.controller.execute();

        if (this.controller.status !== "COMPLETE") {
            throw new Error(this.controller.error || "Write failed.");
        }
    }

    read() {
        this.controller.writeCommand("READ");
        this.controller.execute();

        if (this.controller.status !== "COMPLETE") {
            throw new Error(this.controller.error || "Read failed.");
        }

        return this.controller.dataRegister;
    }
}


// ============================================================================
// 13. PERFORMANCE MODEL
// ============================================================================

function estimateIOTime({
    sizeMB,
    deviceRateMBps,
    busRateMBps,
    latencyMs
}) {
    if (sizeMB < 0) {
        throw new Error("Data size cannot be negative.");
    }

    if (deviceRateMBps <= 0 || busRateMBps <= 0) {
        throw new Error("Rates must be positive.");
    }

    if (latencyMs < 0) {
        throw new Error("Latency cannot be negative.");
    }

    // For this educational model, the slowest stage limits throughput.
    const effectiveRate = Math.min(deviceRateMBps, busRateMBps);

    return latencyMs / 1000 + sizeMB / effectiveRate;
}


// ============================================================================
// 14. CACHE
// ============================================================================

class LRUCache {
    constructor(capacity) {
        if (!Number.isInteger(capacity) || capacity <= 0) {
            throw new Error("Cache capacity must be positive.");
        }

        this.capacity = capacity;
        this.entries = new Map();
    }

    get(key) {
        if (!this.entries.has(key)) {
            return undefined;
        }

        const value = this.entries.get(key);

        // Map insertion order is used to implement LRU behavior.
        this.entries.delete(key);
        this.entries.set(key, value);

        return value;
    }

    set(key, value) {
        if (this.entries.has(key)) {
            this.entries.delete(key);
        }

        this.entries.set(key, value);

        while (this.entries.size > this.capacity) {
            const oldestKey = this.entries.keys().next().value;
            this.entries.delete(oldestKey);
        }
    }
}


// ============================================================================
// 15. COMPLETE I/O SUBSYSTEM
// ============================================================================

class IOSubsystem {
    constructor() {
        this.memory = new Memory(16 * 1024);
        this.interruptController = new InterruptController();
        this.dma = new DMAController(
            this.memory,
            this.interruptController
        );

        this.bus = new Bus("SYSTEM_BUS", 2000);
        this.queue = new IOQueue();
        this.completed = [];
    }

    submit(request) {
        this.queue.submit(request);
    }

    processRead(request, deviceData) {
        if (request.operation !== "READ") {
            throw new Error("Request must be a READ request.");
        }

        if (request.size !== deviceData.length) {
            throw new Error(
                "Request size does not match device payload size."
            );
        }

        if (!this.bus.acquire("DMA")) {
            throw new Error("System bus is currently busy.");
        }

        try {
            this.dma.deviceToMemory(
                deviceData,
                request.address
            );
        } finally {
            this.bus.release("DMA");
        }

        const interrupt = this.interruptController.acknowledge();

        if (!interrupt || interrupt.source !== "DMA") {
            throw new Error("DMA completion interrupt was not received.");
        }

        this.completed.push({
            requestId: request.id,
            status: "SUCCESS",
            bytesTransferred: deviceData.length
        });
    }

    processNext(deviceData) {
        const request = this.queue.next();

        if (!request) {
            return null;
        }

        if (request.operation === "READ") {
            this.processRead(request, deviceData);
        }

        return request;
    }
}


// ============================================================================
// 16. EVENT-DRIVEN DEVICE
// ============================================================================

class SimulatedNetworkAdapter {
    constructor(interruptController) {
        this.interruptController = interruptController;
        this.packetQueue = [];
    }

    receivePacket(packet) {
        if (!Buffer.isBuffer(packet)) {
            throw new TypeError("Network packet must be a Buffer.");
        }

        this.packetQueue.push(packet);

        // The device does not need the CPU to constantly poll it.
        // It generates an event/interrupt when work is available.
        this.interruptController.raise("NETWORK", 2, {
            packetLength: packet.length
        });
    }

    readPacket() {
        return this.packetQueue.shift() || null;
    }
}


// ============================================================================
// 17. SECURITY VALIDATION
// ============================================================================

function validateDMARequest(memory, address, length) {
    if (!Number.isInteger(address) || !Number.isInteger(length)) {
        throw new TypeError("DMA address and length must be integers.");
    }

    if (address < 0 || length < 0 || address + length > memory.size()) {
        throw new RangeError("DMA request exceeds permitted memory.");
    }

    return true;
}


// ============================================================================
// 18. TESTS
// ============================================================================

function runTests() {
    console.log("\nRunning self-tests...");

    const memory = new Memory(100);
    memory.write(10, Buffer.from("abc"));
    console.assert(
        memory.read(10, 3).toString() === "abc",
        "Memory test failed."
    );

    const interrupts = new InterruptController();

    interrupts.raise("LOW", 5);
    interrupts.raise("HIGH", 1);

    console.assert(
        interrupts.acknowledge().source === "HIGH",
        "Interrupt priority test failed."
    );

    const buffer = new IOBuffer(1);

    console.assert(buffer.write("A"), "Buffer write failed.");
    console.assert(!buffer.write("B"), "Buffer overflow test failed.");
    console.assert(buffer.read() === "A", "Buffer read failed.");
    console.assert(buffer.read() === null, "Empty buffer test failed.");

    const bus = new Bus("TEST", 1000);

    console.assert(
        bus.acquire("CPU"),
        "Bus acquisition failed."
    );

    console.assert(
        !bus.acquire("DMA"),
        "Bus arbitration failed."
    );

    bus.release("CPU");

    const cache = new LRUCache(2);
    cache.set("A", 1);
    cache.set("B", 2);
    cache.get("A");
    cache.set("C", 3);

    console.assert(
        cache.get("B") === undefined,
        "LRU eviction test failed."
    );

    console.log("All self-tests passed.");
}


// ============================================================================
// 19. DEMONSTRATIONS
// ============================================================================

async function main() {
    console.log("INPUT AND OUTPUT SYSTEMS");
    console.log("Devices | Controllers | Interrupts | DMA | Buses");

    const interactive = process.argv.includes("--interactive");

    if (interactive) {
        const name = await askQuestion("Enter your name: ");
        console.log(`Hello, ${name || "Anonymous"}.`);

        const value = await askQuestion("Enter an integer: ");
        const number = Number(value);

        if (Number.isInteger(number)) {
            console.log(`Square: ${number * number}`);
        } else {
            console.log("Invalid integer input.");
        }
    }

    console.log("\n1. DEVICE");

    const ssd = new Device(
        "Educational SSD",
        DeviceType.STORAGE,
        3500,
        0.08
    );

    console.log(ssd.describe());

    console.log("\n2. CONTROLLER");

    const controller = new DeviceController(ssd);
    const driver = new DeviceDriver(controller);

    driver.write(Buffer.from("Operating-system request"));
    console.log("Controller status:", controller.status);

    console.log("Controller read:", driver.read().toString());

    console.log("\n3. POLLING");

    console.log(pollingSimulation());

    console.log("\n4. INTERRUPT");

    console.log(interruptSimulation());

    console.log("\n5. DMA");

    const memory = new Memory(1024);
    const interrupts = new InterruptController();
    const dma = new DMAController(memory, interrupts);

    const payload = Buffer.from("DMA transferred block");

    dma.deviceToMemory(payload, 100);

    console.log(
        "Memory:",
        memory.read(100, payload.length).toString()
    );

    console.log(
        "Interrupt:",
        interrupts.acknowledge()
    );

    console.log("\n6. BUS");

    const bus = new Bus("SYSTEM_BUS", 1000);

    if (bus.acquire("DMA_CONTROLLER")) {
        console.log("DMA acquired bus.");
        console.log(
            "250 MB transfer time:",
            bus.transferTimeSeconds(250),
            "seconds"
        );
        bus.release("DMA_CONTROLLER");
    }

    console.log("\n7. BUFFER");

    const buffer = new IOBuffer(3);

    for (const item of ["A", "B", "C", "D"]) {
        console.log(
            `Write ${item}:`,
            buffer.write(item) ? "accepted" : "buffer full"
        );
    }

    while (buffer.size > 0) {
        console.log("Read:", buffer.read());
    }

    console.log("\n8. I/O QUEUE");

    const queue = new IOQueue();

    queue.submit(new IORequest(1, "READ", 100, 4096));
    queue.submit(new IORequest(2, "WRITE", 200, 8192));
    queue.submit(new IORequest(3, "READ", 500, 16384));

    while (queue.length > 0) {
        const request = queue.next();

        console.log({
            id: request.id,
            operation: request.operation,
            address: request.address,
            size: request.size
        });
    }

    console.log("\n9. ASYNCHRONOUS I/O");

    const start = Date.now();

    const asyncResults = await Promise.all([
        asynchronousIO(100, () => "Storage operation completed"),
        asynchronousIO(50, () => "Network operation completed")
    ]);

    console.log(asyncResults);
    console.log("Elapsed approximately:", Date.now() - start, "ms");

    console.log("\n10. PERFORMANCE");

    console.log(
        "100 MB:",
        estimateIOTime({
            sizeMB: 100,
            deviceRateMBps: 3500,
            busRateMBps: 1000,
            latencyMs: 0.08
        }),
        "seconds"
    );

    console.log("\n11. CACHE");

    const cache = new LRUCache(2);

    cache.set("block-1", "A");
    cache.set("block-2", "B");

    console.log("Cache hit:", cache.get("block-1"));

    cache.set("block-3", "C");

    console.log("Evicted block-2:", cache.get("block-2"));
    console.log("Present block-3:", cache.get("block-3"));

    console.log("\n12. COMPLETE I/O PIPELINE");

    const io = new IOSubsystem();

    const request = new IORequest(
        101,
        "READ",
        4096,
        15
    );

    io.submit(request);

    const deviceData = Buffer.from("Hello I/O World");

    io.processNext(deviceData);

    console.log(
        "Memory result:",
        io.memory.read(4096, deviceData.length).toString()
    );

    console.log("Completions:", io.completed);

    console.log("\n13. NETWORK INTERRUPT");

    const network = new SimulatedNetworkAdapter(
        io.interruptController
    );

    network.receivePacket(Buffer.from("Incoming packet"));

    const networkInterrupt = io.interruptController.acknowledge();

    console.log("Interrupt:", networkInterrupt);

    const packet = network.readPacket();

    console.log("Packet:", packet.toString());

    console.log("\n14. SECURITY VALIDATION");

    try {
        validateDMARequest(io.memory, 4096, 15);
        console.log("Valid DMA request accepted.");

        validateDMARequest(io.memory, -1, 10);
    } catch (error) {
        console.log("Invalid DMA request rejected:", error.message);
    }

    console.log("\n15. SELF-TESTS");

    runTests();

    console.log("\nEducational execution completed.");
}


main().catch((error) => {
    console.error("Fatal I/O simulation error:", error.message);
    process.exitCode = 1;
});
