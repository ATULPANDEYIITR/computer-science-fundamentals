"""
CPU Simulator: Central Processing Unit Fundamentals Through a Working Emulator

This standalone study program demonstrates how a simplified CPU executes
machine instructions. It models:

- Arithmetic Logic Unit (ALU)
- Control Unit
- General-purpose registers
- Program Counter (PC)
- Instruction Register (IR)
- Memory
- Flags
- Fetch-decode-execute cycle
- Immediate and register operands
- Arithmetic and logical operations
- Conditional and unconditional branching
- Stack operations
- Function-like CALL/RET behavior
- Memory addressing
- Input/output instructions
- Program validation
- Tracing and debugging
- Instruction counting
- Cycle estimation
- Performance considerations
- CPU state inspection

The simulator is intentionally small enough to understand while retaining
the essential architectural ideas found in real processors.

No external packages are required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Iterable, Optional


# ============================================================================
# SECTION 1: BASIC CPU TERMINOLOGY
# ============================================================================

def print_section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


print_section("1. CPU COMPONENTS")

print(
    """
A Central Processing Unit executes instructions.

The major components modeled by this simulator are:

ALU:
    Performs arithmetic and logical operations.

Control Unit:
    Fetches instructions, decodes them, and coordinates execution.

Registers:
    Very small, fast storage locations inside the CPU.

Program Counter (PC):
    Holds the address of the next instruction to fetch.

Instruction Register (IR):
    Holds the currently executing instruction.

Memory:
    Stores instructions and data.

Flags:
    Record properties of an ALU result, such as zero, negative, carry,
    and overflow.

The fundamental instruction cycle is:

    FETCH -> DECODE -> EXECUTE -> UPDATE STATE -> FETCH ...

