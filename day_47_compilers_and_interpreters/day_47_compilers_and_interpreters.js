"use strict";

/*
 * A JavaScript compiler/runtime laboratory.
 *
 * Demonstrates a separate compilation pipeline, bytecode verification,
 * closure environments, asynchronous compilation, and a fuel-limited VM.
 * Requires Node.js 18 or later. No third-party packages are required.
 */

class CompileError extends Error {}
class VerificationError extends Error {}
class ExecutionError extends Error {}

const OPCODES = Object.freeze({
  CONST: "CONST",
  LOAD: "LOAD",
  STORE: "STORE",
  ADD: "ADD",
  MUL: "MUL",
  DIV: "DIV",
  LT: "LT",
  JUMP: "JUMP",
  JUMP_IF_FALSE: "JUMP_IF_FALSE",
  PRINT: "PRINT",
  HALT: "HALT"
});

function tokenize(source) {
  const pattern =
    /\s+|\/\/[^\n]*|(?:\d+(?:\.\d+)?)|(?:[A-Za-z_]\w*)|(?:==|!=|<=|>=|[+\-*/(){};=<>])/gy;
  const tokens = [];
  let position = 0;

  while (position < source.length) {
    pattern.lastIndex = position;
    const match = pattern.exec(source);

    if (!match) {
      throw new CompileError(
        `Unexpected character ${JSON.stringify(source[position])} ` +
        `at offset ${position}`
      );
    }

    const text = match[0];
    position = pattern.lastIndex;

    if (/^\s+$/.test(text) || text.startsWith("//")) {
      continue;
    }

    if (/^\d/.test(text)) {
      tokens.push({
        type: "NUMBER",
        value: Number(text)
      });
    } else if (/^[A-Za-z_]/.test(text)) {
      const keywords = ["let", "print", "while", "true", "false"];
      tokens.push({
        type: keywords.includes(text) ? text.toUpperCase() : "IDENTIFIER",
        value: text
      });
    } else {
      tokens.push({ type: text, value: text });
    }
  }

  tokens.push({ type: "EOF", value: null });
  return tokens;
}

class Parser {
  constructor(tokens) {
    this.tokens = tokens;
    this.position = 0;
  }

  peek() {
    return this.tokens[this.position];
  }

  match(...types) {
    if (types.includes(this.peek().type)) {
      return this.tokens[this.position++];
    }
    return null;
  }

  consume(type, message) {
    const token = this.match(type);
    if (!token) {
      throw new CompileError(
        `${message}; found ${this.peek().type}`
      );
    }
    return token;
  }

  parse() {
    const statements = [];
    while (this.peek().type !== "EOF") {
      statements.push(this.statement());
    }
    return statements;
  }

  statement() {
    if (this.match("LET")) {
      const name = this.consume("IDENTIFIER", "Expected variable name").value;
      this.consume("=", "Expected '='");
      const value = this.expression();
      this.consume(";", "Expected ';'");
      return { kind: "declare", name, value };
    }

    if (this.match("PRINT")) {
      const value = this.expression();
      this.consume(";", "Expected ';' after print");
      return { kind: "print", value };
    }

    if (this.match("WHILE")) {
      this.consume("(", "Expected '(' after while");
      const condition = this.expression();
      this.consume(")", "Expected ')' after condition");
      return { kind: "while", condition, body: this.statement() };
    }

    if (this.match("{")) {
      const body = [];
      while (this.peek().type !== "}" && this.peek().type !== "EOF") {
        body.push(this.statement());
      }
      this.consume("}", "Expected '}'");
      return { kind: "block", body };
    }

    if (this.peek().type === "IDENTIFIER") {
      const name = this.match("IDENTIFIER").value;
      this.consume("=", "Expected '=' in assignment");
      const value = this.expression();
      this.consume(";", "Expected ';' after assignment");
      return { kind: "assign", name, value };
    }

    throw new CompileError(`Unexpected statement token ${this.peek().type}`);
  }

  expression() {
    return this.comparison();
  }

  comparison() {
    let expression = this.addition();

    while (this.match("<", "==", "!=", "<=", ">=")) {
      const operator = this.tokens[this.position - 1].type;
      expression = {
        kind: "binary",
        operator,
        left: expression,
        right: this.addition()
      };
    }

    return expression;
  }

  addition() {
    let expression = this.multiplication();

    while (this.match("+", "-")) {
      const operator = this.tokens[this.position - 1].type;
      expression = {
        kind: "binary",
        operator,
        left: expression,
        right: this.multiplication()
      };
    }

    return expression;
  }

