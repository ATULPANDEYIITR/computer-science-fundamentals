"""
Boolean Simplification
======================

A comprehensive, self-contained study script covering Boolean algebra from
absolute beginner level through advanced symbolic simplification.

Topics covered
--------------
1. Boolean values and logical operators
2. Boolean terminology and notation
3. Truth tables
4. Fundamental Boolean identities
5. Complement and double-complement laws
6. Identity, domination, idempotent, involution, and complement laws
7. Commutative, associative, and distributive laws
8. Absorption laws
9. De Morgan's laws
10. Consensus theorem
11. Redundancy and simplification patterns
12. Step-by-step algebraic simplification
13. Boolean expression parsing
14. Symbolic expression trees
15. Structural simplification
16. Truth-table-based equivalence checking
17. Canonical Sum of Products (SOP)
18. Canonical Product of Sums (POS)
19. Minterms and maxterms
20. Conversion between ordinary and canonical forms
21. Don't-care conditions
22. Quine-McCluskey-style minimization
23. Prime implicants and essential prime implicants
24. Complexity and performance considerations
25. Common mistakes and edge cases
26. Practical digital-logic applications
27. Automated testing of Boolean identities
28. A complete end-to-end demonstration

Notation used in comments
-------------------------
AND  : A · B, represented in Python as A & B
OR   : A + B, represented in Python as A | B
NOT  : A', represented in Python as ~A
XOR  : A ⊕ B
XNOR : A ⊙ B

The symbolic classes in this script use explicit objects for Boolean
expressions. Python's built-in bool values are used for actual evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Callable, Iterable, Optional, Sequence


# ============================================================================
# SECTION 1: BASIC BOOLEAN CONCEPTS
# ============================================================================

print("=" * 80)
print("BOOLEAN SIMPLIFICATION")
print("=" * 80)


def boolean_and(a: bool, b: bool) -> bool:
    """Return the Boolean AND of two values."""
    return a and b


def boolean_or(a: bool, b: bool) -> bool:
    """Return the Boolean OR of two values."""
    return a or b


def boolean_not(a: bool) -> bool:
    """Return the Boolean complement of a value."""
    return not a


def boolean_xor(a: bool, b: bool) -> bool:
    """Return XOR: true exactly when the inputs are different."""
    return a != b


def boolean_xnor(a: bool, b: bool) -> bool:
    """Return XNOR: true exactly when the inputs are equal."""
    return a == b


def boolean_implies(a: bool, b: bool) -> bool:
    """
    Boolean implication.

    A -> B is equivalent to A' + B.
    The only false case is A=True and B=False.
    """
    return (not a) or b


print("\nBasic Boolean operations:")
for a, b in [(False, False), (False, True), (True, False), (True, True)]:
    print(
        f"A={int(a)}, B={int(b)} | "
        f"AND={int(boolean_and(a, b))}, "
        f"OR={int(boolean_or(a, b))}, "
        f"XOR={int(boolean_xor(a, b))}, "
        f"XNOR={int(boolean_xnor(a, b))}"
    )


# ============================================================================
# SECTION 2: TRUTH TABLE GENERATION
# ============================================================================

def all_boolean_inputs(variable_names: Sequence[str]):
    """
    Generate every possible assignment for a sequence of Boolean variables.

    For n variables, there are exactly 2^n combinations.
    """
    for values in product([False, True], repeat=len(variable_names)):
        yield dict(zip(variable_names, values))


def truth_table(
    variable_names: Sequence[str],
    expression: Callable[..., bool],
) -> list[dict[str, bool]]:
    """
    Evaluate an expression for every possible input combination.

    The returned rows contain the input values followed by the output.
    """
    rows = []

    for assignment in all_boolean_inputs(variable_names):
        result = bool(expression(**assignment))
        rows.append({**assignment, "Output": result})

    return rows


def print_truth_table(
    variable_names: Sequence[str],
    expression: Callable[..., bool],
    title: str = "Truth Table",
) -> None:
    """Print a formatted truth table."""
    rows = truth_table(variable_names, expression)

    print(f"\n{title}")
    print("-" * 60)

    headers = [*variable_names, "Output"]
    print(" | ".join(headers))
    print("-" * 60)

    for row in rows:
        print(
            " | ".join(
                str(int(row[column]))
                for column in headers
            )
        )


print_truth_table(
    ["A", "B"],
    lambda A, B: A and B,
    "AND truth table",
)


# ============================================================================
# SECTION 3: BOOLEAN ALGEBRA IDENTITIES
# ============================================================================

"""
Boolean algebra is governed by identities that preserve logical behavior.

The most important identities are demonstrated below using truth tables.

Identity laws:
    A + 0 = A
    A · 1 = A

Null / domination laws:
    A + 1 = 1
    A · 0 = 0

Idempotent laws:
    A + A = A
    A · A = A

Complement laws:
    A + A' = 1
    A · A' = 0

