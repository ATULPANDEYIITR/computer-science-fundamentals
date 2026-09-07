# Binary Arithmetic: Addition, Subtraction, Multiplication, Division, Carry, and Borrow Operations

## Introduction

Binary arithmetic is arithmetic performed using the binary numeral system. Binary numbers use only two digits:

- `0`
- `1`

Computers use binary representation because digital electronic systems can reliably represent two distinct states, commonly interpreted as off/on, low/high voltage, or false/true.

The arithmetic principles of binary numbers are closely related to decimal arithmetic. The major difference is the base of the number system.

Decimal arithmetic uses powers of 10:

    347 = 3 × 10² + 4 × 10¹ + 7 × 10⁰

Binary arithmetic uses powers of 2:

    1011₂ = 1 × 2³ + 0 × 2² + 1 × 2¹ + 1 × 2⁰

Therefore:

    1011₂ = 8 + 0 + 2 + 1 = 11₁₀

The Python script systematically implements binary arithmetic algorithms instead of relying only on Python's built-in integer conversion and arithmetic operators. This makes the underlying carry, borrow, complement, shifting, multiplication, and division mechanisms explicit.

---

# Fundamental Binary Concepts

## Binary Digits

A binary digit is called a bit.

A bit has exactly two possible values:

- `0`
- `1`

Multiple bits form a binary number.

Examples:

    1
    10
    101
    1101
    111111

The number of possible combinations for `n` bits is:

    2ⁿ

For example:

- 1 bit represents 2 combinations.
- 2 bits represent 4 combinations.
- 8 bits represent 256 combinations.
- 32 bits represent 4,294,967,296 combinations.

---

# Binary Positional Notation

Every position in a binary number represents a power of 2.

For:

    101101₂

The positions are:

| Bit | Position | Value |
|---|---:|---:|
| 1 | 5 | 32 |
| 0 | 4 | 0 |
| 1 | 3 | 8 |
| 1 | 2 | 4 |
| 0 | 1 | 0 |
| 1 | 0 | 1 |

Therefore:

    101101₂ = 32 + 8 + 4 + 1
            = 45₁₀

The script contains `explain_binary_places()` to calculate these positions and decimal contributions.

---

# Binary Validation

A valid binary number contains only `0` and `1`.

The script validates binary strings through:

    validate_binary()

The validation logic handles:

- Empty strings
- Invalid digits
- Explicit positive signs
- Explicit negative signs
- A sign without digits

Examples of valid input:

    1010
    +1010
    -1010

Examples of invalid input:

    1020
    12
    abc
    -
    ""

Validation is important because arithmetic algorithms assume every character represents a valid binary digit.

---

# Decimal to Binary Conversion

## Repeated Division by 2

A decimal integer can be converted to binary by repeatedly dividing it by 2 and recording the remainder.

For decimal 13:

    13 ÷ 2 = 6 remainder 1
     6 ÷ 2 = 3 remainder 0
     3 ÷ 2 = 1 remainder 1
     1 ÷ 2 = 0 remainder 1

Reading the remainders from bottom to top:

    1101₂

The script implements this algorithm in:

    decimal_to_binary_manual()

Negative numbers are handled by separating the sign from the magnitude.

---

# Binary to Decimal Conversion

A binary number can be converted to decimal by processing each bit from left to right.

The update rule is:

    current_value = current_value × 2 + next_bit

For:

    1011

The calculation is:

    0 × 2 + 1 = 1
    1 × 2 + 0 = 2
    2 × 2 + 1 = 5
    5 × 2 + 1 = 11

The script implements this logic in:

    binary_to_decimal_manual()

This approach is efficient because each bit is processed once.

Time complexity:

    O(n)

where `n` is the number of bits.

---

# Binary Addition

Binary addition follows the same positional principle as decimal addition.

The basic rules are:

    0 + 0 = 0
    0 + 1 = 1
    1 + 0 = 1
    1 + 1 = 10

The last rule is important:

    1 + 1 = 2₁₀ = 10₂

The current position receives `0`, and a carry of `1` moves to the next higher position.

---

# Carry Operations

A carry occurs when the sum of bits in a position cannot fit into one binary digit.

For example:

    1 + 1 = 10

The least significant bit is:

    0

The carry is:

    1

When an incoming carry is included, the largest possible sum is:

    1 + 1 + 1 = 3