  multiplication() {
    let expression = this.primary();

    while (this.match("*", "/")) {
      const operator = this.tokens[this.position - 1].type;
      expression = {
        kind: "binary",
        operator,
        left: expression,
        right: this.primary()
      };
    }

    return expression;
  }

  primary() {
    const number = this.match("NUMBER");
    if (number) {
      return { kind: "constant", value: number.value };
    }

    if (this.match("TRUE")) {
      return { kind: "constant", value: true };
    }

    if (this.match("FALSE")) {
      return { kind: "constant", value: false };
    }

    const identifier = this.match("IDENTIFIER");
    if (identifier) {
      return { kind: "variable", name: identifier.value };
    }

    if (this.match("(")) {
      const expression = this.expression();
      this.consume(")", "Expected ')'");
      return expression;
    }

    throw new CompileError(
      `Expected expression; found ${this.peek().type}`
    );
  }
}

/*
 * Lexical scope analysis rejects unresolved names before bytecode execution.
 * A nested block receives a copy of its parent's visible declarations.
 */
function analyze(statements, inherited = new Set()) {
  const visible = new Set(inherited);

  for (const statement of statements) {
    switch (statement.kind) {
      case "declare":
        inspectExpression(statement.value, visible);
        if (visible.has(statement.name)) {
          throw new CompileError(
            `Duplicate declaration '${statement.name}'`
          );
        }
        visible.add(statement.name);
        break;

      case "assign":
        if (!visible.has(statement.name)) {
          throw new CompileError(
            `Assignment to undeclared variable '${statement.name}'`
          );
        }
        inspectExpression(statement.value, visible);
        break;

      case "print":
        inspectExpression(statement.value, visible);
        break;

      case "block":
        analyze(statement.body, visible);
        break;

      case "while":
        inspectExpression(statement.condition, visible);
        analyze([statement.body], visible);
        break;

      default:
        throw new CompileError(`Unknown statement ${statement.kind}`);
    }
  }

  return visible;
}

function inspectExpression(expression, visible) {
  if (expression.kind === "variable" && !visible.has(expression.name)) {
    throw new CompileError(`Unknown variable '${expression.name}'`);
  }

  if (expression.kind === "binary") {
    inspectExpression(expression.left, visible);
    inspectExpression(expression.right, visible);
  }
}

/*
 * Lexical environments use parent links instead of copying all variable
 * values. This is the same basic mechanism used by many interpreters.
 */
class Environment {
  constructor(parent = null) {
    this.parent = parent;
    this.values = new Map();
  }

  declare(name, value) {
    if (this.values.has(name)) {
      throw new ExecutionError(`Duplicate binding '${name}'`);
    }
    this.values.set(name, value);
  }

  resolve(name) {
    if (this.values.has(name)) {
      return this;
    }
    if (this.parent) {
      return this.parent.resolve(name);
    }
    throw new ExecutionError(`Undefined variable '${name}'`);
  }

  get(name) {
    return this.resolve(name).values.get(name);
  }

  assign(name, value) {
    this.resolve(name).values.set(name, value);
  }
}

function requireNumber(value, operator) {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new ExecutionError(`${operator} requires finite numeric operands`);
  }
  return value;
}

function evaluate(expression, environment) {
  if (expression.kind === "constant") {
    return expression.value;
  }

  if (expression.kind === "variable") {
    return environment.get(expression.name);
  }

  const left = evaluate(expression.left, environment);
  const right = evaluate(expression.right, environment);

  switch (expression.operator) {
    case "+":
      return requireNumber(left, "+") + requireNumber(right, "+");
    case "-":
      return requireNumber(left, "-") - requireNumber(right, "-");
    case "*":
      return requireNumber(left, "*") * requireNumber(right, "*");
    case "/": {
      requireNumber(left, "/");
      requireNumber(right, "/");
      if (right === 0) {
        throw new ExecutionError("Division by zero");
      }
      return left / right;
    }
    case "<":
      return requireNumber(left, "<") < requireNumber(right, "<");
    case "==":
      return typeof left === typeof right && left === right;
    case "!=":
      return typeof left !== typeof right || left !== right;
    case "<=":
      return requireNumber(left, "<=") <= requireNumber(right, "<=");
    case ">=":
      return requireNumber(left, ">=") >= requireNumber(right, ">=");
    default:
      throw new ExecutionError(`Unknown operator '${expression.operator}'`);
  }
}

