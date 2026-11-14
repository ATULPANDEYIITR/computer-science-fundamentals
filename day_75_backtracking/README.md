# Backtracking Algorithms and State Space Tree Exploration

## 1. Technical Scope

Backtracking is an algorithmic problem-solving technique that constructs solutions incrementally and abandons a partial solution when it cannot lead to a valid complete solution.

It is particularly useful for combinatorial problems in which the number of possible arrangements grows rapidly with input size.

This implementation examines four closely related concepts:

- State space tree construction and traversal.
- Permutation generation.
- Combination generation.
- The N-Queens constraint-satisfaction problem.

Five implementations provide different engineering perspectives:

| File | Implementation perspective |
|---|---|
| Python | Reusable recursive search engine and algorithm laboratory |
| JavaScript | Generator-based, event-driven and asynchronous search |
| C++17 | Resource-controlled search and optimized constraint evaluation |
| Java 17 | Enterprise-oriented domain modeling and search orchestration |
| PostgreSQL | Persistent search execution, state-space storage and reporting |

All implementations use actual search algorithms rather than relying on predefined solution collections.

## 2. Backtracking Fundamentals

### 2.1 Definition

Backtracking builds a solution one decision at a time.

At every stage, the algorithm:

1. Identifies the current partial solution.
2. Generates possible next decisions.
3. Evaluates whether a decision satisfies the applicable constraints.
4. Extends the current solution when the decision is valid.
5. Recursively explores the resulting state.
6. Reverses the decision when exploration returns.

The final operation is essential. A recursive branch must restore the state it modified before another branch is evaluated.

This process is commonly described as choose, explore and undo.

### 2.2 State Space Tree

A state space tree represents the possible decisions of a search problem.

Each node represents a search state. An edge represents a decision that transforms one state into another.

The root represents the initial state. Internal nodes represent partial solutions. Leaf nodes represent completed solutions, invalid terminal states or states with no remaining valid decisions.

Consider generating permutations of three distinct elements.

The tree begins with three possible first decisions. Each first decision creates two possible second decisions, followed by one remaining decision.

The resulting tree contains:

- One root node.
- Three nodes at depth one.
- Six nodes at depth two.
- Six terminal solution nodes.

The total number of nodes is:

1 + 3 + 6 + 6 = 16

The number of complete permutations is:

3! = 6

### 2.3 Partial Solutions and Complete Solutions

A partial solution contains decisions made so far but does not necessarily satisfy all final requirements.

A complete solution satisfies every requirement of the problem.

For example, a partial N-Queens arrangement containing three non-attacking queens on a four-row board is not yet a complete solution.

A valid complete solution must contain exactly four queens, one in each row and column, with no shared diagonal.

### 2.4 Pruning

Pruning removes a search branch when its current state cannot produce a valid result.

Without pruning, the algorithm may explore large portions of the state space that cannot contribute to an answer.

Three important forms of pruning are implemented:

| Technique | Purpose |
|---|---|
| Constraint pruning | Reject conflicting decisions |
| Duplicate pruning | Avoid equivalent arrangements |
| Feasibility pruning | Stop when insufficient candidates remain |

Pruning improves practical search performance without changing the set of valid solutions.

## 3. Permutations

### 3.1 Definition

A permutation is an arrangement of elements in which order matters.

For a collection of `n` distinct elements, the number of permutations is:

\[
P(n)=n!
\]

For example, the permutations of `[1, 2, 3]` are:

- `[1, 2, 3]`
- `[1, 3, 2]`
- `[2, 1, 3]`
- `[2, 3, 1]`
- `[3, 1, 2]`
- `[3, 2, 1]`

There are six arrangements.

### 3.2 Recursive Mechanism

The permutation algorithm maintains:

- An input collection.
- A current path.
- A used-position array or equivalent structure.
- A collection of completed results.

At each recursive level, it selects an unused element.

The algorithm terminates when the path contains every input element.

The used-position structure prevents an element from appearing more than once in an individual permutation.

### 3.3 Duplicate Elements

Consider:

`[1, 2, 2]`

The mathematical number of distinct permutations is:

\[
\frac{3!}{2!}=3
\]

A naive implementation can generate repeated results because the two occurrences of `2` are treated as independent choices.

The implementations sort the input and apply duplicate-aware selection.

When two equal elements occur consecutively, the later occurrence cannot be selected at the same decision depth while the earlier occurrence remains unused.

