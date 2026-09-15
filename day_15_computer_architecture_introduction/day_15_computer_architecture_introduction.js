/*
 * Computer Architecture Introduction
 * ===================================
 *
 * This file complements the Python implementation with JavaScript examples
 * covering CPU concepts, instruction execution, memory, caches, asynchronous
 * I/O, event-driven behavior, performance calculations and a small CPU model.
 *
 * It uses only standard JavaScript features and can run with:
 *
 *     node computer_architecture_introduction.js
 *
 * Browser-related concepts are demonstrated through platform-independent
 * abstractions rather than requiring a particular HTML page.
 */

"use strict";


// ============================================================================
// 1. BASIC REPRESENTATION
// ============================================================================

function printSection(title) {
    console.log("\n" + "=".repeat(76));
    console.log(title);
    console.log("=".repeat(76));
}

function demonstrateNumberRepresentation() {
    printSection("1. Binary, Hexadecimal and Fixed-Width Values");

    const values = [0, 1, 2, 10, 42, 127, 128, 255];

    for (const value of values) {
        const binary = value.toString(2).padStart(8, "0");
        const hexadecimal = value.toString(16).toUpperCase().padStart(2, "0");

        console.log(
            `${value.toString().padStart(3)} decimal = ` +
            `${binary} binary = 0x${hexadecimal} hexadecimal`
        );
    }

    function toUnsigned8(value) {
        // JavaScript numbers are not inherently 8-bit integers.
        // Masking explicitly creates the behavior of an 8-bit datapath.
        return value & 0xFF;
    }

    console.log("\n8-bit wraparound:");
    console.log("250 + 10 =", toUnsigned8(250 + 10));

    function toSigned8(value) {
        const unsignedValue = value & 0xFF;
        return unsignedValue & 0x80
            ? unsignedValue - 0x100
            : unsignedValue;
    }

    console.log("\nTwo's-complement interpretation:");
    for (const value of [0, 1, 127, 128, 129, 255]) {
        console.log(
            `0b${value.toString(2).padStart(8, "0")} -> ${toSigned8(value)}`
        );
    }
}


// ============================================================================
// 2. REGISTERS
// ============================================================================

class Register {
    constructor(name, width = 8) {
        if (width <= 0 || !Number.isInteger(width)) {
            throw new RangeError("Register width must be a positive integer.");
        }

        this.name = name;
        this.width = width;
        this.value = 0;
    }

    write(value) {
        if (this.width <= 32) {
            const mask = this.width === 32
                ? 0xFFFFFFFF
                : (2 ** this.width) - 1;

            this.value = value & mask;
        } else {
            this.value = BigInt(value);
        }
    }

    read() {
        return this.value;
    }
}


// ============================================================================
// 3. ALU
// ============================================================================

class ALU {
    add(a, b) {
        const rawResult = a + b;

        return {
            result: rawResult & 0xFF,
            carry: rawResult > 0xFF
        };
    }

    subtract(a, b) {
        const rawResult = a - b;

        return {
            result: rawResult & 0xFF,
            borrow: rawResult < 0
        };
    }

    and(a, b) {
        return (a & b) & 0xFF;
    }

    or(a, b) {
        return (a | b) & 0xFF;
    }

    xor(a, b) {
        return (a ^ b) & 0xFF;
    }

    shiftLeft(value, amount) {
        return (value << amount) & 0xFF;
    }

    shiftRight(value, amount) {
        return (value & 0xFF) >>> amount;
    }
}

function demonstrateALU() {
    printSection("2. Arithmetic Logic Unit");

    const alu = new ALU();

    console.log("100 + 50 =", alu.add(100, 50));
    console.log("250 + 20 =", alu.add(250, 20));
    console.log(
        "0b10101010 AND 0b11001100 =",
        alu.and(0b10101010, 0b11001100)
    );
    console.log(
        "0b10101010 XOR 0b11001100 =",
        alu.xor(0b10101010, 0b11001100)
    );
}


// ============================================================================
// 4. MEMORY
// ============================================================================

class ByteMemory {
    constructor(size) {
        if (!Number.isInteger(size) || size <= 0) {
            throw new RangeError("Memory size must be positive.");
        }

        this.data = new Uint8Array(size);
    }

