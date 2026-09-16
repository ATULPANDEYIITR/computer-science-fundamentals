/*
 * CPU Simulator: Central Processing Unit Fundamentals Through a Working Emulator
 *
 * This standalone JavaScript program demonstrates a small CPU architecture
 * with registers, memory, ALU operations, flags, PC, IR, stack operations,
 * branching, CALL/RET, tracing, input/output, assembly parsing, and
 * asynchronous execution.
 *
 * It can run in Node.js without external packages.
 */


// ============================================================================
// 1. CPU ARCHITECTURE
// ============================================================================

const OPCODE = Object.freeze({
    NOP: "NOP",
    LOAD: "LOAD",
    STORE: "STORE",
    MOV: "MOV",

    ADD: "ADD",
    SUB: "SUB",
    MUL: "MUL",
    DIV: "DIV",
    INC: "INC",
    DEC: "DEC",

    AND: "AND",
    OR: "OR",
    XOR: "XOR",
    NOT: "NOT",
    SHL: "SHL",
    SHR: "SHR",

    CMP: "CMP",
    JMP: "JMP",
    JZ: "JZ",
    JNZ: "JNZ",
    JN: "JN",
    JP: "JP",

    PUSH: "PUSH",
    POP: "POP",
    CALL: "CALL",
    RET: "RET",

    IN: "IN",
    OUT: "OUT",
    HALT: "HALT"
});


function instruction(opcode, ...operands) {
    return { opcode, operands };
}


// ============================================================================
// 2. FLAGS
// ============================================================================

class Flags {
    constructor() {
        this.reset();
    }

    reset() {
        this.zero = false;
        this.negative = false;
        this.carry = false;
        this.overflow = false;
    }

    toString() {
        return `Z=${Number(this.zero)} N=${Number(this.negative)} ` +
            `C=${Number(this.carry)} V=${Number(this.overflow)}`;
    }
}


// ============================================================================
// 3. ALU
// ============================================================================

class ALU {
    constructor(wordSize = 16) {
        if (wordSize < 4 || wordSize > 32) {
            throw new Error("wordSize must be between 4 and 32");
        }

        this.wordSize = wordSize;
        this.mask = 2 ** wordSize - 1;
        this.signBit = 2 ** (wordSize - 1);
    }

    normalize(value) {
        // JavaScript Number arithmetic is used here because this educational
        // CPU is limited to 32-bit-or-less words.
        return value & this.mask;
    }

    signed(value) {
        const normalized = this.normalize(value);

        if (normalized >= this.signBit) {
            return normalized - 2 ** this.wordSize;
        }

        return normalized;
    }

    setFlags(result, flags, carry = false, overflow = false) {
        const normalized = this.normalize(result);

        flags.zero = normalized === 0;
        flags.negative = normalized >= this.signBit;
        flags.carry = carry;
        flags.overflow = overflow;

        return normalized;
    }

    add(left, right, flags) {
        const raw = left + right;
        const result = this.normalize(raw);

        const leftSigned = this.signed(left);
        const rightSigned = this.signed(right);
        const resultSigned = this.signed(result);

        const overflow =
            (leftSigned >= 0 && rightSigned >= 0 && resultSigned < 0) ||
            (leftSigned < 0 && rightSigned < 0 && resultSigned >= 0);

        return this.setFlags(
            result,
            flags,
            raw > this.mask,
            overflow
        );
    }

    subtract(left, right, flags) {
        const result = this.normalize(left - right);

        const leftSigned = this.signed(left);
        const rightSigned = this.signed(right);
        const resultSigned = this.signed(result);

        const overflow =
            (leftSigned >= 0 && rightSigned < 0 && resultSigned < 0) ||
            (leftSigned < 0 && rightSigned >= 0 && resultSigned >= 0);

        return this.setFlags(
            result,
            flags,
            left >= right,
            overflow
        );
    }

    multiply(left, right, flags) {
        const raw = left * right;
        return this.setFlags(raw, flags, raw > this.mask);
    }

    divide(left, right, flags) {
        if (right === 0) {
            throw new Error("Division by zero");
        }

        return this.setFlags(Math.floor(left / right), flags);
    }

