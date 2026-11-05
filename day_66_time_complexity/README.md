# Time Complexity and Asymptotic Analysis

## 1. Introduction

Time complexity describes how the computational work of an algorithm changes as its input size increases.

It provides a mathematical way to evaluate algorithms independently of specific hardware, programming languages, processor speeds, and execution environments.

The implementations in this project examine three principal asymptotic notations:

- Big-O: asymptotic upper bound.
- Big-Omega: asymptotic lower bound.
- Big-Theta: asymptotically tight bound.

The project also implements growth-function comparisons, operation counting, searching, sorting, benchmarking, and performance-policy evaluation.

## 2. Mathematical Foundations

### 2.1 Input size

Let `n` represent the size of an algorithm's input.

For an array, `n` is generally the number of elements.

For a graph, input size may depend on the number of vertices and edges:

- `V`: number of vertices.
- `E`: number of edges.

An algorithm's running time can be represented as a function:

`T(n)`

This function describes the number of elementary operations performed for an input of size `n`.

Actual execution time is affected by implementation details and hardware. Operation counts provide a more portable analytical model.

### 2.2 Big-O notation

Big-O specifies an asymptotic upper bound.

A function `f(n)` belongs to `O(g(n))` if there are positive constants `c` and `n₀` such that:

`0 ≤ f(n) ≤ c × g(n)` for every `n ≥ n₀`.

The constants and lower-order terms become less important as input size increases.

Example:

`f(n) = 3n² + 5n + 7`

Its asymptotic upper bound is:

`O(n²)`

Big-O is commonly used when discussing worst-case complexity, although the notation itself does not automatically mean worst case. It describes an upper bound on whichever function is being analyzed.

### 2.3 Big-Omega notation

Big-Omega specifies an asymptotic lower bound.

A function `f(n)` belongs to `Ω(g(n))` if positive constants `c` and `n₀` exist such that:

`f(n) ≥ c × g(n)` for every `n ≥ n₀`.

Example:

`f(n) = 3n² + 5n + 7`

Its asymptotic lower bound is:

`Ω(n²)`

Big-Omega is frequently used to discuss best-case behavior or minimum required work, but its mathematical meaning is a lower bound, not necessarily the best case.

### 2.4 Big-Theta notation

Big-Theta specifies a tight asymptotic bound.

A function `f(n)` belongs to `Θ(g(n))` if positive constants `c₁`, `c₂`, and `n₀` exist such that:

`c₁ × g(n) ≤ f(n) ≤ c₂ × g(n)`

for every `n ≥ n₀`.

For:

`f(n) = 3n² + 5n + 7`

the tight bound is:

`Θ(n²)`

This means the function grows at the same asymptotic rate as `n²`, up to constant factors.

### 2.5 Relationship between the notations

| Notation | Mathematical meaning | Main purpose |
|---|---|---|
| Big-O | Upper bound | Limits growth |
| Big-Omega | Lower bound | Establishes minimum growth |
| Big-Theta | Tight bound | Establishes matching growth rates |

An algorithm may have different best-case, average-case, and worst-case functions.

These cases must be analyzed separately.

For example, linear search has:

- Best case: `Θ(1)`.
- Average case: `Θ(n)` under common assumptions about target position.
- Worst case: `Θ(n)`.

Its worst-case upper bound is `O(n)`, and its worst-case tight bound is `Θ(n)`.

## 3. Common Complexity Classes

The seven classes implemented in the source files are presented below.

| Complexity | Name | Typical example |
|---|---|---|
| `O(1)` | Constant | Array indexing |
| `O(log n)` | Logarithmic | Binary search |
| `O(n)` | Linear | Linear search |
| `O(n log n)` | Linearithmic | Merge sort |
| `O(n²)` | Quadratic | Bubble sort |
| `O(n³)` | Cubic | Three nested loops |
| `O(2ⁿ)` | Exponential | Naive recursive Fibonacci |

### 3.1 Constant complexity

A constant-time operation performs a fixed amount of work independent of input size.

Example: retrieving an element using an array index.

`array[index]`

Its time complexity is `O(1)` under the usual random-access array model.

### 3.2 Logarithmic complexity

