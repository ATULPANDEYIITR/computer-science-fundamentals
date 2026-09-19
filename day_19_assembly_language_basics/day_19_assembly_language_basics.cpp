/*
 * Assembly Language Basics: MIPS-style registers, instructions, labels,
 * memory operations, arithmetic instructions, and a realistic case study.
 *
 * Compile:
 *   g++ -std=c++17 -O2 -Wall -Wextra -pedantic assembly_case_study.cpp -o assembly_case_study
 *
 * This program models a simplified MIPS-like machine and then uses that
 * machine to execute an array-processing workload.
 *
 * The implementation is educational. It demonstrates machine-level concepts
 * without attempting to reproduce every MARS/RARS instruction or system call.
 */

#include <array>
#include <cstdint>
#include <exception>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using Word = std::int32_t;
using UWord = std::uint32_t;
using Address = std::uint32_t;

constexpr std::size_t REGISTER_COUNT = 32;
constexpr Address DATA_BASE = 0x10010000;
constexpr Address STACK_BASE = 0x7FFFEFFC;
constexpr std::size_t WORD_SIZE = 4;

Word toSigned(UWord value) {
    return static_cast<Word>(value);
}

UWord toUnsigned(Word value) {
    return static_cast<UWord>(value);
}

/*
 * The register names below follow common MIPS conventions used in MARS/RARS.
 *
 * $zero : constant zero
 * $v0-$v1 : return values
 * $a0-$a3 : arguments
 * $t0-$t9 : temporary registers
 * $s0-$s7 : saved registers
 * $sp : stack pointer
 * $fp : frame pointer
 * $ra : return address
 */
class RegisterFile {
private:
    std::array<UWord, REGISTER_COUNT> registers{};

    static const std::unordered_map<std::string, int>& names() {
        static const std::unordered_map<std::string, int> table = {
            {"$zero", 0}, {"$at", 1},
            {"$v0", 2}, {"$v1", 3},
            {"$a0", 4}, {"$a1", 5}, {"$a2", 6}, {"$a3", 7},
            {"$t0", 8}, {"$t1", 9}, {"$t2", 10}, {"$t3", 11},
            {"$t4", 12}, {"$t5", 13}, {"$t6", 14}, {"$t7", 15},
            {"$s0", 16}, {"$s1", 17}, {"$s2", 18}, {"$s3", 19},
            {"$s4", 20}, {"$s5", 21}, {"$s6", 22}, {"$s7", 23},
            {"$t8", 24}, {"$t9", 25},
            {"$k0", 26}, {"$k1", 27},
            {"$gp", 28}, {"$sp", 29}, {"$fp", 30}, {"$ra", 31}
        };

        return table;
    }

public:
    int indexOf(const std::string& name) const {
        auto it = names().find(name);

        if (it == names().end()) {
            throw std::invalid_argument("Unknown register: " + name);
        }

        return it->second;
    }

    Word read(const std::string& name) const {
        return toSigned(registers.at(indexOf(name)));
    }

    void write(const std::string& name, Word value) {
        const int index = indexOf(name);

        // Hardware behavior: $zero cannot be changed.
        if (index != 0) {
            registers.at(index) = toUnsigned(value);
        }
    }

    void dump(const std::vector<std::string>& namesToPrint) const {
        std::cout << "Register state:\n";

        for (const auto& name : namesToPrint) {
            const Word value = read(name);

            std::cout
                << "  " << std::setw(6) << name
                << " = " << std::setw(12) << value
                << "  (0x"
                << std::hex << std::uppercase
                << std::setw(8) << std::setfill('0')
                << toUnsigned(value)
                << std::dec << std::setfill(' ')
                << ")\n";
        }
    }
};

/*
 * Sparse byte-addressable memory.
 *
 * A real machine has virtual memory, physical memory, caches, page tables,
 * protection bits, and other mechanisms. A map is sufficient for demonstrating
 * addresses, word alignment, load/store instructions, and arrays.
 */
class Memory {
private:
    std::map<Address, std::uint8_t> bytes;

    void requireAligned(Address address) const {
        if (address % WORD_SIZE != 0) {
            std::ostringstream message;
            message << "Unaligned word address: 0x"
                    << std::hex << address;
            throw std::invalid_argument(message.str());
        }
    }

public:
    void storeByte(Address address, std::uint8_t value) {
        bytes[address] = value;
    }

