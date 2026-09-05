"""
Binary Number System
====================

A comprehensive, self-contained study script covering:

1. Number systems and positional notation
2. Binary digits and place values
3. Decimal-to-binary conversion
4. Binary-to-decimal conversion
5. Conversion between binary, octal, hexadecimal, and decimal
6. Binary arithmetic
7. Signed binary integers
8. One's complement and two's complement
9. Binary fractions
10. Floating-point concepts
11. Bitwise operations
12. Bit manipulation techniques
13. Overflow and underflow
14. Binary representation in real computers
15. Common mistakes, debugging, performance, and security considerations

Only Python's standard library is used.
"""

from decimal import Decimal, getcontext
from fractions import Fraction


# ============================================================================
# 1. FUNDAMENTALS: NUMBER SYSTEMS AND POSITIONAL NOTATION
# ============================================================================

print("=" * 80)
print("1. NUMBER SYSTEM FUNDAMENTALS")
print("=" * 80)

# A number system has a base (radix).
#
# Decimal: base 10 -> digits 0 through 9
# Binary:  base 2  -> digits 0 and 1
# Octal:   base 8  -> digits 0 through 7
# Hex:     base 16 -> digits 0 through 9 and A through F


def positional_value(digits, base):
    """
    Calculate the decimal value of a sequence of digits in a positional system.

    Example:
        [1, 0, 1, 1] in base 2
        = 1*2^3 + 0*2^2 + 1*2^1 + 1*2^0
        = 11
    """
    value = 0

    for digit in digits:
        if digit < 0 or digit >= base:
            raise ValueError(f"Digit {digit} is invalid for base {base}.")
        value = value * base + digit

    return value


print("1011₂ =", positional_value([1, 0, 1, 1], 2), "in decimal")
print("123₄ =", positional_value([1, 2, 3], 4), "in decimal")


# ============================================================================
# 2. BINARY PLACE VALUES
# ============================================================================

print("\n" + "=" * 80)
print("2. BINARY PLACE VALUES")
print("=" * 80)

binary_number = "101101"

print(f"Binary number: {binary_number}")

for position, bit in enumerate(reversed(binary_number)):
    contribution = int(bit) * (2 ** position)
    print(f"Bit {bit} at position {position}: {bit} × 2^{position} = {contribution}")

print(f"{binary_number}₂ = {int(binary_number, 2)}₁₀")


# ============================================================================
# 3. VALIDATING BINARY STRINGS
# ============================================================================

print("\n" + "=" * 80)
print("3. BINARY VALIDATION")
print("=" * 80)


def validate_binary(binary_string, allow_fraction=True):
    """
    Validate a binary number represented as a string.

    Valid examples:
        101
        0
        -1101
        101.01
        -0.101

    Invalid examples:
        102
        10A1
        1.0.1
        empty string
    """
    if not isinstance(binary_string, str):
        raise TypeError("Binary input must be a string.")

    binary_string = binary_string.strip()

    if not binary_string:
        raise ValueError("Binary input cannot be empty.")

    if binary_string[0] in "+-":
        binary_string = binary_string[1:]

    if not binary_string:
        raise ValueError("A sign must be followed by binary digits.")

    if binary_string.count(".") > 1:
        raise ValueError("A binary number can contain at most one decimal point.")

    if "." in binary_string:
        if not allow_fraction:
            raise ValueError("Binary fractions are not allowed.")

        integer_part, fractional_part = binary_string.split(".")

        if not integer_part and not fractional_part:
            raise ValueError("Binary number must contain at least one digit.")

        digits = integer_part + fractional_part
    else:
        digits = binary_string

    if not digits:
        raise ValueError("Binary number must contain digits.")

    invalid_digits = set(digits) - {"0", "1"}

    if invalid_digits:
        raise ValueError(
            f"Invalid binary digit(s): {sorted(invalid_digits)}. "
            "Binary numbers contain only 0 and 1."
        )

    return True


validation_examples = ["10101", "-110", "101.101", "102", "10.1.0"]

for example in validation_examples:
    try:
        validate_binary(example)
        print(f"{example!r} is valid.")
    except (TypeError, ValueError) as error:
        print(f"{example!r} is invalid: {error}")


# ============================================================================
# 4. BINARY TO DECIMAL CONVERSION
# ============================================================================

print("\n" + "=" * 80)
print("4. BINARY TO DECIMAL CONVERSION")
print("=" * 80)


def binary_to_decimal(binary_string):
    """
    Convert a binary integer or binary fraction to Decimal.

    Decimal is used to reduce the effects of ordinary binary floating-point
    representation when displaying the result.
    """
    validate_binary(binary_string)

    text = binary_string.strip()
    sign = 1

    if text.startswith("-"):
        sign = -1
        text = text[1:]
    elif text.startswith("+"):
        text = text[1:]

    if "." in text:
        integer_part, fractional_part = text.split(".")
    else:
        integer_part, fractional_part = text, ""

    integer_value = 0

    for bit in integer_part:
        integer_value = integer_value * 2 + int(bit)

    fractional_value = Decimal(0)

    for index, bit in enumerate(fractional_part, start=1):
        if bit == "1":
            fractional_value += Decimal(1) / (Decimal(2) ** index)

    return sign * (Decimal(integer_value) + fractional_value)


for example in ["1011", "110010", "101.101", "-11.01"]:
    print(f"{example}₂ = {binary_to_decimal(example)}₁₀")


# ============================================================================
# 5. DECIMAL INTEGER TO BINARY
# ============================================================================

print("\n" + "=" * 80)
print("5. DECIMAL INTEGER TO BINARY")
print("=" * 80)


def decimal_integer_to_binary(number):
    """
    Convert an integer to binary using repeated division by 2.

    Example for 13:

        13 / 2 -> remainder 1
         6 / 2 -> remainder 0
         3 / 2 -> remainder 1
         1 / 2 -> remainder 1

    Reading remainders from bottom to top gives 1101.
    """
    if not isinstance(number, int):
        raise TypeError("This function requires an integer.")

    if number == 0:
        return "0"

    sign = "-" if number < 0 else ""
    number = abs(number)

    digits = []

    while number > 0:
        remainder = number % 2
        digits.append(str(remainder))
        number //= 2

    return sign + "".join(reversed(digits))


