/*
 * Instruction Cycle: Fetch, Decode, Execute, Memory Access, Write Back
 * ====================================================================
 *
 * A self-contained JavaScript study implementation of a simplified CPU.
 *
 * The implementation demonstrates:
 *   - registers
 *   - program counter
 *   - instruction register
 *   - memory
 *   - flags
 *   - fetch
 *   - decode
 *   - execute
 *   - memory access
 *   - write back
 *   - branches
 *   - stacks
 *   - exceptions
 *   - addressing modes
 *   - pipeline timing
 *   - hazards
 *   - cache behavior
 *   - performance calculations
 *
 * Run with:
 *   node instruction-cycle.js
 *
 * The simulator models concepts rather than a commercial processor ISA.
 */

"use strict";

// ---------------------------------------------------------------------------
// Instruction definitions
// ---------------------------------------------------------------------------

const Opcode = Object.freeze({
    NOP: "NOP",
    LOAD: "LOAD",
    STORE: "STORE",
    MOV: "MOV",
    ADD: "ADD",
    SUB: "SUB",
    MUL: "MUL",
    DIV: "DIV",
    CMP: "CMP",
    JMP: "JMP",
    JZ: "JZ",
    PUSH: "PUSH",
    POP: "POP",
    HALT: "HALT"
});

class CPUFault extends Error {
    constructor(message) {
        super(message);
        this.name = "CPUFault";
    }
}

class InvalidInstruction extends CPUFault {
    constructor(message) {
        super(message);
        this.name = "InvalidInstruction";
    }
}

class MemoryFault extends CPUFault {
    constructor(message) {
        super(message);
        this.name = "MemoryFault";
    }
}

class DivisionByZeroFault extends CPUFault {
    constructor(message) {
        super(message);
        this.name = "DivisionByZeroFault";
    }
}

class StackFault extends CPUFault {
    constructor(message) {
        super(message);
        this.name = "StackFault";
    }
}

// ---------------------------------------------------------------------------
// Instruction object
// ---------------------------------------------------------------------------

class Instruction {
    constructor(
        opcode,
        {
            destination = null,
            sourceA = null,
            sourceB = null,
            immediate = null,
            address = null
        } = {}
    ) {
        this.opcode = opcode;
        this.destination = destination;
        this.sourceA = sourceA;
        this.sourceB = sourceB;
        this.immediate = immediate;
        this.address = address;
    }

    toString() {
        const operands = [];

        if (this.destination !== null) {
            operands.push(this.destination);
        }

        if (this.sourceA !== null) {
            operands.push(this.sourceA);
        }

        if (this.sourceB !== null) {
            operands.push(this.sourceB);
        }

        if (this.immediate !== null) {
            operands.push(`#${this.immediate}`);
        }

        if (this.address !== null) {
            operands.push(`[${this.address}]`);
        }

        return operands.length > 0
            ? `${this.opcode} ${operands.join(", ")}`
            : this.opcode;
    }
}

// ---------------------------------------------------------------------------
// Flags
// ---------------------------------------------------------------------------

class Flags {
    constructor() {
        this.zero = false;
        this.negative = false;
        this.carry = false;
        this.overflow = false;
    }

    toString() {
        return (
            `Z=${Number(this.zero)} ` +
            `N=${Number(this.negative)} ` +
            `C=${Number(this.carry)} ` +
            `V=${Number(this.overflow)}`
        );
    }
}

// ---------------------------------------------------------------------------
// CPU
// ---------------------------------------------------------------------------

class CPU {
    constructor(memorySize = 256) {
        this.memorySize = memorySize;

        this.registers = {};
        for (let index = 0; index < 8; index += 1) {
            this.registers[`R${index}`] = 0;
        }

        this.memory = new Array(memorySize).fill(0);

        // PC identifies the next instruction to fetch.
        this.pc = 0;

        // IR stores the currently fetched instruction.
        this.ir = null;

        // MAR and MDR model memory-address and memory-data registers.
        this.mar = null;
        this.mdr = null;

        // Stack grows downward in this educational model.
        this.sp = memorySize - 1;

        this.flags = new Flags();
        this.halted = false;
        this.cycleCount = 0;
        this.instructionCount = 0;
    }

