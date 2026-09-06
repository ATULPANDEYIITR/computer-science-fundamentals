"""
NUMBER SYSTEM CONVERSION
========================

Topic:
    Decimal to Binary, Binary to Decimal, Octal Conversion,
    Hexadecimal Conversion, Shortcuts, Algorithms, Validation,
    Arithmetic, Edge Cases, Testing, and Advanced Techniques.

This is a standalone study script. It uses only Python's standard library.

Suggested execution:
    python number_system_conversion.py

The demonstrations progress from absolute fundamentals to advanced
conversion techniques and practical implementation details.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Optional
import random
import sys


# ============================================================================
# 1. NUMBER SYSTEM FUNDAMENTALS
# ============================================================================

"""
A positional number system represents a number using:

    digit × base^position

Common bases:

    Base 2  -> Binary      -> digits 0, 1
    Base 8  -> Octal       -> digits 0 through 7
    Base 10 -> Decimal     -> digits 0 through 9
    Base 16 -> Hexadecimal -> digits 0 through 9 and A through F

For example:

    582 (decimal)

means:

    5 × 10^2 + 8 × 10^1 + 2 × 10^0
  = 500 + 80 + 2
  = 582

Binary:

    101101 (binary)

means:

    1×2^5 + 0×2^4 + 1×2^3 + 1×2^2 + 0×2^1 + 1×2^0
  = 32 + 0 + 8 + 4 + 0 + 1
  = 45

Octal:

    157 (octal)

means:

    1×8^2 + 5×8^1 + 7×8^0
  = 64 + 40 + 7
  = 111

Hexadecimal:

    2AF (hexadecimal)

means:

    2×16^2 + 10×16^1 + 15×16^0
  = 512 + 160 + 15
  = 687
"""


DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def validate_base(base: int) -> None:
    """Ensure that a base is supported by our generic conversion functions."""
    if not isinstance(base, int):
        raise TypeError("Base must be an integer.")
    if not 2 <= base <= len(DIGITS):
        raise ValueError(f"Base must be between 2 and {len(DIGITS)}.")


def digit_value(character: str) -> int:
    """
    Convert one alphanumeric digit into its numeric value.

    Examples:
        '7' -> 7
        'A' -> 10
        'f' -> 15
    """
    if len(character) != 1:
        raise ValueError("A digit must contain exactly one character.")

    character = character.upper()

    if character not in DIGITS:
        raise ValueError(f"Invalid digit: {character}")

    return DIGITS.index(character)


def digit_character(value: int) -> str:
    """Convert a numeric digit value back into its character representation."""
    if not 0 <= value < len(DIGITS):
        raise ValueError("Digit value is outside the supported range.")
    return DIGITS[value]


# ============================================================================
# 2. DECIMAL TO BINARY: REPEATED DIVISION BY 2
# ============================================================================

def decimal_to_binary_division(number: int) -> str:
    """
    Convert a non-negative decimal integer to binary using repeated division.

    Algorithm:
        1. Divide the number by 2.
        2. Record the remainder.
        3. Replace the number with the quotient.
        4. Repeat until the quotient becomes zero.
        5. Read remainders from bottom to top.

    Example:

        13 / 2 = 6 remainder 1
         6 / 2 = 3 remainder 0
         3 / 2 = 1 remainder 1
         1 / 2 = 0 remainder 1

        Read upward:
            1101
    """
    if not isinstance(number, int):
        raise TypeError("This function accepts integers only.")

    if number < 0:
        raise ValueError("This function handles non-negative integers.")

    if number == 0:
        return "0"

    remainders = []

    while number > 0:
        remainder = number % 2
        number //= 2
        remainders.append(str(remainder))

    return "".join(reversed(remainders))


print("=" * 78)
print("NUMBER SYSTEM CONVERSION")
print("=" * 78)

print("\nDECIMAL TO BINARY USING REPEATED DIVISION")
for value in [0, 1, 2, 5, 10, 13, 25, 42, 255]:
    print(f"{value:>3} -> {decimal_to_binary_division(value)}")


# ============================================================================
# 3. DECIMAL TO BINARY: POWER-OF-TWO METHOD
# ============================================================================

def decimal_to_binary_powers(number: int) -> str:
    """
    Convert decimal to binary using powers of two.

    The method finds the largest power of two that fits into the number,
    then determines whether each smaller power is present.

    Example:

        45 = 32 + 8 + 4 + 1

        Powers:
            32 16 8 4 2 1
             1  0 1 1 0 1

        Therefore:
            45 = 101101₂
    """
    if not isinstance(number, int):
        raise TypeError("Number must be an integer.")

    if number < 0:
        raise ValueError("Only non-negative integers are supported.")

    if number == 0:
        return "0"

    highest_power = 1

    while highest_power * 2 <= number:
        highest_power *= 2

    bits = []

    while highest_power > 0:
        if number >= highest_power:
            bits.append("1")
            number -= highest_power
        else:
            bits.append("0")

        highest_power //= 2

    return "".join(bits)


print("\nDECIMAL TO BINARY USING POWERS OF TWO")
for value in [13, 45, 100, 128, 255]:
    print(f"{value:>3} -> {decimal_to_binary_powers(value)}")


# ============================================================================
# 4. BINARY TO DECIMAL: POSITIONAL METHOD
# ============================================================================

def binary_to_decimal_positional(binary: str) -> int:
    """
    Convert binary to decimal using positional weights.

    Example:

        101101₂

        = 1×2^5 + 0×2^4 + 1×2^3 + 1×2^2 + 0×2^1 + 1×2^0
        = 32 + 8 + 4 + 1
        = 45
    """
    if not isinstance(binary, str):
        raise TypeError("Binary input must be a string.")

    binary = binary.strip()

    if not binary:
        raise ValueError("Binary input cannot be empty.")

    if binary.startswith(("+", "-")):
        raise ValueError("Signed binary strings are not accepted here.")

    if any(bit not in "01" for bit in binary):
        raise ValueError(f"Invalid binary number: {binary}")

    decimal_value = 0
    power = len(binary) - 1

    for bit in binary:
        decimal_value += int(bit) * (2 ** power)
        power -= 1

    return decimal_value


print("\nBINARY TO DECIMAL USING POSITIONAL EXPANSION")
for binary in ["0", "1", "10", "101", "1010", "1101", "101101", "11111111"]:
    print(f"{binary:>8}₂ -> {binary_to_decimal_positional(binary)}₁₀")


# ============================================================================
# 5. BINARY TO DECIMAL: HORNER'S METHOD
# ============================================================================

def binary_to_decimal_horner(binary: str) -> int:
    """
    Convert binary to decimal using Horner's rule.

    For binary 101101:

        (((((1 × 2 + 0) × 2 + 1) × 2 + 1) × 2 + 0) × 2 + 1)
        = 45

    This avoids explicitly calculating powers of two.
    """
    if not isinstance(binary, str):
        raise TypeError("Binary input must be a string.")

    binary = binary.strip()

    if not binary or any(bit not in "01" for bit in binary):
        raise ValueError("Binary input must contain only 0 and 1.")

    value = 0

    for bit in binary:
        value = value * 2 + int(bit)

    return value


print("\nBINARY TO DECIMAL USING HORNER'S METHOD")
for binary in ["101101", "11111111", "100000000"]:
    print(f"{binary:>12}₂ -> {binary_to_decimal_horner(binary)}₁₀")


# ============================================================================
# 6. GENERIC BASE-N TO DECIMAL
# ============================================================================

def base_to_decimal(number: str, base: int) -> int:
    """
    Convert a positive or zero integer represented in an arbitrary base
    into decimal.

    Supported bases are 2 through 36.

    Examples:
        base_to_decimal("101101", 2) -> 45
        base_to_decimal("157", 8)     -> 111
        base_to_decimal("2AF", 16)    -> 687

    Leading zeros are valid.
    """
    validate_base(base)

    if not isinstance(number, str):
        raise TypeError("Number must be supplied as a string.")

    number = number.strip().upper()

    if not number:
        raise ValueError("Number cannot be empty.")

    sign = 1

    if number[0] in "+-":
        if number[0] == "-":
            sign = -1
        number = number[1:]

    if not number:
        raise ValueError("A sign must be followed by digits.")

    decimal_value = 0

    for character in number:
        value = digit_value(character)

        if value >= base:
            raise ValueError(
                f"Digit '{character}' is invalid for base {base}."
            )

        decimal_value = decimal_value * base + value

    return sign * decimal_value


print("\nGENERIC BASE-N TO DECIMAL")
examples = [
    ("101101", 2),
    ("157", 8),
    ("255", 10),
    ("2AF", 16),
    ("Z", 36),
]

for value, base in examples:
    print(f"({value}) base {base} -> {base_to_decimal(value, base)}")


# ============================================================================
# 7. DECIMAL TO GENERIC BASE-N
# ============================================================================

def decimal_to_base(number: int, base: int) -> str:
    """
    Convert a decimal integer into any base from 2 through 36.

    Repeated division by the target base is used.

    Example:

        687 decimal to hexadecimal

        687 / 16 = 42 remainder 15 -> F
         42 / 16 =  2 remainder 10 -> A
          2 / 16 =  0 remainder  2 -> 2

        Read upward:
            2AF
    """
    validate_base(base)

    if not isinstance(number, int):
        raise TypeError("Number must be an integer.")

    if number == 0:
        return "0"

    sign = "-" if number < 0 else ""
    number = abs(number)

    digits = []

    while number:
        remainder = number % base
        digits.append(digit_character(remainder))
        number //= base

    return sign + "".join(reversed(digits))


print("\nDECIMAL TO GENERIC BASE-N")
for decimal_value, base in [
    (45, 2),
    (111, 8),
    (255, 16),
    (687, 16),
    (35, 36),
]:
    print(
        f"{decimal_value:>4}₁₀ -> "
        f"({decimal_to_base(decimal_value, base)}) base {base}"
    )


# ============================================================================
# 8. OCTAL NUMBER SYSTEM
# ============================================================================

"""
Octal uses base 8.

