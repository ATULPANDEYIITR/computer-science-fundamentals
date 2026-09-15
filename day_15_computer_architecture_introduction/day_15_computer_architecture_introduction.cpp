/*
 * Computer Architecture Introduction
 * ===================================
 *
 * C++17 industry-style educational case study:
 *
 * A small embedded sensor-processing computer is modeled from the ISA level
 * down to CPU registers, memory, ALU operations, I/O, cache behavior and
 * instruction execution.
 *
 * Build:
 *     g++ -std=c++17 -O2 computer_architecture_introduction.cpp -o architecture
 *
 * Run:
 *     ./architecture
 *
 * Windows:
 *     architecture.exe
 */

#include <algorithm>
#include <array>
#include <cstdint>
#include <exception>
#include <iomanip>
#include <iostream>
#include <optional>
#include <queue>
#include <random>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using Byte = std::uint8_t;
using Word = std::uint16_t;


// ============================================================================
// 1. ISA DEFINITION
// ============================================================================

enum class Opcode : Byte {
    NOP       = 0x00,
    LOAD_IMM  = 0x10,
    LOAD      = 0x11,
    STORE     = 0x12,
    ADD       = 0x20,
    SUB       = 0x21,
    AND_OP    = 0x22,
    OR_OP     = 0x23,
    XOR_OP    = 0x24,
    SHL       = 0x25,
    SHR       = 0x26,
    JMP       = 0x30,
    JZ        = 0x31,
    CMP       = 0x32,
    IN        = 0x40,
    OUT       = 0x41,
    HALT      = 0xFF
};

std::string opcodeName(Opcode opcode) {
    switch (opcode) {
        case Opcode::NOP:      return "NOP";
        case Opcode::LOAD_IMM: return "LOAD_IMM";
        case Opcode::LOAD:     return "LOAD";
        case Opcode::STORE:    return "STORE";
        case Opcode::ADD:      return "ADD";
        case Opcode::SUB:      return "SUB";
        case Opcode::AND_OP:   return "AND";
        case Opcode::OR_OP:    return "OR";
        case Opcode::XOR_OP:   return "XOR";
        case Opcode::SHL:      return "SHL";
        case Opcode::SHR:      return "SHR";
        case Opcode::JMP:      return "JMP";
        case Opcode::JZ:       return "JZ";
        case Opcode::CMP:      return "CMP";
        case Opcode::IN:       return "IN";
        case Opcode::OUT:      return "OUT";
        case Opcode::HALT:     return "HALT";
    }

    return "UNKNOWN";
}


// ============================================================================
// 2. INSTRUCTION REPRESENTATION
// ============================================================================

struct Instruction {
    Opcode opcode;
    Byte operand;

    Word encode() const {
        // The educational ISA uses:
        // high byte = opcode
        // low byte  = operand
        return static_cast<Word>(
            (static_cast<Word>(opcode) << 8) | operand
        );
    }

    static Instruction decode(Word word) {
        const Byte rawOpcode = static_cast<Byte>((word >> 8) & 0xFF);
        const Byte operand = static_cast<Byte>(word & 0xFF);

        const Opcode opcode = static_cast<Opcode>(rawOpcode);

        switch (opcode) {
            case Opcode::NOP:
            case Opcode::LOAD_IMM:
            case Opcode::LOAD:
            case Opcode::STORE:
            case Opcode::ADD:
            case Opcode::SUB:
            case Opcode::AND_OP:
            case Opcode::OR_OP:
            case Opcode::XOR_OP:
            case Opcode::SHL:
            case Opcode::SHR:
            case Opcode::JMP:
            case Opcode::JZ:
            case Opcode::CMP:
            case Opcode::IN:
            case Opcode::OUT:
            case Opcode::HALT:
                return {opcode, operand};
        }

        throw std::runtime_error("Unknown opcode: " +
                                 std::to_string(rawOpcode));
    }

    std::string toString() const {
        if (operand != 0) {
            return opcodeName(opcode) + " " + std::to_string(operand);
        }

        return opcodeName(opcode);
    }
};


// ============================================================================
// 3. MEMORY
// ============================================================================

class Memory {
private:
    std::vector<Byte> bytes;