function interpret(statements, output = [], fuel = { remaining: 10000 }) {
  const globalEnvironment = new Environment();

  function tick() {
    fuel.remaining -= 1;
    if (fuel.remaining < 0) {
      throw new ExecutionError("Interpreter execution budget exhausted");
    }
  }

  function execute(statement, environment) {
    tick();

    switch (statement.kind) {
      case "declare":
        environment.declare(
          statement.name,
          evaluate(statement.value, environment)
        );
        break;

      case "assign":
        environment.assign(
          statement.name,
          evaluate(statement.value, environment)
        );
        break;

      case "print":
        output.push(String(evaluate(statement.value, environment)));
        break;

      case "block": {
        const child = new Environment(environment);
        for (const nested of statement.body) {
          execute(nested, child);
        }
        break;
      }

      case "while":
        while (true) {
          tick();
          const condition = evaluate(statement.condition, environment);
          if (typeof condition !== "boolean") {
            throw new ExecutionError("while condition must be Boolean");
          }
          if (!condition) {
            break;
          }
          execute(statement.body, environment);
        }
        break;

      default:
        throw new ExecutionError(`Unknown statement '${statement.kind}'`);
    }
  }

  for (const statement of statements) {
    execute(statement, globalEnvironment);
  }

  return output;
}

class Emitter {
  constructor() {
    this.code = [];
  }

  emit(op, argument = null) {
    this.code.push({ op, argument });
    return this.code.length - 1;
  }

  patch(index, target) {
    this.code[index].argument = target;
  }

  compile(statements) {
    for (const statement of statements) {
      this.statement(statement);
    }
    this.emit(OPCODES.HALT);
    return this.code;
  }

  statement(node) {
    switch (node.kind) {
      case "declare":
      case "assign":
        this.expression(node.value);
        this.emit(OPCODES.STORE, node.name);
        break;

      case "print":
        this.expression(node.value);
        this.emit(OPCODES.PRINT);
        break;

      case "block":
        for (const child of node.body) {
          this.statement(child);
        }
        break;

      case "while": {
        const start = this.code.length;
        this.expression(node.condition);
        const exit = this.emit(OPCODES.JUMP_IF_FALSE, null);
        this.statement(node.body);
        this.emit(OPCODES.JUMP, start);
        this.patch(exit, this.code.length);
        break;
      }

      default:
        throw new CompileError(`Cannot compile '${node.kind}'`);
    }
  }

  expression(node) {
    if (node.kind === "constant") {
      this.emit(OPCODES.CONST, node.value);
      return;
    }

    if (node.kind === "variable") {
      this.emit(OPCODES.LOAD, node.name);
      return;
    }

    this.expression(node.left);
    this.expression(node.right);

    const mapping = {
      "+": OPCODES.ADD,
      "*": OPCODES.MUL,
      "/": OPCODES.DIV,
      "<": OPCODES.LT
    };

    const opcode = mapping[node.operator];
    if (!opcode) {
      throw new CompileError(
        `Bytecode backend does not support '${node.operator}'`
      );
    }

    this.emit(opcode);
  }
}

/*
 * Static verification catches malformed jump targets and missing HALT.
 * It is a structural verifier, not a complete proof of stack correctness.
 */
function verifyBytecode(code) {
  if (code.length === 0 || code[code.length - 1].op !== OPCODES.HALT) {
    throw new VerificationError("Bytecode must end with HALT");
  }

  const known = new Set(Object.values(OPCODES));

  for (let index = 0; index < code.length; index++) {
    const instruction = code[index];

    if (!known.has(instruction.op)) {
      throw new VerificationError(
        `Unknown opcode at instruction ${index}`
      );
    }

    if (
      instruction.op === OPCODES.JUMP ||
      instruction.op === OPCODES.JUMP_IF_FALSE
    ) {
      if (
        !Number.isInteger(instruction.argument) ||
        instruction.argument < 0 ||
        instruction.argument >= code.length
      ) {
        throw new VerificationError(
          `Invalid jump target at instruction ${index}`
        );
      }
    }
  }

  return true;
}

class BytecodeVM {
  constructor(code, { fuel = 10000, trace = false } = {}) {
    verifyBytecode(code);
    this.code = code;
    this.fuel = fuel;
    this.trace = trace;
    this.ip = 0;
    this.stack = [];
    this.environment = new Map();
    this.output = [];
  }

  pop() {
    if (this.stack.length === 0) {
      throw new ExecutionError(
        `Stack underflow at instruction ${this.ip - 1}`
      );
    }
    return this.stack.pop();
  }