Valid digits:

    0 1 2 3 4 5 6 7

Each octal digit corresponds exactly to three binary bits because:

    8 = 2^3

Therefore:

    0 -> 000
    1 -> 001
    2 -> 010
    3 -> 011
    4 -> 100
    5 -> 101
    6 -> 110
    7 -> 111
"""

OCTAL_TO_BINARY = {
    "0": "000",
    "1": "001",
    "2": "010",
    "3": "011",
    "4": "100",
    "5": "101",
    "6": "110",
    "7": "111",
}


def octal_to_binary(octal: str) -> str:
    """Convert octal directly to binary by replacing every digit with 3 bits."""
    octal = octal.strip()

    if not octal:
        raise ValueError("Octal input cannot be empty.")

    if any(character not in "01234567" for character in octal):
        raise ValueError("Octal numbers may contain only digits 0 through 7.")

    binary = "".join(OCTAL_TO_BINARY[digit] for digit in octal)

    # Leading zeros introduced by the fixed three-bit groups are removed,
    # except when the entire value is zero.
    return binary.lstrip("0") or "0"


def binary_to_octal(binary: str) -> str:
    """
    Convert binary to octal.

    Shortcut:
        Group binary digits from the right into groups of three.

    Example:
        1101011
        1 | 101 | 011
        001 | 101 | 011
          1     5     3
        = 153₈
    """
    binary = binary.strip()

    if not binary or any(bit not in "01" for bit in binary):
        raise ValueError("Binary input must contain only 0 and 1.")

    padding = (-len(binary)) % 3
    padded = "0" * padding + binary

    octal_digits = []

    for index in range(0, len(padded), 3):
        group = padded[index:index + 3]
        octal_digits.append(str(int(group, 2)))

    return "".join(octal_digits).lstrip("0") or "0"


def octal_to_decimal(octal: str) -> int:
    """Convert octal directly to decimal."""
    return base_to_decimal(octal, 8)


def decimal_to_octal(decimal_value: int) -> str:
    """Convert decimal directly to octal."""
    return decimal_to_base(decimal_value, 8)


print("\nOCTAL CONVERSIONS")
for octal in ["0", "7", "10", "17", "25", "157", "777"]:
    binary = octal_to_binary(octal)
    decimal = octal_to_decimal(octal)
    print(f"{octal:>4}₈ -> binary {binary:>12} -> decimal {decimal}")


print("\nBINARY TO OCTAL USING THREE-BIT GROUPS")
for binary in ["101", "1010", "1101011", "11111111"]:
    print(f"{binary:>10}₂ -> {binary_to_octal(binary)}₈")


# ============================================================================
# 9. HEXADECIMAL NUMBER SYSTEM
# ============================================================================

"""
Hexadecimal uses base 16.

Valid digits:

    0 1 2 3 4 5 6 7 8 9 A B C D E F

The alphabetic digits represent:

    A = 10
    B = 11
    C = 12
    D = 13
    E = 14
    F = 15

Each hexadecimal digit corresponds exactly to four binary bits because:

    16 = 2^4

Mapping:

    0 -> 0000
    1 -> 0001
    ...
    9 -> 1001
    A -> 1010
    B -> 1011
    C -> 1100
    D -> 1101
    E -> 1110
    F -> 1111
"""

HEX_TO_BINARY = {
    "0": "0000",
    "1": "0001",
    "2": "0010",
    "3": "0011",
    "4": "0100",
    "5": "0101",
    "6": "0110",
    "7": "0111",
    "8": "1000",
    "9": "1001",
    "A": "1010",
    "B": "1011",
    "C": "1100",
    "D": "1101",
    "E": "1110",
    "F": "1111",
}


def hexadecimal_to_binary(hexadecimal: str) -> str:
    """Convert hexadecimal directly to binary using four-bit groups."""
    hexadecimal = hexadecimal.strip().upper()

    if not hexadecimal:
        raise ValueError("Hexadecimal input cannot be empty.")

    if any(character not in HEX_TO_BINARY for character in hexadecimal):
        raise ValueError("Invalid hexadecimal digit.")

    binary = "".join(HEX_TO_BINARY[digit] for digit in hexadecimal)

    return binary.lstrip("0") or "0"


def binary_to_hexadecimal(binary: str) -> str:
    """
    Convert binary to hexadecimal.

    Shortcut:
        Group binary digits from the right into groups of four.

    Example:
        101101011
        0001 | 0110 | 1011
           1      6      B
        = 16B₁₆
    """
    binary = binary.strip()

    if not binary or any(bit not in "01" for bit in binary):
        raise ValueError("Binary input must contain only 0 and 1.")

    padding = (-len(binary)) % 4
    padded = "0" * padding + binary

    hexadecimal_digits = []

    for index in range(0, len(padded), 4):
        group = padded[index:index + 4]
        hexadecimal_digits.append(digit_character(int(group, 2)))

    return "".join(hexadecimal_digits).lstrip("0") or "0"


def hexadecimal_to_decimal(hexadecimal: str) -> int:
    """Convert hexadecimal directly to decimal."""
    return base_to_decimal(hexadecimal, 16)


def decimal_to_hexadecimal(decimal_value: int) -> str:
    """Convert decimal directly to hexadecimal."""
    return decimal_to_base(decimal_value, 16)


print("\nHEXADECIMAL CONVERSIONS")
for hexadecimal in ["0", "A", "F", "10", "2A", "FF", "2AF", "DEADBEEF"]:
    binary = hexadecimal_to_binary(hexadecimal)
    decimal = hexadecimal_to_decimal(hexadecimal)
    print(
        f"{hexadecimal:>10}₁₆ -> "
        f"binary {binary:>40} -> decimal {decimal}"
    )


print("\nBINARY TO HEXADECIMAL USING FOUR-BIT GROUPS")
for binary in ["1010", "1111", "101101", "101101011", "11111111"]:
    print(f"{binary:>14}₂ -> {binary_to_hexadecimal(binary)}₁₆")


# ============================================================================
# 10. OCTAL TO HEXADECIMAL THROUGH BINARY
# ============================================================================

def octal_to_hexadecimal(octal: str) -> str:
    """
    Convert octal to hexadecimal through binary.

    This is useful because both octal and hexadecimal map naturally
    to binary:

        octal digit  -> 3 bits
        hex digit    -> 4 bits
    """
    binary = octal_to_binary(octal)
    return binary_to_hexadecimal(binary)


def hexadecimal_to_octal(hexadecimal: str) -> str:
    """Convert hexadecimal to octal through binary."""
    binary = hexadecimal_to_binary(hexadecimal)
    return binary_to_octal(binary)


print("\nOCTAL <-> HEXADECIMAL THROUGH BINARY")
for octal in ["17", "157", "777", "1234"]:
    hexadecimal = octal_to_hexadecimal(octal)
    print(f"{octal}₈ -> {hexadecimal}₁₆")

for hexadecimal in ["F", "2A", "FF", "ABC"]:
    octal = hexadecimal_to_octal(hexadecimal)
    print(f"{hexadecimal}₁₆ -> {octal}₈")


# ============================================================================
# 11. DECIMAL, BINARY, OCTAL, HEXADECIMAL ROUND-TRIP
# ============================================================================

@dataclass(frozen=True)
class NumberRepresentations:
    """Store the same integer in four commonly used bases."""

    decimal: int
    binary: str
    octal: str
    hexadecimal: str


def represent_number(number: int) -> NumberRepresentations:
    """Create decimal, binary, octal, and hexadecimal representations."""
    if not isinstance(number, int):
        raise TypeError("Number must be an integer.")

    return NumberRepresentations(
        decimal=number,
        binary=decimal_to_base(number, 2),
        octal=decimal_to_base(number, 8),
        hexadecimal=decimal_to_base(number, 16),
    )


print("\nCOMPLETE REPRESENTATION TABLE")
for number in [0, 1, 8, 10, 15, 16, 31, 64, 255, 1024]:
    representation = represent_number(number)
    print(
        f"{representation.decimal:>5}₁₀ | "
        f"{representation.binary:>12}₂ | "
        f"{representation.octal:>6}₈ | "
        f"{representation.hexadecimal:>6}₁₆"
    )


# ============================================================================
# 12. IMPORTANT SHORTCUTS
# ============================================================================

"""
SHORTCUT 1: Binary <-> Octal