    validateRegister(name) {
        if (!Object.prototype.hasOwnProperty.call(this.registers, name)) {
            throw new InvalidInstruction(`Unknown register: ${name}`);
        }
    }

    readRegister(name) {
        this.validateRegister(name);
        return this.registers[name];
    }

    writeRegister(name, value) {
        this.validateRegister(name);
        this.registers[name] = value;
    }

    validateMemoryAddress(address) {
        if (
            !Number.isInteger(address) ||
            address < 0 ||
            address >= this.memorySize
        ) {
            throw new MemoryFault(
                `Invalid memory address: ${address}`
            );
        }
    }

    readMemory(address) {
        this.validateMemoryAddress(address);

        // MAR identifies the location being accessed.
        this.mar = address;

        // MDR receives the data read from memory.
        this.mdr = this.memory[address];

        return this.mdr;
    }

    writeMemory(address, value) {
        this.validateMemoryAddress(address);

        this.mar = address;
        this.mdr = value;
        this.memory[address] = value;
    }

    updateArithmeticFlags(result) {
        this.flags.zero = result === 0;
        this.flags.negative = result < 0;

        // This simplified JavaScript model does not emulate a fixed-width
        // hardware integer ALU, so carry and overflow remain false.
        this.flags.carry = false;
        this.flags.overflow = false;
    }

    aluAdd(left, right) {
        const result = left + right;
        this.updateArithmeticFlags(result);
        return result;
    }

    aluSub(left, right) {
        const result = left - right;
        this.updateArithmeticFlags(result);
        return result;
    }

    aluMul(left, right) {
        const result = left * right;
        this.updateArithmeticFlags(result);
        return result;
    }

    aluDiv(left, right) {
        if (right === 0) {
            throw new DivisionByZeroFault("Division by zero");
        }

        const result = Math.trunc(left / right);
        this.updateArithmeticFlags(result);
        return result;
    }

    // -----------------------------------------------------------------------
    // FETCH
    // -----------------------------------------------------------------------

    fetch(program) {
        if (this.pc < 0 || this.pc >= program.length) {
            throw new InvalidInstruction(
                `PC ${this.pc} is outside the program`
            );
        }

        // Fetch obtains the instruction identified by the PC.
        this.ir = program[this.pc];

        // A fixed-size educational ISA advances PC after fetch.
        this.pc += 1;

        return this.ir;
    }

    // -----------------------------------------------------------------------
    // DECODE
    // -----------------------------------------------------------------------

    decode(instruction) {
        const decoded = {
            opcode: instruction.opcode,
            destination: instruction.destination,
            sourceA: instruction.sourceA,
            sourceB: instruction.sourceB,
            immediate: instruction.immediate,
            address: instruction.address
        };

        // Register reads conceptually happen as part of instruction decode.
        if (instruction.sourceA !== null) {
            decoded.valueA = this.readRegister(instruction.sourceA);
        }

        if (instruction.sourceB !== null) {
            decoded.valueB = this.readRegister(instruction.sourceB);
        }

        return decoded;
    }

    // -----------------------------------------------------------------------
    // EXECUTE
    // -----------------------------------------------------------------------

