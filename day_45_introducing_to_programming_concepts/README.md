# Introduction to Programming Concepts

## Scope

Programming is the process of expressing operations and decisions in a formal language that a computer system can execute. Understanding a program requires more than memorizing syntax. A programmer must know how values are represented, how expressions are evaluated, how state changes, how errors arise, and how source code becomes executable behavior.

This repository studies six closely related concepts:

- **Programs:** Instructions and data arranged to perform a defined task.
- **Syntax:** The grammatical rules governing valid source code.
- **Semantics:** The meaning and behavior of valid expressions and statements.
- **Variables:** Names associated with values or storage locations, depending on the language.
- **Data types:** Rules governing values, operations, representation, and permitted conversions.
- **Compilation:** Translation of source code into an intermediate representation or machine-executable form, depending on the language and runtime.

The implementations use different application scenarios so that the concepts are examined through numerical processing, controlled expression evaluation, manufacturing quality assessment, enterprise order processing, and a relational programming-exercise platform.

## Programs, syntax, and semantics

A program is a structured description of computational behavior. Its source text is processed according to the grammar of the programming language.

Consider the expression `2 + 3 * 4`. Its result is `14`, not `20`, because multiplication has higher precedence than addition. The expression `(2 + 3) * 4` produces `20`. Both expressions are syntactically valid, but their different structures produce different results.

Syntax and semantics must be distinguished during debugging.

| Situation | Meaning | Example |
|---|---|---|
| Syntax error | The source violates the language grammar. | `total = 12 +` |
| Runtime error | Execution reaches an operation that cannot complete. | Division by zero |
| Semantic defect | The program executes but produces an unintended result. | Applying tax before a discount when the business policy requires the reverse |
| Validation failure | Input violates a defined domain rule. | A negative order quantity |
| Test failure | Actual behavior differs from expected behavior. | Expected `14`, received `20` |

These failure types require different responses. A parser cannot determine whether a syntactically valid business calculation follows the intended pricing policy. That requires domain rules and tests.

## Variables and data types

A variable provides a name through which a program refers to a value or state.

Python names are bound to objects, and type annotations communicate intended usage without ordinarily enforcing types at runtime. JavaScript variables refer to dynamically typed values. C++ declarations participate in static type checking and influence storage and operation selection. Java combines static typing with runtime object behavior.

The distinction affects how invalid operations are discovered.

| Language | Typical typing model | Important consequence |
|---|---|---|
| Python | Dynamic typing | An operation may fail at runtime even when a variable has an annotation. |
| JavaScript | Dynamic typing with coercion | Strict comparisons and explicit input validation reduce unexpected conversions. |
| C++ | Static typing | The compiler rejects many incompatible operations before execution, although runtime validation remains necessary. |
| Java | Static typing | Declared domain types and access control make invalid states easier to constrain. |
| PostgreSQL | Typed columns and constraints | Data integrity rules can reject invalid records even when application code has a defect. |

A type is not merely a label. It influences which operations are meaningful and how values are represented. For example, a Boolean value and an integer may behave similarly in some contexts, but treating them as interchangeable can violate an application's input contract.

### Numeric representation

Binary floating-point cannot exactly represent every decimal fraction. Financial calculations that require reproducible decimal rounding should therefore use an appropriate representation.

The Python implementation calculates an invoice in integer paise. The Java implementation uses `BigDecimal` with explicit rounding. These choices avoid treating a binary floating-point approximation as an exact monetary amount.

The C++ manufacturing case study uses floating-point measurements because temperature deviations and pressure tolerances are measured quantities. It validates finiteness before comparing readings. The appropriate representation depends on the domain, not merely on the convenience of a language's default numeric type.

## Expressions, control flow, and functions

Expressions combine values and operations to produce results. Statements control execution, create assignments, select branches, and repeat work.

The Python script calculates a tax-inclusive invoice, classifies scores, validates input, and evaluates restricted arithmetic expressions. The JavaScript program models project-state transitions and processes work items asynchronously. The C++ case study applies independent quality checks to manufacturing batches. The Java program uses an order-processing state machine to enforce business sequencing.

Functions establish boundaries around behavior. A function that validates its arguments before calculating a result has a clearer contract than one that accepts arbitrary values and fails unpredictably.

