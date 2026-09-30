'use strict';

/*
 * Operating System Architecture
 *
 * JavaScript-specific model of:
 *   - Monolithic kernel boundaries
 *   - Microkernel IPC
 *   - Hybrid kernel service placement
 *   - Layered architecture validation
 *
 * The implementation uses Node.js features such as EventEmitter, asynchronous
 * message delivery, classes, Maps, Sets, Promises, and structured validation.
 *
 * Run with:
 *   node os-architecture.js
 */

const { EventEmitter } = require('node:events');
const { performance } = require('node:perf_hooks');


class ArchitectureError extends Error {
    constructor(message) {
        super(message);
        this.name = 'ArchitectureError';
    }
}


class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = 'ValidationError';
    }
}


class MemoryManager {
    constructor(totalBytes) {
        if (!Number.isInteger(totalBytes) || totalBytes <= 0) {
            throw new ValidationError('Memory capacity must be a positive integer');
        }

        this.totalBytes = totalBytes;
        this.allocations = new Map();
    }

    get usedBytes() {
        let total = 0;

        for (const bytes of this.allocations.values()) {
            total += bytes;
        }

        return total;
    }

    get freeBytes() {
        return this.totalBytes - this.usedBytes;
    }

    allocate(owner, bytes) {
        if (!owner) {
            throw new ValidationError('Memory owner is required');
        }

        if (!Number.isInteger(bytes) || bytes <= 0) {
            throw new ValidationError('Allocation size must be positive');
        }

        if (this.allocations.has(owner)) {
            throw new ArchitectureError(`Owner already has memory: ${owner}`);
        }

        if (bytes > this.freeBytes) {
            throw new RangeError(
                `Insufficient memory: requested=${bytes}, free=${this.freeBytes}`
            );
        }

        this.allocations.set(owner, bytes);
    }

    release(owner) {
        if (!this.allocations.has(owner)) {
            throw new ArchitectureError(`Unknown memory owner: ${owner}`);
        }

        this.allocations.delete(owner);
    }
}


class ProcessManager {
    constructor(memoryManager) {
        this.memory = memoryManager;
        this.processes = new Map();
        this.nextPid = 1000;
    }

    createProcess(name, memoryBytes) {
        if (typeof name !== 'string' || name.trim() === '') {
            throw new ValidationError('Process name cannot be empty');
        }

        const pid = this.nextPid++;
        const owner = `process:${pid}`;

        this.memory.allocate(owner, memoryBytes);

        const process = {
            pid,
            name,
            state: 'ready',
            memoryBytes
        };

        this.processes.set(pid, process);
        return process;
    }

    terminateProcess(pid) {
        const process = this.processes.get(pid);

        if (!process) {
            throw new RangeError(`Unknown PID ${pid}`);
        }

        this.memory.release(`process:${pid}`);
        process.state = 'terminated';
        this.processes.delete(pid);
    }
}


class FileSystem {
    constructor() {
        this.files = new Map();
    }

    create(path, content = '') {
        if (!path.startsWith('/')) {
            throw new ValidationError('File path must be absolute');
        }

        if (this.files.has(path)) {
            throw new Error(`File already exists: ${path}`);
        }

        this.files.set(path, content);
    }

    read(path) {
        if (!this.files.has(path)) {
            throw new Error(`File does not exist: ${path}`);
        }

        return this.files.get(path);
    }

    write(path, content) {
        if (!this.files.has(path)) {
            throw new Error(`File does not exist: ${path}`);
        }

        this.files.set(path, content);
    }
}


class DeviceManager {
    constructor() {
        this.devices = new Map([
            ['console0', { type: 'terminal', online: true }],
            ['disk0', { type: 'storage', online: true }],
            ['net0', { type: 'network', online: true }]
        ]);
    }

    write(deviceName, data) {
        const device = this.devices.get(deviceName);

        if (!device) {
            throw new Error(`Unknown device: ${deviceName}`);
        }

        if (!device.online) {
            throw new Error(`Device is offline: ${deviceName}`);
        }

        if (typeof data !== 'string' || data.length === 0) {
            throw new ValidationError('Device data cannot be empty');
        }

        return {
            device: deviceName,
            bytes: Buffer.byteLength(data, 'utf8'),
            accepted: true
        };
    }
}


