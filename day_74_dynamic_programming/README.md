# Dynamic Programming: Memoization, Tabulation, Optimal Substructure and Overlapping Subproblems

## Technical Scope

Dynamic Programming (DP) is an algorithm design technique used to solve problems that can be divided into smaller, related subproblems.

Instead of independently solving the same subproblem multiple times, dynamic programming stores previously calculated results and reuses them.

The implementations in this repository demonstrate four central ideas:

- Memoization
- Tabulation
- Optimal substructure
- Overlapping subproblems

They also apply these ideas to practical optimization problems involving project selection, resource allocation, task scheduling, path counting, and sequence comparison.

The five implementations use different engineering approaches while solving related mathematical problems.

## 1. Fundamental Concepts

### Dynamic Programming

A dynamic programming problem generally has a collection of states, decisions, and transitions.

A state represents a smaller version of the original problem.

A transition describes how the solution to one state depends on previously solved states.

A typical recurrence is:

\[
DP(i,w)=\max
\begin{cases}
DP(i-1,w)\\
v_i+DP(i-1,w-c_i)
\end{cases}
\]

Here:

- \(i\) represents the number of considered items.
- \(w\) represents the available capacity.
- \(v_i\) represents the value of item \(i\).
- \(c_i\) represents the cost of item \(i\).

The recurrence evaluates two decisions:

1. Exclude the current item.
2. Include the current item if sufficient capacity remains.

The better result becomes the solution for the current state.

### Memoization

Memoization is a top-down dynamic programming technique.

It starts with the original problem and recursively solves smaller subproblems.

Each calculated result is stored in a cache.

When the same state is requested again, the stored result is returned rather than recalculated.

**Characteristics:**

- Uses recursion.
- Calculates states when required.
- Stores previously computed results.
- Avoids unnecessary state calculations.
- Can introduce recursion-depth limitations.

For a problem with \(n\) items and capacity \(W\), the memoized 0/1 knapsack algorithm has a worst-case time complexity of \(O(nW)\).

Its cache can require \(O(nW)\) space, excluding recursion overhead.

### Tabulation

Tabulation is a bottom-up dynamic programming technique.

It begins with the smallest known states and calculates progressively larger states.

The final answer is obtained from the completed table.

**Characteristics:**

- Usually uses iteration.
- Does not require recursive calls.
- Makes calculation order explicit.
- Can be easier to inspect and debug.
- Often supports space optimization.

For the 0/1 knapsack implementation, the complete table requires \(O(nW)\) time and \(O(nW)\) space.

### Optimal Substructure

A problem has optimal substructure when an optimal solution can be constructed from optimal solutions to smaller subproblems.

For example, consider selecting projects under a fixed budget.

If a project is selected, the remaining decision must be optimal for the remaining budget and remaining projects.

The original optimization problem can therefore be expressed through smaller optimization problems.

### Overlapping Subproblems

Overlapping subproblems occur when the same smaller problem is encountered repeatedly.

Consider the Fibonacci recurrence:

\[
F(n)=F(n-1)+F(n-2)
\]

The recursive calculation repeatedly requests values such as \(F(n-2)\).

Without caching, the same values are calculated multiple times.

Memoization stores these values, while tabulation calculates each required value once.

## 2. Memoization and Tabulation Compared

| Characteristic | Memoization | Tabulation |
|---|---|---|
| Approach | Top-down | Bottom-up |
| Execution | Recursive | Iterative |
| Calculation order | Demand-driven | Predefined |
| State storage | Cache or map | DP table |
| Recursion overhead | Present | Absent |
| Unused states | Often avoided | Often calculated |
| Debugging | Recursive state tracing | Table inspection |
| Space optimization | Cache management | Rolling arrays |
| Common risk | Stack depth | Incorrect iteration order |

Neither technique is universally superior.

Memoization is useful when only a small proportion of possible states is required.

Tabulation is useful when the dependency structure is clear and most states are needed.

The problem structure, memory requirements, and execution environment determine the appropriate implementation.

## 3. Python Implementation

The Python implementation provides a collection of independent dynamic programming algorithms.

### Fibonacci

Two approaches are implemented:

- `fibonacci_memoized()`
- `fibonacci_tabulated()`

The memoized implementation uses `functools.lru_cache`.

