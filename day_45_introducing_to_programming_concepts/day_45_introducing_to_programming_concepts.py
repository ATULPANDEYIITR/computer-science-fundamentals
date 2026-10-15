#!/usr/bin/env python3
"""
Introduction to Programming Concepts
====================================

A self-contained executable study of programs, syntax, semantics, variables,
data types, expressions, control flow, functions, compilation concepts,
runtime errors, validation, testing, and basic performance considerations.

Run with:
    python programming_concepts.py

Requires Python 3.10 or later. Uses only the Python standard library.
"""

from __future__ import annotations

import ast
import math
import operator
import platform
import sys
import unittest
from dataclasses import dataclass
from enum import Enum
from typing import Callable, TypeAlias


Number: TypeAlias = int | float


def display_heading(title: str) -> None:
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")


# A program is a collection of instructions whose execution produces behavior.
def calculate_rectangle_area(width: float, height: float) -> float:
    """Calculate area after rejecting invalid dimensions."""
    if not math.isfinite(width) or not math.isfinite(height):
        raise ValueError("Dimensions must be finite numbers.")
    if width < 0 or height < 0:
        raise ValueError("Dimensions cannot be negative.")
    return width * height


# Syntax determines which arrangements of tokens form valid Python statements.
# Semantics determines what valid statements mean when they execute.
def demonstrate_syntax_and_semantics() -> None:
    valid_source = "total = 12 + 8\nprint(total)"
    print("Valid source code:")
    print(valid_source)

    tree = ast.parse(valid_source)
    print("Parsed syntax tree:", ast.dump(tree, include_attributes=False))

    namespace: dict[str, object] = {}
    exec(compile(valid_source, "<demonstration>", "exec"), namespace)
    print("Meaning of the assignment: total =", namespace["total"])

    invalid_source = "total = 12 +"
    try:
        ast.parse(invalid_source)
    except SyntaxError as error:
        print(
            "Syntax error detected:",
            f"line {error.lineno}, offset {error.offset}: {error.msg}",
        )

    valid_but_failing_source = "result = 10 / 0"
    try:
        exec(compile(valid_but_failing_source, "<example>", "exec"), {})
    except ZeroDivisionError as error:
        print("Runtime error detected:", type(error).__name__)


# Variables are names bound to objects. Type annotations document expectations,
# but ordinary Python annotations do not enforce types at runtime.
def demonstrate_variables_and_types() -> None:
    employee_name: str = "Mira Shah"
    employee_id: int = 2048
    hourly_rate: float = 725.50
    is_active: bool = True
    assigned_projects: list[str] = ["API migration", "Test automation"]
    skill_levels: dict[str, int] = {"Python": 4, "SQL": 3}
    completed_languages: set[str] = {"Python", "JavaScript", "Python"}
    manager: str | None = None

    print("Employee:", employee_name)
    print("Identifier:", employee_id)
    print("Hourly rate:", hourly_rate)
    print("Active:", is_active)
    print("Projects:", assigned_projects)
    print("Skills:", skill_levels)
    print("Unique languages:", completed_languages)
    print("Manager:", manager)

    values = [
        employee_name,
        employee_id,
        hourly_rate,
        is_active,
        assigned_projects,
        skill_levels,
        completed_languages,
        manager,
    ]

    for value in values:
        print(f"{value!r} -> {type(value).__name__}")

    # bool is a subclass of int in Python, so exact-type checks matter
    # when an API must distinguish True from the integer 1.
    print("isinstance(True, int):", isinstance(True, int))
    print("type(True) is int:", type(True) is int)


def demonstrate_expressions_and_control_flow() -> None:
    prices = [1250.00, 799.50, 450.00]
    subtotal = sum(prices)
    discount_rate = 0.10 if subtotal >= 2000 else 0.0
    discount = subtotal * discount_rate
    tax = (subtotal - discount) * 0.18
    total = subtotal - discount + tax

    print(f"Subtotal: {subtotal:.2f}")
    print(f"Discount: {discount:.2f}")
    print(f"Tax: {tax:.2f}")
    print(f"Total: {total:.2f}")

    for price in prices:
        if price >= 1000:
            category = "premium"
        elif price >= 500:
            category = "standard"
        else:
            category = "economy"
        print(f"Price {price:.2f}: {category}")

    attempt = 0
    maximum_attempts = 3
    while attempt < maximum_attempts:
        attempt += 1
        print(f"Processing attempt {attempt}")