Since:

    8 = 2^3

Group binary digits in sets of three.

Example:

    11010110

    011 | 010 | 110
     3     2     6

    = 326₈

When converting binary to octal, pad on the LEFT if necessary.

SHORTCUT 2: Binary <-> Hexadecimal

Since:

    16 = 2^4

Group binary digits in sets of four.

Example:

    11010110

    1101 | 0110
       D      6

    = D6₁₆

SHORTCUT 3: Decimal -> Binary

Repeated division by 2 gives remainders.

SHORTCUT 4: Decimal -> Octal

Repeated division by 8 gives remainders.

SHORTCUT 5: Decimal -> Hexadecimal

Repeated division by 16 gives remainders.

SHORTCUT 6: Binary -> Decimal

Use powers of two or Horner's method.

SHORTCUT 7: Hexadecimal -> Decimal

Use powers of 16.

Example:

    2AF₁₆

    = 2×256 + A×16 + F
    = 2×256 + 10×16 + 15
    = 687
"""


# ============================================================================
# 13. STEP-BY-STEP CONVERSION TRACE
# ============================================================================

def decimal_to_base_with_trace(number: int, base: int) -> list[tuple[int, int, int]]:
    """
    Return every quotient/remainder step of decimal-to-base conversion.

    Each tuple contains:
        (current_number, quotient, remainder)

    This is useful for learning the repeated-division algorithm.
    """
    validate_base(base)

    if not isinstance(number, int):
        raise TypeError("Number must be an integer.")

    if number < 0:
        raise ValueError("Trace function accepts non-negative integers.")

    if number == 0:
        return [(0, 0, 0)]

    trace = []
    current = number

    while current > 0:
        quotient, remainder = divmod(current, base)
        trace.append((current, quotient, remainder))
        current = quotient

    return trace


def print_conversion_trace(number: int, base: int) -> None:
    """Print a human-readable repeated-division conversion."""
    print(f"\nTRACE: {number} decimal -> base {base}")

    trace = decimal_to_base_with_trace(number, base)

    for current, quotient, remainder in trace:
        print(
            f"{current:>8} ÷ {base:<2} = "
            f"{quotient:>8} remainder {remainder} "
            f"({digit_character(remainder)})"
        )

    print(f"Result: {decimal_to_base(number, base)}")


print_conversion_trace(687, 16)
print_conversion_trace(157, 8)
print_conversion_trace(45, 2)


# ============================================================================
# 14. STEP-BY-STEP BINARY TO DECIMAL TRACE
# ============================================================================

def binary_to_decimal_with_trace(binary: str) -> list[tuple[str, int, int]]:
    """
    Show Horner's method step by step.

    Each tuple contains:
        (current_bit, previous_value, new_value)
    """
    binary = binary.strip()

    if not binary or any(bit not in "01" for bit in binary):
        raise ValueError("Invalid binary number.")

    trace = []
    value = 0

    for bit in binary:
        previous = value
        value = value * 2 + int(bit)
        trace.append((bit, previous, value))

    return trace


def print_binary_to_decimal_trace(binary: str) -> None:
    """Print the running calculation for binary-to-decimal conversion."""
    print(f"\nTRACE: {binary} binary -> decimal")

    for bit, previous, current in binary_to_decimal_with_trace(binary):
        print(
            f"({previous} × 2) + {bit} = {current}"
        )

    print(f"Result: {binary_to_decimal_horner(binary)}")


print_binary_to_decimal_trace("101101")


# ============================================================================
# 15. FRACTIONAL NUMBER SYSTEM CONVERSION
# ============================================================================

"""
Integer conversion and fractional conversion use different algorithms.

For an integer:

    Repeated division by the target base.

For a fractional decimal value:

    Repeated multiplication by the target base.

Example:

    0.625 decimal to binary

    0.625 × 2 = 1.25   -> integer part 1
    0.25  × 2 = 0.5    -> integer part 0
    0.5   × 2 = 1.0    -> integer part 1

    Therefore:

        0.625₁₀ = 0.101₂

Some fractions do not terminate in the target base.

Example:

    0.1 decimal in binary is repeating:

        0.0001100110011...

This occurs because 1/10 cannot be represented as a finite sum
of negative powers of 2.
"""


def decimal_fraction_to_base(
    fraction: float,
    base: int,
    max_digits: int = 32,
) -> str:
    """
    Convert a decimal fractional value in [0, 1) to a base representation.

    The result is approximate when the fraction does not terminate.

    max_digits limits the number of fractional digits to avoid infinite
    loops for repeating fractions.
    """
    validate_base(base)

    if not isinstance(fraction, (int, float)):
        raise TypeError("Fraction must be numeric.")

    if not 0 <= fraction < 1:
        raise ValueError("Fraction must be in the interval [0, 1).")

    if not isinstance(max_digits, int) or max_digits <= 0:
        raise ValueError("max_digits must be a positive integer.")

    digits = []

    for _ in range(max_digits):
        fraction *= base
        integer_part = int(fraction)

        digits.append(digit_character(integer_part))
        fraction -= integer_part

        if fraction == 0:
            break

    return "0." + "".join(digits)


print("\nFRACTIONAL CONVERSION")
for fraction in [0.5, 0.625, 0.75, 0.1]:
    print(
        f"{fraction}₁₀ -> "
        f"{decimal_fraction_to_base(fraction, 2, 16)}₂"
    )


# ============================================================================
# 16. GENERAL FRACTIONAL BASE-N TO DECIMAL
# ============================================================================

def base_fraction_to_decimal(number: str, base: int) -> float:
    """
    Convert a base-N fractional number into a Python float.

    Example:

        101.101₂

        = 1×2^2 + 0×2^1 + 1×2^0
          + 1×2^-1 + 0×2^-2 + 1×2^-3

        = 5.625
    """
    validate_base(base)

    if not isinstance(number, str):
        raise TypeError("Number must be a string.")

    number = number.strip().upper()

    if number.count(".") > 1:
        raise ValueError("A number may contain at most one decimal point.")

    integer_part, separator, fractional_part = number.partition(".")

    if not integer_part:
        integer_part = "0"

    if separator and not fractional_part:
        raise ValueError("A decimal point must be followed by digits.")

    integer_value = base_to_decimal(integer_part, base)

    fractional_value = 0.0

    for position, character in enumerate(fractional_part, start=1):
        value = digit_value(character)

        if value >= base:
            raise ValueError(
                f"Digit '{character}' is invalid for base {base}."
            )

        fractional_value += value * (base ** -position)

    return integer_value + fractional_value


print("\nBASE-N FRACTIONS TO DECIMAL")
for value, base in [
    ("101.101", 2),
    ("17.4", 8),
    ("A.F", 16),
    ("2A.C", 16),
]:
    print(f"{value} base {base} -> {base_fraction_to_decimal(value, base)}")


# ============================================================================
# 17. COMPLETE INTEGER CONVERTER WITH MULTIPLE BASES
# ============================================================================

def convert_integer(number: str, source_base: int, target_base: int) -> str:
    """
    Convert an integer string directly from one base to another.

    Conceptually:

        source representation
                |
                v
           decimal value
                |
                v
        target representation

    The decimal intermediate is a mathematical value, not a requirement
    that a physical decimal representation be constructed during every
    implementation.
    """
    decimal_value = base_to_decimal(number, source_base)
    return decimal_to_base(decimal_value, target_base)


print("\nARBITRARY BASE-TO-BASE CONVERSIONS")
conversion_examples = [
    ("101101", 2, 8),
    ("101101", 2, 16),
    ("157", 8, 2),
    ("157", 8, 16),
    ("2AF", 16, 2),
    ("2AF", 16, 8),
    ("2AF", 16, 10),
]

for number, source_base, target_base in conversion_examples:
    result = convert_integer(number, source_base, target_base)
    print(
        f"({number}) base {source_base} -> "
        f"({result}) base {target_base}"
    )


# ============================================================================
# 18. PYTHON'S BUILT-IN NUMBER CONVERSION FUNCTIONS
# ============================================================================

"""
Python provides highly optimized built-in conversion facilities.

    bin(45)       -> '0b101101'
    oct(45)       -> '0o55'
    hex(45)       -> '0x2d'

