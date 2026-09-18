/*
 * Instruction Set Architecture (ISA)
 * Topic:
 *   Instructions, operands, opcodes, registers, addressing modes
 *
 * This file demonstrates ISA concepts using JavaScript and a small
 * event-driven virtual CPU. The implementation is intentionally educational
 * and uses no external packages.
 */

"use strict";

// ---------------------------------------------------------------------------
// 1. ISA TERMINOLOGY
// ---------------------------------------------------------------------------

const isaConcepts = {
    ISA: "The programmer-visible contract of a processor.",
    instruction: "An encoded operation executed by the CPU.",
    opcode: "The operation identifier inside an instruction.",
    operand: "A value, register, address, or constant used by an instruction.",
    register: "Small, fast CPU storage locations.",
    addressingMode: "The rule used to locate or calculate an operand.",
    instructionEncoding: "The binary representation of an instruction."
};

console.log("ISA concepts:");
for (const [name, definition] of Object.entries(isaConcepts)) {
    console.log(`${name}: ${definition}`);
}


// ---------------------------------------------------------------------------
// 2. OPCODES
// ---------------------------------------------------------------------------

const OPCODE = Object.freeze({
    NOP: 0x00,
    MOV: 0x01,
    ADD: 0x02,
    SUB: 0x03,
    AND: 0x04,
    OR: 0x05,
    XOR: 0x06,
    SHL: 0x07,
    SHR: 0x08,
    LOAD: 0x09,
    STORE: 0x0A,
    JMP: 0x0B,
    JZ: 0x0C,
    CMP: 0x0D,
    HALT: 0x0E
});

const OPCODE_NAME = Object.fromEntries(
    Object.entries(OPCODE).map(([name, value]) => [value, name])
);


// ---------------------------------------------------------------------------
// 3. INSTRUCTION REPRESENTATION
// ---------------------------------------------------------------------------

class Instruction {
    constructor(opcode, operands = [], immediate = null) {
        if (!Object.values(OPCODE).includes(opcode)) {
            throw new Error(`Unknown opcode: ${opcode}`);
        }

        this.opcode = opcode;
        this.operands = [...operands];
        this.immediate = immediate;
    }

    toString() {
        const parts = this.operands.map(value => `R${value}`);

        if (this.immediate !== null) {
            parts.push(`#${this.immediate}`);
        }

        return `${OPCODE_NAME[this.opcode]} ${parts.join(", ")}`.trim();
    }
}


// ---------------------------------------------------------------------------
// 4. REGISTER FILE
// ---------------------------------------------------------------------------

class RegisterFile {
    constructor(count = 8, width = 16) {
        if (count <= 0 || width <= 0) {
            throw new Error("Register count and width must be positive.");
        }

        this.count = count;
        this.width = width;
        this.mask = (2 ** width) - 1;
        this.values = new Uint32Array(count);
    }

    validateIndex(index) {
        if (!Number.isInteger(index) || index < 0 || index >= this.count) {
            throw new RangeError(`Invalid register R${index}.`);
        }
    }

    read(index) {
        this.validateIndex(index);
        return this.values[index];
    }

    write(index, value) {
        this.validateIndex(index);
        this.values[index] = value & this.mask;
    }

    dump() {
        return Array.from(this.values, (value, index) =>
            `R${index}=${value.toString(16).padStart(4, "0").toUpperCase()}`
        ).join(" ");
    }
}


// ---------------------------------------------------------------------------
// 5. BYTE-ADDRESSABLE MEMORY
// ---------------------------------------------------------------------------

class Memory {
    constructor(size = 256) {
        if (!Number.isInteger(size) || size <= 0) {
            throw new Error("Memory size must be positive.");
        }

        this.data = new Uint8Array(size);
    }

    validateAddress(address) {
        if (!Number.isInteger(address) || address < 0 || address >= this.data.length) {
            throw new RangeError(`Memory address ${address} is invalid.`);
        }
    }

    readByte(address) {
        this.validateAddress(address);
        return this.data[address];
    }

