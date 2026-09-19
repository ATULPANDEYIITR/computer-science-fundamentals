/*
 * Assembly Language Basics: Registers, Instructions, Labels, Memory
 * Operations, and Arithmetic Instructions
 *
 * This file provides a JavaScript educational simulator for a small subset
 * of MIPS-style instructions used in MARS and RARS.
 *
 * JavaScript is useful here because a CPU model can be represented naturally
 * with arrays, maps, classes, functions, and event-driven tracing.
 *
 * The implementation is intentionally independent of MARS/RARS. It models
 * fundamental machine behavior rather than attempting to reproduce every
 * simulator-specific feature or system call.
 */

"use strict";

// -----------------------------------------------------------------------------
// 32-bit helpers
// -----------------------------------------------------------------------------

function toUint32(value) {
    return value >>> 0;
}

function toInt32(value) {
    return value | 0;
}

function signExtend16(value) {
    const unsignedValue = value & 0xFFFF;
    return unsignedValue & 0x8000
        ? unsignedValue - 0x10000
        : unsignedValue;
}

// -----------------------------------------------------------------------------
// Register names
// -----------------------------------------------------------------------------

const REGISTER_NAMES = {
    "$zero": 0,
    "$at": 1,
    "$v0": 2,
    "$v1": 3,
    "$a0": 4,
    "$a1": 5,
    "$a2": 6,
    "$a3": 7,
    "$t0": 8,
    "$t1": 9,
    "$t2": 10,
    "$t3": 11,
    "$t4": 12,
    "$t5": 13,
    "$t6": 14,
    "$t7": 15,
    "$s0": 16,
    "$s1": 17,
    "$s2": 18,
    "$s3": 19,
    "$s4": 20,
    "$s5": 21,
    "$s6": 22,
    "$s7": 23,
    "$t8": 24,
    "$t9": 25,
    "$k0": 26,
    "$k1": 27,
    "$gp": 28,
    "$sp": 29,
    "$fp": 30,
    "$ra": 31
};

for (let index = 0; index < 32; index += 1) {
    REGISTER_NAMES[`$r${index}`] = index;
}

function registerIndex(name) {
    const normalized = name.trim().toLowerCase();

    if (!(normalized in REGISTER_NAMES)) {
        throw new Error(`Unknown register: ${name}`);
    }

    return REGISTER_NAMES[normalized];
}

// -----------------------------------------------------------------------------
// Register file
// -----------------------------------------------------------------------------

class RegisterFile {
    constructor() {
        this.values = new Int32Array(32);
    }

    read(name) {
        return this.values[registerIndex(name)];
    }

    write(name, value) {
        const index = registerIndex(name);

        // $zero is hard-wired to zero.
        if (index !== 0) {
            this.values[index] = toInt32(value);
        }
    }

    dump(names = [
        "$zero", "$v0", "$a0", "$t0", "$t1",
        "$t2", "$s0", "$sp", "$ra"
    ]) {
        console.log("Register state:");

        for (const name of names) {
            const value = this.read(name);
            console.log(
                `${name.padStart(6)} = ${String(value).padStart(12)} ` +
                `(0x${toUint32(value).toString(16).padStart(8, "0").toUpperCase()})`
            );
        }
    }
}

// -----------------------------------------------------------------------------
// Byte-addressable memory
// -----------------------------------------------------------------------------

class Memory {
    constructor() {
        // Map is convenient for sparse educational memory.
        this.bytes = new Map();
    }

    storeByte(address, value) {
        this.bytes.set(toUint32(address), value & 0xFF);
    }

    loadByte(address) {
        return this.bytes.get(toUint32(address)) ?? 0;
    }

    storeWord(address, value) {
        if (address % 4 !== 0) {
            throw new Error(`Unaligned word address: 0x${address.toString(16)}`);
        }

        const unsignedValue = toUint32(value);

        // Little-endian byte order.
        for (let offset = 0; offset < 4; offset += 1) {
            this.storeByte(
                address + offset,
                unsignedValue >>> (offset * 8)
            );
        }
    }

