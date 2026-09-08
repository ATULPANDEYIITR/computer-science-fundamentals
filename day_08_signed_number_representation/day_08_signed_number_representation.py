"""
Signed Number Representation
============================

A self-contained study program covering:

1. Binary fundamentals
2. Unsigned integers
3. Sign-magnitude representation
4. One's complement representation
5. Two's complement representation
6. Signed integer ranges
7. Binary addition and subtraction
8. Overflow detection
9. Sign extension and truncation
10. Integer conversion between representations
11. Arithmetic logic unit concepts
12. Edge cases and common mistakes
13. Practical simulations and tests

All examples use Python's arbitrary-precision integers, while helper functions
explicitly simulate fixed-width machine integer behavior.
"""

from dataclasses import dataclass
from typing import Tuple


# ============================================================================
# 1. FUNDAMENTAL BINARY CONCEPTS
# ============================================================================

def print_section(title: str) -> None:
    """Print a visually separated section heading."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def validate_bit_width(bits: int) -> None:
    """Ensure that a bit width is a positive integer."""
    if not isinstance(bits, int) or bits <= 0:
        raise ValueError("Bit width must be a positive integer.")


def mask_for_bits(bits: int) -> int:
    """
    Return a mask containing exactly 'bits' number of 1s.

    Example:
        bits = 4
        mask = 0b1111 = 15
    """
    validate_bit_width(bits)
    return (1 << bits) - 1


def binary_string(value: int, bits: int) -> str:
    """
    Format an integer as a fixed-width binary string.

    The value is masked first, which simulates storing it in a fixed-width
    hardware register.
    """
    validate_bit_width(bits)
    masked_value = value & mask_for_bits(bits)
    return format(masked_value, f"0{bits}b")


def group_binary(binary: str, group_size: int = 4) -> str:
    """
    Group a binary string for readability.

    Example:
        11010101 -> 1101 0101
    """
    groups = []
    for index in range(0, len(binary), group_size):
        groups.append(binary[index:index + group_size])
    return " ".join(groups)


def unsigned_range(bits: int) -> Tuple[int, int]:
    """
    Return the minimum and maximum unsigned integer values.

    For n bits:
        minimum = 0
        maximum = 2^n - 1
    """
    validate_bit_width(bits)
    return 0, mask_for_bits(bits)


# ============================================================================
# 2. UNSIGNED INTEGER REPRESENTATION
# ============================================================================

def unsigned_to_bits(value: int, bits: int) -> int:
    """
    Convert a non-negative integer to a fixed-width unsigned bit pattern.

    Raises OverflowError if the value cannot fit.
    """
    validate_bit_width(bits)

    minimum, maximum = unsigned_range(bits)

    if value < minimum or value > maximum:
        raise OverflowError(
            f"{value} cannot be represented as an unsigned {bits}-bit integer."
        )

    return value


def bits_to_unsigned(bit_pattern: int, bits: int) -> int:
    """
    Interpret a bit pattern as an unsigned integer.
    """
    return bit_pattern & mask_for_bits(bits)


# ============================================================================
# 3. SIGN-MAGNITUDE REPRESENTATION
# ============================================================================

def sign_magnitude_range(bits: int) -> Tuple[int, int]:
    """
    Return the mathematical range representable by sign-magnitude.

    One bit is reserved for the sign:
        0 = positive
        1 = negative

    Remaining bits represent magnitude.

    Range:
        -(2^(n-1)-1) to +(2^(n-1)-1)

    Sign-magnitude has two representations of zero:
        +0 = 0000...
        -0 = 1000...
    """
    validate_bit_width(bits)

    if bits < 2:
        raise ValueError("Sign-magnitude requires at least 2 bits.")

    maximum_magnitude = (1 << (bits - 1)) - 1
    return -maximum_magnitude, maximum_magnitude


def integer_to_sign_magnitude(value: int, bits: int) -> int:
    """
    Convert an integer into a sign-magnitude bit pattern.

    Example with 8 bits:
        +5 -> 00000101
        -5 -> 10000101
    """
    minimum, maximum = sign_magnitude_range(bits)

    if value < minimum or value > maximum:
        raise OverflowError(
            f"{value} cannot be represented in {bits}-bit sign-magnitude."
        )

    magnitude_mask = (1 << (bits - 1)) - 1

    if value < 0:
        sign_bit = 1 << (bits - 1)
        magnitude = abs(value)
        return sign_bit | magnitude

    return value & magnitude_mask


def sign_magnitude_to_integer(bit_pattern: int, bits: int) -> int:
    """
    Interpret a fixed-width bit pattern as a sign-magnitude number.

    Both positive zero and negative zero are returned as Python integer 0.
    """
    validate_bit_width(bits)

    if bits < 2:
        raise ValueError("Sign-magnitude requires at least 2 bits.")

    pattern = bit_pattern & mask_for_bits(bits)
    sign_bit = 1 << (bits - 1)
    magnitude_mask = sign_bit - 1
    magnitude = pattern & magnitude_mask

    if pattern & sign_bit:
        return -magnitude

    return magnitude


def is_negative_zero_sign_magnitude(bit_pattern: int, bits: int) -> bool:
    """
    Detect negative zero in sign-magnitude representation.

    Example with 8 bits:
        10000000 represents -0.
    """
    validate_bit_width(bits)

    pattern = bit_pattern & mask_for_bits(bits)
    sign_bit = 1 << (bits - 1)
    magnitude_mask = sign_bit - 1

    return bool(pattern & sign_bit) and (pattern & magnitude_mask) == 0


# ============================================================================
# 4. ONE'S COMPLEMENT REPRESENTATION
# ============================================================================

def ones_complement_range(bits: int) -> Tuple[int, int]:
    """
    Return the representable mathematical range for one's complement.

    Positive numbers:
        0xxxx...

    Negative numbers:
        Bitwise inversion of the positive representation.

    Like sign-magnitude, one's complement has two representations of zero:
        +0 = 0000...
        -0 = 1111...
    """
    validate_bit_width(bits)

    if bits < 2:
        raise ValueError("One's complement requires at least 2 bits.")

    maximum = (1 << (bits - 1)) - 1
    return -maximum, maximum


def integer_to_ones_complement(value: int, bits: int) -> int:
    """
    Convert an integer into one's complement representation.

    To represent a negative number:
        1. Represent its absolute value.
        2. Invert every bit.
    """
    minimum, maximum = ones_complement_range(bits)

    if value < minimum or value > maximum:
        raise OverflowError(
            f"{value} cannot be represented in {bits}-bit one's complement."
        )

    if value >= 0:
        return value

    positive_pattern = abs(value)
    return (~positive_pattern) & mask_for_bits(bits)


def ones_complement_to_integer(bit_pattern: int, bits: int) -> int:
    """
    Interpret a bit pattern as a one's complement signed integer.

    If the most significant bit is 0, the value is non-negative.

    If the most significant bit is 1:
        1. Invert all bits.
        2. Interpret the result as the magnitude.
        3. Apply the negative sign.
    """
    validate_bit_width(bits)

    if bits < 2:
        raise ValueError("One's complement requires at least 2 bits.")

    pattern = bit_pattern & mask_for_bits(bits)
    sign_bit = 1 << (bits - 1)

    if pattern & sign_bit == 0:
        return pattern

    inverted = (~pattern) & mask_for_bits(bits)
    return -inverted


def is_negative_zero_ones_complement(bit_pattern: int, bits: int) -> bool:
    """
    Detect negative zero in one's complement.

    For any bit width:
        negative zero = all bits set to 1.
    """
    return (bit_pattern & mask_for_bits(bits)) == mask_for_bits(bits)


def ones_complement_add(a_pattern: int, b_pattern: int, bits: int) -> int:
    """
    Add two one's complement bit patterns.

    One's complement arithmetic uses end-around carry:

        If addition produces a carry beyond the most significant bit,
        the carry is added back to the least significant bit.

    Example:
        1111 + 0001
        = 1 0000
        Lower bits = 0000
        End-around carry = 1
        Result = 0001
    """
    validate_bit_width(bits)

    mask = mask_for_bits(bits)
    total = (a_pattern & mask) + (b_pattern & mask)

    while total > mask:
        total = (total & mask) + (total >> bits)

    return total & mask


# ============================================================================
# 5. TWO'S COMPLEMENT REPRESENTATION
# ============================================================================

def twos_complement_range(bits: int) -> Tuple[int, int]:
    """
    Return the range of a signed two's complement integer.

    For n bits:
        minimum = -2^(n-1)
        maximum =  2^(n-1)-1

    The negative range has one extra value.

    Example with 4 bits:
        -8 through +7
    """
    validate_bit_width(bits)

    if bits < 2:
        raise ValueError("Signed two's complement requires at least 2 bits.")

    minimum = -(1 << (bits - 1))
    maximum = (1 << (bits - 1)) - 1

    return minimum, maximum


def integer_to_twos_complement(value: int, bits: int) -> int:
    """
    Convert a Python integer to a fixed-width two's complement bit pattern.

    For negative numbers, adding 2^n produces the corresponding unsigned
    interpretation of the bit pattern.

    Example for 8 bits:
        -5 + 256 = 251
        251 = 11111011
    """
    minimum, maximum = twos_complement_range(bits)

    if value < minimum or value > maximum:
        raise OverflowError(
            f"{value} cannot be represented in {bits}-bit two's complement."
        )

    return value & mask_for_bits(bits)


def twos_complement_to_integer(bit_pattern: int, bits: int) -> int:
    """
    Interpret a fixed-width bit pattern as a two's complement signed integer.

    If the sign bit is 0:
        value is non-negative.

    If the sign bit is 1:
        subtract 2^n from the unsigned interpretation.
    """
    validate_bit_width(bits)

    pattern = bit_pattern & mask_for_bits(bits)
    sign_bit = 1 << (bits - 1)

    if pattern & sign_bit:
        return pattern - (1 << bits)

    return pattern


def negate_twos_complement(bit_pattern: int, bits: int) -> int:
    """
    Negate a two's complement number at the bit level.

    Mathematical rule:
        -x = (~x) + 1

    The result is limited to the selected bit width.

    Important edge case:
        The most negative value cannot be negated within the same width.

    Example for 8 bits:
        -128 = 10000000

        Inverting:
        01111111

        Adding one:
        10000000

        Therefore negating -128 in 8 bits produces -128 again.
    """
    mask = mask_for_bits(bits)
    return ((~bit_pattern) + 1) & mask


# ============================================================================
# 6. COMPARING THE THREE SIGNED REPRESENTATIONS
# ============================================================================

@dataclass(frozen=True)
class RepresentationResult:
    """Store a representation name, bit pattern, and decoded value."""
    representation: str
    bit_pattern: str
    decoded_value: int


def compare_representations(value: int, bits: int) -> list[RepresentationResult]:
    """
    Represent one value using all supported signed representations.

    Some values cannot be represented in all formats because two's complement
    has a slightly larger negative range.
    """
    results = []

    try:
        pattern = integer_to_sign_magnitude(value, bits)
        results.append(
            RepresentationResult(
                "Sign-magnitude",
                binary_string(pattern, bits),
                sign_magnitude_to_integer(pattern, bits),
            )
        )
    except OverflowError:
        pass

    try:
        pattern = integer_to_ones_complement(value, bits)
        results.append(
            RepresentationResult(
                "One's complement",
                binary_string(pattern, bits),
                ones_complement_to_integer(pattern, bits),
            )
        )
    except OverflowError:
        pass

    try:
        pattern = integer_to_twos_complement(value, bits)
        results.append(
            RepresentationResult(
                "Two's complement",
                binary_string(pattern, bits),
                twos_complement_to_integer(pattern, bits),
            )
        )
    except OverflowError:
        pass

    return results


# ============================================================================
# 7. FIXED-WIDTH TWO'S COMPLEMENT ARITHMETIC
# ============================================================================

def twos_complement_add(
    a_pattern: int,
    b_pattern: int,
    bits: int,
) -> Tuple[int, bool]:
    """
    Add two fixed-width two's complement values.

    Returns:
        result_pattern
        overflow

    Hardware addition is identical for signed and unsigned bit patterns.
    Interpretation differs.

    Signed overflow occurs when:
        - two positive numbers produce a negative result, or
        - two negative numbers produce a positive result.
    """
    mask = mask_for_bits(bits)

    a = a_pattern & mask
    b = b_pattern & mask
    result = (a + b) & mask

    sign_bit = 1 << (bits - 1)

    a_negative = bool(a & sign_bit)
    b_negative = bool(b & sign_bit)
    result_negative = bool(result & sign_bit)

    overflow = (
        (not a_negative and not b_negative and result_negative)
        or (a_negative and b_negative and not result_negative)
    )

    return result, overflow


def twos_complement_subtract(
    a_pattern: int,
    b_pattern: int,
    bits: int,
) -> Tuple[int, bool]:
    """
    Subtract b from a using two's complement arithmetic:

        a - b = a + (-b)

    Negation is performed at the bit level.
    """
    negative_b = negate_twos_complement(b_pattern, bits)
    return twos_complement_add(a_pattern, negative_b, bits)


def signed_add_values(a: int, b: int, bits: int) -> Tuple[int, bool]:
    """
    Convenience function that accepts mathematical integers and simulates
    fixed-width two's complement addition.
    """
    a_pattern = integer_to_twos_complement(a, bits)
    b_pattern = integer_to_twos_complement(b, bits)

    result_pattern, overflow = twos_complement_add(
        a_pattern,
        b_pattern,
        bits,
    )

    return twos_complement_to_integer(result_pattern, bits), overflow


def signed_subtract_values(a: int, b: int, bits: int) -> Tuple[int, bool]:
    """
    Convenience function for fixed-width two's complement subtraction.
    """
    a_pattern = integer_to_twos_complement(a, bits)
    b_pattern = integer_to_twos_complement(b, bits)

    result_pattern, overflow = twos_complement_subtract(
        a_pattern,
        b_pattern,
        bits,
    )

    return twos_complement_to_integer(result_pattern, bits), overflow


# ============================================================================
# 8. OVERFLOW DETECTION USING MATHEMATICAL RANGE
# ============================================================================

def would_signed_overflow(value: int, bits: int) -> bool:
    """
    Determine whether a mathematical integer fits in a signed two's
    complement width.
    """
    minimum, maximum = twos_complement_range(bits)
    return value < minimum or value > maximum


def demonstrate_overflow(bits: int) -> None:
    """
    Demonstrate common signed overflow situations.
    """
    minimum, maximum = twos_complement_range(bits)

    print(f"{bits}-bit signed range: {minimum} to {maximum}")

    if maximum >= 1:
        result, overflow = signed_add_values(maximum, 1, bits)
        print(
            f"{maximum} + 1 -> stored result {result}, "
            f"overflow={overflow}"
        )

    if minimum <= -1:
        result, overflow = signed_subtract_values(minimum, 1, bits)
        print(
            f"{minimum} - 1 -> stored result {result}, "
            f"overflow={overflow}"
        )


# ============================================================================
# 9. SIGN EXTENSION
# ============================================================================

def sign_extend(bit_pattern: int, from_bits: int, to_bits: int) -> int:
    """
    Extend a two's complement number from a smaller width to a larger width.

    Sign extension preserves the numerical value.

    If the original sign bit is:
        0 -> fill new high bits with 0
        1 -> fill new high bits with 1

    Example:
        4-bit -3 = 1101

        Sign-extended to 8 bits:
        11111101
    """
    validate_bit_width(from_bits)
    validate_bit_width(to_bits)

    if to_bits < from_bits:
        raise ValueError(
            "Target width must be greater than or equal to source width."
        )

    source_mask = mask_for_bits(from_bits)
    pattern = bit_pattern & source_mask
    sign_bit = 1 << (from_bits - 1)

    if pattern & sign_bit:
        extension_mask = mask_for_bits(to_bits) ^ source_mask
        return pattern | extension_mask

    return pattern


def zero_extend(bit_pattern: int, from_bits: int, to_bits: int) -> int:
    """
    Extend an unsigned number by adding zeros on the left.

    Zero extension does not preserve the meaning of a negative two's
    complement number because it changes the sign interpretation.
    """
    validate_bit_width(from_bits)
    validate_bit_width(to_bits)

    if to_bits < from_bits:
        raise ValueError(
            "Target width must be greater than or equal to source width."
        )

    return bit_pattern & mask_for_bits(from_bits)


# ============================================================================
# 10. TRUNCATION
# ============================================================================

def truncate_to_bits(value: int, bits: int) -> int:
    """
    Keep only the lowest 'bits' bits.

    This simulates assignment to a smaller fixed-width register.

    Truncation may change both magnitude and sign.
    """
    return value & mask_for_bits(bits)


# ============================================================================
# 11. ARITHMETIC SHIFTS
# ============================================================================

def logical_left_shift(bit_pattern: int, shift: int, bits: int) -> int:
    """
    Shift left and discard bits that exceed the selected width.

    For fixed-width binary arithmetic, left shifting may cause overflow.
    """
    if shift < 0:
        raise ValueError("Shift count cannot be negative.")

    return (bit_pattern << shift) & mask_for_bits(bits)


def logical_right_shift(bit_pattern: int, shift: int, bits: int) -> int:
    """
    Logical right shift fills new high bits with zeros.

    This is commonly associated with unsigned values.
    """
    if shift < 0:
        raise ValueError("Shift count cannot be negative.")

    return (bit_pattern & mask_for_bits(bits)) >> shift


def arithmetic_right_shift(bit_pattern: int, shift: int, bits: int) -> int:
    """
    Arithmetic right shift preserves the sign of a two's complement value.

    Positive values receive zeros.
    Negative values receive ones.

    Python's right shift on integers already behaves as an arithmetic shift
    for negative Python integers, so this function converts through the signed
    interpretation and then returns a fixed-width pattern.
    """
    if shift < 0:
        raise ValueError("Shift count cannot be negative.")

    signed_value = twos_complement_to_integer(bit_pattern, bits)
    shifted = signed_value >> shift
    return shifted & mask_for_bits(bits)


# ============================================================================
# 12. BITWISE OPERATIONS ON SIGNED VALUES
# ============================================================================

def signed_bitwise_demo(a: int, b: int, bits: int) -> dict[str, int]:
    """
    Demonstrate fixed-width bitwise operations.

    Hardware works with bit patterns. Whether the result is interpreted as
    signed or unsigned is a separate decision.
    """
    a_pattern = integer_to_twos_complement(a, bits)
    b_pattern = integer_to_twos_complement(b, bits)
    mask = mask_for_bits(bits)

    and_pattern = a_pattern & b_pattern
    or_pattern = a_pattern | b_pattern
    xor_pattern = a_pattern ^ b_pattern
    not_a_pattern = (~a_pattern) & mask

    return {
        "a": twos_complement_to_integer(a_pattern, bits),
        "b": twos_complement_to_integer(b_pattern, bits),
        "and": twos_complement_to_integer(and_pattern, bits),
        "or": twos_complement_to_integer(or_pattern, bits),
        "xor": twos_complement_to_integer(xor_pattern, bits),
        "not_a": twos_complement_to_integer(not_a_pattern, bits),
    }


# ============================================================================
# 13. CONVERSION TABLES
# ============================================================================

def representation_table(bits: int) -> list[dict[str, str]]:
    """
    Produce a table showing every bit pattern interpreted in all three
    signed representations and as an unsigned integer.

    This is especially useful for small widths such as 4 bits.
    """
    validate_bit_width(bits)

    table = []

    for pattern in range(1 << bits):
        row = {
            "bits": binary_string(pattern, bits),
            "unsigned": str(bits_to_unsigned(pattern, bits)),
            "sign_magnitude": str(
                sign_magnitude_to_integer(pattern, bits)
            ),
            "ones_complement": str(
                ones_complement_to_integer(pattern, bits)
            ),
            "twos_complement": str(
                twos_complement_to_integer(pattern, bits)
            ),
        }
        table.append(row)

    return table


def print_representation_table(bits: int) -> None:
    """Print a compact representation comparison table."""
    table = representation_table(bits)

    headers = [
        "Bits",
        "Unsigned",
        "Sign-Magnitude",
        "One's Complement",
        "Two's Complement",
    ]

    widths = [len(header) for header in headers]

    for row in table:
        widths[0] = max(widths[0], len(row["bits"]))
        widths[1] = max(widths[1], len(row["unsigned"]))
        widths[2] = max(widths[2], len(row["sign_magnitude"]))
        widths[3] = max(widths[3], len(row["ones_complement"]))
        widths[4] = max(widths[4], len(row["twos_complement"]))

    format_string = (
        f"{{:<{widths[0]}}}  "
        f"{{:>{widths[1]}}}  "
        f"{{:>{widths[2]}}}  "
        f"{{:>{widths[3]}}}  "
        f"{{:>{widths[4]}}}"
    )

    print(format_string.format(*headers))
    print("-" * (sum(widths) + 8))

    for row in table:
        print(
            format_string.format(
                row["bits"],
                row["unsigned"],
                row["sign_magnitude"],
                row["ones_complement"],
                row["twos_complement"],
            )
        )


# ============================================================================
# 14. BINARY ADDITION VISUALIZATION
# ============================================================================

def binary_addition_steps(a: int, b: int, bits: int) -> list[dict[str, int]]:
    """
    Simulate binary addition from right to left.

    Each returned dictionary contains:
        bit position
        input bits
        carry in
        sum bit
        carry out

    Bit position 0 is the least significant bit.
    """
    mask = mask_for_bits(bits)
    a &= mask
    b &= mask

    carry = 0
    steps = []

    for position in range(bits):
        a_bit = (a >> position) & 1
        b_bit = (b >> position) & 1

        total = a_bit + b_bit + carry
        sum_bit = total & 1
        carry_out = total >> 1

        steps.append(
            {
                "position": position,
                "a_bit": a_bit,
                "b_bit": b_bit,
                "carry_in": carry,
                "sum_bit": sum_bit,
                "carry_out": carry_out,
            }
        )

        carry = carry_out

    return steps


def print_binary_addition_steps(a: int, b: int, bits: int) -> None:
    """Print a binary addition process."""
    print(f"A: {binary_string(a, bits)}")
    print(f"B: {binary_string(b, bits)}")

    steps = binary_addition_steps(a, b, bits)

    for step in reversed(steps):
        print(
            f"Bit {step['position']}: "
            f"{step['a_bit']} + {step['b_bit']} + "
            f"carry {step['carry_in']} -> "
            f"sum {step['sum_bit']}, carry {step['carry_out']}"
        )


# ============================================================================
# 15. COMMON PITFALLS AS EXECUTABLE EXAMPLES
# ============================================================================

def demonstrate_common_mistakes() -> None:
    """
    Demonstrate several subtle errors commonly made when working with
    signed binary integers.
    """
    print_section("COMMON MISTAKES AND EDGE CASES")

    bits = 8

    # Mistake 1: Interpreting a bit pattern without knowing its representation.
    pattern = 0b11111011

    print(
        f"Pattern {binary_string(pattern, bits)} interpreted as unsigned: "
        f"{bits_to_unsigned(pattern, bits)}"
    )
    print(
        f"Pattern {binary_string(pattern, bits)} interpreted as "
        f"two's complement: "
        f"{twos_complement_to_integer(pattern, bits)}"
    )
    print(
        f"Pattern {binary_string(pattern, bits)} interpreted as "
        f"one's complement: "
        f"{ones_complement_to_integer(pattern, bits)}"
    )

    # Mistake 2: Assuming all signed formats have the same range.
    sm_min, sm_max = sign_magnitude_range(bits)
    oc_min, oc_max = ones_complement_range(bits)
    tc_min, tc_max = twos_complement_range(bits)

    print(
        f"Sign-magnitude range: {sm_min} to {sm_max}"
    )
    print(
        f"One's complement range: {oc_min} to {oc_max}"
    )
    print(
        f"Two's complement range: {tc_min} to {tc_max}"
    )

    # Mistake 3: Ignoring negative zero.
    negative_zero_sm = 1 << (bits - 1)
    negative_zero_oc = mask_for_bits(bits)

    print(
        f"Sign-magnitude negative zero: "
        f"{binary_string(negative_zero_sm, bits)}"
    )
    print(
        f"Detected: "
        f"{is_negative_zero_sign_magnitude(negative_zero_sm, bits)}"
    )

    print(
        f"One's complement negative zero: "
        f"{binary_string(negative_zero_oc, bits)}"
    )
    print(
        f"Detected: "
        f"{is_negative_zero_ones_complement(negative_zero_oc, bits)}"
    )

    # Mistake 4: Negating the most negative two's complement value.
    minimum, _ = twos_complement_range(bits)
    minimum_pattern = integer_to_twos_complement(minimum, bits)
    negated_pattern = negate_twos_complement(minimum_pattern, bits)

    print(
        f"Minimum {bits}-bit value: {minimum}, "
        f"bits={binary_string(minimum_pattern, bits)}"
    )
    print(
        f"Negating within {bits} bits gives "
        f"{twos_complement_to_integer(negated_pattern, bits)}, "
        f"bits={binary_string(negated_pattern, bits)}"
    )


# ============================================================================
# 16. SIMPLE FIXED-WIDTH SIGNED INTEGER CLASS
# ============================================================================

@dataclass
class FixedWidthInt:
    """
    A small educational model of a fixed-width two's complement integer.

    The class stores only the bit pattern. Arithmetic wraps at the configured
    width, reproducing the behavior of many low-level systems.

    This is intentionally different from Python's normal int type, which has
    arbitrary precision.
    """

    value: int
    bits: int

    def __post_init__(self) -> None:
        validate_bit_width(self.bits)
        self.value &= mask_for_bits(self.bits)

    @classmethod
    def from_signed(cls, value: int, bits: int) -> "FixedWidthInt":
        """Construct from a signed mathematical integer."""
        pattern = integer_to_twos_complement(value, bits)
        return cls(pattern, bits)

    @property
    def signed(self) -> int:
        """Return the two's complement signed interpretation."""
        return twos_complement_to_integer(self.value, self.bits)

    @property
    def unsigned(self) -> int:
        """Return the unsigned interpretation."""
        return bits_to_unsigned(self.value, self.bits)

    @property
    def binary(self) -> str:
        """Return the fixed-width binary representation."""
        return binary_string(self.value, self.bits)

    def add(self, other: "FixedWidthInt") -> Tuple["FixedWidthInt", bool]:
        """Add two values of equal width and report signed overflow."""
        self._require_same_width(other)

        result, overflow = twos_complement_add(
            self.value,
            other.value,
            self.bits,
        )

        return FixedWidthInt(result, self.bits), overflow

    def subtract(
        self,
        other: "FixedWidthInt",
    ) -> Tuple["FixedWidthInt", bool]:
        """Subtract two values of equal width and report signed overflow."""
        self._require_same_width(other)

        result, overflow = twos_complement_subtract(
            self.value,
            other.value,
            self.bits,
        )

        return FixedWidthInt(result, self.bits), overflow

    def negate(self) -> "FixedWidthInt":
        """Negate using two's complement bit-level arithmetic."""
        return FixedWidthInt(
            negate_twos_complement(self.value, self.bits),
            self.bits,
        )

    def _require_same_width(self, other: "FixedWidthInt") -> None:
        """Prevent arithmetic between incompatible widths."""
        if self.bits != other.bits:
            raise ValueError(
                "Fixed-width integers must have the same bit width."
            )

    def __repr__(self) -> str:
        return (
            f"FixedWidthInt(bits={self.bits}, "
            f"binary='{self.binary}', "
            f"signed={self.signed}, "
            f"unsigned={self.unsigned})"
        )


