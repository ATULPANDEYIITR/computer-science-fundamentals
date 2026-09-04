# NUMBER SYSTEMS INTRODUCTION
# Decimal System, Binary System, Octal System, Hexadecimal System, and Positional Notation

# ============================================================
# PART 1: PYTHON TEACHING SCRIPT
# ============================================================

"""
NUMBER SYSTEMS

This program is designed as a complete practical study of number systems.

It covers:

1. What a number system is
2. Base and radix
3. Decimal number system
4. Binary number system
5. Octal number system
6. Hexadecimal number system
7. Positional notation
8. Place values
9. Converting numbers between bases
10. Fractional numbers
11. Binary, octal, and hexadecimal relationships
12. Bits, nibbles, and bytes
13. Fixed-width representations
14. Overflow
15. Powers of two
16. Binary arithmetic
17. Bitwise operations
18. Bit masks
19. Python's built-in number-system functions
20. General base-N representation
21. Representation versus value
22. Finite and repeating fractions
23. Common mistakes
24. Verification techniques

The script intentionally uses ordinary Python constructs so that each
concept can be observed directly rather than being hidden behind a
special-purpose library.
"""

# ============================================================
# 1. WHAT IS A NUMBER SYSTEM?
# ============================================================

print("=" * 70)
print("NUMBER SYSTEMS")
print("=" * 70)

print("""
A number system is a method of representing numerical values using
a defined collection of symbols and rules.

The most familiar system is decimal.

Computers primarily use binary.

Octal and hexadecimal are compact ways of writing binary values.

The important idea is that the same numerical value can have different
representations depending on the base being used.
""")

print("The value 10 can be represented as:")
print("Decimal :", 10)
print("Binary  :", bin(10))
print("Octal   :", oct(10))
print("Hex     :", hex(10))

# The value has not changed.
# Only its representation has changed.

# ============================================================
# 2. BASE OR RADIX
# ============================================================

print("\n" + "=" * 70)
print("BASE / RADIX")
print("=" * 70)

print("""
The base of a number system tells us how many different digit symbols
are available before another positional place is required.

Decimal has base 10.
Binary has base 2.
Octal has base 8.
Hexadecimal has base 16.
""")

bases = {
    "Decimal": 10,
    "Binary": 2,
    "Octal": 8,
    "Hexadecimal": 16
}

for name, base in bases.items():
    print(f"{name:12} -> base {base}")

print("""
For a base b:

Valid digits range from 0 through b - 1.

Therefore:

Base 2  -> 0, 1
Base 8  -> 0 through 7
Base 10 -> 0 through 9
Base 16 -> 0 through 9 and A through F
""")

# ============================================================
# 3. DECIMAL NUMBER SYSTEM
# ============================================================

print("\n" + "=" * 70)
print("DECIMAL NUMBER SYSTEM")
print("=" * 70)

print("""
Decimal is a positional number system with base 10.

Its symbols are:

0 1 2 3 4 5 6 7 8 9

Consider:

5832

Each digit has a different positional weight.
""")

number = 5832

print("Number:", number)
print("8 is in the hundreds position.")
print("3 is in the tens position.")
print("2 is in the ones position.")

print("""
5832 can be expanded as:

5 × 10^3
+ 8 × 10^2
+ 3 × 10^1
+ 2 × 10^0

= 5000 + 800 + 30 + 2
= 5832
""")

decimal_expansion = (
    5 * 10**3
    + 8 * 10**2
    + 3 * 10**1
    + 2 * 10**0
)

print("Python calculation:", decimal_expansion)

# ============================================================
# 4. POSITIONAL NOTATION
# ============================================================

print("\n" + "=" * 70)
print("POSITIONAL NOTATION")
print("=" * 70)

print("""
The general positional notation formula is:

Value = Σ(dᵢ × bⁱ)

where:

dᵢ = digit at position i
b   = base
i   = positional exponent

The rightmost integer digit has exponent 0.

Moving left increases the exponent:

..., b^3, b^2, b^1, b^0

For fractional positions, exponents become negative:

b^-1, b^-2, b^-3, ...
""")

print("""
For decimal 472:

4 × 10² + 7 × 10¹ + 2 × 10⁰
= 400 + 70 + 2
= 472
""")

# ============================================================
# 5. BINARY NUMBER SYSTEM
# ============================================================

print("\n" + "=" * 70)
print("BINARY NUMBER SYSTEM")
print("=" * 70)

print("""
Binary is a base-2 positional number system.

It has only two digits:

0
1

Each binary digit is called a bit.

Binary is fundamental to digital computing because electronic systems
can naturally represent two distinguishable states.
""")

binary_number = "101101"

print("Binary number:", binary_number)

print("""
Its positional expansion is:

1 × 2^5
+ 0 × 2^4
+ 1 × 2^3
+ 1 × 2^2
+ 0 × 2^1
+ 1 × 2^0
""")

binary_value = (
    1 * 2**5
    + 0 * 2**4
    + 1 * 2**3
    + 1 * 2**2
    + 0 * 2**1
    + 1 * 2**0
)

print("Decimal value:", binary_value)

# ============================================================
# 6. BINARY PLACE VALUES
# ============================================================

print("\n" + "=" * 70)
print("BINARY PLACE VALUES")
print("=" * 70)

print("""
Binary positional values are powers of two:

2^0  = 1
2^1  = 2
2^2  = 4
2^3  = 8
2^4  = 16
2^5  = 32
2^6  = 64
2^7  = 128
2^8  = 256
2^9  = 512
2^10 = 1024
""")

for exponent in range(11):
    print(f"2^{exponent:2} = {2**exponent}")

# ============================================================
# 7. BINARY TO DECIMAL
# ============================================================

print("\n" + "=" * 70)
print("BINARY TO DECIMAL")
print("=" * 70)

def binary_to_decimal(binary_string):
    """
    Convert a binary integer represented as a string to decimal
    without using int(binary_string, 2).
    """

    value = 0

    for digit in binary_string:
        if digit not in "01":
            raise ValueError("Invalid binary digit.")

        value = value * 2 + int(digit)

    return value


examples = ["0", "1", "10", "101", "1010", "11111111"]

for binary in examples:
    print(binary, "=", binary_to_decimal(binary))

print("""
The repeated operation:

value = value × base + digit

is a general positional evaluation technique.

For binary:

value = value × 2 + digit
""")

# ============================================================
# 8. DECIMAL TO BINARY
# ============================================================

print("\n" + "=" * 70)
print("DECIMAL TO BINARY")
print("=" * 70)

def decimal_to_binary(number):
    """
    Convert a non-negative decimal integer to binary manually.
    """

    if number < 0:
        raise ValueError("This function expects a non-negative integer.")

    if number == 0:
        return "0"

    digits = []

    while number > 0:
        remainder = number % 2
        digits.append(str(remainder))
        number //= 2

    return "".join(reversed(digits))


for number in [0, 1, 2, 5, 10, 15, 16, 25, 64, 100, 255]:
    result = decimal_to_binary(number)
    print(f"{number:3} -> {result}")

print("""
Decimal-to-binary conversion repeatedly divides the number by 2.

At every step:

quotient = number // 2
remainder = number % 2

The remainders, read from bottom to top, form the binary number.
""")

# ============================================================
# 9. DECIMAL TO BINARY USING POWERS OF TWO
# ============================================================

print("\n" + "=" * 70)
print("DECIMAL TO BINARY USING POWERS OF TWO")
print("=" * 70)

def decimal_to_binary_by_powers(number):
    if number == 0:
        return "0"

    highest_power = 0

    while 2 ** (highest_power + 1) <= number:
        highest_power += 1

    result = []

    remaining = number

    for power in range(highest_power, -1, -1):
        value = 2 ** power

        if value <= remaining:
            result.append("1")
            remaining -= value
        else:
            result.append("0")

    return "".join(result)


for n in [13, 42, 73, 100, 255]:
    print(f"{n:3} -> {decimal_to_binary_by_powers(n)}")

print("""
For example:

13 = 8 + 4 + 1

8  4  2  1
1  1  0  1

Therefore:

13 = 1101₂
""")

# ============================================================
# 10. OCTAL NUMBER SYSTEM
# ============================================================

print("\n" + "=" * 70)
print("OCTAL NUMBER SYSTEM")
print("=" * 70)

print("""
Octal is a base-8 positional number system.

Its valid digits are:

0 1 2 3 4 5 6 7

The digit 8 is not valid in an octal number.

Octal was historically useful because three binary bits correspond
exactly to one octal digit.
""")

octal_value = "725"

print("Octal number:", octal_value)

print("""
725₈ means:

7 × 8²
+ 2 × 8¹
+ 5 × 8⁰

= 448 + 16 + 5
= 469₁₀
""")

print("Decimal:", int(octal_value, 8))

# ============================================================
# 11. HEXADECIMAL NUMBER SYSTEM
# ============================================================

print("\n" + "=" * 70)
print("HEXADECIMAL NUMBER SYSTEM")
print("=" * 70)

print("""
Hexadecimal is base 16.

It requires sixteen symbols:

0 1 2 3 4 5 6 7 8 9 A B C D E F

The letters represent values:

A = 10
B = 11
C = 12
D = 13
E = 14
F = 15
""")

hex_digits = {
    "0": 0,
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "A": 10,
    "B": 11,
    "C": 12,
    "D": 13,
    "E": 14,
    "F": 15
}

for symbol, value in hex_digits.items():
    print(f"{symbol} -> {value}")

# ============================================================
# 12. HEXADECIMAL TO DECIMAL
# ============================================================

print("\n" + "=" * 70)
print("HEXADECIMAL TO DECIMAL")
print("=" * 70)