for value in [0, 1, 2, 5, 13, 255, -42]:
    print(f"{value}₁₀ = {decimal_integer_to_binary(value)}₂")


# ============================================================================
# 6. USING PYTHON'S BUILT-IN CONVERSION FACILITIES
# ============================================================================

print("\n" + "=" * 80)
print("6. PYTHON BUILT-IN CONVERSION")
print("=" * 80)

number = 42

print("Decimal:", number)
print("Binary using bin():", bin(number))
print("Binary without prefix:", format(number, "b"))
print("8-bit binary:", format(number, "08b"))
print("16-bit binary:", format(number, "016b"))

binary_text = "101010"
print(f"int({binary_text!r}, 2) =", int(binary_text, 2))


# ============================================================================
# 7. DECIMAL FRACTIONS TO BINARY
# ============================================================================

print("\n" + "=" * 80)
print("7. DECIMAL FRACTIONS TO BINARY")
print("=" * 80)


def decimal_fraction_to_binary(value, precision=20):
    """
    Convert a decimal value to binary.

    Integer part:
        Convert using repeated division.

    Fractional part:
        Repeatedly multiply by 2.
        Each resulting integer part becomes the next binary digit.

    A finite decimal fraction may have an infinite binary representation.

    Example:
        0.625 × 2 = 1.25 -> digit 1
        0.25  × 2 = 0.5  -> digit 0
        0.5   × 2 = 1.0  -> digit 1

        Therefore: 0.625 = 0.101₂
    """
    if precision < 0:
        raise ValueError("Precision must be non-negative.")

    getcontext().prec = max(precision * 3 + 20, 50)

    value = Decimal(str(value))

    if value == 0:
        return "0"

    sign = "-" if value < 0 else ""
    value = abs(value)

    integer_part = int(value)
    fractional_part = value - Decimal(integer_part)

    integer_binary = decimal_integer_to_binary(integer_part)

    if fractional_part == 0 or precision == 0:
        return sign + integer_binary

    fractional_digits = []

    for _ in range(precision):
        fractional_part *= 2

        if fractional_part >= 1:
            fractional_digits.append("1")
            fractional_part -= 1
        else:
            fractional_digits.append("0")

        if fractional_part == 0:
            break

    return sign + integer_binary + "." + "".join(fractional_digits)


for value in ["0.5", "0.625", "10.25", "0.1"]:
    print(f"{value}₁₀ ≈ {decimal_fraction_to_binary(value, precision=24)}₂")

print("\nImportant:")
print("0.1 has a finite decimal representation but an infinite repeating binary representation.")


# ============================================================================
# 8. BINARY FRACTIONS USING EXACT RATIONAL NUMBERS
# ============================================================================

print("\n" + "=" * 80)
print("8. EXACT BINARY FRACTIONS")
print("=" * 80)


def binary_fraction_to_fraction(binary_string):
    """
    Convert a binary fraction into an exact Fraction object.
    """
    validate_binary(binary_string)

    text = binary_string.strip()
    sign = -1 if text.startswith("-") else 1

    if text[0] in "+-":
        text = text[1:]

    if "." in text:
        integer_part, fractional_part = text.split(".")
    else:
        integer_part, fractional_part = text, ""

    numerator = int(integer_part or "0", 2)

    fraction = Fraction(numerator, 1)

    for index, bit in enumerate(fractional_part, start=1):
        if bit == "1":
            fraction += Fraction(1, 2 ** index)

    return sign * fraction


for example in ["0.1", "0.01", "0.101", "11.11"]:
    exact_value = binary_fraction_to_fraction(example)
    print(f"{example}₂ = {exact_value} = {float(exact_value)}₁₀")


# ============================================================================
# 9. BINARY ADDITION
# ============================================================================

print("\n" + "=" * 80)
print("9. BINARY ADDITION")
print("=" * 80)

# Binary addition rules:
#
# 0 + 0 = 0
# 0 + 1 = 1
# 1 + 0 = 1
# 1 + 1 = 10  -> write 0, carry 1
# 1 + 1 + 1 = 11 -> write 1, carry 1


def binary_add(left, right):
    """
    Add two non-negative binary integers manually.
    """
    validate_binary(left, allow_fraction=False)
    validate_binary(right, allow_fraction=False)

    if left.startswith("-") or right.startswith("-"):
        raise ValueError("This manual demonstration accepts non-negative integers.")

    left = left.lstrip("0") or "0"
    right = right.lstrip("0") or "0"

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


addition_examples = [
    ("0", "0"),
    ("1", "1"),
    ("101", "11"),
    ("1111", "1"),
]

for left, right in addition_examples:
    print(f"{left} + {right} = {binary_add(left, right)}")


# ============================================================================
# 10. BINARY SUBTRACTION
# ============================================================================

print("\n" + "=" * 80)
print("10. BINARY SUBTRACTION")
print("=" * 80)

# Fundamental rules:
#
# 0 - 0 = 0
# 1 - 0 = 1
# 1 - 1 = 0
# 0 - 1 requires borrowing.
#
# Borrowing in binary gives:
# 10₂ - 1₂ = 1₂


def binary_subtract_nonnegative(left, right):
    """
    Subtract right from left using binary digit operations.

    The result is returned as a signed binary string.
    """
    validate_binary(left, allow_fraction=False)
    validate_binary(right, allow_fraction=False)

    if left.startswith("-") or right.startswith("-"):
        raise ValueError("Only non-negative binary inputs are accepted.")

    left_value = int(left, 2)
    right_value = int(right, 2)

    sign = ""

    if left_value < right_value:
        left_value, right_value = right_value, left_value
        sign = "-"

    result = []

    while left_value > 0 or right_value > 0:
        left_bit = left_value & 1
        right_bit = right_value & 1

        result.append(str(left_bit ^ right_bit))

        # Borrow is handled by integer arithmetic in this compact implementation.
        left_value >>= 1
        right_value >>= 1

    # The arithmetic implementation below gives the correct result directly.
    magnitude = abs(int(left, 2) - int(right, 2))

    return sign + format(magnitude, "b")


