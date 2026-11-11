# Recursion: Recursive Thinking, Recursion Trees, Base Cases, and Algorithms

## 1. Technical Scope

Recursion is a problem-solving technique in which a function solves a problem by calling itself on smaller instances of that problem.

A recursive solution requires three essential components:

1. A clearly defined input problem.
2. One or more base cases that terminate recursion.
3. A recursive case that reduces the original problem toward a base case.

The implementations in this repository examine recursion through mathematical computation, searching, sorting, hierarchical structures, dependency resolution, and relational database operations.

The central design principle is that each recursive call must make measurable progress toward termination.

## 2. Recursive Problem Decomposition

A recursive algorithm expresses a problem in terms of smaller instances of the same problem.

A general recurrence is:

\[
T(n)=aT(n/b)+f(n)
\]

Where:

- \(T(n)\) represents the execution cost.
- \(a\) represents the number of recursive subproblems.
- \(n/b\) represents the approximate size of each subproblem.
- \(f(n)\) represents the work performed outside recursive calls.

A recursive function can be represented mathematically as:

\[
F(n)=
\begin{cases}
B(n), & n \in \text{Base Cases}\\
R(F(n-1),n), & \text{Otherwise}
\end{cases}
\]

The base case supplies the result directly. The recursive case transforms the current problem into a smaller problem.

### Recursive execution example

Factorial is defined as:

\[
n!=n(n-1)!
\]

With:

\[
0!=1
\]

The execution for \(5!\) is:

\[
5!=5\times4\times3\times2\times1
\]

The call sequence is:

factorial(5)
    factorial(4)
        factorial(3)
            factorial(2)
                factorial(1)
                    return 1
                return 2
            return 6

This example demonstrates two execution phases:

- Descent: recursive calls are created.
- Unwinding: returned values are combined.

The call stack maintains the active function calls and their local execution state.

## 3. Base Cases and Termination

A base case is a condition that produces a result without another recursive call.

Without an appropriate base case, recursive execution can continue until the runtime exhausts its call stack.

A valid recursive algorithm must satisfy:

- At least one reachable base case exists.
- Recursive calls reduce the problem.
- The reduction eventually reaches a base case.
- Inputs are validated before expensive execution.
- Recursive results have clearly defined meanings.

### Types of base cases

| Problem | Base case |
|---|---|
| Factorial | `n <= 1` |
| Fibonacci | `n <= 1` |
| Binary search | `left > right` |
| Merge sort | List length is zero or one |
| Tree traversal | Node is null |
| Graph traversal | Node has already been completed |

A termination condition is not necessarily the same as an empty input.

For binary search, termination occurs when the search interval becomes invalid. For a tree traversal, termination occurs when the current node does not exist.

### Incorrect recursive progress

A function that repeatedly calls itself with the same input does not reduce its problem:

solve(n)
    solve(n)


A function that reduces its input can terminate:

```scss
solve(n)
    solve(n - 1)
```

The second structure still requires a valid base case and appropriate input constraints.

## 4. Recursion Trees

A recursion tree represents recursive calls as nodes in a tree.

Each node represents one subproblem. Its children represent the recursive calls created by that subproblem.

Consider:

\[
T(n)=2T(n/2)+n
\]

For an input of 16:

```r
                    T(16)
                  /       \
              T(8)         T(8)
             /   \         /   \
          T(4)  T(4)    T(4)  T(4)
          / \    / \     / \    / \
        T(2) ...              ...
```

The recursion tree has multiple levels.

At each level:

- The number of subproblems increases.
- The size of individual subproblems decreases.
- The total work depends on the cost of each node.

For merge sort, the work at each level is approximately proportional to \(n\).

The number of levels is:

\[
\log_2(n)
\]

Therefore:

\[
T(n)=O(n\log n)
\]

### Recursion-tree terminology

| Term | Meaning |
|---|---|
| Root | Original problem |
| Internal node | A problem that produces recursive calls |
| Leaf | A terminal or base-case problem |
| Level | Distance from the root |
| Height | Maximum depth of the tree |
| Branching factor | Number of children per node |
| Work per node | Non-recursive computation |
| Total work | Sum of work across all nodes |

The Python, JavaScript, and C++ implementations include bounded recursion-tree construction and display.

The display limit is important because constructing a complete tree for exponential recursion can itself consume excessive memory.

## 5. Recursive Algorithms and Their Complexity

