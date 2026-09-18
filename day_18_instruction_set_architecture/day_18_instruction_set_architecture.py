"""
Instruction Set Architecture (ISA)
Topic: Instructions, Operands, Opcodes, Registers, Addressing Modes

This standalone study program introduces ISA concepts from beginner level and
progresses toward instruction decoding, addressing modes, register files,
memory operations, a tiny assembler, and a small virtual CPU.

The implementation is intentionally educational. It models concepts found in
real processors without attempting to reproduce a particular commercial ISA.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Callable, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# 1. FUNDAMENTAL ISA TERMINOLOGY
# ---------------------------------------------------------------------------

def explain_fundamentals() -> None:
    print("=" * 78)
    print("1. ISA FUNDAMENTALS")
    print("=" * 78)

    concepts = {
        "Instruction Set Architecture (ISA)": (
            "The programmer-visible specification of a processor. It defines "
            "instructions, registers, data types, memory behavior, addressing "
            "modes, and observable machine-state rules."
        ),
        "Instruction": (
            "A binary operation encoded according to the ISA. Examples include "
            "ADD, LOAD, STORE, AND, SHIFT, and BRANCH."
        ),
        "Opcode": (
            "The operation field identifying what an instruction does."
        ),
        "Operand": (
            "A value, register, memory location, or immediate constant used "
            "by an instruction."
        ),
        "Register": (
            "A small, fast storage location inside the CPU."
        ),
        "Addressing mode": (
            "The rule used to determine where an instruction obtains an "
            "operand or address."
        ),
        "Instruction encoding": (
            "The binary layout used to represent an instruction."
        ),
    }

    for name, definition in concepts.items():
        print(f"{name:30} {definition}")

    print("\nISA is distinct from microarchitecture.")
    print("ISA: what software can observe.")
    print("Microarchitecture: how a processor internally implements the ISA.")


# ---------------------------------------------------------------------------
# 2. MACHINE STATE
# ---------------------------------------------------------------------------

class Flags:
    """A minimal condition-code register."""

    def __init__(self) -> None:
        self.zero = False
        self.negative = False
        self.carry = False
        self.overflow = False

    def __str__(self) -> str:
        return (
            f"Z={int(self.zero)} "
            f"N={int(self.negative)} "
            f"C={int(self.carry)} "
            f"V={int(self.overflow)}"
        )


class RegisterFile:
    """A small general-purpose register file."""

    def __init__(self, count: int = 8, width: int = 16) -> None:
        if count <= 0 or width <= 0:
            raise ValueError("Register count and width must be positive.")

        self.count = count
        self.width = width
        self.mask = (1 << width) - 1
        self.values = [0] * count

    def read(self, index: int) -> int:
        self._validate(index)
        return self.values[index]

    def write(self, index: int, value: int) -> None:
        self._validate(index)
        # Fixed-width registers wrap naturally, as they do in many CPUs.
        self.values[index] = value & self.mask

    def _validate(self, index: int) -> None:
        if not 0 <= index < self.count:
            raise IndexError(f"Invalid register R{index}.")

    def dump(self) -> None:
        print("Registers:", " ".join(
            f"R{i}={value:04X}" for i, value in enumerate(self.values)
        ))


class Memory:
    """Byte-addressable memory."""

    def __init__(self, size: int = 256) -> None:
        if size <= 0:
            raise ValueError("Memory size must be positive.")
        self.data = bytearray(size)

    def read_byte(self, address: int) -> int:
        self._validate(address)
        return self.data[address]

    def write_byte(self, address: int, value: int) -> None:
        self._validate(address)
        self.data[address] = value & 0xFF

    def read_word(self, address: int) -> int:
        """Read a 16-bit little-endian word."""
        low = self.read_byte(address)
        high = self.read_byte(address + 1)
        return low | (high << 8)

    def write_word(self, address: int, value: int) -> None:
        """Write a 16-bit little-endian word."""
        self.write_byte(address, value)
        self.write_byte(address + 1, value >> 8)

    def _validate(self, address: int) -> None:
        if not 0 <= address < len(self.data):
            raise MemoryError(f"Address {address} is outside memory.")


# ---------------------------------------------------------------------------
# 3. OPCODES AND INSTRUCTION TYPES
# ---------------------------------------------------------------------------

class Opcode(Enum):
    NOP = 0x00
    MOV = 0x01
    ADD = 0x02
    SUB = 0x03
    AND = 0x04
    OR = 0x05
    XOR = 0x06
    SHL = 0x07
    SHR = 0x08
    LOAD = 0x09
    STORE = 0x0A
    JMP = 0x0B
    JZ = 0x0C
    CMP = 0x0D
    HALT = 0x0E


@dataclass
class Instruction:
    """Decoded representation of an instruction."""

    opcode: Opcode
    operands: Tuple[int, ...] = ()
    immediate: Optional[int] = None

    def __str__(self) -> str:
        operand_text = ", ".join(map(str, self.operands))
        if self.immediate is not None:
            operand_text = (
                f"{operand_text}, #{self.immediate}"
                if operand_text else f"#{self.immediate}"
            )
        return f"{self.opcode.name} {operand_text}".strip()


# ---------------------------------------------------------------------------
# 4. BASIC OPERAND CATEGORIES
# ---------------------------------------------------------------------------

def demonstrate_operands() -> None:
    print("\n" + "=" * 78)
    print("2. OPERANDS")
    print("=" * 78)

    examples = [
        ("Register operand", "R1", "Value currently stored in register R1"),
        ("Immediate operand", "#42", "Constant encoded in the instruction"),
        ("Memory operand", "[100]", "Value loaded from memory address 100"),
        ("Register-indirect", "[R2]", "Address stored in R2"),
        ("PC-relative", "[PC+8]", "Address relative to the program counter"),
    ]

    for category, syntax, meaning in examples:
        print(f"{category:20} {syntax:10} {meaning}")


# ---------------------------------------------------------------------------
# 5. ADDRESSING MODES
# ---------------------------------------------------------------------------

class AddressingMode(Enum):
    REGISTER = "register"
    IMMEDIATE = "immediate"
    DIRECT = "direct"
    REGISTER_INDIRECT = "register_indirect"
    BASE_OFFSET = "base_offset"
    PC_RELATIVE = "pc_relative"
    INDEXED = "indexed"


@dataclass
class AddressingExample:
    mode: AddressingMode
    syntax: str
    explanation: str


def demonstrate_addressing_modes() -> None:
    print("\n" + "=" * 78)
    print("3. ADDRESSING MODES")
    print("=" * 78)

    examples = [
        AddressingExample(
            AddressingMode.REGISTER,
            "R3",
            "Operand is already in a register."
        ),
        AddressingExample(
            AddressingMode.IMMEDIATE,
            "#25",
            "Constant 25 is part of the instruction."
        ),
        AddressingExample(
            AddressingMode.DIRECT,
            "[200]",
            "Instruction contains the memory address."
        ),
        AddressingExample(
            AddressingMode.REGISTER_INDIRECT,
            "[R4]",
            "R4 contains the memory address."
        ),
        AddressingExample(
            AddressingMode.BASE_OFFSET,
            "[R4+12]",
            "Effective address = R4 + 12."
        ),
        AddressingExample(
            AddressingMode.PC_RELATIVE,
            "[PC+16]",
            "Effective address = PC + signed displacement."
        ),
        AddressingExample(
            AddressingMode.INDEXED,
            "[R4+R5]",
            "Effective address combines base and index registers."
        ),
    ]

    for example in examples:
        print(f"{example.mode.value:20} {example.syntax:12} "
              f"{example.explanation}")


# ---------------------------------------------------------------------------
# 6. EFFECTIVE ADDRESS CALCULATION
# ---------------------------------------------------------------------------

def effective_address(
    mode: AddressingMode,
    *,
    register_value: int = 0,
    index_value: int = 0,
    displacement: int = 0,
    pc: int = 0,
    direct_address: int = 0,
) -> int:
    """Calculate an effective address according to the selected mode."""

    if mode == AddressingMode.DIRECT:
        return direct_address

    if mode == AddressingMode.REGISTER_INDIRECT:
        return register_value

    if mode == AddressingMode.BASE_OFFSET:
        return register_value + displacement

    if mode == AddressingMode.INDEXED:
        return register_value + index_value + displacement

    if mode == AddressingMode.PC_RELATIVE:
        return pc + displacement

    raise ValueError(f"{mode.value} does not produce a memory address.")


# ---------------------------------------------------------------------------
# 7. SIMPLE ASSEMBLER
# ---------------------------------------------------------------------------

REGISTER_PATTERN = re.compile(r"R([0-7])$", re.IGNORECASE)


def parse_register(token: str) -> int:
    match = REGISTER_PATTERN.fullmatch(token.strip())
    if not match:
        raise ValueError(f"Invalid register: {token}")
    return int(match.group(1))


def parse_number(token: str) -> int:
    token = token.strip()
    if token.startswith("#"):
        token = token[1:]

    # int(..., 0) supports decimal, hexadecimal, binary, and octal prefixes.
    return int(token, 0)


def tokenize_assembly(line: str) -> List[str]:
    """
    Tokenize simple assembly syntax while preserving memory expressions.

    Example:
        LOAD R1, [R2+4]
    becomes:
        ["LOAD", "R1", "[R2+4]"]
    """
    line = line.split(";", 1)[0].strip()
    if not line:
        return []

    return [part.strip() for part in line.split(",")]


def assemble_line(line: str) -> Instruction:
    """Convert one human-readable assembly line into a decoded instruction."""
    tokens = tokenize_assembly(line)

    if not tokens:
        raise ValueError("Empty instruction.")

    operation = tokens[0].upper()
    try:
        opcode = Opcode[operation]
    except KeyError as exc:
        raise ValueError(f"Unknown opcode: {operation}") from exc

    operands = tokens[1:]

    if opcode in {Opcode.NOP, Opcode.HALT}:
        if operands:
            raise ValueError(f"{operation} takes no operands.")
        return Instruction(opcode)

    if opcode in {
        Opcode.MOV,
        Opcode.ADD,
        Opcode.SUB,
        Opcode.AND,
        Opcode.OR,
        Opcode.XOR,
        Opcode.CMP,
    }:
        if len(operands) != 2:
            raise ValueError(f"{operation} requires two operands.")

        destination_or_left = parse_register(operands[0])
        second = operands[1]

        if second.startswith("#"):
            return Instruction(
                opcode,
                operands=(destination_or_left,),
                immediate=parse_number(second),
            )

        return Instruction(
            opcode,
            operands=(destination_or_left, parse_register(second)),
        )

    if opcode in {Opcode.SHL, Opcode.SHR}:
        if len(operands) != 2:
            raise ValueError(f"{operation} requires two operands.")

        register = parse_register(operands[0])
        amount = parse_number(operands[1])
        return Instruction(
            opcode,
            operands=(register,),
            immediate=amount,
        )

    if opcode == Opcode.LOAD:
        if len(operands) != 2:
            raise ValueError("LOAD requires a destination and address.")

        destination = parse_register(operands[0])
        address_expression = operands[1]

        if not (address_expression.startswith("[")
                and address_expression.endswith("]")):
            raise ValueError("LOAD memory operand must use [address] syntax.")

        expression = address_expression[1:-1].replace(" ", "")

        if expression.startswith("R"):
            match = re.fullmatch(r"R([0-7])(?:\+(-?\d+))?", expression)
            if not match:
                raise ValueError("Invalid register-indirect address.")

            base = int(match.group(1))
            offset = int(match.group(2) or "0")

            # Encode base register and signed displacement.
            return Instruction(
                opcode,
                operands=(destination, base),
                immediate=offset,
            )

        return Instruction(
            opcode,
            operands=(destination,),
            immediate=int(expression, 0),
        )

    if opcode == Opcode.STORE:
        if len(operands) != 2:
            raise ValueError("STORE requires a source and address.")

        source = parse_register(operands[0])
        address_expression = operands[1]

        if not address_expression.startswith("["):
            raise ValueError("STORE memory operand must use [address] syntax.")

        expression = address_expression[1:-1].replace(" ", "")

        if expression.startswith("R"):
            match = re.fullmatch(r"R([0-7])(?:\+(-?\d+))?", expression)
            if not match:
                raise ValueError("Invalid register-indirect address.")

            base = int(match.group(1))
            offset = int(match.group(2) or "0")

            return Instruction(
                opcode,
                operands=(source, base),
                immediate=offset,
            )

        return Instruction(
            opcode,
            operands=(source,),
            immediate=int(expression, 0),
        )

    if opcode in {Opcode.JMP, Opcode.JZ}:
        if len(operands) != 1:
            raise ValueError(f"{operation} requires one address.")

        return Instruction(opcode, immediate=parse_number(operands[0]))

    raise NotImplementedError(f"Assembler rule missing for {operation}.")


# ---------------------------------------------------------------------------
# 8. VIRTUAL CPU
# ---------------------------------------------------------------------------

class VirtualCPU:
    """
    Educational CPU implementing a small register-memory ISA.

    Instruction cycle:
        Fetch -> Decode -> Execute -> Update PC

    The model uses:
        8 general-purpose 16-bit registers
        16-bit program counter
        16-bit word-oriented arithmetic
        byte-addressable memory
        zero, negative, carry and overflow flags
    """

    def __init__(self, memory_size: int = 256) -> None:
        self.registers = RegisterFile(count=8, width=16)
        self.memory = Memory(memory_size)
        self.flags = Flags()
        self.program_counter = 0
        self.halted = False
        self.program: List[Instruction] = []
        self.steps = 0

    def load_program(self, program: List[Instruction]) -> None:
        self.program = program
        self.program_counter = 0
        self.halted = False
        self.steps = 0

    def _set_arithmetic_flags(
        self,
        result: int,
        carry: bool = False,
        overflow: bool = False,
    ) -> None:
        masked = result & self.registers.mask
        sign_bit = 1 << (self.registers.width - 1)

        self.flags.zero = masked == 0
        self.flags.negative = bool(masked & sign_bit)
        self.flags.carry = carry
        self.flags.overflow = overflow

    def _add(self, left: int, right: int) -> int:
        raw = left + right
        result = raw & self.registers.mask

        sign_bit = 1 << (self.registers.width - 1)
        signed_left = left if left < sign_bit else left - (1 << self.registers.width)
        signed_right = (
            right if right < sign_bit
            else right - (1 << self.registers.width)
        )
        signed_result = (
            result if result < sign_bit
            else result - (1 << self.registers.width)
        )

        overflow = (
            (signed_left >= 0 and signed_right >= 0 and signed_result < 0)
            or
            (signed_left < 0 and signed_right < 0 and signed_result >= 0)
        )

        self._set_arithmetic_flags(
            result,
            carry=raw > self.registers.mask,
            overflow=overflow,
        )
        return result

    def _subtract(self, left: int, right: int) -> int:
        raw = left - right
        result = raw & self.registers.mask

        sign_bit = 1 << (self.registers.width - 1)
        signed_left = left if left < sign_bit else left - (1 << self.registers.width)
        signed_right = (
            right if right < sign_bit
            else right - (1 << self.registers.width)
        )
        signed_result = (
            result if result < sign_bit
            else result - (1 << self.registers.width)
        )

        overflow = (
            (signed_left >= 0 and signed_right < 0 and signed_result < 0)
            or
            (signed_left < 0 and signed_right >= 0 and signed_result >= 0)
        )

        self._set_arithmetic_flags(
            result,
            carry=left >= right,
            overflow=overflow,
        )
        return result

    def _read_second_operand(self, instruction: Instruction) -> int:
        if instruction.immediate is not None:
            return instruction.immediate & self.registers.mask

        return self.registers.read(instruction.operands[1])

    def step(self) -> None:
        """Execute exactly one instruction."""

        if self.halted:
            return

        if not 0 <= self.program_counter < len(self.program):
            raise RuntimeError("Program counter left program bounds.")

        instruction = self.program[self.program_counter]
        current_pc = self.program_counter
        self.program_counter += 1

        opcode = instruction.opcode

        if opcode == Opcode.NOP:
            pass

        elif opcode == Opcode.MOV:
            destination = instruction.operands[0]
            value = self._read_second_operand(instruction)
            self.registers.write(destination, value)

        elif opcode == Opcode.ADD:
            destination = instruction.operands[0]
            left = self.registers.read(destination)
            right = self._read_second_operand(instruction)
            self.registers.write(destination, self._add(left, right))

        elif opcode == Opcode.SUB:
            destination = instruction.operands[0]
            left = self.registers.read(destination)
            right = self._read_second_operand(instruction)
            self.registers.write(destination, self._subtract(left, right))

        elif opcode in {Opcode.AND, Opcode.OR, Opcode.XOR}:
            destination = instruction.operands[0]
            left = self.registers.read(destination)
            right = self._read_second_operand(instruction)

            if opcode == Opcode.AND:
                result = left & right
            elif opcode == Opcode.OR:
                result = left | right
            else:
                result = left ^ right

            self.registers.write(destination, result)
            self._set_arithmetic_flags(result)

        elif opcode in {Opcode.SHL, Opcode.SHR}:
            destination = instruction.operands[0]
            amount = instruction.immediate or 0
            value = self.registers.read(destination)

            if amount < 0:
                raise ValueError("Shift amount cannot be negative.")

            if opcode == Opcode.SHL:
                result = value << amount
            else:
                result = value >> amount

            self.registers.write(destination, result)
            self._set_arithmetic_flags(result)

        elif opcode == Opcode.CMP:
            left = self.registers.read(instruction.operands[0])
            right = self._read_second_operand(instruction)
            self._subtract(left, right)

        elif opcode == Opcode.LOAD:
            destination = instruction.operands[0]

            if len(instruction.operands) == 2:
                base = self.registers.read(instruction.operands[1])
                address = base + (instruction.immediate or 0)
            else:
                address = instruction.immediate or 0

            self.registers.write(
                destination,
                self.memory.read_word(address),
            )

        elif opcode == Opcode.STORE:
            source = instruction.operands[0]

            if len(instruction.operands) == 2:
                base = self.registers.read(instruction.operands[1])
                address = base + (instruction.immediate or 0)
            else:
                address = instruction.immediate or 0

            self.memory.write_word(
                address,
                self.registers.read(source),
            )

        elif opcode == Opcode.JMP:
            self._validate_program_target(instruction.immediate)
            self.program_counter = instruction.immediate

        elif opcode == Opcode.JZ:
            if self.flags.zero:
                self._validate_program_target(instruction.immediate)
                self.program_counter = instruction.immediate

        elif opcode == Opcode.HALT:
            self.halted = True

        else:
            raise RuntimeError(f"Unsupported opcode: {opcode}")

        self.steps += 1

        if self.program_counter == current_pc and opcode != Opcode.JMP:
            # A branch may legitimately create a self-loop. This check is
            # intentionally not used as a loop detector.
            pass

    def _validate_program_target(self, target: Optional[int]) -> None:
        if target is None or not 0 <= target < len(self.program):
            raise RuntimeError(f"Invalid branch target: {target}")

    def run(self, max_steps: int = 1000) -> None:
        """Execute until HALT or until a safety step limit is reached."""

        while not self.halted:
            if self.steps >= max_steps:
                raise RuntimeError(
                    "Execution stopped by maximum-step safety limit."
                )
            self.step()

    def dump_state(self) -> None:
        print(f"PC={self.program_counter} HALTED={self.halted}")
        self.registers.dump()
        print("Flags:", self.flags)


# ---------------------------------------------------------------------------
# 9. INSTRUCTION ENCODING
# ---------------------------------------------------------------------------

def encode_instruction(instruction: Instruction) -> int:
    """
    Encode the educational instruction into a 32-bit machine word.

    Layout:
        bits 31..24 : opcode
        bits 23..20 : operand/register A
        bits 19..16 : operand/register B
        bits 15..0  : immediate

    This fixed layout is intentionally simple. Real ISAs commonly use
    multiple instruction formats with different field arrangements.
    """

    opcode = instruction.opcode.value
    operand_a = instruction.operands[0] if instruction.operands else 0
    operand_b = instruction.operands[1] if len(instruction.operands) > 1 else 0
    immediate = instruction.immediate or 0

    if not 0 <= operand_a <= 0xF:
        raise ValueError("Operand A does not fit in four bits.")

    if not 0 <= operand_b <= 0xF:
        raise ValueError("Operand B does not fit in four bits.")

    return (
        (opcode << 24)
        | (operand_a << 20)
        | (operand_b << 16)
        | (immediate & 0xFFFF)
    )


def decode_instruction(machine_word: int) -> Instruction:
    """Decode the educational 32-bit instruction format."""

    opcode_value = (machine_word >> 24) & 0xFF
    operand_a = (machine_word >> 20) & 0xF
    operand_b = (machine_word >> 16) & 0xF
    immediate = machine_word & 0xFFFF

    try:
        opcode = Opcode(opcode_value)
    except ValueError as exc:
        raise ValueError(f"Unknown opcode 0x{opcode_value:02X}") from exc

    if opcode in {Opcode.NOP, Opcode.HALT}:
        return Instruction(opcode)

    if opcode in {
        Opcode.JMP,
        Opcode.JZ,
    }:
        return Instruction(opcode, immediate=immediate)

    if opcode in {Opcode.SHL, Opcode.SHR}:
        return Instruction(opcode, operands=(operand_a,), immediate=immediate)

    if opcode in {Opcode.LOAD, Opcode.STORE}:
        # Zero B indicates direct addressing in this educational encoding.
        if operand_b == 0:
            return Instruction(
                opcode,
                operands=(operand_a,),
                immediate=immediate,
            )

        return Instruction(
            opcode,
            operands=(operand_a, operand_b),
            immediate=immediate,
        )

    if opcode in {
        Opcode.MOV,
        Opcode.ADD,
        Opcode.SUB,
        Opcode.AND,
        Opcode.OR,
        Opcode.XOR,
        Opcode.CMP,
    }:
        return Instruction(
            opcode,
            operands=(operand_a, operand_b),
        )

    raise ValueError(f"Cannot decode {opcode.name}.")


# ---------------------------------------------------------------------------
# 10. EXAMPLES
# ---------------------------------------------------------------------------

def example_address_calculation() -> None:
    print("\n" + "=" * 78)
    print("4. EFFECTIVE ADDRESS EXAMPLES")
    print("=" * 78)

    print(
        "Direct [200]:",
        effective_address(AddressingMode.DIRECT, direct_address=200),
    )
    print(
        "Indirect [R2], R2=100:",
        effective_address(
            AddressingMode.REGISTER_INDIRECT,
            register_value=100,
        ),
    )
    print(
        "Base+offset [R2+12], R2=100:",
        effective_address(
            AddressingMode.BASE_OFFSET,
            register_value=100,
            displacement=12,
        ),
    )
    print(
        "Indexed [R2+R3], R2=100, R3=20:",
        effective_address(
            AddressingMode.INDEXED,
            register_value=100,
            index_value=20,
        ),
    )
    print(
        "PC-relative [PC+16], PC=50:",
        effective_address(
            AddressingMode.PC_RELATIVE,
            pc=50,
            displacement=16,
        ),
    )


def example_instruction_encoding() -> None:
    print("\n" + "=" * 78)
    print("5. INSTRUCTION ENCODING")
    print("=" * 78)

    instruction = Instruction(
        Opcode.ADD,
        operands=(1, 2),
    )

    machine_word = encode_instruction(instruction)
    decoded = decode_instruction(machine_word)

    print("Assembly:", instruction)
    print(f"Machine word: 0x{machine_word:08X}")
    print("Decoded:", decoded)


def example_virtual_cpu() -> None:
    print("\n" + "=" * 78)
    print("6. VIRTUAL CPU EXECUTION")
    print("=" * 78)

    assembly_program = [
        "MOV R0, #10",
        "MOV R1, #20",
        "ADD R0, R1",
        "STORE R0, [100]",
        "LOAD R2, [100]",
        "CMP R2, #30",
        "JZ 8",
        "MOV R3, #999",
        "HALT",
    ]

    program = [assemble_line(line) for line in assembly_program]

    for address, instruction in enumerate(program):
        print(f"{address:02}: {instruction}")

    cpu = VirtualCPU()
    cpu.load_program(program)
    cpu.run()

    print("\nFinal state:")
    cpu.dump_state()
    print("Memory[100..101]:", list(cpu.memory.data[100:102]))
    print("Expected R0=30 and R2=30.")


def example_edge_cases() -> None:
    print("\n" + "=" * 78)
    print("7. EDGE CASES AND ERROR HANDLING")
    print("=" * 78)

    # Fixed-width arithmetic wraps around.
    registers = RegisterFile(width=8)
    registers.write(0, 255)
    registers.write(1, 1)

    wrapped = (registers.read(0) + registers.read(1)) & registers.mask
    print("8-bit 255 + 1 =", wrapped, "(wraparound)")

    try:
        registers.read(99)
    except IndexError as exc:
        print("Invalid register:", exc)

    memory = Memory(16)

    try:
        memory.read_word(15)
    except MemoryError as exc:
        print("Unaligned/out-of-bounds word access:", exc)

    try:
        assemble_line("UNKNOWN R1, R2")
    except ValueError as exc:
        print("Assembler error:", exc)

    try:
        assemble_line("ADD R1")
    except ValueError as exc:
        print("Operand-count error:", exc)


# ---------------------------------------------------------------------------
# 11. CONCEPTUAL COMPARISONS
# ---------------------------------------------------------------------------

def comparison_table() -> None:
    print("\n" + "=" * 78)
    print("8. IMPORTANT DISTINCTIONS")
    print("=" * 78)

    rows = [
        ("Opcode", "Identifies operation", "ADD"),
        ("Operand", "Identifies data/source/destination", "R1, #10"),
        ("Register", "CPU-local storage", "R1"),
        ("Memory address", "Identifies memory location", "0x100"),
        ("Addressing mode", "Explains how operand/address is obtained",
         "[R2+8]"),
        ("ISA", "Software-visible machine contract", "Instruction definitions"),
        ("Microarchitecture", "Internal processor implementation",
         "Pipeline/cache/execution units"),
    ]

    for concept, role, example in rows:
        print(f"{concept:20} | {role:45} | {example}")


# ---------------------------------------------------------------------------
# 12. MAIN STUDY PROGRAM
# ---------------------------------------------------------------------------

def main() -> None:
    explain_fundamentals()
    demonstrate_operands()
    demonstrate_addressing_modes()
    example_address_calculation()
    example_instruction_encoding()
    example_virtual_cpu()
    example_edge_cases()
    comparison_table()

    print("\n" + "=" * 78)
    print("9. STUDY CHECKPOINTS")
    print("=" * 78)

    checkpoints = [
        "An opcode identifies an operation; it is not the operand itself.",
        "Registers are storage locations defined by the ISA.",
        "Immediate values are constants encoded inside instructions.",
        "An addressing mode defines how an operand or effective address is found.",
        "A LOAD normally moves data from memory into a register.",
        "A STORE normally moves data from a register into memory.",
        "The program counter identifies the next instruction to execute.",
        "Conditional branches often depend on flags or comparison results.",
        "Instruction encoding maps assembly-level fields into binary fields.",
        "ISA specifies behavior; microarchitecture determines how that behavior "
        "is implemented internally.",
    ]

    for checkpoint in checkpoints:
        print("*", checkpoint)

    print("\nStudy complete.")


if __name__ == "__main__":
    main()