In binary:

    3 = 11₂

Therefore:

    sum bit = 1
    carry = 1

The script implements this operation through:

    binary_add()

The general arithmetic calculation is:

    total = bit_a + bit_b + carry_in

    sum_bit = total mod 2
    carry_out = total // 2

---

# Binary Addition Algorithm

The script implements multi-bit addition in:

    add_binary_strings()

The algorithm proceeds from right to left because the rightmost bit is the least significant bit.

For every position:

1. Read the current bit from the first number.
2. Read the current bit from the second number.
3. Include the carry from the previous position.
4. Calculate the current sum bit.
5. Calculate the carry for the next position.
6. Continue until all positions have been processed.
7. Append the final carry if necessary.

For example:

    101
  + 011
  -----
   1000

The algorithm has time complexity:

    O(max(n, m))

where `n` and `m` are the lengths of the two operands.

---

# Half Adder

A half adder is a logical circuit that adds two bits.

Inputs:

    A
    B

Outputs:

    Sum
    Carry

The sum is:

    A XOR B

The carry is:

    A AND B

Examples:

| A | B | Sum | Carry |
|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 |
| 0 | 1 | 1 | 0 |
| 1 | 0 | 1 | 0 |
| 1 | 1 | 0 | 1 |

The script implements this in:

    half_adder()

---

# Full Adder

A full adder adds three binary values:

- First operand bit
- Second operand bit
- Carry-in

The sum formula is:

    Sum = A XOR B XOR Carry-in

The carry formula is:

    Carry-out =
        (A AND B)
        OR
        (Carry-in AND (A XOR B))

The script implements this in:

    full_adder()

A full adder is more useful than a half adder for multi-bit arithmetic because every position except the least significant position may receive an incoming carry.

---

# Ripple-Carry Addition

A ripple-carry adder connects multiple full adders.

The carry output from one bit position becomes the carry input of the next position.

For example:

    Bit 0 carry
        ↓
    Full Adder 0
        ↓
    Full Adder 1
        ↓
    Full Adder 2
        ↓
    Full Adder 3

This sequential carry dependency is called carry propagation.

The script demonstrates this concept through:

    ripple_carry_add()

A major hardware limitation of ripple-carry addition is propagation delay. The next position may need to wait for the previous position's carry to become available.

For large hardware adders, architectures such as carry-lookahead adders can reduce this dependency.

---

# Fixed-Width Binary Arithmetic

Real processors typically perform arithmetic using fixed-width registers.

Common widths include:

- 8 bits
- 16 bits
- 32 bits
- 64 bits

For an unsigned `n`-bit integer, the range is:

    0 through 2ⁿ - 1

For example, a 4-bit unsigned number ranges from:

    0000 = 0

through:

    1111 = 15

If:

    1111
  + 0001
  ------
   10000

the result requires five bits.

A 4-bit register cannot store the fifth bit.

The stored result becomes:

    0000

and the extra carry represents overflow.

The script implements fixed-width addition through:

    unsigned_binary_add_fixed_width()

---

# Unsigned Overflow

Unsigned overflow occurs when arithmetic produces a value larger than the maximum value representable using the available number of bits.

For `n` bits:

    maximum = 2ⁿ - 1

The script detects unsigned addition overflow using the carry beyond the most significant bit.

The implementation is:

    unsigned_addition_overflow()

For unsigned addition:

    Carry out = 1

is a direct indicator of overflow.

---

# Binary Subtraction

The basic binary subtraction rules are:

    0 - 0 = 0
    1 - 0 = 1
    1 - 1 = 0

The difficult case is:

    0 - 1

A single unsigned binary digit cannot represent `-1`, so borrowing is required.

---

# Borrow Operations

Consider:

    10₂ - 1₂

The higher-order `1` can be borrowed.

Conceptually:

    10₂

becomes:

    0 × 2 + 2 × 1

Therefore:

    10₂ - 1₂ = 01₂

For a single bit operation:

    0 - 1

the result bit becomes:

    1

and a borrow of:

    1

is passed to the next higher position.

The script implements individual subtraction operations in:

    binary_subtract()

---

# Binary Subtraction Algorithm

The function:

    subtract_binary_strings()

performs column-by-column subtraction.

For each position:

    difference = A - B - borrow_in

If the difference is negative:

