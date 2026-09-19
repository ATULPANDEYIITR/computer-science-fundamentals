"""
Assembly Language Basics: Registers, Instructions, Labels, Memory Operations,
and Arithmetic Instructions

A self-contained educational Python implementation that models a useful subset
of MIPS-style assembly concepts used by MARS and RARS.

The simulator is intentionally small enough to study, but complete enough to
demonstrate:
- Registers and register conventions
- Immediate and register operands
- Labels
- Program counters
- Arithmetic and logical instructions
- Memory operations
- Branches and jumps
- Stack operations
- Procedure calls
- Signed 32-bit arithmetic
- Overflow behavior
- Address calculation
- Debugging and tracing
- A small realistic array-processing program

MARS and RARS are educational MIPS simulators. Their exact instruction sets,
pseudo-instruction behavior, system-call interfaces, and configuration options
can differ by version. This file focuses on core concepts rather than attempting
to reproduce every simulator feature.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Fundamental machine constants
# ---------------------------------------------------------------------------

WORD_SIZE = 4
REGISTER_COUNT = 32
MEMORY_BASE = 0x10010000
STACK_BASE = 0x7FFFEFFC
MASK_32 = 0xFFFFFFFF
SIGN_BIT = 0x80000000


def u32(value: int) -> int:
    """Convert an integer to an unsigned 32-bit representation."""
    return value & MASK_32


def s32(value: int) -> int:
    """Interpret the low 32 bits as a signed two's-complement integer."""
    value &= MASK_32
    return value - (1 << 32) if value & SIGN_BIT else value


def add_signed(a: int, b: int) -> int:
    """
    Model MIPS 'add'.

    The real MIPS add instruction traps on signed overflow. This educational
    helper raises OverflowError so the behavior is visible rather than silently
    wrapping.
    """
    result = s32(a) + s32(b)
    if result < -(1 << 31) or result > (1 << 31) - 1:
        raise OverflowError(f"signed overflow: {a} + {b}")
    return result


def add_unsigned(a: int, b: int) -> int:
    """Model 32-bit wrapping arithmetic such as addu."""
    return s32(u32(a) + u32(b))


def sign_extend_16(value: int) -> int:
    """Convert a 16-bit immediate to a signed Python integer."""
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


# ---------------------------------------------------------------------------
# Register model
# ---------------------------------------------------------------------------

REGISTER_NAMES = {
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
    "$ra": 31,
}

REGISTER_NAMES.update({f"$r{i}": i for i in range(REGISTER_COUNT)})


def register_number(name: str) -> int:
    """Return the numeric register index for names such as $t0 or $sp."""
    normalized = name.strip().lower()
    if normalized not in REGISTER_NAMES:
        raise ValueError(f"unknown register: {name}")
    return REGISTER_NAMES[normalized]


class RegisterFile:
    """A model of the 32 general-purpose MIPS registers."""

    def __init__(self) -> None:
        self.values = [0] * REGISTER_COUNT

    def read(self, name: str) -> int:
        return s32(self.values[register_number(name)])

    def write(self, name: str, value: int) -> None:
        index = register_number(name)

        # $zero is hard-wired to zero in MIPS.
        if index != 0:
            self.values[index] = u32(value)

    def dump(self, names: Optional[List[str]] = None) -> None:
        if names is None:
            names = ["$zero", "$v0", "$a0", "$t0", "$t1", "$t2",
                     "$s0", "$s1", "$sp", "$ra"]

        print("Register state:")
        for name in names:
            print(f"  {name:>6} = {self.read(name):12d}  "
                  f"(0x{u32(self.read(name)):08X})")


# ---------------------------------------------------------------------------
# Memory model
# ---------------------------------------------------------------------------

