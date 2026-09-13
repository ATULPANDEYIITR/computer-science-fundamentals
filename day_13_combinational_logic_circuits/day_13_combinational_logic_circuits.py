"""
COMBINATIONAL LOGIC CIRCUITS
============================

Topic:
    Adders, subtractors, multiplexers, demultiplexers, encoders, and decoders.

Purpose:
    A standalone educational Python program that models important combinational
    logic circuits from beginner to advanced level.

The program uses Boolean values (0/1), truth-table generation, and functions
that model digital circuits. It demonstrates:

    1. Combinational logic fundamentals
    2. Boolean operations and basic gates
    3. Truth tables
    4. Half adder
    5. Full adder
    6. Ripple-carry adder
    7. Carry look-ahead concepts
    8. Half subtractor
    9. Full subtractor
    10. Multi-bit subtraction using two's complement
    11. Multiplexers
    12. Demultiplexers
    13. Encoders
    14. Priority encoders
    15. Decoders
    16. Decoder-based logic implementation
    17. Comparator circuits
    18. Seven-segment decoding
    19. Error detection and validation
    20. Propagation-delay simulation
    21. Glitch and hazard concepts
    22. Circuit composition
    23. Exhaustive testing
    24. Practical design considerations

No external packages are required.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Callable, Iterable, List, Optional, Sequence, Tuple


# ============================================================================
# SECTION 1: BASIC DIGITAL LOGIC REPRESENTATION
# ============================================================================

Bit = int


def validate_bit(value: int) -> Bit:
    """Validate and normalize a digital bit.

    A digital bit must be either 0 or 1. Boolean values are accepted because
    bool is a subclass of int in Python.
    """
    if value not in (0, 1, False, True):
        raise ValueError(f"Digital bit must be 0 or 1, received: {value!r}")
    return int(value)


def validate_bits(bits: Sequence[int]) -> List[Bit]:
    """Validate a sequence of digital bits."""
    return [validate_bit(bit) for bit in bits]


def bits_to_int(bits: Sequence[int]) -> int:
    """Convert a most-significant-bit-first bit sequence to an integer."""
    validated = validate_bits(bits)
    value = 0

    for bit in validated:
        value = (value << 1) | bit

    return value


def int_to_bits(value: int, width: int) -> List[Bit]:
    """Convert an integer to a fixed-width most-significant-bit-first list.

    Example:
        int_to_bits(5, 4) -> [0, 1, 0, 1]
    """
    if value < 0:
        raise ValueError("Unsigned integer conversion requires value >= 0.")

    if width <= 0:
        raise ValueError("Width must be positive.")

    if value >= (1 << width):
        raise ValueError(f"{value} cannot be represented using {width} bits.")

    return [(value >> position) & 1 for position in range(width - 1, -1, -1)]


def format_bits(bits: Sequence[int]) -> str:
    """Return a bit sequence as a readable binary string."""
    return "".join(str(validate_bit(bit)) for bit in bits)


# ============================================================================
# SECTION 2: BASIC LOGIC GATES
# ============================================================================

def NOT(a: int) -> Bit:
    """NOT gate: output is the complement of the input."""
    a = validate_bit(a)
    return 1 - a


def AND(a: int, b: int) -> Bit:
    """AND gate: output is 1 only when both inputs are 1."""
    return validate_bit(a) & validate_bit(b)


def OR(a: int, b: int) -> Bit:
    """OR gate: output is 1 when at least one input is 1."""
    return validate_bit(a) | validate_bit(b)


def XOR(a: int, b: int) -> Bit:
    """XOR gate: output is 1 when the inputs are different."""
    return validate_bit(a) ^ validate_bit(b)


def NAND(a: int, b: int) -> Bit:
    """NAND gate: complement of AND."""
    return NOT(AND(a, b))


def NOR(a: int, b: int) -> Bit:
    """NOR gate: complement of OR."""
    return NOT(OR(a, b))


def XNOR(a: int, b: int) -> Bit:
    """XNOR gate: output is 1 when the inputs are equal."""
    return NOT(XOR(a, b))


def demonstrate_basic_gates() -> None:
    """Print the truth table of the basic two-input gates."""
    print("\nBASIC LOGIC GATES")
    print("-" * 72)
    print("A B | AND OR XOR NAND NOR XNOR")

    for a, b in product((0, 1), repeat=2):
        print(
            f"{a} {b} |  {AND(a, b)}    {OR(a, b)}   {XOR(a, b)}"
            f"    {NAND(a, b)}    {NOR(a, b)}    {XNOR(a, b)}"
        )

    print("\nNOT")
    print("A | NOT")
    for a in (0, 1):
        print(f"{a} |  {NOT(a)}")


# ============================================================================
# SECTION 3: BOOLEAN IDENTITIES
# ============================================================================

def demonstrate_boolean_identities() -> None:
    """Verify several fundamental Boolean algebra identities.

    These identities are important because combinational circuits can often
    be simplified before hardware implementation.
    """
    print("\nBOOLEAN ALGEBRA IDENTITIES")
    print("-" * 72)

    identities = [
        (
            "A AND 1 = A",
            lambda a: AND(a, 1) == a,
        ),
        (
            "A OR 0 = A",
            lambda a: OR(a, 0) == a,
        ),
        (
            "A AND 0 = 0",
            lambda a: AND(a, 0) == 0,
        ),
        (
            "A OR 1 = 1",
            lambda a: OR(a, 1) == 1,
        ),
        (
            "A XOR 0 = A",
            lambda a: XOR(a, 0) == a,
        ),
        (
            "A XOR 1 = NOT(A)",
            lambda a: XOR(a, 1) == NOT(a),
        ),
        (
            "A XOR A = 0",
            lambda a: XOR(a, a) == 0,
        ),
        (
            "A XNOR A = 1",
            lambda a: XNOR(a, a) == 1,
        ),
    ]

    for description, test in identities:
        passed = all(test(a) for a in (0, 1))
        print(f"{description:<28} -> {'PASS' if passed else 'FAIL'}")


# ============================================================================
# SECTION 4: COMBINATIONAL LOGIC FUNDAMENTALS
# ============================================================================

def explain_combinational_logic() -> None:
    """Print the fundamental characteristics of combinational circuits."""
    print(
        """
COMBINATIONAL LOGIC

A combinational circuit is a digital circuit whose outputs are determined
by its current inputs.

Conceptually:

    Inputs -> Logic Network -> Outputs

For a combinational circuit:

    output(t) = F(input(t))

There is no stored previous state in the ideal Boolean model.

Examples:
    - Adders
    - Subtractors
    - Multiplexers
    - Demultiplexers
    - Encoders
    - Decoders
    - Comparators
    - Code converters

This differs from sequential logic, where outputs can depend on current
inputs and previous state. Flip-flops, registers, and counters are examples
of sequential circuits.

Important engineering properties include:
    - Number of inputs and outputs
    - Boolean function implemented
    - Gate count
    - Propagation delay
    - Fan-in and fan-out
    - Power consumption
    - Area
    - Glitch behavior
    - Testability
    - Hardware technology used
