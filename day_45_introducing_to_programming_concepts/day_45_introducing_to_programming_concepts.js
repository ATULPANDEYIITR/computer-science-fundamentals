"use strict";

/*
 * Introduction to Programming Concepts
 *
 * Demonstrates JavaScript program execution, syntax and semantics, dynamic
 * typing, coercion, closures, validation, asynchronous execution, and the
 * distinction between parsing and safely interpreting arithmetic expressions.
 *
 * Run with Node.js 18 or later:
 *     node programming_concepts.js
 */

const { performance } = require("node:perf_hooks");

function heading(title) {
  console.log(`\n${"=".repeat(68)}\n${title}\n${"=".repeat(68)}`);
}

// A JavaScript expression produces a value; a statement controls execution.
function calculateProjectCost(hours, hourlyRate) {
  if (
    typeof hours !== "number" ||
    typeof hourlyRate !== "number" ||
    !Number.isFinite(hours) ||
    !Number.isFinite(hourlyRate) ||
    hours < 0 ||
    hourlyRate < 0
  ) {
    throw new TypeError("Hours and rate must be finite, non-negative numbers.");
  }

  return hours * hourlyRate;
}

function demonstrateValuesAndCoercion() {
  const employee = "Mira";
  const projectHours = 18;
  const hourlyRate = 725.5;
  const active = true;
  const assignedTasks = ["review pull request", "run tests"];
  const metadata = { team: "Platform", priority: "high" };
  let manager = null;
  let uninitialized;

  console.log({
    employee,
    projectHours,
    hourlyRate,
    active,
    assignedTasks,
    metadata,
    manager,
    uninitialized,
  });

  // JavaScript has both strict equality and coercive equality.
  console.log("5 === '5':", 5 === "5");
  console.log("5 == '5':", 5 == "5"); // Intentional coercion demonstration.

  // NaN is a number-typed value that is not equal to itself.
  console.log("typeof NaN:", typeof NaN);
  console.log("Number.isNaN(NaN):", Number.isNaN(NaN));

  // Use Number.isFinite before accepting numeric input from an API or form.
  console.log("Finite rate:", Number.isFinite(hourlyRate));
  console.log("Cost:", calculateProjectCost(projectHours, hourlyRate));
}

function createBudgetTracker(initialBudget) {
  if (!Number.isSafeInteger(initialBudget) || initialBudget < 0) {
    throw new RangeError("Budget must be a non-negative safe integer.");
  }

  // The closure retains private state without exposing a mutable budget field.
  let remaining = initialBudget;

  return Object.freeze({
    spend(amount) {
      if (!Number.isSafeInteger(amount) || amount <= 0) {
        throw new RangeError("Expense must be a positive safe integer.");
      }
      if (amount > remaining) {
        throw new RangeError("Expense exceeds the remaining budget.");
      }
      remaining -= amount;
      return remaining;
    },
    getRemaining() {
      return remaining;
    },
  });
}

function demonstrateClosuresAndImmutability() {
  const budget = createBudgetTracker(100000);
  console.log("Remaining after deployment:", budget.spend(25000));
  console.log("Remaining after testing:", budget.spend(12000));

  try {
    budget.spend(70000);
  } catch (error) {
    console.log("Budget validation:", error.message);
  }

  // Object.freeze protects this API object's properties. Private closure state
  // is separately protected by not returning the variable itself.
  console.log("Final remaining budget:", budget.getRemaining());
}

class Project {
  constructor(name, owner, deadline) {
    if (typeof name !== "string" || !name.trim()) {
      throw new TypeError("Project name is required.");
    }
    if (typeof owner !== "string" || !owner.trim()) {
      throw new TypeError("Project owner is required.");
    }

    const parsedDeadline = new Date(deadline);
    if (!Number.isFinite(parsedDeadline.getTime())) {
      throw new TypeError("Deadline must be a valid date.");
    }

    this.name = name.trim();
    this.owner = owner.trim();
    this.deadline = parsedDeadline;
    this.status = "planned";
  }