The int() function can parse strings when the source base is supplied:

    int("101101", 2) -> 45
    int("55", 8)     -> 45
    int("2D", 16)    -> 45

The prefixes:

    0b -> binary
    0o -> octal
    0x -> hexadecimal

can also be understood by int() when base=0:

    int("0b101101", 0)
    int("0o55", 0)
    int("0x2D", 0)

For general educational implementations, the manual functions above
show the underlying algorithms rather than hiding them behind built-ins.
"""


print("\nPYTHON BUILT-IN CONVERSION FUNCTIONS")
value = 45
print("bin(45) =", bin(value))
print("oct(45) =", oct(value))
print("hex(45) =", hex(value))

print('int("101101", 2) =', int("101101", 2))
print('int("55", 8) =', int("55", 8))
print('int("2D", 16) =', int("2D", 16))
print('int("0b101101", 0) =', int("0b101101", 0))


# ============================================================================
# 19. PREFIX HANDLING
# ============================================================================

def parse_prefixed_integer(value: str) -> int:
    """
    Parse common Python-style prefixes.

    Supported prefixes:
        0b -> binary
        0o -> octal
        0x -> hexadecimal

    Decimal numbers without a prefix are treated as base 10.
    """
    if not isinstance(value, str):
        raise TypeError("Value must be a string.")

    value = value.strip()

    if not value:
        raise ValueError("Value cannot be empty.")

    lower = value.lower()

    if lower.startswith("0b"):
        return base_to_decimal(value[2:], 2)
    if lower.startswith("0o"):
        return base_to_decimal(value[2:], 8)
    if lower.startswith("0x"):
        return base_to_decimal(value[2:], 16)

    return base_to_decimal(value, 10)


print("\nPREFIX PARSING")
for value in ["101", "0b101", "0o101", "0x101", "0xFF"]:
    print(f"{value:>8} -> {parse_prefixed_integer(value)}")


# ============================================================================
# 20. LEADING ZEROES
# ============================================================================

"""
Leading zeros do not change an unsigned positional integer's value.

Examples:

    00010110₂ = 10110₂
    00077₈   = 77₈
    0000FF₁₆ = FF₁₆

But fixed-width binary is important in computing.

For example:

    5 decimal

    normal representation:
        101

    8-bit representation:
        00000101

The value is the same, but the width carries information about
storage and representation.
"""


def format_fixed_width_binary(number: int, width: int) -> str:
    """Return a non-negative integer as exactly width binary digits."""
    if not isinstance(number, int):
        raise TypeError("Number must be an integer.")

    if number < 0:
        raise ValueError("Number must be non-negative.")

    if not isinstance(width, int) or width <= 0:
        raise ValueError("Width must be a positive integer.")

    if number >= 2 ** width:
        raise ValueError(
            f"{number} cannot be represented using {width} unsigned bits."
        )

    return format(number, f"0{width}b")


print("\nFIXED-WIDTH BINARY")
for value in [0, 1, 5, 127, 128, 255]:
    print(f"{value:>3} -> {format_fixed_width_binary(value, 8)}")


# ============================================================================
# 21. BIT LENGTH
# ============================================================================

"""
For a positive integer n, the minimum number of binary bits required
for an unsigned representation is:

    floor(log2(n)) + 1

Python exposes this efficiently through:

    n.bit_length()

Examples:

    1  -> 1 bit
    2  -> 2 bits
    3  -> 2 bits
    4  -> 3 bits
    7  -> 3 bits
    8  -> 4 bits

Zero is a special case:

    0.bit_length() == 0

although the conventional written representation of zero still uses
one digit: "0".
"""


print("\nBIT LENGTH")
for value in [0, 1, 2, 3, 4, 7, 8, 255, 256, 1023, 1024]:
    print(f"{value:>5} -> minimum binary digits: {value.bit_length()}")


# ============================================================================
# 22. POWERS OF TWO SHORTCUT
# ============================================================================

def is_power_of_two(number: int) -> bool:
    """
    Determine whether a positive integer is a power of two.

    Binary property:

        powers of two contain exactly one set bit.

        1   = 0001
        2   = 0010
        4   = 0100
        8   = 1000

    The expression:

        n & (n - 1)

    clears the lowest set bit.

    For a power of two, no other set bits remain.
    """
    return number > 0 and (number & (number - 1)) == 0


print("\nPOWER-OF-TWO CHECK")
for value in [0, 1, 2, 3, 4, 8, 10, 16, 31, 32, 64]:
    print(f"{value:>3} -> {is_power_of_two(value)}")


# ============================================================================
# 23. BITWISE OPERATORS AND NUMBER REPRESENTATION
# ============================================================================

"""
Binary representation is closely connected to bitwise operations.

Operators:

    &   AND
    |   OR
    ^   XOR
    ~   NOT
    <<  left shift
    >>  right shift

Example:

    12 = 1100₂
     5 = 0101₂

    12 & 5 = 0100₂ = 4
    12 | 5 = 1101₂ = 13
    12 ^ 5 = 1001₂ = 9

Left shift:

    5 << 2

means:

    0101 << 2 = 10100 = 20

For non-negative integers:

    n << k = n × 2^k

Right shift:

    20 >> 2 = 5

For non-negative integers:

    n >> k = floor(n / 2^k)
"""


def show_bitwise_operations(left: int, right: int) -> None:
    """Display common bitwise operations using decimal and binary forms."""
    print(f"\nBITWISE OPERATIONS: {left} and {right}")

    print(f"{left:>3} = {left:08b}")
    print(f"{right:>3} = {right:08b}")

    print(f"{left} & {right} = {left & right:>3} = {left & right:08b}")
    print(f"{left} | {right} = {left | right:>3} = {left | right:08b}")
    print(f"{left} ^ {right} = {left ^ right:>3} = {left ^ right:08b}")


show_bitwise_operations(12, 5)

print("\nSHIFT EXAMPLES")
for value in [1, 2, 5, 10]:
    print(
        f"{value:>3} << 2 = {value << 2:>3}, "
        f"{value:>3} >> 1 = {value >> 1:>3}"
    )


# ============================================================================
# 24. NEGATIVE NUMBERS AND TWO'S COMPLEMENT
# ============================================================================

"""
Negative integers require an interpretation rule.

A common computer representation is two's complement.

For an n-bit signed integer:

    range = -2^(n-1) through 2^(n-1) - 1

For 8 bits:

    -128 through +127

To obtain -5 in 8-bit two's complement:

    +5:
        00000101

    invert all bits:
        11111010

    add 1:
        11111011

Therefore:

    -5 = 11111011₂ in 8-bit two's complement

Python integers are not restricted to a fixed width, so Python's
bitwise representation of negative integers should not be confused
with a single fixed-width binary string.

The following functions explicitly enforce a chosen width.
"""


def signed_to_twos_complement(number: int, width: int) -> str:
    """
    Represent a signed integer using exactly `width` two's-complement bits.
    """
    if not isinstance(number, int):
        raise TypeError("Number must be an integer.")

    if not isinstance(width, int) or width <= 0:
        raise ValueError("Width must be positive.")

    minimum = -(2 ** (width - 1))
    maximum = 2 ** (width - 1) - 1

    if not minimum <= number <= maximum:
        raise ValueError(
            f"{number} is outside the {width}-bit signed range "
            f"[{minimum}, {maximum}]."
        )

    if number < 0:
        encoded = (1 << width) + number
    else:
        encoded = number

    return format(encoded, f"0{width}b")


def twos_complement_to_signed(binary: str) -> int:
    """Interpret a fixed-width binary string as a two's-complement integer."""
    if not isinstance(binary, str):
        raise TypeError("Binary value must be a string.")

    binary = binary.strip()

    if not binary or any(bit not in "01" for bit in binary):
        raise ValueError("Invalid binary string.")

    width = len(binary)
    unsigned_value = int(binary, 2)

    if binary[0] == "0":
        return unsigned_value

    return unsigned_value - (1 << width)


print("\nTWO'S COMPLEMENT")
for value in [-128, -5, -1, 0, 1, 5, 127]:
    print(f"{value:>4} -> {signed_to_twos_complement(value, 8)}")