This eliminates equivalent branches without requiring a separate global result-deduplication operation.

### 3.4 Complexity

For distinct elements:

- Time complexity: \(O(n \cdot n!)\), including result construction.
- Auxiliary search space: \(O(n)\).
- Output storage: \(O(n \cdot n!)\).

The number of complete arrangements dominates execution time.

## 4. Combinations

### 4.1 Definition

A combination selects elements without considering their order.

For `n` distinct elements and a selection size of `k`, the number of combinations is:

\[
C(n,k)=\frac{n!}{k!(n-k)!}
\]

For `[1, 2, 3, 4]`, selecting two elements produces:

| Combination |
|---|
| `[1, 2]` |
| `[1, 3]` |
| `[1, 4]` |
| `[2, 3]` |
| `[2, 4]` |
| `[3, 4]` |

The result contains six combinations.

### 4.2 Difference Between Permutations and Combinations

| Property | Permutations | Combinations |
|---|---|---|
| Does order matter? | Yes | No |
| Can positions be reused? | No in this implementation | No |
| Selection strategy | Any unused position | Increasing input index |
| Typical count | \(n!\) | \(\binom{n}{k}\) |
| Main state | Used positions | Starting index |

The most important implementation distinction is the starting index.

A combination search only considers candidates after the previously selected position.

Consequently, `[1, 2]` is generated, but `[2, 1]` is never generated.

### 4.3 Feasibility Pruning

Suppose four elements remain to be selected, but only three candidate positions are available.

The branch cannot produce a valid combination.

It is therefore unnecessary to continue recursion.

The combination implementations calculate the last permissible candidate index using the number of remaining selections.

This prevents unnecessary recursive calls.

### 4.4 Duplicate Handling

For duplicate input values, sorting and skipping repeated values at the same decision depth prevent duplicate combinations.

The implementation uses value-based combination semantics rather than treating identical occurrences as distinguishable objects.

### 4.5 Complexity

For distinct values, the number of complete solutions is:

\[
\binom{n}{k}
\]

Including result construction, output-sensitive time complexity is:

\[
O\left(k\binom{n}{k}\right)
\]

Auxiliary recursion space is \(O(k)\), excluding stored results.

## 5. N-Queens Problem

### 5.1 Problem Definition

The N-Queens problem requires placing `N` queens on an `N × N` chessboard so that no two queens attack one another.

A queen attacks:

- Other pieces in its row.
- Other pieces in its column.
- Other pieces along both diagonal directions.

A valid arrangement must satisfy:

1. Exactly one queen in each row.
2. Exactly one queen in each column.
3. No shared descending diagonal.
4. No shared ascending diagonal.

The four-queen problem has two valid solutions.

### 5.2 State Representation

All implementations place one queen per row.

The current state is represented by an array in which the element at index `r` identifies the column containing the queen in row `r`.

For example:

`[1, 3, 0, 2]`

represents the following board:

| Row | Column |
|---|---|
| 0 | 1 |
| 1 | 3 |
| 2 | 0 |
| 3 | 2 |

### 5.3 Constraint Evaluation

A queen at position `(r, c)` conflicts with an existing queen when any of the following conditions holds:

**Column conflict**

\[
c_1=c_2
\]

**Descending diagonal conflict**

\[
r_1-c_1=r_2-c_2
\]

**Ascending diagonal conflict**

\[
r_1+c_1=r_2+c_2
\]

These mathematical properties allow diagonal conflicts to be detected using integer keys.

The Python and Java implementations use sets to maintain occupied columns and diagonals.

The C++ implementation uses integer bitmasks.

The PostgreSQL implementation maintains corresponding integer masks and records accepted and rejected candidate decisions.

### 5.4 Backtracking Workflow

For each row:

1. Generate candidate columns.
2. Check the column constraint.
3. Check both diagonal constraints.
4. Reject conflicting positions.
5. Record a valid position.
6. Explore the next row.
7. Remove the position when recursion returns.

When all rows contain queens, a complete solution has been found.

### 5.5 Bitmask Optimization

The C++ implementation and optimized Python implementation represent occupied columns and diagonals using integer bitmasks.

For a board of size `N`, the full mask is:

\[
M=2^N-1
\]

The available columns are:

\[
A=M\ \&\ \sim(C\ |\ L\ |\ R)
\]

Where:

- `C` represents occupied columns.
- `L` represents one diagonal direction.
- `R` represents the opposite diagonal direction.
- `A` represents currently available positions.