    loadWord(address) {
        if (address % 4 !== 0) {
            throw new Error(`Unaligned word address: 0x${address.toString(16)}`);
        }

        let value = 0;

        for (let offset = 0; offset < 4; offset += 1) {
            value |= this.loadByte(address + offset) << (offset * 8);
        }

        return toInt32(value);
    }
}

// -----------------------------------------------------------------------------
// Instruction representation
// -----------------------------------------------------------------------------

class Instruction {
    constructor(opcode, operands = [], source = "") {
        this.opcode = opcode.toLowerCase();
        this.operands = operands;
        this.source = source || [opcode, ...operands].join(" ");
    }

    toString() {
        return this.source;
    }
}

// -----------------------------------------------------------------------------
// Mini MIPS interpreter
// -----------------------------------------------------------------------------

class MiniMIPS {
    constructor({ trace = false } = {}) {
        this.registers = new RegisterFile();
        this.memory = new Memory();
        this.program = [];
        this.labels = new Map();
        this.pc = 0;
        this.trace = trace;
        this.running = false;
    }

    loadProgram(program, labels = {}) {
        this.program = program;
        this.labels = new Map(Object.entries(labels));
        this.pc = 0;
    }

    resolveMemoryAddress(operand) {
        // Expected form: offset(base), for example 8($sp).
        const match = operand.replaceAll(" ", "").match(
            /^(-?\d+)\((\$[A-Za-z0-9]+)\)$/
        );

        if (!match) {
            throw new Error(`Invalid memory operand: ${operand}`);
        }

        const offset = Number.parseInt(match[1], 10);
        const base = this.registers.read(match[2]);

        return toUint32(base + offset);
    }