"""
    )


# ============================================================================
# SECTION 5: TRUTH TABLE UTILITIES
# ============================================================================

def generate_truth_table(
    input_count: int,
    circuit: Callable[..., Sequence[int]],
) -> List[Tuple[Tuple[int, ...], Tuple[int, ...]]]:
    """Generate every input/output combination for a combinational circuit."""
    if input_count <= 0:
        raise ValueError("input_count must be positive.")

    rows = []

    for inputs in product((0, 1), repeat=input_count):
        outputs = tuple(validate_bit(value) for value in circuit(*inputs))
        rows.append((inputs, outputs))

    return rows


def print_truth_table(
    input_names: Sequence[str],
    output_names: Sequence[str],
    circuit: Callable[..., Sequence[int]],
) -> None:
    """Print a truth table for a circuit."""
    rows = generate_truth_table(len(input_names), circuit)

    print(" ".join(f"{name:>5}" for name in input_names), end="")
    print(" |", end="")
    print(" ".join(f"{name:>5}" for name in output_names))

    print("-" * (6 * len(input_names) + 3 + 6 * len(output_names)))

    for inputs, outputs in rows:
        print(" ".join(f"{value:>5}" for value in inputs), end="")
        print(" |", end="")
        print(" ".join(f"{value:>5}" for value in outputs))


# ============================================================================
# SECTION 6: HALF ADDER
# ============================================================================

def half_adder(a: int, b: int) -> Tuple[Bit, Bit]:
    """Half adder.

    Inputs:
        a, b

    Outputs:
        sum = A XOR B
        carry = A AND B

    A half adder cannot accept an incoming carry from a previous bit.
    """
    a = validate_bit(a)
    b = validate_bit(b)

    sum_bit = XOR(a, b)
    carry = AND(a, b)

    return sum_bit, carry


def demonstrate_half_adder() -> None:
    """Display and verify the half-adder truth table."""
    print("\nHALF ADDER")
    print("-" * 72)
    print("A B | SUM CARRY")

    expected = {
        (0, 0): (0, 0),
        (0, 1): (1, 0),
        (1, 0): (1, 0),
        (1, 1): (0, 1),
    }

    for inputs in product((0, 1), repeat=2):
        result = half_adder(*inputs)
        print(f"{inputs[0]} {inputs[1]} |  {result[0]}     {result[1]}")
        assert result == expected[inputs]


# ============================================================================
# SECTION 7: FULL ADDER
# ============================================================================

def full_adder(a: int, b: int, carry_in: int) -> Tuple[Bit, Bit]:
    """Full adder.

    A full adder adds:
        A + B + CarryIn

    Equations:
        SUM   = A XOR B XOR CarryIn
        CARRY = AB + CarryIn(A XOR B)

    A full adder can be constructed from two half adders and one OR gate.
    """
    a = validate_bit(a)
    b = validate_bit(b)
    carry_in = validate_bit(carry_in)

    first_sum, first_carry = half_adder(a, b)
    final_sum, second_carry = half_adder(first_sum, carry_in)

    carry_out = OR(first_carry, second_carry)

    return final_sum, carry_out


def full_adder_direct(a: int, b: int, carry_in: int) -> Tuple[Bit, Bit]:
    """Full adder using direct Boolean equations."""
    a = validate_bit(a)
    b = validate_bit(b)
    carry_in = validate_bit(carry_in)

    sum_bit = XOR(XOR(a, b), carry_in)
    carry_out = OR(AND(a, b), AND(carry_in, XOR(a, b)))

    return sum_bit, carry_out


def demonstrate_full_adder() -> None:
    """Display the complete full-adder truth table."""
    print("\nFULL ADDER")
    print("-" * 72)
    print("A B Cin | SUM COUT")

    for inputs in product((0, 1), repeat=3):
        result = full_adder(*inputs)
        direct_result = full_adder_direct(*inputs)

        assert result == direct_result

        print(
            f"{inputs[0]} {inputs[1]}  {inputs[2]}  |"
            f"  {result[0]}    {result[1]}"
        )


# ============================================================================
# SECTION 8: MULTI-BIT RIPPLE-CARRY ADDER
# ============================================================================

@dataclass
class AdditionResult:
    """Result of a binary addition operation."""

    bits: List[Bit]
    carry_out: Bit

    @property
    def integer_value(self) -> int:
        """Return the unsigned integer represented by the result bits."""
        return bits_to_int(self.bits)


def ripple_carry_adder(
    a_bits: Sequence[int],
    b_bits: Sequence[int],
    carry_in: int = 0,
) -> AdditionResult:
    """Add two equal-width binary numbers using cascaded full adders.

    Bits are supplied most-significant-bit first.

    Internally, addition starts at the least-significant bit because carry
    information flows toward more significant positions.
    """
    a = validate_bits(a_bits)
    b = validate_bits(b_bits)
    carry = validate_bit(carry_in)

    if len(a) != len(b):
        raise ValueError("Both operands must have the same width.")

    result_reversed: List[Bit] = []

    for index in range(len(a) - 1, -1, -1):
        sum_bit, carry = full_adder(a[index], b[index], carry)
        result_reversed.append(sum_bit)

    return AdditionResult(
        bits=list(reversed(result_reversed)),
        carry_out=carry,
    )


def demonstrate_ripple_carry_adder() -> None:
    """Demonstrate several multi-bit additions."""
    print("\nRIPPLE-CARRY ADDER")
    print("-" * 72)

    examples = [
        (3, 5, 4),
        (7, 8, 5),
        (15, 1, 4),
        (10, 6, 5),
    ]

    for a_value, b_value, width in examples:
        a_bits = int_to_bits(a_value, width)
        b_bits = int_to_bits(b_value, width)
        result = ripple_carry_adder(a_bits, b_bits)

        combined_value = (result.carry_out << width) | result.integer_value

        print(
            f"{a_value:>3} + {b_value:<3} = "
            f"{combined_value:<3}   "
            f"{format_bits(a_bits)} + {format_bits(b_bits)} "
            f"-> {result.carry_out}{format_bits(result.bits)}"
        )

        assert combined_value == a_value + b_value


# ============================================================================
# SECTION 9: CARRY PROPAGATE AND GENERATE
# ============================================================================

def carry_propagate(a: int, b: int) -> Bit:
    """Carry-propagate term for a bit position.

    Using the XOR definition:
        P = A XOR B

    A carry entering this position propagates through when A and B differ.
    """
    return XOR(a, b)


def carry_generate(a: int, b: int) -> Bit:
    """Carry-generate term.

    G = A AND B

    A carry is generated at the current position when both inputs are 1.
    """
    return AND(a, b)


def demonstrate_carry_logic() -> None:
    """Show generate and propagate behavior."""
    print("\nCARRY GENERATE AND PROPAGATE")
    print("-" * 72)
    print("A B | P=A XOR B | G=A AND B")

    for a, b in product((0, 1), repeat=2):
        print(
            f"{a} {b} |"
            f"     {carry_propagate(a, b)}     |"
            f"      {carry_generate(a, b)}"
        )


def carry_lookahead_4bit(
    a_bits: Sequence[int],
    b_bits: Sequence[int],
    carry_in: int = 0,
) -> AdditionResult:
    """Four-bit carry-lookahead addition.

    The equations are:

        C1 = G0 + P0*C0
        C2 = G1 + P1*G0 + P1*P0*C0
        C3 = G2 + P2*G1 + P2*P1*G0 + P2*P1*P0*C0
        C4 = G3 + P3*G2 + P3*P2*G1
             + P3*P2*P1*G0 + P3*P2*P1*P0*C0

    The implementation uses integer Boolean operations to model these
    equations. A real hardware implementation would use gates arranged
    to compute these terms in parallel.
    """
    a = validate_bits(a_bits)
    b = validate_bits(b_bits)
    carry_in = validate_bit(carry_in)

    if len(a) != 4 or len(b) != 4:
        raise ValueError("Carry-lookahead demonstration requires exactly 4 bits.")

    # Convert MSB-first representation to positions 0..3 = LSB..MSB.
    a0, a1, a2, a3 = reversed(a)
    b0, b1, b2, b3 = reversed(b)

    p0, p1, p2, p3 = (
        carry_propagate(a0, b0),
        carry_propagate(a1, b1),
        carry_propagate(a2, b2),
        carry_propagate(a3, b3),
    )

    g0, g1, g2, g3 = (
        carry_generate(a0, b0),
        carry_generate(a1, b1),
        carry_generate(a2, b2),
        carry_generate(a3, b3),
    )

    c0 = carry_in

    c1 = OR(g0, AND(p0, c0))

    c2 = OR(
        g1,
        OR(
            AND(p1, g0),
            AND(AND(p1, p0), c0),
        ),
    )

    c3 = OR(
        g2,
        OR(
            AND(p2, g1),
            OR(
                AND(AND(p2, p1), g0),
                AND(AND(AND(p2, p1), p0), c0),
            ),
        ),
    )

    c4 = OR(
        g3,
        OR(
            AND(p3, g2),
            OR(
                AND(AND(p3, p2), g1),
                OR(
                    AND(AND(AND(p3, p2), p1), g0),
                    AND(AND(AND(AND(p3, p2), p1), p0), c0),
                ),
            ),
        ),
    )

    s0 = XOR(p0, c0)
    s1 = XOR(p1, c1)
    s2 = XOR(p2, c2)
    s3 = XOR(p3, c3)

    return AdditionResult(
        bits=[s3, s2, s1, s0],
        carry_out=c4,
    )


# ============================================================================
# SECTION 10: HALF SUBTRACTOR
# ============================================================================

def half_subtractor(a: int, b: int) -> Tuple[Bit, Bit]:
    """Half subtractor.

    Computes:
        A - B

    Outputs:
        Difference = A XOR B
        Borrow     = NOT(A) AND B

    A half subtractor has no borrow-in input.
    """
    a = validate_bit(a)
    b = validate_bit(b)

    difference = XOR(a, b)
    borrow = AND(NOT(a), b)

    return difference, borrow


def demonstrate_half_subtractor() -> None:
    """Display the half-subtractor truth table."""
    print("\nHALF SUBTRACTOR")
    print("-" * 72)
    print("A B | DIFFERENCE BORROW")

    for a, b in product((0, 1), repeat=2):
        difference, borrow = half_subtractor(a, b)
        print(f"{a} {b} |     {difference}        {borrow}")


# ============================================================================
# SECTION 11: FULL SUBTRACTOR
# ============================================================================

def full_subtractor(
    a: int,
    b: int,
    borrow_in: int,
) -> Tuple[Bit, Bit]:
    """Full subtractor.

    Computes:

        A - B - BorrowIn

    Equations:

        Difference = A XOR B XOR BorrowIn

        BorrowOut = (~A AND B)
                    OR (~A AND BorrowIn)
                    OR (B AND BorrowIn)

    A full subtractor can also be constructed from two half subtractors and
    an OR gate.
    """
    a = validate_bit(a)
    b = validate_bit(b)
    borrow_in = validate_bit(borrow_in)

    first_difference, first_borrow = half_subtractor(a, b)
    final_difference, second_borrow = half_subtractor(
        first_difference,
        borrow_in,
    )

    borrow_out = OR(first_borrow, second_borrow)

    return final_difference, borrow_out


def demonstrate_full_subtractor() -> None:
    """Display and validate the full-subtractor truth table."""
    print("\nFULL SUBTRACTOR")
    print("-" * 72)
    print("A B Bin | DIFF BOUT")

    for inputs in product((0, 1), repeat=3):
        result = full_subtractor(*inputs)

        a, b, borrow_in = inputs

        # Mathematical validation:
        # If the raw result is negative, one borrow of 2 is required at
        # this one-bit position.
        raw = a - b - borrow_in
        expected_difference = raw % 2
        expected_borrow = 1 if raw < 0 else 0

        assert result == (expected_difference, expected_borrow)

        print(
            f"{a} {b}  {borrow_in}  |"
            f"   {result[0]}     {result[1]}"
        )


# ============================================================================
# SECTION 12: TWO'S COMPLEMENT SUBTRACTION
# ============================================================================

def invert_bits(bits: Sequence[int]) -> List[Bit]:
    """Invert every bit in a sequence."""
    return [NOT(bit) for bit in validate_bits(bits)]


def twos_complement(bits: Sequence[int]) -> List[Bit]:
    """Return the two's complement of a fixed-width bit sequence."""
    validated = validate_bits(bits)

    inverted = invert_bits(validated)

    one = int_to_bits(1, len(validated))
    result = ripple_carry_adder(inverted, one)

    return result.bits