class Memory:
    """
    Sparse byte-addressable memory.

    Real processors use physical/virtual memory systems that are much more
    complicated. A sparse dictionary is enough to demonstrate addresses,
    offsets, alignment, and load/store operations.
    """

    def __init__(self) -> None:
        self.bytes: Dict[int, int] = {}

    def store_byte(self, address: int, value: int) -> None:
        self.bytes[address] = value & 0xFF

    def load_byte(self, address: int) -> int:
        return self.bytes.get(address, 0)

    def store_word(self, address: int, value: int) -> None:
        if address % WORD_SIZE != 0:
            raise ValueError(f"unaligned word address: 0x{address:08X}")

        value = u32(value)

        # Little-endian representation is used here for demonstration.
        for offset in range(WORD_SIZE):
            self.store_byte(address + offset, value >> (offset * 8))

    def load_word(self, address: int) -> int:
        if address % WORD_SIZE != 0:
            raise ValueError(f"unaligned word address: 0x{address:08X}")

        value = 0
        for offset in range(WORD_SIZE):
            value |= self.load_byte(address + offset) << (offset * 8)

        return s32(value)

    def dump_words(self, start: int, count: int) -> None:
        print("Memory:")
        for i in range(count):
            address = start + i * WORD_SIZE
            print(f"  0x{address:08X}: {self.load_word(address):12d}")


# ---------------------------------------------------------------------------
# A tiny instruction representation
# ---------------------------------------------------------------------------

@dataclass
class Instruction:
    opcode: str
    operands: Tuple[str, ...] = ()
    source: str = ""

    def __str__(self) -> str:
        return self.source or " ".join((self.opcode, *self.operands))


# ---------------------------------------------------------------------------
# Mini MIPS machine
# ---------------------------------------------------------------------------

