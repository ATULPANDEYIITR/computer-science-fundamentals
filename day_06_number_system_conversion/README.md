# Number System Conversion

## Topic

**Number System Conversion: Decimal to Binary, Binary to Decimal, Octal Conversion, Hexadecimal Conversion, and Shortcuts**

This document accompanies the Python study script and explains the mathematical principles, algorithms, implementation techniques, shortcuts, edge cases, and practical applications of positional number systems.

---

## 1. Number Systems and Bases

A number system defines how numerical values are represented using a fixed collection of digits and a base.

The base determines the value contributed by each position.

For a positional number system with base \(b\):

\[
d_n d_{n-1} \dots d_1 d_0
\]

represents:

\[
d_n b^n + d_{n-1}b^{n-1} + \dots + d_1b^1 + d_0b^0
\]

The most important number systems in computing are:

| Number System | Base | Valid Digits |
|---|---:|---|
| Binary | 2 | 0, 1 |
| Octal | 8 | 0–7 |
| Decimal | 10 | 0–9 |
| Hexadecimal | 16 | 0–9, A–F |

Decimal is the ordinary human number system. Binary is fundamental to digital computing. Octal and hexadecimal provide compact representations of binary values.

---

## 2. Positional Notation

Consider the decimal number:

\[
582_{10}
\]

Its expanded form is:

\[
5(10^2)+8(10^1)+2(10^0)
\]

\[
=500+80+2
\]

\[
=582
\]

The same principle works in every base.

For example:

\[
101101_2
\]

is:

\[
1(2^5)+0(2^4)+1(2^3)+1(2^2)+0(2^1)+1(2^0)
\]

\[
=32+8+4+1
\]

\[
=45_{10}
\]

The digits themselves do not determine the value without knowing the base.

---

## 3. Binary Number System

Binary is base 2 and has only two digits:

- `0`
- `1`

Each position represents a power of two.

The first powers are:

| Power | Value |
|---:|---:|
| \(2^0\) | 1 |
| \(2^1\) | 2 |
| \(2^2\) | 4 |
| \(2^3\) | 8 |
| \(2^4\) | 16 |
| \(2^5\) | 32 |
| \(2^6\) | 64 |
| \(2^7\) | 128 |
| \(2^8\) | 256 |

For example:

\[
1101_2
\]

equals:

\[
8+4+1=13
\]

Therefore:

\[
1101_2=13_{10}
\]

---

## 4. Decimal to Binary

### Repeated Division by 2

The standard algorithm for converting a non-negative decimal integer to binary is repeated division by 2.

For every iteration:

1. Divide the current value by 2.
2. Record the remainder.
3. Replace the current value with the quotient.
4. Continue until the quotient becomes zero.
5. Read the remainders from bottom to top.

For 13:

| Current Value | Quotient | Remainder |
|---:|---:|---:|
| 13 | 6 | 1 |
| 6 | 3 | 0 |
| 3 | 1 | 1 |
| 1 | 0 | 1 |

Reading the remainders upward gives:

\[
1101_2
\]

Therefore:

\[
13_{10}=1101_2
\]

The Python implementation `decimal_to_binary_division()` implements this algorithm directly.

---

## 5. Decimal to Binary Using Powers of Two

Another useful method is to identify which powers of two make up the number.

For 45:

\[
45=32+8+4+1
\]

The relevant powers are:

| Power | 32 | 16 | 8 | 4 | 2 | 1 |
|---|---:|---:|---:|---:|---:|---:|
| Present? | 1 | 0 | 1 | 1 | 0 | 1 |

Therefore:

\[
45_{10}=101101_2
\]

This approach is especially useful for manual examination problems.

---

## 6. Binary to Decimal

### Positional Expansion

To convert binary to decimal, multiply every binary digit by its corresponding power of two.

For:

\[
101101_2
\]

we get:

\[
1(2^5)+0(2^4)+1(2^3)+1(2^2)+0(2^1)+1(2^0)
\]

\[
=32+8+4+1
\]

\[
=45
\]

The script implements this as `binary_to_decimal_positional()`.

---

## 7. Binary to Decimal Using Horner's Method

A more efficient computational approach is to process the digits from left to right.

For each digit:

\[
value = value\times2 + digit
\]

For `101101`:

\[
0\times2+1=1
\]

\[
1\times2+0=2
\]

\[
2\times2+1=5
\]

\[
5\times2+1=11
\]

\[
11\times2+0=22
\]

\[
22\times2+1=45
\]

Therefore:

\[
101101_2=45_{10}
\]

This is the binary-specific form of Horner's method for evaluating a polynomial.

---

## 8. Generic Base-to-Decimal Conversion

The same positional principle works for any base.

For a number represented in base \(b\):

\[
d_nd_{n-1}\dots d_0
\]

the value can be calculated iteratively using:

\[
value=value\times b+d
\]

This avoids explicitly calculating every power.

The script generalizes this concept through `base_to_decimal()`.

For example:

- `101101` base 2 becomes 45
- `157` base 8 becomes 111
- `2AF` base 16 becomes 687

---

## 9. Decimal to an Arbitrary Base

Decimal-to-base conversion uses repeated division by the target base.

For hexadecimal conversion, divide repeatedly by 16.

For 687:

\[
687\div16=42\text{ remainder }15
\]

\[
42\div16=2\text{ remainder }10
\]

\[
2\div16=0\text{ remainder }2
\]

The remainder values are:

- 15 = F
- 10 = A
- 2 = 2

Read upward:

\[
687_{10}=2AF_{16}
\]

The general implementation is `decimal_to_base()`.

---

## 10. Octal Number System

Octal is base 8.

Its valid digits are:

`0 1 2 3 4 5 6 7`

The positional weights are powers of eight:

\[
8^0=1
\]

\[
8^1=8
\]

\[
8^2=64
\]

\[
8^3=512
\]

For example:

\[
157_8
\]

means:

\[
1(8^2)+5(8^1)+7(8^0)
\]

\[
=64+40+7
\]

\[
=111_{10}
\]

---

## 11. Octal to Decimal

Octal-to-decimal conversion follows the same positional rule.

For:

\[
725_8
\]

the value is:

\[
7(8^2)+2(8^1)+5(8^0)
\]

\[
=448+16+5
\]

\[
=469_{10}
\]

The script performs this using the generic base conversion mechanism with base 8.

---

## 12. Decimal to Octal

Repeated division by 8 is used.

For example, to convert 45:

\[
45\div8=5\text{ remainder }5
\]

\[
5\div8=0\text{ remainder }5
\]

Reading upward:

\[
45_{10}=55_8
\]

The same algorithm used for decimal-to-binary conversion therefore works for octal when the divisor changes from 2 to 8.

---

## 13. Binary and Octal Shortcut

The most important octal shortcut comes from:

\[
8=2^3
\]

Therefore, one octal digit corresponds exactly to three binary bits.

### Mapping

| Octal | Binary |
|---:|---:|
| 0 | 000 |
| 1 | 001 |
| 2 | 010 |
| 3 | 011 |
| 4 | 100 |
| 5 | 101 |
| 6 | 110 |
| 7 | 111 |

For:

\[
1101011_2
\]

group from the **right** into groups of three:

\[
1\ |\ 101\ |\ 011
\]

Pad the first group on the left:

\[
001\ |\ 101\ |\ 011
\]

Convert each group:

\[
001=1
\]

\[
101=5
\]

\[
011=3
\]

Therefore:

\[
1101011_2=153_8
\]

---

## 14. Why Binary Must Be Grouped from the Right

The rightmost binary bit is the least significant bit.

Octal and hexadecimal grouping is based on powers of two, so groups must begin at the least significant side.

For example:

`101101`

correct octal grouping is:

`101 | 101`

not:

`101 | 101`

In cases where the length is not divisible by three, padding is added to the **left**, never the right.

For example:

`1010`

becomes:

`001 | 010`

and therefore:

\[
1010_2=12_8
\]

---

## 15. Hexadecimal Number System

Hexadecimal is base 16.

It requires sixteen symbols:

| Decimal Value | Hexadecimal |
|---:|---:|
| 0 | 0 |
| 1 | 1 |
| 2 | 2 |
| 3 | 3 |
| 4 | 4 |
| 5 | 5 |
| 6 | 6 |
| 7 | 7 |
| 8 | 8 |
| 9 | 9 |
| 10 | A |
| 11 | B |
| 12 | C |
| 13 | D |
| 14 | E |
| 15 | F |