hex_number = "2AF"

print("""
2AF₁₆ means:

2 × 16²
+ A × 16¹
+ F × 16⁰

A = 10
F = 15

Therefore:

2 × 256
+ 10 × 16
+ 15

= 512 + 160 + 15
= 687
""")

print("Decimal:", int(hex_number, 16))

# ============================================================
# 13. GENERAL BASE CONVERSION TO DECIMAL
# ============================================================

print("\n" + "=" * 70)
print("GENERAL BASE-N TO DECIMAL CONVERSION")
print("=" * 70)

DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def base_to_decimal(number_string, base):
    """
    Convert a positive or zero integer represented in an arbitrary
    base between 2 and 36 into decimal.
    """

    if not 2 <= base <= 36:
        raise ValueError("Base must be between 2 and 36.")

    number_string = number_string.upper()

    value = 0

    for character in number_string:
        if character not in DIGITS:
            raise ValueError(f"Unknown digit: {character}")

        digit = DIGITS.index(character)

        if digit >= base:
            raise ValueError(
                f"Digit {character} is invalid for base {base}."
            )

        value = value * base + digit

    return value


tests = [
    ("1011", 2),
    ("725", 8),
    ("255", 10),
    ("2AF", 16),
    ("1Z", 36)
]

for value, base in tests:
    print(f"{value} base {base} = {base_to_decimal(value, base)} decimal")

# ============================================================
# 14. DECIMAL TO GENERAL BASE
# ============================================================

print("\n" + "=" * 70)
print("DECIMAL TO GENERAL BASE")
print("=" * 70)

def decimal_to_base(number, base):
    """
    Convert a non-negative decimal integer into a representation
    using a base between 2 and 36.
    """

    if not 2 <= base <= 36:
        raise ValueError("Base must be between 2 and 36.")

    if number == 0:
        return "0"

    digits = []

    while number > 0:
        remainder = number % base
        digits.append(DIGITS[remainder])
        number //= base

    return "".join(reversed(digits))


for base in [2, 3, 4, 5, 8, 10, 12, 16, 20, 36]:
    print(
        f"100 decimal in base {base:2} = "
        f"{decimal_to_base(100, base)}"
    )

# ============================================================
# 15. BINARY TO OCTAL
# ============================================================

print("\n" + "=" * 70)
print("BINARY TO OCTAL")
print("=" * 70)

print("""
Three binary bits correspond to one octal digit because:

8 = 2³

Therefore binary can be grouped into sets of three.

Example:

101101111

Group from the right:

101 101 111

Convert each group:

101 = 5
101 = 5
111 = 7

Therefore:

101101111₂ = 557₈
""")

binary = "101101111"
print("Python verification:", oct(int(binary, 2)))

# ============================================================
# 16. BINARY TO HEXADECIMAL
# ============================================================

print("\n" + "=" * 70)
print("BINARY TO HEXADECIMAL")
print("=" * 70)

print("""
Four binary bits correspond to one hexadecimal digit because:

16 = 2⁴

Example:

10101111

Group into four:

1010 1111

1010 = A
1111 = F

Therefore:

10101111₂ = AF₁₆
""")

binary = "10101111"
print("Python verification:", hex(int(binary, 2)))

# ============================================================
# 17. HEXADECIMAL TO BINARY
# ============================================================

print("\n" + "=" * 70)
print("HEXADECIMAL TO BINARY")
print("=" * 70)

hex_to_binary = {
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
    "F": "1111"
}

for symbol, binary_value in hex_to_binary.items():
    print(f"{symbol} -> {binary_value}")

print("""
Each hexadecimal digit represents exactly four bits.

For example:

3C₁₆

3 -> 0011
C -> 1100

Therefore:

3C₁₆ = 00111100₂
""")

# ============================================================
# 18. OCTAL TO BINARY
# ============================================================

print("\n" + "=" * 70)
print("OCTAL TO BINARY")
print("=" * 70)

octal_to_binary = {
    "0": "000",
    "1": "001",
    "2": "010",
    "3": "011",
    "4": "100",
    "5": "101",
    "6": "110",
    "7": "111"
}

for symbol, binary_value in octal_to_binary.items():
    print(f"{symbol} -> {binary_value}")

print("""
Example:

57₈

5 -> 101
7 -> 111

Therefore:

57₈ = 101111₂
""")

# ============================================================
# 19. RADIX POINT AND FRACTIONAL NUMBERS
# ============================================================

print("\n" + "=" * 70)
print("FRACTIONAL NUMBERS")
print("=" * 70)

print("""
The decimal point is more generally called a radix point.

For a base-b system:

Positions to the left of the radix point use:

b^0, b^1, b^2, ...

Positions to the right use:

b^-1, b^-2, b^-3, ...

For example:

12.34₁₀

= 1 × 10¹
+ 2 × 10⁰
+ 3 × 10^-1
+ 4 × 10^-2

= 10 + 2 + 0.3 + 0.04
= 12.34
""")

fractional_decimal = (
    1 * 10**1
    + 2 * 10**0
    + 3 * 10**-1
    + 4 * 10**-2
)

print("Calculated value:", fractional_decimal)

# ============================================================
# 20. BINARY FRACTIONS
# ============================================================

print("\n" + "=" * 70)
print("BINARY FRACTIONS")
print("=" * 70)

print("""
Binary fractional positions are:

2^-1 = 0.5
2^-2 = 0.25
2^-3 = 0.125
2^-4 = 0.0625
2^-5 = 0.03125

Consider:

101.101₂

The integer part is:

1×2² + 0×2¹ + 1×2⁰
= 4 + 0 + 1
= 5

The fractional part is:

1×2^-1 + 0×2^-2 + 1×2^-3
= 0.5 + 0 + 0.125
= 0.625

Therefore:

101.101₂ = 5.625₁₀
""")

binary_fraction = (
    1 * 2**2
    + 0 * 2**1
    + 1 * 2**0
    + 1 * 2**-1
    + 0 * 2**-2
    + 1 * 2**-3
)

print("Calculated value:", binary_fraction)

# ============================================================
# 21. DECIMAL FRACTION TO BINARY FRACTION
# ============================================================

print("\n" + "=" * 70)
print("DECIMAL FRACTION TO BINARY")
print("=" * 70)

print("""
A common method for converting a decimal fraction to another base
is repeated multiplication by the target base.

For:

0.625

Multiply by 2:

0.625 × 2 = 1.25

The integer part is 1.
Keep the fractional part 0.25.

Again:

0.25 × 2 = 0.5

Integer part = 0.

Again:

0.5 × 2 = 1.0

Integer part = 1.

Therefore:

0.625₁₀ = 0.101₂
""")

fraction = 0.625
bits = []

for _ in range(10):
    fraction *= 2
    bit = int(fraction)
    bits.append(str(bit))
    fraction -= bit

print("Generated bits:", "".join(bits))

# ============================================================
# 22. WHY SOME DECIMAL FRACTIONS REPEAT IN BINARY
# ============================================================

print("\n" + "=" * 70)
print("NON-TERMINATING BINARY FRACTIONS")
print("=" * 70)

print("""
Not every finite decimal fraction has a finite binary representation.

For example:

0.1₁₀

does not have a finite exact representation in base 2.

The repeated multiplication process produces:

0.1 × 2 = 0.2
0.2 × 2 = 0.4
0.4 × 2 = 0.8
0.8 × 2 = 1.6
0.6 × 2 = 1.2
0.2 × 2 = 0.4

The pattern repeats.

This is not a defect of binary.

It is a property of positional representations.

A fraction terminates in base b when, after reduction, its denominator
contains only prime factors that also occur in b.
""")

print("""
For decimal:

Base 10 = 2 × 5

Therefore fractions whose reduced denominator contains only factors
2 and 5 can terminate in decimal.

For binary:

Base 2 contains only factor 2.

Therefore a fraction terminates in binary only when its reduced
denominator is a power of two.
""")

# ============================================================
# 23. PYTHON NUMBER LITERALS
# ============================================================

print("\n" + "=" * 70)
print("PYTHON NUMBER LITERALS")
print("=" * 70)

print("""
Python allows integer literals to be written directly in several bases.

Decimal:
25

Binary:
0b11001

Octal:
0o31

Hexadecimal:
0x19
""")

decimal_number = 25
binary_literal = 0b11001
octal_literal = 0o31
hex_literal = 0x19

print("Decimal literal:", decimal_number)
print("Binary literal :", binary_literal)
print("Octal literal  :", octal_literal)
print("Hex literal    :", hex_literal)

print("""
All four variables contain the same numerical value:

25
""")

# ============================================================
# 24. PYTHON CONVERSION FUNCTIONS
# ============================================================

print("\n" + "=" * 70)
print("PYTHON BUILT-IN CONVERSIONS")
print("=" * 70)

value = 255

print("bin(255) :", bin(value))
print("oct(255) :", oct(value))
print("hex(255) :", hex(value))

print("""
int() can interpret a string according to a specified base.

Examples:

int("1010", 2)
int("17", 8)
int("255", 10)
int("FF", 16)
""")

print(int("1010", 2))
print(int("17", 8))
print(int("255", 10))
print(int("FF", 16))

# ============================================================
# 25. FORMAT FUNCTION
# ============================================================

print("\n" + "=" * 70)
print("FORMAT FUNCTION")
print("=" * 70)

value = 255

print("Binary      :", format(value, "b"))
print("Octal       :", format(value, "o"))
print("Decimal     :", format(value, "d"))
print("Hexadecimal :", format(value, "x"))
print("HEX         :", format(value, "X"))

print("""
format() is especially useful when you need a representation without
the Python prefixes.
""")