# ============================================================================
# 17. TESTS
# ============================================================================

def run_tests() -> None:
    """
    Run correctness checks covering important ranges and edge cases.
    """
    print_section("RUNNING VALIDATION TESTS")

    # Test conversion round trips for small bit widths.
    for bits in range(2, 9):
        minimum, maximum = twos_complement_range(bits)

        for value in range(minimum, maximum + 1):
            pattern = integer_to_twos_complement(value, bits)
            decoded = twos_complement_to_integer(pattern, bits)

            assert decoded == value, (
                f"Two's complement round trip failed: "
                f"value={value}, bits={bits}"
            )

    # Test one's complement round trips.
    for bits in range(2, 9):
        minimum, maximum = ones_complement_range(bits)

        for value in range(minimum, maximum + 1):
            pattern = integer_to_ones_complement(value, bits)
            decoded = ones_complement_to_integer(pattern, bits)

            assert decoded == value, (
                f"One's complement round trip failed: "
                f"value={value}, bits={bits}"
            )

    # Test sign-magnitude round trips.
    for bits in range(2, 9):
        minimum, maximum = sign_magnitude_range(bits)

        for value in range(minimum, maximum + 1):
            pattern = integer_to_sign_magnitude(value, bits)
            decoded = sign_magnitude_to_integer(pattern, bits)

            assert decoded == value, (
                f"Sign-magnitude round trip failed: "
                f"value={value}, bits={bits}"
            )

    # Test sign extension.
    four_bit_negative_three = integer_to_twos_complement(-3, 4)
    extended = sign_extend(four_bit_negative_three, 4, 8)

    assert twos_complement_to_integer(extended, 8) == -3

    # Test signed overflow.
    result, overflow = signed_add_values(127, 1, 8)
    assert result == -128
    assert overflow is True

    result, overflow = signed_add_values(-128, -1, 8)
    assert result == 127
    assert overflow is True

    # Test valid arithmetic.
    result, overflow = signed_add_values(20, -5, 8)
    assert result == 15
    assert overflow is False

    # Test fixed-width class.
    a = FixedWidthInt.from_signed(127, 8)
    b = FixedWidthInt.from_signed(1, 8)

    result, overflow = a.add(b)

    assert result.signed == -128
    assert overflow is True

    print("All tests passed successfully.")


