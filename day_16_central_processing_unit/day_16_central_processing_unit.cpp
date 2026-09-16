/*
    CPU Simulator Case Study
    =========================

    Scenario:
        A small industrial controller CPU is modeled as a virtual processor.
        The controller reads sensor values, stores them in memory, computes
        an aggregate value, compares the result against a threshold, and
        produces a status output.

    This program progressively implements:

        - Registers
        - Program Counter
        - Instruction Register
        - Memory
        - Stack Pointer
        - Flags
        - ALU
        - Instruction decoding
        - Fetch-decode-execute cycle
        - Arithmetic and logical instructions
        - Memory operations
        - Conditional branching
        - CALL / RET
        - Input / output
        - Assembly-like program representation
        - Validation
        - Instruction tracing
        - Cycle estimation
        - Complexity discussion

    Build:
        g++ -std=c++17 -O2 cpu_simulator.cpp -o cpu_simulator

    The program uses only the C++17 standard library.
*/

#include <array>
#include <cstdint>
#include <exception>
#include <iomanip>
#include <iostream>
#include <limits>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>


// ============================================================================
// 1. BASIC TYPES
// ============================================================================

using Word = std::uint16_t;
using Address = std::size_t;

constexpr std::size_t REGISTER_COUNT = 8;
constexpr std::size_t MEMORY_SIZE = 256;


// ============================================================================
// 2. OPCODES
// ============================================================================

enum class Opcode {
    NOP,
    LOAD,
    STORE,
    MOV,

    ADD,
    SUB,
    MUL,
    DIV,
    INC,
    DEC,

    AND_OP,
    OR_OP,
    XOR_OP,
    NOT_OP,
    SHL,
    SHR,

    CMP,
    JMP,
    JZ,
    JNZ,
    JN,
    JP,

    PUSH,
    POP,
    CALL,
    RET,

    IN,
    OUT,
    HALT
};


std::string opcodeName(Opcode opcode) {
    switch (opcode) {
        case Opcode::NOP:    return "NOP";
        case Opcode::LOAD:   return "LOAD";
        case Opcode::STORE:  return "STORE";
        case Opcode::MOV:    return "MOV";

        case Opcode::ADD:    return "ADD";
        case Opcode::SUB:    return "SUB";
        case Opcode::MUL:    return "MUL";
        case Opcode::DIV:    return "DIV";
        case Opcode::INC:    return "INC";
        case Opcode::DEC:    return "DEC";

        case Opcode::AND_OP: return "AND";
        case Opcode::OR_OP:  return "OR";
        case Opcode::XOR_OP: return "XOR";
        case Opcode::NOT_OP: return "NOT";
        case Opcode::SHL:    return "SHL";
        case Opcode::SHR:    return "SHR";

        case Opcode::CMP:    return "CMP";
        case Opcode::JMP:    return "JMP";
        case Opcode::JZ:     return "JZ";
        case Opcode::JNZ:    return "JNZ";
        case Opcode::JN:     return "JN";
        case Opcode::JP:     return "JP";

        case Opcode::PUSH:   return "PUSH";
        case Opcode::POP:    return "POP";
        case Opcode::CALL:   return "CALL";
        case Opcode::RET:    return "RET";

        case Opcode::IN:     return "IN";
        case Opcode::OUT:    return "OUT";
        case Opcode::HALT:   return "HALT";
    }

    throw std::logic_error("Unknown opcode");
}


// ============================================================================
// 3. OPERANDS AND INSTRUCTIONS
// ============================================================================

enum class OperandType {
    REGISTER,
    IMMEDIATE,
    ADDRESS
};


struct Operand {
    OperandType type;
    std::int32_t value;

    static Operand reg(std::size_t index) {
        if (index >= REGISTER_COUNT) {
            throw std::out_of_range("Register index out of range");
        }

        return {OperandType::REGISTER, static_cast<std::int32_t>(index)};
    }

    static Operand immediate(std::int32_t value) {
        return {OperandType::IMMEDIATE, value};
    }

    static Operand address(std::int32_t value) {
        return {OperandType::ADDRESS, value};
    }
};


struct Instruction {
    Opcode opcode;
    std::vector<Operand> operands;
    std::string source;

    Instruction(
        Opcode opcode,
        std::vector<Operand> operands = {},
        std::string source = ""
    )
        : opcode(opcode),
          operands(std::move(operands)),
          source(std::move(source)) {}
};


// ============================================================================
// 4. FLAGS
// ============================================================================

struct Flags {
    bool zero = false;
    bool negative = false;
    bool carry = false;
    bool overflow = false;

    void reset() {
        zero = false;
        negative = false;
        carry = false;
        overflow = false;
    }

