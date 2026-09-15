"""
Computer Architecture Introduction
===================================

A self-contained study program covering:

- Computer architecture vs. computer organization
- ISA (Instruction Set Architecture)
- CPU structure
- Registers
- ALU
- Control unit
- Program counter and instruction register
- Memory hierarchy
- RAM, ROM, cache and storage
- Input/output
- Buses
- Instruction cycle
- Fetch, decode, execute, memory and write-back
- Addressing modes
- Instruction formats
- RISC and CISC
- Stack and accumulator concepts
- Interrupts
- Pipelining
- Branches and hazards
- Performance and CPI
- Endianness
- Virtual memory concepts
- Assembly-like instruction execution
- A small educational CPU simulator
- A cache simulator
- I/O simulation
- Debugging and validation
- Architecture trade-offs
- A simple Logisim-style datapath model

The program intentionally uses only the Python standard library.

Run:
    python computer_architecture_introduction.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from collections import OrderedDict, defaultdict
from typing import Callable, Dict, List, Optional, Tuple
import math
import random
import statistics
import struct


# ============================================================================
# 1. BASIC TERMINOLOGY
# ============================================================================

def section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def explain_terminology() -> None:
    section("1. Computer Architecture Terminology")

    terminology = {
        "Computer architecture":
            "The programmer-visible design of a computer system.",
        "Computer organization":
            "The internal implementation used to realize an architecture.",
        "ISA":
            "Instruction Set Architecture: the contract between software and CPU.",
        "Microarchitecture":
            "The internal CPU design used to implement an ISA.",
        "CPU":
            "Central Processing Unit: executes instructions and controls computation.",
        "ALU":
            "Arithmetic Logic Unit: performs arithmetic and logical operations.",
        "Register":
            "A very small, very fast storage location inside the CPU.",
        "Program Counter":
            "Register containing the address of the next instruction to fetch.",
        "Instruction Register":
            "Register holding the instruction currently being processed.",
        "Memory":
            "Storage directly addressable by the processor, normally organized by addresses.",
        "I/O":
            "Input and output mechanisms through which a computer communicates with devices.",
        "Bus":
            "A communication pathway carrying data, addresses, or control signals.",
        "Clock":
            "A timing signal used to coordinate synchronous CPU operations.",
        "Cache":
            "Small, fast memory that keeps frequently or recently used data near the CPU.",
        "Pipeline":
            "A technique that overlaps different stages of multiple instructions.",
    }

    for term, definition in terminology.items():
        print(f"{term:24} : {definition}")


# ============================================================================
# 2. ARCHITECTURE VS ORGANIZATION
# ============================================================================

def architecture_vs_organization() -> None:
    section("2. Architecture vs. Organization")

    architecture_examples = [
        ("ISA", "What instructions exist?"),
        ("Registers", "Which programmer-visible registers exist?"),
        ("Data types", "What integer/address sizes are supported?"),
        ("Addressing", "How does software specify operands?"),
        ("Memory model", "How are memory accesses defined?"),
    ]

    organization_examples = [
        ("Pipeline", "How many internal stages execute instructions?"),
        ("Cache", "How is cache arranged and sized?"),
        ("Branch predictor", "How are branches predicted internally?"),
        ("Execution units", "How many ALUs or functional units exist?"),
        ("Clock implementation", "How are timing and synchronization implemented?"),
    ]

    print("Architecture is primarily the programmer-visible specification.")
    print("Organization is primarily how hardware implements that specification.")

    print("\nArchitecture examples:")
    for item, question in architecture_examples:
        print(f"  {item:18} -> {question}")

    print("\nOrganization examples:")
    for item, question in organization_examples:
        print(f"  {item:18} -> {question}")

    print(
        "\nTwo processors can implement the same ISA while using very different "
        "microarchitectures."
    )


# ============================================================================
# 3. BINARY, HEXADECIMAL AND TWO'S COMPLEMENT
# ============================================================================

def binary_and_integer_representation() -> None:
    section("3. Binary, Hexadecimal and Integer Representation")

    values = [0, 1, 2, 10, 42, 127, 128, 255]

    for value in values:
        print(
            f"{value:3} decimal = "
            f"{value:08b} binary = "
            f"0x{value:02X} hexadecimal"
        )

    def to_signed(value: int, bits: int) -> int:
        """Interpret an unsigned bit pattern as a two's-complement integer."""
        mask = 1 << (bits - 1)
        if value & mask:
            return value - (1 << bits)
        return value

    print("\n8-bit two's-complement interpretation:")
    for raw in [0, 1, 127, 128, 129, 254, 255]:
        print(f"0b{raw:08b} -> {to_signed(raw, 8):4}")

    print("\nImportant 8-bit signed range:")
    print("Minimum:", -(2 ** 7))
    print("Maximum:", 2 ** 7 - 1)

    def add_fixed_width(a: int, b: int, bits: int) -> int:
        """Perform integer addition with fixed-width wraparound."""
        mask = (1 << bits) - 1
        return (a + b) & mask

    print("\n8-bit wraparound:")
    print("250 + 10 =", add_fixed_width(250, 10, 8), "(unsigned representation)")


# ============================================================================
# 4. LOGICAL CPU COMPONENTS
# ============================================================================

@dataclass
class Register:
    name: str
    width: int
    value: int = 0

    def write(self, value: int) -> None:
        mask = (1 << self.width) - 1
        self.value = value & mask

    def read(self) -> int:
        return self.value


