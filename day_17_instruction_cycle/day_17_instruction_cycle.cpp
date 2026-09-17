/*
 * Instruction Cycle: Fetch, Decode, Execute, Memory Access, Write Back
 *
 * Complete C++17 case study.
 *
 * Scenario:
 *   A small embedded telemetry processor receives sensor readings in memory.
 *   The processor executes a compact instruction program that:
 *
 *       1. loads sensor values,
 *       2. calculates an aggregate,
 *       3. compares the aggregate against a threshold,
 *       4. stores a status code,
 *       5. halts.
 *
 * The program demonstrates the complete instruction cycle:
 *
 *       FETCH -> DECODE -> EXECUTE -> MEMORY -> WRITE BACK
 *
 * It also demonstrates:
 *   - instruction representation
 *   - register file
 *   - program counter
 *   - ALU operations
 *   - memory addressing
 *   - control flow
 *   - validation
 *   - exceptions
 *   - statistics
 *   - modular design
 *   - pipeline concepts
 *   - dependency and hazard analysis
 *   - algorithmic complexity
 *
 * Compile:
 *   g++ -std=c++17 -O2 instruction_cycle.cpp -o instruction_cycle
 */

#include <algorithm>
#include <array>
#include <cstdint>
#include <exception>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using Word = std::int32_t;


// -----------------------------------------------------------------------------
// Opcode
// -----------------------------------------------------------------------------

enum class Opcode {
    NOP,
    HALT,

    ADD,
    SUB,
    MUL,
    DIV,

    AND_OP,
    OR_OP,
    XOR_OP,

    ADDI,
    MOVI,

    LOAD,
    STORE,

    CMP,

    BEQ,
    BNE,
    BLT,
    BGT,
    JMP
};


std::string opcodeName(Opcode opcode) {
    switch (opcode) {
        case Opcode::NOP: return "NOP";
        case Opcode::HALT: return "HALT";
        case Opcode::ADD: return "ADD";
        case Opcode::SUB: return "SUB";
        case Opcode::MUL: return "MUL";
        case Opcode::DIV: return "DIV";
        case Opcode::AND_OP: return "AND";
        case Opcode::OR_OP: return "OR";
        case Opcode::XOR_OP: return "XOR";
        case Opcode::ADDI: return "ADDI";
        case Opcode::MOVI: return "MOVI";
        case Opcode::LOAD: return "LOAD";
        case Opcode::STORE: return "STORE";
        case Opcode::CMP: return "CMP";
        case Opcode::BEQ: return "BEQ";
        case Opcode::BNE: return "BNE";
        case Opcode::BLT: return "BLT";
        case Opcode::BGT: return "BGT";
        case Opcode::JMP: return "JMP";
    }

    return "UNKNOWN";
}


// -----------------------------------------------------------------------------
// Instruction
// -----------------------------------------------------------------------------

struct Instruction {
    Opcode opcode{Opcode::NOP};

    int rd{-1};
    int rs1{-1};
    int rs2{-1};

    Word immediate{0};
    int target{-1};

    std::string toString() const {
        std::ostringstream out;

        out << opcodeName(opcode);

        switch (opcode) {
            case Opcode::NOP:
            case Opcode::HALT:
                break;

            case Opcode::ADD:
            case Opcode::SUB:
            case Opcode::MUL:
            case Opcode::DIV:
            case Opcode::AND_OP:
            case Opcode::OR_OP:
            case Opcode::XOR_OP:
                out << " R" << rd
                    << ", R" << rs1
                    << ", R" << rs2;
                break;

            case Opcode::ADDI:
                out << " R" << rd
                    << ", R" << rs1
                    << ", " << immediate;
                break;

            case Opcode::MOVI:
                out << " R" << rd
                    << ", " << immediate;
                break;

            case Opcode::LOAD:
                out << " R" << rd
                    << ", [R" << rs1
                    << " + " << immediate << "]";
                break;

            case Opcode::STORE:
                out << " R" << rs1
                    << ", [R" << rs2
                    << " + " << immediate << "]";
                break;

            case Opcode::CMP:
                out << " R" << rs1
                    << ", R" << rs2;
                break;

            case Opcode::BEQ:
            case Opcode::BNE:
            case Opcode::BLT:
            case Opcode::BGT:
            case Opcode::JMP:
                out << " " << target;
                break;
        }

        return out.str();
    }
};