    std::string toString() const {
        std::ostringstream output;

        output
            << "Z=" << zero
            << " N=" << negative
            << " C=" << carry
            << " V=" << overflow;

        return output.str();
    }
};


// ============================================================================
// 5. ALU
// ============================================================================

class ALU {
private:
    static constexpr std::uint32_t MASK = 0xFFFF;
    static constexpr std::uint32_t SIGN_BIT = 0x8000;

public:
    static Word normalize(std::uint32_t value) {
        return static_cast<Word>(value & MASK);
    }

    static std::int32_t signedValue(Word value) {
        if (value & SIGN_BIT) {
            return static_cast<std::int32_t>(value) - 65536;
        }

        return static_cast<std::int32_t>(value);
    }

    static void setResultFlags(
        Word result,
        Flags& flags,
        bool carry = false,
        bool overflow = false
    ) {
        flags.zero = result == 0;
        flags.negative = (result & SIGN_BIT) != 0;
        flags.carry = carry;
        flags.overflow = overflow;
    }

    static Word add(Word left, Word right, Flags& flags) {
        const std::uint32_t raw =
            static_cast<std::uint32_t>(left) +
            static_cast<std::uint32_t>(right);

        const Word result = normalize(raw);

        const auto leftSigned = signedValue(left);
        const auto rightSigned = signedValue(right);
        const auto resultSigned = signedValue(result);

        const bool overflow =
            (leftSigned >= 0 &&
             rightSigned >= 0 &&
             resultSigned < 0)
            ||
            (leftSigned < 0 &&
             rightSigned < 0 &&
             resultSigned >= 0);

        setResultFlags(
            result,
            flags,
            raw > MASK,
            overflow
        );

        return result;
    }

    static Word subtract(
        Word left,
        Word right,
        Flags& flags
    ) {
        const Word result =
            normalize(
                static_cast<std::uint32_t>(left) -
                static_cast<std::uint32_t>(right)
            );

        const auto leftSigned = signedValue(left);
        const auto rightSigned = signedValue(right);
        const auto resultSigned = signedValue(result);

        const bool overflow =
            (leftSigned >= 0 &&
             rightSigned < 0 &&
             resultSigned < 0)
            ||
            (leftSigned < 0 &&
             rightSigned >= 0 &&
             resultSigned >= 0);

        setResultFlags(
            result,
            flags,
            left >= right,
            overflow
        );

        return result;
    }

    static Word multiply(
        Word left,
        Word right,
        Flags& flags
    ) {
        const std::uint32_t raw =
            static_cast<std::uint32_t>(left) *
            static_cast<std::uint32_t>(right);

        const Word result = normalize(raw);

        setResultFlags(
            result,
            flags,
            raw > MASK
        );

        return result;
    }

    static Word divide(
        Word left,
        Word right,
        Flags& flags
    ) {
        if (right == 0) {
            throw std::domain_error("Division by zero");
        }

        const Word result =
            static_cast<Word>(left / right);

        setResultFlags(result, flags);

        return result;
    }

    static Word bitAnd(
        Word left,
        Word right,
        Flags& flags
    ) {
        const Word result = left & right;
        setResultFlags(result, flags);
        return result;
    }

    static Word bitOr(
        Word left,
        Word right,
        Flags& flags
    ) {
        const Word result = left | right;
        setResultFlags(result, flags);
        return result;
    }

    static Word bitXor(
        Word left,
        Word right,
        Flags& flags
    ) {
        const Word result = left ^ right;
        setResultFlags(result, flags);
        return result;
    }

    static Word bitNot(Word value, Flags& flags) {
        const Word result = static_cast<Word>(~value);
        setResultFlags(result, flags);
        return result;
    }

    static Word shiftLeft(
        Word value,
        unsigned amount,
        Flags& flags
    ) {
        if (amount > 16) {
            setResultFlags(0, flags);
            return 0;
        }

        bool carry = false;

        if (amount > 0) {
            carry =
                (value & (1u << (16 - amount))) != 0;
        }

        const Word result =
            static_cast<Word>(
                static_cast<std::uint32_t>(value) << amount
            );

        setResultFlags(result, flags, carry);

        return result;
    }

    static Word shiftRight(
        Word value,
        unsigned amount,
        Flags& flags
    ) {
        if (amount > 16) {
            setResultFlags(0, flags);
            return 0;
        }

        bool carry = false;

        if (amount > 0) {
            carry =
                (value & (1u << (amount - 1))) != 0;
        }

        const Word result =
            static_cast<Word>(value >> amount);

        setResultFlags(result, flags, carry);

        return result;
    }
};


// ============================================================================
// 6. CPU
// ============================================================================