class ALU:
    """A small educational arithmetic and logic unit."""

    def add(self, a: int, b: int) -> Tuple[int, bool]:
        result = a + b
        overflow = result > 0xFF
        return result & 0xFF, overflow

    def subtract(self, a: int, b: int) -> Tuple[int, bool]:
        result = a - b
        borrow = result < 0
        return result & 0xFF, borrow

    def and_op(self, a: int, b: int) -> int:
        return a & b

    def or_op(self, a: int, b: int) -> int:
        return a | b

    def xor_op(self, a: int, b: int) -> int:
        return a ^ b

    def shift_left(self, value: int, amount: int) -> int:
        return (value << amount) & 0xFF

    def shift_right(self, value: int, amount: int) -> int:
        return (value & 0xFF) >> amount


def demonstrate_cpu_components() -> None:
    section("4. CPU Components")

    accumulator = Register("ACC", 8)
    temporary = Register("TMP", 8)
    pc = Register("PC", 8)
    ir = Register("IR", 8)

    alu = ALU()

    accumulator.write(100)
    temporary.write(50)

    result, carry = alu.add(accumulator.read(), temporary.read())

    print("Registers:")
    for register in [accumulator, temporary, pc, ir]:
        print(f"  {register.name}: {register.read()}")

    print("\nALU:")
    print("  100 + 50 =", result)
    print("  carry =", carry)
    print("  0b10101010 AND 0b11001100 =",
          bin(alu.and_op(0b10101010, 0b11001100)))
    print("  0b10101010 OR  0b11001100 =",
          bin(alu.or_op(0b10101010, 0b11001100)))
    print("  0b10101010 XOR 0b11001100 =",
          bin(alu.xor_op(0b10101010, 0b11001100)))


# ============================================================================
# 5. MEMORY MODEL
# ============================================================================

class Memory:
    """Byte-addressable memory with explicit bounds checking."""

    def __init__(self, size: int):
        if size <= 0:
            raise ValueError("Memory size must be positive.")
        self.size = size
        self.data = bytearray(size)

    def _validate_address(self, address: int) -> None:
        if not 0 <= address < self.size:
            raise IndexError(f"Memory address out of range: {address}")

    def read_byte(self, address: int) -> int:
        self._validate_address(address)
        return self.data[address]

    def write_byte(self, address: int, value: int) -> None:
        self._validate_address(address)
        if not 0 <= value <= 255:
            raise ValueError("A byte must be between 0 and 255.")
        self.data[address] = value

    def read_word(self, address: int, little_endian: bool = True) -> int:
        if address < 0 or address + 1 >= self.size:
            raise IndexError("16-bit word access is outside memory.")
        first = self.read_byte(address)
        second = self.read_byte(address + 1)
        if little_endian:
            return first | (second << 8)
        return (first << 8) | second

    def write_word(
        self,
        address: int,
        value: int,
        little_endian: bool = True,
    ) -> None:
        if not 0 <= value <= 0xFFFF:
            raise ValueError("A 16-bit word must fit into 16 bits.")
        if address < 0 or address + 1 >= self.size:
            raise IndexError("16-bit word access is outside memory.")

        low = value & 0xFF
        high = (value >> 8) & 0xFF

        if little_endian:
            self.write_byte(address, low)
            self.write_byte(address + 1, high)
        else:
            self.write_byte(address, high)
            self.write_byte(address + 1, low)

    def dump(self, start: int, end: int) -> None:
        for address in range(start, min(end, self.size)):
            print(f"{address:04X}: {self.data[address]:02X}")


def demonstrate_memory() -> None:
    section("5. Memory and Endianness")

    memory = Memory(32)
    memory.write_word(4, 0x1234, little_endian=True)

    print("Little-endian bytes for 0x1234:")
    memory.dump(4, 6)

    memory.write_word(8, 0x1234, little_endian=False)

    print("\nBig-endian bytes for 0x1234:")
    memory.dump(8, 10)

    print("\nReading values:")
    print("Little endian:", hex(memory.read_word(4, True)))
    print("Big endian:", hex(memory.read_word(8, False)))

    try:
        memory.read_byte(100)
    except IndexError as error:
        print("\nExpected memory error:", error)


# ============================================================================
# 6. INSTRUCTION SET ARCHITECTURE
# ============================================================================

class Opcode(Enum):
    NOP = 0x00
    LOAD_IMM = 0x10
    LOAD = 0x11
    STORE = 0x12
    ADD = 0x20
    SUB = 0x21
    AND = 0x22
    OR = 0x23
    XOR = 0x24
    SHL = 0x25
    SHR = 0x26
    JMP = 0x30
    JZ = 0x31
    CMP = 0x32
    IN = 0x40
    OUT = 0x41
    HALT = 0xFF


@dataclass
class Instruction:
    opcode: Opcode
    operand: int = 0

    def encode(self) -> int:
        return (self.opcode.value << 8) | (self.operand & 0xFF)

    @staticmethod
    def decode(word: int) -> "Instruction":
        opcode_value = (word >> 8) & 0xFF
        operand = word & 0xFF

        try:
            opcode = Opcode(opcode_value)
        except ValueError as error:
            raise ValueError(f"Unknown opcode: 0x{opcode_value:02X}") from error

        return Instruction(opcode, operand)

    def __str__(self) -> str:
        if self.operand:
            return f"{self.opcode.name} {self.operand}"
        return self.opcode.name


