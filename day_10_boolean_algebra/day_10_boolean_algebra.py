"""
Boolean Algebra: Beginner to Advanced Study Script
===================================================

This self-contained script teaches Boolean algebra using Python.

Topics covered:
- Boolean values and Boolean data types
- Truth tables
- AND, OR, NOT, XOR
- NAND, NOR, XNOR
- Boolean expressions
- Operator precedence
- Comparison operators
- Short-circuit evaluation
- Truth-table generation
- Boolean algebra laws
- Simplification and equivalence checking
- De Morgan's laws
- Universal gates
- Logic circuits represented in Python
- Half adders and full adders
- Multiplexers and decoders
- Bitwise Boolean operations
- Binary values and masks
- Karnaugh-map concepts
- Sum-of-products and product-of-sums
- Canonical forms
- Don't-care conditions
- Combinational circuit design
- Sequential-logic context
- Logisim-oriented circuit thinking
- Validation, testing, debugging, and edge cases
- Practical applications
- Performance and implementation considerations
"""

from __future__ import annotations

from itertools import product
from typing import Callable, Iterable, Sequence


# ============================================================================
# 1. FUNDAMENTAL BOOLEAN VALUES
# ============================================================================

print("=" * 80)
print("1. BOOLEAN VALUES")
print("=" * 80)

# Python has two Boolean values:
# True  -> logical 1
# False -> logical 0

true_value = True
false_value = False

print("True:", true_value)
print("False:", false_value)
print("Type of True:", type(true_value).__name__)

# bool() converts many Python values into Boolean values.
print("\nbool(True):", bool(True))
print("bool(False):", bool(False))
print("bool(1):", bool(1))
print("bool(0):", bool(0))
print("bool('hello'):", bool("hello"))
print("bool(''):", bool(""))
print("bool([]):", bool([]))

# Important:
# Boolean logic is about True/False.
# Truthiness is a Python concept in which other objects are interpreted
# as True or False in conditions.


# ============================================================================
# 2. BASIC LOGICAL OPERATORS
# ============================================================================

print("\n" + "=" * 80)
print("2. AND, OR, NOT")
print("=" * 80)

a = True
b = False

# AND is True only when both inputs are True.
print("a AND b:", a and b)

# OR is True when at least one input is True.
print("a OR b:", a or b)

# NOT reverses the Boolean value.
print("NOT a:", not a)
print("NOT b:", not b)

print("\nTruth-table values:")
for x in (False, True):
    for y in (False, True):
        print(
            f"x={x!s:<5} y={y!s:<5} "
            f"x AND y={x and y!s:<5} "
            f"x OR y={x or y!s:<5}"
        )


# ============================================================================
# 3. XOR
# ============================================================================

print("\n" + "=" * 80)
print("3. XOR")
print("=" * 80)

# XOR means exclusive OR.
# XOR is True when the two inputs are different.

def xor(a: bool, b: bool) -> bool:
    """Return the exclusive OR of two Boolean inputs."""
    return a != b


for x, y in product((False, True), repeat=2):
    print(f"{x} XOR {y} = {xor(x, y)}")

# XOR can also be expressed as:
# (A OR B) AND NOT(A AND B)
def xor_from_basic_gates(a: bool, b: bool) -> bool:
    """Implement XOR using only AND, OR, and NOT."""
    return (a or b) and not (a and b)


print("\nXOR implementation equivalence:")
for x, y in product((False, True), repeat=2):
    direct = xor(x, y)
    constructed = xor_from_basic_gates(x, y)
    print(x, y, direct, constructed, direct == constructed)


# ============================================================================
# 4. NAND, NOR, XNOR
# ============================================================================

print("\n" + "=" * 80)
print("4. DERIVED LOGIC GATES")
print("=" * 80)


def nand(a: bool, b: bool) -> bool:
    """NAND = NOT(AND)."""
    return not (a and b)


def nor(a: bool, b: bool) -> bool:
    """NOR = NOT(OR)."""
    return not (a or b)


def xnor(a: bool, b: bool) -> bool:
    """XNOR is the logical complement of XOR."""
    return not xor(a, b)


print("A B | AND OR XOR NAND NOR XNOR")
print("-" * 35)

for a, b in product((False, True), repeat=2):
    print(
        f"{int(a)} {int(b)} | "
        f" {int(a and b)}   "
        f"{int(a or b)}   "
        f" {int(xor(a, b))}    "
        f" {int(nand(a, b))}    "
        f" {int(nor(a, b))}    "
        f"  {int(xnor(a, b))}"
    )


# ============================================================================
# 5. TRUTH TABLE GENERATION
# ============================================================================

print("\n" + "=" * 80)
print("5. TRUTH TABLES")
print("=" * 80)


def generate_truth_table(
    variable_names: Sequence[str],
    expression: Callable[..., bool],
) -> list[dict[str, bool]]:
    """
    Generate a complete truth table for a Boolean expression.

    For n variables, a truth table contains 2^n combinations.
    """
    table = []

    for values in product((False, True), repeat=len(variable_names)):
        result = bool(expression(*values))
        row = dict(zip(variable_names, values))
        row["result"] = result
        table.append(row)

    return table


def print_truth_table(table: list[dict[str, bool]]) -> None:
    """Print a truth table in a readable format."""
    if not table:
        print("Empty truth table.")
        return

    headers = list(table[0].keys())
    print(" | ".join(headers))
    print("-" * (len(headers) * 8))

    for row in table:
        print(
            " | ".join(
                str(int(row[header]))
                for header in headers
            )
        )


table = generate_truth_table(
    ["A", "B"],
    lambda A, B: A and (A or B),
)

print("Truth table for A AND (A OR B):")
print_truth_table(table)


# ============================================================================
# 6. BOOLEAN EXPRESSIONS
# ============================================================================

print("\n" + "=" * 80)
print("6. BOOLEAN EXPRESSIONS")
print("=" * 80)

# A Boolean expression combines variables and logical operators.
#
# Mathematical notation:
# A · B       -> AND
# A + B       -> OR
# A'          -> NOT A
# A ⊕ B       -> XOR
#
# Python equivalents:
# A and B
# A or B
# not A
# A != B

A = True
B = False
C = True

expression_1 = A and B
expression_2 = A or B
expression_3 = not A
expression_4 = (A and B) or C
expression_5 = A and (B or C)

print("A AND B:", expression_1)
print("A OR B:", expression_2)
print("NOT A:", expression_3)
print("(A AND B) OR C:", expression_4)
print("A AND (B OR C):", expression_5)


# ============================================================================
# 7. OPERATOR PRECEDENCE
# ============================================================================

print("\n" + "=" * 80)
print("7. BOOLEAN OPERATOR PRECEDENCE")
print("=" * 80)

# Python evaluates Boolean operators in this order:
# 1. not
# 2. and
# 3. or
#
# Parentheses should be used when clarity matters.

value_without_parentheses = True or False and False
value_with_parentheses = (True or False) and False

print("True or False and False:", value_without_parentheses)
print("(True or False) and False:", value_with_parentheses)

# Because AND has higher precedence than OR:
# True or (False and False)
# becomes True.

print("Explicit interpretation:", True or (False and False))


# ============================================================================
# 8. COMPARISON OPERATORS AS BOOLEAN EXPRESSIONS
# ============================================================================

print("\n" + "=" * 80)
print("8. COMPARISON OPERATORS")
print("=" * 80)

x = 10
y = 20

print("x == y:", x == y)
print("x != y:", x != y)
print("x < y:", x < y)
print("x <= y:", x <= y)
print("x > y:", x > y)
print("x >= y:", x >= y)

# Comparisons return Boolean values and can be combined.
age = 25
has_id = True

allowed = age >= 18 and has_id
print("Access allowed:", allowed)


# ============================================================================
# 9. BOOLEAN ALGEBRA LAWS
# ============================================================================

print("\n" + "=" * 80)
print("9. BOOLEAN ALGEBRA LAWS")
print("=" * 80)