class CPU {
private:
    std::array<Word, REGISTER_COUNT> registers{};
    std::array<Word, MEMORY_SIZE> memory{};

    Address programCounter = 0;
    Address stackPointer = MEMORY_SIZE - 1;

    std::optional<Instruction> instructionRegister;

    Flags flags;

    std::vector<Instruction> program;

    std::vector<Word> inputBuffer;
    std::vector<Word> outputBuffer;

    bool halted = false;
    bool tracing = false;

    std::uint64_t cycles = 0;
    std::uint64_t instructionsExecuted = 0;

public:
    // ------------------------------------------------------------------------
    // Register access
    // ------------------------------------------------------------------------

    Word readRegister(std::size_t index) const {
        validateRegister(index);
        return registers[index];
    }

    void writeRegister(std::size_t index, Word value) {
        validateRegister(index);
        registers[index] = value;
    }

    // ------------------------------------------------------------------------
    // Memory access
    // ------------------------------------------------------------------------

    Word readMemory(Address address) const {
        validateMemoryAddress(address);
        return memory[address];
    }

    void writeMemory(Address address, Word value) {
        validateMemoryAddress(address);
        memory[address] = value;
    }

    // ------------------------------------------------------------------------
    // Program loading
    // ------------------------------------------------------------------------

    void loadProgram(std::vector<Instruction> newProgram) {
        if (newProgram.size() > MEMORY_SIZE) {
            throw std::length_error(
                "Program exceeds simulated memory capacity"
            );
        }

        program = std::move(newProgram);

        programCounter = 0;
        stackPointer = MEMORY_SIZE - 1;
        instructionRegister.reset();

        halted = false;
        cycles = 0;
        instructionsExecuted = 0;

        outputBuffer.clear();
    }

    // ------------------------------------------------------------------------
    // Input/output
    // ------------------------------------------------------------------------

    void setInput(std::vector<Word> input) {
        inputBuffer = std::move(input);
    }

    const std::vector<Word>& output() const {
        return outputBuffer;
    }

    // ------------------------------------------------------------------------
    // Configuration
    // ------------------------------------------------------------------------

    void setTracing(bool enabled) {
        tracing = enabled;
    }

    // ------------------------------------------------------------------------
    // Fetch
    // ------------------------------------------------------------------------

    Instruction fetch() {
        if (programCounter >= program.size()) {
            throw std::runtime_error(
                "Program counter points outside the loaded program"
            );
        }

        // The instruction register stores the fetched instruction.
        instructionRegister = program[programCounter];

        // Sequential execution advances PC before execution.
        ++programCounter;

        return *instructionRegister;
    }

    // ------------------------------------------------------------------------
    // Operand resolution
    // ------------------------------------------------------------------------

    Word resolveValue(const Operand& operand) const {
        switch (operand.type) {
            case OperandType::REGISTER:
                return readRegister(
                    static_cast<std::size_t>(operand.value)
                );

            case OperandType::IMMEDIATE:
                return static_cast<Word>(operand.value);

            case OperandType::ADDRESS:
                throw std::invalid_argument(
                    "Address operand cannot be used as a value"
                );
        }

        throw std::logic_error("Unknown operand type");
    }

    Address resolveAddress(const Operand& operand) const {
        if (operand.type != OperandType::ADDRESS &&
            operand.type != OperandType::IMMEDIATE) {
            throw std::invalid_argument(
                "Expected memory address"
            );
        }

        if (operand.value < 0) {
            throw std::out_of_range(
                "Negative memory address"
            );
        }

        return static_cast<Address>(operand.value);
    }

    // ------------------------------------------------------------------------
    // Stack
    // ------------------------------------------------------------------------

    void push(Word value) {
        if (stackPointer >= MEMORY_SIZE) {
            throw std::runtime_error("Invalid stack pointer");
        }

        writeMemory(stackPointer, value);

        if (stackPointer == 0) {
            stackPointer = MEMORY_SIZE;
        } else {
            --stackPointer;
        }
    }

    Word pop() {
        if (stackPointer >= MEMORY_SIZE - 1) {
            throw std::runtime_error("Stack underflow");
        }

        ++stackPointer;
        return readMemory(stackPointer);
    }

    // ------------------------------------------------------------------------
    // Instruction execution
    // ------------------------------------------------------------------------

