"""
Sequential Logic Circuits
==========================

A self-contained study and simulation script covering:

1. Combinational versus sequential logic
2. State, feedback, and clock signals
3. Latches: SR, gated SR, D
4. Flip-flops: D, JK, T, edge-triggered behavior
5. Setup time, hold time, propagation delay, metastability
6. Registers: parallel, shift, serial/parallel conversions
7. Counters: asynchronous, synchronous, up, down, modulo, ring, Johnson
8. Frequency division
9. Finite-state-machine concepts
10. Timing analysis
11. Practical comparisons, edge cases, and testing
12. A small synchronous digital-system simulation

The script uses only Python's standard library.

Run:
    python sequential_logic_circuits.py
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, List, Optional, Sequence, Tuple
import math


# ============================================================================
# SECTION 1: BASIC LOGIC PRIMITIVES
# ============================================================================

def logic_not(value: int) -> int:
    """Return NOT for a binary value."""
    validate_bit(value)
    return 1 - value


def logic_and(*values: int) -> int:
    """Return AND of all supplied binary values."""
    if not values:
        raise ValueError("AND requires at least one input.")
    for value in values:
        validate_bit(value)
    return int(all(values))


def logic_or(*values: int) -> int:
    """Return OR of all supplied binary values."""
    if not values:
        raise ValueError("OR requires at least one input.")
    for value in values:
        validate_bit(value)
    return int(any(values))


def logic_xor(*values: int) -> int:
    """Return XOR of all supplied binary values."""
    if not values:
        raise ValueError("XOR requires at least one input.")
    for value in values:
        validate_bit(value)
    result = 0
    for value in values:
        result ^= value
    return result


def validate_bit(value: int) -> None:
    """Require a value to be exactly binary 0 or 1."""
    if value not in (0, 1):
        raise ValueError(f"Expected binary value 0 or 1, got {value!r}")


def bits_to_string(bits: Sequence[int]) -> str:
    """Format a sequence of bits as a binary string."""
    for bit in bits:
        validate_bit(bit)
    return "".join(str(bit) for bit in bits)


def bits_to_int(bits: Sequence[int]) -> int:
    """Interpret bits from most significant to least significant."""
    value = 0
    for bit in bits:
        validate_bit(bit)
        value = (value << 1) | bit
    return value


def int_to_bits(value: int, width: int) -> List[int]:
    """Convert an integer into exactly width bits."""
    if value < 0:
        raise ValueError("Only non-negative integers are supported.")
    if width <= 0:
        raise ValueError("Width must be positive.")
    if value >= 2**width:
        raise ValueError(f"{value} cannot fit into {width} bits.")
    return [(value >> position) & 1 for position in range(width - 1, -1, -1)]


# ============================================================================
# SECTION 2: COMBINATIONAL VERSUS SEQUENTIAL LOGIC
# ============================================================================

def combinational_half_adder(a: int, b: int) -> Tuple[int, int]:
    """
    Half adder.

    Sum = A XOR B
    Carry = A AND B

    There is no stored state. The output depends only on current inputs.
    """
    validate_bit(a)
    validate_bit(b)
    return logic_xor(a, b), logic_and(a, b)


def combinational_full_adder(a: int, b: int, carry_in: int) -> Tuple[int, int]:
    """
    Full adder.

    A full adder processes two data bits plus an incoming carry.
    """
    validate_bit(a)
    validate_bit(b)
    validate_bit(carry_in)

    sum_bit = logic_xor(a, b, carry_in)
    carry_out = logic_or(
        logic_and(a, b),
        logic_and(a, carry_in),
        logic_and(b, carry_in),
    )
    return sum_bit, carry_out


def demonstrate_combinational_logic() -> None:
    print("\n=== Combinational Logic Baseline ===")
    print("Half adder truth table:")
    print("A B | SUM CARRY")
    for a in (0, 1):
        for b in (0, 1):
            sum_bit, carry = combinational_half_adder(a, b)
            print(f"{a} {b} |  {sum_bit}    {carry}")

    print("\nFull adder truth table:")
    print("A B Cin | SUM Cout")
    for a in (0, 1):
        for b in (0, 1):
            for carry_in in (0, 1):
                sum_bit, carry = combinational_full_adder(a, b, carry_in)
                print(f"{a} {b}  {carry_in}  |  {sum_bit}    {carry}")


# ============================================================================
# SECTION 3: CLOCK SIGNALS
# ============================================================================

class ClockLevel(Enum):
    LOW = 0
    HIGH = 1


@dataclass
class Clock:
    """
    Idealized digital clock.

    A real clock is a periodic electrical waveform. This educational model
    represents only its logical level and transition count.
    """

    period: float
    time: float = 0.0
    level: int = 0
    rising_edges: int = 0
    falling_edges: int = 0

    def __post_init__(self) -> None:
        if self.period <= 0:
            raise ValueError("Clock period must be positive.")
        validate_bit(self.level)

    @property
    def frequency(self) -> float:
        """Frequency in cycles per unit time."""
        return 1.0 / self.period

    def toggle(self) -> None:
        """Move the clock from LOW to HIGH or HIGH to LOW."""
        previous = self.level
        self.level = 1 - self.level

        if previous == 0 and self.level == 1:
            self.rising_edges += 1
        elif previous == 1 and self.level == 0:
            self.falling_edges += 1

    def advance_half_cycle(self) -> None:
        """Advance by half a period and toggle the clock."""
        self.time += self.period / 2
        self.toggle()

    def run_cycles(self, cycles: int) -> List[Tuple[float, int]]:
        """Generate clock samples at each half-cycle."""
        if cycles < 0:
            raise ValueError("cycles must not be negative.")

        samples = []
        for _ in range(cycles * 2):
            self.advance_half_cycle()
            samples.append((self.time, self.level))
        return samples


def demonstrate_clock() -> None:
    print("\n=== Clock Signal ===")
    clock = Clock(period=10.0)
    print(f"Period: {clock.period}")
    print(f"Frequency: {clock.frequency}")
    print("Transitions:")

    for time, level in clock.run_cycles(3):
        edge = "rising" if level else "falling"
        print(f"t={time:5.1f}  level={level}  {edge} edge")


# ============================================================================
# SECTION 4: SR LATCH
# ============================================================================

class SRLatch:
    """
    NOR-based active-high SR latch.

    Inputs:
        S = Set
        R = Reset

    Characteristic behavior:
        S=0, R=0 -> Hold previous state
        S=1, R=0 -> Set Q=1
        S=0, R=1 -> Reset Q=0
        S=1, R=1 -> Invalid/forbidden for a conventional NOR SR latch

    A latch is level-sensitive rather than edge-triggered.
    """

    def __init__(self) -> None:
        self.q = 0

    @property
    def q_bar(self) -> int:
        return logic_not(self.q)

    def apply(self, set_input: int, reset_input: int) -> int:
        validate_bit(set_input)
        validate_bit(reset_input)

        if set_input == 1 and reset_input == 1:
            raise ValueError("NOR SR latch has an invalid S=1, R=1 condition.")
        if set_input == 1:
            self.q = 1
        elif reset_input == 1:
            self.q = 0

        return self.q


def demonstrate_sr_latch() -> None:
    print("\n=== SR Latch ===")
    latch = SRLatch()

    sequence = [
        (0, 0),
        (1, 0),
        (0, 0),
        (0, 1),
        (0, 0),
    ]

    print("S R | Q")
    for set_input, reset_input in sequence:
        q = latch.apply(set_input, reset_input)
        print(f"{set_input} {reset_input} | {q}")


# ============================================================================
# SECTION 5: GATED SR LATCH
# ============================================================================

class GatedSRLatch:
    """
    SR latch controlled by an enable signal.

    When enable=0, the latch holds its state.
    When enable=1, S/R inputs can change the state.
    """

    def __init__(self) -> None:
        self.q = 0

    def apply(self, set_input: int, reset_input: int, enable: int) -> int:
        validate_bit(set_input)
        validate_bit(reset_input)
        validate_bit(enable)

        if enable == 0:
            return self.q

        if set_input == reset_input == 1:
            raise ValueError("Invalid gated SR latch condition.")

        if set_input:
            self.q = 1
        elif reset_input:
            self.q = 0

        return self.q


# ============================================================================
# SECTION 6: D LATCH
# ============================================================================

class DLatch:
    """
    Level-sensitive D latch.

    When enable=1:
        Q follows D.

    When enable=0:
        Q retains its previous state.

    The D latch removes the invalid S=R=1 combination found in an
    ordinary NOR SR latch by deriving S and R from a single D input.
    """

    def __init__(self, initial: int = 0) -> None:
        validate_bit(initial)
        self.q = initial

    def apply(self, d: int, enable: int) -> int:
        validate_bit(d)
        validate_bit(enable)

        if enable:
            self.q = d

        return self.q

    @property
    def q_bar(self) -> int:
        return logic_not(self.q)


def demonstrate_d_latch() -> None:
    print("\n=== D Latch ===")
    latch = DLatch()

    print("D EN | Q")
    sequence = [
        (1, 0),
        (0, 0),
        (1, 1),
        (0, 1),
        (1, 0),
        (0, 0),
    ]

    for d, enable in sequence:
        print(f"{d}  {enable}  | {latch.apply(d, enable)}")


# ============================================================================
# SECTION 7: FLIP-FLOP FOUNDATION
# ============================================================================

class Edge(Enum):
    RISING = 1
    FALLING = 0


class DFlipFlop:
    """
    Positive-edge-triggered D flip-flop.

    Q changes only on a rising clock edge.

    Between active edges, Q remains stable even if D changes.
    """

    def __init__(self, initial: int = 0) -> None:
        validate_bit(initial)
        self.q = initial
        self.previous_clock = 0

    @property
    def q_bar(self) -> int:
        return logic_not(self.q)

    def clock(self, d: int, clock: int) -> int:
        validate_bit(d)
        validate_bit(clock)

        rising_edge = self.previous_clock == 0 and clock == 1
        if rising_edge:
            self.q = d

        self.previous_clock = clock
        return self.q

    def reset(self) -> None:
        self.q = 0


def demonstrate_d_flip_flop() -> None:
    print("\n=== Positive-Edge D Flip-Flop ===")
    flip_flop = DFlipFlop()

    sequence = [
        (1, 0),
        (1, 1),
        (0, 1),
        (0, 0),
        (0, 1),
        (1, 1),
        (1, 0),
    ]

    print("D CLK | Q")
    for d, clock in sequence:
        q = flip_flop.clock(d, clock)
        print(f"{d}  {clock}   | {q}")


# ============================================================================
# SECTION 8: JK FLIP-FLOP
# ============================================================================

class JKFlipFlop:
    """
    Positive-edge-triggered JK flip-flop.

    Characteristic behavior:
        J=0, K=0 -> Hold
        J=0, K=1 -> Reset
        J=1, K=0 -> Set
        J=1, K=1 -> Toggle

    JK logic removes the invalid input combination of a basic SR latch.
    """

    def __init__(self, initial: int = 0) -> None:
        validate_bit(initial)
        self.q = initial
        self.previous_clock = 0

    def clock(self, j: int, k: int, clock: int) -> int:
        validate_bit(j)
        validate_bit(k)
        validate_bit(clock)

        rising_edge = self.previous_clock == 0 and clock == 1

        if rising_edge:
            if j == 0 and k == 0:
                pass
            elif j == 0 and k == 1:
                self.q = 0
            elif j == 1 and k == 0:
                self.q = 1
            else:
                self.q = logic_not(self.q)

        self.previous_clock = clock
        return self.q


def demonstrate_jk_flip_flop() -> None:
    print("\n=== JK Flip-Flop ===")
    flip_flop = JKFlipFlop()

    print("J K CLK | Q")
    test_cases = [
        (0, 0),
        (1, 0),
        (0, 0),
        (0, 1),
        (1, 1),
        (1, 1),
    ]

    clock = 0
    for j, k in test_cases:
        clock = 1
        q = flip_flop.clock(j, k, clock)
        print(f"{j} {k}  {clock}   | {q}")
        clock = 0
        flip_flop.clock(j, k, clock)


# ============================================================================
# SECTION 9: T FLIP-FLOP
# ============================================================================

class TFlipFlop:
    """
    Positive-edge-triggered T flip-flop.

    T=0 -> Hold
    T=1 -> Toggle

    T flip-flops are especially useful in binary counters.
    """

    def __init__(self, initial: int = 0) -> None:
        validate_bit(initial)
        self.q = initial
        self.previous_clock = 0

    def clock(self, t: int, clock: int) -> int:
        validate_bit(t)
        validate_bit(clock)

        rising_edge = self.previous_clock == 0 and clock == 1

        if rising_edge and t:
            self.q = logic_not(self.q)

        self.previous_clock = clock
        return self.q


def demonstrate_t_flip_flop() -> None:
    print("\n=== T Flip-Flop ===")
    flip_flop = TFlipFlop()

    clock = 0
    print("T CLK | Q")
    for _ in range(8):
        clock = 1
        q = flip_flop.clock(1, clock)
        print(f"1  {clock}   | {q}")
        clock = 0
        flip_flop.clock(1, clock)


# ============================================================================
# SECTION 10: CHARACTERISTIC AND EXCITATION TABLES
# ============================================================================

def print_flip_flop_tables() -> None:
    print("\n=== Flip-Flop Characteristic Tables ===")

    print("\nD flip-flop:")
    print("D | Q(next)")
    for d in (0, 1):
        print(f"{d} |   {d}")

    print("\nJK flip-flop:")
    print("J K | Q(next) when Q=0 | Q(next) when Q=1")
    for j in (0, 1):
        for k in (0, 1):
            ff = JKFlipFlop(initial=0)
            ff.clock(j, k, 0)
            q0 = ff.clock(j, k, 1)

            ff = JKFlipFlop(initial=1)
            ff.clock(j, k, 0)
            q1 = ff.clock(j, k, 1)

            print(f"{j} {k} |        {q0}          |        {q1}")

    print("\nT flip-flop:")
    print("T | Q(next)")
    for t in (0, 1):
        for q in (0, 1):
            next_q = q if t == 0 else logic_not(q)
            print(f"{t} | {next_q} when Q={q}")


# ============================================================================
# SECTION 11: TIMING CONCEPTS
# ============================================================================

@dataclass(frozen=True)
class TimingParameters:
    """
    Simplified timing model.

    setup_time:
        Minimum time data must be stable before the active edge.

    hold_time:
        Minimum time data must remain stable after the active edge.

    propagation_delay:
        Approximate delay between active clock edge and output response.
    """

    setup_time: float
    hold_time: float
    propagation_delay: float

    def __post_init__(self) -> None:
        if self.setup_time < 0:
            raise ValueError("setup_time cannot be negative.")
        if self.hold_time < 0:
            raise ValueError("hold_time cannot be negative.")
        if self.propagation_delay < 0:
            raise ValueError("propagation_delay cannot be negative.")


def timing_check(
    data_change_time: float,
    clock_edge_time: float,
    parameters: TimingParameters,
) -> Tuple[bool, bool]:
    """
    Check setup and hold requirements.

    Returns:
        (setup_ok, hold_ok)

    This is a conceptual check. Real timing analysis also depends on clock
    skew, jitter, routing, cell libraries, process/voltage/temperature
    conditions, and many other effects.
    """
    time_before_edge = clock_edge_time - data_change_time
    setup_ok = time_before_edge >= parameters.setup_time

    # A complete hold check requires a second data-transition timestamp.
    # This function uses only a setup-oriented interpretation.
    hold_ok = True

    return setup_ok, hold_ok


def demonstrate_timing() -> None:
    print("\n=== Timing Parameters ===")

    parameters = TimingParameters(
        setup_time=2.0,
        hold_time=1.0,
        propagation_delay=0.5,
    )

    for data_time in (6.0, 8.5, 9.5):
        setup_ok, hold_ok = timing_check(
            data_change_time=data_time,
            clock_edge_time=10.0,
            parameters=parameters,
        )
        print(
            f"Data transition at t={data_time:4.1f}: "
            f"setup_ok={setup_ok}, hold_check={hold_ok}"
        )

    print(
        "\nMetastability occurs when a storage element receives a transition "
        "too close to its sampling edge. A digital simulator cannot predict "
        "the analog resolution behavior of a real metastable device."
    )


# ============================================================================
# SECTION 12: REGISTER ABSTRACTION
# ============================================================================

class Register:
    """
    Parallel-load register built from conceptual D flip-flops.

    Each bit has its own storage element, and all bits are sampled on the
    same clock edge.
    """

    def __init__(self, width: int, initial: int = 0) -> None:
        if width <= 0:
            raise ValueError("Register width must be positive.")
        self.width = width
        self.bits = int_to_bits(initial, width)

    def load(self, value: int) -> None:
        self.bits = int_to_bits(value, self.width)

    def read(self) -> int:
        return bits_to_int(self.bits)

    def read_binary(self) -> str:
        return bits_to_string(self.bits)

    def clear(self) -> None:
        self.bits = [0] * self.width

    def set_all(self) -> None:
        self.bits = [1] * self.width

    def __repr__(self) -> str:
        return f"Register(width={self.width}, value={self.read()})"


def demonstrate_register() -> None:
    print("\n=== Parallel Register ===")
    register = Register(width=8)

    for value in (0, 5, 42, 255):
        register.load(value)
        print(
            f"Loaded decimal={value:3d}, "
            f"binary={register.read_binary()}, "
            f"read={register.read():3d}"
        )


# ============================================================================
# SECTION 13: SHIFT REGISTER
# ============================================================================

class ShiftDirection(Enum):
    LEFT = "left"
    RIGHT = "right"


class ShiftRegister:
    """
    Generic shift register.

    Bits are represented MSB -> LSB.

    A left shift moves every bit toward the MSB side and inserts a bit at
    the LSB side.

    A right shift moves every bit toward the LSB side and inserts a bit at
    the MSB side.
    """

    def __init__(self, width: int, initial: int = 0) -> None:
        if width <= 0:
            raise ValueError("Width must be positive.")
        self.width = width
        self.bits = int_to_bits(initial, width)

    def shift_left(self, serial_input: int = 0) -> int:
        validate_bit(serial_input)
        shifted_out = self.bits[0]
        self.bits = self.bits[1:] + [serial_input]
        return shifted_out

    def shift_right(self, serial_input: int = 0) -> int:
        validate_bit(serial_input)
        shifted_out = self.bits[-1]
        self.bits = [serial_input] + self.bits[:-1]
        return shifted_out

    def load(self, value: int) -> None:
        self.bits = int_to_bits(value, self.width)

    def read(self) -> int:
        return bits_to_int(self.bits)

    def binary(self) -> str:
        return bits_to_string(self.bits)


def demonstrate_shift_register() -> None:
    print("\n=== Shift Register ===")
    register = ShiftRegister(width=8, initial=0b10110010)
    print(f"Initial: {register.binary()}")

    for serial_bit in (1, 0, 1):
        shifted_out = register.shift_left(serial_bit)
        print(
            f"Input={serial_bit}, shifted_out={shifted_out}, "
            f"state={register.binary()}"
        )


# ============================================================================
# SECTION 14: SERIAL/PARALLEL CONVERSION
# ============================================================================

def serial_to_parallel(bits: Iterable[int], width: int) -> int:
    """
    Build an integer from serial bits arriving most-significant bit first.
    """
    register = ShiftRegister(width=width)

    for bit in bits:
        register.shift_left(bit)

    return register.read()


def parallel_to_serial(value: int, width: int) -> List[int]:
    """
    Convert a parallel value into MSB-first serial bits.
    """
    return int_to_bits(value, width)


def demonstrate_serial_parallel() -> None:
    print("\n=== Serial/Parallel Conversion ===")
    value = 0b11010110
    serial_bits = parallel_to_serial(value, 8)
    reconstructed = serial_to_parallel(serial_bits, 8)

    print(f"Parallel value:       {value}")
    print(f"Serial transmission:  {serial_bits}")
    print(f"Reconstructed value:  {reconstructed}")


# ============================================================================
# SECTION 15: SYNCHRONOUS BINARY COUNTER
# ============================================================================

class SynchronousUpCounter:
    """
    Synchronous modulo-2^width binary up-counter.

    Every bit conceptually updates on the same clock edge.

    State sequence for 3 bits:
        000 -> 001 -> 010 -> 011 -> 100 -> 101 -> 110 -> 111 -> 000
    """

    def __init__(self, width: int, initial: int = 0) -> None:
        if width <= 0:
            raise ValueError("Counter width must be positive.")
        self.width = width
        self.modulus = 2**width
        if not 0 <= initial < self.modulus:
            raise ValueError("Initial state does not fit the counter.")
        self.count = initial

    def tick(self) -> int:
        self.count = (self.count + 1) % self.modulus
        return self.count

    def reset(self) -> None:
        self.count = 0

    def binary(self) -> str:
        return bits_to_string(int_to_bits(self.count, self.width))


class SynchronousDownCounter:
    """Synchronous modulo-2^width binary down-counter."""

    def __init__(self, width: int, initial: int = 0) -> None:
        if width <= 0:
            raise ValueError("Counter width must be positive.")
        self.width = width
        self.modulus = 2**width
        if not 0 <= initial < self.modulus:
            raise ValueError("Initial state does not fit the counter.")
        self.count = initial

    def tick(self) -> int:
        self.count = (self.count - 1) % self.modulus
        return self.count

    def reset(self) -> None:
        self.count = 0

    def binary(self) -> str:
        return bits_to_string(int_to_bits(self.count, self.width))


def demonstrate_binary_counters() -> None:
    print("\n=== Synchronous Binary Counters ===")

    up = SynchronousUpCounter(width=3)
    print("Up counter:")
    for _ in range(10):
        print(up.binary(), end=" ")
        up.tick()

    print("\nDown counter:")
    down = SynchronousDownCounter(width=3, initial=7)
    for _ in range(10):
        print(down.binary(), end=" ")
        down.tick()

    print()


# ============================================================================
# SECTION 16: MODULO-N COUNTER
# ============================================================================

class ModuloCounter:
    """
    Counter that cycles through 0..modulus-1.

    A non-power-of-two modulus uses only a subset of the available binary
    states. A real implementation must deliberately handle unused states.
    """

    def __init__(self, modulus: int, initial: int = 0) -> None:
        if modulus <= 0:
            raise ValueError("Modulus must be positive.")
        if not 0 <= initial < modulus:
            raise ValueError("Initial value must be within the modulus.")
        self.modulus = modulus
        self.count = initial
        self.width = max(1, math.ceil(math.log2(modulus)))

    def tick(self) -> int:
        self.count = (self.count + 1) % self.modulus
        return self.count

    def reset(self) -> None:
        self.count = 0

    def binary(self) -> str:
        return bits_to_string(int_to_bits(self.count, self.width))


def demonstrate_modulo_counter() -> None:
    print("\n=== Modulo-10 Counter ===")
    counter = ModuloCounter(10)

    for _ in range(15):
        print(f"{counter.count} ({counter.binary()})", end=" -> ")
        counter.tick()

    print("repeat")


# ============================================================================
# SECTION 17: ASYNCHRONOUS/RIPPLE COUNTER
# ============================================================================

class RippleCounter:
    """
    Educational model of an asynchronous ripple counter.

    In a real ripple counter, one flip-flop's output clocks the next stage.
    Therefore the state does not change simultaneously across all bits.
    This produces propagation-delay-related transient states.

    This model records the conceptual bit-by-bit transition.
    """

    def __init__(self, width: int) -> None:
        if width <= 0:
            raise ValueError("Width must be positive.")
        self.width = width
        self.bits = [0] * width

    def tick(self) -> List[str]:
        transitions = []
        carry = 1

        for index in range(self.width - 1, -1, -1):
            if not carry:
                break

            old = self.bits[index]
            self.bits[index] = logic_not(old)

            transitions.append(bits_to_string(self.bits))
            carry = int(old == 1)

        return transitions

    def value(self) -> int:
        return bits_to_int(self.bits)


def demonstrate_ripple_counter() -> None:
    print("\n=== Asynchronous Ripple Counter ===")
    counter = RippleCounter(width=4)

    for tick_number in range(10):
        transitions = counter.tick()
        print(
            f"Tick {tick_number + 1:2d}: "
            f"transient sequence={transitions}, final={bits_to_string(counter.bits)}"
        )


# ============================================================================
# SECTION 18: RING COUNTER
# ============================================================================

class RingCounter:
    """
    One-hot ring counter.

    Example with four bits:
        1000 -> 0100 -> 0010 -> 0001 -> 1000

    A ring counter requires a valid one-hot starting state.
    """

    def __init__(self, width: int) -> None:
        if width < 2:
            raise ValueError("Ring counter width must be at least 2.")
        self.width = width
        self.bits = [1] + [0] * (width - 1)

    def tick(self) -> List[int]:
        self.bits = [self.bits[-1]] + self.bits[:-1]
        return self.bits.copy()

    def binary(self) -> str:
        return bits_to_string(self.bits)


def demonstrate_ring_counter() -> None:
    print("\n=== Ring Counter ===")
    counter = RingCounter(4)

    for _ in range(8):
        print(counter.binary())
        counter.tick()


# ============================================================================
# SECTION 19: JOHNSON COUNTER
# ============================================================================

class JohnsonCounter:
    """
    Twisted-ring or Johnson counter.

    The inverted output of the final stage is fed back into the first stage.

    For four bits, one common sequence is:
        0000
        1000
        1100
        1110
        1111
        0111
        0011
        0001
        0000
    """

    def __init__(self, width: int) -> None:
        if width < 2:
            raise ValueError("Johnson counter width must be at least 2.")
        self.width = width
        self.bits = [0] * width

    def tick(self) -> List[int]:
        feedback = logic_not(self.bits[-1])
        self.bits = [feedback] + self.bits[:-1]
        return self.bits.copy()

    def binary(self) -> str:
        return bits_to_string(self.bits)


def demonstrate_johnson_counter() -> None:
    print("\n=== Johnson Counter ===")
    counter = JohnsonCounter(4)

    for _ in range(10):
        print(counter.binary())
        counter.tick()


# ============================================================================
# SECTION 20: FREQUENCY DIVISION
# ============================================================================

def t_flip_flop_frequency_division(input_edges: int) -> int:
    """
    A T flip-flop configured with T=1 toggles at every active clock edge.

    Consequently:
        output frequency = input frequency / 2

    The function returns the number of output rising transitions in a simple
    idealized model after the specified number of input rising edges.
    """
    if input_edges < 0:
        raise ValueError("input_edges must not be negative.")

    q = 0
    output_rising_edges = 0

    for _ in range(input_edges):
        old_q = q
        q = logic_not(q)

        if old_q == 0 and q == 1:
            output_rising_edges += 1

    return output_rising_edges


def demonstrate_frequency_division() -> None:
    print("\n=== Frequency Division ===")
    input_edges = 20
    output_edges = t_flip_flop_frequency_division(input_edges)

    print(f"Input clock rising edges:  {input_edges}")
    print(f"Output rising transitions: {output_edges}")
    print("Ideal T flip-flop division ratio: 2:1")


# ============================================================================
# SECTION 21: RESET AND PRESET
# ============================================================================

class ResettableDFlipFlop(DFlipFlop):
    """
    D flip-flop with an asynchronous active-high reset.

    Reset dominates normal clocked operation in this simplified model.
    """

    def clock_with_reset(self, d: int, clock: int, reset: int) -> int:
        validate_bit(d)
        validate_bit(clock)
        validate_bit(reset)

        if reset:
            self.q = 0
            self.previous_clock = clock
            return self.q

        return self.clock(d, clock)


def demonstrate_reset() -> None:
    print("\n=== Resettable Flip-Flop ===")
    flip_flop = ResettableDFlipFlop(initial=1)

    print("Initial Q:", flip_flop.q)
    print("Clock with D=0:", flip_flop.clock_with_reset(0, 0, 0))
    print("Rising edge:", flip_flop.clock_with_reset(0, 1, 0))
    print("Reset asserted:", flip_flop.clock_with_reset(1, 1, 1))
    print("After reset removed:", flip_flop.clock_with_reset(1, 1, 0))


# ============================================================================
# SECTION 22: EDGE-TRIGGERED VERSUS LEVEL-SENSITIVE STORAGE
# ============================================================================

def compare_latch_and_flip_flop() -> None:
    print("\n=== Latch Versus Flip-Flop ===")

    latch = DLatch()
    flip_flop = DFlipFlop()

    print("D EN/CLK | Latch Q | Flip-Flop Q")

    samples = [
        (1, 0),
        (1, 1),
        (0, 1),
        (0, 0),
        (1, 0),
        (1, 1),
    ]

    for d, control in samples:
        latch_q = latch.apply(d, control)
        ff_q = flip_flop.clock(d, control)

        print(f"{d}    {control}    |    {latch_q}    |       {ff_q}")


# ============================================================================
# SECTION 23: REGISTER OPERATIONS
# ============================================================================

class UniversalShiftRegister(ShiftRegister):
    """
    Universal shift register supporting:

        HOLD
        SHIFT LEFT
        SHIFT RIGHT
        PARALLEL LOAD

    A hardware implementation would normally use multiplexers feeding
    flip-flop inputs.
    """

    def hold(self) -> None:
        pass

    def parallel_load(self, value: int) -> None:
        self.load(value)

    def operate(
        self,
        mode: str,
        serial_input: int = 0,
        parallel_value: Optional[int] = None,
    ) -> None:
        normalized_mode = mode.upper()

        if normalized_mode == "HOLD":
            return

        if normalized_mode == "LEFT":
            self.shift_left(serial_input)
        elif normalized_mode == "RIGHT":
            self.shift_right(serial_input)
        elif normalized_mode == "LOAD":
            if parallel_value is None:
                raise ValueError("LOAD requires parallel_value.")
            self.parallel_load(parallel_value)
        else:
            raise ValueError(f"Unknown shift-register mode: {mode}")


def demonstrate_universal_shift_register() -> None:
    print("\n=== Universal Shift Register ===")
    register = UniversalShiftRegister(8)

    operations = [
        ("LOAD", 0, 0b10011001),
        ("LEFT", 1, None),
        ("RIGHT", 0, None),
        ("HOLD", 0, None),
        ("LOAD", 0, 0b11110000),
        ("RIGHT", 1, None),
    ]

    for mode, serial_input, parallel_value in operations:
        register.operate(mode, serial_input, parallel_value)
        print(f"{mode:5s} -> {register.binary()}")


# ============================================================================
# SECTION 24: FINITE-STATE MACHINE
# ============================================================================

class TrafficState(Enum):
    RED = "RED"
    GREEN = "GREEN"
    YELLOW = "YELLOW"


class TrafficLightFSM:
    """
    Small Moore-style finite-state machine.

    The next state depends on the current state and an input condition.
    Output is determined by the current state.
    """

    def __init__(self) -> None:
        self.state = TrafficState.RED

    def tick(self, vehicle_waiting: bool = False) -> TrafficState:
        if self.state == TrafficState.RED:
            self.state = TrafficState.GREEN
        elif self.state == TrafficState.GREEN:
            if vehicle_waiting:
                self.state = TrafficState.GREEN
            else:
                self.state = TrafficState.YELLOW
        elif self.state == TrafficState.YELLOW:
            self.state = TrafficState.RED

        return self.state


def demonstrate_fsm() -> None:
    print("\n=== Finite-State Machine ===")
    fsm = TrafficLightFSM()

    for waiting in (False, False, False, True, False):
        state = fsm.tick(vehicle_waiting=waiting)
        print(f"vehicle_waiting={waiting:<5} -> state={state.value}")


# ============================================================================
# SECTION 25: SEQUENTIAL ARITHMETIC EXAMPLE
# ============================================================================

class Accumulator:
    """
    Synchronous accumulator.

    On each clock tick:
        register <= register + input

    The register therefore stores state between operations.
    """

    def __init__(self, width: int) -> None:
        if width <= 0:
            raise ValueError("Width must be positive.")
        self.width = width
        self.modulus = 2**width
        self.value = 0

    def tick(self, input_value: int) -> int:
        if not 0 <= input_value < self.modulus:
            raise ValueError("Input does not fit the accumulator.")
        self.value = (self.value + input_value) % self.modulus
        return self.value

    def reset(self) -> None:
        self.value = 0


def demonstrate_accumulator() -> None:
    print("\n=== Synchronous Accumulator ===")
    accumulator = Accumulator(width=8)

    for value in (10, 20, 50, 100, 100):
        result = accumulator.tick(value)
        print(f"input={value:3d}, accumulated={result:3d}")


# ============================================================================
# SECTION 26: EDGE CASES AND INVALID STATES
# ============================================================================

def demonstrate_edge_cases() -> None:
    print("\n=== Edge Cases ===")

    cases = [
        ("Invalid bit", lambda: validate_bit(2)),
        ("Negative register width", lambda: Register(-1)),
        ("Value too large", lambda: Register(4, 16)),
        ("Invalid modulo", lambda: ModuloCounter(0)),
        ("Invalid SR condition", lambda: SRLatch().apply(1, 1)),
        ("Invalid shift input", lambda: ShiftRegister(4).shift_left(2)),
    ]

    for description, operation in cases:
        try:
            operation()
        except ValueError as error:
            print(f"{description}: correctly rejected -> {error}")


# ============================================================================
# SECTION 27: SIMPLE TIMING DIAGRAM GENERATOR
# ============================================================================

def generate_clock_waveform(cycles: int) -> List[int]:
    """Return a simple list of 0/1 clock levels."""
    if cycles < 0:
        raise ValueError("cycles must not be negative.")

    waveform = []
    for _ in range(cycles):
        waveform.extend([0, 1])
    return waveform


def demonstrate_timing_waveform() -> None:
    print("\n=== Digital Timing Waveform ===")

    clock = generate_clock_waveform(8)
    data = [0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0]

    print("Index: ", " ".join(f"{i:02d}" for i in range(len(clock))))
    print("CLK:   ", " ".join(str(x) for x in clock))
    print("DATA:  ", " ".join(str(x) for x in data))

    print(
        "\nA positive-edge flip-flop samples DATA at transitions where "
        "CLK changes from 0 to 1."
    )


# ============================================================================
# SECTION 28: COUNTER DESIGN CALCULATIONS
# ============================================================================

def minimum_counter_bits(modulus: int) -> int:
    """
    Return the minimum number of bits required to represent modulus states.

    For a modulo-N counter:
        width = ceil(log2(N))
    """
    if modulus <= 0:
        raise ValueError("Modulus must be positive.")
    return max(1, math.ceil(math.log2(modulus)))


def demonstrate_counter_design() -> None:
    print("\n=== Counter Width Calculations ===")

    for modulus in (2, 3, 4, 5, 8, 10, 16, 17, 100, 256):
        width = minimum_counter_bits(modulus)
        available_states = 2**width
        unused_states = available_states - modulus

        print(
            f"Modulo {modulus:3d}: "
            f"{width:2d} bits, "
            f"{available_states:3d} binary states, "
            f"{unused_states:3d} unused states"
        )


# ============================================================================
# SECTION 29: SYNCHRONOUS COUNTER WITH ENABLE
# ============================================================================

class EnabledCounter:
    """
    Counter with synchronous enable and synchronous reset.

    At a clock event:
        reset -> count becomes zero
        enable=1 -> increment
        enable=0 -> hold
    """

    def __init__(self, width: int) -> None:
        if width <= 0:
            raise ValueError("Width must be positive.")
        self.width = width
        self.modulus = 2**width
        self.count = 0

    def tick(self, enable: int = 1, reset: int = 0) -> int:
        validate_bit(enable)
        validate_bit(reset)

        if reset:
            self.count = 0
        elif enable:
            self.count = (self.count + 1) % self.modulus

        return self.count


def demonstrate_enabled_counter() -> None:
    print("\n=== Enabled Counter ===")
    counter = EnabledCounter(width=4)

    operations = [
        (1, 0),
        (1, 0),
        (0, 0),
        (0, 0),
        (1, 0),
        (1, 1),
        (1, 0),
    ]

    for enable, reset in operations:
        value = counter.tick(enable, reset)
        print(f"enable={enable}, reset={reset} -> {value:04b}")


# ============================================================================
# SECTION 30: SYNCHRONOUS DATA PATH
# ============================================================================

class SynchronousPipeline:
    """
    Two-stage pipeline model.

    Stage 1 captures the input.
    Stage 2 captures stage 1's previous value.

    This demonstrates why registers are central to synchronous digital
    systems: they separate combinational work into timing stages.
    """

    def __init__(self) -> None:
        self.stage1 = 0
        self.stage2 = 0

    def tick(self, input_value: int) -> Tuple[int, int]:
        old_stage1 = self.stage1
        self.stage1 = input_value
        self.stage2 = old_stage1
        return self.stage1, self.stage2


def demonstrate_pipeline() -> None:
    print("\n=== Two-Stage Synchronous Pipeline ===")

    pipeline = SynchronousPipeline()

    for value in (10, 20, 30, 40, 50):
        stage1, stage2 = pipeline.tick(value)
        print(f"input={value:2d} -> stage1={stage1:2d}, stage2={stage2:2d}")


# ============================================================================
# SECTION 31: TESTING
# ============================================================================

def test_logic_gates() -> None:
    assert logic_not(0) == 1
    assert logic_not(1) == 0
    assert logic_and(1, 1) == 1
    assert logic_and(1, 0) == 0
    assert logic_or(0, 1) == 1
    assert logic_or(0, 0) == 0
    assert logic_xor(0, 1) == 1
    assert logic_xor(1, 1) == 0


def test_sr_latch() -> None:
    latch = SRLatch()
    assert latch.q == 0
    assert latch.apply(1, 0) == 1
    assert latch.apply(0, 0) == 1
    assert latch.apply(0, 1) == 0

    try:
        latch.apply(1, 1)
    except ValueError:
        pass
    else:
        raise AssertionError("SR latch should reject S=R=1.")


def test_d_latch() -> None:
    latch = DLatch()

    latch.apply(1, 1)
    assert latch.q == 1

    latch.apply(0, 0)
    assert latch.q == 1

    latch.apply(0, 1)
    assert latch.q == 0


def test_d_flip_flop() -> None:
    ff = DFlipFlop()

    ff.clock(1, 0)
    assert ff.q == 0

    ff.clock(1, 1)
    assert ff.q == 1

    ff.clock(0, 1)
    assert ff.q == 1

    ff.clock(0, 0)
    assert ff.q == 1

    ff.clock(0, 1)
    assert ff.q == 0


def test_jk_flip_flop() -> None:
    ff = JKFlipFlop()

    ff.clock(0, 0)
    ff.clock(0, 1)
    assert ff.q == 0

    ff.clock(0, 0)
    ff.clock(1, 1)
    assert ff.q == 1

    ff.clock(1, 0)
    ff.clock(1, 1)
    assert ff.q == 0


def test_t_flip_flop() -> None:
    ff = TFlipFlop()

    ff.clock(1, 0)
    ff.clock(1, 1)
    assert ff.q == 1

    ff.clock(1, 0)
    ff.clock(1, 1)
    assert ff.q == 0


def test_register() -> None:
    register = Register(8)
    register.load(173)
    assert register.read() == 173
    assert register.read_binary() == "10101101"

    register.clear()
    assert register.read() == 0


def test_shift_register() -> None:
    register = ShiftRegister(4, 0b1011)

    shifted_out = register.shift_left(0)
    assert shifted_out == 1
    assert register.read() == 0b0110

    shifted_out = register.shift_right(1)
    assert shifted_out == 0
    assert register.read() == 0b1011


def test_counters() -> None:
    up = SynchronousUpCounter(3, 7)
    assert up.tick() == 0

    down = SynchronousDownCounter(3, 0)
    assert down.tick() == 7

    modulo = ModuloCounter(10, 9)
    assert modulo.tick() == 0


def test_ring_counter() -> None:
    counter = RingCounter(4)
    assert counter.binary() == "1000"
    counter.tick()
    assert counter.binary() == "0100"


def test_johnson_counter() -> None:
    counter = JohnsonCounter(4)
    sequence = []

    for _ in range(8):
        sequence.append(counter.binary())
        counter.tick()

    assert len(set(sequence)) == 8


def run_tests() -> None:
    print("\n=== Automated Tests ===")

    tests = [
        test_logic_gates,
        test_sr_latch,
        test_d_latch,
        test_d_flip_flop,
        test_jk_flip_flop,
        test_t_flip_flop,
        test_register,
        test_shift_register,
        test_counters,
        test_ring_counter,
        test_johnson_counter,
    ]

    passed = 0

    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
        passed += 1

    print(f"{passed}/{len(tests)} tests passed.")


# ============================================================================
# SECTION 32: PRACTICAL DESIGN COMPARISON
# ============================================================================

def print_comparison_table() -> None:
    print("\n=== Sequential Logic Comparison ===")

    rows = [
        ("SR latch", "Level-sensitive", "Set/reset", "Basic storage"),
        ("D latch", "Level-sensitive", "D + enable", "Controlled storage"),
        ("D flip-flop", "Edge-triggered", "D", "Registers and pipelines"),
        ("JK flip-flop", "Edge-triggered", "J + K", "Toggle/set/reset"),
        ("T flip-flop", "Edge-triggered", "T", "Counters/dividers"),
        ("Register", "Clocked", "Multiple D bits", "Data storage"),
        ("Counter", "Clocked", "Clock/enable", "Counting/timing"),
    ]

    print(f"{'Device':<18} {'Timing':<18} {'Inputs':<18} {'Typical use'}")
    print("-" * 80)

    for device, timing, inputs, usage in rows:
        print(f"{device:<18} {timing:<18} {inputs:<18} {usage}")


# ============================================================================
# SECTION 33: COMMON DESIGN MISTAKES
# ============================================================================

def print_common_mistakes() -> None:
    print("\n=== Common Design Mistakes ===")

    mistakes = [
        (
            "Confusing a latch with a flip-flop",
            "A latch is level-sensitive; a conventional edge-triggered flip-flop "
            "samples on a clock edge."
        ),
        (
            "Ignoring setup and hold time",
            "Data that changes too close to the sampling edge can cause timing "
            "failure or metastability."
        ),
        (
            "Using ripple counters where simultaneous state changes are required",
            "Ripple propagation creates intermediate states and accumulated delay."
        ),
        (
            "Leaving unused modulo-counter states unmanaged",
            "A fault or disturbance can place the machine in an unused state."
        ),
        (
            "Treating reset as an ordinary data input",
            "Reset timing and whether it is synchronous or asynchronous matter "
            "to the architecture."
        ),
        (
            "Assuming simulation proves hardware timing correctness",
            "Digital functional simulation does not model every analog and "
            "physical timing effect."
        ),
        (
            "Creating unintended combinational feedback",
            "Feedback without deliberate storage or timing control can produce "
            "oscillation, instability, or synthesis problems."
        ),
    ]

    for name, explanation in mistakes:
        print(f"\n{name}")
        print(f"  {explanation}")


# ============================================================================
# SECTION 34: REAL-WORLD APPLICATIONS
# ============================================================================

def print_applications() -> None:
    print("\n=== Real-World Applications ===")

    applications = {
        "Latches": [
            "temporary data storage",
            "clock-gating and timing structures in appropriate designs",
            "control and interface circuits",
        ],
        "D flip-flops": [
            "CPU and microcontroller registers",
            "pipeline stages",
            "synchronizers",
            "state-machine storage",
        ],
        "Registers": [
            "processor registers",
            "configuration storage",
            "serial communication interfaces",
            "data buffering",
        ],
        "Counters": [
            "digital clocks",
            "event counting",
            "frequency division",
            "timers",
            "address generation",
        ],
        "Shift registers": [
            "serial-to-parallel conversion",
            "parallel-to-serial conversion",
            "delay lines",
            "LED and display control",
        ],
        "Finite-state machines": [
            "protocol controllers",
            "traffic controllers",
            "bus controllers",
            "instruction-control logic",
        ],
    }

    for category, examples in applications.items():
        print(f"\n{category}:")
        for example in examples:
            print(f"  - {example}")


# ============================================================================
# SECTION 35: DESIGN KNOWLEDGE CHECK
# ============================================================================

def knowledge_check() -> None:
    print("\n=== Knowledge Check ===")

    questions = [
        (
            "What distinguishes sequential logic from combinational logic?",
            "Sequential logic has state, so outputs can depend on previous inputs."
        ),
        (
            "What does a D flip-flop store?",
            "One binary data value, sampled according to its clocking behavior."
        ),
        (
            "What does a T flip-flop do when T=1?",
            "It toggles its state on each active clock edge."
        ),
        (
            "Why are registers built from multiple storage elements?",
            "Each storage element stores one bit, so multiple bits require multiple "
            "storage elements."
        ),
        (
            "Why does a modulo-10 counter need four bits?",
            "Four bits provide 16 possible binary states, enough for ten states."
        ),
        (
            "Why is metastability important?",
            "A physical storage element can enter an uncertain analog state when "
            "timing requirements are violated."
        ),
    ]

    for question, answer in questions:
        print(f"\nQ: {question}")
        print(f"A: {answer}")


# ============================================================================
# SECTION 36: COMPLETE MINI DIGITAL SYSTEM
# ============================================================================

class MiniDigitalSystem:
    """
    A compact synchronous system combining several concepts.

    Components:
        - 8-bit input register
        - 8-bit accumulator
        - modulo-16 counter
        - enable control

    Every operation occurs conceptually at a system clock tick.
    """

    def __init__(self) -> None:
        self.input_register = Register(8)
        self.accumulator = Accumulator(8)
        self.counter = EnabledCounter(4)

    def tick(self, input_value: int, enable: int = 1, reset: int = 0) -> dict:
        if not 0 <= input_value <= 255:
            raise ValueError("Input must fit in 8 bits.")

        if reset:
            self.input_register.clear()
            self.accumulator.reset()
            self.counter.tick(enable=0, reset=1)
        else:
            self.input_register.load(input_value)
            self.accumulator.tick(self.input_register.read())
            self.counter.tick(enable=enable, reset=0)

        return {
            "input_register": self.input_register.read(),
            "accumulator": self.accumulator.value,
            "counter": self.counter.count,
        }


def demonstrate_mini_system() -> None:
    print("\n=== Complete Mini Synchronous System ===")

    system = MiniDigitalSystem()

    for input_value, enable in [
        (10, 1),
        (20, 1),
        (30, 0),
        (40, 1),
        (50, 1),
    ]:
        state = system.tick(input_value, enable)
        print(
            f"input={input_value:3d}, enable={enable} -> "
            f"input_reg={state['input_register']:3d}, "
            f"accumulator={state['accumulator']:3d}, "
            f"counter={state['counter']:2d}"
        )

    print("Resetting system...")
    print(system.tick(0, enable=0, reset=1))


# ============================================================================
# SECTION 37: MAIN STUDY PROGRAM
# ============================================================================

def main() -> None:
    print("=" * 80)
    print("SEQUENTIAL LOGIC CIRCUITS: COMPLETE PYTHON STUDY PROGRAM")
    print("=" * 80)

    demonstrate_combinational_logic()
    demonstrate_clock()

    demonstrate_sr_latch()
    demonstrate_d_latch()
    demonstrate_d_flip_flop()
    demonstrate_jk_flip_flop()
    demonstrate_t_flip_flop()

    print_flip_flop_tables()
    demonstrate_timing()

    demonstrate_register()
    demonstrate_shift_register()
    demonstrate_serial_parallel()

    demonstrate_binary_counters()
    demonstrate_modulo_counter()
    demonstrate_ripple_counter()
    demonstrate_ring_counter()
    demonstrate_johnson_counter()
    demonstrate_frequency_division()

    demonstrate_reset()
    compare_latch_and_flip_flop()
    demonstrate_universal_shift_register()

    demonstrate_fsm()
    demonstrate_accumulator()
    demonstrate_edge_cases()
    demonstrate_timing_waveform()
    demonstrate_counter_design()
    demonstrate_enabled_counter()
    demonstrate_pipeline()

    run_tests()
    print_comparison_table()
    print_common_mistakes()
    print_applications()
    knowledge_check()
    demonstrate_mini_system()

    print("\n" + "=" * 80)
    print("END OF SEQUENTIAL LOGIC CIRCUITS STUDY PROGRAM")
    print("=" * 80)


if __name__ == "__main__":
    main()