The Python `calculate_rectangle_area` function rejects negative or non-finite dimensions. The Java `Order.price` method accepts an order only after validation. These are examples of domain-specific contracts, not merely language syntax.

## Compilation and execution

Source code typically passes through several stages before its behavior becomes observable.

A simplified execution pipeline is:

Source text → lexical analysis → parsing → semantic checks → translation or interpretation → execution → observable results

The exact stages vary by language implementation.

### Python

The Python script parses source into an abstract syntax tree using `ast.parse`, creates a code object using `compile`, and executes a controlled example. Python commonly compiles source into bytecode that its runtime executes. The generated bytecode and its instructions are implementation details, so they should not be assumed to remain identical across Python versions.

### JavaScript

Node.js parses JavaScript and executes it through its runtime. Modern JavaScript engines may interpret code, compile it to machine code, and optimize frequently executed paths. These internal stages are implementation-dependent.

The JavaScript program also demonstrates asynchronous work using promises and `async`/`await`. This is an execution model concern: asynchronous completion and error propagation must be handled explicitly even when source syntax is valid.

### C++

C++ source is normally processed by a compiler and linker to produce an executable. The manufacturing program can be built with a C++17 compiler using warnings enabled. Static type checking, compilation diagnostics, and linking errors identify different classes of defects before or during the build process.

### Java

The Java source is compiled into JVM class files and executed by a Java Virtual Machine. The JVM may interpret bytecode or compile frequently executed code at runtime. The order-processing model relies on Java's static types, records, enums, collections, and exception handling to express domain constraints.

### PostgreSQL

SQL is a declarative language. The database parses statements, validates object references and types, and plans and executes queries. The SQL script uses DDL to define the data model and DML to record programming-exercise activity. Constraints and triggers enforce selected invariants inside the database.

Compilation and execution are therefore not identical across all five programming languages and SQL. Each environment has its own translation, validation, execution, and error-reporting mechanisms.

## Python implementation

The Python program progresses from basic assignments to validation, object modeling, a restricted expression interpreter, compilation, and automated tests.

### Syntax and runtime behavior

`demonstrate_syntax_and_semantics` parses valid source and intentionally invalid source. It separately executes an expression that raises `ZeroDivisionError`. This illustrates why syntactic validity does not guarantee successful execution.

### Data validation and domain modeling

The script uses `CourseResult` to represent a student's score. The frozen dataclass prevents ordinary field reassignment after construction, while `__post_init__` enforces a non-empty name and a finite score between zero and one hundred.

The `summarize_scores` function rejects Boolean values, non-numeric entries, non-finite values, and scores outside the allowed range. Its explicit validation is important because Python annotations alone do not enforce these restrictions.

### Restricted expression interpreter

`evaluate_arithmetic` uses Python's AST parser to recognize a deliberately small arithmetic language. It supports numeric literals, unary signs, addition, subtraction, multiplication, division, and exponentiation.

It does not execute arbitrary Python expressions. Names, function calls, attribute access, imports, and other unsupported syntax are rejected. Limits on input length, nesting depth, exponent magnitude, and result size reduce accidental resource exhaustion.

This is a useful distinction between parsing and evaluating. A language parser can recognize an expression without authorizing every operation that the host language supports.

The interpreter is educational rather than a complete production sandbox. Applications that process hostile input still need resource limits, process isolation where appropriate, and careful handling of denial-of-service risks.

### Compilation and tests

`demonstrate_compilation_stages` uses `ast.parse` and `compile`, then executes the resulting code object. The `dis` module exposes bytecode instructions for inspection.

The unit tests check arithmetic, invoice calculations, validation, score boundaries, and expression rejection. The script exits unsuccessfully if a test fails, making failures visible to automated execution environments.

## JavaScript implementation

The JavaScript file emphasizes dynamic values, coercion, closures, state transitions, tokenization, parsing, and asynchronous processing.

### Coercion and validation

The program contrasts `===` with `==`. Strict equality avoids implicit type conversion during comparison. The coercive comparison is intentionally included to show how two differently typed values can compare as equal.

`Number.isFinite` is used to validate numeric inputs. This avoids accepting values such as `NaN` and positive infinity as legitimate project costs.

### Closures and controlled state