"""
Important Boolean algebra laws:

Identity:
A + 0 = A
A · 1 = A

Null / domination:
A + 1 = 1
A · 0 = 0

Idempotent:
A + A = A
A · A = A

Complement:
A + A' = 1
A · A' = 0

Double negation:
(A')' = A

Commutative:
A + B = B + A
A · B = B · A

Associative:
(A + B) + C = A + (B + C)
(A · B) · C = A · (B · C)

Distributive:
A · (B + C) = (A · B) + (A · C)
A + (B · C) = (A + B) · (A + C)

Absorption:
A + A·B = A
A·(A + B) = A

De Morgan:
(A·B)' = A' + B'
(A+B)' = A'·B'
"""


def boolean_law_tests() -> None:
    """Verify fundamental Boolean algebra laws exhaustively."""

    values = (False, True)

    for A, B, C in product(values, repeat=3):
        assert (A or False) == A
        assert (A and True) == A

        assert (A or True) is True
        assert (A and False) is False

        assert (A or A) == A
        assert (A and A) == A

        assert (A or not A) is True
        assert (A and not A) is False

        assert not (not A) == A

        assert (A or B) == (B or A)
        assert (A and B) == (B and A)

        assert ((A or B) or C) == (A or (B or C))
        assert ((A and B) and C) == (A and (B and C))

        assert (A and (B or C)) == ((A and B) or (A and C))
        assert (A or (B and C)) == ((A or B) and (A or C))

        assert (A or (A and B)) == A
        assert (A and (A or B)) == A

        assert not (A and B) == ((not A) or (not B))
        assert not (A or B) == ((not A) and (not B))

    print("All Boolean algebra law tests passed.")


boolean_law_tests()


# ============================================================================
# 10. DE MORGAN'S LAWS
# ============================================================================

print("\n" + "=" * 80)
print("10. DE MORGAN'S LAWS")
print("=" * 80)


def demonstrate_demorgan() -> None:
    """Demonstrate both De Morgan transformations."""

    print("A B | NOT(A AND B) | (NOT A) OR (NOT B)")
    print("-" * 50)

    for A, B in product((False, True), repeat=2):
        left = not (A and B)
        right = (not A) or (not B)
        print(int(A), int(B), "|", int(left), "            |", int(right))
        assert left == right

    print("\nA B | NOT(A OR B) | (NOT A) AND (NOT B)")
    print("-" * 50)

    for A, B in product((False, True), repeat=2):
        left = not (A or B)
        right = (not A) and (not B)
        print(int(A), int(B), "|", int(left), "           |", int(right))
        assert left == right


demonstrate_demorgan()


# ============================================================================
# 11. BOOLEAN EXPRESSION EQUIVALENCE
# ============================================================================

print("\n" + "=" * 80)
print("11. EXPRESSION EQUIVALENCE")
print("=" * 80)


def expressions_are_equivalent(
    variable_names: Sequence[str],
    first: Callable[..., bool],
    second: Callable[..., bool],
) -> bool:
    """
    Compare two Boolean expressions for every possible input.

    This is a formal truth-table-based equivalence test.
    """
    for values in product((False, True), repeat=len(variable_names)):
        if bool(first(*values)) != bool(second(*values)):
            return False
    return True


equivalent = expressions_are_equivalent(
    ["A", "B"],
    lambda A, B: A and (A or B),
    lambda A, B: A,
)

print("A AND (A OR B) == A:", equivalent)

equivalent = expressions_are_equivalent(
    ["A", "B"],
    lambda A, B: not (A and B),
    lambda A, B: (not A) or (not B),
)

print("De Morgan equivalence:", equivalent)


# ============================================================================
# 12. CANONICAL SUM-OF-PRODUCTS
# ============================================================================

print("\n" + "=" * 80)
print("12. SUM-OF-PRODUCTS")
print("=" * 80)

"""
A Sum-of-Products (SOP) expression is an OR of AND terms.

Example:
F(A,B) = A'B + AB

Each product term represents a combination of variables.

Canonical SOP uses minterms. Every minterm contains every variable.
"""


def minterm(index: int, variable_count: int) -> tuple[bool, ...]:
    """Return the Boolean assignment represented by a minterm index."""
    if index < 0 or index >= 2**variable_count:
        raise ValueError("Minterm index is outside the valid range.")

    bits = format(index, f"0{variable_count}b")
    return tuple(bit == "1" for bit in bits)


print("Three-variable minterms:")
for index in range(8):
    print(index, minterm(index, 3))


def canonical_sop(
    variable_names: Sequence[str],
    expression: Callable[..., bool],
) -> list[tuple[int, tuple[bool, ...]]]:
    """
    Return minterm indices for which the expression evaluates to True.
    """
    result = []

    for index, values in enumerate(
        product((False, True), repeat=len(variable_names))
    ):
        if expression(*values):
            result.append((index, values))

    return result


sop_terms = canonical_sop(
    ["A", "B", "C"],
    lambda A, B, C: (A and B) or (not A and C),
)

print("Minterms producing 1:")
for index, values in sop_terms:
    print(f"m{index}", values)


# ============================================================================
# 13. PRODUCT-OF-SUMS
# ============================================================================

print("\n" + "=" * 80)
print("13. PRODUCT-OF-SUMS")
print("=" * 80)

"""
Product-of-Sums (POS) is an AND of OR terms.

For a canonical POS representation, maxterms correspond to
input combinations for which the function is False.
"""


def canonical_pos_indices(
    variable_count: int,
    expression: Callable[..., bool],
) -> list[int]:
    """Return maxterm indices for which an expression evaluates to False."""
    indices = []

    for index, values in enumerate(
        product((False, True), repeat=variable_count)
    ):
        if not expression(*values):
            indices.append(index)

    return indices


pos_indices = canonical_pos_indices(
    3,
    lambda A, B, C: (A and B) or C,
)

print("Maxterm indices:")
print(pos_indices)


# ============================================================================
# 14. UNIVERSAL GATES
# ============================================================================

print("\n" + "=" * 80)
print("14. UNIVERSAL GATES: NAND AND NOR")
print("=" * 80)

"""
NAND and NOR are universal gates.

Any Boolean function can be constructed using only NAND gates.
Any Boolean function can also be constructed using only NOR gates.
"""


def nand_not(a: bool) -> bool:
    """NOT implemented using NAND."""
    return nand(a, a)


def nand_and(a: bool, b: bool) -> bool:
    """AND implemented using NAND only."""
    return nand(nand(a, b), nand(a, b))


def nand_or(a: bool, b: bool) -> bool:
    """OR implemented using NAND only using De Morgan's law."""
    return nand(nand(a, a), nand(b, b))


def nor_not(a: bool) -> bool:
    """NOT implemented using NOR."""
    return nor(a, a)


def nor_or(a: bool, b: bool) -> bool:
    """OR implemented using NOR only."""
    return nor(nor(a, b), nor(a, b))


def nor_and(a: bool, b: bool) -> bool:
    """AND implemented using NOR only."""
    return nor(nor(a, a), nor(b, b))


for a, b in product((False, True), repeat=2):
    assert nand_not(a) == (not a)
    assert nand_and(a, b) == (a and b)
    assert nand_or(a, b) == (a or b)

    assert nor_not(a) == (not a)
    assert nor_or(a, b) == (a or b)
    assert nor_and(a, b) == (a and b)

print("NAND-only and NOR-only constructions verified.")


# ============================================================================
# 15. LOGIC GATE CLASSES
# ============================================================================

print("\n" + "=" * 80)
print("15. LOGIC GATE ABSTRACTION")
print("=" * 80)


class LogicGate:
    """Base class for a Boolean logic gate."""

    name = "LogicGate"

    def evaluate(self, *inputs: bool) -> bool:
        raise NotImplementedError("Subclasses must implement evaluate().")

    def __call__(self, *inputs: bool) -> bool:
        return self.evaluate(*inputs)


class AndGate(LogicGate):
    name = "AND"

    def evaluate(self, *inputs: bool) -> bool:
        if not inputs:
            raise ValueError("AND gate requires at least one input.")
        return all(inputs)


class OrGate(LogicGate):
    name = "OR"

    def evaluate(self, *inputs: bool) -> bool:
        if not inputs:
            raise ValueError("OR gate requires at least one input.")
        return any(inputs)


