"""
NUMBER SYSTEMS INTRODUCTION
===========================

This program is designed as an interactive academic learning module covering:

1. Decimal Number System
2. Binary Number System
3. Octal Number System
4. Hexadecimal Number System
5. Positional Notation
6. Place Value and Positional Weights
7. Conversion Between Number Systems
8. Integer and Fractional Number Conversion
9. Binary Arithmetic Concepts
10. Relationships Between Binary, Octal, and Hexadecimal
11. Practical Computing Applications
12. Common Errors and Peculiarities

The script is intentionally explanatory. It prints concepts, examples,
calculations, and demonstrations directly in the terminal.
"""


# ============================================================
# SECTION 1: INTRODUCTION TO NUMBER SYSTEMS
# ============================================================

print("\n" + "=" * 80)
print("NUMBER SYSTEMS: INTRODUCTION")
print("=" * 80)

print("""
A number system is a method for representing numerical quantities using
symbols and rules.

Humans commonly use the decimal number system because it contains ten digits:

    0, 1, 2, 3, 4, 5, 6, 7, 8, 9

Computers, on the other hand, operate fundamentally using electronic states.
A digital circuit can easily represent two stable conditions, such as:

    OFF / ON
    LOW / HIGH
    FALSE / TRUE
    0 / 1

For this reason, binary representation is fundamental to digital computing.

Different number systems use different numbers of symbols. The number of unique
symbols available in a number system is called its BASE or RADIX.
""")


# ============================================================
# SECTION 2: BASE OR RADIX
# ============================================================

print("\n" + "=" * 80)
print("BASE OR RADIX")
print("=" * 80)

print("""
The base of a number system determines how many unique digits or symbols are
available before positional values increase.

Examples:

    Decimal       Base 10
    Binary        Base 2
    Octal         Base 8
    Hexadecimal   Base 16

A number written in one number system can represent exactly the same quantity
as a number written in another system.

For example:

    Decimal 10
    Binary  1010
    Octal   12
    Hex     A

All four representations refer to the same numerical quantity.
""")


# ============================================================
# SECTION 3: DECIMAL NUMBER SYSTEM
# ============================================================

print("\n" + "=" * 80)
print("DECIMAL NUMBER SYSTEM")
print("=" * 80)

print("""
The decimal system has a base of 10.

Allowed digits:

    0 1 2 3 4 5 6 7 8 9

The position of each digit determines its value.

Consider:

    5832

The digits represent:

    5 × 10³
    8 × 10²
    3 × 10¹
    2 × 10⁰

Therefore:

    5832
    =
    5 × 1000
    +
    8 × 100
    +
    3 × 10
    +
    2 × 1

    = 5000 + 800 + 30 + 2
    = 5832

The decimal point separates positive and negative powers of 10.

For example:

    47.326

    4 × 10¹
    7 × 10⁰
    3 × 10⁻¹
    2 × 10⁻²
    6 × 10⁻³
""")


# ============================================================
# SECTION 4: BINARY NUMBER SYSTEM
# ============================================================

print("\n" + "=" * 80)
print("BINARY NUMBER SYSTEM")
print("=" * 80)

print("""
The binary number system has base 2.

Allowed digits:

    0 and 1

Each position represents a power of 2.

Consider:

    101101₂

Its positional values are:

    1 × 2⁵
    0 × 2⁴
    1 × 2³
    1 × 2²
    0 × 2¹
    1 × 2⁰

Therefore:

    1 × 32 = 32
    0 × 16 = 0
    1 × 8  = 8
    1 × 4  = 4
    0 × 2  = 0
    1 × 1  = 1

Total:

    32 + 8 + 4 + 1 = 45

Therefore:

    101101₂ = 45₁₀
""")


# ============================================================
# SECTION 5: OCTAL NUMBER SYSTEM
# ============================================================

print("\n" + "=" * 80)
print("OCTAL NUMBER SYSTEM")
print("=" * 80)

print("""
The octal number system has base 8.

Allowed digits:

    0 1 2 3 4 5 6 7

Digits such as 8 and 9 are not valid in octal.

Example:

    572₈

Positional expansion:

    5 × 8²
    7 × 8¹
    2 × 8⁰

Calculation:

    5 × 64 = 320
    7 × 8  = 56
    2 × 1  = 2

Therefore:

    572₈ = 378₁₀
""")