    validateAddress(address) {
        if (!Number.isInteger(address) ||
            address < 0 ||
            address >= this.data.length) {
            throw new RangeError(`Invalid memory address: ${address}`);
        }
    }

    readByte(address) {
        this.validateAddress(address);
        return this.data[address];
    }

    writeByte(address, value) {
        this.validateAddress(address);

        if (!Number.isInteger(value) || value < 0 || value > 255) {
            throw new RangeError("Byte value must be an integer from 0 to 255.");
        }

        this.data[address] = value;
    }

    readUint16BE(address) {
        return (
            (this.readByte(address) << 8) |
            this.readByte(address + 1)
        ) >>> 0;
    }

    writeUint16BE(address, value) {
        if (!Number.isInteger(value) || value < 0 || value > 0xFFFF) {
            throw new RangeError("Value must fit in 16 bits.");
        }

        this.writeByte(address, (value >>> 8) & 0xFF);
        this.writeByte(address + 1, value & 0xFF);
    }

    dump(start, end) {
        for (let address = start; address < end; address++) {
            this.validateAddress(address);
            console.log(
                `${address.toString(16).padStart(4, "0").toUpperCase()}: ` +
                `${this.data[address].toString(16).padStart(2, "0").toUpperCase()}`
            );
        }
    }
}

function demonstrateMemory() {
    printSection("3. Byte-Addressable Memory");

    const memory = new ByteMemory(32);

    memory.writeUint16BE(4, 0x1234);

    console.log("Stored 0x1234 in big-endian order:");
    memory.dump(4, 6);

    console.log(
        "Read back:",
        "0x" + memory.readUint16BE(4).toString(16).toUpperCase()
    );

    try {
        memory.readByte(100);
    } catch (error) {
        console.log("Expected memory error:", error.message);
    }
}


// ============================================================================
// 5. ISA
// ============================================================================

const OPCODES = Object.freeze({
    NOP: 0x00,
    LOAD_IMM: 0x10,
    LOAD: 0x11,
    STORE: 0x12,
    ADD: 0x20,
    SUB: 0x21,
    AND: 0x22,
    OR: 0x23,
    XOR: 0x24,
    JMP: 0x30,
    JZ: 0x31,
    CMP: 0x32,
    OUT: 0x41,
    HALT: 0xFF
});

const OPCODE_NAMES = Object.fromEntries(
    Object.entries(OPCODES).map(([name, value]) => [value, name])
);

class Instruction {
    constructor(opcode, operand = 0) {
        if (!Number.isInteger(opcode) || opcode < 0 || opcode > 255) {
            throw new RangeError("Opcode must fit in one byte.");
        }

        if (!Number.isInteger(operand) || operand < 0 || operand > 255) {
            throw new RangeError("Operand must fit in one byte.");
        }

        this.opcode = opcode;
        this.operand = operand;
    }

    encode() {
        return ((this.opcode << 8) | this.operand) >>> 0;
    }

    static decode(word) {
        const opcode = (word >>> 8) & 0xFF;
        const operand = word & 0xFF;

        if (!(opcode in OPCODE_NAMES)) {
            throw new Error(`Unknown opcode 0x${opcode.toString(16)}`);
        }

        return new Instruction(opcode, operand);
    }

    toString() {
        const name = OPCODE_NAMES[this.opcode] ?? "UNKNOWN";
        return this.operand
            ? `${name} ${this.operand}`
            : name;
    }
}


// ============================================================================
// 6. CPU SIMULATOR
// ============================================================================

class EducationalCPU {
    constructor(memorySize = 256) {
        this.memory = new ByteMemory(memorySize);

        this.pc = new Register("PC", 8);
        this.ir = new Register("IR", 16);
        this.acc = new Register("ACC", 8);
        this.mar = new Register("MAR", 8);
        this.mdr = new Register("MDR", 8);

        this.zeroFlag = false;
        this.carryFlag = false;

        this.halted = false;
        this.cycles = 0;
        this.instructionsExecuted = 0;

        this.output = [];
    }