/*
 * Monolithic kernel:
 *
 * The central object owns process, filesystem, and device services. Calls are
 * ordinary method calls rather than messages sent to isolated service servers.
 */
class MonolithicKernel {
    constructor() {
        this.memory = new MemoryManager(64 * 1024 * 1024);
        this.processManager = new ProcessManager(this.memory);
        this.fileSystem = new FileSystem();
        this.deviceManager = new DeviceManager();
    }

    systemCallCreateProcess(name, memoryBytes) {
        return this.processManager.createProcess(name, memoryBytes);
    }

    systemCallFileCreate(path, content) {
        return this.fileSystem.create(path, content);
    }

    systemCallDeviceWrite(device, data) {
        return this.deviceManager.write(device, data);
    }
}


/*
 * IPC service model:
 *
 * EventEmitter represents an asynchronous communication mechanism. The
 * Promise returned by request() makes the message lifecycle explicit:
 *
 * client -> message queue -> service handler -> response -> client
 */
class IPCBus extends EventEmitter {
    constructor() {
        super();
        this.services = new Map();
        this.requestCounter = 0;
    }

    registerService(name, handler) {
        if (this.services.has(name)) {
            throw new ArchitectureError(`Service already registered: ${name}`);
        }

        this.services.set(name, handler);
    }

    request(sender, serviceName, operation, payload) {
        if (!this.services.has(serviceName)) {
            return Promise.reject(
                new Error(`No IPC service named ${serviceName}`)
            );
        }

        const requestId = ++this.requestCounter;

        const message = Object.freeze({
            requestId,
            sender,
            receiver: serviceName,
            operation,
            payload
        });

        this.emit('message', message);

        return Promise.resolve()
            .then(() => this.services.get(serviceName)(message))
            .then(result => ({
                requestId,
                service: serviceName,
                result
            }));
    }
}


class FileServer {
    constructor() {
        this.fileSystem = new FileSystem();
    }

    handle(message) {
        switch (message.operation) {
            case 'create':
                this.fileSystem.create(
                    message.payload.path,
                    message.payload.content ?? ''
                );
                return { status: 'created' };

            case 'read':
                return {
                    status: 'ok',
                    content: this.fileSystem.read(message.payload.path)
                };

            case 'write':
                this.fileSystem.write(
                    message.payload.path,
                    message.payload.content
                );
                return { status: 'written' };

            default:
                throw new ValidationError(
                    `Unsupported filesystem operation: ${message.operation}`
                );
        }
    }
}


class DeviceServer {
    constructor() {
        this.deviceManager = new DeviceManager();
    }

    handle(message) {
        if (message.operation !== 'write') {
            throw new ValidationError(
                `Unsupported device operation: ${message.operation}`
            );
        }

        return this.deviceManager.write(
            message.payload.device,
            message.payload.data
        );
    }
}


/*
 * Microkernel model:
 *
 * The kernel-facing IPC bus is deliberately separate from the filesystem and
 * device services. The client cannot directly access either service's state.
 */
class Microkernel {
    constructor() {
        this.ipc = new IPCBus();

        this.fileServer = new FileServer();
        this.deviceServer = new DeviceServer();

        this.ipc.registerService(
            'filesystem',
            message => this.fileServer.handle(message)
        );

        this.ipc.registerService(
            'device',
            message => this.deviceServer.handle(message)
        );
    }

    async runWorkflow() {
        const createResponse = await this.ipc.request(
            'shell',
            'filesystem',
            'create',
            {
                path: '/home/atul/notes.txt',
                content: 'microkernel service boundary'
            }
        );

        const readResponse = await this.ipc.request(
            'shell',
            'filesystem',
            'read',
            {
                path: '/home/atul/notes.txt'
            }
        );

        const deviceResponse = await this.ipc.request(
            'shell',
            'device',
            'write',
            {
                device: 'console0',
                data: 'message delivered through IPC'
            }
        );

        return {
            createResponse,
            readResponse,
            deviceResponse
        };
    }
}


/*
 * Hybrid kernel:
 *
 * This model deliberately puts scheduling/process management on the kernel
 * side while placing selected storage functionality behind IPC.
 */