# ============================================================
# SECTION 6: HEXADECIMAL NUMBER SYSTEM
# ============================================================

print("\n" + "=" * 80)
print("HEXADECIMAL NUMBER SYSTEM")
print("=" * 80)

print("""
The hexadecimal system has base 16.

Sixteen symbols are required.

The symbols are:

    Decimal Value    Hexadecimal Symbol
    -------------    ------------------
          0                  0
          1                  1
          2                  2
          3                  3
          4                  4
          5                  5
          6                  6
          7                  7
          8                  8
          9                  9
         10                  A
         11                  B
         12                  C
         13                  D
         14                  E
         15                  F

Example:

    2AF₁₆

Expansion:

    2 × 16²
    A × 16¹
    F × 16⁰

Since:

    A = 10
    F = 15

Therefore:

    2 × 256 = 512
    10 × 16 = 160
    15 × 1 = 15

Total:

    512 + 160 + 15 = 687

Therefore:

    2AF₁₆ = 687₁₀
""")


# ============================================================
# SECTION 7: POSITIONAL NOTATION
# ============================================================

print("\n" + "=" * 80)
print("POSITIONAL NOTATION")
print("=" * 80)

print("""
Modern number systems are generally positional number systems.

This means that the value of a digit depends on:

1. The digit itself
2. Its position
3. The base of the number system

The general positional representation of a number is:

    dₙ × bⁿ
    + dₙ₋₁ × bⁿ⁻¹
    + ...
    + d₁ × b¹
    + d₀ × b⁰

For fractional positions:

    d₋₁ × b⁻¹
    + d₋₂ × b⁻²
    + ...

Where:

    d = digit
    b = base

For example, consider:

    345.67₁₀

This means:

    3 × 10²
    +
    4 × 10¹
    +
    5 × 10⁰
    +
    6 × 10⁻¹
    +
    7 × 10⁻²
""")


# ============================================================
# SECTION 8: GENERIC POSITIONAL EXPANSION FUNCTION
# ============================================================

def positional_expansion(number_string, base):
    """
    Converts an integer representation in the specified base into decimal
    while displaying the positional calculation.
    """

    digits = "0123456789ABCDEF"

    number_string = number_string.upper()
    decimal_value = 0

    print(f"\nPositional expansion of {number_string} in base {base}:")

    power = len(number_string) - 1

    for character in number_string:
        digit_value = digits.index(character)

        if digit_value >= base:
            raise ValueError(
                f"Digit '{character}' is not valid for base {base}"
            )

        contribution = digit_value * (base ** power)

        print(
            f"{character} ({digit_value}) × "
            f"{base}^{power} = {contribution}"
        )

        decimal_value += contribution
        power -= 1

    print(f"\nDecimal value = {decimal_value}")

    return decimal_value


print("\n" + "=" * 80)
print("POSITIONAL EXPANSION DEMONSTRATION")
print("=" * 80)

positional_expansion("101101", 2)
positional_expansion("572", 8)
positional_expansion("2AF", 16)


# ============================================================
# SECTION 9: DECIMAL TO BINARY CONVERSION
# ============================================================

print("\n" + "=" * 80)
print("DECIMAL TO BINARY CONVERSION")
print("=" * 80)

print("""
The standard method for converting a decimal integer into another base is
repeated division.

The decimal number is repeatedly divided by the target base.

The remainders are collected.

The final representation is obtained by reading the remainders from bottom
to top.

Example:

    Convert 45₁₀ to binary.

    45 ÷ 2 = 22 remainder 1
    22 ÷ 2 = 11 remainder 0
    11 ÷ 2 = 5  remainder 1
     5 ÷ 2 = 2  remainder 1
     2 ÷ 2 = 1  remainder 0
     1 ÷ 2 = 0  remainder 1

Reading upward:

    101101

Therefore:

    45₁₀ = 101101₂
""")


