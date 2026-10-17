# Compilers, Interpreters, Bytecode, and Runtime Environments

## Technical scope

A compiler transforms a program from one representation into another. An interpreter evaluates a program by executing its meaning directly or by driving an intermediate representation. A runtime environment supplies the state and services needed during execution, including variable bindings, operand stacks, memory, error handling, and execution limits.

These mechanisms are related, but they solve different problems. Compilation establishes how a program is represented and prepared for execution. Interpretation defines how its operations are evaluated. Bytecode provides a machine-oriented intermediate representation. The runtime environment maintains the state in which that representation executes.

The implementations use small expression languages to make these boundaries visible. The Python implementation supports statements, expressions, loops, and direct versus compiled execution. The JavaScript implementation explores environment chains, bytecode verification, and asynchronous orchestration. The C++ implementation models a typed policy-evaluation engine. The Java implementation focuses on immutable programs and enterprise deployment-policy evaluation. The PostgreSQL schema records the lifecycle of source programs, compilation results, instructions, runtime contexts, and executions.

## Compilation pipeline

A conventional language implementation separates source processing into stages:

`Source text → Tokens → Syntax tree → Semantic validation → Intermediate representation → Runtime execution`

Each stage establishes properties required by the next stage.

**Lexical analysis** recognizes meaningful units such as identifiers, numeric literals, operators, punctuation, and keywords. The Python lexer records line and column positions so malformed characters can be reported precisely.

**Parsing** verifies that tokens follow the language grammar. Recursive-descent parsing encodes operator precedence through separate parsing methods. Multiplication and division bind more tightly than addition and subtraction, while comparisons bind less tightly than arithmetic operations.

**Semantic analysis** validates meaning beyond grammatical correctness. An expression such as `print missing_value;` can be syntactically valid while referencing an undeclared variable. The semantic analyzers reject such references before execution.

**Intermediate representation** makes execution independent of the original source syntax. The Python and JavaScript compilers emit stack-machine instructions. The C++ and Java programs use explicit instruction and value types to separate policy expressions from runtime evaluation.

**Execution** consumes the compiled representation, maintains an instruction pointer, manipulates an operand stack, and accesses runtime variables. Runtime checks remain necessary because static analysis cannot establish every property of a program.

## Interpreters and compilation are different execution strategies

A tree-walking interpreter traverses syntax-tree nodes and evaluates their operations directly. The Python implementation evaluates `Binary`, `Variable`, `If`, and `While` nodes without first generating bytecode. This is straightforward to inspect and debug because execution follows the structure of the source program.

A bytecode-based implementation first translates the syntax tree into instructions. Its virtual machine then dispatches on opcodes such as `CONSTANT`, `LOAD`, `ADD`, `JUMP_IF_FALSE`, and `HALT`.

| Property | Direct interpretation | Bytecode execution |
|---|---|---|
| Execution input | Syntax tree | Instruction sequence |
| Operation dispatch | AST node types | Opcodes |
| Control flow | Recursive evaluation and loops | Instruction-pointer changes |
| Intermediate storage | AST nodes and environment | Operand stack and environment |
| Typical advantage | Simpler implementation and diagnostics | Reusable intermediate representation and compact operations |
| Typical cost | Repeated tree traversal and node dispatch | Compilation overhead and VM dispatch overhead |

Neither approach is universally faster. A small one-time expression may be cheaper to interpret directly. A repeatedly executed program can justify compilation because the compiled representation can be reused. Native-code compilation can provide further optimization opportunities, but it introduces machine-specific code generation and more demanding correctness requirements.

The Python program runs the same source through its tree-walking interpreter and bytecode virtual machine, then asserts that their observable outputs match. This differential check is useful because two independent execution paths can expose semantic inconsistencies.

## Bytecode and stack-machine execution

Bytecode is an intermediate instruction format designed for execution by a virtual machine or another runtime. It is not necessarily machine code for a physical processor.

Consider the arithmetic expression `4 + 3 * 2`. A stack-based compiler can emit instructions conceptually equivalent to:

- `CONSTANT 4`
- `CONSTANT 3`
- `CONSTANT 2`
- `MULTIPLY`
- `ADD`
- `HALT`

The virtual machine pushes constants onto its operand stack. `MULTIPLY` removes the top two values and pushes their product. `ADD` combines the remaining operands. The resulting stack contains the expression result.

This representation makes evaluation order explicit. The compiler determines instruction order according to expression precedence, while the virtual machine implements the behavior of each opcode.