class MiniMIPS:
    """
    A compact interpreter for selected MIPS-like instructions.

    Supported instructions:
        li      rd, immediate
        move    rd, rs
        add     rd, rs, rt
        addu    rd, rs, rt
        addi    rt, rs, immediate
        addiu   rt, rs, immediate
        sub     rd, rs, rt
        mul     rd, rs, rt
        and     rd, rs, rt
        or      rd, rs, rt
        xor     rd, rs, rt
        sll     rd, rt, shift
        srl     rd, rt, shift
        slt     rd, rs, rt
        lw      rt, offset(base)
        sw      rt, offset(base)
        beq     rs, rt, label
        bne     rs, rt, label
        j       label
        jal     label
        jr      rs
        nop

    The syntax is intentionally simplified and does not parse every feature
    supported by MARS/RARS.
    """

    def __init__(self, trace: bool = False) -> None:
        self.registers = RegisterFile()
        self.memory = Memory()
        self.program: List[Instruction] = []
        self.labels: Dict[str, int] = {}
        self.pc = 0
        self.trace = trace
        self.running = False

    def load_program(self, instructions: List[Instruction],
                     labels: Dict[str, int]) -> None:
        self.program = instructions
        self.labels = labels
        self.pc = 0

    def address_from_operand(self, operand: str) -> int:
        """
        Resolve syntax such as 8($sp).

        In assembly, the effective address is normally:
            base register + signed immediate offset
        """
        operand = operand.strip()

        if "(" not in operand or not operand.endswith(")"):
            raise ValueError(f"invalid memory operand: {operand}")

        offset_text, register_text = operand[:-1].split("(", 1)
        offset = int(offset_text, 0)
        base = self.registers.read(register_text)

        return u32(base + offset)

    def step(self) -> None:
        if not (0 <= self.pc < len(self.program)):
            self.running = False
            return

        instruction = self.program[self.pc]
        opcode = instruction.opcode.lower()
        operands = instruction.operands

        if self.trace:
            print(f"[PC={self.pc:03d}] {instruction}")

        # Increment first. Branches and jumps overwrite PC when necessary.
        next_pc = self.pc + 1

        try:
            if opcode == "nop":
                pass

            elif opcode == "li":
                rd, immediate = operands
                self.registers.write(rd, int(immediate, 0))

            elif opcode == "move":
                rd, rs = operands
                self.registers.write(rd, self.registers.read(rs))

            elif opcode in {"add", "addu", "sub", "mul"}:
                rd, rs, rt = operands
                a = self.registers.read(rs)
                b = self.registers.read(rt)

                if opcode == "add":
                    result = add_signed(a, b)
                elif opcode == "addu":
                    result = add_unsigned(a, b)
                elif opcode == "sub":
                    result = a - b
                    if result < -(1 << 31) or result > (1 << 31) - 1:
                        raise OverflowError(f"signed overflow: {a} - {b}")
                else:
                    result = u32(a * b)

                self.registers.write(rd, result)

            elif opcode in {"addi", "addiu"}:
                rt, rs, immediate = operands
                immediate_value = sign_extend_16(int(immediate, 0))
                source = self.registers.read(rs)

                if opcode == "addi":
                    result = add_signed(source, immediate_value)
                else:
                    result = add_unsigned(source, immediate_value)

                self.registers.write(rt, result)

            elif opcode in {"and", "or", "xor"}:
                rd, rs, rt = operands
                a = u32(self.registers.read(rs))
                b = u32(self.registers.read(rt))

                if opcode == "and":
                    result = a & b
                elif opcode == "or":
                    result = a | b
                else:
                    result = a ^ b

                self.registers.write(rd, result)

            elif opcode in {"sll", "srl"}:
                rd, rt, shift = operands
                value = u32(self.registers.read(rt))
                amount = int(shift, 0) & 0x1F

                if opcode == "sll":
                    result = u32(value << amount)
                else:
                    result = value >> amount

                self.registers.write(rd, result)

            elif opcode == "slt":
                rd, rs, rt = operands
                self.registers.write(
                    rd,
                    1 if self.registers.read(rs) < self.registers.read(rt)
                    else 0,
                )

            elif opcode == "lw":
                rt, address_operand = operands
                address = self.address_from_operand(address_operand)
                self.registers.write(rt, self.memory.load_word(address))

            elif opcode == "sw":
                rt, address_operand = operands
                address = self.address_from_operand(address_operand)
                self.memory.store_word(
                    address,
                    self.registers.read(rt),
                )

            elif opcode in {"beq", "bne"}:
                rs, rt, label = operands
                equal = self.registers.read(rs) == self.registers.read(rt)

                should_branch = equal if opcode == "beq" else not equal

                if should_branch:
                    if label not in self.labels:
                        raise ValueError(f"unknown label: {label}")
                    next_pc = self.labels[label]

            elif opcode in {"j", "jal"}:
                (label,) = operands

                if label not in self.labels:
                    raise ValueError(f"unknown label: {label}")

                if opcode == "jal":
                    self.registers.write("$ra", next_pc)

                next_pc = self.labels[label]

            elif opcode == "jr":
                (rs,) = operands
                next_pc = self.registers.read(rs)

            else:
                raise ValueError(f"unsupported instruction: {opcode}")

        except Exception:
            self.running = False
            raise

        self.pc = next_pc

    def run(self, max_steps: int = 10_000) -> int:
        self.running = True
        steps = 0

        while self.running and 0 <= self.pc < len(self.program):
            self.step()
            steps += 1

            if steps >= max_steps:
                raise RuntimeError(
                    "execution limit reached; possible infinite loop"
                )

        self.running = False
        return steps


def parse_memory_operand(text: str) -> str:
    """Keep memory operands together when constructing instructions."""
    return text.replace(" ", "")


# ---------------------------------------------------------------------------
# Example 1: registers and arithmetic
# ---------------------------------------------------------------------------

def example_register_arithmetic() -> None:
    print("\n=== Example 1: Registers and arithmetic ===")

    cpu = MiniMIPS(trace=False)

    program = [
        Instruction("li", ("$t0", "25"), "li $t0, 25"),
        Instruction("li", ("$t1", "17"), "li $t1, 17"),
        Instruction("add", ("$t2", "$t0", "$t1"), "add $t2, $t0, $t1"),
        Instruction("sub", ("$t3", "$t0", "$t1"), "sub $t3, $t0, $t1"),
        Instruction("mul", ("$t4", "$t2", "$t3"), "mul $t4, $t2, $t3"),
    ]

    cpu.load_program(program, {})
    cpu.run()

    cpu.registers.dump(["$t0", "$t1", "$t2", "$t3", "$t4"])

    # $zero must remain zero even if a program attempts to write it.
    cpu.registers.write("$zero", 999)
    assert cpu.registers.read("$zero") == 0