def decimal_to_base(number, base):
    """
    Converts a non-negative decimal integer into the specified base.
    """

    if number == 0:
        return "0"

    digits = "0123456789ABCDEF"

    result = []
    original_number = number

    while number > 0:
        remainder = number % base
        result.append(digits[remainder])

        print(
            f"{number} ÷ {base} = {number // base} "
            f"remainder {remainder}"
        )

        number //= base

    result.reverse()
    converted = "".join(result)

    print(
        f"\n{original_number} in base {base} = {converted}"
    )

    return converted


print("\nDecimal 45 to Binary:")
decimal_to_base(45, 2)


# ============================================================
# SECTION 10: DECIMAL TO OCTAL
# ============================================================

print("\n" + "=" * 80)
print("DECIMAL TO OCTAL CONVERSION")
print("=" * 80)

print("""
The same repeated-division method is used for octal conversion.

The only difference is that the divisor is 8.

Example:

    Convert 378₁₀ to octal.
""")

decimal_to_base(378, 8)


# ============================================================
# SECTION 11: DECIMAL TO HEXADECIMAL
# ============================================================

print("\n" + "=" * 80)
print("DECIMAL TO HEXADECIMAL CONVERSION")
print("=" * 80)

print("""
For hexadecimal conversion, repeated division uses 16 as the divisor.

Remainders from 10 through 15 are represented as:

    10 = A
    11 = B
    12 = C
    13 = D
    14 = E
    15 = F
""")

decimal_to_base(687, 16)


# ============================================================
# SECTION 12: BINARY TO DECIMAL
# ============================================================

print("\n" + "=" * 80)
print("BINARY TO DECIMAL CONVERSION")
print("=" * 80)

binary_number = "1101011"

print(f"""
Consider the binary number:

    {binary_number}₂

Python can directly interpret a string using a specified base.
""")

decimal_value = int(binary_number, 2)

print(f"{binary_number}₂ = {decimal_value}₁₀")

positional_expansion(binary_number, 2)


# ============================================================
# SECTION 13: OCTAL TO DECIMAL
# ============================================================

print("\n" + "=" * 80)
print("OCTAL TO DECIMAL CONVERSION")
print("=" * 80)

octal_number = "725"

print(f"""
Octal number:

    {octal_number}₈
""")

decimal_value = int(octal_number, 8)

print(f"{octal_number}₈ = {decimal_value}₁₀")

positional_expansion(octal_number, 8)


# ============================================================
# SECTION 14: HEXADECIMAL TO DECIMAL
# ============================================================

print("\n" + "=" * 80)
print("HEXADECIMAL TO DECIMAL CONVERSION")
print("=" * 80)

hex_number = "3E7"

print(f"""
Hexadecimal number:

    {hex_number}₁₆
""")

decimal_value = int(hex_number, 16)

print(f"{hex_number}₁₆ = {decimal_value}₁₀")

positional_expansion(hex_number, 16)


# ============================================================
# SECTION 15: RELATIONSHIP BETWEEN BINARY AND OCTAL
# ============================================================

print("\n" + "=" * 80)
print("BINARY AND OCTAL RELATIONSHIP")
print("=" * 80)

print("""
Octal has a direct relationship with binary because:

    8 = 2³

Therefore, every octal digit corresponds exactly to three binary bits.

Examples:

    Octal      Binary
    -----      ------
      0         000
      1         001
      2         010
      3         011
      4         100
      5         101
      6         110
      7         111

Example conversion:

    Binary:

        110101111

Group from the right into sets of three:

        110 101 111

Convert each group:

        110 = 6
        101 = 5
        111 = 7

Therefore:

        110101111₂ = 657₈
""")


# ============================================================
# SECTION 16: BINARY TO OCTAL FUNCTION
# ============================================================

def binary_to_octal(binary_string):
    """
    Converts a binary string into octal by grouping bits in groups of three.
    """

    binary_string = binary_string.strip()

    padding = (3 - len(binary_string) % 3) % 3

    binary_string = "0" * padding + binary_string

    groups = [
        binary_string[i:i + 3]
        for i in range(0, len(binary_string), 3)
    ]

    octal_digits = [
        str(int(group, 2))
        for group in groups
    ]

    print("Binary groups:")

    for group in groups:
        print(f"    {group} = {int(group, 2)}")

    return "".join(octal_digits)


