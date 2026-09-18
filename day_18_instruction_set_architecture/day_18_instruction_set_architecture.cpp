/*
 * Instruction Set Architecture Case Study
 *
 * Scenario:
 *   A small embedded telemetry controller receives sensor samples, stores
 *   them in memory, computes a derived value, compares it with a threshold,
 *   and branches to an alert or normal-processing path.
 *
 * The program implements an educational CPU with:
 *   - 8 general-purpose 16-bit registers
 *   - 16-bit arithmetic
 *   - byte-addressable memory
 *   - opcodes
 *   - register and immediate operands
 *   - direct and base-plus-offset addressing
 *   - comparison and conditional branch
 *   - instruction encoding/decoding
 *   - a fetch-decode-execute cycle
 *
 * Compile:
 *   g++ -std=c++17 -Wall -Wextra -pedantic isa_case_study.cpp -o isa_case_study
 */

#include <array>
#include <cstdint>
#include <exception>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

enum class Opcode : std::uint8_t {
    NOP   = 0x00,
    MOV   = 0x01,
    ADD   = 0x02,
    SUB   = 0x03,
    AND   = 0x04,
    OR    = 0x05,
    XOR   = 0x06,
    SHL   = 0x07,
    SHR   = 0x08,
    LOAD  = 0x09,
    STORE = 0x0A,
    JMP   = 0x0B,
    JZ    = 0x0C,
    CMP   = 0x0D,
    HALT  = 0x0E
};

std::string opcodeName(Opcode opcode) {
    switch (opcode) {
        case Opcode::NOP:   return "NOP";
        case Opcode::MOV:   return "MOV";
        case Opcode::ADD:   return "ADD";
        case Opcode::SUB:   return "SUB";
        case Opcode::AND:   return "AND";
        case Opcode::OR:    return "OR";
        case Opcode::XOR:   return "XOR";
        case Opcode::SHL:   return "SHL";
        case Opcode::SHR:   return "SHR";
        case Opcode::LOAD:  return "LOAD";
        case Opcode::STORE: return "STORE";
        case Opcode::JMP:   return "JMP";
        case Opcode::JZ:    return "JZ";
        case Opcode::CMP:   return "CMP";
        case Opcode::HALT:  return "HALT";
    }

    throw std::runtime_error("Unknown opcode.");
}

struct Instruction {
    Opcode opcode{};
    std::uint8_t operandA{0};
    std::uint8_t operandB{0};
    std::uint16_t immediate{0};
    bool hasImmediate{false};

    std::string toString() const {
        std::string result = opcodeName(opcode);

        switch (opcode) {
            case Opcode::NOP:
            case Opcode::HALT:
                return result;

            case Opcode::JMP:
            case Opcode::JZ:
                return result + " " + std::to_string(immediate);

            case Opcode::SHL:
            case Opcode::SHR:
                return result + " R" + std::to_string(operandA)
                    + ", #" + std::to_string(immediate);

            case Opcode::LOAD:
            case Opcode::STORE:
                if (operandB == 0) {
                    return result + " R" + std::to_string(operandA)
                        + ", [" + std::to_string(immediate) + "]";
                }

                return result + " R" + std::to_string(operandA)
                    + ", [R" + std::to_string(operandB)
                    + "+" + std::to_string(immediate) + "]";

            default:
                if (hasImmediate) {
                    return result + " R" + std::to_string(operandA)
                        + ", #" + std::to_string(immediate);
                }

                return result + " R" + std::to_string(operandA)
                    + ", R" + std::to_string(operandB);
        }
    }
};

class RegisterFile {
private:
    static constexpr std::size_t REGISTER_COUNT = 8;
    std::array<std::uint16_t, REGISTER_COUNT> registers_{};

    static void validate(std::size_t index) {
        if (index >= REGISTER_COUNT) {
            throw std::out_of_range("Register index is outside R0-R7.");
        }
    }

public:
    std::uint16_t read(std::size_t index) const {
        validate(index);
        return registers_[index];
    }