    logical(operation, left, right, flags) {
        let result;

        switch (operation) {
            case OPCODE.AND:
                result = left & right;
                break;
            case OPCODE.OR:
                result = left | right;
                break;
            case OPCODE.XOR:
                result = left ^ right;
                break;
            default:
                throw new Error(`Unknown logical operation: ${operation}`);
        }

        return this.setFlags(result, flags);
    }

    not(value, flags) {
        return this.setFlags(~value, flags);
    }

    shiftLeft(value, amount, flags) {
        if (!Number.isInteger(amount) || amount < 0) {
            throw new Error("Shift amount must be a non-negative integer");
        }

        const carry = amount > 0 && amount <= this.wordSize
            ? Boolean(value & (2 ** (this.wordSize - amount)))
            : false;

        return this.setFlags(value * 2 ** amount, flags, carry);
    }

    shiftRight(value, amount, flags) {
        if (!Number.isInteger(amount) || amount < 0) {
            throw new Error("Shift amount must be a non-negative integer");
        }

        const carry = amount > 0 && amount <= this.wordSize
            ? Boolean(value & (2 ** (amount - 1)))
            : false;

        return this.setFlags(Math.floor(value / 2 ** amount), flags, carry);
    }
}


// ============================================================================
// 4. CPU
// ============================================================================

class CPU {
    constructor({
        wordSize = 16,
        memorySize = 256,
        registerCount = 8
    } = {}) {
        this.wordSize = wordSize;
        this.memorySize = memorySize;
        this.registerCount = registerCount;

        this.mask = 2 ** wordSize - 1;

        this.registers = new Array(registerCount).fill(0);
        this.memory = new Array(memorySize).fill(0);

        this.pc = 0;
        this.sp = memorySize - 1;
        this.ir = null;

        this.flags = new Flags();
        this.alu = new ALU(wordSize);

        this.program = [];
        this.halted = false;

        this.cycles = 0;
        this.instructionsExecuted = 0;

        this.outputBuffer = [];
        this.inputBuffer = [];

        this.traceEnabled = false;
    }

    registerIndex(register) {
        if (typeof register !== "string" || !/^R\d+$/i.test(register)) {
            throw new Error(`Invalid register: ${register}`);
        }

        const index = Number(register.slice(1));

        if (index < 0 || index >= this.registerCount) {
            throw new Error(`Register out of range: ${register}`);
        }

        return index;
    }

    readRegister(register) {
        return this.registers[this.registerIndex(register)];
    }

    writeRegister(register, value) {
        const index = this.registerIndex(register);
        this.registers[index] = value & this.mask;
    }

    validateMemoryAddress(address) {
        if (!Number.isInteger(address)) {
            throw new Error("Memory address must be an integer");
        }

        if (address < 0 || address >= this.memorySize) {
            throw new Error(`Invalid memory address: ${address}`);
        }
    }

    readMemory(address) {
        this.validateMemoryAddress(address);
        return this.memory[address];
    }

    writeMemory(address, value) {
        this.validateMemoryAddress(address);
        this.memory[address] = value & this.mask;
    }

    resolveValue(operand) {
        if (typeof operand === "string" && /^R\d+$/i.test(operand)) {
            return this.readRegister(operand);
        }

        if (typeof operand === "number" && Number.isFinite(operand)) {
            return operand & this.mask;
        }

        throw new Error(`Unsupported operand: ${operand}`);
    }

    loadProgram(program, startAddress = 0) {
        if (
            startAddress < 0 ||
            startAddress + program.length > this.memorySize
        ) {
            throw new Error("Program does not fit in memory");
        }

        this.program = [...program];
        this.pc = startAddress;
        this.halted = false;
        this.ir = null;
        this.cycles = 0;
        this.instructionsExecuted = 0;
        this.outputBuffer = [];
    }

    fetch() {
        if (this.pc < 0 || this.pc >= this.program.length) {
            throw new Error(
                `PC ${this.pc} points outside the loaded program`
            );
        }

        this.ir = this.program[this.pc];
        this.pc += 1;

        return this.ir;
    }