binary_example = "110101111"

octal_result = binary_to_octal(binary_example)

print(
    f"\n{binary_example}₂ = {octal_result}₈"
)


# ============================================================
# SECTION 17: RELATIONSHIP BETWEEN BINARY AND HEXADECIMAL
# ============================================================

print("\n" + "=" * 80)
print("BINARY AND HEXADECIMAL RELATIONSHIP")
print("=" * 80)

print("""
Hexadecimal has a direct relationship with binary because:

    16 = 2⁴

Therefore, every hexadecimal digit corresponds exactly to four binary bits.

Examples:

    Binary      Hexadecimal
    ------      -----------
    0000             0
    0001             1
    0010             2
    0011             3
    0100             4
    0101             5
    0110             6
    0111             7
    1000             8
    1001             9
    1010             A
    1011             B
    1100             C
    1101             D
    1110             E
    1111             F

Example:

    Binary:

        110101111010

Group into four bits:

        1101 0111 1010

Convert:

        1101 = D
        0111 = 7
        1010 = A

Therefore:

        110101111010₂ = D7A₁₆
""")


# ============================================================
# SECTION 18: BINARY TO HEXADECIMAL FUNCTION
# ============================================================

def binary_to_hexadecimal(binary_string):
    """
    Converts a binary string to hexadecimal using groups of four bits.
    """

    digits = "0123456789ABCDEF"

    padding = (4 - len(binary_string) % 4) % 4

    binary_string = "0" * padding + binary_string

    groups = [
        binary_string[i:i + 4]
        for i in range(0, len(binary_string), 4)
    ]

    hexadecimal_digits = []

    for group in groups:
        value = int(group, 2)

        print(
            f"    {group} = {digits[value]}"
        )

        hexadecimal_digits.append(
            digits[value]
        )

    return "".join(hexadecimal_digits)


binary_example = "110101111010"

print("\nBinary groups:")

hex_result = binary_to_hexadecimal(binary_example)

print(
    f"\n{binary_example}₂ = {hex_result}₁₆"
)


# ============================================================
# SECTION 19: FRACTIONAL NUMBER REPRESENTATION
# ============================================================

print("\n" + "=" * 80)
print("FRACTIONAL NUMBER REPRESENTATION")
print("=" * 80)

print("""
Number systems also represent fractional quantities.

In decimal:

    0.375

means:

    3 × 10⁻¹
    +
    7 × 10⁻²
    +
    5 × 10⁻³

Binary fractions use negative powers of 2.

For example:

    0.101₂

means:

    1 × 2⁻¹
    +
    0 × 2⁻²
    +
    1 × 2⁻³

Calculation:

    1 × 0.5
    +
    0 × 0.25
    +
    1 × 0.125

    = 0.625

Therefore:

    0.101₂ = 0.625₁₀
""")


# ============================================================
# SECTION 20: DECIMAL FRACTION TO BINARY
# ============================================================

print("\n" + "=" * 80)
print("DECIMAL FRACTION TO BINARY")
print("=" * 80)

print("""
To convert the fractional part of a decimal number to another base, repeated
multiplication is used.

For binary conversion:

1. Multiply the fractional part by 2.
2. Record the integer part.
3. Continue using the remaining fractional part.
4. Read the integer parts from top to bottom.

Example:

    0.625 × 2 = 1.25     integer digit = 1
    0.25  × 2 = 0.50     integer digit = 0
    0.50  × 2 = 1.00     integer digit = 1

Therefore:

    0.625₁₀ = 0.101₂
""")


def decimal_fraction_to_base(fraction, base, precision=12):
    """
    Converts a decimal fraction between 0 and 1 into the specified base.

    Precision limits the number of generated digits.
    """

    digits = "0123456789ABCDEF"

    result = []

    for _ in range(precision):

        fraction *= base

        digit = int(fraction)

        result.append(
            digits[digit]
        )

        fraction -= digit

        if fraction == 0:
            break

    return "".join(result)


fraction = 0.625

binary_fraction = decimal_fraction_to_base(
    fraction,
    2
)

print(
    f"\n0.625₁₀ = 0.{binary_fraction}₂"
)