A real processor contains substantially more hardware, but this model
captures the core idea of instruction execution.
"""
)


# ============================================================================
# SECTION 2: INSTRUCTION SET
# ============================================================================

class Opcode(str, Enum):
    NOP = "NOP"

    # Data movement
    LOAD = "LOAD"
    STORE = "STORE"
    MOV = "MOV"

    # Arithmetic
    ADD = "ADD"
    SUB = "SUB"
    MUL = "MUL"
    DIV = "DIV"
    INC = "INC"
    DEC = "DEC"

    # Logical
    AND = "AND"
    OR = "OR"
    XOR = "XOR"
    NOT = "NOT"
    SHL = "SHL"
    SHR = "SHR"

    # Comparison and control flow
    CMP = "CMP"
    JMP = "JMP"
    JZ = "JZ"
    JNZ = "JNZ"
    JN = "JN"
    JP = "JP"

    # Stack and procedure control
    PUSH = "PUSH"
    POP = "POP"
    CALL = "CALL"
    RET = "RET"

    # Input/output and termination
    IN = "IN"
    OUT = "OUT"
    HALT = "HALT"


@dataclass
class Instruction:
    opcode: Opcode
    operands: tuple = ()

    def __str__(self) -> str:
        if not self.operands:
            return self.opcode.value
        return f"{self.opcode.value} " + ", ".join(map(str, self.operands))


# ============================================================================
# SECTION 3: FLAGS
# ============================================================================

@dataclass
class Flags:
    """
    CPU status flags.

    Z: Zero flag. Set when the result is zero.
    N: Negative flag. Set when the signed result is negative.
    C: Carry flag. Used for unsigned arithmetic and shifts.
    V: Overflow flag. Indicates signed arithmetic overflow.
    """

    zero: bool = False
    negative: bool = False
    carry: bool = False
    overflow: bool = False

    def reset(self) -> None:
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


# ============================================================================
# SECTION 4: ALU
# ============================================================================

class ALU:
    """
    Arithmetic Logic Unit.

    The ALU operates on fixed-width unsigned bit patterns.

    Internally values are kept in the range:

        0 <= value <= 2^word_size - 1

    Signed interpretation uses two's complement.
    """

    def __init__(self, word_size: int = 16):
        if word_size < 4 or word_size > 32:
            raise ValueError("word_size must be between 4 and 32 bits")

        self.word_size = word_size
        self.mask = (1 << word_size) - 1
        self.sign_bit = 1 << (word_size - 1)

    def normalize(self, value: int) -> int:
        return value & self.mask

    def signed(self, value: int) -> int:
        value = self.normalize(value)
        if value & self.sign_bit:
            return value - (1 << self.word_size)
        return value

    def update_flags(
        self,
        result: int,
        *,
        carry: bool = False,
        overflow: bool = False,
    ) -> int:
        result = self.normalize(result)

        # The zero and negative flags describe the normalized result.
        self.last_flags.zero = result == 0
        self.last_flags.negative = bool(result & self.sign_bit)
        self.last_flags.carry = carry
        self.last_flags.overflow = overflow

        return result

    def prepare_flags(self, flags: Flags) -> None:
        self.last_flags = flags

    def add(self, left: int, right: int, flags: Flags) -> int:
        self.prepare_flags(flags)
        raw = left + right
        result = self.normalize(raw)

        carry = raw > self.mask

        left_signed = self.signed(left)
        right_signed = self.signed(right)
        result_signed = self.signed(result)

        # Signed overflow occurs when two operands with the same sign
        # produce a result with the opposite sign.
        overflow = (
            (left_signed >= 0 and right_signed >= 0 and result_signed < 0)
            or
            (left_signed < 0 and right_signed < 0 and result_signed >= 0)
        )

        return self.update_flags(result, carry=carry, overflow=overflow)

    def subtract(self, left: int, right: int, flags: Flags) -> int:
        self.prepare_flags(flags)
        result = self.normalize(left - right)
        carry = left >= right

        left_signed = self.signed(left)
        right_signed = self.signed(right)
        result_signed = self.signed(result)

        # Signed subtraction overflow:
        # positive - negative -> negative
        # negative - positive -> positive
        overflow = (
            (left_signed >= 0 and right_signed < 0 and result_signed < 0)
            or
            (left_signed < 0 and right_signed >= 0 and result_signed >= 0)
        )

        return self.update_flags(result, carry=carry, overflow=overflow)

    def multiply(self, left: int, right: int, flags: Flags) -> int:
        self.prepare_flags(flags)
        raw = left * right
        result = self.normalize(raw)
        return self.update_flags(result, carry=raw > self.mask)

    def divide(self, left: int, right: int, flags: Flags) -> int:
        if right == 0:
            raise ZeroDivisionError("ALU division by zero")
        self.prepare_flags(flags)
        result = left // right
        return self.update_flags(result)

    def logical(self, operation: str, left: int, right: int, flags: Flags) -> int:
        self.prepare_flags(flags)

        operations: dict[str, Callable[[int, int], int]] = {
            "AND": lambda a, b: a & b,
            "OR": lambda a, b: a | b,
            "XOR": lambda a, b: a ^ b,
        }

        if operation not in operations:
            raise ValueError(f"Unknown logical operation: {operation}")

        result = operations[operation](left, right)
        return self.update_flags(result)

    def bitwise_not(self, value: int, flags: Flags) -> int:
        self.prepare_flags(flags)
        return self.update_flags(~value)

    def shift_left(self, value: int, amount: int, flags: Flags) -> int:
        self.prepare_flags(flags)

        if amount < 0:
            raise ValueError("Shift amount cannot be negative")

        if amount == 0:
            return self.update_flags(value)

        carry = bool(value & (1 << (self.word_size - amount))) if amount <= self.word_size else False
        result = self.normalize(value << amount)

        return self.update_flags(result, carry=carry)

    def shift_right(self, value: int, amount: int, flags: Flags) -> int:
        self.prepare_flags(flags)

        if amount < 0:
            raise ValueError("Shift amount cannot be negative")

        if amount == 0:
            return self.update_flags(value)

        carry = bool(value & (1 << (amount - 1))) if amount <= self.word_size else False
        result = value >> amount

        return self.update_flags(result, carry=carry)


# ============================================================================
# SECTION 5: CPU
# ============================================================================

@dataclass
class CPU:
    """
    A complete educational CPU simulator.

    The architecture uses:
        - 8 general-purpose registers: R0-R7
        - 16-bit words
        - 256 memory cells
        - PC
        - IR
        - SP
        - FLAGS
    """

    word_size: int = 16
    memory_size: int = 256
    register_count: int = 8

    registers: list[int] = field(init=False)
    memory: list[int] = field(init=False)
    pc: int = field(default=0, init=False)
    sp: int = field(init=False)
    ir: Optional[Instruction] = field(default=None, init=False)
    flags: Flags = field(default_factory=Flags, init=False)
    halted: bool = field(default=False, init=False)
    cycles: int = field(default=0, init=False)
    instructions_executed: int = field(default=0, init=False)
    output_buffer: list[int] = field(default_factory=list, init=False)
    input_buffer: list[int] = field(default_factory=list, init=False)
    trace_enabled: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.memory_size <= 0:
            raise ValueError("memory_size must be positive")

        self.registers = [0] * self.register_count
        self.memory = [0] * self.memory_size

        # Stack grows downward from the highest memory address.
        self.sp = self.memory_size - 1

        self.alu = ALU(self.word_size)
        self.alu.prepare_flags(self.flags)

        self.program: list[Instruction] = []

    # ---------------------------------------------------------------------
    # Register and memory helpers
    # ---------------------------------------------------------------------

    @property
    def value_mask(self) -> int:
        return (1 << self.word_size) - 1

    def register_index(self, register: str) -> int:
        if not isinstance(register, str) or not register.upper().startswith("R"):
            raise ValueError(f"Invalid register: {register}")

        try:
            index = int(register[1:])
        except ValueError as exc:
            raise ValueError(f"Invalid register: {register}") from exc

        if not 0 <= index < self.register_count:
            raise ValueError(f"Register out of range: {register}")

        return index

    def read_register(self, register: str) -> int:
        return self.registers[self.register_index(register)]

    def write_register(self, register: str, value: int) -> None:
        index = self.register_index(register)
        self.registers[index] = value & self.value_mask

    def validate_address(self, address: int) -> None:
        if not isinstance(address, int):
            raise TypeError("Memory address must be an integer")

        if not 0 <= address < self.memory_size:
            raise MemoryError(f"Invalid memory address: {address}")

    def read_memory(self, address: int) -> int:
        self.validate_address(address)
        return self.memory[address]

    def write_memory(self, address: int, value: int) -> None:
        self.validate_address(address)
        self.memory[address] = value & self.value_mask

    # ---------------------------------------------------------------------
    # Operand resolution
    # ---------------------------------------------------------------------

    def resolve_value(self, operand) -> int:
        """
        Resolve an operand.

        Supported forms:
            "R0"      -> register value
            integer   -> immediate value
        """
        if isinstance(operand, str) and operand.upper().startswith("R"):
            return self.read_register(operand)

        if isinstance(operand, int):
            return operand & self.value_mask

        raise ValueError(f"Unsupported value operand: {operand}")

    # ---------------------------------------------------------------------
    # Program loading
    # ---------------------------------------------------------------------

    def load_program(self, program: Iterable[Instruction], start_address: int = 0) -> None:
        instructions = list(program)

        if start_address < 0 or start_address + len(instructions) > self.memory_size:
            raise MemoryError("Program does not fit into memory")

        self.program = instructions
        self.pc = start_address
        self.halted = False
        self.ir = None
        self.cycles = 0
        self.instructions_executed = 0
        self.output_buffer.clear()

    # ---------------------------------------------------------------------
    # Fetch
    # ---------------------------------------------------------------------

    def fetch(self) -> Instruction:
        if not 0 <= self.pc < len(self.program):
            raise RuntimeError(
                f"Program counter {self.pc} points outside the loaded program"
            )

        # Fetch reads the instruction addressed by PC.
        self.ir = self.program[self.pc]

        # Normal sequential execution advances PC.
        self.pc += 1

        return self.ir

    # ---------------------------------------------------------------------
    # Stack
    # ---------------------------------------------------------------------

    def push(self, value: int) -> None:
        if self.sp < 0:
            raise MemoryError("Stack overflow")

        self.write_memory(self.sp, value)
        self.sp -= 1

    def pop(self) -> int:
        if self.sp >= self.memory_size - 1:
            raise MemoryError("Stack underflow")

        self.sp += 1
        return self.read_memory(self.sp)

    # ---------------------------------------------------------------------
    # Decode and execute
    # ---------------------------------------------------------------------

    def execute(self, instruction: Instruction) -> None:
        opcode = instruction.opcode
        operands = instruction.operands

        if opcode == Opcode.NOP:
            return

        if opcode == Opcode.HALT:
            self.halted = True
            return

        if opcode == Opcode.LOAD:
            destination, address = operands
            self.write_register(destination, self.read_memory(address))
            return

        if opcode == Opcode.STORE:
            source, address = operands
            self.write_memory(address, self.read_register(source))
            return

        if opcode == Opcode.MOV:
            destination, source = operands
            self.write_register(destination, self.resolve_value(source))
            return

        if opcode in {
            Opcode.ADD,
            Opcode.SUB,
            Opcode.MUL,
            Opcode.DIV,
            Opcode.AND,
            Opcode.OR,
            Opcode.XOR,
        }:
            destination, left, right = operands

            left_value = self.resolve_value(left)
            right_value = self.resolve_value(right)

            if opcode == Opcode.ADD:
                result = self.alu.add(left_value, right_value, self.flags)
            elif opcode == Opcode.SUB:
                result = self.alu.subtract(left_value, right_value, self.flags)
            elif opcode == Opcode.MUL:
                result = self.alu.multiply(left_value, right_value, self.flags)
            elif opcode == Opcode.DIV:
                result = self.alu.divide(left_value, right_value, self.flags)
            else:
                result = self.alu.logical(
                    opcode.value,
                    left_value,
                    right_value,
                    self.flags,
                )

            self.write_register(destination, result)
            return

        if opcode == Opcode.INC:
            register, = operands
            current = self.read_register(register)
            result = self.alu.add(current, 1, self.flags)
            self.write_register(register, result)
            return

        if opcode == Opcode.DEC:
            register, = operands
            current = self.read_register(register)
            result = self.alu.subtract(current, 1, self.flags)
            self.write_register(register, result)
            return

        if opcode == Opcode.NOT:
            destination, source = operands
            result = self.alu.bitwise_not(
                self.resolve_value(source),
                self.flags,
            )
            self.write_register(destination, result)
            return

        if opcode == Opcode.SHL:
            destination, source, amount = operands
            result = self.alu.shift_left(
                self.resolve_value(source),
                self.resolve_value(amount),
                self.flags,
            )
            self.write_register(destination, result)
            return

        if opcode == Opcode.SHR:
            destination, source, amount = operands
            result = self.alu.shift_right(
                self.resolve_value(source),
                self.resolve_value(amount),
                self.flags,
            )
            self.write_register(destination, result)
            return

        if opcode == Opcode.CMP:
            left, right = operands
            self.alu.subtract(
                self.resolve_value(left),
                self.resolve_value(right),
                self.flags,
            )
            return

        if opcode == Opcode.JMP:
            target, = operands
            self.validate_program_address(target)
            self.pc = target
            return

        if opcode == Opcode.JZ:
            target, = operands
            if self.flags.zero:
                self.validate_program_address(target)
                self.pc = target
            return

        if opcode == Opcode.JNZ:
            target, = operands
            if not self.flags.zero:
                self.validate_program_address(target)
                self.pc = target
            return

        if opcode == Opcode.JN:
            target, = operands
            if self.flags.negative:
                self.validate_program_address(target)
                self.pc = target
            return

        if opcode == Opcode.JP:
            target, = operands
            if not self.flags.negative:
                self.validate_program_address(target)
                self.pc = target
            return

        if opcode == Opcode.PUSH:
            source, = operands
            self.push(self.resolve_value(source))
            return

        if opcode == Opcode.POP:
            destination, = operands
            self.write_register(destination, self.pop())
            return

        if opcode == Opcode.CALL:
            target, = operands
            self.validate_program_address(target)

            # PC already points to the instruction after CALL.
            # Storing it enables RET to resume execution.
            self.push(self.pc)
            self.pc = target
            return

        if opcode == Opcode.RET:
            self.pc = self.pop()
            self.validate_program_address(self.pc)
            return

        if opcode == Opcode.IN:
            destination, = operands

            if not self.input_buffer:
                raise RuntimeError("IN instruction requires an input value")

            self.write_register(destination, self.input_buffer.pop(0))
            return

        if opcode == Opcode.OUT:
            source, = operands
            self.output_buffer.append(self.resolve_value(source))
            return

        raise NotImplementedError(f"Unsupported opcode: {opcode}")

    def validate_program_address(self, address: int) -> None:
        if not isinstance(address, int):
            raise TypeError("Program address must be an integer")

        if not 0 <= address < len(self.program):
            raise RuntimeError(
                f"Invalid program address {address}; "
                f"program contains {len(self.program)} instructions"
            )

    # ---------------------------------------------------------------------
    # Clock and run loop
    # ---------------------------------------------------------------------

    def cycle_cost(self, instruction: Instruction) -> int:
        """
        Simplified timing model.

        Real CPUs use much more complicated timing behavior involving
        pipelines, caches, branch prediction, superscalar execution,
        out-of-order execution, memory latency, and many other factors.

        This table is only an educational approximation.
        """
        costs = {
            Opcode.NOP: 1,
            Opcode.MOV: 1,
            Opcode.LOAD: 3,
            Opcode.STORE: 3,
            Opcode.ADD: 1,
            Opcode.SUB: 1,
            Opcode.MUL: 3,
            Opcode.DIV: 8,
            Opcode.INC: 1,
            Opcode.DEC: 1,
            Opcode.AND: 1,
            Opcode.OR: 1,
            Opcode.XOR: 1,
            Opcode.NOT: 1,
            Opcode.SHL: 1,
            Opcode.SHR: 1,
            Opcode.CMP: 1,
            Opcode.JMP: 1,
            Opcode.JZ: 1,
            Opcode.JNZ: 1,
            Opcode.JN: 1,
            Opcode.JP: 1,
            Opcode.PUSH: 2,
            Opcode.POP: 2,
            Opcode.CALL: 3,
            Opcode.RET: 3,
            Opcode.IN: 2,
            Opcode.OUT: 2,
            Opcode.HALT: 1,
        }

        return costs.get(instruction.opcode, 1)

    def step(self) -> None:
        if self.halted:
            return

        old_pc = self.pc
        instruction = self.fetch()

        if self.trace_enabled:
            print(
                f"PC={old_pc:03d} | "
                f"{instruction!s:<24} | "
                f"before={self.registers}"
            )

        self.execute(instruction)
        self.instructions_executed += 1
        self.cycles += self.cycle_cost(instruction)

        if self.trace_enabled:
            print(
                f"       {'':<24} | "
                f"after ={self.registers} | "
                f"{self.flags}"
            )

    def run(self, max_steps: int = 100_000) -> None:
        steps = 0

        while not self.halted:
            if steps >= max_steps:
                raise RuntimeError(
                    "Maximum instruction count reached. "
                    "Possible infinite loop."
                )

            self.step()
            steps += 1

    def reset(self) -> None:
        self.registers = [0] * self.register_count
        self.memory = [0] * self.memory_size
        self.pc = 0
        self.sp = self.memory_size - 1
        self.ir = None
        self.flags.reset()
        self.halted = False
        self.cycles = 0
        self.instructions_executed = 0
        self.output_buffer.clear()
        self.input_buffer.clear()

    def dump_state(self) -> None:
        print("Registers:")
        for index, value in enumerate(self.registers):
            print(
                f"  R{index}: unsigned={value:5d} "
                f"signed={self.alu.signed(value):6d} "
                f"hex=0x{value:04X}"
            )

        print(f"PC:      {self.pc}")
        print(f"SP:      {self.sp}")
        print(f"IR:      {self.ir}")
        print(f"Flags:   {self.flags}")
        print(f"Cycles:  {self.cycles}")
        print(f"Executed:{self.instructions_executed}")
        print(f"Output:  {self.output_buffer}")


# ============================================================================
# SECTION 6: PROGRAM CONSTRUCTION HELPERS
# ============================================================================

def I(opcode: Opcode, *operands) -> Instruction:
    """Short helper for creating instructions."""
    return Instruction(opcode, operands)


def run_program(
    title: str,
    program: list[Instruction],
    *,
    trace: bool = False,
    input_values: Optional[list[int]] = None,
) -> CPU:
    print_section(title)

    cpu = CPU()
    cpu.load_program(program)
    cpu.trace_enabled = trace

    if input_values:
        cpu.input_buffer.extend(input_values)

    cpu.run()
    cpu.dump_state()

    return cpu


# ============================================================================
# SECTION 7: BEGINNER EXAMPLE - ADD TWO NUMBERS
# ============================================================================

addition_program = [
    I(Opcode.MOV, "R0", 12),
    I(Opcode.MOV, "R1", 30),
    I(Opcode.ADD, "R2", "R0", "R1"),
    I(Opcode.OUT, "R2"),
    I(Opcode.HALT),
]

cpu = run_program(
    "2. Beginner CPU Program: Add Two Numbers",
    addition_program,
)

print("Expected output:", cpu.output_buffer)
print("The ALU calculated 12 + 30 and stored the result in R2.")


# ============================================================================
# SECTION 8: MEMORY LOAD AND STORE
# ============================================================================

memory_program = [
    I(Opcode.MOV, "R0", 1234),
    I(Opcode.STORE, "R0", 100),
    I(Opcode.LOAD, "R1", 100),
    I(Opcode.OUT, "R1"),
    I(Opcode.HALT),
]

cpu = run_program(
    "3. Memory: STORE and LOAD",
    memory_program,
)

print("Memory address 100 contains:", cpu.memory[100])
print("Output:", cpu.output_buffer)


# ============================================================================
# SECTION 9: FLAGS AND CONDITIONAL BRANCHING
# ============================================================================

comparison_program = [
    I(Opcode.MOV, "R0", 42),
    I(Opcode.MOV, "R1", 42),
    I(Opcode.CMP, "R0", "R1"),
    I(Opcode.JZ, 6),
    I(Opcode.MOV, "R2", 0),
    I(Opcode.JMP, 7),
    I(Opcode.MOV, "R2", 1),
    I(Opcode.OUT, "R2"),
    I(Opcode.HALT),
]

cpu = run_program(
    "4. Flags and Conditional Branching",
    comparison_program,
)

print("Output 1 means the comparison found equal values.")


# ============================================================================
# SECTION 10: LOOP - SUM 1 THROUGH N
# ============================================================================

# Program:
#
# R0 = counter
# R1 = accumulator
# R2 = N
#
# loop:
#   R1 = R1 + R0
#   R0 = R0 + 1
#   compare R0 with R2 + 1
#   branch while R0 <= N
#
# Since the instruction set has no JLE, we use an equality-based loop
# with a carefully selected termination condition.

sum_program = [
    I(Opcode.MOV, "R0", 1),       # 0
    I(Opcode.MOV, "R1", 0),       # 1
    I(Opcode.MOV, "R2", 11),      # 2
    I(Opcode.ADD, "R1", "R1", "R0"),  # 3
    I(Opcode.INC, "R0"),          # 4
    I(Opcode.CMP, "R0", "R2"),    # 5
    I(Opcode.JNZ, 3),             # 6
    I(Opcode.OUT, "R1"),          # 7
    I(Opcode.HALT),               # 8
]

cpu = run_program(
    "5. Loop Example: Sum 1 Through 10",
    sum_program,
)

print("Expected output:", 55)
print("Actual output:", cpu.output_buffer)


# ============================================================================
# SECTION 11: ALU EDGE CASES
# ============================================================================

print_section("6. ALU Edge Cases")

cpu = CPU(word_size=8)

# 8-bit unsigned range is 0-255.
result = cpu.alu.add(250, 10, cpu.flags)

print("8-bit 250 + 10 =", result)
print("Carry:", cpu.flags.carry)
print("Signed result:", cpu.alu.signed(result))

result = cpu.alu.add(127, 1, cpu.flags)

print("8-bit signed 127 + 1 bit pattern =", result)
print("Signed interpretation:", cpu.alu.signed(result))
print("Overflow:", cpu.flags.overflow)

result = cpu.alu.subtract(0, 1, cpu.flags)

print("8-bit 0 - 1 =", result)
print("Signed interpretation:", cpu.alu.signed(result))
print("Carry:", cpu.flags.carry)


# ============================================================================
# SECTION 12: BITWISE OPERATIONS
# ============================================================================

bitwise_program = [
    I(Opcode.MOV, "R0", 0b10101010),
    I(Opcode.MOV, "R1", 0b11001100),
    I(Opcode.AND, "R2", "R0", "R1"),
    I(Opcode.OR, "R3", "R0", "R1"),
    I(Opcode.XOR, "R4", "R0", "R1"),
    I(Opcode.NOT, "R5", "R0"),
    I(Opcode.SHL, "R6", "R0", 2),
    I(Opcode.SHR, "R7", "R0", 2),
    I(Opcode.HALT),
]

cpu = run_program(
    "7. Bitwise ALU Operations",
    bitwise_program,
)

print("R2 AND:", bin(cpu.registers[2]))
print("R3 OR :", bin(cpu.registers[3]))
print("R4 XOR:", bin(cpu.registers[4]))
print("R5 NOT:", hex(cpu.registers[5]))


# ============================================================================
# SECTION 13: STACK OPERATIONS
# ============================================================================

stack_program = [
    I(Opcode.MOV, "R0", 10),
    I(Opcode.MOV, "R1", 20),
    I(Opcode.PUSH, "R0"),
    I(Opcode.PUSH, "R1"),
    I(Opcode.POP, "R2"),
    I(Opcode.POP, "R3"),
    I(Opcode.OUT, "R2"),
    I(Opcode.OUT, "R3"),
    I(Opcode.HALT),
]

cpu = run_program(
    "8. Stack Operations",
    stack_program,
)

print(
    "The stack is LIFO: the last value pushed is the first value popped."
)
print("Output:", cpu.output_buffer)


# ============================================================================
# SECTION 14: CALL AND RET
# ============================================================================

# Main:
#   CALL function
#   OUT R0
#   HALT
#
# Function:
#   R0 = 7 * 6
#   RET
#
# CALL pushes the return PC onto the stack.
# RET pops it and restores the PC.

call_program = [
    I(Opcode.CALL, 4),                 # 0
    I(Opcode.OUT, "R0"),               # 1
    I(Opcode.HALT),                    # 2
    I(Opcode.NOP),                     # 3
    I(Opcode.MOV, "R0", 7),            # 4
    I(Opcode.MOV, "R1", 6),            # 5
    I(Opcode.MUL, "R0", "R0", "R1"),   # 6
    I(Opcode.RET),                     # 7
]

cpu = run_program(
    "9. CALL/RET and Procedure Execution",
    call_program,
)

print("Function result:", cpu.output_buffer)


# ============================================================================
# SECTION 15: INPUT / OUTPUT
# ============================================================================

io_program = [
    I(Opcode.IN, "R0"),
    I(Opcode.IN, "R1"),
    I(Opcode.ADD, "R2", "R0", "R1"),
    I(Opcode.OUT, "R2"),
    I(Opcode.HALT),
]

cpu = run_program(
    "10. Input and Output Instructions",
    io_program,
    input_values=[25, 17],
)

print("Input values:", [25, 17])
print("Output:", cpu.output_buffer)


# ============================================================================
# SECTION 16: TRACE MODE
# ============================================================================

trace_program = [
    I(Opcode.MOV, "R0", 3),
    I(Opcode.MOV, "R1", 4),
    I(Opcode.ADD, "R2", "R0", "R1"),
    I(Opcode.OUT, "R2"),
    I(Opcode.HALT),
]

run_program(
    "11. Instruction-Level Debugging With Trace Mode",
    trace_program,
    trace=True,
)


# ============================================================================
# SECTION 17: CPU VALIDATION
# ============================================================================

print_section("12. Validation and Failure Conditions")

validation_cpu = CPU()

invalid_programs = [
    (
        "Invalid register",
        [I(Opcode.MOV, "R99", 10), I(Opcode.HALT)],
    ),
    (
        "Division by zero",
        [
            I(Opcode.MOV, "R0", 10),
            I(Opcode.MOV, "R1", 0),
            I(Opcode.DIV, "R2", "R0", "R1"),
            I(Opcode.HALT),
        ],
    ),
    (
        "Stack underflow",
        [I(Opcode.POP, "R0"), I(Opcode.HALT)],
    ),
]

for description, program in invalid_programs:
    try:
        test_cpu = CPU()
        test_cpu.load_program(program)
        test_cpu.run()
    except (ValueError, RuntimeError, MemoryError, ZeroDivisionError) as error:
        print(f"{description}: correctly rejected -> {error}")


# ============================================================================
# SECTION 18: SIMPLE ASSEMBLER
# ============================================================================

class Assembler:
    """
    Converts a small textual assembly language into Instruction objects.

    Supported syntax examples:

        MOV R0, 10
        ADD R2, R0, R1
        STORE R2, 100
        JMP loop
        loop:
            INC R0
    """

    REGISTER_OPERANDS = {
        Opcode.MOV: 2,
        Opcode.LOAD: 1,
        Opcode.STORE: 1,
        Opcode.ADD: 3,
        Opcode.SUB: 3,
        Opcode.MUL: 3,
        Opcode.DIV: 3,
        Opcode.AND: 3,
        Opcode.OR: 3,
        Opcode.XOR: 3,
        Opcode.NOT: 2,
        Opcode.SHL: 3,
        Opcode.SHR: 3,
        Opcode.INC: 1,
        Opcode.DEC: 1,
        Opcode.CMP: 2,
        Opcode.JMP: 1,
        Opcode.JZ: 1,
        Opcode.JNZ: 1,
        Opcode.JN: 1,
        Opcode.JP: 1,
        Opcode.PUSH: 1,
        Opcode.POP: 1,
        Opcode.CALL: 1,
        Opcode.RET: 0,
        Opcode.IN: 1,
        Opcode.OUT: 1,
        Opcode.HALT: 0,
        Opcode.NOP: 0,
    }

    def parse_value(self, token: str):
        token = token.strip()

        if token.upper().startswith("R"):
            return token.upper()

        # int(..., 0) accepts decimal, hexadecimal, binary and octal.
        return int(token, 0)

    def first_pass(self, lines: list[str]) -> dict[str, int]:
        labels: dict[str, int] = {}
        instruction_address = 0

        for raw_line in lines:
            line = raw_line.split(";", 1)[0].strip()

            if not line:
                continue

            if ":" in line:
                label, remainder = line.split(":", 1)
                label = label.strip()

                if not label.isidentifier():
                    raise ValueError(f"Invalid label: {label}")

                if label in labels:
                    raise ValueError(f"Duplicate label: {label}")

                labels[label] = instruction_address
                line = remainder.strip()

                if not line:
                    continue

            instruction_address += 1

        return labels

    def assemble(self, source: str) -> list[Instruction]:
        lines = source.splitlines()
        labels = self.first_pass(lines)
        program: list[Instruction] = []

        for raw_line in lines:
            line = raw_line.split(";", 1)[0].strip()

            if not line:
                continue

            if ":" in line:
                _, line = line.split(":", 1)
                line = line.strip()

                if not line:
                    continue

            pieces = line.split(None, 1)
            mnemonic = pieces[0].upper()

            try:
                opcode = Opcode(mnemonic)
            except ValueError as exc:
                raise ValueError(f"Unknown opcode: {mnemonic}") from exc

            operand_text = pieces[1] if len(pieces) > 1 else ""

            operands = []
            if operand_text:
                operands = [
                    self.parse_value(token)
                    for token in operand_text.split(",")
                    if token.strip()
                ]

            expected = self.REGISTER_OPERANDS[opcode]
            if len(operands) != expected:
                raise ValueError(
                    f"{mnemonic} expects {expected} operands, "
                    f"got {len(operands)}"
                )

            # Branch and CALL operands may be labels.
            branch_opcodes = {
                Opcode.JMP,
                Opcode.JZ,
                Opcode.JNZ,
                Opcode.JN,
                Opcode.JP,
                Opcode.CALL,
            }

            if opcode in branch_opcodes:
                original = operand_text.strip()

                if not original.isdigit() and not original.startswith(("0x", "0b")):
                    if original not in labels:
                        raise ValueError(f"Undefined label: {original}")
                    operands = [labels[original]]

            program.append(Instruction(opcode, tuple(operands)))

        return program


assembly_source = """
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
"""

assembler = Assembler()
assembled_program = assembler.assemble(assembly_source)

cpu = run_program(
    "13. Text Assembly and Labels",
    assembled_program,
)

print("Assembly result:", cpu.output_buffer)


# ============================================================================
# SECTION 19: PROGRAM PERFORMANCE
# ============================================================================

print_section("14. Instruction Count and Simplified CPU Cost")

performance_program = [
    I(Opcode.MOV, "R0", 100),
    I(Opcode.MOV, "R1", 200),
    I(Opcode.ADD, "R2", "R0", "R1"),
    I(Opcode.MUL, "R3", "R2", "R1"),
    I(Opcode.STORE, "R3", 120),
    I(Opcode.LOAD, "R4", 120),
    I(Opcode.HALT),
]

cpu = CPU()
cpu.load_program(performance_program)
cpu.run()

print("Instructions executed:", cpu.instructions_executed)
print("Estimated cycles:", cpu.cycles)
print(
    "This demonstrates why instruction count alone does not necessarily "
    "represent execution time: different instructions may have different "
    "costs."
)


# ============================================================================
# SECTION 20: FACTORIAL
# ============================================================================

# Calculate 5! using repeated multiplication.
factorial_program = [
    I(Opcode.MOV, "R0", 5),            # counter
    I(Opcode.MOV, "R1", 1),            # result
    I(Opcode.MOV, "R2", 1),            # termination value
    I(Opcode.MUL, "R1", "R1", "R0"),   # loop starts here
    I(Opcode.DEC, "R0"),
    I(Opcode.CMP, "R0", "R2"),
    I(Opcode.JP, 3),
    I(Opcode.OUT, "R1"),
    I(Opcode.HALT),
]

cpu = run_program(
    "15. More Complex Algorithm: Factorial",
    factorial_program,
)

print("5! =", cpu.output_buffer[0])


# ============================================================================
# SECTION 21: CPU ARCHITECTURE OBSERVATIONS
# ============================================================================

print_section("16. Architectural Observations")

observations = [
    "The PC determines which instruction is fetched next.",
    "The IR represents the instruction currently being executed.",
    "The control unit determines which operation must occur.",
    "The ALU performs arithmetic and logical work.",
    "Registers provide fast temporary storage.",
    "Memory is larger but conceptually slower than registers.",
    "Flags allow arithmetic results to influence control flow.",
    "Branches change the normal sequential PC progression.",
    "CALL and RET demonstrate how a stack can support procedures.",
    "A CPU simulator makes hidden machine-state transitions observable.",
]

for observation in observations:
    print("-", observation)


# ============================================================================
# SECTION 22: BEST PRACTICES AND SECURITY CONSIDERATIONS
# ============================================================================

print_section("17. Simulator Design Considerations")

print(
    """