for binary in ["00000101", "11111011", "11111111", "10000000"]:
    print(f"{binary} -> {twos_complement_to_signed(binary)}")


# ============================================================================
# 25. MANUAL TWO'S COMPLEMENT CONSTRUCTION
# ============================================================================

def manual_twos_complement(binary: str) -> str:
    """
    Compute the two's complement of a fixed-width binary string manually.

    Algorithm:
        1. Invert every bit.
        2. Add one.

    The result stays at the same width.
    """
    if not isinstance(binary, str):
        raise TypeError("Binary must be a string.")

    binary = binary.strip()

    if not binary or any(bit not in "01" for bit in binary):
        raise ValueError("Invalid binary number.")

    inverted = "".join("1" if bit == "0" else "0" for bit in binary)

    value = (int(inverted, 2) + 1) % (2 ** len(binary))

    return format(value, f"0{len(binary)}b")


print("\nMANUAL TWO'S COMPLEMENT")
for binary in ["00000101", "00000001", "01111111"]:
    print(f"{binary} -> {manual_twos_complement(binary)}")


# ============================================================================
# 26. OCTAL AND HEXADECIMAL TABLES
# ============================================================================

def print_binary_octal_table() -> None:
    """Display the complete one-digit octal-to-binary mapping."""
    print("\nOCTAL <-> BINARY TABLE")
    print("Octal | Binary")
    print("------|-------")

    for octal_digit, binary in OCTAL_TO_BINARY.items():
        print(f"  {octal_digit}   | {binary}")


def print_hexadecimal_binary_table() -> None:
    """Display the complete hexadecimal-to-binary mapping."""
    print("\nHEXADECIMAL <-> BINARY TABLE")
    print("Hex | Binary")
    print("----|-------")

    for hexadecimal_digit, binary in HEX_TO_BINARY.items():
        print(f" {hexadecimal_digit}  | {binary}")


print_binary_octal_table()
print_hexadecimal_binary_table()


# ============================================================================
# 27. ARITHMETIC IN DIFFERENT BASES
# ============================================================================

def add_numbers_in_base(
    left: str,
    right: str,
    base: int,
) -> str:
    """
    Add two non-negative integers represented in the same base.

    The implementation converts both operands to decimal internally,
    performs integer addition, and converts the result back.

    This is useful for verifying base arithmetic.
    """
    left_decimal = base_to_decimal(left, base)
    right_decimal = base_to_decimal(right, base)

    return decimal_to_base(left_decimal + right_decimal, base)


def subtract_numbers_in_base(
    left: str,
    right: str,
    base: int,
) -> str:
    """
    Subtract two integers represented in the same base.

    Negative results are supported.
    """
    left_decimal = base_to_decimal(left, base)
    right_decimal = base_to_decimal(right, base)

    return decimal_to_base(left_decimal - right_decimal, base)


def multiply_numbers_in_base(
    left: str,
    right: str,
    base: int,
) -> str:
    """Multiply two integer representations in an arbitrary base."""
    left_decimal = base_to_decimal(left, base)
    right_decimal = base_to_decimal(right, base)

    return decimal_to_base(left_decimal * right_decimal, base)


print("\nARITHMETIC IN DIFFERENT BASES")
print("1011₂ + 110₂ =", add_numbers_in_base("1011", "110", 2), "₂")
print("17₈ + 5₈ =", add_numbers_in_base("17", "5", 8), "₈")
print("A₁₆ + 6₁₆ =", add_numbers_in_base("A", "6", 16), "₁₆")
print("FF₁₆ + 1₁₆ =", add_numbers_in_base("FF", "1", 16), "₁₆")
print("100₂ - 1₂ =", subtract_numbers_in_base("100", "1", 2), "₂")
print("F₁₆ × 10₁₆ =", multiply_numbers_in_base("F", "10", 16), "₁₆")


# ============================================================================
# 28. MANUAL BINARY ADDITION
# ============================================================================

def add_binary_strings(left: str, right: str) -> str:
    """
    Add two binary strings without converting them to Python integers.

    The addition proceeds from right to left while maintaining a carry.

    Truth table for one binary position:

        0 + 0 + 0 = sum 0, carry 0
        0 + 0 + 1 = sum 1, carry 0
        0 + 1 + 1 = sum 0, carry 1
        1 + 1 + 1 = sum 1, carry 1
    """
    if not isinstance(left, str) or not isinstance(right, str):
        raise TypeError("Binary operands must be strings.")

    left = left.strip()
    right = right.strip()

    if not left or not right:
        raise ValueError("Binary operands cannot be empty.")

    if any(bit not in "01" for bit in left + right):
        raise ValueError("Binary operands must contain only 0 and 1.")

    i = len(left) - 1
    j = len(right) - 1
    carry = 0
    result = []

    while i >= 0 or j >= 0 or carry:
        left_bit = int(left[i]) if i >= 0 else 0
        right_bit = int(right[j]) if j >= 0 else 0

        total = left_bit + right_bit + carry

        result.append(str(total % 2))
        carry = total // 2

        i -= 1
        j -= 1

    return "".join(reversed(result))


print("\nMANUAL BINARY ADDITION")
for left, right in [
    ("0", "0"),
    ("1", "1"),
    ("101", "11"),
    ("1111", "1"),
    ("101101", "11011"),
]:
    result = add_binary_strings(left, right)
    print(f"{left} + {right} = {result}")


# ============================================================================
# 29. MANUAL BINARY SUBTRACTION
# ============================================================================

def subtract_binary_strings(left: str, right: str) -> str:
    """
    Subtract binary strings without using int(binary, 2).

    This implementation assumes left >= right.

    Borrow rules include:

        0 - 0 = 0
        1 - 0 = 1
        1 - 1 = 0
        0 - 1 requires a borrow.
    """
    left_value = binary_to_decimal_horner(left)
    right_value = binary_to_decimal_horner(right)

    if left_value < right_value:
        raise ValueError("This implementation requires left >= right.")

    result = decimal_to_base(left_value - right_value, 2)

    return result


print("\nMANUAL BINARY SUBTRACTION")
for left, right in [
    ("10", "1"),
    ("101", "10"),
    ("10000", "1"),
    ("1111", "101"),
]:
    print(f"{left} - {right} = {subtract_binary_strings(left, right)}")


# ============================================================================
# 30. VALIDATION AND ERROR HANDLING
# ============================================================================

print("\nVALIDATION EXAMPLES")

invalid_inputs = [
    ("102", 2),
    ("89", 8),
    ("1G", 16),
    ("", 2),
    ("2", 2),
]

for number, base in invalid_inputs:
    try:
        result = base_to_decimal(number, base)
        print(f"{number} base {base} -> {result}")
    except (TypeError, ValueError) as error:
        print(f"{number!r} base {base} -> ERROR: {error}")


# ============================================================================
# 31. EDGE CASES
# ============================================================================

"""
Important edge cases:

1. Zero
       0₁₀ = 0₂ = 0₈ = 0₁₆

2. One
       1₁₀ = 1₂ = 1₈ = 1₁₆

3. Leading zeroes
       000101₂ = 101₂

4. Invalid digits
       2 is invalid in binary.
       8 and 9 are invalid in octal.
       G is invalid in hexadecimal.

5. Negative numbers
       Need an explicit representation convention.
       Two's complement is common for fixed-width machine integers.

6. Fractions
       Some fractions terminate in one base and repeat in another.

7. Fixed width
       255 fits in 8 unsigned bits.
       256 requires 9 unsigned bits.

8. Case
       Hexadecimal A-F are case-insensitive in our parser.

9. Empty input
       Must be rejected rather than interpreted as zero.

10. Width overflow
       An unsigned 8-bit representation cannot represent 256.
"""


# ============================================================================
# 32. AUTOMATED TESTS
# ============================================================================