    writeByte(address, value) {
        this.validateAddress(address);
        this.data[address] = value & 0xFF;
    }

    readWord(address) {
        this.validateAddress(address);
        this.validateAddress(address + 1);

        // Little-endian 16-bit word.
        return this.data[address] | (this.data[address + 1] << 8);
    }

    writeWord(address, value) {
        this.validateAddress(address);
        this.validateAddress(address + 1);

        this.data[address] = value & 0xFF;
        this.data[address + 1] = (value >>> 8) & 0xFF;
    }
}


// ---------------------------------------------------------------------------
// 6. ADDRESSING MODES
// ---------------------------------------------------------------------------

const AddressingMode = Object.freeze({
    REGISTER: "register",
    IMMEDIATE: "immediate",
    DIRECT: "direct",
    REGISTER_INDIRECT: "register-indirect",
    BASE_OFFSET: "base-offset",
    INDEXED: "indexed",
    PC_RELATIVE: "pc-relative"
});

function calculateEffectiveAddress(mode, {
    registerValue = 0,
    indexValue = 0,
    displacement = 0,
    directAddress = 0,
    programCounter = 0
} = {}) {
    switch (mode) {
        case AddressingMode.DIRECT:
            return directAddress;

        case AddressingMode.REGISTER_INDIRECT:
            return registerValue;

        case AddressingMode.BASE_OFFSET:
            return registerValue + displacement;

        case AddressingMode.INDEXED:
            return registerValue + indexValue + displacement;

        case AddressingMode.PC_RELATIVE:
            return programCounter + displacement;

        default:
            throw new Error(
                `${mode} does not directly calculate a memory address.`
            );
    }
}

console.log("\nAddressing mode examples:");
console.log(
    "Direct:",
    calculateEffectiveAddress(AddressingMode.DIRECT, {
        directAddress: 200
    })
);
console.log(
    "Register indirect:",
    calculateEffectiveAddress(AddressingMode.REGISTER_INDIRECT, {
        registerValue: 100
    })
);
console.log(
    "Base + offset:",
    calculateEffectiveAddress(AddressingMode.BASE_OFFSET, {
        registerValue: 100,
        displacement: 12
    })
);
console.log(
    "Indexed:",
    calculateEffectiveAddress(AddressingMode.INDEXED, {
        registerValue: 100,
        indexValue: 20
    })
);
console.log(
    "PC relative:",
    calculateEffectiveAddress(AddressingMode.PC_RELATIVE, {
        programCounter: 50,
        displacement: 16
    })
);


// ---------------------------------------------------------------------------
// 7. INSTRUCTION ENCODING
// ---------------------------------------------------------------------------

/*
 * Educational 32-bit instruction format:
 *
 *   31       24 23    20 19    16 15                 0
 *   +----------+--------+--------+--------------------+
 *   |  opcode  |  regA  |  regB  |     immediate     |
 *   +----------+--------+--------+--------------------+
 *
 * Real processors frequently have multiple instruction formats.
 */

function encodeInstruction(instruction) {
    const regA = instruction.operands[0] ?? 0;
    const regB = instruction.operands[1] ?? 0;
    const immediate = instruction.immediate ?? 0;

    if (regA < 0 || regA > 15 || regB < 0 || regB > 15) {
        throw new RangeError("Register field does not fit in four bits.");
    }

    return (
        ((instruction.opcode & 0xFF) << 24) |
        ((regA & 0x0F) << 20) |
        ((regB & 0x0F) << 16) |
        (immediate & 0xFFFF)
    ) >>> 0;
}