  start() {
    if (this.status !== "planned") {
      throw new Error(`Cannot start a project in state '${this.status}'.`);
    }
    this.status = "in_progress";
  }

  complete() {
    if (this.status !== "in_progress") {
      throw new Error("Only an in-progress project can be completed.");
    }
    this.status = "completed";
  }

  describe() {
    return `${this.name} (${this.status}), owner=${this.owner}, deadline=${this.deadline.toISOString()}`;
  }
}

function demonstrateStateTransitions() {
  const project = new Project(
    "Service Migration",
    "Mira",
    "2026-12-15T00:00:00Z"
  );

  project.start();
  console.log(project.describe());
  project.complete();
  console.log(project.describe());

  try {
    project.start();
  } catch (error) {
    console.log("Invalid state transition:", error.message);
  }
}

// This interpreter accepts only explicitly permitted syntax. It never evaluates
// arbitrary source with eval() or Function(), which could execute hostile code.
const binaryOperations = new Map([
  ["+", (a, b) => a + b],
  ["-", (a, b) => a - b],
  ["*", (a, b) => a * b],
  ["/", (a, b) => {
    if (b === 0) throw new RangeError("Division by zero.");
    return a / b;
  }],
  ["**", (a, b) => {
    if (Math.abs(b) > 100) throw new RangeError("Exponent is too large.");
    return a ** b;
  }],
]);

function tokenizeArithmetic(source) {
  if (typeof source !== "string" || source.trim() === "") {
    throw new SyntaxError("Expression must be a non-empty string.");
  }
  if (source.length > 200) {
    throw new RangeError("Expression exceeds 200 characters.");
  }

  const tokens = [];
  const pattern = /\s*(?:(\d+(?:\.\d+)?)|(\*\*|[()+\-*/]))/y;
  let position = 0;

  while (position < source.length) {
    pattern.lastIndex = position;
    const match = pattern.exec(source);
    if (!match) {
      throw new SyntaxError(`Unsupported character at offset ${position}.`);
    }

    tokens.push(
      match[1] !== undefined
        ? { type: "number", value: Number(match[1]) }
        : { type: "operator", value: match[2] }
    );
    position = pattern.lastIndex;
  }

  return tokens;
}

function evaluateArithmetic(source) {
  const tokens = tokenizeArithmetic(source);
  let position = 0;
  let nesting = 0;

  function peek() {
    return tokens[position];
  }

  function consume(expected) {
    const token = tokens[position];
    if (!token || token.value !== expected) {
      throw new SyntaxError(`Expected '${expected}'.`);
    }
    position += 1;
    return token;
  }

  function parsePrimary() {
    const token = peek();
    if (!token) throw new SyntaxError("Unexpected end of expression.");

    if (token.type === "number") {
      position += 1;
      if (!Number.isFinite(token.value) || token.value > 1e12) {
        throw new RangeError("Numeric literal is out of range.");
      }
      return token.value;
    }

    if (token.value === "+" || token.value === "-") {
      position += 1;
      const value = parsePrimary();
      return token.value === "-" ? -value : value;
    }

    if (token.value === "(") {
      nesting += 1;
      if (nesting > 30) throw new RangeError("Expression nesting is too deep.");
      position += 1;
      const value = parseAdditive();
      consume(")");
      nesting -= 1;
      return value;
    }

    throw new SyntaxError(`Unexpected token '${token.value}'.`);
  }

  // Exponentiation is right-associative: 2 ** 3 ** 2 means 2 ** (3 ** 2).
  function parsePower() {
    const left = parsePrimary();
    if (peek()?.value === "**") {
      position += 1;
      const right = parseUnary();
      return applyOperation("**", left, right);
    }
    return left;
  }

  function parseUnary() {
    const token = peek();
    if (token && (token.value === "+" || token.value === "-")) {
      position += 1;
      const value = parseUnary();
      return token.value === "-" ? -value : value;
    }
    return parsePower();
  }

  function parseMultiplicative() {
    let left = parseUnary();
    while (peek() && ["*", "/"].includes(peek().value)) {
      const operation = peek().value;
      position += 1;
      left = applyOperation(operation, left, parseUnary());
    }
    return left;
  }

  function parseAdditive() {
    let left = parseMultiplicative();
    while (peek() && ["+", "-"].includes(peek().value)) {
      const operation = peek().value;
      position += 1;
      left = applyOperation(operation, left, parseMultiplicative());
    }
    return left;
  }

  function applyOperation(operation, left, right) {
    const implementation = binaryOperations.get(operation);
    if (!implementation) throw new SyntaxError("Unsupported operation.");

    const value = implementation(left, right);
    if (!Number.isFinite(value) || Math.abs(value) > 1e100) {
      throw new RangeError("Expression result is out of range.");
    }
    return value;
  }

  const result = parseAdditive();
  if (position !== tokens.length) {
    throw new SyntaxError(`Unexpected token '${tokens[position].value}'.`);
  }
  return result;
}