// -----------------------------------------------------------------------------
// Instruction constructors
// -----------------------------------------------------------------------------

Instruction movi(int rd, Word value) {
    return {Opcode::MOVI, rd, -1, -1, value, -1};
}

Instruction add(int rd, int rs1, int rs2) {
    return {Opcode::ADD, rd, rs1, rs2, 0, -1};
}

Instruction sub(int rd, int rs1, int rs2) {
    return {Opcode::SUB, rd, rs1, rs2, 0, -1};
}

Instruction mul(int rd, int rs1, int rs2) {
    return {Opcode::MUL, rd, rs1, rs2, 0, -1};
}

Instruction addi(int rd, int rs1, Word value) {
    return {Opcode::ADDI, rd, rs1, -1, value, -1};
}

Instruction load(int rd, int base, Word offset) {
    return {Opcode::LOAD, rd, base, -1, offset, -1};
}

Instruction store(int source, int base, Word offset) {
    return {Opcode::STORE, -1, source, base, offset, -1};
}

Instruction cmp(int rs1, int rs2) {
    return {Opcode::CMP, -1, rs1, rs2, 0, -1};
}

Instruction beq(int target) {
    return {Opcode::BEQ, -1, -1, -1, 0, target};
}

Instruction blt(int target) {
    return {Opcode::BLT, -1, -1, -1, 0, target};
}

Instruction halt() {
    return {Opcode::HALT};
}


// -----------------------------------------------------------------------------
// Processor exceptions
// -----------------------------------------------------------------------------

class CPUException : public std::runtime_error {
public:
    explicit CPUException(const std::string& message)
        : std::runtime_error(message) {}
};

class MemoryException : public CPUException {
public:
    explicit MemoryException(const std::string& message)
        : CPUException(message) {}
};

class RegisterException : public CPUException {
public:
    explicit RegisterException(const std::string& message)
        : CPUException(message) {}
};

class DivisionByZeroException : public CPUException {
public:
    explicit DivisionByZeroException(const std::string& message)
        : CPUException(message) {}
};


// -----------------------------------------------------------------------------
// CPU control state
// -----------------------------------------------------------------------------

struct Flags {
    bool zero{false};
    bool negative{false};
    bool carry{false};
    bool overflow{false};
};


struct ControlSignals {
    bool alu{false};
    bool memoryRead{false};
    bool memoryWrite{false};
    bool writeBack{false};
    bool branch{false};
    bool halt{false};
};


struct ExecutionResult {
    std::optional<Word> aluResult;
    std::optional<int> memoryAddress;
    std::optional<Word> storeValue;
    std::optional<Word> writeValue;

    bool branchTaken{false};
};


// -----------------------------------------------------------------------------
// CPU
// -----------------------------------------------------------------------------

class CPU {
public:
    static constexpr std::size_t RegisterCount = 8;
    static constexpr std::size_t MemorySize = 256;

private:
    std::vector<Instruction> program_;
    std::array<Word, RegisterCount> registers_{};
    std::array<Word, MemorySize> memory_{};

    Flags flags_{};

    std::size_t pc_{0};
    std::size_t cycles_{0};
    std::size_t instructionsExecuted_{0};

    bool halted_{false};
    bool traceEnabled_{true};

    std::map<std::string, std::size_t> statistics_{
        {"arithmetic", 0},
        {"logical", 0},
        {"memory", 0},
        {"branch", 0},
        {"control", 0}
    };

public:
    explicit CPU(
        std::vector<Instruction> program,
        bool trace = true
    )
        : program_(std::move(program)),
          traceEnabled_(trace) {}

    // -------------------------------------------------------------------------
    // Register access
    // -------------------------------------------------------------------------

    Word readRegister(int index) const {
        validateRegister(index);
        return registers_[static_cast<std::size_t>(index)];
    }