# ============================================================================
# 7. I/O DEVICES
# ============================================================================

class InputDevice:
    """Simple memory-mapped-style input abstraction."""

    def __init__(self, values: List[int]):
        self.values = list(values)

    def read(self) -> int:
        if not self.values:
            raise RuntimeError("Input device has no data available.")
        return self.values.pop(0)


class OutputDevice:
    def __init__(self):
        self.values: List[int] = []

    def write(self, value: int) -> None:
        self.values.append(value & 0xFF)
        print(f"[OUTPUT DEVICE] {value & 0xFF}")


# ============================================================================
# 8. EDUCATIONAL CPU
# ============================================================================

class CPU:
    """
    A small 8-bit accumulator CPU.

    Instruction format:
        16-bit instruction
        high byte = opcode
        low byte  = operand/address/immediate

    Registers:
        PC  - program counter
        IR  - instruction register
        ACC - accumulator
        MAR - memory address register
        MDR - memory data register
        FLAGS.Z - zero flag
        FLAGS.C - carry/borrow flag
    """

    def __init__(self, memory_size: int = 256):
        self.memory = Memory(memory_size)
        self.pc = Register("PC", 8)
        self.ir = Register("IR", 16)
        self.acc = Register("ACC", 8)
        self.mar = Register("MAR", 8)
        self.mdr = Register("MDR", 8)

        self.zero_flag = False
        self.carry_flag = False
        self.halted = False
        self.cycles = 0
        self.instructions_executed = 0

        self.input_device = InputDevice([])
        self.output_device = OutputDevice()

    def load_program(self, program: List[Instruction], start: int = 0) -> None:
        address = start
        for instruction in program:
            if address + 1 >= self.memory.size:
                raise MemoryError("Program does not fit into memory.")

            encoded = instruction.encode()
            self.memory.write_word(address, encoded, little_endian=False)
            address += 2

        self.pc.write(start)
        self.halted = False

    def fetch(self) -> Instruction:
        """Fetch stage: read instruction pointed to by PC."""
        self.mar.write(self.pc.read())

        word = self.memory.read_word(self.mar.read(), little_endian=False)
        self.mdr.write(word & 0xFF)

        self.ir.write(word)
        self.pc.write(self.pc.read() + 2)

        return Instruction.decode(word)

    def update_flags(self, result: int, carry: bool = False) -> None:
        self.zero_flag = (result & 0xFF) == 0
        self.carry_flag = carry

    def execute(self, instruction: Instruction) -> None:
        """Decode/execute stage for the educational instruction set."""

        opcode = instruction.opcode
        operand = instruction.operand

        if opcode == Opcode.NOP:
            return

        if opcode == Opcode.LOAD_IMM:
            self.acc.write(operand)
            self.update_flags(self.acc.read())
            return

        if opcode == Opcode.LOAD:
            self.acc.write(self.memory.read_byte(operand))
            self.update_flags(self.acc.read())
            return

        if opcode == Opcode.STORE:
            self.memory.write_byte(operand, self.acc.read())
            return

        if opcode == Opcode.ADD:
            result, carry = ALU().add(
                self.acc.read(),
                self.memory.read_byte(operand),
            )
            self.acc.write(result)
            self.update_flags(result, carry)
            return

        if opcode == Opcode.SUB:
            result, borrow = ALU().subtract(
                self.acc.read(),
                self.memory.read_byte(operand),
            )
            self.acc.write(result)
            self.update_flags(result, borrow)
            return

        if opcode == Opcode.AND:
            result = ALU().and_op(
                self.acc.read(),
                self.memory.read_byte(operand),
            )
            self.acc.write(result)
            self.update_flags(result)
            return

        if opcode == Opcode.OR:
            result = ALU().or_op(
                self.acc.read(),
                self.memory.read_byte(operand),
            )
            self.acc.write(result)
            self.update_flags(result)
            return

        if opcode == Opcode.XOR:
            result = ALU().xor_op(
                self.acc.read(),
                self.memory.read_byte(operand),
            )
            self.acc.write(result)
            self.update_flags(result)
            return

        if opcode == Opcode.SHL:
            result = ALU().shift_left(self.acc.read(), operand)
            self.acc.write(result)
            self.update_flags(result)
            return

        if opcode == Opcode.SHR:
            result = ALU().shift_right(self.acc.read(), operand)
            self.acc.write(result)
            self.update_flags(result)
            return

        if opcode == Opcode.JMP:
            self.pc.write(operand)
            return

        if opcode == Opcode.JZ:
            if self.zero_flag:
                self.pc.write(operand)
            return

        if opcode == Opcode.CMP:
            difference = (
                self.acc.read() - self.memory.read_byte(operand)
            ) & 0xFF
            self.zero_flag = difference == 0
            return

        if opcode == Opcode.IN:
            self.acc.write(self.input_device.read())
            self.update_flags(self.acc.read())
            return

        if opcode == Opcode.OUT:
            self.output_device.write(self.acc.read())
            return

        if opcode == Opcode.HALT:
            self.halted = True
            return

        raise RuntimeError(f"Unsupported instruction: {opcode}")

    def step(self, trace: bool = False) -> None:
        if self.halted:
            return

        old_pc = self.pc.read()
        instruction = self.fetch()

        if trace:
            print(
                f"cycle={self.cycles + 1:03} "
                f"PC={old_pc:03} "
                f"IR={instruction}"
            )

        self.execute(instruction)

        self.cycles += 1
        self.instructions_executed += 1

    def run(self, max_cycles: int = 1000, trace: bool = False) -> None:
        while not self.halted:
            if self.cycles >= max_cycles:
                raise RuntimeError(
                    "Execution stopped because the cycle limit was reached."
                )
            self.step(trace=trace)

    def dump_registers(self) -> None:
        print(
            f"PC={self.pc.read():03} "
            f"IR=0x{self.ir.read():04X} "
            f"ACC={self.acc.read():03} "
            f"MAR={self.mar.read():03} "
            f"MDR={self.mdr.read():03} "
            f"Z={int(self.zero_flag)} "
            f"C={int(self.carry_flag)}"
        )