  numericBinary(operation) {
    const right = requireNumber(this.pop(), operation);
    const left = requireNumber(this.pop(), operation);
    this.stack.push(operation(left, right));
  }

  run() {
    while (this.ip < this.code.length) {
      if (--this.fuel < 0) {
        throw new ExecutionError("Virtual-machine fuel exhausted");
      }

      const current = this.ip;
      const instruction = this.code[this.ip++];

      if (this.trace) {
        console.log({
          ip: current,
          instruction,
          stack: [...this.stack]
        });
      }

      switch (instruction.op) {
        case OPCODES.HALT:
          return this.output;

        case OPCODES.CONST:
          this.stack.push(instruction.argument);
          break;

        case OPCODES.LOAD:
          if (!this.environment.has(instruction.argument)) {
            throw new ExecutionError(
              `Undefined variable '${instruction.argument}'`
            );
          }
          this.stack.push(this.environment.get(instruction.argument));
          break;

        case OPCODES.STORE:
          this.environment.set(instruction.argument, this.pop());
          break;

        case OPCODES.PRINT:
          this.output.push(String(this.pop()));
          break;

        case OPCODES.ADD:
          this.numericBinary((a, b) => a + b);
          break;

        case OPCODES.MUL:
          this.numericBinary((a, b) => a * b);
          break;

        case OPCODES.DIV:
          this.numericBinary((a, b) => {
            if (b === 0) {
              throw new ExecutionError("Division by zero");
            }
            return a / b;
          });
          break;

        case OPCODES.LT: {
          const right = requireNumber(this.pop(), "<");
          const left = requireNumber(this.pop(), "<");
          this.stack.push(left < right);
          break;
        }

        case OPCODES.JUMP:
          this.ip = instruction.argument;
          break;

        case OPCODES.JUMP_IF_FALSE: {
          const condition = this.pop();
          if (typeof condition !== "boolean") {
            throw new ExecutionError("Conditional jump requires Boolean");
          }
          if (!condition) {
            this.ip = instruction.argument;
          }
          break;
        }

        default:
          throw new ExecutionError(
            `Unsupported opcode '${instruction.op}'`
          );
      }
    }

    throw new ExecutionError("Program terminated without HALT");
  }
}

function compile(source) {
  const ast = new Parser(tokenize(source)).parse();
  analyze(ast);
  const code = new Emitter().compile(ast);
  verifyBytecode(code);
  return code;
}

/*
 * Promise-based compilation is useful in applications that compile user
 * scripts without blocking an event handler while other work is scheduled.
 * This example schedules compilation asynchronously but does not claim that
 * CPU-heavy compilation runs in a separate thread.
 */
async function compileAsync(source) {
  await Promise.resolve();
  return compile(source);
}

function expectFailure(description, action) {
  try {
    action();
  } catch (error) {
    console.log(`${description}: ${error.name}: ${error.message}`);
    return;
  }
  throw new Error(`Expected failure: ${description}`);
}

async function main() {
  const source = `
    let completed = 0;
    let jobs = 4;

    while (jobs > 0) {
      completed = completed + jobs;
      jobs = jobs - 1;
    }

    print completed;
    print completed / 2;
  `;

  const ast = new Parser(tokenize(source)).parse();
  analyze(ast);

  const interpreted = interpret(ast);
  const code = await compileAsync(source);
  const compiled = new BytecodeVM(code).run();

  console.log("Direct interpreter:", interpreted);
  console.log("Compiled bytecode:", compiled);
  console.log("Bytecode instructions:", code);
  console.assert(
    JSON.stringify(interpreted) === JSON.stringify(compiled),
    "Interpreter and VM outputs differ"
  );

  console.log("Traced execution:");
  new BytecodeVM(code, { trace: true }).run();

  expectFailure("Unknown identifier", () => compile("print secret;"));
  expectFailure("Invalid source character", () => tokenize("print @;"));
  expectFailure(
    "Division by zero",
    () => new BytecodeVM(compile("let x = 4 / 0; print x;")).run()
  );
  expectFailure(
    "Malformed bytecode",
    () => verifyBytecode([{ op: OPCODES.JUMP, argument: 500 }])
  );
  expectFailure(
    "Infinite loop protection",
    () => new BytecodeVM(
      compile("while (true) {}"),
      { fuel: 20 }
    ).run()
  );

  console.log("JavaScript compiler/runtime laboratory completed.");
}

main().catch((error) => {
  console.error(`${error.name}: ${error.message}`);
  process.exitCode = 1;
});
