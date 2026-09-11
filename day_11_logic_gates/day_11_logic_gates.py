"""
LOGIC GATES
===========

A self-contained study and demonstration program covering:

1. Binary logic and Boolean values
2. AND gate
3. OR gate
4. NOT gate
5. NAND gate
6. NOR gate
7. XOR gate
8. XNOR gate
9. Truth tables
10. Boolean expressions
11. Universal gates
12. Gate equivalence and relationships
13. Compound logic circuits
14. Half adder
15. Full adder
16. Multiplexer
17. Equality and parity checking
18. Validation and edge cases
19. Practical applications
20. Testing and implementation considerations

The program uses only Python's standard library.
"""


# ============================================================================
# 1. FOUNDATIONS: BINARY LOGIC
# ============================================================================

print("=" * 78)
print("LOGIC GATES")
print("=" * 78)

print("""
Digital logic works primarily with two logical states:

0 -> False, LOW, OFF
1 -> True, HIGH, ON

A logic gate receives one or more binary inputs and produces a binary output.

Boolean algebra is the mathematical system used to describe these operations.
Python's bool type maps naturally to Boolean logic.
""")

print("Python Boolean values:")
print("False =", False)
print("True  =", True)
print("False as integer =", int(False))
print("True as integer  =", int(True))


def bit(value):
    """
    Convert a Python Boolean value to a digital logic bit.

    False -> 0
    True  -> 1
    """
    return int(bool(value))


def validate_bit(value):
    """
    Validate that a value represents exactly one binary state.

    Accepted:
        0
        1
        False
        True

    Rejected:
        Other integers
        Strings
        Floating-point values
        Arbitrary truthy/falsy objects
    """
    if isinstance(value, bool):
        return int(value)

    if isinstance(value, int) and value in (0, 1):
        return value

    raise ValueError("A logic input must be exactly 0, 1, False, or True.")


def normalize_bits(*inputs):
    """Validate and normalize any number of binary inputs."""
    return tuple(validate_bit(value) for value in inputs)


# ============================================================================
# 2. BASIC LOGIC GATES
# ============================================================================

print("\n" + "=" * 78)
print("BASIC LOGIC GATES")
print("=" * 78)


def AND(a, b):
    """
    AND gate.

    Boolean expression:
        Y = A · B

    The output is 1 only when both inputs are 1.
    """
    a, b = normalize_bits(a, b)
    return a & b


def OR(a, b):
    """
    OR gate.

    Boolean expression:
        Y = A + B

    In Boolean algebra, + represents OR rather than arithmetic addition.

    The output is 1 when at least one input is 1.
    """
    a, b = normalize_bits(a, b)
    return a | b


def NOT(a):
    """
    NOT gate.

    Boolean expression:
        Y = A'

    The output is the complement of the input.
    """
    a = validate_bit(a)
    return 1 - a


def NAND(a, b):
    """
    NAND gate.

    Boolean expression:
        Y = (A · B)'

    NAND is NOT followed by AND.
    """
    return NOT(AND(a, b))


def NOR(a, b):
    """
    NOR gate.

    Boolean expression:
        Y = (A + B)'

    NOR is NOT followed by OR.
    """
    return NOT(OR(a, b))


def XOR(a, b):
    """
    XOR gate.

    Boolean expression:
        Y = A ⊕ B
        Y = A'B + AB'

    The output is 1 when the two inputs are different.
    """
    a, b = normalize_bits(a, b)
    return a ^ b


def XNOR(a, b):
    """
    XNOR gate.

    Boolean expression:
        Y = (A ⊕ B)'

    The output is 1 when the two inputs are equal.
    """
    return NOT(XOR(a, b))


print("AND(1, 1)  =", AND(1, 1))
print("OR(0, 1)   =", OR(0, 1))
print("NOT(1)     =", NOT(1))
print("NAND(1, 1) =", NAND(1, 1))
print("NOR(0, 0)  =", NOR(0, 0))
print("XOR(0, 1)  =", XOR(0, 1))
print("XNOR(1, 1) =", XNOR(1, 1))


# ============================================================================
# 3. TWO-INPUT TRUTH TABLES
# ============================================================================

print("\n" + "=" * 78)
print("TWO-INPUT TRUTH TABLES")
print("=" * 78)

print("""
For two binary inputs there are:

    2^2 = 4

possible input combinations.
""")

two_input_combinations = [
    (0, 0),
    (0, 1),
    (1, 0),
    (1, 1),
]

print("A B | AND OR NAND NOR XOR XNOR")
print("-" * 31)

for a, b in two_input_combinations:
    print(
        f"{a} {b} |  "
        f"{AND(a, b)}   "
        f"{OR(a, b)}   "
        f"{NAND(a, b)}    "
        f"{NOR(a, b)}   "
        f"{XOR(a, b)}    "
        f"{XNOR(a, b)}"
    )


# ============================================================================
# 4. NOT TRUTH TABLE
# ============================================================================

print("\n" + "=" * 78)
print("NOT GATE TRUTH TABLE")
print("=" * 78)

print("A | NOT A")
print("--------")

for a in (0, 1):
    print(f"{a} |   {NOT(a)}")


# ============================================================================
# 5. BOOLEAN EXPRESSIONS
# ============================================================================

print("\n" + "=" * 78)
print("BOOLEAN EXPRESSIONS")
print("=" * 78)

print("""
Common Boolean notation:

AND:
    A · B
    AB
    A AND B

OR:
    A + B
    A OR B

NOT:
    A'
    ¬A
    NOT A

XOR:
    A ⊕ B

XNOR:
    (A ⊕ B)'

Important distinction:

Arithmetic:
    1 + 1 = 2

Boolean algebra:
    1 OR 1 = 1

Therefore Boolean operators should not be interpreted as ordinary
arithmetic operators.
""")

