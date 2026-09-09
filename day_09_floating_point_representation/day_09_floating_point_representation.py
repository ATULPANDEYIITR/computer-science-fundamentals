"""
Floating Point Representation: From Fundamentals to Advanced IEEE 754 Concepts
===============================================================================

A self-contained study script covering:

1. Why computers need floating-point representation
2. Fixed-point versus floating-point representation
3. Scientific notation and normalized binary notation
4. IEEE 754 terminology and structure
5. Binary32 (single precision) and Binary64 (double precision)
6. Sign, exponent, bias, significand/fraction
7. Normalized and subnormal numbers
8. Zero, infinities, NaN, and special encodings
9. Decimal-to-binary conversion
10. Binary floating-point precision
11. Machine epsilon and ULP
12. Rounding modes
13. Rounding error and representation error
14. Catastrophic cancellation
15. Absorption and loss of significance
16. Overflow and underflow
17. Gradual underflow
18. Python float behavior
19. Exact integer limits
20. Decimal and Fraction alternatives
21. Stable numerical algorithms
22. Summation algorithms including Kahan summation
23. Equality comparisons and tolerances
24. Bit-level inspection and reconstruction
25. NaN and infinity behavior
26. Signed zero
27. Decimal conversion and hexadecimal floating-point notation
28. Performance and storage considerations
29. Numerical testing and debugging
30. Practical and production-oriented best practices

The examples intentionally use only Python's standard library.
"""

from __future__ import annotations

import math
import struct
import sys
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
from typing import Iterable, Optional


# =============================================================================
# 1. INTRODUCTION: WHAT IS A FLOATING-POINT NUMBER?
# =============================================================================

def section(title: str) -> None:
    """Print a readable section heading."""
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def explain_basic_idea() -> None:
    """
    Demonstrate the basic idea behind floating-point representation.

    Floating-point representation is analogous to scientific notation:

        6.022 × 10^23

    A binary floating-point value conceptually has the form:

        sign × significand × 2^exponent

    IEEE 754 specifies how these components are encoded in bits.
    """
    section("1. Floating-Point Representation")

    print("Decimal scientific notation:")
    print("  602200000000000000000000 = 6.022 × 10^23")

    print("\nBinary scientific notation:")
    print("  101.101₂ = 1.01101₂ × 2^2")

    print("\nPython's float normally uses IEEE 754 binary64:")
    print(f"  type(1.5) = {type(1.5).__name__}")
    print(f"  sys.float_info.radix = {sys.float_info.radix}")
    print(f"  sys.float_info.mant_dig = {sys.float_info.mant_dig}")
    print(f"  sys.float_info.max_exp = {sys.float_info.max_exp}")
    print(f"  sys.float_info.min_exp = {sys.float_info.min_exp}")


# =============================================================================
# 2. FIXED-POINT VERSUS FLOATING-POINT
# =============================================================================

def demonstrate_fixed_point_vs_floating_point() -> None:
    """
    Compare fixed-point and floating-point representations.

    Fixed-point assigns a predetermined number of digits to the fractional
    portion. Floating-point allows the binary point to move by storing an
    exponent.
    """
    section("2. Fixed-Point versus Floating-Point")

    values = [12.34, 1234.0, 0.001234]

    print("Conceptual fixed-point scale = 100:")
    for value in values:
        encoded = round(value * 100)
        decoded = encoded / 100
        print(f"  {value:10g} -> integer {encoded:8d} -> {decoded:g}")

    print("\nFloating-point values:")
    for value in values:
        print(f"  {value:g} -> {value.hex()}")

    print(
        "\nFixed-point is useful when a fixed decimal scale is required, "
        "such as monetary quantities stored as integer cents."
    )
    print(
        "Floating-point is useful when values span a large dynamic range, "
        "such as scientific measurements."
    )


# =============================================================================
# 3. BINARY FRACTIONS
# =============================================================================

def binary_fraction_to_fraction(bits: str) -> Fraction:
    """
    Convert a binary fraction such as '101.101' into an exact Fraction.

    This function supports a binary point but does not support a sign.
    """
    if bits.count(".") > 1:
        raise ValueError("A binary number may contain at most one point.")

    integer_part, _, fractional_part = bits.partition(".")

    if not integer_part:
        integer_part = "0"

    if not fractional_part:
        fractional_part = ""

    if any(character not in "01" for character in integer_part + fractional_part):
        raise ValueError("Binary input may contain only 0 and 1.")

    integer_value = int(integer_part, 2)

    fractional_value = Fraction(0, 1)
    for position, bit in enumerate(fractional_part, start=1):
        if bit == "1":
            fractional_value += Fraction(1, 2**position)

    return Fraction(integer_value, 1) + fractional_value


def demonstrate_binary_fractions() -> None:
    """
    Show how binary fractions are constructed.

    For example:

        0.101₂
        = 1×2^-1 + 0×2^-2 + 1×2^-3
        = 1/2 + 1/8
        = 5/8
    """
    section("3. Binary Fractions")

    examples = ["101.101", "0.101", "0.1", "1.01101"]

    for binary_value in examples:
        exact = binary_fraction_to_fraction(binary_value)
        print(f"{binary_value:>10}₂ = {exact} = {float(exact):.17g}")

    print(
        "\nImportant fact: a finite decimal fraction does not necessarily "
        "have a finite binary representation."
    )
    print("For example, 0.1 has an infinite binary expansion.")


# =============================================================================
# 4. IEEE 754 STRUCTURE
# =============================================================================

def ieee754_layout(bits: int, exponent_bits: int, fraction_bits: int) -> str:
    """
    Return a textual description of an IEEE 754 encoding layout.
    """
    if bits != 1 + exponent_bits + fraction_bits:
        raise ValueError("Bit counts must add up to the total size.")

    return (
        f"sign={1} bit, exponent={exponent_bits} bits, "
        f"fraction={fraction_bits} bits"
    )


def demonstrate_ieee754_layout() -> None:
    """Explain common IEEE 754 binary formats."""
    section("4. IEEE 754 Formats")

    print("Binary32:")
    print("  total bits      : 32")
    print("  sign bits       : 1")
    print("  exponent bits   : 8")
    print("  fraction bits   : 23")
    print("  precision       : 24 significant binary bits for normal numbers")
    print("  exponent bias   : 127")

    print("\nBinary64:")
    print("  total bits      : 64")
    print("  sign bits       : 1")
    print("  exponent bits   : 11")
    print("  fraction bits   : 52")
    print("  precision       : 53 significant binary bits for normal numbers")
    print("  exponent bias   : 1023")

    print("\nLayout:")
    print("  [sign][biased exponent][fraction]")


# =============================================================================
# 5. BINARY64 ENCODING AND DECODING
# =============================================================================

def float_to_uint64(value: float) -> int:
    """Return the raw IEEE 754 binary64 bit pattern as an unsigned integer."""
    return struct.unpack(">Q", struct.pack(">d", value))[0]


def uint64_to_float(bits: int) -> float:
    """Convert a 64-bit integer bit pattern into an IEEE 754 binary64 float."""
    if not 0 <= bits <= 0xFFFFFFFFFFFFFFFF:
        raise ValueError("A binary64 bit pattern must contain exactly 64 bits.")
    return struct.unpack(">d", struct.pack(">Q", bits))[0]


def bits_to_string(bits: int, width: int = 64) -> str:
    """Format an integer as a fixed-width binary string."""
    return format(bits, f"0{width}b")


def decode_binary64_bits(bits: int) -> dict[str, object]:
    """
    Decode an IEEE 754 binary64 bit pattern.

    The returned fields include:
        sign
        exponent_field
        fraction_field
        unbiased_exponent
        category
        value
    """
    if not 0 <= bits <= 0xFFFFFFFFFFFFFFFF:
        raise ValueError("bits must be a 64-bit unsigned integer.")

    sign = (bits >> 63) & 1
    exponent_field = (bits >> 52) & 0x7FF
    fraction_field = bits & ((1 << 52) - 1)

    if exponent_field == 0:
        if fraction_field == 0:
            category = "zero"
        else:
            category = "subnormal"
    elif exponent_field == 0x7FF:
        if fraction_field == 0:
            category = "infinity"
        else:
            category = "nan"
    else:
        category = "normal"

    if exponent_field == 0:
        unbiased_exponent = -1022
    elif exponent_field == 0x7FF:
        unbiased_exponent = None
    else:
        unbiased_exponent = exponent_field - 1023

    return {
        "sign": sign,
        "exponent_field": exponent_field,
        "fraction_field": fraction_field,
        "unbiased_exponent": unbiased_exponent,
        "category": category,
        "value": uint64_to_float(bits),
    }


def describe_float(value: float) -> None:
    """Print a detailed binary64 representation of a Python float."""
    bits = float_to_uint64(value)
    decoded = decode_binary64_bits(bits)
    bit_string = bits_to_string(bits)

    print(f"value             : {value!r}")
    print(f"hexadecimal       : {value.hex()}")
    print(f"binary64 bits     : {bit_string}")
    print(f"sign              : {decoded['sign']}")
    print(f"exponent field    : {decoded['exponent_field']}")
    print(f"fraction field    : {decoded['fraction_field']}")
    print(f"unbiased exponent : {decoded['unbiased_exponent']}")
    print(f"category          : {decoded['category']}")


def demonstrate_binary64_encoding() -> None:
    """Inspect common binary64 values."""
    section("5. Binary64 Bit-Level Representation")

    values = [1.0, -1.0, 0.5, 2.5, 0.1, 0.0, -0.0]

    for value in values:
        print("\n" + "-" * 50)
        describe_float(value)


# =============================================================================
# 6. NORMALIZED NUMBERS
# =============================================================================

def demonstrate_normalized_encoding() -> None:
    """
    Explain normalized binary64 values.

    For normal values:

        (-1)^sign × (1.fraction)₂ × 2^(E - bias)

    The leading 1 is implicit and therefore is not stored in the fraction
    field.
    """
    section("6. Normalized IEEE 754 Numbers")

    value = 6.5

    print(f"Value: {value}")
    print("6.5 in binary = 110.1₂")
    print("Normalized      = 1.101₂ × 2²")

    bits = float_to_uint64(value)
    exponent_field = (bits >> 52) & 0x7FF
    fraction_field = bits & ((1 << 52) - 1)

    print(f"\nStored exponent field = {exponent_field}")
    print(f"Unbiased exponent     = {exponent_field - 1023}")
    print(f"Stored fraction       = {fraction_field:052b}")
    print("The leading normalized 1 is implicit.")


# =============================================================================
# 7. DECIMAL TO BINARY CONVERSION
# =============================================================================

def decimal_fraction_to_binary(
    fraction: Fraction,
    maximum_bits: int = 64,
) -> str:
    """
    Produce a binary expansion for a non-negative Fraction.

    The result is truncated after maximum_bits fractional positions.
    This function is intended for educational inspection rather than IEEE
    encoding.
    """
    if fraction < 0:
        raise ValueError("This demonstration expects a non-negative value.")

    integer_part = fraction.numerator // fraction.denominator
    remainder = fraction - integer_part

    integer_bits = bin(integer_part)[2:]

    if remainder == 0:
        return integer_bits

    fractional_bits = []
    for _ in range(maximum_bits):
        remainder *= 2
        if remainder >= 1:
            fractional_bits.append("1")
            remainder -= 1
        else:
            fractional_bits.append("0")

        if remainder == 0:
            break

    suffix = "" if remainder == 0 else "..."
    return integer_bits + "." + "".join(fractional_bits) + suffix