The least significant available bit is extracted using:

\[
b=A\ \&\ (-A)
\]

This enables efficient candidate extraction and avoids repeated set membership operations.

The diagonal masks are shifted when the algorithm moves to the next row.

Bitmask operations reduce the overhead of constraint evaluation, although the underlying search remains combinatorial.

### 5.6 Known Solution Counts

| Board size | Number of solutions |
|---:|---:|
| 1 | 1 |
| 2 | 0 |
| 3 | 0 |
| 4 | 2 |
| 5 | 10 |
| 6 | 4 |
| 7 | 40 |
| 8 | 92 |

These values provide useful correctness checks for N-Queens implementations.

## 6. State Restoration and Search Correctness

Correct state restoration is one of the most important properties of recursive backtracking.

Suppose a search branch selects a candidate and modifies three structures:

- Current solution path.
- Used-position collection.
- Occupied diagonal collection.

All three modifications must be reversed after the recursive call.

Failure to restore even one structure can contaminate subsequent branches.

This can produce:

- Missing solutions.
- Duplicate solutions.
- Incorrect constraint rejection.
- Invalid complete arrangements.

The implementations use explicit cleanup after recursive calls.

The search state is branch-local in the sense that every branch receives a consistent state derived from its parent and returns control after undoing its own changes.

For production implementations, exception-safe state restoration is particularly important. A resource-limit exception or cancellation must not be mistaken for a valid completion.

## 7. Python Implementation

The Python implementation provides a reusable algorithm laboratory.

### 7.1 Architecture

| Component | Responsibility |
|---|---|
| `SearchConfiguration` | Defines search limits |
| `SearchStatistics` | Tracks execution metrics |
| `BacktrackingEngine` | Manages recursive search accounting |
| `PermutationSolver` | Generates distinct permutations |
| `CombinationSolver` | Generates combinations |
| `NQueensSolver` | Evaluates board constraints using sets |
| `NQueensBitmaskSolver` | Provides optimized bitmask search |
| `NQueensSolution` | Represents a complete board arrangement |

### 7.2 Python-Specific Design Decisions

Dataclasses provide structured configuration and result models.

Enums provide explicit search-type representation.

Sets support efficient constraint membership checks.

Lists represent the current recursive path.

Exceptions distinguish invalid configurations from controlled search termination.

The `finally` blocks ensure that execution timing is recorded when a search terminates normally or raises an exception.

### 7.3 Search Limits

Two independent limits are available:

- Maximum visited nodes.
- Maximum completed solutions.

These limits prevent uncontrolled result generation in resource-constrained environments.

The limits do not guarantee that every search will finish within a fixed execution time. They restrict the number of search operations and results instead.

### 7.4 Practical Considerations

The implementation stores complete results in memory.

This is convenient for educational analysis and small combinatorial problems.

For large searches, a streaming interface would reduce memory consumption by allowing consumers to process individual solutions without retaining every result.

The JSON export function demonstrates structured result persistence.

Production applications should validate output paths and restrict file permissions.

## 8. JavaScript Implementation

The JavaScript implementation focuses on event-driven search execution.

### 8.1 Generator-Based Traversal

JavaScript generator functions use `yield` to expose solutions incrementally.

The search algorithm does not need to construct the complete result collection before exposing its first solution.

The implementation uses:

- Generator functions for recursive traversal.
- `EventEmitter` for search monitoring.
- `SearchSession` for lifecycle and statistics.
- `SearchPolicy` for resource limits.
- `AbortController` for cancellation.
- Promises for asynchronous result consumption.

### 8.2 Event Model

The search session emits three event categories:

| Event | Purpose |
|---|---|
| `node` | Reports a visited state |
| `solution` | Reports a complete solution |
| `pruned` | Reports an eliminated branch |
| `finished` | Reports the final search state |

This separation allows monitoring systems to observe execution without becoming part of the algorithm's constraint logic.

### 8.3 Asynchronous Consumption

The `consume` function periodically yields control to the Node.js event loop using `setImmediate`.

This improves responsiveness when processing large result collections.

The underlying recursive generator remains synchronous between these yielding points.

The asynchronous wrapper does not make the recursive search computationally parallel.

### 8.4 Cancellation

`AbortController` provides a standard cancellation signal.

The search session checks the signal before processing new states and before recording solutions.

A cancelled search raises `SearchCancelledError`.

Cancellation is distinct from successful completion and resource-limit termination.