def demonstrate_cpu() -> None:
    section("8. Instruction Cycle with a Small CPU")

    cpu = CPU()

    # Store constants in memory.
    cpu.memory.write_byte(200, 25)
    cpu.memory.write_byte(201, 17)

    # Program:
    #   LOAD address 200
    #   ADD address 201
    #   STORE address 202
    #   OUT
    #   HALT
    #
    # Instruction addresses increase by two because each instruction is 16 bits.
    program = [
        Instruction(Opcode.LOAD, 200),
        Instruction(Opcode.ADD, 201),
        Instruction(Opcode.STORE, 202),
        Instruction(Opcode.OUT),
        Instruction(Opcode.HALT),
    ]

    cpu.load_program(program)
    cpu.run(trace=True)

    print("\nFinal registers:")
    cpu.dump_registers()
    print("Memory[202] =", cpu.memory.read_byte(202))
    print("Cycles =", cpu.cycles)


# ============================================================================
# 9. CONDITIONAL CONTROL FLOW
# ============================================================================

def demonstrate_control_flow() -> None:
    section("9. Conditional Control Flow")

    cpu = CPU()

    # This program computes 7 + 5.
    cpu.memory.write_byte(200, 7)
    cpu.memory.write_byte(201, 5)

    program = [
        Instruction(Opcode.LOAD, 200),
        Instruction(Opcode.ADD, 201),
        Instruction(Opcode.STORE, 202),
        Instruction(Opcode.OUT),
        Instruction(Opcode.HALT),
    ]

    cpu.load_program(program)
    cpu.run()

    print("Expected result:", 12)
    print("Actual result:", cpu.memory.read_byte(202))

    # Demonstrate a comparison and conditional jump.
    cpu = CPU()
    cpu.memory.write_byte(200, 9)

    program = [
        Instruction(Opcode.LOAD_IMM, 9),  # address 0
        Instruction(Opcode.CMP, 200),     # address 2
        Instruction(Opcode.JZ, 8),        # address 4
        Instruction(Opcode.LOAD_IMM, 0),  # address 6
        Instruction(Opcode.LOAD_IMM, 1),  # address 8
        Instruction(Opcode.OUT),          # address 10
        Instruction(Opcode.HALT),         # address 12
    ]

    cpu.load_program(program)
    cpu.run()

    print("Conditional branch output:", cpu.output_device.values)


# ============================================================================
# 10. ADDRESSING MODES
# ============================================================================

def explain_addressing_modes() -> None:
    section("10. Addressing Modes")

    modes = [
        ("Immediate", "Operand is contained inside instruction", "LOAD_IMM 42"),
        ("Direct", "Instruction contains memory address", "LOAD 200"),
        ("Register", "Operand is stored in a CPU register", "ADD R1"),
        ("Indirect", "Register contains address of operand", "LOAD [R1]"),
        ("Indexed", "Base address plus index", "LOAD [R1 + R2]"),
        ("Relative", "Address is relative to PC", "BRANCH +12"),
        ("Stack", "Operand is implicitly on stack", "PUSH R1"),
    ]

    for name, meaning, example in modes:
        print(f"{name:12} | {meaning:48} | {example}")

    print(
        "\nAddressing modes affect instruction encoding, compiler design, "
        "code size, hardware complexity and execution behavior."
    )


# ============================================================================
# 11. RISC VS CISC
# ============================================================================

def compare_risc_and_cisc() -> None:
    section("11. RISC and CISC")

    comparison = [
        ("Instruction philosophy", "Generally simpler", "Can include complex instructions"),
        ("Instruction length", "Often regular", "Often variable"),
        ("Memory operations", "Often load/store", "May allow memory operands"),
        ("Decoding", "Typically simpler", "Can be more complex"),
        ("Code density", "Can require more instructions", "Can achieve compact code"),
        ("Hardware complexity", "Often shifted toward simpler datapaths", "Can require complex decoding"),
    ]

    print(f"{'Characteristic':22} | {'RISC':34} | {'CISC':34}")
    print("-" * 96)
    for characteristic, risc, cisc in comparison:
        print(f"{characteristic:22} | {risc:34} | {cisc:34}")

    print(
        "\nRISC and CISC are design philosophies rather than a simple "
        "fast-versus-slow classification."
    )


# ============================================================================
# 12. CACHE SIMULATOR
# ============================================================================