def demonstrate_decimal_to_binary() -> None:
    """Convert several exact rational values to binary expansions."""
    section("7. Decimal and Rational Values in Binary")

    examples = [
        Fraction(1, 2),
        Fraction(3, 4),
        Fraction(1, 8),
        Fraction(1, 10),
        Fraction(1, 5),
        Fraction(1, 3),
    ]

    for value in examples:
        binary = decimal_fraction_to_binary(value, maximum_bits=32)
        print(f"{value!s:>5} = {float(value):.17g} -> {binary}")

    print(
        "\nA rational number has a finite binary expansion only when its "
        "reduced denominator contains no prime factors other than 2."
    )


# =============================================================================
# 8. EXACTLY REPRESENTABLE DECIMAL FRACTIONS
# =============================================================================

def is_exact_binary_fraction(fraction: Fraction) -> bool:
    """
    Determine whether a rational number has a finite binary expansion.

    After reducing the denominator, repeatedly divide out factors of two.
    A denominator of 1 means the value has a finite binary representation.
    """
    denominator = fraction.denominator

    while denominator % 2 == 0:
        denominator //= 2

    return denominator == 1


def demonstrate_exact_representation() -> None:
    """Show which simple rational numbers terminate in binary."""
    section("8. Which Fractions Are Exactly Representable?")

    examples = [
        Fraction(1, 2),
        Fraction(1, 4),
        Fraction(3, 8),
        Fraction(1, 10),
        Fraction(1, 20),
        Fraction(7, 16),
        Fraction(1, 3),
    ]

    for value in examples:
        status = "finite binary expansion" if is_exact_binary_fraction(value) else (
            "infinite binary expansion"
        )
        print(f"{value!s:>5}: {status}")


# =============================================================================
# 9. PRECISION
# =============================================================================

def demonstrate_precision() -> None:
    """
    Demonstrate binary64's approximately 15-17 decimal significant-digit
    behavior.

    Binary64 has 53 significant binary bits for normal numbers.
    """
    section("9. Precision")

    print(f"Binary64 significand precision: {sys.float_info.mant_dig} bits")
    print(f"Decimal digits commonly associated with precision: {sys.float_info.dig}")

    values = [
        1.234567890123456,
        1.2345678901234567,
        1.23456789012345678,
        123456789012345.0,
        1234567890123456.0,
    ]

    for value in values:
        print(f"{value!r:>22} -> {value:.17g}")

    print(
        "\nPrecision is not the same as range. Precision describes how many "
        "significant bits can distinguish nearby values."
    )


# =============================================================================
# 10. MACHINE EPSILON
# =============================================================================

def compute_machine_epsilon() -> float:
    """
    Compute machine epsilon by repeatedly halving a positive value.

    For binary64, this produces 2^-52, which is the distance from 1.0 to the
    next larger representable value.
    """
    epsilon = 1.0

    while 1.0 + epsilon / 2.0 != 1.0:
        epsilon /= 2.0

    return epsilon


def demonstrate_machine_epsilon() -> None:
    """Explore machine epsilon and its relationship to representability."""
    section("10. Machine Epsilon")

    computed = compute_machine_epsilon()
    library_value = sys.float_info.epsilon

    print(f"Computed epsilon : {computed:.20e}")
    print(f"Library epsilon  : {library_value:.20e}")
    print(f"2^-52            : {2.0**-52:.20e}")

    print("\nBehavior near 1.0:")
    for factor in [0.25, 0.5, 1.0, 2.0, 4.0]:
        delta = factor * library_value
        print(
            f"1.0 + {factor:g}*epsilon = "
            f"{1.0 + delta:.17g}"
        )


# =============================================================================
# 11. ULP
# =============================================================================

def ulp_distance(value: float) -> float:
    """
    Return the spacing to the next representable float toward +infinity.

    math.nextafter() is used because spacing changes with magnitude.
    """
    if math.isnan(value):
        return math.nan

    next_value = math.nextafter(value, math.inf)
    return next_value - value


def demonstrate_ulp() -> None:
    """
    Explain ULP, meaning Unit in the Last Place.

    Unlike machine epsilon, ULP spacing depends on the magnitude of the
    floating-point value.
    """
    section("11. ULP and Spacing")

    values = [1.0, 2.0, 10.0, 1_000_000.0, 1e20, 1e-20]

    for value in values:
        print(
            f"value={value:>12.4g}, "
            f"next={math.nextafter(value, math.inf):.17g}, "
            f"ULP={ulp_distance(value):.17g}"
        )

    print(
        "\nFor normal binary64 values, spacing grows approximately in "
        "proportion to the magnitude of the value."
    )


# =============================================================================
# 12. NEXTAFTER AND ADJACENT REPRESENTABLE VALUES
# =============================================================================

def demonstrate_nextafter() -> None:
    """Show how to inspect adjacent floating-point values."""
    section("12. Adjacent Floating-Point Values")

    value = 1.0

    lower = math.nextafter(value, -math.inf)
    upper = math.nextafter(value, math.inf)

    print(f"Previous value below 1.0: {lower:.17g}")
    print(f"Exactly 1.0            : {value:.17g}")
    print(f"Next value above 1.0   : {upper:.17g}")

    print(f"\n1.0 - previous = {value - lower:.20e}")
    print(f"next - 1.0     = {upper - value:.20e}")

    print(
        "\nThe spacing immediately below and above a power of two can differ."
    )


# =============================================================================
# 13. ROUNDING
# =============================================================================

def demonstrate_rounding_error() -> None:
    """
    Demonstrate round-to-nearest-even and representation error.

    Python's binary64 operations normally use the hardware/implementation
    floating-point arithmetic defined by IEEE 754 semantics.
    """
    section("13. Rounding and Representation Error")

    value = 0.1
    exact = Fraction(1, 10)
    stored = Fraction.from_float(value)
    error = stored - exact

    print(f"Requested decimal value : {value}")
    print(f"Exact rational value    : {exact}")
    print(f"Stored binary64 value   : {stored}")
    print(f"Exact representation?   : {stored == exact}")
    print(f"Representation error    : {error}")
    print(f"Error as float          : {float(error):.20e}")

    print("\nPython's repr() is designed to provide a useful round-trip string:")
    print(repr(value))


# =============================================================================
# 14. THE CLASSIC 0.1 + 0.2 EXAMPLE
# =============================================================================

def demonstrate_why_point_one_plus_point_two_is_not_exact() -> None:
    """Inspect the classic floating-point addition example."""
    section("14. Why 0.1 + 0.2 Is Not Exactly 0.3")

    a = 0.1
    b = 0.2
    result = a + b

    print(f"0.1 + 0.2 = {result:.17g}")
    print(f"0.3       = {0.3:.17g}")
    print(f"Exact equality: {result == 0.3}")

    print("\nHexadecimal representations:")
    print(f"0.1 -> {a.hex()}")
    print(f"0.2 -> {b.hex()}")
    print(f"0.3 -> {0.3.hex()}")
    print(f"sum -> {result.hex()}")

    print(
        "\nThe issue is not that addition itself is broken. The operands "
        "are already rounded binary approximations, and the correctly "
        "rounded result of adding those approximations is not the same "
        "binary64 value as the separately rounded decimal value 0.3."
    )


# =============================================================================
# 15. ACCUMULATION OF ERROR
# =============================================================================

def demonstrate_accumulated_error() -> None:
    """Show how repeated floating-point operations can accumulate error."""
    section("15. Accumulated Rounding Error")

    naive_sum = 0.0

    for _ in range(10):
        naive_sum += 0.1

    print(f"Ten additions of 0.1: {naive_sum:.17g}")
    print(f"Exact mathematical result: 1.0")
    print(f"Difference: {naive_sum - 1.0:.20e}")

    print("\nLarge count example:")
    total = sum(0.01 for _ in range(100))
    print(f"sum(0.01 for _ in range(100)) = {total:.17g}")
    print(f"Difference from 1.0          = {total - 1.0:.20e}")


# =============================================================================
# 16. CANCELLATION
# =============================================================================

def demonstrate_cancellation() -> None:
    """
    Demonstrate cancellation.

    Subtracting two nearly equal numbers can eliminate leading significant
    digits, leaving a result dominated by previously introduced errors.
    """
    section("16. Catastrophic Cancellation")

    large_a = 1_000_000_000_000_000.0
    large_b = 999_999_999_999_999.0

    direct_difference = large_a - large_b

    print(f"a = {large_a:.17g}")
    print(f"b = {large_b:.17g}")
    print(f"a - b = {direct_difference:.17g}")

    x = 1e16
    expression = math.sqrt(x * x + 1.0) - x

    print("\nA cancellation-prone expression:")
    print(f"sqrt(x² + 1) - x for x={x:.1e}")
    print(f"Naive result: {expression:.17g}")

    stable_expression = 1.0 / (math.sqrt(x * x + 1.0) + x)
    print(f"Stable reformulation: {stable_expression:.17g}")

    print(
        "\nThe algebraically equivalent rationalized expression avoids "
        "subtracting two nearly equal large quantities."
    )


# =============================================================================
# 17. ABSORPTION
# =============================================================================

def demonstrate_absorption() -> None:
    """
    Demonstrate absorption, where adding a very small number to a very large
    number can produce no observable change in floating-point representation.
    """
    section("17. Absorption and Loss of Small Terms")

    large = 1e16
    small = 1.0

    result = large + small

    print(f"large = {large:.17g}")
    print(f"small = {small:.17g}")
    print(f"large + small = {result:.17g}")
    print(f"Changed? {result != large}")

    print(
        "\nThis happens because the spacing between representable values near "
        "1e16 is larger than 1.0."
    )
    print(f"ULP near 1e16 = {ulp_distance(large):.17g}")


# =============================================================================
# 18. OVERFLOW
# =============================================================================

def demonstrate_overflow() -> None:
    """
    Demonstrate floating-point overflow.

    Binary64's largest finite value is approximately 1.7976931348623157e308.
    """
    section("18. Overflow")

    maximum = sys.float_info.max

    print(f"Maximum finite binary64 value: {maximum:.17e}")

    multiplied = maximum * 2.0
    print(f"maximum * 2.0: {multiplied}")
    print(f"Is infinity? {math.isinf(multiplied)}")

    try:
        integer_power = 10.0**400
        print(integer_power)
    except OverflowError as error:
        print(f"10.0**400 raised OverflowError: {error}")

    print(
        "\nOverflow generally produces infinity for IEEE 754 floating-point "
        "operations, although particular language/library operations may "
        "raise an exception instead."
    )


# =============================================================================
# 19. UNDERFLOW
# =============================================================================

def demonstrate_underflow() -> None:
    """
    Demonstrate gradual underflow.

    Binary64's smallest positive normal value is approximately 2^-1022.
    Values below this can be represented as subnormals down to approximately
    2^-1074.
    """
    section("19. Underflow and Subnormal Numbers")

    minimum_normal = sys.float_info.min
    minimum_subnormal = math.nextafter(0.0, math.inf)

    print(f"Minimum positive normal: {minimum_normal:.17e}")
    print(f"Minimum positive subnormal: {minimum_subnormal:.17e}")

    print("\nA sequence of powers near the lower range:")
    for exponent in [-1020, -1022, -1023, -1070, -1074]:
        value = 2.0**exponent
        print(f"2^{exponent:5d} = {value:.17e}")

    print(
        "\nSubnormals preserve a gradual transition toward zero instead of "
        "immediately flushing every value below the normal threshold to zero."
    )


# =============================================================================
# 20. SPECIAL VALUES
# =============================================================================

def demonstrate_special_values() -> None:
    """Demonstrate zero, signed zero, infinity, and NaN."""
    section("20. IEEE 754 Special Values")

    positive_zero = 0.0
    negative_zero = -0.0
    positive_infinity = math.inf
    negative_infinity = -math.inf
    not_a_number = math.nan

    values = [
        ("+0", positive_zero),
        ("-0", negative_zero),
        ("+infinity", positive_infinity),
        ("-infinity", negative_infinity),
        ("NaN", not_a_number),
    ]

    for name, value in values:
        print(f"{name:>12}: value={value!r}, hex={value.hex()}")

    print("\nClassification:")
    for name, value in values:
        print(
            f"{name:>12}: "
            f"finite={math.isfinite(value)}, "
            f"infinite={math.isinf(value)}, "
            f"nan={math.isnan(value)}"
        )