    void write(std::size_t index, std::uint32_t value) {
        validate(index);

        // Explicit truncation models a 16-bit physical register.
        registers_[index] = static_cast<std::uint16_t>(value);
    }

    void dump() const {
        for (std::size_t i = 0; i < REGISTER_COUNT; ++i) {
            std::cout << "R" << i
                      << "=0x"
                      << std::hex
                      << std::setw(4)
                      << std::setfill('0')
                      << registers_[i]
                      << std::dec
                      << std::setfill(' ')
                      << " ";
        }
        std::cout << '\n';
    }
};

class Memory {
private:
    std::vector<std::uint8_t> bytes_;

    void validateByteAddress(std::size_t address) const {
        if (address >= bytes_.size()) {
            throw std::out_of_range("Memory address is outside memory.");
        }
    }

public:
    explicit Memory(std::size_t size = 256)
        : bytes_(size, 0) {
        if (size < 2) {
            throw std::invalid_argument(
                "Memory must contain at least two bytes."
            );
        }
    }

    std::uint8_t readByte(std::size_t address) const {
        validateByteAddress(address);
        return bytes_[address];
    }

    void writeByte(std::size_t address, std::uint8_t value) {
        validateByteAddress(address);
        bytes_[address] = value;
    }

    std::uint16_t readWord(std::size_t address) const {
        validateByteAddress(address);
        validateByteAddress(address + 1);

        // Little-endian representation.
        return static_cast<std::uint16_t>(
            bytes_[address] |
            (static_cast<std::uint16_t>(bytes_[address + 1]) << 8)
        );
    }

    void writeWord(std::size_t address, std::uint16_t value) {
        validateByteAddress(address);
        validateByteAddress(address + 1);

        bytes_[address] =
            static_cast<std::uint8_t>(value & 0xFF);

        bytes_[address + 1] =
            static_cast<std::uint8_t>((value >> 8) & 0xFF);
    }
};

struct Flags {
    bool zero{false};
    bool negative{false};
    bool carry{false};
    bool overflow{false};

    void print() const {
        std::cout
            << "Z=" << zero
            << " N=" << negative
            << " C=" << carry
            << " V=" << overflow
            << '\n';
    }
};

class CPU {
private:
    RegisterFile registers_;
    Memory memory_;
    Flags flags_;

    std::vector<Instruction> program_;
    std::size_t programCounter_{0};
    bool halted_{false};
    std::size_t steps_{0};

    static constexpr std::size_t MAX_REGISTERS = 8;
    static constexpr std::size_t MAX_STEPS = 10000;

    void validateRegister(std::uint8_t index) const {
        if (index >= MAX_REGISTERS) {
            throw std::runtime_error("Invalid register operand.");
        }
    }

    void validateTarget(std::uint16_t target) const {
        if (target >= program_.size()) {
            throw std::runtime_error(
                "Branch target leaves the program."
            );
        }
    }

    void updateFlags(
        std::uint16_t result,
        bool carry = false,
        bool overflow = false
    ) {
        flags_.zero = result == 0;
        flags_.negative = (result & 0x8000U) != 0;
        flags_.carry = carry;
        flags_.overflow = overflow;
    }

    std::uint16_t add16(
        std::uint16_t left,
        std::uint16_t right
    ) {
        const std::uint32_t raw =
            static_cast<std::uint32_t>(left) +
            static_cast<std::uint32_t>(right);

        const auto result =
            static_cast<std::uint16_t>(raw & 0xFFFFU);

        const std::int32_t signedLeft =
            (left & 0x8000U)
                ? static_cast<std::int32_t>(left) - 65536
                : static_cast<std::int32_t>(left);

        const std::int32_t signedRight =
            (right & 0x8000U)
                ? static_cast<std::int32_t>(right) - 65536
                : static_cast<std::int32_t>(right);

        const std::int32_t signedResult =
            (result & 0x8000U)
                ? static_cast<std::int32_t>(result) - 65536
                : static_cast<std::int32_t>(result);

        const bool overflow =
            (signedLeft >= 0 &&
             signedRight >= 0 &&
             signedResult < 0) ||
            (signedLeft < 0 &&
             signedRight < 0 &&
             signedResult >= 0);

        updateFlags(
            result,
            raw > 0xFFFFU,
            overflow
        );

        return result;
    }