    void validateAddress(std::size_t address) const {
        if (address >= bytes.size()) {
            throw std::out_of_range("Memory address out of range: " +
                                    std::to_string(address));
        }
    }

public:
    explicit Memory(std::size_t size)
        : bytes(size, 0) {
        if (size == 0) {
            throw std::invalid_argument("Memory size must be positive.");
        }
    }

    std::size_t size() const {
        return bytes.size();
    }

    Byte readByte(std::size_t address) const {
        validateAddress(address);
        return bytes[address];
    }

    void writeByte(std::size_t address, Byte value) {
        validateAddress(address);
        bytes[address] = value;
    }

    Word readWordBE(std::size_t address) const {
        if (address + 1 >= bytes.size()) {
            throw std::out_of_range("16-bit memory read out of range.");
        }

        return static_cast<Word>(
            (static_cast<Word>(bytes[address]) << 8) |
            bytes[address + 1]
        );
    }

    void writeWordBE(std::size_t address, Word value) {
        if (address + 1 >= bytes.size()) {
            throw std::out_of_range("16-bit memory write out of range.");
        }

        bytes[address] =
            static_cast<Byte>((value >> 8) & 0xFF);

        bytes[address + 1] =
            static_cast<Byte>(value & 0xFF);
    }

    void dump(std::size_t start, std::size_t end) const {
        for (std::size_t address = start;
             address < end && address < bytes.size();
             ++address) {

            std::cout
                << std::hex
                << std::uppercase
                << std::setw(4)
                << std::setfill('0')
                << address
                << ": "
                << std::setw(2)
                << static_cast<int>(bytes[address])
                << '\n';
        }

        std::cout << std::dec;
    }
};


// ============================================================================
// 4. ALU
// ============================================================================

struct ALUResult {
    Byte result;
    bool flag;
};

class ALU {
public:
    ALUResult add(Byte a, Byte b) const {
        const unsigned int raw =
            static_cast<unsigned int>(a) +
            static_cast<unsigned int>(b);

        return {
            static_cast<Byte>(raw & 0xFF),
            raw > 0xFF
        };
    }

    ALUResult subtract(Byte a, Byte b) const {
        const int raw =
            static_cast<int>(a) -
            static_cast<int>(b);

        return {
            static_cast<Byte>(raw & 0xFF),
            raw < 0
        };
    }

    Byte bitAnd(Byte a, Byte b) const {
        return static_cast<Byte>(a & b);
    }

    Byte bitOr(Byte a, Byte b) const {
        return static_cast<Byte>(a | b);
    }

    Byte bitXor(Byte a, Byte b) const {
        return static_cast<Byte>(a ^ b);
    }

    Byte shiftLeft(Byte value, Byte amount) const {
        if (amount >= 8) {
            return 0;
        }

        return static_cast<Byte>(
            (static_cast<unsigned int>(value) << amount) & 0xFF
        );
    }

    Byte shiftRight(Byte value, Byte amount) const {
        if (amount >= 8) {
            return 0;
        }

        return static_cast<Byte>(value >> amount);
    }
};


// ============================================================================
// 5. I/O DEVICES
// ============================================================================

class SensorDevice {
private:
    std::queue<Byte> samples;

public:
    explicit SensorDevice(std::vector<Byte> initialSamples) {
        for (Byte sample : initialSamples) {
            samples.push(sample);
        }
    }

    Byte read() {
        if (samples.empty()) {
            throw std::runtime_error("Sensor has no data.");
        }

        Byte value = samples.front();
        samples.pop();
        return value;
    }
};

class ConsoleDevice {
private:
    std::vector<Byte> values;

public:
    void write(Byte value) {
        values.push_back(value);
        std::cout << "[CONSOLE DEVICE] " << static_cast<int>(value)
                  << '\n';
    }

    const std::vector<Byte>& history() const {
        return values;
    }
};


// ============================================================================
// 6. DIRECT-MAPPED CACHE
// ============================================================================

class DirectMappedCache {
private:
    struct Line {
        bool valid = false;
        std::size_t tag = 0;
        std::size_t address = 0;
    };

