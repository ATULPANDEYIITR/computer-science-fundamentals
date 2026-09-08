# Signed Number Representation in Computer Systems

## Introduction

Digital computers store information as binary digits, commonly called bits. A bit can contain either `0` or `1`. Binary representation is straightforward for non-negative integers because each bit contributes a positive power of two. Representing negative integers is more complicated because the hardware must encode both magnitude and sign within a fixed number of bits.

This study program examines four important integer interpretations:

- Unsigned integers
- Sign-magnitude representation
- One's complement representation
- Two's complement representation

The Python script models these representations explicitly rather than relying only on Python's built-in integer behavior. Python integers normally have arbitrary precision, while computer processors usually work with fixed-width registers such as 8-bit, 16-bit, 32-bit, and 64-bit values.

The distinction between arbitrary-precision arithmetic and fixed-width arithmetic is essential because fixed-width systems can overflow, wrap around, truncate values, and interpret the same bit pattern differently depending on whether it is treated as signed or unsigned.

---

# Binary Fundamentals

## Bits and Bit Patterns

A bit is the smallest unit of binary information.

A sequence of bits forms a bit pattern. For example:

    1011

contains four bits.

The positions are associated with powers of two:

    1 × 2^3
    0 × 2^2
    1 × 2^1
    1 × 2^0

Therefore:

    1011₂ = 8 + 0 + 2 + 1 = 11₁₀

The rightmost bit is the least significant bit, abbreviated as LSB. The leftmost bit is the most significant bit, abbreviated as MSB.

For an unsigned integer with `n` bits, the bit positions represent:

    2^(n-1), 2^(n-2), ..., 2^1, 2^0

---

# Fixed-Width Storage

A fixed-width integer can contain only a limited number of bit patterns.

For `n` bits, the total number of possible patterns is:

    2^n

For example, an 8-bit register has:

    2^8 = 256

possible bit patterns.

The same collection of 256 patterns can be interpreted in different ways. The binary pattern:

    11111011

can represent:

- 251 as an unsigned integer
- -123 in sign-magnitude
- -4 in one's complement
- -5 in two's complement

The bit pattern itself does not contain an intrinsic mathematical meaning. The meaning comes from the representation rule used to interpret it.

This distinction is one of the central principles of signed number representation.

---

# Unsigned Integer Representation

Unsigned integers represent only non-negative values.

For an `n`-bit unsigned integer:

    Minimum = 0
    Maximum = 2^n - 1

For 8 bits:

    Minimum = 0
    Maximum = 255

The pattern:

    11111111

represents:

    255

because every bit contributes positively:

    128 + 64 + 32 + 16 + 8 + 4 + 2 + 1 = 255

The script implements unsigned conversion using fixed-width masks.

A mask containing `n` ones is calculated as:

    (1 << n) - 1

For 8 bits:

    (1 << 8) - 1
    = 256 - 1
    = 255
    = 11111111₂

Masking a value with this pattern keeps only the lowest `n` bits.

---

# Sign-Magnitude Representation

## Basic Principle

Sign-magnitude representation reserves the most significant bit for the sign.

The convention is:

- `0` in the sign bit means non-negative
- `1` in the sign bit means negative

The remaining bits represent the magnitude.

For an 8-bit value:

    00000101

represents:

    +5

The pattern:

    10000101

represents:

    -5

The first bit indicates negativity, while the remaining seven bits represent the magnitude `5`.

## Range

One bit is reserved for the sign, leaving `n - 1` bits for magnitude.

Therefore the range is:

    -(2^(n-1) - 1) to +(2^(n-1) - 1)

For 8 bits:

    -127 to +127

The range is symmetric around zero.

## The Negative Zero Problem

Sign-magnitude has two different representations of zero.

Positive zero:

    00000000

Negative zero:

    10000000

Both represent mathematical zero.

This creates an unnecessary duplicate representation. Arithmetic and comparison operations must handle two bit patterns representing the same mathematical value.

The Python script detects negative zero explicitly through the `is_negative_zero_sign_magnitude` function.

## Advantages

Sign-magnitude is conceptually simple because the sign and magnitude are visually separated.

It resembles familiar decimal notation:

    +25
    -25

## Limitations

Sign-magnitude arithmetic is inconvenient for hardware because addition and subtraction require special handling based on the signs of the operands.

The duplicate zero representation is another disadvantage.

Sign-magnitude is historically important and remains relevant in some specialized contexts, particularly floating-point sign fields, but it is not the standard representation for modern signed integer arithmetic.

---

# One's Complement Representation

## Basic Principle

One's complement represents a negative number by inverting every bit of its positive representation.

For example, using 8 bits:

    +5 = 00000101

Invert every bit:

    -5 = 11111010

The bitwise complement operation changes:

    0 → 1
    1 → 0