Logarithmic algorithms repeatedly reduce the remaining problem size by a constant factor.

Binary search divides a sorted search interval approximately in half at every iteration.

Its recurrence is:

`T(n) = T(n/2) + O(1)`

Therefore:

`T(n) = Θ(log n)`

The algorithm requires sorted input. Sorting the input separately introduces additional computational cost.

### 3.3 Linear complexity

Linear algorithms perform work proportional to the number of input elements.

A complete array traversal performs approximately `n` iterations.

`T(n) = Θ(n)`

Linear search demonstrates this behavior.

### 3.4 Linearithmic complexity

Merge sort divides an input into smaller parts, sorts the parts recursively, and merges the results.

Its recurrence is:

`T(n) = 2T(n/2) + Θ(n)`

The resulting complexity is:

`Θ(n log n)`

Its auxiliary memory requirement is generally `O(n)` for the implementations provided.

### 3.5 Quadratic complexity

Two complete nested loops commonly produce:

`T(n) = n × n`

Therefore:

`T(n) = Θ(n²)`

Bubble sort is a practical example.

An optimized bubble sort can terminate early when no swaps occur. Its best-case complexity is `Θ(n)`, while its average- and worst-case complexity remains `Θ(n²)`.

### 3.6 Cubic complexity

Three nested loops, each traversing the input, produce:

`T(n) = Θ(n³)`

Such algorithms become expensive quickly as the input grows.

### 3.7 Exponential complexity

Exponential algorithms may explore an increasing number of combinations or recursive branches.

Naive recursive Fibonacci repeatedly solves overlapping subproblems.

Its recurrence is:

`T(n) = T(n-1) + T(n-2) + O(1)`

Its growth is exponential.

Memoization or iterative dynamic programming reduces Fibonacci computation to `O(n)` time.

## 4. Growth-Rate Comparison

The following table compares representative growth functions.

| n | 1 | log₂(n) | n | n log₂(n) | n² | n³ |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 1 | 3.32 | 10 | 33.22 | 100 | 1,000 |
| 100 | 1 | 6.64 | 100 | 664.39 | 10,000 | 1,000,000 |
| 1,000 | 1 | 9.97 | 1,000 | 9,965.78 | 1,000,000 | 1,000,000,000 |

These values illustrate why algorithm selection matters.

A quadratic algorithm with an input of 1,000 elements may perform approximately one million iterations, while a linear algorithm performs approximately one thousand.

The exact operation count depends on the algorithm and implementation.

## 5. Asymptotic Analysis Techniques

### 5.1 Sequential statements

For sequential operations, their running times are added.

If:

`T(n) = O(n) + O(n²)`

then:

`T(n) = O(n²)`

The dominant term determines the asymptotic growth.

### 5.2 Nested loops

For two complete nested loops:

`T(n) = n × n = Θ(n²)`

For three complete nested loops:

`T(n) = n × n × n = Θ(n³)`

### 5.3 Triangular loops

Consider an outer loop with an inner loop that runs from zero to the current outer-loop index.

The total number of iterations is:

`1 + 2 + 3 + ... + n`

Using the arithmetic-series formula:

`T(n) = n(n + 1) / 2`

Therefore:

`T(n) = Θ(n²)`

The exact operation count differs from `n²`, but the asymptotic class is the same.

### 5.4 Logarithmic loops

A loop that repeatedly doubles a value until it reaches `n` performs approximately:

`log₂(n)` iterations.

A loop that repeatedly halves a value has the same asymptotic complexity.

### 5.5 Recurrence relations

Recursive algorithms can be analyzed using recurrence relations.

Examples:

| Algorithm | Recurrence | Complexity |
|---|---|---|
| Binary search | `T(n) = T(n/2) + O(1)` | `Θ(log n)` |
| Merge sort | `T(n) = 2T(n/2) + O(n)` | `Θ(n log n)` |
| Naive Fibonacci | `T(n) = T(n-1) + T(n-2) + O(1)` | Exponential |

The Master Theorem provides a systematic method for solving many divide-and-conquer recurrences.

For:

`T(n) = aT(n/b) + f(n)`

the values of `a`, `b`, and `f(n)` help determine the resulting asymptotic complexity.