    std::vector<Line> lines;
    std::size_t hitCount = 0;
    std::size_t missCount = 0;

public:
    explicit DirectMappedCache(std::size_t lineCount)
        : lines(lineCount) {

        if (lineCount == 0) {
            throw std::invalid_argument("Cache must have at least one line.");
        }
    }

    bool access(std::size_t address) {
        const std::size_t index = address % lines.size();
        const std::size_t tag = address / lines.size();

        Line& line = lines[index];

        if (line.valid && line.tag == tag) {
            ++hitCount;
            return true;
        }

        ++missCount;
        line.valid = true;
        line.tag = tag;
        line.address = address;

        return false;
    }

    std::size_t hits() const {
        return hitCount;
    }

    std::size_t misses() const {
        return missCount;
    }

    double hitRate() const {
        const std::size_t total = hitCount + missCount;

        if (total == 0) {
            return 0.0;
        }

        return static_cast<double>(hitCount) /
               static_cast<double>(total);
    }
};


// ============================================================================
// 7. CPU
// ============================================================================

class CPU {
private:
    Memory memory;
    ALU alu;

    // Programmer-visible and internal CPU registers.
    Word pc = 0;
    Word ir = 0;
    Byte acc = 0;
    Byte mar = 0;
    Byte mdr = 0;

    bool zeroFlag = false;
    bool carryFlag = false;
    bool halted = false;

    std::uint64_t cycles = 0;
    std::uint64_t instructionsExecuted = 0;

    ConsoleDevice& console;

public:
    explicit CPU(
        std::size_t memorySize,
        ConsoleDevice& outputDevice
    )
        : memory(memorySize),
          console(outputDevice) {}

    Memory& getMemory() {
        return memory;
    }

    const Memory& getMemory() const {
        return memory;
    }

    void loadProgram(
        const std::vector<Instruction>& program,
        std::size_t startAddress = 0
    ) {
        std::size_t address = startAddress;

        for (const Instruction& instruction : program) {
            if (address + 1 >= memory.size()) {
                throw std::runtime_error("Program does not fit in memory.");
            }

            memory.writeWordBE(address, instruction.encode());
            address += 2;
        }

        pc = static_cast<Word>(startAddress);
        halted = false;
        cycles = 0;
        instructionsExecuted = 0;
    }

private:
    // ------------------------------------------------------------------------
    // Fetch
    // ------------------------------------------------------------------------

    Instruction fetch() {
        mar = static_cast<Byte>(pc & 0xFF);

        // The program is word-aligned in this educational model.
        const Word instructionWord = memory.readWordBE(pc);

        mdr = static_cast<Byte>(instructionWord & 0xFF);
        ir = instructionWord;

        pc = static_cast<Word>(pc + 2);

        return Instruction::decode(instructionWord);
    }

    // ------------------------------------------------------------------------
    // Execute
    // ------------------------------------------------------------------------

    void updateFlags(Byte result, bool carry = false) {
        zeroFlag = result == 0;
        carryFlag = carry;
    }