    void writeRegister(int index, Word value) {
        validateRegister(index);
        registers_[static_cast<std::size_t>(index)] = value;
    }

    void validateRegister(int index) const {
        if (index < 0 ||
            index >= static_cast<int>(RegisterCount)) {
            throw RegisterException(
                "Invalid register R" + std::to_string(index)
            );
        }
    }

    // -------------------------------------------------------------------------
    // Memory access
    // -------------------------------------------------------------------------

    Word readMemory(int address) const {
        validateMemory(address);
        return memory_[static_cast<std::size_t>(address)];
    }

    void writeMemory(int address, Word value) {
        validateMemory(address);
        memory_[static_cast<std::size_t>(address)] = value;
    }

    void validateMemory(int address) const {
        if (address < 0 ||
            address >= static_cast<int>(MemorySize)) {
            throw MemoryException(
                "Memory address out of bounds: " +
                std::to_string(address)
            );
        }
    }

    // -------------------------------------------------------------------------
    // Trace
    // -------------------------------------------------------------------------

    void trace(const std::string& message) const {
        if (!traceEnabled_) {
            return;
        }

        std::cout
            << "[cycle "
            << std::setw(3)
            << cycles_
            << "] "
            << message
            << '\n';
    }

    // -------------------------------------------------------------------------
    // FETCH
    // -------------------------------------------------------------------------

    std::pair<std::size_t, Instruction> fetch() {
        if (pc_ >= program_.size()) {
            throw CPUException(
                "Program counter outside instruction memory: " +
                std::to_string(pc_)
            );
        }

        const std::size_t currentPC = pc_;
        const Instruction instruction = program_[pc_];

        // One instruction occupies one logical program slot in this model.
        ++pc_;

        trace(
            "FETCH   PC=" +
            std::to_string(currentPC) +
            "  " +
            instruction.toString()
        );

        return {currentPC, instruction};
    }

    // -------------------------------------------------------------------------
    // DECODE
    // -------------------------------------------------------------------------

    ControlSignals decode(const Instruction& instruction) {
        ControlSignals signals;

        switch (instruction.opcode) {
            case Opcode::ADD:
            case Opcode::SUB:
            case Opcode::MUL:
            case Opcode::DIV:
            case Opcode::ADDI:
            case Opcode::MOVI:
            case Opcode::CMP:
                signals.alu = true;
                break;

            case Opcode::LOAD:
                signals.alu = true;
                signals.memoryRead = true;
                signals.writeBack = true;
                break;

            case Opcode::STORE:
                signals.alu = true;
                signals.memoryWrite = true;
                break;

            case Opcode::AND_OP:
            case Opcode::OR_OP:
            case Opcode::XOR_OP:
                signals.alu = true;
                break;

            case Opcode::BEQ:
            case Opcode::BNE:
            case Opcode::BLT:
            case Opcode::BGT:
                signals.branch = true;
                break;

            case Opcode::HALT:
                signals.halt = true;
                break;

            case Opcode::NOP:
            case Opcode::JMP:
                break;
        }

        if (instruction.opcode == Opcode::ADD ||
            instruction.opcode == Opcode::SUB ||
            instruction.opcode == Opcode::MUL ||
            instruction.opcode == Opcode::DIV ||
            instruction.opcode == Opcode::ADDI ||
            instruction.opcode == Opcode::MOVI ||
            instruction.opcode == Opcode::LOAD ||
            instruction.opcode == Opcode::AND_OP ||
            instruction.opcode == Opcode::OR_OP ||
            instruction.opcode == Opcode::XOR_OP) {
            signals.writeBack = true;
        }

        trace(
            "DECODE  " +
            instruction.toString()
        );

        return signals;
    }

    // -------------------------------------------------------------------------
    // EXECUTE
    // -------------------------------------------------------------------------