The letters are case-insensitive for numerical parsing.

Thus:

\[
A_{16}=10_{10}
\]

and:

\[
F_{16}=15_{10}
\]

---

## 16. Hexadecimal to Decimal

For:

\[
2AF_{16}
\]

expand using powers of 16:

\[
2(16^2)+A(16^1)+F(16^0)
\]

Substitute the values:

\[
2(256)+10(16)+15
\]

\[
=512+160+15
\]

\[
=687
\]

Therefore:

\[
2AF_{16}=687_{10}
\]

---

## 17. Decimal to Hexadecimal

Repeated division by 16 is used.

For 687:

| Current Value | Quotient | Remainder |
|---:|---:|---:|
| 687 | 42 | 15 = F |
| 42 | 2 | 10 = A |
| 2 | 0 | 2 |

Read the remainders upward:

\[
2AF_{16}
\]

Therefore:

\[
687_{10}=2AF_{16}
\]

---

## 18. Binary and Hexadecimal Shortcut

The key relationship is:

\[
16=2^4
\]

Therefore, every hexadecimal digit represents exactly four binary bits.

### Mapping

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

For:

\[
101101011_2
\]

pad from the left:

\[
0001\ |\ 0110\ |\ 1011
\]

Therefore:

\[
1\ |\ 6\ |\ B
\]

and:

\[
101101011_2=16B_{16}
\]

---

## 19. Hexadecimal to Binary

The reverse shortcut is even easier.

Replace every hexadecimal digit with four binary bits.

For:

\[
2AF_{16}
\]

use:

\[
2=0010
\]

\[
A=1010
\]

\[
F=1111
\]

Therefore:

\[
2AF_{16}=001010101111_2
\]

Leading zeroes can be removed when fixed width is not required:

\[
1010101111_2
\]

The script implements this using `hexadecimal_to_binary()`.

---

## 20. Octal to Hexadecimal

There is no equally direct one-digit grouping between octal and hexadecimal because:

\[
8=2^3
\]

while:

\[
16=2^4
\]

Their common relationship is binary.

Therefore:

\[
\text{Octal}\rightarrow\text{Binary}\rightarrow\text{Hexadecimal}
\]

For example:

\[
55_8
\]

becomes:

\[
101101_2
\]

and then:

\[
2D_{16}
\]

Thus:

\[
55_8=2D_{16}
\]

---

## 21. Hexadecimal to Octal

The reverse process is:

\[
\text{Hexadecimal}\rightarrow\text{Binary}\rightarrow\text{Octal}
\]

For example:

\[
2D_{16}
\]

becomes:

\[
0010\ |\ 1101
\]

which gives:

\[
101101_2
\]

Group into three bits:

\[
101\ |\ 101
\]

Therefore:

\[
55_8
\]

---

## 22. The Most Important Shortcuts

### Decimal to Binary

Repeated division by 2.

### Decimal to Octal

Repeated division by 8.

### Decimal to Hexadecimal

Repeated division by 16.

### Binary to Decimal

Use powers of 2 or Horner's method.

### Octal to Decimal

Use powers of 8.

### Hexadecimal to Decimal

Use powers of 16.

### Binary to Octal

Group three bits at a time from the right.

### Octal to Binary

Replace each octal digit with three bits.

### Binary to Hexadecimal

Group four bits at a time from the right.

### Hexadecimal to Binary

Replace each hexadecimal digit with four bits.

### Octal to Hexadecimal

Convert through binary.

### Hexadecimal to Octal

Convert through binary.

---

## 23. General Power-of-Two Rule

The shortcuts are consequences of powers of two.

If:

\[
base=2^k
\]

then one digit in that base corresponds to exactly \(k\) binary bits.

Examples:

| Base | Relationship | Binary Bits per Digit |
|---:|---:|---:|
| 2 | \(2^1\) | 1 |
| 4 | \(2^2\) | 2 |
| 8 | \(2^3\) | 3 |
| 16 | \(2^4\) | 4 |
| 32 | \(2^5\) | 5 |