    std::uint8_t loadByte(Address address) const {
        auto it = bytes.find(address);
        return it == bytes.end() ? 0 : it->second;
    }

    void storeWord(Address address, Word value) {
        requireAligned(address);

        const UWord unsignedValue = toUnsigned(value);

        // Store four bytes in little-endian order.
        for (std::size_t offset = 0; offset < WORD_SIZE; ++offset) {
            storeByte(
                address + static_cast<Address>(offset),
                static_cast<std::uint8_t>(
                    (unsignedValue >> (offset * 8)) & 0xFFU
                )
            );
        }
    }

    Word loadWord(Address address) const {
        requireAligned(address);

        UWord value = 0;

        for (std::size_t offset = 0; offset < WORD_SIZE; ++offset) {
            value |= static_cast<UWord>(loadByte(
                address + static_cast<Address>(offset)
            )) << (offset * 8);
        }

        return toSigned(value);
    }
};

struct Instruction {
    std::string opcode;
    std::vector<std::string> operands;
    std::string source;

    Instruction(
        std::string operation,
        std::vector<std::string> arguments = {},
        std::string original = ""
    )
        : opcode(std::move(operation)),
          operands(std::move(arguments)),
          source(std::move(original)) {}

    std::string display() const {
        if (!source.empty()) {
            return source;
        }

        std::ostringstream result;
        result << opcode;

        for (const auto& operand : operands) {
            result << " " << operand;
        }

        return result.str();
    }
};

/*
 * Simplified MIPS CPU.
 *
 * Program counter:
 *   The PC identifies the next instruction.
 *
 * Memory operand:
 *   offset(base)
 *
 * Example:
 *   lw $t0, 8($sp)
 *
 * means:
 *   effective_address = $sp + 8
 *   $t0 = memory[effective_address]
 */
class MiniMIPS {
private:
    RegisterFile registers;
    Memory memory;
    std::vector<Instruction> program;
    std::unordered_map<std::string, std::size_t> labels;
    std::size_t pc = 0;
    bool trace = false;

    static int parseInteger(const std::string& text) {
        std::size_t consumed = 0;
        long long value = std::stoll(text, &consumed, 0);

        if (consumed != text.size()) {
            throw std::invalid_argument("Invalid integer: " + text);
        }

        if (
            value < std::numeric_limits<int>::min() ||
            value > std::numeric_limits<int>::max()
        ) {
            throw std::out_of_range("Integer outside supported range: " + text);
        }

        return static_cast<int>(value);
    }

    static std::pair<int, std::string> parseMemoryOperand(
        const std::string& operand
    ) {
        const std::size_t leftParenthesis = operand.find('(');
        const std::size_t rightParenthesis = operand.find(')');

        if (
            leftParenthesis == std::string::npos ||
            rightParenthesis == std::string::npos ||
            rightParenthesis != operand.size() - 1
        ) {
            throw std::invalid_argument(
                "Invalid memory operand: " + operand
            );
        }

        const std::string offsetText =
            operand.substr(0, leftParenthesis);

        const std::string baseRegister =
            operand.substr(
                leftParenthesis + 1,
                rightParenthesis - leftParenthesis - 1
            );

        return {parseInteger(offsetText), baseRegister};
    }

    Address effectiveAddress(const std::string& operand) const {
        const auto [offset, baseRegister] =
            parseMemoryOperand(operand);

        const Word base = registers.read(baseRegister);

        return static_cast<Address>(
            static_cast<std::int64_t>(base) + offset
        );
    }

    std::size_t labelAddress(const std::string& label) const {
        auto it = labels.find(label);

        if (it == labels.end()) {
            throw std::invalid_argument(
                "Unknown label: " + label
            );
        }

        return it->second;
    }

    Word checkedAdd(Word a, Word b) const {
        const std::int64_t result =
            static_cast<std::int64_t>(a) +
            static_cast<std::int64_t>(b);

        if (
            result < std::numeric_limits<Word>::min() ||
            result > std::numeric_limits<Word>::max()
        ) {
            throw std::overflow_error(
                "Signed addition overflow"
            );
        }

        return static_cast<Word>(result);
    }