The instruction pointer identifies the next instruction to execute. Conditional branches remove a Boolean condition from the stack and change the instruction pointer when the condition is false. An unconditional jump implements loop repetition. The Python compiler uses this mechanism to lower `while` statements into a condition check, conditional exit, loop body, and backward jump.

A correct compiler must keep instruction operands consistent with opcode definitions. A `LOAD` operand represents a variable name, while a `CONSTANT` operand represents a literal value. Branch operands identify valid instruction positions. Invalid operands or jump targets must not be trusted simply because an instruction sequence has the expected shape.

## Runtime environments and variable bindings

A runtime environment associates variable names with values. Its design determines how variable lookup, assignment, scope, and lifetime behave.

The Python virtual machine stores bindings in a dictionary. The JavaScript interpreter uses an `Environment` object with a parent reference, allowing nested blocks to resolve variables through a chain of environments. The Java and C++ implementations use typed value representations to reject operations on incompatible values.

Lexical scope determines which bindings are visible at a location in the source program. A child environment can reference values in its parent without copying all parent bindings. Assignment must update the environment that owns the binding rather than accidentally creating a new variable in the child scope.

A production runtime may manage much more than variables. It may include call stacks, heap objects, garbage collection, module loading, exception propagation, native interfaces, thread scheduling, and operating-system resources. These examples intentionally implement only the mechanisms needed by their small languages.

## Python implementation

The Python script provides a complete educational compiler pipeline.

### Lexer and parser

The lexer produces immutable `Token` records containing token type, value, line, and column. It recognizes numeric literals, identifiers, reserved keywords, comparison operators, punctuation, and single-line comments. Invalid characters cause a `LexError` with a source location.

The recursive-descent parser constructs immutable AST nodes. Separate methods encode equality, comparison, additive, multiplicative, unary, and primary expression precedence. Statement parsing handles declarations, assignments, output statements, conditional branches, blocks, and loops.

### Semantic validation

`SemanticAnalyzer` checks variable declarations and references before execution. Block and branch analysis use copied sets of visible names to prevent declarations in a nested branch from becoming visible outside it.

The analyzer is deliberately conservative. It does not prove that every runtime operation is safe, nor does it implement a complete type system. For example, a variable can hold a Boolean or number, so invalid arithmetic can still require runtime detection.

### Direct interpretation and bytecode compilation

`Interpreter` evaluates AST nodes and stores values in a dictionary. It rejects division by zero, nonnumeric arithmetic, invalid conditions, and undefined runtime variables. A step budget prevents an accidental infinite loop from running without bound.

`BytecodeCompiler` translates the same nodes into instructions. It patches conditional and unconditional jump destinations after the relevant instruction positions are known. `VirtualMachine` maintains the instruction pointer, operand stack, runtime environment, output list, and instruction budget.

The demonstration compares the outputs of both execution strategies. It also prints bytecode and optionally traces instruction execution with the current stack state. Failure demonstrations distinguish lexical errors, syntax errors, semantic errors, and runtime errors.

## JavaScript implementation

The JavaScript file emphasizes event-driven integration and environment behavior.

Its tokenizer recognizes source tokens using a sticky regular expression. The sticky flag requires token recognition to begin exactly at the current source offset. When no valid token begins at that position, the lexer reports an error rather than silently skipping unknown input.

The parser and semantic analyzer create and validate a separate syntax representation. The `Environment` class implements parent-linked lexical environments using `Map` objects. Its `resolve` method searches the current environment and then its ancestors. Assignments update the environment that owns the existing binding.

The bytecode emitter converts expressions and statements into instructions. `verifyBytecode` rejects unknown opcodes, missing termination, and invalid jump destinations. This is structural validation; it is not a complete verification of stack types or every possible execution path.

The virtual machine applies an instruction fuel limit. This is particularly important when evaluating externally supplied programs because a valid loop may never terminate. Fuel limits constrain execution work but do not independently provide process isolation, memory quotas, or protection from every denial-of-service attack.

`compileAsync` demonstrates Promise-based asynchronous orchestration. It schedules compilation asynchronously in the JavaScript execution model but does not move CPU-intensive compilation to a worker thread. A genuinely CPU-intensive compiler may require a worker or another execution context to prevent blocking an event loop.

The compiler intentionally supports a smaller operator set than the Python implementation. Its arithmetic bytecode backend accepts only the operations explicitly mapped by the emitter. A source operator recognized by the parser is not automatically supported by every backend.

## C++ case study: a typed policy execution engine