def unsigned_subtraction(
    a_value: int,
    b_value: int,
    width: int,
) -> Tuple[List[Bit], Bit]:
    """Perform fixed-width subtraction using two's complement.

    The operation is:

        A - B = A + two's_complement(B)

    The returned bit pattern is the width-bit result. The final carry is also
    returned because fixed-width arithmetic can overflow or wrap.
    """
    if not (0 <= a_value < (1 << width)):
        raise ValueError("a_value does not fit the selected width.")

    if not (0 <= b_value < (1 << width)):
        raise ValueError("b_value does not fit the selected width.")

    a_bits = int_to_bits(a_value, width)
    b_bits = int_to_bits(b_value, width)

    negative_b = twos_complement(b_bits)
    result = ripple_carry_adder(a_bits, negative_b)

    return result.bits, result.carry_out


def signed_twos_complement_value(bits: Sequence[int]) -> int:
    """Interpret a fixed-width bit sequence as a signed two's-complement value."""
    validated = validate_bits(bits)
    width = len(validated)
    unsigned_value = bits_to_int(validated)

    if validated[0] == 0:
        return unsigned_value

    return unsigned_value - (1 << width)


def demonstrate_twos_complement() -> None:
    """Demonstrate positive and negative fixed-width subtraction."""
    print("\nTWO'S COMPLEMENT SUBTRACTION")
    print("-" * 72)

    width = 5
    examples = [
        (13, 5),
        (5, 13),
        (9, 9),
        (0, 1),
    ]

    for a, b in examples:
        result_bits, carry = unsigned_subtraction(a, b, width)
        signed_result = signed_twos_complement_value(result_bits)

        print(
            f"{a:>2} - {b:<2} -> "
            f"{format_bits(result_bits)} "
            f"(signed interpretation: {signed_result:>3}, carry={carry})"
        )