# ============================================================
# SECTION 21: INTEGER AND FRACTIONAL PARTS
# ============================================================

print("\n" + "=" * 80)
print("CONVERTING COMPLETE DECIMAL NUMBERS")
print("=" * 80)

print("""
A decimal number containing both integer and fractional components can be
converted by handling both parts separately.

Example:

    10.625₁₀

Integer part:

    10₁₀ = 1010₂

Fractional part:

    0.625₁₀ = 0.101₂

Therefore:

    10.625₁₀ = 1010.101₂
""")


def decimal_number_to_binary(number, precision=12):
    """
    Converts a positive decimal number containing integer and fractional
    components into binary.
    """

    integer_part = int(number)
    fractional_part = number - integer_part

    integer_binary = decimal_to_base(
        integer_part,
        2
    )

    if fractional_part == 0:
        return integer_binary

    fractional_binary = decimal_fraction_to_base(
        fractional_part,
        2,
        precision
    )

    return (
        integer_binary
        + "."
        + fractional_binary
    )


number = 10.625

binary_number = decimal_number_to_binary(number)

print(
    f"\n{number}₁₀ = {binary_number}₂"
)


# ============================================================
# SECTION 22: BINARY ARITHMETIC
# ============================================================

print("\n" + "=" * 80)
print("BINARY ARITHMETIC")
print("=" * 80)

print("""
Binary arithmetic follows the same conceptual principles as decimal arithmetic,
but only two digits are available.

BINARY ADDITION:

    0 + 0 = 0
    0 + 1 = 1
    1 + 0 = 1
    1 + 1 = 10

The result 10₂ means:

    0 with a carry of 1

Another important case:

    1 + 1 + 1 = 11₂

because:

    1 + 1 + 1 = 3₁₀
    3₁₀ = 11₂
""")


# ============================================================
# SECTION 23: BINARY ADDITION DEMONSTRATION
# ============================================================

binary_a = "101101"
binary_b = "11011"

decimal_a = int(binary_a, 2)
decimal_b = int(binary_b, 2)

binary_sum = bin(
    decimal_a + decimal_b
)[2:]

print(f"""
Example:

    {binary_a}₂ = {decimal_a}₁₀
    {binary_b}₂ = {decimal_b}₁₀

Decimal addition:

    {decimal_a} + {decimal_b} = {decimal_a + decimal_b}

Binary result:

    {binary_sum}₂
""")


# ============================================================
# SECTION 24: BINARY SUBTRACTION
# ============================================================

print("\n" + "=" * 80)
print("BINARY SUBTRACTION")
print("=" * 80)

print("""
Basic binary subtraction:

    0 - 0 = 0
    1 - 0 = 1
    1 - 1 = 0

The operation:

    0 - 1

requires borrowing.

Borrowing one from the next binary position means borrowing:

    10₂

because:

    10₂ = 2₁₀

Therefore:

    10₂ - 1₂ = 1₂

Binary subtraction is fundamental to computer arithmetic, although practical
computer processors frequently implement subtraction using binary complements.
""")


# ============================================================
# SECTION 25: BINARY MULTIPLICATION
# ============================================================

print("\n" + "=" * 80)
print("BINARY MULTIPLICATION")
print("=" * 80)

print("""
Binary multiplication is simplified because there are only two possible digits.

Rules:

    0 × 0 = 0
    0 × 1 = 0
    1 × 0 = 0
    1 × 1 = 1

Multiplication by 2 in binary shifts the number left by one position.

Example:

    101₂ = 5₁₀

Shift left:

    1010₂ = 10₁₀

This corresponds to multiplication by 2.

More generally:

    Left shift by n positions
    =
    multiplication by 2ⁿ

provided overflow and representation constraints are not involved.
""")


# ============================================================
# SECTION 26: LEADING ZEROS
# ============================================================

print("\n" + "=" * 80)
print("LEADING ZEROS")
print("=" * 80)

print("""
Leading zeros normally do not change the numerical value of a number.

Examples:

    00101₂ = 101₂

Both represent:

    5₁₀

Leading zeros become important in computing because fixed-width storage systems
require numbers to occupy a predetermined number of bits.

For example:

    5 represented using 8 bits:

    00000101

The value remains 5, but the representation now explicitly occupies eight bits.
""")