    void execute(const Instruction& instruction) {
        const auto& operands = instruction.operands;

        switch (instruction.opcode) {
            case Opcode::NOP:
                break;

            case Opcode::HALT:
                halted = true;
                break;

            case Opcode::MOV: {
                requireOperands(operands, 2);

                const auto destination =
                    registerIndex(operands[0]);

                const Word value =
                    resolveValue(operands[1]);

                writeRegister(destination, value);
                break;
            }

            case Opcode::LOAD: {
                requireOperands(operands, 2);

                const auto destination =
                    registerIndex(operands[0]);

                const Address address =
                    resolveAddress(operands[1]);

                writeRegister(
                    destination,
                    readMemory(address)
                );

                break;
            }

            case Opcode::STORE: {
                requireOperands(operands, 2);

                const auto source =
                    registerIndex(operands[0]);

                const Address address =
                    resolveAddress(operands[1]);

                writeMemory(
                    address,
                    readRegister(source)
                );

                break;
            }

            case Opcode::ADD:
            case Opcode::SUB:
            case Opcode::MUL:
            case Opcode::DIV:
            case Opcode::AND_OP:
            case Opcode::OR_OP:
            case Opcode::XOR_OP: {
                requireOperands(operands, 3);

                const auto destination =
                    registerIndex(operands[0]);

                const Word left =
                    resolveValue(operands[1]);

                const Word right =
                    resolveValue(operands[2]);

                Word result = 0;

                switch (instruction.opcode) {
                    case Opcode::ADD:
                        result = ALU::add(left, right, flags);
                        break;

                    case Opcode::SUB:
                        result = ALU::subtract(left, right, flags);
                        break;

                    case Opcode::MUL:
                        result = ALU::multiply(left, right, flags);
                        break;

                    case Opcode::DIV:
                        result = ALU::divide(left, right, flags);
                        break;

                    case Opcode::AND_OP:
                        result = ALU::bitAnd(left, right, flags);
                        break;

                    case Opcode::OR_OP:
                        result = ALU::bitOr(left, right, flags);
                        break;

                    case Opcode::XOR_OP:
                        result = ALU::bitXor(left, right, flags);
                        break;

                    default:
                        throw std::logic_error(
                            "Invalid arithmetic/logical opcode"
                        );
                }

                writeRegister(destination, result);
                break;
            }

            case Opcode::INC: {
                requireOperands(operands, 1);

                const auto index =
                    registerIndex(operands[0]);

                writeRegister(
                    index,
                    ALU::add(
                        readRegister(index),
                        1,
                        flags
                    )
                );

                break;
            }

            case Opcode::DEC: {
                requireOperands(operands, 1);

                const auto index =
                    registerIndex(operands[0]);

                writeRegister(
                    index,
                    ALU::subtract(
                        readRegister(index),
                        1,
                        flags
                    )
                );

                break;
            }

            case Opcode::NOT_OP: {
                requireOperands(operands, 2);

                const auto destination =
                    registerIndex(operands[0]);

                writeRegister(
                    destination,
                    ALU::bitNot(
                        resolveValue(operands[1]),
                        flags
                    )
                );

                break;
            }

            case Opcode::SHL: {
                requireOperands(operands, 3);

                const auto destination =
                    registerIndex(operands[0]);

                const Word value =
                    resolveValue(operands[1]);

                const Word amount =
                    resolveValue(operands[2]);

                writeRegister(
                    destination,
                    ALU::shiftLeft(
                        value,
                        amount,
                        flags
                    )
                );

                break;
            }

            case Opcode::SHR: {
                requireOperands(operands, 3);

                const auto destination =
                    registerIndex(operands[0]);

                const Word value =
                    resolveValue(operands[1]);

                const Word amount =
                    resolveValue(operands[2]);

                writeRegister(
                    destination,
                    ALU::shiftRight(
                        value,
                        amount,
                        flags
                    )
                );

                break;
            }

            case Opcode::CMP: {
                requireOperands(operands, 2);

                ALU::subtract(
                    resolveValue(operands[0]),
                    resolveValue(operands[1]),
                    flags
                );

                break;
            }

            case Opcode::JMP:
                branchIf(true, operands);
                break;

            case Opcode::JZ:
                branchIf(flags.zero, operands);
                break;

            case Opcode::JNZ:
                branchIf(!flags.zero, operands);
                break;

            case Opcode::JN:
                branchIf(flags.negative, operands);
                break;

            case Opcode::JP:
                branchIf(!flags.negative, operands);
                break;

            case Opcode::PUSH:
                requireOperands(operands, 1);
                push(resolveValue(operands[0]));
                break;

            case Opcode::POP: {
                requireOperands(operands, 1);

                const auto destination =
                    registerIndex(operands[0]);

                writeRegister(destination, pop());
                break;
            }

            case Opcode::CALL: {
                requireOperands(operands, 1);

                const Address target =
                    resolveAddress(operands[0]);

                validateProgramAddress(target);

                // PC has already advanced beyond CALL, so it is the
                // correct return address to save.
                push(static_cast<Word>(programCounter));

                programCounter = target;
                break;
            }

            case Opcode::RET:
                programCounter = pop();
                validateProgramAddress(programCounter);
                break;

            case Opcode::IN: {
                requireOperands(operands, 1);

                if (inputBuffer.empty()) {
                    throw std::runtime_error(
                        "Input buffer is empty"
                    );
                }

                const auto destination =
                    registerIndex(operands[0]);

                writeRegister(
                    destination,
                    inputBuffer.front()
                );

                inputBuffer.erase(inputBuffer.begin());

                break;
            }

            case Opcode::OUT:
                requireOperands(operands, 1);

                outputBuffer.push_back(
                    resolveValue(operands[0])
                );

                break;
        }
    }