class NotGate(LogicGate):
    name = "NOT"

    def evaluate(self, *inputs: bool) -> bool:
        if len(inputs) != 1:
            raise ValueError("NOT gate requires exactly one input.")
        return not inputs[0]


class XorGate(LogicGate):
    name = "XOR"

    def evaluate(self, *inputs: bool) -> bool:
        if len(inputs) != 2:
            raise ValueError("This XOR gate requires exactly two inputs.")
        return inputs[0] != inputs[1]


gate_examples = [
    AndGate(),
    OrGate(),
    NotGate(),
    XorGate(),
]

for gate in gate_examples:
    print(gate.name)


# ============================================================================
# 16. CIRCUITS AS COMPOSITIONS OF GATES
# ============================================================================

print("\n" + "=" * 80)
print("16. COMBINATIONAL CIRCUITS")
print("=" * 80)


def circuit_example(A: bool, B: bool, C: bool) -> bool:
    """
    Circuit:

        A ----\
              AND ----\
        B ----/       \
                       OR ---- output
        C -------------/

    F = (A AND B) OR C
    """
    first_gate = AndGate()(A, B)
    return OrGate()(first_gate, C)


table = generate_truth_table(
    ["A", "B", "C"],
    circuit_example,
)

print_truth_table(table)


# ============================================================================
# 17. HALF ADDER
# ============================================================================

print("\n" + "=" * 80)
print("17. HALF ADDER")
print("=" * 80)

"""
A half adder adds two one-bit binary values.

Inputs:
A, B

Outputs:
Sum   = A XOR B
Carry = A AND B
"""


def half_adder(A: bool, B: bool) -> tuple[bool, bool]:
    """Return (sum, carry) for two one-bit inputs."""
    return xor(A, B), A and B


print("A B | Sum Carry")
print("-" * 20)

for A, B in product((False, True), repeat=2):
    sum_bit, carry_bit = half_adder(A, B)
    print(f"{int(A)} {int(B)} |  {int(sum_bit)}    {int(carry_bit)}")


# ============================================================================
# 18. FULL ADDER
# ============================================================================

print("\n" + "=" * 80)
print("18. FULL ADDER")
print("=" * 80)

"""
A full adder adds:
A + B + CarryIn

Outputs:
Sum
CarryOut
"""


def full_adder(
    A: bool,
    B: bool,
    carry_in: bool,
) -> tuple[bool, bool]:
    """Return (sum, carry_out) for a full adder."""
    first_sum, first_carry = half_adder(A, B)
    final_sum, second_carry = half_adder(first_sum, carry_in)
    carry_out = first_carry or second_carry
    return final_sum, carry_out


print("A B Cin | Sum Cout")
print("-" * 24)

for A, B, carry_in in product((False, True), repeat=3):
    sum_bit, carry_out = full_adder(A, B, carry_in)
    print(
        f"{int(A)} {int(B)}  {int(carry_in)}  |"
        f"  {int(sum_bit)}   {int(carry_out)}"
    )


# ============================================================================
# 19. RIPPLE-CARRY ADDER
# ============================================================================

print("\n" + "=" * 80)
print("19. MULTI-BIT BINARY ADDITION")
print("=" * 80)


def add_binary_strings(first: str, second: str) -> str:
    """
    Add two non-empty binary strings using full-adder logic.

    This intentionally avoids Python's integer conversion so the
    Boolean circuit behavior is visible.
    """
    if not first or not second:
        raise ValueError("Binary strings must not be empty.")

    if any(bit not in "01" for bit in first + second):
        raise ValueError("Binary strings may contain only 0 and 1.")

    width = max(len(first), len(second))
    first = first.zfill(width)
    second = second.zfill(width)

    result = []
    carry = False

    for index in range(width - 1, -1, -1):
        A = first[index] == "1"
        B = second[index] == "1"

        sum_bit, carry = full_adder(A, B, carry)
        result.append("1" if sum_bit else "0")

    if carry:
        result.append("1")

    return "".join(reversed(result))


binary_examples = [
    ("0", "0"),
    ("1", "1"),
    ("1010", "0011"),
    ("1111", "0001"),
    ("101101", "011011"),
]

for first, second in binary_examples:
    result = add_binary_strings(first, second)
    expected = bin(int(first, 2) + int(second, 2))[2:]
    print(f"{first} + {second} = {result} | Expected: {expected}")
    assert result == expected


# ============================================================================
# 20. MULTIPLEXER
# ============================================================================

print("\n" + "=" * 80)
print("20. MULTIPLEXER")
print("=" * 80)

"""
A multiplexer selects one input from several possible inputs.

For a 2-to-1 multiplexer:

S = 0 -> output D0
S = 1 -> output D1

Boolean expression:
Y = (NOT S AND D0) OR (S AND D1)
"""


def multiplexer_2_to_1(
    D0: bool,
    D1: bool,
    select: bool,
) -> bool:
    """Return selected input from a two-input multiplexer."""
    return ((not select) and D0) or (select and D1)


for select in (False, True):
    print(
        f"Select={int(select)} -> "
        f"Output={int(multiplexer_2_to_1(True, False, select))}"
    )


# ============================================================================
# 21. DECODER
# ============================================================================

print("\n" + "=" * 80)
print("21. TWO-BIT DECODER")
print("=" * 80)

"""
A 2-to-4 decoder activates exactly one output for each two-bit input.
"""


def decoder_2_to_4(A: bool, B: bool) -> tuple[bool, bool, bool, bool]:
    """Return one-hot outputs for a two-bit input."""
    return (
        (not A) and (not B),
        (not A) and B,
        A and (not B),
        A and B,
    )


for A, B in product((False, True), repeat=2):
    print(f"{int(A)}{int(B)} ->", tuple(int(x) for x in decoder_2_to_4(A, B)))


# ============================================================================
# 22. BITWISE BOOLEAN OPERATIONS
# ============================================================================

print("\n" + "=" * 80)
print("22. BITWISE OPERATIONS")
print("=" * 80)

"""
Python's bitwise operators operate on integer bits:

&  bitwise AND
|  bitwise OR
^  bitwise XOR
~  bitwise NOT
<< left shift
>> right shift

These are different from Python's logical operators:
and, or, not

Example:
5 = 0101
3 = 0011

5 & 3 = 0001 = 1
5 | 3 = 0111 = 7
5 ^ 3 = 0110 = 6
"""

first_number = 5
second_number = 3

print("5 & 3:", first_number & second_number)
print("5 | 3:", first_number | second_number)
print("5 ^ 3:", first_number ^ second_number)
print("5 << 1:", first_number << 1)
print("5 >> 1:", first_number >> 1)

# Python integers use signed, unbounded integer representation.
# Therefore ~5 is not simply "the complement of four displayed bits".
print("~5:", ~5)


# ============================================================================
# 23. FIXED-WIDTH BITWISE NOT
# ============================================================================

print("\n" + "=" * 80)
print("23. FIXED-WIDTH BITWISE COMPLEMENT")
print("=" * 80)


def bitwise_not_fixed_width(value: int, width: int) -> int:
    """
    Compute a NOT operation within a fixed number of bits.

    Example:
    0101 -> 1010 for width=4
    """
    if width <= 0:
        raise ValueError("Width must be positive.")

    if value < 0 or value >= 2**width:
        raise ValueError("Value does not fit within the requested width.")

    mask = (1 << width) - 1
    return (~value) & mask


value = 5
width = 4

complement = bitwise_not_fixed_width(value, width)

print(f"{value:04b} -> {complement:04b}")


# ============================================================================
# 24. BIT MASKS
# ============================================================================

print("\n" + "=" * 80)
print("24. BIT MASKS")
print("=" * 80)

"""
Bit masks are useful for representing Boolean flags compactly.

Suppose:
bit 0 = READ
bit 1 = WRITE
bit 2 = EXECUTE
"""

READ = 1 << 0
WRITE = 1 << 1
EXECUTE = 1 << 2

permissions = READ | WRITE

print("Permissions:", bin(permissions))
print("Can read:", bool(permissions & READ))
print("Can write:", bool(permissions & WRITE))
print("Can execute:", bool(permissions & EXECUTE))