def run_deterministic_tests() -> None:
    """Run deterministic tests covering fundamental conversion behavior."""

    known_values = [
        0,
        1,
        2,
        3,
        7,
        8,
        9,
        10,
        15,
        16,
        31,
        32,
        63,
        64,
        127,
        128,
        255,
        256,
        1023,
        1024,
        65535,
        65536,
    ]

    for number in known_values:
        binary = decimal_to_base(number, 2)
        octal = decimal_to_base(number, 8)
        hexadecimal = decimal_to_base(number, 16)

        assert base_to_decimal(binary, 2) == number
        assert base_to_decimal(octal, 8) == number
        assert base_to_decimal(hexadecimal, 16) == number

        assert decimal_to_binary_division(number) == binary
        assert decimal_to_binary_powers(number) == binary

        assert binary_to_decimal_positional(binary) == number
        assert binary_to_decimal_horner(binary) == number

        assert octal_to_decimal(octal) == number
        assert hexadecimal_to_decimal(hexadecimal) == number

        assert binary_to_octal(binary) == octal
        assert binary_to_hexadecimal(binary) == hexadecimal

    assert octal_to_binary("0") == "0"
    assert hexadecimal_to_binary("0") == "0"

    assert octal_to_binary("10") == "1000"
    assert hexadecimal_to_binary("10") == "10000"

    assert decimal_fraction_to_base(0.5, 2) == "0.1"
    assert decimal_fraction_to_base(0.625, 2) == "0.101"

    assert base_fraction_to_decimal("0.1", 2) == 0.5
    assert base_fraction_to_decimal("101.101", 2) == 5.625

    assert add_binary_strings("101", "11") == "1000"
    assert add_numbers_in_base("FF", "1", 16) == "100"

    assert is_power_of_two(1)
    assert is_power_of_two(2)
    assert is_power_of_two(1024)
    assert not is_power_of_two(0)
    assert not is_power_of_two(3)

    assert signed_to_twos_complement(-5, 8) == "11111011"
    assert twos_complement_to_signed("11111011") == -5

    print("\nDeterministic tests: PASSED")


def run_randomized_round_trip_tests(
    iterations: int = 1000,
    seed: int = 42,
) -> None:
    """
    Test random integers by converting them among several bases and back.

    Randomized round-trip testing is useful because conversion functions
    should preserve the mathematical value.
    """
    random_generator = random.Random(seed)

    bases = [2, 8, 10, 16, 3, 5, 7, 12, 20, 36]

    for _ in range(iterations):
        number = random_generator.randint(0, 10**18)

        for base in bases:
            representation = decimal_to_base(number, base)
            recovered = base_to_decimal(representation, base)

            assert recovered == number, (
                f"Round-trip failure: {number}, base {base}, "
                f"representation {representation}"
            )

    print(f"Randomized tests ({iterations} iterations): PASSED")


run_deterministic_tests()
run_randomized_round_trip_tests()


# ============================================================================
# 33. PERFORMANCE DISCUSSION THROUGH MEASUREMENT
# ============================================================================

"""
For a number represented with n digits in a base:

    Conversion by scanning every digit is O(n).

Repeated division also requires approximately O(n) iterations because
each division reduces the remaining magnitude by a factor related to
the target base.

The number of digits itself grows logarithmically with the value:

    digits ≈ log_base(value)

Python's built-in conversions are implemented efficiently and should
normally be preferred in production when a manual educational algorithm
is not specifically required.
"""

import time


def measure_conversion(function: Callable[[int], str], values: Iterable[int]) -> float:
    """Return elapsed time for applying a conversion function to values."""
    start = time.perf_counter()

    for value in values:
        function(value)

    return time.perf_counter() - start


print("\nPERFORMANCE DEMONSTRATION")

performance_values = list(range(0, 10000))

manual_time = measure_conversion(
    lambda value: decimal_to_base(value, 2),
    performance_values,
)

builtin_time = measure_conversion(
    lambda value: format(value, "b"),
    performance_values,
)

print(f"Manual base-2 conversion time : {manual_time:.6f} seconds")
print(f"Python format(..., 'b') time : {builtin_time:.6f} seconds")
print(
    "Timing varies by machine and should be treated as an illustration, "
    "not as a benchmark."
)


# ============================================================================
# 34. BASE CONVERSION USING RECURSION
# ============================================================================

def decimal_to_base_recursive(number: int, base: int) -> str:
    """
    Recursive implementation of repeated division.

    The recursive structure naturally produces digits from the most
    significant side because recursive calls return before the current
    remainder is appended.

    This is educational. Iteration is generally preferable for very
    large
    values because recursion introduces call-stack overhead.
    """
    validate_base(base)

    if not isinstance(number, int):
        raise TypeError("Number must be an integer.")

    if number < 0:
        return "-" + decimal_to_base_recursive(-number, base)

    if number < base:
        return digit_character(number)

    quotient, remainder = divmod(number, base)

    return (
        decimal_to_base_recursive(quotient, base)
        + digit_character(remainder)
    )


print("\nRECURSIVE CONVERSION")
for number, base in [(45, 2), (157, 8), (687, 16)]:
    print(
        f"{number} -> {decimal_to_base_recursive(number, base)} "
        f"(base {base})"
    )


# ============================================================================
# 35. CONVERSION WITHOUT STRING LOOKUP TABLES
# ============================================================================

def decimal_to_binary_bitwise(number: int) -> str:
    """
    Convert a non-negative integer to binary using bitwise operations.

    A bit mask examines one bit at a time.

    For example, for 13:

        13 = 1101₂

    A shifting mask can inspect each bit.

    This demonstrates the close relationship between binary conversion
    and bit-level computer operations.
    """
    if not isinstance(number, int):
        raise TypeError("Number must be an integer.")

    if number < 0:
        raise ValueError("Only non-negative integers are supported.")

    if number == 0:
        return "0"

    highest_bit = number.bit_length() - 1
    result = []

    for position in range(highest_bit, -1, -1):
        result.append("1" if number & (1 << position) else "0")

    return "".join(result)


print("\nBITWISE DECIMAL TO BINARY")
for number in [0, 1, 5, 13, 42, 255, 1024]:
    print(f"{number:>5} -> {decimal_to_binary_bitwise(number)}")


# ============================================================================
# 36. BINARY TO DECIMAL USING BITWISE OPERATIONS
# ============================================================================

def binary_to_decimal_bitwise(binary: str) -> int:
    """
    Convert binary to decimal using left shifts and OR.

    Equivalent conceptual operation:

        value = (value << 1) | current_bit

    This is another form of Horner's method for base 2.
    """
    if not isinstance(binary, str):
        raise TypeError("Binary input must be a string.")

    binary = binary.strip()

    if not binary or any(bit not in "01" for bit in binary):
        raise ValueError("Invalid binary string.")

    value = 0

    for bit in binary:
        value = (value << 1) | int(bit)

    return value


print("\nBITWISE BINARY TO DECIMAL")
for binary in ["1", "10", "101", "101101", "11111111"]:
    print(f"{binary:>10} -> {binary_to_decimal_bitwise(binary)}")


# ============================================================================
# 37. RELATIONSHIP BETWEEN BINARY, OCTAL, AND HEX
# ============================================================================

def demonstrate_grouping_shortcut(binary: str) -> None:
    """
    Display the exact grouping used to convert binary to octal and hex.

    Octal groups:
        3 bits

    Hexadecimal groups:
        4 bits
    """
    binary = binary.strip()

    if not binary or any(bit not in "01" for bit in binary):
        raise ValueError("Invalid binary string.")

    octal_padding = (-len(binary)) % 3
    hex_padding = (-len(binary)) % 4

    octal_padded = "0" * octal_padding + binary
    hex_padded = "0" * hex_padding + binary

    octal_groups = [
        octal_padded[index:index + 3]
        for index in range(0, len(octal_padded), 3)
    ]

    hex_groups = [
        hex_padded[index:index + 4]
        for index in range(0, len(hex_padded), 4)
    ]

    print("\nGROUPING SHORTCUT")
    print(f"Binary: {binary}")
    print(f"Octal groups: {' | '.join(octal_groups)}")
    print(f"Octal result: {binary_to_octal(binary)}")
    print(f"Hex groups:   {' | '.join(hex_groups)}")
    print(f"Hex result:   {binary_to_hexadecimal(binary)}")


demonstrate_grouping_shortcut("110101101011")


# ============================================================================
# 38. WHY OCTAL AND HEXADECIMAL ARE USED
# ============================================================================

"""
Binary is the natural representation for digital hardware, but long
binary strings are difficult for humans to read.

Octal compresses binary by a factor of approximately three bits per digit.

Hexadecimal compresses binary by four bits per digit.

Examples:

    Binary:
        1111111111111111

    Octal:
        177777

    Hexadecimal:
        FFFF

Hexadecimal is particularly common in:

    - memory addresses
    - machine code
    - bit masks
    - RGB color values
    - debugging
    - network identifiers
    - binary file inspection
    - checksums and hashes
    - low-level programming

Octal historically appears in:

    - Unix permission notation
    - older computer systems
    - contexts where three-bit grouping is useful

For example, Unix permissions commonly use:

    755

where each digit corresponds to a three-bit permission group.
"""


# ============================================================================
# 39. PRACTICAL RGB HEXADECIMAL EXAMPLE
# ============================================================================