1. Add 2 to obtain the current difference bit.
2. Set the borrow for the next position.

The algorithm processes bits from right to left.

For example:

    1010
  - 0011
  ------
    0111

The script also handles cases where the result is negative.

Example:

    11 - 101 = -10

---

# Half Subtractor

A half subtractor subtracts two bits.

Inputs:

    A
    B

Outputs:

    Difference
    Borrow

The difference formula is:

    Difference = A XOR B

The borrow formula is:

    Borrow = NOT A AND B

The script implements this in:

    half_subtractor()

---

# Full Subtractor

A full subtractor processes:

- First operand bit
- Second operand bit
- Borrow-in

The difference is:

    A XOR B XOR Borrow-in

The borrow-out is:

    (NOT A AND B)
    OR
    (Borrow-in AND NOT(A XOR B))

The script implements this in:

    full_subtractor()

---

# Ones' Complement

The ones' complement of a binary number is created by flipping every bit.

Rules:

    0 → 1
    1 → 0

Example:

    0101

becomes:

    1010

The script implements bit inversion using:

    invert_bits()

and fixed-width ones' complement using:

    ones_complement()

---

# Two's Complement

Two's complement is the most widely used representation for signed integers in modern computer systems.

To calculate the two's complement:

1. Start with the fixed-width binary magnitude.
2. Invert all bits.
3. Add 1.

For example, represent `-5` using 8 bits.

Positive 5:

    00000101

Invert:

    11111010

Add 1:

    11111011

Therefore:

    11111011

represents:

    -5

in 8-bit two's-complement representation.

The script implements this process in:

    twos_complement()

---

# Why Two's Complement Is Important

Two's complement allows subtraction to be performed using addition.

Instead of directly computing:

    A - B

a processor can compute:

    A + (-B)

where `-B` is represented using two's complement.

This allows a common arithmetic circuit to support both addition and subtraction.

The script demonstrates this through:

    subtract_using_twos_complement()

Any carry beyond the fixed width is discarded.

---

# Signed Two's-Complement Range

For an `n`-bit two's-complement integer:

    minimum = -2^(n-1)

    maximum = 2^(n-1) - 1

For 4 bits:

    minimum = -8
    maximum = 7

The range is asymmetric because one additional negative value is available.

The bit patterns are:

| Binary | Signed Decimal |
|---|---:|
| 0000 | 0 |
| 0001 | 1 |
| 0010 | 2 |
| 0011 | 3 |
| 0100 | 4 |
| 0101 | 5 |
| 0110 | 6 |
| 0111 | 7 |
| 1000 | -8 |
| 1001 | -7 |
| 1010 | -6 |
| 1011 | -5 |
| 1100 | -4 |
| 1101 | -3 |
| 1110 | -2 |
| 1111 | -1 |

The script provides:

    signed_decimal_to_twos_complement()

and:

    twos_complement_to_signed_decimal()

---

# Signed Overflow

Signed overflow differs from unsigned overflow.

For two's-complement addition, signed overflow occurs when:

- Two positive values produce a negative result.
- Two negative values produce a positive result.

The sign-bit rule is:

    If A and B have the same sign,
    and the result has a different sign,
    signed overflow occurred.

The script implements this in:

    signed_addition_overflow()

A carry beyond the most significant bit is not sufficient by itself to detect signed overflow.

This distinction is important.

---

# Binary Multiplication

Binary multiplication is simpler than decimal multiplication because each multiplier digit is either `0` or `1`.

The basic rules are:

    0 × 0 = 0
    0 × 1 = 0
    1 × 0 = 0
    1 × 1 = 1

For individual bits:

    A × B = A AND B

---

# Long Binary Multiplication

Long binary multiplication uses partial products.

For each `1` in the multiplier:

1. Copy the multiplicand.
2. Shift it left according to the bit position.
3. Add the partial product to the accumulated result.

For each `0`:

- The partial product contributes zero.

The script implements this in:

    multiply_binary_long()

The shift operation is equivalent to multiplication by powers of 2.

For example:

    101 << 2

becomes:

    10100

and:

    5 × 4 = 20

because:

    2² = 4

---

# Shift-and-Add Multiplication

The shift-and-add algorithm uses an iterative method.

The algorithm maintains:

- Result
- Multiplicand
- Multiplier

The process is:

1. Inspect the least significant bit of the multiplier.
2. If it is `1`, add the current multiplicand to the result.
3. Shift the multiplicand left.
4. Shift the multiplier right.
5. Repeat until the multiplier becomes zero.

The script implements this in:

    multiply_binary_shift_add()

The algorithm closely reflects how binary arithmetic can be organized in hardware.

---

# Signed Binary Multiplication

The script also supports explicitly signed binary strings through:

    multiply_signed_binary()

The sign rules are identical to decimal multiplication:

    Positive × Positive = Positive
    Positive × Negative = Negative
    Negative × Positive = Negative
    Negative × Negative = Positive

The magnitudes are multiplied separately.

---

# Binary Shift Operations

## Left Shift

A left shift moves all bits toward higher-order positions.

Example:

    1011 << 2

becomes:

    101100

For unsigned values without overflow:

    x << n = x × 2ⁿ

The script implements this in:

    left_shift_binary()

---

## Right Shift

A logical right shift moves bits toward lower-order positions.

Example:

    1011 >> 2

becomes:

    10

For unsigned values:

    x >> n = floor(x / 2ⁿ)

Bits shifted beyond the right side are discarded.

The script implements this in:

    right_shift_binary()

---

# Binary Division

Binary division follows the same general concept as decimal long division.

The script implements long division through:

    divide_binary_long()

The function returns:

    quotient
    remainder

The fundamental division identity is:

    dividend = divisor × quotient + remainder

The remainder must satisfy:

    0 ≤ remainder < divisor

---

# Binary Long Division Algorithm

For every bit of the dividend:

1. Shift the current remainder left.
2. Bring down the next dividend bit.
3. Compare the remainder with the divisor.
4. If the remainder is greater than or equal to the divisor:
   - Subtract the divisor.
   - Add `1` to the quotient position.
5. Otherwise:
   - Leave the remainder unchanged.
   - Add `0` to the quotient position.

The algorithm requires comparison and subtraction operations.

The script provides:

    compare_unsigned_binary()

and:

    subtract_unsigned_binary()

to support the division implementation.

---

# Division by Zero

Division by zero is mathematically undefined.

The script explicitly checks:

    divisor == "0"

and raises:

    ZeroDivisionError

This is an important validation requirement in any arithmetic implementation.

---

# Signed Binary Division

The function:

    divide_signed_binary()

supports signed binary values.

The quotient sign follows:

    sign(dividend) × sign(divisor)

The implementation truncates the quotient toward zero.

The remainder retains the sign of the dividend when the remainder is non-zero.

---

# Restoring Division

Restoring division is a binary division method commonly associated with computer architecture.

The conceptual procedure is:

1. Shift the partial remainder.
2. Bring down a new dividend bit.
3. Attempt subtraction of the divisor.
4. If subtraction succeeds, set the quotient bit to `1`.
5. If subtraction would produce a negative partial remainder, restore the previous value and set the quotient bit to `0`.

The script demonstrates the algorithm through:

    restoring_division()

At the string-based algorithm level, restoration is represented by preserving the previous remainder when subtraction is not possible.

---

# Bitwise Operations

Binary arithmetic is closely related to bitwise logic.

Python supports:

    AND       &
    OR        |
    XOR       ^
    NOT       ~
    Left shift  <<
    Right shift >>

The script demonstrates these operations through:

    bitwise_demonstration()

---

# XOR and Binary Addition

XOR produces the sum of two bits without considering carry.

Examples:

    0 XOR 0 = 0
    0 XOR 1 = 1
    1 XOR 0 = 1
    1 XOR 1 = 0

The final case requires a carry.

Carry positions are identified by:

    A AND B

The carry must move one position to the left:

    carry = (A AND B) << 1

Therefore binary addition can be expressed as repeated application of:

    partial_sum = A XOR B
    carry = (A AND B) << 1

The process continues until:

    carry = 0

The script implements this in:

    add_using_bitwise_operations()

---

# Fixed-Width Binary Object

The script defines:

    FixedWidthBinary

This class represents a binary word with a fixed number of bits.

It provides:

- Bit width
- Unsigned interpretation
- Signed two's-complement interpretation
- Fixed-width addition
- Fixed-width subtraction

The class demonstrates an important software design principle: a bit pattern and its numerical interpretation are separate concepts.

For example:

    11111101

can represent:

    253

when interpreted as unsigned 8-bit binary.