The tabulated implementation maintains only two previous values.

The tabulated approach therefore requires constant auxiliary space.

| Approach | Time | Auxiliary space |
|---|---:|---:|
| Basic recursion | \(O(2^n)\) | \(O(n)\) |
| Memoization | \(O(n)\) | \(O(n)\) |
| Tabulation | \(O(n)\) | \(O(1)\) |

Python integers support arbitrary-precision arithmetic, avoiding fixed-width integer overflow.

### Grid Path Counting

The grid problem calculates the number of paths from the top-left cell to the bottom-right cell.

Only two movements are permitted:

- Right
- Down

Obstacles prevent movement through selected cells.

The recurrence is:

\[
DP(r,c)=DP(r-1,c)+DP(r,c-1)
\]

Blocked cells have a value of zero.

The destination has a value of one when it is reachable.

The tabulated implementation uses a single-dimensional array instead of retaining the complete grid.

Its complexity is:

- Time: \(O(RC)\)
- Auxiliary space: \(O(C)\)

### 0/1 Knapsack

The project-selection example models a limited-resource decision.

Each item contains:

- Name
- Resource cost
- Expected value

Each item can be selected at most once.

The implementation provides both memoization and tabulation.

The result includes:

- Maximum achievable value
- Selected items
- Number of computed states
- Algorithm used

The selected items are reconstructed by comparing the optimal include and exclude decisions.

This distinction matters because calculating the maximum value alone does not identify the actual portfolio.

### Longest Common Subsequence

The LCS implementation compares two strings.

A subsequence preserves the original character order, although its characters need not be adjacent.

For matching characters:

\[
DP(i,j)=1+DP(i-1,j-1)
\]

For different characters:

\[
DP(i,j)=\max(DP(i-1,j),DP(i,j-1))
\]

The implementation returns both the subsequence length and an actual reconstructed subsequence.

Complexity:

- Time: \(O(nm)\)
- Space: \(O(nm)\)

### Validation and Testing

The Python implementation includes:

- Invalid capacity checks.
- Invalid grid dimension checks.
- Obstacle boundary validation.
- Project validation.
- Empty-input cases.
- Zero-capacity cases.
- Algorithm comparison.
- Automated unit tests.

The test suite verifies that memoization and tabulation return equivalent optimization results.

## 4. JavaScript Implementation

The JavaScript implementation emphasizes event-driven computation, asynchronous execution, and scheduling optimization.

### Generic Memoization

The `memoize()` function accepts a calculation function and a cache-key function.

A JavaScript `Map` stores previously calculated results.

The cache exposes:

- `clear()`
- `cacheSize()`

This provides explicit control over cached state.

The cache key must uniquely represent the function arguments. JSON serialization is suitable for the simple immutable inputs used here, but more complex applications should provide a deliberate key function.

### Asynchronous Memoization

The `memoizeAsync()` implementation caches pending Promises.

This is important when multiple requests ask for the same asynchronous calculation before the first calculation finishes.

Instead of starting duplicate operations, concurrent callers share the pending Promise.

Failed operations are removed from the cache.

This prevents a temporary failure from becoming a permanently cached result.

### Weighted Interval Scheduling

Weighted interval scheduling selects non-overlapping jobs to maximize total benefit.

Each job has:

- Identifier
- Start time
- End time
- Profit

Two jobs are compatible when the earlier job finishes no later than the next job starts.

The implementation sorts jobs by finishing time.

Binary search identifies the latest compatible predecessor.

The recurrence is:

\[
DP(i)=\max(P_i+DP(p(i)),DP(i-1))
\]

Here, \(p(i)\) is the index of the latest compatible job.

Complexity:

- Sorting: \(O(n\log n)\)
- Predecessor calculation: \(O(n\log n)\)
- DP calculation: \(O(n)\)
- Reconstruction: \(O(n)\)

Total time complexity is \(O(n\log n)\).

### Event-Driven Execution

`DynamicProgrammingEngine` extends Node.js `EventEmitter`.

It exposes three events:

| Event | Meaning |
|---|---|
| `started` | A computation has begun |
| `completed` | A computation finished successfully |
| `failed` | A computation encountered an error |

The engine tracks running tasks and completed results.

A task cannot be started again under the same identifier while it is already running.

This separates computation from execution monitoring.

### Budget Optimization