    void execute(const Instruction& instruction) {
        const Byte operand = instruction.operand;

        switch (instruction.opcode) {
            case Opcode::NOP:
                break;

            case Opcode::LOAD_IMM:
                acc = operand;
                updateFlags(acc);
                break;

            case Opcode::LOAD:
                acc = memory.readByte(operand);
                updateFlags(acc);
                break;

            case Opcode::STORE:
                memory.writeByte(operand, acc);
                break;

            case Opcode::ADD: {
                const ALUResult result =
                    alu.add(acc, memory.readByte(operand));

                acc = result.result;
                updateFlags(acc, result.flag);
                break;
            }

            case Opcode::SUB: {
                const ALUResult result =
                    alu.subtract(acc, memory.readByte(operand));

                acc = result.result;
                updateFlags(acc, result.flag);
                break;
            }

            case Opcode::AND_OP:
                acc = alu.bitAnd(
                    acc,
                    memory.readByte(operand)
                );
                updateFlags(acc);
                break;

            case Opcode::OR_OP:
                acc = alu.bitOr(
                    acc,
                    memory.readByte(operand)
                );
                updateFlags(acc);
                break;

            case Opcode::XOR_OP:
                acc = alu.bitXor(
                    acc,
                    memory.readByte(operand)
                );
                updateFlags(acc);
                break;

            case Opcode::SHL:
                acc = alu.shiftLeft(acc, operand);
                updateFlags(acc);
                break;

            case Opcode::SHR:
                acc = alu.shiftRight(acc, operand);
                updateFlags(acc);
                break;

            case Opcode::JMP:
                pc = operand;
                break;

            case Opcode::JZ:
                if (zeroFlag) {
                    pc = operand;
                }
                break;

            case Opcode::CMP: {
                const Byte memoryValue =
                    memory.readByte(operand);

                const Byte difference =
                    static_cast<Byte>(acc - memoryValue);

                zeroFlag = difference == 0;
                break;
            }

            case Opcode::IN:
                // A real CPU would interact through an I/O controller,
                // interrupt mechanism or memory-mapped I/O interface.
                // The case study keeps the operation deterministic.
                throw std::runtime_error(
                    "IN requires an attached input controller."
                );

            case Opcode::OUT:
                console.write(acc);
                break;

            case Opcode::HALT:
                halted = true;
                break;
        }
    }

public:
    void step(bool trace = false) {
        if (halted) {
            return;
        }

        const Word oldPC = pc;
        const Instruction instruction = fetch();

        if (trace) {
            std::cout
                << "cycle=" << std::setw(3)
                << (cycles + 1)
                << " PC=" << std::setw(3)
                << oldPC
                << " IR=0x"
                << std::hex
                << std::uppercase
                << std::setw(4)
                << std::setfill('0')
                << ir
                << std::dec
                << std::setfill(' ')
                << " "
                << instruction.toString()
                << '\n';
        }

        execute(instruction);

        ++cycles;
        ++instructionsExecuted;
    }

    void run(
        std::uint64_t maximumCycles = 1000,
        bool trace = false
    ) {
        while (!halted) {
            if (cycles >= maximumCycles) {
                throw std::runtime_error(
                    "CPU stopped at the maximum cycle limit."
                );
            }

            step(trace);
        }
    }

    void dumpRegisters() const {
        std::cout
            << "PC=" << pc
            << " IR=0x"
            << std::hex
            << std::uppercase
            << std::setw(4)
            << std::setfill('0')
            << ir
            << std::dec
            << std::setfill(' ')
            << " ACC=" << static_cast<int>(acc)
            << " MAR=" << static_cast<int>(mar)
            << " MDR=" << static_cast<int>(mdr)
            << " Z=" << zeroFlag
            << " C=" << carryFlag
            << '\n';
    }

    std::uint64_t cycleCount() const {
        return cycles;
    }

    std::uint64_t instructionCount() const {
        return instructionsExecuted;
    }
};


// ============================================================================
// 8. CONTROL UNIT MODEL
// ============================================================================

struct ControlSignals {
    bool registerWrite = false;
    bool memoryRead = false;
    bool memoryWrite = false;
    bool branch = false;
    std::string aluOperation = "NONE";
};

class ControlUnit {
public:
    ControlSignals decode(Opcode opcode) const {
        ControlSignals signals;

        switch (opcode) {
            case Opcode::LOAD:
                signals.registerWrite = true;
                signals.memoryRead = true;
                break;

            case Opcode::STORE:
                signals.memoryWrite = true;
                break;

            case Opcode::ADD:
                signals.registerWrite = true;
                signals.memoryRead = true;
                signals.aluOperation = "ADD";
                break;

            case Opcode::SUB:
                signals.registerWrite = true;
                signals.memoryRead = true;
                signals.aluOperation = "SUB";
                break;

            case Opcode::AND_OP:
                signals.registerWrite = true;
                signals.memoryRead = true;
                signals.aluOperation = "AND";
                break;

            case Opcode::OR_OP:
                signals.registerWrite = true;
                signals.memoryRead = true;
                signals.aluOperation = "OR";
                break;

            case Opcode::XOR_OP:
                signals.registerWrite = true;
                signals.memoryRead = true;
                signals.aluOperation = "XOR";
                break;

            case Opcode::JMP:
            case Opcode::JZ:
                signals.branch = true;
                break;

            default:
                break;
        }

        return signals;
    }
};