# =============================================================================
# 21. SIGNED ZERO
# =============================================================================

def demonstrate_signed_zero() -> None:
    """
    Signed zero compares equal numerically but can preserve directional
    information in certain operations.
    """
    section("21. Signed Zero")

    positive_zero = 0.0
    negative_zero = -0.0

    print(f"+0 == -0: {positive_zero == negative_zero}")
    print(f"copysign(+1, +0): {math.copysign(1.0, positive_zero)}")
    print(f"copysign(+1, -0): {math.copysign(1.0, negative_zero)}")

    print("\nDivision by zero is normally an exception in Python:")
    for value in [positive_zero, negative_zero]:
        try:
            print(1.0 / value)
        except ZeroDivisionError as error:
            print(f"1.0 / {value!r} -> {type(error).__name__}")

    print(
        "\nIEEE 754 defines signed zero, but language-level handling of "
        "operations involving zero can differ."
    )


# =============================================================================
# 22. NaN
# =============================================================================

def demonstrate_nan() -> None:
    """Demonstrate important NaN semantics."""
    section("22. NaN Semantics")

    nan_value = float("nan")

    print(f"nan == nan: {nan_value == nan_value}")
    print(f"nan != nan: {nan_value != nan_value}")
    print(f"math.isnan(nan): {math.isnan(nan_value)}")

    print("\nArithmetic involving NaN:")
    print(f"nan + 10.0 = {nan_value + 10.0}")
    print(f"nan * 10.0 = {nan_value * 10.0}")
    print(f"nan < 10.0  = {nan_value < 10.0}")
    print(f"nan > 10.0  = {nan_value > 10.0}")

    print(
        "\nNaN should normally be detected with math.isnan(), not by comparing "
        "a value with itself."
    )


# =============================================================================
# 23. INFINITY
# =============================================================================

def demonstrate_infinity() -> None:
    """Demonstrate infinity propagation and exceptional expressions."""
    section("23. Infinity")

    positive_infinity = math.inf
    negative_infinity = -math.inf

    print(f"inf + 100 = {positive_infinity + 100}")
    print(f"inf * 2   = {positive_infinity * 2}")
    print(f"-inf < 0  = {negative_infinity < 0}")

    print("\nOperations that become undefined in IEEE 754:")
    undefined_results = [
        ("inf - inf", positive_infinity - positive_infinity),
        ("inf * 0", positive_infinity * 0.0),
        ("inf / inf", positive_infinity / positive_infinity),
    ]

    for expression, result in undefined_results:
        print(f"{expression:12} -> {result}")


# =============================================================================
# 24. SUBNORMAL DETECTION
# =============================================================================

def is_subnormal(value: float) -> bool:
    """Return True when value is finite, nonzero, and below the normal range."""
    return (
        value != 0.0
        and math.isfinite(value)
        and abs(value) < sys.float_info.min
    )


def demonstrate_subnormal_detection() -> None:
    """Classify values around the normal/subnormal boundary."""
    section("24. Detecting Subnormal Values")

    values = [
        0.0,
        math.nextafter(0.0, math.inf),
        sys.float_info.min,
        sys.float_info.min / 2.0,
    ]

    for value in values:
        print(
            f"{value:.17e}: "
            f"subnormal={is_subnormal(value)}, "
            f"finite={math.isfinite(value)}"
        )


# =============================================================================
# 25. FLOAT TO RATIONAL
# =============================================================================

def demonstrate_exact_stored_value() -> None:
    """
    Show the exact rational value represented by a Python float.

    Fraction.from_float() exposes the exact binary64 value rather than the
    decimal number that the programmer originally intended.
    """
    section("25. Exact Rational Value of a Binary64 Float")

    values = [0.1, 0.2, 0.3, 1.5, 0.125]

    for value in values:
        exact = Fraction.from_float(value)
        print(f"{value!r:>5} -> {exact}")

    print(
        "\nValues such as 0.125 are exact because 1/8 has a denominator "
        "that is a power of two."
    )


# =============================================================================
# 26. HEXADECIMAL FLOATING-POINT NOTATION
# =============================================================================

def demonstrate_hex_float() -> None:
    """
    Python's float.hex() provides an exact hexadecimal representation of the
    binary floating-point value.
    """
    section("26. Hexadecimal Floating-Point Notation")

    values = [0.1, 0.5, 1.0, 6.5, math.pi]

    for value in values:
        hexadecimal = value.hex()
        reconstructed = float.fromhex(hexadecimal)

        print(f"value        = {value!r}")
        print(f"hexadecimal  = {hexadecimal}")
        print(f"reconstructed = {reconstructed!r}")
        print(f"exact round trip = {value == reconstructed}")
        print()


# =============================================================================
# 27. FLOAT COMPARISON
# =============================================================================

def demonstrate_float_comparison() -> None:
    """Show why direct equality can be inappropriate for approximate results."""
    section("27. Floating-Point Equality")

    a = 0.1 + 0.2
    b = 0.3

    print(f"a = {a:.17g}")
    print(f"b = {b:.17g}")
    print(f"a == b: {a == b}")

    print("\nUsing math.isclose:")
    print(f"math.isclose(a, b): {math.isclose(a, b)}")

    print(
        "\nFor numerical comparisons, tolerance should reflect the error "
        "scale and requirements of the problem."
    )


# =============================================================================
# 28. ABSOLUTE AND RELATIVE TOLERANCE
# =============================================================================

def demonstrate_tolerances() -> None:
    """
    Explain absolute versus relative tolerance.

    math.isclose() uses:

        abs(a-b) <= max(rel_tol * max(|a|, |b|), abs_tol)
    """
    section("28. Absolute and Relative Tolerance")

    pairs = [
        (1.000000000000001, 1.0),
        (1_000_000.0, 1_000_000.000001),
        (1e-12, 0.0),
    ]

    for a, b in pairs:
        print(f"a={a:.17g}, b={b:.17g}")
        print(f"  default isclose: {math.isclose(a, b)}")
        print(
            f"  strict relative tolerance: "
            f"{math.isclose(a, b, rel_tol=1e-12, abs_tol=0.0)}"
        )
        print(
            f"  absolute tolerance 1e-10: "
            f"{math.isclose(a, b, rel_tol=0.0, abs_tol=1e-10)}"
        )

    print(
        "\nAn absolute tolerance is particularly important when values are "
        "near zero because relative error can become poorly conditioned."
    )


# =============================================================================
# 29. KAHAN SUMMATION
# =============================================================================

def naive_sum(values: Iterable[float]) -> float:
    """Compute a straightforward floating-point sum."""
    total = 0.0

    for value in values:
        total += value

    return total


def kahan_sum(values: Iterable[float]) -> float:
    """
    Compute a sum using Kahan compensated summation.

    The compensation variable tracks low-order information lost during
    floating-point addition.
    """
    total = 0.0
    compensation = 0.0

    for value in values:
        corrected_value = value - compensation
        temporary = total + corrected_value
        compensation = (temporary - total) - corrected_value
        total = temporary

    return total


def demonstrate_kahan_summation() -> None:
    """Compare naive and compensated summation."""
    section("29. Kahan Compensated Summation")

    values = [0.1] * 10_000

    naive = naive_sum(values)
    compensated = kahan_sum(values)
    exact = 1_000.0

    print(f"Exact mathematical result: {exact:.17g}")
    print(f"Naive sum               : {naive:.17g}")
    print(f"Kahan sum               : {compensated:.17g}")
    print(f"Naive absolute error    : {abs(naive - exact):.20e}")
    print(f"Kahan absolute error    : {abs(compensated - exact):.20e}")

    print(
        "\nCompensated summation can reduce error, although it adds operations "
        "and does not make floating-point arithmetic exact."
    )


# =============================================================================
# 30. PAIRWISE SUMMATION
# =============================================================================

def pairwise_sum(values: list[float]) -> float:
    """
    Sum values recursively in balanced groups.

    Pairwise summation can reduce accumulated error compared with a simple
    left-to-right sum for some data distributions.
    """
    if not values:
        return 0.0

    if len(values) == 1:
        return values[0]

    midpoint = len(values) // 2
    return pairwise_sum(values[:midpoint]) + pairwise_sum(values[midpoint:])


def demonstrate_pairwise_summation() -> None:
    """Compare summation strategies."""
    section("30. Pairwise Summation")

    values = [0.1] * 10_000

    print(f"Naive sum   : {naive_sum(values):.17g}")
    print(f"Pairwise sum: {pairwise_sum(values):.17g}")
    print(f"Kahan sum   : {kahan_sum(values):.17g}")


# =============================================================================
# 31. NUMERICALLY STABLE LOGARITHMIC CALCULATIONS
# =============================================================================

def stable_log_one_plus_x(x: float) -> float:
    """
    Compute log(1+x) accurately for small x.

    math.log1p(x) is designed to avoid losing precision when x is close to
    zero.
    """
    return math.log1p(x)


def demonstrate_stable_logarithms() -> None:
    """Compare naive and stable log(1+x) calculations."""
    section("31. Numerically Stable Functions")

    x = 1e-16

    naive = math.log(1.0 + x)
    stable = math.log1p(x)

    print(f"x = {x:.17g}")
    print(f"log(1 + x) naive : {naive:.17g}")
    print(f"log1p(x)         : {stable:.17g}")

    print(
        "\nLibrary functions such as log1p, expm1, hypot, and fsum exist "
        "because straightforward algebraic expressions can lose precision."
    )


# =============================================================================
# 32. HIGH-ACCURACY SUMMATION WITH math.fsum
# =============================================================================

def demonstrate_math_fsum() -> None:
    """Demonstrate Python's higher-accuracy summation function."""
    section("32. math.fsum")

    values = [0.1] * 10_000

    naive = sum(values)
    accurate = math.fsum(values)

    print(f"sum(values)  = {naive:.17g}")
    print(f"math.fsum    = {accurate:.17g}")
    print(f"Expected     = {1000.0:.17g}")


# =============================================================================
# 33. ORDER-DEPENDENCE
# =============================================================================

def demonstrate_order_dependence() -> None:
    """
    Show that floating-point addition is not generally associative.

    Mathematically:
        (a+b)+c = a+(b+c)

    In floating-point arithmetic, the rounded intermediate result can make
    the two expressions different.
    """
    section("33. Non-Associativity of Floating-Point Addition")

    a = 1e16
    b = -1e16
    c = 1.0

    left_associative = (a + b) + c
    right_associative = a + (b + c)

    print(f"(a + b) + c = {left_associative}")
    print(f"a + (b + c) = {right_associative}")

    print(f"Equal? {left_associative == right_associative}")

    print(
        "\nThis is one reason parallel reductions and distributed numerical "
        "computations can produce slightly different results depending on "
        "the order in which partial sums are combined."
    )


# =============================================================================
# 34. FMA
# =============================================================================

def demonstrate_fma_concept() -> None:
    """
    Explain fused multiply-add.

    A true FMA computes a*b+c with one final rounding rather than separately
    rounding the multiplication and addition.

    Python versions/platforms do not universally expose math.fma(), so this
    demonstration detects availability rather than assuming it exists.
    """
    section("34. Fused Multiply-Add")

    a = 1.0000000000000002
    b = 1.0000000000000002
    c = -1.0

    separate = a * b + c

    print(f"a * b + c using separate operations: {separate:.17g}")

    fma_function = getattr(math, "fma", None)

    if fma_function is not None:
        fused = fma_function(a, b, c)
        print(f"math.fma(a, b, c): {fused:.17g}")
    else:
        print(
            "This Python build does not expose math.fma(); a true fused "
            "operation cannot be demonstrated directly here."
        )

    print(
        "\nFMA is important in numerical algorithms because reducing the "
        "number of intermediate roundings can improve accuracy."
    )