The C++ program models a release-governance service that evaluates a numerical risk score and compares it with a policy threshold.

The risk expression combines the number of changed files and critical findings:

`risk = changed_files * 2 + critical_findings * 10`

A separate expression evaluates whether the result is below a configured threshold. The environment receives the values that a repository analysis service would supply.

### Architecture and data representation

The AST uses polymorphic expression nodes. `NumberExpr`, `BooleanExpr`, `VariableExpr`, and `BinaryExpr` represent distinct expression forms. `std::unique_ptr` expresses exclusive ownership of child nodes, while `std::variant` represents the runtime value as either a number or a Boolean.

The compiler traverses the expression tree and emits a vector of instructions. The virtual machine executes those instructions with an operand stack and an `std::unordered_map` environment. Variable lookup is expected constant time on average, although hash-table operations can degrade under unfavorable collision patterns.

The typed value representation prevents a Boolean from being silently interpreted as a number. Numeric operations also reject non-finite values. Division by zero and undefined variables produce explicit runtime exceptions.

### Validation and limitations

The VM checks that bytecode ends with `HALT` and that branch targets refer to valid instruction positions. The current expression compiler does not generate branches, but the runtime instruction set defines them for extension.

The instruction budget bounds the number of executed instructions. It does not guarantee a fixed wall-clock execution time because individual instructions can have different costs. The program also lacks source parsing, a complete static type checker, bytecode serialization, and a sandbox for untrusted native extensions.

The case study illustrates why compiler correctness and runtime correctness are separate concerns. A correctly compiled expression can still fail because a required variable is missing or because a numeric operation is invalid for its inputs.

## Java implementation: enterprise policy execution

The Java program represents deployment rules as immutable domain objects. Its `Expression` hierarchy distinguishes literals, variable references, and binary expressions. Sealed interfaces constrain the set of permitted expression variants, while records make value objects explicit.

The compiler accepts an allowlist of permitted context variables. This prevents policies from referencing arbitrary runtime data. Compilation emits an immutable instruction list that can be reused across deployments.

The virtual machine receives a separate context for each execution. Its operand stack is private to the execution instance, and its instruction budget limits execution work. This design separates reusable compiled policy data from mutable execution state.

The deployment example evaluates two independently compiled rules: the absence of critical findings and a sufficiently long deployment window. A policy service combines the resulting Boolean decisions. This composition keeps policy orchestration distinct from the low-level arithmetic and comparison instructions supported by the VM.

The value model distinguishes `NumberValue` and `BooleanValue`. Arithmetic and comparison instructions require numeric values, while equality compares typed values. Non-finite numeric values and division by zero are rejected.

The compiler's variable allowlist is not a substitute for authorization. An enterprise deployment service must still decide who can modify policies, who can execute them, which contexts may be supplied, and how policy changes are audited. Bytecode immutability prevents accidental modification through the exposed instruction list, but it does not automatically establish that a policy is safe or trustworthy.

## PostgreSQL model and runtime audit trail

The SQL script records compiler and runtime activity as relational data. It does not implement a programming-language compiler inside SQL. Its purpose is to support traceability, reporting, and database-level integrity for the artifacts produced by an external compiler service.

### Relational entities

| Relation | Responsibility |
|---|---|
| `compiler_versions` | Identifies compiler versions and their target execution format. |
| `source_programs` | Stores source text and ownership metadata. |
| `compilations` | Records whether a particular source program compiled successfully or failed. |
| `bytecode_instructions` | Stores ordered opcodes and JSONB operands. |
| `runtime_contexts` | Stores the input bindings supplied to executions. |
| `executions` | Records runtime outcomes, errors, instruction counts, and timing. |

Foreign keys establish the source-to-compilation-to-instruction and compilation-to-execution relationships. Primary keys prevent duplicate instruction positions within a compilation. Check constraints distinguish successful compilations from failed compilations and successful executions from failed executions.

The bytecode table uses a composite primary key of compilation identifier and instruction index. This prevents two instructions from occupying the same position in one program. The successful-compilation trigger validates that instruction positions begin at zero, remain contiguous, and terminate with `HALT`.

The deferred constraint trigger runs at transaction completion, allowing all instructions to be inserted before the completed sequence is validated. The check applies when the compilation row is inserted or updated; a production implementation would also need to protect against later modifications to instruction rows that invalidate an already-validated compilation.

### Query and index design

The compilation-time index supports retrieval of recent compilation records for a source program. The execution-status index supports operational failure reports. The GIN index on JSONB contexts helps queries that search inside structured runtime bindings. The opcode index supports instruction-level inspection by opcode.