class DirectMappedCache:
    """
    Minimal direct-mapped cache.

    Address is divided into:
        tag | index | block offset

    This model uses one byte per cache line for simplicity.
    """

    def __init__(self, number_of_lines: int = 4):
        if number_of_lines <= 0:
            raise ValueError("Cache must have at least one line.")
        self.number_of_lines = number_of_lines
        self.lines: List[Optional[Tuple[int, int]]] = [
            None
        ] * number_of_lines
        self.hits = 0
        self.misses = 0

    def access(self, address: int) -> str:
        if address < 0:
            raise ValueError("Address cannot be negative.")

        index = address % self.number_of_lines
        tag = address // self.number_of_lines
        line = self.lines[index]

        if line is not None and line[0] == tag:
            self.hits += 1
            return "HIT"

        self.misses += 1
        self.lines[index] = (tag, address)
        return "MISS"

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total else 0.0


def demonstrate_cache() -> None:
    section("12. Cache Behavior")

    cache = DirectMappedCache(number_of_lines=4)
    addresses = [0, 1, 2, 3, 0, 1, 4, 0, 8, 0]

    for address in addresses:
        print(f"Address {address:2} -> {cache.access(address)}")

    print(f"\nHits: {cache.hits}")
    print(f"Misses: {cache.misses}")
    print(f"Hit rate: {cache.hit_rate:.2%}")

    print(
        "\nA cache improves average access time when programs exhibit locality."
    )
    print("Temporal locality: recently used data may be used again.")
    print("Spatial locality: nearby addresses may be used soon.")


# ============================================================================
# 13. MEMORY HIERARCHY
# ============================================================================

def explain_memory_hierarchy() -> None:
    section("13. Memory Hierarchy")

    hierarchy = [
        ("Registers", "Smallest / fastest", "Inside CPU"),
        ("L1 cache", "Very fast", "Near execution units"),
        ("L2 cache", "Fast", "Larger than L1"),
        ("L3 cache", "Larger / slower", "Often shared"),
        ("RAM", "Much larger / slower", "Main memory"),
        ("SSD/HDD", "Very large / persistent", "Secondary storage"),
    ]

    for level, characteristic, location in hierarchy:
        print(f"{level:14} | {characteristic:22} | {location}")

    print(
        "\nThe hierarchy exists because fast storage is expensive in area, "
        "power and hardware resources, while large storage is comparatively slower."
    )


# ============================================================================
# 14. I/O AND INTERRUPTS
# ============================================================================

@dataclass
class InterruptController:
    pending: List[str] = field(default_factory=list)

    def raise_interrupt(self, source: str) -> None:
        self.pending.append(source)

    def next_interrupt(self) -> Optional[str]:
        if not self.pending:
            return None
        return self.pending.pop(0)


def demonstrate_io_and_interrupts() -> None:
    section("14. I/O and Interrupts")

    controller = InterruptController()

    controller.raise_interrupt("keyboard")
    controller.raise_interrupt("timer")
    controller.raise_interrupt("network")

    while True:
        interrupt = controller.next_interrupt()
        if interrupt is None:
            break
        print("CPU servicing interrupt from:", interrupt)

    print(
        "\nAn interrupt allows hardware to request CPU attention instead of "
        "requiring the CPU to continuously poll every device."
    )


# ============================================================================
# 15. PERFORMANCE MODEL
# ============================================================================

def cpu_execution_time(
    instruction_count: int,
    average_cpi: float,
    clock_frequency_hz: float,
) -> float:
    """
    CPU time = instruction count * CPI / clock frequency.
    """
    if instruction_count < 0:
        raise ValueError("Instruction count cannot be negative.")
    if average_cpi <= 0:
        raise ValueError("CPI must be positive.")
    if clock_frequency_hz <= 0:
        raise ValueError("Clock frequency must be positive.")

    return instruction_count * average_cpi / clock_frequency_hz


def demonstrate_performance() -> None:
    section("15. Performance and CPI")

    instruction_count = 1_000_000
    cpi = 1.5
    frequency = 3_000_000_000

    time_seconds = cpu_execution_time(
        instruction_count,
        cpi,
        frequency,
    )

    print("Instruction count:", instruction_count)
    print("Average CPI:", cpi)
    print("Clock frequency:", frequency, "Hz")
    print("Estimated CPU time:", time_seconds, "seconds")

    print("\nPerformance observations:")
    print("- Higher clock frequency can reduce time when other factors remain equal.")
    print("- Lower CPI can reduce execution time.")
    print("- Reducing instruction count can also improve performance.")
    print("- Memory stalls, branch mispredictions and cache misses affect effective CPI.")


# ============================================================================
# 16. PIPELINING MODEL
# ============================================================================

def pipeline_timeline(
    instructions: int,
    stages: Tuple[str, ...] = ("IF", "ID", "EX", "MEM", "WB"),
) -> List[List[str]]:
    """
    Construct a simple idealized pipeline schedule.

    This is an educational model and ignores structural/data/control hazards.
    """
    if instructions <= 0:
        return []

    timeline: List[List[str]] = []

    for instruction_number in range(instructions):
        row = [""] * (instructions + len(stages) - 1)
        start = instruction_number
        for stage_offset, stage in enumerate(stages):
            row[start + stage_offset] = stage
        timeline.append(row)

    return timeline