a, b = 1, 0

print("A =", a)
print("B =", b)
print("A AND B =", AND(a, b))
print("A OR B  =", OR(a, b))
print("A XOR B =", XOR(a, b))
print("A XNOR B =", XNOR(a, b))


# ============================================================================
# 6. THREE-INPUT LOGIC
# ============================================================================

print("\n" + "=" * 78)
print("MULTI-INPUT LOGIC")
print("=" * 78)

print("""
A gate can conceptually have more than two inputs.

For an AND operation:
    A · B · C

The result is 1 only when every input is 1.

For an OR operation:
    A + B + C

The result is 1 when at least one input is 1.
""")


def AND_many(*inputs):
    """Return 1 only when every supplied input is 1."""
    if not inputs:
        raise ValueError("AND_many requires at least one input.")

    normalized = normalize_bits(*inputs)
    return int(all(normalized))


def OR_many(*inputs):
    """Return 1 when at least one supplied input is 1."""
    if not inputs:
        raise ValueError("OR_many requires at least one input.")

    normalized = normalize_bits(*inputs)
    return int(any(normalized))


print("AND_many(1, 1, 1) =", AND_many(1, 1, 1))
print("AND_many(1, 1, 0) =", AND_many(1, 1, 0))
print("OR_many(0, 0, 1)  =", OR_many(0, 0, 1))
print("OR_many(0, 0, 0)  =", OR_many(0, 0, 0))


# ============================================================================
# 7. EXHAUSTIVE THREE-INPUT TRUTH TABLE
# ============================================================================

print("\n" + "=" * 78)
print("THREE-INPUT AND/OR")
print("=" * 78)

print("A B C | AND OR")
print("--------------")

for a in (0, 1):
    for b in (0, 1):
        for c in (0, 1):
            print(
                f"{a} {b} {c} | "
                f" {AND_many(a, b, c)}   "
                f"{OR_many(a, b, c)}"
            )


# ============================================================================
# 8. FUNDAMENTAL IDENTITIES
# ============================================================================

print("\n" + "=" * 78)
print("BOOLEAN IDENTITIES")
print("=" * 78)

print("""
Important Boolean identities include:

Identity laws:
    A · 1 = A
    A + 0 = A

Null laws:
    A · 0 = 0
    A + 1 = 1

Idempotent laws:
    A · A = A
    A + A = A

Complement laws:
    A · A' = 0
    A + A' = 1

Double negation:
    (A')' = A

Commutative laws:
    A · B = B · A
    A + B = B + A

Associative laws:
    (A · B) · C = A · (B · C)
    (A + B) + C = A + (B + C)

Distributive laws:
    A · (B + C) = AB + AC
    A + BC = (A + B)(A + C)

De Morgan's laws:
    (AB)' = A' + B'
    (A + B)' = A'B'

These identities are useful for simplifying circuits.
""")


def verify_boolean_identity(left_expression, right_expression, variables):
    """
    Compare two Boolean expressions for every possible input combination.

    `left_expression` and `right_expression` are functions accepting the
    same number of positional Boolean inputs.
    """
    for combination in variables:
        if left_expression(*combination) != right_expression(*combination):
            return False
    return True


all_pairs = two_input_combinations

print(
    "De Morgan law 1:",
    verify_boolean_identity(
        lambda a, b: NOT(AND(a, b)),
        lambda a, b: OR(NOT(a), NOT(b)),
        all_pairs,
    ),
)

print(
    "De Morgan law 2:",
    verify_boolean_identity(
        lambda a, b: NOT(OR(a, b)),
        lambda a, b: AND(NOT(a), NOT(b)),
        all_pairs,
    ),
)


# ============================================================================
# 9. GATE RELATIONSHIPS
# ============================================================================

print("\n" + "=" * 78)
print("RELATIONSHIPS BETWEEN GATES")
print("=" * 78)

print("""
NAND:
    NAND(A, B) = NOT(AND(A, B))

NOR:
    NOR(A, B) = NOT(OR(A, B))

XOR:
    XOR(A, B) = A'B + AB'

XNOR:
    XNOR(A, B) = AB + A'B'

XNOR is the complement of XOR.

Therefore:

    XNOR(A, B) = NOT(XOR(A, B))

XOR is commonly interpreted as:
    "Exactly one input is 1" for two inputs.

XNOR is commonly interpreted as:
    "The inputs are equal" for two inputs.
""")

for a, b in all_pairs:
    print(
        f"A={a}, B={b}: "
        f"XOR={XOR(a, b)}, "
        f"XNOR={XNOR(a, b)}, "
        f"equal={int(a == b)}"
    )


# ============================================================================
# 10. UNIVERSAL GATES
# ============================================================================

print("\n" + "=" * 78)
print("UNIVERSAL GATES: NAND AND NOR")
print("=" * 78)

print("""
A universal gate can be used by itself to construct the fundamental
logic operations.

NAND can construct NOT:
    NOT(A) = NAND(A, A)

NAND can construct AND:
    AND(A, B) = NAND(NAND(A, B), NAND(A, B))

NAND can construct OR:
    OR(A, B) = NAND(NAND(A, A), NAND(B, B))

Similarly, NOR can construct:

    NOT(A) = NOR(A, A)

    OR(A, B) = NOR(NOR(A, B), NOR(A, B))

    AND(A, B) = NOR(NOR(A, A), NOR(B, B))

This property is important in digital circuit design because an entire
logic system can theoretically be constructed from a single gate type.
""")


def NAND_only_not(a):
    return NAND(a, a)


def NAND_only_and(a, b):
    temporary = NAND(a, b)
    return NAND(temporary, temporary)


def NAND_only_or(a, b):
    not_a = NAND(a, a)
    not_b = NAND(b, b)
    return NAND(not_a, not_b)