## 6. Python Implementation

The Python script provides an executable analytical environment.

### Main components

| Component | Responsibility |
|---|---|
| `ComplexityClass` | Defines common complexity categories |
| `ComplexityBounds` | Stores upper, lower, and tight bounds |
| `BenchmarkResult` | Stores measurements |
| `linear_algorithm()` | Counts linear operations |
| `logarithmic_algorithm()` | Counts logarithmic iterations |
| `quadratic_algorithm()` | Counts nested-loop operations |
| `triangular_algorithm()` | Counts triangular-loop operations |
| `linearithmic_algorithm()` | Models linearithmic growth |
| `exponential_algorithm()` | Counts naive recursive Fibonacci calls |
| `linear_search()` | Implements sequential search |
| `binary_search()` | Implements binary search |
| `merge_sort()` | Implements divide-and-conquer sorting |
| `bubble_sort()` | Implements comparison-based sorting |

The benchmark mechanism records operation counts and elapsed time.

These measurements serve different purposes:

- Operation counts demonstrate algorithmic growth.
- Execution time measures actual runtime under the current environment.

Elapsed time should not be treated as a direct mathematical proof of asymptotic complexity.

The exponential demonstration limits its input size because recursive computation becomes expensive rapidly.

## 7. JavaScript Implementation

The JavaScript implementation uses an event-driven performance-analysis architecture.

### Main components

| Component | Responsibility |
|---|---|
| `ComplexityRegistry` | Stores complexity definitions |
| `ComplexityBound` | Represents mathematical bounds |
| `OperationCounter` | Maintains operation counts |
| `GrowthAnalyzer` | Evaluates growth functions |
| `SearchService` | Implements search algorithms |
| `SortingService` | Implements sorting algorithms |
| `PerformanceMonitor` | Publishes measurement events |
| `WorkloadRunner` | Executes asynchronous workloads |

The `Map` collection maintains complexity definitions, while private class fields protect internal state.

The `EventEmitter` publishes completed measurements.

The asynchronous runner yields to the Node.js event loop before starting a workload. The actual synchronous calculation still occupies the JavaScript execution thread while running.

This distinction matters when designing performance-sensitive Node.js services.

## 8. C++17 Implementation

The C++17 implementation emphasizes operation counting, modular design, and efficient data handling.

### Main components

| Component | Responsibility |
|---|---|
| `ComplexityAnalyzer` | Computes growth functions and operation counts |
| `SearchEngine` | Provides linear and binary search |
| `SortingEngine` | Provides merge sort and insertion sort |
| `PerformanceMonitor` | Records execution measurements |
| `Measurement` | Stores workload metrics |
| `ComplexityBounds` | Represents mathematical asymptotic bounds |

The sorting implementations use STL containers and standard algorithms for validation.

Merge sort creates additional vectors to divide and merge data. Its additional memory consumption is approximately linear.

Insertion sort modifies a copied vector and requires constant auxiliary space apart from the copied result.

The implementation uses validation limits to prevent unreasonable workloads and integer overflow in operation-count calculations.

## 9. Java 17 Implementation

The Java implementation models time complexity as part of an enterprise performance-governance workflow.

### Main components

| Component | Responsibility |
|---|---|
| `ComplexityClass` | Defines permitted complexity categories |
| `AlgorithmProfile` | Stores algorithm characteristics |
| `Workload` | Represents a submitted computational task |
| `PerformancePolicy` | Defines execution limits |
| `EvaluationResult` | Represents a governance decision |
| `AlgorithmService` | Executes search and sorting operations |
| `GovernanceService` | Evaluates workload eligibility |
| `AsyncWorkloadService` | Executes independent workloads asynchronously |

The policy service checks:

1. Whether the input size is within the permitted limit.
2. Whether the expected operation count is acceptable.
3. Whether the algorithm's complexity class is permitted.
4. Whether the workload identifier has already been registered.

An algorithm can be computationally valid but still fail an organizational performance policy.

This distinction separates algorithm correctness from operational eligibility.

The asynchronous service uses a bounded thread pool to execute independent workloads without creating an unrestricted number of threads.