# ============================================================================
# 18. MAIN DEMONSTRATION
# ============================================================================

def demonstrate_fundamentals() -> None:
    """Demonstrate binary and unsigned representation."""
    print_section("1. BINARY AND UNSIGNED INTEGER FUNDAMENTALS")

    bits = 8
    value = 173

    print(f"Decimal value: {value}")
    print(f"{bits}-bit binary: {binary_string(value, bits)}")
    print(f"Grouped binary: {group_binary(binary_string(value, bits))}")

    minimum, maximum = unsigned_range(bits)
    print(f"{bits}-bit unsigned range: {minimum} to {maximum}")


def demonstrate_signed_representations() -> None:
    """Demonstrate one value in multiple signed representations."""
    print_section("2. SIGN-MAGNITUDE, ONE'S COMPLEMENT, AND TWO'S COMPLEMENT")

    bits = 8

    for value in [5, -5, 0, -127]:
        print(f"\nDecimal value: {value}")

        for result in compare_representations(value, bits):
            print(
                f"{result.representation:18}: "
                f"{result.bit_pattern} -> {result.decoded_value}"
            )

    print("\nSpecial two's complement value:")

    minimum, _ = twos_complement_range(bits)
    pattern = integer_to_twos_complement(minimum, bits)

    print(
        f"{minimum} -> {binary_string(pattern, bits)}"
    )