`BudgetOptimizer` applies 0/1 knapsack to project selection.

It evaluates projects under a fixed budget and returns a selected portfolio.

The implementation demonstrates why reconstruction information must be maintained separately when using a one-dimensional optimization array.

## 5. C++17 Implementation

The C++ implementation focuses on efficient resource allocation and explicit state management.

### FibonacciSolver

The class uses:

- `vector<uint64_t>` for cached results.
- `vector<bool>` for computed-state tracking.
- A recursive private calculation method.

The implementation restricts the Fibonacci index to 92 because the result must fit in an unsigned 64-bit integer.

### PortfolioOptimizer

This class implements memoized project selection.

The state is:

\[
DP(i,w)
\]

where:

- \(i\) is the current project.
- \(w\) is the remaining budget.

The cache is represented by two-dimensional vectors.

The separate Boolean table distinguishes an uncomputed state from a computed state whose optimal value happens to be zero.

This is an important state-management decision.

### Tabulation

`solveTabulated()` constructs the complete DP table.

It retains the previous project row when calculating the current project row.

This enforces the 0/1 restriction because the current project cannot be selected repeatedly.

### Space Optimization

`solveSpaceOptimized()` reduces the two-dimensional table to one dimension.

The capacity loop moves in descending order.

This iteration direction is essential.

If capacity moved upward, the same project could contribute multiple times to the same solution, changing the problem into unbounded knapsack.

### Longest Common Subsequence

The C++ implementation reconstructs a common subsequence using the completed DP table.

It uses STL containers and algorithms rather than external libraries.

### Engineering Considerations

The implementation includes:

- Project identifier validation.
- Duplicate detection.
- Budget restrictions.
- Integer-boundary validation.
- Exception handling.
- State tracking.
- Result reconstruction.
- Automated consistency tests.

The full knapsack table offers straightforward reconstruction.

The space-optimized implementation reduces memory usage but does not independently retain enough information to reconstruct the selected projects.

## 6. Java 17 Implementation

The Java implementation models dynamic programming as an enterprise resource-allocation service.

### Domain Modeling

Java records represent immutable business data.

The main domain types are:

| Type | Responsibility |
|---|---|
| `Project` | Defines a resource-consuming project |
| `ScheduledTask` | Defines a time-bounded task |
| `AllocationPolicy` | Defines resource-allocation restrictions |
| `OptimizationResult` | Represents an optimization result |
| `SchedulingResult` | Represents a scheduling result |

Immutable records reduce accidental changes to business inputs during optimization.

### AllocationPolicy

The allocation policy validates:

- Maximum budget.
- Maximum number of projects.
- Project identifier uniqueness.
- Project value requirements.

Separating policy validation from optimization makes the service easier to maintain.

A project can be mathematically feasible but still violate an enterprise policy.

These are different conditions.

### ResourceAllocationService

The service supports two algorithms through the `Algorithm` enum:

- `MEMOIZATION`
- `TABULATION`

The public `optimize()` method delegates to the appropriate implementation.

Both algorithms produce the same result structure.

This makes their behavior comparable without exposing their internal calculation mechanisms.

### TaskSchedulingService

This service implements weighted interval scheduling.

Only tasks with `APPROVED` status can participate.

The service:

1. Validates task identifiers.
2. Checks task eligibility.
3. Sorts tasks by finishing time.
4. Finds compatible predecessors.
5. Calculates optimal scheduling values.
6. Reconstructs the selected tasks.

The status restriction represents a business rule rather than a mathematical requirement of dynamic programming.

### State and Failure Management

Custom exceptions distinguish optimization failures from policy violations.

The implementation also uses immutable input lists and immutable result collections.

These choices reduce unintended modification of data during calculation.

## 7. PostgreSQL Implementation

The PostgreSQL implementation provides a relational model for storing optimization inputs, executions, intermediate states, and final results.

### Database Architecture

The principal relationship is:

    Projects
       |
       v
    Optimization Runs
       |
       v
    Run Project Snapshots
       |
       v
    DP States
       |
       v
    Selected Projects
       |
       v
    Optimization Reports

### Projects

The `projects` table stores the project catalog.

Each project contains:

- Project identifier.
- Project code.
- Project name.
- Resource cost.
- Expected value.
- Approval status.
- Creation timestamp.