# ============================================================================
# SECTION 13: ADDER-SUBTRACTOR
# ============================================================================

def add_subtract(
    a_bits: Sequence[int],
    b_bits: Sequence[int],
    subtract: int = 0,
) -> AdditionResult:
    """Perform addition or subtraction using one controlled adder.

    When subtract = 0:
        A + B

    When subtract = 1:
        A + (~B) + 1
        A - B

    The XOR gates conditionally invert B when subtraction is requested.
    The subtraction control is also used as the initial carry-in.
    """
    a = validate_bits(a_bits)
    b = validate_bits(b_bits)
    subtract = validate_bit(subtract)

    if len(a) != len(b):
        raise ValueError("Operands must have equal width.")

    modified_b = [XOR(bit, subtract) for bit in b]

    return ripple_carry_adder(
        a,
        modified_b,
        carry_in=subtract,
    )


def demonstrate_adder_subtractor() -> None:
    """Demonstrate one circuit performing both addition and subtraction."""
    print("\nCOMBINATIONAL ADDER-SUBTRACTOR")
    print("-" * 72)

    width = 5

    for a, b, subtract in [
        (12, 5, 0),
        (12, 5, 1),
        (5, 12, 1),
    ]:
        result = add_subtract(
            int_to_bits(a, width),
            int_to_bits(b, width),
            subtract,
        )

        raw = (result.carry_out << width) | result.integer_value

        operation = "-" if subtract else "+"
        print(
            f"{a:>2} {operation} {b:<2} -> "
            f"{format_bits(result.bits)} "
            f"(raw fixed-width result={raw})"
        )


# ============================================================================
# SECTION 14: MULTIPLEXERS
# ============================================================================

def multiplexer_2_to_1(d0: int, d1: int, select: int) -> Bit:
    """2-to-1 multiplexer.

    select = 0 -> output D0
    select = 1 -> output D1

    Boolean equation:

        Y = (~S AND D0) OR (S AND D1)
    """
    d0 = validate_bit(d0)
    d1 = validate_bit(d1)
    select = validate_bit(select)

    return OR(
        AND(NOT(select), d0),
        AND(select, d1),
    )


def multiplexer_4_to_1(
    d0: int,
    d1: int,
    d2: int,
    d3: int,
    s1: int,
    s0: int,
) -> Bit:
    """4-to-1 multiplexer.

    Select mapping:

        S1 S0
         0  0 -> D0
         0  1 -> D1
         1  0 -> D2
         1  1 -> D3
    """
    data = [validate_bit(d) for d in (d0, d1, d2, d3)]
    s1 = validate_bit(s1)
    s0 = validate_bit(s0)

    index = (s1 << 1) | s0
    return data[index]


def multiplexer(
    data_inputs: Sequence[int],
    select_bits: Sequence[int],
) -> Bit:
    """General power-of-two multiplexer.

    For N select lines, the number of data inputs is 2**N.
    """
    data = validate_bits(data_inputs)
    selects = validate_bits(select_bits)

    expected_inputs = 1 << len(selects)

    if len(data) != expected_inputs:
        raise ValueError(
            f"{len(selects)} select lines require "
            f"{expected_inputs} data inputs."
        )

    index = bits_to_int(selects)
    return data[index]


def demonstrate_multiplexers() -> None:
    """Demonstrate 2-to-1 and 4-to-1 multiplexers."""
    print("\nMULTIPLEXERS")
    print("-" * 72)

    print("2-to-1 multiplexer")
    for select in (0, 1):
        output = multiplexer_2_to_1(0, 1, select)
        print(f"D0=0, D1=1, S={select} -> Y={output}")

    print("\n4-to-1 multiplexer")
    data = [0, 1, 1, 0]

    for s1, s0 in product((0, 1), repeat=2):
        output = multiplexer_4_to_1(*data, s1, s0)
        print(f"S1S0={s1}{s0} -> selected value={output}")


# ============================================================================
# SECTION 15: MUX AS A UNIVERSAL FUNCTION IMPLEMENTATION TOOL
# ============================================================================

def implement_boolean_function_with_4_to_1_mux(
    inputs: Sequence[int],
) -> Bit:
    """Implement F(A,B,C) = Σm(1,2,5,7) using a 4-to-1 MUX.

    Select lines:
        A, B

    Data inputs depend on C:

        AB=00 -> D0 = C
        AB=01 -> D1 = NOT(C)
        AB=10 -> D2 = C
        AB=11 -> D3 = 1

    The function is useful for demonstrating that a multiplexer can implement
    arbitrary Boolean functions when its data inputs are connected to suitable
    constants or remaining variables.
    """
    if len(inputs) != 3:
        raise ValueError("Exactly three inputs A, B, C are required.")

    a, b, c = validate_bits(inputs)

    d0 = c
    d1 = NOT(c)
    d2 = c
    d3 = 1

    return multiplexer_4_to_1(d0, d1, d2, d3, a, b)


def demonstrate_mux_function_implementation() -> None:
    """Verify a Boolean function implemented using a MUX."""
    print("\nBOOLEAN FUNCTION USING A MULTIPLEXER")
    print("-" * 72)
    print("F(A,B,C) = Σm(1,2,5,7)")
    print("A B C | F")

    minterms = {1, 2, 5, 7}

    for inputs in product((0, 1), repeat=3):
        output = implement_boolean_function_with_4_to_1_mux(inputs)
        minterm = bits_to_int(inputs)
        expected = 1 if minterm in minterms else 0

        assert output == expected
        print(f"{inputs[0]} {inputs[1]} {inputs[2]} | {output}")


# ============================================================================
# SECTION 16: DEMULTIPLEXERS
# ============================================================================

def demultiplexer_1_to_2(
    data: int,
    select: int,
) -> Tuple[Bit, Bit]:
    """1-to-2 demultiplexer.

    The input is routed to exactly one output.

        S=0 -> (D, 0)
        S=1 -> (0, D)
    """
    data = validate_bit(data)
    select = validate_bit(select)

    y0 = AND(data, NOT(select))
    y1 = AND(data, select)

    return y0, y1


def demultiplexer_1_to_4(
    data: int,
    s1: int,
    s0: int,
) -> Tuple[Bit, Bit, Bit, Bit]:
    """1-to-4 demultiplexer."""
    data = validate_bit(data)
    s1 = validate_bit(s1)
    s0 = validate_bit(s0)

    outputs = [0, 0, 0, 0]
    outputs[(s1 << 1) | s0] = data

    return tuple(outputs)


def demultiplexer(
    data: int,
    select_bits: Sequence[int],
) -> List[Bit]:
    """General 1-to-N demultiplexer for N = 2**select_count."""
    data = validate_bit(data)
    selects = validate_bits(select_bits)

    output_count = 1 << len(selects)
    outputs = [0] * output_count

    outputs[bits_to_int(selects)] = data

    return outputs


def demonstrate_demultiplexers() -> None:
    """Demonstrate data routing through demultiplexers."""
    print("\nDEMULTIPLEXERS")
    print("-" * 72)

    for select in (0, 1):
        print(
            f"1-to-2: D=1, S={select} -> "
            f"{demultiplexer_1_to_2(1, select)}"
        )

    for selects in product((0, 1), repeat=2):
        output = demultiplexer_1_to_4(1, *selects)
        print(f"1-to-4: S={selects} -> {output}")