def demonstrate_negative_zero() -> None:
    """Show the duplicate zero problem."""
    print_section("3. THE NEGATIVE ZERO PROBLEM")

    bits = 4

    positive_zero = 0
    negative_zero_sm = 1 << (bits - 1)
    negative_zero_oc = mask_for_bits(bits)

    print(
        f"Sign-magnitude +0: "
        f"{binary_string(positive_zero, bits)}"
    )
    print(
        f"Sign-magnitude -0: "
        f"{binary_string(negative_zero_sm, bits)}"
    )

    print(
        f"One's complement +0: "
        f"{binary_string(positive_zero, bits)}"
    )
    print(
        f"One's complement -0: "
        f"{binary_string(negative_zero_oc, bits)}"
    )

    print(
        "Two's complement has exactly one zero: "
        f"{binary_string(0, bits)}"
    )


def demonstrate_twos_complement_negation() -> None:
    """Demonstrate invert-and-add-one negation."""
    print_section("4. TWO'S COMPLEMENT NEGATION")

    bits = 8
    value = 18

    original = integer_to_twos_complement(value, bits)
    inverted = (~original) & mask_for_bits(bits)
    negated = negate_twos_complement(original, bits)

    print(f"Value: {value}")
    print(f"Original: {binary_string(original, bits)}")
    print(f"Inverted: {binary_string(inverted, bits)}")
    print(f"+ 1 result: {binary_string(negated, bits)}")
    print(
        f"Decoded result: "
        f"{twos_complement_to_integer(negated, bits)}"
    )