def NOR_only_not(a):
    return NOR(a, a)


def NOR_only_or(a, b):
    temporary = NOR(a, b)
    return NOR(temporary, temporary)


def NOR_only_and(a, b):
    not_a = NOR(a, a)
    not_b = NOR(b, b)
    return NOR(not_a, not_b)


print("\nNAND-only implementations:")

for a, b in all_pairs:
    print(
        f"{a} {b} -> "
        f"AND={NAND_only_and(a, b)}, "
        f"OR={NAND_only_or(a, b)}"
    )

print("\nNOR-only implementations:")

for a, b in all_pairs:
    print(
        f"{a} {b} -> "
        f"AND={NOR_only_and(a, b)}, "
        f"OR={NOR_only_or(a, b)}"
    )


# ============================================================================
# 11. COMPOUND LOGIC CIRCUITS
# ============================================================================

print("\n" + "=" * 78)
print("COMPOUND LOGIC CIRCUITS")
print("=" * 78)

print("""
Real digital systems are usually built by combining gates.

Example:

    Y = (A AND B) OR (NOT C)

This circuit contains:

    1. An AND operation
    2. A NOT operation
    3. An OR operation
""")


def compound_circuit(a, b, c):
    """Implement Y = (A AND B) OR (NOT C)."""
    first_stage = AND(a, b)
    second_stage = NOT(c)
    output = OR(first_stage, second_stage)
    return output


print("A B C | Y = (A AND B) OR (NOT C)")
print("--------------------------------")

for a in (0, 1):
    for b in (0, 1):
        for c in (0, 1):
            print(f"{a} {b} {c} | {compound_circuit(a, b, c)}")


def equivalent_circuit(a, b, c):
    """
    Another implementation of:

        Y = AB + C'

    This function makes intermediate signals explicit.
    """
    ab = AND(a, b)
    not_c = NOT(c)
    return OR(ab, not_c)


print(
    "\nCompound circuit equivalence:",
    verify_boolean_identity(
        compound_circuit,
        equivalent_circuit,
        [
            (a, b, c)
            for a in (0, 1)
            for b in (0, 1)
            for c in (0, 1)
        ],
    ),
)


# ============================================================================
# 12. XOR IMPLEMENTATIONS
# ============================================================================

print("\n" + "=" * 78)
print("XOR IMPLEMENTATIONS")
print("=" * 78)

print("""
XOR can be expressed using AND, OR, and NOT:

    A XOR B = A'B + AB'

It can also be expressed using NAND gates alone.

One NAND-only construction is:

    X1 = NAND(A, B)
    X2 = NAND(A, X1)
    X3 = NAND(B, X1)
    XOR = NAND(X2, X3)
""")


def XOR_using_basic_gates(a, b):
    """Implement XOR using only AND, OR, and NOT."""
    return OR(
        AND(NOT(a), b),
        AND(a, NOT(b)),
    )


def XOR_using_nand(a, b):
    """Implement XOR using NAND gates only."""
    x1 = NAND(a, b)
    x2 = NAND(a, x1)
    x3 = NAND(b, x1)
    return NAND(x2, x3)


print("A B | XOR | basic-gates | NAND-only")
print("-----------------------------------")

for a, b in all_pairs:
    print(
        f"{a} {b} |  {XOR(a, b)}  |"
        f"      {XOR_using_basic_gates(a, b)}      |"
        f"      {XOR_using_nand(a, b)}"
    )


# ============================================================================
# 13. XNOR AS AN EQUALITY CHECK
# ============================================================================

print("\n" + "=" * 78)
print("XNOR AS AN EQUALITY CHECK")
print("=" * 78)

print("""
XNOR is particularly useful for equality comparison.

For two bits:

    A XNOR B = 1

exactly when:

    A == B
""")


def equal_bits(a, b):
    return XNOR(a, b)


for a, b in all_pairs:
    print(f"{a} == {b} -> {equal_bits(a, b)}")


# ============================================================================
# 14. PARITY
# ============================================================================

print("\n" + "=" * 78)
print("XOR AND PARITY")
print("=" * 78)

print("""
XOR has an important relationship with parity.

For several bits:

    A XOR B XOR C ...

is 1 when an odd number of inputs are 1.

It is 0 when an even number of inputs are 1.

This property is used in parity generation and checking.
""")


def XOR_many(*inputs):
    """Return the XOR of all supplied binary inputs."""
    if not inputs:
        raise ValueError("XOR_many requires at least one input.")

    result = 0

    for value in inputs:
        result ^= validate_bit(value)

    return result


parity_examples = [
    (0, 0, 0),
    (0, 0, 1),
    (0, 1, 1),
    (1, 1, 1),
    (1, 0, 1),
]

for values in parity_examples:
    print(f"{values} -> XOR parity = {XOR_many(*values)}")


# ============================================================================
# 15. HALF ADDER
# ============================================================================

print("\n" + "=" * 78)
print("HALF ADDER")
print("=" * 78)

print("""
A half adder adds two one-bit binary numbers.

Inputs:
    A
    B

Outputs:
    Sum
    Carry

Equations:

    Sum   = A XOR B
    Carry = A AND B
""")


def half_adder(a, b):
    """Return the sum and carry produced by adding two binary bits."""
    a, b = normalize_bits(a, b)

    sum_bit = XOR(a, b)
    carry_bit = AND(a, b)

    return sum_bit, carry_bit


print("A B | Sum Carry")
print("--------------")

for a, b in all_pairs:
    sum_bit, carry_bit = half_adder(a, b)
    print(f"{a} {b} |  {sum_bit}    {carry_bit}")


# ============================================================================
# 16. FULL ADDER
# ============================================================================

print("\n" + "=" * 78)
print("FULL ADDER")
print("=" * 78)