    validateProgramAddress(address) {
        if (!Number.isInteger(address)) {
            throw new Error("Program address must be an integer");
        }

        if (address < 0 || address >= this.program.length) {
            throw new Error(`Invalid program address: ${address}`);
        }
    }

    push(value) {
        if (this.sp < 0) {
            throw new Error("Stack overflow");
        }

        this.writeMemory(this.sp, value);
        this.sp -= 1;
    }

    pop() {
        if (this.sp >= this.memorySize - 1) {
            throw new Error("Stack underflow");
        }

        this.sp += 1;
        return this.readMemory(this.sp);
    }

    execute(currentInstruction) {
        const { opcode, operands } = currentInstruction;

        switch (opcode) {
            case OPCODE.NOP:
                return;

            case OPCODE.HALT:
                this.halted = true;
                return;

            case OPCODE.MOV: {
                const [destination, source] = operands;
                this.writeRegister(
                    destination,
                    this.resolveValue(source)
                );
                return;
            }

            case OPCODE.LOAD: {
                const [destination, address] = operands;
                this.writeRegister(
                    destination,
                    this.readMemory(address)
                );
                return;
            }

            case OPCODE.STORE: {
                const [source, address] = operands;
                this.writeMemory(
                    address,
                    this.readRegister(source)
                );
                return;
            }

            case OPCODE.ADD:
            case OPCODE.SUB:
            case OPCODE.MUL:
            case OPCODE.DIV:
            case OPCODE.AND:
            case OPCODE.OR:
            case OPCODE.XOR: {
                const [destination, left, right] = operands;

                const leftValue = this.resolveValue(left);
                const rightValue = this.resolveValue(right);

                let result;

                if (opcode === OPCODE.ADD) {
                    result = this.alu.add(
                        leftValue,
                        rightValue,
                        this.flags
                    );
                } else if (opcode === OPCODE.SUB) {
                    result = this.alu.subtract(
                        leftValue,
                        rightValue,
                        this.flags
                    );
                } else if (opcode === OPCODE.MUL) {
                    result = this.alu.multiply(
                        leftValue,
                        rightValue,
                        this.flags
                    );
                } else if (opcode === OPCODE.DIV) {
                    result = this.alu.divide(
                        leftValue,
                        rightValue,
                        this.flags
                    );
                } else {
                    result = this.alu.logical(
                        opcode,
                        leftValue,
                        rightValue,
                        this.flags
                    );
                }

                this.writeRegister(destination, result);
                return;
            }

            case OPCODE.INC: {
                const [register] = operands;
                const result = this.alu.add(
                    this.readRegister(register),
                    1,
                    this.flags
                );
                this.writeRegister(register, result);
                return;
            }

            case OPCODE.DEC: {
                const [register] = operands;
                const result = this.alu.subtract(
                    this.readRegister(register),
                    1,
                    this.flags
                );
                this.writeRegister(register, result);
                return;
            }

            case OPCODE.NOT: {
                const [destination, source] = operands;
                this.writeRegister(
                    destination,
                    this.alu.not(
                        this.resolveValue(source),
                        this.flags
                    )
                );
                return;
            }

            case OPCODE.SHL: {
                const [destination, source, amount] = operands;
                this.writeRegister(
                    destination,
                    this.alu.shiftLeft(
                        this.resolveValue(source),
                        this.resolveValue(amount),
                        this.flags
                    )
                );
                return;
            }

            case OPCODE.SHR: {
                const [destination, source, amount] = operands;
                this.writeRegister(
                    destination,
                    this.alu.shiftRight(
                        this.resolveValue(source),
                        this.resolveValue(amount),
                        this.flags
                    )
                );
                return;
            }

            case OPCODE.CMP: {
                const [left, right] = operands;

                this.alu.subtract(
                    this.resolveValue(left),
                    this.resolveValue(right),
                    this.flags
                );
                return;
            }

            case OPCODE.JMP:
            case OPCODE.JZ:
            case OPCODE.JNZ:
            case OPCODE.JN:
            case OPCODE.JP: {
                const [target] = operands;

                let shouldBranch = false;

                if (opcode === OPCODE.JMP) {
                    shouldBranch = true;
                } else if (opcode === OPCODE.JZ) {
                    shouldBranch = this.flags.zero;
                } else if (opcode === OPCODE.JNZ) {
                    shouldBranch = !this.flags.zero;
                } else if (opcode === OPCODE.JN) {
                    shouldBranch = this.flags.negative;
                } else if (opcode === OPCODE.JP) {
                    shouldBranch = !this.flags.negative;
                }

                if (shouldBranch) {
                    this.validateProgramAddress(target);
                    this.pc = target;
                }

                return;
            }

            case OPCODE.PUSH: {
                const [source] = operands;
                this.push(this.resolveValue(source));
                return;
            }

            case OPCODE.POP: {
                const [destination] = operands;
                this.writeRegister(destination, this.pop());
                return;
            }

            case OPCODE.CALL: {
                const [target] = operands;
                this.validateProgramAddress(target);

                this.push(this.pc);
                this.pc = target;
                return;
            }

            case OPCODE.RET:
                this.pc = this.pop();
                this.validateProgramAddress(this.pc);
                return;

            case OPCODE.IN: {
                const [destination] = operands;

                if (this.inputBuffer.length === 0) {
                    throw new Error("IN requires an input value");
                }

                this.writeRegister(
                    destination,
                    this.inputBuffer.shift()
                );

                return;
            }

            case OPCODE.OUT: {
                const [source] = operands;
                this.outputBuffer.push(
                    this.resolveValue(source)
                );
                return;
            }

            default:
                throw new Error(`Unsupported opcode: ${opcode}`);
        }
    }