for left, right in [("1010", "11"), ("1000", "1"), ("10", "101")]:
    print(f"{left} - {right} = {binary_subtract_nonnegative(left, right)}")


# ============================================================================
# 11. BINARY MULTIPLICATION
# ============================================================================

print("\n" + "=" * 80)
print("11. BINARY MULTIPLICATION")
print("=" * 80)

# Binary multiplication is simpler than decimal multiplication because each
# multiplier digit is either 0 or 1.
#
# Multiplying by:
#   0 -> produces 0
#   1 -> copies the multiplicand
#
# Each position represents a power-of-two shift.


def binary_multiply(left, right):
    """
    Multiply two non-negative binary integers using shift-and-add logic.
    """
    validate_binary(left, allow_fraction=False)
    validate_binary(right, allow_fraction=False)

    if left.startswith("-") or right.startswith("-"):
        raise ValueError("Only non-negative binary inputs are accepted.")

    multiplicand = int(left, 2)
    multiplier = int(right, 2)
    result = 0

    while multiplier > 0:
        if multiplier & 1:
            result += multiplicand

        multiplicand <<= 1
        multiplier >>= 1

    return format(result, "b")


print("101 × 11 =", binary_multiply("101", "11"))
print("111 × 101 =", binary_multiply("111", "101"))


# ============================================================================
# 12. BINARY DIVISION
# ============================================================================

print("\n" + "=" * 80)
print("12. BINARY DIVISION")
print("=" * 80)


def binary_divide(dividend, divisor):
    """
    Divide binary integers and return quotient and remainder.
    """
    validate_binary(dividend, allow_fraction=False)
    validate_binary(divisor, allow_fraction=False)

    if dividend.startswith("-") or divisor.startswith("-"):
        raise ValueError("Only non-negative binary inputs are accepted.")

    dividend_value = int(dividend, 2)
    divisor_value = int(divisor, 2)

    if divisor_value == 0:
        raise ZeroDivisionError("Division by zero is undefined.")

    quotient, remainder = divmod(dividend_value, divisor_value)

    return format(quotient, "b"), format(remainder, "b")


quotient, remainder = binary_divide("1101", "11")

print("1101₂ ÷ 11₂")
print("Quotient:", quotient)
print("Remainder:", remainder)


# ============================================================================
# 13. BITWISE OPERATIONS
# ============================================================================

print("\n" + "=" * 80)
print("13. BITWISE OPERATIONS")
print("=" * 80)

a = 0b1100
b = 0b1010

print("a =", format(a, "04b"))
print("b =", format(b, "04b"))
print("a AND b =", format(a & b, "04b"))
print("a OR  b =", format(a | b, "04b"))
print("a XOR b =", format(a ^ b, "04b"))
print("NOT a conceptually depends on a chosen bit width.")
print("a << 1 =", format(a << 1, "05b"))
print("a >> 1 =", format(a >> 1, "04b"))


# ============================================================================
# 14. BITWISE OPERATION DEFINITIONS
# ============================================================================

print("\n" + "=" * 80)
print("14. BITWISE OPERATION RULES")
print("=" * 80)

# AND:
# 0 & 0 = 0
# 0 & 1 = 0
# 1 & 0 = 0
# 1 & 1 = 1
#
# OR:
# 0 | 0 = 0
# 0 | 1 = 1
# 1 | 0 = 1
# 1 | 1 = 1
#
# XOR:
# 0 ^ 0 = 0
# 0 ^ 1 = 1
# 1 ^ 0 = 1
# 1 ^ 1 = 0

for x in [0, 1]:
    for y in [0, 1]:
        print(f"{x} AND {y} = {x & y}, OR = {x | y}, XOR = {x ^ y}")


# ============================================================================
# 15. BIT MASKING
# ============================================================================

print("\n" + "=" * 80)
print("15. BIT MASKING")
print("=" * 80)

permissions = 0b1101

READ = 0b0001
WRITE = 0b0010
EXECUTE = 0b0100
ADMIN = 0b1000


def has_permission(permission_set, permission):
    return (permission_set & permission) != 0


print("Permissions:", format(permissions, "04b"))
print("READ:", has_permission(permissions, READ))
print("WRITE:", has_permission(permissions, WRITE))
print("EXECUTE:", has_permission(permissions, EXECUTE))
print("ADMIN:", has_permission(permissions, ADMIN))

# Set a bit.
permissions |= WRITE
print("After enabling WRITE:", format(permissions, "04b"))

# Clear a bit.
permissions &= ~ADMIN
print("After disabling ADMIN:", format(permissions, "04b"))

# Toggle a bit.
permissions ^= EXECUTE
print("After toggling EXECUTE:", format(permissions, "04b"))


# ============================================================================
# 16. CHECKING, SETTING, CLEARING, AND TOGGLING A BIT
# ============================================================================

print("\n" + "=" * 80)
print("16. BASIC BIT MANIPULATION")
print("=" * 80)


def is_bit_set(number, position):
    return (number & (1 << position)) != 0


def set_bit(number, position):
    return number | (1 << position)


def clear_bit(number, position):
    return number & ~(1 << position)


def toggle_bit(number, position):
    return number ^ (1 << position)


value = 0b1010

print("Initial:", format(value, "04b"))
print("Bit 1 set?", is_bit_set(value, 1))
print("Set bit 0:", format(set_bit(value, 0), "04b"))
print("Clear bit 1:", format(clear_bit(value, 1), "04b"))
print("Toggle bit 2:", format(toggle_bit(value, 2), "04b"))


# ============================================================================
# 17. COUNTING SET BITS
# ============================================================================

print("\n" + "=" * 80)
print("17. COUNTING SET BITS")
print("=" * 80)


