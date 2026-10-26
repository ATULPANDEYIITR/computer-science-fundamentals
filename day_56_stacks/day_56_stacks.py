from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
import operator
from typing import Callable, Generic, Iterable, TypeVar


T = TypeVar("T")


class StackError(Exception):
    """Base exception for stack-related failures."""


class StackUnderflow(StackError):
    """Raised when a pop or peek is attempted on an empty stack."""


class InvalidExpression(StackError):
    """Raised when an expression cannot be parsed or evaluated."""


class Stack(Generic[T]):
    """Array-backed LIFO stack with explicit capacity validation."""

    def __init__(self, capacity: int | None = None) -> None:
        if capacity is not None and capacity <= 0:
            raise ValueError("capacity must be positive")
        self._items: list[T] = []
        self._capacity = capacity

    def push(self, item: T) -> None:
        if self._capacity is not None and len(self._items) >= self._capacity:
            raise StackError("stack overflow: capacity reached")
        self._items.append(item)

    def pop(self) -> T:
        if not self._items:
            raise StackUnderflow("cannot pop from an empty stack")
        return self._items.pop()

    def peek(self) -> T:
        if not self._items:
            raise StackUnderflow("cannot peek at an empty stack")
        return self._items[-1]

    def is_empty(self) -> bool:
        return not self._items

    def size(self) -> int:
        return len(self._items)

    def clear(self) -> None:
        self._items.clear()

    def __iter__(self):
        return reversed(self._items)

    def __repr__(self) -> str:
        return f"Stack({self._items!r})"


class TokenType(Enum):
    NUMBER = "NUMBER"
    OPERATOR = "OPERATOR"
    LEFT_PAREN = "LEFT_PAREN"
    RIGHT_PAREN = "RIGHT_PAREN"


@dataclass(frozen=True)
class Token:
    kind: TokenType
    value: str


class ExpressionEvaluator:
    """
    Converts infix expressions to postfix notation and evaluates postfix
    expressions using separate operator and operand stacks.

    Supported operators:
        +, -, *, /, %, ^

    Unary minus is represented internally as 'u-'.
    """

    PRECEDENCE = {
        "u-": 4,
        "^": 3,
        "*": 2,
        "/": 2,
        "%": 2,
        "+": 1,
        "-": 1,
    }

    RIGHT_ASSOCIATIVE = {"^", "u-"}

    BINARY_OPERATORS: dict[str, Callable[[float, float], float]] = {
        "+": operator.add,
        "-": operator.sub,
        "*": operator.mul,
        "/": operator.truediv,
        "%": operator.mod,
        "^": operator.pow,
    }

    def tokenize(self, expression: str) -> list[Token]:
        tokens: list[Token] = []
        i = 0
        expect_operand = True

        while i < len(expression):
            char = expression[i]

            if char.isspace():
                i += 1
                continue

            if char.isdigit() or char == ".":
                start = i
                dots = 0
                digits = 0

                while i < len(expression) and (
                    expression[i].isdigit() or expression[i] == "."
                ):
                    if expression[i] == ".":
                        dots += 1
                    else:
                        digits += 1
                    i += 1

                literal = expression[start:i]
                if dots > 1 or digits == 0:
                    raise InvalidExpression(f"invalid number: {literal}")

                tokens.append(Token(TokenType.NUMBER, literal))
                expect_operand = False
                continue

            if char == "(":
                tokens.append(Token(TokenType.LEFT_PAREN, char))
                expect_operand = True
                i += 1
                continue

            if char == ")":
                if expect_operand:
                    raise InvalidExpression("unexpected closing parenthesis")
                tokens.append(Token(TokenType.RIGHT_PAREN, char))
                expect_operand = False
                i += 1
                continue

            if char in "+-*/%^":
                if char == "-" and expect_operand:
                    tokens.append(Token(TokenType.OPERATOR, "u-"))
                elif expect_operand:
                    raise InvalidExpression(
                        f"unexpected binary operator: {char}"
                    )
                else:
                    tokens.append(Token(TokenType.OPERATOR, char))
                    expect_operand = True
                i += 1
                continue

            raise InvalidExpression(f"unsupported character: {char}")

        if not tokens or expect_operand:
            raise InvalidExpression("incomplete expression")

        return tokens

    def infix_to_postfix(self, expression: str) -> list[str]:
        tokens = self.tokenize(expression)
        output: list[str] = []
        operators: Stack[str] = Stack()

        for token in tokens:
            if token.kind is TokenType.NUMBER:
                output.append(token.value)

            elif token.kind is TokenType.LEFT_PAREN:
                operators.push(token.value)

            elif token.kind is TokenType.RIGHT_PAREN:
                while not operators.is_empty() and operators.peek() != "(":
                    output.append(operators.pop())

                if operators.is_empty():
                    raise InvalidExpression("unmatched closing parenthesis")

                operators.pop()

            else:
                current = token.value

                while (
                    not operators.is_empty()
                    and operators.peek() != "("
                    and (
                        self.PRECEDENCE[operators.peek()] > self.PRECEDENCE[current]
                        or (
                            self.PRECEDENCE[operators.peek()]
                            == self.PRECEDENCE[current]
                            and current not in self.RIGHT_ASSOCIATIVE
                        )
                    )
                ):
                    output.append(operators.pop())

                operators.push(current)

        while not operators.is_empty():
            top = operators.pop()
            if top == "(":
                raise InvalidExpression("unmatched opening parenthesis")
            output.append(top)

        return output

    def evaluate_postfix(self, postfix: Iterable[str]) -> float:
        values: Stack[float] = Stack()

        for token in postfix:
            if token not in self.PRECEDENCE:
                try:
                    values.push(float(token))
                except ValueError as exc:
                    raise InvalidExpression(f"invalid postfix token: {token}") from exc
                continue

            if token == "u-":
                try:
                    values.push(-values.pop())
                except StackUnderflow as exc:
                    raise InvalidExpression("missing operand for unary minus") from exc
                continue

            try:
                right = values.pop()
                left = values.pop()
            except StackUnderflow as exc:
                raise InvalidExpression(f"missing operand for {token}") from exc

            if token in {"/", "%"} and right == 0:
                raise InvalidExpression("division or modulo by zero")

            try:
                result = self.BINARY_OPERATORS[token](left, right)
            except (OverflowError, ValueError, ZeroDivisionError) as exc:
                raise InvalidExpression(
                    f"operator {token} failed for {left} and {right}"
                ) from exc

            if not math.isfinite(result):
                raise InvalidExpression("non-finite arithmetic result")

            values.push(result)

        if values.size() != 1:
            raise InvalidExpression("malformed postfix expression")

        return values.pop()

    def evaluate(self, expression: str) -> float:
        return self.evaluate_postfix(self.infix_to_postfix(expression))