    execute(decoded) {
        const result = {};
        const { opcode } = decoded;

        switch (opcode) {
            case Opcode.NOP:
                return result;

            case Opcode.MOV:
                if (decoded.immediate !== null) {
                    result.value = decoded.immediate;
                } else if (decoded.sourceA !== null) {
                    result.value = this.readRegister(decoded.sourceA);
                } else {
                    throw new InvalidInstruction(
                        "MOV requires an immediate or source register"
                    );
                }
                return result;

            case Opcode.ADD:
                result.value = this.aluAdd(
                    decoded.valueA,
                    decoded.valueB
                );
                return result;

            case Opcode.SUB:
                result.value = this.aluSub(
                    decoded.valueA,
                    decoded.valueB
                );
                return result;

            case Opcode.MUL:
                result.value = this.aluMul(
                    decoded.valueA,
                    decoded.valueB
                );
                return result;

            case Opcode.DIV:
                result.value = this.aluDiv(
                    decoded.valueA,
                    decoded.valueB
                );
                return result;

            case Opcode.CMP:
                result.comparison = this.aluSub(
                    decoded.valueA,
                    decoded.valueB
                );
                return result;

            case Opcode.LOAD:
                if (decoded.address === null) {
                    throw new InvalidInstruction(
                        "LOAD requires a memory address"
                    );
                }

                result.memoryAddress = decoded.address;
                return result;

            case Opcode.STORE:
                if (decoded.address === null) {
                    throw new InvalidInstruction(
                        "STORE requires a memory address"
                    );
                }

                if (decoded.sourceA === null) {
                    throw new InvalidInstruction(
                        "STORE requires a source register"
                    );
                }

                result.memoryAddress = decoded.address;
                result.storeValue = this.readRegister(decoded.sourceA);
                return result;

            case Opcode.JMP:
                if (decoded.address === null) {
                    throw new InvalidInstruction(
                        "JMP requires a target address"
                    );
                }

                result.branchTarget = decoded.address;
                return result;

            case Opcode.JZ:
                if (decoded.address === null) {
                    throw new InvalidInstruction(
                        "JZ requires a target address"
                    );
                }

                if (this.flags.zero) {
                    result.branchTarget = decoded.address;
                }

                return result;

            case Opcode.PUSH:
            case Opcode.POP:
            case Opcode.HALT:
                return result;

            default:
                throw new InvalidInstruction(
                    `Unsupported opcode: ${opcode}`
                );
        }
    }

    // -----------------------------------------------------------------------
    // MEMORY ACCESS
    // -----------------------------------------------------------------------

    memoryAccess(decoded, result) {
        switch (decoded.opcode) {
            case Opcode.LOAD:
                result.value = this.readMemory(
                    result.memoryAddress
                );
                break;

            case Opcode.STORE:
                this.writeMemory(
                    result.memoryAddress,
                    result.storeValue
                );
                break;

            case Opcode.PUSH:
                if (decoded.sourceA === null) {
                    throw new InvalidInstruction(
                        "PUSH requires a source register"
                    );
                }

                if (this.sp <= 0) {
                    throw new StackFault("Stack overflow");
                }

                this.memory[this.sp] =
                    this.readRegister(decoded.sourceA);

                this.sp -= 1;
                break;

            case Opcode.POP:
                if (decoded.destination === null) {
                    throw new InvalidInstruction(
                        "POP requires a destination register"
                    );
                }

                if (this.sp >= this.memorySize - 1) {
                    throw new StackFault("Stack underflow");
                }

                this.sp += 1;
                result.value = this.memory[this.sp];
                break;

            default:
                break;
        }
    }

    // -----------------------------------------------------------------------
    // WRITE BACK
    // -----------------------------------------------------------------------

    writeBack(decoded, result) {
        const registerWritingOpcodes = new Set([
            Opcode.MOV,
            Opcode.ADD,
            Opcode.SUB,
            Opcode.MUL,
            Opcode.DIV,
            Opcode.LOAD,
            Opcode.POP
        ]);

        if (registerWritingOpcodes.has(decoded.opcode)) {
            if (decoded.destination === null) {
                throw new InvalidInstruction(
                    `${decoded.opcode} requires a destination`
                );
            }

            if (!Object.prototype.hasOwnProperty.call(result, "value")) {
                throw new InvalidInstruction(
                    `${decoded.opcode} has no result to write back`
                );
            }

            this.writeRegister(
                decoded.destination,
                result.value
            );
        }

        if (
            decoded.opcode === Opcode.JMP ||
            decoded.opcode === Opcode.JZ
        ) {
            if (Object.prototype.hasOwnProperty.call(
                result,
                "branchTarget"
            )) {
                this.pc = result.branchTarget;
            }
        }

        if (decoded.opcode === Opcode.HALT) {
            this.halted = true;
        }
    }