    // ------------------------------------------------------------------------
    // Clock
    // ------------------------------------------------------------------------

    std::uint64_t cycleCost(Opcode opcode) const {
        switch (opcode) {
            case Opcode::LOAD:
            case Opcode::STORE:
                return 3;

            case Opcode::MUL:
                return 3;

            case Opcode::DIV:
                return 8;

            case Opcode::PUSH:
            case Opcode::POP:
                return 2;

            case Opcode::CALL:
            case Opcode::RET:
                return 3;

            case Opcode::IN:
            case Opcode::OUT:
                return 2;

            default:
                return 1;
        }
    }

    void step() {
        if (halted) {
            return;
        }

        const Address oldPC = programCounter;
        const Instruction current = fetch();

        if (tracing) {
            std::cout
                << "PC=" << std::setw(3) << oldPC
                << " | "
                << std::left << std::setw(24)
                << instructionToString(current)
                << std::right
                << " | R0=" << registers[0]
                << " R1=" << registers[1]
                << " R2=" << registers[2]
                << '\n';
        }

        execute(current);

        ++instructionsExecuted;
        cycles += cycleCost(current.opcode);
    }

    void run(std::uint64_t maxSteps = 100000) {
        std::uint64_t steps = 0;

        while (!halted) {
            if (steps >= maxSteps) {
                throw std::runtime_error(
                    "Maximum execution count exceeded; "
                    "possible infinite loop"
                );
            }

            step();
            ++steps;
        }
    }

    // ------------------------------------------------------------------------
    // State inspection
    // ------------------------------------------------------------------------

    void dumpState() const {
        std::cout << "\nCPU STATE\n";
        std::cout << "---------\n";

        for (std::size_t i = 0; i < REGISTER_COUNT; ++i) {
            std::cout
                << "R" << i
                << " = "
                << std::setw(5)
                << registers[i]
                << " signed="
                << std::setw(6)
                << ALU::signedValue(registers[i])
                << " hex=0x"
                << std::hex
                << std::setw(4)
                << std::setfill('0')
                << registers[i]
                << std::dec
                << std::setfill(' ')
                << '\n';
        }

        std::cout
            << "PC = " << programCounter << '\n'
            << "SP = " << stackPointer << '\n'
            << "FLAGS = " << flags.toString() << '\n'
            << "INSTRUCTIONS = " << instructionsExecuted << '\n'
            << "CYCLES = " << cycles << '\n';

        std::cout << "OUTPUT = [";

        for (std::size_t i = 0; i < outputBuffer.size(); ++i) {
            if (i != 0) {
                std::cout << ", ";
            }

            std::cout << outputBuffer[i];
        }

        std::cout << "]\n";
    }

private:
    static void validateRegister(std::size_t index) {
        if (index >= REGISTER_COUNT) {
            throw std::out_of_range(
                "Register index out of range"
            );
        }
    }

    static std::size_t registerIndex(const Operand& operand) {
        if (operand.type != OperandType::REGISTER) {
            throw std::invalid_argument(
                "Expected register operand"
            );
        }

        return static_cast<std::size_t>(operand.value);
    }

    void validateMemoryAddress(Address address) const {
        if (address >= MEMORY_SIZE) {
            throw std::out_of_range(
                "Memory address out of range"
            );
        }
    }

    void validateProgramAddress(Address address) const {
        if (address >= program.size()) {
            throw std::out_of_range(
                "Program address out of range"
            );
        }
    }

    static void requireOperands(
        const std::vector<Operand>& operands,
        std::size_t expected
    ) {
        if (operands.size() != expected) {
            throw std::invalid_argument(
                "Incorrect operand count"
            );
        }
    }

    void branchIf(
        bool condition,
        const std::vector<Operand>& operands
    ) {
        requireOperands(operands, 1);

        const Address target =
            resolveAddress(operands[0]);

        if (condition) {
            validateProgramAddress(target);
            programCounter = target;
        }
    }