# ============================================================================
# SECTION 17: ENCODERS
# ============================================================================

def encoder_4_to_2(one_hot_inputs: Sequence[int]) -> Tuple[Bit, Bit]:
    """4-to-2 encoder.

    Valid one-hot inputs:

        0001 -> 00
        0010 -> 01
        0100 -> 10
        1000 -> 11

    A basic encoder assumes exactly one input is active.
    """
    inputs = validate_bits(one_hot_inputs)

    if len(inputs) != 4:
        raise ValueError("4-to-2 encoder requires four inputs.")

    if sum(inputs) != 1:
        raise ValueError(
            "Basic encoder requires exactly one active input."
        )

    active_index = inputs.index(1)

    return int_to_bits(active_index, 2)


def demonstrate_encoder() -> None:
    """Demonstrate valid and invalid encoder inputs."""
    print("\n4-TO-2 ENCODER")
    print("-" * 72)

    for active_index in range(4):
        one_hot = [0] * 4
        one_hot[active_index] = 1

        encoded = encoder_4_to_2(one_hot)

        print(
            f"{format_bits(one_hot)} -> {format_bits(encoded)}"
        )

    print("\nInvalid multiple-active input:")
    try:
        encoder_4_to_2([0, 1, 1, 0])
    except ValueError as error:
        print(f"Rejected correctly: {error}")


# ============================================================================
# SECTION 18: PRIORITY ENCODER
# ============================================================================

def priority_encoder_4_to_2(
    inputs: Sequence[int],
) -> Tuple[Bit, Bit, Bit]:
    """4-to-2 priority encoder.

    Input 3 has the highest priority.

    Outputs:
        encoded_bit_1
        encoded_bit_0
        valid

    Example:
        0110 -> 10, valid=1

    Input 3 is active, so lower-priority inputs are ignored.
    """
    values = validate_bits(inputs)

    if len(values) != 4:
        raise ValueError("Priority encoder requires four inputs.")

    for index in range(3, -1, -1):
        if values[index]:
            encoded = int_to_bits(index, 2)
            return encoded[0], encoded[1], 1

    return 0, 0, 0