## Range

Like sign-magnitude, one's complement uses one bit position effectively as part of the signed representation and provides the range:

    -(2^(n-1) - 1) to +(2^(n-1) - 1)

For 8 bits:

    -127 to +127

## Two Representations of Zero

One's complement also has positive and negative zero.

Positive zero:

    00000000

Negative zero:

    11111111

The negative zero problem complicates comparisons and arithmetic.

The script demonstrates this condition with the `is_negative_zero_ones_complement` function.

---

# One's Complement Addition

One's complement arithmetic uses a special rule called end-around carry.

Suppose addition produces a carry beyond the fixed-width register.

The carry is not discarded. It is added back to the least significant position.

Conceptually:

    Carry beyond MSB + lower result

For example:

    1111
    0001
    ----
   10000

The lower four bits are:

    0000

The carry is:

    1

End-around carry produces:

    0000 + 1 = 0001

The script implements this process in `ones_complement_add`.

A loop is used because adding the end-around carry could theoretically produce another carry in larger generalized arithmetic operations.

---

# Two's Complement Representation

## Basic Principle

Two's complement is the standard representation for signed integers in modern computer systems.

A negative value can be produced from a positive value by:

1. Inverting all bits
2. Adding one

For example, with 8 bits:

    +5 = 00000101

Invert:

    11111010

Add one:

    11111011

Therefore:

    11111011 = -5

## Mathematical Interpretation

For an `n`-bit two's complement number:

- If the most significant bit is `0`, the value is non-negative.
- If the most significant bit is `1`, subtract `2^n` from the unsigned interpretation.

For an 8-bit pattern:

    11111011

Unsigned interpretation:

    251

Since the sign bit is set:

    251 - 256 = -5

This is implemented by:

    pattern - (1 << bits)

when the sign bit is set.

---

# Two's Complement Range

For `n` bits:

    Minimum = -2^(n-1)
    Maximum = 2^(n-1) - 1

For 8 bits:

    Minimum = -128
    Maximum = +127

Unlike sign-magnitude and one's complement, the range is asymmetric.

The negative side contains one additional value.

This happens because two's complement does not waste a bit pattern on negative zero.

For 8 bits:

    00000000 = 0

There is no second zero representation.

The extra negative pattern becomes:

    10000000 = -128

---

# Why Two's Complement Is Used

Two's complement has several important advantages.

## One Representation of Zero

Only:

    00000000

represents zero.

## Addition Uses Ordinary Binary Addition

The same binary adder can add both signed and unsigned integers.

The hardware simply adds bit patterns.

For example, in 8 bits:

    +5 = 00000101
    -5 = 11111011

Adding them:

    00000101
    11111011
    --------
   100000000

The lower eight bits are:

    00000000

which represents zero.

The carry beyond the selected width is discarded.

## Subtraction Becomes Addition

The expression:

    A - B

can be implemented as:

    A + (-B)

The negative value is generated through bit inversion and addition of one.

This simplifies arithmetic logic unit design.

---

# The Most Negative Value

Two's complement contains a subtle edge case.

For 8 bits:

    -128 = 10000000

The positive range ends at:

    +127 = 01111111

Therefore positive `128` cannot be represented using 8-bit signed two's complement.

Negating `-128` within eight bits produces:

    10000000

again.

The process is:

    10000000

Invert:

    01111111

Add one:

    10000000

The mathematical result should be `+128`, but that value does not fit.

The fixed-width result therefore wraps to the same bit pattern.

This is an important edge case in programming languages and low-level systems.

---

# Signed Integer Overflow

Overflow occurs when the correct mathematical result cannot fit within the selected fixed width.

For 8-bit two's complement:

    Maximum = 127

Therefore:

    127 + 1 = 128

cannot be represented.

The stored bit pattern becomes:

    10000000

which represents:

    -128

This is wraparound at the bit level.

## Signed Addition Overflow Rule

Signed overflow occurs when:

- two positive operands produce a negative result, or
- two negative operands produce a positive result

Examples:

    127 + 1

Both operands are positive, but the result pattern has a negative sign.

Overflow occurred.

Similarly:

    -128 + -1

Both operands are negative, but the fixed-width result becomes positive.

Overflow occurred.

The script implements this detection in `twos_complement_add`.

---

# Carry and Overflow Are Different

A carry out of the most significant bit is not identical to signed overflow.

Carry is primarily associated with unsigned arithmetic.

Signed overflow depends on the sign relationship between operands and result.

For signed arithmetic, examining only the final carry bit is not sufficient to detect overflow.

The script therefore checks the signs of:

- the first operand
- the second operand
- the result

This distinction is fundamental in processor arithmetic.

---

# Two's Complement Subtraction

Subtraction is performed by negating the second operand and adding it.