    // -----------------------------------------------------------------------
    // Complete instruction cycle
    // -----------------------------------------------------------------------

    step(program, trace = false) {
        if (this.halted) {
            return;
        }

        const instructionPc = this.pc;

        // Five stages are performed in sequence in this non-pipelined model.
        const instruction = this.fetch(program);
        const decoded = this.decode(instruction);
        const result = this.execute(decoded);
        this.memoryAccess(decoded, result);
        this.writeBack(decoded, result);

        this.cycleCount += 1;
        this.instructionCount += 1;

        if (trace) {
            console.log(
                `Cycle ${String(this.cycleCount).padStart(3, "0")} | ` +
                `PC=${String(instructionPc).padStart(3, "0")} | ` +
                `${instruction.toString().padEnd(24)} | ` +
                `R1=${String(this.registers.R1).padStart(4)} ` +
                `R2=${String(this.registers.R2).padStart(4)} ` +
                `R3=${String(this.registers.R3).padStart(4)} | ` +
                this.flags.toString()
            );
        }
    }

    run(program, trace = false, maxSteps = 1000) {
        let steps = 0;

        while (!this.halted) {
            if (steps >= maxSteps) {
                throw new Error(
                    "Maximum execution steps reached; possible infinite loop."
                );
            }

            this.step(program, trace);
            steps += 1;
        }
    }

    dumpState() {
        console.log("\nCPU STATE");
        console.log("-".repeat(60));
        console.log(`PC:            ${this.pc}`);
        console.log(`IR:            ${this.ir}`);
        console.log(`MAR:           ${this.mar}`);
        console.log(`MDR:           ${this.mdr}`);
        console.log(`SP:            ${this.sp}`);
        console.log(`Flags:         ${this.flags}`);
        console.log(`Halted:        ${this.halted}`);
        console.log(`Cycles:        ${this.cycleCount}`);
        console.log(`Instructions:  ${this.instructionCount}`);
        console.log("Registers:", this.registers);
    }
}

// ---------------------------------------------------------------------------
// Basic example
// ---------------------------------------------------------------------------

function basicArithmeticExample() {
    console.log("\n" + "=".repeat(72));
    console.log("EXAMPLE 1: BASIC ARITHMETIC");
    console.log("=".repeat(72));

    const cpu = new CPU();

    const program = [
        new Instruction(Opcode.MOV, {
            destination: "R1",
            immediate: 12
        }),
        new Instruction(Opcode.MOV, {
            destination: "R2",
            immediate: 8
        }),
        new Instruction(Opcode.ADD, {
            destination: "R3",
            sourceA: "R1",
            sourceB: "R2"
        }),
        new Instruction(Opcode.HALT)
    ];

    cpu.run(program, true);
    cpu.dumpState();

    console.assert(
        cpu.registers.R3 === 20,
        "R3 should equal 20"
    );
}

// ---------------------------------------------------------------------------
// Memory example
// ---------------------------------------------------------------------------

function memoryExample() {
    console.log("\n" + "=".repeat(72));
    console.log("EXAMPLE 2: MEMORY ACCESS");
    console.log("=".repeat(72));

    const cpu = new CPU();

    // Initial data is already present in memory before execution.
    cpu.memory[100] = 42;

    const program = [
        new Instruction(Opcode.LOAD, {
            destination: "R1",
            address: 100
        }),
        new Instruction(Opcode.MOV, {
            destination: "R2",
            immediate: 8
        }),
        new Instruction(Opcode.ADD, {
            destination: "R3",
            sourceA: "R1",
            sourceB: "R2"
        }),
        new Instruction(Opcode.STORE, {
            sourceA: "R3",
            address: 101
        }),
        new Instruction(Opcode.HALT)
    ];

    cpu.run(program, true);

    console.log(`Memory[100] = ${cpu.memory[100]}`);
    console.log(`Memory[101] = ${cpu.memory[101]}`);

    console.assert(cpu.memory[101] === 50);
}

