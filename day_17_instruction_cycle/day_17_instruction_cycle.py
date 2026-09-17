"""
Instruction Cycle: Fetch, Decode, Execute, Memory Access, Write Back
====================================================================

A standalone study program that models how a CPU processes instructions.

The examples progress from:
1. Basic CPU terminology
2. Registers and memory
3. Instruction representation
4. The five-stage instruction cycle
5. Fetch
6. Decode
7. Execute
8. Memory access
9. Write back
10. Different instruction types
11. Program counter and instruction register behavior
12. Addressing concepts
13. Flags and conditional execution
14. Stack operations
15. Branches and control flow
16. Exceptions and invalid instructions
17. Multi-cycle timing
18. Pipeline concepts
19. Data hazards
20. Forwarding and stalls
21. Performance measurements
22. A small industry-style CPU simulator

The implementation intentionally models architectural concepts rather than any
specific commercial CPU instruction set.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple
import time


# ---------------------------------------------------------------------------
# 1. Fundamental terminology
# ---------------------------------------------------------------------------

class Opcode(Enum):
    """Operations understood by our educational CPU."""

    NOP = auto()
    LOAD = auto()
    STORE = auto()
    MOV = auto()
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    CMP = auto()
    JMP = auto()
    JZ = auto()
    PUSH = auto()
    POP = auto()
    HALT = auto()


class CPUFault(Exception):
    """Base class for CPU simulation faults."""


class InvalidInstruction(CPUFault):
    """Raised when an instruction is not valid for the simulator."""


class MemoryFault(CPUFault):
    """Raised for invalid memory operations."""


class DivisionByZeroFault(CPUFault):
    """Raised for division by zero."""


class StackFault(CPUFault):
    """Raised for stack underflow or overflow."""


@dataclass
class Instruction:
    """
    Generic educational instruction.

    Examples:
        ADD R1, R2, R3
        LOAD R1, [100]
        STORE R1, [200]
        JZ 20
    """

    opcode: Opcode
    destination: Optional[str] = None
    source_a: Optional[str] = None
    source_b: Optional[str] = None
    immediate: Optional[int] = None
    address: Optional[int] = None
    label: Optional[str] = None

    def __str__(self) -> str:
        operands: List[str] = []

        if self.destination is not None:
            operands.append(self.destination)

        if self.source_a is not None:
            operands.append(self.source_a)

        if self.source_b is not None:
            operands.append(self.source_b)

        if self.immediate is not None:
            operands.append(f"#{self.immediate}")

        if self.address is not None:
            operands.append(f"[{self.address}]")

        if self.label is not None:
            operands.append(self.label)

        return self.opcode.name + (" " + ", ".join(operands) if operands else "")


# ---------------------------------------------------------------------------
# 2. CPU architectural state
# ---------------------------------------------------------------------------

@dataclass
class Flags:
    """
    Simplified condition-code register.

    Real processors expose architecture-specific flags. Common examples include
    zero, negative/sign, carry, overflow, and parity.
    """

    zero: bool = False
    negative: bool = False
    carry: bool = False
    overflow: bool = False

    def as_string(self) -> str:
        return (
            f"Z={int(self.zero)} "
            f"N={int(self.negative)} "
            f"C={int(self.carry)} "
            f"V={int(self.overflow)}"
        )


@dataclass
class CPU:
    """
    Five-stage educational CPU.

    The CPU contains:
        - general-purpose registers
        - program counter (PC)
        - instruction register (IR)
        - memory
        - stack pointer (SP)
        - flags
        - halted state
        - cycle counter
    """

    memory_size: int = 256
    register_names: Tuple[str, ...] = (
        "R0",
        "R1",
        "R2",
        "R3",
        "R4",
        "R5",
        "R6",
        "R7",
    )
    registers: Dict[str, int] = field(default_factory=dict)
    memory: List[int] = field(default_factory=list)
    pc: int = 0
    ir: Optional[Instruction] = None
    mar: Optional[int] = None
    mdr: Optional[int] = None
    sp: int = 255
    flags: Flags = field(default_factory=Flags)
    halted: bool = False
    cycle_count: int = 0
    instruction_count: int = 0

    def __post_init__(self) -> None:
        self.registers = {name: 0 for name in self.register_names}
        self.memory = [0] * self.memory_size
        self.sp = self.memory_size - 1

    # -----------------------------------------------------------------------
    # Register operations
    # -----------------------------------------------------------------------

    def read_register(self, name: str) -> int:
        self._validate_register(name)
        return self.registers[name]

    def write_register(self, name: str, value: int) -> None:
        self._validate_register(name)

        # R0 is conventionally useful as a normal register in this simulator.
        # Some real ISAs define a special constant-zero register instead.
        self.registers[name] = value

    def _validate_register(self, name: str) -> None:
        if name not in self.registers:
            raise InvalidInstruction(f"Unknown register: {name}")

    # -----------------------------------------------------------------------
    # Memory operations
    # -----------------------------------------------------------------------

    def read_memory(self, address: int) -> int:
        self._validate_memory_address(address)
        self.mar = address
        self.mdr = self.memory[address]
        return self.mdr

    def write_memory(self, address: int, value: int) -> None:
        self._validate_memory_address(address)
        self.mar = address
        self.mdr = value
        self.memory[address] = value

    def _validate_memory_address(self, address: int) -> None:
        if not 0 <= address < self.memory_size:
            raise MemoryFault(
                f"Memory address {address} outside 0..{self.memory_size - 1}"
            )

    # -----------------------------------------------------------------------
    # ALU and flag calculation
    # -----------------------------------------------------------------------

    def alu_add(self, left: int, right: int) -> int:
        result = left + right
        self._update_arithmetic_flags(result)
        return result

    def alu_sub(self, left: int, right: int) -> int:
        result = left - right
        self._update_arithmetic_flags(result)
        return result

    def alu_mul(self, left: int, right: int) -> int:
        result = left * right
        self._update_arithmetic_flags(result)
        return result

    def alu_div(self, left: int, right: int) -> int:
        if right == 0:
            raise DivisionByZeroFault("Division by zero")
        result = left // right
        self._update_arithmetic_flags(result)
        return result

    def _update_arithmetic_flags(self, result: int) -> None:
        self.flags.zero = result == 0
        self.flags.negative = result < 0

        # This simplified model does not emulate a fixed-width integer
        # register, so carry and overflow are left false unless a more
        # specialized ALU is implemented.
        self.flags.carry = False
        self.flags.overflow = False

    # -----------------------------------------------------------------------
    # Five instruction-cycle stages
    # -----------------------------------------------------------------------

    def fetch(self, program: List[Instruction]) -> Instruction:
        """
        FETCH stage.

        1. PC identifies the next instruction.
        2. Instruction memory is accessed.
        3. Instruction is copied into IR.
        4. PC advances to the following instruction.

        A real processor may use separate instruction caches, translation
        mechanisms, prefetching, and many other implementation details.
        """

        if self.pc < 0 or self.pc >= len(program):
            raise InvalidInstruction(f"PC {self.pc} points outside the program")

        self.ir = program[self.pc]
        self.pc += 1
        return self.ir

    def decode(self, instruction: Instruction) -> Dict[str, object]:
        """
        DECODE stage.

        The control unit determines what the opcode means and identifies
        registers, immediates, addresses, and other operands.

        This simulator represents the decoded result as a dictionary.
        """
        decoded: Dict[str, object] = {
            "opcode": instruction.opcode,
            "destination": instruction.destination,
            "source_a": instruction.source_a,
            "source_b": instruction.source_b,
            "immediate": instruction.immediate,
            "address": instruction.address,
        }

        # Reading source registers is part of the conceptual decode/read phase.
        if instruction.source_a is not None:
            decoded["value_a"] = self.read_register(instruction.source_a)

        if instruction.source_b is not None:
            decoded["value_b"] = self.read_register(instruction.source_b)

        return decoded

    def execute(
        self,
        decoded: Dict[str, object],
        program: List[Instruction],
    ) -> Dict[str, object]:
        """
        EXECUTE stage.

        The ALU or control logic performs the operation.

        Important distinction:
            - ADD/SUB/MUL/DIV perform arithmetic here.
            - LOAD/STORE require a later memory-access stage.
            - JMP/JZ modify control flow.
            - HALT changes processor state.
        """

        opcode = decoded["opcode"]
        result: Dict[str, object] = {}

        if opcode == Opcode.NOP:
            return result

        if opcode == Opcode.MOV:
            if decoded["immediate"] is not None:
                result["value"] = int(decoded["immediate"])
            elif decoded["source_a"] is not None:
                result["value"] = self.read_register(
                    str(decoded["source_a"])
                )
            else:
                raise InvalidInstruction("MOV requires an immediate or source")
            return result

        if opcode == Opcode.ADD:
            result["value"] = self.alu_add(
                int(decoded["value_a"]),
                int(decoded["value_b"]),
            )
            return result

        if opcode == Opcode.SUB:
            result["value"] = self.alu_sub(
                int(decoded["value_a"]),
                int(decoded["value_b"]),
            )
            return result

        if opcode == Opcode.MUL:
            result["value"] = self.alu_mul(
                int(decoded["value_a"]),
                int(decoded["value_b"]),
            )
            return result

        if opcode == Opcode.DIV:
            result["value"] = self.alu_div(
                int(decoded["value_a"]),
                int(decoded["value_b"]),
            )
            return result

        if opcode == Opcode.CMP:
            difference = self.alu_sub(
                int(decoded["value_a"]),
                int(decoded["value_b"]),
            )
            result["comparison"] = difference
            return result

        if opcode == Opcode.LOAD:
            if decoded["address"] is None:
                raise InvalidInstruction("LOAD requires a memory address")
            result["memory_address"] = int(decoded["address"])
            return result

        if opcode == Opcode.STORE:
            if decoded["address"] is None:
                raise InvalidInstruction("STORE requires a memory address")
            if decoded["source_a"] is None:
                raise InvalidInstruction("STORE requires a source register")
            result["memory_address"] = int(decoded["address"])
            result["store_value"] = self.read_register(
                str(decoded["source_a"])
            )
            return result

        if opcode == Opcode.JMP:
            if decoded["address"] is None:
                raise InvalidInstruction("JMP requires a target")
            result["branch_target"] = int(decoded["address"])
            return result

        if opcode == Opcode.JZ:
            if decoded["address"] is None:
                raise InvalidInstruction("JZ requires a target")
            if self.flags.zero:
                result["branch_target"] = int(decoded["address"])
            return result

        if opcode in (Opcode.PUSH, Opcode.POP, Opcode.HALT):
            return result

        raise InvalidInstruction(f"Unsupported opcode: {opcode}")

    def memory_access(self, decoded: Dict[str, object], result: Dict[str, object]) -> None:
        """
        MEMORY ACCESS stage.

        LOAD:
            address -> memory -> MDR -> eventual destination register

        STORE:
            source value -> memory

        Arithmetic instructions do not need data-memory access.
        """

        opcode = decoded["opcode"]

        if opcode == Opcode.LOAD:
            address = int(result["memory_address"])
            result["value"] = self.read_memory(address)

        elif opcode == Opcode.STORE:
            address = int(result["memory_address"])
            value = int(result["store_value"])
            self.write_memory(address, value)

        elif opcode == Opcode.PUSH:
            if decoded["source_a"] is None:
                raise InvalidInstruction("PUSH requires a source register")

            if self.sp <= 0:
                raise StackFault("Stack overflow")

            self.memory[self.sp] = self.read_register(
                str(decoded["source_a"])
            )
            self.sp -= 1

        elif opcode == Opcode.POP:
            if decoded["destination"] is None:
                raise InvalidInstruction("POP requires a destination register")

            if self.sp >= self.memory_size - 1:
                raise StackFault("Stack underflow")

            self.sp += 1
            result["value"] = self.memory[self.sp]

    def write_back(self, decoded: Dict[str, object], result: Dict[str, object]) -> None:
        """
        WRITE-BACK stage.

        Results are committed to architectural registers.

        Stores have already updated memory in the memory-access stage, so they
        normally have no register write-back.
        """

        opcode = decoded["opcode"]
        destination = decoded["destination"]

        if opcode in {
            Opcode.MOV,
            Opcode.ADD,
            Opcode.SUB,
            Opcode.MUL,
            Opcode.DIV,
            Opcode.LOAD,
            Opcode.POP,
        }:
            if destination is None:
                raise InvalidInstruction(
                    f"{opcode.name} requires a destination register"
                )

            if "value" not in result:
                raise InvalidInstruction(
                    f"{opcode.name} produced no value for write-back"
                )

            self.write_register(destination, int(result["value"]))

        if opcode in {Opcode.JMP, Opcode.JZ}:
            if "branch_target" in result:
                target = int(result["branch_target"])
                if not 0 <= target < 10_000:
                    raise InvalidInstruction(
                        f"Invalid branch target: {target}"
                    )
                self.pc = target

        if opcode == Opcode.HALT:
            self.halted = True

    # -----------------------------------------------------------------------
    # Complete instruction cycle
    # -----------------------------------------------------------------------

    def step(
        self,
        program: List[Instruction],
        trace: bool = False,
    ) -> None:
        """
        Execute one complete instruction.

        Conceptually:

            FETCH
              |
              v
            DECODE
              |
              v
            EXECUTE
              |
              v
            MEMORY ACCESS
              |
              v
            WRITE BACK

        Actual processors may overlap stages through pipelining.
        This simple model completes one instruction before starting the next.
        """

        if self.halted:
            return

        current_pc = self.pc
        instruction = self.fetch(program)
        decoded = self.decode(instruction)
        result = self.execute(decoded, program)
        self.memory_access(decoded, result)
        self.write_back(decoded, result)

        self.cycle_count += 1
        self.instruction_count += 1

        if trace:
            print(
                f"Cycle {self.cycle_count:03d} | "
                f"PC={current_pc:03d} | "
                f"{instruction!s:24} | "
                f"R1={self.registers['R1']:4} "
                f"R2={self.registers['R2']:4} "
                f"R3={self.registers['R3']:4} | "
                f"{self.flags.as_string()}"
            )

    def run(
        self,
        program: List[Instruction],
        trace: bool = False,
        max_steps: int = 1_000,
    ) -> None:
        """Run until HALT or until a safety step limit is reached."""

        steps = 0

        while not self.halted:
            if steps >= max_steps:
                raise RuntimeError(
                    "Execution stopped because max_steps was reached. "
                    "The program may contain an infinite loop."
                )

            self.step(program, trace=trace)
            steps += 1

    def dump_state(self) -> None:
        print("\nCPU STATE")
        print("-" * 60)
        print(f"PC:        {self.pc}")
        print(f"IR:        {self.ir}")
        print(f"MAR:       {self.mar}")
        print(f"MDR:       {self.mdr}")
        print(f"SP:        {self.sp}")
        print(f"Flags:     {self.flags.as_string()}")
        print(f"Halted:    {self.halted}")
        print(f"Cycles:    {self.cycle_count}")
        print(f"Instructions: {self.instruction_count}")
        print("Registers:")
        for name, value in self.registers.items():
            print(f"  {name}: {value}")


# ---------------------------------------------------------------------------
# 3. Basic instruction examples
# ---------------------------------------------------------------------------

def example_basic_arithmetic() -> None:
    """Demonstrate fetch, decode, execute and write-back."""

    print("\n" + "=" * 72)
    print("EXAMPLE 1: BASIC ARITHMETIC")
    print("=" * 72)

    cpu = CPU()

    program = [
        Instruction(Opcode.MOV, destination="R1", immediate=12),
        Instruction(Opcode.MOV, destination="R2", immediate=8),
        Instruction(
            Opcode.ADD,
            destination="R3",
            source_a="R1",
            source_b="R2",
        ),
        Instruction(Opcode.HALT),
    ]

    cpu.run(program, trace=True)
    cpu.dump_state()

    assert cpu.registers["R3"] == 20


# ---------------------------------------------------------------------------
# 4. Memory access example
# ---------------------------------------------------------------------------

def example_load_store() -> None:
    """Demonstrate the difference between register and memory operations."""

    print("\n" + "=" * 72)
    print("EXAMPLE 2: LOAD AND STORE")
    print("=" * 72)

    cpu = CPU()
    cpu.memory[100] = 42

    program = [
        Instruction(Opcode.LOAD, destination="R1", address=100),
        Instruction(Opcode.MOV, destination="R2", immediate=8),
        Instruction(
            Opcode.ADD,
            destination="R3",
            source_a="R1",
            source_b="R2",
        ),
        Instruction(Opcode.STORE, source_a="R3", address=101),
        Instruction(Opcode.HALT),
    ]

    cpu.run(program, trace=True)

    print(f"\nMemory[100] = {cpu.memory[100]}")
    print(f"Memory[101] = {cpu.memory[101]}")
    assert cpu.memory[101] == 50


# ---------------------------------------------------------------------------
# 5. Conditional execution and flags
# ---------------------------------------------------------------------------

def example_branching() -> None:
    """
    Demonstrate comparison, zero flag and conditional branching.

    Program idea:
        R1 = 10
        R2 = 10
        CMP R1, R2
        JZ 6
        R3 = 999      # skipped
        HALT
        R3 = 123      # branch destination
        HALT
    """

    print("\n" + "=" * 72)
    print("EXAMPLE 3: FLAGS AND CONDITIONAL BRANCHING")
    print("=" * 72)

    cpu = CPU()

    program = [
        Instruction(Opcode.MOV, destination="R1", immediate=10),  # 0
        Instruction(Opcode.MOV, destination="R2", immediate=10),  # 1
        Instruction(Opcode.CMP, source_a="R1", source_b="R2"),    # 2
        Instruction(Opcode.JZ, address=5),                        # 3
        Instruction(Opcode.MOV, destination="R3", immediate=999), # 4
        Instruction(Opcode.MOV, destination="R3", immediate=123), # 5
        Instruction(Opcode.HALT),                                 # 6
    ]

    cpu.run(program, trace=True)

    print(f"\nR3 after conditional branch = {cpu.registers['R3']}")
    assert cpu.registers["R3"] == 123


# ---------------------------------------------------------------------------
# 6. Stack example
# ---------------------------------------------------------------------------

def example_stack() -> None:
    """Demonstrate PUSH and POP as memory-backed stack operations."""

    print("\n" + "=" * 72)
    print("EXAMPLE 4: STACK OPERATIONS")
    print("=" * 72)

    cpu = CPU()

    program = [
        Instruction(Opcode.MOV, destination="R1", immediate=55),
        Instruction(Opcode.PUSH, source_a="R1"),
        Instruction(Opcode.MOV, destination="R1", immediate=99),
        Instruction(Opcode.POP, destination="R2"),
        Instruction(Opcode.HALT),
    ]

    cpu.run(program, trace=True)

    print(f"\nR1 = {cpu.registers['R1']}")
    print(f"R2 = {cpu.registers['R2']}")
    assert cpu.registers["R2"] == 55


# ---------------------------------------------------------------------------
# 7. Instruction timing model
# ---------------------------------------------------------------------------

@dataclass
class StageTiming:
    """Simplified timing information for each instruction stage."""

    fetch: int = 1
    decode: int = 1
    execute: int = 1
    memory: int = 1
    write_back: int = 1

    @property
    def total(self) -> int:
        return (
            self.fetch
            + self.decode
            + self.execute
            + self.memory
            + self.write_back
        )


def demonstrate_non_pipelined_timing() -> None:
    """
    Show why a five-stage non-pipelined processor requires all stages for
    every instruction before the next instruction begins.
    """

    print("\n" + "=" * 72)
    print("EXAMPLE 5: NON-PIPELINED TIMING")
    print("=" * 72)

    timing = StageTiming()
    instruction_count = 6

    cycles = instruction_count * timing.total

    print(f"Stages per instruction: {timing.total}")
    print(f"Instructions:           {instruction_count}")
    print(f"Approximate cycles:     {cycles}")

    print(
        "\nA five-stage non-pipelined implementation therefore needs "
        "approximately 5 cycles per instruction when each stage consumes "
        "one cycle."
    )


# ---------------------------------------------------------------------------
# 8. Pipeline timing model
# ---------------------------------------------------------------------------

def pipeline_cycle_count(
    instruction_count: int,
    stage_count: int = 5,
) -> int:
    """
    Ideal pipeline cycle count.

    For N instructions and K stages:

        cycles = K + N - 1

    This assumes:
        - every stage takes one cycle
        - no hazards
        - no branch penalties
        - no cache misses
        - no structural conflicts
        - no interrupts or exceptions
    """

    if instruction_count <= 0:
        return 0

    if stage_count <= 0:
        raise ValueError("stage_count must be positive")

    return stage_count + instruction_count - 1


def demonstrate_pipeline() -> None:
    """Print a conceptual five-stage pipeline schedule."""

    print("\n" + "=" * 72)
    print("EXAMPLE 6: IDEAL FIVE-STAGE PIPELINE")
    print("=" * 72)

    instructions = ["I1", "I2", "I3", "I4"]

    stages = [
        "F",  # Fetch
        "D",  # Decode
        "E",  # Execute
        "M",  # Memory
        "W",  # Write back
    ]

    print("\nCycle-by-cycle conceptual schedule:\n")

    total_cycles = pipeline_cycle_count(len(instructions), len(stages))

    for cycle in range(1, total_cycles + 1):
        active = []

        for instruction_index, instruction_name in enumerate(instructions):
            stage_index = cycle - instruction_index - 1

            if 0 <= stage_index < len(stages):
                active.append(
                    f"{instruction_name}:{stages[stage_index]}"
                )

        print(f"Cycle {cycle}: " + " | ".join(active))

    print(
        f"\nIdeal cycles for {len(instructions)} instructions: "
        f"{total_cycles}"
    )


# ---------------------------------------------------------------------------
# 9. Pipeline hazards
# ---------------------------------------------------------------------------

@dataclass
class PipelineInstruction:
    """Minimal representation used to reason about data dependencies."""

    name: str
    reads: Tuple[str, ...] = ()
    writes: Tuple[str, ...] = ()


def detect_raw_hazard(
    older: PipelineInstruction,
    newer: PipelineInstruction,
) -> List[str]:
    """
    Detect a Read After Write (RAW) dependency.

    RAW:
        Instruction A writes R1
        Instruction B reads R1

    A pipeline may require forwarding or a stall depending on the CPU design.
    """

    return [
        register
        for register in newer.reads
        if register in older.writes
    ]


def demonstrate_hazards() -> None:
    """Explain RAW dependencies with actual data structures."""

    print("\n" + "=" * 72)
    print("EXAMPLE 7: DATA HAZARD")
    print("=" * 72)

    instruction_a = PipelineInstruction(
        name="ADD R1, R2, R3",
        reads=("R2", "R3"),
        writes=("R1",),
    )

    instruction_b = PipelineInstruction(
        name="SUB R4, R1, R5",
        reads=("R1", "R5"),
        writes=("R4",),
    )

    hazards = detect_raw_hazard(instruction_a, instruction_b)

    print(f"Older instruction: {instruction_a.name}")
    print(f"Newer instruction: {instruction_b.name}")
    print(f"RAW dependencies:  {hazards}")

    print(
        "\nPossible solutions include forwarding, inserting a stall, "
        "compiler scheduling, or a combination of hardware and software "
        "techniques."
    )


# ---------------------------------------------------------------------------
# 10. Addressing modes
# ---------------------------------------------------------------------------

class AddressingMode(Enum):
    IMMEDIATE = auto()
    REGISTER = auto()
    DIRECT = auto()
    REGISTER_INDIRECT = auto()
    BASE_OFFSET = auto()


def resolve_address(
    mode: AddressingMode,
    operand: int,
    registers: Dict[str, int],
    register: Optional[str] = None,
    offset: int = 0,
) -> int:
    """
    Resolve an effective address for several common addressing modes.

    This is conceptual. Actual ISA syntax and supported modes vary.
    """

    if mode == AddressingMode.IMMEDIATE:
        return operand

    if mode == AddressingMode.REGISTER:
        if register is None:
            raise ValueError("REGISTER mode requires a register")
        return registers[register]

    if mode == AddressingMode.DIRECT:
        return operand

    if mode == AddressingMode.REGISTER_INDIRECT:
        if register is None:
            raise ValueError("REGISTER_INDIRECT requires a register")
        return registers[register]

    if mode == AddressingMode.BASE_OFFSET:
        if register is None:
            raise ValueError("BASE_OFFSET requires a base register")
        return registers[register] + offset

    raise ValueError(f"Unsupported addressing mode: {mode}")


def demonstrate_addressing_modes() -> None:
    print("\n" + "=" * 72)
    print("EXAMPLE 8: ADDRESSING MODES")
    print("=" * 72)

    registers = {
        "R1": 100,
        "R2": 20,
    }

    examples = [
        (
            "Immediate",
            resolve_address(AddressingMode.IMMEDIATE, 42, registers),
        ),
        (
            "Register",
            resolve_address(
                AddressingMode.REGISTER,
                0,
                registers,
                register="R2",
            ),
        ),
        (
            "Direct",
            resolve_address(AddressingMode.DIRECT, 120, registers),
        ),
        (
            "Register indirect",
            resolve_address(
                AddressingMode.REGISTER_INDIRECT,
                0,
                registers,
                register="R1",
            ),
        ),
        (
            "Base + offset",
            resolve_address(
                AddressingMode.BASE_OFFSET,
                0,
                registers,
                register="R1",
                offset=12,
            ),
        ),
    ]

    for name, value in examples:
        print(f"{name:20} -> {value}")


# ---------------------------------------------------------------------------
# 11. Exceptions and edge cases
# ---------------------------------------------------------------------------

def demonstrate_edge_cases() -> None:
    """Exercise failure paths that a CPU implementation must consider."""

    print("\n" + "=" * 72)
    print("EXAMPLE 9: EDGE CASES AND EXCEPTIONS")
    print("=" * 72)

    # Invalid memory address.
    cpu = CPU()

    try:
        cpu.read_memory(-1)
    except MemoryFault as error:
        print(f"Memory fault handled: {error}")

    # Division by zero.
    try:
        cpu.alu_div(10, 0)
    except DivisionByZeroFault as error:
        print(f"Arithmetic fault handled: {error}")

    # Unknown register.
    try:
        cpu.read_register("R99")
    except InvalidInstruction as error:
        print(f"Instruction/register fault handled: {error}")

    # Infinite-loop protection.
    infinite_program = [
        Instruction(Opcode.JMP, address=0),
    ]

    try:
        cpu.run(infinite_program, max_steps=5)
    except RuntimeError as error:
        print(f"Execution-limit condition handled: {error}")


# ---------------------------------------------------------------------------
# 12. Complete arithmetic case study
# ---------------------------------------------------------------------------

def build_sum_of_values_program(
    start_address: int,
    count: int,
) -> Tuple[List[Instruction], int]:
    """
    Build a program that loads consecutive values from memory and sums them.

    Registers:
        R1 = current address
        R2 = number of remaining values
        R3 = accumulated sum
        R4 = current value
        R5 = constant 1

    This demonstrates how several instruction-cycle stages cooperate to
    implement a higher-level algorithm.
    """

    if count <= 0:
        raise ValueError("count must be positive")

    program: List[Instruction] = [
        Instruction(Opcode.MOV, destination="R1", immediate=start_address),
        Instruction(Opcode.MOV, destination="R2", immediate=count),
        Instruction(Opcode.MOV, destination="R3", immediate=0),
        Instruction(Opcode.MOV, destination="R5", immediate=1),
    ]

    loop_start = len(program)

    # The educational instruction set has direct memory addressing but no
    # register-indirect LOAD. We therefore construct the program after
    # knowing the fixed memory addresses.
    for index in range(count):
        program.append(
            Instruction(
                Opcode.LOAD,
                destination="R4",
                address=start_address + index,
            )
        )
        program.append(
            Instruction(
                Opcode.ADD,
                destination="R3",
                source_a="R3",
                source_b="R4",
            )
        )

    # A direct sequence is used here to keep the simulator's ISA simple.
    program.append(Instruction(Opcode.HALT))

    return program, loop_start


def demonstrate_sum_case_study() -> None:
    """Use the simulator to calculate a memory-resident sum."""

    print("\n" + "=" * 72)
    print("EXAMPLE 10: MEMORY SUM CASE STUDY")
    print("=" * 72)

    cpu = CPU()

    values = [4, 7, 11, 18, 25]
    start_address = 40

    for offset, value in enumerate(values):
        cpu.memory[start_address + offset] = value

    program, _ = build_sum_of_values_program(
        start_address=start_address,
        count=len(values),
    )

    cpu.run(program, trace=True)

    expected = sum(values)

    print(f"\nInput values: {values}")
    print(f"CPU result:   {cpu.registers['R3']}")
    print(f"Expected:     {expected}")
    print(f"Cycles:       {cpu.cycle_count}")

    assert cpu.registers["R3"] == expected


# ---------------------------------------------------------------------------
# 13. CPI and performance concepts
# ---------------------------------------------------------------------------

@dataclass
class PerformanceModel:
    """
    Basic CPU performance model.

    CPU time can be expressed as:

        CPU time = instruction_count * CPI * clock_cycle_time

    or:

        CPU time = (instruction_count * CPI) / clock_frequency
    """

    instruction_count: int
    cpi: float
    frequency_hz: float

    @property
    def cycles(self) -> float:
        return self.instruction_count * self.cpi

    @property
    def execution_time_seconds(self) -> float:
        return self.cycles / self.frequency_hz

    @property
    def instructions_per_second(self) -> float:
        return self.instruction_count / self.execution_time_seconds


def demonstrate_performance() -> None:
    print("\n" + "=" * 72)
    print("EXAMPLE 11: PERFORMANCE MODEL")
    print("=" * 72)

    model = PerformanceModel(
        instruction_count=1_000_000,
        cpi=1.5,
        frequency_hz=3_000_000_000,
    )

    print(f"Instruction count: {model.instruction_count:,}")
    print(f"CPI:               {model.cpi}")
    print(f"Clock frequency:   {model.frequency_hz / 1e9:.1f} GHz")
    print(f"CPU cycles:        {model.cycles:,.0f}")
    print(f"Execution time:    {model.execution_time_seconds:.9f} s")
    print(
        f"Instruction rate:  "
        f"{model.instructions_per_second / 1e6:.2f} million/s"
    )


# ---------------------------------------------------------------------------
# 14. Micro-operation view
# ---------------------------------------------------------------------------

def demonstrate_micro_operations() -> None:
    """
    Show conceptual micro-operations.

    A complex machine instruction can be implemented internally using smaller
    register-transfer or control operations. Exact micro-operations are
    implementation-dependent.
    """

    print("\n" + "=" * 72)
    print("EXAMPLE 12: MICRO-OPERATIONS")
    print("=" * 72)

    instruction = "ADD R3, R1, R2"

    micro_operations = [
        "MAR <- PC",
        "IR <- InstructionMemory[MAR]",
        "PC <- PC + instruction_size",
        "Decode IR",
        "A <- R1",
        "B <- R2",
        "ALUOut <- A + B",
        "R3 <- ALUOut",
    ]

    print(f"Instruction: {instruction}\n")

    for number, operation in enumerate(micro_operations, start=1):
        print(f"{number:02d}. {operation}")


# ---------------------------------------------------------------------------
# 15. Cache and memory hierarchy discussion through simulation
# ---------------------------------------------------------------------------

@dataclass
class SimpleCache:
    """
    Tiny direct-mapped cache model.

    It demonstrates why memory access can have different effective latency.
    """

    lines: int = 4
    cache: Dict[int, int] = field(default_factory=dict)
    hits: int = 0
    misses: int = 0

    def access(self, address: int, memory: List[int]) -> int:
        index = address % self.lines

        if index in self.cache and self.cache[index] == address:
            self.hits += 1
            return memory[address]

        self.misses += 1
        self.cache[index] = address
        return memory[address]

    @property
    def hit_rate(self) -> float:
        accesses = self.hits + self.misses
        return self.hits / accesses if accesses else 0.0


def demonstrate_cache_effect() -> None:
    print("\n" + "=" * 72)
    print("EXAMPLE 13: CACHE HIT AND MISS")
    print("=" * 72)

    memory = [index * 10 for index in range(32)]
    cache = SimpleCache(lines=4)

    addresses = [0, 0, 0, 1, 1, 4, 4, 0, 8, 8]

    for address in addresses:
        value = cache.access(address, memory)
        print(f"Address {address:2} -> value {value:3}")

    print(f"\nHits:     {cache.hits}")
    print(f"Misses:   {cache.misses}")
    print(f"Hit rate: {cache.hit_rate:.2%}")


# ---------------------------------------------------------------------------
# 16. Instruction classification
# ---------------------------------------------------------------------------

def classify_instruction(instruction: Instruction) -> str:
    """Classify instructions by their main architectural role."""

    arithmetic = {
        Opcode.ADD,
        Opcode.SUB,
        Opcode.MUL,
        Opcode.DIV,
        Opcode.CMP,
    }

    memory = {Opcode.LOAD, Opcode.STORE, Opcode.PUSH, Opcode.POP}
    control = {Opcode.JMP, Opcode.JZ, Opcode.HALT}
    data_transfer = {Opcode.MOV}

    if instruction.opcode in arithmetic:
        return "Arithmetic / logic"
    if instruction.opcode in memory:
        return "Memory / stack"
    if instruction.opcode in control:
        return "Control flow"
    if instruction.opcode in data_transfer:
        return "Data transfer"
    return "Other"


def demonstrate_instruction_classes() -> None:
    print("\n" + "=" * 72)
    print("EXAMPLE 14: INSTRUCTION CLASSIFICATION")
    print("=" * 72)

    instructions = [
        Instruction(Opcode.MOV, destination="R1", immediate=10),
        Instruction(Opcode.ADD, destination="R2", source_a="R1", source_b="R1"),
        Instruction(Opcode.LOAD, destination="R3", address=50),
        Instruction(Opcode.STORE, source_a="R3", address=51),
        Instruction(Opcode.JMP, address=10),
        Instruction(Opcode.HALT),
    ]

    for instruction in instructions:
        print(f"{str(instruction):30} -> {classify_instruction(instruction)}")


# ---------------------------------------------------------------------------
# 17. Debugging and tracing
# ---------------------------------------------------------------------------

def demonstrate_debugging_trace() -> None:
    """
    Show the information a debugger or CPU trace can expose.

    Useful debugging observations include:
        - PC before instruction
        - instruction being executed
        - register values
        - memory addresses
        - flags
        - unexpected control-flow changes
    """

    print("\n" + "=" * 72)
    print("EXAMPLE 15: DEBUGGING WITH A TRACE")
    print("=" * 72)

    cpu = CPU()

    program = [
        Instruction(Opcode.MOV, destination="R1", immediate=3),
        Instruction(Opcode.MOV, destination="R2", immediate=4),
        Instruction(Opcode.MUL, destination="R3", source_a="R1", source_b="R2"),
        Instruction(Opcode.STORE, source_a="R3", address=150),
        Instruction(Opcode.HALT),
    ]

    cpu.run(program, trace=True)

    print(f"\nFinal memory[150] = {cpu.memory[150]}")


# ---------------------------------------------------------------------------
# 18. Validation tests
# ---------------------------------------------------------------------------

def run_self_tests() -> None:
    """Run compact assertions over core simulator behavior."""

    print("\n" + "=" * 72)
    print("SELF-TESTS")
    print("=" * 72)

    # Arithmetic.
    cpu = CPU()
    program = [
        Instruction(Opcode.MOV, destination="R1", immediate=9),
        Instruction(Opcode.MOV, destination="R2", immediate=3),
        Instruction(Opcode.ADD, destination="R3", source_a="R1", source_b="R2"),
        Instruction(Opcode.SUB, destination="R4", source_a="R1", source_b="R2"),
        Instruction(Opcode.MUL, destination="R5", source_a="R1", source_b="R2"),
        Instruction(Opcode.DIV, destination="R6", source_a="R1", source_b="R2"),
        Instruction(Opcode.HALT),
    ]
    cpu.run(program)

    assert cpu.registers["R3"] == 12
    assert cpu.registers["R4"] == 6
    assert cpu.registers["R5"] == 27
    assert cpu.registers["R6"] == 3

    # Memory.
    cpu = CPU()
    cpu.memory[10] = 77
    program = [
        Instruction(Opcode.LOAD, destination="R1", address=10),
        Instruction(Opcode.STORE, source_a="R1", address=11),
        Instruction(Opcode.HALT),
    ]
    cpu.run(program)

    assert cpu.registers["R1"] == 77
    assert cpu.memory[11] == 77

    # Branch.
    cpu = CPU()
    program = [
        Instruction(Opcode.MOV, destination="R1", immediate=0),
        Instruction(Opcode.CMP, source_a="R1", source_b="R1"),
        Instruction(Opcode.JZ, address=4),
        Instruction(Opcode.MOV, destination="R2", immediate=999),
        Instruction(Opcode.MOV, destination="R2", immediate=123),
        Instruction(Opcode.HALT),
    ]
    cpu.run(program)

    assert cpu.registers["R2"] == 123

    # Division by zero.
    cpu = CPU()
    try:
        cpu.alu_div(10, 0)
    except DivisionByZeroFault:
        pass
    else:
        raise AssertionError("Division by zero was not detected")

    print("All self-tests passed.")


# ---------------------------------------------------------------------------
# 19. Advanced conceptual model: instruction pipeline records
# ---------------------------------------------------------------------------

@dataclass
class PipelineRegister:
    """
    Data transferred between pipeline stages.

    Real processors use pipeline registers/latches to hold values between
    stages so multiple instructions can occupy different stages simultaneously.
    """

    instruction: Optional[Instruction] = None
    decoded: Dict[str, object] = field(default_factory=dict)
    result: Dict[str, object] = field(default_factory=dict)


def demonstrate_pipeline_registers() -> None:
    print("\n" + "=" * 72)
    print("EXAMPLE 16: PIPELINE REGISTERS")
    print("=" * 72)

    if_id = PipelineRegister(
        instruction=Instruction(
            Opcode.ADD,
            destination="R3",
            source_a="R1",
            source_b="R2",
        )
    )

    id_ex = PipelineRegister(
        instruction=if_id.instruction,
        decoded={
            "opcode": Opcode.ADD,
            "destination": "R3",
            "source_a": "R1",
            "source_b": "R2",
            "value_a": 10,
            "value_b": 20,
        },
    )

    ex_mem = PipelineRegister(
        instruction=id_ex.instruction,
        decoded=id_ex.decoded,
        result={"value": 30},
    )

    mem_wb = PipelineRegister(
        instruction=ex_mem.instruction,
        decoded=ex_mem.decoded,
        result=ex_mem.result,
    )

    print(f"IF/ID  instruction: {if_id.instruction}")
    print(f"ID/EX  decoded:     {id_ex.decoded}")
    print(f"EX/MEM result:      {ex_mem.result}")
    print(f"MEM/WB result:      {mem_wb.result}")

    print(
        "\nThese registers separate stages and allow different instructions "
        "to progress through the pipeline concurrently."
    )


# ---------------------------------------------------------------------------
# 20. Real-world design considerations
# ---------------------------------------------------------------------------

def print_design_considerations() -> None:
    """
    Print concise technical observations.

    These are deliberately connected to the executable simulator.
    """

    print("\n" + "=" * 72)
    print("DESIGN CONSIDERATIONS")
    print("=" * 72)

    considerations = [
        (
            "Instruction set architecture",
            "Defines programmer-visible instructions, registers, "
            "addressing modes, and architectural state."
        ),
        (
            "Microarchitecture",
            "Defines how the ISA is implemented internally, including "
            "pipelines, caches, execution units, and control logic."
        ),
        (
            "Clocking",
            "Synchronous designs use clock cycles to coordinate state "
            "transitions."
        ),
        (
            "Pipelining",
            "Overlaps instruction stages to increase throughput."
        ),
        (
            "Hazards",
            "Dependencies, resource conflicts, and control-flow changes "
            "can prevent ideal pipeline progress."
        ),
        (
            "Memory hierarchy",
            "Registers, caches, RAM, and storage have different capacity "
            "and latency characteristics."
        ),
        (
            "Exceptions",
            "Faults such as invalid instructions, protection violations, "
            "and arithmetic faults require controlled processor behavior."
        ),
        (
            "Security",
            "Modern CPUs use privilege levels, virtual memory, isolation, "
            "memory protection, and hardware security mechanisms."
        ),
    ]

    for title, explanation in considerations:
        print(f"{title:24}: {explanation}")


# ---------------------------------------------------------------------------
# 21. Benchmark the educational simulator
# ---------------------------------------------------------------------------

def benchmark_simulator() -> None:
    """
    Measure simulator execution time.

    This measures Python simulator overhead, not physical CPU instruction
    latency. It demonstrates an important distinction between simulation
    performance and hardware performance.
    """

    print("\n" + "=" * 72)
    print("EXAMPLE 17: SIMULATOR BENCHMARK")
    print("=" * 72)

    cpu = CPU()

    program = [
        Instruction(Opcode.MOV, destination="R1", immediate=1),
        Instruction(Opcode.MOV, destination="R2", immediate=2),
        Instruction(Opcode.ADD, destination="R3", source_a="R1", source_b="R2"),
        Instruction(Opcode.HALT),
    ]

    start = time.perf_counter()
    repetitions = 1_000

    for _ in range(repetitions):
        cpu = CPU()
        cpu.run(program)

    elapsed = time.perf_counter() - start

    print(f"Simulated programs: {repetitions:,}")
    print(f"Elapsed time:       {elapsed:.6f} seconds")
    print(
        "\nThis benchmark measures interpreter/simulator overhead. "
        "It should not be interpreted as a hardware CPU benchmark."
    )


# ---------------------------------------------------------------------------
# 22. Main educational sequence
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Run the complete instructional demonstration.

    The ordering mirrors the conceptual progression:
        architectural state
        -> instruction
        -> five-stage cycle
        -> memory and control flow
        -> timing
        -> pipeline
        -> hazards
        -> advanced implementation concerns
    """

    print("=" * 72)
    print("INSTRUCTION CYCLE EDUCATIONAL CPU SIMULATOR")
    print("=" * 72)

    print(
        "\nThe core cycle is:"
        "\n  1. Fetch"
        "\n  2. Decode"
        "\n  3. Execute"
        "\n  4. Memory access"
        "\n  5. Write back"
    )

    example_basic_arithmetic()
    example_load_store()
    example_branching()
    example_stack()
    demonstrate_non_pipelined_timing()
    demonstrate_pipeline()
    demonstrate_hazards()
    demonstrate_addressing_modes()
    demonstrate_edge_cases()
    demonstrate_sum_case_study()
    demonstrate_performance()
    demonstrate_micro_operations()
    demonstrate_cache_effect()
    demonstrate_instruction_classes()
    demonstrate_debugging_trace()
    run_self_tests()
    demonstrate_pipeline_registers()
    print_design_considerations()
    benchmark_simulator()

    print("\n" + "=" * 72)
    print("EDUCATIONAL SIMULATION COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()