print("""
A full adder adds three one-bit values:

    A
    B
    Carry-in

Outputs:

    Sum
    Carry-out

Equations:

    Sum = A XOR B XOR Cin

    Carry-out = AB + Cin(A XOR B)

A full adder can be constructed from two half adders and one OR gate.
""")


def full_adder(a, b, carry_in):
    """
    Implement a full adder using two half adders and one OR gate.
    """
    first_sum, first_carry = half_adder(a, b)
    final_sum, second_carry = half_adder(first_sum, carry_in)

    carry_out = OR(first_carry, second_carry)

    return final_sum, carry_out


print("A B Cin | Sum Cout")
print("------------------")

for a in (0, 1):
    for b in (0, 1):
        for carry_in in (0, 1):
            sum_bit, carry_out = full_adder(a, b, carry_in)
            print(f"{a} {b}  {carry_in}  |  {sum_bit}   {carry_out}")


# ============================================================================
# 17. RIPPLE-CARRY ADDER
# ============================================================================

print("\n" + "=" * 78)
print("MULTI-BIT BINARY ADDITION")
print("=" * 78)

print("""
A multi-bit binary adder can be constructed by connecting full adders.

The carry produced by one position becomes the carry-in for the next
position.

This is called a ripple-carry arrangement because the carry propagates
through the stages.
""")


def ripple_carry_add(binary_a, binary_b):
    """
    Add two non-negative binary integers represented as equal-length
    strings.

    Example:
        "1011" + "0011" -> "1110"

    The implementation demonstrates the logical structure rather than
    using Python's built-in integer addition.
    """
    if not isinstance(binary_a, str) or not isinstance(binary_b, str):
        raise TypeError("Binary inputs must be strings.")

    if len(binary_a) != len(binary_b):
        raise ValueError("Binary strings must have equal length.")

    if not binary_a:
        raise ValueError("Binary strings cannot be empty.")

    if any(character not in "01" for character in binary_a + binary_b):
        raise ValueError("Binary strings may contain only 0 and 1.")

    carry = 0
    result = []

    for a_character, b_character in zip(
        reversed(binary_a),
        reversed(binary_b),
    ):
        a = int(a_character)
        b = int(b_character)

        sum_bit, carry = full_adder(a, b, carry)
        result.append(str(sum_bit))

    if carry:
        result.append(str(carry))

    return "".join(reversed(result))


addition_examples = [
    ("0000", "0000"),
    ("0001", "0001"),
    ("0011", "0101"),
    ("1010", "0011"),
    ("1111", "0001"),
]

for left, right in addition_examples:
    result = ripple_carry_add(left, right)
    expected = bin(int(left, 2) + int(right, 2))[2:]
    print(f"{left} + {right} = {result} | expected = {expected}")


# ============================================================================
# 18. MULTIPLEXER
# ============================================================================

print("\n" + "=" * 78)
print("2-TO-1 MULTIPLEXER")
print("=" * 78)

print("""
A multiplexer, or MUX, selects one input from several available inputs.

For a 2-to-1 multiplexer:

    Inputs:
        D0
        D1

    Select:
        S

    Output:
        Y

Equation:

    Y = S'D0 + SD1

When S = 0:
    Y = D0

When S = 1:
    Y = D1
""")


def multiplexer_2_to_1(d0, d1, select):
    """Implement Y = S'D0 + SD1."""
    d0, d1, select = normalize_bits(d0, d1, select)

    first_term = AND(NOT(select), d0)
    second_term = AND(select, d1)

    return OR(first_term, second_term)


for select in (0, 1):
    for d0 in (0, 1):
        for d1 in (0, 1):
            output = multiplexer_2_to_1(d0, d1, select)
            print(
                f"D0={d0}, D1={d1}, S={select} -> Y={output}"
            )


# ============================================================================
# 19. BINARY EQUALITY COMPARISON
# ============================================================================

print("\n" + "=" * 78)
print("MULTI-BIT EQUALITY COMPARISON")
print("=" * 78)

print("""
To determine whether two multi-bit binary values are equal:

1. Compare each corresponding bit using XNOR.
2. AND all XNOR outputs.

For:

    A3 A2 A1 A0
    B3 B2 B1 B0

equality is:

    (A3 XNOR B3)
    AND
    (A2 XNOR B2)
    AND
    (A1 XNOR B1)
    AND
    (A0 XNOR B0)
""")


def binary_equal(bits_a, bits_b):
    """
    Compare two equal-length binary strings using XNOR-style comparison.
    """
    if not isinstance(bits_a, str) or not isinstance(bits_b, str):
        raise TypeError("Binary values must be strings.")

    if len(bits_a) != len(bits_b):
        raise ValueError("Binary values must have equal length.")

    if not bits_a:
        raise ValueError("Binary values cannot be empty.")

    if any(character not in "01" for character in bits_a + bits_b):
        raise ValueError("Binary values may contain only 0 and 1.")

    comparisons = [
        XNOR(int(a), int(b))
        for a, b in zip(bits_a, bits_b)
    ]

    return AND_many(*comparisons)


comparison_examples = [
    ("1010", "1010"),
    ("1010", "1000"),
    ("0000", "0000"),
    ("1111", "0111"),
]

for left, right in comparison_examples:
    print(
        f"{left} == {right} -> "
        f"{binary_equal(left, right)}"
    )


# ============================================================================
# 20. LOGIC GATE OBJECT MODEL
# ============================================================================

print("\n" + "=" * 78)
print("OBJECT-ORIENTED LOGIC GATES")
print("=" * 78)

print("""
A logic gate can also be modeled as an object.

This approach is useful when constructing larger circuit representations,
where gates have names, input connections, and outputs.
""")


