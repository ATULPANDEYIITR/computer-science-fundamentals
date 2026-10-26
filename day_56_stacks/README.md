# Stack Operations, Applications, and Expression Evaluation

## Scope

This project treats the stack as a LIFO data structure and develops its use across three related areas:

- fundamental stack operations such as `push`, `pop`, `peek`, `clear`, emptiness checks, and capacity enforcement;
- practical stack applications such as balanced-delimiter validation, browser history, monotonic-stack processing, and event/state handling;
- expression processing through postfix evaluation and operator/operand stack separation.

The implementations deliberately use different engineering perspectives. Python emphasizes reusable data structures and expression parsing. JavaScript emphasizes event-driven processing and runtime validation. C++17 implements a governance-oriented technical case study while retaining stack-based algorithms. Java 17 models explicit domain types and enterprise service boundaries. PostgreSQL represents persistent stack state, operation history, validation, and reporting relationally.

The central relationship is:

`Input or workflow state → stack operations → intermediate state → application-specific decision`

A stack is not merely a container. Its LIFO ordering provides the behavior required by nested structures, undo/redo histories, operator processing, depth-first algorithms, and monotonic scans.

## Core Stack Model

A stack exposes the most recent element as its top.

Plain-text representation:

`bottom → [A] [B] [C] ← top`

After `push(D)`:

`bottom → [A] [B] [C] [D] ← top`

After `pop()`:

`bottom → [A] [B] [C] ← top`

The fundamental operations are:

| Operation | Meaning | Typical complexity |
|---|---|---:|
| `push(x)` | Place `x` on the top | O(1) amortized |
| `pop()` | Remove and return the top | O(1) |
| `peek()` | Inspect the top without removal | O(1) |
| `isEmpty()` | Determine whether no elements remain | O(1) |
| `size()` | Return the number of elements | O(1) |
| `clear()` | Remove all elements | O(n) in many implementations |

The LIFO rule is the defining invariant:

`last inserted element = first removed element`

Overflow occurs when a bounded stack has reached its configured capacity. Underflow occurs when `pop` or `peek` is attempted on an empty stack.

## Stack Representation

The Python implementation uses a list-backed `Stack[T]` with optional capacity enforcement. Python's list provides amortized constant-time append and constant-time removal from the end.

The JavaScript implementation uses an array-backed class. The implementation explicitly rejects invalid capacities and exposes stack state through a copied array so callers cannot directly replace the internal storage.

The C++17 implementation uses `std::vector<T>`. This provides contiguous storage and efficient end insertion/removal. Capacity is represented as a logical application-level limit rather than relying on the vector's physical capacity.

The Java 17 implementation uses `ArrayDeque<T>` internally. `ArrayDeque` is appropriate for LIFO operations because insertion and removal at the front are constant-time operations without the synchronization overhead of legacy collection types.

PostgreSQL represents a persistent stack as ordered rows:

`stack_id + position + value_text`

The greatest `position` is the top of the stack. A descending position lookup therefore implements `peek` and `pop`.

## Stack Operations

The five source implementations distinguish physical storage from application behavior.

A basic operation sequence is:

`push(A) → push(B) → push(C) → pop()`

The result is `C`, not `A`.

The implementations explicitly test:

- normal insertion;
- normal removal;
- top inspection;
- empty-stack behavior;
- bounded-stack overflow;
- invalid input;
- state reporting.

The PostgreSQL functions `push_value`, `pop_value`, `peek_value`, and `clear_stack` turn these operations into database transactions. Successful and failed attempts are recorded in `stack_operations`, making operational behavior auditable rather than transient.

## Balanced Delimiters

Balanced-delimiter validation is a direct application of LIFO ordering.

For the input:

`{[()]}`

the opening delimiters are pushed:

`{ → [ → (`

When closing delimiters arrive, the most recent opening delimiter must match first:

`( → [ → {`

The algorithm rejects a closing delimiter when:

- the stack is empty;
- the top opening delimiter does not match;
- opening delimiters remain after processing the input.

The time complexity is O(n), and the auxiliary space is O(n) in the worst case.

This pattern generalizes to nested configuration structures, source-code parsing, markup validation, and syntax analysis.

The Python, JavaScript, C++17, and Java implementations contain executable delimiter validation. The PostgreSQL implementation uses a restricted expression validator focused on expression syntax and parenthesis structure rather than attempting to execute arbitrary expression text.

## Expression Evaluation

Expression evaluation demonstrates two distinct stacks:

`operator stack`

and

`operand stack`

For an infix expression such as:

`3 + 4 * 2`

operator precedence requires multiplication before addition.

The postfix form is:

`3 4 2 * +`

Postfix evaluation is naturally stack-based:

