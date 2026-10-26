"use strict";

/*
 * Stack applications:
 *   1. Basic LIFO operations
 *   2. Balanced-delimiter validation
 *   3. Infix-to-postfix conversion
 *   4. Postfix evaluation
 *   5. Monotonic-stack next-greater-element processing
 *   6. Event-driven browser-history simulation
 *
 * Node.js 18+ is sufficient; no external packages are required.
 */

class StackError extends Error {}
class StackUnderflowError extends StackError {}
class StackOverflowError extends StackError {}
class InvalidExpressionError extends StackError {}

class Stack {
  constructor(capacity = null) {
    if (capacity !== null && (!Number.isInteger(capacity) || capacity <= 0)) {
      throw new RangeError("capacity must be a positive integer");
    }

    this.items = [];
    this.capacity = capacity;
  }

  push(value) {
    if (this.capacity !== null && this.items.length >= this.capacity) {
      throw new StackOverflowError("stack capacity reached");
    }
    this.items.push(value);
  }

  pop() {
    if (this.items.length === 0) {
      throw new StackUnderflowError("cannot pop from an empty stack");
    }
    return this.items.pop();
  }

  peek() {
    if (this.items.length === 0) {
      throw new StackUnderflowError("cannot peek at an empty stack");
    }
    return this.items[this.items.length - 1];
  }

  isEmpty() {
    return this.items.length === 0;
  }

  size() {
    return this.items.length;
  }

  clear() {
    this.items.length = 0;
  }

  toArray() {
    return [...this.items];
  }
}

const PRECEDENCE = Object.freeze({
  "u-": 4,
  "^": 3,
  "*": 2,
  "/": 2,
  "%": 2,
  "+": 1,
  "-": 1
});

const RIGHT_ASSOCIATIVE = new Set(["^", "u-"]);

function tokenize(expression) {
  if (typeof expression !== "string" || expression.trim() === "") {
    throw new InvalidExpressionError("expression must be a non-empty string");
  }

  const tokens = [];
  let i = 0;
  let expectOperand = true;

  while (i < expression.length) {
    const ch = expression[i];

    if (/\s/.test(ch)) {
      i++;
      continue;
    }

    if (/[0-9.]/.test(ch)) {
      const start = i;
      let dots = 0;
      let digits = 0;

      while (i < expression.length && /[0-9.]/.test(expression[i])) {
        if (expression[i] === ".") dots++;
        else digits++;
        i++;
      }

      const value = expression.slice(start, i);

      if (dots > 1 || digits === 0) {
        throw new InvalidExpressionError(`invalid number: ${value}`);
      }

      tokens.push({ type: "number", value });
      expectOperand = false;
      continue;
    }

    if (ch === "(") {
      tokens.push({ type: "leftParen", value: ch });
      expectOperand = true;
      i++;
      continue;
    }

    if (ch === ")") {
      if (expectOperand) {
        throw new InvalidExpressionError("unexpected closing parenthesis");
      }

      tokens.push({ type: "rightParen", value: ch });
      expectOperand = false;
      i++;
      continue;
    }

    if ("+-*/%^".includes(ch)) {
      if (ch === "-" && expectOperand) {
        tokens.push({ type: "operator", value: "u-" });
      } else if (expectOperand) {
        throw new InvalidExpressionError(`unexpected operator: ${ch}`);
      } else {
        tokens.push({ type: "operator", value: ch });
        expectOperand = true;
      }

      i++;
      continue;
    }

    throw new InvalidExpressionError(`unsupported character: ${ch}`);
  }

  if (tokens.length === 0 || expectOperand) {
    throw new InvalidExpressionError("incomplete expression");
  }

  return tokens;
}