Mathematically:

    A - B = A + (-B)

At the bit level:

    -B = (~B) + 1

The script implements this sequence in:

- `negate_twos_complement`
- `twos_complement_subtract`

The implementation models the same principle used in arithmetic hardware.

---

# Sign Extension

When a signed integer is moved to a larger width, its mathematical value should normally be preserved.

This requires sign extension.

Suppose a 4-bit number is:

    1101

In two's complement, this represents:

    -3

To convert it to 8 bits, the new high bits must repeat the sign bit:

    11111101

This still represents:

    -3

For negative values, the added bits are ones.

For non-negative values, the added bits are zeros.

The script implements this behavior in `sign_extend`.

---

# Zero Extension

Zero extension adds zeros to the high-order side.

For an unsigned value:

    1101

extended from 4 bits to 8 bits becomes:

    00001101

As an unsigned value, this preserves the numerical value `13`.

For a signed two's complement interpretation, the original 4-bit value was `-3`, while the zero-extended 8-bit pattern represents `13`.

Therefore zero extension is appropriate for unsigned values but generally not for preserving signed negative values.

The script demonstrates both sign extension and zero extension.

---

# Truncation

Truncation occurs when a value is reduced to a smaller number of bits.

Only the lower bits are retained.

For example, if an 8-bit value is reduced to 4 bits, the upper four bits are discarded.

The operation can be modeled as:

    value & ((1 << bits) - 1)

Truncation can change:

- magnitude
- sign
- numerical meaning

A value that fits in a larger signed width may not fit in a smaller signed width.

---

# Logical and Arithmetic Shifts

## Logical Right Shift

A logical right shift inserts zeros from the left.

Example:

    10000000 >> 1

becomes:

    01000000

This operation treats the bit pattern as an unsigned sequence.

## Arithmetic Right Shift

An arithmetic right shift preserves the sign.

For a negative two's complement number, ones are inserted at the left.

Example:

    10000000

arithmetic right shifted by one becomes:

    11000000

The result remains negative.

The script implements arithmetic right shift by:

1. Decoding the fixed-width bit pattern as a signed integer.
2. Applying Python's arithmetic right shift.
3. Masking the result back to the original width.

---

# Left Shifts and Overflow

A left shift moves bits toward more significant positions.

For fixed-width values, bits shifted beyond the selected width are discarded.

The script models this behavior by masking the result.

A left shift can cause information loss.

For example, an 8-bit value shifted left may produce a mathematical result outside the 8-bit range.

This can create overflow or change the sign of a signed value.

A left shift should therefore not automatically be treated as multiplication by two unless the resulting value remains representable.

---

# Bitwise Operations and Signed Integers

Bitwise operations manipulate bit patterns directly.

The important operations are:

- AND
- OR
- XOR
- NOT

The hardware operation does not depend on whether a number is considered signed.

Signedness affects interpretation.

For example, the bit pattern resulting from an AND operation can be interpreted as:

- an unsigned integer
- a two's complement signed integer
- another encoded value

The script demonstrates bitwise operations using fixed-width two's complement patterns and then decodes the results as signed integers.

---

# Representation Comparison

The script generates complete tables for small bit widths.

A 4-bit table is especially useful because all possible patterns can be examined manually.

The same pattern may have different meanings.

For example:

    1000

can represent:

- 8 as unsigned
- 0 with negative sign in sign-magnitude
- -7 in one's complement
- -8 in two's complement

This illustrates why a binary pattern must always be interpreted according to its representation.

---

# Binary Addition Process

The script includes a bit-by-bit addition simulation.

Each bit position records:

- first operand bit
- second operand bit
- carry entering the position
- resulting sum bit
- carry leaving the position

For each position:

    total = a_bit + b_bit + carry_in

The resulting bit is:

    total modulo 2

The outgoing carry is:

    total divided by 2 using integer division

This directly models binary addition.

The simulation processes bits from the least significant position toward the most significant position.

---

# FixedWidthInt Class

The `FixedWidthInt` class models a simplified fixed-width two's complement integer.

Unlike Python's built-in integers, it stores only a limited number of bits.

Its internal state is always masked to the configured width.

The class provides:

- signed interpretation
- unsigned interpretation
- binary representation
- addition
- subtraction
- negation
- overflow reporting

This design demonstrates an important implementation principle: the stored data can remain a bit pattern while multiple properties expose different interpretations.

For example, one stored pattern can have both:

- a signed numerical value
- an unsigned numerical value

The difference is interpretation, not physical storage.

---

# Arithmetic Wrapping

Fixed-width hardware arithmetic usually retains only the available number of bits.

If an operation produces more bits than the register can store, the extra high-order bits are discarded.

This is modeled by:

    result & mask

For an 8-bit register:

    mask = 255