def count_set_bits_naive(number):
    """
    Count set bits by examining each binary digit.
    """
    if number < 0:
        raise ValueError("Use a fixed width when counting bits of negative numbers.")

    count = 0

    while number:
        count += number & 1
        number >>= 1

    return count


def count_set_bits_kernighan(number):
    """
    Brian Kernighan's algorithm.

    Each iteration removes the lowest set bit:
        n = n & (n - 1)

    Number of iterations equals the number of set bits.
    """
    if number < 0:
        raise ValueError("Use a fixed width for negative numbers.")

    count = 0

    while number:
        number &= number - 1
        count += 1

    return count


number = 0b10110100

print("Number:", format(number, "08b"))
print("Naive count:", count_set_bits_naive(number))
print("Kernighan count:", count_set_bits_kernighan(number))
print("Python bit_count():", number.bit_count())


# ============================================================================
# 18. SIGNED INTEGER REPRESENTATION
# ============================================================================

print("\n" + "=" * 80)
print("18. SIGNED INTEGER REPRESENTATION")
print("=" * 80)

# Three historically important approaches:
#
# 1. Sign-magnitude
# 2. One's complement
# 3. Two's complement
#
# Modern computers almost universally use two's complement for signed integers.


# ============================================================================
# 19. UNSIGNED INTEGER RANGE
# ============================================================================

print("\n" + "=" * 80)
print("19. UNSIGNED INTEGER RANGE")
print("=" * 80)


def unsigned_range(bits):
    if bits <= 0:
        raise ValueError("Bit width must be positive.")

    return 0, (2 ** bits) - 1


for bits in [4, 8, 16, 32]:
    minimum, maximum = unsigned_range(bits)
    print(f"{bits}-bit unsigned range: {minimum} to {maximum}")


# ============================================================================
# 20. TWO'S COMPLEMENT REPRESENTATION
# ============================================================================

print("\n" + "=" * 80)
print("20. TWO'S COMPLEMENT")
print("=" * 80)


def twos_complement_encode(number, bits):
    """
    Encode a signed integer using a fixed-width two's complement representation.
    """
    if bits <= 0:
        raise ValueError("Bit width must be positive.")

    minimum = -(2 ** (bits - 1))
    maximum = (2 ** (bits - 1)) - 1

    if not minimum <= number <= maximum:
        raise OverflowError(
            f"{number} cannot be represented in {bits}-bit two's complement."
        )

    if number < 0:
        number = (1 << bits) + number

    return format(number, f"0{bits}b")


def twos_complement_decode(binary_string):
    """
    Decode a fixed-width two's complement binary string.
    """
    validate_binary(binary_string, allow_fraction=False)

    if binary_string.startswith("-") or binary_string.startswith("+"):
        raise ValueError("Two's complement representation does not use a sign character.")

    bits = len(binary_string)
    value = int(binary_string, 2)

    if binary_string[0] == "1":
        value -= 1 << bits

    return value


for number in [-8, -5, -1, 0, 1, 7]:
    encoded = twos_complement_encode(number, 4)
    decoded = twos_complement_decode(encoded)
    print(f"{number:>3} -> {encoded} -> {decoded}")


# ============================================================================
# 21. MANUAL TWO'S COMPLEMENT NEGATION
# ============================================================================

print("\n" + "=" * 80)
print("21. TWO'S COMPLEMENT NEGATION")
print("=" * 80)


def twos_complement_negate(binary_string):
    """
    Negate a fixed-width binary value using:
        1. Bit inversion
        2. Add 1
    """
    validate_binary(binary_string, allow_fraction=False)

    if binary_string.startswith(("+", "-")):
        raise ValueError("Use an unsigned bit pattern without a sign.")

    bits = len(binary_string)
    value = int(binary_string, 2)

    inverted = (~value) & ((1 << bits) - 1)
    negated = (inverted + 1) & ((1 << bits) - 1)

    return format(negated, f"0{bits}b")


example = "00000101"
print("Original:", example)
print("Negated pattern:", twos_complement_negate(example))
print("Decoded:", twos_complement_decode(twos_complement_negate(example)))


# ============================================================================
# 22. SIGNED RANGE AND ASYMMETRY
# ============================================================================

print("\n" + "=" * 80)
print("22. SIGNED TWO'S COMPLEMENT RANGE")
print("=" * 80)


def signed_range(bits):
    if bits <= 0:
        raise ValueError("Bit width must be positive.")

    return -(2 ** (bits - 1)), (2 ** (bits - 1)) - 1


for bits in [4, 8, 16, 32]:
    minimum, maximum = signed_range(bits)
    print(f"{bits}-bit signed range: {minimum} to {maximum}")

print("\nNotice that the negative range contains one additional value.")
print("For 8 bits: -128 through +127.")


# ============================================================================
# 23. INTEGER OVERFLOW
# ============================================================================

print("\n" + "=" * 80)
print("23. FIXED-WIDTH INTEGER OVERFLOW")
print("=" * 80)


def unsigned_add_with_width(left, right, bits):
    """
    Demonstrate modular arithmetic used by fixed-width unsigned integers.
    """
    if bits <= 0:
        raise ValueError("Bit width must be positive.")

    mask = (1 << bits) - 1
    raw_sum = left + right
    wrapped_sum = raw_sum & mask
    overflow = raw_sum > mask

    return wrapped_sum, overflow


wrapped, overflow = unsigned_add_with_width(250, 10, 8)

print("250 + 10 in mathematical arithmetic =", 260)
print("250 + 10 in 8-bit unsigned arithmetic =", wrapped)
print("Overflow occurred?", overflow)

# Python integers do not normally overflow because Python integers have
# arbitrary precision, limited primarily by available memory.


# ============================================================================
# 24. CONVERSION BETWEEN BINARY AND OCTAL
# ============================================================================

print("\n" + "=" * 80)
print("24. BINARY AND OCTAL")
print("=" * 80)

# One octal digit represents exactly 3 binary bits because:
# 8 = 2^3