// ---------------------------------------------------------------------------
// Branching example
// ---------------------------------------------------------------------------

function branchingExample() {
    console.log("\n" + "=".repeat(72));
    console.log("EXAMPLE 3: FLAGS AND CONDITIONAL BRANCHING");
    console.log("=".repeat(72));

    const cpu = new CPU();

    const program = [
        new Instruction(Opcode.MOV, {
            destination: "R1",
            immediate: 10
        }),
        new Instruction(Opcode.MOV, {
            destination: "R2",
            immediate: 10
        }),
        new Instruction(Opcode.CMP, {
            sourceA: "R1",
            sourceB: "R2"
        }),
        new Instruction(Opcode.JZ, {
            address: 5
        }),
        new Instruction(Opcode.MOV, {
            destination: "R3",
            immediate: 999
        }),
        new Instruction(Opcode.MOV, {
            destination: "R3",
            immediate: 123
        }),
        new Instruction(Opcode.HALT)
    ];

    cpu.run(program, true);

    console.log(`R3 = ${cpu.registers.R3}`);
    console.assert(cpu.registers.R3 === 123);
}

// ---------------------------------------------------------------------------
// Stack example
// ---------------------------------------------------------------------------

function stackExample() {
    console.log("\n" + "=".repeat(72));
    console.log("EXAMPLE 4: STACK");
    console.log("=".repeat(72));

    const cpu = new CPU();

    const program = [
        new Instruction(Opcode.MOV, {
            destination: "R1",
            immediate: 55
        }),
        new Instruction(Opcode.PUSH, {
            sourceA: "R1"
        }),
        new Instruction(Opcode.MOV, {
            destination: "R1",
            immediate: 99
        }),
        new Instruction(Opcode.POP, {
            destination: "R2"
        }),
        new Instruction(Opcode.HALT)
    ];

    cpu.run(program, true);

    console.log(`R1 = ${cpu.registers.R1}`);
    console.log(`R2 = ${cpu.registers.R2}`);

    console.assert(cpu.registers.R2 === 55);
}

// ---------------------------------------------------------------------------
// Pipeline timing
// ---------------------------------------------------------------------------

function pipelineCycleCount(instructionCount, stageCount = 5) {
    if (instructionCount <= 0) {
        return 0;
    }

    if (stageCount <= 0) {
        throw new RangeError("stageCount must be positive");
    }

    return stageCount + instructionCount - 1;
}

function pipelineExample() {
    console.log("\n" + "=".repeat(72));
    console.log("EXAMPLE 5: FIVE-STAGE PIPELINE");
    console.log("=".repeat(72));

    const instructions = ["I1", "I2", "I3", "I4"];
    const stages = ["F", "D", "E", "M", "W"];

    const cycles = pipelineCycleCount(
        instructions.length,
        stages.length
    );

    for (let cycle = 1; cycle <= cycles; cycle += 1) {
        const active = [];

        instructions.forEach((name, index) => {
            const stageIndex = cycle - index - 1;

            if (
                stageIndex >= 0 &&
                stageIndex < stages.length
            ) {
                active.push(`${name}:${stages[stageIndex]}`);
            }
        });

        console.log(
            `Cycle ${cycle}: ${active.join(" | ")}`
        );
    }

    console.log(`Ideal pipeline cycles: ${cycles}`);
}

// ---------------------------------------------------------------------------
// Hazard detection
// ---------------------------------------------------------------------------