    static std::string operandToString(const Operand& operand) {
        std::ostringstream output;

        switch (operand.type) {
            case OperandType::REGISTER:
                output << "R" << operand.value;
                break;

            case OperandType::IMMEDIATE:
                output << operand.value;
                break;

            case OperandType::ADDRESS:
                output << "[" << operand.value << "]";
                break;
        }

        return output.str();
    }

    static std::string instructionToString(
        const Instruction& instruction
    ) {
        std::ostringstream output;

        output << opcodeName(instruction.opcode);

        if (!instruction.operands.empty()) {
            output << " ";

            for (std::size_t i = 0;
                 i < instruction.operands.size();
                 ++i) {
                if (i != 0) {
                    output << ", ";
                }

                output << operandToString(
                    instruction.operands[i]
                );
            }
        }

        return output.str();
    }
};


// ============================================================================
// 7. INSTRUCTION FACTORIES
// ============================================================================

Instruction MOV(
    std::size_t destination,
    std::int32_t value
) {
    return {
        Opcode::MOV,
        {
            Operand::reg(destination),
            Operand::immediate(value)
        },
        "MOV"
    };
}


Instruction MOVR(
    std::size_t destination,
    std::size_t source
) {
    return {
        Opcode::MOV,
        {
            Operand::reg(destination),
            Operand::reg(source)
        },
        "MOV"
    };
}


Instruction ADD(
    std::size_t destination,
    std::size_t left,
    std::size_t right
) {
    return {
        Opcode::ADD,
        {
            Operand::reg(destination),
            Operand::reg(left),
            Operand::reg(right)
        },
        "ADD"
    };
}


Instruction ADDI(
    std::size_t destination,
    std::size_t left,
    std::int32_t immediate
) {
    return {
        Opcode::ADD,
        {
            Operand::reg(destination),
            Operand::reg(left),
            Operand::immediate(immediate)
        },
        "ADD"
    };
}


Instruction SUBI(
    std::size_t destination,
    std::size_t left,
    std::int32_t immediate
) {
    return {
        Opcode::SUB,
        {
            Operand::reg(destination),
            Operand::reg(left),
            Operand::immediate(immediate)
        },
        "SUB"
    };
}


Instruction LOAD(
    std::size_t destination,
    Address address
) {
    return {
        Opcode::LOAD,
        {
            Operand::reg(destination),
            Operand::address(static_cast<std::int32_t>(address))
        },
        "LOAD"
    };
}


Instruction STORE(
    std::size_t source,
    Address address
) {
    return {
        Opcode::STORE,
        {
            Operand::reg(source),
            Operand::address(static_cast<std::int32_t>(address))
        },
        "STORE"
    };
}


// ============================================================================
// 8. CASE STUDY: INDUSTRIAL SENSOR AGGREGATOR
// ============================================================================

class SensorController {
private:
    CPU cpu;

    // These addresses represent memory-mapped sensor locations.
    static constexpr Address SENSOR_1 = 100;
    static constexpr Address SENSOR_2 = 101;
    static constexpr Address SENSOR_3 = 102;

    static constexpr Address RESULT = 110;
    static constexpr Address STATUS = 111;

public:
    void writeSensors(
        Word sensor1,
        Word sensor2,
        Word sensor3
    ) {
        cpu.writeMemory(SENSOR_1, sensor1);
        cpu.writeMemory(SENSOR_2, sensor2);
        cpu.writeMemory(SENSOR_3, sensor3);
    }

    std::vector<Instruction> buildProgram() const {
        /*
            Program design:

            R0 = sensor 1
            R1 = sensor 2
            R2 = sensor 3
            R3 = aggregate
            R4 = threshold
            R5 = status

            The program computes:

                aggregate = sensor1 + sensor2 + sensor3

            Then:

                if aggregate >= 300:
                    status = 1
                else:
                    status = 0

            The program uses CMP followed by conditional control flow.
        */

        return {
            LOAD(0, SENSOR_1),             // 0
            LOAD(1, SENSOR_2),             // 1
            LOAD(2, SENSOR_3),             // 2

            ADD(3, 0, 1),                  // 3
            ADD(3, 3, 2),                  // 4

            STORE(3, RESULT),              // 5

            MOV(4, 300),                   // 6
            {
                Opcode::CMP,
                {
                    Operand::reg(3),
                    Operand::reg(4)
                },
                "CMP"
            },

            /*
                A full ISA would normally have a JGE instruction.
                Our educational ISA instead uses JP after subtraction.
                This example treats non-negative subtraction as the
                condition for aggregate >= threshold.
            */
            {
                Opcode::JN,
                {
                    Operand::address(11)
                },
                "JN below_threshold"
            },

            MOV(5, 1),                     // 9
            STORE(5, STATUS),              // 10
            {Opcode::HALT, {}, "HALT"},

            MOV(5, 0),                     // 12
            STORE(5, STATUS),              // 13
            {Opcode::HALT, {}, "HALT"}
        };
    }