    ExecutionResult execute(
        const Instruction& instruction
    ) {
        ExecutionResult result;

        auto r = [this](int index) {
            return readRegister(index);
        };

        switch (instruction.opcode) {
            case Opcode::NOP:
                break;

            case Opcode::MOVI: {
                const Word value = instruction.immediate;

                result.aluResult = value;
                result.writeValue = value;

                updateFlags(value);
                ++statistics_["arithmetic"];
                break;
            }

            case Opcode::ADD: {
                const Word value =
                    r(instruction.rs1) +
                    r(instruction.rs2);

                result.aluResult = value;
                result.writeValue = value;

                updateFlags(value);
                ++statistics_["arithmetic"];
                break;
            }

            case Opcode::SUB: {
                const Word value =
                    r(instruction.rs1) -
                    r(instruction.rs2);

                result.aluResult = value;
                result.writeValue = value;

                updateFlags(value);
                ++statistics_["arithmetic"];
                break;
            }

            case Opcode::MUL: {
                const Word value =
                    r(instruction.rs1) *
                    r(instruction.rs2);

                result.aluResult = value;
                result.writeValue = value;

                updateFlags(value);
                ++statistics_["arithmetic"];
                break;
            }

            case Opcode::DIV: {
                const Word divisor = r(instruction.rs2);

                if (divisor == 0) {
                    throw DivisionByZeroException(
                        "DIV attempted with divisor zero."
                    );
                }

                const Word value =
                    r(instruction.rs1) / divisor;

                result.aluResult = value;
                result.writeValue = value;

                updateFlags(value);
                ++statistics_["arithmetic"];
                break;
            }

            case Opcode::ADDI: {
                const Word value =
                    r(instruction.rs1) +
                    instruction.immediate;

                result.aluResult = value;
                result.writeValue = value;

                updateFlags(value);
                ++statistics_["arithmetic"];
                break;
            }

            case Opcode::AND_OP: {
                const Word value =
                    r(instruction.rs1) &
                    r(instruction.rs2);

                result.aluResult = value;
                result.writeValue = value;

                updateFlags(value);
                ++statistics_["logical"];
                break;
            }

            case Opcode::OR_OP: {
                const Word value =
                    r(instruction.rs1) |
                    r(instruction.rs2);

                result.aluResult = value;
                result.writeValue = value;

                updateFlags(value);
                ++statistics_["logical"];
                break;
            }

            case Opcode::XOR_OP: {
                const Word value =
                    r(instruction.rs1) ^
                    r(instruction.rs2);

                result.aluResult = value;
                result.writeValue = value;

                updateFlags(value);
                ++statistics_["logical"];
                break;
            }

            case Opcode::LOAD: {
                const Word address =
                    r(instruction.rs1) +
                    instruction.immediate;

                result.memoryAddress =
                    static_cast<int>(address);

                ++statistics_["memory"];
                break;
            }

            case Opcode::STORE: {
                const Word address =
                    r(instruction.rs2) +
                    instruction.immediate;

                result.memoryAddress =
                    static_cast<int>(address);

                result.storeValue =
                    r(instruction.rs1);

                ++statistics_["memory"];
                break;
            }

            case Opcode::CMP: {
                const Word difference =
                    r(instruction.rs1) -
                    r(instruction.rs2);

                updateFlags(difference);
                ++statistics_["arithmetic"];
                break;
            }

            case Opcode::BEQ:
                result.branchTaken = flags_.zero;
                ++statistics_["branch"];
                break;

            case Opcode::BNE:
                result.branchTaken = !flags_.zero;
                ++statistics_["branch"];
                break;

            case Opcode::BLT:
                result.branchTaken = flags_.negative;
                ++statistics_["branch"];
                break;

            case Opcode::BGT:
                result.branchTaken =
                    !flags_.zero &&
                    !flags_.negative;

                ++statistics_["branch"];
                break;

            case Opcode::JMP:
                result.branchTaken = true;
                ++statistics_["branch"];
                break;

            case Opcode::HALT:
                ++statistics_["control"];
                break;
        }

        trace(
            "EXECUTE " +
            instruction.toString()
        );

        return result;
    }

    // -------------------------------------------------------------------------
    // MEMORY ACCESS
    // -------------------------------------------------------------------------