    std::uint16_t subtract16(
        std::uint16_t left,
        std::uint16_t right
    ) {
        const std::int32_t raw =
            static_cast<std::int32_t>(left) -
            static_cast<std::int32_t>(right);

        const auto result =
            static_cast<std::uint16_t>(raw & 0xFFFF);

        const std::int32_t signedLeft =
            (left & 0x8000U)
                ? static_cast<std::int32_t>(left) - 65536
                : static_cast<std::int32_t>(left);

        const std::int32_t signedRight =
            (right & 0x8000U)
                ? static_cast<std::int32_t>(right) - 65536
                : static_cast<std::int32_t>(right);

        const std::int32_t signedResult =
            (result & 0x8000U)
                ? static_cast<std::int32_t>(result) - 65536
                : static_cast<std::int32_t>(result);

        const bool overflow =
            (signedLeft >= 0 &&
             signedRight < 0 &&
             signedResult < 0) ||
            (signedLeft < 0 &&
             signedRight >= 0 &&
             signedResult >= 0);

        updateFlags(
            result,
            left >= right,
            overflow
        );

        return result;
    }

    std::uint16_t secondOperand(const Instruction& instruction) const {
        if (instruction.hasImmediate) {
            return instruction.immediate;
        }

        validateRegister(instruction.operandB);
        return registers_.read(instruction.operandB);
    }

    std::size_t effectiveAddress(const Instruction& instruction) const {
        /*
         * operandB == 0 is treated as direct addressing in this educational
         * encoding. Otherwise operandB identifies the base register.
         */
        if (instruction.operandB == 0) {
            return instruction.immediate;
        }

        validateRegister(instruction.operandB);

        return static_cast<std::size_t>(
            registers_.read(instruction.operandB)
        ) + instruction.immediate;
    }

public:
    explicit CPU(std::size_t memorySize = 256)
        : memory_(memorySize) {}

    void loadProgram(std::vector<Instruction> program) {
        program_ = std::move(program);
        programCounter_ = 0;
        halted_ = false;
        steps_ = 0;
    }