def demonstrate_pipelining() -> None:
    section("16. Instruction Pipelining")

    timeline = pipeline_timeline(5)

    print("     " + " ".join(f"C{i + 1:>3}" for i in range(len(timeline[0]))))
    for number, row in enumerate(timeline, 1):
        print(f"I{number:<3} " + " ".join(f"{x:>3}" for x in row))

    print(
        "\nIdeal pipeline throughput improves because multiple instructions "
        "occupy different stages at the same time."
    )

    print("\nImportant hazards:")
    print("  Data hazard      -> instruction depends on earlier instruction.")
    print("  Control hazard   -> branch changes the instruction stream.")
    print("  Structural hazard -> hardware resources conflict.")


# ============================================================================
# 17. STACK MACHINE
# ============================================================================

class StackMachine:
    """A small stack-based virtual machine."""

    def __init__(self):
        self.stack: List[int] = []

    def push(self, value: int) -> None:
        self.stack.append(value)

    def pop(self) -> int:
        if not self.stack:
            raise RuntimeError("Stack underflow.")
        return self.stack.pop()

    def add(self) -> None:
        right = self.pop()
        left = self.pop()
        self.push(left + right)

    def multiply(self) -> None:
        right = self.pop()
        left = self.pop()
        self.push(left * right)

    def top(self) -> int:
        if not self.stack:
            raise RuntimeError("Stack is empty.")
        return self.stack[-1]


def demonstrate_stack_machine() -> None:
    section("17. Stack-Based Execution")

    machine = StackMachine()

    # Evaluate: (2 + 3) * 4
    machine.push(2)
    machine.push(3)
    machine.add()
    machine.push(4)
    machine.multiply()

    print("Expression: (2 + 3) * 4")
    print("Result:", machine.top())

    try:
        machine.pop()
        machine.pop()
    except RuntimeError as error:
        print("Expected stack error:", error)


# ============================================================================
# 18. SIMPLE ASSEMBLER
# ============================================================================

class Assembler:
    """
    Converts a tiny assembly language into Instruction objects.

    Supported syntax:
        LOAD_IMM 10
        LOAD 200
        ADD 201
        STORE 202
        OUT
        HALT
    """

    def __init__(self):
        self.opcodes = {
            name: opcode for name, opcode in Opcode.__members__.items()
        }

    def assemble_line(self, line: str) -> Optional[Instruction]:
        line = line.split("#", 1)[0].strip()

        if not line:
            return None

        tokens = line.replace(",", " ").split()
        mnemonic = tokens[0].upper()

        if mnemonic not in self.opcodes:
            raise ValueError(f"Unknown mnemonic: {mnemonic}")

        opcode = self.opcodes[mnemonic]

        if len(tokens) == 1:
            operand = 0
        elif len(tokens) == 2:
            operand_text = tokens[1]
            operand = int(operand_text, 0)
            if not 0 <= operand <= 255:
                raise ValueError("Operand must fit in 8 bits.")
        else:
            raise ValueError(f"Invalid instruction: {line}")

        return Instruction(opcode, operand)

    def assemble(self, source: str) -> List[Instruction]:
        program = []

        for line_number, line in enumerate(source.splitlines(), 1):
            try:
                instruction = self.assemble_line(line)
            except ValueError as error:
                raise ValueError(
                    f"Assembly error on line {line_number}: {error}"
                ) from error

            if instruction is not None:
                program.append(instruction)

        return program


def demonstrate_assembler() -> None:
    section("18. Assembly-Like Programming")

    source = """
        # Add two values stored in memory.
        LOAD 200
        ADD 201
        STORE 202
        OUT
        HALT
    """

    assembler = Assembler()
    program = assembler.assemble(source)

    for address, instruction in enumerate(program):
        print(f"{address * 2:04X}: {instruction}")

    cpu = CPU()
    cpu.memory.write_byte(200, 30)
    cpu.memory.write_byte(201, 12)
    cpu.load_program(program)
    cpu.run()

    print("Stored result:", cpu.memory.read_byte(202))


# ============================================================================
# 19. LOGISIM-STYLE DATAPATH
# ============================================================================

@dataclass
class ControlSignals:
    reg_write: bool = False
    alu_operation: str = "NONE"
    memory_read: bool = False
    memory_write: bool = False
    branch: bool = False


@dataclass
class Datapath:
    register_file: List[int] = field(
        default_factory=lambda: [0] * 4
    )
    alu: ALU = field(default_factory=ALU)

    def execute_alu(
        self,
        source_a: int,
        source_b: int,
        operation: str,
    ) -> int:
        operations: Dict[str, Callable[[int, int], int]] = {
            "ADD": lambda a, b: (a + b) & 0xFF,
            "SUB": lambda a, b: (a - b) & 0xFF,
            "AND": lambda a, b: a & b,
            "OR": lambda a, b: a | b,
            "XOR": lambda a, b: a ^ b,
        }

        if operation not in operations:
            raise ValueError(f"Unsupported ALU operation: {operation}")

        return operations[operation](source_a, source_b)

    def write_register(self, index: int, value: int) -> None:
        if not 0 <= index < len(self.register_file):
            raise IndexError("Register index out of range.")
        self.register_file[index] = value & 0xFF