class LogicGate:
    """Base class for a simple logic gate."""

    name = "Logic Gate"

    def evaluate(self, *inputs):
        """Evaluate the gate. Subclasses provide the implementation."""
        raise NotImplementedError("Subclasses must implement evaluate().")

    def __call__(self, *inputs):
        """Allow a gate object to be called like a function."""
        return self.evaluate(*inputs)

    def __repr__(self):
        return self.name


class AndGate(LogicGate):
    name = "AND"

    def evaluate(self, a, b):
        return AND(a, b)


class OrGate(LogicGate):
    name = "OR"

    def evaluate(self, a, b):
        return OR(a, b)


class NotGate(LogicGate):
    name = "NOT"

    def evaluate(self, a):
        return NOT(a)


class NandGate(LogicGate):
    name = "NAND"

    def evaluate(self, a, b):
        return NAND(a, b)


class NorGate(LogicGate):
    name = "NOR"

    def evaluate(self, a, b):
        return NOR(a, b)


class XorGate(LogicGate):
    name = "XOR"

    def evaluate(self, a, b):
        return XOR(a, b)


class XnorGate(LogicGate):
    name = "XNOR"

    def evaluate(self, a, b):
        return XNOR(a, b)


gate_objects = [
    AndGate(),
    OrGate(),
    NandGate(),
    NorGate(),
    XorGate(),
    XnorGate(),
]

for gate in gate_objects:
    print(f"{gate}(1, 0) = {gate(1, 0)}")

not_gate = NotGate()
print(f"{not_gate}(1) = {not_gate(1)}")


# ============================================================================
# 21. CIRCUIT COMPOSITION WITH OBJECTS
# ============================================================================

print("\n" + "=" * 78)
print("CIRCUIT COMPOSITION")
print("=" * 78)

print("""
A compound circuit can be represented as a collection of gate objects.

Example:

    X = A AND B
    Y = NOT C
    OUT = X OR Y
""")


class CompoundCircuit:
    """
    Circuit implementing:

        OUT = (A AND B) OR (NOT C)
    """

    def __init__(self):
        self.and_gate = AndGate()
        self.not_gate = NotGate()
        self.or_gate = OrGate()

    def evaluate(self, a, b, c):
        first = self.and_gate(a, b)
        second = self.not_gate(c)
        return self.or_gate(first, second)


circuit = CompoundCircuit()

for a, b, c in [
    (0, 0, 0),
    (0, 1, 0),
    (1, 1, 0),
    (1, 1, 1),
]:
    print(
        f"A={a}, B={b}, C={c} -> "
        f"OUT={circuit.evaluate(a, b, c)}"
    )


# ============================================================================
# 22. LOGIC EXPRESSION EVALUATION
# ============================================================================

print("\n" + "=" * 78)
print("COMPOUND BOOLEAN EXPRESSIONS")
print("=" * 78)

print("""
A circuit can contain several nested operations.

Example:

    Y = ((A OR B) AND (NOT C)) XOR D

The safest implementation strategy is to name intermediate signals.
This makes the logic easier to inspect and debug.
""")


def advanced_logic_expression(a, b, c, d):
    """Implement ((A OR B) AND (NOT C)) XOR D."""
    a, b, c, d = normalize_bits(a, b, c, d)

    or_result = OR(a, b)
    not_c = NOT(c)
    and_result = AND(or_result, not_c)
    return XOR(and_result, d)


for a in (0, 1):
    for b in (0, 1):
        for c in (0, 1):
            for d in (0, 1):
                output = advanced_logic_expression(a, b, c, d)

                if output:
                    print(
                        f"A={a}, B={b}, C={c}, D={d} -> "
                        f"Y={output}"
                    )


# ============================================================================
# 23. EDGE CASES AND VALIDATION
# ============================================================================

print("\n" + "=" * 78)
print("INPUT VALIDATION AND EDGE CASES")
print("=" * 78)

print("""
Digital logic is binary. A robust implementation should not silently
convert arbitrary values into logical states.

For example:

    bool("0") == True

This is because a non-empty Python string is truthy.

That behavior is usually undesirable when parsing digital bits.

The validation functions above therefore accept only:

    0
    1
    False
    True
""")


invalid_inputs = [
    2,
    -1,
    "0",
    "1",
    0.5,
    None,
]

for invalid in invalid_inputs:
    try:
        validate_bit(invalid)
        print(f"{invalid!r} unexpectedly accepted")
    except ValueError as error:
        print(f"{invalid!r} rejected: {error}")


# ============================================================================
# 24. GATE PROPERTIES
# ============================================================================

print("\n" + "=" * 78)
print("GATE PROPERTIES")
print("=" * 78)

print("""
AND and OR are commutative:

    A AND B = B AND A
    A OR B  = B OR A

XOR is also commutative:

    A XOR B = B XOR A

XNOR is also commutative:

    A XNOR B = B XNOR A

NOT is unary and therefore has only one input.

NAND and NOR are complements of AND and OR.
""")


def test_commutative(operation):
    """Test whether a two-input operation is commutative."""
    return all(
        operation(a, b) == operation(b, a)
        for a, b in all_pairs
    )


for operation, name in [
    (AND, "AND"),
    (OR, "OR"),
    (NAND, "NAND"),
    (NOR, "NOR"),
    (XOR, "XOR"),
    (XNOR, "XNOR"),
]:
    print(f"{name} commutative -> {test_commutative(operation)}")


# ============================================================================
# 25. ASSOCIATIVITY
# ============================================================================

print("\n" + "=" * 78)
print("ASSOCIATIVITY")
print("=" * 78)

print("""
AND, OR, and XOR are associative:

    (A AND B) AND C = A AND (B AND C)

    (A OR B) OR C = A OR (B OR C)

    (A XOR B) XOR C = A XOR (B XOR C)

This means groups of these operations can be rearranged without changing
the logical result.

Not every Boolean operation has this property.
""")