# Add a flag.
permissions |= EXECUTE

# Remove a flag.
permissions &= ~WRITE

print("Updated permissions:", bin(permissions))


# ============================================================================
# 25. BOOLEAN VALUES AS INTEGER VALUES
# ============================================================================

print("\n" + "=" * 80)
print("25. BOOLEAN AND INTEGER RELATIONSHIP IN PYTHON")
print("=" * 80)

print("True == 1:", True == 1)
print("False == 0:", False == 0)
print("True + True:", True + True)
print("False + True:", False + True)

# bool is a subclass of int in Python.
print("isinstance(True, int):", isinstance(True, int))

# This relationship is useful in some calculations, but Boolean values
# should still be used explicitly when the intent is logical rather than
# numerical.


# ============================================================================
# 26. SHORT-CIRCUIT EVALUATION
# ============================================================================

print("\n" + "=" * 80)
print("26. SHORT-CIRCUIT EVALUATION")
print("=" * 80)


def demonstrate_side_effect(label: str) -> bool:
    """Print when this function is actually evaluated."""
    print("Evaluated:", label)
    return True


print("False AND function:")
result = False and demonstrate_side_effect("AND right side")
print("Result:", result)

print("\nTrue OR function:")
result = True or demonstrate_side_effect("OR right side")
print("Result:", result)

"""
AND stops when it already knows the result is False.
OR stops when it already knows the result is True.

This is important for:
- performance
- safe conditional expressions
- avoiding unnecessary function calls
- guarding operations that could fail
"""

number = 0

safe_check = number != 0 and (100 / number > 1)
print("\nSafe division check:", safe_check)


# ============================================================================
# 27. TRUTH TABLE COMPLEXITY
# ============================================================================

print("\n" + "=" * 80)
print("27. TRUTH-TABLE SIZE")
print("=" * 80)

"""
With n independent Boolean variables:

number of rows = 2^n

Examples:
1 variable -> 2 rows
2 variables -> 4 rows
3 variables -> 8 rows
10 variables -> 1024 rows
20 variables -> 1,048,576 rows

Exhaustive truth-table testing becomes expensive as the number of
variables grows exponentially.
"""


def truth_table_row_count(variable_count: int) -> int:
    if variable_count < 0:
        raise ValueError("Variable count cannot be negative.")
    return 2**variable_count


for variable_count in range(1, 11):
    print(
        f"{variable_count:2} variables -> "
        f"{truth_table_row_count(variable_count):5} rows"
    )


# ============================================================================
# 28. BOOLEAN FUNCTION WITH THREE VARIABLES
# ============================================================================

print("\n" + "=" * 80)
print("28. THREE-VARIABLE BOOLEAN FUNCTION")
print("=" * 80)


def majority(A: bool, B: bool, C: bool) -> bool:
    """
    Majority function.

    Output is True when at least two of the three inputs are True.

    Boolean form:
    AB + AC + BC
    """
    return (A and B) or (A and C) or (B and C)


majority_table = generate_truth_table(
    ["A", "B", "C"],
    majority,
)

print_truth_table(majority_table)


# ============================================================================
# 29. BOOLEAN EXPRESSION SIMPLIFICATION BY EQUIVALENCE
# ============================================================================

print("\n" + "=" * 80)
print("29. SIMPLIFICATION BY TRUTH-TABLE VERIFICATION")
print("=" * 80)

"""
A truth table can verify whether a proposed simplification is correct.

Example:

F = AB + A'B
F = B(A + A')
F = B(1)
F = B
"""


def original_expression(A: bool, B: bool) -> bool:
    return (A and B) or ((not A) and B)


def simplified_expression(A: bool, B: bool) -> bool:
    return B


print(
    "AB + A'B equivalent to B:",
    expressions_are_equivalent(
        ["A", "B"],
        original_expression,
        simplified_expression,
    ),
)


# ============================================================================
# 30. CONSENSUS THEOREM
# ============================================================================

print("\n" + "=" * 80)
print("30. CONSENSUS THEOREM")
print("=" * 80)

"""
Consensus theorem:

AB + A'C + BC = AB + A'C

The BC term is the consensus term and is redundant.
"""


def consensus_original(A: bool, B: bool, C: bool) -> bool:
    return (A and B) or ((not A) and C) or (B and C)


def consensus_simplified(A: bool, B: bool, C: bool) -> bool:
    return (A and B) or ((not A) and C)


print(
    "Consensus theorem verified:",
    expressions_are_equivalent(
        ["A", "B", "C"],
        consensus_original,
        consensus_simplified,
    ),
)


# ============================================================================
# 31. ABSORPTION EXAMPLES
# ============================================================================

print("\n" + "=" * 80)
print("31. ABSORPTION LAW")
print("=" * 80)

print("A + AB = A")

for A, B in product((False, True), repeat=2):
    left = A or (A and B)
    right = A
    print(
        f"A={int(A)}, B={int(B)} -> "
        f"left={int(left)}, right={int(right)}"
    )
    assert left == right


# ============================================================================
# 32. KARNAUGH MAP CONCEPT
# ============================================================================

print("\n" + "=" * 80)
print("32. KARNAUGH MAP CONCEPT")
print("=" * 80)

"""
A Karnaugh map (K-map) is a graphical method for simplifying Boolean
functions.

Key principles:
- Cells represent minterms.
- Adjacent cells differ in one variable.
- Groups contain powers of two cells: 1, 2, 4, 8, ...
- Groups should be as large as possible.
- Groups may wrap around edges.
- Overlapping groups are allowed when useful.
- Variables that change inside a group are eliminated.
- Variables that remain constant form the simplified term.

For two variables, Gray-code ordering is:

       B
       0  1
A=0    m0 m1
A=1    m2 m3

For larger maps, rows and columns also use Gray-code ordering.
"""

gray_code_2bit = ["00", "01", "11", "10"]
print("Two-bit Gray-code order:", gray_code_2bit)


# ============================================================================
# 33. GRAY CODE PROPERTY
# ============================================================================

print("\n" + "=" * 80)
print("33. GRAY-CODE ADJACENCY")
print("=" * 80)


def hamming_distance(first: str, second: str) -> int:
    """Return the number of positions containing different bits."""
    if len(first) != len(second):
        raise ValueError("Strings must have equal length.")
    return sum(a != b for a, b in zip(first, second))


for first, second in zip(gray_code_2bit, gray_code_2bit[1:]):
    distance = hamming_distance(first, second)
    print(first, second, "distance =", distance)
    assert distance == 1


# ============================================================================
# 34. DON'T-CARE CONDITIONS
# ============================================================================

print("\n" + "=" * 80)
print("34. DON'T-CARE CONDITIONS")
print("=" * 80)

"""
A don't-care input is a condition whose output does not matter for the
application.

It is often represented by X.

During Boolean simplification, don't-care cells may be treated as either
0 or 1 when doing so produces a simpler implementation.

Example application:
A circuit may receive only valid BCD digits 0000 through 1001.
Inputs 1010 through 1111 may never occur, so they can sometimes be
treated as don't-care states.

Important limitation:
A don't-care assumption is valid only when those states truly cannot
occur or their output is genuinely irrelevant.
"""


VALID_BCD_VALUES = set(range(10))
DONT_CARE_BCD_VALUES = set(range(10, 16))

print("Valid BCD values:", sorted(VALID_BCD_VALUES))
print("Potential don't-care values:", sorted(DONT_CARE_BCD_VALUES))


# ============================================================================
# 35. BOOLEAN INPUT VALIDATION
# ============================================================================

print("\n" + "=" * 80)
print("35. INPUT VALIDATION")
print("=" * 80)


def require_boolean(value: object, name: str = "value") -> bool:
    """
    Require an actual Boolean object.

    bool(1) is True, but this function deliberately rejects 1 because
    it may be important to distinguish logical inputs from integers.
    """
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be a Boolean value.")
    return value


try:
    require_boolean(True, "input")
    print("True accepted.")

    require_boolean(1, "input")
except TypeError as error:
    print("Validation error:", error)


# ============================================================================
# 36. LOGIC CIRCUIT INPUT VALIDATION
# ============================================================================