`createBudgetTracker` retains its budget in a closure. Callers can request the remaining budget or spend an amount, but they cannot directly assign to the internal variable.

The returned interface is frozen to prevent reassignment of its exposed methods. The closure provides the meaningful protection of the budget value itself.

### Object state transitions

The `Project` class permits a project to move from `planned` to `in_progress` and then to `completed`. Invalid transitions throw errors.

This model demonstrates why state-changing operations should validate the current state rather than simply overwrite a status field. Real systems may need additional protections against concurrent changes and unauthorized transitions.

### Tokenization and parsing

The arithmetic evaluator tokenizes only numbers and selected operators. Its parser uses separate functions for precedence levels so multiplication binds more tightly than addition. Exponentiation is right-associative.

The implementation rejects arbitrary identifiers, function calls, unsupported symbols, division by zero, excessive nesting, and non-finite results. It deliberately avoids `eval`, which would execute general JavaScript source instead of restricting input to arithmetic.

The parser demonstrates an important limitation: accepting a small expression grammar does not make an unrestricted host-language evaluator safe. Security depends on limiting the accepted syntax and operations.

### Asynchronous execution

`processWorkItems` uses `Promise.all` to process independent work items and then sorts the results by identifier. If an item fails validation, the returned promise rejects and the caller handles the error.

The example does not simulate a network request. Its purpose is to show promise aggregation, asynchronous function contracts, and error propagation without unnecessary external services.

## C++ case study: manufacturing quality assessment

The C++ program models a production facility that assesses batches using defect rates, temperature deviations, and pressure deviations.

### Architecture

`ProductionBatch` represents the observed production data. `MachineParameters` groups related measurements. `QualityPolicy` owns the acceptance thresholds and evaluates a batch. `BatchAssessment` records the computed metrics, final classification, and findings. `ProductionReport` aggregates assessments.

This separation prevents report formatting from becoming entangled with validation and policy evaluation.

### Algorithms and data structures

For a batch with \(d\) defective units out of \(n\) produced units, the defect percentage is

\[
\text{Defect rate} = \frac{d}{n} \times 100
\]

The implementation requires \(n > 0\) and \(0 \leq d \leq n\), making the calculation well-defined.

Temperature and pressure deviations are absolute differences between measured and target values. Defect violations cause rejection, while out-of-tolerance machine readings require inspection unless the batch is already rejected.

A `std::map` stores assessments by batch identifier. Insertion and lookup take logarithmic time in the number of records, and iteration produces keys in sorted order. For very large reports, storage, indexing, and aggregation requirements would determine whether a different data structure is preferable.

### Error handling and design trade-offs

The program rejects empty identifiers, impossible defect counts, non-finite measurements, non-positive pressure, duplicate assessments, and invalid policy thresholds.

Exceptions communicate invalid input or state to the caller. The main function catches failures and returns a non-zero exit status for an unexpected fatal error.

The policy uses floating-point tolerances for physical measurements. Real manufacturing systems would also need calibrated instruments, units of measurement, traceable timestamps, versioned policies, and durable audit records. Those operational requirements are distinct from the language mechanisms shown in the example.

## Java implementation: enterprise order processing

The Java program models an order moving through validation, pricing, approval, or rejection.

### Domain model

The `Product`, `OrderLine`, `PricingPolicy`, and `Invoice` records represent data with explicit types. Their compact constructors validate required values and numeric ranges.

The `Order` class owns mutable lifecycle state and exposes controlled operations. Its lines are copied with `List.copyOf`, preventing callers from modifying the collection through a reference supplied during construction.

The `OrderStatus` enum prevents arbitrary status strings from becoming valid application states.

### Pricing semantics

The subtotal is the sum of each product price multiplied by its quantity. If the subtotal reaches the configured threshold, the policy applies a percentage discount. Tax is calculated on the discounted amount and rounded to two decimal places using `RoundingMode.HALF_UP`.

The sequence is significant because changing the order of discount and tax calculations can change the total.

`BigDecimal` is appropriate for these monetary calculations, provided values are constructed from decimal strings or other exact representations rather than imprecise binary floating-point values.

### State transitions and failures

An order must be created before validation, validated before pricing, and priced before approval. Rejected orders are terminal in this example.