    Word checkedSub(Word a, Word b) const {
        const std::int64_t result =
            static_cast<std::int64_t>(a) -
            static_cast<std::int64_t>(b);

        if (
            result < std::numeric_limits<Word>::min() ||
            result > std::numeric_limits<Word>::max()
        ) {
            throw std::overflow_error(
                "Signed subtraction overflow"
            );
        }

        return static_cast<Word>(result);
    }

public:
    void loadProgram(
        std::vector<Instruction> instructions,
        std::unordered_map<std::string, std::size_t> programLabels
    ) {
        program = std::move(instructions);
        labels = std::move(programLabels);
        pc = 0;
    }

    RegisterFile& getRegisters() {
        return registers;
    }

    const RegisterFile& getRegisters() const {
        return registers;
    }

    Memory& getMemory() {
        return memory;
    }

    void setTrace(bool enabled) {
        trace = enabled;
    }

    std::size_t step() {
        if (pc >= program.size()) {
            return pc;
        }

        const Instruction& instruction = program.at(pc);

        if (trace) {
            std::cout
                << "[PC=" << std::setw(3) << pc << "] "
                << instruction.display() << "\n";
        }

        const std::string& op = instruction.opcode;
        const auto& args = instruction.operands;

        // Sequential execution normally advances the PC by one instruction.
        std::size_t nextPC = pc + 1;

        if (op == "nop") {
            // No operation.
        }
        else if (op == "li") {
            registers.write(
                args.at(0),
                static_cast<Word>(parseInteger(args.at(1)))
            );
        }
        else if (op == "move") {
            registers.write(
                args.at(0),
                registers.read(args.at(1))
            );
        }
        else if (op == "add") {
            registers.write(
                args.at(0),
                checkedAdd(
                    registers.read(args.at(1)),
                    registers.read(args.at(2))
                )
            );
        }
        else if (op == "addu") {
            const UWord result =
                toUnsigned(registers.read(args.at(1))) +
                toUnsigned(registers.read(args.at(2)));

            registers.write(args.at(0), toSigned(result));
        }
        else if (op == "sub") {
            registers.write(
                args.at(0),
                checkedSub(
                    registers.read(args.at(1)),
                    registers.read(args.at(2))
                )
            );
        }
        else if (op == "mul") {
            const std::int64_t result =
                static_cast<std::int64_t>(
                    registers.read(args.at(1))
                ) *
                static_cast<std::int64_t>(
                    registers.read(args.at(2))
                );

            registers.write(
                args.at(0),
                static_cast<Word>(result)
            );
        }
        else if (op == "addi" || op == "addiu") {
            const int immediate =
                parseInteger(args.at(2));

            /*
             * Real MIPS immediate fields are 16 bits. We explicitly sign
             * extend the low 16 bits to demonstrate that mechanism.
             */
            const std::int16_t signedImmediate =
                static_cast<std::int16_t>(immediate & 0xFFFF);

            const Word source =
                registers.read(args.at(1));

            if (op == "addi") {
                registers.write(
                    args.at(0),
                    checkedAdd(
                        source,
                        static_cast<Word>(signedImmediate)
                    )
                );
            }
            else {
                const UWord result =
                    toUnsigned(source) +
                    static_cast<UWord>(
                        static_cast<std::int32_t>(signedImmediate)
                    );

                registers.write(
                    args.at(0),
                    toSigned(result)
                );
            }
        }
        else if (op == "and" || op == "or" || op == "xor") {
            const UWord left =
                toUnsigned(registers.read(args.at(1)));
            const UWord right =
                toUnsigned(registers.read(args.at(2)));

            UWord result = 0;

            if (op == "and") {
                result = left & right;
            }
            else if (op == "or") {
                result = left | right;
            }
            else {
                result = left ^ right;
            }

            registers.write(
                args.at(0),
                toSigned(result)
            );
        }
        else if (op == "sll" || op == "srl") {
            const UWord value =
                toUnsigned(registers.read(args.at(1)));

            const unsigned shift =
                static_cast<unsigned>(
                    parseInteger(args.at(2))
                ) & 31U;

            const UWord result =
                op == "sll"
                    ? static_cast<UWord>(value << shift)
                    : static_cast<UWord>(value >> shift);

            registers.write(
                args.at(0),
                toSigned(result)
            );
        }
        else if (op == "slt") {
            registers.write(
                args.at(0),
                registers.read(args.at(1)) <
                    registers.read(args.at(2))
                    ? 1
                    : 0
            );
        }
        else if (op == "lw") {
            const Address address =
                effectiveAddress(args.at(1));

            registers.write(
                args.at(0),
                memory.loadWord(address)
            );
        }
        else if (op == "sw") {
            const Address address =
                effectiveAddress(args.at(1));

            memory.storeWord(
                address,
                registers.read(args.at(0))
            );
        }
        else if (op == "beq" || op == "bne") {
            const bool equal =
                registers.read(args.at(0)) ==
                registers.read(args.at(1));

            const bool shouldBranch =
                op == "beq" ? equal : !equal;

            if (shouldBranch) {
                nextPC = labelAddress(args.at(2));
            }
        }
        else if (op == "j") {
            nextPC = labelAddress(args.at(0));
        }
        else if (op == "jal") {
            // Save the address of the next instruction.
            registers.write(
                "$ra",
                static_cast<Word>(nextPC)
            );

            nextPC = labelAddress(args.at(0));
        }
        else if (op == "jr") {
            nextPC = static_cast<std::size_t>(
                registers.read(args.at(0))
            );
        }
        else {
            throw std::invalid_argument(
                "Unsupported instruction: " + op
            );
        }

        pc = nextPC;
        return pc;
    }