### 8.5 Engineering Considerations

JavaScript bitwise operations use signed 32-bit integer semantics.

The implementation therefore limits N-Queens board size to 15.

The input validation also restricts collection length and requires a consistent value type.

A production implementation handling larger domains should use a representation appropriate to its numeric constraints, such as `BigInt` for wider integer masks.

## 9. C++17 Implementation

The C++ implementation emphasizes efficient data structures, controlled resource consumption and explicit state management.

### 9.1 Architecture

| Component | Responsibility |
|---|---|
| `SearchLimits` | Defines resource limits |
| `SearchStatistics` | Stores execution metrics |
| `SearchEngine` | Centralizes accounting and limit enforcement |
| `PermutationSolver` | Performs duplicate-aware enumeration |
| `CombinationSolver` | Performs index-constrained enumeration |
| `NQueensSolver` | Performs bitmask-based board search |
| `SearchLimitExceeded` | Represents controlled search termination |

### 9.2 STL Usage

The implementation uses:

- `vector` for paths and solutions.
- `vector<bool>` for used-position tracking.
- `sort` for duplicate normalization.
- `fill` for state initialization.
- `runtime_error` for controlled failures.
- `chrono` for execution measurement.
- `uint32_t` for bitmask representation.

### 9.3 Bitmask Constraints

The N-Queens solver uses unsigned integer masks to represent occupied columns and diagonals.

The operation `available & (~available + 1)` extracts the least significant available bit.

The compiler intrinsic `__builtin_ctz` identifies its column index.

This implementation targets GCC and Clang environments that provide the intrinsic.

The board-size restriction ensures that all masks remain within the supported integer width.

### 9.4 Failure Handling

Search limits are checked centrally.

If a limit is exceeded, the exception propagates through the recursive search and terminates the operation.

The caller receives a controlled error rather than an incomplete result being presented as a successful search.

Execution statistics are finalized even when recursive traversal raises an exception.

## 10. Java 17 Implementation

The Java implementation models backtracking as an enterprise search service.

Its central design objective is separation between problem definitions, search policies, domain models and orchestration.

### 10.1 Domain Model

| Type | Purpose |
|---|---|
| `SearchRequest` | Immutable search configuration |
| `SearchSolution` | Immutable completed result |
| `SearchReport` | Execution report |
| `SearchType` | Identifies the algorithm |
| `SearchStatus` | Represents lifecycle state |
| `SearchPolicy` | Defines resource-control rules |
| `SearchContext` | Maintains execution state |
| `SearchService` | Defines the search service contract |
| `SearchOrchestrator` | Coordinates execution |

Java records provide compact immutable data structures.

The `List.copyOf` operation prevents callers from modifying request inputs and returned result lists through the original mutable collection references.

### 10.2 Service Separation

Each algorithm has an independent service implementation.

`PermutationService` manages unused positions and duplicate elimination.

`CombinationService` manages increasing candidate indices and feasibility pruning.

`NQueensService` manages the three constraint collections.

The orchestrator selects the correct service using the search type.

This design allows the orchestration layer to remain independent of individual algorithm implementations.

### 10.3 Policy Evaluation

`BoundedSearchPolicy` defines maximum permitted node and solution counts.

`SearchContext` evaluates these limits during traversal.

This separates resource governance from individual candidate-selection rules.

### 10.4 Lifecycle Management

Search jobs have explicit states:

`CREATED → RUNNING → COMPLETED`

Failure paths produce:

- `FAILED`
- `LIMIT_EXCEEDED`

The implementation does not permit a completed search to be treated as a new running operation through the same lifecycle state.

### 10.5 Enterprise Implications

This structure is appropriate for applications that need:

- Centralized execution monitoring.
- Consistent input validation.
- Reusable algorithm services.
- Immutable request boundaries.
- Standardized failure reporting.
- Independent policy changes.

The demonstration executes synchronously. A production service would need additional mechanisms for durable job persistence, concurrent execution control, cancellation, authorization and distributed resource management.

## 11. PostgreSQL Implementation

The PostgreSQL implementation treats search execution as a persistent relational workflow.

Unlike the in-memory implementations, it records visited states, candidate decisions, completed solutions and execution events.

### 11.1 Relational Domain Model

The principal relationship is:

Search Job  
→ State-Space Nodes  
→ Candidate Decisions  
→ Complete Solutions  
→ Search Events

Each search job identifies one algorithm and its input configuration.