# ============================================================
# SECTION 27: BIT, NIBBLE, BYTE
# ============================================================

print("\n" + "=" * 80)
print("BIT, NIBBLE, AND BYTE")
print("=" * 80)

print("""
A BIT is a single binary digit.

Examples:

    0
    1

A NIBBLE contains four bits.

Example:

    1010

A BYTE conventionally contains eight bits.

Example:

    11001010

Because one hexadecimal digit represents exactly four binary bits:

    One hexadecimal digit = one nibble

Therefore:

    Two hexadecimal digits = one byte

Example:

    Binary:

        11001010

    Grouped:

        1100 1010

    Hexadecimal:

        C    A

Therefore:

    11001010₂ = CA₁₆
""")


# ============================================================
# SECTION 28: WHY HEXADECIMAL IS USED
# ============================================================

print("\n" + "=" * 80)
print("WHY HEXADECIMAL IS IMPORTANT IN COMPUTING")
print("=" * 80)

print("""
Binary numbers can become long and difficult to read.

For example:

    111111101101101110101111

The equivalent hexadecimal representation is much shorter:

    FEDBAF

Hexadecimal is particularly useful for representing:

    • Memory addresses
    • Machine-level values
    • Binary data
    • Colour values
    • Debugging information
    • Network identifiers
    • Unicode and character representations

A hexadecimal representation is compact while preserving a direct relationship
with the underlying binary representation.
""")


# ============================================================
# SECTION 29: HEXADECIMAL COLOUR REPRESENTATION
# ============================================================

print("\n" + "=" * 80)
print("HEXADECIMAL IN DIGITAL COLOUR REPRESENTATION")
print("=" * 80)

print("""
Digital colour values are frequently represented using hexadecimal notation.

A common RGB representation uses:

    #RRGGBB

Each pair represents an intensity between:

    00₁₆ and FF₁₆

Decimal interpretation:

    00₁₆ = 0
    FF₁₆ = 255

Examples:

    #FF0000

    Red   = 255
    Green = 0
    Blue  = 0

    #00FF00

    Red   = 0
    Green = 255
    Blue  = 0

    #0000FF

    Red   = 0
    Green = 0
    Blue  = 255
""")


# ============================================================
# SECTION 30: NUMBER SYSTEM VALIDATION
# ============================================================

print("\n" + "=" * 80)
print("VALIDATING DIGITS IN A NUMBER SYSTEM")
print("=" * 80)


def validate_number(number_string, base):
    """
    Checks whether every digit in a number is valid for the specified base.
    """

    digits = "0123456789ABCDEF"

    number_string = number_string.upper()

    for character in number_string:

        if character not in digits:
            return False

        if digits.index(character) >= base:
            return False

    return True


test_cases = [
    ("10101", 2),
    ("10201", 2),
    ("728", 8),
    ("725", 8),
    ("1AF", 16),
    ("1AG", 16)
]

for number_string, base in test_cases:

    validity = validate_number(
        number_string,
        base
    )

    print(
        f"{number_string} in base {base}: "
        f"{'VALID' if validity else 'INVALID'}"
    )


# ============================================================
# SECTION 31: REPRESENTATION VS VALUE
# ============================================================

print("\n" + "=" * 80)
print("REPRESENTATION VERSUS NUMERICAL VALUE")
print("=" * 80)

print("""
A fundamental distinction must be made between:

    Representation

and:

    Numerical value

The strings:

    10₁₀
    10₂
    10₈
    10₁₆

look identical, but their values are different.

    10₂  = 2₁₀
    10₈  = 8₁₀
    10₁₀ = 10₁₀
    10₁₆ = 16₁₀

The written symbols alone are insufficient to determine the value unless the
base is known.

This is why base subscripts are important in mathematics and computer science.
""")


# ============================================================
# SECTION 32: PYTHON NUMBER SYSTEM FEATURES
# ============================================================

print("\n" + "=" * 80)
print("NUMBER SYSTEMS IN PYTHON")
print("=" * 80)