`push 3`
`push 4`
`push 2`
`pop 2`
`pop 4`
`4 * 2 = 8`
`push 8`
`pop 8`
`pop 3`
`3 + 8 = 11`

The final operand stack contains one value:

`[11]`

A valid postfix expression must leave exactly one operand after evaluation.

### Infix-to-Postfix Conversion

The Python and JavaScript implementations convert infix expressions into postfix notation using an operator stack.

The conversion follows these rules:

- numbers go directly to the output;
- `(` goes onto the operator stack;
- `)` causes operators to be emitted until `(` is reached;
- higher-precedence operators are emitted before lower-precedence operators;
- left-associative operators of equal precedence are emitted before the incoming operator;
- exponentiation is treated as right-associative;
- unary minus is represented internally as `u-`.

The supported binary operators are:

`+  -  *  /  %  ^`

Invalid expressions are rejected rather than being passed to the host language's evaluator. This is an important security property because expression input must not become executable source code.

### Expression Failure Cases

The implementations detect conditions such as:

- empty expressions;
- incomplete expressions;
- unsupported characters;
- unmatched parentheses;
- missing operands;
- division by zero;
- malformed postfix expressions;
- non-finite arithmetic results.

The Python implementation exposes `InvalidExpression` and `StackUnderflow` exceptions. JavaScript uses dedicated error classes. C++17 uses standard exceptions. Java uses domain-specific runtime exceptions.

## Monotonic Stack

The next-greater-element problem demonstrates a stack whose contents maintain a useful ordering invariant.

For:

`[4, 5, 2, 10, 8]`

the next greater values are:

`[5, 10, 10, -1, -1]`

The stack stores indices rather than values. When a new value is greater than the value represented by the top index, that element's next greater value has been discovered.

Each index is:

- pushed at most once;
- popped at most once.

Therefore the total running time is O(n), even though an individual iteration may perform several pops.

This is a major reason monotonic stacks are useful in problems involving:

- next greater or smaller elements;
- nearest greater or smaller values;
- temperature-style waiting-time problems;
- histogram boundaries;
- range dominance relationships.

## Browser History

Browser history provides a classic two-stack application.

The state is separated into:

`back stack ← current page → forward stack`

Visiting a new page pushes the current page onto the back stack and clears the forward stack.

A back operation:

`current → forward`
`back top → current`

A forward operation:

`current → back`
`forward top → current`

The JavaScript implementation models this behavior with `BrowserHistory`. The Python implementation contains a corresponding demonstration.

The important invariant is that visiting a new location invalidates the previously available forward path.

## Event-Driven Processing

The JavaScript implementation adds an event-driven perspective through `StackEventProcessor`.

Handlers are stored by event name in a `Map`. Multiple handlers can be registered for the same event, and asynchronous handlers are executed sequentially.

This is useful when a stack operation changes application state and related components must react to the change.

For example:

`job event → state handler → audit handler`

Sequential execution is deliberate for state-changing workflows because it avoids nondeterministic ordering between handlers.

The implementation does not execute arbitrary source text, and it validates handler types before registration.

## C++17 Governance Case Study

The C++17 program combines stack-based algorithms with a repository-governance scenario.

The governance model contains:

- pull request identity;
- source and target branches;
- commits;
- reviews;
- status checks;
- branch protection policy;
- merge eligibility;
- merge state.

These concepts remain distinct even though the same program uses a stack data structure.

The `MergeEligibilityEngine` evaluates conditions such as:

- draft status;
- branch identity;
- presence of commits;
- merge conflicts;
- branch synchronization;
- linear-history requirements;
- unresolved conversations;
- status-check failures;
- current approval count.

The example intentionally demonstrates failure handling by making an otherwise valid pull request develop a merge conflict and then rejecting the merge.

The stack itself is used for the data-structure operations and algorithmic demonstrations. The governance engine shows how deterministic state evaluation can coexist with those algorithms without confusing a stack with a repository policy.

## Java 17 Enterprise Model

The Java implementation uses explicit domain types:

- `Commit` record;
- `Review` record;
- `StatusCheck` record;
- `BranchProtectionPolicy` record;
- `PullRequest` aggregate;
- `MergePolicy` interface;
- `EnterpriseMergePolicy` policy implementation;
- `MergeService` application service.

This separation prevents policy conditions from being embedded directly inside the data structure.

The pull request has explicit state transitions:

`DRAFT → OPEN → MERGED`

with validation preventing a merge when policy conditions are not satisfied.

The approval calculation uses the latest review state for each reviewer. A reviewer whose latest decision is `CHANGES_REQUESTED` does not continue to count as an approval merely because that reviewer approved an earlier revision.

The stack abstraction is generic and can therefore store multiple domain types. It also uses explicit exceptions for underflow and overflow.

## PostgreSQL Relational Model