    void memoryAccess(
        const Instruction& instruction,
        ExecutionResult& result
    ) {
        if (instruction.opcode == Opcode::LOAD) {
            if (!result.memoryAddress.has_value()) {
                throw CPUException(
                    "LOAD did not produce an address."
                );
            }

            const Word value =
                readMemory(*result.memoryAddress);

            result.writeValue = value;

            trace(
                "MEMORY  LOAD[" +
                std::to_string(*result.memoryAddress) +
                "] -> " +
                std::to_string(value)
            );
        }

        if (instruction.opcode == Opcode::STORE) {
            if (!result.memoryAddress.has_value() ||
                !result.storeValue.has_value()) {
                throw CPUException(
                    "STORE missing address or value."
                );
            }

            writeMemory(
                *result.memoryAddress,
                *result.storeValue
            );

            trace(
                "MEMORY  STORE[" +
                std::to_string(*result.memoryAddress) +
                "] <- " +
                std::to_string(*result.storeValue)
            );
        }
    }

    // -------------------------------------------------------------------------
    // WRITE BACK
    // -------------------------------------------------------------------------

    void writeBack(
        const Instruction& instruction,
        const ExecutionResult& result
    ) {
        const bool writesRegister =
            instruction.opcode == Opcode::ADD ||
            instruction.opcode == Opcode::SUB ||
            instruction.opcode == Opcode::MUL ||
            instruction.opcode == Opcode::DIV ||
            instruction.opcode == Opcode::ADDI ||
            instruction.opcode == Opcode::MOVI ||
            instruction.opcode == Opcode::LOAD ||
            instruction.opcode == Opcode::AND_OP ||
            instruction.opcode == Opcode::OR_OP ||
            instruction.opcode == Opcode::XOR_OP;

        if (!writesRegister) {
            return;
        }

        if (!result.writeValue.has_value()) {
            throw CPUException(
                "Instruction requires write-back but has no result."
            );
        }

        writeRegister(
            instruction.rd,
            *result.writeValue
        );

        trace(
            "WRITE   R" +
            std::to_string(instruction.rd) +
            " <- " +
            std::to_string(*result.writeValue)
        );
    }

    // -------------------------------------------------------------------------
    // FLAGS
    // -------------------------------------------------------------------------

    void updateFlags(Word value) {
        flags_.zero = value == 0;
        flags_.negative = value < 0;

        // Carry and overflow are architecture-specific. This educational
        // processor keeps them available but does not model every bit-width
        // overflow rule.
        flags_.carry = false;
        flags_.overflow = false;
    }

    // -------------------------------------------------------------------------
    // Run
    // -------------------------------------------------------------------------

    void run(std::size_t maxInstructions = 10000) {
        while (!halted_) {
            if (instructionsExecuted_ >= maxInstructions) {
                throw CPUException(
                    "Instruction limit exceeded."
                );
            }

            ++cycles_;

            const auto [address, instruction] = fetch();

            const ControlSignals control =
                decode(instruction);

            (void)control;

            ExecutionResult result =
                execute(instruction);

            memoryAccess(
                instruction,
                result
            );

            writeBack(
                instruction,
                result
            );

            if (result.branchTaken) {
                if (instruction.target < 0 ||
                    instruction.target >=
                        static_cast<int>(program_.size())) {
                    throw CPUException(
                        "Invalid branch target: " +
                        std::to_string(instruction.target)
                    );
                }

                pc_ =
                    static_cast<std::size_t>(
                        instruction.target
                    );

                trace(
                    "CONTROL branch -> PC=" +
                    std::to_string(pc_)
                );
            }

            if (instruction.opcode == Opcode::HALT) {
                halted_ = true;
            }

            ++instructionsExecuted_;
        }
    }

    // -------------------------------------------------------------------------
    // Diagnostic output
    // -------------------------------------------------------------------------