# ---------------------------------------------------------------------------
# Example 2: memory and arrays
# ---------------------------------------------------------------------------

def example_memory_operations() -> None:
    print("\n=== Example 2: Memory operations ===")

    cpu = MiniMIPS()

    array_address = MEMORY_BASE

    # Simulate:
    #   int numbers[] = {10, 20, 30, 40};
    # Every integer occupies four bytes.
    values = [10, 20, 30, 40]

    for index, value in enumerate(values):
        cpu.memory.store_word(
            array_address + index * WORD_SIZE,
            value,
        )

    program = [
        # t0 = address of numbers[0]
        Instruction("li", ("$t0", str(array_address)),
                    f"li $t0, {array_address}"),

        # Load numbers[2].
        Instruction("lw", ("$t1", "8($t0)"), "lw $t1, 8($t0)"),

        # Add five and store into numbers[2].
        Instruction("addi", ("$t1", "$t1", "5"),
                    "addi $t1, $t1, 5"),
        Instruction("sw", ("$t1", "8($t0)"),
                    "sw $t1, 8($t0)"),
    ]

    cpu.load_program(program, {})
    cpu.run()

    cpu.memory.dump_words(array_address, len(values))

    assert cpu.memory.load_word(array_address + 8) == 35


# ---------------------------------------------------------------------------
# Example 3: labels and loops
# ---------------------------------------------------------------------------

def example_loop_with_labels() -> None:
    print("\n=== Example 3: Labels and loops ===")

    cpu = MiniMIPS(trace=False)

    # Calculate:
    #
    #   sum = 1 + 2 + 3 + 4 + 5
    #
    # Assembly structure:
    #
    #   li   $t0, 1       # current value
    #   li   $t1, 0       # sum
    #   li   $t2, 5       # limit
    #
    # loop:
    #   add  $t1, $t1, $t0
    #   addi $t0, $t0, 1
    #   bne  $t0, $t3, loop
    #
    # Here we deliberately use a compare register to show that branches
    # operate on registers rather than high-level boolean expressions.

    program = [
        Instruction("li", ("$t0", "1"), "li $t0, 1"),
        Instruction("li", ("$t1", "0"), "li $t1, 0"),
        Instruction("li", ("$t2", "5"), "li $t2, 5"),
        Instruction("addi", ("$t3", "$t2", "1"),
                    "addi $t3, $t2, 1"),
        Instruction("add", ("$t1", "$t1", "$t0"),
                    "add $t1, $t1, $t0"),
        Instruction("addi", ("$t0", "$t0", "1"),
                    "addi $t0, $t0, 1"),
        Instruction("bne", ("$t0", "$t3", "loop"),
                    "bne $t0, $t3, loop"),
    ]

    labels = {"loop": 4}

    cpu.load_program(program, labels)
    cpu.run()

    print("Sum:", cpu.registers.read("$t1"))
    assert cpu.registers.read("$t1") == 15


# ---------------------------------------------------------------------------
# Example 4: procedure calls and the stack
# ---------------------------------------------------------------------------