    cycleCost(currentInstruction) {
        const costs = {
            NOP: 1,
            MOV: 1,
            LOAD: 3,
            STORE: 3,
            ADD: 1,
            SUB: 1,
            MUL: 3,
            DIV: 8,
            INC: 1,
            DEC: 1,
            AND: 1,
            OR: 1,
            XOR: 1,
            NOT: 1,
            SHL: 1,
            SHR: 1,
            CMP: 1,
            JMP: 1,
            JZ: 1,
            JNZ: 1,
            JN: 1,
            JP: 1,
            PUSH: 2,
            POP: 2,
            CALL: 3,
            RET: 3,
            IN: 2,
            OUT: 2,
            HALT: 1
        };

        return costs[currentInstruction.opcode] ?? 1;
    }

    step() {
        if (this.halted) {
            return;
        }

        const oldPC = this.pc;
        const currentInstruction = this.fetch();

        if (this.traceEnabled) {
            console.log(
                `PC=${String(oldPC).padStart(3, "0")} | ` +
                `${formatInstruction(currentInstruction)} | ` +
                `before=${JSON.stringify(this.registers)}`
            );
        }

        this.execute(currentInstruction);

        this.instructionsExecuted += 1;
        this.cycles += this.cycleCost(currentInstruction);

        if (this.traceEnabled) {
            console.log(
                `       ${" ".repeat(24)} | ` +
                `after=${JSON.stringify(this.registers)} | ` +
                `${this.flags}`
            );
        }
    }

    run(maxSteps = 100000) {
        let steps = 0;

        while (!this.halted) {
            if (steps >= maxSteps) {
                throw new Error(
                    "Maximum instruction count reached; possible infinite loop"
                );
            }

            this.step();
            steps += 1;
        }
    }

    // Asynchronous execution illustrates an application-level simulator
    // that periodically yields control to the JavaScript event loop.
    async runAsync(maxSteps = 100000, batchSize = 1000) {
        let steps = 0;

        while (!this.halted) {
            for (
                let batch = 0;
                batch < batchSize && !this.halted;
                batch += 1
            ) {
                if (steps >= maxSteps) {
                    throw new Error(
                        "Maximum instruction count reached"
                    );
                }

                this.step();
                steps += 1;
            }

            // setImmediate is a Node.js event-loop mechanism. It prevents
            // a very large simulated workload from monopolizing the loop.
            await new Promise(resolve => setImmediate(resolve));
        }
    }