Check constraints prevent invalid costs and negative values.

The project status separates proposed and rejected projects from approved optimization inputs.

### Optimization Runs

The `optimization_runs` table represents an individual execution.

It records:

- Selected algorithm.
- Available budget.
- Execution status.
- Maximum achievable value.
- Total allocated resources.
- Number of computed states.
- Completion time.
- Error information.

The execution status distinguishes pending, running, completed, and failed calculations.

### Run Project Snapshots

A snapshot is important because the original project catalog may change.

An optimization run must use the project costs and values that existed when its inputs were captured.

The `run_projects` table therefore stores a copy of the relevant project attributes.

This prevents subsequent catalog modifications from silently changing the meaning of an earlier optimization result.

### DP States

The `dp_states` table persists intermediate calculations.

Its composite primary key is:

`(run_id, item_index, remaining_budget)`

This identifies one state within one optimization execution.

The table records:

- Item index.
- Remaining budget.
- Maximum achievable value.
- Selected project identifiers.

The primary key prevents duplicate state records for the same execution and capacity.

The resulting table can be inspected to understand how the optimum develops as more projects become available.

### Selected Projects

The `selected_projects` table stores the final reconstructed solution.

It connects an optimization run to the selected projects.

It also records the allocated cost and realized value.

Foreign keys maintain referential integrity.

### Procedures and Functions

`create_optimization_run()` creates an execution and captures approved projects.

`execute_knapsack()` performs bottom-up tabulation.

It:

1. Validates the execution.
2. Initializes the base states.
3. Iterates through project snapshots.
4. Evaluates inclusion and exclusion decisions.
5. Stores each DP state.
6. Reconstructs the selected projects.
7. Calculates total resource consumption.
8. Updates the execution result.

The function also records failure information before propagating an error.

### Triggers and Constraints

The snapshot-validation trigger checks that an individual project does not exceed the available budget.

Database constraints independently enforce basic integrity requirements.

This division is intentional:

- Constraints enforce persistent data rules.
- Triggers enforce cross-table validation.
- Procedures implement multi-step database workflows.
- Functions perform algorithmic calculations.

### Reporting

The database provides views and queries for:

- Project value-per-resource-unit analysis.
- Completed optimization runs.
- Selected project retrieval.
- Resource utilization.
- State inspection.
- Algorithm comparison.
- Eligibility determination.
- Aggregated optimization performance.

The database also includes execution diagnostics through `EXPLAIN`.

## 8. Practical Dynamic Programming Problems

The implementations cover several distinct problem categories.

| Problem | State | Main Technique | Complexity |
|---|---|---|---|
| Fibonacci | Previous sequence positions | Memoization / Tabulation | \(O(n)\) |
| Grid paths | Grid coordinates | Tabulation | \(O(RC)\) |
| 0/1 Knapsack | Item and remaining capacity | Memoization / Tabulation | \(O(nW)\) |
| Longest common subsequence | Two sequence positions | Tabulation | \(O(nm)\) |
| Weighted interval scheduling | Sorted job position | Tabulation + binary search | \(O(n\log n)\) |

These problems illustrate different state structures.

Fibonacci uses a one-dimensional dependency.

Grid path counting uses spatial dependencies.

Knapsack uses decisions involving both item position and remaining capacity.

LCS uses two sequence positions.

Weighted interval scheduling uses compatibility between previously completed intervals.

## 9. Important Algorithmic Distinctions

### 0/1 Knapsack Versus Unbounded Knapsack

These problems have different selection rules.

| Characteristic | 0/1 Knapsack | Unbounded Knapsack |
|---|---|---|
| Item reuse | At most once | Unlimited |
| Capacity iteration | Descending | Usually ascending |
| State dependency | Previous item layer | May reuse current item |
| Application | Unique projects | Repeatable resources |

The implementations use 0/1 knapsack because each enterprise project can be selected only once.

### Knapsack Versus Weighted Interval Scheduling

Both are optimization problems, but their constraints differ.

Knapsack restricts total resource consumption.

Weighted interval scheduling restricts overlapping time intervals.

The former uses a remaining-capacity state.

The latter uses a compatible predecessor state.

Their recurrences should not be treated as interchangeable.

### Optimization Value Versus Solution Reconstruction