def demonstrate_arithmetic() -> None:
    """Demonstrate signed fixed-width arithmetic."""
    print_section("5. FIXED-WIDTH TWO'S COMPLEMENT ARITHMETIC")

    bits = 8

    examples = [
        (20, 30),
        (20, -5),
        (-20, -30),
        (127, 1),
        (-128, -1),
    ]

    for a, b in examples:
        result, overflow = signed_add_values(a, b, bits)

        print(
            f"{a:4} + {b:4} = "
            f"stored {result:4}, overflow={overflow}"
        )

    subtraction_examples = [
        (10, 5),
        (10, -5),
        (-100, 20),
        (-128, 1),
    ]

    print("\nSubtraction:")

    for a, b in subtraction_examples:
        result, overflow = signed_subtract_values(a, b, bits)

        print(
            f"{a:4} - {b:4} = "
            f"stored {result:4}, overflow={overflow}"
        )


def demonstrate_extensions_and_shifts() -> None:
    """Demonstrate sign extension, zero extension, and shifts."""
    print_section("6. SIGN EXTENSION, ZERO EXTENSION, AND SHIFTS")

    original_bits = 4
    target_bits = 8
    value = -3

    pattern = integer_to_twos_complement(value, original_bits)
    sign_extended = sign_extend(
        pattern,
        original_bits,
        target_bits,
    )
    zero_extended = zero_extend(
        pattern,
        original_bits,
        target_bits,
    )

    print(
        f"{original_bits}-bit {value}: "
        f"{binary_string(pattern, original_bits)}"
    )
    print(
        f"Sign extended to {target_bits} bits: "
        f"{binary_string(sign_extended, target_bits)} -> "
        f"{twos_complement_to_integer(sign_extended, target_bits)}"
    )
    print(
        f"Zero extended to {target_bits} bits: "
        f"{binary_string(zero_extended, target_bits)} -> "
        f"{twos_complement_to_integer(zero_extended, target_bits)}"
    )

    shift_pattern = integer_to_twos_complement(-16, 8)

    print(
        f"\nOriginal -16: "
        f"{binary_string(shift_pattern, 8)}"
    )

    logical = logical_right_shift(shift_pattern, 2, 8)
    arithmetic = arithmetic_right_shift(shift_pattern, 2, 8)

    print(
        f"Logical right shift by 2: "
        f"{binary_string(logical, 8)} -> "
        f"{twos_complement_to_integer(logical, 8)}"
    )
    print(
        f"Arithmetic right shift by 2: "
        f"{binary_string(arithmetic, 8)} -> "
        f"{twos_complement_to_integer(arithmetic, 8)}"
    )