## 10. PostgreSQL Implementation

The PostgreSQL script models a relational performance-governance system.

### 10.1 Database structure

The principal relationships are:

`complexity_definitions`

→ `algorithms`

→ `workloads`

→ `performance_policies`

`performance_policies`

→ `policy_allowed_complexities`

The database maintains algorithm classifications, permitted workloads, execution measurements, and policy decisions.

### 10.2 Main tables

| Table | Purpose |
|---|---|
| `complexity_definitions` | Stores Big-O, Big-Omega, and Big-Theta |
| `algorithms` | Registers algorithms and their complexity characteristics |
| `performance_policies` | Defines input and operation limits |
| `policy_allowed_complexities` | Defines permitted complexity classes |
| `workloads` | Stores submitted tasks and execution measurements |

### 10.3 Integrity controls

Primary keys identify records.

Foreign keys maintain relationships between algorithms, complexity classes, workloads, and policies.

Unique constraints prevent duplicate algorithm names, policy names, and workload codes.

Check constraints prevent invalid negative measurements and resource limits.

A trigger evaluates workload eligibility before insertion or relevant updates.

It rejects workloads that violate:

- Maximum input size.
- Maximum expected operation count.
- Permitted complexity classes.
- Active-policy requirements.

### 10.4 Stored functions

`evaluate_growth()` calculates representative growth-function values for an input size.

`check_asymptotic_bound()` evaluates an upper, lower, or tight bound using supplied mathematical values.

`complete_workload()` records execution measurements and checks the applicable performance limits.

`is_workload_eligible()` determines whether a workload has passed its initial policy evaluation.

### 10.5 Database reporting

The reporting views provide:

- Algorithm complexity classifications.
- Best-, average-, and worst-case descriptions.
- Auxiliary space requirements.
- Workload acceptance and rejection counts.
- Average execution times.
- Input-size statistics.
- Performance-policy outcomes.

Indexes support common workload filtering and retrieval patterns.

The `EXPLAIN` statement demonstrates how PostgreSQL presents query execution plans.

Database query-plan cost is an optimizer estimate. It should not be confused with the mathematical time complexity of an algorithm.

## 11. Searching: Complexity Comparison

### Linear search

Linear search examines elements sequentially.

| Case | Complexity |
|---|---|
| Best | `Θ(1)` |
| Average | `Θ(n)` |
| Worst | `Θ(n)` |
| Auxiliary space | `O(1)` |

It does not require sorted input.

### Binary search

Binary search repeatedly reduces the search interval.

| Case | Complexity |
|---|---|
| Best | `Θ(1)` |
| Average | `Θ(log n)` |
| Worst | `Θ(log n)` |
| Auxiliary space | `O(1)` for iterative implementation |

It requires sorted data and efficient random access for the standard array-based complexity guarantee.

### Practical comparison

| Property | Linear search | Binary search |
|---|---|---|
| Sorted input | Not required | Required |
| Best case | `O(1)` | `O(1)` |
| Worst case | `O(n)` | `O(log n)` |
| Implementation | Simple | Requires interval management |
| Suitable for | Small or unsorted collections | Large sorted collections |

## 12. Sorting: Complexity Comparison

| Algorithm | Best case | Average case | Worst case | Auxiliary space |
|---|---|---|---|---|
| Bubble sort with early exit | `O(n)` | `O(n²)` | `O(n²)` | `O(1)` |
| Insertion sort | `O(n)` | `O(n²)` | `O(n²)` | `O(1)` |
| Merge sort | `O(n log n)` | `O(n log n)` | `O(n log n)` | `O(n)` |

Merge sort is suitable for larger inputs requiring predictable comparison complexity.

Insertion sort can be useful for small or nearly sorted collections.

Bubble sort is mainly useful for demonstrating nested-loop behavior and the effect of early termination.

## 13. Time Complexity Versus Space Complexity

Time complexity measures computational work.

Space complexity measures memory consumption.

An algorithm may improve execution time by using additional memory.

For example:

| Algorithm | Time | Auxiliary space |
|---|---|---|
| Iterative binary search | `O(log n)` | `O(1)` |
| Recursive binary search | `O(log n)` | `O(log n)` |
| Merge sort | `O(n log n)` | `O(n)` |
| Insertion sort | `O(n²)` | `O(1)` |