The PostgreSQL implementation persists stack state and operational history.

The principal relationships are:

`stack_instances`
`    ↓`
`stack_values`
`    ↓`
`stack_operations`

Expression processing is represented separately:

`expressions`
`    ↓`
`expression_results`

This separation prevents transient stack state from being confused with expression metadata.

### Stack Tables

`stack_instances` stores:

- stack identity;
- name;
- optional capacity;
- creation time.

`stack_values` stores:

- stack identity;
- position;
- value;
- insertion time.

The composite primary key `(stack_id, position)` prevents two values from occupying the same stack position.

`stack_operations` records:

- operation type;
- supplied value;
- success state;
- failure reason;
- timestamp.

This makes deliberate failure cases observable.

### Database-Level Integrity

The database enforces:

- positive capacities;
- non-negative stack positions;
- valid operation types;
- foreign-key relationships;
- unique stack names;
- valid expression types;
- successful operations or explicit error messages.

The stack functions use row locking where appropriate. A push checks capacity after locking the stack row, reducing the risk of concurrent operations bypassing the logical capacity rule.

## Transactional Behavior

The PostgreSQL script includes a transaction around a stack mutation.

The database operation model is:

`BEGIN → lock/read state → mutate → record operation → COMMIT`

A failure raises an exception rather than silently continuing with a partially applied state change.

The use of transactions matters when a stack operation participates in a larger workflow. The stack mutation and its audit record should not diverge.

## Validation and Security

Stack implementations are simple, but production use still requires defensive controls.

Important controls include:

- reject invalid capacities;
- reject operations on empty stacks;
- reject pushes beyond configured limits;
- validate expression syntax;
- reject unsupported operators;
- detect arithmetic errors;
- restrict input length for untrusted expressions;
- avoid evaluating expression text as executable code;
- avoid exposing sensitive stack contents in logs;
- use database constraints as a second line of validation;
- use transactions for state-changing database operations.

Expression evaluation is particularly sensitive. A safe evaluator parses an explicitly supported grammar. It should not call mechanisms equivalent to JavaScript `eval`, Python `eval`, or arbitrary dynamic SQL.

## Failure Handling

The implementations deliberately include failure paths rather than treating only successful operations as valid behavior.

| Failure | Appropriate response |
|---|---|
| Pop from empty stack | Underflow error |
| Peek from empty stack | Underflow error |
| Push into full bounded stack | Overflow error |
| Unmatched `(` | Invalid expression |
| Unexpected `)` | Invalid expression |
| Missing operand | Invalid expression |
| Division by zero | Arithmetic failure |
| Unsupported character | Validation failure |
| Malformed postfix input | Evaluation failure |
| Non-finite result | Reject arithmetic result |

Failure state is part of the domain model. It should be observable, testable, and handled explicitly.

## Performance Characteristics

For a stack containing `n` elements:

| Operation or application | Time | Auxiliary space |
|---|---:|---:|
| Push | O(1) amortized | O(1) |
| Pop | O(1) | O(1) |
| Peek | O(1) | O(1) |
| Balanced delimiters | O(n) | O(n) |
| Postfix evaluation | O(n) | O(n) |
| Infix-to-postfix conversion | O(n) | O(n) |
| Next greater element | O(n) | O(n) |
| Browser back/forward | O(1) per navigation | O(n) |
| PostgreSQL top lookup | O(log n) with position index | O(1) result storage |

The monotonic-stack algorithms are linear because individual elements are not repeatedly pushed and popped without bound.

## File Responsibilities

| File | Technical responsibility |
|---|---|
| Python | Generic stack, validation, expression parsing/evaluation, delimiter validation, monotonic stack, browser history, tests |
| JavaScript | Array-backed stack, asynchronous event processing, expression evaluation, browser history, validation, tests |
| C++17 | Generic STL-backed stack, algorithmic applications, postfix evaluation, repository-governance merge engine |
| Java 17 | Generic stack, immutable records, explicit domain model, policy interface, merge service, state transitions |
| PostgreSQL | Persistent stack state, operation functions, constraints, transaction handling, expression records, validation, reporting |

## Design Distinctions

A stack is the data structure.

An application is the algorithm that exploits LIFO behavior.

Expression evaluation is an application in which stacks separate operands from operators.

A monotonic stack is a specialized stack whose ordering invariant enables linear-time range processing.

Browser history uses two stacks to model reversible navigation.

Database persistence is different from an in-memory stack because row ordering, transactions, concurrency, indexes, and constraints must explicitly represent the stack invariant.

The implementations therefore distinguish:

`storage mechanism`
→ `LIFO invariant`
→ `application algorithm`
→ `validation`
→ `state transition`
→ `failure handling`

That separation is the central engineering principle across the five implementations.