    loadProgram(program, start = 0) {
        let address = start;

        for (const instruction of program) {
            this.memory.writeUint16BE(address, instruction.encode());
            address += 2;
        }

        this.pc.write(start);
        this.halted = false;
    }

    fetch() {
        // Fetch stage:
        // 1. PC supplies the instruction address.
        // 2. Memory supplies the instruction.
        // 3. IR receives the instruction.
        // 4. PC advances to the next instruction.
        const currentAddress = this.pc.read();

        this.mar.write(currentAddress);

        const word = this.memory.readUint16BE(currentAddress);

        this.mdr.write(word & 0xFF);
        this.ir.write(word);

        this.pc.write(currentAddress + 2);

        return Instruction.decode(word);
    }

    updateFlags(result, carry = false) {
        this.zeroFlag = (result & 0xFF) === 0;
        this.carryFlag = carry;
    }

    execute(instruction) {
        const { opcode, operand } = instruction;
        const alu = new ALU();

        switch (opcode) {
            case OPCODES.NOP:
                break;

            case OPCODES.LOAD_IMM:
                this.acc.write(operand);
                this.updateFlags(this.acc.read());
                break;

            case OPCODES.LOAD:
                this.acc.write(this.memory.readByte(operand));
                this.updateFlags(this.acc.read());
                break;

            case OPCODES.STORE:
                this.memory.writeByte(operand, this.acc.read());
                break;

            case OPCODES.ADD: {
                const operation = alu.add(
                    this.acc.read(),
                    this.memory.readByte(operand)
                );

                this.acc.write(operation.result);
                this.updateFlags(operation.result, operation.carry);
                break;
            }

            case OPCODES.SUB: {
                const operation = alu.subtract(
                    this.acc.read(),
                    this.memory.readByte(operand)
                );

                this.acc.write(operation.result);
                this.updateFlags(operation.result, operation.borrow);
                break;
            }

            case OPCODES.AND: {
                const result = alu.and(
                    this.acc.read(),
                    this.memory.readByte(operand)
                );

                this.acc.write(result);
                this.updateFlags(result);
                break;
            }

            case OPCODES.OR: {
                const result = alu.or(
                    this.acc.read(),
                    this.memory.readByte(operand)
                );

                this.acc.write(result);
                this.updateFlags(result);
                break;
            }

            case OPCODES.XOR: {
                const result = alu.xor(
                    this.acc.read(),
                    this.memory.readByte(operand)
                );

                this.acc.write(result);
                this.updateFlags(result);
                break;
            }

            case OPCODES.JMP:
                this.pc.write(operand);
                break;

            case OPCODES.JZ:
                if (this.zeroFlag) {
                    this.pc.write(operand);
                }
                break;

            case OPCODES.CMP: {
                const difference = (
                    this.acc.read() -
                    this.memory.readByte(operand)
                ) & 0xFF;

                this.zeroFlag = difference === 0;
                break;
            }

            case OPCODES.OUT:
                this.output.push(this.acc.read());
                console.log(`[OUTPUT DEVICE] ${this.acc.read()}`);
                break;

            case OPCODES.HALT:
                this.halted = true;
                break;

            default:
                throw new Error(
                    `Unsupported opcode: 0x${opcode.toString(16)}`
                );
        }
    }

    step(trace = false) {
        if (this.halted) {
            return;
        }

        const oldPC = this.pc.read();
        const instruction = this.fetch();

        if (trace) {
            console.log(
                `cycle=${String(this.cycles + 1).padStart(3, "0")} ` +
                `PC=${String(oldPC).padStart(3, "0")} ` +
                `IR=${instruction}`
            );
        }

        this.execute(instruction);

        this.cycles++;
        this.instructionsExecuted++;
    }

    run(maxCycles = 1000, trace = false) {
        while (!this.halted) {
            if (this.cycles >= maxCycles) {
                throw new Error("Maximum CPU cycle limit reached.");
            }

            this.step(trace);
        }
    }

    dumpRegisters() {
        console.log({
            PC: this.pc.read(),
            IR: `0x${this.ir.read().toString(16).padStart(4, "0")}`,
            ACC: this.acc.read(),
            MAR: this.mar.read(),
            MDR: this.mdr.read(),
            Z: this.zeroFlag,
            C: this.carryFlag
        });
    }
}