def example_procedure_call() -> None:
    print("\n=== Example 4: Procedure call and stack ===")

    cpu = MiniMIPS(trace=False)

    # Model:
    #
    #   int square_plus_one(int x) {
    #       return x * x + 1;
    #   }
    #
    # Argument convention:
    #   $a0 = argument
    # Return convention:
    #   $v0 = result
    #
    # jal stores the return address in $ra.
    #
    # The stack is demonstrated by saving $ra before a nested operation.
    stack_pointer = STACK_BASE

    program = [
        Instruction("li", ("$sp", str(stack_pointer)),
                    f"li $sp, {stack_pointer}"),
        Instruction("li", ("$a0", "7"), "li $a0, 7"),
        Instruction("jal", ("square_plus_one",),
                    "jal square_plus_one"),
        Instruction("j", ("program_end",), "j program_end"),

        # Function begins here.
        # Save return address.
        Instruction("sw", ("$ra", "0($sp)"),
                    "sw $ra, 0($sp)"),
        Instruction("mul", ("$t0", "$a0", "$a0"),
                    "mul $t0, $a0, $a0"),
        Instruction("addi", ("$v0", "$t0", "1"),
                    "addi $v0, $t0, 1"),
        Instruction("lw", ("$ra", "0($sp)"),
                    "lw $ra, 0($sp)"),
        Instruction("jr", ("$ra",), "jr $ra"),

        Instruction("nop", (), "nop"),
    ]

    labels = {
        "square_plus_one": 4,
        "program_end": 9,
    }

    cpu.load_program(program, labels)
    cpu.run()

    print("Function result:", cpu.registers.read("$v0"))
    assert cpu.registers.read("$v0") == 50


# ---------------------------------------------------------------------------
# Example 5: overflow and unsigned behavior
# ---------------------------------------------------------------------------

def example_overflow() -> None:
    print("\n=== Example 5: Signed overflow versus wrapping ===")

    cpu = MiniMIPS()

    maximum = (1 << 31) - 1
    cpu.registers.write("$t0", maximum)
    cpu.registers.write("$t1", 1)

    try:
        result = add_signed(
            cpu.registers.read("$t0"),
            cpu.registers.read("$t1"),
        )
        print("Unexpected signed result:", result)
    except OverflowError as error:
        print("Signed add detected overflow:", error)

    wrapped = add_unsigned(
        cpu.registers.read("$t0"),
        cpu.registers.read("$t1"),
    )
    print("32-bit wrapping result:", wrapped)
    assert wrapped == -(1 << 31)


# ---------------------------------------------------------------------------
# Example 6: bit operations and shifts
# ---------------------------------------------------------------------------

def example_bit_operations() -> None:
    print("\n=== Example 6: Bitwise operations ===")

    cpu = MiniMIPS()

    program = [
        Instruction("li", ("$t0", "0x0F0F"), "li $t0, 0x0F0F"),
        Instruction("li", ("$t1", "0x00FF"), "li $t1, 0x00FF"),
        Instruction("and", ("$t2", "$t0", "$t1"),
                    "and $t2, $t0, $t1"),
        Instruction("or", ("$t3", "$t0", "$t1"),
                    "or $t3, $t0, $t1"),
        Instruction("xor", ("$t4", "$t0", "$t1"),
                    "xor $t4, $t0, $t1"),
        Instruction("sll", ("$t5", "$t1", "4"),
                    "sll $t5, $t1, 4"),
        Instruction("srl", ("$t6", "$t5", "4"),
                    "srl $t6, $t5, 4"),
    ]

    cpu.load_program(program, {})
    cpu.run()

    cpu.registers.dump(["$t0", "$t1", "$t2", "$t3", "$t4", "$t5", "$t6"])


# ---------------------------------------------------------------------------
# Example 7: realistic array-processing case study
# ---------------------------------------------------------------------------