Therefore every result is reduced to the range:

    0 through 255

before being interpreted as signed or unsigned.

This is modular arithmetic modulo:

    2^n

For an 8-bit register:

    modulo 256

Two's complement arithmetic is therefore closely related to arithmetic in the ring of integers modulo `2^n`.

---

# Common Mistake: Confusing Storage With Interpretation

The pattern:

    11111011

is only a sequence of bits.

It does not automatically mean `-5`.

Its meaning depends on interpretation.

As unsigned:

    251

As two's complement:

    -5

As one's complement:

    -4

Correct low-level programming requires knowledge of both:

- bit width
- signed representation

---

# Common Mistake: Assuming All Signed Formats Have the Same Range

For 8 bits:

Sign-magnitude:

    -127 to +127

One's complement:

    -127 to +127

Two's complement:

    -128 to +127

Two's complement uses every available bit pattern for a unique integer.

Sign-magnitude and one's complement use two patterns for zero.

---

# Common Mistake: Ignoring Negative Zero

Sign-magnitude and one's complement have two zeros.

Programs or systems using these formats must define how comparisons treat:

- positive zero
- negative zero

The values are mathematically equal but have different bit patterns.

Two's complement avoids this problem.

---

# Common Mistake: Assuming Negation Always Changes the Value

For most two's complement values:

    negate(negate(x)) = x

The most negative value is a special case.

For an `n`-bit value:

    -2^(n-1)

cannot be represented as a positive number within the same width.

Negation therefore wraps to the same pattern.

---

# Common Mistake: Using Zero Extension for Signed Negative Values

Consider the 4-bit pattern:

    1101

As two's complement:

    -3

Zero extension:

    00001101

As 8-bit two's complement:

    +13

Sign extension:

    11111101

As 8-bit two's complement:

    -3

Signed negative values require sign extension to preserve meaning.

---

# Validation and Testing

The script includes automated assertions.

The tests verify round-trip conversion:

    integer → bit pattern → integer

for:

- sign-magnitude
- one's complement
- two's complement

The test suite also checks:

- sign extension
- signed overflow
- valid arithmetic
- fixed-width object behavior

Small bit widths are tested exhaustively across their complete representable ranges.

Exhaustive testing is practical for small finite domains and is particularly effective for verifying encoding algorithms.

---

# Performance Considerations

The algorithms in the script operate primarily on Python integers and bitwise operations.

Most conversions are constant-time with respect to normal machine-sized integer widths.

The representation table generation requires:

    2^n

iterations because every bit pattern is examined.

This is practical for small values such as 4 or 8 bits but becomes expensive for large widths.

For example:

    2^4 = 16
    2^8 = 256
    2^16 = 65,536
    2^32 = 4,294,967,296

Generating complete tables for 32-bit representations is computationally impractical.

The script therefore uses exhaustive tables only as an educational mechanism for small widths.

---

# Implementation Considerations

The script consistently masks bit patterns before interpreting them.

This is important because Python integers are not naturally restricted to a fixed width.

For a fixed-width simulation:

    pattern & ((1 << bits) - 1)

removes all bits outside the selected width.

This behavior is necessary to accurately model:

- registers
- integer overflow
- truncation
- bitwise NOT
- fixed-width arithmetic

Without explicit masking, Python's arbitrary-precision integer model would not behave like a fixed-width processor register.

---

# Security and Reliability Considerations

Signed integer representation can create correctness and security issues when software mixes:

- signed values
- unsigned values
- different integer widths

Potential problems include:

- incorrect range validation
- unexpected conversion behavior
- integer overflow
- integer underflow
- incorrect comparison results
- truncation of security-sensitive values
- sign extension errors

A value should be validated before conversion to a smaller or differently signed type.

Program logic should not assume that a value retains its mathematical meaning after:

- truncation
- reinterpretation
- signed-to-unsigned conversion
- unsigned-to-signed conversion

Critical systems should explicitly define integer widths and conversion behavior.

---

# Real-World Applications

Signed number representation is fundamental to computer architecture and systems programming.

It is relevant to:

- processor arithmetic logic units
- assembly language
- operating systems
- embedded systems
- network protocols
- binary file formats
- compiler implementation
- device drivers
- cryptographic software
- digital signal processing
- numerical computing

Two's complement is especially important because modern processors typically implement signed integer arithmetic using this representation.

Understanding the representation makes it possible to explain behavior such as:

- why `11111111` can represent `255` or `-1`
- why overflow changes the stored result
- why `-128` is special in 8-bit arithmetic
- why signed extension repeats the sign bit
- why subtraction can be implemented using addition
- why the same binary adder can process signed and unsigned operands

The script models these behaviors explicitly and connects the mathematical definitions of signed representation with practical fixed-width binary operations.