class HybridKernel {
    constructor() {
        this.memory = new MemoryManager(128 * 1024 * 1024);
        this.processManager = new ProcessManager(this.memory);

        this.ipc = new IPCBus();
        this.storageServer = new FileServer();

        this.ipc.registerService(
            'storage-service',
            message => this.storageServer.handle(message)
        );
    }

    createProcess(name, memoryBytes) {
        return this.processManager.createProcess(name, memoryBytes);
    }

    storageRequest(operation, payload) {
        return this.ipc.request(
            'kernel-storage-client',
            'storage-service',
            operation,
            payload
        );
    }
}


/*
 * Layered architecture:
 *
 * The Map stores layer levels and dependency relationships. A dependency is
 * legal only when a higher layer depends on a lower layer. This makes the
 * layering rule executable instead of merely descriptive.
 */
class LayeredArchitecture {
    constructor() {
        this.layers = new Map([
            ['hardware', 0],
            ['kernel', 1],
            ['system-services', 2],
            ['runtime', 3],
            ['applications', 4]
        ]);

        this.dependencies = new Map([
            ['hardware', new Set()],
            ['kernel', new Set(['hardware'])],
            ['system-services', new Set(['kernel'])],
            ['runtime', new Set(['system-services'])],
            ['applications', new Set(['runtime'])]
        ]);
    }

    addDependency(source, target) {
        if (!this.layers.has(source)) {
            throw new ValidationError(`Unknown source layer: ${source}`);
        }

        if (!this.layers.has(target)) {
            throw new ValidationError(`Unknown target layer: ${target}`);
        }

        const sourceLevel = this.layers.get(source);
        const targetLevel = this.layers.get(target);

        if (targetLevel >= sourceLevel) {
            throw new ArchitectureError(
                `${source} cannot depend on ${target}; ` +
                'dependencies must point downward'
            );
        }

        this.dependencies.get(source).add(target);
    }

    validate() {
        const errors = [];

        for (const [source, targets] of this.dependencies.entries()) {
            for (const target of targets) {
                if (this.layers.get(target) >= this.layers.get(source)) {
                    errors.push(`${source} -> ${target}`);
                }
            }
        }

        return errors;
    }
}


async function demonstrateMonolithic() {
    console.log('\n=== MONOLITHIC KERNEL ===');

    const kernel = new MonolithicKernel();

    const process = kernel.systemCallCreateProcess(
        'editor',
        4 * 1024 * 1024
    );

    kernel.systemCallFileCreate(
        '/documents/design.txt',
        'direct kernel subsystem call'
    );

    const deviceResult = kernel.systemCallDeviceWrite(
        'console0',
        'editor started'
    );

    console.log(`Process PID: ${process.pid}`);
    console.log(
        `Filesystem content: ${kernel.fileSystem.read('/documents/design.txt')}`
    );
    console.log(
        `Device result: ${deviceResult.bytes} bytes accepted`
    );
}


async function demonstrateMicrokernel() {
    console.log('\n=== MICROKERNEL ===');

    const kernel = new Microkernel();

    kernel.ipc.on('message', message => {
        console.log(
            `IPC message ${message.requestId}: ` +
            `${message.sender} -> ${message.receiver} ` +
            `(${message.operation})`
        );
    });

    const workflow = await kernel.runWorkflow();

    console.log(
        `Filesystem response: ${workflow.createResponse.result.status}`
    );
    console.log(
        `Read response: ${workflow.readResponse.result.content}`
    );
    console.log(
        `Device response: ${workflow.deviceResponse.result.accepted}`
    );
}


async function demonstrateHybrid() {
    console.log('\n=== HYBRID KERNEL ===');

    const kernel = new HybridKernel();

    const process = kernel.createProcess(
        'compiler',
        8 * 1024 * 1024
    );

    await kernel.storageRequest(
        'create',
        {
            path: '/build/artifact.txt',
            content: 'hybrid service boundary'
        }
    );

    const response = await kernel.storageRequest(
        'read',
        {
            path: '/build/artifact.txt'
        }
    );

    console.log(`Kernel process PID: ${process.pid}`);
    console.log(`Storage service response: ${response.result.content}`);
}