# ============================================================
# 26. PREFIXES
# ============================================================

print("\n" + "=" * 70)
print("NUMBER SYSTEM PREFIXES")
print("=" * 70)

print("""
Common Python prefixes:

0b -> binary
0o -> octal
0x -> hexadecimal

Examples:

0b1010
0o12
0xA

All represent decimal 10.
""")

print(0b1010, 0o12, 0xA)

# ============================================================
# 27. LEADING ZEROS
# ============================================================

print("\n" + "=" * 70)
print("LEADING ZEROS")
print("=" * 70)

print("""
Leading zeros normally do not change the numerical value.

For example:

101₂
000101₂
000000101₂

all represent the same value.

But leading zeros become important when a fixed-width representation
is required.
""")

value = 5

print("Normal binary:", bin(value))
print("8-bit binary :", format(value, "08b"))
print("16-bit binary:", format(value, "016b"))

# ============================================================
# 28. BITS, NIBBLES, AND BYTES
# ============================================================

print("\n" + "=" * 70)
print("BITS, NIBBLES, AND BYTES")
print("=" * 70)

print("""
A bit is one binary digit.

A nibble contains 4 bits.

A byte contains 8 bits.

Therefore:

1 nibble = 4 bits
1 byte = 8 bits
2 hexadecimal digits = 1 byte

Because one hexadecimal digit represents four bits.
""")

value = 173

binary = format(value, "08b")
hexadecimal = format(value, "02X")

print("Value:", value)
print("8-bit binary:", binary)
print("Two-digit hex:", hexadecimal)

# ============================================================
# 29. UNSIGNED N-BIT RANGE
# ============================================================

print("\n" + "=" * 70)
print("UNSIGNED N-BIT RANGE")
print("=" * 70)

print("""
An unsigned n-bit value can represent:

0 through 2^n - 1

because there are 2^n possible bit patterns.
""")

for bits in [1, 2, 3, 4, 8, 16, 32]:
    maximum = 2**bits - 1
    number_of_values = 2**bits

    print(
        f"{bits:2} bits -> "
        f"{number_of_values} possible values -> "
        f"0 through {maximum}"
    )

# ============================================================
# 30. INFORMATION CAPACITY
# ============================================================

print("\n" + "=" * 70)
print("INFORMATION CAPACITY")
print("=" * 70)

print("""
If a position has b possible symbols and there are n positions,
the number of possible combinations is:

b^n
""")

for base in [2, 8, 10, 16]:
    for positions in [1, 2, 3, 4]:
        print(
            f"Base {base:2}, positions {positions}: "
            f"{base**positions} combinations"
        )

# ============================================================
# 31. OVERFLOW
# ============================================================

print("\n" + "=" * 70)
print("FIXED-WIDTH OVERFLOW")
print("=" * 70)

print("""
Suppose an unsigned value is restricted to 8 bits.

The largest value is:

255

Adding 1 mathematically gives:

256

But 256 requires 9 bits:

100000000₂

If only eight bits are retained:

00000000₂

The value wraps around to zero in an unsigned 8-bit system.
""")

value = 255
wrapped = (value + 1) % 256

print("255 + 1 =", value + 1)
print("8-bit wrapped result:", wrapped)
print("Binary:", format(wrapped, "08b"))

# ============================================================
# 32. BINARY ADDITION
# ============================================================

print("\n" + "=" * 70)
print("BINARY ADDITION")
print("=" * 70)

print("""
Binary addition follows these basic rules:

0 + 0 = 0
0 + 1 = 1
1 + 0 = 1
1 + 1 = 10
1 + 1 + 1 = 11

The result 10₂ means:

1 × 2¹ + 0 × 2⁰ = 2
""")

a = 0b1011
b = 0b0110
result = a + b

print("1011₂ + 0110₂")
print(format(a, "04b"), "+", format(b, "04b"))
print("Result:", format(result, "05b"))
print("Decimal:", result)

# ============================================================
# 33. BINARY SUBTRACTION
# ============================================================

print("\n" + "=" * 70)
print("BINARY SUBTRACTION")
print("=" * 70)

print("""
Binary subtraction uses borrowing in the same general manner as
decimal subtraction.

For example:

10110₂ - 00111₂ = 01111₂

In decimal:

22 - 7 = 15
""")

a = 0b10110
b = 0b00111
result = a - b

print("10110₂ - 00111₂")
print("Result:", format(result, "05b"))
print("Decimal:", result)

# ============================================================
# 34. BINARY MULTIPLICATION
# ============================================================

print("\n" + "=" * 70)
print("BINARY MULTIPLICATION")
print("=" * 70)

print("""
Binary multiplication is based on:

0 × 0 = 0
0 × 1 = 0
1 × 0 = 0
1 × 1 = 1

Multiplication by 2 shifts an integer one position to the left.
""")

a = 0b1011

print("Original:", format(a, "b"), "=", a)
print("× 2     :", format(a << 1, "b"), "=", a << 1)
print("× 4     :", format(a << 2, "b"), "=", a << 2)

# ============================================================
# 35. BINARY DIVISION
# ============================================================

print("\n" + "=" * 70)
print("BINARY DIVISION")
print("=" * 70)

print("""
Integer division by powers of two corresponds to right shifting.

For non-negative integers:

n // 2
n // 4
n // 8

correspond to shifting right by:

1
2
3

positions respectively.
""")

value = 40