def test_associative(operation):
    """Test associativity for a binary Boolean operation."""
    for a in (0, 1):
        for b in (0, 1):
            for c in (0, 1):
                left = operation(operation(a, b), c)
                right = operation(a, operation(b, c))

                if left != right:
                    return False

    return True


for operation, name in [
    (AND, "AND"),
    (OR, "OR"),
    (XOR, "XOR"),
    (XNOR, "XNOR"),
    (NAND, "NAND"),
    (NOR, "NOR"),
]:
    print(f"{name} associative -> {test_associative(operation)}")


# ============================================================================
# 26. MONOTONICITY
# ============================================================================

print("\n" + "=" * 78)
print("IMPORTANT DISTINCTION: XOR IS NOT ORDINARY OR")
print("=" * 78)

print("""
OR means:

    At least one input is 1.

XOR means:

    The inputs are different.

Therefore:

    OR(1, 1)  = 1
    XOR(1, 1) = 0

This is one of the most common beginner mistakes.
""")

print("OR(1, 1)  =", OR(1, 1))
print("XOR(1, 1) =", XOR(1, 1))


# ============================================================================
# 27. NAND AND NOR OUTPUT CONDITIONS
# ============================================================================

print("\n" + "=" * 78)
print("NAND AND NOR BEHAVIOR")
print("=" * 78)

print("""
NAND is 0 only when every input to the underlying AND is 1.

For two inputs:

    NAND(1, 1) = 0

All other combinations produce 1.

NOR is 1 only when every input to the underlying OR is 0.

For two inputs:

    NOR(0, 0) = 1

All other combinations produce 0.
""")

print("NAND truth table:")
for pair in all_pairs:
    print(pair, "->", NAND(*pair))

print("\nNOR truth table:")
for pair in all_pairs:
    print(pair, "->", NOR(*pair))


# ============================================================================
# 28. LOGIC GATE COMPARISON
# ============================================================================

print("\n" + "=" * 78)
print("LOGIC GATE COMPARISON")
print("=" * 78)

print("""
Gate   | Output condition
-------|------------------------------------------------
AND    | 1 only when all inputs are 1
OR     | 1 when at least one input is 1
NOT    | Inverts its single input
NAND   | Inverse of AND
NOR    | Inverse of OR
XOR    | 1 when the two inputs differ
XNOR   | 1 when the two inputs are equal

For two inputs, AND and OR are monotonic Boolean operations.
XOR and XNOR have different behavior because they depend on whether
the input values agree or disagree.
""")


# ============================================================================
# 29. SIMPLE LOGIC-BASED ACCESS CONTROL
# ============================================================================

print("\n" + "=" * 78)
print("PRACTICAL APPLICATION: ACCESS CONTROL")
print("=" * 78)

print("""
Logic gates can model simple decision systems.

Example requirement:

    Access is allowed when:
        valid_card AND valid_pin

Or:

    Emergency access =
        administrator OR emergency_override
""")


def normal_access(valid_card, valid_pin):
    return AND(valid_card, valid_pin)


def emergency_access(administrator, emergency_override):
    return OR(administrator, emergency_override)


for card, pin in all_pairs:
    print(
        f"Card={card}, PIN={pin} -> "
        f"access={normal_access(card, pin)}"
    )

print("\nEmergency access:")
for administrator, override in all_pairs:
    print(
        f"Admin={administrator}, Override={override} -> "
        f"access={emergency_access(administrator, override)}"
    )


# ============================================================================
# 30. PRACTICAL APPLICATION: ALARM LOGIC
# ============================================================================

print("\n" + "=" * 78)
print("PRACTICAL APPLICATION: ALARM LOGIC")
print("=" * 78)

print("""
Suppose an alarm should activate when:

    door_open AND system_armed

This can be represented directly with an AND gate.
""")


def alarm_active(door_open, system_armed):
    return AND(door_open, system_armed)


for door in (0, 1):
    for armed in (0, 1):
        print(
            f"Door open={door}, Armed={armed} -> "
            f"Alarm={alarm_active(door, armed)}"
        )


# ============================================================================
# 31. PRACTICAL APPLICATION: EQUALITY AND DIFFERENCE
# ============================================================================

print("\n" + "=" * 78)
print("PRACTICAL APPLICATION: COMPARISON")
print("=" * 78)

print("""
XNOR is suitable for detecting equality:

    equal = XNOR(A, B)

XOR is suitable for detecting difference:

    different = XOR(A, B)
""")


def compare_bits(a, b):
    return {
        "equal": XNOR(a, b),
        "different": XOR(a, b),
    }


for a, b in all_pairs:
    print(f"{a}, {b} -> {compare_bits(a, b)}")


# ============================================================================
# 32. LOGIC CIRCUIT TESTING
# ============================================================================

print("\n" + "=" * 78)
print("AUTOMATED TESTING")
print("=" * 78)

print("""
Truth tables make exhaustive testing straightforward.

For a circuit with n binary inputs, there are:

    2^n

possible combinations.

For small circuits, exhaustive truth-table testing can therefore verify
every possible input combination.
""")


def assert_gate_truth_tables():
    """Exhaustively verify the fundamental two-input gate definitions."""

    expected_and = {
        (0, 0): 0,
        (0, 1): 0,
        (1, 0): 0,
        (1, 1): 1,
    }

    expected_or = {
        (0, 0): 0,
        (0, 1): 1,
        (1, 0): 1,
        (1, 1): 1,
    }

    expected_nand = {
        pair: 1 - value
        for pair, value in expected_and.items()
    }

    expected_nor = {
        pair: 1 - value
        for pair, value in expected_or.items()
    }

    expected_xor = {
        (0, 0): 0,
        (0, 1): 1,
        (1, 0): 1,
        (1, 1): 0,
    }

    expected_xnor = {
        pair: 1 - value
        for pair, value in expected_xor.items()
    }

    operations = [
        (AND, expected_and),
        (OR, expected_or),
        (NAND, expected_nand),
        (NOR, expected_nor),
        (XOR, expected_xor),
        (XNOR, expected_xnor),
    ]

    for operation, expected in operations:
        for pair, expected_value in expected.items():
            actual = operation(*pair)
            assert actual == expected_value, (
                f"{operation.__name__}{pair} "
                f"returned {actual}, expected {expected_value}"
            )