Every state-space node belongs to one job and can reference its parent node.

Candidate decisions record whether a particular value was accepted or rejected under a named constraint.

Complete solutions are stored independently from partial search states.

Execution events provide an audit trail of job creation, execution and termination.

### 11.2 Database Tables

| Table | Responsibility |
|---|---|
| `search_jobs` | Stores configurations and execution status |
| `search_nodes` | Stores the state-space tree |
| `candidate_decisions` | Records candidate evaluations |
| `search_solutions` | Stores complete solutions |
| `search_events` | Stores execution events |

### 11.3 Referential Integrity

Primary keys uniquely identify records.

Foreign keys prevent search nodes, solutions and decisions from referring to nonexistent parent records.

The composite foreign key on search nodes ensures that a child references a parent from the same search job.

The unique constraint on `(job_id, solution_number)` prevents duplicate solution numbering within one job.

Check constraints validate resource limits, counters and algorithm-specific configurations.

### 11.4 Triggers

The node validation trigger verifies:

- Root depth equals zero.
- Child depth equals parent depth plus one.
- Parent and child belong to the same search job.

The lifecycle trigger enforces valid status transitions.

Terminal states cannot be reopened through ordinary status updates.

These database mechanisms provide integrity enforcement independently of application-level validation.

### 11.5 Recursive Search Functions

`execute_search` coordinates the database-backed algorithms.

It implements three recursive procedures:

- `permutation_search`
- `combination_search`
- `queens_search`

The nested node insertion function creates the corresponding tree records.

The solution procedure persists completed results.

Each recursive procedure restores its working state before returning to its caller.

The search node limit is enforced centrally.

The solution limit is enforced when a complete result is recorded.

### 11.6 Transactional Behavior

The script creates jobs and executes their search workflows within a transaction.

The job status and solution records are committed together when the transaction succeeds.

A failure that propagates out of the transaction rolls back the transaction's changes.

The controlled resource-limit path records the termination state and returns `LIMIT_EXCEEDED`.

This distinction is important when interpreting search status and persisted results.

A database transaction provides atomicity but does not provide automatic durability for intermediate search progress before commit.

Long-running production searches should consider checkpointing and shorter transactions.

### 11.7 Reporting

The SQL script includes reporting operations for:

- Job retrieval.
- Solution retrieval.
- Algorithm-level aggregation.
- State-space tree inspection.
- Constraint decision analysis.
- N-Queens solution validation.
- Failure and resource-limit reporting.
- Execution audit retrieval.

The reporting views separate operational statistics from the underlying search records.

### 11.8 Database Performance

The implementation indexes:

- Job status and creation time.
- Algorithm type.
- Job and node depth.
- Parent-node relationships.
- Candidate decisions.
- Job solution numbering.
- Event timestamps.

These indexes support the main retrieval and reporting patterns.

Persisting every search node and decision creates substantial write overhead.

The database implementation is therefore intended for inspectable, moderate-sized searches and educational workflow analysis rather than unrestricted high-volume combinatorial computation.

## 12. Comparison of Backtracking Variants

| Property | Permutations | Combinations | N-Queens |
|---|---|---|---|
| Primary objective | Arrange elements | Select elements | Place non-attacking queens |
| Decision variable | Next unused element | Next eligible index | Next column in a row |
| Main constraint | No repeated position | Increasing index | Columns and diagonals |
| Duplicate handling | Required for repeated values | Required for repeated values | Not applicable |
| Pruning | Duplicate elimination | Feasibility and duplicate checks | Constraint conflicts |
| Typical output | Ordered arrangements | Unordered selections | Valid board configurations |

These algorithms share the same recursive framework but use different decision rules and state representations.

They should not be treated as interchangeable implementations.

## 13. Algorithm Complexity

The complexity of backtracking depends on the number of possible states, the cost of evaluating a candidate and the amount of output retained.

| Algorithm | Search characteristics | Auxiliary space |
|---|---|---|
| Permutations | Factorial growth | \(O(n)\) |
| Combinations | Binomial growth | \(O(k)\) |
| N-Queens | Exponential search with constraint pruning | \(O(n)\) |

For permutations, the number of complete solutions with distinct elements is \(n!\).

For combinations, the number of complete solutions is \(\binom{n}{k}\).

N-Queens has a much more complex search structure. The number of solutions does not describe the entire search cost because the algorithm also visits partial states and rejects conflicting candidates.