function decodeInstruction(machineWord) {
    machineWord = machineWord >>> 0;

    const opcode = (machineWord >>> 24) & 0xFF;
    const regA = (machineWord >>> 20) & 0x0F;
    const regB = (machineWord >>> 16) & 0x0F;
    const immediate = machineWord & 0xFFFF;

    if (OPCODE_NAME[opcode] === undefined) {
        throw new Error(`Unknown opcode 0x${opcode.toString(16)}`);
    }

    if (opcode === OPCODE.NOP || opcode === OPCODE.HALT) {
        return new Instruction(opcode);
    }

    if (opcode === OPCODE.JMP || opcode === OPCODE.JZ) {
        return new Instruction(opcode, [], immediate);
    }

    if (opcode === OPCODE.SHL || opcode === OPCODE.SHR) {
        return new Instruction(opcode, [regA], immediate);
    }

    if (opcode === OPCODE.LOAD || opcode === OPCODE.STORE) {
        if (regB === 0) {
            return new Instruction(opcode, [regA], immediate);
        }

        return new Instruction(opcode, [regA, regB], immediate);
    }

    return new Instruction(opcode, [regA, regB]);
}

const encoded = encodeInstruction(
    new Instruction(OPCODE.ADD, [1, 2])
);

console.log("\nInstruction encoding:");
console.log(`Encoded: 0x${encoded.toString(16).padStart(8, "0").toUpperCase()}`);
console.log("Decoded:", decodeInstruction(encoded).toString());


// ---------------------------------------------------------------------------
// 8. VIRTUAL CPU
// ---------------------------------------------------------------------------

class VirtualCPU {
    constructor(memorySize = 256) {
        this.registers = new RegisterFile(8, 16);
        this.memory = new Memory(memorySize);

        this.flags = {
            zero: false,
            negative: false,
            carry: false,
            overflow: false
        };

        this.programCounter = 0;
        this.program = [];
        this.halted = false;
        this.steps = 0;
    }

    loadProgram(program) {
        this.program = [...program];
        this.programCounter = 0;
        this.halted = false;
        this.steps = 0;
    }

    setFlags(result, carry = false, overflow = false) {
        const value = result & 0xFFFF;

        this.flags.zero = value === 0;
        this.flags.negative = Boolean(value & 0x8000);
        this.flags.carry = carry;
        this.flags.overflow = overflow;
    }

    add16(left, right) {
        const raw = left + right;
        const result = raw & 0xFFFF;

        const signedLeft = left & 0x8000 ? left - 0x10000 : left;
        const signedRight = right & 0x8000 ? right - 0x10000 : right;
        const signedResult = result & 0x8000
            ? result - 0x10000
            : result;

        const overflow =
            (signedLeft >= 0 && signedRight >= 0 && signedResult < 0) ||
            (signedLeft < 0 && signedRight < 0 && signedResult >= 0);

        this.setFlags(result, raw > 0xFFFF, overflow);
        return result;
    }

    subtract16(left, right) {
        const raw = left - right;
        const result = raw & 0xFFFF;

        const signedLeft = left & 0x8000 ? left - 0x10000 : left;
        const signedRight = right & 0x8000 ? right - 0x10000 : right;
        const signedResult = result & 0x8000
            ? result - 0x10000
            : result;

        const overflow =
            (signedLeft >= 0 && signedRight < 0 && signedResult < 0) ||
            (signedLeft < 0 && signedRight >= 0 && signedResult >= 0);

        this.setFlags(result, left >= right, overflow);
        return result;
    }

    readSecondOperand(instruction) {
        if (instruction.immediate !== null) {
            return instruction.immediate & 0xFFFF;
        }

        return this.registers.read(instruction.operands[1]);
    }

    validateProgramTarget(target) {
        if (
            !Number.isInteger(target) ||
            target < 0 ||
            target >= this.program.length
        ) {
            throw new Error(`Invalid program target: ${target}`);
        }
    }