    std::size_t run(std::size_t maximumSteps = 10000) {
        std::size_t steps = 0;

        while (pc < program.size()) {
            step();
            ++steps;

            if (steps >= maximumSteps) {
                throw std::runtime_error(
                    "Execution limit reached; possible infinite loop"
                );
            }
        }

        return steps;
    }
};

/*
 * Realistic case study:
 *
 * A monitoring subsystem receives a fixed-size block of signed sensor
 * measurements. The low-level routine must calculate:
 *
 *   1. total
 *   2. maximum
 *   3. minimum
 *   4. number of values above a threshold
 *
 * This resembles work that could be performed inside an embedded or
 * performance-sensitive system.
 *
 * The assembly-level representation demonstrates:
 *   - contiguous memory
 *   - word addressing
 *   - pointer arithmetic
 *   - counters
 *   - conditional branches
 *   - comparisons
 *   - register allocation
 *   - output registers
 */
class SensorAnalyticsCaseStudy {
private:
    MiniMIPS cpu;
    Address dataAddress = DATA_BASE;
    std::vector<Word> measurements;

public:
    explicit SensorAnalyticsCaseStudy(
        std::vector<Word> input
    )
        : measurements(std::move(input)) {

        if (measurements.empty()) {
            throw std::invalid_argument(
                "Sensor input cannot be empty"
            );
        }

        // Store the input array in simulated memory.
        for (std::size_t i = 0; i < measurements.size(); ++i) {
            cpu.getMemory().storeWord(
                dataAddress +
                    static_cast<Address>(i * WORD_SIZE),
                measurements.at(i)
            );
        }
    }