    step() {
        if (this.pc < 0 || this.pc >= this.program.length) {
            this.running = false;
            return;
        }

        const instruction = this.program[this.pc];
        const { opcode, operands } = instruction;

        if (this.trace) {
            console.log(`[PC=${String(this.pc).padStart(3, "0")}] ${instruction}`);
        }

        let nextPC = this.pc + 1;

        switch (opcode) {
            case "nop":
                break;

            case "li": {
                const [rd, immediate] = operands;
                this.registers.write(rd, Number.parseInt(immediate, 0));
                break;
            }

            case "move": {
                const [rd, rs] = operands;
                this.registers.write(rd, this.registers.read(rs));
                break;
            }

            case "add":
            case "addu":
            case "sub":
            case "mul": {
                const [rd, rs, rt] = operands;
                const left = this.registers.read(rs);
                const right = this.registers.read(rt);

                let result;

                if (opcode === "add") {
                    // JavaScript arithmetic can exceed 32 bits, so explicitly
                    // test signed range before storing the result.
                    const candidate = left + right;

                    if (
                        candidate < -2147483648 ||
                        candidate > 2147483647
                    ) {
                        throw new RangeError(
                            `Signed overflow: ${left} + ${right}`
                        );
                    }

                    result = candidate;
                } else if (opcode === "sub") {
                    const candidate = left - right;

                    if (
                        candidate < -2147483648 ||
                        candidate > 2147483647
                    ) {
                        throw new RangeError(
                            `Signed overflow: ${left} - ${right}`
                        );
                    }

                    result = candidate;
                } else if (opcode === "mul") {
                    result = Math.imul(left, right);
                } else {
                    result = toInt32(
                        toUint32(left) + toUint32(right)
                    );
                }

                this.registers.write(rd, result);
                break;
            }

            case "addi":
            case "addiu": {
                const [rt, rs, immediate] = operands;
                const source = this.registers.read(rs);
                const immediateValue = signExtend16(
                    Number.parseInt(immediate, 0)
                );

                if (opcode === "addi") {
                    const candidate = source + immediateValue;

                    if (
                        candidate < -2147483648 ||
                        candidate > 2147483647
                    ) {
                        throw new RangeError(
                            `Signed immediate overflow: ${source} + ${immediateValue}`
                        );
                    }

                    this.registers.write(rt, candidate);
                } else {
                    this.registers.write(
                        rt,
                        toInt32(toUint32(source) + toUint32(immediateValue))
                    );
                }

                break;
            }

            case "and":
            case "or":
            case "xor": {
                const [rd, rs, rt] = operands;
                const left = this.registers.read(rs);
                const right = this.registers.read(rt);

                let result;

                if (opcode === "and") {
                    result = left & right;
                } else if (opcode === "or") {
                    result = left | right;
                } else {
                    result = left ^ right;
                }

                this.registers.write(rd, result);
                break;
            }

            case "sll":
            case "srl": {
                const [rd, rt, shiftText] = operands;
                const value = toUint32(this.registers.read(rt));
                const shift = Number.parseInt(shiftText, 0) & 31;

                const result = opcode === "sll"
                    ? toUint32(value << shift)
                    : value >>> shift;

                this.registers.write(rd, result);
                break;
            }

            case "slt": {
                const [rd, rs, rt] = operands;

                this.registers.write(
                    rd,
                    this.registers.read(rs) < this.registers.read(rt) ? 1 : 0
                );
                break;
            }

            case "lw": {
                const [rt, addressOperand] = operands;
                const address = this.resolveMemoryAddress(addressOperand);

                this.registers.write(
                    rt,
                    this.memory.loadWord(address)
                );
                break;
            }

            case "sw": {
                const [rt, addressOperand] = operands;
                const address = this.resolveMemoryAddress(addressOperand);

                this.memory.storeWord(
                    address,
                    this.registers.read(rt)
                );
                break;
            }

            case "beq":
            case "bne": {
                const [rs, rt, label] = operands;

                if (!this.labels.has(label)) {
                    throw new Error(`Unknown label: ${label}`);
                }

                const equal =
                    this.registers.read(rs) === this.registers.read(rt);

                const branch = opcode === "beq" ? equal : !equal;

                if (branch) {
                    nextPC = this.labels.get(label);
                }

                break;
            }

            case "j":
            case "jal": {
                const [label] = operands;

                if (!this.labels.has(label)) {
                    throw new Error(`Unknown label: ${label}`);
                }

                if (opcode === "jal") {
                    this.registers.write("$ra", nextPC);
                }

                nextPC = this.labels.get(label);
                break;
            }

            case "jr": {
                const [rs] = operands;
                nextPC = this.registers.read(rs);
                break;
            }

            default:
                throw new Error(`Unsupported opcode: ${opcode}`);
        }

        this.pc = nextPC;
    }

    run(maxSteps = 10000) {
        this.running = true;
        let steps = 0;

        while (
            this.running &&
            this.pc >= 0 &&
            this.pc < this.program.length
        ) {
            this.step();
            steps += 1;

            if (steps >= maxSteps) {
                throw new Error(
                    "Execution limit reached; possible infinite loop."
                );
            }
        }

        this.running = false;
        return steps;
    }
}

// -----------------------------------------------------------------------------
// Example: arithmetic
// -----------------------------------------------------------------------------

function arithmeticExample() {
    console.log("\n=== JavaScript Example 1: Arithmetic ===");

    const cpu = new MiniMIPS();

    cpu.loadProgram([
        new Instruction("li", ["$t0", "18"]),
        new Instruction("li", ["$t1", "7"]),
        new Instruction("add", ["$t2", "$t0", "$t1"]),
        new Instruction("sub", ["$t3", "$t0", "$t1"]),
        new Instruction("mul", ["$t4", "$t2", "$t3"])
    ]);

    cpu.run();

    cpu.registers.dump(["$t0", "$t1", "$t2", "$t3", "$t4"]);
}

// -----------------------------------------------------------------------------
// Example: memory and address arithmetic
// -----------------------------------------------------------------------------