    dumpState() {
        console.log("\nCPU STATE");

        this.registers.forEach((value, index) => {
            console.log(
                `R${index}: unsigned=${value} ` +
                `signed=${this.alu.signed(value)} ` +
                `hex=0x${value.toString(16).padStart(4, "0")}`
            );
        });

        console.log(`PC: ${this.pc}`);
        console.log(`SP: ${this.sp}`);
        console.log(`IR: ${this.ir ? formatInstruction(this.ir) : "none"}`);
        console.log(`FLAGS: ${this.flags}`);
        console.log(`INSTRUCTIONS: ${this.instructionsExecuted}`);
        console.log(`CYCLES: ${this.cycles}`);
        console.log(`OUTPUT: ${JSON.stringify(this.outputBuffer)}`);
    }
}


// ============================================================================
// 5. FORMATTING
// ============================================================================

function formatInstruction(currentInstruction) {
    if (currentInstruction.operands.length === 0) {
        return currentInstruction.opcode;
    }

    return `${currentInstruction.opcode} ` +
        currentInstruction.operands.join(", ");
}


// ============================================================================
// 6. SIMPLE ASSEMBLER
// ============================================================================

class Assembler {
    parseOperand(token) {
        token = token.trim();

        if (/^R\d+$/i.test(token)) {
            return token.toUpperCase();
        }

        if (/^0x[0-9a-f]+$/i.test(token)) {
            return Number.parseInt(token, 16);
        }

        if (/^0b[01]+$/i.test(token)) {
            return Number.parseInt(token.slice(2), 2);
        }

        if (/^-?\d+$/.test(token)) {
            return Number(token);
        }

        return token;
    }

    firstPass(lines) {
        const labels = new Map();
        let address = 0;

        for (const rawLine of lines) {
            let line = rawLine.split(";", 1)[0].trim();

            if (!line) {
                continue;
            }

            if (line.includes(":")) {
                const [label, ...rest] = line.split(":");
                const cleanLabel = label.trim();

                if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(cleanLabel)) {
                    throw new Error(`Invalid label: ${cleanLabel}`);
                }

                if (labels.has(cleanLabel)) {
                    throw new Error(`Duplicate label: ${cleanLabel}`);
                }

                labels.set(cleanLabel, address);
                line = rest.join(":").trim();

                if (!line) {
                    continue;
                }
            }

            address += 1;
        }

        return labels;
    }

    assemble(source) {
        const lines = source.split(/\r?\n/);
        const labels = this.firstPass(lines);
        const program = [];

        for (const rawLine of lines) {
            let line = rawLine.split(";", 1)[0].trim();

            if (!line) {
                continue;
            }

            if (line.includes(":")) {
                line = line.split(":").slice(1).join(":").trim();

                if (!line) {
                    continue;
                }
            }

            const parts = line.split(/\s+/, 2);
            const opcode = parts[0].toUpperCase();
            const operandText = parts[1] ?? "";

            if (!Object.values(OPCODE).includes(opcode)) {
                throw new Error(`Unknown opcode: ${opcode}`);
            }

            const operands = operandText
                ? operandText
                    .split(",")
                    .map(token => this.parseOperand(token))
                : [];

            const branchInstructions = new Set([
                OPCODE.JMP,
                OPCODE.JZ,
                OPCODE.JNZ,
                OPCODE.JN,
                OPCODE.JP,
                OPCODE.CALL
            ]);

            if (branchInstructions.has(opcode)) {
                if (
                    operands.length !== 1 ||
                    typeof operands[0] === "string" &&
                    !/^R\d+$/i.test(operands[0])
                ) {
                    const label = operands[0];

                    if (!labels.has(label)) {
                        throw new Error(`Undefined label: ${label}`);
                    }

                    operands[0] = labels.get(label);
                }
            }

            program.push(instruction(opcode, ...operands));
        }

        return program;
    }
}


// ============================================================================
// 7. TEST HELPERS
// ============================================================================

function runExample(title, program, {
    input = [],
    trace = false
} = {}) {
    console.log(`\n${"=".repeat(78)}`);
    console.log(title);
    console.log("=".repeat(78));

    const cpu = new CPU();

    cpu.loadProgram(program);
    cpu.inputBuffer.push(...input);
    cpu.traceEnabled = trace;

    cpu.run();
    cpu.dumpState();

    return cpu;
}