function demonstrateCPU() {
    printSection("4. Instruction Cycle");

    const cpu = new EducationalCPU();

    cpu.memory.writeByte(200, 25);
    cpu.memory.writeByte(201, 17);

    const program = [
        new Instruction(OPCODES.LOAD, 200),
        new Instruction(OPCODES.ADD, 201),
        new Instruction(OPCODES.STORE, 202),
        new Instruction(OPCODES.OUT),
        new Instruction(OPCODES.HALT)
    ];

    cpu.loadProgram(program);
    cpu.run(100, true);

    console.log("\nFinal registers:");
    cpu.dumpRegisters();

    console.log("Memory[202] =", cpu.memory.readByte(202));
    console.log("Cycles =", cpu.cycles);
}


// ============================================================================
// 7. ASSEMBLER
// ============================================================================

function assemble(source) {
    const program = [];

    for (const [lineIndex, originalLine] of source.split(/\r?\n/).entries()) {
        const line = originalLine.split("#")[0].trim();

        if (!line) {
            continue;
        }

        const tokens = line.replaceAll(",", " ").split(/\s+/);
        const mnemonic = tokens[0].toUpperCase();

        if (!(mnemonic in OPCODES)) {
            throw new Error(
                `Assembly error on line ${lineIndex + 1}: ${mnemonic}`
            );
        }

        let operand = 0;

        if (tokens.length === 2) {
            operand = Number(tokens[1]);

            if (!Number.isInteger(operand) ||
                operand < 0 ||
                operand > 255) {
                throw new Error(
                    `Assembly error on line ${lineIndex + 1}: invalid operand`
                );
            }
        } else if (tokens.length > 2) {
            throw new Error(
                `Assembly error on line ${lineIndex + 1}: too many operands`
            );
        }

        program.push(new Instruction(OPCODES[mnemonic], operand));
    }

    return program;
}

function demonstrateAssembly() {
    printSection("5. Assembly-Like Programming");

    const source = `
        LOAD 200
        ADD 201
        STORE 202
        OUT
        HALT
    `;

    const program = assemble(source);

    program.forEach((instruction, index) => {
        console.log(
            `${(index * 2).toString(16).padStart(4, "0").toUpperCase()}: ` +
            instruction.toString()
        );
    });

    const cpu = new EducationalCPU();

    cpu.memory.writeByte(200, 30);
    cpu.memory.writeByte(201, 12);

    cpu.loadProgram(program);
    cpu.run();

    console.log("Result:", cpu.memory.readByte(202));
}


// ============================================================================
// 8. CACHE
// ============================================================================

class DirectMappedCache {
    constructor(lineCount = 4) {
        if (!Number.isInteger(lineCount) || lineCount <= 0) {
            throw new RangeError("Cache line count must be positive.");
        }

        this.lines = new Array(lineCount).fill(null);
        this.hits = 0;
        this.misses = 0;
    }

    access(address) {
        if (!Number.isInteger(address) || address < 0) {
            throw new RangeError("Address must be a non-negative integer.");
        }

        const index = address % this.lines.length;
        const tag = Math.floor(address / this.lines.length);
        const line = this.lines[index];

        if (line !== null && line.tag === tag) {
            this.hits++;
            return "HIT";
        }

        this.misses++;
        this.lines[index] = { tag, address };
        return "MISS";
    }

    get hitRate() {
        const total = this.hits + this.misses;
        return total === 0 ? 0 : this.hits / total;
    }
}

function demonstrateCache() {
    printSection("6. Cache and Locality");

    const cache = new DirectMappedCache(4);
    const accesses = [0, 1, 2, 3, 0, 1, 4, 0, 8, 0];

    for (const address of accesses) {
        console.log(`Address ${address}: ${cache.access(address)}`);
    }

    console.log("Hits:", cache.hits);
    console.log("Misses:", cache.misses);
    console.log("Hit rate:", `${(cache.hitRate * 100).toFixed(2)}%`);

    console.log(
        "\nSpatial locality means nearby addresses are likely to be accessed."
    );
    console.log(
        "Temporal locality means recently accessed data may be reused."
    );
}