# Decimal arithmetic is often preferable for financial values. This example
# uses integer paise to avoid binary floating-point rounding errors.
def calculate_invoice_paise(
    unit_price_paise: int,
    quantity: int,
    tax_basis_points: int,
) -> dict[str, int]:
    if type(unit_price_paise) is not int or unit_price_paise < 0:
        raise ValueError("Unit price must be a non-negative integer in paise.")
    if type(quantity) is not int or quantity < 0:
        raise ValueError("Quantity must be a non-negative integer.")
    if type(tax_basis_points) is not int or not 0 <= tax_basis_points <= 10000:
        raise ValueError("Tax rate must be between 0 and 10000 basis points.")

    subtotal = unit_price_paise * quantity
    # Integer arithmetic implements half-up rounding for a non-negative amount.
    tax = (subtotal * tax_basis_points + 5000) // 10000
    return {"subtotal_paise": subtotal, "tax_paise": tax, "total_paise": subtotal + tax}


# Functions isolate behavior, provide reusable interfaces, and reduce duplication.
def summarize_scores(scores: list[Number]) -> dict[str, float]:
    if not scores:
        raise ValueError("At least one score is required.")

    normalized: list[float] = []
    for score in scores:
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise TypeError("Every score must be an integer or float.")
        numeric_score = float(score)
        if not math.isfinite(numeric_score):
            raise ValueError("Scores must be finite.")
        if not 0 <= numeric_score <= 100:
            raise ValueError("Scores must be between 0 and 100.")
        normalized.append(numeric_score)

    return {
        "count": float(len(normalized)),
        "minimum": min(normalized),
        "maximum": max(normalized),
        "mean": sum(normalized) / len(normalized),
    }


@dataclass(frozen=True)
class CourseResult:
    student: str
    score: float

    def __post_init__(self) -> None:
        if not self.student.strip():
            raise ValueError("Student name cannot be empty.")
        if isinstance(self.score, bool) or not isinstance(self.score, (int, float)):
            raise TypeError("Score must be numeric.")
        if not math.isfinite(float(self.score)) or not 0 <= self.score <= 100:
            raise ValueError("Score must be finite and between 0 and 100.")

    @property
    def passed(self) -> bool:
        return self.score >= 40


def demonstrate_objects_and_data_processing() -> None:
    results = [
        CourseResult("Asha", 86),
        CourseResult("Kabir", 73.5),
        CourseResult("Leena", 39),
        CourseResult("Dev", 91),
    ]

    passing_students = [result for result in results if result.passed]
    ordered_results = sorted(results, key=lambda result: result.score, reverse=True)

    print("Passing students:", [result.student for result in passing_students])
    print(
        "Score ranking:",
        [(result.student, result.score) for result in ordered_results],
    )
    print("Statistics:", summarize_scores([result.score for result in results]))


# A deliberately small expression interpreter demonstrates the distinction
# between parsing source code and safely evaluating supported semantics.
# It accepts numeric literals and selected arithmetic operators only.
class ArithmeticExpressionError(ValueError):
    """Raised when an expression is invalid or uses unsupported syntax."""


BINARY_OPERATORS: dict[type[ast.operator], Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}