function demonstrateParsing() {
  for (const expression of [
    "12 + 8 * 3",
    "(12 + 8) * 3",
    "2 ** 3 ** 2",
    "-15 / 3",
  ]) {
    console.log(`${expression} = ${evaluateArithmetic(expression)}`);
  }

  for (const expression of ["1 / 0", "process.exit()", "2 @ 3", "2 ** 101"]) {
    try {
      console.log(evaluateArithmetic(expression));
    } catch (error) {
      console.log(`Rejected ${JSON.stringify(expression)}: ${error.message}`);
    }
  }
}

// Promise-based work is asynchronous even when the individual operation is
// simple. Await makes dependencies explicit without blocking the event loop.
async function processWorkItems(items) {
  const results = await Promise.all(
    items.map(async (item) => {
      if (!Number.isSafeInteger(item.id) || item.id <= 0) {
        throw new TypeError("Work item IDs must be positive safe integers.");
      }

      // The task is intentionally deterministic; a real application could
      // replace this calculation with an awaited network or filesystem call.
      return {
        id: item.id,
        durationMinutes: item.durationMinutes,
        billableMinutes: Math.ceil(item.durationMinutes / 15) * 15,
      };
    })
  );

  return results.sort((a, b) => a.id - b.id);
}

async function demonstrateAsynchronousExecution() {
  const start = performance.now();
  const results = await processWorkItems([
    { id: 3, durationMinutes: 31 },
    { id: 1, durationMinutes: 17 },
    { id: 2, durationMinutes: 60 },
  ]);

  console.log("Processed work:", results);
  console.log(`Elapsed time: ${(performance.now() - start).toFixed(3)} ms`);

  try {
    await processWorkItems([{ id: -1, durationMinutes: 20 }]);
  } catch (error) {
    console.log("Asynchronous validation failure:", error.message);
  }
}

function runAssertions() {
  const assert = require("node:assert/strict");

  assert.equal(calculateProjectCost(2, 500), 1000);
  assert.throws(() => calculateProjectCost(-1, 500), TypeError);
  assert.equal(evaluateArithmetic("2 + 3 * 4"), 14);
  assert.equal(evaluateArithmetic("2 ** 3 ** 2"), 512);
  assert.throws(() => evaluateArithmetic("1 / 0"), RangeError);
  assert.throws(() => evaluateArithmetic("require('fs')"), SyntaxError);

  const project = new Project("API", "Asha", "2027-01-01");
  project.start();
  assert.equal(project.status, "in_progress");
  assert.throws(() => project.start(), Error);

  console.log("All assertions passed.");
}

async function main() {
  heading("JavaScript Values, Types, and Coercion");
  demonstrateValuesAndCoercion();

  heading("Closures and Controlled State");
  demonstrateClosuresAndImmutability();

  heading("Objects and Valid State Transitions");
  demonstrateStateTransitions();

  heading("Tokenization, Parsing, and Expression Semantics");
  demonstrateParsing();

  heading("Asynchronous Work Processing");
  await demonstrateAsynchronousExecution();

  heading("Executable Assertions");
  runAssertions();
}

main().catch((error) => {
  console.error("Program failed:", error.message);
  process.exitCode = 1;
});