The recursive binary search uses additional call-stack memory.

The iterative implementation avoids that recursion overhead.

An algorithm should therefore be evaluated using both time and space requirements.

## 14. Empirical Benchmarking

Empirical benchmarking measures actual execution behavior.

The project uses:

- Python `time.perf_counter()`.
- JavaScript `performance.now()`.
- C++ `std::chrono`.
- Java concurrent workload execution.
- PostgreSQL execution measurements.

A useful benchmark should control:

- Input size.
- Input distribution.
- Hardware conditions.
- Runtime version.
- Warm-up effects.
- Background processes.
- Memory availability.
- Number of repeated measurements.

For reliable comparisons, execute each workload multiple times and compare median or percentile measurements rather than relying on one execution.

Operation counts should be recorded separately from elapsed time.

An implementation that performs fewer operations is not automatically faster in every environment because memory access, cache behavior, allocation, and instruction costs also matter.

## 15. Common Analytical Mistakes

### Confusing Big-O with worst-case complexity

Big-O is a mathematical upper bound. Worst-case analysis is a choice of input-case model.

### Assuming every nested loop is quadratic

A nested loop does not automatically imply `O(n²)`.

Consider an inner loop that repeatedly halves its input. Its total work may be `O(n log n)` or another growth function depending on the loop structure.

### Ignoring input constraints

Binary search is not valid on unsorted input.

An algorithm's complexity claim must include its preconditions.

### Ignoring auxiliary memory

Recursive algorithms consume stack space, while divide-and-conquer sorting may allocate additional storage.

### Treating measurements as mathematical proofs

A benchmark only measures selected executions.

It cannot establish an asymptotic bound for every possible input size.

### Ignoring constant factors

Two algorithms with the same asymptotic complexity can have different practical performance.

Big-O notation does not describe every real-world performance difference.

## 16. Practical Applications

Time-complexity analysis is useful in:

- Selecting search and sorting algorithms.
- Designing database retrieval operations.
- Evaluating API request processing.
- Reviewing nested-loop data transformations.
- Planning large-scale data processing.
- Identifying computational bottlenecks.
- Designing resource limits.
- Evaluating algorithmic scalability.
- Establishing software performance policies.
- Reviewing the computational cost of recursive algorithms.

In production systems, complexity analysis should be combined with profiling, workload testing, memory analysis, and operational monitoring.

## 17. Execution Instructions

### Python

Save the first source file as `time_complexity.py`.

Run:

`python time_complexity.py`

### JavaScript

Save the second source file as `time_complexity.js`.

Run:

`node time_complexity.js`

### C++17

Save the third source file as `time_complexity.cpp`.

Compile:

`g++ -std=c++17 -O2 -Wall -Wextra -pedantic time_complexity.cpp -o time_complexity`

Run:

`./time_complexity`

### Java 17

Save the fourth source file as `Main.java`.

Compile:

`javac Main.java`

Run:

`java Main`

### PostgreSQL

Save the fifth source file as `time_complexity.sql`.

Execute:

`psql -U postgres -d postgres -f time_complexity.sql`

The SQL script creates the `complexity_lab` schema and its associated tables, functions, triggers, views, policies, and sample records.

## 18. Implementation Limitations

The implementations provide educational operation-count models and representative performance-governance mechanisms.

Their limitations include:

- Operation counts depend on which operations are selected for measurement.
- Growth-function values are mathematical estimates, not exact execution times.
- Empirical timings vary by runtime and hardware.
- The recursive Fibonacci example is intentionally restricted to small inputs.
- The PostgreSQL policy engine evaluates submitted metadata and measurements; it does not execute arbitrary application algorithms.
- The asymptotic bound evaluation function checks supplied numerical values and does not prove that a bound holds for all sufficiently large inputs.
- The JavaScript asynchronous workload runner does not make CPU-intensive synchronous algorithms execute in parallel.
- Input-size restrictions protect demonstrations from excessively expensive computations.

These distinctions are essential when moving from theoretical algorithm analysis to production performance engineering.