// ============================================================================
// 9. EMBEDDED SENSOR PROCESSOR CASE STUDY
// ============================================================================

class SensorProcessor {
private:
    SensorDevice sensor;
    ConsoleDevice console;
    CPU cpu;

public:
    SensorProcessor()
        : sensor({17, 25, 33, 41}),
          console(),
          cpu(512, console) {}

    Byte readSensorSample() {
        return sensor.read();
    }

    Byte processTwoSamples() {
        // The application reads two sensor samples.
        // In a real embedded system, this could be performed through
        // memory-mapped registers or a peripheral bus.
        const Byte first = readSensorSample();
        const Byte second = readSensorSample();

        // Reserve high memory locations for data.
        constexpr std::size_t FIRST_SAMPLE = 400;
        constexpr std::size_t SECOND_SAMPLE = 401;
        constexpr std::size_t RESULT = 402;

        cpu.getMemory().writeByte(FIRST_SAMPLE, first);
        cpu.getMemory().writeByte(SECOND_SAMPLE, second);

        /*
         * Machine program:
         *
         * LOAD 400
         * ADD 401
         * STORE 402
         * OUT
         * HALT
         *
         * This illustrates how a high-level application requirement
         * eventually becomes a sequence of ISA-level operations.
         */
        const std::vector<Instruction> program = {
            {Opcode::LOAD,  static_cast<Byte>(FIRST_SAMPLE)},
            {Opcode::ADD,   static_cast<Byte>(SECOND_SAMPLE)},
            {Opcode::STORE, static_cast<Byte>(RESULT)},
            {Opcode::OUT,   0},
            {Opcode::HALT,  0}
        };

        cpu.loadProgram(program);
        cpu.run(100, true);

        return cpu.getMemory().readByte(RESULT);
    }

    void printDiagnostics() const {
        std::cout << "\nCPU diagnostics:\n";
        cpu.dumpRegisters();
        std::cout
            << "Cycles: "
            << cpu.cycleCount()
            << "\nInstructions: "
            << cpu.instructionCount()
            << '\n';
    }
};


// ============================================================================
// 10. PERFORMANCE MODEL
// ============================================================================

double cpuExecutionTime(
    std::uint64_t instructionCount,
    double cpi,
    double clockFrequencyHz
) {
    if (cpi <= 0.0 || clockFrequencyHz <= 0.0) {
        throw std::invalid_argument(
            "CPI and clock frequency must be positive."
        );
    }

    return (
        static_cast<double>(instructionCount) *
        cpi /
        clockFrequencyHz
    );
}


// ============================================================================
// 11. PIPELINE MODEL
// ============================================================================

class PipelineModel {
private:
    std::vector<std::string> stages;

public:
    explicit PipelineModel(
        std::vector<std::string> pipelineStages
    )
        : stages(std::move(pipelineStages)) {

        if (stages.empty()) {
            throw std::invalid_argument(
                "A pipeline requires at least one stage."
            );
        }
    }

    void printIdealSchedule(std::size_t instructionCount) const {
        const std::size_t totalCycles =
            instructionCount + stages.size() - 1;

        std::cout << "\nIdeal pipeline schedule:\n";

        for (std::size_t instruction = 0;
             instruction < instructionCount;
             ++instruction) {

            std::cout
                << "I"
                << instruction + 1
                << " ";

            for (std::size_t cycle = 0;
                 cycle < totalCycles;
                 ++cycle) {

                const std::ptrdiff_t stageIndex =
                    static_cast<std::ptrdiff_t>(cycle) -
                    static_cast<std::ptrdiff_t>(instruction);

                if (stageIndex >= 0 &&
                    static_cast<std::size_t>(stageIndex) < stages.size()) {

                    std::cout
                        << std::setw(4)
                        << stages[stageIndex];
                } else {
                    std::cout << std::setw(4) << ".";
                }
            }

            std::cout << '\n';
        }
    }
};


// ============================================================================
// 12. VIRTUAL MEMORY TRANSLATION
// ============================================================================

class PageTable {
private:
    struct Entry {
        std::size_t physicalFrame;
        bool present;
    };