def example_array_statistics() -> None:
    print("\n=== Example 7: Array-processing case study ===")

    cpu = MiniMIPS(trace=False)

    # The program calculates the sum and maximum of an integer array.
    #
    # Equivalent high-level logic:
    #
    #   sum = 0
    #   max = numbers[0]
    #   for i in range(length):
    #       value = numbers[i]
    #       sum += value
    #       if value > max:
    #           max = value
    #
    # Registers:
    #   $t0 = array pointer
    #   $t1 = remaining count
    #   $t2 = sum
    #   $t3 = current value
    #   $t4 = maximum
    #   $t5 = zero
    #
    # This demonstrates that a CPU does not have a built-in "array" object.
    # Arrays are contiguous memory and indexing is address arithmetic.

    values = [12, -4, 31, 18, 7, 25]
    base = MEMORY_BASE

    for index, value in enumerate(values):
        cpu.memory.store_word(base + index * WORD_SIZE, value)

    program = [
        Instruction("li", ("$t0", str(base)), f"li $t0, {base}"),
        Instruction("li", ("$t1", str(len(values))),
                    f"li $t1, {len(values)}"),
        Instruction("li", ("$t2", "0"), "li $t2, 0"),
        Instruction("lw", ("$t4", "0($t0)"), "lw $t4, 0($t0)"),
        Instruction("li", ("$t5", "0"), "li $t5, 0"),

        # Loop starts here.
        Instruction("lw", ("$t3", "0($t0)"), "lw $t3, 0($t0)"),
        Instruction("add", ("$t2", "$t2", "$t3"),
                    "add $t2, $t2, $t3"),

        # If current < maximum, skip replacement.
        Instruction("slt", ("$t6", "$t3", "$t4"),
                    "slt $t6, $t3, $t4"),
        Instruction("bne", ("$t6", "$t5", "skip_max"),
                    "bne $t6, $t5, skip_max"),

        Instruction("move", ("$t4", "$t3"), "move $t4, $t3"),

        # Move to next element.
        Instruction("addi", ("$t0", "$t0", "4"),
                    "addi $t0, $t0, 4"),
        Instruction("addi", ("$t1", "$t1", "-1"),
                    "addi $t1, $t1, -1"),
        Instruction("bne", ("$t1", "$t5", "loop"),
                    "bne $t1, $t5, loop"),

        Instruction("j", ("end",), "j end"),

        # skip_max:
        Instruction("addi", ("$t0", "$t0", "4"),
                    "addi $t0, $t0, 4"),
        Instruction("addi", ("$t1", "$t1", "-1"),
                    "addi $t1, $t1, -1"),
        Instruction("bne", ("$t1", "$t5", "loop"),
                    "bne $t1, $t5, loop"),

        Instruction("nop", (), "nop"),
    ]

    labels = {
        "loop": 5,
        "skip_max": 13,
        "end": 16,
    }

    # The branch layout above intentionally shows the mechanics, but for
    # robust execution we use a corrected compact program below.
    program = [
        Instruction("li", ("$t0", str(base)), f"li $t0, {base}"),
        Instruction("li", ("$t1", str(len(values))),
                    f"li $t1, {len(values)}"),
        Instruction("li", ("$t2", "0"), "li $t2, 0"),
        Instruction("lw", ("$t4", "0($t0)"), "lw $t4, 0($t0)"),
        Instruction("li", ("$t5", "0"), "li $t5, 0"),

        Instruction("lw", ("$t3", "0($t0)"), "lw $t3, 0($t0)"),
        Instruction("add", ("$t2", "$t2", "$t3"),
                    "add $t2, $t2, $t3"),
        Instruction("slt", ("$t6", "$t4", "$t3"),
                    "slt $t6, $t4, $t3"),
        Instruction("beq", ("$t6", "$t5", "no_max_update"),
                    "beq $t6, $t5, no_max_update"),
        Instruction("move", ("$t4", "$t3"), "move $t4, $t3"),

        Instruction("addi", ("$t0", "$t0", "4"),
                    "addi $t0, $t0, 4"),
        Instruction("addi", ("$t1", "$t1", "-1"),
                    "addi $t1, $t1, -1"),
        Instruction("bne", ("$t1", "$t5", "loop"),
                    "bne $t1, $t5, loop"),
        Instruction("j", ("end",), "j end"),

        # no_max_update:
        Instruction("addi", ("$t0", "$t0", "4"),
                    "addi $t0, $t0, 4"),
        Instruction("addi", ("$t1", "$t1", "-1"),
                    "addi $t1", "$t1", "-1"),
        Instruction("bne", ("$t1", "$t5", "loop"),
                    "bne $t1", "$t5", "loop"),

        Instruction("nop", (), "nop"),
    ]

    # Fix the two source tuples in the intentionally explicit representation.
    program[15] = Instruction(
        "addi", ("$t1", "$t1", "-1"), "addi $t1, $t1, -1"
    )
    program[16] = Instruction(
        "bne", ("$t1", "$t5", "loop"), "bne $t1, $t5, loop"
    )

    labels = {
        "loop": 5,
        "no_max_update": 14,
        "end": 17,
    }

    cpu.load_program(program, labels)
    cpu.run()

    print("Sum:", cpu.registers.read("$t2"))
    print("Maximum:", cpu.registers.read("$t4"))

    assert cpu.registers.read("$t2") == sum(values)
    assert cpu.registers.read("$t4") == max(values)