def binary_to_octal(binary_string):
    validate_binary(binary_string, allow_fraction=False)

    if binary_string.startswith(("+", "-")):
        raise ValueError("This demonstration accepts unsigned binary strings.")

    return format(int(binary_string, 2), "o")


def octal_to_binary(octal_string):
    value = int(octal_string, 8)
    return format(value, "b")


binary_example = "111101011"
octal_value = binary_to_octal(binary_example)

print(f"{binary_example}₂ = {octal_value}₈")
print(f"{octal_value}₈ = {octal_to_binary(octal_value)}₂")


# ============================================================================
# 25. CONVERSION BETWEEN BINARY AND HEXADECIMAL
# ============================================================================

print("\n" + "=" * 80)
print("25. BINARY AND HEXADECIMAL")
print("=" * 80)

# One hexadecimal digit represents exactly 4 binary bits because:
# 16 = 2^4


def binary_to_hex(binary_string):
    validate_binary(binary_string, allow_fraction=False)

    if binary_string.startswith(("+", "-")):
        raise ValueError("This demonstration accepts unsigned binary strings.")

    return format(int(binary_string, 2), "X")


def hex_to_binary(hex_string):
    value = int(hex_string, 16)
    return format(value, "b")


binary_example = "1101111010101101"
hex_value = binary_to_hex(binary_example)

print(f"{binary_example}₂ = {hex_value}₁₆")
print(f"{hex_value}₁₆ = {hex_to_binary(hex_value)}₂")


# ============================================================================
# 26. BINARY GROUPING
# ============================================================================

print("\n" + "=" * 80)
print("26. GROUPING BINARY DIGITS")
print("=" * 80)


def group_binary(binary_string, group_size):
    """
    Group a binary integer from right to left.

    Useful for octal (groups of 3) and hexadecimal (groups of 4).
    """
    validate_binary(binary_string, allow_fraction=False)

    if group_size <= 0:
        raise ValueError("Group size must be positive.")

    padding = (-len(binary_string)) % group_size
    padded = "0" * padding + binary_string

    return " ".join(
        padded[index:index + group_size]
        for index in range(0, len(padded), group_size)
    )


print("Binary:", "1101111010101101")
print("Groups of 3:", group_binary("1101111010101101", 3))
print("Groups of 4:", group_binary("1101111010101101", 4))


# ============================================================================
# 27. CHARACTER ENCODING AS BINARY
# ============================================================================

print("\n" + "=" * 80)
print("27. TEXT AND BINARY")
print("=" * 80)


def text_to_binary(text, encoding="utf-8"):
    """
    Convert text into its encoded byte representation.
    """
    return " ".join(format(byte, "08b") for byte in text.encode(encoding))


def binary_to_text(binary_text, encoding="utf-8"):
    """
    Convert space-separated 8-bit binary bytes back into text.
    """
    parts = binary_text.split()

    if any(len(part) != 8 for part in parts):
        raise ValueError("Each byte must contain exactly 8 binary digits.")

    for part in parts:
        validate_binary(part, allow_fraction=False)

    data = bytes(int(part, 2) for part in parts)

    return data.decode(encoding)


message = "Hi"
binary_message = text_to_binary(message)

print("Text:", message)
print("Binary bytes:", binary_message)
print("Decoded text:", binary_to_text(binary_message))


# ============================================================================
# 28. BYTES AND INTEGER CONVERSION
# ============================================================================

print("\n" + "=" * 80)
print("28. BYTES AND INTEGERS")
print("=" * 80)

number = 1025

big_endian = number.to_bytes(2, byteorder="big")
little_endian = number.to_bytes(2, byteorder="little")

print("Number:", number)
print("Big-endian bytes:", big_endian)
print("Little-endian bytes:", little_endian)

print(
    "Big-endian binary:",
    " ".join(format(byte, "08b") for byte in big_endian),
)

print(
    "Little-endian binary:",
    " ".join(format(byte, "08b") for byte in little_endian),
)


# ============================================================================
# 29. ENDIANNESS
# ============================================================================

print("\n" + "=" * 80)
print("29. ENDIANNESS")
print("=" * 80)

# Endianness concerns the order of bytes in multi-byte values.
#
# Big-endian:
#   Most significant byte first.
#
# Little-endian:
#   Least significant byte first.
#
# Bit order inside an individual byte should not be confused with byte order.


# ============================================================================
# 30. BINARY FRACTIONS AND POWERS OF TWO
# ============================================================================

print("\n" + "=" * 80)
print("30. BINARY FRACTION PLACE VALUES")
print("=" * 80)

# Positions to the right of the binary point represent:
#
# 2^-1 = 1/2
# 2^-2 = 1/4
# 2^-3 = 1/8
# 2^-4 = 1/16

fractional_example = "101.101"

print(f"{fractional_example}₂")
print("= 1×4 + 0×2 + 1×1 + 1×1/2 + 0×1/4 + 1×1/8")
print("=", binary_to_decimal(fractional_example))


# ============================================================================
# 31. TERMINATING AND REPEATING BINARY FRACTIONS
# ============================================================================

print("\n" + "=" * 80)
print("31. TERMINATING VS REPEATING BINARY FRACTIONS")
print("=" * 80)


def fraction_has_terminating_binary_representation(numerator, denominator):
    """
    A reduced rational number has a terminating binary representation only when
    its denominator contains no prime factors other than 2.
    """
    fraction = Fraction(numerator, denominator)
    denominator = fraction.denominator

    while denominator % 2 == 0:
        denominator //= 2

    return denominator == 1


examples = [
    (1, 2),
    (1, 4),
    (3, 8),
    (1, 10),
    (1, 3),
]

for numerator, denominator in examples:
    terminates = fraction_has_terminating_binary_representation(
        numerator,
        denominator,
    )
    print(
        f"{numerator}/{denominator}: "
        f"{'terminating' if terminates else 'repeating'} binary representation"
    )


# ============================================================================
# 32. FLOATING-POINT CONCEPTS
# ============================================================================

print("\n" + "=" * 80)
print("32. FLOATING-POINT CONCEPTS")
print("=" * 80)