def demonstrate_datapath() -> None:
    section("19. Logisim-Style Datapath")

    datapath = Datapath()
    datapath.register_file[0] = 14
    datapath.register_file[1] = 28

    control = ControlSignals(
        reg_write=True,
        alu_operation="ADD",
    )

    if control.reg_write:
        result = datapath.execute_alu(
            datapath.register_file[0],
            datapath.register_file[1],
            control.alu_operation,
        )
        datapath.write_register(2, result)

    print("Registers:", datapath.register_file)
    print(
        "\nA Logisim-style circuit can represent the same logical flow using "
        "registers, multiplexers, ALUs, control signals, clocks and buses."
    )


# ============================================================================
# 20. VIRTUAL MEMORY CONCEPT
# ============================================================================

@dataclass
class PageTableEntry:
    virtual_page: int
    physical_frame: int
    present: bool = True


class SimplePageTable:
    """Educational virtual-to-physical address translation."""

    def __init__(self):
        self.entries: Dict[int, PageTableEntry] = {}

    def map_page(self, virtual_page: int, physical_frame: int) -> None:
        self.entries[virtual_page] = PageTableEntry(
            virtual_page,
            physical_frame,
            True,
        )

    def translate(self, virtual_address: int, page_size: int = 16) -> int:
        if virtual_address < 0:
            raise ValueError("Virtual address cannot be negative.")

        virtual_page = virtual_address // page_size
        offset = virtual_address % page_size

        entry = self.entries.get(virtual_page)

        if entry is None or not entry.present:
            raise MemoryError("Page fault: page is not mapped.")

        return entry.physical_frame * page_size + offset


def demonstrate_virtual_memory() -> None:
    section("20. Virtual Memory")

    page_table = SimplePageTable()
    page_table.map_page(0, 5)
    page_table.map_page(1, 2)

    virtual_addresses = [0, 3, 16, 20]

    for address in virtual_addresses:
        try:
            physical = page_table.translate(address)
            print(f"Virtual {address:3} -> Physical {physical:3}")
        except MemoryError as error:
            print(f"Virtual {address:3} -> {error}")

    print(
        "\nReal systems use much more sophisticated page tables, translation "
        "lookaside buffers, protection bits and operating-system page management."
    )


# ============================================================================
# 21. BOOLEAN LOGIC
# ============================================================================

def demonstrate_logic_gates() -> None:
    section("21. Digital Logic Foundations")

    bit_values = [0, 1]

    print("A B | AND OR XOR")
    print("----------------")
    for a in bit_values:
        for b in bit_values:
            print(f"{a} {b} |  {a & b}   {a | b}   {a ^ b}")

    print("\nNOT gate:")
    for value in bit_values:
        print(f"NOT {value} -> {1 - value}")

    print(
        "\nCPUs are constructed from digital logic. Larger structures such as "
        "adders, multiplexers, decoders, registers and ALUs are built from these concepts."
    )


# ============================================================================
# 22. TESTING
# ============================================================================

def run_tests() -> None:
    section("22. Self-Tests")

    memory = Memory(16)
    memory.write_byte(5, 123)
    assert memory.read_byte(5) == 123

    memory.write_word(6, 0xBEEF, little_endian=False)
    assert memory.read_word(6, little_endian=False) == 0xBEEF

    alu = ALU()
    result, carry = alu.add(200, 100)
    assert result == 44
    assert carry is True

    assembler = Assembler()
    instruction = assembler.assemble_line("LOAD_IMM 42")
    assert instruction is not None
    assert instruction.opcode == Opcode.LOAD_IMM
    assert instruction.operand == 42

    cpu = CPU()
    cpu.memory.write_byte(200, 10)
    cpu.memory.write_byte(201, 20)
    cpu.load_program(
        [
            Instruction(Opcode.LOAD, 200),
            Instruction(Opcode.ADD, 201),
            Instruction(Opcode.STORE, 202),
            Instruction(Opcode.HALT),
        ]
    )
    cpu.run()
    assert cpu.memory.read_byte(202) == 30

    cache = DirectMappedCache(2)
    assert cache.access(0) == "MISS"
    assert cache.access(0) == "HIT"

    print("All self-tests passed.")


# ============================================================================
# 23. EDGE CASES AND FAILURE MODES
# ============================================================================

def demonstrate_edge_cases() -> None:
    section("23. Edge Cases and Failure Modes")

    cases = [
        ("Invalid memory address", lambda: Memory(4).read_byte(10)),
        ("Invalid byte value", lambda: Memory(4).write_byte(0, 300)),
        ("Unknown instruction", lambda: Instruction.decode(0x9900)),
        ("Stack underflow", lambda: StackMachine().pop()),
        ("Invalid assembly", lambda: Assembler().assemble_line("UNKNOWN 1")),
        ("Unmapped virtual page", lambda: SimplePageTable().translate(100)),
    ]

    for description, operation in cases:
        try:
            operation()
        except (IndexError, ValueError, RuntimeError, MemoryError) as error:
            print(f"{description:25} -> handled: {error}")


# ============================================================================
# 24. SIMPLE BRANCH-PREDICTION MODEL
# ============================================================================

class OneBitBranchPredictor:
    """
    A minimal one-bit predictor.

    True  = predict taken
    False = predict not taken
    """

    def __init__(self):
        self.state: Dict[int, bool] = {}

    def predict(self, branch_address: int) -> bool:
        return self.state.get(branch_address, False)

    def update(self, branch_address: int, actually_taken: bool) -> None:
        self.state[branch_address] = actually_taken