// ============================================================================
// 9. PERFORMANCE
// ============================================================================

function cpuTime(instructionCount, cpi, clockFrequencyHz) {
    if (instructionCount < 0) {
        throw new RangeError("Instruction count cannot be negative.");
    }

    if (cpi <= 0 || clockFrequencyHz <= 0) {
        throw new RangeError("CPI and frequency must be positive.");
    }

    return instructionCount * cpi / clockFrequencyHz;
}

function demonstratePerformance() {
    printSection("7. CPU Performance");

    const instructionCount = 1_000_000;
    const cpi = 1.5;
    const frequency = 3_000_000_000;

    console.log(
        "Estimated CPU time:",
        cpuTime(instructionCount, cpi, frequency),
        "seconds"
    );

    console.log("\nImportant relationship:");
    console.log("CPU time = Instruction Count × CPI / Clock Frequency");
}


// ============================================================================
// 10. ASYNCHRONOUS I/O AND INTERRUPT-LIKE EVENTS
// ============================================================================

class InterruptController {
    constructor() {
        this.pending = [];
    }

    raise(source) {
        this.pending.push(source);
    }

    next() {
        return this.pending.shift() ?? null;
    }
}

function wait(milliseconds) {
    return new Promise(resolve => setTimeout(resolve, milliseconds));
}

async function demonstrateAsyncIO() {
    printSection("8. Event-Driven I/O");

    const controller = new InterruptController();

    // JavaScript's event loop is not a hardware interrupt controller.
    // This example is intentionally conceptual: asynchronous callbacks
    // allow software to react to events without continuously blocking.
    const eventSources = [
        ["keyboard", 10],
        ["timer", 20],
        ["network", 5]
    ];

    for (const [source, delay] of eventSources) {
        setTimeout(() => {
            controller.raise(source);
        }, delay);
    }

    await wait(40);

    while (true) {
        const interrupt = controller.next();

        if (interrupt === null) {
            break;
        }

        console.log("CPU-like event handler servicing:", interrupt);
    }
}


// ============================================================================
// 11. FUNCTIONAL VIEW OF DATAPATH OPERATIONS
// ============================================================================

function executeALUOperation(a, b, operation) {
    const operations = {
        ADD: (x, y) => (x + y) & 0xFF,
        SUB: (x, y) => (x - y) & 0xFF,
        AND: (x, y) => x & y,
        OR: (x, y) => x | y,
        XOR: (x, y) => x ^ y
    };

    const operationFunction = operations[operation];

    if (!operationFunction) {
        throw new Error(`Unsupported ALU operation: ${operation}`);
    }

    return operationFunction(a, b);
}

function demonstrateDatapath() {
    printSection("9. Datapath and Control Separation");

    const registers = [14, 28, 0, 0];

    const controlSignals = {
        sourceRegisterA: 0,
        sourceRegisterB: 1,
        destinationRegister: 2,
        aluOperation: "ADD",
        registerWrite: true
    };

    const result = executeALUOperation(
        registers[controlSignals.sourceRegisterA],
        registers[controlSignals.sourceRegisterB],
        controlSignals.aluOperation
    );

    if (controlSignals.registerWrite) {
        registers[controlSignals.destinationRegister] = result;
    }

    console.log("Control signals:", controlSignals);
    console.log("Register file:", registers);
}


// ============================================================================
// 12. END-TO-END CASE STUDY
// ============================================================================

class SimpleProcessorSystem {
    constructor() {
        this.cpu = new EducationalCPU(512);

        // A device register abstraction:
        // application code can write commands to a simulated device.
        this.devices = new Map([
            ["console", []],
            ["sensor", [17, 25, 33]]
        ]);
    }

    readSensor() {
        const sensor = this.devices.get("sensor");

        if (!sensor || sensor.length === 0) {
            throw new Error("Sensor has no sample available.");
        }

        return sensor.shift();
    }

    writeConsole(value) {
        this.devices.get("console").push(value & 0xFF);
        console.log(`[CONSOLE DEVICE] ${value & 0xFF}`);
    }