print("\n" + "=" * 80)
print("36. VALIDATED LOGIC GATE")
print("=" * 80)


def validated_and(a: object, b: object) -> bool:
    """Perform AND only when both inputs are actual Boolean values."""
    return require_boolean(a, "a") and require_boolean(b, "b")


print("validated_and(True, False):", validated_and(True, False))

try:
    validated_and(True, 1)
except TypeError as error:
    print("Expected validation error:", error)


# ============================================================================
# 37. LOGICAL VS BITWISE OPERATORS
# ============================================================================

print("\n" + "=" * 80)
print("37. LOGICAL VS BITWISE OPERATORS")
print("=" * 80)

"""
Logical:
    and
    or
    not

Bitwise:
    &
    |
    ^
    ~

Logical operators work with truth values and short-circuit.
Bitwise operators operate on the binary representation of integers.

Example:
5 = 0101
3 = 0011

5 & 3 = 0001
"""


logical_result = True and False
bitwise_result = 5 & 3

print("True and False:", logical_result)
print("5 & 3:", bitwise_result)


# ============================================================================
# 38. XOR APPLICATION: PARITY
# ============================================================================

print("\n" + "=" * 80)
print("38. XOR AND PARITY")
print("=" * 80)

"""
XOR can be used to calculate the parity of bits.

For an even number of 1 bits, XOR of all bits is 0.
For an odd number of 1 bits, XOR of all bits is 1.
"""


def xor_reduce(bits: Iterable[bool]) -> bool:
    """Return XOR of all Boolean values in an iterable."""
    result = False

    for bit in bits:
        result = xor(result, bit)

    return result


parity_examples = [
    [False, False, False],
    [True, False, False],
    [True, True, False],
    [True, True, True],
    [True, False, True, True],
]

for bits in parity_examples:
    print(
        tuple(int(bit) for bit in bits),
        "XOR parity =",
        int(xor_reduce(bits)),
    )


# ============================================================================
# 39. EVEN PARITY CHECKER
# ============================================================================


def has_even_parity(bits: Iterable[bool]) -> bool:
    """Return True when a sequence contains an even number of 1 bits."""
    return not xor_reduce(bits)


print("\nEven parity:")
for bits in parity_examples:
    print(tuple(int(x) for x in bits), has_even_parity(bits))


# ============================================================================
# 40. COMBINATIONAL CIRCUIT PROPERTY
# ============================================================================

print("\n" + "=" * 80)
print("40. COMBINATIONAL LOGIC")
print("=" * 80)

"""
A combinational circuit's output depends only on its current inputs.

Examples:
- adders
- multiplexers
- decoders
- encoders
- comparators
- arithmetic logic units

There is no internal memory required to determine the output.
"""


def comparator_1bit(A: bool, B: bool) -> tuple[bool, bool, bool]:
    """
    Return:
    greater_than
    equal
    less_than
    """
    greater = A and not B
    equal = xnor(A, B)
    less = not A and B

    return greater, equal, less


for A, B in product((False, True), repeat=2):
    print(
        f"{int(A)} {int(B)} ->",
        tuple(int(value) for value in comparator_1bit(A, B)),
    )


# ============================================================================
# 41. BOOLEAN REPRESENTATION OF STATE
# ============================================================================

print("\n" + "=" * 80)
print("41. BOOLEAN FLAGS")
print("=" * 80)

"""
Boolean values are frequently used to represent state:

is_authenticated
is_enabled
has_permission
is_valid
is_complete
is_connected

Good Boolean variable names generally describe a condition.
"""

is_authenticated = True
is_admin = False
account_active = True

can_access_admin_area = (
    is_authenticated
    and is_admin
    and account_active
)

print("Can access admin area:", can_access_admin_area)


# ============================================================================
# 42. CONDITIONAL LOGIC
# ============================================================================

print("\n" + "=" * 80)
print("42. CONDITIONAL EXPRESSIONS")
print("=" * 80)


def classify_number(number: int) -> str:
    """Classify an integer using Boolean conditions."""
    if number == 0:
        return "zero"

    if number > 0 and number % 2 == 0:
        return "positive even"

    if number > 0 and number % 2 != 0:
        return "positive odd"

    if number < 0 and number % 2 == 0:
        return "negative even"

    return "negative odd"


for number in (-3, -2, 0, 1, 2, 5):
    print(number, "->", classify_number(number))


# ============================================================================
# 43. ERROR HANDLING
# ============================================================================

print("\n" + "=" * 80)
print("43. ERROR HANDLING")
print("=" * 80)


def safe_binary_add(first: str, second: str) -> str | None:
    """
    Safely add two binary strings.

    Returns None when validation fails.
    """
    try:
        return add_binary_strings(first, second)
    except ValueError as error:
        print("Input error:", error)
        return None


print("Valid:", safe_binary_add("101", "11"))
print("Invalid:", safe_binary_add("102", "11"))


# ============================================================================
# 44. BOOLEAN EXPRESSION TESTING
# ============================================================================

print("\n" + "=" * 80)
print("44. TESTING BOOLEAN FUNCTIONS")
print("=" * 80)


def test_half_adder() -> None:
    """Exhaustively test all half-adder combinations."""
    expected = {
        (False, False): (False, False),
        (False, True): (True, False),
        (True, False): (True, False),
        (True, True): (False, True),
    }

    for inputs, expected_output in expected.items():
        assert half_adder(*inputs) == expected_output


def test_full_adder() -> None:
    """Exhaustively test all full-adder combinations."""
    for A, B, carry_in in product((False, True), repeat=3):
        expected_sum = (int(A) + int(B) + int(carry_in)) % 2 == 1
        expected_carry = int(A) + int(B) + int(carry_in) >= 2

        assert full_adder(A, B, carry_in) == (
            expected_sum,
            expected_carry,
        )


test_half_adder()
test_full_adder()

print("Half-adder tests passed.")
print("Full-adder tests passed.")


# ============================================================================
# 45. EDGE CASES
# ============================================================================

print("\n" + "=" * 80)
print("45. EDGE CASES")
print("=" * 80)

edge_cases = [
    ("AND", lambda: AndGate()(True, True, True)),
    ("OR", lambda: OrGate()(False, False, False)),
    ("XOR", lambda: XorGate()(True, False)),
    ("NOT", lambda: NotGate()(True)),
]

for name, operation in edge_cases:
    print(name, "->", operation())

try:
    NotGate()(True, False)
except ValueError as error:
    print("NOT edge-case error:", error)

try:
    XorGate()(True, False, True)
except ValueError as error:
    print("XOR edge-case error:", error)

try:
    AndGate()()
except ValueError as error:
    print("AND edge-case error:", error)


# ============================================================================
# 46. BOOLEAN FUNCTION AS A FIRST-CLASS OBJECT
# ============================================================================

print("\n" + "=" * 80)
print("46. FUNCTIONS AS BOOLEAN COMPONENTS")
print("=" * 80)


def apply_boolean_function(
    function: Callable[[bool, bool], bool],
    A: bool,
    B: bool,
) -> bool:
    """Apply a two-input Boolean function."""
    return function(A, B)


operations = {
    "AND": lambda A, B: A and B,
    "OR": lambda A, B: A or B,
    "XOR": xor,
    "NAND": nand,
    "NOR": nor,
    "XNOR": xnor,
}

for name, operation in operations.items():
    print(
        f"{name}:",
        apply_boolean_function(operation, True, False),
    )


# ============================================================================
# 47. LOGIC CIRCUIT NETWORK
# ============================================================================

print("\n" + "=" * 80)
print("47. MULTI-GATE NETWORK")
print("=" * 80)


def multi_gate_network(A: bool, B: bool, C: bool, D: bool) -> bool:
    """
    Example network:

    X = A AND B
    Y = C XOR D
    Z = X OR Y
    F = NOT Z
    """
    X = A and B
    Y = xor(C, D)
    Z = X or Y
    F = not Z

    return F


network_table = generate_truth_table(
    ["A", "B", "C", "D"],
    multi_gate_network,
)

print_truth_table(network_table)


# ============================================================================
# 48. INPUT COUNT AND GATE GENERALIZATION
# ============================================================================

