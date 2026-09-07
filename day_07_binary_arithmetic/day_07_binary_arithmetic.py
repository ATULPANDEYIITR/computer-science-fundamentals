"""
Binary Arithmetic: A Comprehensive Study Script
================================================

This self-contained script teaches binary arithmetic from beginner to advanced
concepts, including:

- Binary number representation
- Decimal and binary conversion
- Binary addition
- Carry operations
- Binary subtraction
- Borrow operations
- Ones' complement and two's complement
- Signed binary integers
- Binary multiplication
- Shift-and-add multiplication
- Binary division
- Long division
- Restoring division
- Edge cases and error handling
- Overflow and fixed-width arithmetic
- Bitwise operations related to binary arithmetic
- Algorithms, validation, testing, and debugging considerations
- Practical computer architecture concepts

The script uses only Python's standard library.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


# =============================================================================
# SECTION 1: FUNDAMENTALS OF BINARY NUMBERS
# =============================================================================

def validate_binary(binary: str) -> None:
    """
    Validate a binary string.

    A binary number may optionally begin with '+' or '-'.
    Remaining characters must be only '0' or '1'.

    Examples:
        "1011"   -> valid
        "-1011"  -> valid
        "+1011"  -> valid
        "1021"   -> invalid
        ""       -> invalid
    """
    if not isinstance(binary, str):
        raise TypeError("Binary values must be provided as strings.")

    if not binary:
        raise ValueError("Binary string cannot be empty.")

    digits = binary

    if binary[0] in "+-":
        if len(binary) == 1:
            raise ValueError("A sign without binary digits is invalid.")
        digits = binary[1:]

    if any(bit not in "01" for bit in digits):
        raise ValueError(
            f"Invalid binary number {binary!r}. "
            "Only the digits 0 and 1 are allowed."
        )


def normalize_binary(binary: str) -> str:
    """
    Remove unnecessary leading zeros from an unsigned binary string.

    Examples:
        "000101" -> "101"
        "0000"   -> "0"
    """
    validate_binary(binary)

    if binary[0] in "+-":
        raise ValueError("normalize_binary expects an unsigned binary string.")

    normalized = binary.lstrip("0")
    return normalized if normalized else "0"


def binary_to_decimal_manual(binary: str) -> int:
    """
    Convert a binary string to decimal without using int(binary, 2).

    Binary positional notation:

        1011₂

        = 1 * 2³
        + 0 * 2²
        + 1 * 2¹
        + 1 * 2⁰

        = 8 + 0 + 2 + 1
        = 11
    """
    validate_binary(binary)

    sign = 1

    if binary[0] == "-":
        sign = -1
        binary = binary[1:]
    elif binary[0] == "+":
        binary = binary[1:]

    decimal_value = 0

    for bit in binary:
        # Shift the existing value one binary position to the left,
        # then add the incoming bit.
        decimal_value = decimal_value * 2 + (1 if bit == "1" else 0)

    return sign * decimal_value


def decimal_to_binary_manual(number: int) -> str:
    """
    Convert an integer to binary using repeated division by 2.

    Example for 13:

        13 / 2 -> quotient 6, remainder 1
         6 / 2 -> quotient 3, remainder 0
         3 / 2 -> quotient 1, remainder 1
         1 / 2 -> quotient 0, remainder 1

    Reading remainders from bottom to top:

        1101
    """
    if not isinstance(number, int):
        raise TypeError("decimal_to_binary_manual expects an integer.")

    if number == 0:
        return "0"

    sign = ""

    if number < 0:
        sign = "-"
        number = abs(number)

    bits: List[str] = []

    while number > 0:
        remainder = number % 2
        bits.append(str(remainder))
        number //= 2

    return sign + "".join(reversed(bits))


def explain_binary_places(binary: str) -> List[Tuple[int, int, int]]:
    """
    Return positional information for an unsigned binary number.

    Each tuple contains:

        (bit_position, bit_value, decimal_contribution)

    Example:

        "1011"

    produces conceptual information equivalent to:

        position 3 -> 1 -> 8
        position 2 -> 0 -> 0
        position 1 -> 1 -> 2
        position 0 -> 1 -> 1
    """
    binary = normalize_binary(binary)
    explanation = []

    for index, bit in enumerate(binary):
        position = len(binary) - 1 - index
        value = int(bit)
        contribution = value * (2 ** position)
        explanation.append((position, value, contribution))

    return explanation


# =============================================================================
# SECTION 2: BINARY ADDITION AND CARRY OPERATIONS
# =============================================================================

@dataclass
class AdditionStep:
    """
    Represents one column of binary addition.
    """

    position: int
    bit_a: int
    bit_b: int
    carry_in: int
    sum_bit: int
    carry_out: int


def binary_add(bit_a: int, bit_b: int, carry_in: int = 0) -> Tuple[int, int]:
    """
    Add two binary digits and an incoming carry.

    Possible inputs:

        0 + 0 + 0 = 0 -> sum 0, carry 0
        0 + 1 + 0 = 1 -> sum 1, carry 0
        1 + 1 + 0 = 2 -> binary 10 -> sum 0, carry 1
        1 + 1 + 1 = 3 -> binary 11 -> sum 1, carry 1

    Returns:

        (sum_bit, carry_out)
    """
    if bit_a not in (0, 1) or bit_b not in (0, 1) or carry_in not in (0, 1):
        raise ValueError("Binary digits and carry must be 0 or 1.")

    total = bit_a + bit_b + carry_in

    sum_bit = total % 2
    carry_out = total // 2

    return sum_bit, carry_out


def add_binary_strings(
    binary_a: str,
    binary_b: str,
    return_steps: bool = False,
):
    """
    Add two unsigned binary numbers.

    The algorithm starts at the least significant bit and moves left.

    Time complexity:
        O(max(len(a), len(b)))

    Space complexity:
        O(max(len(a), len(b)))
    """
    a = normalize_binary(binary_a)
    b = normalize_binary(binary_b)

    max_length = max(len(a), len(b))

    a = a.zfill(max_length)
    b = b.zfill(max_length)

    carry = 0
    result_bits: List[str] = []
    steps: List[AdditionStep] = []

    for offset in range(max_length):
        index = max_length - 1 - offset

        bit_a = int(a[index])
        bit_b = int(b[index])

        carry_in = carry

        sum_bit, carry = binary_add(bit_a, bit_b, carry_in)

        result_bits.append(str(sum_bit))

        steps.append(
            AdditionStep(
                position=offset,
                bit_a=bit_a,
                bit_b=bit_b,
                carry_in=carry_in,
                sum_bit=sum_bit,
                carry_out=carry,
            )
        )

    if carry:
        result_bits.append("1")

    result = "".join(reversed(result_bits))

    if return_steps:
        return result, steps

    return result


def half_adder(bit_a: int, bit_b: int) -> Tuple[int, int]:
    """
    Half adder.

    A half adder adds two bits but has no carry input.

    sum   = A XOR B
    carry = A AND B
    """
    if bit_a not in (0, 1) or bit_b not in (0, 1):
        raise ValueError("Half adder inputs must be 0 or 1.")

    sum_bit = bit_a ^ bit_b
    carry = bit_a & bit_b

    return sum_bit, carry


def full_adder(bit_a: int, bit_b: int, carry_in: int) -> Tuple[int, int]:
    """
    Full adder implemented through boolean logic.

    A full adder adds:

        A
        B
        Carry-in

    Sum:

        A XOR B XOR Carry-in

    Carry-out:

        (A AND B) OR
        (Carry-in AND (A XOR B))
    """
    if any(bit not in (0, 1) for bit in (bit_a, bit_b, carry_in)):
        raise ValueError("Full adder inputs must be 0 or 1.")

    partial_sum = bit_a ^ bit_b

    sum_bit = partial_sum ^ carry_in

    carry_out = (bit_a & bit_b) | (carry_in & partial_sum)

    return sum_bit, carry_out


def ripple_carry_add(
    binary_a: str,
    binary_b: str,
) -> str:
    """
    Simulate a ripple-carry adder.

    In hardware, the carry output from one full adder becomes
    the carry input to the next full adder.

    This dependency is called carry propagation.
    """
    a = normalize_binary(binary_a)
    b = normalize_binary(binary_b)

    width = max(len(a), len(b))

    a = a.zfill(width)
    b = b.zfill(width)

    carry = 0
    result = []

    for index in range(width - 1, -1, -1):
        bit_a = int(a[index])
        bit_b = int(b[index])

        sum_bit, carry = full_adder(bit_a, bit_b, carry)

        result.append(str(sum_bit))

    if carry:
        result.append("1")

    return "".join(reversed(result))


# =============================================================================
# SECTION 3: FIXED-WIDTH BINARY ADDITION AND OVERFLOW
# =============================================================================

def unsigned_binary_add_fixed_width(
    binary_a: str,
    binary_b: str,
    width: int,
) -> Tuple[str, int]:
    """
    Add two unsigned binary values using a fixed number of bits.

    Returns:

        (result_within_width, carry_out)

    Example using 4 bits:

        1111
      + 0001
      ------
      0000 with carry_out = 1

    The carry represents an overflow beyond the fixed width.
    """
    if width <= 0:
        raise ValueError("Width must be positive.")

    a = normalize_binary(binary_a)
    b = normalize_binary(binary_b)

    if len(a) > width or len(b) > width:
        raise ValueError("Input exceeds the selected fixed width.")

    a = a.zfill(width)
    b = b.zfill(width)

    carry = 0
    result = []

    for index in range(width - 1, -1, -1):
        sum_bit, carry = full_adder(
            int(a[index]),
            int(b[index]),
            carry,
        )

        result.append(str(sum_bit))

    return "".join(reversed(result)), carry


def unsigned_addition_overflow(
    binary_a: str,
    binary_b: str,
    width: int,
) -> bool:
    """
    Detect unsigned overflow.

    Unsigned overflow occurs when addition produces a carry
    beyond the most significant bit.
    """
    _, carry_out = unsigned_binary_add_fixed_width(
        binary_a,
        binary_b,
        width,
    )

    return bool(carry_out)


def signed_addition_overflow(
    binary_a: str,
    binary_b: str,
    width: int,
) -> bool:
    """
    Detect two's-complement signed overflow.

    Signed overflow occurs when:

    - Two positive numbers produce a negative result.
    - Two negative numbers produce a positive result.

    Equivalent sign-bit rule:

        If A and B have the same sign,
        and the result has a different sign,
        overflow occurred.
    """
    result, _ = unsigned_binary_add_fixed_width(
        binary_a,
        binary_b,
        width,
    )

    a = normalize_binary(binary_a).zfill(width)
    b = normalize_binary(binary_b).zfill(width)

    sign_a = a[0]
    sign_b = b[0]
    sign_result = result[0]

    return sign_a == sign_b and sign_result != sign_a


# =============================================================================
# SECTION 4: BINARY SUBTRACTION AND BORROW OPERATIONS
# =============================================================================

@dataclass
class SubtractionStep:
    """
    Represents one column of binary subtraction.
    """

    position: int
    bit_a: int
    bit_b: int
    borrow_in: int
    difference_bit: int
    borrow_out: int


def binary_subtract(bit_a: int, bit_b: int, borrow_in: int = 0) -> Tuple[int, int]:
    """
    Subtract two bits and an incoming borrow.

    We calculate:

        bit_a - bit_b - borrow_in

    If the value becomes negative, add 2 to obtain the current
    difference bit and borrow 1 from the next higher position.

    Examples:

        0 - 0 = 0, borrow 0
        1 - 0 = 1, borrow 0
        1 - 1 = 0, borrow 0
        0 - 1 = -1

    Since -1 cannot be represented as a single unsigned binary bit,
    borrow from the next position:

        10₂ - 1₂ = 1₂

    Therefore:

        difference bit = 1
        borrow out = 1
    """
    if any(bit not in (0, 1) for bit in (bit_a, bit_b, borrow_in)):
        raise ValueError("Binary digits and borrow must be 0 or 1.")

    difference = bit_a - bit_b - borrow_in

    if difference < 0:
        difference += 2
        borrow_out = 1
    else:
        borrow_out = 0

    return difference, borrow_out


def subtract_binary_strings(
    binary_a: str,
    binary_b: str,
    return_steps: bool = False,
):
    """
    Subtract unsigned binary B from unsigned binary A.

    This implementation returns a signed result when B > A.

    Examples:

        1010 - 0011 = 0111
        0011 - 0101 = -0010 conceptually -> -10
    """
    a = normalize_binary(binary_a)
    b = normalize_binary(binary_b)

    decimal_a = binary_to_decimal_manual(a)
    decimal_b = binary_to_decimal_manual(b)

    # To keep the column subtraction algorithm focused on unsigned magnitude,
    # reverse operands when the final answer must be negative.
    if decimal_a < decimal_b:
        magnitude_result = subtract_binary_strings(b, a, False)
        result = "-" + normalize_binary(magnitude_result)

        if return_steps:
            return result, []

        return result

    width = max(len(a), len(b))

    a = a.zfill(width)
    b = b.zfill(width)

    borrow = 0
    result = []
    steps: List[SubtractionStep] = []

    for offset in range(width):
        index = width - 1 - offset

        bit_a = int(a[index])
        bit_b = int(b[index])

        borrow_in = borrow

        difference_bit, borrow = binary_subtract(
            bit_a,
            bit_b,
            borrow_in,
        )

        result.append(str(difference_bit))

        steps.append(
            SubtractionStep(
                position=offset,
                bit_a=bit_a,
                bit_b=bit_b,
                borrow_in=borrow_in,
                difference_bit=difference_bit,
                borrow_out=borrow,
            )
        )

    if borrow != 0:
        raise ArithmeticError(
            "Unexpected final borrow in magnitude subtraction."
        )

    answer = normalize_binary("".join(reversed(result)))

    if return_steps:
        return answer, steps

    return answer


def half_subtractor(bit_a: int, bit_b: int) -> Tuple[int, int]:
    """
    Half subtractor.

    Difference:

        A XOR B

    Borrow:

        NOT A AND B
    """
    if bit_a not in (0, 1) or bit_b not in (0, 1):
        raise ValueError("Half subtractor inputs must be 0 or 1.")

    difference = bit_a ^ bit_b
    borrow = (1 - bit_a) & bit_b

    return difference, borrow


def full_subtractor(
    bit_a: int,
    bit_b: int,
    borrow_in: int,
) -> Tuple[int, int]:
    """
    Full subtractor using boolean relationships.

    Difference:

        A XOR B XOR Borrow-in

    Borrow-out:

        (NOT A AND B)
        OR
        (Borrow-in AND NOT(A XOR B))
    """
    if any(bit not in (0, 1) for bit in (bit_a, bit_b, borrow_in)):
        raise ValueError("Full subtractor inputs must be 0 or 1.")

    difference = bit_a ^ bit_b ^ borrow_in

    borrow_out = (
        ((1 - bit_a) & bit_b)
        | (borrow_in & (1 - (bit_a ^ bit_b)))
    )

    return difference, borrow_out


# =============================================================================
# SECTION 5: ONES' COMPLEMENT AND TWOS' COMPLEMENT
# =============================================================================

def invert_bits(binary: str) -> str:
    """
    Compute the ones' complement by flipping every bit.

        0 -> 1
        1 -> 0
    """
    validate_binary(binary)

    if binary[0] in "+-":
        raise ValueError("Complement operations require unsigned bit patterns.")

    return "".join("1" if bit == "0" else "0" for bit in binary)


def ones_complement(binary: str, width: int) -> str:
    """
    Return the fixed-width ones' complement.
    """
    normalized = normalize_binary(binary)

    if len(normalized) > width:
        raise ValueError("Input exceeds selected width.")

    return invert_bits(normalized.zfill(width))


def twos_complement(binary: str, width: int) -> str:
    """
    Return the fixed-width two's complement.

    Two's complement is:

        ones' complement + 1

    Example using 8 bits:

        +5 = 00000101

        invert:
        11111010

        add 1:
        11111011

    Therefore 11111011 represents -5 in signed two's complement.
    """
    if width <= 0:
        raise ValueError("Width must be positive.")

    normalized = normalize_binary(binary)

    if len(normalized) > width:
        raise ValueError("Input exceeds selected width.")

    inverted = invert_bits(normalized.zfill(width))

    result, _ = unsigned_binary_add_fixed_width(
        inverted,
        "1",
        width,
    )

    return result


def signed_decimal_to_twos_complement(number: int, width: int) -> str:
    """
    Convert a signed decimal integer into a fixed-width two's-complement pattern.

    Range for width n:

        -2^(n-1) through 2^(n-1) - 1
    """
    if width <= 0:
        raise ValueError("Width must be positive.")

    minimum = -(2 ** (width - 1))
    maximum = (2 ** (width - 1)) - 1

    if number < minimum or number > maximum:
        raise OverflowError(
            f"{number} cannot be represented in {width}-bit signed two's complement."
        )

    if number >= 0:
        return decimal_to_binary_manual(number).zfill(width)

    magnitude = decimal_to_binary_manual(abs(number))

    return twos_complement(magnitude, width)


def twos_complement_to_signed_decimal(binary: str) -> int:
    """
    Interpret a binary pattern as a signed two's-complement integer.

    If the most significant bit is 0:
        the number is non-negative.

    If the most significant bit is 1:
        the number is negative.

    For an n-bit pattern:

        signed_value = unsigned_value - 2^n
    """
    validate_binary(binary)

    if binary[0] in "+-":
        raise ValueError("Two's-complement patterns do not use explicit signs.")

    width = len(binary)
    unsigned_value = binary_to_decimal_manual(binary)

    if binary[0] == "0":
        return unsigned_value

    return unsigned_value - (2 ** width)


def subtract_using_twos_complement(
    binary_a: str,
    binary_b: str,
    width: int,
) -> str:
    """
    Compute A - B using:

        A + two's complement(B)

    Any carry beyond the fixed width is discarded.

    This is a fundamental reason computer hardware can often use
    the same adder circuit for both addition and subtraction.
    """
    a = normalize_binary(binary_a).zfill(width)
    b = normalize_binary(binary_b).zfill(width)

    if len(normalize_binary(binary_a)) > width:
        raise ValueError("A exceeds width.")

    if len(normalize_binary(binary_b)) > width:
        raise ValueError("B exceeds width.")

    negative_b = twos_complement(b, width)

    result, _ = unsigned_binary_add_fixed_width(
        a,
        negative_b,
        width,
    )

    return result


# =============================================================================
# SECTION 6: BINARY MULTIPLICATION
# =============================================================================

def multiply_binary_digits(bit_a: int, bit_b: int) -> int:
    """
    Multiply two binary digits.

    Binary multiplication is equivalent to logical AND:

        0 * 0 = 0
        0 * 1 = 0
        1 * 0 = 0
        1 * 1 = 1
    """
    if bit_a not in (0, 1) or bit_b not in (0, 1):
        raise ValueError("Binary digits must be 0 or 1.")

    return bit_a & bit_b


def multiply_binary_long(binary_a: str, binary_b: str) -> str:
    """
    Multiply two unsigned binary numbers using long multiplication.

    Example:

            101
          x 011
          -----
            101       <- 1 * 101
           1010       <- 1 * 101 shifted left
          00000       <- 0 * 101 shifted left twice
          -----
           1111

    Each shift to the left multiplies the partial product by 2.
    """
    a = normalize_binary(binary_a)
    b = normalize_binary(binary_b)

    if a == "0" or b == "0":
        return "0"

    result = "0"

    reversed_b = reversed(b)

    for shift, bit in enumerate(reversed_b):
        if bit == "1":
            partial_product = a + ("0" * shift)
            result = add_binary_strings(result, partial_product)

    return normalize_binary(result)


def multiply_binary_shift_add(binary_a: str, binary_b: str) -> str:
    """
    Multiply using the shift-and-add algorithm.

    Algorithm:

        result = 0
        multiplicand = A
        multiplier = B

        while multiplier != 0:
            if least significant bit of multiplier is 1:
                result += multiplicand

            multiplicand <<= 1
            multiplier >>= 1

    This corresponds closely to binary multiplication hardware.
    """
    a = normalize_binary(binary_a)
    b = normalize_binary(binary_b)

    result = "0"
    multiplicand = a
    multiplier = binary_to_decimal_manual(b)

    while multiplier > 0:
        if multiplier & 1:
            result = add_binary_strings(result, multiplicand)

        multiplicand += "0"
        multiplier >>= 1

    return normalize_binary(result)


def multiply_signed_binary(
    binary_a: str,
    binary_b: str,
) -> str:
    """
    Multiply explicitly signed binary strings.

    Examples:

        -101 * 11 = -1111
        -101 * -11 = 1111
    """
    validate_binary(binary_a)
    validate_binary(binary_b)

    sign = 1

    if binary_a.startswith("-"):
        sign *= -1
        binary_a = binary_a[1:]

    elif binary_a.startswith("+"):
        binary_a = binary_a[1:]

    if binary_b.startswith("-"):
        sign *= -1
        binary_b = binary_b[1:]

    elif binary_b.startswith("+"):
        binary_b = binary_b[1:]

    product = multiply_binary_shift_add(binary_a, binary_b)

    if product == "0":
        return "0"

    return "-" + product if sign < 0 else product


# =============================================================================
# SECTION 7: SHIFT OPERATIONS
# =============================================================================

def left_shift_binary(binary: str, positions: int) -> str:
    """
    Logical left shift for an unsigned binary string.

        binary << n

    For non-negative integers, shifting left by n positions multiplies
    the value by 2^n.

    Example:

        101 << 2

        10100

        5 * 4 = 20
    """
    binary = normalize_binary(binary)

    if positions < 0:
        raise ValueError("Shift positions cannot be negative.")

    if binary == "0":
        return "0"

    return binary + ("0" * positions)


def right_shift_binary(binary: str, positions: int) -> str:
    """
    Logical right shift for an unsigned binary string.

        binary >> n

    For unsigned integers, this corresponds to integer division by 2^n.

    Bits shifted beyond the right edge are discarded.
    """
    binary = normalize_binary(binary)

    if positions < 0:
        raise ValueError("Shift positions cannot be negative.")

    if positions >= len(binary):
        return "0"

    return normalize_binary(binary[:-positions]) if positions else binary


# =============================================================================
# SECTION 8: BINARY DIVISION
# =============================================================================

def compare_unsigned_binary(binary_a: str, binary_b: str) -> int:
    """
    Compare two unsigned binary strings.

    Returns:

        -1 if A < B
         0 if A == B
         1 if A > B
    """
    a = normalize_binary(binary_a)
    b = normalize_binary(binary_b)

    if len(a) < len(b):
        return -1

    if len(a) > len(b):
        return 1

    if a < b:
        return -1

    if a > b:
        return 1

    return 0


def subtract_unsigned_binary(
    binary_a: str,
    binary_b: str,
) -> str:
    """
    Subtract B from A when A >= B.

    Raises an error when A < B.
    """
    if compare_unsigned_binary(binary_a, binary_b) < 0:
        raise ValueError("Unsigned subtraction requires A >= B.")

    result = subtract_binary_strings(binary_a, binary_b)

    if result.startswith("-"):
        raise ArithmeticError("Unexpected negative result.")

    return result


def divide_binary_long(
    dividend: str,
    divisor: str,
) -> Tuple[str, str]:
    """
    Divide unsigned binary numbers using long division.

    Returns:

        (quotient, remainder)

    Mathematical identity:

        dividend = divisor * quotient + remainder

    with:

        0 <= remainder < divisor

    Division by zero raises ZeroDivisionError.
    """
    dividend = normalize_binary(dividend)
    divisor = normalize_binary(divisor)

    if divisor == "0":
        raise ZeroDivisionError("Binary division by zero is undefined.")

    if compare_unsigned_binary(dividend, divisor) < 0:
        return "0", dividend

    quotient_bits: List[str] = []
    remainder = "0"

    for bit in dividend:
        # Bring down the next dividend bit.
        remainder = normalize_binary(remainder + bit)

        if compare_unsigned_binary(remainder, divisor) >= 0:
            remainder = subtract_unsigned_binary(remainder, divisor)
            quotient_bits.append("1")
        else:
            quotient_bits.append("0")

    quotient = normalize_binary("".join(quotient_bits))
    remainder = normalize_binary(remainder)

    return quotient, remainder


def divide_signed_binary(
    dividend: str,
    divisor: str,
) -> Tuple[str, str]:
    """
    Signed binary division with truncation toward zero.

    Returns:

        (quotient, remainder)

    The remainder has the same sign as the dividend when non-zero.
    """
    validate_binary(dividend)
    validate_binary(divisor)

    dividend_sign = -1 if dividend.startswith("-") else 1
    divisor_sign = -1 if divisor.startswith("-") else 1

    unsigned_dividend = dividend.lstrip("+-")
    unsigned_divisor = divisor.lstrip("+-")

    quotient, remainder = divide_binary_long(
        unsigned_dividend,
        unsigned_divisor,
    )

    quotient_sign = dividend_sign * divisor_sign

    if quotient != "0" and quotient_sign < 0:
        quotient = "-" + quotient

    if remainder != "0" and dividend_sign < 0:
        remainder = "-" + remainder

    return quotient, remainder


# =============================================================================
# SECTION 9: RESTORING DIVISION ALGORITHM
# =============================================================================

def restoring_division(
    dividend: str,
    divisor: str,
) -> Tuple[str, str]:
    """
    Educational implementation of restoring division for unsigned values.

    Conceptual process:

    1. Shift the partial remainder left.
    2. Bring down the next dividend bit.
    3. Attempt subtraction of the divisor.
    4. If subtraction is successful, quotient bit is 1.
    5. Otherwise restore the previous remainder and quotient bit is 0.

    At the algorithmic string level, restoration is represented by retaining
    the previous remainder when subtraction would make it negative.
    """
    dividend = normalize_binary(dividend)
    divisor = normalize_binary(divisor)

    if divisor == "0":
        raise ZeroDivisionError("Division by zero is undefined.")

    remainder = "0"
    quotient_bits = []

    for bit in dividend:
        remainder = normalize_binary(remainder + bit)

        previous_remainder = remainder

        if compare_unsigned_binary(remainder, divisor) >= 0:
            remainder = subtract_unsigned_binary(remainder, divisor)
            quotient_bits.append("1")
        else:
            remainder = previous_remainder
            quotient_bits.append("0")

    return (
        normalize_binary("".join(quotient_bits)),
        normalize_binary(remainder),
    )


# =============================================================================
# SECTION 10: BITWISE OPERATIONS AND THEIR RELATIONSHIP TO BINARY ARITHMETIC
# =============================================================================

def bitwise_demonstration(number_a: int, number_b: int) -> dict:
    """
    Demonstrate Python bitwise operations.

    AND:
        a & b

    OR:
        a | b

    XOR:
        a ^ b

    NOT:
        ~a

    Left shift:
        a << n

    Right shift:
        a >> n

    Python integers are arbitrary precision and signed, so ~a follows the
    identity:

        ~a == -a - 1
    """
    return {
        "a_decimal": number_a,
        "b_decimal": number_b,
        "a_binary": bin(number_a),
        "b_binary": bin(number_b),
        "and": number_a & number_b,
        "or": number_a | number_b,
        "xor": number_a ^ number_b,
        "not_a": ~number_a,
        "left_shift_a_by_1": number_a << 1,
        "right_shift_a_by_1": number_a >> 1,
    }


def add_using_bitwise_operations(
    number_a: int,
    number_b: int,
) -> int:
    """
    Add two non-negative integers using only bitwise concepts.

    Key identities:

        XOR gives addition without carries.

        AND gives positions where carries occur.

        Carry positions move left by one bit.

    Repeated process:

        partial_sum = a XOR b
        carry       = (a AND b) << 1

    Continue until carry becomes zero.
    """
    if number_a < 0 or number_b < 0:
        raise ValueError(
            "This educational implementation accepts non-negative integers."
        )

    a = number_a
    b = number_b

    while b != 0:
        partial_sum = a ^ b
        carry = (a & b) << 1

        a = partial_sum
        b = carry

    return a


# =============================================================================
# SECTION 11: FIXED-WIDTH TWO'S-COMPLEMENT ARITHMETIC
# =============================================================================

@dataclass
class FixedWidthBinary:
    """
    Represent a fixed-width binary word.

    The stored bit pattern is interpreted according to a specified width.
    """

    bits: str

    def __post_init__(self) -> None:
        validate_binary(self.bits)

        if self.bits[0] in "+-":
            raise ValueError("Fixed-width bit patterns cannot contain signs.")

    @property
    def width(self) -> int:
        return len(self.bits)

    @property
    def unsigned_value(self) -> int:
        return binary_to_decimal_manual(self.bits)

    @property
    def signed_value(self) -> int:
        return twos_complement_to_signed_decimal(self.bits)

    def add(self, other: "FixedWidthBinary") -> "FixedWidthBinary":
        """
        Fixed-width addition.

        Bits beyond the selected width are discarded.
        """
        if self.width != other.width:
            raise ValueError("Both operands must have the same width.")

        result, _ = unsigned_binary_add_fixed_width(
            self.bits,
            other.bits,
            self.width,
        )

        return FixedWidthBinary(result)

    def subtract(self, other: "FixedWidthBinary") -> "FixedWidthBinary":
        """
        Fixed-width subtraction using two's complement.
        """
        if self.width != other.width:
            raise ValueError("Both operands must have the same width.")

        result = subtract_using_twos_complement(
            self.bits,
            other.bits,
            self.width,
        )

        return FixedWidthBinary(result)


# =============================================================================
# SECTION 12: ALGORITHMIC VERIFICATION AND TESTING
# =============================================================================

def verify_binary_conversion() -> None:
    """
    Verify manual decimal/binary conversion for a range of values.
    """
    for number in range(-100, 101):
        binary = decimal_to_binary_manual(number)
        reconstructed = binary_to_decimal_manual(binary)

        assert reconstructed == number, (
            f"Conversion failed for {number}: "
            f"{binary} -> {reconstructed}"
        )


def verify_binary_addition() -> None:
    """
    Compare manual binary addition with Python integer arithmetic.
    """
    for a in range(0, 65):
        for b in range(0, 65):
            binary_a = decimal_to_binary_manual(a)
            binary_b = decimal_to_binary_manual(b)

            result = add_binary_strings(binary_a, binary_b)
            expected = a + b

            assert binary_to_decimal_manual(result) == expected, (
                f"Addition failed: {a} + {b}"
            )


def verify_binary_subtraction() -> None:
    """
    Compare manual binary subtraction with Python integer arithmetic.
    """
    for a in range(0, 65):
        for b in range(0, 65):
            binary_a = decimal_to_binary_manual(a)
            binary_b = decimal_to_binary_manual(b)

            result = subtract_binary_strings(binary_a, binary_b)

            assert binary_to_decimal_manual(result) == a - b, (
                f"Subtraction failed: {a} - {b}"
            )


def verify_binary_multiplication() -> None:
    """
    Compare binary multiplication algorithms with Python arithmetic.
    """
    for a in range(0, 33):
        for b in range(0, 33):
            binary_a = decimal_to_binary_manual(a)
            binary_b = decimal_to_binary_manual(b)

            long_result = multiply_binary_long(binary_a, binary_b)
            shift_result = multiply_binary_shift_add(binary_a, binary_b)

            assert binary_to_decimal_manual(long_result) == a * b
            assert binary_to_decimal_manual(shift_result) == a * b


def verify_binary_division() -> None:
    """
    Verify quotient and remainder properties.

    For every non-zero divisor:

        dividend = divisor * quotient + remainder

        0 <= remainder < divisor
    """
    for dividend in range(0, 100):
        for divisor in range(1, 20):
            binary_dividend = decimal_to_binary_manual(dividend)
            binary_divisor = decimal_to_binary_manual(divisor)

            quotient, remainder = divide_binary_long(
                binary_dividend,
                binary_divisor,
            )

            quotient_value = binary_to_decimal_manual(quotient)
            remainder_value = binary_to_decimal_manual(remainder)

            assert quotient_value == dividend // divisor
            assert remainder_value == dividend % divisor

            assert (
                divisor * quotient_value + remainder_value
                == dividend
            )

            assert 0 <= remainder_value < divisor


# =============================================================================
# SECTION 13: DEMONSTRATIONS
# =============================================================================

def demonstrate_fundamentals() -> None:
    print("\n" + "=" * 80)
    print("1. BINARY FUNDAMENTALS")
    print("=" * 80)

    decimal_number = 45
    binary_number = decimal_to_binary_manual(decimal_number)

    print(f"Decimal: {decimal_number}")
    print(f"Binary : {binary_number}")
    print(
        f"Back to decimal: "
        f"{binary_to_decimal_manual(binary_number)}"
    )

    print("\nPositional values:")

    for position, bit, contribution in explain_binary_places(binary_number):
        print(
            f"2^{position}: bit={bit}, "
            f"contribution={contribution}"
        )


def demonstrate_addition() -> None:
    print("\n" + "=" * 80)
    print("2. BINARY ADDITION AND CARRY")
    print("=" * 80)

    a = "101101"
    b = "111011"

    result, steps = add_binary_strings(a, b, return_steps=True)

    print(f"{a} + {b} = {result}")
    print(
        f"Decimal verification: "
        f"{binary_to_decimal_manual(a)} + "
        f"{binary_to_decimal_manual(b)} = "
        f"{binary_to_decimal_manual(result)}"
    )

    print("\nColumn operations from least significant position:")

    for step in steps:
        print(
            f"Position {step.position}: "
            f"{step.bit_a} + {step.bit_b} + carry {step.carry_in} "
            f"= sum {step.sum_bit}, carry {step.carry_out}"
        )

    print("\nHalf adder for 1 and 1:")
    print(f"sum, carry = {half_adder(1, 1)}")

    print("\nFull adder for 1, 1, carry 1:")
    print(f"sum, carry = {full_adder(1, 1, 1)}")

    print("\nRipple-carry addition:")
    print(f"{a} + {b} = {ripple_carry_add(a, b)}")


def demonstrate_overflow() -> None:
    print("\n" + "=" * 80)
    print("3. FIXED-WIDTH OVERFLOW")
    print("=" * 80)

    result, carry = unsigned_binary_add_fixed_width(
        "1111",
        "0001",
        4,
    )

    print("4-bit unsigned arithmetic:")
    print(f"1111 + 0001 -> result={result}, carry_out={carry}")

    print(
        "Unsigned overflow:",
        unsigned_addition_overflow("1111", "0001", 4),
    )

    signed_result, _ = unsigned_binary_add_fixed_width(
        "0111",
        "0001",
        4,
    )

    print("\n4-bit signed interpretation:")
    print(
        f"0111 ({twos_complement_to_signed_decimal('0111')}) + "
        f"0001 ({twos_complement_to_signed_decimal('0001')})"
    )
    print(
        f"Stored result: {signed_result} "
        f"({twos_complement_to_signed_decimal(signed_result)})"
    )
    print(
        "Signed overflow:",
        signed_addition_overflow("0111", "0001", 4),
    )


def demonstrate_subtraction() -> None:
    print("\n" + "=" * 80)
    print("4. BINARY SUBTRACTION AND BORROW")
    print("=" * 80)

    a = "101010"
    b = "001111"

    result, steps = subtract_binary_strings(a, b, return_steps=True)

    print(f"{a} - {b} = {result}")

    for step in steps:
        print(
            f"Position {step.position}: "
            f"{step.bit_a} - {step.bit_b} - borrow {step.borrow_in} "
            f"= difference {step.difference_bit}, "
            f"borrow {step.borrow_out}"
        )

    print("\nNegative result:")
    print(f"11 - 101 = {subtract_binary_strings('11', '101')}")

    print("\nHalf subtractor for 0 - 1:")
    print(
        "difference, borrow =",
        half_subtractor(0, 1),
    )

    print("\nFull subtractor for 0 - 1 with borrow 1:")
    print(
        "difference, borrow =",
        full_subtractor(0, 1, 1),
    )


def demonstrate_complements() -> None:
    print("\n" + "=" * 80)
    print("5. ONES' COMPLEMENT AND TWOS' COMPLEMENT")
    print("=" * 80)

    value = "0101"

    print(f"Original        : {value}")
    print(f"Ones' complement: {ones_complement(value, 4)}")
    print(f"Twos' complement: {twos_complement(value, 4)}")

    negative_five = signed_decimal_to_twos_complement(-5, 8)

    print("\n-5 represented using 8-bit two's complement:")
    print(negative_five)
    print(
        "Decoded value:",
        twos_complement_to_signed_decimal(negative_five),
    )

    subtraction = subtract_using_twos_complement(
        "001010",
        "000111",
        6,
    )

    print("\nSubtraction through two's complement:")
    print("001010 - 000111 =", subtraction)
    print(
        "Unsigned interpretation:",
        binary_to_decimal_manual(subtraction),
    )


def demonstrate_multiplication() -> None:
    print("\n" + "=" * 80)
    print("6. BINARY MULTIPLICATION")
    print("=" * 80)

    a = "1101"
    b = "1011"

    long_result = multiply_binary_long(a, b)
    shift_result = multiply_binary_shift_add(a, b)

    print(f"{a} * {b}")
    print("Long multiplication:", long_result)
    print("Shift-and-add       :", shift_result)

    print(
        "Decimal verification:",
        binary_to_decimal_manual(a),
        "*",
        binary_to_decimal_manual(b),
        "=",
        binary_to_decimal_manual(long_result),
    )

    print("\nSigned multiplication:")
    print("-101 * 11 =", multiply_signed_binary("-101", "11"))
    print("-101 * -11 =", multiply_signed_binary("-101", "-11"))


def demonstrate_shifts() -> None:
    print("\n" + "=" * 80)
    print("7. BINARY SHIFT OPERATIONS")
    print("=" * 80)

    value = "1011"

    print(f"{value} << 3 = {left_shift_binary(value, 3)}")
    print(f"{value} >> 2 = {right_shift_binary(value, 2)}")


def demonstrate_division() -> None:
    print("\n" + "=" * 80)
    print("8. BINARY DIVISION")
    print("=" * 80)

    dividend = "110101"
    divisor = "101"

    quotient, remainder = divide_binary_long(
        dividend,
        divisor,
    )

    print(f"{dividend} / {divisor}")
    print("Quotient :", quotient)
    print("Remainder:", remainder)

    dividend_value = binary_to_decimal_manual(dividend)
    divisor_value = binary_to_decimal_manual(divisor)

    print(
        f"Verification: {dividend_value} = "
        f"{divisor_value} * "
        f"{binary_to_decimal_manual(quotient)} + "
        f"{binary_to_decimal_manual(remainder)}"
    )

    restoring_q, restoring_r = restoring_division(
        dividend,
        divisor,
    )

    print("\nRestoring division result:")
    print("Quotient :", restoring_q)
    print("Remainder:", restoring_r)

    print("\nSigned division:")
    quotient, remainder = divide_signed_binary(
        "-1101",
        "11",
    )

    print("-1101 / 11 =", quotient, "remainder", remainder)

    print("\nDivision edge case:")
    quotient, remainder = divide_binary_long("101", "1000")
    print("101 / 1000 =", quotient, "remainder", remainder)


def demonstrate_bitwise_addition() -> None:
    print("\n" + "=" * 80)
    print("9. BITWISE ADDITION")
    print("=" * 80)

    a = 13
    b = 29

    print(f"{a} + {b} using XOR and carry propagation:")
    print(add_using_bitwise_operations(a, b))

    print("\nBitwise operation values:")

    for key, value in bitwise_demonstration(a, b).items():
        print(f"{key}: {value}")


def demonstrate_fixed_width_class() -> None:
    print("\n" + "=" * 80)
    print("10. FIXED-WIDTH TWO'S-COMPLEMENT OBJECT")
    print("=" * 80)

    positive_five = FixedWidthBinary(
        signed_decimal_to_twos_complement(5, 8)
    )

    negative_three = FixedWidthBinary(
        signed_decimal_to_twos_complement(-3, 8)
    )

    result = positive_five.add(negative_three)

    print("A bits:", positive_five.bits)
    print("A signed value:", positive_five.signed_value)

    print("B bits:", negative_three.bits)
    print("B signed value:", negative_three.signed_value)

    print("A + B bits:", result.bits)
    print("A + B signed value:", result.signed_value)


def demonstrate_edge_cases() -> None:
    print("\n" + "=" * 80)
    print("11. EDGE CASES AND EXCEPTIONS")
    print("=" * 80)

    print("0 + 0 =", add_binary_strings("0", "0"))
    print("0 * 10101 =", multiply_binary_long("0", "10101"))
    print("101 >> 10 =", right_shift_binary("101", 10))

    try:
        divide_binary_long("1010", "0")
    except ZeroDivisionError as error:
        print("Division by zero error:", error)

    try:
        normalize_binary("10201")
    except ValueError as error:
        print("Invalid binary error:", error)

    try:
        signed_decimal_to_twos_complement(8, 4)
    except OverflowError as error:
        print("Signed range error:", error)


def run_verification_tests() -> None:
    print("\n" + "=" * 80)
    print("12. VERIFICATION TESTS")
    print("=" * 80)

    verify_binary_conversion()
    print("Binary conversion tests passed.")

    verify_binary_addition()
    print("Binary addition tests passed.")

    verify_binary_subtraction()
    print("Binary subtraction tests passed.")

    verify_binary_multiplication()
    print("Binary multiplication tests passed.")

    verify_binary_division()
    print("Binary division tests passed.")


# =============================================================================
# MAIN PROGRAM
# =============================================================================

def main() -> None:
    """
    Execute all demonstrations and verification tests.
    """
    demonstrate_fundamentals()
    demonstrate_addition()
    demonstrate_overflow()
    demonstrate_subtraction()
    demonstrate_complements()
    demonstrate_multiplication()
    demonstrate_shifts()
    demonstrate_division()
    demonstrate_bitwise_addition()
    demonstrate_fixed_width_class()
    demonstrate_edge_cases()
    run_verification_tests()

    print("\n" + "=" * 80)
    print("BINARY ARITHMETIC STUDY SCRIPT COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    main()