    void buildAndRun() {
        /*
         * Register allocation:
         *
         * $t0 = current array pointer
         * $t1 = remaining number of elements
         * $t2 = sum
         * $t3 = current measurement
         * $t4 = maximum
         * $t5 = minimum
         * $t6 = threshold
         * $t7 = count above threshold
         * $t8 = comparison result
         * $t9 = zero
         *
         * Results:
         *   $v0 = sum
         *   $v1 = maximum
         *   $s0 = minimum
         *   $s1 = threshold count
         */

        std::vector<Instruction> program = {
            Instruction("li", {"$t0", std::to_string(dataAddress)},
                        "li $t0, DATA_BASE"),
            Instruction("li", {"$t1", std::to_string(measurements.size())},
                        "li $t1, COUNT"),
            Instruction("li", {"$t2", "0"},
                        "li $t2, 0"),
            Instruction("lw", {"$t4", "0($t0)"},
                        "lw $t4, 0($t0)"),
            Instruction("move", {"$t5", "$t4"},
                        "move $t5, $t4"),
            Instruction("li", {"$t6", "20"},
                        "li $t6, 20"),
            Instruction("li", {"$t7", "0"},
                        "li $t7, 0"),
            Instruction("li", {"$t9", "0"},
                        "li $t9, 0"),

            // loop:
            Instruction("lw", {"$t3", "0($t0)"},
                        "lw $t3, 0($t0)"),
            Instruction("add", {"$t2", "$t2", "$t3"},
                        "add $t2, $t2, $t3"),

            // maximum = max(maximum, current)
            Instruction("slt", {"$t8", "$t4", "$t3"},
                        "slt $t8, $t4, $t3"),
            Instruction("beq", {"$t8", "$t9", "check_min"},
                        "beq $t8, $t9, check_min"),
            Instruction("move", {"$t4", "$t3"},
                        "move $t4, $t3"),

            // minimum = min(minimum, current)
            // check_min:
            Instruction("slt", {"$t8", "$t3", "$t5"},
                        "slt $t8, $t3, $t5"),
            Instruction("beq", {"$t8", "$t9", "check_threshold"},
                        "beq $t8, $t9, check_threshold"),
            Instruction("move", {"$t5", "$t3"},
                        "move $t5, $t3"),

            // if current > threshold, count++
            // check_threshold:
            Instruction("slt", {"$t8", "$t6", "$t3"},
                        "slt $t8, $t6, $t3"),
            Instruction("beq", {"$t8", "$t9", "advance"},
                        "beq $t8, $t9, advance"),
            Instruction("addi", {"$t7", "$t7", "1"},
                        "addi $t7, $t7, 1"),

            // advance:
            Instruction("addi", {"$t0", "$t0", "4"},
                        "addi $t0, $t0, 4"),
            Instruction("addi", {"$t1", "$t1", "-1"},
                        "addi $t1, $t1, -1"),
            Instruction("bne", {"$t1", "$t9", "loop"},
                        "bne $t1, $t9, loop"),

            // Export results.
            Instruction("move", {"$v0", "$t2"},
                        "move $v0, $t2"),
            Instruction("move", {"$v1", "$t4"},
                        "move $v1, $t4"),
            Instruction("move", {"$s0", "$t5"},
                        "move $s0, $t5"),
            Instruction("move", {"$s1", "$t7"},
                        "move $s1, $t7")
        };

        /*
         * The labels identify instruction addresses. They are not data.
         * A label is a symbolic name resolved by an assembler into an address.
         */
        const std::unordered_map<std::string, std::size_t> labels = {
            {"loop", 8},
            {"check_min", 13},
            {"check_threshold", 16},
            {"advance", 19}
        };

        cpu.loadProgram(std::move(program), labels);

        const std::size_t executed =
            cpu.run();

        std::cout << "Instructions executed: "
                  << executed << "\n";

        const Word sum = cpu.getRegisters().read("$v0");
        const Word maximum = cpu.getRegisters().read("$v1");
        const Word minimum = cpu.getRegisters().read("$s0");
        const Word aboveThreshold =
            cpu.getRegisters().read("$s1");

        std::cout << "Sensor measurements:\n";

        for (Word value : measurements) {
            std::cout << "  " << value << "\n";
        }

        std::cout << "Calculated sum: " << sum << "\n";
        std::cout << "Calculated maximum: " << maximum << "\n";
        std::cout << "Calculated minimum: " << minimum << "\n";
        std::cout
            << "Values above threshold 20: "
            << aboveThreshold << "\n";

        validateResults(
            sum,
            maximum,
            minimum,
            aboveThreshold
        );
    }

    void validateResults(
        Word sum,
        Word maximum,
        Word minimum,
        Word aboveThreshold
    ) const {
        Word expectedSum = 0;
        Word expectedMaximum = measurements.front();
        Word expectedMinimum = measurements.front();
        Word expectedAboveThreshold = 0;

        for (Word value : measurements) {
            expectedSum += value;

            if (value > expectedMaximum) {
                expectedMaximum = value;
            }

            if (value < expectedMinimum) {
                expectedMinimum = value;
            }

            if (value > 20) {
                ++expectedAboveThreshold;
            }
        }

        if (
            sum != expectedSum ||
            maximum != expectedMaximum ||
            minimum != expectedMinimum ||
            aboveThreshold != expectedAboveThreshold
        ) {
            throw std::runtime_error(
                "Assembly case-study validation failed"
            );
        }

        std::cout << "Case-study validation: PASSED\n";
    }

    MiniMIPS& machine() {
        return cpu;
    }
};

void testRegisterFile() {
    RegisterFile registers;

    registers.write("$t0", -123);
    if (registers.read("$t0") != -123) {
        throw std::runtime_error(
            "Register read/write test failed"
        );
    }

    registers.write("$zero", 999);

    if (registers.read("$zero") != 0) {
        throw std::runtime_error(
            "$zero invariant failed"
        );
    }
}