    void run() {
        cpu.loadProgram(buildProgram());
        cpu.run();
    }

    void printResults() const {
        std::cout
            << "\nIndustrial controller result\n"
            << "----------------------------\n"
            << "Sensor 1: " << cpu.readMemory(SENSOR_1) << '\n'
            << "Sensor 2: " << cpu.readMemory(SENSOR_2) << '\n'
            << "Sensor 3: " << cpu.readMemory(SENSOR_3) << '\n'
            << "Aggregate: " << cpu.readMemory(RESULT) << '\n'
            << "Status: " << cpu.readMemory(STATUS) << '\n';

        std::cout
            << "Status meaning: "
            << (cpu.readMemory(STATUS) == 1
                ? "threshold reached"
                : "below threshold")
            << '\n';
    }

    CPU& machine() {
        return cpu;
    }
};


// ============================================================================
// 9. SIMPLE PROGRAMS
// ============================================================================

void printSection(const std::string& title) {
    std::cout
        << "\n"
        << std::string(78, '=')
        << "\n"
        << title
        << "\n"
        << std::string(78, '=')
        << "\n";
}


void additionExample() {
    printSection("1. Basic ALU Execution");

    CPU cpu;

    cpu.loadProgram({
        MOV(0, 12),
        MOV(1, 30),
        ADD(2, 0, 1),
        {
            Opcode::OUT,
            {Operand::reg(2)},
            "OUT R2"
        },
        {Opcode::HALT, {}, "HALT"}
    });

    cpu.run();
    cpu.dumpState();
}


void memoryExample() {
    printSection("2. Memory Load and Store");

    CPU cpu;

    cpu.loadProgram({
        MOV(0, 1234),
        STORE(0, 100),
        LOAD(1, 100),
        {
            Opcode::OUT,
            {Operand::reg(1)},
            "OUT R1"
        },
        {Opcode::HALT, {}, "HALT"}
    });

    cpu.run();

    std::cout
        << "Memory[100] = "
        << cpu.readMemory(100)
        << '\n';

    cpu.dumpState();
}


void factorialExample() {
    printSection("3. Iterative Factorial");

    /*
        Calculate 5! using:

            result = 1
            counter = 5

            result *= counter
            counter--
            repeat while counter > 1
    */

    CPU cpu;

    cpu.loadProgram({
        MOV(0, 5),                         // counter
        MOV(1, 1),                         // result

        // 2: loop
        {
            Opcode::MUL,
            {
                Operand::reg(1),
                Operand::reg(1),
                Operand::reg(0)
            },
            "MUL R1, R1, R0"
        },

        {
            Opcode::DEC,
            {Operand::reg(0)},
            "DEC R0"
        },

        {
            Opcode::CMP,
            {
                Operand::reg(0),
                Operand::immediate(1)
            },
            "CMP R0, 1"
        },

        {
            Opcode::JP,
            {Operand::address(2)},
            "JP loop"
        },

        {
            Opcode::OUT,
            {Operand::reg(1)},
            "OUT R1"
        },

        {Opcode::HALT, {}, "HALT"}
    });

    cpu.run();
    cpu.dumpState();
}


// ============================================================================
// 10. CALL/RET CASE
// ============================================================================

void functionCallExample() {
    printSection("4. CALL / RET");

    CPU cpu;

    cpu.loadProgram({
        {
            Opcode::CALL,
            {Operand::address(4)},
            "CALL multiply"
        },

        {
            Opcode::OUT,
            {Operand::reg(0)},
            "OUT R0"
        },

        {Opcode::HALT, {}, "HALT"},
        {Opcode::NOP, {}, "NOP"},

        MOV(0, 7),                         // function
        MOV(1, 6),

        {
            Opcode::MUL,
            {
                Operand::reg(0),
                Operand::reg(0),
                Operand::reg(1)
            },
            "MUL R0, R0, R1"
        },

        {Opcode::RET, {}, "RET"}
    });

    cpu.run();
    cpu.dumpState();
}


// ============================================================================
// 11. ERROR HANDLING
// ============================================================================