The same pattern represents:

    -3

when interpreted as signed 8-bit two's complement.

The bits are identical. The interpretation differs.

---

# Important Distinction: Representation Versus Value

A binary string does not inherently determine whether a value is signed or unsigned.

For example:

    1111

can mean:

    15

as an unsigned 4-bit integer.

It can mean:

    -1

as a signed 4-bit two's-complement integer.

The meaning depends on the representation convention.

This distinction is fundamental in programming, processor architecture, serialization, networking, and systems programming.

---

# Common Mistakes

## Treating Binary Strings as Ordinary Decimal Strings

The string:

    "101"

does not represent one hundred one in binary arithmetic.

Its binary value is:

    5

---

## Ignoring Leading Zeros in Fixed-Width Systems

For mathematical calculations:

    101
    000101

represent the same unsigned value.

For fixed-width systems, the number of bits can matter.

For example:

    11111111

may represent:

    255 unsigned

or:

    -1 signed 8-bit

Leading zeros affect the width and therefore the interpretation.

---

## Confusing Carry With Signed Overflow

For unsigned arithmetic:

    carry beyond the most significant bit

indicates overflow.

For signed two's-complement arithmetic, overflow is determined by sign relationships.

The two conditions are not identical.

---

## Forgetting Borrow Propagation

In subtraction, a borrow can propagate across several zero bits.

For example:

    10000 - 1

requires borrowing through multiple positions.

Algorithms must correctly propagate the borrow.

---

## Forgetting to Discard Excess Bits in Fixed-Width Arithmetic

Hardware registers have fixed capacity.

A result may mathematically require more bits than the register can store.

For example, with 4-bit arithmetic:

    1111 + 0001 = 10000

The stored 4-bit result is:

    0000

The extra bit is discarded, although overflow information may be recorded separately.

---

## Treating Python Integers as Fixed-Width Integers

Python integers use arbitrary precision.

This means Python does not naturally overflow at 8, 16, 32, or 64 bits.

Fixed-width behavior must be implemented explicitly when simulating computer registers.

The script demonstrates this distinction using fixed-width functions.

---

# Edge Cases Covered

The script handles several important edge cases.

## Zero

Examples:

    0 + 0
    0 × 10101
    0 / non-zero value

Zero must remain normalized as:

    "0"

rather than an empty string.

---

## Negative Results

The subtraction implementation supports:

    smaller - larger

and returns an explicitly signed binary result.

Example:

    11 - 101 = -10

---

## Division by Zero

The script raises:

    ZeroDivisionError

for division by zero.

---

## Invalid Binary Characters

Strings containing characters other than binary digits are rejected.

Examples:

    102
    1102
    abc

---

## Signed Representation Limits

A number cannot always fit into a selected two's-complement width.

For example, an 4-bit signed two's-complement integer can represent:

    -8 through 7

Attempting to represent `8` in this width produces an overflow condition.

The script raises:

    OverflowError

when a requested signed value does not fit.

---

## Shifting Beyond the Bit Length

For logical right shifting of an unsigned value:

    101 >> 10

the result is:

    0

The script explicitly handles this case.

---

# Testing and Verification

Arithmetic algorithms should be verified against known mathematical behavior.

The script contains verification functions for:

- Decimal-to-binary conversion
- Binary-to-decimal conversion
- Addition
- Subtraction
- Multiplication
- Division

The functions include:

    verify_binary_conversion()

    verify_binary_addition()

    verify_binary_subtraction()

    verify_binary_multiplication()

    verify_binary_division()

The tests compare manually implemented algorithms against Python's integer arithmetic.

---

# Division Verification Identity

For each valid division:

    dividend = divisor × quotient + remainder

The script verifies this identity.

It also checks:

    0 ≤ remainder < divisor

These conditions are stronger than merely comparing a quotient because they verify the mathematical structure of the division result.

---

# Performance Considerations

## Conversion

Binary-to-decimal conversion:

    O(n)

where `n` is the number of bits.

Decimal-to-binary conversion depends on the number of output bits and is effectively proportional to:

    O(log₂(value))

for a positive integer.

---

## Addition

Binary addition processes each bit once:

    O(max(n, m))

---

## Subtraction

Binary subtraction also processes each bit once:

    O(max(n, m))

---

## Long Multiplication

The educational long multiplication algorithm can require repeated addition of partial products.