# Binary floating-point values commonly store numbers conceptually using:
#
# sign × significand × 2^exponent
#
# IEEE 754 floating-point formats use fixed numbers of bits for these fields.
#
# Important consequences:
# - Many decimal fractions cannot be represented exactly.
# - Floating-point arithmetic can introduce rounding.
# - Equality comparisons may require tolerances.

value = 0.1 + 0.2

print("0.1 + 0.2 =", value)
print("0.1 + 0.2 == 0.3 ?", value == 0.3)


def approximately_equal(left, right, tolerance=1e-12):
    return abs(left - right) <= tolerance


print(
    "Approximately equal?",
    approximately_equal(0.1 + 0.2, 0.3),
)


# ============================================================================
# 33. FLOATING-POINT BIT REPRESENTATION
# ============================================================================

print("\n" + "=" * 80)
print("33. FLOATING-POINT BIT REPRESENTATION")
print("=" * 80)

import struct


def float_to_binary64(value):
    """
    Display a Python float as an IEEE 754 binary64 bit pattern.

    Most Python implementations use IEEE 754 double precision for float.
    """
    packed = struct.pack(">d", value)
    integer = int.from_bytes(packed, byteorder="big")
    return format(integer, "064b")


float_value = 13.25
float_bits = float_to_binary64(float_value)

print("Float:", float_value)
print("Binary64:", float_bits)
print("Sign bit:", float_bits[0])
print("Exponent bits:", float_bits[1:12])
print("Fraction bits:", float_bits[12:])


# ============================================================================
# 34. SHIFTING AND MULTIPLICATION BY POWERS OF TWO
# ============================================================================

print("\n" + "=" * 80)
print("34. BIT SHIFTS AND POWERS OF TWO")
print("=" * 80)

value = 13

print("Value:", value, "Binary:", format(value, "b"))
print("value << 1:", value << 1, "Binary:", format(value << 1, "b"))
print("value << 2:", value << 2, "Binary:", format(value << 2, "b"))
print("value >> 1:", value >> 1, "Binary:", format(value >> 1, "b"))

# For non-negative integers:
#
# n << k is equivalent to n × 2^k
# n >> k is equivalent to floor(n / 2^k)


# ============================================================================
# 35. POWER-OF-TWO TEST
# ============================================================================

print("\n" + "=" * 80)
print("35. TESTING WHETHER A NUMBER IS A POWER OF TWO")
print("=" * 80)


def is_power_of_two(number):
    """
    Positive powers of two have exactly one set bit.

    Example:
        8  = 1000
        16 = 10000

    n & (n - 1) removes the lowest set bit.
    """
    return number > 0 and (number & (number - 1)) == 0


for value in [0, 1, 2, 3, 4, 5, 8, 12, 16]:
    print(f"{value:>2}: {is_power_of_two(value)}")


# ============================================================================
# 36. EXTRACTING THE LOWEST SET BIT
# ============================================================================

print("\n" + "=" * 80)
print("36. LOWEST SET BIT")
print("=" * 80)


def lowest_set_bit(number):
    """
    Return a mask containing only the lowest set bit.

    For positive integers:
        n & -n
    """
    if number <= 0:
        raise ValueError("Number must be positive.")

    return number & -number


number = 0b1011000
lowest = lowest_set_bit(number)

print("Number:", format(number, "08b"))
print("Lowest set bit:", format(lowest, "08b"))


# ============================================================================
# 37. CLEARING THE LOWEST SET BIT
# ============================================================================

print("\n" + "=" * 80)
print("37. CLEARING THE LOWEST SET BIT")
print("=" * 80)

number = 0b10110100

print("Original:", format(number, "08b"))
print("After n & (n - 1):", format(number & (number - 1), "08b"))


# ============================================================================
# 38. PARITY
# ============================================================================

print("\n" + "=" * 80)
print("38. PARITY")
print("=" * 80)


def parity(number):
    """
    Return:
        0 for an even number of set bits
        1 for an odd number of set bits
    """
    if number < 0:
        raise ValueError("Use a fixed width for negative values.")

    result = 0

    while number:
        result ^= number & 1
        number >>= 1

    return result


for value in [0b0000, 0b0001, 0b0011, 0b0111, 0b1111]:
    print(f"{format(value, '04b')}: parity = {parity(value)}")


# ============================================================================
# 39. XOR PROPERTIES
# ============================================================================

print("\n" + "=" * 80)
print("39. XOR PROPERTIES")
print("=" * 80)

# Important identities:
#
# a XOR 0 = a
# a XOR a = 0
# a XOR b = b XOR a
#
# XOR can be used in reversible transformations.

secret = 0b10101100
key = 0b11001010

encrypted = secret ^ key
decrypted = encrypted ^ key

print("Secret:   ", format(secret, "08b"))
print("Key:      ", format(key, "08b"))
print("XOR value:", format(encrypted, "08b"))
print("Recovered:", format(decrypted, "08b"))

# XOR alone is not a secure encryption system unless used within a properly
# designed cryptographic scheme with strong key management.


# ============================================================================
# 40. FINDING A UNIQUE VALUE USING XOR
# ============================================================================

print("\n" + "=" * 80)
print("40. UNIQUE ELEMENT USING XOR")
print("=" * 80)


def find_unique_value(values):
    """
    Find the value that appears once when every other value appears exactly twice.
    """
    result = 0

    for value in values:
        result ^= value

    return result


values = [7, 3, 5, 3, 7]
print("Values:", values)
print("Unique value:", find_unique_value(values))


# ============================================================================
# 41. BINARY SEARCH AND THE BINARY SYSTEM
# ============================================================================

print("\n" + "=" * 80)
print("41. BINARY SEARCH")
print("=" * 80)


def binary_search(sorted_values, target):
    """
    Binary search repeatedly divides a sorted search space in half.

    Time complexity:
        O(log n)

    This algorithm is conceptually related to powers of two and repeated halving.
    """
    left = 0
    right = len(sorted_values) - 1

    while left <= right:
        middle = left + (right - left) // 2

        if sorted_values[middle] == target:
            return middle

        if sorted_values[middle] < target:
            left = middle + 1
        else:
            right = middle - 1

    return -1