print("\n" + "=" * 80)
print("48. MULTI-INPUT GATES")
print("=" * 80)


def multi_input_and(inputs: Sequence[bool]) -> bool:
    """Return True only if every input is True."""
    if not inputs:
        raise ValueError("At least one input is required.")
    return all(inputs)


def multi_input_or(inputs: Sequence[bool]) -> bool:
    """Return True if at least one input is True."""
    if not inputs:
        raise ValueError("At least one input is required.")
    return any(inputs)


samples = [
    [True, True, True],
    [True, False, True],
    [False, False, False],
    [True],
]

for sample in samples:
    print(
        sample,
        "AND =", multi_input_and(sample),
        "OR =", multi_input_or(sample),
    )


# ============================================================================
# 49. BOOLEAN EXPRESSION EVALUATION FROM BITS
# ============================================================================

print("\n" + "=" * 80)
print("49. BOOLEAN EXPRESSION USING BINARY INPUTS")
print("=" * 80)


def evaluate_security_condition(
    authenticated: bool,
    has_role: bool,
    emergency_override: bool,
    account_locked: bool,
) -> bool:
    """
    Access condition:

    ((authenticated AND has_role) OR emergency_override)
    AND NOT account_locked
    """
    return (
        (authenticated and has_role) or emergency_override
    ) and not account_locked


security_cases = [
    (True, True, False, False),
    (True, False, False, False),
    (False, False, True, False),
    (True, True, False, True),
]

for case in security_cases:
    print(case, "->", evaluate_security_condition(*case))


# ============================================================================
# 50. SECURITY CONSIDERATIONS
# ============================================================================

print("\n" + "=" * 80)
print("50. BOOLEAN LOGIC AND SECURITY")
print("=" * 80)

"""
Boolean conditions often control security-sensitive behavior.

Examples:
    is_authenticated AND has_permission
    is_verified AND account_active
    request_valid AND token_valid

Important practices:
- Do not confuse truthiness with authorization.
- Validate security-sensitive inputs explicitly.
- Avoid accidental use of OR where AND is required.
- Parenthesize complicated conditions.
- Test both allowed and denied paths.
- Include failure cases.
- Do not assume an input is safe merely because it evaluates as True.
- Keep authorization decisions centralized where practical.
- Prefer explicit conditions over clever expressions.
"""

authenticated = True
has_permission = False

authorization_result = authenticated and has_permission

print("Authenticated:", authenticated)
print("Has permission:", has_permission)
print("Authorized:", authorization_result)


# ============================================================================
# 51. DEBUGGING BOOLEAN EXPRESSIONS
# ============================================================================

print("\n" + "=" * 80)
print("51. DEBUGGING")
print("=" * 80)


def debug_access_condition(
    authenticated: bool,
    verified: bool,
    active: bool,
) -> bool:
    """Print intermediate Boolean values before producing a result."""

    authentication_check = authenticated
    verification_check = verified
    activity_check = active

    print("authentication_check:", authentication_check)
    print("verification_check:", verification_check)
    print("activity_check:", activity_check)

    result = (
        authentication_check
        and verification_check
        and activity_check
    )

    print("final result:", result)
    return result


debug_access_condition(True, False, True)


# ============================================================================
# 52. BOOLEAN EXPRESSION WITH INTERMEDIATE NODES
# ============================================================================

print("\n" + "=" * 80)
print("52. CIRCUIT DEBUGGING WITH INTERMEDIATE SIGNALS")
print("=" * 80)


def inspect_circuit(
    A: bool,
    B: bool,
    C: bool,
) -> dict[str, bool]:
    """Expose internal circuit signals for debugging."""
    signal_1 = A and B
    signal_2 = not C
    signal_3 = signal_1 or signal_2
    output = not signal_3

    return {
        "A": A,
        "B": B,
        "C": C,
        "signal_1": signal_1,
        "signal_2": signal_2,
        "signal_3": signal_3,
        "output": output,
    }


print(inspect_circuit(True, True, False))


# ============================================================================
# 53. DELAY AND HARDWARE CONSIDERATIONS
# ============================================================================

print("\n" + "=" * 80)
print("53. HARDWARE IMPLEMENTATION CONSIDERATIONS")
print("=" * 80)

"""
Python evaluates Boolean expressions as software operations.

Physical digital circuits have additional properties:

- propagation delay
- gate delay
- fan-in
- fan-out
- power consumption
- transistor count
- physical area
- signal integrity
- clock timing
- setup and hold constraints in sequential systems

Two Boolean expressions can be logically equivalent while having different
hardware costs.

For example, simplification may reduce the number of gates or levels of
logic, potentially improving area and timing.
"""

logical_depth_example_1 = "(A AND B) OR C"
logical_depth_example_2 = "A AND (B OR C)"

print("Equivalent in some contexts but structurally different:")
print(logical_depth_example_1)
print(logical_depth_example_2)


# ============================================================================
# 54. HAZARDS AND GLITCHES
# ============================================================================

print("\n" + "=" * 80)
print("54. LOGIC HAZARDS")
print("=" * 80)

"""
In physical circuits, different signal paths can have different propagation
delays.

When multiple inputs change, intermediate gate outputs may temporarily
produce an unintended value before settling.

This can create glitches or hazards.

Common categories include:
- static-1 hazards
- static-0 hazards
- dynamic hazards

Pure truth-table analysis does not show propagation-time behavior.
Hardware timing analysis is therefore necessary for timing-sensitive designs.
"""


# ============================================================================
# 55. LOGISIM-STYLE CIRCUIT MODEL
# ============================================================================

print("\n" + "=" * 80)
print("55. LOGISIM-STYLE THINKING")
print("=" * 80)

"""
A Logisim circuit can be modeled conceptually as:

Inputs -> Gates -> Intermediate wires -> Output

For a circuit such as:

F = (A AND B) OR (NOT C)

the corresponding structure is:

A ----\
       AND ----\
B ----/         \
                OR ---- F
C --> NOT ------/

When constructing the circuit in Logisim:
1. Place input pins.
2. Place the required gates.
3. Connect wires.
4. Place the output pin.
5. Test every input combination.
6. Compare the observed output with the truth table.

This Python script uses functions to model the same Boolean behavior.
"""


def logisim_style_example(A: bool, B: bool, C: bool) -> bool:
    and_output = A and B
    not_output = not C
    final_output = and_output or not_output
    return final_output


print_truth_table(
    generate_truth_table(
        ["A", "B", "C"],
        logisim_style_example,
    )
)


# ============================================================================
# 56. FORMAL CIRCUIT VERIFICATION
# ============================================================================

print("\n" + "=" * 80)
print("56. CIRCUIT VERIFICATION")
print("=" * 80)


def verify_circuit(
    variable_names: Sequence[str],
    reference: Callable[..., bool],
    implementation: Callable[..., bool],
) -> tuple[bool, list[tuple[tuple[bool, ...], bool, bool]]]:
    """
    Compare an implementation against a reference function.

    Returns:
        (is_equivalent, mismatches)
    """
    mismatches = []

    for values in product((False, True), repeat=len(variable_names)):
        expected = bool(reference(*values))
        actual = bool(implementation(*values))

        if expected != actual:
            mismatches.append((values, expected, actual))

    return not mismatches, mismatches


reference_function = lambda A, B, C: (A and B) or (not C)
implementation_function = logisim_style_example

is_correct, mismatches = verify_circuit(
    ["A", "B", "C"],
    reference_function,
    implementation_function,
)

print("Circuit correct:", is_correct)
print("Mismatches:", mismatches)


# ============================================================================
# 57. BOOLEAN FUNCTION CLASS
# ============================================================================

print("\n" + "=" * 80)
print("57. BOOLEAN FUNCTION OBJECT")
print("=" * 80)