### 5.1 Factorial

Factorial multiplies an integer by the factorial of its predecessor.

\[
F(n)=nF(n-1)
\]

Base case:

\[
F(0)=1
\]

Complexity:

- Time: \(O(n)\)
- Auxiliary space: \(O(n)\)

Each recursive call remains on the stack until the smaller factorial has been calculated.

### 5.2 Fibonacci

The Fibonacci sequence is:

\[
F(0)=0
\]

\[
F(1)=1
\]

\[
F(n)=F(n-1)+F(n-2)
\]

A direct recursive implementation creates overlapping subproblems.

For example, calculating \(F(5)\) requires calculations that overlap:

```r
                  F(5)
                /      \
             F(4)      F(3)
             /  \      /  \
          F(3) F(2)  F(2) F(1)
```

The same values are repeatedly calculated.

Complexity:

- Naive recursive time: \(O(2^n)\)
- Auxiliary stack space: \(O(n)\)

The implementations restrict naive Fibonacci inputs to avoid excessive computation.

### 5.3 Memoization

Memoization stores previously calculated results.

Before solving a subproblem, the algorithm checks whether its result is already available.

If it is available, the stored result is returned.

For Fibonacci:

\[
F(n)=F(n-1)+F(n-2)
\]

Each distinct input is calculated once.

Complexity:

- Time: \(O(n)\)
- Space: \(O(n)\)

The Python implementation uses a dictionary, JavaScript uses a `Map`, Java uses a `HashMap`, and PostgreSQL demonstrates persistent result storage.

Memoization is useful when recursive subproblems overlap.

It is less useful when every recursive call produces a completely different subproblem.

### 5.4 Binary Search

Binary search repeatedly divides a sorted search interval into two parts.

At each recursive call, one half is discarded.

\[
T(n)=T(n/2)+O(1)
\]

Complexity:

- Time: \(O(\log n)\)
- Auxiliary space: \(O(\log n)\) for recursive execution.

The implementation validates that the input is sorted before searching.

An absent target produces `-1`.

An empty collection terminates immediately.

### 5.5 Merge Sort

Merge sort follows divide-and-conquer.

Its execution consists of:

1. Divide the input into two halves.
2. Recursively sort both halves.
3. Merge the sorted halves.

The recurrence is:

\[
T(n)=2T(n/2)+O(n)
\]

Complexity:

- Time: \(O(n\log n)\)
- Auxiliary space: \(O(n)\)

The implementations use a separate merge operation to combine sorted subproblems.

Merge sort also handles empty collections, single-element collections, duplicate values, and negative integers.

## 6. Recursive Data Structures

Recursion is particularly useful for structures that contain smaller structures of the same type.

A binary tree is a common example.

Each node contains:

- A value.
- A left child.
- A right child.

A tree can be defined recursively:

\[
Tree = Node(value,left,right)
\]

A missing child represents a base case.

### Tree traversal

Three common depth-first traversal orders are implemented.

| Traversal | Execution order |
|---|---|
| Preorder | Root, left, right |
| Inorder | Left, root, right |
| Postorder | Left, right, root |

Example:

```
              10
             /  \
            5    15
           / \     \
          2   7     20
```

Expected traversals:

| Method | Result |
|---|---|
| Preorder | 10, 5, 2, 7, 15, 20 |
| Inorder | 2, 5, 7, 10, 15, 20 |
| Postorder | 2, 7, 5, 20, 15, 10 |

For a tree containing \(V\) nodes:

- Time: \(O(V)\)
- Auxiliary space: \(O(h)\), where \(h\) is the tree height.

A balanced tree has logarithmic height. A highly unbalanced tree can have linear height.

The implementations also detect repeated node references where applicable.

## 7. Recursive Graph and Dependency Processing

Recursive algorithms are not restricted to mathematical sequences or trees.

They can process dependency graphs, organizational structures, nested directories, and hierarchical business data.

A dependency graph represents relationships between tasks.

For example:

```yaml
Compile
   |
   v
Build
   |
   v
Unit Test
   |
   v
Integration Test
   |
   v
Deploy
```

A task cannot execute until its prerequisites have been completed.

Depth-first search provides a natural way to calculate a valid execution order.

### Graph traversal states

| State | Meaning |
|---|---|
| Unvisited | Task has not been examined |
| Active | Task is currently being explored |
| Complete | Task and its dependencies have been processed |