# ---------------------------------------------------------------------------
# Educational reference tables
# ---------------------------------------------------------------------------

def print_reference() -> None:
    print("\n=== MIPS reference ===")

    instructions = [
        ("li", "li $t0, 10", "Load an immediate value"),
        ("add", "add $t0, $t1, $t2", "Signed register addition"),
        ("sub", "sub $t0, $t1, $t2", "Signed subtraction"),
        ("mul", "mul $t0, $t1, $t2", "Integer multiplication"),
        ("addi", "addi $t0, $t1, 4", "Register plus immediate"),
        ("lw", "lw $t0, 8($sp)", "Load a 32-bit word"),
        ("sw", "sw $t0, 8($sp)", "Store a 32-bit word"),
        ("beq", "beq $t0, $t1, label", "Branch when equal"),
        ("bne", "bne $t0, $t1, label", "Branch when not equal"),
        ("j", "j label", "Unconditional jump"),
        ("jal", "jal function", "Jump and save return address"),
        ("jr", "jr $ra", "Return through register"),
    ]

    for mnemonic, syntax, meaning in instructions:
        print(f"{mnemonic:>5} | {syntax:<30} | {meaning}")

    print("\nImportant register roles:")
    roles = [
        ("$zero", "Always zero"),
        ("$v0-$v1", "Return values"),
        ("$a0-$a3", "Function arguments"),
        ("$t0-$t9", "Temporary registers"),
        ("$s0-$s7", "Saved registers"),
        ("$sp", "Stack pointer"),
        ("$fp", "Frame pointer"),
        ("$ra", "Return address"),
    ]

    for name, role in roles:
        print(f"  {name:<8} {role}")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def run_tests() -> None:
    print("\n=== Self-tests ===")

    registers = RegisterFile()
    registers.write("$t0", -123)
    assert registers.read("$t0") == -123

    registers.write("$zero", 42)
    assert registers.read("$zero") == 0

    memory = Memory()
    memory.store_word(0x1000, -123456)
    assert memory.load_word(0x1000) == -123456

    assert sign_extend_16(0x7FFF) == 32767
    assert sign_extend_16(0xFFFF) == -1

    cpu = MiniMIPS()
    program = [
        Instruction("li", ("$t0", "9")),
        Instruction("li", ("$t1", "3")),
        Instruction("sub", ("$t2", "$t0", "$t1")),
    ]
    cpu.load_program(program, {})
    cpu.run()
    assert cpu.registers.read("$t2") == 6

    print("All self-tests passed.")


# ---------------------------------------------------------------------------
# Main educational execution
# ---------------------------------------------------------------------------

def main() -> None:
    print("MIPS Assembly Language Basics Study Program")
    print("Concepts: registers, instructions, labels, memory, arithmetic")

    run_tests()
    print_reference()
    example_register_arithmetic()
    example_memory_operations()
    example_loop_with_labels()
    example_procedure_call()
    example_overflow()
    example_bit_operations()
    example_array_statistics()

    print("\n=== Study notes ===")
    print("1. Registers hold small, directly accessible values.")
    print("2. Memory holds larger collections of data and program state.")
    print("3. A label names an instruction address.")
    print("4. lw/sw move words between registers and memory.")
    print("5. Arithmetic instructions operate on registers or immediates.")
    print("6. Branches change control flow by changing the program counter.")
    print("7. jal/jr provide the basic mechanism for procedure calls.")
    print("8. MARS and RARS provide a visual environment for observing these ideas.")


if __name__ == "__main__":
    main()