data = [3, 7, 11, 18, 24, 31, 42, 56]

print("Data:", data)
print("Index of 31:", binary_search(data, 31))
print("Index of 100:", binary_search(data, 100))


# ============================================================================
# 42. BINARY DATA STORAGE
# ============================================================================

print("\n" + "=" * 80)
print("42. BINARY DATA STORAGE")
print("=" * 80)

# A bit is a binary digit.
#
# Common units:
#   1 bit  = one binary digit
#   8 bits = one byte
#
# Larger storage quantities are commonly expressed using decimal SI prefixes
# or binary IEC prefixes. These should not be confused.
#
# Example:
#   1 kB  = 1000 bytes
#   1 KiB = 1024 bytes


def bytes_to_bits(byte_count):
    return byte_count * 8


for byte_count in [1, 2, 16, 1024]:
    print(f"{byte_count} bytes = {bytes_to_bits(byte_count)} bits")


# ============================================================================
# 43. FIXED-WIDTH FORMATTING
# ============================================================================

print("\n" + "=" * 80)
print("43. FIXED-WIDTH BINARY")
print("=" * 80)


def format_unsigned_binary(number, bits):
    """
    Format a non-negative integer using exactly the requested number of bits.
    """
    if number < 0:
        raise ValueError("Number must be non-negative.")

    maximum = (1 << bits) - 1

    if number > maximum:
        raise OverflowError(
            f"{number} requires more than {bits} bits."
        )

    return format(number, f"0{bits}b")


for number in [0, 1, 15, 255]:
    print(f"{number} as 8 bits:", format_unsigned_binary(number, 8))


# ============================================================================
# 44. COMMON BINARY CONVERSION MISTAKES
# ============================================================================

print("\n" + "=" * 80)
print("44. COMMON MISTAKES")
print("=" * 80)

mistakes = [
    "Treating binary digits as decimal digits",
    "Forgetting that binary place values are powers of 2",
    "Reading repeated-division remainders in the wrong order",
    "Assuming every decimal fraction terminates in binary",
    "Ignoring fixed-width overflow",
    "Using Python's unlimited integers as a model of fixed-width hardware",
    "Confusing signed and unsigned interpretations",
    "Applying bitwise NOT without considering representation width",
    "Confusing byte order with bit order",
]

for index, mistake in enumerate(mistakes, start=1):
    print(f"{index}. {mistake}")


# ============================================================================
# 45. NEGATIVE NUMBERS AND PYTHON BITWISE OPERATIONS
# ============================================================================

print("\n" + "=" * 80)
print("45. NEGATIVE NUMBERS IN PYTHON")
print("=" * 80)

# Python integers have arbitrary precision. Bitwise operations involving
# negative numbers behave conceptually like infinite-width two's complement.
#
# Therefore:
#     ~n == -n - 1

for number in [0, 1, 5, -1, -5]:
    print(f"~({number}) = {~number}, and -n-1 = {-number - 1}")


# ============================================================================
# 46. MASKING TO SIMULATE FIXED-WIDTH HARDWARE
# ============================================================================

print("\n" + "=" * 80)
print("46. SIMULATING FIXED-WIDTH VALUES")
print("=" * 80)


def to_unsigned_width(number, bits):
    """
    Restrict an integer to a fixed number of low-order bits.
    """
    if bits <= 0:
        raise ValueError("Bit width must be positive.")

    mask = (1 << bits) - 1
    return number & mask


for number in [-1, -2, 255, 256, 300]:
    print(
        f"{number:>4} as 8-bit unsigned:",
        format(to_unsigned_width(number, 8), "08b"),
    )


# ============================================================================
# 47. SIGN EXTENSION
# ============================================================================

print("\n" + "=" * 80)
print("47. SIGN EXTENSION")
print("=" * 80)


def sign_extend(binary_string, new_width):
    """
    Extend a two's complement binary representation while preserving its value.
    """
    validate_binary(binary_string, allow_fraction=False)

    current_width = len(binary_string)

    if new_width < current_width:
        raise ValueError("New width must be greater than or equal to current width.")

    sign_bit = binary_string[0]

    return sign_bit * (new_width - current_width) + binary_string


negative_five_4bit = twos_complement_encode(-5, 4)

print("-5 in 4 bits:", negative_five_4bit)
print("-5 extended to 8 bits:", sign_extend(negative_five_4bit, 8))
print(
    "Decoded:",
    twos_complement_decode(sign_extend(negative_five_4bit, 8)),
)


# ============================================================================
# 48. BINARY SERIALIZATION
# ============================================================================

print("\n" + "=" * 80)
print("48. BINARY SERIALIZATION")
print("=" * 80)


def serialize_uint16(number, byteorder="big"):
    """
    Serialize an unsigned 16-bit integer.
    """
    if not 0 <= number <= 65535:
        raise OverflowError("Value must fit in an unsigned 16-bit integer.")

    return number.to_bytes(2, byteorder=byteorder)


def deserialize_uint16(data, byteorder="big"):
    """
    Deserialize exactly two bytes into an unsigned 16-bit integer.
    """
    if len(data) != 2:
        raise ValueError("Exactly 2 bytes are required.")

    return int.from_bytes(data, byteorder=byteorder)


serialized = serialize_uint16(50000, "big")

print("Serialized bytes:", serialized)
print("Deserialized value:", deserialize_uint16(serialized, "big"))


# ============================================================================
# 49. PERFORMANCE CONSIDERATIONS
# ============================================================================

print("\n" + "=" * 80)
print("49. PERFORMANCE CONSIDERATIONS")
print("=" * 80)

# Bitwise operations are often efficient because hardware directly operates
# on binary data.
#
# Typical uses include:
# - Flags
# - Permissions
# - Compact state representation
# - Hashing algorithms
# - Compression
# - Network protocols
# - Cryptographic primitives
#
# Performance still depends on:
# - Algorithmic complexity
# - CPU architecture
# - Compiler/runtime behavior
# - Memory access patterns
# - Integer size