The active state detects cycles.

Consider:

```arduino
Task A -> Task B
Task B -> Task C
Task C -> Task A
```

This graph cannot have a valid topological execution order.

The dependency implementations reject this situation instead of entering an endless traversal.

For a directed acyclic graph:

- Time: \(O(V+E)\)
- Space: \(O(V)\)

Where \(V\) is the number of vertices and \(E\) is the number of edges.

## 8. Python Implementation

The Python implementation provides a measurable recursion engine.

### Main components

| Component | Responsibility |
|---|---|
| `RecursionEngine` | Manages recursive algorithms |
| `RecursionMetrics` | Tracks calls, depth, cache hits, and comparisons |
| `RecursionNode` | Represents a recursion-tree node |
| `TreeNode` | Represents a binary tree |
| `Algorithm` | Identifies supported algorithms |
| `InvalidInputError` | Handles invalid inputs |
| `RecursionLimitError` | Handles depth-budget violations |

### Implemented mechanisms

- Direct recursive factorial.
- Naive recursive Fibonacci.
- Memoized Fibonacci.
- Iterative Fibonacci comparison.
- Recursive binary search.
- Merge sort.
- Preorder, inorder, and postorder traversal.
- Recursion-tree construction.
- Recursive filesystem-size calculation.
- Automated assertions.
- Optional JSON reporting.

The filesystem operation ignores symbolic links. This avoids following external paths and reduces the risk of recursive filesystem cycles.

The script uses the standard library and does not require third-party packages.

## 9. JavaScript Implementation

The JavaScript implementation uses event-driven monitoring and asynchronous operations.

### Main components

| Component | Responsibility |
|---|---|
| `ExecutionMonitor` | Tracks recursive execution |
| `EventEmitter` | Publishes recursive-call and cache-hit events |
| `DependencyEngine` | Resolves dependency graphs |
| `BinaryTreeNode` | Models binary tree nodes |
| `RecursionBudgetError` | Controls excessive recursion |
| `CycleDetectedError` | Reports circular dependencies |

### Distinct implementation decisions

The `Map` structure supports memoization.

The `Set` structure tracks dependency states.

`WeakSet` tracks visited tree objects without requiring explicit cleanup.

The asynchronous tree-sum implementation uses `async` functions and `await` to demonstrate recursive asynchronous execution.

Directory traversal uses Node.js filesystem promises.

The implementation separates:

- Mathematical computation.
- Dependency evaluation.
- Tree traversal.
- Filesystem operations.
- Event reporting.

This separation makes it easier to monitor recursive execution without embedding reporting logic into every algorithm.

JavaScript uses `Number` for ordinary numeric computation, so precision and overflow restrictions are validated. BigInt is used where larger exact Fibonacci results are needed.

## 10. C++17 Implementation

The C++ implementation emphasizes explicit resource management, domain modeling, and algorithmic efficiency.

### Main components

| Component | Responsibility |
|---|---|
| `RecursionEngine` | Executes recursive algorithms |
| `Metrics` | Maintains execution measurements |
| `TreeNode` | Models a binary tree |
| `RecursionTreeNode` | Represents recursive call decomposition |
| `DependencyGraph` | Resolves task dependencies |
| `TraversalOrder` | Defines traversal behavior |
| `unique_ptr` | Manages tree-node ownership |

### Important implementation decisions

The binary tree uses `unique_ptr` to establish clear ownership.

Merge sort uses a reusable auxiliary vector rather than allocating a new merge buffer at every recursive level.

Memoized Fibonacci uses an `unordered_map`.

The dependency resolver uses depth-first search with three execution states.

Custom exceptions distinguish validation failures from depth-limit failures.

The implementation avoids external libraries and is compatible with C++17.

## 11. Java 17 Enterprise Implementation

The Java implementation models recursive computation as a structured enterprise service.

### Domain types

| Type | Responsibility |
|---|---|
| `RecursionContext` | Controls recursion execution |
| `MetricsCollector` | Maintains execution measurements |
| `ComputationResult` | Stores an immutable computation result |
| `DependencyTask` | Represents a task and its prerequisites |
| `TreeNode` | Represents a binary tree |
| `DependencyService` | Calculates dependency order |
| `TreeService` | Performs recursive tree operations |
| `ComputationService` | Manages computation execution |

Java records provide immutable data-transfer structures.