function memoryExample() {
    console.log("\n=== JavaScript Example 2: Memory ===");

    const cpu = new MiniMIPS();
    const baseAddress = 0x10010000;

    cpu.memory.storeWord(baseAddress, 100);
    cpu.memory.storeWord(baseAddress + 4, 200);
    cpu.memory.storeWord(baseAddress + 8, 300);

    cpu.loadProgram([
        new Instruction("li", ["$t0", String(baseAddress)]),
        new Instruction("lw", ["$t1", "8($t0)"]),
        new Instruction("addi", ["$t1", "$t1", "25"]),
        new Instruction("sw", ["$t1", "8($t0)"])
    ]);

    cpu.run();

    console.log(
        "numbers[2] =",
        cpu.memory.loadWord(baseAddress + 8)
    );
}

// -----------------------------------------------------------------------------
// Example: loop with labels
// -----------------------------------------------------------------------------

function loopExample() {
    console.log("\n=== JavaScript Example 3: Loop and labels ===");

    const cpu = new MiniMIPS();

    // Calculate 1 + 2 + 3 + 4 + 5.
    const program = [
        new Instruction("li", ["$t0", "1"]),
        new Instruction("li", ["$t1", "0"]),
        new Instruction("li", ["$t2", "6"]),

        new Instruction("add", ["$t1", "$t1", "$t0"]),
        new Instruction("addi", ["$t0", "$t0", "1"]),
        new Instruction("bne", ["$t0", "$t2", "loop"])
    ];

    cpu.loadProgram(program, { loop: 3 });
    cpu.run();

    console.log("Sum =", cpu.registers.read("$t1"));
}

// -----------------------------------------------------------------------------
// Example: function call
// -----------------------------------------------------------------------------

function functionExample() {
    console.log("\n=== JavaScript Example 4: Procedure call ===");

    const cpu = new MiniMIPS();

    /*
     * The calling convention used by this small demonstration is:
     *
     * $a0 -> argument
     * $v0 -> return value
     * $ra -> return address
     *
     * The stack is used to preserve $ra.
     */
    const program = [
        new Instruction("li", ["$sp", "0x7FFFEFFC"]),
        new Instruction("li", ["$a0", "8"]),
        new Instruction("jal", ["square"]),
        new Instruction("j", ["end"]),

        // square:
        new Instruction("sw", ["$ra", "0($sp)"]),
        new Instruction("mul", ["$v0", "$a0", "$a0"]),
        new Instruction("lw", ["$ra", "0($sp)"]),
        new Instruction("jr", ["$ra"]),

        new Instruction("nop")
    ];

    cpu.loadProgram(program, {
        square: 4,
        end: 8
    });

    cpu.run();

    console.log("8 squared =", cpu.registers.read("$v0"));
}

// -----------------------------------------------------------------------------
// Example: array statistics
// -----------------------------------------------------------------------------

function arrayStatisticsExample() {
    console.log("\n=== JavaScript Example 5: Array statistics ===");

    const cpu = new MiniMIPS();
    const values = [14, -2, 31, 9, 22, 17];
    const base = 0x10010000;

    for (let index = 0; index < values.length; index += 1) {
        cpu.memory.storeWord(
            base + index * 4,
            values[index]
        );
    }

    /*
     * Assembly-level algorithm:
     *
     * pointer = base
     * count = length
     * sum = 0
     * maximum = first element
     *
     * Repeat:
     *   load current element
     *   add it to sum
     *   compare it with maximum
     *   advance pointer by four bytes
     *   decrement count
     */
    const program = [
        new Instruction("li", ["$t0", String(base)]),
        new Instruction("li", ["$t1", String(values.length)]),
        new Instruction("li", ["$t2", "0"]),
        new Instruction("lw", ["$t4", "0($t0)"]),
        new Instruction("li", ["$t5", "0"]),

        new Instruction("lw", ["$t3", "0($t0)"]),
        new Instruction("add", ["$t2", "$t2", "$t3"]),
        new Instruction("slt", ["$t6", "$t4", "$t3"]),
        new Instruction("beq", ["$t6", "$t5", "skip_max"]),
        new Instruction("move", ["$t4", "$t3"]),

        new Instruction("addi", ["$t0", "$t0", "4"]),
        new Instruction("addi", ["$t1", "$t1", "-1"]),
        new Instruction("bne", ["$t1", "$t5", "loop"]),
        new Instruction("j", ["end"]),

        new Instruction("addi", ["$t0", "$t0", "4"]),
        new Instruction("addi", ["$t1", "$t1", "-1"]),
        new Instruction("bne", ["$t1", "$t5", "loop"]),

        new Instruction("nop")
    ];

    cpu.loadProgram(program, {
        loop: 5,
        skip_max: 14,
        end: 17
    });

    cpu.run();

    const sum = cpu.registers.read("$t2");
    const maximum = cpu.registers.read("$t4");

    console.log("Sum =", sum);
    console.log("Maximum =", maximum);

    if (sum !== values.reduce((a, b) => a + b, 0)) {
        throw new Error("Array sum test failed.");
    }

    if (maximum !== Math.max(...values)) {
        throw new Error("Array maximum test failed.");
    }
}