This is the mathematical reason binary-to-octal and binary-to-hexadecimal shortcuts work.

---

## 24. Leading Zeroes

Leading zeroes do not normally change numerical value.

For example:

\[
101_2=00000101_2
\]

Both represent 5.

The difference becomes important when a fixed width is required.

An 8-bit representation of 5 is:

`00000101`

A 16-bit representation is:

`0000000000000101`

The value is identical, but the representation contains different amounts of storage information.

The script provides `format_fixed_width_binary()` for this purpose.

---

## 25. Bit Length

The number of bits needed for a positive unsigned integer is:

\[
\lfloor\log_2(n)\rfloor+1
\]

For example:

\[
8=1000_2
\]

requires four bits.

\[
7=111_2
\]

requires three bits.

Python's `int.bit_length()` exposes this concept directly.

Zero is a special case in Python:

`0.bit_length()` is 0, even though the written representation of zero is normally one binary digit: `0`.

---

## 26. Binary and Bitwise Operations

Binary representation is directly connected to bitwise operations.

The principal operators are:

| Operator | Meaning |
|---|---|
| `&` | AND |
| `|` | OR |
| `^` | XOR |
| `~` | NOT |
| `<<` | Left shift |
| `>>` | Right shift |

For example:

\[
12=1100_2
\]

\[
5=0101_2
\]

AND:

\[
1100
\]

AND

\[
0101
\]

gives:

\[
0100=4
\]

OR gives:

\[
1101=13
\]

XOR gives:

\[
1001=9
\]

These operations are central to low-level programming, bit masks, permissions, flags, protocols, and systems programming.

---

## 27. Bit Shifting

For non-negative integers:

\[
n<<k=n\times2^k
\]

For example:

\[
5<<2=20
\]

because:

\[
5\times4=20
\]

Right shifting a non-negative integer corresponds to integer division by a power of two:

\[
n>>k=\left\lfloor\frac{n}{2^k}\right\rfloor
\]

For example:

\[
20>>2=5
\]

The binary representation makes the operation intuitive:

`10100`

shift right by two positions:

`00101`

which represents 5.

---

## 28. Negative Numbers and Two's Complement

Positive integer conversion alone is insufficient for understanding machine-level representation.

Computers commonly represent signed integers using **two's complement**.

For an \(n\)-bit signed two's-complement integer, the range is:

\[
-2^{n-1}
\]

through:

\[
2^{n-1}-1
\]

For eight bits:

\[
-128\text{ through }127
\]

### Representing -5

Start with +5:

`00000101`

Invert every bit:

`11111010`

Add 1:

`11111011`

Therefore, in eight-bit two's complement:

\[
-5=11111011_2
\]

The script implements this explicitly with `signed_to_twos_complement()`.

---

## 29. Two's-Complement Decoding

For an eight-bit value beginning with `0`, the value is interpreted as a non-negative integer.

For a value beginning with `1`, subtract:

\[
2^8
\]

from the unsigned interpretation.

For:

`11111011`

the unsigned value is:

\[
251
\]

Then:

\[
251-256=-5
\]

Therefore:

\[
11111011_2=-5
\]

under eight-bit two's-complement interpretation.

---

## 30. Python Integers and Fixed Width

Python integers have arbitrary precision.

They are not automatically restricted to:

- 8 bits
- 16 bits
- 32 bits
- 64 bits

Consequently, Python's integer representation should not automatically be interpreted as a particular machine word.

When a fixed-width representation is required, the width must be explicitly specified.

This distinction is important in:

- systems programming
- networking
- cryptography
- binary file processing
- embedded programming
- hardware interfaces
- serialization

---

## 31. Unsigned and Signed Ranges

For an unsigned \(n\)-bit integer:

\[
0\leq x\leq2^n-1
\]

For a signed two's-complement \(n\)-bit integer:

\[
-2^{n-1}\leq x\leq2^{n-1}-1
\]

Examples:

| Width | Unsigned Range | Signed Two's Complement |
|---:|---|---|
| 4 | 0 to 15 | -8 to 7 |
| 8 | 0 to 255 | -128 to 127 |
| 16 | 0 to 65535 | -32768 to 32767 |
| 32 | 0 to 4294967295 | -2147483648 to 2147483647 |
| 64 | 0 to \(2^{64}-1\) | \(-2^{63}\) to \(2^{63}-1\) |