def demonstrate_bitwise_operations() -> None:
    """Demonstrate signed bitwise operations."""
    print_section("7. BITWISE OPERATIONS ON FIXED-WIDTH SIGNED INTEGERS")

    results = signed_bitwise_demo(-12, 10, 8)

    for name, value in results.items():
        pattern = integer_to_twos_complement(value, 8)

        print(
            f"{name:6}: "
            f"{binary_string(pattern, 8)} -> {value}"
        )


def demonstrate_fixed_width_class() -> None:
    """Demonstrate the FixedWidthInt educational model."""
    print_section("8. FIXED-WIDTH INTEGER OBJECT MODEL")

    a = FixedWidthInt.from_signed(100, 8)
    b = FixedWidthInt.from_signed(60, 8)

    result, overflow = a.add(b)

    print(f"A: {a}")
    print(f"B: {b}")
    print(f"A + B: {result}")
    print(f"Overflow: {overflow}")

    negative = FixedWidthInt.from_signed(-25, 8)

    print(f"\nNegative value: {negative}")
    print(f"Negated value: {negative.negate()}")


def demonstrate_addition_process() -> None:
    """Demonstrate bit-by-bit binary addition."""
    print_section("9. BIT-BY-BIT BINARY ADDITION")

    print_binary_addition_steps(
        0b01011010,
        0b00110111,
        8,
    )


def demonstrate_table() -> None:
    """Print a complete small-width representation table."""
    print_section("10. COMPLETE 4-BIT REPRESENTATION TABLE")
    print_representation_table(4)


def main() -> None:
    """Run the complete signed number representation tutorial."""
    demonstrate_fundamentals()
    demonstrate_signed_representations()
    demonstrate_negative_zero()
    demonstrate_twos_complement_negation()
    demonstrate_arithmetic()
    demonstrate_overflow(8)
    demonstrate_extensions_and_shifts()
    demonstrate_bitwise_operations()
    demonstrate_fixed_width_class()
    demonstrate_addition_process()
    demonstrate_table()
    demonstrate_common_mistakes()
    run_tests()


if __name__ == "__main__":
    main()