Enums represent traversal orders and computation states.

The dependency service maintains explicit execution states.

The service layer separates computation from orchestration and result reporting.

`Math.addExact` and `Math.multiplyExact`-style arithmetic checks are relevant when adapting these algorithms to larger numerical workloads. The implemented Fibonacci method uses checked addition.

The implementation also demonstrates how recursive methods can be placed behind service interfaces and domain-specific validation boundaries.

## 12. PostgreSQL Recursive Implementation

PostgreSQL supports recursion through recursive common table expressions.

The standard structure is:

```sql
WITH RECURSIVE hierarchy AS (
    -- Initial rows
    SELECT ...

    UNION ALL

    -- Recursive rows
    SELECT ...
    FROM source_table
    JOIN hierarchy
        ON ...
)
SELECT *
FROM hierarchy;
```

The initial query establishes the anchor rows.

The recursive query generates the next level using the previous result.

Execution continues until the recursive query produces no additional rows.

### Database entities

| Table | Purpose |
|---|---|
| `organizations` | Stores organizational units |
| `employees` | Stores employees and manager relationships |
| `projects` | Stores project records |
| `tasks` | Stores hierarchical project tasks |
| `task_dependencies` | Stores prerequisite relationships |
| `fibonacci_cache` | Stores previously calculated Fibonacci values |

### Recursive database mechanisms

**Employee hierarchy**

The `employee_hierarchy` view calculates management levels, employee paths, and reporting relationships.

**Task hierarchy**

The `task_hierarchy` view recursively follows parent-task relationships.

**Dependency processing**

The dependency function derives execution levels from prerequisite relationships.

**Project aggregation**

The project-effort view calculates task counts and total estimated hours.

**Mathematical recursion**

The factorial and Fibonacci functions demonstrate recursive computation within PL/pgSQL.

**Persistent memoization**

The Fibonacci cache stores previously calculated results in a relational table.

**Cycle prevention**

Triggers detect cycles in management hierarchies, task hierarchies, and task dependencies.

**Transactional processing**

The `complete_task` procedure verifies prerequisite completion before changing a task's status.

The implementation uses foreign keys, check constraints, unique constraints, and indexes to enforce relational integrity.

## 13. Important Distinctions

### Recursion versus iteration

| Characteristic | Recursion | Iteration |
|---|---|---|
| Execution | Function calls itself | Repeated loop execution |
| State | Call stack | Explicit variables |
| Termination | Base condition | Loop condition |
| Memory | Often proportional to depth | Often constant auxiliary space |
| Suitability | Trees and divide-and-conquer | Sequential repetition |

Recursion can express hierarchical problems more naturally.

Iteration can be preferable when recursion depth is large or stack usage must be minimized.

### Recursion versus memoization

Recursion defines how a problem is decomposed.

Memoization defines how previously calculated results are reused.

They are complementary techniques rather than competing algorithms.

### Recursion versus divide-and-conquer

Recursion is a method of function decomposition.

Divide-and-conquer is an algorithmic strategy that divides a problem into smaller subproblems, solves them, and combines their results.

Merge sort uses both techniques.

### Recursion versus backtracking

Backtracking explores alternative choices and reverses decisions when a partial solution cannot lead to a valid complete solution.

Typical applications include:

- Constraint satisfaction.
- Permutation generation.
- Maze solving.
- Combinatorial search.

Backtracking is a specialized recursive search strategy.

## 14. Complexity Reference

| Algorithm | Time | Auxiliary space |
|---|---|---|
| Factorial | \(O(n)\) | \(O(n)\) |
| Naive Fibonacci | \(O(2^n)\) | \(O(n)\) |
| Memoized Fibonacci | \(O(n)\) | \(O(n)\) |
| Iterative Fibonacci | \(O(n)\) | \(O(1)\) |
| Binary search | \(O(\log n)\) | \(O(\log n)\) |
| Merge sort | \(O(n\log n)\) | \(O(n)\) |
| Tree traversal | \(O(V)\) | \(O(h)\) |
| Dependency resolution | \(O(V+E)\) | \(O(V)\) |

Here:

- \(n\) is the input size.
- \(V\) is the number of tree or graph vertices.
- \(E\) is the number of graph edges.
- \(h\) is the maximum tree or traversal depth.

Actual runtime also depends on allocation costs, data representation, cache behavior, runtime stack limits, and the cost of combining recursive results.