def demonstrate_priority_encoder() -> None:
    """Demonstrate priority encoding."""
    print("\n4-TO-2 PRIORITY ENCODER")
    print("-" * 72)
    print("D3 D2 D1 D0 | Y1 Y0 VALID")

    examples = [
        [0, 0, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
        [0, 1, 0, 1],
        [1, 0, 0, 1],
        [1, 1, 1, 1],
    ]

    for inputs in examples:
        y1, y0, valid = priority_encoder_4_to_2(inputs)
        print(
            f"{format_bits(inputs)}   |"
            f"  {y1}  {y0}    {valid}"
        )


# ============================================================================
# SECTION 19: DECODERS
# ============================================================================

def decoder_2_to_4(
    a: int,
    b: int,
    enable: int = 1,
) -> Tuple[Bit, Bit, Bit, Bit]:
    """2-to-4 decoder with active-high enable.

    When enabled, exactly one output is high:

        AB=00 -> 0001
        AB=01 -> 0010
        AB=10 -> 0100
        AB=11 -> 1000

    When disabled, all outputs are 0.
    """
    a = validate_bit(a)
    b = validate_bit(b)
    enable = validate_bit(enable)

    if not enable:
        return 0, 0, 0, 0

    outputs = [0, 0, 0, 0]
    outputs[(a << 1) | b] = 1

    return tuple(outputs)


def decoder(
    select_bits: Sequence[int],
    enable: int = 1,
) -> List[Bit]:
    """General active-high binary decoder."""
    selects = validate_bits(select_bits)
    enable = validate_bit(enable)

    outputs = [0] * (1 << len(selects))

    if enable:
        outputs[bits_to_int(selects)] = 1

    return outputs


def demonstrate_decoders() -> None:
    """Demonstrate 2-to-4 and general decoder behavior."""
    print("\nDECODERS")
    print("-" * 72)

    for a, b in product((0, 1), repeat=2):
        outputs = decoder_2_to_4(a, b)
        print(f"{a}{b} -> {format_bits(outputs)}")

    print("\n3-to-8 decoder:")
    for inputs in product((0, 1), repeat=3):
        outputs = decoder(inputs)
        print(f"{format_bits(inputs)} -> {format_bits(outputs)}")


# ============================================================================
# SECTION 20: DECODER AS A MINTERM GENERATOR
# ============================================================================

def boolean_function_from_minterms(
    inputs: Sequence[int],
    minterms: Iterable[int],
) -> Bit:
    """Implement a sum-of-minterms Boolean function.

    A decoder produces one-hot minterm lines. ORing the selected minterms
    implements a sum-of-products function.
    """
    values = validate_bits(inputs)
    minterm_set = set(minterms)

    current_minterm = bits_to_int(values)

    return 1 if current_minterm in minterm_set else 0


def demonstrate_decoder_function_implementation() -> None:
    """Demonstrate implementation of F(A,B,C) = Σm(0,3,5,6)."""
    print("\nBOOLEAN FUNCTION USING DECODER MINTERMS")
    print("-" * 72)

    minterms = {0, 3, 5, 6}

    print("F(A,B,C) = Σm(0,3,5,6)")
    print("A B C | F")

    for inputs in product((0, 1), repeat=3):
        output = boolean_function_from_minterms(inputs, minterms)
        print(f"{inputs[0]} {inputs[1]} {inputs[2]} | {output}")


# ============================================================================
# SECTION 21: COMPARATORS
# ============================================================================

def one_bit_comparator(a: int, b: int) -> Tuple[Bit, Bit, Bit]:
    """Compare two one-bit values.

    Outputs:
        A > B
        A = B
        A < B
    """
    a = validate_bit(a)
    b = validate_bit(b)

    greater = AND(a, NOT(b))
    equal = XNOR(a, b)
    less = AND(NOT(a), b)

    return greater, equal, less


def magnitude_comparator(
    a_value: int,
    b_value: int,
    width: int,
) -> Tuple[Bit, Bit, Bit]:
    """Compare two unsigned fixed-width integers using bit-level logic.

    Comparison starts from the most significant bit. Once a higher-order
    position differs, lower-order positions no longer determine the result.
    """
    a_bits = int_to_bits(a_value, width)
    b_bits = int_to_bits(b_value, width)

    for a_bit, b_bit in zip(a_bits, b_bits):
        greater, equal, less = one_bit_comparator(a_bit, b_bit)

        if greater:
            return 1, 0, 0

        if less:
            return 0, 0, 1

        # If equal, continue toward the next lower bit.

    return 0, 1, 0


def demonstrate_comparator() -> None:
    """Demonstrate unsigned magnitude comparison."""
    print("\nMAGNITUDE COMPARATOR")
    print("-" * 72)

    for a, b in [(3, 5), (9, 4), (7, 7), (15, 1)]:
        result = magnitude_comparator(a, b, 4)
        print(
            f"A={a:>2}, B={b:<2} -> "
            f"A>B={result[0]}, A=B={result[1]}, A<B={result[2]}"
        )


# ============================================================================
# SECTION 22: SEVEN-SEGMENT DECODER
# ============================================================================

SEGMENT_NAMES = ("a", "b", "c", "d", "e", "f", "g")

# Segment order:
#
#       a
#      ---
#   f |   | b
#      -g-
#   e |   | c
#      ---
#       d
#
# Each tuple uses 1 = segment ON, 0 = segment OFF.
SEVEN_SEGMENT_DIGITS = {
    0: (1, 1, 1, 1, 1, 1, 0),
    1: (0, 1, 1, 0, 0, 0, 0),
    2: (1, 1, 0, 1, 1, 0, 1),
    3: (1, 1, 1, 1, 0, 0, 1),
    4: (0, 1, 1, 0, 0, 1, 1),
    5: (1, 0, 1, 1, 0, 1, 1),
    6: (1, 0, 1, 1, 1, 1, 1),
    7: (1, 1, 1, 0, 0, 0, 0),
    8: (1, 1, 1, 1, 1, 1, 1),
    9: (1, 1, 1, 1, 0, 1, 1),
}


def seven_segment_decoder(digit: int) -> Tuple[Bit, ...]:
    """Convert decimal digit 0-9 to seven-segment control signals."""
    if digit not in SEVEN_SEGMENT_DIGITS:
        raise ValueError("Seven-segment decoder accepts digits 0 through 9.")

    return SEVEN_SEGMENT_DIGITS[digit]


def render_seven_segment(digit: int) -> str:
    """Render a seven-segment digit as text."""
    segments = seven_segment_decoder(digit)

    a, b, c, d, e, f, g = segments

    line_1 = f" {'---' if a else '   '} "
    line_2 = f"{'|' if f else ' '}   {'|' if b else ' '}"
    line_3 = f" {'---' if g else '   '} "
    line_4 = f"{'|' if e else ' '}   {'|' if c else ' '}"
    line_5 = f" {'---' if d else '   '} "

    return "\n".join((line_1, line_2, line_3, line_4, line_5))


def demonstrate_seven_segment() -> None:
    """Display a seven-segment representation of several digits."""
    print("\nSEVEN-SEGMENT DECODER")
    print("-" * 72)

    for digit in (0, 2, 4, 7, 8, 9):
        print(f"Digit {digit}:")
        print(render_seven_segment(digit))
        print()


# ============================================================================
# SECTION 23: CIRCUIT COMPOSITION
# ============================================================================

def full_adder_using_mux(
    a: int,
    b: int,
    carry_in: int,
) -> Tuple[Bit, Bit]:
    """Build a full adder conceptually from multiplexers.

    A MUX can implement arbitrary Boolean functions. Here, two MUX structures
    are used as truth-table selectors for SUM and CARRY.
    """
    inputs = (validate_bit(a), validate_bit(b), validate_bit(carry_in))
    index = bits_to_int(inputs)

    sum_truth_table = [
        0, 1, 1, 0,
        1, 0, 0, 1,
    ]

    carry_truth_table = [
        0, 0, 0, 1,
        0, 1, 1, 1,
    ]

    # An 8-to-1 MUX can select directly using the three input variables.
    sum_bit = multiplexer(sum_truth_table, inputs)
    carry_out = multiplexer(carry_truth_table, inputs)

    return sum_bit, carry_out


def demonstrate_circuit_composition() -> None:
    """Verify a full adder built using multiplexer selection."""
    print("\nCIRCUIT COMPOSITION: FULL ADDER USING MUX LOGIC")
    print("-" * 72)

    for inputs in product((0, 1), repeat=3):
        mux_result = full_adder_using_mux(*inputs)
        normal_result = full_adder(*inputs)

        assert mux_result == normal_result

        print(
            f"{format_bits(inputs)} -> "
            f"SUM={mux_result[0]}, CARRY={mux_result[1]}"
        )


# ============================================================================
# SECTION 24: PROPAGATION DELAY MODEL
# ============================================================================

@dataclass(frozen=True)
class Signal:
    """A digital signal with an associated arrival time."""

    value: Bit
    time: float


def delayed_not(signal: Signal, delay: float) -> Signal:
    """Model a NOT gate with propagation delay."""
    return Signal(NOT(signal.value), signal.time + delay)


def delayed_and(a: Signal, b: Signal, delay: float) -> Signal:
    """Model an AND gate with propagation delay."""
    return Signal(
        AND(a.value, b.value),
        max(a.time, b.time) + delay,
    )


def delayed_or(a: Signal, b: Signal, delay: float) -> Signal:
    """Model an OR gate with propagation delay."""
    return Signal(
        OR(a.value, b.value),
        max(a.time, b.time) + delay,
    )


def demonstrate_propagation_delay() -> None:
    """Illustrate why a real circuit does not change instantaneously."""
    print("\nPROPAGATION DELAY MODEL")
    print("-" * 72)

    # Example:
    # Y = A AND (NOT B)
    # NOT and AND have different arrival times.
    a = Signal(1, 0.0)
    b = Signal(1, 0.0)

    not_b = delayed_not(b, delay=2.0)
    output = delayed_and(a, not_b, delay=3.0)

    print(f"B arrives at t={b.time:.1f}")
    print(f"NOT(B) arrives at t={not_b.time:.1f}")
    print(f"Y arrives at t={output.time:.1f}")
    print(f"Y value = {output.value}")


# ============================================================================
# SECTION 25: HAZARD / GLITCH DEMONSTRATION
# ============================================================================

def explain_hazards() -> None:
    """Print an explanation of combinational hazards."""
    print(
        """
COMBINATIONAL HAZARDS

A Boolean expression can be logically correct in the steady state while
the physical gate network temporarily produces an incorrect output during
an input transition.

This temporary incorrect pulse is called a glitch or hazard.

Common types:

    Static-1 hazard:
        The output should remain 1 but temporarily falls to 0.

    Static-0 hazard:
        The output should remain 0 but temporarily rises to 1.

    Dynamic hazard:
        The output changes multiple times before reaching its final value.

Causes include:
    - Unequal propagation delays
    - Different gate depths
    - Physical routing differences
    - Simultaneous input transitions

Important design techniques include:
    - Adding consensus terms where appropriate
    - Using hazard-aware Boolean minimization
    - Registering outputs when synchronous behavior is acceptable
    - Avoiding unsafe asynchronous control paths
    - Reviewing timing rather than considering Boolean equations alone
"""
    )


# ============================================================================
# SECTION 26: EDGE CASES AND INVALID CONDITIONS
# ============================================================================

def demonstrate_edge_cases() -> None:
    """Demonstrate validation and important invalid conditions."""
    print("\nEDGE CASES AND VALIDATION")
    print("-" * 72)

    cases = [
        (
            "Invalid bit",
            lambda: validate_bit(2),
        ),
        (
            "Unequal adder widths",
            lambda: ripple_carry_adder([1, 0], [1]),
        ),
        (
            "Invalid basic encoder input",
            lambda: encoder_4_to_2([1, 1, 0, 0]),
        ),
        (
            "Invalid MUX input count",
            lambda: multiplexer([0, 1, 0], [0, 1]),
        ),
        (
            "Invalid seven-segment digit",
            lambda: seven_segment_decoder(12),
        ),
        (
            "Negative unsigned conversion",
            lambda: int_to_bits(-1, 4),
        ),
    ]

    for name, operation in cases:
        try:
            operation()
        except ValueError as error:
            print(f"{name:<32} -> correctly rejected: {error}")


# ============================================================================
# SECTION 27: EXHAUSTIVE TESTING
# ============================================================================

def exhaustive_test_basic_gates() -> None:
    """Test all combinations of basic gates."""
    for a, b in product((0, 1), repeat=2):
        assert AND(a, b) == int(a == 1 and b == 1)
        assert OR(a, b) == int(a == 1 or b == 1)
        assert XOR(a, b) == int(a != b)
        assert NAND(a, b) == NOT(AND(a, b))
        assert NOR(a, b) == NOT(OR(a, b))
        assert XNOR(a, b) == int(a == b)

    for a in (0, 1):
        assert NOT(NOT(a)) == a


def exhaustive_test_adders() -> None:
    """Test half and full adders against arithmetic."""
    for a, b in product((0, 1), repeat=2):
        sum_bit, carry = half_adder(a, b)
        expected = a + b

        assert sum_bit == expected % 2
        assert carry == expected // 2

    for a, b, carry_in in product((0, 1), repeat=3):
        sum_bit, carry_out = full_adder(a, b, carry_in)
        expected = a + b + carry_in

        assert sum_bit == expected % 2
        assert carry_out == expected // 2


def exhaustive_test_subtractors() -> None:
    """Test subtractor circuits against one-bit arithmetic."""
    for a, b in product((0, 1), repeat=2):
        difference, borrow = half_subtractor(a, b)
        raw = a - b

        assert difference == raw % 2
        assert borrow == int(raw < 0)

    for a, b, borrow_in in product((0, 1), repeat=3):
        difference, borrow_out = full_subtractor(a, b, borrow_in)
        raw = a - b - borrow_in

        assert difference == raw % 2
        assert borrow_out == int(raw < 0)


def exhaustive_test_mux() -> None:
    """Test all 4-to-1 multiplexer selections."""
    for data in product((0, 1), repeat=4):
        for s1, s0 in product((0, 1), repeat=2):
            output = multiplexer_4_to_1(*data, s1, s0)
            expected = data[(s1 << 1) | s0]
            assert output == expected


def exhaustive_test_demux() -> None:
    """Test all 1-to-4 demultiplexer selections."""
    for data in (0, 1):
        for s1, s0 in product((0, 1), repeat=2):
            outputs = demultiplexer_1_to_4(data, s1, s0)
            expected = [0, 0, 0, 0]
            expected[(s1 << 1) | s0] = data

            assert list(outputs) == expected


def exhaustive_test_encoders_and_decoders() -> None:
    """Test valid encoder and decoder mappings."""
    for index in range(4):
        one_hot = [0] * 4
        one_hot[index] = 1

        encoded = encoder_4_to_2(one_hot)
        assert bits_to_int(encoded) == index

        decoded = decoder(encoded)
        assert decoded[index] == 1
        assert sum(decoded) == 1


def exhaustive_test_comparator() -> None:
    """Test all 4-bit unsigned comparator combinations."""
    for a in range(16):
        for b in range(16):
            result = magnitude_comparator(a, b, 4)

            expected = (
                int(a > b),
                int(a == b),
                int(a < b),
            )

            assert result == expected


def exhaustive_test_all() -> None:
    """Run all available exhaustive circuit tests."""
    print("\nRUNNING EXHAUSTIVE TESTS")
    print("-" * 72)

    tests = [
        ("Basic gates", exhaustive_test_basic_gates),
        ("Adders", exhaustive_test_adders),
        ("Subtractors", exhaustive_test_subtractors),
        ("Multiplexers", exhaustive_test_mux),
        ("Demultiplexers", exhaustive_test_demux),
        ("Encoders/decoders", exhaustive_test_encoders_and_decoders),
        ("Comparators", exhaustive_test_comparator),
    ]

    for name, test in tests:
        test()
        print(f"{name:<24} -> PASS")

    print("All exhaustive tests passed.")


# ============================================================================
# SECTION 28: PERFORMANCE AND SCALING
# ============================================================================

def compare_adder_architectures() -> None:
    """Print a conceptual comparison of common adder architectures."""
    print(
        """
ADDER ARCHITECTURE COMPARISON

Ripple-carry adder:
    - Simple
    - Small hardware cost
    - Carry travels through every bit
    - Worst-case delay grows approximately linearly with bit width

Carry-lookahead adder:
    - Computes carry information using generate/propagate logic
    - Lower carry dependency depth
    - More hardware and wiring
    - Useful when speed is important

Carry-select adder:
    - Computes possible results for both carry assumptions
    - Selects the correct result when carry is known
    - Trades hardware area for speed

Carry-save adder:
    - Useful when adding multiple operands
    - Does not immediately propagate carries through the complete width
    - Common in multiplier and arithmetic-tree structures

There is no universally best architecture. The choice depends on:
    - Required clock frequency
    - Area budget
    - Power budget
    - Operand width
    - Technology
    - Wiring complexity
"""
    )


def compare_data_routing_circuits() -> None:
    """Compare MUX, DEMUX, encoder, and decoder functions."""
    print(
        """
DATA ROUTING AND CODE-CONVERSION COMPARISON

Multiplexer:
    Many inputs -> One output
    Purpose: Select one data source.

Demultiplexer:
    One input -> Many possible outputs
    Purpose: Route data to one destination.

Encoder:
    Many input lines -> Fewer encoded output lines
    Purpose: Convert an active input position to binary code.
    Basic encoder normally expects one active input.

Priority encoder:
    Many input lines -> Encoded priority position + valid information.
    Multiple active inputs are allowed.

Decoder:
    Binary code -> One active output line
    Purpose: Expand encoded information into one-hot control signals.

These circuits are frequently combined in processors, communication
interfaces, memory systems, control units, display systems, and digital
selection networks.
"""
    )


# ============================================================================
# SECTION 29: SECURITY AND RELIABILITY CONSIDERATIONS
# ============================================================================

def explain_reliability_and_security() -> None:
    """Explain relevant digital-system reliability considerations."""
    print(
        """
RELIABILITY AND SECURITY CONSIDERATIONS

Combinational circuits are not usually described as security mechanisms by
themselves, but their correctness can affect system security and reliability.

Important considerations include:

1. Invalid input states
   A circuit may receive combinations that were not expected by its basic
   specification. Encoders are a common example.

2. Floating or undefined physical signals
   Real hardware inputs should not be assumed to be clean Boolean values.

3. Timing hazards
   Glitches can activate downstream control logic if timing assumptions are
   unsafe.

4. Fault tolerance
   Critical systems may use redundancy, parity, error detection, or voting
   structures.

5. Side-channel behavior
   Real digital hardware can have observable timing, power, or electromagnetic
   characteristics. A Boolean truth table alone does not describe those
   physical effects.

6. Verification
   Exhaustive simulation is particularly useful for small combinational
   circuits because all input combinations can often be tested.
"""
    )


# ============================================================================
# SECTION 30: DESIGN WORKFLOW
# ============================================================================

def explain_design_workflow() -> None:
    """Print a practical workflow for designing a combinational circuit."""
    print(
        """
COMBINATIONAL CIRCUIT DESIGN WORKFLOW

Step 1:
    Define the problem precisely.

Step 2:
    Identify every input and output.

Step 3:
    Assign meaningful names and specify whether signals are active-high or
    active-low.

Step 4:
    Build the truth table.

Step 5:
    Derive Boolean expressions.

Step 6:
    Simplify the expressions using Boolean algebra, Karnaugh maps, or other
    logic minimization methods.

Step 7:
    Select an implementation:
        - gates
        - MUX
        - decoder
        - PLA
        - FPGA LUTs
        - standard-cell logic

Step 8:
    Check invalid and unused input combinations.

Step 9:
    Analyze timing and propagation delay.

Step 10:
    Test exhaustively where practical.

Step 11:
    Verify synthesis or hardware implementation against the original
    functional specification.

The central principle is that functional correctness and physical timing
correctness are related but distinct concerns.
"""
    )


# ============================================================================
# SECTION 31: PRACTICAL EXAMPLES
# ============================================================================

def practical_example_address_selection() -> None:
    """Use a decoder as a simple address-selection model."""
    print("\nPRACTICAL EXAMPLE: ADDRESS DECODING")
    print("-" * 72)

    address_bits = [1, 0, 1]
    chip_select = decoder(address_bits)

    print(f"Address = {format_bits(address_bits)}")
    print(f"Chip-select lines = {format_bits(chip_select)}")
    print(
        "Exactly one destination is selected because a binary decoder converts"
        " the address into a one-hot output."
    )


def practical_example_data_selection() -> None:
    """Use a multiplexer to select one of several data sources."""
    print("\nPRACTICAL EXAMPLE: DATA SELECTION")
    print("-" * 72)

    sensors = [1, 0, 1, 1]

    for selection in range(4):
        select_bits = int_to_bits(selection, 2)
        selected_value = multiplexer(sensors, select_bits)

        print(
            f"Sensors={sensors}, select={format_bits(select_bits)} "
            f"-> selected={selected_value}"
        )


def practical_example_interrupt_priority() -> None:
    """Use a priority encoder as an interrupt-selection model."""
    print("\nPRACTICAL EXAMPLE: PRIORITY ENCODING")
    print("-" * 72)

    interrupt_requests = [0, 1, 1, 0]

    encoded = priority_encoder_4_to_2(interrupt_requests)

    print(
        f"Requests D3..D0 = {format_bits(interrupt_requests)}"
    )
    print(
        f"Selected priority source = {bits_to_int(encoded[:2])}"
        f", valid={encoded[2]}"
    )


def practical_example_arithmetic_unit() -> None:
    """Demonstrate an arithmetic unit selecting addition or subtraction."""
    print("\nPRACTICAL EXAMPLE: SIMPLE ARITHMETIC UNIT")
    print("-" * 72)

    width = 8
    a = 37
    b = 12

    for subtract in (0, 1):
        result = add_subtract(
            int_to_bits(a, width),
            int_to_bits(b, width),
            subtract,
        )

        operation = "-" if subtract else "+"
        expected = a - b if subtract else a + b

        print(
            f"{a} {operation} {b} -> "
            f"{format_bits(result.bits)} -> "
            f"{bits_to_int(result.bits)}"
        )

        assert bits_to_int(result.bits) == expected


# ============================================================================
# SECTION 32: IMPORTANT DISTINCTIONS
# ============================================================================

def explain_important_distinctions() -> None:
    """Print important conceptual distinctions."""
    print(
        """
IMPORTANT DISTINCTIONS

Half adder vs full adder:
    Half adder has no carry-in.
    Full adder accepts carry-in and produces carry-out.

Half subtractor vs full subtractor:
    Half subtractor has no borrow-in.
    Full subtractor accepts borrow-in.

Adder vs adder-subtractor:
    An adder performs addition.
    An adder-subtractor uses controlled inversion and carry-in to perform
    both operations.

MUX vs DEMUX:
    MUX selects one of many inputs.
    DEMUX routes one input toward one of many outputs.

Encoder vs decoder:
    Encoder compresses an active position into a binary code.
    Decoder expands a binary code into one-hot outputs.

Basic encoder vs priority encoder:
    Basic encoder requires exactly one active input.
    Priority encoder resolves multiple active inputs using priority.

Ripple carry vs carry lookahead:
    Ripple carry waits for carry propagation from lower positions.
    Carry lookahead computes carries using generate/propagate relationships.

Combinational vs sequential logic:
    Combinational logic depends on current inputs.
    Sequential logic includes state or memory.
"""
    )


# ============================================================================
# SECTION 33: COMPLETE DEMONSTRATION
# ============================================================================

def run_course() -> None:
    """Run the complete educational demonstration."""
    print("=" * 80)
    print("COMBINATIONAL LOGIC CIRCUITS")
    print("Adders, Subtractors, Multiplexers, Demultiplexers,")
    print("Encoders, Decoders, Comparators, and Related Concepts")
    print("=" * 80)

    explain_combinational_logic()

    demonstrate_basic_gates()
    demonstrate_boolean_identities()

    print("\nTRUTH TABLE: FULL ADDER")
    print("-" * 72)
    print_truth_table(
        ["A", "B", "Cin"],
        ["S", "Cout"],
        full_adder,
    )

    demonstrate_half_adder()
    demonstrate_full_adder()

    demonstrate_ripple_carry_adder()
    demonstrate_carry_logic()

    print("\nCARRY-LOOKAHEAD EXAMPLE")
    print("-" * 72)

    a = int_to_bits(9, 4)
    b = int_to_bits(6, 4)

    cla_result = carry_lookahead_4bit(a, b)
    ripple_result = ripple_carry_adder(a, b)

    print(
        f"{format_bits(a)} + {format_bits(b)} -> "
        f"CLA={cla_result.carry_out}{format_bits(cla_result.bits)}, "
        f"RCA={ripple_result.carry_out}{format_bits(ripple_result.bits)}"
    )

    assert cla_result == ripple_result

    demonstrate_half_subtractor()
    demonstrate_full_subtractor()
    demonstrate_twos_complement()
    demonstrate_adder_subtractor()

    demonstrate_multiplexers()
    demonstrate_mux_function_implementation()

    demonstrate_demultiplexers()

    demonstrate_encoder()
    demonstrate_priority_encoder()

    demonstrate_decoders()
    demonstrate_decoder_function_implementation()

    demonstrate_comparator()
    demonstrate_seven_segment()

    demonstrate_circuit_composition()

    demonstrate_propagation_delay()
    explain_hazards()

    demonstrate_edge_cases()

    practical_example_address_selection()
    practical_example_data_selection()
    practical_example_interrupt_priority()
    practical_example_arithmetic_unit()

    compare_adder_architectures()
    compare_data_routing_circuits()
    explain_reliability_and_security()
    explain_design_workflow()
    explain_important_distinctions()

    exhaustive_test_all()

    print("\nCOURSE DEMONSTRATION COMPLETE")
    print("=" * 80)


# ============================================================================
# SECTION 34: ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    run_course()