UNARY_OPERATORS: dict[type[ast.unaryop], Callable[[float], float]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def evaluate_arithmetic(source: str) -> float:
    if not source.strip():
        raise ArithmeticExpressionError("Expression cannot be empty.")
    if len(source) > 200:
        raise ArithmeticExpressionError("Expression exceeds 200 characters.")

    try:
        tree = ast.parse(source, mode="eval")
    except SyntaxError as error:
        raise ArithmeticExpressionError("Invalid expression syntax.") from error

    def visit(node: ast.AST, depth: int = 0) -> float:
        if depth > 30:
            raise ArithmeticExpressionError("Expression nesting is too deep.")

        if isinstance(node, ast.Expression):
            return visit(node.body, depth + 1)

        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(
                node.value, (int, float)
            ):
                raise ArithmeticExpressionError("Only numeric literals are allowed.")
            value = float(node.value)
            if not math.isfinite(value) or abs(value) > 1e12:
                raise ArithmeticExpressionError("Numeric literal is out of range.")
            return value

        if isinstance(node, ast.BinOp):
            function = BINARY_OPERATORS.get(type(node.op))
            if function is None:
                raise ArithmeticExpressionError("Unsupported binary operator.")

            left = visit(node.left, depth + 1)
            right = visit(node.right, depth + 1)

            if isinstance(node.op, ast.Pow) and abs(right) > 100:
                raise ArithmeticExpressionError("Exponent magnitude exceeds 100.")

            try:
                result = function(left, right)
            except (ArithmeticError, OverflowError, ValueError) as error:
                raise ArithmeticExpressionError(
                    f"Arithmetic operation failed: {error}"
                ) from error

            if not math.isfinite(result) or abs(result) > 1e100:
                raise ArithmeticExpressionError("Result is out of range.")
            return result

        if isinstance(node, ast.UnaryOp):
            function = UNARY_OPERATORS.get(type(node.op))
            if function is None:
                raise ArithmeticExpressionError("Unsupported unary operator.")
            return function(visit(node.operand, depth + 1))

        raise ArithmeticExpressionError(
            f"Unsupported expression element: {type(node).__name__}"
        )

    return visit(tree)


def demonstrate_expression_interpreter() -> None:
    examples = [
        "12 + 8 * 3",
        "(12 + 8) * 3",
        "2 ** 10",
        "-15 / 3",
    ]

    for source in examples:
        print(f"{source} = {evaluate_arithmetic(source)}")

    rejected = [
        "10 / 0",
        "import os",
        "__import__('os').system('echo unsafe')",
        "2 ** 101",
        "True + 1",
    ]

    for source in rejected:
        try:
            evaluate_arithmetic(source)
        except ArithmeticExpressionError as error:
            print(f"Rejected {source!r}: {error}")


# Compilation converts source into a representation that a runtime can execute.
# Python's compile() creates a code object; this is not native machine-code
# compilation in the same sense as a typical C++ compiler.
def demonstrate_compilation_stages() -> None:
    source = """
def calculate_total(quantity, unit_price):
    if quantity < 0 or unit_price < 0:
        raise ValueError("Inputs must be non-negative")
    return quantity * unit_price

total = calculate_total(4, 125)
"""

    parsed_tree = ast.parse(source)
    code_object = compile(parsed_tree, "<invoice_example>", "exec")

    namespace: dict[str, object] = {}
    exec(code_object, namespace)

    print("AST root:", type(parsed_tree).__name__)
    print("Compiled representation:", type(code_object).__name__)
    print("Execution result:", namespace["total"])
    print("Python version:", platform.python_version())
    print("Implementation:", platform.python_implementation())

    # Python bytecode is an implementation detail and may vary by version.
    function = namespace["calculate_total"]
    print("Function bytecode instructions:")
    import dis
    dis.dis(function)


class ProgrammingConceptTests(unittest.TestCase):
    def test_rectangle_area(self) -> None:
        self.assertEqual(calculate_rectangle_area(4, 5), 20)
        with self.assertRaises(ValueError):
            calculate_rectangle_area(-1, 5)

    def test_invoice_uses_integer_money(self) -> None:
        self.assertEqual(
            calculate_invoice_paise(10000, 3, 1800),
            {"subtotal_paise": 30000, "tax_paise": 5400, "total_paise": 35400},
        )

    def test_invoice_rejects_boolean_quantity(self) -> None:
        with self.assertRaises(ValueError):
            calculate_invoice_paise(100, True, 1800)

    def test_score_validation(self) -> None:
        self.assertEqual(summarize_scores([50, 70])["mean"], 60.0)
        with self.assertRaises(ValueError):
            summarize_scores([])
        with self.assertRaises(ValueError):
            summarize_scores([101])
        with self.assertRaises(TypeError):
            summarize_scores([True])

    def test_course_result(self) -> None:
        self.assertTrue(CourseResult("Asha", 40).passed)
        self.assertFalse(CourseResult("Leena", 39.9).passed)
        with self.assertRaises(ValueError):
            CourseResult("Dev", float("nan"))

    def test_expression_evaluation(self) -> None:
        self.assertEqual(evaluate_arithmetic("2 + 3 * 4"), 14)
        self.assertEqual(evaluate_arithmetic("(2 + 3) * 4"), 20)
        with self.assertRaises(ArithmeticExpressionError):
            evaluate_arithmetic("1 / 0")
        with self.assertRaises(ArithmeticExpressionError):
            evaluate_arithmetic("open('file.txt')")

    def test_boolean_is_not_a_number_literal(self) -> None:
        with self.assertRaises(ArithmeticExpressionError):
            evaluate_arithmetic("True + 1")


def run_tests() -> None:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        ProgrammingConceptTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)


def main() -> None:
    display_heading("Programs, Syntax, and Semantics")
    demonstrate_syntax_and_semantics()

    display_heading("Variables and Data Types")
    demonstrate_variables_and_types()

    display_heading("Expressions and Control Flow")
    demonstrate_expressions_and_control_flow()

    display_heading("Functions, Validation, and Numeric Representation")
    print(calculate_invoice_paise(12550, 4, 1800))
    demonstrate_objects_and_data_processing()

    display_heading("Parsing and Safe Expression Evaluation")
    demonstrate_expression_interpreter()

    display_heading("Compilation and Execution")
    demonstrate_compilation_stages()

    display_heading("Executable Tests")
    run_tests()


if __name__ == "__main__":
    main()