function detectRawHazard(older, newer) {
    return newer.reads.filter(
        register => older.writes.includes(register)
    );
}

function hazardExample() {
    console.log("\n" + "=".repeat(72));
    console.log("EXAMPLE 6: RAW DATA HAZARD");
    console.log("=".repeat(72));

    const older = {
        name: "ADD R1, R2, R3",
        reads: ["R2", "R3"],
        writes: ["R1"]
    };

    const newer = {
        name: "SUB R4, R1, R5",
        reads: ["R1", "R5"],
        writes: ["R4"]
    };

    const hazards = detectRawHazard(older, newer);

    console.log(`Older: ${older.name}`);
    console.log(`Newer: ${newer.name}`);
    console.log(`RAW dependencies: ${hazards.join(", ")}`);
}

// ---------------------------------------------------------------------------
// Addressing modes
// ---------------------------------------------------------------------------

const AddressingMode = Object.freeze({
    IMMEDIATE: "IMMEDIATE",
    REGISTER: "REGISTER",
    DIRECT: "DIRECT",
    REGISTER_INDIRECT: "REGISTER_INDIRECT",
    BASE_OFFSET: "BASE_OFFSET"
});

function resolveAddress(
    mode,
    operand,
    registers,
    register = null,
    offset = 0
) {
    switch (mode) {
        case AddressingMode.IMMEDIATE:
            return operand;

        case AddressingMode.REGISTER:
            if (register === null) {
                throw new Error(
                    "REGISTER mode requires a register"
                );
            }
            return registers[register];

        case AddressingMode.DIRECT:
            return operand;

        case AddressingMode.REGISTER_INDIRECT:
            if (register === null) {
                throw new Error(
                    "REGISTER_INDIRECT requires a register"
                );
            }
            return registers[register];

        case AddressingMode.BASE_OFFSET:
            if (register === null) {
                throw new Error(
                    "BASE_OFFSET requires a base register"
                );
            }
            return registers[register] + offset;

        default:
            throw new Error(`Unsupported mode: ${mode}`);
    }
}

function addressingExample() {
    console.log("\n" + "=".repeat(72));
    console.log("EXAMPLE 7: ADDRESSING MODES");
    console.log("=".repeat(72));

    const registers = {
        R1: 100,
        R2: 20
    };

    console.log(
        "Immediate:",
        resolveAddress(
            AddressingMode.IMMEDIATE,
            42,
            registers
        )
    );

    console.log(
        "Register:",
        resolveAddress(
            AddressingMode.REGISTER,
            0,
            registers,
            "R2"
        )
    );

    console.log(
        "Direct:",
        resolveAddress(
            AddressingMode.DIRECT,
            120,
            registers
        )
    );

    console.log(
        "Register indirect:",
        resolveAddress(
            AddressingMode.REGISTER_INDIRECT,
            0,
            registers,
            "R1"
        )
    );

    console.log(
        "Base + offset:",
        resolveAddress(
            AddressingMode.BASE_OFFSET,
            0,
            registers,
            "R1",
            12
        )
    );
}

// ---------------------------------------------------------------------------
// Edge cases
// ---------------------------------------------------------------------------

function edgeCaseExample() {
    console.log("\n" + "=".repeat(72));
    console.log("EXAMPLE 8: EDGE CASES");
    console.log("=".repeat(72));

    const cpu = new CPU();

    try {
        cpu.readMemory(-1);
    } catch (error) {
        console.log(
            `Memory exception handled: ${error.message}`
        );
    }

    try {
        cpu.aluDiv(10, 0);
    } catch (error) {
        console.log(
            `Division exception handled: ${error.message}`
        );
    }

    try {
        cpu.readRegister("R99");
    } catch (error) {
        console.log(
            `Register exception handled: ${error.message}`
        );
    }

    try {
        cpu.run(
            [new Instruction(Opcode.JMP, { address: 0 })],
            false,
            5
        );
    } catch (error) {
        console.log(
            `Execution-limit exception handled: ${error.message}`
        );
    }
}