    step() {
        if (this.halted) {
            return;
        }

        if (
            this.programCounter < 0 ||
            this.programCounter >= this.program.length
        ) {
            throw new Error("Program counter is outside program.");
        }

        const instruction = this.program[this.programCounter];
        this.programCounter++;

        switch (instruction.opcode) {
            case OPCODE.NOP:
                break;

            case OPCODE.MOV: {
                const destination = instruction.operands[0];
                this.registers.write(
                    destination,
                    this.readSecondOperand(instruction)
                );
                break;
            }

            case OPCODE.ADD: {
                const destination = instruction.operands[0];
                const left = this.registers.read(destination);
                const right = this.readSecondOperand(instruction);
                this.registers.write(
                    destination,
                    this.add16(left, right)
                );
                break;
            }

            case OPCODE.SUB: {
                const destination = instruction.operands[0];
                const left = this.registers.read(destination);
                const right = this.readSecondOperand(instruction);
                this.registers.write(
                    destination,
                    this.subtract16(left, right)
                );
                break;
            }

            case OPCODE.AND:
            case OPCODE.OR:
            case OPCODE.XOR: {
                const destination = instruction.operands[0];
                const left = this.registers.read(destination);
                const right = this.readSecondOperand(instruction);

                let result;

                if (instruction.opcode === OPCODE.AND) {
                    result = left & right;
                } else if (instruction.opcode === OPCODE.OR) {
                    result = left | right;
                } else {
                    result = left ^ right;
                }

                this.registers.write(destination, result);
                this.setFlags(result);
                break;
            }

            case OPCODE.SHL:
            case OPCODE.SHR: {
                const destination = instruction.operands[0];
                const amount = instruction.immediate ?? 0;
                const value = this.registers.read(destination);

                if (amount < 0) {
                    throw new RangeError("Negative shift count.");
                }

                const result = instruction.opcode === OPCODE.SHL
                    ? value << amount
                    : value >>> amount;

                this.registers.write(destination, result);
                this.setFlags(result);
                break;
            }

            case OPCODE.CMP: {
                const left = this.registers.read(instruction.operands[0]);
                const right = this.readSecondOperand(instruction);
                this.subtract16(left, right);
                break;
            }

            case OPCODE.LOAD: {
                const destination = instruction.operands[0];

                let address;
                if (instruction.operands.length === 2) {
                    address =
                        this.registers.read(instruction.operands[1]) +
                        (instruction.immediate ?? 0);
                } else {
                    address = instruction.immediate ?? 0;
                }

                this.registers.write(
                    destination,
                    this.memory.readWord(address)
                );
                break;
            }

            case OPCODE.STORE: {
                const source = instruction.operands[0];

                let address;
                if (instruction.operands.length === 2) {
                    address =
                        this.registers.read(instruction.operands[1]) +
                        (instruction.immediate ?? 0);
                } else {
                    address = instruction.immediate ?? 0;
                }

                this.memory.writeWord(
                    address,
                    this.registers.read(source)
                );
                break;
            }

            case OPCODE.JMP:
                this.validateProgramTarget(instruction.immediate);
                this.programCounter = instruction.immediate;
                break;

            case OPCODE.JZ:
                if (this.flags.zero) {
                    this.validateProgramTarget(instruction.immediate);
                    this.programCounter = instruction.immediate;
                }
                break;

            case OPCODE.HALT:
                this.halted = true;
                break;

            default:
                throw new Error(
                    `Unsupported opcode ${instruction.opcode}.`
                );
        }

        this.steps++;
    }

    run(maxSteps = 1000) {
        while (!this.halted) {
            if (this.steps >= maxSteps) {
                throw new Error("Execution limit reached.");
            }

            this.step();
        }
    }

    state() {
        return {
            pc: this.programCounter,
            registers: this.registers.dump(),
            flags: { ...this.flags },
            halted: this.halted,
            steps: this.steps
        };
    }
}


// ---------------------------------------------------------------------------
// 9. ASSEMBLY-LIKE PROGRAM
// ---------------------------------------------------------------------------

const program = [
    new Instruction(OPCODE.MOV, [0], 10),
    new Instruction(OPCODE.MOV, [1], 20),
    new Instruction(OPCODE.ADD, [0, 1]),
    new Instruction(OPCODE.STORE, [0], 100),
    new Instruction(OPCODE.LOAD, [2], 100),
    new Instruction(OPCODE.CMP, [2], 30),
    new Instruction(OPCODE.JZ, [], 8),
    new Instruction(OPCODE.MOV, [3], 999),
    new Instruction(OPCODE.HALT)
];

console.log("\nProgram:");
program.forEach((instruction, address) => {
    console.log(`${address.toString().padStart(2, "0")}: ${instruction}`);
});