# ============================================================================
# 50. SECURITY CONSIDERATIONS
# ============================================================================

print("\n" + "=" * 80)
print("50. SECURITY CONSIDERATIONS")
print("=" * 80)

# Binary processing is common in security-sensitive systems.
#
# Important concerns:
#
# 1. Integer overflow:
#    Fixed-width arithmetic can wrap unexpectedly in lower-level languages.
#
# 2. Signed/unsigned conversion:
#    Incorrect interpretation can create validation vulnerabilities.
#
# 3. Bit masks:
#    Incorrect masks can accidentally grant or remove permissions.
#
# 4. Serialization:
#    Validate lengths, ranges, byte order, and input format.
#
# 5. Cryptography:
#    XOR and bit operations are primitives, not automatically secure encryption.
#
# 6. Floating-point:
#    Avoid using approximate floating-point arithmetic for exact security checks.


# ============================================================================
# 51. PRACTICAL EXAMPLE: COMPACT FLAGS
# ============================================================================

print("\n" + "=" * 80)
print("51. PRACTICAL EXAMPLE: COMPACT FEATURE FLAGS")
print("=" * 80)


class FeatureFlags:
    """
    Store multiple Boolean states inside one integer.

    Each feature occupies one bit.
    """

    DARK_MODE = 1 << 0
    EMAIL_ALERTS = 1 << 1
    TWO_FACTOR_AUTH = 1 << 2
    BETA_ACCESS = 1 << 3

    def __init__(self, flags=0):
        self.flags = flags

    def enable(self, feature):
        self.flags |= feature

    def disable(self, feature):
        self.flags &= ~feature

    def enabled(self, feature):
        return bool(self.flags & feature)

    def display(self):
        return format(self.flags, "08b")


features = FeatureFlags()

features.enable(FeatureFlags.DARK_MODE)
features.enable(FeatureFlags.TWO_FACTOR_AUTH)

print("Flags:", features.display())
print("Dark mode:", features.enabled(FeatureFlags.DARK_MODE))
print("Email alerts:", features.enabled(FeatureFlags.EMAIL_ALERTS))
print("Two-factor:", features.enabled(FeatureFlags.TWO_FACTOR_AUTH))


# ============================================================================
# 52. PRACTICAL EXAMPLE: BINARY PACKING
# ============================================================================

print("\n" + "=" * 80)
print("52. PRACTICAL EXAMPLE: PACKING SMALL VALUES")
print("=" * 80)


def pack_two_nibbles(high, low):
    """
    Pack two 4-bit values into one byte.
    """
    if not 0 <= high <= 15:
        raise ValueError("High value must fit in 4 bits.")

    if not 0 <= low <= 15:
        raise ValueError("Low value must fit in 4 bits.")

    return (high << 4) | low


def unpack_two_nibbles(value):
    """
    Extract two 4-bit values from one byte.
    """
    if not 0 <= value <= 255:
        raise ValueError("Value must fit in one byte.")

    high = (value >> 4) & 0b1111
    low = value & 0b1111

    return high, low


packed = pack_two_nibbles(10, 5)

print("Packed byte:", format(packed, "08b"))
print("Unpacked:", unpack_two_nibbles(packed))


# ============================================================================
# 53. TESTING CONVERSION FUNCTIONS
# ============================================================================

print("\n" + "=" * 80)
print("53. TESTING")
print("=" * 80)


def run_tests():
    """
    Small self-contained test suite using assertions.
    """
    assert decimal_integer_to_binary(0) == "0"
    assert decimal_integer_to_binary(13) == "1101"
    assert decimal_integer_to_binary(-13) == "-1101"

    assert binary_to_decimal("1101") == Decimal(13)
    assert binary_to_decimal("0.101") == Decimal("0.625")

    assert binary_add("101", "11") == "1000"
    assert binary_multiply("101", "11") == "1111"

    quotient, remainder = binary_divide("1101", "11")
    assert quotient == "100"
    assert remainder == "1"

    assert twos_complement_encode(-1, 8) == "11111111"
    assert twos_complement_decode("11111111") == -1
    assert twos_complement_decode("01111111") == 127

    assert is_power_of_two(1)
    assert is_power_of_two(1024)
    assert not is_power_of_two(0)
    assert not is_power_of_two(12)

    assert count_set_bits_kernighan(0b1011) == 3
    assert find_unique_value([4, 2, 4, 7, 2]) == 7

    assert pack_two_nibbles(10, 5) == 0b10100101
    assert unpack_two_nibbles(0b10100101) == (10, 5)

    print("All tests passed successfully.")


run_tests()


# ============================================================================
# 54. FINAL INTEGRATED DEMONSTRATION
# ============================================================================

print("\n" + "=" * 80)
print("54. INTEGRATED DEMONSTRATION")
print("=" * 80)


def demonstrate_binary_number(number):
    """
    Display several representations and binary properties of an integer.
    """
    if not isinstance(number, int):
        raise TypeError("Input must be an integer.")

    print(f"\nDecimal number: {number}")
    print(f"Binary:         {format(number, 'b')}")
    print(f"Octal:          {format(number, 'o')}")
    print(f"Hexadecimal:    {format(number, 'X')}")

    if number >= 0:
        print(f"Set bits:       {number.bit_count()}")
        print(f"Power of two:   {is_power_of_two(number)}")

    if -128 <= number <= 127:
        encoded = twos_complement_encode(number, 8)
        print(f"8-bit signed:   {encoded}")
        print(f"Decoded value:  {twos_complement_decode(encoded)}")

    if 0 <= number <= 255:
        print(f"8-bit unsigned: {format_unsigned_binary(number, 8)}")


for number in [-42, -1, 0, 5, 42, 127]:
    demonstrate_binary_number(number)


print("\n" + "=" * 80)
print("END OF BINARY NUMBER SYSTEM STUDY SCRIPT")
print("=" * 80)