// ---------------------------------------------------------------------------
// Cache example
// ---------------------------------------------------------------------------

class DirectMappedCache {
    constructor(lineCount = 4) {
        if (lineCount <= 0) {
            throw new RangeError(
                "lineCount must be positive"
            );
        }

        this.lineCount = lineCount;
        this.lines = new Map();
        this.hits = 0;
        this.misses = 0;
    }

    access(address, memory) {
        const index = address % this.lineCount;

        if (
            this.lines.has(index) &&
            this.lines.get(index) === address
        ) {
            this.hits += 1;
            return memory[address];
        }

        this.misses += 1;
        this.lines.set(index, address);

        return memory[address];
    }

    get hitRate() {
        const accesses = this.hits + this.misses;
        return accesses === 0
            ? 0
            : this.hits / accesses;
    }
}

function cacheExample() {
    console.log("\n" + "=".repeat(72));
    console.log("EXAMPLE 9: CACHE HIT/MISS");
    console.log("=".repeat(72));

    const memory = Array.from(
        { length: 32 },
        (_, index) => index * 10
    );

    const cache = new DirectMappedCache(4);

    const addresses = [
        0, 0, 0, 1, 1,
        4, 4, 0, 8, 8
    ];

    for (const address of addresses) {
        const value = cache.access(address, memory);
        console.log(
            `Address ${String(address).padStart(2)} -> ${value}`
        );
    }

    console.log(`Hits: ${cache.hits}`);
    console.log(`Misses: ${cache.misses}`);
    console.log(
        `Hit rate: ${(cache.hitRate * 100).toFixed(2)}%`
    );
}

// ---------------------------------------------------------------------------
// Performance model
// ---------------------------------------------------------------------------

function cpuExecutionTime(
    instructionCount,
    cpi,
    frequencyHz
) {
    if (
        instructionCount < 0 ||
        cpi <= 0 ||
        frequencyHz <= 0
    ) {
        throw new RangeError(
            "Performance parameters must be positive."
        );
    }

    const cycles = instructionCount * cpi;
    const seconds = cycles / frequencyHz;

    return {
        cycles,
        seconds,
        instructionsPerSecond:
            instructionCount / seconds
    };
}

function performanceExample() {
    console.log("\n" + "=".repeat(72));
    console.log("EXAMPLE 10: CPU PERFORMANCE");
    console.log("=".repeat(72));

    const result = cpuExecutionTime(
        1_000_000,
        1.5,
        3_000_000_000
    );

    console.log(
        `Cycles: ${result.cycles.toLocaleString()}`
    );

    console.log(
        `Execution time: ${result.seconds.toFixed(9)} s`
    );

    console.log(
        `Instruction rate: ` +
        `${(result.instructionsPerSecond / 1e6).toFixed(2)} M/s`
    );
}

// ---------------------------------------------------------------------------
// Micro-operation example
// ---------------------------------------------------------------------------

function microOperationExample() {
    console.log("\n" + "=".repeat(72));
    console.log("EXAMPLE 11: MICRO-OPERATIONS");
    console.log("=".repeat(72));

    const microOperations = [
        "MAR <- PC",
        "IR <- InstructionMemory[MAR]",
        "PC <- PC + instruction_size",
        "Decode IR",
        "A <- R1",
        "B <- R2",
        "ALUOut <- A + B",
        "R3 <- ALUOut"
    ];

    microOperations.forEach(
        (operation, index) => {
            console.log(
                `${String(index + 1).padStart(2, "0")}. ${operation}`
            );
        }
    );
}

// ---------------------------------------------------------------------------
// Instruction classification
// ---------------------------------------------------------------------------