function demonstrateLayering() {
    console.log('\n=== LAYERED ARCHITECTURE ===');

    const architecture = new LayeredArchitecture();

    console.log(
        `Initial validation errors: ${architecture.validate().length}`
    );

    try {
        architecture.addDependency(
            'applications',
            'kernel'
        );

        console.log('Application-to-kernel dependency accepted');
    } catch (error) {
        console.log(
            `Layering rule rejected direct dependency: ${error.message}`
        );
    }

    console.log(
        'Valid dependency example: applications -> runtime -> system-services'
    );
}


function demonstrateIsolation() {
    console.log('\n=== FAILURE ISOLATION ===');

    const kernel = new Microkernel();

    return kernel.ipc
        .request(
            'shell',
            'filesystem',
            'read',
            {
                path: '/missing.txt'
            }
        )
        .catch(error => {
            console.log(`Filesystem service failed: ${error.message}`);
        })
        .then(() => {
            return kernel.ipc.request(
                'shell',
                'device',
                'write',
                {
                    device: 'console0',
                    data: 'device service still available'
                }
            );
        })
        .then(response => {
            console.log(
                `Independent device service: ${response.result.accepted}`
            );
        });
}


function demonstrateValidation() {
    console.log('\n=== VALIDATION AND SECURITY BOUNDARIES ===');

    const kernel = new Microkernel();

    const invalidRequests = [
        kernel.ipc.request(
            'untrusted-client',
            'filesystem',
            'delete-all',
            {}
        ),
        kernel.ipc.request(
            'untrusted-client',
            'device',
            'write',
            {
                device: 'unknown0',
                data: 'unauthorized operation'
            }
        )
    ];

    return Promise.allSettled(invalidRequests).then(results => {
        for (const result of results) {
            if (result.status === 'rejected') {
                console.log(`Rejected request: ${result.reason.message}`);
            }
        }
    });
}


function measureDirectPath(iterations) {
    const kernel = new MonolithicKernel();

    kernel.systemCallFileCreate(
        '/tmp/benchmark.txt',
        'x'
    );

    const start = performance.now();

    for (let i = 0; i < iterations; i += 1) {
        kernel.fileSystem.read('/tmp/benchmark.txt');
    }

    return performance.now() - start;
}


async function measureIPCPath(iterations) {
    const kernel = new Microkernel();

    await kernel.ipc.request(
        'setup',
        'filesystem',
        'create',
        {
            path: '/tmp/benchmark.txt',
            content: 'x'
        }
    );

    const start = performance.now();

    for (let i = 0; i < iterations; i += 1) {
        await kernel.ipc.request(
            'benchmark',
            'filesystem',
            'read',
            {
                path: '/tmp/benchmark.txt'
            }
        );
    }

    return performance.now() - start;
}


async function demonstratePerformancePath() {
    console.log('\n=== SOFTWARE PATH TIMING ===');

    const iterations = 10000;

    const directTime = measureDirectPath(iterations);
    const ipcTime = await measureIPCPath(iterations);

    console.log(
        `Direct subsystem path: ${directTime.toFixed(3)} ms`
    );

    console.log(
        `IPC-style path: ${ipcTime.toFixed(3)} ms`
    );

    console.log(
        'These are Node.js model timings, not real operating-system benchmarks.'
    );
}


async function main() {
    console.log('OPERATING SYSTEM ARCHITECTURE LAB');
    console.log('=================================');

    await demonstrateMonolithic();
    await demonstrateMicrokernel();
    await demonstrateHybrid();
    demonstrateLayering();
    await demonstrateIsolation();
    await demonstrateValidation();
    await demonstratePerformancePath();

    console.log('\n=== ARCHITECTURAL RELATIONSHIPS ===');
    console.log(
        'Monolithic: privileged subsystems communicate primarily through direct calls.'
    );
    console.log(
        'Microkernel: user-space services communicate with clients through IPC.'
    );
    console.log(
        'Hybrid: selected facilities remain integrated while others use service boundaries.'
    );
    console.log(
        'Layered: components are organized around controlled dependency levels.'
    );

    console.log('\nLab completed successfully.');
}


main().catch(error => {
    console.error(`Fatal architecture-lab error: ${error.message}`);
    process.exitCode = 1;
});