    runCalculation() {
        // A realistic architectural idea is being modeled:
        // application logic becomes machine instructions, which operate
        // on registers and memory through the ISA.
        const firstMeasurement = this.readSensor();
        const secondMeasurement = this.readSensor();

        this.cpu.memory.writeByte(400, firstMeasurement);
        this.cpu.memory.writeByte(401, secondMeasurement);

        const program = [
            new Instruction(OPCODES.LOAD, 400),
            new Instruction(OPCODES.ADD, 401),
            new Instruction(OPCODES.STORE, 402),
            new Instruction(OPCODES.OUT),
            new Instruction(OPCODES.HALT)
        ];

        this.cpu.loadProgram(program);
        this.cpu.run();

        const result = this.cpu.memory.readByte(402);

        this.writeConsole(result);

        return result;
    }
}

function demonstrateCaseStudy() {
    printSection("10. Small Embedded-Style Case Study");

    const system = new SimpleProcessorSystem();
    const result = system.runCalculation();

    console.log("Sensor calculation result:", result);
}


// ============================================================================
// 13. TESTS
// ============================================================================

function runTests() {
    printSection("11. Self-Tests");

    const memory = new ByteMemory(16);
    memory.writeByte(3, 99);

    console.assert(
        memory.readByte(3) === 99,
        "Memory read/write failed."
    );

    const alu = new ALU();
    const addition = alu.add(200, 100);

    console.assert(
        addition.result === 44 && addition.carry === true,
        "ALU addition failed."
    );

    const instruction = Instruction.decode(
        new Instruction(OPCODES.LOAD_IMM, 42).encode()
    );

    console.assert(
        instruction.opcode === OPCODES.LOAD_IMM &&
        instruction.operand === 42,
        "Instruction encoding failed."
    );

    const cpu = new EducationalCPU();

    cpu.memory.writeByte(200, 10);
    cpu.memory.writeByte(201, 20);

    cpu.loadProgram([
        new Instruction(OPCODES.LOAD, 200),
        new Instruction(OPCODES.ADD, 201),
        new Instruction(OPCODES.STORE, 202),
        new Instruction(OPCODES.HALT)
    ]);

    cpu.run();

    console.assert(
        cpu.memory.readByte(202) === 30,
        "CPU execution failed."
    );

    const cache = new DirectMappedCache(2);

    console.assert(cache.access(0) === "MISS", "First cache access failed.");
    console.assert(cache.access(0) === "HIT", "Second cache access failed.");

    console.log("All JavaScript self-tests passed.");
}


// ============================================================================
// 14. EDGE CASES
// ============================================================================

function demonstrateEdgeCases() {
    printSection("12. Edge Cases");

    const cases = [
        ["Invalid memory address", () => {
            new ByteMemory(4).readByte(20);
        }],
        ["Invalid byte", () => {
            new ByteMemory(4).writeByte(0, 999);
        }],
        ["Unknown opcode", () => {
            Instruction.decode(0x9900);
        }],
        ["Invalid assembly", () => {
            assemble("UNKNOWN 10");
        }]
    ];

    for (const [name, operation] of cases) {
        try {
            operation();
            console.log(name, "did not fail as expected.");
        } catch (error) {
            console.log(name, "-> handled:", error.message);
        }
    }
}


// ============================================================================
// 15. MAIN
// ============================================================================

async function main() {
    console.log("COMPUTER ARCHITECTURE INTRODUCTION");
    console.log("CPU, ISA, memory, I/O and organization laboratory");

    demonstrateNumberRepresentation();
    demonstrateALU();
    demonstrateMemory();
    demonstrateCPU();
    demonstrateAssembly();
    demonstrateCache();
    demonstratePerformance();
    await demonstrateAsyncIO();
    demonstrateDatapath();
    demonstrateCaseStudy();
    runTests();
    demonstrateEdgeCases();

    printSection("16. Architectural Relationship");
    console.log(
        "Software executes through an ISA. The CPU implements that ISA using "
        + "a datapath and control logic. Memory and I/O provide the resources "
        + "with which instructions interact."
    );
}

main().catch(error => {
    console.error("Program failed:", error);
    process.exitCode = 1;
});