Involution:
    (A')' = A

Commutative:
    A + B = B + A
    A · B = B · A

Associative:
    A + (B + C) = (A + B) + C
    A · (B · C) = (A · B) · C

Distributive:
    A(B + C) = AB + AC
    A + BC = (A + B)(A + C)

Absorption:
    A + AB = A
    A(A + B) = A
"""


def assert_boolean_identity(
    variable_names: Sequence[str],
    left: Callable[..., bool],
    right: Callable[..., bool],
    description: str,
) -> None:
    """Verify an alleged Boolean identity exhaustively."""
    for assignment in all_boolean_inputs(variable_names):
        left_value = bool(left(**assignment))
        right_value = bool(right(**assignment))

        if left_value != right_value:
            raise AssertionError(
                f"Identity failed: {description}; "
                f"counterexample={assignment}"
            )

    print(f"[PASS] {description}")


def demonstrate_fundamental_identities() -> None:
    print("\nFundamental Boolean identities:")

    assert_boolean_identity(
        ["A"],
        lambda A: A or False,
        lambda A: A,
        "A + 0 = A",
    )

    assert_boolean_identity(
        ["A"],
        lambda A: A and True,
        lambda A: A,
        "A · 1 = A",
    )

    assert_boolean_identity(
        ["A"],
        lambda A: A or True,
        lambda A: True,
        "A + 1 = 1",
    )

    assert_boolean_identity(
        ["A"],
        lambda A: A and False,
        lambda A: False,
        "A · 0 = 0",
    )

    assert_boolean_identity(
        ["A"],
        lambda A: A or A,
        lambda A: A,
        "A + A = A",
    )

    assert_boolean_identity(
        ["A"],
        lambda A: A and A,
        lambda A: A,
        "A · A = A",
    )

    assert_boolean_identity(
        ["A"],
        lambda A: A or (not A),
        lambda A: True,
        "A + A' = 1",
    )

    assert_boolean_identity(
        ["A"],
        lambda A: A and (not A),
        lambda A: False,
        "A · A' = 0",
    )

    assert_boolean_identity(
        ["A"],
        lambda A: not (not A),
        lambda A: A,
        "(A')' = A",
    )

    assert_boolean_identity(
        ["A", "B"],
        lambda A, B: A or B,
        lambda A, B: B or A,
        "A + B = B + A",
    )

    assert_boolean_identity(
        ["A", "B"],
        lambda A, B: A and B,
        lambda A, B: B and A,
        "AB = BA",
    )

    assert_boolean_identity(
        ["A", "B", "C"],
        lambda A, B, C: A or (B or C),
        lambda A, B, C: (A or B) or C,
        "A + (B + C) = (A + B) + C",
    )

    assert_boolean_identity(
        ["A", "B", "C"],
        lambda A, B, C: A and (B and C),
        lambda A, B, C: (A and B) and C,
        "A(BC) = (AB)C",
    )

    assert_boolean_identity(
        ["A", "B", "C"],
        lambda A, B, C: A and (B or C),
        lambda A, B, C: (A and B) or (A and C),
        "A(B + C) = AB + AC",
    )

    assert_boolean_identity(
        ["A", "B", "C"],
        lambda A, B, C: A or (B and C),
        lambda A, B, C: (A or B) and (A or C),
        "A + BC = (A + B)(A + C)",
    )

    assert_boolean_identity(
        ["A", "B"],
        lambda A, B: A or (A and B),
        lambda A, B: A,
        "A + AB = A",
    )

    assert_boolean_identity(
        ["A", "B"],
        lambda A, B: A and (A or B),
        lambda A, B: A,
        "A(A + B) = A",
    )


demonstrate_fundamental_identities()


# ============================================================================
# SECTION 4: DE MORGAN'S LAWS
# ============================================================================

"""
De Morgan's laws are central to Boolean simplification.

First law:
    (A + B)' = A'B'

Second law:
    (AB)' = A' + B'

For three variables:

    (A + B + C)' = A'B'C'

    (ABC)' = A' + B' + C'

The general principle is:

    NOT(OR of terms) = AND of the individual NOT terms

    NOT(AND of terms) = OR of the individual NOT terms
"""


def demonstrate_de_morgan() -> None:
    print("\nDe Morgan's laws:")

    assert_boolean_identity(
        ["A", "B"],
        lambda A, B: not (A or B),
        lambda A, B: (not A) and (not B),
        "(A + B)' = A'B'",
    )

    assert_boolean_identity(
        ["A", "B"],
        lambda A, B: not (A and B),
        lambda A, B: (not A) or (not B),
        "(AB)' = A' + B'",
    )

    assert_boolean_identity(
        ["A", "B", "C"],
        lambda A, B, C: not (A or B or C),
        lambda A, B, C: (not A) and (not B) and (not C),
        "(A + B + C)' = A'B'C'",
    )

    assert_boolean_identity(
        ["A", "B", "C"],
        lambda A, B, C: not (A and B and C),
        lambda A, B, C: (not A) or (not B) or (not C),
        "(ABC)' = A' + B' + C'",
    )


demonstrate_de_morgan()


# ============================================================================
# SECTION 5: ADVANCED BOOLEAN THEOREMS
# ============================================================================

"""
Consensus theorem:

    AB + A'C + BC = AB + A'C

The term BC is called the consensus term.

The theorem can be understood as follows:
if AB is true, the result is already true;
if A'C is true, the result is already true;
therefore BC cannot independently create a new true output.

Dual form:

    (A + B)(A' + C)(B + C) = (A + B)(A' + C)

Another useful theorem:

    A + A'B = A + B

Dual form:

    A(A' + B) = AB
"""


def demonstrate_advanced_theorems() -> None:
    print("\nAdvanced Boolean theorems:")

    assert_boolean_identity(
        ["A", "B"],
        lambda A, B: A or ((not A) and B),
        lambda A, B: A or B,
        "A + A'B = A + B",
    )

    assert_boolean_identity(
        ["A", "B"],
        lambda A, B: A and ((not A) or B),
        lambda A, B: A and B,
        "A(A' + B) = AB",
    )

    assert_boolean_identity(
        ["A", "B", "C"],
        lambda A, B, C: (A and B) or ((not A) and C) or (B and C),
        lambda A, B, C: (A and B) or ((not A) and C),
        "AB + A'C + BC = AB + A'C",
    )

    assert_boolean_identity(
        ["A", "B", "C"],
        lambda A, B, C: (A or B) and ((not A) or C) and (B or C),
        lambda A, B, C: (A or B) and ((not A) or C),
        "(A+B)(A'+C)(B+C) = (A+B)(A'+C)",
    )


demonstrate_advanced_theorems()


# ============================================================================
# SECTION 6: COMMON SIMPLIFICATION PATTERNS
# ============================================================================

def simplify_pattern_examples() -> None:
    """
    Demonstrate standard algebraic simplification patterns.

    These examples are deliberately evaluated rather than merely stated.
    """
    print("\nCommon simplification patterns:")

    examples = [
        (
            "A + AB",
            lambda A, B: A or (A and B),
            lambda A, B: A,
        ),
        (
            "A(A+B)",
            lambda A, B: A and (A or B),
            lambda A, B: A,
        ),
        (
            "A + A'B",
            lambda A, B: A or ((not A) and B),
            lambda A, B: A or B,
        ),
        (
            "AB + AB'",
            lambda A, B: (A and B) or (A and (not B)),
            lambda A, B: A,
        ),
        (
            "(A+B)(A+B')",
            lambda A, B: (A or B) and (A or (not B)),
            lambda A, B: A,
        ),
        (
            "A + A'BC",
            lambda A, B, C: A or ((not A) and B and C),
            lambda A, B, C: A or (B and C),
        ),
    ]

    for item in examples:
        if len(item) == 3:
            name, original, simplified = item
            variables = ["A", "B", "C"] if "C" in name else ["A", "B"]

            assert_boolean_identity(
                variables,
                original,
                simplified,
                f"{name} simplifies correctly",
            )


simplify_pattern_examples()


# ============================================================================
# SECTION 7: SYMBOLIC BOOLEAN EXPRESSION TREE
# ============================================================================

"""
The previous sections evaluate Boolean expressions numerically.

For actual symbolic simplification, an expression must be represented as
data. The following classes create an abstract syntax tree.

Example:

    (A + B)C'

is represented structurally as:

    AND(
        OR(A, B),
        NOT(C)
    )

This allows a simplifier to inspect operators and operands instead of
evaluating only a final true/false result.
"""


class BoolExpr:
    """Base class for symbolic Boolean expressions."""

    def evaluate(self, values: dict[str, bool]) -> bool:
        raise NotImplementedError

    def variables(self) -> set[str]:
        raise NotImplementedError

    def simplify(self) -> "BoolExpr":
        return self

    def __or__(self, other: "BoolExpr") -> "BoolExpr":
        return Or(self, other)

    def __and__(self, other: "BoolExpr") -> "BoolExpr":
        return And(self, other)

    def __invert__(self) -> "BoolExpr":
        return Not(self)


@dataclass(frozen=True)
class BoolConstant(BoolExpr):
    value: bool

    def evaluate(self, values: dict[str, bool]) -> bool:
        return self.value

    def variables(self) -> set[str]:
        return set()

    def __str__(self) -> str:
        return "1" if self.value else "0"


@dataclass(frozen=True)
class Variable(BoolExpr):
    name: str

    def evaluate(self, values: dict[str, bool]) -> bool:
        if self.name not in values:
            raise KeyError(f"Missing value for variable {self.name!r}")
        return bool(values[self.name])

    def variables(self) -> set[str]:
        return {self.name}

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Not(BoolExpr):
    operand: BoolExpr

    def evaluate(self, values: dict[str, bool]) -> bool:
        return not self.operand.evaluate(values)

    def variables(self) -> set[str]:
        return self.operand.variables()

    def __str__(self) -> str:
        if isinstance(self.operand, Variable):
            return f"{self.operand}'"
        return f"({self.operand})'"


@dataclass(frozen=True)
class And(BoolExpr):
    left: BoolExpr
    right: BoolExpr

    def evaluate(self, values: dict[str, bool]) -> bool:
        return (
            self.left.evaluate(values)
            and self.right.evaluate(values)
        )

    def variables(self) -> set[str]:
        return self.left.variables() | self.right.variables()

    def __str__(self) -> str:
        return f"({self.left}·{self.right})"


@dataclass(frozen=True)
class Or(BoolExpr):
    left: BoolExpr
    right: BoolExpr

    def evaluate(self, values: dict[str, bool]) -> bool:
        return (
            self.left.evaluate(values)
            or self.right.evaluate(values)
        )

    def variables(self) -> set[str]:
        return self.left.variables() | self.right.variables()

    def __str__(self) -> str:
        return f"({self.left}+{self.right})"


ZERO = BoolConstant(False)
ONE = BoolConstant(True)


def V(name: str) -> Variable:
    """Convenient constructor for a symbolic variable."""
    return Variable(name)


def N(expr: BoolExpr) -> BoolExpr:
    """Convenient constructor for symbolic NOT."""
    return Not(expr)


def A(expr1: BoolExpr, expr2: BoolExpr) -> BoolExpr:
    """Convenient constructor for symbolic AND."""
    return And(expr1, expr2)


def O(expr1: BoolExpr, expr2: BoolExpr) -> BoolExpr:
    """Convenient constructor for symbolic OR."""
    return Or(expr1, expr2)


A_var = V("A")
B_var = V("B")
C_var = V("C")
D_var = V("D")

symbolic_expression = (A_var | B_var) & ~C_var

print("\nSymbolic expression tree:")
print("Expression:", symbolic_expression)
print("Variables:", sorted(symbolic_expression.variables()))
print(
    "Evaluation for A=1, B=0, C=0:",
    int(symbolic_expression.evaluate({"A": True, "B": False, "C": False})),
)


# ============================================================================
# SECTION 8: EXPRESSION NORMALIZATION
# ============================================================================

def flatten_operator(
    expr: BoolExpr,
    operator_type: type,
) -> list[BoolExpr]:
    """
    Flatten nested occurrences of the same associative operator.

    Example:
        A + (B + C)
    becomes:
        [A, B, C]
    """
    if isinstance(expr, operator_type):
        return (
            flatten_operator(expr.left, operator_type)
            + flatten_operator(expr.right, operator_type)
        )

    return [expr]


def make_balanced_operator(
    operands: Sequence[BoolExpr],
    operator_type: type,
) -> BoolExpr:
    """Build a binary expression tree from a sequence of operands."""
    if not operands:
        raise ValueError("At least one operand is required.")

    result = operands[0]

    for operand in operands[1:]:
        result = operator_type(result, operand)

    return result


def structural_key(expr: BoolExpr) -> str:
    """
    Return a stable structural representation.

    This is useful when applying idempotent and duplicate-removal rules.
    """
    return str(expr)


def normalize_associative(expr: BoolExpr) -> BoolExpr:
    """
    Recursively flatten and rebuild AND/OR expressions.

    This does not itself change Boolean meaning.
    """
    if isinstance(expr, Variable) or isinstance(expr, BoolConstant):
        return expr

    if isinstance(expr, Not):
        return Not(normalize_associative(expr.operand))

    if isinstance(expr, And):
        operands = [
            normalize_associative(item)
            for item in flatten_operator(expr, And)
        ]
        return make_balanced_operator(operands, And)

    if isinstance(expr, Or):
        operands = [
            normalize_associative(item)
            for item in flatten_operator(expr, Or)
        ]
        return make_balanced_operator(operands, Or)

    raise TypeError(f"Unsupported expression: {type(expr).__name__}")


# ============================================================================
# SECTION 9: SYMBOLIC SIMPLIFICATION ENGINE
# ============================================================================

def contains_complement_pair(
    operands: Sequence[BoolExpr],
) -> bool:
    """Return True if both X and X' occur among operands."""
    keys = {structural_key(item) for item in operands}

    for operand in operands:
        if structural_key(Not(operand)) in keys:
            return True

    return False


def remove_duplicate_operands(
    operands: Sequence[BoolExpr],
) -> list[BoolExpr]:
    """Apply idempotent behavior by removing duplicate terms."""
    unique: dict[str, BoolExpr] = {}

    for operand in operands:
        unique[structural_key(operand)] = operand

    return list(unique.values())


def simplify_not(expr: BoolExpr) -> BoolExpr:
    """
    Simplify a NOT node using:
        0' = 1
        1' = 0
        (A')' = A
    """
    operand = simplify_expression(expr.operand)

    if isinstance(operand, BoolConstant):
        return ONE if not operand.value else ZERO

    if isinstance(operand, Not):
        return operand.operand

    return Not(operand)


def simplify_and(expr: And) -> BoolExpr:
    """
    Apply local AND simplification rules.

    Rules include:
        A·0 = 0
        A·1 = A
        A·A = A
        A·A' = 0
    """
    operands = [
        simplify_expression(item)
        for item in flatten_operator(expr, And)
    ]

    operands = remove_duplicate_operands(operands)

    if any(isinstance(item, BoolConstant) and not item.value for item in operands):
        return ZERO

    operands = [
        item
        for item in operands
        if not (isinstance(item, BoolConstant) and item.value)
    ]

    if not operands:
        return ONE

    if contains_complement_pair(operands):
        return ZERO

    if len(operands) == 1:
        return operands[0]

    return make_balanced_operator(operands, And)


def simplify_or(expr: Or) -> BoolExpr:
    """
    Apply local OR simplification rules.

    Rules include:
        A+1 = 1
        A+0 = A
        A+A = A
        A+A' = 1
    """
    operands = [
        simplify_expression(item)
        for item in flatten_operator(expr, Or)
    ]

    operands = remove_duplicate_operands(operands)

    if any(isinstance(item, BoolConstant) and item.value for item in operands):
        return ONE

    operands = [
        item
        for item in operands
        if not (isinstance(item, BoolConstant) and not item.value)
    ]

    if not operands:
        return ZERO

    if contains_complement_pair(operands):
        return ONE

    if len(operands) == 1:
        return operands[0]

    return make_balanced_operator(operands, Or)


def simplify_absorption(expr: BoolExpr) -> BoolExpr:
    """
    Apply absorption to flattened AND/OR expressions.

    OR absorption:
        A + AB = A

    AND absorption:
        A(A+B) = A

    The implementation identifies direct subset relationships between
    product-like terms where possible.
    """
    if isinstance(expr, Or):
        terms = flatten_operator(expr, Or)

        # Convert each OR term into a set of AND factors.
        factor_sets: list[tuple[BoolExpr, set[str]]] = []

        for term in terms:
            factors = flatten_operator(term, And)
            factor_sets.append(
                (
                    term,
                    {structural_key(factor) for factor in factors},
                )
            )

        kept: list[BoolExpr] = []

        for original, factors in factor_sets:
            absorbed = False

            for _, other_factors in factor_sets:
                if other_factors < factors:
                    absorbed = True
                    break

            if not absorbed:
                kept.append(original)

        if len(kept) != len(terms):
            return make_balanced_operator(kept, Or)

    if isinstance(expr, And):
        terms = flatten_operator(expr, And)

        # Dual absorption:
        # A(A+B) = A.
        kept: list[BoolExpr] = []

        for index, term in enumerate(terms):
            absorbed = False

            if isinstance(term, Or):
                inner_terms = flatten_operator(term, Or)

                for other_index, other in enumerate(terms):
                    if index == other_index:
                        continue

                    if any(
                        structural_key(other) == structural_key(inner)
                        for inner in inner_terms
                    ):
                        absorbed = True
                        break

            if not absorbed:
                kept.append(term)

        if len(kept) != len(terms):
            return make_balanced_operator(kept, And)

    return expr


def simplify_distributive_patterns(expr: BoolExpr) -> BoolExpr:
    """
    Apply selected useful distributive/factoring transformations.

    Important distinction:
    Boolean algebra has two distributive laws:

        A(B+C) = AB+AC
        A+BC = (A+B)(A+C)

    Simplification is not simply "expand everything".
    Factoring can be much more compact than expansion.
    """
    if isinstance(expr, Or):
        terms = flatten_operator(expr, Or)

        # Pattern:
        # AB + AB' = A
        for i, left in enumerate(terms):
            left_factors = flatten_operator(left, And)

            for j, right in enumerate(terms):
                if i >= j:
                    continue

                right_factors = flatten_operator(right, And)

                left_keys = {structural_key(x): x for x in left_factors}
                right_keys = {structural_key(x): x for x in right_factors}

                common_keys = set(left_keys) & set(right_keys)

                for common_key in common_keys:
                    left_remaining = [
                        x for key, x in left_keys.items()
                        if key != common_key
                    ]
                    right_remaining = [
                        x for key, x in right_keys.items()
                        if key != common_key
                    ]

                    if len(left_remaining) == 1 and len(right_remaining) == 1:
                        if (
                            structural_key(Not(left_remaining[0]))
                            == structural_key(right_remaining[0])
                            or
                            structural_key(Not(right_remaining[0]))
                            == structural_key(left_remaining[0])
                        ):
                            common = left_keys[common_key]
                            remaining = [
                                term
                                for k, term in enumerate(terms)
                                if k not in {i, j}
                            ]
                            remaining.append(common)
                            return make_balanced_operator(remaining, Or)

    return expr


def simplify_expression(expr: BoolExpr) -> BoolExpr:
    """
    Perform repeated local symbolic simplification.

    This is a teaching-oriented simplifier, not a complete industrial
    Boolean minimization package. Complete minimization can require
    global optimization algorithms such as Quine-McCluskey or Espresso.
    """
    if isinstance(expr, (Variable, BoolConstant)):
        return expr

    if isinstance(expr, Not):
        return simplify_not(expr)

    if isinstance(expr, And):
        simplified = simplify_and(expr)
        simplified = simplify_absorption(simplified)
        simplified = simplify_distributive_patterns(simplified)

        if str(simplified) != str(expr):
            return simplify_expression(simplified)

        return simplified

    if isinstance(expr, Or):
        simplified = simplify_or(expr)
        simplified = simplify_absorption(simplified)
        simplified = simplify_distributive_patterns(simplified)

        if str(simplified) != str(expr):
            return simplify_expression(simplified)

        return simplified

    raise TypeError(f"Unsupported expression: {type(expr).__name__}")


print("\nSymbolic simplification examples:")

symbolic_examples = [
    ("A + AB", A_var | (A_var & B_var)),
    ("A(A + B)", A_var & (A_var | B_var)),
    ("A + A'", A_var | ~A_var),
    ("AA'", A_var & ~A_var),
    ("A + 0", A_var | ZERO),
    ("A · 1", A_var & ONE),
    ("A + AB + AC", (A_var & B_var) | (A_var & C_var) | A_var),
]

for label, expression in symbolic_examples:
    simplified = simplify_expression(expression)
    print(f"{label:<20} -> {simplified}")


# ============================================================================
# SECTION 10: EQUIVALENCE CHECKING
# ============================================================================

def equivalent(
    left: BoolExpr,
    right: BoolExpr,
) -> bool:
    """
    Determine whether two symbolic Boolean expressions are equivalent.

    Exhaustive truth-table comparison is exact but exponential in the number
    of variables. For n variables, this requires up to 2^n evaluations.
    """
    variables = sorted(left.variables() | right.variables())

    for assignment in all_boolean_inputs(variables):
        if left.evaluate(assignment) != right.evaluate(assignment):
            return False

    return True


def demonstrate_equivalence_checking() -> None:
    print("\nEquivalence checking:")

    left = A_var | (A_var & B_var)
    right = A_var

    print("Expression 1:", left)
    print("Expression 2:", right)
    print("Equivalent:", equivalent(left, right))

    non_equivalent_left = A_var & B_var
    non_equivalent_right = A_var | B_var

    print("Expression 3:", non_equivalent_left)
    print("Expression 4:", non_equivalent_right)
    print(
        "Equivalent:",
        equivalent(non_equivalent_left, non_equivalent_right),
    )


demonstrate_equivalence_checking()


# ============================================================================
# SECTION 11: SOP AND POS TERMINOLOGY
# ============================================================================

"""
Sum of Products (SOP)
---------------------
An OR of AND terms.

Example:
    AB + A'C + BC

Each AND term is a product term.
The entire expression is a sum of products.

Product of Sums (POS)
---------------------
An AND of OR terms.

Example:
    (A+B)(A'+C)(B+C)

Each OR term is a sum term.
The entire expression is a product of sums.

Canonical SOP
-------------
Every product term contains every variable exactly once, either complemented
or uncomplemented.

For variables A, B, C:

    A'BC
    AB'C
    ABC'

are canonical product terms.

Canonical POS
-------------
Every sum term contains every variable exactly once.

For variables A, B, C:

    (A+B+C')
    (A+B'+C)
    (A'+B+C)

are canonical sum terms.
"""


def minterm(
    assignment: dict[str, bool],
    variable_names: Sequence[str],
) -> BoolExpr:
    """
    Construct a canonical minterm.

    A minterm is 1 for exactly one input combination.
    """
    factors: list[BoolExpr] = []

    for variable_name in variable_names:
        variable = Variable(variable_name)
        factors.append(
            variable
            if assignment[variable_name]
            else Not(variable)
        )

    if not factors:
        return ONE

    return make_balanced_operator(factors, And)


def maxterm(
    assignment: dict[str, bool],
    variable_names: Sequence[str],
) -> BoolExpr:
    """
    Construct a canonical maxterm.

    A maxterm is 0 for exactly one input combination.

    To create a maxterm:
        input 0 -> variable appears uncomplemented
        input 1 -> variable appears complemented
    """
    terms: list[BoolExpr] = []

    for variable_name in variable_names:
        variable = Variable(variable_name)
        terms.append(
            variable
            if not assignment[variable_name]
            else Not(variable)
        )

    if not terms:
        return ZERO

    return make_balanced_operator(terms, Or)


# ============================================================================
# SECTION 12: CANONICAL SOP FROM TRUTH TABLE
# ============================================================================

def canonical_sop(
    variable_names: Sequence[str],
    expression: Callable[..., bool],
) -> tuple[BoolExpr, list[int]]:
    """
    Build canonical SOP by collecting every minterm for which the function is 1.

    Minterm numbering follows the binary ordering of variable_names.
    For A,B,C:
        ABC = 111 -> minterm 7
        A'BC = 011 -> minterm 3
    """
    minterms: list[BoolExpr] = []
    indices: list[int] = []

    for index, assignment in enumerate(all_boolean_inputs(variable_names)):
        if expression(**assignment):
            minterms.append(minterm(assignment, variable_names))
            indices.append(index)

    if not minterms:
        return ZERO, indices

    return make_balanced_operator(minterms, Or), indices


def canonical_pos(
    variable_names: Sequence[str],
    expression: Callable[..., bool],
) -> tuple[BoolExpr, list[int]]:
    """
    Build canonical POS by collecting every maxterm for which the function is 0.
    """
    maxterms: list[BoolExpr] = []
    indices: list[int] = []

    for index, assignment in enumerate(all_boolean_inputs(variable_names)):
        if not expression(**assignment):
            maxterms.append(maxterm(assignment, variable_names))
            indices.append(index)

    if not maxterms:
        return ONE, indices

    return make_balanced_operator(maxterms, And), indices


def demonstrate_canonical_forms() -> None:
    print("\nCanonical forms:")

    variables = ["A", "B", "C"]

    def function(A: bool, B: bool, C: bool) -> bool:
        # F = 1 for minterms 1, 2, 5, 7.
        return (
            (not A and not B and C)
            or (not A and B and not C)
            or (A and not B and C)
            or (A and B and C)
        )

    sop, sop_indices = canonical_sop(variables, function)
    pos, pos_indices = canonical_pos(variables, function)

    print("Canonical SOP:")
    print(sop)
    print("Minterm indices:", sop_indices)

    print("\nCanonical POS:")
    print(pos)
    print("Maxterm indices:", pos_indices)

    print("\nStandard notation:")
    print(f"F(A,B,C) = Σm({', '.join(map(str, sop_indices))})")
    print(f"F(A,B,C) = ΠM({', '.join(map(str, pos_indices))})")


demonstrate_canonical_forms()


# ============================================================================
# SECTION 13: DECIMAL INDEXING AND BINARY ASSIGNMENTS
# ============================================================================

def index_to_assignment(
    index: int,
    variable_names: Sequence[str],
) -> dict[str, bool]:
    """
    Convert a decimal minterm/maxterm index into a Boolean assignment.

    Example for A,B,C:
        index 5 = binary 101
        A=1, B=0, C=1
    """
    count = len(variable_names)

    if index < 0 or index >= 2**count:
        raise ValueError(
            f"Index {index} is invalid for {count} variables."
        )

    bits = f"{index:0{count}b}"

    return {
        variable: bit == "1"
        for variable, bit in zip(variable_names, bits)
    }


def assignment_to_index(
    assignment: dict[str, bool],
    variable_names: Sequence[str],
) -> int:
    """Convert a Boolean assignment to its binary index."""
    bits = "".join(
        "1" if assignment[name] else "0"
        for name in variable_names
    )

    return int(bits, 2)


print("\nIndex conversion examples:")

for index in [0, 1, 3, 5, 7]:
    assignment = index_to_assignment(index, ["A", "B", "C"])
    recovered = assignment_to_index(assignment, ["A", "B", "C"])

    print(
        f"index={index:>2} -> {assignment} -> recovered index={recovered}"
    )


# ============================================================================
# SECTION 14: CANONICAL FORM VERIFICATION
# ============================================================================

def expression_from_minterms(
    variable_names: Sequence[str],
    indices: Iterable[int],
) -> BoolExpr:
    """Build SOP from a collection of minterm indices."""
    indices = list(indices)

    if not indices:
        return ZERO

    terms = [
        minterm(
            index_to_assignment(index, variable_names),
            variable_names,
        )
        for index in indices
    ]

    return make_balanced_operator(terms, Or)


def expression_from_maxterms(
    variable_names: Sequence[str],
    indices: Iterable[int],
) -> BoolExpr:
    """Build POS from a collection of maxterm indices."""
    indices = list(indices)

    if not indices:
        return ONE

    terms = [
        maxterm(
            index_to_assignment(index, variable_names),
            variable_names,
        )
        for index in indices
    ]

    return make_balanced_operator(terms, And)


def verify_minterm_expression(
    variable_names: Sequence[str],
    indices: Sequence[int],
) -> None:
    """Verify that each listed minterm is true only for its own index."""
    expression = expression_from_minterms(variable_names, indices)

    for index, assignment in enumerate(
        all_boolean_inputs(variable_names)
    ):
        expected = index in indices
        actual = expression.evaluate(assignment)

        if expected != actual:
            raise AssertionError(
                "Minterm construction failed: "
                f"index={index}, assignment={assignment}"
            )

    print(
        f"[PASS] Canonical SOP verified for minterms {list(indices)}"
    )


verify_minterm_expression(["A", "B", "C"], [1, 2, 5, 7])


# ============================================================================
# SECTION 15: SOP TERM REPRESENTATION FOR MINIMIZATION
# ============================================================================

"""
For minimization algorithms, a product term can be represented as a pattern.

For variables A,B,C:

    101 means A B' C
    1-1 means A C

A dash means the variable has been eliminated from the term.

The Quine-McCluskey method combines terms that differ in exactly one fixed
variable.

Example:

    100
    101

differ only in the last bit, so:

    10-

This corresponds to:

    AB'

because C no longer matters.
"""


@dataclass(frozen=True)
class Implicant:
    pattern: str
    covered_minterms: frozenset[int]
    source_terms: frozenset[str] = frozenset()

    def literals(self) -> int:
        """Number of fixed literals in the implicant."""
        return sum(bit != "-" for bit in self.pattern)

    def can_combine_with(self, other: "Implicant") -> bool:
        """
        Two implicants can combine if they differ in exactly one fixed
        position and do not conflict through existing don't-care positions.
        """
        differences = 0

        for left, right in zip(self.pattern, other.pattern):
            if left == right:
                continue

            if left == "-" or right == "-":
                return False

            differences += 1

        return differences == 1

    def combine(self, other: "Implicant") -> "Implicant":
        """Combine two compatible implicants."""
        if not self.can_combine_with(other):
            raise ValueError("Implicants cannot be combined.")

        new_pattern = "".join(
            "-" if left != right else left
            for left, right in zip(self.pattern, other.pattern)
        )

        return Implicant(
            pattern=new_pattern,
            covered_minterms=self.covered_minterms
            | other.covered_minterms,
            source_terms=self.source_terms
            | other.source_terms,
        )

    def to_expression(
        self,
        variable_names: Sequence[str],
    ) -> BoolExpr:
        """Convert an implicant pattern into a symbolic product term."""
        factors: list[BoolExpr] = []

        for bit, variable_name in zip(self.pattern, variable_names):
            variable = Variable(variable_name)

            if bit == "1":
                factors.append(variable)
            elif bit == "0":
                factors.append(Not(variable))

        if not factors:
            return ONE

        return make_balanced_operator(factors, And)

    def __str__(self) -> str:
        return self.pattern


# ============================================================================
# SECTION 16: QUINE-MCCLUSKEY MINIMIZATION
# ============================================================================

def initial_implicants(
    variable_count: int,
    minterms: Sequence[int],
) -> list[Implicant]:
    """Create one fully specified implicant for each minterm."""
    result = []

    for index in sorted(set(minterms)):
        pattern = f"{index:0{variable_count}b}"
        result.append(
            Implicant(
                pattern=pattern,
                covered_minterms=frozenset({index}),
                source_terms=frozenset({pattern}),
            )
        )

    return result


def combine_implicant_round(
    implicants: Sequence[Implicant],
) -> tuple[list[Implicant], set[str]]:
    """
    Perform one Quine-McCluskey combination round.

    Returns:
        combined implicants
        patterns that were successfully combined
    """
    combined: dict[str, Implicant] = {}
    used: set[str] = set()

    groups: dict[int, list[Implicant]] = {}

    for implicant in implicants:
        ones = implicant.pattern.count("1")
        groups.setdefault(ones, []).append(implicant)

    sorted_group_numbers = sorted(groups)

    for group_number in sorted_group_numbers:
        left_group = groups[group_number]
        right_group = groups.get(group_number + 1, [])

        for left in left_group:
            for right in right_group:
                if left.can_combine_with(right):
                    result = left.combine(right)
                    combined[result.pattern] = result

                    used.add(left.pattern)
                    used.add(right.pattern)

    return list(combined.values()), used


def prime_implicants(
    variable_count: int,
    minterms: Sequence[int],
) -> list[Implicant]:
    """
    Find prime implicants using iterative Quine-McCluskey combination.

    A prime implicant is an implicant that cannot be combined further while
    remaining valid for the required minterm set.
    """
    current = initial_implicants(variable_count, minterms)
    primes: dict[str, Implicant] = {}

    while current:
        next_round, used = combine_implicant_round(current)

        for implicant in current:
            if implicant.pattern not in used:
                primes[implicant.pattern] = implicant

        current = next_round

    return sorted(
        primes.values(),
        key=lambda item: (item.literals(), item.pattern),
    )


def prime_implicant_chart(
    primes: Sequence[Implicant],
    minterms: Sequence[int],
) -> dict[int, list[Implicant]]:
    """Create a prime-implicant chart."""
    chart: dict[int, list[Implicant]] = {}

    for minterm_index in sorted(set(minterms)):
        chart[minterm_index] = [
            prime
            for prime in primes
            if minterm_index in prime.covered_minterms
        ]

    return chart


def essential_prime_implicants(
    primes: Sequence[Implicant],
    minterms: Sequence[int],
) -> list[Implicant]:
    """
    Identify essential prime implicants.

    A prime implicant is essential when it is the only prime implicant that
    covers at least one required minterm.
    """
    chart = prime_implicant_chart(primes, minterms)
    essentials: dict[str, Implicant] = {}

    for covering_primes in chart.values():
        if len(covering_primes) == 1:
            prime = covering_primes[0]
            essentials[prime.pattern] = prime

    return list(essentials.values())


def greedy_cover_prime_implicants(
    primes: Sequence[Implicant],
    minterms: Sequence[int],
) -> list[Implicant]:
    """
    Produce a compact cover using essential implicants followed by a greedy
    selection.

    This is intentionally explicit rather than pretending that a greedy
    strategy is universally optimal.

    Exact minimum-cover selection can itself become a combinatorial problem.
    """
    remaining = set(minterms)
    selected: dict[str, Implicant] = {}

    essentials = essential_prime_implicants(primes, minterms)

    for prime in essentials:
        selected[prime.pattern] = prime
        remaining -= set(prime.covered_minterms)

    while remaining:
        candidates = [
            prime
            for prime in primes
            if prime.pattern not in selected
        ]

        if not candidates:
            raise RuntimeError(
                "The prime-implicant chart could not be completely covered."
            )

        best = max(
            candidates,
            key=lambda prime: (
                len(set(prime.covered_minterms) & remaining),
                -prime.literals(),
            ),
        )

        selected[best.pattern] = best
        remaining -= set(best.covered_minterms)

    return list(selected.values())


def minimize_sop(
    variable_names: Sequence[str],
    minterms: Sequence[int],
    dont_cares: Sequence[int] = (),
) -> tuple[BoolExpr, list[Implicant]]:
    """
    Minimize an SOP function using Quine-McCluskey prime implicants.

    Don't-care terms may participate in grouping but are not required to be
    covered in the final expression.
    """
    variable_count = len(variable_names)
    required = sorted(set(minterms))
    allowed = sorted(set(required) | set(dont_cares))

    if any(index < 0 or index >= 2**variable_count for index in allowed):
        raise ValueError("A minterm or don't-care index is out of range.")

    primes = prime_implicants(variable_count, allowed)

    # A prime is usable in the final expression only if it covers at least
    # one required minterm.
    useful_primes = [
        prime
        for prime in primes
        if set(prime.covered_minterms) & set(required)
    ]

    selected = greedy_cover_prime_implicants(
        useful_primes,
        required,
    )

    expressions = [
        prime.to_expression(variable_names)
        for prime in selected
    ]

    if not expressions:
        return ZERO, selected

    result = make_balanced_operator(expressions, Or)

    return result, selected


def demonstrate_quine_mccluskey() -> None:
    print("\nQuine-McCluskey minimization:")

    variables = ["A", "B", "C", "D"]
    minterms = [0, 1, 2, 5, 6, 7, 8, 9, 10, 14]

    simplified, selected = minimize_sop(
        variables,
        minterms,
    )

    print("Variables:", variables)
    print("Required minterms:", minterms)
    print("Selected implicants:")

    for implicant in selected:
        print(
            f"  pattern={implicant.pattern}, "
            f"literals={implicant.literals()}, "
            f"covers={sorted(implicant.covered_minterms)}"
        )

    print("Reduced SOP:", simplified)

    original = expression_from_minterms(variables, minterms)

    print(
        "Equivalent to original canonical SOP:",
        equivalent(original, simplified),
    )


demonstrate_quine_mccluskey()


# ============================================================================
# SECTION 17: DON'T-CARE CONDITIONS
# ============================================================================

"""
A don't-care condition is an input combination for which the output may be
treated as either 0 or 1 for optimization purposes.

Common sources include:

- unused states in finite-state machines
- impossible input combinations
- BCD codes that are not used
- hardware modes that cannot occur

Example:

    Required 1s: 1, 3, 7
    Don't cares: 5

A minimizer may use minterm 5 as though it were a 1 if that allows a larger
implicant, but the final expression is judged only on required minterms.

This can significantly reduce gate count.
"""


def demonstrate_dont_cares() -> None:
    print("\nDon't-care minimization:")

    variables = ["A", "B", "C"]
    required = [1, 3, 7]
    dont_cares = [5]

    result, selected = minimize_sop(
        variables,
        required,
        dont_cares,
    )

    print("Required 1 minterms:", required)
    print("Don't-care minterms:", dont_cares)
    print("Selected implicants:")

    for implicant in selected:
        print(
            f"  {implicant.pattern} -> "
            f"covers {sorted(implicant.covered_minterms)}"
        )

    print("Reduced expression:", result)

    # Verify only required minterms and all zero cases outside the allowed
    # don't-care set.
    allowed = set(required) | set(dont_cares)

    for index, assignment in enumerate(
        all_boolean_inputs(variables)
    ):
        actual = result.evaluate(assignment)

        if index in required and not actual:
            raise AssertionError(
                f"Required minterm {index} was not covered."
            )

        if index not in allowed and actual:
            raise AssertionError(
                f"Expression incorrectly produces 1 at zero minterm {index}."
            )

    print("[PASS] Don't-care result verified.")


demonstrate_dont_cares()


# ============================================================================
# SECTION 18: BOOLEAN FUNCTION METRICS
# ============================================================================

def expression_cost(expr: BoolExpr) -> dict[str, int]:
    """
    Estimate structural cost.

    These are educational metrics, not physical hardware timing models.

    AND/OR gate counts depend on the chosen gate fan-in assumptions.
    NOT count represents explicit complement operations.
    literal_count approximates the number of variable occurrences.
    """
    metrics = {
        "AND gates": 0,
        "OR gates": 0,
        "NOT gates": 0,
        "literals": 0,
    }

    def visit(node: BoolExpr) -> None:
        if isinstance(node, Variable):
            metrics["literals"] += 1

        elif isinstance(node, BoolConstant):
            pass

        elif isinstance(node, Not):
            metrics["NOT gates"] += 1
            visit(node.operand)

        elif isinstance(node, And):
            metrics["AND gates"] += 1
            visit(node.left)
            visit(node.right)

        elif isinstance(node, Or):
            metrics["OR gates"] += 1
            visit(node.left)
            visit(node.right)

        else:
            raise TypeError(type(node).__name__)

    visit(expr)
    return metrics


def compare_expression_costs() -> None:
    print("\nExpression cost comparison:")

    original = (
        (A_var & B_var)
        | (A_var & ~B_var)
        | (A_var & C_var)
    )

    simplified = A_var

    print("Original:", original)
    print("Original cost:", expression_cost(original))

    print("Simplified:", simplified)
    print("Simplified cost:", expression_cost(simplified))

    print("Equivalent:", equivalent(original, simplified))


compare_expression_costs()


# ============================================================================
# SECTION 19: GATE-LEVEL INTERPRETATION
# ============================================================================

"""
Boolean simplification is closely related to digital circuit optimization.

Examples:

    A + AB = A

A circuit implementing A OR (A AND B) can be reduced to a direct connection
from A.

Similarly:

    AB + AB' = A

means that a circuit containing two AND gates followed by an OR gate can be
reduced to A.

De Morgan's laws are especially important when a design must use a particular
gate family.

For example:

    (AB)' = A' + B'

This explains the functional relationship between NAND and OR-with-inverted
inputs.

Likewise:

    (A+B)' = A'B'

connects NOR with AND gates having inverted inputs.
"""


def nand(a: bool, b: bool) -> bool:
    """NAND = NOT(AND)."""
    return not (a and b)


def nor(a: bool, b: bool) -> bool:
    """NOR = NOT(OR)."""
    return not (a or b)


def xor_using_basic_operations(a: bool, b: bool) -> bool:
    """
    XOR expressed using AND, OR and NOT:

        A XOR B = A'B + AB'
    """
    return ((not a) and b) or (a and (not b))


def xnor_using_basic_operations(a: bool, b: bool) -> bool:
    """
    XNOR expressed as:

        AB + A'B'
    """
    return (a and b) or ((not a) and (not b))


def demonstrate_gate_relationships() -> None:
    print("\nGate relationships:")

    assert_boolean_identity(
        ["A", "B"],
        lambda A, B: nand(A, B),
        lambda A, B: not (A and B),
        "NAND = NOT(AND)",
    )

    assert_boolean_identity(
        ["A", "B"],
        lambda A, B: nor(A, B),
        lambda A, B: not (A or B),
        "NOR = NOT(OR)",
    )

    assert_boolean_identity(
        ["A", "B"],
        xor_using_basic_operations,
        boolean_xor,
        "A'B + AB' = A XOR B",
    )

    assert_boolean_identity(
        ["A", "B"],
        xnor_using_basic_operations,
        boolean_xnor,
        "AB + A'B' = A XNOR B",
    )


demonstrate_gate_relationships()


# ============================================================================
# SECTION 20: EDGE CASES
# ============================================================================

def demonstrate_edge_cases() -> None:
    print("\nEdge cases:")

    constant_zero = ZERO
    constant_one = ONE

    print("0 + A ->", simplify_expression(constant_zero | A_var))
    print("1 + A ->", simplify_expression(constant_one | A_var))
    print("0 · A ->", simplify_expression(constant_zero & A_var))
    print("1 · A ->", simplify_expression(constant_one & A_var))
    print("A + A' ->", simplify_expression(A_var | ~A_var))
    print("A · A' ->", simplify_expression(A_var & ~A_var))
    print("(A')' ->", simplify_expression(~~A_var))

    # A function with no true rows is constant zero.
    empty_sop = expression_from_minterms(["A", "B"], [])
    print("SOP with no minterms ->", empty_sop)

    # A function with every row true is constant one.
    universal_sop = expression_from_minterms(
        ["A", "B"],
        [0, 1, 2, 3],
    )
    print("SOP with all minterms ->", simplify_expression(universal_sop))


demonstrate_edge_cases()


# ============================================================================
# SECTION 21: COMMON MISTAKES
# ============================================================================

"""
Common mistakes:

1. Treating Boolean algebra like ordinary arithmetic.

   Incorrect:
       A + A = 2A

   Correct:
       A + A = A

2. Assuming distributive laws work exactly like familiar algebra.

   Boolean algebra has two distributive laws:
       A(B+C) = AB+AC
       A+BC = (A+B)(A+C)

3. Forgetting that + means OR and multiplication means AND.

4. Applying De Morgan's law incorrectly.

   Incorrect:
       (A+B)' = A' + B'

   Correct:
       (A+B)' = A'B'

5. Confusing minterms and maxterms.

   Minterm:
       exactly one input row produces 1.

   Maxterm:
       exactly one input row produces 0.

6. Confusing canonical and minimal forms.

   Canonical form includes every variable in every term.
   Minimal form attempts to reduce the number of terms/literals/gates.

7. Assuming algebraic simplification always gives the globally minimum circuit.

   Gate cost depends on:
       - gate availability
       - fan-in
       - inversion cost
       - propagation delay
       - area
       - power
       - technology library
"""


def demonstrate_mistake_prevention() -> None:
    print("\nMistake-prevention checks:")

    # The following identities are deliberately verified.
    assert_boolean_identity(
        ["A"],
        lambda A: A or A,
        lambda A: A,
        "Repeated OR does not produce 2A",
    )

    assert_boolean_identity(
        ["A", "B"],
        lambda A, B: not (A or B),
        lambda A, B: (not A) and (not B),
        "Correct De Morgan OR complement",
    )

    assert_boolean_identity(
        ["A", "B"],
        lambda A, B: not (A and B),
        lambda A, B: (not A) or (not B),
        "Correct De Morgan AND complement",
    )


demonstrate_mistake_prevention()


# ============================================================================
# SECTION 22: PERFORMANCE CONSIDERATIONS
# ============================================================================

"""
Important complexity observations:

Truth-table enumeration
------------------------
For n variables:
    number of rows = 2^n

Therefore:
    n=3   -> 8 rows
    n=10  -> 1,024 rows
    n=20  -> 1,048,576 rows
    n=30  -> 1,073,741,824 rows

Exhaustive equivalence checking becomes expensive as the number of variables
increases.

Quine-McCluskey
---------------
Quine-McCluskey is systematic and exact for small Boolean functions, but its
intermediate number of implicants can grow rapidly.

Practical hardware synthesis
----------------------------
For larger designs, industrial logic minimization commonly uses more
specialized optimization methods rather than constructing enormous truth
tables.

Therefore, "simpler expression" and "faster circuit" are not automatically
identical goals.
"""


def complexity_table(max_variables: int = 10) -> None:
    print("\nTruth-table growth:")

    for n in range(max_variables + 1):
        print(f"{n:>2} variables -> {2**n:>6} truth-table rows")


complexity_table(8)


# ============================================================================
# SECTION 23: BOOLEAN EXPRESSION EVALUATION FROM MINTERMS
# ============================================================================

def evaluate_minterm_function(
    variable_names: Sequence[str],
    minterms: Sequence[int],
    assignment: dict[str, bool],
) -> bool:
    """
    Evaluate a Boolean function defined by its minterm list.

    This avoids constructing a symbolic expression first.
    """
    index = assignment_to_index(assignment, variable_names)
    return index in set(minterms)


def verify_minterm_evaluation() -> None:
    print("\nMinterm-function evaluation:")

    variables = ["A", "B", "C"]
    selected_minterms = [1, 2, 5, 7]

    for assignment in all_boolean_inputs(variables):
        result = evaluate_minterm_function(
            variables,
            selected_minterms,
            assignment,
        )

        index = assignment_to_index(assignment, variables)

        print(
            f"index={index} assignment={assignment} "
            f"F={int(result)}"
        )


verify_minterm_evaluation()


# ============================================================================
# SECTION 24: SOP/POS DUALITY
# ============================================================================

"""
Boolean duality is a powerful conceptual principle.

If a valid Boolean identity is transformed by simultaneously swapping:

    +  <->  ·
    0  <->  1

the resulting dual identity is also valid.

Examples:

Identity:
    A + 0 = A

Dual:
    A · 1 = A

Identity:
    A + 1 = 1

Dual:
    A · 0 = 0

Identity:
    A + AB = A

Dual:
    A(A+B) = A

Identity:
    A(B+C) = AB+AC

Dual:
    A+BC = (A+B)(A+C)
"""


def demonstrate_duality() -> None:
    print("\nBoolean duality:")

    assert_boolean_identity(
        ["A"],
        lambda A: A or False,
        lambda A: A,
        "Identity law",
    )

    assert_boolean_identity(
        ["A"],
        lambda A: A and True,
        lambda A: A,
        "Dual identity law",
    )

    assert_boolean_identity(
        ["A", "B"],
        lambda A, B: A or (A and B),
        lambda A, B: A,
        "Absorption",
    )

    assert_boolean_identity(
        ["A", "B"],
        lambda A, B: A and (A or B),
        lambda A, B: A,
        "Dual absorption",
    )


demonstrate_duality()


# ============================================================================
# SECTION 25: PRACTICAL EXAMPLE - MAJORITY FUNCTION
# ============================================================================

"""
A three-input majority function outputs 1 when at least two inputs are 1.

Its canonical SOP is:

    F = A'BC + AB'C + ABC' + ABC

This simplifies to:

    F = AB + AC + BC

The simplified form is a classic example of Boolean minimization.
"""


def majority_canonical(A: bool, B: bool, C: bool) -> bool:
    return (
        ((not A) and B and C)
        or (A and (not B) and C)
        or (A and B and (not C))
        or (A and B and C)
    )


def majority_minimal(A: bool, B: bool, C: bool) -> bool:
    return (A and B) or (A and C) or (B and C)


def demonstrate_majority_function() -> None:
    print("\nThree-input majority function:")

    assert_boolean_identity(
        ["A", "B", "C"],
        majority_canonical,
        majority_minimal,
        "Canonical majority SOP = AB + AC + BC",
    )

    canonical_expression, indices = canonical_sop(
        ["A", "B", "C"],
        majority_canonical,
    )

    minimal_expression = (
        (A_var & B_var)
        | (A_var & C_var)
        | (B_var & C_var)
    )

    print("Canonical SOP:", canonical_expression)
    print("Minterms:", indices)
    print("Minimal form:", minimal_expression)
    print(
        "Equivalent:",
        equivalent(canonical_expression, minimal_expression),
    )


demonstrate_majority_function()


# ============================================================================
# SECTION 26: PRACTICAL EXAMPLE - HALF ADDER
# ============================================================================

"""
A half adder adds two one-bit binary values.

Inputs:
    A, B

Outputs:
    Sum   = A XOR B
    Carry = AB

XOR can be expanded as:

    A'B + AB'

The simplified circuit therefore uses:
    Sum   = A'B + AB'
    Carry = AB
"""


def half_adder(A: bool, B: bool) -> tuple[bool, bool]:
    sum_bit = boolean_xor(A, B)
    carry = A and B
    return sum_bit, carry


def demonstrate_half_adder() -> None:
    print("\nHalf-adder truth table:")
    print("A B | Sum Carry")
    print("----------------")

    for A, B in product([False, True], repeat=2):
        sum_bit, carry = half_adder(A, B)

        print(
            f"{int(A)} {int(B)} | "
            f" {int(sum_bit)}    {int(carry)}"
        )


demonstrate_half_adder()


# ============================================================================
# SECTION 27: PRACTICAL EXAMPLE - FULL ADDER
# ============================================================================

"""
A full adder has:

    Inputs:
        A
        B
        Cin

    Outputs:
        Sum
        Cout

A common implementation is:

    Sum = A XOR B XOR Cin

    Cout = AB + ACin + BCin

The carry equation is itself a majority function.
"""


def full_adder(
    A: bool,
    B: bool,
    carry_in: bool,
) -> tuple[bool, bool]:
    sum_bit = A ^ B ^ carry_in
    carry_out = (
        (A and B)
        or (A and carry_in)
        or (B and carry_in)
    )

    return sum_bit, carry_out


def demonstrate_full_adder() -> None:
    print("\nFull-adder truth table:")
    print("A B Cin | Sum Cout")
    print("-------------------")

    for A, B, carry_in in product([False, True], repeat=3):
        sum_bit, carry_out = full_adder(A, B, carry_in)

        print(
            f"{int(A)} {int(B)}  {int(carry_in)}  | "
            f" {int(sum_bit)}    {int(carry_out)}"
        )


demonstrate_full_adder()


# ============================================================================
# SECTION 28: STATIC VALIDATION OF A SIMPLIFICATION
# ============================================================================

def validate_simplification(
    original: BoolExpr,
    simplified: BoolExpr,
) -> dict[str, object]:
    """
    Return a detailed equivalence report.

    This is useful when an algebraic transformation is performed manually.
    """
    variables = sorted(
        original.variables() | simplified.variables()
    )

    mismatches = []

    for assignment in all_boolean_inputs(variables):
        original_value = original.evaluate(assignment)
        simplified_value = simplified.evaluate(assignment)

        if original_value != simplified_value:
            mismatches.append(
                {
                    "assignment": assignment,
                    "original": original_value,
                    "simplified": simplified_value,
                }
            )

    return {
        "equivalent": not mismatches,
        "variables": variables,
        "tested_rows": 2 ** len(variables),
        "mismatches": mismatches,
    }


def demonstrate_validation_report() -> None:
    print("\nSimplification validation report:")

    original = (
        (A_var & B_var)
        | (A_var & ~B_var)
    )

    simplified = A_var

    report = validate_simplification(
        original,
        simplified,
    )

    print("Original:", original)
    print("Simplified:", simplified)
    print("Variables:", report["variables"])
    print("Rows tested:", report["tested_rows"])
    print("Equivalent:", report["equivalent"])
    print("Mismatches:", report["mismatches"])


demonstrate_validation_report()


# ============================================================================
# SECTION 29: TEST SUITE FOR CORE BOOLEAN IDENTITIES
# ============================================================================

def run_boolean_identity_test_suite() -> None:
    """
    Execute a compact regression suite.

    A simplification engine should be tested against mathematical identities,
    because a syntactically smaller expression is useful only if its Boolean
    meaning is preserved.
    """
    tests = [
        (
            ["A"],
            lambda A: A or False,
            lambda A: A,
            "Identity OR",
        ),
        (
            ["A"],
            lambda A: A and True,
            lambda A: A,
            "Identity AND",
        ),
        (
            ["A"],
            lambda A: A or True,
            lambda A: True,
            "Domination OR",
        ),
        (
            ["A"],
            lambda A: A and False,
            lambda A: False,
            "Domination AND",
        ),
        (
            ["A"],
            lambda A: A or A,
            lambda A: A,
            "Idempotent OR",
        ),
        (
            ["A"],
            lambda A: A and A,
            lambda A: A,
            "Idempotent AND",
        ),
        (
            ["A"],
            lambda A: A or not A,
            lambda A: True,
            "Complement OR",
        ),
        (
            ["A"],
            lambda A: A and not A,
            lambda A: False,
            "Complement AND",
        ),
        (
            ["A"],
            lambda A: not not A,
            lambda A: A,
            "Involution",
        ),
        (
            ["A", "B"],
            lambda A, B: not (A or B),
            lambda A, B: not A and not B,
            "De Morgan OR",
        ),
        (
            ["A", "B"],
            lambda A, B: not (A and B),
            lambda A, B: not A or not B,
            "De Morgan AND",
        ),
        (
            ["A", "B"],
            lambda A, B: A or A and B,
            lambda A, B: A,
            "Absorption OR",
        ),
        (
            ["A", "B"],
            lambda A, B: A and (A or B),
            lambda A, B: A,
            "Absorption AND",
        ),
        (
            ["A", "B", "C"],
            lambda A, B, C: A and (B or C),
            lambda A, B, C: A and B or A and C,
            "Distributive AND over OR",
        ),
        (
            ["A", "B", "C"],
            lambda A, B, C: A or (B and C),
            lambda A, B, C: (A or B) and (A or C),
            "Distributive OR over AND",
        ),
    ]

    print("\nRunning Boolean identity test suite:")

    passed = 0

    for variables, left, right, name in tests:
        assert_boolean_identity(
            variables,
            left,
            right,
            name,
        )
        passed += 1

    print(f"Passed {passed}/{len(tests)} identity tests.")


run_boolean_identity_test_suite()


# ============================================================================
# SECTION 30: ADVANCED DISCUSSION THROUGH EXECUTABLE EXAMPLES
# ============================================================================

def demonstrate_related_forms() -> None:
    """
    Show how one Boolean function can have multiple valid representations.

    A Boolean function may have:
        - a truth table
        - canonical SOP
        - canonical POS
        - reduced SOP
        - reduced POS
        - a gate-level implementation

    These representations differ syntactically but may describe exactly the
    same function.
    """
    print("\nRelated representations of one Boolean function:")

    variables = ["A", "B", "C"]

    def function(A: bool, B: bool, C: bool) -> bool:
        return (
            (A and B)
            or (A and C)
            or (B and C)
        )

    sop, minterm_indices = canonical_sop(
        variables,
        function,
    )

    pos, maxterm_indices = canonical_pos(
        variables,
        function,
    )

    reduced = (
        (A_var & B_var)
        | (A_var & C_var)
        | (B_var & C_var)
    )

    print("Minterms:", minterm_indices)
    print("Canonical SOP:", sop)
    print("Maxterms:", maxterm_indices)
    print("Canonical POS:", pos)
    print("Reduced SOP:", reduced)

    print(
        "Canonical SOP equivalent to reduced SOP:",
        equivalent(sop, reduced),
    )

    print(
        "Canonical POS equivalent to reduced SOP:",
        equivalent(pos, reduced),
    )


demonstrate_related_forms()


# ============================================================================
# SECTION 31: INPUT VALIDATION AND ERROR HANDLING
# ============================================================================

def validate_variable_names(variable_names: Sequence[str]) -> None:
    """Validate variable names used by canonical-form utilities."""
    if not variable_names:
        raise ValueError("At least one variable is required.")

    if len(set(variable_names)) != len(variable_names):
        raise ValueError("Variable names must be unique.")

    for name in variable_names:
        if not name:
            raise ValueError("Variable names cannot be empty.")

        if not name.replace("_", "").isalnum():
            raise ValueError(
                f"Invalid variable name: {name!r}"
            )


def safe_index_to_assignment(
    index: int,
    variable_names: Sequence[str],
) -> Optional[dict[str, bool]]:
    """
    Return None instead of raising for invalid user input.

    Production software often separates strict internal functions from
    user-facing validation wrappers.
    """
    try:
        validate_variable_names(variable_names)
        return index_to_assignment(index, variable_names)
    except (TypeError, ValueError):
        return None


def demonstrate_error_handling() -> None:
    print("\nValidation and error handling:")

    valid = safe_index_to_assignment(
        5,
        ["A", "B", "C"],
    )

    invalid = safe_index_to_assignment(
        8,
        ["A", "B", "C"],
    )

    print("Valid conversion:", valid)
    print("Invalid conversion:", invalid)


demonstrate_error_handling()


# ============================================================================
# SECTION 32: IMPORTANT DISTINCTIONS
# ============================================================================

"""
Boolean simplification involves several concepts that should not be confused.

Boolean identity
----------------
An equality that holds for every possible assignment.

Example:
    A + 0 = A

Boolean expression
------------------
A syntactic representation of a Boolean function.

Boolean function
----------------
The mapping from input combinations to output values.

Truth table
-----------
An exhaustive listing of that mapping.

Canonical form
--------------
A standardized representation in which every term contains every variable.

Minimal/reduced form
--------------------
A representation with reduced logical complexity according to a chosen cost
criterion.

Minterm
-------
A product term that evaluates to 1 on exactly one input row.

Maxterm
-------
A sum term that evaluates to 0 on exactly one input row.

Prime implicant
---------------
An implicant that cannot be expanded further without covering an invalid
0-input.

Essential prime implicant
-------------------------
A prime implicant that uniquely covers at least one required minterm.

Don't-care
----------
An input condition whose output does not constrain the implementation.

These distinctions matter because canonical form is not necessarily minimal.
"""


# ============================================================================
# SECTION 33: FINAL INTEGRATED DEMONSTRATION
# ============================================================================

def integrated_demo() -> None:
    """
    Integrate the major techniques into one complete example.

    Function:
        F(A,B,C,D) = Σm(0,1,2,5,6,7,8,9,10,14)

    The workflow is:
        1. define the function by minterms
        2. construct canonical SOP
        3. minimize it
        4. inspect implicants
        5. verify equivalence
        6. estimate structural cost
    """
    print("\n" + "=" * 80)
    print("INTEGRATED BOOLEAN SIMPLIFICATION WORKFLOW")
    print("=" * 80)

    variables = ["A", "B", "C", "D"]
    minterms = [0, 1, 2, 5, 6, 7, 8, 9, 10, 14]

    original = expression_from_minterms(
        variables,
        minterms,
    )

    minimized, implicants = minimize_sop(
        variables,
        minterms,
    )

    print("\nVariables:")
    print(variables)

    print("\nRequired minterms:")
    print(minterms)

    print("\nCanonical SOP:")
    print(original)

    print("\nSelected prime implicants:")

    for implicant in implicants:
        print(
            f"  {implicant.pattern} | "
            f"literals={implicant.literals()} | "
            f"covered={sorted(implicant.covered_minterms)}"
        )

    print("\nReduced SOP:")
    print(minimized)

    print("\nEquivalence:")
    print(equivalent(original, minimized))

    print("\nOriginal structural cost:")
    print(expression_cost(original))

    print("\nReduced structural cost:")
    print(expression_cost(minimized))

    print("\nTruth-table verification:")

    for index, assignment in enumerate(
        all_boolean_inputs(variables)
    ):
        original_value = original.evaluate(assignment)
        reduced_value = minimized.evaluate(assignment)

        status = "PASS" if original_value == reduced_value else "FAIL"

        print(
            f"{status}: index={index:2}, "
            f"assignment={assignment}, "
            f"original={int(original_value)}, "
            f"reduced={int(reduced_value)}"
        )


integrated_demo()


# ============================================================================
# SECTION 34: STUDY CHECKLIST
# ============================================================================

"""
A learner who understands this script should be able to explain and apply:

Fundamentals
------------
[ ] Boolean 0 and 1
[ ] AND, OR, NOT
[ ] XOR and XNOR
[ ] Truth tables
[ ] Boolean expressions
[ ] Boolean functions

Identities
----------
[ ] Identity
[ ] Domination
[ ] Idempotent
[ ] Complement
[ ] Involution
[ ] Commutative
[ ] Associative
[ ] Distributive
[ ] Absorption
[ ] Consensus
[ ] Duality

De Morgan
---------
[ ] Complement of OR
[ ] Complement of AND
[ ] Multi-variable complements
[ ] Gate-level interpretation

Canonical forms
---------------
[ ] Minterm
[ ] Maxterm
[ ] Canonical SOP
[ ] Canonical POS
[ ] Σm notation
[ ] ΠM notation
[ ] Binary index conversion

Minimization
------------
[ ] Prime implicants
[ ] Essential prime implicants
[ ] Prime implicant chart
[ ] Quine-McCluskey
[ ] Don't-care conditions

Verification
------------
[ ] Truth-table equivalence
[ ] Exhaustive validation
[ ] Structural simplification
[ ] Regression testing

Applications
------------
[ ] Logic gates
[ ] NAND/NOR transformations
[ ] XOR
[ ] Majority logic
[ ] Half adder
[ ] Full adder
[ ] Digital circuit optimization

Engineering considerations
---------------------------
[ ] Literal count
[ ] Gate count
[ ] Fan-in
[ ] Delay
[ ] Area
[ ] Power
[ ] Scalability
[ ] Exact versus heuristic minimization
"""


print("\n" + "=" * 80)
print("BOOLEAN SIMPLIFICATION STUDY SCRIPT COMPLETED")
print("=" * 80)
print(
    "The examples above demonstrate Boolean identities, De Morgan's laws, "
    "symbolic simplification, canonical forms, minimization, verification, "
    "and digital-logic applications."
)