## 15. Validation and Failure Conditions

The implementations handle important recursive failure conditions.

| Condition | Handling |
|---|---|
| Negative factorial input | Reject |
| Negative Fibonacci input | Reject |
| Excessive input | Enforce configured limit |
| Invalid binary-search ordering | Reject |
| Missing binary-search target | Return `-1` |
| Empty sorting input | Return empty collection |
| Null tree node | Treat as a base case |
| Repeated tree node | Detect invalid structure |
| Circular dependency | Raise an error |
| Excessive recursion depth | Reject execution |
| Unknown dependency | Reject graph |
| Missing filesystem path | Report filesystem failure |
| Unfinished prerequisite | Reject task completion |

Validation is important because a recursive algorithm can be mathematically correct but operationally unsafe when it receives malformed input.

## 16. Performance and Security Considerations

### Stack consumption

Each recursive call can allocate a stack frame.

Deep recursion can cause stack overflow even when the algorithm's total computational work is reasonable.

Depth budgets provide a basic operational safeguard.

They do not replace algorithm-specific resource limits.

### Exponential computation

Naive Fibonacci is computationally expensive because it repeatedly evaluates overlapping subproblems.

Memoization or iteration should be preferred for larger inputs.

### Memory allocation

Recursive algorithms can allocate many temporary objects.

Merge sort benefits from reusing auxiliary storage.

Tree structures require careful ownership and cycle handling.

### Graph cycles

Dependency graphs must be validated before execution.

A cycle prevents a valid topological ordering.

Three-state depth-first search identifies cycles in linear time relative to graph size.

### Filesystem safety

Recursive directory inspection should:

- Avoid following symbolic links unless explicitly required.
- Handle permission failures.
- Limit traversal depth.
- Avoid unrestricted traversal of untrusted directories.
- Consider concurrent filesystem changes.

### Database safety

Recursive queries should use suitable indexes on parent and dependency columns.

Cycle prevention must account for concurrent transactions when the application permits simultaneous hierarchy updates. Trigger-based checks alone are not a substitute for an appropriate concurrency-control strategy.

Persistent caches require a clear consistency policy when computation definitions or input rules change.

### Numeric precision

Different languages have different numeric limits.

- Python integers support arbitrary-precision integer arithmetic.
- JavaScript `Number` uses IEEE 754 floating-point representation.
- JavaScript `BigInt` supports arbitrary-precision integers.
- C++17 integer types have fixed ranges.
- Java primitive integer types have fixed ranges.
- PostgreSQL `NUMERIC` supports arbitrary-precision decimal arithmetic within configured limits.

Numeric constraints should be part of the algorithm's input contract.

## 17. Execution and Verification

### Python

Run the script:

`python recursion.py`

Run assertions:

`python recursion.py --tests`

Generate a JSON report:

`python recursion.py --output recursion-report.json`

Inspect a directory recursively:

`python recursion.py --directory ./sample-data`

The report file is created exclusively. Existing files are not overwritten.

### JavaScript

Run:

`node recursion.js`

The program displays recursive-call events, cache hits, execution order, traversal results, and performance measurements.

### C++17

Compile:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic recursion.cpp -o recursion`

Run:

`./recursion`

### Java 17

Compile:

`javac RecursionEnterprise.java`

Run with assertions enabled:

`java -ea RecursionEnterprise`

### PostgreSQL

Execute the SQL script using:

`psql -U postgres -d your_database -f recursion.sql`

The script creates the `recursion_lab` schema and its database objects.

The database user needs permission to create schemas, tables, functions, procedures, and triggers.

The script includes sample data, reporting queries, recursive functions, validation mechanisms, and a transaction demonstration.

## 18. Learning Outcomes

The five implementations establish practical distinctions between:

- Recursive definitions and recursive execution.
- Base cases and recursive cases.
- Call-stack behavior and result unwinding.
- Recursion trees and execution complexity.
- Naive recursion and memoization.
- Recursive search and divide-and-conquer.
- Tree traversal and graph traversal.
- Dependency resolution and cycle detection.
- Recursive computation and persistent database queries.
- Algorithmic correctness and operational safety.

The most important property of a recursive algorithm is not simply that it calls itself. Its recursive structure must reduce a well-defined problem, preserve the correctness of intermediate results, and guarantee a valid termination condition.

        return 24
    return 120