    void step() {
        if (halted_) {
            return;
        }

        if (programCounter_ >= program_.size()) {
            throw std::runtime_error(
                "Program counter is outside program."
            );
        }

        const Instruction instruction = program_[programCounter_++];

        switch (instruction.opcode) {
            case Opcode::NOP:
                break;

            case Opcode::MOV: {
                validateRegister(instruction.operandA);

                if (instruction.hasImmediate) {
                    registers_.write(
                        instruction.operandA,
                        instruction.immediate
                    );
                } else {
                    registers_.write(
                        instruction.operandA,
                        registers_.read(instruction.operandB)
                    );
                }
                break;
            }

            case Opcode::ADD: {
                validateRegister(instruction.operandA);

                const auto left =
                    registers_.read(instruction.operandA);

                const auto right =
                    secondOperand(instruction);

                registers_.write(
                    instruction.operandA,
                    add16(left, right)
                );
                break;
            }

            case Opcode::SUB: {
                validateRegister(instruction.operandA);

                const auto left =
                    registers_.read(instruction.operandA);

                const auto right =
                    secondOperand(instruction);

                registers_.write(
                    instruction.operandA,
                    subtract16(left, right)
                );
                break;
            }

            case Opcode::AND:
            case Opcode::OR:
            case Opcode::XOR: {
                validateRegister(instruction.operandA);

                const auto left =
                    registers_.read(instruction.operandA);

                const auto right =
                    secondOperand(instruction);

                std::uint16_t result = 0;

                if (instruction.opcode == Opcode::AND) {
                    result = static_cast<std::uint16_t>(
                        left & right
                    );
                } else if (instruction.opcode == Opcode::OR) {
                    result = static_cast<std::uint16_t>(
                        left | right
                    );
                } else {
                    result = static_cast<std::uint16_t>(
                        left ^ right
                    );
                }

                registers_.write(
                    instruction.operandA,
                    result
                );

                updateFlags(result);
                break;
            }

            case Opcode::SHL: {
                validateRegister(instruction.operandA);

                const auto value =
                    registers_.read(instruction.operandA);

                const unsigned shift =
                    instruction.immediate & 0x1F;

                const std::uint32_t raw =
                    static_cast<std::uint32_t>(value) << shift;

                const auto result =
                    static_cast<std::uint16_t>(raw & 0xFFFFU);

                registers_.write(
                    instruction.operandA,
                    result
                );

                updateFlags(result, raw > 0xFFFFU);
                break;
            }

            case Opcode::SHR: {
                validateRegister(instruction.operandA);

                const auto value =
                    registers_.read(instruction.operandA);

                const unsigned shift =
                    instruction.immediate & 0x1F;

                const auto result =
                    static_cast<std::uint16_t>(
                        value >> shift
                    );

                registers_.write(
                    instruction.operandA,
                    result
                );

                updateFlags(result);
                break;
            }

            case Opcode::LOAD: {
                validateRegister(instruction.operandA);

                const std::size_t address =
                    effectiveAddress(instruction);

                registers_.write(
                    instruction.operandA,
                    memory_.readWord(address)
                );
                break;
            }

            case Opcode::STORE: {
                validateRegister(instruction.operandA);

                const std::size_t address =
                    effectiveAddress(instruction);

                memory_.writeWord(
                    address,
                    registers_.read(instruction.operandA)
                );
                break;
            }

            case Opcode::CMP: {
                validateRegister(instruction.operandA);

                const auto left =
                    registers_.read(instruction.operandA);

                const auto right =
                    secondOperand(instruction);

                // CMP changes flags but does not store the subtraction result.
                static_cast<void>(subtract16(left, right));
                break;
            }

            case Opcode::JMP:
                validateTarget(instruction.immediate);
                programCounter_ = instruction.immediate;
                break;

            case Opcode::JZ:
                if (flags_.zero) {
                    validateTarget(instruction.immediate);
                    programCounter_ = instruction.immediate;
                }
                break;

            case Opcode::HALT:
                halted_ = true;
                break;
        }

        ++steps_;

        if (steps_ > MAX_STEPS) {
            throw std::runtime_error(
                "Execution stopped by safety step limit."
            );
        }
    }

    void run() {
        while (!halted_) {
            step();
        }
    }

    void printState() const {
        std::cout << "Program counter: "
                  << programCounter_ << '\n';

        std::cout << "Registers: ";
        registers_.dump();

        std::cout << "Flags: ";
        flags_.print();

        std::cout << "Steps: "
                  << steps_ << '\n';
    }

    std::uint16_t readRegister(std::size_t index) const {
        return registers_.read(index);
    }

    std::uint16_t readMemoryWord(std::size_t address) const {
        return memory_.readWord(address);
    }
};

/*
 * Encoding:
 *
 *   31       24 23    20 19    16 15                 0
 *   +----------+--------+--------+--------------------+
 *   |  opcode  |  regA  |  regB  |     immediate     |
 *   +----------+--------+--------+--------------------+
 *
 * This is not a commercial ISA encoding. It is intentionally regular so that
 * the relationship between assembly fields and machine bits is visible.
 */
std::uint32_t encode(const Instruction& instruction) {
    const std::uint32_t opcode =
        static_cast<std::uint32_t>(instruction.opcode);

    if (instruction.operandA > 0x0F ||
        instruction.operandB > 0x0F) {
        throw std::runtime_error(
            "Register field does not fit in four bits."
        );
    }

    return (opcode << 24) |
           (static_cast<std::uint32_t>(instruction.operandA) << 20) |
           (static_cast<std::uint32_t>(instruction.operandB) << 16) |
           instruction.immediate;
}