def rgb_to_hex(red: int, green: int, blue: int) -> str:
    """
    Convert an RGB color to six-digit hexadecimal notation.

    Each RGB channel is stored as an unsigned 8-bit value:

        0 through 255

    Each channel therefore needs exactly two hexadecimal digits.
    """
    channels = [red, green, blue]

    if any(not isinstance(channel, int) for channel in channels):
        raise TypeError("RGB channels must be integers.")

    if any(channel < 0 or channel > 255 for channel in channels):
        raise ValueError("RGB channels must be between 0 and 255.")

    return "#" + "".join(f"{channel:02X}" for channel in channels)


def hex_to_rgb(hexadecimal: str) -> tuple[int, int, int]:
    """Convert #RRGGBB or RRGGBB hexadecimal notation into RGB channels."""
    if not isinstance(hexadecimal, str):
        raise TypeError("Hexadecimal color must be a string.")

    value = hexadecimal.strip()

    if value.startswith("#"):
        value = value[1:]

    if len(value) != 6:
        raise ValueError("RGB hexadecimal value must contain six digits.")

    if any(character not in HEX_TO_BINARY for character in value.upper()):
        raise ValueError("Invalid hexadecimal RGB value.")

    return (
        int(value[0:2], 16),
        int(value[2:4], 16),
        int(value[4:6], 16),
    )


print("\nRGB AND HEXADECIMAL")
for rgb in [(0, 0, 0), (255, 255, 255), (255, 0, 0), (12, 34, 56)]:
    hexadecimal = rgb_to_hex(*rgb)
    recovered = hex_to_rgb(hexadecimal)
    print(f"{rgb} -> {hexadecimal} -> {recovered}")


# ============================================================================
# 40. OCTAL UNIX-PERMISSION EXAMPLE
# ============================================================================

def explain_unix_permission_digit(digit: int) -> dict[str, bool]:
    """
    Decode one octal permission digit.

    Bit values:

        4 -> read
        2 -> write
        1 -> execute

    Example:

        7 = 4 + 2 + 1 -> read, write, execute
        5 = 4 + 1     -> read, execute
    """
    if not isinstance(digit, int) or not 0 <= digit <= 7:
        raise ValueError("Permission digit must be between 0 and 7.")

    return {
        "read": bool(digit & 4),
        "write": bool(digit & 2),
        "execute": bool(digit & 1),
    }


def decode_permission_mode(mode: str) -> list[dict[str, bool]]:
    """Decode a three-digit Unix-style permission mode such as 755."""
    if not isinstance(mode, str):
        raise TypeError("Mode must be a string.")

    mode = mode.strip()

    if len(mode) != 3 or any(digit not in "01234567" for digit in mode):
        raise ValueError("Mode must contain exactly three octal digits.")

    return [explain_unix_permission_digit(int(digit)) for digit in mode]


print("\nOCTAL PERMISSION EXAMPLE")
mode = "755"
decoded_permissions = decode_permission_mode(mode)

for identity, permissions in zip(
    ["owner", "group", "others"],
    decoded_permissions,
):
    print(f"{identity:>7}: {permissions}")


# ============================================================================
# 41. CHECKSUM-LIKE HEX REPRESENTATION
# ============================================================================

def bytes_to_hexadecimal(data: bytes) -> str:
    """
    Convert raw bytes to hexadecimal.

    Each byte is represented using exactly two hexadecimal digits.

    Example:

        byte 255 -> FF
        byte 10  -> 0A
    """
    if not isinstance(data, bytes):
        raise TypeError("Input must be bytes.")

    return "".join(f"{byte:02X}" for byte in data)


def hexadecimal_to_bytes(hexadecimal: str) -> bytes:
    """Convert an even-length hexadecimal string back into bytes."""
    if not isinstance(hexadecimal, str):
        raise TypeError("Hexadecimal input must be a string.")

    value = hexadecimal.strip()

    if value.startswith(("0x", "0X")):
        value = value[2:]

    if len(value) % 2 != 0:
        raise ValueError("A byte-oriented hexadecimal string needs even length.")

    if any(character not in HEX_TO_BINARY for character in value.upper()):
        raise ValueError("Invalid hexadecimal byte string.")

    return bytes(
        int(value[index:index + 2], 16)
        for index in range(0, len(value), 2)
    )


print("\nBYTES <-> HEXADECIMAL")
raw_data = b"Hello"
hexadecimal_data = bytes_to_hexadecimal(raw_data)
recovered_data = hexadecimal_to_bytes(hexadecimal_data)

print("Bytes:", raw_data)
print("Hex :", hexadecimal_data)
print("Back:", recovered_data)


# ============================================================================
# 42. COMMON MISTAKES DEMONSTRATED
# ============================================================================

"""
Mistake 1:
    Reading decimal-style digits as though the base were 10.

    101₂ is not one hundred one.

    It is:
        1×4 + 0×2 + 1×1 = 5.

Mistake 2:
    Forgetting that hexadecimal A-F represent 10-15.

Mistake 3:
    Grouping binary from the LEFT rather than the RIGHT.

    Correct:
        groups are formed from the least significant side.

Mistake 4:
    Forgetting left-side padding when groups are incomplete.

Mistake 5:
    Reading repeated-division remainders top-to-bottom.

    They must be read bottom-to-top.

Mistake 6:
    Assuming every decimal fraction has a finite binary representation.

Mistake 7:
    Confusing numerical value with fixed-width representation.

    5 = 101
    5 = 00000101

Mistake 8:
    Treating a negative Python integer as though it were automatically
    an eight-bit two's-complement value.

Mistake 9:
    Accepting invalid digits without checking them.

Mistake 10:
    Removing leading zeroes when fixed width is semantically important.
"""


# ============================================================================
# 43. CONVERSION PRACTICE PROBLEMS WITH ANSWERS
# ============================================================================

@dataclass(frozen=True)
class ConversionProblem:
    question: str
    answer: str


practice_problems = [
    ConversionProblem("13 decimal to binary", "1101"),
    ConversionProblem("25 decimal to binary", "11001"),
    ConversionProblem("45 decimal to octal", "55"),
    ConversionProblem("255 decimal to hexadecimal", "FF"),
    ConversionProblem("101101 binary to decimal", "45"),
    ConversionProblem("1101011 binary to octal", "153"),
    ConversionProblem("1101011 binary to hexadecimal", "6B"),
    ConversionProblem("157 octal to decimal", "111"),
    ConversionProblem("2AF hexadecimal to decimal", "687"),
    ConversionProblem("FF hexadecimal to binary", "11111111"),
]


def display_practice_problems() -> None:
    """Display solved conversion problems."""
    print("\nPRACTICE PROBLEMS WITH ANSWERS")

    for problem in practice_problems:
        print(f"{problem.question:<45} = {problem.answer}")


display_practice_problems()


# ============================================================================
# 44. CONVERSION MATRIX
# ============================================================================

def conversion_matrix(number: int) -> dict[str, str]:
    """Return representations of an integer in common bases."""
    return {
        "binary": decimal_to_base(number, 2),
        "octal": decimal_to_base(number, 8),
        "decimal": decimal_to_base(number, 10),
        "hexadecimal": decimal_to_base(number, 16),
    }


print("\nCONVERSION MATRIX FOR 687")
for name, representation in conversion_matrix(687).items():
    print(f"{name:>12}: {representation}")


# ============================================================================
# 45. DIRECT POWER RELATIONSHIPS
# ============================================================================

"""
Important mathematical relationships:

    2^1 = 2
    2^2 = 4
    2^3 = 8
    2^4 = 16

Therefore:

    octal      = base 2^3
    hexadecimal = base 2^4

This explains the shortcuts rather than making them rules to memorize
without understanding.

General principle:

If:

    target base = 2^k

then:

    k binary bits correspond exactly to one target-base digit.

Examples:

    base 4  = 2^2 -> 2 bits per digit
    base 8  = 2^3 -> 3 bits per digit
    base 16 = 2^4 -> 4 bits per digit
    base 32 = 2^5 -> 5 bits per digit
"""


def binary_to_power_of_two_base(binary: str, bits_per_digit: int) -> str:
    """
    Generic binary conversion for bases that are powers of two.

    Examples:

        bits_per_digit = 3 -> base 8
        bits_per_digit = 4 -> base 16
    """
    if bits_per_digit <= 0:
        raise ValueError("bits_per_digit must be positive.")

    base = 2 ** bits_per_digit

    if base > len(DIGITS):
        raise ValueError("Resulting base exceeds supported digit alphabet.")

    return convert_integer(binary, 2, base)


print("\nPOWER-OF-TWO BASE SHORTCUT")
print("101101₂ -> base 8 :", binary_to_power_of_two_base("101101", 3))
print("101101₂ -> base 16:", binary_to_power_of_two_base("101101", 4))


# ============================================================================
# 46. BASE REPRESENTATION OBJECT
# ============================================================================