function classifyInstruction(opcode) {
    const arithmetic = new Set([
        Opcode.ADD,
        Opcode.SUB,
        Opcode.MUL,
        Opcode.DIV,
        Opcode.CMP
    ]);

    const memory = new Set([
        Opcode.LOAD,
        Opcode.STORE,
        Opcode.PUSH,
        Opcode.POP
    ]);

    const control = new Set([
        Opcode.JMP,
        Opcode.JZ,
        Opcode.HALT
    ]);

    if (arithmetic.has(opcode)) {
        return "Arithmetic / logic";
    }

    if (memory.has(opcode)) {
        return "Memory / stack";
    }

    if (control.has(opcode)) {
        return "Control flow";
    }

    if (opcode === Opcode.MOV) {
        return "Data transfer";
    }

    return "Other";
}

function classificationExample() {
    console.log("\n" + "=".repeat(72));
    console.log("EXAMPLE 12: INSTRUCTION CLASSES");
    console.log("=".repeat(72));

    const opcodes = [
        Opcode.MOV,
        Opcode.ADD,
        Opcode.LOAD,
        Opcode.STORE,
        Opcode.JMP,
        Opcode.HALT
    ];

    opcodes.forEach(opcode => {
        console.log(
            `${opcode.padEnd(8)} -> ${classifyInstruction(opcode)}`
        );
    });
}

// ---------------------------------------------------------------------------
// Self tests
// ---------------------------------------------------------------------------

function runSelfTests() {
    console.log("\n" + "=".repeat(72));
    console.log("SELF-TESTS");
    console.log("=".repeat(72));

    const cpu = new CPU();

    const arithmeticProgram = [
        new Instruction(Opcode.MOV, {
            destination: "R1",
            immediate: 9
        }),
        new Instruction(Opcode.MOV, {
            destination: "R2",
            immediate: 3
        }),
        new Instruction(Opcode.ADD, {
            destination: "R3",
            sourceA: "R1",
            sourceB: "R2"
        }),
        new Instruction(Opcode.SUB, {
            destination: "R4",
            sourceA: "R1",
            sourceB: "R2"
        }),
        new Instruction(Opcode.MUL, {
            destination: "R5",
            sourceA: "R1",
            sourceB: "R2"
        }),
        new Instruction(Opcode.DIV, {
            destination: "R6",
            sourceA: "R1",
            sourceB: "R2"
        }),
        new Instruction(Opcode.HALT)
    ];

    cpu.run(arithmeticProgram);

    console.assert(cpu.registers.R3 === 12);
    console.assert(cpu.registers.R4 === 6);
    console.assert(cpu.registers.R5 === 27);
    console.assert(cpu.registers.R6 === 3);

    const memoryCpu = new CPU();
    memoryCpu.memory[10] = 77;

    memoryCpu.run([
        new Instruction(Opcode.LOAD, {
            destination: "R1",
            address: 10
        }),
        new Instruction(Opcode.STORE, {
            sourceA: "R1",
            address: 11
        }),
        new Instruction(Opcode.HALT)
    ]);

    console.assert(memoryCpu.registers.R1 === 77);
    console.assert(memoryCpu.memory[11] === 77);

    try {
        cpu.aluDiv(10, 0);
        console.assert(
            false,
            "Division by zero should have thrown"
        );
    } catch (error) {
        console.assert(
            error instanceof DivisionByZeroFault
        );
    }

    console.log("Self-tests completed.");
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function main() {
    console.log("=".repeat(72));
    console.log("INSTRUCTION CYCLE EDUCATIONAL CPU");
    console.log("=".repeat(72));

    console.log(
        "\nFive conceptual stages: " +
        "Fetch -> Decode -> Execute -> Memory -> Write Back"
    );

    basicArithmeticExample();
    memoryExample();
    branchingExample();
    stackExample();
    pipelineExample();
    hazardExample();
    addressingExample();
    edgeCaseExample();
    cacheExample();
    performanceExample();
    microOperationExample();
    classificationExample();
    runSelfTests();

    console.log("\nSimulation complete.");
}

main();