const cpu = new VirtualCPU();
cpu.loadProgram(program);
cpu.run();

console.log("\nCPU state:");
console.log(cpu.state());


// ---------------------------------------------------------------------------
// 10. ASYNCHRONOUS EXECUTION
// ---------------------------------------------------------------------------

/*
 * JavaScript is particularly useful for demonstrating event-driven and
 * asynchronous execution. A CPU simulator can yield periodically so that
 * browser or server event loops remain responsive.
 */

function runWithYielding(cpu, maxSteps = 1000) {
    return new Promise((resolve, reject) => {
        function executeChunk() {
            try {
                let operationsThisChunk = 0;

                while (
                    !cpu.halted &&
                    cpu.steps < maxSteps &&
                    operationsThisChunk < 10
                ) {
                    cpu.step();
                    operationsThisChunk++;
                }

                if (cpu.halted) {
                    resolve(cpu.state());
                    return;
                }

                if (cpu.steps >= maxSteps) {
                    reject(new Error("Asynchronous execution limit reached."));
                    return;
                }

                // Yield to the JavaScript event loop.
                setTimeout(executeChunk, 0);
            } catch (error) {
                reject(error);
            }
        }

        executeChunk();
    });
}

const asynchronousCpu = new VirtualCPU();
asynchronousCpu.loadProgram([
    new Instruction(OPCODE.MOV, [0], 5),
    new Instruction(OPCODE.MOV, [1], 7),
    new Instruction(OPCODE.ADD, [0, 1]),
    new Instruction(OPCODE.HALT)
]);

runWithYielding(asynchronousCpu)
    .then(state => {
        console.log("\nAsynchronous CPU execution:");
        console.log(state);
    })
    .catch(error => {
        console.error("CPU error:", error.message);
    });


// ---------------------------------------------------------------------------
// 11. PERFORMANCE CONSIDERATIONS
// ---------------------------------------------------------------------------

function benchmarkRegisterOperations(iterations = 1_000_000) {
    const registers = new RegisterFile(8, 16);
    const start = performance.now();

    for (let i = 0; i < iterations; i++) {
        registers.write(0, registers.read(0) + 1);
    }

    const elapsed = performance.now() - start;

    return {
        iterations,
        elapsedMilliseconds: elapsed,
        finalValue: registers.read(0)
    };
}

console.log("\nPerformance experiment:");
console.log(benchmarkRegisterOperations());

/*
 * Performance observations:
 *
 * 1. Registers are modeled as array-like storage and are cheap to access.
 * 2. A real processor has dedicated register hardware rather than a
 *    JavaScript object.
 * 3. Real CPU performance also depends on pipelines, caches, branch
 *    prediction, instruction-level parallelism, memory latency, and compiler
 *    generated code.
 * 4. A virtual CPU adds interpretation overhead because every simulated
 *    instruction is executed by another program.
 */


// ---------------------------------------------------------------------------
// 12. EDGE CASES
// ---------------------------------------------------------------------------

console.log("\nEdge cases:");

try {
    const registers = new RegisterFile(8, 8);
    registers.write(0, 255);
    registers.write(1, 1);

    const wrapped = (registers.read(0) + registers.read(1)) & 0xFF;
    console.log("8-bit 255 + 1 =", wrapped);
} catch (error) {
    console.error(error.message);
}

try {
    const memory = new Memory(16);
    memory.readWord(15);
} catch (error) {
    console.log("Memory boundary error:", error.message);
}

try {
    new Instruction(0xFF);
} catch (error) {
    console.log("Opcode validation error:", error.message);
}

/*
 * Important implementation distinction:
 *
 * JavaScript Number is normally a floating-point IEEE-754 value. Bitwise
 * operators convert values to signed 32-bit integers. Therefore a JavaScript
 * CPU simulator must explicitly mask values when modeling fixed-width CPU
 * registers. Uint8Array and Uint32Array can help represent machine-like
 * storage, but they do not make JavaScript itself a hardware ISA.
 */