print("""
Python provides direct support for several number system representations.

Binary literals use:

    0b

Example:

    0b1010

Octal literals use:

    0o

Example:

    0o12

Hexadecimal literals use:

    0x

Example:

    0xA
""")

binary_literal = 0b1010
octal_literal = 0o12
hexadecimal_literal = 0xA

print("0b1010 =", binary_literal)
print("0o12   =", octal_literal)
print("0xA    =", hexadecimal_literal)

print("""
Python internally treats these values as integers.

The prefixes describe how the programmer writes the literal. Once interpreted,
the numerical object represents the corresponding mathematical value.
""")


# ============================================================
# SECTION 33: PYTHON BASE CONVERSION FUNCTIONS
# ============================================================

print("\n" + "=" * 80)
print("PYTHON BASE CONVERSION FUNCTIONS")
print("=" * 80)

number = 255

print(f"Decimal:       {number}")
print(f"Binary:        {bin(number)}")
print(f"Octal:         {oct(number)}")
print(f"Hexadecimal:   {hex(number)}")

print("""
The functions:

    bin()
    oct()
    hex()

convert decimal integers into binary, octal, and hexadecimal string
representations.

The prefixes are included:

    0b
    0o
    0x

The int() function can interpret strings using a specified base.
""")

print(
    int("11111111", 2)
)

print(
    int("377", 8)
)

print(
    int("FF", 16)
)


# ============================================================
# SECTION 34: GENERAL BASE CONVERSION
# ============================================================

print("\n" + "=" * 80)
print("GENERAL BASE CONVERSION")
print("=" * 80)

print("""
A general conversion between two bases can conceptually be performed in two
steps:

    Source Base
        ↓
    Decimal Value
        ↓
    Target Base

For example:

    101101₂
        ↓
    45₁₀
        ↓
    55₈

Therefore:

    101101₂ = 55₈

Direct shortcuts are available when the bases have a mathematical relationship.

Examples:

    Binary ↔ Octal

because:

    8 = 2³

Binary ↔ Hexadecimal

because:

    16 = 2⁴
""")


def convert_base(number_string, source_base, target_base):
    """
    Converts an integer from one supported base to another.

    Supported range: bases 2 through 16.
    """

    decimal_value = int(
        number_string,
        source_base
    )

    if target_base == 10:
        return str(decimal_value)

    digits = "0123456789ABCDEF"

    result = []

    while decimal_value > 0:

        remainder = (
            decimal_value
            % target_base
        )

        result.append(
            digits[remainder]
        )

        decimal_value //= target_base

    result.reverse()

    return "".join(result)


examples = [
    ("101101", 2, 8),
    ("101101", 2, 16),
    ("FF", 16, 2),
    ("725", 8, 16)
]

for number_string, source, target in examples:

    converted = convert_base(
        number_string,
        source,
        target
    )

    print(
        f"{number_string} (base {source}) "
        f"= {converted} (base {target})"
    )


# ============================================================
# SECTION 35: NON-TERMINATING REPRESENTATIONS
# ============================================================

print("\n" + "=" * 80)
print("NON-TERMINATING REPRESENTATIONS")
print("=" * 80)

print("""
Not every number has a finite representation in every base.

A fraction may terminate in one number system but repeat indefinitely in
another.

For example:

    1 / 3

In decimal:

    0.333333...

This representation repeats indefinitely.

The same concept occurs in binary.

The decimal value:

    0.1

does not have a finite binary representation.

Its binary representation begins approximately as:

    0.00011001100110011...

This is significant in computing.

Many decimal fractions cannot be represented exactly using a finite number of
binary digits.

As a result, floating-point calculations may sometimes produce values that
appear slightly different from the mathematically expected decimal result.
""")


print("\nPython floating-point demonstration:")

value = 0.1 + 0.2

print("0.1 + 0.2 =", value)
print("0.1 + 0.2 == 0.3 :", value == 0.3)


# ============================================================
# SECTION 36: INFORMATION CAPACITY
# ============================================================

print("\n" + "=" * 80)
print("INFORMATION CAPACITY OF DIGITS")
print("=" * 80)