class BooleanFunction:
    """
    Represent a Boolean function with named variables and an evaluator.
    """

    def __init__(
        self,
        variable_names: Sequence[str],
        evaluator: Callable[..., bool],
    ) -> None:
        if not variable_names:
            raise ValueError("At least one variable is required.")

        if len(set(variable_names)) != len(variable_names):
            raise ValueError("Variable names must be unique.")

        self.variable_names = tuple(variable_names)
        self.evaluator = evaluator

    def evaluate(self, values: Sequence[bool]) -> bool:
        """Evaluate the function for a sequence of Boolean values."""
        if len(values) != len(self.variable_names):
            raise ValueError(
                "The number of values must match the number of variables."
            )

        if not all(isinstance(value, bool) for value in values):
            raise TypeError("All values must be Boolean.")

        return bool(self.evaluator(*values))

    def truth_table(self) -> list[dict[str, bool]]:
        """Generate the function's truth table."""
        return generate_truth_table(
            self.variable_names,
            self.evaluator,
        )


majority_function = BooleanFunction(
    ["A", "B", "C"],
    majority,
)

print("Majority(True, True, False):", majority_function.evaluate(
    [True, True, False]
))

print("Majority(False, False, True):", majority_function.evaluate(
    [False, False, True]
))


# ============================================================================
# 58. FUNCTION COMPOSITION
# ============================================================================

print("\n" + "=" * 80)
print("58. FUNCTION COMPOSITION")
print("=" * 80)


def compose_boolean_functions(
    first: Callable[[bool, bool], bool],
    second: Callable[[bool, bool], bool],
) -> Callable[[bool, bool], bool]:
    """
    Compose two Boolean functions by feeding the same two inputs to both
    and OR-ing their results.
    """

    def composed(A: bool, B: bool) -> bool:
        return first(A, B) or second(A, B)

    return composed


and_or_composed = compose_boolean_functions(
    lambda A, B: A and B,
    lambda A, B: A or B,
)

print("Composed function:")
for A, B in product((False, True), repeat=2):
    print(A, B, "->", and_or_composed(A, B))


# ============================================================================
# 59. CONSTANT BOOLEAN FUNCTIONS
# ============================================================================

print("\n" + "=" * 80)
print("59. CONSTANT FUNCTIONS")
print("=" * 80)


def constant_zero(*_: bool) -> bool:
    """Boolean function that always returns zero."""
    return False


def constant_one(*_: bool) -> bool:
    """Boolean function that always returns one."""
    return True


print_truth_table(
    generate_truth_table(["A", "B"], constant_zero)
)

print_truth_table(
    generate_truth_table(["A", "B"], constant_one)
)


# ============================================================================
# 60. BOOLEAN FUNCTION CLASSIFICATION
# ============================================================================

print("\n" + "=" * 80)
print("60. FUNCTION CLASSIFICATION")
print("=" * 80)


def classify_boolean_function(
    variable_names: Sequence[str],
    expression: Callable[..., bool],
) -> str:
    """
    Classify a Boolean function as:
    - contradiction: always false
    - tautology: always true
    - contingent: sometimes true and sometimes false
    """
    outputs = [
        bool(expression(*values))
        for values in product((False, True), repeat=len(variable_names))
    ]

    if all(not value for value in outputs):
        return "contradiction"

    if all(outputs):
        return "tautology"

    return "contingent"


print(
    "A AND NOT A:",
    classify_boolean_function(
        ["A"],
        lambda A: A and not A,
    ),
)

print(
    "A OR NOT A:",
    classify_boolean_function(
        ["A"],
        lambda A: A or not A,
    ),
)

print(
    "A XOR B:",
    classify_boolean_function(
        ["A", "B"],
        xor,
    ),
)


# ============================================================================
# 61. MONOTONICITY CONCEPT
# ============================================================================

print("\n" + "=" * 80)
print("61. MONOTONE BOOLEAN FUNCTIONS")
print("=" * 80)

"""
A Boolean function is monotone increasing when changing an input from
0 to 1 cannot change the output from 1 to 0.

AND and OR are monotone.
XOR is not monotone.

This property matters in logic theory and circuit analysis.
"""


def is_monotone_increasing(
    variable_names: Sequence[str],
    expression: Callable[..., bool],
) -> bool:
    """
    Exhaustively test monotonicity.

    If x <= y component-wise, then f(x) <= f(y) must hold.
    """
    assignments = list(
        product((False, True), repeat=len(variable_names))
    )

    for first in assignments:
        first_output = bool(expression(*first))

        for second in assignments:
            second_output = bool(expression(*second))

            componentwise_less_or_equal = all(
                (not a) or b
                for a, b in zip(first, second)
            )

            if componentwise_less_or_equal and first_output and not second_output:
                return False

    return True


print(
    "AND monotone:",
    is_monotone_increasing(["A", "B"], lambda A, B: A and B),
)

print(
    "OR monotone:",
    is_monotone_increasing(["A", "B"], lambda A, B: A or B),
)

print(
    "XOR monotone:",
    is_monotone_increasing(["A", "B"], xor),
)


# ============================================================================
# 62. BOOLEAN DIFFERENCE / SENSITIVITY CONCEPT
# ============================================================================

print("\n" + "=" * 80)
print("62. INPUT SENSITIVITY")
print("=" * 80)

"""
An input is influential for a particular assignment if changing only that
input changes the function output.

This idea is related to Boolean derivatives and circuit sensitivity.
"""


def input_is_influential(
    expression: Callable[..., bool],
    values: Sequence[bool],
    index: int,
) -> bool:
    """Check whether changing one input changes the function output."""
    original = list(values)
    changed = list(values)

    if index < 0 or index >= len(values):
        raise IndexError("Input index out of range.")

    changed[index] = not changed[index]

    return bool(expression(*original)) != bool(expression(*changed))


for index in range(3):
    print(
        "Majority input",
        index,
        "influential:",
        input_is_influential(
            majority,
            [True, True, False],
            index,
        ),
    )


# ============================================================================
# 63. LOGICAL EQUIVALENCE OF DIFFERENT IMPLEMENTATIONS
# ============================================================================

print("\n" + "=" * 80)
print("63. ALTERNATIVE IMPLEMENTATIONS")
print("=" * 80)

"""
The same Boolean function may have many implementations.

Example:
XOR can be implemented directly, using basic gates, or using NAND gates.

Logical equivalence does not guarantee equal:
- propagation delay
- gate count
- power consumption
- physical area
- wiring complexity
"""

def xor_using_nand(a: bool, b: bool) -> bool:
    """Construct XOR using four NAND gates."""
    first = nand(a, b)
    second = nand(a, first)
    third = nand(b, first)
    return nand(second, third)


for A, B in product((False, True), repeat=2):
    assert xor_using_nand(A, B) == xor(A, B)

print("NAND XOR implementation verified.")


# ============================================================================
# 64. FORMAL BOOLEAN IDENTITIES TEST
# ============================================================================

print("\n" + "=" * 80)
print("64. ADDITIONAL IDENTITY TESTS")
print("=" * 80)


def test_additional_identities() -> None:
    values = (False, True)

    for A, B, C in product(values, repeat=3):
        # Distributive law.
        assert A and (B or C) == ((A and B) or (A and C))
        assert A or (B and C) == ((A or B) and (A or C))

        # Absorption.
        assert A or (A and B) == A
        assert A and (A or B) == A

        # Consensus theorem.
        assert (
            (A and B) or ((not A) and C) or (B and C)
        ) == (
            (A and B) or ((not A) and C)
        )

        # Alternative XOR expression.
        assert xor(A, B) == (
            (A and not B) or (not A and B)
        )

        # XNOR.
        assert xnor(A, B) == (
            (A and B) or ((not A) and (not B))
        )

    print("All additional identities passed.")


test_additional_identities()


# ============================================================================
# 65. PRACTICAL BOOLEAN DECISION SYSTEM
# ============================================================================

print("\n" + "=" * 80)
print("65. PRACTICAL DECISION SYSTEM")
print("=" * 80)


def transaction_allowed(
    authenticated: bool,
    sufficient_balance: bool,
    account_active: bool,
    fraud_flag: bool,
    manual_override: bool,
) -> bool:
    """
    Example business rule:

    Transaction is allowed when:
        account is authenticated
        AND account has sufficient balance
        AND account is active
        AND there is no fraud flag

    A manual override can permit the transaction only when the account
    is authenticated and active.
    """
    standard_path = (
        authenticated
        and sufficient_balance
        and account_active
        and not fraud_flag
    )

    override_path = (
        authenticated
        and account_active
        and manual_override
    )

    return standard_path or override_path


