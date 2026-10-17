#!/usr/bin/env python3
"""A self-contained compiler, bytecode virtual machine, and interpreter.

The implementation demonstrates lexical analysis, parsing, abstract syntax
trees, semantic validation, bytecode generation, stack-based execution,
runtime environments, interpretation, diagnostics, and instruction tracing.

Run with Python 3.10 or later:
    python compiler_runtime_lab.py
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable


class LanguageError(Exception):
    """Base exception for source-language failures."""


class LexError(LanguageError):
    """Invalid character or malformed token."""


class ParseError(LanguageError):
    """Invalid source grammar."""


class SemanticError(LanguageError):
    """Invalid variable or operation semantics."""


class RuntimeLanguageError(LanguageError):
    """Failure during program execution."""


@dataclass(frozen=True)
class Token:
    kind: str
    value: Any
    line: int
    column: int


KEYWORDS = {"let", "print", "if", "else", "while", "true", "false"}
SINGLE_CHAR_TOKENS = {
    "+": "PLUS",
    "-": "MINUS",
    "*": "STAR",
    "/": "SLASH",
    "(": "LPAREN",
    ")": "RPAREN",
    "{": "LBRACE",
    "}": "RBRACE",
    ";": "SEMICOLON",
    "=": "ASSIGN",
    "<": "LESS",
    ">": "GREATER",
}

DOUBLE_CHAR_TOKENS = {
    "==": "EQUAL",
    "!=": "NOT_EQUAL",
    "<=": "LESS_EQUAL",
    ">=": "GREATER_EQUAL",
}


def tokenize(source: str) -> list[Token]:
    """Convert source text into a location-aware token stream."""
    tokens: list[Token] = []
    i = 0
    line = 1
    column = 1

    while i < len(source):
        char = source[i]

        if char in " \t\r":
            i += 1
            column += 1
            continue

        if char == "\n":
            i += 1
            line += 1
            column = 1
            continue

        if source.startswith("//", i):
            while i < len(source) and source[i] != "\n":
                i += 1
                column += 1
            continue

        start_line, start_column = line, column

        if char.isdigit():
            start = i
            while i < len(source) and source[i].isdigit():
                i += 1
                column += 1

            if i < len(source) and source[i] == ".":
                if i + 1 < len(source) and source[i + 1].isdigit():
                    i += 1
                    column += 1
                    while i < len(source) and source[i].isdigit():
                        i += 1
                        column += 1

            text = source[start:i]
            value = float(text) if "." in text else int(text)
            tokens.append(Token("NUMBER", value, start_line, start_column))
            continue

        if char.isalpha() or char == "_":
            start = i
            while i < len(source) and (
                source[i].isalnum() or source[i] == "_"
            ):
                i += 1
                column += 1

            text = source[start:i]
            kind = text.upper() if text in KEYWORDS else "IDENTIFIER"
            tokens.append(Token(kind, text, start_line, start_column))
            continue

        pair = source[i:i + 2]
        if pair in DOUBLE_CHAR_TOKENS:
            tokens.append(
                Token(DOUBLE_CHAR_TOKENS[pair], pair, line, column)
            )
            i += 2
            column += 2
            continue

        if char in SINGLE_CHAR_TOKENS:
            tokens.append(
                Token(SINGLE_CHAR_TOKENS[char], char, line, column)
            )
            i += 1
            column += 1
            continue

        raise LexError(
            f"Unexpected character {char!r} at {line}:{column}"
        )

    tokens.append(Token("EOF", None, line, column))
    return tokens


# Immutable AST nodes keep parsing separate from execution strategy.
@dataclass(frozen=True)
class Number:
    value: int | float


@dataclass(frozen=True)
class Boolean:
    value: bool


@dataclass(frozen=True)
class Variable:
    name: str


@dataclass(frozen=True)
class Binary:
    operator: str
    left: Any
    right: Any


@dataclass(frozen=True)
class Unary:
    operator: str
    operand: Any


@dataclass(frozen=True)
class Declaration:
    name: str
    initializer: Any


@dataclass(frozen=True)
class Assignment:
    name: str
    expression: Any


@dataclass(frozen=True)
class Print:
    expression: Any


@dataclass(frozen=True)
class Block:
    statements: tuple[Any, ...]


@dataclass(frozen=True)
class If:
    condition: Any
    then_branch: Any
    else_branch: Any | None


@dataclass(frozen=True)
class While:
    condition: Any
    body: Any


class Parser:
    """Recursive-descent parser with conventional expression precedence."""

    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.current = 0

    def peek(self) -> Token:
        return self.tokens[self.current]

    def check(self, kind: str) -> bool:
        return self.peek().kind == kind

    def advance(self) -> Token:
        token = self.peek()
        if token.kind != "EOF":
            self.current += 1
        return token

    def match(self, *kinds: str) -> bool:
        if self.check_any(*kinds):
            self.advance()
            return True
        return False

    def check_any(self, *kinds: str) -> bool:
        return self.peek().kind in kinds

    def consume(self, kind: str, message: str) -> Token:
        if self.check(kind):
            return self.advance()
        token = self.peek()
        raise ParseError(
            f"{message} at {token.line}:{token.column}; "
            f"found {token.kind}"
        )

    def parse(self) -> tuple[Any, ...]:
        statements = []
        while not self.check("EOF"):
            statements.append(self.statement())
        return tuple(statements)

    def statement(self) -> Any:
        if self.match("LET"):
            name = self.consume(
                "IDENTIFIER", "Expected a variable name"
            ).value
            self.consume("ASSIGN", "Expected '=' after variable name")
            initializer = self.expression()
            self.consume("SEMICOLON", "Expected ';' after declaration")
            return Declaration(name, initializer)

        if self.match("PRINT"):
            expression = self.expression()
            self.consume("SEMICOLON", "Expected ';' after print")
            return Print(expression)

        if self.match("IF"):
            self.consume("LPAREN", "Expected '(' after if")
            condition = self.expression()
            self.consume("RPAREN", "Expected ')' after condition")
            then_branch = self.statement()
            else_branch = (
                self.statement() if self.match("ELSE") else None
            )
            return If(condition, then_branch, else_branch)

        if self.match("WHILE"):
            self.consume("LPAREN", "Expected '(' after while")
            condition = self.expression()
            self.consume("RPAREN", "Expected ')' after condition")
            return While(condition, self.statement())

        if self.match("LBRACE"):
            statements = []
            while not self.check("RBRACE") and not self.check("EOF"):
                statements.append(self.statement())
            self.consume("RBRACE", "Expected '}' after block")
            return Block(tuple(statements))

        if self.check("IDENTIFIER"):
            name = self.advance().value
            self.consume("ASSIGN", "Expected '=' in assignment")
            expression = self.expression()
            self.consume("SEMICOLON", "Expected ';' after assignment")
            return Assignment(name, expression)

        token = self.peek()
        raise ParseError(
            f"Expected a statement at {token.line}:{token.column}"
        )

    def expression(self) -> Any:
        return self.equality()

    def equality(self) -> Any:
        expression = self.comparison()
        while self.match("EQUAL", "NOT_EQUAL"):
            operator = self.tokens[self.current - 1].value
            expression = Binary(operator, expression, self.comparison())
        return expression

    def comparison(self) -> Any:
        expression = self.term()
        while self.match("LESS", "LESS_EQUAL", "GREATER", "GREATER_EQUAL"):
            operator = self.tokens[self.current - 1].value
            expression = Binary(operator, expression, self.term())
        return expression

    def term(self) -> Any:
        expression = self.factor()
        while self.match("PLUS", "MINUS"):
            operator = self.tokens[self.current - 1].value
            expression = Binary(operator, expression, self.factor())
        return expression

    def factor(self) -> Any:
        expression = self.unary()
        while self.match("STAR", "SLASH"):
            operator = self.tokens[self.current - 1].value
            expression = Binary(operator, expression, self.unary())
        return expression

    def unary(self) -> Any:
        if self.match("MINUS"):
            return Unary("-", self.unary())
        return self.primary()

    def primary(self) -> Any:
        if self.match("NUMBER"):
            return Number(self.tokens[self.current - 1].value)

        if self.match("TRUE"):
            return Boolean(True)

        if self.match("FALSE"):
            return Boolean(False)

        if self.match("IDENTIFIER"):
            return Variable(self.tokens[self.current - 1].value)

        if self.match("LPAREN"):
            expression = self.expression()
            self.consume("RPAREN", "Expected ')' after expression")
            return expression

        token = self.peek()
        raise ParseError(
            f"Expected an expression at {token.line}:{token.column}"
        )


class SemanticAnalyzer:
    """Validate declarations and references before execution."""

    def analyze(self, statements: tuple[Any, ...]) -> None:
        self._statements(statements, set())

    def _statements(self, statements: tuple[Any, ...], scope: set[str]) -> None:
        for statement in statements:
            if isinstance(statement, Declaration):
                if statement.name in scope:
                    raise SemanticError(
                        f"Variable {statement.name!r} already declared"
                    )
                self._expression(statement.initializer, scope)
                scope.add(statement.name)

            elif isinstance(statement, Assignment):
                if statement.name not in scope:
                    raise SemanticError(
                        f"Assignment to undeclared variable {statement.name!r}"
                    )
                self._expression(statement.expression, scope)

            elif isinstance(statement, Print):
                self._expression(statement.expression, scope)

            elif isinstance(statement, Block):
                self._statements(statement.statements, set(scope))

            elif isinstance(statement, If):
                self._expression(statement.condition, scope)
                self._statements((statement.then_branch,), set(scope))
                if statement.else_branch is not None:
                    self._statements((statement.else_branch,), set(scope))

            elif isinstance(statement, While):
                self._expression(statement.condition, scope)
                self._statements((statement.body,), set(scope))

    def _expression(self, expression: Any, scope: set[str]) -> None:
        if isinstance(expression, Variable):
            if expression.name not in scope:
                raise SemanticError(
                    f"Reference to undeclared variable {expression.name!r}"
                )
        elif isinstance(expression, Binary):
            self._expression(expression.left, scope)
            self._expression(expression.right, scope)
        elif isinstance(expression, Unary):
            self._expression(expression.operand, scope)


class Interpreter:
    """Direct AST interpreter using a mutable environment."""

    def __init__(self) -> None:
        self.environment: dict[str, Any] = {}
        self.output: list[str] = []
        self.steps = 0
        self.step_limit = 10_000

    def execute(self, statements: tuple[Any, ...]) -> list[str]:
        for statement in statements:
            self._statement(statement)
        return self.output

    def _tick(self) -> None:
        self.steps += 1
        if self.steps > self.step_limit:
            raise RuntimeLanguageError("Execution step limit exceeded")

    def _statement(self, statement: Any) -> None:
        self._tick()

        if isinstance(statement, Declaration):
            self.environment[statement.name] = self._expression(
                statement.initializer
            )
        elif isinstance(statement, Assignment):
            if statement.name not in self.environment:
                raise RuntimeLanguageError(
                    f"Undefined variable {statement.name!r}"
                )
            self.environment[statement.name] = self._expression(
                statement.expression
            )
        elif isinstance(statement, Print):
            self.output.append(
                self._format(self._expression(statement.expression))
            )
        elif isinstance(statement, Block):
            for child in statement.statements:
                self._statement(child)
        elif isinstance(statement, If):
            if self._truthy(self._expression(statement.condition)):
                self._statement(statement.then_branch)
            elif statement.else_branch is not None:
                self._statement(statement.else_branch)
        elif isinstance(statement, While):
            while self._truthy(self._expression(statement.condition)):
                self._statement(statement.body)

    def _expression(self, expression: Any) -> Any:
        self._tick()

        if isinstance(expression, Number):
            return expression.value
        if isinstance(expression, Boolean):
            return expression.value
        if isinstance(expression, Variable):
            if expression.name not in self.environment:
                raise RuntimeLanguageError(
                    f"Undefined variable {expression.name!r}"
                )
            return self.environment[expression.name]
        if isinstance(expression, Unary):
            value = self._expression(expression.operand)
            if expression.operator == "-" and self._is_number(value):
                return -value
            raise RuntimeLanguageError("Invalid unary operand")
        if isinstance(expression, Binary):
            left = self._expression(expression.left)
            right = self._expression(expression.right)
            return self._binary(expression.operator, left, right)

        raise RuntimeLanguageError("Unsupported expression node")

    @staticmethod
    def _is_number(value: Any) -> bool:
        return type(value) in (int, float)

    def _binary(self, operator: str, left: Any, right: Any) -> Any:
        if operator in {"+", "-", "*", "/"}:
            if not self._is_number(left) or not self._is_number(right):
                raise RuntimeLanguageError(
                    f"Operator {operator} requires numeric operands"
                )

            if operator == "+":
                return left + right
            if operator == "-":
                return left - right
            if operator == "*":
                return left * right
            if right == 0:
                raise RuntimeLanguageError("Division by zero")
            return left / right

        if operator in {"<", "<=", ">", ">="}:
            if not self._is_number(left) or not self._is_number(right):
                raise RuntimeLanguageError(
                    f"Operator {operator} requires numeric operands"
                )
            return {
                "<": left < right,
                "<=": left <= right,
                ">": left > right,
                ">=": left >= right,
            }[operator]

        if operator in {"==", "!="}:
            equal = type(left) is type(right) and left == right
            return equal if operator == "==" else not equal

        raise RuntimeLanguageError(f"Unknown operator {operator!r}")

    @staticmethod
    def _truthy(value: Any) -> bool:
        if type(value) is not bool:
            raise RuntimeLanguageError("Conditions must be Boolean")
        return value

    @staticmethod
    def _format(value: Any) -> str:
        if type(value) is bool:
            return "true" if value else "false"
        return str(value)


class Op(Enum):
    CONSTANT = auto()
    LOAD = auto()
    STORE = auto()
    ADD = auto()
    SUBTRACT = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    NEGATE = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    EQUAL = auto()
    NOT_EQUAL = auto()
    JUMP_IF_FALSE = auto()
    JUMP = auto()
    PRINT = auto()
    HALT = auto()


@dataclass
class Instruction:
    op: Op
    argument: Any = None


class BytecodeCompiler:
    """Lower AST nodes into instructions for a stack-based virtual machine."""

    def __init__(self) -> None:
        self.instructions: list[Instruction] = []

    def compile(self, statements: tuple[Any, ...]) -> list[Instruction]:
        for statement in statements:
            self._statement(statement)
        self.instructions.append(Instruction(Op.HALT))
        return self.instructions

    def emit(self, op: Op, argument: Any = None) -> int:
        self.instructions.append(Instruction(op, argument))
        return len(self.instructions) - 1

    def patch(self, index: int, target: int) -> None:
        self.instructions[index].argument = target

    def _statement(self, statement: Any) -> None:
        if isinstance(statement, Declaration):
            self._expression(statement.initializer)
            self.emit(Op.STORE, statement.name)
        elif isinstance(statement, Assignment):
            self._expression(statement.expression)
            self.emit(Op.STORE, statement.name)
        elif isinstance(statement, Print):
            self._expression(statement.expression)
            self.emit(Op.PRINT)
        elif isinstance(statement, Block):
            for child in statement.statements:
                self._statement(child)
        elif isinstance(statement, If):
            self._expression(statement.condition)
            false_jump = self.emit(Op.JUMP_IF_FALSE, None)
            self._statement(statement.then_branch)

            if statement.else_branch is None:
                self.patch(false_jump, len(self.instructions))
            else:
                end_jump = self.emit(Op.JUMP, None)
                self.patch(false_jump, len(self.instructions))
                self._statement(statement.else_branch)
                self.patch(end_jump, len(self.instructions))

        elif isinstance(statement, While):
            loop_start = len(self.instructions)
            self._expression(statement.condition)
            exit_jump = self.emit(Op.JUMP_IF_FALSE, None)
            self._statement(statement.body)
            self.emit(Op.JUMP, loop_start)
            self.patch(exit_jump, len(self.instructions))

    def _expression(self, expression: Any) -> None:
        if isinstance(expression, Number):
            self.emit(Op.CONSTANT, expression.value)
        elif isinstance(expression, Boolean):
            self.emit(Op.CONSTANT, expression.value)
        elif isinstance(expression, Variable):
            self.emit(Op.LOAD, expression.name)
        elif isinstance(expression, Unary):
            self._expression(expression.operand)
            self.emit(Op.NEGATE)
        elif isinstance(expression, Binary):
            self._expression(expression.left)
            self._expression(expression.right)
            operation = {
                "+": Op.ADD,
                "-": Op.SUBTRACT,
                "*": Op.MULTIPLY,
                "/": Op.DIVIDE,
                "<": Op.LESS,
                "<=": Op.LESS_EQUAL,
                ">": Op.GREATER,
                ">=": Op.GREATER_EQUAL,
                "==": Op.EQUAL,
                "!=": Op.NOT_EQUAL,
            }[expression.operator]
            self.emit(operation)


class VirtualMachine:
    """Execute bytecode with an operand stack and runtime environment."""

    def __init__(
        self,
        instructions: list[Instruction],
        trace: bool = False,
        step_limit: int = 10_000,
    ) -> None:
        self.instructions = instructions
        self.trace = trace
        self.step_limit = step_limit
        self.stack: list[Any] = []
        self.environment: dict[str, Any] = {}
        self.output: list[str] = []
        self.ip = 0
        self.steps = 0

    def run(self) -> list[str]:
        while self.ip < len(self.instructions):
            self.steps += 1
            if self.steps > self.step_limit:
                raise RuntimeLanguageError(
                    "Virtual-machine instruction limit exceeded"
                )

            instruction = self.instructions[self.ip]

            if self.trace:
                print(
                    f"ip={self.ip:03} op={instruction.op.name:16} "
                    f"arg={instruction.argument!r} stack={self.stack!r}"
                )

            self.ip += 1
            op, arg = instruction.op, instruction.argument

            if op == Op.HALT:
                break
            elif op == Op.CONSTANT:
                self.stack.append(arg)
            elif op == Op.LOAD:
                if arg not in self.environment:
                    raise RuntimeLanguageError(
                        f"Undefined variable {arg!r}"
                    )
                self.stack.append(self.environment[arg])
            elif op == Op.STORE:
                self.environment[arg] = self._pop()
            elif op == Op.PRINT:
                self.output.append(Interpreter._format(self._pop()))
            elif op == Op.NEGATE:
                value = self._pop()
                if not Interpreter._is_number(value):
                    raise RuntimeLanguageError(
                        "Unary minus requires a numeric operand"
                    )
                self.stack.append(-value)
            elif op == Op.JUMP_IF_FALSE:
                condition = self._pop()
                if type(condition) is not bool:
                    raise RuntimeLanguageError(
                        "Conditional jump requires a Boolean"
                    )
                if not condition:
                    self.ip = arg
            elif op == Op.JUMP:
                self.ip = arg
            else:
                right = self._pop()
                left = self._pop()
                operator = {
                    Op.ADD: "+",
                    Op.SUBTRACT: "-",
                    Op.MULTIPLY: "*",
                    Op.DIVIDE: "/",
                    Op.LESS: "<",
                    Op.LESS_EQUAL: "<=",
                    Op.GREATER: ">",
                    Op.GREATER_EQUAL: ">=",
                    Op.EQUAL: "==",
                    Op.NOT_EQUAL: "!=",
                }[op]
                result = Interpreter()._binary(operator, left, right)
                self.stack.append(result)

        return self.output

    def _pop(self) -> Any:
        if not self.stack:
            raise RuntimeLanguageError(
                f"Operand stack underflow near instruction {self.ip - 1}"
            )
        return self.stack.pop()


def compile_source(source: str) -> list[Instruction]:
    tokens = tokenize(source)
    syntax_tree = Parser(tokens).parse()
    SemanticAnalyzer().analyze(syntax_tree)
    return BytecodeCompiler().compile(syntax_tree)


def run_interpreter(source: str) -> list[str]:
    syntax_tree = Parser(tokenize(source)).parse()
    SemanticAnalyzer().analyze(syntax_tree)
    return Interpreter().execute(syntax_tree)


def run_compiled(source: str, trace: bool = False) -> list[str]:
    bytecode = compile_source(source)
    return VirtualMachine(bytecode, trace=trace).run()


def demonstrate_failure(
    title: str,
    source: str,
    expected_error: type[Exception],
    runner: Callable[[str], Any],
) -> None:
    print(f"\n{title}")
    try:
        runner(source)
    except expected_error as error:
        print(f"Handled {type(error).__name__}: {error}")
    else:
        raise AssertionError(f"Expected {expected_error.__name__}")


def main() -> None:
    source = """
    // Compute the sum of the first five positive integers.
    let total = 0;
    let counter = 1;

    while (counter <= 5) {
        total = total + counter;
        counter = counter + 1;
    }

    if (total == 15) {
        print total;
    } else {
        print 0;
    }

    print total / 3;
    print true;
    """

    print("DIRECT INTERPRETATION")
    interpreted = run_interpreter(source)
    for value in interpreted:
        print(value)

    print("\nCOMPILED BYTECODE")
    bytecode = compile_source(source)
    for index, instruction in enumerate(bytecode):
        print(f"{index:03}: {instruction.op.name:<16} {instruction.argument!r}")

    print("\nBYTECODE EXECUTION")
    compiled = run_compiled(source)
    for value in compiled:
        print(value)

    assert interpreted == compiled
    assert interpreted == ["15", "5.0", "true"]
    print("\nDifferential execution check passed.")

    print("\nINSTRUCTION TRACE")
    VirtualMachine(bytecode, trace=True).run()

    demonstrate_failure(
        "Lexical error",
        "let amount = 10 @ 2;",
        LexError,
        compile_source,
    )

    demonstrate_failure(
        "Syntax error",
        "let amount = ;",
        ParseError,
        compile_source,
    )

    demonstrate_failure(
        "Semantic error",
        "print missing_value;",
        SemanticError,
        compile_source,
    )

    demonstrate_failure(
        "Runtime division by zero",
        "let result = 12 / 0; print result;",
        RuntimeLanguageError,
        run_compiled,
    )

    demonstrate_failure(
        "Type error in a condition",
        "if (5) print 1;",
        RuntimeLanguageError,
        run_compiled,
    )

    demonstrate_failure(
        "Execution budget prevents an infinite loop",
        "while (true) {}",
        RuntimeLanguageError,
        lambda text: VirtualMachine(
            compile_source(text), step_limit=30
        ).run(),
    )

    print("\nCompiler and runtime laboratory completed.")


if __name__ == "__main__":
    main()