def assert_composite_circuits():
    """Verify important circuit relationships."""

    for a, b in all_pairs:
        assert XOR(a, b) == XOR_using_basic_gates(a, b)
        assert XOR(a, b) == XOR_using_nand(a, b)

        assert AND(a, b) == NAND_only_and(a, b)
        assert OR(a, b) == NAND_only_or(a, b)

        assert AND(a, b) == NOR_only_and(a, b)
        assert OR(a, b) == NOR_only_or(a, b)

        assert XNOR(a, b) == int(a == b)


assert_gate_truth_tables()
assert_composite_circuits()

print("All fundamental gate tests passed.")
print("All composite circuit tests passed.")


# ============================================================================
# 33. ERROR HANDLING
# ============================================================================

print("\n" + "=" * 78)
print("ERROR HANDLING")
print("=" * 78)

print("""
Typical implementation errors include:

1. Supplying non-binary values.
2. Supplying too few arguments.
3. Supplying too many arguments.
4. Mixing binary strings of different lengths.
5. Treating strings such as "0" as Boolean values without validation.
6. Confusing arithmetic addition with Boolean OR.
7. Confusing OR with XOR.
8. Forgetting that NAND and NOR invert their underlying operations.
""")


error_examples = [
    lambda: AND(1, 2),
    lambda: NOT("0"),
    lambda: AND_many(),
    lambda: ripple_carry_add("101", "11"),
    lambda: binary_equal("101", "10"),
]

for example in error_examples:
    try:
        example()
    except (TypeError, ValueError) as error:
        print(f"Handled error: {error}")


# ============================================================================
# 34. PERFORMANCE CONSIDERATIONS
# ============================================================================

print("\n" + "=" * 78)
print("PERFORMANCE CONSIDERATIONS")
print("=" * 78)

print("""
For a fixed-size individual gate, evaluation is effectively constant time.

For an exhaustive truth table with n inputs:

    number of combinations = 2^n

Therefore exhaustive testing grows exponentially with the number of
independent inputs.

Examples:

    1 input  -> 2 combinations
    2 inputs -> 4 combinations
    3 inputs -> 8 combinations
    4 inputs -> 16 combinations
    10 inputs -> 1024 combinations
    20 inputs -> 1,048,576 combinations

For large circuits, formal verification, symbolic methods, simulation
strategies, or specialized hardware-design tools may be more appropriate
than naïvely enumerating every possible input.
""")


def number_of_truth_table_rows(number_of_inputs):
    """Return the number of possible binary input combinations."""
    if not isinstance(number_of_inputs, int):
        raise TypeError("Number of inputs must be an integer.")

    if number_of_inputs < 0:
        raise ValueError("Number of inputs cannot be negative.")

    return 2 ** number_of_inputs


for input_count in [1, 2, 3, 4, 8, 10]:
    print(
        f"{input_count} input(s) -> "
        f"{number_of_truth_table_rows(input_count)} combinations"
    )


# ============================================================================
# 35. PROPAGATION DELAY AND REAL HARDWARE
# ============================================================================

print("\n" + "=" * 78)
print("REAL HARDWARE CONSIDERATIONS")
print("=" * 78)

print("""
The Python functions in this file model ideal Boolean behavior.

Physical digital gates are not instantaneous mathematical objects.

Real hardware has characteristics such as:

- Propagation delay
- Rise time
- Fall time
- Power consumption
- Fan-in
- Fan-out
- Noise margins
- Supply-voltage requirements
- Physical area
- Temperature dependence

A circuit can therefore be logically correct but still require engineering
analysis for timing, power, signal integrity, and reliability.

In synchronous digital systems, clock timing and setup/hold constraints
become especially important.
""")


# ============================================================================
# 36. HAZARD AND GLITCH CONSIDERATIONS
# ============================================================================

print("\n" + "=" * 78)
print("LOGIC HAZARDS")
print("=" * 78)

print("""
When real signals pass through gates with different propagation delays,
a circuit can temporarily produce an unintended output transition.

These transient behaviors are commonly called glitches or hazards.

The Boolean expression describes the stable logical relationship, but it
does not by itself describe the complete timing behavior of a physical
implementation.

This distinction is important:

    Boolean correctness != complete hardware timing correctness
""")


# ============================================================================
# 37. COMBINATIONAL VS SEQUENTIAL LOGIC
# ============================================================================

print("\n" + "=" * 78)
print("COMBINATIONAL VS SEQUENTIAL LOGIC")
print("=" * 78)

print("""
Logic gates are fundamental building blocks of both combinational and
sequential digital systems.

COMBINATIONAL LOGIC:

    Output depends only on current inputs.

Examples:
    Adders
    Multiplexers
    Comparators
    Decoders
    Encoders

SEQUENTIAL LOGIC:

    Output depends on current inputs and stored state.

Examples:
    Latches
    Flip-flops
    Registers
    Counters
    Memory elements

The gates themselves do not provide memory merely by performing AND, OR,
NOT, NAND, NOR, XOR, or XNOR operations. Storage requires feedback and
appropriate circuit structures.
""")


# ============================================================================
# 38. LOGIC GATES IN COMPUTERS
# ============================================================================

print("\n" + "=" * 78)
print("REAL-WORLD APPLICATIONS")
print("=" * 78)