def demonstrate_branch_prediction() -> None:
    section("24. Branch Prediction")

    predictor = OneBitBranchPredictor()
    outcomes = [True, True, True, False, True, True, False]

    correct = 0

    for cycle, outcome in enumerate(outcomes, 1):
        prediction = predictor.predict(100)
        if prediction == outcome:
            correct += 1

        print(
            f"Branch {cycle}: predicted={prediction}, actual={outcome}"
        )

        predictor.update(100, outcome)

    print(f"Prediction accuracy: {correct / len(outcomes):.2%}")

    print(
        "\nModern CPUs use substantially more sophisticated predictors, "
        "but the fundamental objective is the same: reduce control-hazard cost."
    )


# ============================================================================
# 25. PRODUCTION DESIGN CONSIDERATIONS
# ============================================================================

def explain_production_considerations() -> None:
    section("25. Design, Security and Production Considerations")

    considerations = [
        "Correctness: instruction behavior must conform to the ISA specification.",
        "Reliability: hardware must handle faults, invalid states and exceptional conditions.",
        "Performance: caches, pipelines, branch prediction and execution width affect throughput.",
        "Power: voltage, frequency, switching activity and memory accesses influence energy usage.",
        "Security: speculative execution, privilege levels, memory protection and isolation matter.",
        "Compatibility: software depends on stable architectural contracts.",
        "Verification: CPU implementations require extensive simulation and hardware validation.",
        "Observability: tracing and performance counters help diagnose architectural behavior.",
        "Scalability: multicore systems introduce synchronization, cache coherence and memory-ordering issues.",
        "Maintainability: clean separation between ISA specification and implementation simplifies evolution.",
    ]

    for item in considerations:
        print("-", item)


# ============================================================================
# 26. MINI ARCHITECTURE COMPARISON
# ============================================================================

def compare_machine_models() -> None:
    section("26. Architectural Models")

    models = {
        "Accumulator": "Many operations implicitly use one accumulator register.",
        "Stack": "Operands are implicitly taken from a stack.",
        "Register-memory": "Instructions may combine registers and memory operands.",
        "Load-store": "Arithmetic generally operates on registers; memory uses explicit load/store.",
    }

    for model, description in models.items():
        print(f"{model:18} -> {description}")

    print(
        "\nThe choice influences instruction encoding, compiler strategy, "
        "hardware complexity and code density."
    )


# ============================================================================
# 27. SIMPLE PERFORMANCE EXPERIMENT
# ============================================================================

def performance_experiment() -> None:
    section("27. Locality Experiment")

    size = 100_000
    sequential = list(range(size))

    random_addresses = sequential.copy()
    random.shuffle(random_addresses)

    sequential_unique_pages = len({x // 16 for x in sequential})
    random_unique_pages = len({x // 16 for x in random_addresses})

    print("Sequential accesses:", len(sequential))
    print("Randomized accesses:", len(random_addresses))
    print("Unique 16-byte pages in sequential pattern:",
          sequential_unique_pages)
    print("Unique 16-byte pages in randomized pattern:",
          random_unique_pages)

    print(
        "\nThe number of unique pages is the same here, but the temporal and "
        "spatial order of accesses strongly influences cache and TLB behavior."
    )


# ============================================================================
# 28. STUDY CHECK
# ============================================================================

def knowledge_check() -> None:
    section("28. Knowledge Check")

    questions = [
        (
            "Which component performs arithmetic and logic?",
            "ALU",
        ),
        (
            "Which register normally identifies the next instruction?",
            "PC",
        ),
        (
            "What does ISA stand for?",
            "Instruction Set Architecture",
        ),
        (
            "What is the purpose of cache?",
            "Reduce average memory access time",
        ),
        (
            "What is the first major stage of the instruction cycle?",
            "Fetch",
        ),
        (
            "What does CPI mean?",
            "Cycles Per Instruction",
        ),
        (
            "What is a control hazard?",
            "A pipeline hazard caused by control-flow changes such as branches",
        ),
    ]

    for question, answer in questions:
        print(f"Q: {question}")
        print(f"A: {answer}\n")


# ============================================================================
# 29. MAIN PROGRAM
# ============================================================================

def main() -> None:
    print("COMPUTER ARCHITECTURE INTRODUCTION")
    print("Educational architecture, organization and CPU simulation laboratory")

    explain_terminology()
    architecture_vs_organization()
    binary_and_integer_representation()
    demonstrate_cpu_components()
    demonstrate_memory()
    demonstrate_cpu()
    demonstrate_control_flow()
    explain_addressing_modes()
    compare_risc_and_cisc()
    demonstrate_cache()
    explain_memory_hierarchy()
    demonstrate_io_and_interrupts()
    demonstrate_performance()
    demonstrate_pipelining()
    demonstrate_stack_machine()
    demonstrate_assembler()
    demonstrate_datapath()
    demonstrate_virtual_memory()
    demonstrate_logic_gates()
    run_tests()
    demonstrate_edge_cases()
    demonstrate_branch_prediction()
    explain_production_considerations()
    compare_machine_models()
    performance_experiment()
    knowledge_check()

    section("30. Final Execution State")
    print(
        "The examples above model the central relationship between software, "
        "the ISA, CPU datapath, memory, I/O and the underlying organization."
    )


if __name__ == "__main__":
    main()