---

## 32. Fractional Number Conversion

Integer conversion and fractional conversion use different procedures.

### Decimal Fraction to Another Base

Repeated multiplication is used.

For:

\[
0.625_{10}
\]

multiply by 2:

\[
0.625\times2=1.25
\]

Record the integer part:

`1`

Continue with the fractional part:

\[
0.25\times2=0.5
\]

Record:

`0`

Then:

\[
0.5\times2=1.0
\]

Record:

`1`

Therefore:

\[
0.625_{10}=0.101_2
\]

---

## 33. Repeating Fractions

Not every decimal fraction has a finite binary representation.

For example:

\[
0.1_{10}
\]

has a repeating binary representation.

This happens because a finite representation in base \(b\) exists only when the denominator, after reduction, contains prime factors compatible with \(b\).

For binary, the only prime factor available is 2.

Since:

\[
\frac{1}{10}=\frac{1}{2\times5}
\]

contains the factor 5, it cannot be represented as a finite binary fraction.

This distinction is important when studying floating-point arithmetic.

---

## 34. Fractional Base-to-Decimal Conversion

A value such as:

\[
101.101_2
\]

contains both integer and fractional positions.

The integer portion is:

\[
1(2^2)+0(2^1)+1(2^0)
\]

The fractional portion is:

\[
1(2^{-1})+0(2^{-2})+1(2^{-3})
\]

Therefore:

\[
4+1+\frac12+\frac18
\]

\[
=5.625
\]

The script implements this behavior with `base_fraction_to_decimal()`.

---

## 35. Python Built-in Conversion Functions

Python provides built-in facilities for common bases.

For decimal 45:

- `bin(45)` produces a binary representation with a `0b` prefix.
- `oct(45)` produces an octal representation with a `0o` prefix.
- `hex(45)` produces a hexadecimal representation with a `0x` prefix.

The `int()` function can parse values when a source base is supplied.

Examples conceptually include:

- binary string with base 2
- octal string with base 8
- hexadecimal string with base 16

The manual functions in the study script are still valuable because they expose the actual mathematical algorithms rather than hiding them behind library functions.

For production code, built-ins are normally preferable when they satisfy the requirements.

---

## 36. Prefixes

Common programming-language prefixes include:

| Prefix | Meaning |
|---|---|
| `0b` | Binary |
| `0o` | Octal |
| `0x` | Hexadecimal |

Examples:

- `0b1010`
- `0o12`
- `0xA`

The script provides `parse_prefixed_integer()` to demonstrate explicit prefix handling.

Prefix handling should not be confused with the underlying mathematical base. The prefix is a notation convention used by programming languages.

---

## 37. Generic Base Conversion

The script supports bases from 2 through 36.

The digit alphabet is:

`0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ`

Therefore:

- A represents 10
- B represents 11
- ...
- Z represents 35

This allows conversions such as:

\[
Z_{36}=35_{10}
\]

The generic conversion functions demonstrate that binary, octal, decimal, and hexadecimal are specific cases of a broader positional-number framework.

---

## 38. Arbitrary Base-to-Base Conversion

A general conversion can be performed in two stages:

\[
\text{Source Base}\rightarrow\text{Decimal Value}\rightarrow\text{Target Base}
\]

For example:

\[
101101_2
\]

becomes:

\[
45_{10}
\]

and then:

\[
2D_{16}
\]

Therefore:

\[
101101_2=2D_{16}
\]

The mathematical intermediate value is what matters. Decimal is a convenient conceptual intermediate representation.

The script implements this using `convert_integer()`.

---

## 39. Manual Binary Addition

Binary addition follows the same carry principle as decimal addition.

Basic cases include:

| A | B | Carry In | Sum | Carry Out |
|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 | 0 |
| 0 | 0 | 1 | 1 | 0 |
| 0 | 1 | 0 | 1 | 0 |
| 1 | 1 | 0 | 0 | 1 |
| 1 | 1 | 1 | 1 | 1 |

For example:

```text
  101
+ 011
-----
 1000