    std::unordered_map<std::size_t, Entry> entries;

public:
    void map(
        std::size_t virtualPage,
        std::size_t physicalFrame
    ) {
        entries[virtualPage] = {
            physicalFrame,
            true
        };
    }

    std::size_t translate(
        std::size_t virtualAddress,
        std::size_t pageSize
    ) const {
        if (pageSize == 0) {
            throw std::invalid_argument(
                "Page size must be non-zero."
            );
        }

        const std::size_t virtualPage =
            virtualAddress / pageSize;

        const std::size_t offset =
            virtualAddress % pageSize;

        const auto it = entries.find(virtualPage);

        if (it == entries.end() || !it->second.present) {
            throw std::runtime_error(
                "Page fault: virtual page is not mapped."
            );
        }

        return (
            it->second.physicalFrame * pageSize +
            offset
        );
    }
};


// ============================================================================
// 13. END-TO-END TESTS
// ============================================================================

void runTests() {
    std::cout << "\n" << std::string(76, '=') << '\n';
    std::cout << "SELF-TESTS\n";
    std::cout << std::string(76, '=') << '\n';

    {
        Memory memory(16);
        memory.writeByte(5, 123);

        if (memory.readByte(5) != 123) {
            throw std::runtime_error("Memory test failed.");
        }
    }

    {
        ALU alu;
        const ALUResult result = alu.add(200, 100);

        if (result.result != 44 || !result.flag) {
            throw std::runtime_error("ALU test failed.");
        }
    }

    {
        Instruction instruction{
            Opcode::LOAD_IMM,
            42
        };

        Instruction decoded =
            Instruction::decode(instruction.encode());

        if (decoded.opcode != Opcode::LOAD_IMM ||
            decoded.operand != 42) {
            throw std::runtime_error(
                "Instruction encoding test failed."
            );
        }
    }

    {
        ConsoleDevice console;
        CPU cpu(256, console);

        cpu.getMemory().writeByte(200, 10);
        cpu.getMemory().writeByte(201, 20);

        cpu.loadProgram({
            {Opcode::LOAD, 200},
            {Opcode::ADD, 201},
            {Opcode::STORE, 202},
            {Opcode::HALT, 0}
        });

        cpu.run();

        if (cpu.getMemory().readByte(202) != 30) {
            throw std::runtime_error(
                "CPU execution test failed."
            );
        }
    }

    {
        DirectMappedCache cache(2);

        if (cache.access(0)) {
            throw std::runtime_error(
                "First cache access should miss."
            );
        }

        if (!cache.access(0)) {
            throw std::runtime_error(
                "Second cache access should hit."
            );
        }
    }

    {
        PageTable table;

        table.map(0, 5);

        if (table.translate(3, 16) != 83) {
            throw std::runtime_error(
                "Virtual memory translation test failed."
            );
        }
    }

    std::cout << "All C++ self-tests passed.\n";
}


// ============================================================================
// 14. EDGE CASES
// ============================================================================

void demonstrateEdgeCases() {
    std::cout << "\n" << std::string(76, '=') << '\n';
    std::cout << "EDGE CASES AND FAILURE CONDITIONS\n";
    std::cout << std::string(76, '=') << '\n';

    try {
        Memory memory(4);
        memory.readByte(100);
    } catch (const std::exception& error) {
        std::cout << "Invalid memory access handled: "
                  << error.what()
                  << '\n';
    }

    try {
        Instruction::decode(0x9900);
    } catch (const std::exception& error) {
        std::cout << "Invalid opcode handled: "
                  << error.what()
                  << '\n';
    }

    try {
        PageTable table;
        table.translate(100, 16);
    } catch (const std::exception& error) {
        std::cout << "Page fault handled: "
                  << error.what()
                  << '\n';
    }
}


// ============================================================================
// 15. MAIN CASE STUDY
// ============================================================================