Bitmasks reduce the cost of individual constraint checks but do not eliminate exponential search growth.

## 14. Validation and Edge Cases

The implementations validate important boundary conditions.

| Scenario | Expected behavior |
|---|---|
| Empty permutation input | One empty permutation |
| Combination size zero | One empty combination |
| Combination size equals input length | One complete combination |
| Combination size exceeds input length | Validation failure |
| Repeated permutation values | Duplicate results eliminated |
| Repeated combination values | Duplicate combinations eliminated |
| N-Queens board size one | One solution |
| N-Queens board size two | No solution |
| N-Queens board size three | No solution |
| N-Queens board size four | Two solutions |
| Excessive search nodes | Controlled termination |
| Excessive solutions | Controlled termination |
| Invalid board size | Validation failure |

The Python, C++, Java and JavaScript demonstrations validate representative expected counts.

The PostgreSQL implementation includes relational constraints and solution validation queries.

## 15. Security and Production Considerations

Backtracking algorithms can consume substantial processing time and memory.

A production implementation should consider the following controls.

### Resource Management

- Enforce maximum search nodes.
- Limit the number of stored solutions.
- Restrict maximum input sizes.
- Monitor recursive depth.
- Provide cancellation mechanisms.
- Apply execution timeouts.

### Input Validation

- Reject invalid selection sizes.
- Validate board dimensions.
- Restrict unsupported input types.
- Check numeric bounds.
- Validate configuration before execution.

### Data Protection

- Restrict access to persisted search jobs.
- Apply database role permissions.
- Validate file export destinations.
- Avoid exposing internal exception details to untrusted callers.
- Separate operational audit records from sensitive application data.

### Operational Monitoring

Monitor:

- Nodes visited.
- Solutions found.
- Branches pruned.
- Maximum recursion depth.
- Execution duration.
- Search termination status.
- Resource-limit violations.

These measurements help distinguish inefficient search strategies from inherently difficult problem instances.

## 16. Practical Applications

Backtracking is useful in many computational domains.

| Application | Backtracking role |
|---|---|
| Scheduling | Explore valid time-slot assignments |
| Resource allocation | Construct feasible resource combinations |
| Puzzle solving | Evaluate possible board configurations |
| Graph coloring | Assign colors while preserving constraints |
| Configuration management | Find valid component configurations |
| Cryptographic research | Explore constrained combinatorial spaces |
| Planning systems | Enumerate feasible decision sequences |
| Test generation | Construct input combinations under constraints |

For larger problems, backtracking can be combined with branch-and-bound, constraint propagation, memoization, heuristic variable ordering and parallel search.

The effectiveness of these optimizations depends on the problem structure.

## 17. Implementation Limitations

The five implementations intentionally use different architectural approaches.

| Implementation | Principal limitation |
|---|---|
| Python | Complete result collections can consume substantial memory |
| JavaScript | Recursive generator execution remains single-threaded |
| C++17 | The board-size and mask-width restrictions limit N-Queens input |
| Java 17 | Search orchestration is synchronous and in-memory |
| PostgreSQL | Persisting every state and decision increases database write overhead |

The PostgreSQL implementation also uses recursive PL/pgSQL procedures and should be tested against the intended PostgreSQL version and workload limits.

The JavaScript implementation uses Node.js runtime facilities and should be executed in a compatible Node.js environment.

The C++ implementation uses GCC/Clang bit operations for candidate extraction.

These implementations are designed for understanding search mechanics, evaluating constraints and examining different engineering approaches to the same family of problems.

## 18. Execution and Verification

| File | Runtime |
|---|---|
| Python | Python 3.10 or later |
| JavaScript | Node.js 18 or later |
| C++17 | Compiler supporting C++17 |
| Java | JDK 17 |
| PostgreSQL | PostgreSQL 14 or later |

Expected principal validation results:

| Test | Expected result |
|---|---:|
| Distinct permutations of `[1, 2, 2]` | 3 |
| Combinations of four elements taken two at a time | 6 |
| N-Queens for board size 1 | 1 |
| N-Queens for board size 2 | 0 |
| N-Queens for board size 3 | 0 |
| N-Queens for board size 4 | 2 |
| N-Queens for board size 5 | 10 |

The principal correctness criterion is that every emitted result satisfies the corresponding problem constraints and that no valid distinct result is omitted or duplicated.

The implementations demonstrate the same fundamental search discipline through different data structures, runtime models, service boundaries and persistence mechanisms.