void errorHandlingExample() {
    printSection("5. CPU Validation and Error Handling");

    struct TestCase {
        std::string name;
        std::vector<Instruction> program;
    };

    const std::vector<TestCase> tests = {
        {
            "Division by zero",
            {
                MOV(0, 10),
                MOV(1, 0),
                {
                    Opcode::DIV,
                    {
                        Operand::reg(2),
                        Operand::reg(0),
                        Operand::reg(1)
                    },
                    "DIV R2, R0, R1"
                },
                {Opcode::HALT, {}, "HALT"}
            }
        },

        {
            "Invalid memory address",
            {
                LOAD(0, 999),
                {Opcode::HALT, {}, "HALT"}
            }
        },

        {
            "Stack underflow",
            {
                {
                    Opcode::POP,
                    {Operand::reg(0)},
                    "POP R0"
                },
                {Opcode::HALT, {}, "HALT"}
            }
        }
    };

    for (const auto& test : tests) {
        try {
            CPU cpu;
            cpu.loadProgram(test.program);
            cpu.run();

            std::cout
                << test.name
                << ": unexpectedly succeeded\n";
        }
        catch (const std::exception& error) {
            std::cout
                << test.name
                << ": correctly rejected -> "
                << error.what()
                << '\n';
        }
    }
}


// ============================================================================
// 12. ALU EDGE CASES
// ============================================================================

void aluEdgeCaseExample() {
    printSection("6. ALU Width and Overflow Behavior");

    CPU cpu;

    cpu.loadProgram({
        MOV(0, 65535),
        ADDI(1, 0, 1),
        {Opcode::HALT, {}, "HALT"}
    });

    cpu.run();

    cpu.dumpState();

    std::cout
        << "\n16-bit unsigned wraparound:\n"
        << "65535 + 1 becomes "
        << cpu.readRegister(1)
        << " because only 16 bits are retained.\n";

    Flags flags;

    const Word overflowResult =
        ALU::add(32767, 1, flags);

    std::cout
        << "32767 + 1 bit pattern = "
        << overflowResult
        << '\n'
        << "Signed interpretation = "
        << ALU::signedValue(overflowResult)
        << '\n'
        << "Overflow flag = "
        << flags.overflow
        << '\n';
}


// ============================================================================
// 13. PERFORMANCE MEASUREMENT
// ============================================================================

void performanceExample() {
    printSection("7. Instruction Count and Estimated Cycles");

    CPU cpu;

    cpu.loadProgram({
        MOV(0, 100),
        MOV(1, 200),
        ADD(2, 0, 1),

        {
            Opcode::MUL,
            {
                Operand::reg(3),
                Operand::reg(2),
                Operand::reg(1)
            },
            "MUL R3, R2, R1"
        },

        STORE(3, 120),
        LOAD(4, 120),

        {Opcode::HALT, {}, "HALT"}
    });

    cpu.run();

    cpu.dumpState();

    std::cout
        << "\nThe simplified timing model gives different costs to "
           "memory, multiplication, division, stack, and I/O operations.\n"
           "Real processors use substantially more complex timing behavior.\n";
}


// ============================================================================
// 14. INDUSTRIAL CASE STUDY
// ============================================================================

void industrialCaseStudy() {
    printSection("8. Industry-Style Case Study: Sensor Controller");

    SensorController controller;

    controller.writeSensors(
        100,
        125,
        110
    );

    controller.run();
    controller.printResults();

    /*
        100 + 125 + 110 = 335.

        The threshold is 300, so the simulated controller records status 1.
    */
}


// ============================================================================
// 15. TRACE MODE
// ============================================================================

void traceExample() {
    printSection("9. Instruction Trace");

    CPU cpu;

    cpu.loadProgram({
        MOV(0, 5),
        MOV(1, 7),
        ADD(2, 0, 1),
        {
            Opcode::OUT,
            {Operand::reg(2)},
            "OUT R2"
        },
        {Opcode::HALT, {}, "HALT"}
    });

    cpu.setTracing(true);
    cpu.run();
    cpu.setTracing(false);

    cpu.dumpState();
}


// ============================================================================
// 16. MAIN
// ============================================================================

int main() {
    try {
        additionExample();
        memoryExample();
        factorialExample();
        functionCallExample();
        errorHandlingExample();
        aluEdgeCaseExample();
        performanceExample();
        industrialCaseStudy();
        traceExample();

        printSection("10. Architectural Model");

        std::cout
            << "The simulator models the following execution sequence:\n\n"
            << "FETCH:\n"
            << "  PC selects the next instruction.\n"
            << "  The instruction is copied into IR.\n"
            << "  PC advances to the next sequential address.\n\n"

            << "DECODE:\n"
            << "  The control unit identifies the opcode and operands.\n\n"

            << "EXECUTE:\n"
            << "  The ALU, registers, memory, stack, or control-flow logic\n"
            << "  performs the requested operation.\n\n"

            << "STATE UPDATE:\n"
            << "  Registers, flags, memory, PC, and other state are changed.\n\n"

            << "The cycle repeats until HALT.\n";

        return 0;
    }
    catch (const std::exception& error) {
        std::cerr
            << "Fatal simulator error: "
            << error.what()
            << '\n';

        return 1;
    }
}