For operands with lengths `n` and `m`, the straightforward approach has quadratic behavior in the general case.

More advanced multiplication algorithms exist for very large integers, but the implemented algorithm is appropriate for demonstrating binary arithmetic principles.

---

## Division

Long division processes the dividend bit by bit and performs comparison and possible subtraction.

The implementation prioritizes algorithmic clarity over low-level optimization.

Hardware division units may use specialized algorithms and circuits.

---

# Implementation Design Considerations

The script separates several responsibilities.

## Validation

Input correctness is handled before arithmetic operations.

## Normalization

Leading zeros are removed when an operation represents an unrestricted mathematical integer.

## Fixed Width

Functions requiring hardware-like behavior explicitly receive a width.

## Signed Interpretation

Two's-complement interpretation is kept separate from unsigned interpretation.

## Algorithmic Reuse

Addition supports:

- Direct binary arithmetic
- Two's-complement subtraction
- Long multiplication

Subtraction supports:

- Direct subtraction
- Long division

This reuse reflects the interconnected nature of arithmetic algorithms.

---

# Debugging Binary Arithmetic

Binary arithmetic bugs are often easier to diagnose when intermediate values are visible.

Useful debugging information includes:

- Current bit position
- Operand bits
- Carry-in
- Carry-out
- Borrow-in
- Borrow-out
- Partial remainder
- Partial product
- Fixed-width truncation

The script stores detailed addition and subtraction information using:

    AdditionStep

and:

    SubtractionStep

These data structures allow the arithmetic process to be inspected column by column.

---

# Practical Applications

Binary arithmetic is directly relevant to many areas of computing.

## Computer Processors

Arithmetic logic units perform operations based on binary addition, subtraction, multiplication, shifting, and logical operations.

## Memory Addressing

Memory addresses are binary values manipulated through arithmetic and bitwise operations.

## Networking

Network protocols use binary fields, masks, flags, sequence numbers, and checksums.

## Cryptography

Cryptographic systems frequently rely on modular arithmetic, bitwise operations, shifts, and fixed-width integer behavior.

## Digital Electronics

Adders, subtractors, registers, multiplexers, and arithmetic units operate directly on binary values.

## Embedded Systems

Embedded software often works with fixed-width registers and requires careful overflow handling.

## Operating Systems

Operating systems manipulate binary permissions, memory addresses, processor flags, and hardware registers.

## Data Encoding

Binary arithmetic is used when processing bytes, encoded values, compressed data, and binary file formats.

---

# Security Considerations

Binary arithmetic is relevant to security because incorrect arithmetic behavior can cause serious vulnerabilities.

Important issues include:

- Integer overflow
- Integer underflow
- Incorrect signed/unsigned conversion
- Improper bounds checking
- Truncation during fixed-width conversion
- Incorrect shift behavior
- Arithmetic errors in cryptographic implementations

A value that is valid in one interpretation may become dangerous when converted incorrectly.

For example, converting a negative signed value into an unsigned representation can produce a very large positive value.

Software dealing with memory allocation, buffer sizes, file lengths, packet lengths, and indexes must carefully validate arithmetic operations.

---

# Limitations of the Educational Implementations

The algorithms in the script prioritize transparency and correctness of binary arithmetic concepts.

They are not replacements for optimized arbitrary-precision arithmetic libraries or processor-level arithmetic instructions.

Important limitations include:

- Binary values are represented as Python strings for clarity.
- String manipulation introduces overhead.
- Multiplication is based on straightforward long multiplication and repeated addition.
- Division is based on long division concepts.
- Hardware timing behavior is not physically simulated.
- Carry propagation delay is explained conceptually rather than measured electronically.
- Python's arbitrary-precision integers are used in validation and testing.

These design choices make individual arithmetic mechanisms easier to inspect.

---

# Relationship Between Arithmetic Operations

The operations are strongly connected.

Binary addition is the central operation.

Subtraction can be transformed into:

    addition + two's complement

Multiplication can be transformed into:

    repeated shifted additions

Division can be understood through:

    repeated comparison and subtraction

Shifting is equivalent to multiplication or integer division by powers of 2 for appropriate unsigned values.

Bitwise XOR and AND can be combined to construct addition without directly using the ordinary addition operator.

These relationships explain why binary arithmetic is fundamental to processor architecture and digital computation.