// ============================================================================
// 8. BEGINNER PROGRAM
// ============================================================================

let cpu = runExample(
    "1. Add Two Numbers",
    [
        instruction(OPCODE.MOV, "R0", 12),
        instruction(OPCODE.MOV, "R1", 30),
        instruction(OPCODE.ADD, "R2", "R0", "R1"),
        instruction(OPCODE.OUT, "R2"),
        instruction(OPCODE.HALT)
    ]
);

console.log("Expected output: [42]");
console.log("Actual output:", cpu.outputBuffer);


// ============================================================================
// 9. MEMORY PROGRAM
// ============================================================================

cpu = runExample(
    "2. Register and Memory Interaction",
    [
        instruction(OPCODE.MOV, "R0", 1234),
        instruction(OPCODE.STORE, "R0", 100),
        instruction(OPCODE.LOAD, "R1", 100),
        instruction(OPCODE.OUT, "R1"),
        instruction(OPCODE.HALT)
    ]
);

console.log("Memory[100] =", cpu.memory[100]);


// ============================================================================
// 10. BRANCHING
// ============================================================================

cpu = runExample(
    "3. Comparison and Conditional Branch",
    [
        instruction(OPCODE.MOV, "R0", 50),
        instruction(OPCODE.MOV, "R1", 50),
        instruction(OPCODE.CMP, "R0", "R1"),
        instruction(OPCODE.JZ, 6),
        instruction(OPCODE.MOV, "R2", 0),
        instruction(OPCODE.JMP, 7),
        instruction(OPCODE.MOV, "R2", 1),
        instruction(OPCODE.OUT, "R2"),
        instruction(OPCODE.HALT)
    ]
);


// ============================================================================
// 11. LOOP
// ============================================================================

cpu = runExample(
    "4. Loop: Sum 1 Through 10",
    [
        instruction(OPCODE.MOV, "R0", 1),
        instruction(OPCODE.MOV, "R1", 0),
        instruction(OPCODE.MOV, "R2", 11),

        instruction(OPCODE.ADD, "R1", "R1", "R0"),
        instruction(OPCODE.INC, "R0"),
        instruction(OPCODE.CMP, "R0", "R2"),
        instruction(OPCODE.JNZ, 3),

        instruction(OPCODE.OUT, "R1"),
        instruction(OPCODE.HALT)
    ]
);


// ============================================================================
// 12. CALL / RET
// ============================================================================

cpu = runExample(
    "5. CALL and RET",
    [
        instruction(OPCODE.CALL, 4),
        instruction(OPCODE.OUT, "R0"),
        instruction(OPCODE.HALT),
        instruction(OPCODE.NOP),

        instruction(OPCODE.MOV, "R0", 7),
        instruction(OPCODE.MOV, "R1", 6),
        instruction(OPCODE.MUL, "R0", "R0", "R1"),
        instruction(OPCODE.RET)
    ]
);


// ============================================================================
// 13. ASSEMBLY LANGUAGE
// ============================================================================

const assemblySource = `
; Calculate 1 + 2 + 3 + 4 + 5

MOV R0, 1
MOV R1, 0
MOV R2, 6

loop:
ADD R1, R1, R0
INC R0
CMP R0, R2
JNZ loop

OUT R1
HALT
`;

const assembler = new Assembler();
const assemblyProgram = assembler.assemble(assemblySource);

cpu = runExample(
    "6. Text Assembly With Labels",
    assemblyProgram
);


// ============================================================================
// 14. INPUT / OUTPUT
// ============================================================================

cpu = runExample(
    "7. Input and Output",
    [
        instruction(OPCODE.IN, "R0"),
        instruction(OPCODE.IN, "R1"),
        instruction(OPCODE.ADD, "R2", "R0", "R1"),
        instruction(OPCODE.OUT, "R2"),
        instruction(OPCODE.HALT)
    ],
    {
        input: [100, 23]
    }
);


// ============================================================================
// 15. TRACE MODE
// ============================================================================