# =============================================================================
# 35. FLOAT RANGE
# =============================================================================

def demonstrate_float_range() -> None:
    """Print important binary64 range constants."""
    section("35. Binary64 Range")

    info = sys.float_info

    print(f"radix             = {info.radix}")
    print(f"mant_dig          = {info.mant_dig}")
    print(f"digits             = {info.dig}")
    print(f"epsilon            = {info.epsilon:.17e}")
    print(f"minimum normal     = {info.min:.17e}")
    print(f"maximum             = {info.max:.17e}")
    print(f"max exponent       = {info.max_exp}")
    print(f"min exponent       = {info.min_exp}")
    print(f"max 10 exponent    = {info.max_10_exp}")
    print(f"min 10 exponent    = {info.min_10_exp}")


# =============================================================================
# 36. INTEGER EXACTNESS
# =============================================================================

def demonstrate_exact_integer_range() -> None:
    """
    Binary64 can exactly represent every integer through 2^53.

    Above that threshold, not every integer is representable.
    """
    section("36. Exact Integer Representation")

    exact_limit = 2**53

    print(f"2^53       = {exact_limit}")
    print(f"float(2^53) = {float(exact_limit):.0f}")

    nearby_integers = [
        exact_limit - 1,
        exact_limit,
        exact_limit + 1,
        exact_limit + 2,
        exact_limit + 3,
    ]

    for integer in nearby_integers:
        converted = float(integer)
        print(f"{integer} -> float -> {converted:.0f}")

    print(
        "\nThe important threshold is not that floats stop representing "
        "integers at 2^53. Rather, above 2^53, the spacing becomes greater "
        "than 1, so some consecutive integers cannot be represented."
    )


# =============================================================================
# 37. ROUNDING TO EVEN
# =============================================================================

def demonstrate_round_to_even() -> None:
    """
    Python's built-in round() uses round-half-to-even for decimal rounding.

    IEEE 754's default rounding direction is also roundTiesToEven, although
    Python's round() and binary arithmetic are distinct mechanisms.
    """
    section("37. Round-to-Nearest, Ties-to-Even")

    examples = [2.5, 3.5, 4.5, 5.5, -2.5, -3.5]

    for value in examples:
        print(f"round({value}) = {round(value)}")

    print(
        "\nTie-to-even reduces systematic bias that can arise when every exact "
        "halfway case is rounded in the same direction."
    )


# =============================================================================
# 38. DECIMAL MODULE
# =============================================================================

def demonstrate_decimal() -> None:
    """
    Demonstrate Decimal for decimal arithmetic.

    Decimal values constructed from strings preserve the intended decimal
    value exactly within the configured Decimal context.
    """
    section("38. Decimal Arithmetic")

    binary_result = 0.1 + 0.2
    decimal_result = Decimal("0.1") + Decimal("0.2")

    print(f"float:   {binary_result!r}")
    print(f"Decimal: {decimal_result!r}")
    print(f"Decimal equals Decimal('0.3'): {decimal_result == Decimal('0.3')}")

    print("\nImportant construction distinction:")
    decimal_from_float = Decimal(0.1)
    decimal_from_string = Decimal("0.1")

    print(f"Decimal(0.1)    = {decimal_from_float}")
    print(f"Decimal('0.1')  = {decimal_from_string}")

    print(
        "\nWhen exact decimal intent matters, construct Decimal from a string "
        "or another exact decimal source rather than first creating a binary "
        "float."
    )


# =============================================================================
# 39. DECIMAL CONTEXT AND ROUNDING
# =============================================================================

def demonstrate_decimal_context() -> None:
    """Demonstrate controlled Decimal precision and rounding."""
    section("39. Decimal Context and Rounding")

    with localcontext() as context:
        context.prec = 10
        value = Decimal(1) / Decimal(7)
        print(f"Precision 10: {value}")

    with localcontext() as context:
        context.prec = 30
        value = Decimal(1) / Decimal(7)
        print(f"Precision 30: {value}")

    value = Decimal("2.675")
    rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)

    print(f"\n2.675 rounded to two decimal places: {rounded}")


# =============================================================================
# 40. FRACTION MODULE
# =============================================================================

def demonstrate_fraction() -> None:
    """Demonstrate exact rational arithmetic with Fraction."""
    section("40. Exact Rational Arithmetic")

    a = Fraction(1, 10)
    b = Fraction(2, 10)

    result = a + b

    print(f"1/10 + 2/10 = {result}")
    print(f"Equals 3/10 exactly? {result == Fraction(3, 10)}")
    print(f"As float: {float(result):.17g}")

    print("\nConstructing from a float preserves the exact float value:")
    print(f"Fraction.from_float(0.1) = {Fraction.from_float(0.1)}")
    print(f"Fraction(0.1)            = {Fraction(0.1)}")


# =============================================================================
# 41. FINANCIAL ARITHMETIC EXAMPLE
# =============================================================================

def calculate_compound_interest_float(
    principal: float,
    annual_rate: float,
    periods: int,
) -> float:
    """Calculate compound growth using binary floating-point."""
    return principal * (1.0 + annual_rate) ** periods


def calculate_compound_interest_decimal(
    principal: Decimal,
    annual_rate: Decimal,
    periods: int,
) -> Decimal:
    """Calculate compound growth using Decimal arithmetic."""
    return principal * (Decimal(1) + annual_rate) ** periods


def demonstrate_financial_choice() -> None:
    """Compare float and Decimal for a simple financial calculation."""
    section("41. Choosing Numeric Types for Financial Calculations")

    principal_float = 1000.0
    rate_float = 0.075
    periods = 10

    float_result = calculate_compound_interest_float(
        principal_float,
        rate_float,
        periods,
    )

    principal_decimal = Decimal("1000.00")
    rate_decimal = Decimal("0.075")

    decimal_result = calculate_compound_interest_decimal(
        principal_decimal,
        rate_decimal,
        periods,
    )

    print(f"Float result   : {float_result:.17g}")
    print(f"Decimal result : {decimal_result}")

    print(
        "\nFor monetary systems, Decimal or integer minor units are commonly "
        "preferred when exact decimal accounting rules are required."
    )


# =============================================================================
# 42. INTEGER MINOR UNITS
# =============================================================================

def demonstrate_integer_minor_units() -> None:
    """Demonstrate storing currency as integer minor units."""
    section("42. Integer Minor Units")

    price_cents = 1999
    quantity = 3

    total_cents = price_cents * quantity

    print(f"Price: {price_cents} cents")
    print(f"Quantity: {quantity}")
    print(f"Total: {total_cents} cents")
    print(f"Total in dollars: ${total_cents / 100:.2f}")

    print(
        "\nInteger minor units avoid binary floating-point representation "
        "errors for fixed-scale currency amounts, provided the domain uses "
        "a suitable fixed scale."
    )


# =============================================================================
# 43. CONVERSION TO BINARY32
# =============================================================================

def float32_round_trip(value: float) -> float:
    """
    Round a Python binary64 value to IEEE 754 binary32 and back to Python float.

    struct.pack('f') creates a 32-bit IEEE-style single-precision value on
    standard Python implementations using IEEE 754 binary32 semantics.
    """
    return struct.unpack(">f", struct.pack(">f", value))[0]


def demonstrate_binary32_precision() -> None:
    """Compare binary32 and binary64 precision."""
    section("43. Binary32 versus Binary64")

    values = [
        math.pi,
        0.1,
        1_000_000.123,
        123456.789,
    ]

    for value in values:
        single = float32_round_trip(value)

        print(f"Original binary64: {value:.17g}")
        print(f"Binary32 value   : {single:.17g}")
        print(f"Difference        : {single - value:.17g}")
        print()


# =============================================================================
# 44. BINARY32 BIT INSPECTION
# =============================================================================

def float_to_uint32(value: float) -> int:
    """Return the raw IEEE 754 binary32 bit pattern."""
    return struct.unpack(">I", struct.pack(">f", value))[0]


def decode_binary32_bits(bits: int) -> dict[str, object]:
    """Decode the fields of a binary32 bit pattern."""
    if not 0 <= bits <= 0xFFFFFFFF:
        raise ValueError("bits must be a 32-bit unsigned integer.")

    sign = (bits >> 31) & 1
    exponent_field = (bits >> 23) & 0xFF
    fraction_field = bits & ((1 << 23) - 1)

    if exponent_field == 0:
        category = "zero" if fraction_field == 0 else "subnormal"
    elif exponent_field == 0xFF:
        category = "infinity" if fraction_field == 0 else "nan"
    else:
        category = "normal"

    return {
        "sign": sign,
        "exponent_field": exponent_field,
        "fraction_field": fraction_field,
        "category": category,
    }


def demonstrate_binary32_encoding() -> None:
    """Inspect a binary32 value."""
    section("44. Binary32 Bit Fields")

    value = 0.1
    bits = float_to_uint32(value)
    decoded = decode_binary32_bits(bits)

    print(f"value          = {value!r}")
    print(f"binary32 bits  = {bits_to_string(bits, 32)}")
    print(f"sign           = {decoded['sign']}")
    print(f"exponent field = {decoded['exponent_field']}")
    print(f"fraction field = {decoded['fraction_field']}")
    print(f"category       = {decoded['category']}")


# =============================================================================
# 45. RECONSTRUCTING NORMALIZED BINARY64
# =============================================================================

def reconstruct_normal_binary64(bits: int) -> float:
    """
    Reconstruct a normal binary64 value directly from its fields.

    This educational function handles only normal finite values.
    """
    decoded = decode_binary64_bits(bits)

    if decoded["category"] != "normal":
        raise ValueError("The bit pattern is not a normal finite number.")

    sign = int(decoded["sign"])
    exponent_field = int(decoded["exponent_field"])
    fraction_field = int(decoded["fraction_field"])

    significand = 1.0 + fraction_field / (2**52)
    exponent = exponent_field - 1023

    return (-1.0 if sign else 1.0) * significand * (2.0**exponent)


def demonstrate_reconstruction() -> None:
    """Reconstruct normal values from their IEEE 754 fields."""
    section("45. Reconstructing Normal Binary64 Values")

    values = [1.0, -2.5, 6.5, math.pi]

    for value in values:
        bits = float_to_uint64(value)
        reconstructed = reconstruct_normal_binary64(bits)

        print(f"Original      : {value:.17g}")
        print(f"Reconstructed : {reconstructed:.17g}")
        print(f"Equal         : {value == reconstructed}")
        print()


# =============================================================================
# 46. SPECIAL IEEE 754 ENCODINGS
# =============================================================================

def demonstrate_special_bit_patterns() -> None:
    """
    Show canonical bit-pattern categories.

    Binary64:
        exponent = 0, fraction = 0       -> zero
        exponent = 0, fraction != 0      -> subnormal
        exponent = 2047, fraction = 0    -> infinity
        exponent = 2047, fraction != 0   -> NaN
    """
    section("46. IEEE 754 Special Bit Patterns")

    patterns = {
        "+0": 0x0000000000000000,
        "-0": 0x8000000000000000,
        "+inf": 0x7FF0000000000000,
        "-inf": 0xFFF0000000000000,
        "smallest positive subnormal": 0x0000000000000001,
        "example NaN": 0x7FF8000000000000,
    }

    for name, bits in patterns.items():
        decoded = decode_binary64_bits(bits)
        value = decoded["value"]

        print(f"{name:30} bits={bits_to_string(bits)} value={value!r}")