function infixToPostfix(expression) {
  const tokens = tokenize(expression);
  const output = [];
  const operators = new Stack();

  for (const token of tokens) {
    if (token.type === "number") {
      output.push(token.value);
      continue;
    }

    if (token.type === "leftParen") {
      operators.push(token.value);
      continue;
    }

    if (token.type === "rightParen") {
      while (!operators.isEmpty() && operators.peek() !== "(") {
        output.push(operators.pop());
      }

      if (operators.isEmpty()) {
        throw new InvalidExpressionError("unmatched closing parenthesis");
      }

      operators.pop();
      continue;
    }

    const current = token.value;

    while (
      !operators.isEmpty() &&
      operators.peek() !== "(" &&
      (
        PRECEDENCE[operators.peek()] > PRECEDENCE[current] ||
        (
          PRECEDENCE[operators.peek()] === PRECEDENCE[current] &&
          !RIGHT_ASSOCIATIVE.has(current)
        )
      )
    ) {
      output.push(operators.pop());
    }

    operators.push(current);
  }

  while (!operators.isEmpty()) {
    const op = operators.pop();

    if (op === "(") {
      throw new InvalidExpressionError("unmatched opening parenthesis");
    }

    output.push(op);
  }

  return output;
}

function evaluatePostfix(postfix) {
  const values = new Stack();

  for (const token of postfix) {
    if (!(token in PRECEDENCE)) {
      const value = Number(token);

      if (!Number.isFinite(value)) {
        throw new InvalidExpressionError(`invalid numeric token: ${token}`);
      }

      values.push(value);
      continue;
    }

    if (token === "u-") {
      values.push(-values.pop());
      continue;
    }

    const right = values.pop();
    const left = values.pop();

    if ((token === "/" || token === "%") && right === 0) {
      throw new InvalidExpressionError("division or modulo by zero");
    }

    let result;

    switch (token) {
      case "+":
        result = left + right;
        break;
      case "-":
        result = left - right;
        break;
      case "*":
        result = left * right;
        break;
      case "/":
        result = left / right;
        break;
      case "%":
        result = left % right;
        break;
      case "^":
        result = left ** right;
        break;
      default:
        throw new InvalidExpressionError(`unknown operator: ${token}`);
    }

    if (!Number.isFinite(result)) {
      throw new InvalidExpressionError("non-finite arithmetic result");
    }

    values.push(result);
  }

  if (values.size() !== 1) {
    throw new InvalidExpressionError("malformed postfix expression");
  }

  return values.pop();
}

function evaluateExpression(expression) {
  return evaluatePostfix(infixToPostfix(expression));
}

function balancedDelimiters(text) {
  const stack = new Stack();
  const pairs = new Map([
    [")", "("],
    ["]", "["],
    ["}", "{"]
  ]);

  for (const char of text) {
    if ("([{".includes(char)) {
      stack.push(char);
    } else if (")]}".includes(char)) {
      if (stack.isEmpty() || stack.pop() !== pairs.get(char)) {
        return false;
      }
    }
  }

  return stack.isEmpty();
}

function nextGreaterElements(values) {
  const result = new Array(values.length).fill(-1);
  const indices = new Stack();

  for (let i = 0; i < values.length; i++) {
    while (
      !indices.isEmpty() &&
      values[indices.peek()] < values[i]
    ) {
      result[indices.pop()] = values[i];
    }

    indices.push(i);
  }

  return result;
}

class BrowserHistory {
  constructor(homePage) {
    if (typeof homePage !== "string" || homePage.length === 0) {
      throw new TypeError("homePage must be a non-empty string");
    }

    this.backStack = new Stack();
    this.forwardStack = new Stack();
    this.current = homePage;
  }

  visit(page) {
    if (typeof page !== "string" || page.length === 0) {
      throw new TypeError("page must be a non-empty string");
    }

    this.backStack.push(this.current);
    this.current = page;
    this.forwardStack.clear();
  }

  back() {
    if (!this.backStack.isEmpty()) {
      this.forwardStack.push(this.current);
      this.current = this.backStack.pop();
    }
    return this.current;
  }

  forward() {
    if (!this.forwardStack.isEmpty()) {
      this.backStack.push(this.current);
      this.current = this.forwardStack.pop();
    }
    return this.current;
  }

  state() {
    return {
      current: this.current,
      back: this.backStack.toArray(),
      forward: this.forwardStack.toArray()
    };
  }
}

class StackEventProcessor {
  constructor() {
    this.handlers = new Map();
  }

  on(eventName, handler) {
    if (typeof handler !== "function") {
      throw new TypeError("event handler must be a function");
    }

    if (!this.handlers.has(eventName)) {
      this.handlers.set(eventName, []);
    }

    this.handlers.get(eventName).push(handler);
  }