The methods are synchronized to prevent concurrent callers from interleaving their state checks and transitions on the same object. This is an in-memory demonstration, not a substitute for database transactions or distributed concurrency control.

The status aggregation uses streams and grouping to count orders by state. This separates reporting from the methods that enforce order behavior.

## SQL implementation: a programming-exercise platform

The PostgreSQL schema records learners, exercises, submissions, execution attempts, and test results.

### Relational model

| Table | Responsibility |
|---|---|
| `learners` | Stores learner identities and unique email addresses. |
| `exercises` | Defines exercises, their programming concept, and expected output. |
| `submissions` | Stores source text, language, learner, exercise, and submission time. |
| `execution_attempts` | Records the runtime or compiler, attempt state, and execution errors. |
| `test_results` | Stores individual expected and actual values with pass or failure outcomes. |

Foreign keys prevent submissions from referencing nonexistent learners or exercises. Unique constraints prevent duplicate attempt numbers within a submission and duplicate test names within an attempt.

Check constraints enforce non-empty source text, supported concepts, valid attempt numbers, consistent timestamps, and required details for failure states.

### Execution state versus correctness

The `execution_state` enum distinguishes submission, syntax failure, compilation, runtime failure, and completion.

A completed attempt is not necessarily a correct program. The program may terminate successfully and still produce the wrong answer. Test results therefore exist separately from execution attempts.

The reporting queries preserve this distinction by reporting execution state alongside recorded test outcomes.

### Triggers and transactions

The `enforce_attempt_transition` trigger restricts execution-state changes and requires error details for syntax and runtime failures. Terminal failures and completed attempts cannot be rewritten into other states.

The demonstration attempts an invalid state transition within a protected savepoint. The trigger raises an exception, and the nested exception handler reports the failure without discarding the entire demonstration.

This illustrates database-level enforcement. Application validation remains useful for clear user-facing errors, but database constraints protect stored data when several applications or concurrent sessions access the same records.

### Indexes and reporting

The learner activity index supports queries that retrieve a learner's recent submissions. The execution index supports lookups by submission and state. The partial index on failed tests targets queries that focus on failures.

The `exercise_outcomes` view aggregates submission counts, syntax failures, runtime failures, completed attempts, and test results by exercise. These metrics allow educators to distinguish parsing problems from execution problems and incorrect program behavior.

The indexes should be evaluated against actual query plans and data volumes. Indexes consume storage and increase write costs, so adding indexes without a demonstrated query need can make a database less efficient.

## Common failure modes and their implications

### Confusing syntax with meaning

A program that parses successfully can still calculate the wrong result. Explicit expected values and boundary-focused tests help detect semantic defects.

### Assuming declarations enforce all runtime rules

Python annotations and JavaScript naming conventions do not automatically enforce every domain restriction. Validation must occur at the relevant input boundary.

### Ignoring conversion and precision

Implicit coercion can produce surprising comparisons, while binary floating-point can produce small decimal discrepancies. Explicit conversion and domain-appropriate numeric types make calculations more predictable.

### Treating successful execution as correctness

A process can finish without an exception and still return an incorrect result. Test assertions and expected-versus-actual comparisons address this separate property.

### Allowing invalid state changes

Repeated transitions can violate business assumptions even when every individual statement is syntactically valid. State machines and transition checks prevent operations that do not belong in the current state.

### Validating only in the application

When data is persisted, application-only validation leaves integrity dependent on every caller implementing the same rules correctly. Relational constraints and triggers provide a second enforcement boundary.

## Performance and production considerations

Performance depends on the workload and the selected representation. A simple arithmetic calculation is generally constant-time, while sorting a list of \(n\) records typically requires \(O(n \log n)\) time. Repeated linear searches can become expensive as collections grow.

The expression interpreters impose bounds on source length and nesting to limit resource consumption. More complete evaluators would also need careful limits on operation counts and intermediate values.

Production systems require consistent input contracts, explicit error reporting, tests for boundary conditions, structured logs, and clear separation between computation and presentation. Persisted business operations also need transaction boundaries, authorization, auditability, and appropriate concurrency controls.

These mechanisms serve different purposes: syntax rules define valid source, types constrain operations, semantic rules determine behavior, compilation and runtime systems execute the program, and validation and tests establish whether the observed behavior satisfies the application's requirements.