@dataclass
class BaseNumber:
    """
    Represent an integer together with its base.

    The object validates its digits and exposes conversion methods.
    """

    digits: str
    base: int

    def __post_init__(self) -> None:
        validate_base(self.base)

        if not isinstance(self.digits, str):
            raise TypeError("digits must be a string.")

        self.digits = self.digits.strip().upper()

        if not self.digits:
            raise ValueError("digits cannot be empty.")

        # Validate by parsing. This catches invalid characters and
        # digits that exceed the selected base.
        base_to_decimal(self.digits, self.base)

    @property
    def decimal_value(self) -> int:
        """Return the represented mathematical integer."""
        return base_to_decimal(self.digits, self.base)

    def convert_to(self, target_base: int) -> "BaseNumber":
        """Return the same mathematical value in another base."""
        converted = decimal_to_base(self.decimal_value, target_base)
        return BaseNumber(converted, target_base)

    def __str__(self) -> str:
        return f"{self.digits} (base {self.base})"


print("\nBASE NUMBER OBJECT")
base_number = BaseNumber("2AF", 16)

print("Original:", base_number)
print("Decimal :", base_number.decimal_value)
print("Binary  :", base_number.convert_to(2))
print("Octal   :", base_number.convert_to(8))


# ============================================================================
# 47. COMMAND-LINE CONVERTER
# ============================================================================

def command_line_converter(arguments: Optional[list[str]] = None) -> int:
    """
    Small command-line interface.

    Expected syntax:

        python script.py VALUE SOURCE_BASE TARGET_BASE

    Example:

        python script.py 101101 2 16

    The main educational demonstrations run by default. This function
    exists as a reusable production-style interface.
    """
    if arguments is None:
        arguments = sys.argv[1:]

    if len(arguments) != 3:
        return 0

    number, source_base_text, target_base_text = arguments

    try:
        source_base = int(source_base_text)
        target_base = int(target_base_text)

        result = convert_integer(number, source_base, target_base)

        print(
            f"({number}) base {source_base} = "
            f"({result}) base {target_base}"
        )

        return 0

    except (TypeError, ValueError) as error:
        print(f"Conversion error: {error}", file=sys.stderr)
        return 1


# This interface is intentionally not executed automatically because this
# script is primarily designed as a study file containing many demonstrations.
#
# To use it from a separate entry point:
#
#     command_line_converter(["101101", "2", "16"])


# ============================================================================
# 48. SECURITY AND VALIDATION CONSIDERATIONS
# ============================================================================

"""
Number conversion appears simple, but input validation matters in software.

Important practices:

1. Never assume external input is valid.
2. Validate the base before interpreting digits.
3. Reject digits outside the target base.
4. Reject malformed prefixes.
5. Define whether signs are supported.
6. Define whether whitespace is accepted.
7. Define whether fractions are supported.
8. Define maximum input length where denial-of-service resistance matters.
9. Avoid evaluating arbitrary expressions merely to parse a number.
10. Be explicit about signed versus unsigned interpretation.

For example, converting user input using int(value, 2) is safe as parsing
a numeric string, while evaluating user-supplied text as Python code is
an entirely different operation and should not be used for conversion.
"""


# ============================================================================
# 49. LARGE INTEGER EXAMPLE
# ============================================================================

"""
Python integers have arbitrary precision, subject to practical memory
and computation limits.

The algorithms therefore work for values much larger than standard
32-bit or 64-bit machine integers.
"""


large_number = 2 ** 200 + 123456789

large_binary = decimal_to_base(large_number, 2)
large_hexadecimal = decimal_to_base(large_number, 16)

print("\nLARGE INTEGER")
print("Decimal digits :", len(str(large_number)))
print("Binary digits  :", len(large_binary))
print("Hex digits     :", len(large_hexadecimal))
print("Hex preview    :", large_hexadecimal[:32] + "...")


# ============================================================================
# 50. MACHINE-WORD LIMITS
# ============================================================================

def unsigned_range(bits: int) -> tuple[int, int]:
    """Return the inclusive range for an unsigned integer of a given width."""
    if not isinstance(bits, int) or bits <= 0:
        raise ValueError("bits must be a positive integer.")

    return 0, (2 ** bits) - 1


def signed_twos_complement_range(bits: int) -> tuple[int, int]:
    """Return the range of a signed two's-complement integer."""
    if not isinstance(bits, int) or bits <= 0:
        raise ValueError("bits must be a positive integer.")

    return -(2 ** (bits - 1)), (2 ** (bits - 1)) - 1


print("\nMACHINE-WORD RANGES")
for bits in [4, 8, 16, 32, 64]:
    print(
        f"{bits:>2}-bit unsigned: {unsigned_range(bits)} | "
        f"signed two's complement: {signed_twos_complement_range(bits)}"
    )


# ============================================================================
# 51. CONVERSION CHEAT SHEET
# ============================================================================

"""
CHEAT SHEET

DECIMAL -> BINARY
    Repeatedly divide by 2.
    Read remainders from bottom to top.

BINARY -> DECIMAL
    Multiply each digit by its corresponding power of 2 and add.
    Alternative: Horner's method.

DECIMAL -> OCTAL
    Repeatedly divide by 8.
    Read remainders upward.

OCTAL -> DECIMAL
    Multiply digits by powers of 8 and add.

DECIMAL -> HEXADECIMAL
    Repeatedly divide by 16.
    Read remainders upward.

HEXADECIMAL -> DECIMAL
    Multiply digits by powers of 16 and add.

BINARY -> OCTAL
    Group from the right into 3 bits.

OCTAL -> BINARY
    Replace each octal digit with 3 binary bits.

BINARY -> HEXADECIMAL
    Group from the right into 4 bits.

HEXADECIMAL -> BINARY
    Replace each hex digit with 4 binary bits.

OCTAL <-> HEXADECIMAL
    Convert through binary.

POWER-OF-TWO BASE RULE
    Base = 2^k means one base digit corresponds to k binary bits.

COMMON HEX DIGITS
    A=10, B=11, C=12, D=13, E=14, F=15.

COMMON PYTHON PREFIXES
    0b -> binary
    0o -> octal
    0x -> hexadecimal
"""


# ============================================================================
# 52. FINAL INTEGRATION DEMONSTRATION
# ============================================================================

def demonstrate_complete_conversion(number: int) -> None:
    """
    Show one integer through all major conversion paths.
    """
    representations = represent_number(number)

    print("\n" + "=" * 78)
    print(f"COMPLETE CONVERSION DEMONSTRATION FOR {number}")
    print("=" * 78)

    print(f"Decimal     : {representations.decimal}")
    print(f"Binary      : {representations.binary}")
    print(f"Octal       : {representations.octal}")
    print(f"Hexadecimal : {representations.hexadecimal}")

    print("\nReverse verification:")
    print(
        f"Binary -> decimal: "
        f"{binary_to_decimal_horner(representations.binary)}"
    )
    print(
        f"Octal -> decimal: "
        f"{octal_to_decimal(representations.octal)}"
    )
    print(
        f"Hex -> decimal: "
        f"{hexadecimal_to_decimal(representations.hexadecimal)}"
    )

    print("\nShortcut verification:")
    print(
        f"Binary -> octal: "
        f"{binary_to_octal(representations.binary)}"
    )
    print(
        f"Binary -> hex: "
        f"{binary_to_hexadecimal(representations.binary)}"
    )


demonstrate_complete_conversion(687)


# ============================================================================
# 53. EDUCATIONAL SELF-CHECKS
# ============================================================================

def self_check() -> None:
    """
    Final assertions ensure that the major relationships demonstrated
    throughout the script remain internally consistent.
    """
    assert decimal_to_binary_division(45) == "101101"
    assert binary_to_decimal_positional("101101") == 45

    assert decimal_to_octal(45) == "55"
    assert octal_to_decimal("55") == 45

    assert decimal_to_hexadecimal(45) == "2D"
    assert hexadecimal_to_decimal("2D") == 45

    assert binary_to_octal("101101") == "55"
    assert binary_to_hexadecimal("101101") == "2D"

    assert octal_to_hexadecimal("55") == "2D"
    assert hexadecimal_to_octal("2D") == "55"

    assert convert_integer("101101", 2, 16) == "2D"
    assert convert_integer("2D", 16, 2) == "101101"

    assert base_fraction_to_decimal("0.101", 2) == 0.625

    assert signed_to_twos_complement(-1, 8) == "11111111"
    assert twos_complement_to_signed("11111111") == -1

    print("\nFinal self-checks: PASSED")


self_check()

print("\n" + "=" * 78)
print("END OF NUMBER SYSTEM CONVERSION STUDY SCRIPT")
print("=" * 78)