  async emit(eventName, payload) {
    const handlers = this.handlers.get(eventName) ?? [];

    // Sequential execution makes state-changing handlers deterministic.
    for (const handler of handlers) {
      await handler(payload);
    }
  }
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
}

async function runTests() {
  const stack = new Stack(2);
  stack.push(10);
  stack.push(20);

  try {
    stack.push(30);
    throw new Error("overflow not detected");
  } catch (error) {
    assert(error instanceof StackOverflowError, "overflow type");
  }

  assert(stack.pop() === 20, "LIFO pop");
  assert(stack.peek() === 10, "peek");

  assert(balancedDelimiters("{[()]}"), "balanced delimiters");
  assert(!balancedDelimiters("{[(])}"), "unbalanced delimiters");

  assert(
    JSON.stringify(nextGreaterElements([4, 5, 2, 10, 8])) ===
    JSON.stringify([5, 10, 10, -1, -1]),
    "next greater elements"
  );

  const cases = new Map([
    ["2 + 3 * 4", 14],
    ["(2 + 3) * 4", 20],
    ["2 ^ 3 ^ 2", 512],
    ["-2 * (3 + 4)", -14],
    ["10 % 3", 1],
    ["2 * -3 + 10", 4]
  ]);

  for (const [expression, expected] of cases) {
    assert(
      Math.abs(evaluateExpression(expression) - expected) < 1e-10,
      `expression: ${expression}`
    );
  }

  for (const expression of ["2 / 0", "(2 + 3", "2 +", "2 & 3"]) {
    try {
      evaluateExpression(expression);
      throw new Error(`invalid expression accepted: ${expression}`);
    } catch (error) {
      assert(error instanceof InvalidExpressionError, "invalid expression type");
    }
  }

  const history = new BrowserHistory("home");
  history.visit("products");
  history.visit("stacks");
  assert(history.back() === "products", "history back");
  assert(history.forward() === "stacks", "history forward");

  const events = [];
  const processor = new StackEventProcessor();
  processor.on("push", async value => events.push(`push:${value}`));
  processor.on("push", async value => events.push(`audit:${value}`));
  await processor.emit("push", 42);

  assert(events.join("|") === "push:42|audit:42", "event processing");
}

async function main() {
  await runTests();

  console.log("STACK OPERATIONS");
  const stack = new Stack();
  ["compile", "test", "package"].forEach(item => stack.push(item));
  console.log("top:", stack.peek());
  console.log("pop:", stack.pop());
  console.log("remaining:", stack.toArray());

  console.log("\nBALANCED DELIMITERS");
  console.log("{[()]} ->", balancedDelimiters("{[()]}"));
  console.log("{[(])} ->", balancedDelimiters("{[(])}"));

  console.log("\nMONOTONIC STACK");
  const values = [4, 5, 2, 10, 8];
  console.log("values:", values);
  console.log("next greater:", nextGreaterElements(values));

  console.log("\nEXPRESSION EVALUATION");
  for (const expression of [
    "3 + 4 * 2 / (1 - 5) ^ 2",
    "-2 ^ 3 + 10",
    "(15 % 4) * (2 + 6)"
  ]) {
    const postfix = infixToPostfix(expression);
    console.log(
      `${expression} -> ${postfix.join(" ")} -> ${evaluatePostfix(postfix)}`
    );
  }

  console.log("\nEVENT-DRIVEN STACK WORKFLOW");
  const processor = new StackEventProcessor();
  processor.on("job", async job => {
    console.log(`processing job ${job.id}`);
  });
  processor.on("job", async job => {
    console.log(`audit event for job ${job.id}`);
  });
  await processor.emit("job", { id: "JOB-1042" });

  console.log("\nBROWSER HISTORY");
  const history = new BrowserHistory("home");
  history.visit("catalog");
  history.visit("catalog/stacks");
  history.back();
  history.forward();
  console.log(history.state());

  console.log("\nPerformance: push, pop, and peek are O(1) amortized.");
  console.log("Expression conversion/evaluation and delimiter validation are O(n).");
  console.log("The monotonic-stack algorithm is O(n) because every index is pushed and popped at most once.");
  console.log("Security: reject unsupported tokens, impose input-size limits, and never execute expression text as JavaScript.");
}

main().catch(error => {
  console.error("Fatal error:", error.message);
  process.exitCode = 1;
});