void testMemory() {
    Memory memory;

    memory.storeWord(0x2000, -123456);

    if (memory.loadWord(0x2000) != -123456) {
        throw std::runtime_error(
            "Memory round-trip test failed"
        );
    }

    bool caught = false;

    try {
        memory.storeWord(0x2001, 10);
    }
    catch (const std::invalid_argument&) {
        caught = true;
    }

    if (!caught) {
        throw std::runtime_error(
            "Unaligned memory test failed"
        );
    }
}

void testArithmetic() {
    MiniMIPS cpu;

    cpu.loadProgram({
        Instruction("li", {"$t0", "50"}),
        Instruction("li", {"$t1", "8"}),
        Instruction("add", {"$t2", "$t0", "$t1"}),
        Instruction("sub", {"$t3", "$t0", "$t1"}),
        Instruction("mul", {"$t4", "$t2", "$t3"})
    }, {});

    cpu.run();

    if (cpu.getRegisters().read("$t2") != 58) {
        throw std::runtime_error(
            "Addition test failed"
        );
    }

    if (cpu.getRegisters().read("$t3") != 42) {
        throw std::runtime_error(
            "Subtraction test failed"
        );
    }

    if (cpu.getRegisters().read("$t4") != 2436) {
        throw std::runtime_error(
            "Multiplication test failed"
        );
    }
}

void testBranching() {
    MiniMIPS cpu;

    /*
     * If t0 == t1, branch to equal_case and place 1 in t2.
     * Otherwise place 0 in t2.
     */
    cpu.loadProgram({
        Instruction("li", {"$t0", "5"}),
        Instruction("li", {"$t1", "5"}),
        Instruction("beq", {"$t0", "$t1", "equal_case"}),
        Instruction("li", {"$t2", "0"}),
        Instruction("j", {"end"}),
        Instruction("li", {"$t2", "1"}),
        Instruction("nop")
    }, {
        {"equal_case", 5},
        {"end", 6}
    });

    cpu.run();

    if (cpu.getRegisters().read("$t2") != 1) {
        throw std::runtime_error(
            "Branch test failed"
        );
    }
}

void testOverflow() {
    MiniMIPS cpu;

    cpu.loadProgram({
        Instruction("li", {"$t0", "2147483647"}),
        Instruction("li", {"$t1", "1"}),
        Instruction("add", {"$t2", "$t0", "$t1"})
    }, {});

    bool caught = false;

    try {
        cpu.run();
    }
    catch (const std::overflow_error&) {
        caught = true;
    }

    if (!caught) {
        throw std::runtime_error(
            "Signed overflow test failed"
        );
    }
}

void runTests() {
    std::cout << "=== Self-tests ===\n";

    testRegisterFile();
    testMemory();
    testArithmetic();
    testBranching();
    testOverflow();

    std::cout << "All tests passed.\n\n";
}

int main() {
    try {
        std::cout
            << "MIPS Assembly Language Basics - C++ Case Study\n\n";

        runTests();

        std::cout
            << "=== Industry-style low-level case study ===\n";

        /*
         * Mixed positive and negative measurements force the algorithm to
         * handle signed comparisons rather than assuming every value is
         * positive.
         */
        SensorAnalyticsCaseStudy caseStudy({
            12, 27, -5, 31, 18, 42, 7, 24
        });

        caseStudy.buildAndRun();

        std::cout << "\n=== Register snapshot ===\n";

        caseStudy.machine().getRegisters().dump({
            "$v0", "$v1", "$s0", "$s1",
            "$t0", "$t1", "$sp", "$ra"
        });

        std::cout
            << "\nArchitectural observations:\n"
            << "  - A label is a symbolic instruction address.\n"
            << "  - An array is represented by consecutive memory words.\n"
            << "  - Pointer movement for 32-bit integers advances by four bytes.\n"
            << "  - Branch instructions implement conditional control flow.\n"
            << "  - Registers hold active values while memory holds persistent data.\n"
            << "  - The program counter determines which instruction executes next.\n"
            << "  - MARS/RARS provide visual debugging of these same fundamental ideas.\n";
    }
    catch (const std::exception& error) {
        std::cerr
            << "Fatal error: "
            << error.what()
            << "\n";

        return 1;
    }

    return 0;
}