# =============================================================================
# 47. NaN PAYLOADS AND COMPARISON
# =============================================================================

def demonstrate_nan_payload_behavior() -> None:
    """
    Demonstrate that NaN encodings can contain fraction bits.

    The exact propagation and payload behavior can depend on operations and
    implementation details, so applications should not rely on a particular
    NaN payload being preserved.
    """
    section("47. NaN Payloads")

    nan_bits = 0x7FF8000000000042
    value = uint64_to_float(nan_bits)

    print(f"NaN bit pattern: {bits_to_string(nan_bits)}")
    print(f"Decoded value: {value!r}")
    print(f"math.isnan(value): {math.isnan(value)}")

    print(
        "\nNaN payload bits exist in IEEE 754 encodings, but portable application "
        "logic should normally treat NaN as a category rather than depending "
        "on payload details."
    )


# =============================================================================
# 48. ROUND-TRIP DECIMAL CONVERSION
# =============================================================================

def demonstrate_decimal_round_trip() -> None:
    """
    Explain why a sufficiently precise decimal representation can reproduce
    the same binary64 value.
    """
    section("48. Decimal Round Trips")

    values = [0.1, math.pi, 1.0 / 3.0, 1.2345678901234567]

    for value in values:
        text = repr(value)
        reconstructed = float(text)

        print(f"value          = {value!r}")
        print(f"repr           = {text}")
        print(f"reconstructed  = {reconstructed!r}")
        print(f"same bits      = {float_to_uint64(value) == float_to_uint64(reconstructed)}")
        print()


# =============================================================================
# 49. FORMAT PRECISION
# =============================================================================

def demonstrate_display_vs_storage() -> None:
    """
    Distinguish display formatting from changing the stored floating-point
    value.
    """
    section("49. Display Precision versus Stored Precision")

    value = 1.2345678901234567

    print(f"Stored value repr: {value!r}")
    print(f"Two decimals    : {value:.2f}")
    print(f"Six decimals    : {value:.6f}")
    print(f"17 significant  : {value:.17g}")

    rounded_value = round(value, 2)

    print(f"\nround(value, 2): {rounded_value!r}")
    print(
        "\nFormatting changes how a value is displayed. round() creates a "
        "new numerical value and can therefore discard information."
    )


# =============================================================================
# 50. FLOAT HASHING AND EQUALITY
# =============================================================================

def demonstrate_float_hashing() -> None:
    """Show that equal finite numeric values generally share hash behavior."""
    section("50. Equality and Hashing")

    integer_value = 1
    float_value = 1.0

    print(f"1 == 1.0: {integer_value == float_value}")
    print(f"hash(1) == hash(1.0): {hash(integer_value) == hash(float_value)}")

    print(
        "\nPython's numeric equality and hashing rules allow equal numeric "
        "values of different numeric types to behave consistently as keys."
    )

    nan_value = float("nan")
    print(f"NaN == NaN: {nan_value == nan_value}")
    print(f"hash(NaN): {hash(nan_value)}")


# =============================================================================
# 51. EDGE CASE: EXTREME EXPONENTS
# =============================================================================

def demonstrate_extreme_exponents() -> None:
    """Inspect values close to binary64 exponent limits."""
    section("51. Extreme Exponents")

    values = [
        math.ldexp(1.0, -1022),
        math.ldexp(1.0, -1023),
        math.ldexp(1.0, 1023),
    ]

    for value in values:
        print(f"value={value:.17e}")
        print(f"hex={value.hex()}")
        print()


# =============================================================================
# 52. EDGE CASE: NEGATIVE ZERO IN FORMATTING
# =============================================================================

def demonstrate_negative_zero_formatting() -> None:
    """Show that negative zero can appear in formatted output."""
    section("52. Negative Zero in Output")

    negative_zero = -0.0

    print(f"repr: {negative_zero!r}")
    print(f"fixed-point: {negative_zero:.2f}")
    print(f"sign detected with copysign: {math.copysign(1.0, negative_zero)}")


# =============================================================================
# 53. EDGE CASE: FLOAT CONVERSION OF LARGE INTEGERS
# =============================================================================

def demonstrate_large_integer_conversion() -> None:
    """Show precision loss when converting large integers to float."""
    section("53. Large Integer to Float Conversion")

    integers = [
        2**53 - 1,
        2**53,
        2**53 + 1,
        10**20,
        10**30,
    ]

    for integer in integers:
        converted = float(integer)
        recovered = int(converted)

        print(f"integer  = {integer}")
        print(f"float    = {converted:.17g}")
        print(f"recovered= {recovered}")
        print(f"exact?   = {integer == recovered}")
        print()


# =============================================================================
# 54. CONDITIONING
# =============================================================================

def demonstrate_conditioning() -> None:
    """
    Explain the distinction between conditioning and numerical stability.

    A well-conditioned problem does not magnify small input perturbations much.
    An ill-conditioned problem may be intrinsically sensitive even when solved
    by an excellent algorithm.
    """
    section("54. Conditioning versus Numerical Stability")

    print("Conceptual example: computing a difference of nearly equal values.")
    print("Inputs: a and b")
    print("Problem: f(a,b) = a - b")
    print(
        "If a and b are both huge compared with |a-b|, small relative errors "
        "in a and b can become large relative errors in the difference."
    )

    print(
        "\nConditioning is a property of the mathematical problem. "
        "Stability is a property of the numerical algorithm used to solve it."
    )


# =============================================================================
# 55. SCALE-AWARE COMPARISON
# =============================================================================

def relative_error(approximation: float, reference: float) -> float:
    """
    Calculate relative error.

    If the reference is zero, relative error is undefined in the ordinary
    sense, so math.inf is returned for a nonzero approximation.
    """
    if reference == 0.0:
        return 0.0 if approximation == 0.0 else math.inf

    return abs(approximation - reference) / abs(reference)


def demonstrate_error_metrics() -> None:
    """Demonstrate absolute and relative error."""
    section("55. Absolute Error and Relative Error")

    reference = math.pi
    approximation = 3.14159

    absolute = abs(approximation - reference)
    relative = relative_error(approximation, reference)

    print(f"Reference       : {reference:.17g}")
    print(f"Approximation   : {approximation:.17g}")
    print(f"Absolute error  : {absolute:.17e}")
    print(f"Relative error  : {relative:.17e}")


# =============================================================================
# 56. PROPAGATION OF ERROR
# =============================================================================

def demonstrate_error_propagation() -> None:
    """
    Illustrate first-order error propagation conceptually.

    For y = x^2, a small perturbation dx produces approximately:

        dy ≈ 2x dx

    This is not a replacement for rigorous interval or uncertainty analysis,
    but it illustrates why sensitivity increases with x.
    """
    section("56. Error Propagation")

    x = 1000.0
    dx = 1e-10

    exact_change = (x + dx) ** 2 - x**2
    first_order_change = 2.0 * x * dx

    print(f"x = {x}")
    print(f"dx = {dx:.17e}")
    print(f"Exact change in x²: {exact_change:.17e}")
    print(f"First-order estimate: {first_order_change:.17e}")


# =============================================================================
# 57. VALIDATING FLOATING-POINT INPUT
# =============================================================================

def validate_finite_float(value: float, name: str = "value") -> float:
    """
    Validate that a numeric input is finite.

    Production systems often need explicit policies for NaN and infinity
    rather than allowing special values to propagate silently.
    """
    if not isinstance(value, float):
        raise TypeError(f"{name} must be a float.")

    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite.")

    return value


def demonstrate_validation() -> None:
    """Demonstrate finite-value validation."""
    section("57. Validating Floating-Point Inputs")

    candidates = [1.5, math.inf, math.nan, -3.0]

    for candidate in candidates:
        try:
            validated = validate_finite_float(candidate)
            print(f"{candidate!r}: accepted as {validated!r}")
        except (TypeError, ValueError) as error:
            print(f"{candidate!r}: rejected -> {error}")


# =============================================================================
# 58. NUMERICAL INVARIANTS
# =============================================================================

def demonstrate_numerical_invariant_testing() -> None:
    """
    Show approximate invariant testing.

    Numerical algorithms should often be tested with tolerances rather than
    exact equality.
    """
    section("58. Testing Numerical Results")

    x = 0.1 + 0.2

    exact_expected = 0.3

    print(f"Exact equality test: {x == exact_expected}")
    print(
        "Tolerance test:",
        math.isclose(x, exact_expected, rel_tol=1e-15, abs_tol=1e-15),
    )

    assert math.isclose(
        x,
        exact_expected,
        rel_tol=1e-15,
        abs_tol=1e-15,
    )


# =============================================================================
# 59. PROPERTY-LIKE NUMERICAL TEST
# =============================================================================

def test_float_hex_round_trip() -> None:
    """Assert that float.hex()/fromhex() preserves the exact binary64 value."""
    test_values = [
        0.0,
        -0.0,
        0.1,
        -0.1,
        math.pi,
        math.inf,
        -math.inf,
    ]

    for value in test_values:
        reconstructed = float.fromhex(value.hex())

        if math.isnan(value):
            assert math.isnan(reconstructed)
        else:
            assert float_to_uint64(value) == float_to_uint64(reconstructed)


def demonstrate_round_trip_test() -> None:
    """Run the hexadecimal round-trip test."""
    section("59. Numerical Round-Trip Test")

    test_float_hex_round_trip()
    print("All float hexadecimal round-trip tests passed.")


# =============================================================================
# 60. BIT PATTERN ROUND TRIP
# =============================================================================

def demonstrate_bit_pattern_round_trip() -> None:
    """Verify that packing and unpacking preserves binary64 bits."""
    section("60. Bit Pattern Round-Trip Test")

    patterns = [
        0x0000000000000000,
        0x8000000000000000,
        0x3FF0000000000000,
        0xBFF0000000000000,
        0x7FF0000000000000,
        0xFFF0000000000000,
        0x0000000000000001,
        0x7FF8000000000042,
    ]

    for bits in patterns:
        value = uint64_to_float(bits)
        recovered = float_to_uint64(value)

        print(
            f"original={bits:016X}, "
            f"recovered={recovered:016X}, "
            f"same={bits == recovered}"
        )


# =============================================================================
# 61. MACHINE-LEVEL STORAGE SIZE
# =============================================================================

def demonstrate_storage_size() -> None:
    """Show typical Python float object size versus IEEE binary64 payload size."""
    section("61. Storage Considerations")

    print(f"Raw binary64 payload size: {struct.calcsize('d')} bytes")
    print(f"Python float object size : {sys.getsizeof(1.0)} bytes")

    print(
        "\nA Python float object has object-management overhead beyond the "
        "8-byte IEEE 754 binary64 payload. Compact numerical arrays can use "
        "more memory-efficient native representations."
    )


# =============================================================================
# 62. PERFORMANCE TRADE-OFFS
# =============================================================================

def demonstrate_performance_tradeoffs() -> None:
    """
    Discuss numeric-type trade-offs through a compact comparison.

    Timing is intentionally not performed because machine, interpreter,
    compiler, CPU, and workload differences would make a fixed benchmark
    misleading.
    """
    section("62. Performance Trade-Offs")

    comparison = [
        ("float", "fast general-purpose binary arithmetic", "approximate"),
        ("Decimal", "decimal arithmetic with configurable precision", "decimal-exact within context"),
        ("Fraction", "exact rational arithmetic", "exact"),
        ("int minor units", "fixed-scale integer arithmetic", "exact within chosen scale"),
    ]

    for type_name, strength, exactness in comparison:
        print(f"{type_name:18} | {strength:48} | {exactness}")


# =============================================================================
# 63. SERIALIZATION CONSIDERATIONS
# =============================================================================