Correctness:
    Validate registers, addresses, opcodes, operands, and program targets.

Determinism:
    A simulator should produce the same machine state for the same initial
    state and program.

Bounded execution:
    A maximum instruction limit helps detect accidental infinite loops.

State isolation:
    CPU state should be encapsulated instead of allowing arbitrary mutation.

Integer width:
    Real CPUs operate at defined widths. Masking values reproduces wraparound
    behavior instead of allowing unlimited mathematical integers.

Stack safety:
    Stack overflow and underflow must be detected.

Division:
    Division by zero must produce a controlled failure.

Debugging:
    Instruction tracing and register dumps expose machine-state transitions.

Performance:
    Large programs require efficient instruction dispatch and memory access.

Security:
    A production emulator should treat loaded machine code as untrusted.
    It should impose memory, execution, and resource limits and should not
    expose host-system capabilities merely because a simulated instruction
    requests them.

Important limitation:
    This simulator is an educational ISA emulator. It does not reproduce
    modern CPU microarchitecture such as caches, pipelines, branch predictors,
    speculative execution, reorder buffers, SIMD execution, interrupts,
    privilege rings, virtual memory, or multicore coherence.
    """
)


# ============================================================================
# SECTION 23: FINAL MINI DEMONSTRATION
# ============================================================================

print_section("18. Final CPU State Demonstration")

final_program = [
    I(Opcode.MOV, "R0", 21),
    I(Opcode.MOV, "R1", 2),
    I(Opcode.MUL, "R2", "R0", "R1"),
    I(Opcode.STORE, "R2", 200),
    I(Opcode.LOAD, "R3", 200),
    I(Opcode.CMP, "R3", 42),
    I(Opcode.JZ, 8),
    I(Opcode.MOV, "R4", 0),
    I(Opcode.JMP, 9),
    I(Opcode.MOV, "R4", 1),
    I(Opcode.OUT, "R4"),
    I(Opcode.HALT),
]

final_cpu = CPU()
final_cpu.load_program(final_program)
final_cpu.run()

final_cpu.dump_state()

print(
    """
The complete execution path demonstrates the central CPU abstraction:

1. PC selects an instruction.
2. The instruction is fetched into IR.
3. The control unit interprets its opcode.
4. Operands are obtained from registers, memory, or immediates.
5. The ALU performs computation when required.
6. Flags record relevant result properties.
7. The PC advances or changes because of control flow.
8. The machine repeats until HALT.

This is the essential conceptual foundation of a CPU simulator.
"""
)