print("""
Logic gates are fundamental to digital electronics and computing.

They contribute to:

- Arithmetic logic units
- CPUs
- GPUs
- Memory systems
- Control units
- Comparators
- Adders and subtractors
- Multiplexers and demultiplexers
- Encoders and decoders
- Communication systems
- Error detection
- Parity circuits
- Digital sensors
- Embedded systems
- Programmable logic
- Finite-state machines
- Digital signal processing hardware

At a high level, complex digital systems can be understood as networks
of elementary Boolean operations.
""")


# ============================================================================
# 39. PRACTICAL DESIGN GUIDELINES
# ============================================================================

print("\n" + "=" * 78)
print("DESIGN GUIDELINES")
print("=" * 78)

print("""
When designing a logic circuit:

1. Define the required behavior precisely.
2. Identify all inputs and outputs.
3. Build the truth table when the input space is manageable.
4. Derive Boolean expressions.
5. Simplify the expressions when appropriate.
6. Select suitable gates.
7. Consider whether NAND/NOR-only implementation is useful.
8. Verify every relevant input combination.
9. Consider propagation delay in physical hardware.
10. Consider power, area, fan-out, and fan-in constraints.
11. Test abnormal and boundary conditions.
12. Document signal names and logic assumptions clearly.

For software simulation, validate inputs rather than relying on Python's
general truthiness rules.
""")


# ============================================================================
# 40. COMPLETE GATE DEMONSTRATION
# ============================================================================

print("\n" + "=" * 78)
print("COMPLETE GATE DEMONSTRATION")
print("=" * 78)

def demonstrate_all_gates(a, b):
    """Return every fundamental two-input gate result for A and B."""
    return {
        "AND": AND(a, b),
        "OR": OR(a, b),
        "NAND": NAND(a, b),
        "NOR": NOR(a, b),
        "XOR": XOR(a, b),
        "XNOR": XNOR(a, b),
    }


for pair in all_pairs:
    print(
        f"A={pair[0]}, B={pair[1]} -> "
        f"{demonstrate_all_gates(*pair)}"
    )


# ============================================================================
# 41. FINAL VERIFICATION
# ============================================================================

print("\n" + "=" * 78)
print("FINAL VERIFICATION")
print("=" * 78)


def run_full_verification():
    """
    Run a compact collection of tests covering the important relationships
    demonstrated throughout the program.
    """

    # Fundamental truth tables.
    assert_gate_truth_tables()

    # Universal-gate equivalence.
    for a, b in all_pairs:
        assert NAND_only_not(a) == NOT(a)
        assert NAND_only_and(a, b) == AND(a, b)
        assert NAND_only_or(a, b) == OR(a, b)

        assert NOR_only_not(a) == NOT(a)
        assert NOR_only_and(a, b) == AND(a, b)
        assert NOR_only_or(a, b) == OR(a, b)

    # XOR and XNOR relationships.
    for a, b in all_pairs:
        assert XOR(a, b) == XOR_using_basic_gates(a, b)
        assert XOR(a, b) == XOR_using_nand(a, b)
        assert XNOR(a, b) == NOT(XOR(a, b))
        assert XNOR(a, b) == int(a == b)

    # De Morgan's laws.
    for a, b in all_pairs:
        assert NOT(AND(a, b)) == OR(NOT(a), NOT(b))
        assert NOT(OR(a, b)) == AND(NOT(a), NOT(b))

    # Half-adder arithmetic relationship.
    for a, b in all_pairs:
        sum_bit, carry = half_adder(a, b)
        assert a + b == sum_bit + 2 * carry

    # Full-adder arithmetic relationship.
    for a in (0, 1):
        for b in (0, 1):
            for carry_in in (0, 1):
                sum_bit, carry_out = full_adder(a, b, carry_in)
                assert (
                    a + b + carry_in
                    == sum_bit + 2 * carry_out
                )

    # Multiplexer behavior.
    for d0 in (0, 1):
        for d1 in (0, 1):
            assert multiplexer_2_to_1(d0, d1, 0) == d0
            assert multiplexer_2_to_1(d0, d1, 1) == d1

    # Binary equality.
    assert binary_equal("0000", "0000") == 1
    assert binary_equal("1010", "1010") == 1
    assert binary_equal("1010", "1011") == 0

    # Ripple-carry examples.
    for left, right in addition_examples:
        actual = int(ripple_carry_add(left, right), 2)
        expected = int(left, 2) + int(right, 2)
        assert actual == expected

    return True


if run_full_verification():
    print("All verification tests passed successfully.")


# ============================================================================
# 42. STUDY REFERENCE
# ============================================================================

print("\n" + "=" * 78)
print("QUICK REFERENCE")
print("=" * 78)

print("""
AND
    Symbol: ·
    Meaning: all inputs must be 1
    Python demonstration: AND(a, b)

OR
    Symbol: +
    Meaning: at least one input must be 1
    Python demonstration: OR(a, b)

NOT
    Symbol: '
    Meaning: invert the input
    Python demonstration: NOT(a)

NAND
    Meaning: NOT(AND)
    Universal gate: yes

NOR
    Meaning: NOT(OR)
    Universal gate: yes

XOR
    Symbol: ⊕
    Meaning: inputs differ
    Two-input truth table: 00->0, 01->1, 10->1, 11->0

XNOR
    Meaning: inputs are equal
    Two-input truth table: 00->1, 01->0, 10->0, 11->1

HALF ADDER
    Sum   = XOR(A, B)
    Carry = AND(A, B)

FULL ADDER
    Sum   = XOR(XOR(A, B), Cin)
    Carry = AB + Cin(A XOR B)

MULTIPLEXER
    Y = S'D0 + SD1

DE MORGAN'S LAWS
    (AB)'   = A' + B'
    (A + B)' = A'B'
""")

print("=" * 78)
print("END OF LOGIC GATES STUDY PROGRAM")
print("=" * 78)