def demonstrate_serialization() -> None:
    """
    Demonstrate that decimal textual serialization may not preserve the
    exact binary value unless enough digits are retained.

    repr() is used here because it is designed for a useful round trip.
    """
    section("63. Serialization and Round Trips")

    value = math.pi

    short_text = f"{value:.6f}"
    round_trip_text = repr(value)

    short_recovered = float(short_text)
    round_trip_recovered = float(round_trip_text)

    print(f"Original          : {value!r}")
    print(f"6-decimal text    : {short_text}")
    print(f"Recovered         : {short_recovered!r}")
    print(f"Same exact bits?  : {float_to_uint64(value) == float_to_uint64(short_recovered)}")

    print(f"\nrepr text         : {round_trip_text}")
    print(f"Recovered         : {round_trip_recovered!r}")
    print(
        "Same exact bits?  :",
        float_to_uint64(value) == float_to_uint64(round_trip_recovered),
    )


# =============================================================================
# 64. SORTING SPECIAL VALUES
# =============================================================================

def demonstrate_sorting_special_values() -> None:
    """
    Show why NaN requires special consideration in ordering.

    NaN is unordered with respect to ordinary numbers, so sorting behavior
    should not be assumed to correspond to a mathematical total order.
    """
    section("64. Ordering and NaN")

    values = [3.0, math.nan, 1.0, 2.0]

    print(f"Original: {values}")
    print(f"sorted  : {sorted(values)}")

    print(
        "\nApplications requiring a total order should explicitly define how "
        "NaN values are handled rather than relying on ordinary comparisons."
    )


# =============================================================================
# 65. DOMAIN-SPECIFIC VALIDATION
# =============================================================================

def calculate_percentage(part: float, whole: float) -> float:
    """
    Calculate a percentage with explicit domain validation.

    The example illustrates that numerical correctness includes handling
    invalid domain conditions, not just floating-point precision.
    """
    validate_finite_float(part, "part")
    validate_finite_float(whole, "whole")

    if whole == 0.0:
        raise ValueError("whole must not be zero.")

    return 100.0 * part / whole


def demonstrate_domain_validation() -> None:
    """Exercise the percentage function with ordinary and invalid inputs."""
    section("65. Domain Validation")

    examples = [
        (25.0, 200.0),
        (1.0, 3.0),
        (1.0, 0.0),
        (math.inf, 10.0),
    ]

    for part, whole in examples:
        try:
            result = calculate_percentage(part, whole)
            print(f"{part} / {whole} -> {result:.17g}%")
        except (TypeError, ValueError) as error:
            print(f"{part} / {whole} -> error: {error}")


# =============================================================================
# 66. ROBUST RANGE CHECKS
# =============================================================================

def safely_scale(value: float, scale: float) -> float:
    """
    Scale a finite float and reject a non-finite result.

    This is useful when a computation can overflow and the application cannot
    safely continue with infinity.
    """
    validate_finite_float(value, "value")
    validate_finite_float(scale, "scale")

    result = value * scale

    if not math.isfinite(result):
        raise OverflowError("Scaling produced a non-finite result.")

    return result


def demonstrate_safe_scaling() -> None:
    """Demonstrate explicit overflow handling."""
    section("66. Safe Scaling")

    examples = [
        (100.0, 2.0),
        (1e308, 2.0),
        (-1e200, 1e100),
    ]

    for value, scale in examples:
        try:
            result = safely_scale(value, scale)
            print(f"{value:.3e} * {scale:.3e} = {result:.3e}")
        except (TypeError, ValueError, OverflowError) as error:
            print(f"{value:.3e} * {scale:.3e} -> {error}")


# =============================================================================
# 67. HYPOT AS A STABILITY EXAMPLE
# =============================================================================

def demonstrate_hypot() -> None:
    """
    Compare sqrt(x*x+y*y) with math.hypot().

    math.hypot() is designed to provide robust Euclidean norm computation
    across a wider range of magnitudes.
    """
    section("67. Stable Euclidean Norm")

    x = 1e308
    y = 1e308

    try:
        naive = math.sqrt(x * x + y * y)
    except OverflowError:
        naive = math.inf

    stable = math.hypot(x, y)

    print(f"Naive sqrt(x*x+y*y): {naive}")
    print(f"math.hypot(x,y)    : {stable:.17e}")

    print(
        "\nThe stable function avoids unnecessary intermediate overflow."
    )


# =============================================================================
# 68. EXPONENTIAL STABILITY
# =============================================================================

def demonstrate_exponential_stability() -> None:
    """Demonstrate why expm1 is preferable for small x."""
    section("68. expm1 and Small Differences")

    x = 1e-16

    naive = math.exp(x) - 1.0
    stable = math.expm1(x)

    print(f"x: {x:.17e}")
    print(f"exp(x) - 1: {naive:.17e}")
    print(f"expm1(x)  : {stable:.17e}")

    print(
        "\nFor small x, exp(x) is extremely close to 1, so subtracting 1 "
        "can lose significant digits. expm1 computes the quantity directly."
    )


# =============================================================================
# 69. LOG-SUM-EXP STABILITY
# =============================================================================

def log_sum_exp(values: Iterable[float]) -> float:
    """
    Compute log(sum(exp(values))) using a stable transformation.

    The maximum value is subtracted before exponentiation:

        log(sum(exp(x_i)))
        = m + log(sum(exp(x_i-m)))

    where m=max(x_i).
    """
    values = list(values)

    if not values:
        raise ValueError("values must not be empty.")

    if any(math.isnan(value) for value in values):
        return math.nan

    maximum = max(values)

    if maximum == math.inf:
        return math.inf

    return maximum + math.log(
        math.fsum(math.exp(value - maximum) for value in values)
    )


def demonstrate_log_sum_exp() -> None:
    """Compare naive and stable log-sum-exp."""
    section("69. Log-Sum-Exp Stability")

    values = [1000.0, 1001.0, 1002.0]

    try:
        naive = math.log(sum(math.exp(value) for value in values))
    except OverflowError:
        naive = math.inf

    stable = log_sum_exp(values)

    print(f"Naive log(sum(exp(x))): {naive}")
    print(f"Stable implementation  : {stable:.17g}")


# =============================================================================
# 70. SOFTMAX STABILITY
# =============================================================================

def stable_softmax(values: Iterable[float]) -> list[float]:
    """
    Compute softmax probabilities using a numerically stable transformation.
    """
    values = list(values)

    if not values:
        raise ValueError("values must not be empty.")

    if any(not math.isfinite(value) for value in values):
        raise ValueError("softmax inputs must be finite.")

    maximum = max(values)
    exponentials = [math.exp(value - maximum) for value in values]
    denominator = math.fsum(exponentials)

    return [value / denominator for value in exponentials]


def demonstrate_stable_softmax() -> None:
    """Demonstrate stable softmax with large logits."""
    section("70. Stable Softmax")

    values = [1000.0, 1001.0, 1002.0]

    probabilities = stable_softmax(values)

    print(f"Inputs: {values}")
    print(f"Softmax: {[f'{value:.12f}' for value in probabilities]}")
    print(f"Probability sum: {math.fsum(probabilities):.17g}")


# =============================================================================
# 71. POLYNOMIAL EVALUATION
# =============================================================================

def polynomial_naive(x: float, coefficients: list[float]) -> float:
    """
    Evaluate a polynomial using explicit powers.

    coefficients are ordered from highest degree to constant term.
    """
    degree = len(coefficients) - 1
    result = 0.0

    for index, coefficient in enumerate(coefficients):
        result += coefficient * x ** (degree - index)

    return result


def polynomial_horner(x: float, coefficients: list[float]) -> float:
    """
    Evaluate a polynomial using Horner's method.

    For coefficients [a0, a1, ..., an]:

        (...((a0*x+a1)*x+a2)*x+...)+an
    """
    result = 0.0

    for coefficient in coefficients:
        result = result * x + coefficient

    return result


def demonstrate_horners_method() -> None:
    """Compare polynomial evaluation approaches."""
    section("71. Horner's Method")

    coefficients = [1.0, -3.0, 2.0]
    x = 1.0000001

    naive = polynomial_naive(x, coefficients)
    horner = polynomial_horner(x, coefficients)

    print(f"Polynomial: x² - 3x + 2")
    print(f"x = {x:.17g}")
    print(f"Naive  : {naive:.17g}")
    print(f"Horner : {horner:.17g}")

    print(
        "\nHorner's method generally uses fewer operations and can provide "
        "better numerical behavior, though exact error properties depend on "
        "the polynomial and evaluation point."
    )


# =============================================================================
# 72. FLOATING-POINT ERROR IS NOT RANDOM NOISE
# =============================================================================

def demonstrate_deterministic_rounding() -> None:
    """
    Show that rounding is deterministic for the same inputs and environment.

    Floating-point error is often systematic and structured, not arbitrary
    random noise.
    """
    section("72. Deterministic Floating-Point Error")

    value = 0.1

    first = value * 3.0
    second = value * 3.0

    print(f"First calculation : {first:.17g}")
    print(f"Second calculation: {second:.17g}")
    print(f"Exactly equal     : {first == second}")

    print(
        "\nDeterminism does not imply mathematical exactness. A repeatable "
        "rounded result can still differ from the exact real-number result."
    )


# =============================================================================
# 73. MACHINE EPSILON VERSUS SMALLEST POSITIVE FLOAT
# =============================================================================

def demonstrate_epsilon_vs_minimum() -> None:
    """Clarify a common misconception about epsilon."""
    section("73. Machine Epsilon Is Not the Smallest Positive Float")

    print(f"Machine epsilon: {sys.float_info.epsilon:.17e}")
    print(f"Minimum normal: {sys.float_info.min:.17e}")
    print(f"Minimum subnormal: {math.nextafter(0.0, math.inf):.17e}")

    print(
        "\nMachine epsilon describes local spacing around 1.0. It is not a "
        "measure of the smallest positive floating-point number."
    )


# =============================================================================
# 74. RELATIVE SPACING
# =============================================================================

def demonstrate_relative_spacing() -> None:
    """Inspect ULP relative to magnitude."""
    section("74. Relative Spacing")

    for value in [1.0, 2.0, 4.0, 8.0, 1024.0]:
        spacing = ulp_distance(value)
        print(
            f"value={value:8g}, "
            f"ULP={spacing:.17e}, "
            f"ULP/value={spacing / value:.17e}"
        )


# =============================================================================
# 75. ROUNDING BOUND
# =============================================================================

def demonstrate_rounding_bound() -> None:
    """
    Explain the common relative-rounding model.

    For round-to-nearest arithmetic, the relative error of an individual
    correctly rounded normal result is bounded approximately by half a unit
    in the last place, often expressed as u = 2^-53 for binary64 under a
    simplified model.

    This is a conceptual numerical-analysis model rather than a universal
    statement covering every special case.
    """
    section("75. Unit Roundoff")

    unit_roundoff = 2.0**-53

    print(f"Binary64 unit roundoff u = 2^-53 = {unit_roundoff:.17e}")
    print(f"Machine epsilon         = 2^-52 = {2.0**-52:.17e}")

    print(
        "\nMachine epsilon and unit roundoff are related but are not identical "
        "terms. Machine epsilon is commonly the distance from 1 to the next "
        "larger representable number; unit roundoff is half that spacing for "
        "round-to-nearest in the standard model."
    )


# =============================================================================
# 76. FLOATING-POINT OPERATION MODEL
# =============================================================================

def demonstrate_standard_error_model() -> None:
    """
    Demonstrate the conceptual model:

        fl(x op y) = (x op y)(1 + delta)

    where |delta| is bounded by a small unit-roundoff quantity under suitable
    assumptions.
    """
    section("76. Floating-Point Operation Model")

    x = 1.1
    y = 2.2

    exact = Fraction.from_float(x) + Fraction.from_float(y)
    computed = x + y
    error = Fraction.from_float(computed) - exact

    print(f"x       = {x:.17g}")
    print(f"y       = {y:.17g}")
    print(f"computed= {computed:.17g}")
    print(f"exact sum of stored operands = {exact}")
    print(f"rounding difference          = {error}")

    print(
        "\nNumerical analysis often models each rounded operation as a small "
        "relative perturbation when no overflow, underflow complications, "
        "or severe conditioning issues dominate."
    )