    void dumpState() const {
        std::cout << "\nCPU STATE\n";
        std::cout << "=========\n";

        std::cout
            << "PC: " << pc_ << '\n'
            << "Cycles: " << cycles_ << '\n'
            << "Instructions: "
            << instructionsExecuted_
            << '\n';

        std::cout
            << "Flags: Z="
            << flags_.zero
            << " N="
            << flags_.negative
            << " C="
            << flags_.carry
            << " V="
            << flags_.overflow
            << '\n';

        std::cout << "\nRegisters\n";

        for (std::size_t i = 0; i < RegisterCount; ++i) {
            std::cout
                << "R"
                << i
                << " = "
                << registers_[i]
                << '\n';
        }

        std::cout << "\nNon-zero memory\n";

        for (std::size_t i = 0; i < MemorySize; ++i) {
            if (memory_[i] != 0) {
                std::cout
                    << "MEM["
                    << i
                    << "] = "
                    << memory_[i]
                    << '\n';
            }
        }

        std::cout << "\nInstruction statistics\n";

        for (const auto& [name, count] : statistics_) {
            std::cout
                << std::left
                << std::setw(12)
                << name
                << count
                << '\n';
        }
    }
};


// -----------------------------------------------------------------------------
// Pipeline analysis
// -----------------------------------------------------------------------------

struct PipelineAnalysis {
    std::size_t instructions{0};
    std::size_t idealCycles{0};
    std::size_t estimatedSequentialCycles{0};
};


PipelineAnalysis analyzePipeline(
    const std::vector<Instruction>& program
) {
    PipelineAnalysis analysis;

    analysis.instructions = program.size();

    if (!program.empty()) {
        // Five stages require four additional cycles to fill and drain.
        analysis.idealCycles =
            program.size() + 4;
    }

    analysis.estimatedSequentialCycles =
        program.size();

    return analysis;
}


// -----------------------------------------------------------------------------
// Dependency analysis
// -----------------------------------------------------------------------------

std::optional<int> destinationRegister(
    const Instruction& instruction
) {
    switch (instruction.opcode) {
        case Opcode::ADD:
        case Opcode::SUB:
        case Opcode::MUL:
        case Opcode::DIV:
        case Opcode::ADDI:
        case Opcode::MOVI:
        case Opcode::LOAD:
        case Opcode::AND_OP:
        case Opcode::OR_OP:
        case Opcode::XOR_OP:
            return instruction.rd;

        default:
            return std::nullopt;
    }
}


std::vector<int> sourceRegisters(
    const Instruction& instruction
) {
    switch (instruction.opcode) {
        case Opcode::ADD:
        case Opcode::SUB:
        case Opcode::MUL:
        case Opcode::DIV:
        case Opcode::AND_OP:
        case Opcode::OR_OP:
        case Opcode::XOR_OP:
            return {
                instruction.rs1,
                instruction.rs2
            };

        case Opcode::ADDI:
        case Opcode::LOAD:
            return {
                instruction.rs1
            };

        case Opcode::STORE:
            return {
                instruction.rs1,
                instruction.rs2
            };

        case Opcode::CMP:
            return {
                instruction.rs1,
                instruction.rs2
            };

        default:
            return {};
    }
}


bool hasReadAfterWriteHazard(
    const Instruction& producer,
    const Instruction& consumer
) {
    const auto destination =
        destinationRegister(producer);

    if (!destination.has_value()) {
        return false;
    }

    const auto sources =
        sourceRegisters(consumer);

    return std::find(
        sources.begin(),
        sources.end(),
        *destination
    ) != sources.end();
}


// -----------------------------------------------------------------------------
// Industry-style telemetry processor scenario
// -----------------------------------------------------------------------------