The queries distinguish compilation failures from runtime failures, inspect instructions in program-counter order, extract JSONB values for reporting, and aggregate execution outcomes. These reports help answer whether a failure occurred during source processing, bytecode production, or execution.

The transaction block demonstrates database integrity enforcement. An intentionally inconsistent runtime record is rejected by a check constraint and handled within a nested PL/pgSQL exception block. In an actual execution service, database writes and runtime execution should be designed carefully so partial failures do not create misleading audit records.

## Failure stages and diagnostic boundaries

The same invalid program can fail at different stages, and the distinction affects both debugging and system design.

| Failure stage | Example | Expected handling |
|---|---|---|
| Lexical analysis | Unsupported source character | Report a source position and reject tokenization. |
| Parsing | Missing expression after an operator | Report a grammar error and do not generate executable code. |
| Semantic analysis | Reference to an undeclared variable | Reject the program before execution. |
| Compilation | Unsupported operation in a target backend | Report a compilation diagnostic. |
| Bytecode verification | Invalid branch destination | Reject the instruction sequence before running it. |
| Runtime | Division by zero | Terminate the current execution with a runtime diagnostic. |
| Resource control | Execution budget exhausted | Stop execution and record a resource-limit outcome. |

A source-level diagnostic is generally more useful than a raw instruction index. Production compilers often preserve source-location metadata in intermediate instructions so runtime exceptions can refer back to the original expression.

Error categories should also remain separate in monitoring data. A syntax error may indicate an invalid policy submission, while a missing runtime binding may indicate a defect in the calling service. Combining both into a generic execution failure loses useful operational information.

## Performance and implementation trade-offs

A tree-walking interpreter stores the AST and repeatedly dispatches on its node types. A bytecode interpreter introduces compilation overhead but can use a compact, linear instruction sequence. The actual performance difference depends on the program, runtime, memory layout, and implementation.

For repeated policy evaluation, compiling once and executing against multiple contexts can reduce repeated parsing and semantic-analysis work. Immutable bytecode can be cached using a key that includes source content, compiler version, language configuration, and relevant compilation options.

The stack-machine design avoids allocating a separate object for every intermediate arithmetic result when values are represented efficiently. In the educational implementations, values are still represented through language-specific objects or variants, so they should not be assumed to match the performance of a production virtual machine.

The examples do not implement constant folding, dead-code elimination, register allocation, inline caching, just-in-time compilation, or native machine-code generation. Those optimizations require additional correctness checks and should be justified by measured workloads rather than assumed benefits.

## Runtime security and operational controls

Executing user-supplied code creates risks beyond incorrect arithmetic. An infinite loop can consume CPU time, a large allocation can exhaust memory, and unsafe native interfaces can expose operating-system resources. A simple instruction budget addresses only part of this threat model.

A production runtime should consider:

- **Execution isolation:** Run untrusted workloads in a process or sandbox with restricted permissions and operating-system resource limits.
- **Resource accounting:** Enforce CPU, memory, recursion, output-size, and execution-time limits independently where appropriate.
- **Input validation:** Validate runtime bindings against the expected type and range of each variable.
- **Bytecode integrity:** Associate compiled artifacts with source hashes, compiler versions, and compilation options.
- **Policy authorization:** Restrict who can modify, compile, and execute privileged policies.
- **Diagnostic redaction:** Avoid exposing secrets or sensitive context values in error messages and execution traces.
- **Auditability:** Record the program version, runtime context identifier, execution outcome, and relevant diagnostics without storing unnecessary sensitive data.

Bytecode verification is a defense-in-depth mechanism. Structural checks reduce the chance that malformed instructions reach the VM, but comprehensive verification must also consider operand types, stack depth, control-flow joins, resource consumption, and the semantics of every opcode.

## Reproducibility and debugging

Reliable compiler diagnostics depend on preserving the relationship between source and generated instructions. Recording compiler versions and immutable bytecode artifacts allows an execution failure to be investigated against the exact program representation that ran.

The Python instruction trace displays the program counter, opcode, operand, and stack state. The JavaScript trace provides equivalent execution snapshots. Such traces are useful for small programs, but large production workloads require bounded logging and careful treatment of sensitive values.

The SQL audit model preserves compilation outcomes and execution history. Together, source metadata, compiler identity, bytecode positions, runtime context identifiers, and error classifications provide a basis for reproducing failures without confusing source-level problems with runtime defects.