# =============================================================================
# 77. INPUT REPRESENTATION VERSUS OPERATION ERROR
# =============================================================================

def demonstrate_two_sources_of_error() -> None:
    """Distinguish input representation error from operation rounding error."""
    section("77. Representation Error versus Operation Error")

    decimal_intended = Fraction(1, 10)
    binary_float = 0.1

    representation_error = Fraction.from_float(binary_float) - decimal_intended

    operation_result = binary_float + binary_float
    exact_sum_of_stored_inputs = Fraction.from_float(binary_float) * 2

    operation_error = (
        Fraction.from_float(operation_result) - exact_sum_of_stored_inputs
    )

    print(f"Input representation error: {representation_error}")
    print(f"Operation rounding error   : {operation_error}")

    print(
        "\nA numerical result can therefore differ from the mathematical "
        "problem for multiple reasons."
    )


# =============================================================================
# 78. APPROXIMATE ZERO
# =============================================================================

def approximately_zero(
    value: float,
    absolute_tolerance: float = 1e-12,
) -> bool:
    """Return True if value is sufficiently close to zero."""
    if not math.isfinite(value):
        return False

    if absolute_tolerance < 0:
        raise ValueError("absolute_tolerance must be non-negative.")

    return abs(value) <= absolute_tolerance


def demonstrate_approximate_zero() -> None:
    """Demonstrate absolute tolerance around zero."""
    section("78. Testing Approximate Zero")

    values = [0.0, 1e-15, 1e-10, -1e-13, math.nan]

    for value in values:
        print(f"{value!r:>8}: approximately_zero={approximately_zero(value)}")


# =============================================================================
# 79. AVOIDING FALSE DECIMAL ASSUMPTIONS
# =============================================================================

def demonstrate_decimal_assumptions() -> None:
    """
    Show that formatting a binary float as two decimal places does not make
    its internal representation a two-decimal-place quantity.
    """
    section("79. Displayed Decimal Precision Is Not Internal Decimal Precision")

    price = 2.675

    print(f"Raw repr: {price!r}")
    print(f"Formatted to 2 decimals: {price:.2f}")
    print(f"round(price, 2): {round(price, 2)}")

    print(
        "\nThe familiar 2.675 rounding example arises because the binary64 "
        "value nearest to decimal 2.675 is slightly below the exact decimal "
        "value. Decimal arithmetic can express 2.675 exactly."
    )

    decimal_price = Decimal("2.675")
    print(
        "Decimal quantization:",
        decimal_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN),
    )


# =============================================================================
# 80. EDGE CASE: DIVISION RESULTS
# =============================================================================

def demonstrate_division_behavior() -> None:
    """
    Contrast Python's exception behavior for zero division with IEEE special
    values created explicitly.
    """
    section("80. Division Edge Cases")

    expressions = [
        ("1.0 / 0.0", lambda: 1.0 / 0.0),
        ("0.0 / 0.0", lambda: 0.0 / 0.0),
        ("math.inf / math.inf", lambda: math.inf / math.inf),
    ]

    for name, operation in expressions:
        try:
            print(f"{name} -> {operation()}")
        except ZeroDivisionError as error:
            print(f"{name} -> {type(error).__name__}: {error}")


# =============================================================================
# 81. UNDERFLOW DETECTION
# =============================================================================

def demonstrate_underflow_detection() -> None:
    """Detect when a computation produces zero from a tiny positive result."""
    section("81. Detecting Potential Underflow")

    value = 1e-300

    for _ in range(10):
        value *= 1e-10

    print(f"Repeatedly scaled value: {value:.17e}")
    print(f"Is zero? {value == 0.0}")
    print(f"Is finite? {math.isfinite(value)}")

    print(
        "\nWhen tiny values are meaningful, applications should define "
        "whether underflow to zero is acceptable."
    )


# =============================================================================
# 82. TYPE CHOICE
# =============================================================================

def recommend_numeric_type_for_domain(domain: str) -> str:
    """
    Return a simple domain-oriented recommendation.

    This is deliberately rule-based and educational rather than a universal
    design decision.
    """
    normalized = domain.strip().lower()

    if normalized in {"scientific", "simulation", "graphics", "geometry"}:
        return "float"
    if normalized in {"money", "accounting", "financial"}:
        return "Decimal or integer minor units"
    if normalized in {"exact rational", "rational", "symbolic fraction"}:
        return "Fraction"
    if normalized in {"count", "index", "identifier"}:
        return "int"

    return "Choose based on required range, precision, semantics, and performance."


def demonstrate_type_selection() -> None:
    """Demonstrate domain-specific numeric type selection."""
    section("82. Choosing a Numeric Representation")

    domains = [
        "scientific",
        "money",
        "exact rational",
        "count",
        "unknown",
    ]

    for domain in domains:
        print(f"{domain:20} -> {recommend_numeric_type_for_domain(domain)}")


# =============================================================================
# 83. PRODUCTION BEST PRACTICES
# =============================================================================

def demonstrate_best_practices() -> None:
    """Print concrete floating-point engineering practices."""
    section("83. Floating-Point Best Practices")

    practices = [
        "Do not assume decimal fractions such as 0.1 are exactly representable.",
        "Avoid exact equality for approximate numerical results unless justified.",
        "Choose absolute and relative tolerances based on domain requirements.",
        "Use stable algebraic reformulations when cancellation is possible.",
        "Use math.fsum or compensated/pairwise methods for sensitive summations.",
        "Check for NaN and infinity at system boundaries when appropriate.",
        "Use Decimal or integer minor units when exact decimal accounting is required.",
        "Use Fraction when exact rational arithmetic is required.",
        "Use float when binary approximation and broad dynamic range are appropriate.",
        "Test extreme magnitudes, zeros, signed zeros, NaNs, infinities, and subnormals.",
        "Do not confuse formatted output with the stored numerical representation.",
        "Document numeric precision and tolerance requirements in production systems.",
    ]

    for number, practice in enumerate(practices, start=1):
        print(f"{number:2}. {practice}")


# =============================================================================
# 84. COMMON MISTAKES
# =============================================================================

def demonstrate_common_mistakes() -> None:
    """List common floating-point mistakes and their corrections."""
    section("84. Common Mistakes")

    mistakes = [
        (
            "Mistake",
            "Assuming float(0.1) stores exact decimal 0.1.",
            "Inspect the exact rational value or use Decimal when decimal exactness is required.",
        ),
        (
            "Mistake",
            "Using == for approximate numerical computations.",
            "Use a justified absolute/relative tolerance.",
        ),
        (
            "Mistake",
            "Assuming epsilon is the smallest positive float.",
            "Use math.nextafter(0.0, math.inf) for the smallest positive binary64 value.",
        ),
        (
            "Mistake",
            "Ignoring overflow and infinity.",
            "Validate ranges and explicitly define non-finite-value policy.",
        ),
        (
            "Mistake",
            "Using naive log(exp(x) + exp(y)) for very large x and y.",
            "Use a log-sum-exp transformation.",
        ),
        (
            "Mistake",
            "Subtracting nearly equal large values without considering cancellation.",
            "Find an algebraically stable reformulation when possible.",
        ),
    ]

    for _, mistake, correction in mistakes:
        print(f"\n{mistake}")
        print(f"  Correction: {correction}")


# =============================================================================
# 85. SECURITY AND ROBUSTNESS
# =============================================================================

def demonstrate_security_considerations() -> None:
    """
    Discuss security-relevant numerical robustness.

    Floating-point itself is not generally a security boundary, but unexpected
    NaN, infinity, overflow, or precision loss can affect validation, limits,
    billing, ranking, geometry, and resource calculations.
    """
    section("85. Security and Robustness Considerations")

    checks = [
        "Reject or explicitly handle NaN where it can bypass ordinary comparisons.",
        "Reject unexpected infinities at trust boundaries.",
        "Do not use floating-point values as authoritative monetary quantities when exact accounting is required.",
        "Apply range checks before converting floating-point values to integer sizes or resource limits.",
        "Define behavior for negative zero if sign-sensitive logic is used.",
        "Test extreme values to prevent overflow-driven logic errors.",
        "Avoid relying on unspecified NaN ordering in validation logic.",
    ]

    for check in checks:
        print(f"- {check}")


# =============================================================================
# 86. DEBUGGING WORKFLOW
# =============================================================================

def floating_point_debug_report(value: float) -> dict[str, object]:
    """Create a compact diagnostic report for a floating-point value."""
    bits = float_to_uint64(value)

    return {
        "repr": repr(value),
        "hex": value.hex(),
        "bits": bits_to_string(bits),
        "finite": math.isfinite(value),
        "infinite": math.isinf(value),
        "nan": math.isnan(value),
        "subnormal": is_subnormal(value),
        "ulp_toward_positive": ulp_distance(value),
    }


def demonstrate_debugging_report() -> None:
    """Print diagnostics for ordinary and special values."""
    section("86. Floating-Point Debugging")

    values = [0.1, 1.0, -0.0, math.inf, math.nan]

    for value in values:
        report = floating_point_debug_report(value)
        print(f"\nValue: {value!r}")
        for key, diagnostic in report.items():
            print(f"  {key:24}: {diagnostic}")


# =============================================================================
# 87. NUMERICAL REGRESSION TESTING
# =============================================================================

def test_known_floating_point_properties() -> None:
    """Run a collection of small numerical correctness tests."""
    assert 0.5 == 1.0 / 2.0

    assert math.isclose(
        0.1 + 0.2,
        0.3,
        rel_tol=1e-15,
        abs_tol=1e-15,
    )

    assert math.isinf(math.inf)
    assert math.isnan(math.nan)

    assert is_subnormal(math.nextafter(0.0, math.inf))

    assert float.fromhex((math.pi).hex()) == math.pi

    assert Decimal("0.1") + Decimal("0.2") == Decimal("0.3")

    assert Fraction(1, 10) + Fraction(2, 10) == Fraction(3, 10)


def demonstrate_regression_tests() -> None:
    """Run numerical regression tests."""
    section("87. Numerical Regression Tests")

    test_known_floating_point_properties()
    print("All numerical regression tests passed.")


# =============================================================================
# 88. IEEE 754 CATEGORY CLASSIFIER
# =============================================================================

def classify_float(value: float) -> str:
    """Classify a Python float according to IEEE 754-style categories."""
    if math.isnan(value):
        return "NaN"

    if math.isinf(value):
        return "+infinity" if value > 0 else "-infinity"

    if value == 0.0:
        return "+zero" if math.copysign(1.0, value) > 0 else "-zero"

    if is_subnormal(value):
        return "positive subnormal" if value > 0 else "negative subnormal"

    return "positive normal" if value > 0 else "negative normal"


def demonstrate_classifier() -> None:
    """Classify representative values."""
    section("88. IEEE 754-Style Classification")

    values = [
        0.0,
        -0.0,
        math.nextafter(0.0, math.inf),
        -math.nextafter(0.0, math.inf),
        1.0,
        -1.0,
        math.inf,
        -math.inf,
        math.nan,
    ]

    for value in values:
        print(f"{value!r:>25} -> {classify_float(value)}")


# =============================================================================
# 89. REPRESENTATION OF POWERS OF TWO
# =============================================================================