runExample(
    "8. Instruction-Level Trace",
    [
        instruction(OPCODE.MOV, "R0", 5),
        instruction(OPCODE.MOV, "R1", 8),
        instruction(OPCODE.ADD, "R2", "R0", "R1"),
        instruction(OPCODE.OUT, "R2"),
        instruction(OPCODE.HALT)
    ],
    {
        trace: true
    }
);


// ============================================================================
// 16. ASYNCHRONOUS JAVASCRIPT EXECUTION
// ============================================================================

async function asynchronousExample() {
    console.log(`\n${"=".repeat(78)}`);
    console.log("9. Asynchronous CPU Simulation");
    console.log("=".repeat(78));

    const asyncCPU = new CPU();

    asyncCPU.loadProgram([
        instruction(OPCODE.MOV, "R0", 20),
        instruction(OPCODE.MOV, "R1", 22),
        instruction(OPCODE.ADD, "R2", "R0", "R1"),
        instruction(OPCODE.OUT, "R2"),
        instruction(OPCODE.HALT)
    ]);

    await asyncCPU.runAsync();

    console.log(
        "The simulator yielded to the JavaScript event loop while executing."
    );
    console.log("Output:", asyncCPU.outputBuffer);
}


// ============================================================================
// 17. ERROR CONDITIONS
// ============================================================================

function demonstrateErrors() {
    console.log(`\n${"=".repeat(78)}`);
    console.log("10. Controlled Failure Conditions");
    console.log("=".repeat(78));

    const cases = [
        {
            name: "Division by zero",
            program: [
                instruction(OPCODE.MOV, "R0", 10),
                instruction(OPCODE.MOV, "R1", 0),
                instruction(OPCODE.DIV, "R2", "R0", "R1"),
                instruction(OPCODE.HALT)
            ]
        },
        {
            name: "Stack underflow",
            program: [
                instruction(OPCODE.POP, "R0"),
                instruction(OPCODE.HALT)
            ]
        },
        {
            name: "Invalid memory",
            program: [
                instruction(OPCODE.LOAD, "R0", 999),
                instruction(OPCODE.HALT)
            ]
        }
    ];

    for (const testCase of cases) {
        try {
            const testCPU = new CPU();
            testCPU.loadProgram(testCase.program);
            testCPU.run();

            console.log(`${testCase.name}: unexpectedly succeeded`);
        } catch (error) {
            console.log(
                `${testCase.name}: correctly rejected -> ${error.message}`
            );
        }
    }
}


// ============================================================================
// 18. JAVASCRIPT-SPECIFIC OBSERVATION
// ============================================================================

function explainJavaScriptCharacteristics() {
    console.log(`\n${"=".repeat(78)}`);
    console.log("11. JavaScript-Specific CPU Simulator Considerations");
    console.log("=".repeat(78));

    console.log(`
JavaScript adds useful application-level behavior to the simulator:

1. Classes provide object-oriented CPU, ALU, and assembler abstractions.
2. Arrays represent registers and memory naturally.
3. Map provides convenient label storage during assembly.
4. Set represents groups of branch opcodes.
5. async/await allows long simulations to periodically yield to the event loop.
6. Exceptions provide controlled failure handling.
7. JSON-style objects provide compact instruction representations.

A real JavaScript implementation must also account for JavaScript's
Number semantics. This implementation therefore restricts the simulated
CPU to 32-bit-or-less words and uses bitwise normalization for CPU values.
`);


    const bitwiseCPU = new CPU({ wordSize: 8 });

    const wrapped = bitwiseCPU.alu.add(
        250,
        10,
        bitwiseCPU.flags
    );

    console.log("8-bit 250 + 10 =", wrapped);
    console.log("Carry =", bitwiseCPU.flags.carry);
}


// ============================================================================
// 19. MAIN EXECUTION
// ============================================================================

async function main() {
    demonstrateErrors();
    explainJavaScriptCharacteristics();
    await asynchronousExample();

    console.log(`\n${"=".repeat(78)}`);
    console.log("CPU simulation completed.");
    console.log("=".repeat(78));
}


main().catch(error => {
    console.error("Fatal simulator error:", error);
    process.exitCode = 1;
});