print("""
The number of possible values represented by a fixed number of digits depends
on the base.

For n digits in base b:

    Total combinations = bⁿ

Examples:

    3 binary digits:

        2³ = 8 combinations

    3 octal digits:

        8³ = 512 combinations

    3 hexadecimal digits:

        16³ = 4096 combinations

For n binary bits:

    Total possible patterns = 2ⁿ
""")


for bits in range(1, 9):

    combinations = 2 ** bits

    print(
        f"{bits} bit(s) -> "
        f"{combinations} possible patterns"
    )


# ============================================================
# SECTION 37: FIXED-WIDTH REPRESENTATION
# ============================================================

print("\n" + "=" * 80)
print("FIXED-WIDTH REPRESENTATION")
print("=" * 80)

print("""
Computer systems frequently store integers using a fixed number of bits.

For an unsigned integer containing n bits:

    Minimum value:

        0

    Maximum value:

        2ⁿ - 1

Examples:

    8 bits:

        2⁸ - 1 = 255

    16 bits:

        2¹⁶ - 1 = 65535

    32 bits:

        2³² - 1 = 4294967295

    64 bits:

        2⁶⁴ - 1

Fixed-width representation introduces the concept of overflow.

If a calculation produces a value larger than the available representation,
the system may not be able to store the result without special handling.
""")


for bit_width in [8, 16, 32, 64]:

    maximum_value = (
        2 ** bit_width
        - 1
    )

    print(
        f"{bit_width}-bit unsigned maximum: "
        f"{maximum_value}"
    )


# ============================================================
# SECTION 38: POWERS OF TWO
# ============================================================

print("\n" + "=" * 80)
print("IMPORTANT POWERS OF TWO")
print("=" * 80)

for exponent in range(0, 17):

    print(
        f"2^{exponent:<2} = "
        f"{2 ** exponent}"
    )


# ============================================================
# SECTION 39: COMPARISON TABLE
# ============================================================

print("\n" + "=" * 80)
print("COMPARISON OF COMMON NUMBER SYSTEMS")
print("=" * 80)

systems = [
    ("Binary", 2, "0, 1"),
    ("Octal", 8, "0 to 7"),
    ("Decimal", 10, "0 to 9"),
    ("Hexadecimal", 16, "0 to 9, A to F")
]

print(
    f"{'System':<18}"
    f"{'Base':<10}"
    f"{'Symbols'}"
)

print("-" * 60)

for system, base, symbols in systems:

    print(
        f"{system:<18}"
        f"{base:<10}"
        f"{symbols}"
    )


# ============================================================
# SECTION 40: INTERACTIVE NUMBER SYSTEM CONVERTER
# ============================================================

print("\n" + "=" * 80)
print("INTERACTIVE NUMBER SYSTEM CONVERTER")
print("=" * 80)

print("""
The following converter allows conversion between bases from 2 through 16.

The program validates the supplied number according to its source base.
""")

while True:

    try:

        print("\nEnter 'q' to stop the converter.")

        number_string = input(
            "Enter a number: "
        ).strip()

        if number_string.lower() == "q":
            break

        source_base = int(
            input(
                "Enter source base (2-16): "
            )
        )

        target_base = int(
            input(
                "Enter target base (2-16): "
            )
        )

        if not (
            2 <= source_base <= 16
        ):
            raise ValueError(
                "Source base must be between 2 and 16."
            )

        if not (
            2 <= target_base <= 16
        ):
            raise ValueError(
                "Target base must be between 2 and 16."
            )

        if not validate_number(
            number_string,
            source_base
        ):
            raise ValueError(
                "The number contains digits invalid for the source base."
            )

        converted = convert_base(
            number_string,
            source_base,
            target_base
        )

        decimal_value = int(
            number_string,
            source_base
        )

        print("\nConversion Result")

        print(
            f"Input: {number_string} "
            f"(base {source_base})"
        )

        print(
            f"Decimal value: {decimal_value}"
        )

        print(
            f"Converted value: {converted} "
            f"(base {target_base})"
        )

    except ValueError as error:

        print(
            f"\nInput Error: {error}"
        )


print("\n" + "=" * 80)
print("END OF NUMBER SYSTEMS MODULE")
print("=" * 80)