def demonstrate_powers_of_two() -> None:
    """Show why powers of two are particularly convenient in binary floating point."""
    section("89. Powers of Two")

    powers = [-10, -3, -1, 0, 1, 3, 10, 100]

    for exponent in powers:
        value = 2.0**exponent
        print(
            f"2^{exponent:4d} = {value:.17e}, "
            f"hex={value.hex()}"
        )

    print(
        "\nPowers of two align naturally with binary scientific notation, "
        "which makes them exactly representable when they remain within "
        "the finite range of the format."
    )


# =============================================================================
# 90. DECIMAL VERSUS BINARY PRECISION
# =============================================================================

def demonstrate_decimal_vs_binary() -> None:
    """Compare decimal and binary notions of exactness."""
    section("90. Decimal versus Binary Exactness")

    decimal_values = ["0.1", "0.125", "0.2", "0.25", "0.5"]

    for text in decimal_values:
        fraction = Fraction(Decimal(text))
        binary_exact = is_exact_binary_fraction(fraction)

        print(
            f"{text:>6}: "
            f"exact decimal={True}, "
            f"finite binary={binary_exact}"
        )


# =============================================================================
# 91. INTERVAL-LIKE ERROR BOUND DEMONSTRATION
# =============================================================================

def demonstrate_neighbor_interval() -> None:
    """
    Show that a floating-point value represents a point, while nearby real
    numbers round to it depending on the rounding rule.

    The exact rounding interval at boundaries has subtleties around powers of
    two and subnormals, so this example simply displays neighboring floats.
    """
    section("91. Neighboring Representable Values")

    value = 1.2345

    previous_value = math.nextafter(value, -math.inf)
    next_value = math.nextafter(value, math.inf)

    print(f"previous = {previous_value:.17g}")
    print(f"value    = {value:.17g}")
    print(f"next     = {next_value:.17g}")

    print(f"distance below = {value - previous_value:.17e}")
    print(f"distance above = {next_value - value:.17e}")


# =============================================================================
# 92. PERFORMANCE-SENSITIVE PRECISION CHOICE
# =============================================================================

def demonstrate_precision_tradeoff() -> None:
    """Show a conceptual precision/storage comparison."""
    section("92. Precision, Range, Storage, and Performance")

    rows = [
        ("binary16", 16, 11, "low precision, compact"),
        ("binary32", 32, 24, "moderate precision, compact"),
        ("binary64", 64, 53, "high general-purpose precision"),
    ]

    for format_name, bits, precision, description in rows:
        print(
            f"{format_name:10} | "
            f"bits={bits:2d} | "
            f"significand bits={precision:2d} | "
            f"{description}"
        )

    print(
        "\nLower precision can reduce storage and improve throughput on "
        "hardware designed for it, but it reduces representational accuracy "
        "and range."
    )


# =============================================================================
# 93. WHY FLOATING POINT IS NOT JUST "DECIMAL WITH A DOT"
# =============================================================================

def demonstrate_conceptual_difference() -> None:
    """Clarify the fundamental difference between decimal and binary floats."""
    section("93. Floating Point Is Not Decimal Arithmetic")

    print("Decimal number:")
    print("  12.34 = 1234 × 10^-2")

    print("\nBinary floating-point number:")
    print("  12.34 is approximated using powers of 2")

    print("\nExact decimal representation:")
    print(Decimal("12.34"))

    print("\nBinary64 representation:")
    print(float(Decimal("12.34")).hex())

    print(
        "\nThe decimal appearance of a number does not imply that the stored "
        "representation uses decimal digits."
    )


# =============================================================================
# 94. ALGORITHM DESIGN CHECKLIST
# =============================================================================

def numerical_algorithm_checklist() -> list[str]:
    """Return a production-oriented checklist for floating-point algorithms."""
    return [
        "Identify the expected input range.",
        "Identify the required absolute accuracy.",
        "Identify the required relative accuracy.",
        "Determine whether NaN and infinity are valid domain values.",
        "Check for overflow-prone intermediate expressions.",
        "Check for underflow-prone intermediate expressions.",
        "Look for cancellation.",
        "Check whether operation order affects accuracy.",
        "Use stable library functions where available.",
        "Choose an appropriate summation strategy.",
        "Choose a suitable numeric representation.",
        "Test boundary and adversarial values.",
        "Document tolerance choices.",
    ]


def demonstrate_algorithm_checklist() -> None:
    """Print the numerical algorithm design checklist."""
    section("94. Numerical Algorithm Design Checklist")

    for number, item in enumerate(numerical_algorithm_checklist(), start=1):
        print(f"{number:2}. {item}")


# =============================================================================
# 95. FINAL INTEGRATED DEMONSTRATION
# =============================================================================

def integrated_example() -> None:
    """
    Integrate representation inspection, error analysis, stable comparison,
    and validation into one small workflow.
    """
    section("95. Integrated Floating-Point Analysis")

    measured_value = 0.1 + 0.2
    expected_value = 0.3

    print("Step 1: Computation")
    print(f"  measured = {measured_value:.17g}")

    print("\nStep 2: Representation")
    print(f"  hex = {measured_value.hex()}")

    print("\nStep 3: Exact stored rational value")
    print(f"  stored = {Fraction.from_float(measured_value)}")

    print("\nStep 4: Error")
    print(f"  absolute error = {abs(measured_value - expected_value):.20e}")

    print("\nStep 5: Tolerance-based validation")
    accepted = math.isclose(
        measured_value,
        expected_value,
        rel_tol=1e-15,
        abs_tol=1e-15,
    )
    print(f"  accepted = {accepted}")

    print("\nStep 6: Domain validation")
    try:
        validate_finite_float(measured_value)
        print("  value is finite and suitable for this validation policy")
    except ValueError as error:
        print(f"  rejected: {error}")


# =============================================================================
# 96. EDUCATIONAL QUICK REFERENCE
# =============================================================================

def print_quick_reference() -> None:
    """Print a compact conceptual reference."""
    section("96. Floating-Point Quick Reference")

    reference = [
        ("Binary64 total size", "64 bits"),
        ("Binary64 sign", "1 bit"),
        ("Binary64 exponent", "11 bits, bias 1023"),
        ("Binary64 fraction", "52 stored bits"),
        ("Binary64 precision", "53 significant binary bits for normals"),
        ("Machine epsilon", "2^-52"),
        ("Unit roundoff", "2^-53 under the standard round-to-nearest model"),
        ("Smallest positive normal", "2^-1022"),
        ("Smallest positive subnormal", "2^-1074"),
        ("Maximum finite", "approximately 1.7976931348623157 × 10^308"),
        ("Special exponent", "all zeros or all ones have special meanings"),
        ("NaN comparison", "NaN is not equal to itself"),
        ("Signed zero", "+0 and -0 compare equal"),
        ("Typical Python float", "binary64"),
    ]

    width = max(len(key) for key, _ in reference)

    for key, value in reference:
        print(f"{key:<{width}} : {value}")


# =============================================================================
# 97. SELF-TEST
# =============================================================================

def run_self_tests() -> None:
    """Run core assertions without printing each demonstration."""
    assert compute_machine_epsilon() == sys.float_info.epsilon

    assert binary_fraction_to_fraction("0.101") == Fraction(5, 8)

    assert is_exact_binary_fraction(Fraction(1, 8))
    assert not is_exact_binary_fraction(Fraction(1, 10))

    assert math.nextafter(0.0, math.inf) > 0.0
    assert is_subnormal(math.nextafter(0.0, math.inf))

    assert classify_float(0.0) == "+zero"
    assert classify_float(-0.0) == "-zero"
    assert classify_float(math.inf) == "+infinity"
    assert classify_float(-math.inf) == "-infinity"
    assert classify_float(math.nan) == "NaN"

    assert Decimal("0.1") + Decimal("0.2") == Decimal("0.3")
    assert Fraction(1, 10) + Fraction(2, 10) == Fraction(3, 10)

    assert math.isclose(
        kahan_sum([0.1] * 100),
        10.0,
        rel_tol=1e-15,
        abs_tol=1e-15,
    )

    test_float_hex_round_trip()
    test_known_floating_point_properties()


# =============================================================================
# 98. MAIN DRIVER
# =============================================================================

def main() -> None:
    """
    Execute the complete floating-point tutorial.

    The demonstrations are intentionally sequential so the script can be read
    from top to bottom as a study document.
    """
    explain_basic_idea()
    demonstrate_fixed_point_vs_floating_point()
    demonstrate_binary_fractions()
    demonstrate_ieee754_layout()
    demonstrate_binary64_encoding()
    demonstrate_normalized_encoding()
    demonstrate_decimal_to_binary()
    demonstrate_exact_representation()
    demonstrate_precision()
    demonstrate_machine_epsilon()
    demonstrate_ulp()
    demonstrate_nextafter()
    demonstrate_rounding_error()
    demonstrate_why_point_one_plus_point_two_is_not_exact()
    demonstrate_accumulated_error()
    demonstrate_cancellation()
    demonstrate_absorption()
    demonstrate_overflow()
    demonstrate_underflow()
    demonstrate_special_values()
    demonstrate_signed_zero()
    demonstrate_nan()
    demonstrate_infinity()
    demonstrate_subnormal_detection()
    demonstrate_exact_stored_value()
    demonstrate_hex_float()
    demonstrate_float_comparison()
    demonstrate_tolerances()
    demonstrate_kahan_summation()
    demonstrate_pairwise_summation()
    demonstrate_stable_logarithms()
    demonstrate_math_fsum()
    demonstrate_order_dependence()
    demonstrate_fma_concept()
    demonstrate_float_range()
    demonstrate_exact_integer_range()
    demonstrate_round_to_even()
    demonstrate_decimal()
    demonstrate_decimal_context()
    demonstrate_fraction()
    demonstrate_financial_choice()
    demonstrate_integer_minor_units()
    demonstrate_binary32_precision()
    demonstrate_binary32_encoding()
    demonstrate_reconstruction()
    demonstrate_special_bit_patterns()
    demonstrate_nan_payload_behavior()
    demonstrate_decimal_round_trip()
    demonstrate_display_vs_storage()
    demonstrate_float_hashing()
    demonstrate_extreme_exponents()
    demonstrate_negative_zero_formatting()
    demonstrate_large_integer_conversion()
    demonstrate_conditioning()
    demonstrate_error_metrics()
    demonstrate_error_propagation()
    demonstrate_validation()
    demonstrate_numerical_invariant_testing()
    demonstrate_round_trip_test()
    demonstrate_bit_pattern_round_trip()
    demonstrate_storage_size()
    demonstrate_performance_tradeoffs()
    demonstrate_serialization()
    demonstrate_sorting_special_values()
    demonstrate_domain_validation()
    demonstrate_safe_scaling()
    demonstrate_hypot()
    demonstrate_exponential_stability()
    demonstrate_log_sum_exp()
    demonstrate_stable_softmax()
    demonstrate_horners_method()
    demonstrate_deterministic_rounding()
    demonstrate_epsilon_vs_minimum()
    demonstrate_relative_spacing()
    demonstrate_rounding_bound()
    demonstrate_standard_error_model()
    demonstrate_two_sources_of_error()
    demonstrate_approximate_zero()
    demonstrate_decimal_assumptions()
    demonstrate_division_behavior()
    demonstrate_underflow_detection()
    demonstrate_type_selection()
    demonstrate_best_practices()
    demonstrate_common_mistakes()
    demonstrate_security_considerations()
    demonstrate_debugging_report()
    demonstrate_regression_tests()
    demonstrate_classifier()
    demonstrate_powers_of_two()
    demonstrate_decimal_vs_binary()
    demonstrate_neighbor_interval()
    demonstrate_precision_tradeoff()
    demonstrate_conceptual_difference()
    demonstrate_algorithm_checklist()
    integrated_example()
    print_quick_reference()

    section("99. Self-Test")
    run_self_tests()
    print("All self-tests passed.")


if __name__ == "__main__":
    main()