print("Value:", value)
print("40 // 2 =", value // 2)
print("40 >> 1 =", value >> 1)
print("40 // 4 =", value // 4)
print("40 >> 2 =", value >> 2)
print("40 // 8 =", value // 8)
print("40 >> 3 =", value >> 3)

# ============================================================
# 36. LEFT SHIFT
# ============================================================

print("\n" + "=" * 70)
print("LEFT SHIFT")
print("=" * 70)

print("""
A left shift moves bits toward higher positional values.

For positive integers:

x << n

is equivalent to:

x × 2^n

provided overflow is not being imposed by a fixed-width system.
""")

x = 7

for shift in range(5):
    print(
        f"{x} << {shift} = {x << shift:5} "
        f"binary={format(x << shift, 'b')}"
    )

# ============================================================
# 37. RIGHT SHIFT
# ============================================================

print("\n" + "=" * 70)
print("RIGHT SHIFT")
print("=" * 70)

print("""
For non-negative integers:

x >> n

corresponds to integer division by 2^n.
""")

x = 100

for shift in range(5):
    print(
        f"{x} >> {shift} = {x >> shift}"
    )

# ============================================================
# 38. BITWISE AND
# ============================================================

print("\n" + "=" * 70)
print("BITWISE AND")
print("=" * 70)

print("""
AND compares corresponding bits.

Rules:

0 AND 0 = 0
0 AND 1 = 0
1 AND 0 = 0
1 AND 1 = 1
""")

a = 0b1100
b = 0b1010
result = a & b

print("a     =", format(a, "04b"))
print("b     =", format(b, "04b"))
print("a & b =", format(result, "04b"))

# ============================================================
# 39. BITWISE OR
# ============================================================

print("\n" + "=" * 70)
print("BITWISE OR")
print("=" * 70)

print("""
OR produces 1 if at least one corresponding bit is 1.
""")

a = 0b1100
b = 0b1010
result = a | b

print("a     =", format(a, "04b"))
print("b     =", format(b, "04b"))
print("a | b =", format(result, "04b"))

# ============================================================
# 40. BITWISE XOR
# ============================================================

print("\n" + "=" * 70)
print("BITWISE XOR")
print("=" * 70)

print("""
XOR produces 1 when the corresponding bits are different.

Rules:

0 XOR 0 = 0
0 XOR 1 = 1
1 XOR 0 = 1
1 XOR 1 = 0
""")

a = 0b1100
b = 0b1010
result = a ^ b

print("a     =", format(a, "04b"))
print("b     =", format(b, "04b"))
print("a ^ b =", format(result, "04b"))

# ============================================================
# 41. BITWISE NOT
# ============================================================

print("\n" + "=" * 70)
print("BITWISE NOT")
print("=" * 70)

print("""
Python's ~ operator performs bitwise inversion according to Python's
integer representation rules.

For an integer x:

~x = -(x + 1)

For fixed-width binary reasoning, it is often clearer to explicitly
limit the result to a chosen number of bits.
""")

x = 0b0101

print("x:", format(x, "04b"))
print("~x as Python integer:", ~x)

four_bit_not = (~x) & 0b1111

print("4-bit interpretation:", format(four_bit_not, "04b"))

# ============================================================
# 42. BIT MASKS
# ============================================================

print("\n" + "=" * 70)
print("BIT MASKS")
print("=" * 70)

print("""
A bit mask is a value whose binary pattern is used to inspect or
modify selected bits.

Example:

00001111

can be used to keep only the lowest four bits.
""")

value = 0b10101101
mask = 0b00001111

result = value & mask

print("Value :", format(value, "08b"))
print("Mask  :", format(mask, "08b"))
print("Result:", format(result, "08b"))

# ============================================================
# 43. TESTING A BIT
# ============================================================

print("\n" + "=" * 70)
print("TESTING A BIT")
print("=" * 70)

print("""
To test bit position n:

(value >> n) & 1

Bit positions start from zero at the least significant bit.
""")

value = 0b10110100

print("Value:", format(value, "08b"))

for position in range(8):
    bit = (value >> position) & 1
    print(f"Bit {position}: {bit}")

# ============================================================
# 44. SETTING A BIT
# ============================================================

print("\n" + "=" * 70)
print("SETTING A BIT")
print("=" * 70)

print("""
To set bit n to 1:

value | (1 << n)
""")

value = 0b10000000
position = 2

new_value = value | (1 << position)

print("Before:", format(value, "08b"))
print("After :", format(new_value, "08b"))

# ============================================================
# 45. CLEARING A BIT
# ============================================================

print("\n" + "=" * 70)
print("CLEARING A BIT")
print("=" * 70)

print("""
To clear bit n:

value & ~(1 << n)

When working with fixed-width values, the mask can also be limited
to the intended width.
""")

value = 0b10111111
position = 5

new_value = value & ~(1 << position)

print("Before:", format(value, "08b"))
print("After :", format(new_value, "08b"))

# ============================================================
# 46. TOGGLING A BIT
# ============================================================

print("\n" + "=" * 70)
print("TOGGLING A BIT")
print("=" * 70)

print("""
To toggle bit n:

value ^ (1 << n)
""")

value = 0b10000000
position = 3

new_value = value ^ (1 << position)

print("Before:", format(value, "08b"))
print("After :", format(new_value, "08b"))

# ============================================================
# 47. EVEN AND ODD NUMBERS IN BINARY
# ============================================================

print("\n" + "=" * 70)
print("EVEN AND ODD NUMBERS")
print("=" * 70)

print("""
The least significant bit determines whether a non-negative integer
is even or odd.

LSB = 0 -> even
LSB = 1 -> odd

This works because the 2^0 position has value 1.
""")

for number in range(10):
    least_significant_bit = number & 1
    kind = "odd" if least_significant_bit else "even"

    print(
        f"{number:2} -> {format(number, '04b')} -> {kind}"
    )

# ============================================================
# 48. POWERS OF TWO
# ============================================================

print("\n" + "=" * 70)
print("POWERS OF TWO")
print("=" * 70)

print("""
Powers of two appear constantly in computing.

They determine:

- binary positional values
- memory sizes
- bit ranges
- address spaces
- masks
- shifts
- fixed-width integer limits
""")

for exponent in range(0, 21):
    print(f"2^{exponent:2} = {2**exponent}")

# ============================================================
# 49. NUMBER OF BITS REQUIRED
# ============================================================

print("\n" + "=" * 70)
print("BITS REQUIRED TO REPRESENT A VALUE")
print("=" * 70)

def bits_required(number):
    if number < 0:
        raise ValueError("This function handles non-negative integers.")

    if number == 0:
        return 1

    count = 0

    while number:
        count += 1
        number >>= 1

    return count


for number in [0, 1, 2, 3, 4, 7, 8, 15, 16, 255, 256, 1000]:
    print(
        f"{number:4} -> "
        f"{bits_required(number)} bits -> "
        f"{format(number, 'b')}"
    )

print("""
For a positive integer N, the number of binary digits required is:

floor(log₂(N)) + 1

The special case N = 0 requires one digit: 0.
""")

# ============================================================
# 50. NUMBER OF DIGITS IN AN ARBITRARY BASE
# ============================================================

print("\n" + "=" * 70)
print("DIGITS REQUIRED IN AN ARBITRARY BASE")
print("=" * 70)

import math

def digits_required(number, base):
    if number < 0:
        raise ValueError("Number must be non-negative.")

    if base < 2:
        raise ValueError("Base must be at least 2.")

    if number == 0:
        return 1

    return math.floor(math.log(number, base)) + 1


for number in [1, 8, 15, 16, 255, 256]:
    print(
        f"{number:3} -> "
        f"binary digits={digits_required(number, 2)}, "
        f"octal digits={digits_required(number, 8)}, "
        f"hex digits={digits_required(number, 16)}"
    )

# ============================================================
# 51. REPRESENTATION VERSUS VALUE
# ============================================================

print("\n" + "=" * 70)
print("REPRESENTATION VERSUS VALUE")
print("=" * 70)

print("""
These are different representations of the same value:

1010₂
12₈
10₁₀
A₁₆

The numerical value is ten.

The symbols are different because the bases are different.
""")

print("Binary :", int("1010", 2))
print("Octal  :", int("12", 8))
print("Decimal:", int("10", 10))
print("Hex    :", int("A", 16))

# ============================================================
# 52. HEXADECIMAL AS COMPACT BINARY
# ============================================================

print("\n" + "=" * 70)
print("HEX AS COMPACT BINARY")
print("=" * 70)

print("""
Hexadecimal is particularly useful because one hexadecimal digit
maps exactly to four binary bits.

This makes long binary values easier to read.

Binary:

111111101010110011011001

Hexadecimal:

FEACD9

The hexadecimal form is shorter while preserving the binary structure.
""")

binary = "111111101010110011011001"
value = int(binary, 2)

print("Binary:", binary)
print("Hex   :", format(value, "X"))

# ============================================================
# 53. RGB COLORS AND HEXADECIMAL
# ============================================================

print("\n" + "=" * 70)
print("HEX COLOR REPRESENTATION")
print("=" * 70)

print("""
Digital color systems commonly represent RGB channels using two
hexadecimal digits per channel.

Each channel therefore has 8 bits.

A six-digit hexadecimal color has:

2 digits for red
2 digits for green
2 digits for blue

Example:

#FF8040

FF -> red   = 255
80 -> green = 128
40 -> blue  = 64
""")

color = "FF8040"

red = int(color[0:2], 16)
green = int(color[2:4], 16)
blue = int(color[4:6], 16)

print("Red  :", red)
print("Green:", green)
print("Blue :", blue)

# ============================================================
# 54. CONVERSION VERIFICATION
# ============================================================

print("\n" + "=" * 70)
print("CONVERSION VERIFICATION")
print("=" * 70)

print("""
A conversion should be verified independently.

For example:

decimal -> binary -> decimal

If the final value matches the original value, the conversion is
consistent.
""")

original = 173
binary = decimal_to_binary(original)
back = binary_to_decimal(binary)

print("Original:", original)
print("Binary  :", binary)
print("Back    :", back)
print("Verified:", original == back)

# ============================================================
# 55. CROSS-BASE VERIFICATION
# ============================================================

print("\n" + "=" * 70)
print("CROSS-BASE VERIFICATION")
print("=" * 70)

value = 687

binary = format(value, "b")
octal = format(value, "o")
hexadecimal = format(value, "X")

print("Decimal:", value)
print("Binary :", binary)
print("Octal  :", octal)
print("Hex    :", hexadecimal)

print("Binary back:", int(binary, 2))
print("Octal back :", int(octal, 8))
print("Hex back   :", int(hexadecimal, 16))

# ============================================================
# 56. INVALID DIGITS
# ============================================================

print("\n" + "=" * 70)
print("INVALID DIGITS")
print("=" * 70)

print("""
A digit is valid only if it belongs to the selected base.

Examples:

Binary cannot contain 2.
Octal cannot contain 8 or 9.
Decimal cannot contain A.
Hexadecimal permits A through F.
""")

invalid_examples = [
    ("102", 2),
    ("89", 8),
    ("1A", 10)
]

for text, base in invalid_examples:
    try:
        print(text, "base", base, "=", int(text, base))
    except ValueError:
        print(
            f"{text!r} is invalid in base {base}."
        )

# ============================================================
# 57. GENERAL BASE-N EXAMPLES
# ============================================================

print("\n" + "=" * 70)
print("GENERAL BASE-N EXAMPLES")
print("=" * 70)

print("""
The mathematics does not stop at bases 2, 8, 10, and 16.

Other bases are mathematically valid.

Examples include:

Base 3
Base 5
Base 7
Base 12
Base 20
Base 36

The same positional rules apply.
""")

for base in [2, 3, 5, 7, 8, 10, 12, 16, 20, 36]:
    representation = decimal_to_base(2026, base)
    print(
        f"2026 decimal -> base {base:2} -> {representation}"
    )

# ============================================================
# 58. WHY BASE 8 AND BASE 16 ARE SPECIAL FOR COMPUTING
# ============================================================

print("\n" + "=" * 70)
print("WHY OCTAL AND HEXADECIMAL ARE USEFUL")
print("=" * 70)

print("""
Octal and hexadecimal have a direct relationship with binary.

Octal:

8 = 2³

Therefore one octal digit = three bits.

Hexadecimal:

16 = 2⁴

Therefore one hexadecimal digit = four bits.

This allows binary data to be compressed visually without changing
its underlying bit structure.
""")

# ============================================================
# 59. FIXED-WIDTH REPRESENTATION
# ============================================================

print("\n" + "=" * 70)
print("FIXED-WIDTH REPRESENTATION")
print("=" * 70)

value = 42

for width in [4, 8, 16, 32]:
    print(
        f"{width:2}-bit representation: "
        f"{format(value, f'0{width}b')}"
    )

print("""
Fixed width means the representation contains a predetermined number
of positions.

For example:

42 as an ordinary binary representation:

101010

42 as 8-bit binary:

00101010

The value is unchanged.

Only the representation has been padded.
""")

# ============================================================
# 60. BYTE AND HEX REPRESENTATION
# ============================================================

print("\n" + "=" * 70)
print("BYTE REPRESENTATION")
print("=" * 70)

for value in [0, 1, 15, 16, 127, 128, 255]:
    print(
        f"{value:3} -> "
        f"binary={format(value, '08b')} -> "
        f"hex={format(value, '02X')}"
    )

print("""
For one byte:

00000000 = 00₁₆ = 0
11111111 = FF₁₆ = 255

Therefore two hexadecimal digits can represent every possible
8-bit unsigned value.
""")

# ============================================================
# 61. MANUAL HEXADECIMAL CONVERSION
# ============================================================

print("\n" + "=" * 70)
print("MANUAL HEXADECIMAL CONVERSION")
print("=" * 70)

def decimal_to_hex_manual(number):
    if number == 0:
        return "0"

    digits = []

    while number > 0:
        remainder = number % 16
        digits.append(DIGITS[remainder])
        number //= 16

    return "".join(reversed(digits))


for number in [10, 15, 16, 26, 255, 256, 4095]:
    manual = decimal_to_hex_manual(number)
    built_in = format(number, "X")

    print(
        f"{number:4} -> manual={manual:4} "
        f"built-in={built_in}"
    )

# ============================================================
# 62. MANUAL OCTAL CONVERSION
# ============================================================

print("\n" + "=" * 70)
print("MANUAL OCTAL CONVERSION")
print("=" * 70)

def decimal_to_octal_manual(number):
    return decimal_to_base(number, 8)


for number in [8, 15, 64, 100, 255, 512]:
    print(
        f"{number:3} -> {decimal_to_octal_manual(number)}"
    )

# ============================================================
# 63. BINARY GROUPING
# ============================================================

print("\n" + "=" * 70)
print("BINARY GROUPING")
print("=" * 70)

print("""
For octal:

group from the radix point outward in groups of 3.

For hexadecimal:

group from the radix point outward in groups of 4.

Padding zeros may be added at the outside of the integer portion
without changing the value.
""")

binary = "110101101011"

octal_groups = [
    binary[max(0, len(binary) - i - 3):len(binary) - i]
    for i in range(0, len(binary), 3)
]

print("Binary:", binary)
print("Hex   :", format(int(binary, 2), "X"))
print("Octal :", format(int(binary, 2), "o"))

# ============================================================
# 64. INTEGER AND FRACTIONAL RADIX GROUPING
# ============================================================

print("\n" + "=" * 70)
print("RADIX POINT GROUPING")
print("=" * 70)

print("""
Grouping also works across the radix point.

For hexadecimal:

1010.1101₂

Group as:

1010 . 1101

which becomes:

A.D₁₆

The radix point remains in the same conceptual position.
""")

# ============================================================
# 65. NEGATIVE NUMBERS AND NUMBER SYSTEMS
# ============================================================

print("\n" + "=" * 70)
print("NEGATIVE VALUES")
print("=" * 70)

print("""
A minus sign is separate from the positional digit system.

For example:

-25

means the negative of the value represented by 25.

Computer systems need an encoding method when storing signed integers
in a fixed number of bits.

Common concepts include:

- sign-magnitude
- one's complement
- two's complement

These are signed-integer representations rather than different bases.
""")

negative = -25

print("Decimal:", negative)
print("Absolute value in binary:", format(abs(negative), "b"))

# ============================================================
# 66. PYTHON'S INTEGER MODEL
# ============================================================

print("\n" + "=" * 70)
print("PYTHON INTEGER MODEL")
print("=" * 70)

print("""
Python integers are not limited to ordinary 8-bit, 16-bit, or 32-bit
ranges in the same way as fixed-width machine integers.

Python integers can grow to accommodate arbitrarily large integers
subject to available memory.

Therefore:

2**100

is a valid Python integer.
""")

large_number = 2**100

print("2^100 =", large_number)
print("Binary digit count:", len(format(large_number, "b")))
print("Hexadecimal:", format(large_number, "X"))

# ============================================================
# 67. INTEGER DIVISION AND REMAINDER
# ============================================================

print("\n" + "=" * 70)
print("DIVISION AND REMAINDER")
print("=" * 70)

print("""
Repeated division conversion depends on quotient and remainder.

For any positive integer n and base b:

n = quotient × b + remainder

where:

0 <= remainder < b
""")

n = 157
base = 16

quotient = n // base
remainder = n % base

print(f"{n} = {quotient} × {base} + {remainder}")

# ============================================================
# 68. POSITIONAL EVALUATION FUNCTION
# ============================================================

print("\n" + "=" * 70)
print("POSITIONAL EVALUATION")
print("=" * 70)

def evaluate_digits(digits, base):
    value = 0

    for digit in digits:
        value = value * base + digit

    return value


digits = [3, 5, 2]
base = 7

print("Digits:", digits)
print("Base:", base)
print("Value:", evaluate_digits(digits, base))

print("""
[3, 5, 2] in base 7 means:

3 × 7²
+ 5 × 7¹
+ 2 × 7⁰

= 147 + 35 + 2
= 184
""")

# ============================================================
# 69. COMPARING DIGITS ACROSS BASES
# ============================================================

print("\n" + "=" * 70)
print("DIGIT MEANING DEPENDS ON BASE")
print("=" * 70)

print("""
The symbol 10 does not always mean decimal ten.

10₂ = 2
10₈ = 8
10₁₀ = 10
10₁₆ = 16

The positional notation determines the value.
""")

for base in [2, 8, 10, 16]:
    print(f"10 in base {base} =", int("10", base))

# ============================================================
# 70. SAME VALUE IN MULTIPLE BASES
# ============================================================

print("\n" + "=" * 70)
print("SAME VALUE IN MULTIPLE BASES")
print("=" * 70)

value = 2026

print("Decimal     :", value)
print("Binary      :", format(value, "b"))
print("Octal       :", format(value, "o"))
print("Hexadecimal :", format(value, "X"))

# ============================================================
# 71. COMMON MISTAKES
# ============================================================

print("\n" + "=" * 70)
print("COMMON MISTAKES")
print("=" * 70)

print("""
1. Treating binary 1010 as decimal 1010.

   1010₂ = 10₁₀

2. Using invalid digits.

   102₂ is invalid.

3. Forgetting that hexadecimal A-F represent 10-15.

4. Grouping binary incorrectly.

   Octal -> groups of 3.
   Hex   -> groups of 4.

5. Reading conversion remainders in the wrong direction.

   Repeated-division remainders are read from last to first.

6. Confusing bits with bytes.

   8 bits = 1 byte.

7. Assuming leading zeros change an integer's mathematical value.

8. Forgetting that fractional positions use negative powers.

9. Assuming every finite decimal fraction is finite in binary.

10. Confusing a number's value with its written representation.
""")

# ============================================================
# 72. PRACTICAL CONVERSION TABLE
# ============================================================

print("\n" + "=" * 70)
print("CONVERSION TABLE")
print("=" * 70)

print(
    f"{'Decimal':>8} "
    f"{'Binary':>12} "
    f"{'Octal':>8} "
    f"{'Hex':>8}"
)

print("-" * 42)

for value in range(0, 33):
    print(
        f"{value:8} "
        f"{format(value, 'b'):>12} "
        f"{format(value, 'o'):>8} "
        f"{format(value, 'X'):>8}"
    )

# ============================================================
# 73. AUTOMATIC CONVERSION CHECKER
# ============================================================

print("\n" + "=" * 70)
print("AUTOMATIC CONVERSION CHECKER")
print("=" * 70)

def conversion_report(value):
    binary = format(value, "b")
    octal = format(value, "o")
    hexadecimal = format(value, "X")

    print(f"Decimal     : {value}")
    print(f"Binary      : {binary}")
    print(f"Octal       : {octal}")
    print(f"Hexadecimal : {hexadecimal}")

    print(
        "Binary check:",
        int(binary, 2) == value
    )

    print(
        "Octal check :",
        int(octal, 8) == value
    )

    print(
        "Hex check   :",
        int(hexadecimal, 16) == value
    )


conversion_report(12345)

# ============================================================
# 74. BASE CONVERSION WITH FRACTIONAL PARTS
# ============================================================

print("\n" + "=" * 70)
print("FRACTIONAL BASE CONVERSION")
print("=" * 70)

def decimal_fraction_to_base(fraction, base, places=12):
    """
    Convert a decimal fractional value between 0 and 1 into a
    fractional representation in the requested base.
    """

    if not 0 <= fraction < 1:
        raise ValueError("Fraction must satisfy 0 <= fraction < 1.")

    digits = []

    for _ in range(places):
        fraction *= base
        digit = int(fraction)
        digits.append(DIGITS[digit])
        fraction -= digit

        if fraction == 0:
            break

    return "".join(digits)


for fraction in [0.5, 0.25, 0.625, 0.1]:
    binary_fraction = decimal_fraction_to_base(
        fraction,
        2,
        places=16
    )

    print(
        f"{fraction} decimal -> 0.{binary_fraction} binary"
    )

# ============================================================
# 75. INTEGER PLUS FRACTIONAL CONVERSION
# ============================================================

print("\n" + "=" * 70)
print("INTEGER + FRACTIONAL REPRESENTATION")
print("=" * 70)

def decimal_to_binary_fraction(number, fraction_places=16):
    integer_part = int(number)
    fractional_part = number - integer_part

    integer_binary = decimal_to_binary(integer_part)

    if fractional_part == 0:
        return integer_binary

    fraction_binary = decimal_fraction_to_base(
        fractional_part,
        2,
        fraction_places
    )

    return integer_binary + "." + fraction_binary


for value in [5.5, 5.25, 5.625, 10.75]:
    print(
        f"{value} -> {decimal_to_binary_fraction(value)}"
    )

# ============================================================
# 76. NUMBER SYSTEMS IN COMPUTER SCIENCE
# ============================================================

print("\n" + "=" * 70)
print("NUMBER SYSTEMS IN COMPUTER SCIENCE")
print("=" * 70)

print("""
Number systems appear throughout computer science.

Binary is fundamental to:

- digital logic
- machine representation
- CPU operations
- memory
- networking
- operating systems
- embedded systems

Hexadecimal is common in:

- memory addresses
- machine code
- debugging
- byte dumps
- color values
- cryptographic data
- identifiers
- low-level programming

Octal appears in contexts such as:

- Unix permission notation
- historical computing
- systems where three-bit grouping is useful.
""")

# ============================================================
# 77. UNIX-STYLE OCTAL EXAMPLE
# ============================================================

print("\n" + "=" * 70)
print("OCTAL AND PERMISSIONS")
print("=" * 70)

print("""
A familiar systems example is permission notation such as:

755

The digits are octal digits.

The mathematical base is 8.

The binary interpretation is:

7 -> 111
5 -> 101
5 -> 101

Therefore:

755₈ = 111101101₂
""")

permission = "755"

print(
    permission,
    "octal -> binary:",
    "".join(octal_to_binary[digit] for digit in permission)
)

# ============================================================
# 78. HEX AND MEMORY VALUES
# ============================================================

print("\n" + "=" * 70)
print("HEX AND MEMORY")
print("=" * 70)

print("""
A byte can be displayed using two hexadecimal digits.

Example:

10101100₂
= AC₁₆
= 172₁₀

Hexadecimal therefore provides a convenient visual representation
of raw binary data.
""")

byte = 0b10101100

print("Binary:", format(byte, "08b"))
print("Hex   :", format(byte, "02X"))
print("Decimal:", byte)

# ============================================================
# 79. A COMPLETE MANUAL CONVERSION EXAMPLE
# ============================================================

print("\n" + "=" * 70)
print("COMPLETE CONVERSION EXAMPLE")
print("=" * 70)

print("""
Convert hexadecimal 3F7 to decimal.

Step 1:

3 × 16²

Step 2:

F × 16¹

F = 15

Step 3:

7 × 16⁰

Therefore:

3 × 256
+ 15 × 16
+ 7

= 768 + 240 + 7
= 1015
""")

manual = 3 * 16**2 + 15 * 16**1 + 7 * 16**0

print("Calculated:", manual)
print("Python    :", int("3F7", 16))

# ============================================================
# 80. COMPLETE BINARY TO HEX EXAMPLE
# ============================================================

print("\n" + "=" * 70)
print("COMPLETE BINARY TO HEX EXAMPLE")
print("=" * 70)

print("""
Convert:

110111101010₂

Group into four-bit sections:

1101 1110 1010

Convert each group:

1101 = D
1110 = E
1010 = A

Therefore:

110111101010₂ = DEA₁₆
""")

binary = "110111101010"

print("Python:", format(int(binary, 2), "X"))

# ============================================================
# 81. COMPLETE BINARY TO OCTAL EXAMPLE
# ============================================================

print("\n" + "=" * 70)
print("COMPLETE BINARY TO OCTAL EXAMPLE")
print("=" * 70)

print("""
Convert:

101110011₂

Group into three:

101 110 011

Convert:

101 = 5
110 = 6
011 = 3

Therefore:

101110011₂ = 563₈
""")

binary = "101110011"

print("Python:", format(int(binary, 2), "o"))

# ============================================================
# 82. BASE CONVERSION IDENTITY
# ============================================================

print("\n" + "=" * 70)
print("BASE CONVERSION IDENTITY")
print("=" * 70)

print("""
A base representation is simply a decomposition of a value into
powers of the chosen base.

For base b:

dₙbⁿ + dₙ₋₁bⁿ⁻¹ + ... + d₁b + d₀

The same mathematical value can therefore be reconstructed from
any valid base representation.
""")

# ============================================================
# 83. FINAL PRACTICE DATA
# ============================================================

print("\n" + "=" * 70)
print("PRACTICE VALUES")
print("=" * 70)

practice_values = [
    7,
    8,
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
    512,
    1024,
    2026
]

for value in practice_values:
    print(
        f"{value:5} | "
        f"bin={format(value, 'b'):>14} | "
        f"oct={format(value, 'o'):>7} | "
        f"hex={format(value, 'X'):>6}"
    )

print("\nEnd of number systems teaching script.")


# ============================================================
# PART 2: MARKDOWN / README LEARNING NOTES
# ============================================================

# NUMBER SYSTEMS INTRODUCTION

## 1. Meaning of a Number System

A number system is a structured method of representing numerical values using a defined set of symbols and positional rules.

The most commonly encountered systems in computer science are:

- Decimal: base 10
- Binary: base 2
- Octal: base 8
- Hexadecimal: base 16

The numerical value itself does not depend on how it is written. The representation depends on the selected base.

For example:

- 10₂ = 2₁₀
- 10₈ = 8₁₀
- 10₁₀ = 10₁₀
- 10₁₆ = 16₁₀

The same symbols can therefore have different meanings in different bases.

## 2. Base or Radix

The base of a positional number system determines how many different digit symbols are available.

For base b, valid digits range from:

0 through b - 1

Examples:

| Number system | Base | Valid digits |
|---|---:|---|
| Binary | 2 | 0, 1 |
| Octal | 8 | 0–7 |
| Decimal | 10 | 0–9 |
| Hexadecimal | 16 | 0–9, A–F |

A digit that is greater than or equal to the base is invalid.

Therefore:

102₂ is invalid because 2 is not a binary digit.

89₈ is invalid because 8 and 9 are not octal digits.

1A₁₀ is invalid because A is not a decimal digit.

## 3. Decimal Number System

Decimal is a base-10 positional number system.

Its symbols are:

0, 1, 2, 3, 4, 5, 6, 7, 8, 9

Consider the decimal number:

5832

Its expanded positional form is:

5 × 10³ + 8 × 10² + 3 × 10¹ + 2 × 10⁰

This gives:

5000 + 800 + 30 + 2 = 5832

The position of a digit determines its weight.

The rightmost digit has weight 10⁰.

Every position to the left increases the exponent by one.

## 4. Positional Notation

Positional notation is the central concept behind the standard number systems.

For a base-b number, the value can be expressed as:

Σ(dᵢ × bⁱ)

where:

- dᵢ is the digit at position i
- b is the base
- i is the positional exponent

For the integer portion, the rightmost position has exponent 0.

For example:

472₁₀

means:

4 × 10² + 7 × 10¹ + 2 × 10⁰

The same rule applies to every base.

For example:

725₈

means:

7 × 8² + 2 × 8¹ + 5 × 8⁰

which is:

448 + 16 + 5 = 469₁₀

## 5. Binary Number System

Binary is a base-2 positional number system.

It uses only:

0 and 1

Each binary digit is called a bit.

Binary is fundamental to computing because digital systems can represent information through two-state conditions.

Binary positional weights are powers of two:

| Position | Weight |
|---:|---:|
| 0 | 1 |
| 1 | 2 |
| 2 | 4 |
| 3 | 8 |
| 4 | 16 |
| 5 | 32 |
| 6 | 64 |
| 7 | 128 |
| 8 | 256 |

For example:

101101₂

can be expanded as:

1 × 2⁵ + 0 × 2⁴ + 1 × 2³ + 1 × 2² + 0 × 2¹ + 1 × 2⁰

Therefore:

32 + 0 + 8 + 4 + 0 + 1 = 45

So:

101101₂ = 45₁₀

## 6. Binary to Decimal Conversion

A binary integer can be converted to decimal by evaluating each positional digit.

For:

1101₂

the calculation is:

1 × 2³ + 1 × 2² + 0 × 2¹ + 1 × 2⁰

= 8 + 4 + 0 + 1

= 13

Another computational method is the repeated evaluation rule:

value = value × base + digit

For binary:

value = value × 2 + digit

This is useful when processing a binary string programmatically.

## 7. Decimal to Binary Conversion

One standard method is repeated division by 2.

At each step:

- divide the number by 2
- record the remainder
- continue with the quotient
- read the remainders from bottom to top

For example, converting 13:

13 ÷ 2 = 6 remainder 1

6 ÷ 2 = 3 remainder 0

3 ÷ 2 = 1 remainder 1

1 ÷ 2 = 0 remainder 1

Reading the remainders upward gives:

1101₂

Therefore:

13₁₀ = 1101₂

Another method uses powers of two.

13 can be decomposed as:

13 = 8 + 4 + 1

The powers are:

8, 4, 2, 1

The corresponding selection is:

1, 1, 0, 1

Therefore:

13₁₀ = 1101₂

## 8. Octal Number System

Octal is base 8.

Its valid digits are:

0, 1, 2, 3, 4, 5, 6, 7

For example:

725₈

means:

7 × 8² + 2 × 8¹ + 5 × 8⁰

= 448 + 16 + 5

= 469₁₀

Octal has a particularly useful relationship with binary:

8 = 2³

Therefore every octal digit corresponds exactly to three binary bits.

## 9. Hexadecimal Number System

Hexadecimal is base 16.

It requires sixteen symbols:

0–9 and A–F

The additional symbols represent:

A = 10

B = 11

C = 12

D = 13

E = 14

F = 15

For example:

2AF₁₆

means:

2 × 16² + A × 16¹ + F × 16⁰

Since:

A = 10

F = 15

the value is:

2 × 256 + 10 × 16 + 15

= 512 + 160 + 15

= 687

Therefore:

2AF₁₆ = 687₁₀

## 10. Binary and Hexadecimal

Hexadecimal has a direct four-bit relationship with binary:

16 = 2⁴

Therefore:

1 hexadecimal digit = 4 binary bits

The mapping is:

| Hex | Binary |
|---|---|
| 0 | 0000 |
| 1 | 0001 |
| 2 | 0010 |
| 3 | 0011 |
| 4 | 0100 |
| 5 | 0101 |
| 6 | 0110 |
| 7 | 0111 |
| 8 | 1000 |
| 9 | 1001 |
| A | 1010 |
| B | 1011 |
| C | 1100 |
| D | 1101 |
| E | 1110 |
| F | 1111 |

For example:

10101111₂

can be divided into:

1010 1111

which becomes:

A F

Therefore:

10101111₂ = AF₁₆

## 11. Binary and Octal

Octal has a direct three-bit relationship with binary:

8 = 2³

Therefore:

1 octal digit = 3 binary bits

The mapping is:

| Octal | Binary |
|---|---|
| 0 | 000 |
| 1 | 001 |
| 2 | 010 |
| 3 | 011 |
| 4 | 100 |
| 5 | 101 |
| 6 | 110 |
| 7 | 111 |

For example:

101101111₂

can be grouped as:

101 101 111

which becomes:

5 5 7

Therefore:

101101111₂ = 557₈

## 12. Radix Point

The decimal point is more generally called a radix point because the concept applies to every base.

For a base-b system:

- integer positions use non-negative powers
- fractional positions use negative powers

For example:

12.34₁₀

means:

1 × 10¹ + 2 × 10⁰ + 3 × 10⁻¹ + 4 × 10⁻²

Therefore:

10 + 2 + 0.3 + 0.04 = 12.34

Binary works the same way.

For:

101.101₂

the integer portion is:

1 × 2² + 0 × 2¹ + 1 × 2⁰

= 5

The fractional portion is:

1 × 2⁻¹ + 0 × 2⁻² + 1 × 2⁻³

= 0.5 + 0.125

= 0.625

Therefore:

101.101₂ = 5.625₁₀

## 13. Decimal Fractions to Binary

A decimal fraction can be converted to binary through repeated multiplication by 2.

For:

0.625

multiply by 2:

0.625 × 2 = 1.25

The integer part is 1.

Keep 0.25.

Then:

0.25 × 2 = 0.5

The integer part is 0.

Then:

0.5 × 2 = 1.0

The integer part is 1.

The resulting bits are:

101

Therefore:

0.625₁₀ = 0.101₂

## 14. Why Some Fractions Do Not Terminate

A finite decimal fraction does not necessarily have a finite binary representation.

The reason is mathematical.

A reduced fraction terminates in base b only when all prime factors of its denominator are also prime factors of b.

For decimal:

10 = 2 × 5

Therefore denominators containing only factors of 2 and 5 can produce terminating decimal representations.

For binary:

2 = 2

Only powers of two can produce terminating binary fractions.

For example:

1/2 = 0.1₂

1/4 = 0.01₂

1/8 = 0.001₂

But:

1/10

does not terminate in binary because the denominator contains the factor 5.

This is why values such as decimal 0.1 require repeating binary representations.

## 15. Python Number-System Literals

Python provides direct syntax for several bases.

Decimal:

25

Binary:

0b11001

Octal:

0o31

Hexadecimal:

0x19

All of these represent the same numerical value:

25

The prefixes are:

- 0b for binary
- 0o for octal
- 0x for hexadecimal

## 16. Python Conversion Functions

Python provides:

bin()

oct()

hex()

and:

int()

Examples:

bin(255)

produces the binary representation.

oct(255)

produces the octal representation.

hex(255)

produces the hexadecimal representation.

The int() function can interpret a string according to a specified base.

Examples:

int("1010", 2)

int("17", 8)

int("255", 10)

int("FF", 16)

The second argument tells Python which base is being used.

## 17. Formatting Number Representations

The format() function can generate representations without the Python prefixes.

Examples:

format(255, "b")

format(255, "o")

format(255, "d")

format(255, "x")

format(255, "X")

The format specification determines the desired representation.

Uppercase hexadecimal uses:

A B C D E F

Lowercase hexadecimal uses:

a b c d e f

## 18. Leading Zeros

Leading zeros do not normally change the mathematical value of an integer.

For example:

101₂

000101₂

000000101₂

all represent the same value.

Leading zeros become significant when a fixed-width representation is required.

For example:

5

can be represented as:

101₂

or as an 8-bit value:

00000101₂

The value remains 5.

## 19. Bits, Nibbles, and Bytes

A bit is a single binary digit.

A nibble consists of four bits.

A byte consists of eight bits.

Therefore:

1 nibble = 4 bits

1 byte = 8 bits

2 hexadecimal digits = 1 byte

The last relationship follows directly from the fact that each hexadecimal digit represents four bits.

For example:

10101101₂

can be written as:

AD₁₆

The two hexadecimal digits represent the eight individual bits.

## 20. Unsigned n-Bit Values

An unsigned n-bit representation has:

2ⁿ

possible bit patterns.

The range is:

0 through 2ⁿ - 1

Examples:

| Bits | Number of values | Range |
|---:|---:|---|
| 1 | 2 | 0–1 |
| 2 | 4 | 0–3 |
| 4 | 16 | 0–15 |
| 8 | 256 | 0–255 |
| 16 | 65,536 | 0–65,535 |
| 32 | 4,294,967,296 | 0–4,294,967,295 |

The maximum unsigned value is therefore one less than the total number of possible combinations.

## 21. Fixed-Width Overflow

Suppose a value is restricted to eight bits.

The maximum unsigned value is:

255

In binary:

11111111₂

Adding one mathematically gives:

256

which requires:

100000000₂

That contains nine bits.

If the system retains only eight bits, the result becomes:

00000000₂

This is an example of unsigned wraparound.

The mathematical result and the fixed-width stored result are therefore different concepts.

## 22. Information Capacity

If each position can contain b different symbols and there are n positions, the number of possible combinations is:

bⁿ

For binary:

2ⁿ

For an eight-bit byte:

2⁸ = 256

possible patterns exist.

Those patterns can represent:

0 through 255

when interpreted as unsigned integer values.

The same 256 patterns could represent other kinds of information depending on the encoding.

## 23. Binary Arithmetic

Binary arithmetic follows positional rules similar to decimal arithmetic.

Binary addition rules include:

0 + 0 = 0

0 + 1 = 1

1 + 0 = 1

1 + 1 = 10

The result 10₂ means decimal 2.

Binary subtraction uses borrowing.

Binary multiplication follows:

0 × 0 = 0

0 × 1 = 0

1 × 0 = 0

1 × 1 = 1

Binary arithmetic is the underlying arithmetic representation used by digital computing hardware.

## 24. Binary Shifts

A left shift moves bits toward higher positional values.

For a non-negative integer:

x << n

corresponds to multiplication by:

2ⁿ

when no fixed-width overflow is imposed.

For example:

7 << 1 = 14

7 << 2 = 28

A right shift moves bits toward lower positional values.

For non-negative integers:

x >> n

corresponds to integer division by:

2ⁿ

For example:

40 >> 1 = 20

40 >> 2 = 10

40 >> 3 = 5

## 25. Bitwise AND

AND compares corresponding bits.

The result is 1 only when both input bits are 1.

Rules:

0 AND 0 = 0

0 AND 1 = 0

1 AND 0 = 0

1 AND 1 = 1

Example:

1100
1010
----

1000

The Python operator is:

&

## 26. Bitwise OR

OR produces 1 when at least one corresponding bit is 1.

Example:

1100
1010
----

1110

The Python operator is:

|

## 27. Bitwise XOR

XOR produces 1 when the corresponding bits are different.

Rules:

0 XOR 0 = 0

0 XOR 1 = 1

1 XOR 0 = 1

1 XOR 1 = 0

The Python operator is:

^

XOR is widely used for bit manipulation and other low-level operations.

## 28. Bitwise NOT

The Python operator:

~

inverts the bits according to Python's integer representation rules.

For an integer x:

~x = -(x + 1)

When reasoning about a fixed-width value, the intended width must be explicitly considered.

For example, the four-bit inversion of:

0101

is:

1010

A mask can be used to retain only the desired number of bits.

## 29. Bit Masks

A bit mask is a binary pattern used to select or manipulate particular bits.

For example:

00001111

can be used to select the lowest four bits.

If:

10101101

is ANDed with:

00001111

the result is:

00001101

The higher four bits have been removed.

Bit masks are fundamental in low-level programming, hardware interfaces, networking, permissions, flags, and compact data structures.

## 30. Testing a Bit

To inspect bit position n:

(value >> n) & 1

Bit numbering normally begins at zero from the least significant bit.

For example, if:

value = 10110100₂

bit 0 is the rightmost bit.

Bit 7 is the leftmost bit in an eight-bit representation.

The expression:

(value >> n) & 1

moves the selected bit to the least significant position and then isolates it.

## 31. Setting a Bit

To force bit n to 1:

value | (1 << n)

The expression:

1 << n

creates a mask with only bit n set.

ORing that mask with the original value sets the selected bit.

## 32. Clearing a Bit

To force bit n to 0:

value & ~(1 << n)

The mask identifies the target bit.

The complement reverses the mask so that AND preserves the other bits while clearing the selected position.

When dealing with fixed-width representations, the width of the value should be explicitly controlled.

## 33. Toggling a Bit

To reverse the state of bit n:

value ^ (1 << n)

If the selected bit is:

0

it becomes:

1

If it is:

1

it becomes:

0

XOR is therefore naturally suited to toggling individual bits.

## 34. Even and Odd Numbers

The least significant bit determines whether a non-negative integer is even or odd.

If the least significant bit is:

0 -> even

1 -> odd

This works because the least significant bit represents:

2⁰ = 1

All higher binary positions represent even values, while the final bit determines whether an additional one is present.

In Python:

number & 1

returns the least significant bit.

## 35. Powers of Two

Powers of two are central to binary representation.

Important values include:

2⁰ = 1

2¹ = 2

2² = 4

2³ = 8

2⁴ = 16

2⁵ = 32

2⁶ = 64

2⁷ = 128

2⁸ = 256

2⁹ = 512

2¹⁰ = 1024

and so on.

Powers of two determine positional weights, binary ranges, memory capacities, bit masks, and shift operations.

## 36. Number of Bits Required

For a positive integer N, the number of binary digits required is:

floor(log₂(N)) + 1

For example:

8 = 1000₂

requires four bits.

15 = 1111₂

requires four bits.

16 = 10000₂

requires five bits.

Zero is a special case and is normally represented with one digit:

0

## 37. Number of Digits in Other Bases

For a positive value N in base b, the number of digits is:

floor(log_b(N)) + 1

This follows from the positional relationship between the value and the highest power of the base required to represent it.

The number of digits required therefore depends on the chosen base.

The same value may require many binary digits but fewer hexadecimal digits because hexadecimal represents four binary bits with one digit.

## 38. Hexadecimal and Bytes

One hexadecimal digit represents four bits.

Two hexadecimal digits represent eight bits.

Therefore two hexadecimal digits represent one byte.

An unsigned byte ranges from:

00₁₆

through:

FF₁₆

In decimal:

0 through 255

In binary:

00000000₂

through:

11111111₂

This is one of the main reasons hexadecimal is so common in computer systems.

## 39. Hexadecimal Color Representation

A common practical use of hexadecimal is RGB color representation.

A six-digit color contains:

- two hexadecimal digits for red
- two for green
- two for blue

For:

#FF8040

the channels are:

FF = 255

80 = 128

40 = 64

Each channel uses eight bits.

Therefore the six hexadecimal digits represent:

24 bits

in total.

## 40. Octal in Systems Programming

Octal has historical and practical significance in computing.

One example is Unix-style permission notation.

A value such as:

755

is conventionally interpreted as octal.

Each octal digit corresponds to three binary bits:

7 -> 111

5 -> 101

5 -> 101

Therefore:

755₈ = 111101101₂

The usefulness of octal comes directly from the relationship:

8 = 2³

## 41. Decimal to Arbitrary Base

The repeated-division method is not limited to binary.

To convert a decimal integer into base b:

1. Divide the number by b.
2. Record the remainder.
3. Replace the number with the quotient.
4. Continue until the quotient becomes zero.
5. Read the remainders from last to first.

For any division:

N = quotient × base + remainder

and the remainder always satisfies:

0 ≤ remainder < base

This is the fundamental algorithm behind integer conversion from decimal to another positional base.

## 42. Arbitrary Base to Decimal

To convert a number from base b to decimal:

1. Start with value = 0.
2. Read digits from left to right.
3. Multiply the current value by b.
4. Add the current digit.

The repeated operation is:

value = value × b + digit

For example, for a base-7 number with digits:

352₇

the calculation is:

3 × 7² + 5 × 7¹ + 2 × 7⁰

= 147 + 35 + 2

= 184

The algorithm and the positional expansion are two ways of expressing the same mathematics.

## 43. General Base-N Systems

Number systems do not stop at bases 2, 8, 10, and 16.

Any integer base greater than or equal to 2 can define a positional number system.

Examples include:

Base 3

Base 5

Base 7

Base 12

Base 20

Base 36

For bases above 10, additional symbols are needed.

A common convention uses:

0–9

followed by:

A–Z

Under this convention, base 36 has 36 available symbols.

## 44. Representation and Mathematical Value

A representation is a sequence of symbols.

A value is the mathematical quantity represented by those symbols.

For example:

1010₂

12₈

10₁₀

A₁₆

all represent decimal ten.

Changing the base does not inherently change the underlying mathematical value.

This distinction is important when reading source code, debugging programs, inspecting memory, interpreting network data, and working with binary formats.

## 45. Binary, Octal, and Hexadecimal Relationships

The important relationships are:

8 = 2³

16 = 2⁴

This means:

1 octal digit = 3 bits

1 hexadecimal digit = 4 bits

2 octal digits = 6 bits

2 hexadecimal digits = 8 bits

4 hexadecimal digits = 16 bits

8 hexadecimal digits = 32 bits

16 hexadecimal digits = 64 bits

These relationships explain why hexadecimal is especially convenient for displaying machine-level values.

## 46. Fixed-Width Binary Representation

A fixed-width representation specifies exactly how many bit positions are available.

For example, the value 42 is:

101010₂

As an eight-bit value:

00101010₂

As a sixteen-bit value:

0000000000101010₂

The additional zeros do not alter the mathematical value.

They establish the width of the representation.

Fixed-width reasoning is essential when discussing overflow, registers, memory, network protocols, binary file formats, and machine-level integer types.

## 47. Python Integers Versus Fixed-Width Integers

Python's ordinary integers are not restricted to a fixed 8-bit, 16-bit, or 32-bit range.

For example:

2¹⁰⁰

is a valid Python integer.

Python automatically manages the required storage.

This differs from fixed-width machine representations, where a predetermined number of bits limits the representable range.

Therefore, when studying number systems, it is important to distinguish:

- mathematical integers
- Python integers
- fixed-width machine integers

They follow the same basic positional mathematics but have different storage constraints.

## 48. Overflow

Overflow occurs when a result exceeds the maximum value that can be represented within a fixed-width format.

For an unsigned n-bit representation:

maximum = 2ⁿ - 1

For eight bits:

maximum = 255

Therefore:

255 + 1 = 256

mathematically.

But an eight-bit unsigned representation can retain only:

00000000

after the ninth bit is discarded in a wraparound model.

The mathematical result remains 256 even though the fixed-width stored result may be 0.

## 49. Conversion Verification

Conversion errors are easy to make when working manually.

A reliable approach is to convert in both directions.

For example:

173₁₀

can be converted to:

10101101₂

Then convert:

10101101₂

back to decimal.

The result should be:

173

The same approach can be used across binary, octal, decimal, and hexadecimal.

Independent verification is particularly useful for long values.

## 50. Common Conversion Errors

Typical errors include:

### Treating binary as decimal

1010₂ is not decimal 1010.

It is decimal 10.

### Using invalid digits

102₂ is invalid.

### Forgetting hexadecimal values

A through F represent 10 through 15.

### Incorrect binary grouping

Octal uses groups of three bits.

Hexadecimal uses groups of four bits.

### Reading repeated-division remainders in the wrong order

The final representation is obtained by reading the remainders from bottom to top.

### Confusing bits and bytes

Eight bits make one byte.

### Forgetting negative powers

Fractional positions use:

b⁻¹, b⁻², b⁻³, ...

### Assuming every finite decimal fraction terminates in binary

Decimal 0.1 is a common counterexample.

### Confusing representation with value

1010₂ and 10₁₀ are different written forms of the same value.

## 51. Important Python Functions

The number-system script demonstrates several useful Python operations.

### bin()

Converts an integer to binary representation.

### oct()

Converts an integer to octal representation.

### hex()

Converts an integer to hexadecimal representation.

### int()

Converts a string from a specified base into an integer.

### format()

Produces controlled base representations and supports padding.

### // operator

Performs integer division.

### % operator

Produces the remainder.

The repeated-division conversion algorithm relies heavily on these two operations.

### << operator

Performs a left bit shift.

### >> operator

Performs a right bit shift.

### & operator

Performs bitwise AND.

### | operator

Performs bitwise OR.

### ^ operator

Performs bitwise XOR.

### ~ operator

Performs bitwise inversion according to Python's integer semantics.

## 52. Mathematical Foundation

The entire subject can be reduced to one central principle:

A positional number is a weighted sum of its digits.

For base b:

dₙbⁿ + dₙ₋₁bⁿ⁻¹ + ... + d₁b¹ + d₀b⁰

and, when fractional positions exist:

+ d₋₁b⁻¹ + d₋₂b⁻² + ...

The base determines the weights.

For decimal:

10⁰, 10¹, 10², ...

For binary:

2⁰, 2¹, 2², ...

For octal:

8⁰, 8¹, 8², ...

For hexadecimal:

16⁰, 16¹, 16², ...

Everything else in ordinary base conversion follows from this positional structure.

## 53. Reference Table

| Decimal | Binary | Octal | Hexadecimal |
|---:|---:|---:|---:|
| 0 | 0000 | 0 | 0 |
| 1 | 0001 | 1 | 1 |
| 2 | 0010 | 2 | 2 |
| 3 | 0011 | 3 | 3 |
| 4 | 0100 | 4 | 4 |
| 5 | 0101 | 5 | 5 |
| 6 | 0110 | 6 | 6 |
| 7 | 0111 | 7 | 7 |
| 8 | 1000 | 10 | 8 |
| 9 | 1001 | 11 | 9 |
| 10 | 1010 | 12 | A |
| 11 | 1011 | 13 | B |
| 12 | 1100 | 14 | C |
| 13 | 1101 | 15 | D |
| 14 | 1110 | 16 | E |
| 15 | 1111 | 17 | F |
| 16 | 10000 | 20 | 10 |

## 54. Core Relationships

The most important relationships demonstrated by the script are:

Base 2:

binary digits = 0, 1

Base 8:

octal digits = 0 through 7

Base 10:

decimal digits = 0 through 9

Base 16:

hexadecimal digits = 0 through 9 and A through F

Positional value:

digit × base^position

Binary-to-octal relationship:

8 = 2³

Binary-to-hexadecimal relationship:

16 = 2⁴

Unsigned n-bit range:

0 through 2ⁿ - 1

Number of possible n-bit patterns:

2ⁿ

Bits in a byte:

8

Bits represented by one hexadecimal digit:

4

Bits represented by one octal digit:

3

Number of binary digits needed for positive N:

floor(log₂(N)) + 1

Number of base-b digits needed for positive N:

floor(log_b(N)) + 1

A finite fraction in base b requires the reduced denominator to contain no prime factors outside those contained in b.