transaction_cases = [
    (True, True, True, False, False),
    (True, False, True, False, False),
    (True, False, True, True, True),
    (False, True, True, False, True),
]

for case in transaction_cases:
    print(case, "->", transaction_allowed(*case))


# ============================================================================
# 66. EDGE CASE: EMPTY ITERABLES
# ============================================================================

print("\n" + "=" * 80)
print("66. EMPTY BOOLEAN COLLECTIONS")
print("=" * 80)

"""
Python's all([]) returns True and any([]) returns False.

These results correspond to the mathematical notions of:
- empty conjunction = True
- empty disjunction = False

For application-level APIs, it may still be preferable to reject empty
input when at least one gate input is required.
"""

print("all([]):", all([]))
print("any([]):", any([]))

try:
    multi_input_and([])
except ValueError as error:
    print("Application-level AND validation:", error)

try:
    multi_input_or([])
except ValueError as error:
    print("Application-level OR validation:", error)


# ============================================================================
# 67. THREE-VALUED LOGIC CONTEXT
# ============================================================================

print("\n" + "=" * 80)
print("67. LIMITATIONS OF TWO-VALUED BOOLEAN LOGIC")
print("=" * 80)

"""
Classical Boolean algebra has exactly two values:
0 and 1.

Real systems sometimes need states such as:
- unknown
- high impedance
- uninitialized
- invalid
- don't care

Hardware description and database systems can therefore use logic models
that go beyond classical two-valued Boolean algebra.

Python's bool type itself remains two-valued.
"""

print("Classical values:", False, True)


# ============================================================================
# 68. BOOLEAN LOGIC AND DATABASE FILTERS
# ============================================================================

print("\n" + "=" * 80)
print("68. BOOLEAN LOGIC IN DATA FILTERING")
print("=" * 80)

records = [
    {"name": "A", "age": 22, "active": True},
    {"name": "B", "age": 17, "active": True},
    {"name": "C", "age": 30, "active": False},
    {"name": "D", "age": 25, "active": True},
]

eligible_records = [
    record
    for record in records
    if record["age"] >= 18 and record["active"]
]

for record in eligible_records:
    print(record)


# ============================================================================
# 69. BOOLEAN LOGIC IN MACHINE CONTROL
# ============================================================================

print("\n" + "=" * 80)
print("69. CONTROL LOGIC")
print("=" * 80)


def motor_should_run(
    start_signal: bool,
    stop_signal: bool,
    emergency_stop: bool,
    safety_interlock: bool,
) -> bool:
    """
    A simplified motor-control condition.

    Motor runs when:
    - start is active
    - stop is not active
    - emergency stop is not active
    - safety interlock is active
    """
    return (
        start_signal
        and not stop_signal
        and not emergency_stop
        and safety_interlock
    )


motor_cases = [
    (True, False, False, True),
    (True, True, False, True),
    (True, False, True, True),
    (True, False, False, False),
]

for case in motor_cases:
    print(case, "-> motor:", motor_should_run(*case))


# ============================================================================
# 70. PERFORMANCE CONSIDERATIONS
# ============================================================================

print("\n" + "=" * 80)
print("70. PERFORMANCE")
print("=" * 80)

"""
For ordinary Boolean expressions, Python evaluates a small number of
operations very quickly.

The main scalability issue in this educational implementation is exhaustive
truth-table generation.

For n variables:
    O(2^n)

Therefore:
- 10 variables -> 1,024 combinations
- 20 variables -> 1,048,576 combinations
- 30 variables -> 1,073,741,824 combinations

For larger Boolean systems, symbolic methods, Binary Decision Diagrams,
SAT solvers, algebraic simplification, or specialized hardware-design
tools can be more appropriate than brute-force enumeration.
"""

for n in (10, 20, 30):
    print(f"2^{n} =", 2**n)


# ============================================================================
# 71. BOOLEAN DESIGN BEST PRACTICES
# ============================================================================

print("\n" + "=" * 80)
print("71. BEST PRACTICES")
print("=" * 80)

"""
Best practices demonstrated by this script:

1. Use explicit parentheses for complicated conditions.
2. Give Boolean variables descriptive names.
3. Separate complex logic into intermediate signals.
4. Validate inputs when Boolean type matters.
5. Test every combination for small Boolean functions.
6. Verify circuit implementations against a reference expression.
7. Use truth tables to prove equivalence for small functions.
8. Distinguish logical operators from bitwise operators.
9. Consider hardware cost, not only logical correctness.
10. Treat don't-care conditions carefully.
11. Document security-sensitive conditions.
12. Avoid unnecessarily complex Boolean expressions.
13. Prefer maintainability when several equivalent expressions exist.
"""


# ============================================================================
# 72. COMPLETE STUDY EXERCISE IMPLEMENTATION
# ============================================================================

print("\n" + "=" * 80)
print("72. COMPLETE BOOLEAN CIRCUIT EXERCISE")
print("=" * 80)

"""
Circuit specification:

F = (A XOR B) AND (C OR D)

The implementation below exposes intermediate signals.
"""


def study_circuit(
    A: bool,
    B: bool,
    C: bool,
    D: bool,
) -> bool:
    xor_signal = xor(A, B)
    or_signal = C or D
    output = xor_signal and or_signal
    return output


study_table = generate_truth_table(
    ["A", "B", "C", "D"],
    study_circuit,
)

print_truth_table(study_table)


# ============================================================================
# 73. COMPLETE SELF-VERIFICATION
# ============================================================================

print("\n" + "=" * 80)
print("73. SELF-VERIFICATION")
print("=" * 80)


def run_all_verification_tests() -> None:
    """Run the principal correctness checks in this study script."""

    boolean_law_tests()
    test_additional_identities()
    test_half_adder()
    test_full_adder()

    assert expressions_are_equivalent(
        ["A", "B"],
        lambda A, B: A and (A or B),
        lambda A, B: A,
    )

    assert expressions_are_equivalent(
        ["A", "B"],
        lambda A, B: not (A and B),
        lambda A, B: (not A) or (not B),
    )

    assert expressions_are_equivalent(
        ["A", "B"],
        xor,
        xor_using_nand,
    )

    assert expressions_are_equivalent(
        ["A", "B"],
        lambda A, B: xnor(A, B),
        lambda A, B: (A and B) or ((not A) and (not B)),
    )

    for A, B, C in product((False, True), repeat=3):
        assert majority(A, B, C) == (
            (A and B) or (A and C) or (B and C)
        )

    for first, second in binary_examples:
        assert add_binary_strings(first, second) == bin(
            int(first, 2) + int(second, 2)
        )[2:]

    print("All self-verification tests passed.")


run_all_verification_tests()


# ============================================================================
# 74. FINAL REFERENCE TABLE
# ============================================================================

print("\n" + "=" * 80)
print("74. BOOLEAN GATE REFERENCE")
print("=" * 80)

print(
    """
Gate    Expression             Meaning
------------------------------------------------
AND     A and B                Both true
OR      A or B                 At least one true
NOT     not A                  Inverts A
XOR     A != B                 Inputs differ
NAND    not(A and B)           NOT of AND
NOR     not(A or B)            NOT of OR
XNOR    not(A != B)            Inputs are equal
"""
)


# ============================================================================
# 75. FINAL TRUTH TABLE
# ============================================================================

print("=" * 80)
print("75. FINAL TWO-INPUT TRUTH TABLE")
print("=" * 80)

print(
    "A B | AND OR NOT-A NOT-B XOR NAND NOR XNOR"
)
print("-" * 52)

for A, B in product((False, True), repeat=2):
    print(
        f"{int(A)} {int(B)} |"
        f"  {int(A and B)}"
        f"   {int(A or B)}"
        f"    {int(not A)}"
        f"     {int(not B)}"
        f"    {int(xor(A, B))}"
        f"    {int(nand(A, B))}"
        f"    {int(nor(A, B))}"
        f"    {int(xnor(A, B))}"
    )


print("\nBoolean algebra study script completed successfully.")