A DP table can calculate an optimal numerical value without directly identifying the decisions that produced it.

Reconstruction requires retaining sufficient information to recover those decisions.

The implementations reconstruct selected projects or scheduled tasks by examining the DP states.

Tie-breaking also matters.

When inclusion and exclusion produce equal values, the examples generally prefer exclusion. This creates deterministic results without changing the maximum achievable objective value.

## 10. Complexity and Performance

Dynamic programming replaces repeated computation with state storage.

This improves execution time when the number of distinct states is substantially smaller than the number of recursive calls.

The trade-off is memory consumption.

| Technique | Main Advantage | Main Limitation |
|---|---|---|
| Memoization | Calculates required states | Cache memory and recursion |
| Tabulation | Predictable execution | May calculate unused states |
| Space optimization | Reduced memory | Reconstruction becomes harder |
| State reconstruction | Returns actual decisions | Requires additional information |
| Persistent DP states | Auditable calculations | Database storage overhead |

### State-Space Growth

A dynamic programming solution is not automatically efficient.

If a problem has a very large state space, storing every state can become impractical.

For example, knapsack has pseudo-polynomial complexity.

Its \(O(nW)\) complexity depends on the numerical capacity \(W\), not merely the number of bits needed to represent that capacity.

A capacity of several billion cannot be handled by directly allocating a corresponding DP table.

Practical systems should establish limits on:

- Number of input elements.
- Maximum capacity.
- Total state count.
- Available memory.
- Execution time.
- Numeric precision.

### Integer Safety

The Python implementation uses arbitrary-precision integers.

The JavaScript implementation uses `BigInt` for Fibonacci and grid-path calculations.

The C++ implementation uses unsigned 64-bit integers for bounded Fibonacci calculations.

The Java and PostgreSQL implementations use fixed-width integer types and therefore impose practical input limits.

These differences are important when selecting an implementation for large numerical workloads.

## 11. Validation, Security and Reliability

Dynamic programming systems require validation of both inputs and computed results.

Important controls include:

- Reject negative capacities.
- Reject invalid dimensions.
- Validate resource costs.
- Prevent duplicate identifiers.
- Restrict project eligibility.
- Enforce maximum input sizes.
- Check resource consumption after reconstruction.
- Avoid accepting invalid scheduling intervals.
- Handle arithmetic limits.
- Prevent failed asynchronous calculations from remaining cached.

The PostgreSQL implementation also uses:

- Primary keys.
- Foreign keys.
- Unique constraints.
- Check constraints.
- Referential integrity.
- Execution status tracking.
- Input snapshots.

For production deployment, database execution should run with restricted privileges.

Application access should be limited to authorized procedures and tables.

Expensive optimization jobs should have execution limits and resource monitoring.

Persisting intermediate states can improve auditability, but it increases storage requirements and write overhead.

## 12. Implementation Execution

| File | Runtime | Execution |
|---|---|---|
| Python | Python 3.10+ | `python dynamic_programming.py` |
| JavaScript | Node.js 18+ | `node dynamic_programming.js` |
| C++17 | C++17 compiler | `g++ -std=c++17 -O2 dynamic_programming.cpp -o dynamic_programming` |
| Java | Java 17 | `javac DynamicProgramming.java` followed by `java DynamicProgramming` |
| PostgreSQL | PostgreSQL 15+ | Execute the SQL script against a database |

The PostgreSQL script creates its own `dynamic_programming` schema.

Its sample execution creates two optimization runs and evaluates their project portfolios.

The SQL execution assumes a database role with schema, table, procedure, function, and type creation privileges.

## 13. Learning Outcomes

The implementations establish the following technical distinctions:

- Memoization stores recursively calculated results.
- Tabulation constructs solutions iteratively.
- Optimal substructure allows larger optimal solutions to be constructed from smaller optimal solutions.
- Overlapping subproblems explain why caching avoids repeated computation.
- State definition determines what information a DP algorithm must retain.
- Recurrence relations determine dependencies between states.
- Reconstruction converts optimal numerical results into actionable decisions.
- Space optimization reduces storage but can complicate reconstruction.
- Validation ensures that mathematically optimal results also satisfy application constraints.

The central engineering decision in dynamic programming is identifying a correct state representation and recurrence before choosing between memoization, tabulation, or a space-optimized implementation.