def check_parentheses(text: str) -> bool:
    """Classic application of a stack: balanced delimiter validation."""
    stack: Stack[str] = Stack()
    pairs = {")": "(", "]": "[", "}": "{"}

    for char in text:
        if char in "([{":
            stack.push(char)
        elif char in ")]}":
            if stack.is_empty() or stack.pop() != pairs[char]:
                return False

    return stack.is_empty()


def next_greater_elements(values: list[int]) -> list[int]:
    """
    Monotonic decreasing stack.
    Each element is pushed and popped at most once: O(n) time.
    """
    result = [-1] * len(values)
    indices: Stack[int] = Stack()

    for i, value in enumerate(values):
        while not indices.is_empty() and values[indices.peek()] < value:
            result[indices.pop()] = value
        indices.push(i)

    return result


def browser_history_demo() -> list[str]:
    """Two-stack browser history supporting back and forward navigation."""
    back: Stack[str] = Stack()
    forward: Stack[str] = Stack()
    current = "home"

    def visit(page: str) -> None:
        nonlocal current
        back.push(current)
        current = page
        forward.clear()

    def go_back() -> str:
        nonlocal current
        if back.is_empty():
            return current
        forward.push(current)
        current = back.pop()
        return current

    def go_forward() -> str:
        nonlocal current
        if forward.is_empty():
            return current
        back.push(current)
        current = forward.pop()
        return current

    visit("products")
    visit("products/stacks")
    visit("products/stacks/python")
    go_back()
    go_back()
    go_forward()

    return [current, repr(back), repr(forward)]


def run_tests() -> None:
    stack = Stack[int](2)
    stack.push(10)
    stack.push(20)

    try:
        stack.push(30)
        raise AssertionError("overflow was not detected")
    except StackError:
        pass

    assert stack.pop() == 20
    assert stack.peek() == 10
    assert stack.pop() == 10

    try:
        stack.pop()
        raise AssertionError("underflow was not detected")
    except StackUnderflow:
        pass

    assert check_parentheses("{[()]}") is True
    assert check_parentheses("{[(])}") is False

    assert next_greater_elements([4, 5, 2, 10, 8]) == [5, 10, 10, -1, -1]

    evaluator = ExpressionEvaluator()
    cases = {
        "2 + 3 * 4": 14.0,
        "(2 + 3) * 4": 20.0,
        "2 ^ 3 ^ 2": 512.0,
        "-2 * (3 + 4)": -14.0,
        "10 % 3": 1.0,
        "2 * -3 + 10": 4.0,
    }

    for expression, expected in cases.items():
        actual = evaluator.evaluate(expression)
        assert math.isclose(actual, expected), (expression, actual, expected)

    for invalid in ["2 / 0", "(2 + 3", "2 +", "2 & 3", "2 + * 3"]:
        try:
            evaluator.evaluate(invalid)
            raise AssertionError(f"invalid expression accepted: {invalid}")
        except InvalidExpression:
            pass


def main() -> None:
    run_tests()

    evaluator = ExpressionEvaluator()
    expressions = [
        "3 + 4 * 2 / (1 - 5) ^ 2",
        "-2 ^ 3 + 10",
        "(15 % 4) * (2 + 6)",
    ]

    print("STACK OPERATIONS")
    stack = Stack[str]()
    for item in ["compile", "test", "package"]:
        stack.push(item)
    print("top:", stack.peek())
    print("pop:", stack.pop())
    print("remaining:", stack)

    print("\nPARENTHESES")
    print("{[()]} ->", check_parentheses("{[()]}"))
    print("{[(])} ->", check_parentheses("{[(])}"))

    print("\nMONOTONIC STACK")
    values = [4, 5, 2, 10, 8]
    print("values:", values)
    print("next greater:", next_greater_elements(values))

    print("\nEXPRESSION EVALUATION")
    for expression in expressions:
        postfix = evaluator.infix_to_postfix(expression)
        value = evaluator.evaluate_postfix(postfix)
        print(f"{expression} -> {' '.join(postfix)} -> {value:g}")

    print("\nBROWSER HISTORY")
    print(browser_history_demo())

    print("\nProduction considerations:")
    print("- Stack push/pop/peek are O(1) amortized with an array-backed representation.")
    print("- Expression conversion and evaluation are O(n) for n tokens.")
    print("- Validate untrusted expressions before evaluation and impose length/resource limits.")
    print("- Avoid exposing internal stack contents in production logs when values may be sensitive.")


if __name__ == "__main__":
    main()