int main() {
    try {
        std::cout
            << "COMPUTER ARCHITECTURE INTRODUCTION\n"
            << "ISA, CPU, memory, I/O and organization case study\n";

        std::cout << "\n";
        std::cout
            << "Architecture describes the programmer-visible contract.\n"
            << "Organization describes how hardware implements that contract.\n";

        // --------------------------------------------------------------------
        // Demonstrate instruction encoding.
        // --------------------------------------------------------------------

        std::cout << "\nInstruction encoding example:\n";

        Instruction example{
            Opcode::ADD,
            200
        };

        const Word encoded = example.encode();

        std::cout
            << example.toString()
            << " -> 0x"
            << std::hex
            << std::uppercase
            << std::setw(4)
            << std::setfill('0')
            << encoded
            << std::dec
            << std::setfill(' ')
            << '\n';

        // --------------------------------------------------------------------
        // Control-unit demonstration.
        // --------------------------------------------------------------------

        std::cout << "\nControl-unit example:\n";

        ControlUnit controlUnit;
        ControlSignals signals =
            controlUnit.decode(Opcode::ADD);

        std::cout
            << "ADD -> registerWrite="
            << signals.registerWrite
            << ", memoryRead="
            << signals.memoryRead
            << ", ALU="
            << signals.aluOperation
            << '\n';

        // --------------------------------------------------------------------
        // Embedded sensor case study.
        // --------------------------------------------------------------------

        std::cout << "\nEmbedded sensor processor:\n";

        SensorProcessor processor;

        const Byte result =
            processor.processTwoSamples();

        processor.printDiagnostics();

        std::cout
            << "First calculation result = "
            << static_cast<int>(result)
            << '\n';

        // --------------------------------------------------------------------
        // Cache case study.
        // --------------------------------------------------------------------

        std::cout << "\nCache experiment:\n";

        DirectMappedCache cache(4);

        const std::vector<std::size_t> accesses = {
            0, 1, 2, 3, 0, 1, 4, 0, 8, 0
        };

        for (std::size_t address : accesses) {
            const bool hit = cache.access(address);

            std::cout
                << "Address "
                << std::setw(2)
                << address
                << " -> "
                << (hit ? "HIT" : "MISS")
                << '\n';
        }

        std::cout
            << "Hits: "
            << cache.hits()
            << "\nMisses: "
            << cache.misses()
            << "\nHit rate: "
            << std::fixed
            << std::setprecision(2)
            << cache.hitRate() * 100.0
            << "%\n";

        // --------------------------------------------------------------------
        // Performance model.
        // --------------------------------------------------------------------

        std::cout << "\nPerformance model:\n";

        const double executionTime =
            cpuExecutionTime(
                1'000'000,
                1.5,
                3'000'000'000.0
            );

        std::cout
            << "CPU time for one million instructions: "
            << executionTime
            << " seconds\n";

        // --------------------------------------------------------------------
        // Pipeline.
        // --------------------------------------------------------------------

        PipelineModel pipeline({
            "IF",
            "ID",
            "EX",
            "MEM",
            "WB"
        });

        pipeline.printIdealSchedule(5);

        // --------------------------------------------------------------------
        // Virtual memory.
        // --------------------------------------------------------------------

        std::cout << "\nVirtual memory translation:\n";

        PageTable pageTable;

        pageTable.map(0, 5);
        pageTable.map(1, 2);

        for (std::size_t virtualAddress : {0UL, 3UL, 16UL, 20UL}) {
            try {
                const std::size_t physicalAddress =
                    pageTable.translate(
                        virtualAddress,
                        16
                    );

                std::cout
                    << "Virtual "
                    << virtualAddress
                    << " -> Physical "
                    << physicalAddress
                    << '\n';
            } catch (const std::exception& error) {
                std::cout
                    << "Virtual "
                    << virtualAddress
                    << " -> "
                    << error.what()
                    << '\n';
            }
        }

        runTests();
        demonstrateEdgeCases();

        std::cout << "\nArchitectural design considerations:\n";
        std::cout
            << "- ISA compatibility determines the software-visible contract.\n"
            << "- Microarchitecture determines how efficiently that contract is implemented.\n"
            << "- Caches exploit locality but require hardware complexity and consume area.\n"
            << "- Pipelines increase throughput but introduce hazards.\n"
            << "- Memory protection is essential for safe multi-program execution.\n"
            << "- I/O requires interfaces between computation and external devices.\n"
            << "- Verification is critical because hardware defects can affect every program.\n";

        return 0;
    }
    catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << '\n';

        return 1;
    }
}