Opcode decodeOpcode(std::uint32_t word) {
    const auto raw =
        static_cast<std::uint8_t>((word >> 24) & 0xFFU);

    switch (raw) {
        case 0x00: return Opcode::NOP;
        case 0x01: return Opcode::MOV;
        case 0x02: return Opcode::ADD;
        case 0x03: return Opcode::SUB;
        case 0x04: return Opcode::AND;
        case 0x05: return Opcode::OR;
        case 0x06: return Opcode::XOR;
        case 0x07: return Opcode::SHL;
        case 0x08: return Opcode::SHR;
        case 0x09: return Opcode::LOAD;
        case 0x0A: return Opcode::STORE;
        case 0x0B: return Opcode::JMP;
        case 0x0C: return Opcode::JZ;
        case 0x0D: return Opcode::CMP;
        case 0x0E: return Opcode::HALT;
        default:
            throw std::runtime_error("Unknown encoded opcode.");
    }
}

Instruction decode(std::uint32_t word) {
    Instruction instruction;

    instruction.opcode = decodeOpcode(word);
    instruction.operandA =
        static_cast<std::uint8_t>((word >> 20) & 0x0FU);
    instruction.operandB =
        static_cast<std::uint8_t>((word >> 16) & 0x0FU);
    instruction.immediate =
        static_cast<std::uint16_t>(word & 0xFFFFU);

    switch (instruction.opcode) {
        case Opcode::JMP:
        case Opcode::JZ:
        case Opcode::SHL:
        case Opcode::SHR:
            instruction.hasImmediate = true;
            break;

        case Opcode::MOV:
        case Opcode::ADD:
        case Opcode::SUB:
        case Opcode::AND:
        case Opcode::OR:
        case Opcode::XOR:
        case Opcode::CMP:
            /*
             * A zero immediate flag here means these instructions use
             * register operands in the demonstration program. A real ISA
             * would normally encode operand type explicitly.
             */
            instruction.hasImmediate = false;
            break;

        default:
            instruction.hasImmediate = false;
            break;
    }

    return instruction;
}

void printProgram(const std::vector<Instruction>& program) {
    std::cout << "\nProgram listing:\n";

    for (std::size_t address = 0;
         address < program.size();
         ++address) {
        std::cout
            << std::setw(2)
            << address
            << ": "
            << program[address].toString()
            << '\n';
    }
}

void demonstrateAddressingModes() {
    std::cout << "\nAddressing mode calculations:\n";

    const std::uint16_t base = 100;
    const std::uint16_t index = 20;
    const std::uint16_t offset = 12;
    const std::uint16_t pc = 50;

    std::cout << "Direct [200] = 200\n";
    std::cout << "Register indirect [R2] = "
              << base << '\n';
    std::cout << "Base + offset [R2+12] = "
              << base + offset << '\n';
    std::cout << "Indexed [R2+R3] = "
              << base + index << '\n';
    std::cout << "PC-relative [PC+16] = "
              << pc + 16 << '\n';
}

void demonstrateEncoding() {
    std::cout << "\nInstruction encoding:\n";

    Instruction add{
        Opcode::ADD,
        1,
        2,
        0,
        false
    };

    const auto machineWord = encode(add);

    std::cout
        << add.toString()
        << " -> 0x"
        << std::hex
        << std::setw(8)
        << std::setfill('0')
        << machineWord
        << std::dec
        << std::setfill(' ')
        << '\n';

    const auto decoded = decode(machineWord);

    std::cout
        << "Decoded opcode: "
        << opcodeName(decoded.opcode)
        << '\n';
}