void runTelemetryCaseStudy() {
    std::cout
        << "\n"
        << std::string(70, '=')
        << "\n"
        << "C++ CASE STUDY: EMBEDDED SENSOR TELEMETRY PROCESSOR\n"
        << std::string(70, '=')
        << "\n";

    /*
     * Memory map:
     *
     *   100 = sensor A
     *   101 = sensor B
     *   102 = sensor C
     *   110 = output status
     *
     * Register plan:
     *
     *   R1 = base address 100
     *   R2 = sensor A
     *   R3 = sensor B
     *   R4 = sensor C
     *   R5 = aggregate
     *   R6 = threshold
     *   R7 = status
     *
     * The program calculates:
     *
     *       aggregate = A + B + C
     *
     * If aggregate < threshold:
     *
     *       status = 0
     *
     * Otherwise:
     *
     *       status = 1
     */

    std::vector<Instruction> program = {
        movi(1, 100),        // 0: base address

        load(2, 1, 0),       // 1: sensor A
        load(3, 1, 1),       // 2: sensor B
        load(4, 1, 2),       // 3: sensor C

        add(5, 2, 3),        // 4: A + B
        add(5, 5, 4),        // 5: A + B + C

        movi(6, 100),        // 6: threshold

        cmp(5, 6),           // 7
        blt(11),             // 8: low status

        movi(7, 1),          // 9: high status
        store(7, 1, 10),     // 10: MEM[110] = 1
        halt(),               // 11
    };

    CPU cpu(program, true);

    // External sensor data arrives in data memory before execution.
    cpu.writeMemory(100, 20);
    cpu.writeMemory(101, 30);
    cpu.writeMemory(102, 70);

    cpu.run();

    cpu.dumpState();

    const Word aggregate = cpu.readRegister(5);
    const Word status = cpu.readMemory(110);

    std::cout
        << "\nTelemetry result\n"
        << "-----------------\n"
        << "Aggregate: "
        << aggregate
        << '\n'
        << "Status: "
        << status
        << '\n';

    /*
     * With 20 + 30 + 70 = 120 and threshold 100,
     * the high-status path should store 1.
     */
    if (aggregate != 120) {
        throw CPUException(
            "Telemetry aggregate validation failed."
        );
    }

    if (status != 1) {
        throw CPUException(
            "Telemetry status validation failed."
        );
    }

    const PipelineAnalysis analysis =
        analyzePipeline(program);

    std::cout
        << "\nPipeline analysis\n"
        << "-----------------\n"
        << "Instructions: "
        << analysis.instructions
        << '\n'
        << "Ideal five-stage pipeline cycles: "
        << analysis.idealCycles
        << '\n'
        << "Sequential estimate: "
        << analysis.estimatedSequentialCycles
        << '\n';

    /*
     * Demonstrate a RAW dependency:
     *
     *   ADD R5, R2, R3
     *   ADD R6, R5, R4
     *
     * The second instruction needs the value produced by the first.
     */
    const bool hazard =
        hasReadAfterWriteHazard(
            program[4],
            program[5]
        );

    std::cout
        << "RAW hazard between instructions 4 and 5: "
        << std::boolalpha
        << hazard
        << '\n';
}


// -----------------------------------------------------------------------------
// Fault demonstrations
// -----------------------------------------------------------------------------

void demonstrateFaultHandling() {
    std::cout
        << "\n"
        << std::string(70, '=')
        << "\n"
        << "FAULT HANDLING\n"
        << std::string(70, '=')
        << "\n";

    try {
        CPU cpu({
            movi(1, 10),
            movi(2, 0),
            {Opcode::DIV, 3, 1, 2, 0, -1},
            halt()
        }, false);

        cpu.run();
    }
    catch (const DivisionByZeroException& error) {
        std::cout
            << "Expected arithmetic fault: "
            << error.what()
            << '\n';
    }

    try {
        CPU cpu({
            movi(1, 999),
            load(2, 1, 0),
            halt()
        }, false);

        cpu.run();
    }
    catch (const MemoryException& error) {
        std::cout
            << "Expected memory fault: "
            << error.what()
            << '\n';
    }
}


// -----------------------------------------------------------------------------
// Main
// -----------------------------------------------------------------------------

int main() {
    try {
        runTelemetryCaseStudy();
        demonstrateFaultHandling();

        std::cout
            << "\n"
            << std::string(70, '=')
            << "\n"
            << "CASE STUDY COMPLETED\n"
            << std::string(70, '=')
            << "\n";

        return 0;
    }
    catch (const std::exception& error) {
        std::cerr
            << "CPU simulation failed: "
            << error.what()
            << '\n';

        return 1;
    }
}