// -----------------------------------------------------------------------------
// Edge cases and machine behavior
// -----------------------------------------------------------------------------

function edgeCaseExample() {
    console.log("\n=== JavaScript Example 6: Edge cases ===");

    const registers = new RegisterFile();

    // Writes to $zero are discarded.
    registers.write("$zero", 12345);
    console.log("$zero =", registers.read("$zero"));

    // Two's-complement 32-bit representation.
    registers.write("$t0", 0xFFFFFFFF);
    console.log(
        "0xFFFFFFFF interpreted as signed =",
        registers.read("$t0")
    );

    // Unaligned word access is rejected in this educational model.
    const memory = new Memory();

    try {
        memory.storeWord(0x1001, 42);
    } catch (error) {
        console.log("Unaligned access:", error.message);
    }

    // Infinite loops should be caught by the execution limit.
    const cpu = new MiniMIPS();

    cpu.loadProgram([
        new Instruction("j", ["loop"])
    ], {
        loop: 0
    });

    try {
        cpu.run(20);
    } catch (error) {
        console.log("Execution guard:", error.message);
    }
}

// -----------------------------------------------------------------------------
// Self-tests
// -----------------------------------------------------------------------------

function runTests() {
    console.log("\n=== Self-tests ===");

    const registers = new RegisterFile();

    registers.write("$t0", -100);
    if (registers.read("$t0") !== -100) {
        throw new Error("Register test failed.");
    }

    registers.write("$zero", 100);
    if (registers.read("$zero") !== 0) {
        throw new Error("$zero test failed.");
    }

    const memory = new Memory();
    memory.storeWord(0x2000, -123456);

    if (memory.loadWord(0x2000) !== -123456) {
        throw new Error("Memory test failed.");
    }

    const cpu = new MiniMIPS();

    cpu.loadProgram([
        new Instruction("li", ["$t0", "11"]),
        new Instruction("li", ["$t1", "4"]),
        new Instruction("sub", ["$t2", "$t0", "$t1"])
    ]);

    cpu.run();

    if (cpu.registers.read("$t2") !== 7) {
        throw new Error("Arithmetic test failed.");
    }

    console.log("All JavaScript tests passed.");
}

// -----------------------------------------------------------------------------
// Main
// -----------------------------------------------------------------------------

function main() {
    console.log("MIPS Assembly Language Basics Study Program");

    runTests();
    arithmeticExample();
    memoryExample();
    loopExample();
    functionExample();
    arrayStatisticsExample();
    edgeCaseExample();

    console.log("\nKey ideas:");
    console.log("- Registers are fast CPU storage locations.");
    console.log("- Memory operations use addresses and offsets.");
    console.log("- Labels represent instruction addresses.");
    console.log("- Branches and jumps change the program counter.");
    console.log("- jal/jr provide procedure-call control flow.");
    console.log("- MARS and RARS make these mechanisms visible through simulation.");
}

main();