int main() {
    try {
        std::cout
            << "ISA CASE STUDY: EMBEDDED TELEMETRY CONTROLLER\n"
            << "================================================\n";

        demonstrateAddressingModes();
        demonstrateEncoding();

        /*
         * Case-study memory map:
         *
         *   0x64 (100): temperature sample
         *   0x66 (102): pressure sample
         *   0x68 (104): computed value
         *
         * The CPU first loads two sensor values, adds them, stores the result,
         * then compares the result with an alert threshold.
         *
         * R0 = temperature
         * R1 = pressure
         * R2 = computed measurement
         * R3 = threshold
         */
        CPU cpu;

        /*
         * MOV R0, #250
         * MOV R1, #100
         *
         * These instructions use immediate operands. The constants are part
         * of the instruction rather than fetched from memory.
         *
         * STORE R0, [100]
         * STORE R1, [102]
         *
         * These instructions use direct addressing.
         *
         * LOAD R0, [100]
         * LOAD R1, [102]
         *
         * ADD R0, R1
         * STORE R0, [104]
         *
         * MOV R3, #300
         * CMP R0, R3
         * JZ 12
         * MOV R4, #0
         * HALT
         * MOV R4, #1
         * HALT
         *
         * Because 250 + 100 = 350, the comparison is not equal to 300,
         * so the normal path stores 0 in R4.
         */
        std::vector<Instruction> program{
            {Opcode::MOV,   0, 0, 250, true},
            {Opcode::MOV,   1, 0, 100, true},
            {Opcode::STORE, 0, 0, 100, false},
            {Opcode::STORE, 1, 0, 102, false},
            {Opcode::LOAD,  0, 0, 100, false},
            {Opcode::LOAD,  1, 0, 102, false},
            {Opcode::ADD,   0, 1, 0, false},
            {Opcode::STORE, 0, 0, 104, false},
            {Opcode::MOV,   3, 0, 300, true},
            {Opcode::CMP,   0, 3, 0, false},
            {Opcode::JZ,    0, 0, 13, true},
            {Opcode::MOV,   4, 0, 0, true},
            {Opcode::HALT,  0, 0, 0, false},
            {Opcode::MOV,   4, 0, 1, true},
            {Opcode::HALT,  0, 0, 0, false}
        };

        printProgram(program);

        std::cout << "\nEncoded first instruction: 0x"
                  << std::hex
                  << std::setw(8)
                  << std::setfill('0')
                  << encode(program.front())
                  << std::dec
                  << std::setfill(' ')
                  << '\n';

        cpu.loadProgram(program);
        cpu.run();

        std::cout << "\nFinal CPU state:\n";
        cpu.printState();

        std::cout
            << "\nComputed measurement in memory[104]: "
            << cpu.readMemoryWord(104)
            << '\n';

        std::cout
            << "Alert flag R4: "
            << cpu.readRegister(4)
            << '\n';

        /*
         * Edge-case demonstration:
         *
         * A 16-bit register cannot represent 65536. It wraps to zero.
         * This models modular fixed-width arithmetic.
         */
        CPU overflowCpu;

        std::vector<Instruction> overflowProgram{
            {Opcode::MOV, 0, 0, 65535, true},
            {Opcode::ADD, 0, 0, 1, true},
            {Opcode::HALT, 0, 0, 0, false}
        };

        overflowCpu.loadProgram(overflowProgram);

        /*
         * The ADD above is encoded with hasImmediate=true. This case study's
         * ADD supports that representation through secondOperand().
         */
        overflowCpu.run();

        std::cout
            << "\n16-bit overflow demonstration:\n"
            << "65535 + 1 -> "
            << overflowCpu.readRegister(0)
            << '\n';

        /*
         * Complexity:
         *
         * - Register access: O(1)
         * - Memory byte/word access: O(1)
         * - Instruction execution: O(1) per instruction
         * - Program execution: O(n) for n executed instructions, ignoring
         *   loops that may execute instructions repeatedly.
         *
         * Real processor performance is not determined only by these
         * algorithmic bounds. Pipeline depth, branch prediction, caches,
         * memory hierarchy, superscalar execution, hazards, and clock
         * frequency influence actual execution time.
         */

        /*
         * Security considerations:
         *
         * An ISA simulator should validate register indices, memory addresses,
         * instruction opcodes, branch targets, and execution limits.
         *
         * A real processor also requires hardware-enforced privilege levels,
         * memory protection, isolation, interrupt controls, and mechanisms
         * such as virtual memory where supported by the architecture.
         */
    }
    catch (const std::exception& error) {
        std::cerr
            << "Execution error: "
            << error.what()
            << '\n';

        return 1;
    }

    return 0;
}
