# Greedy Algorithms: Optimization, Scheduling and Huffman Coding

## 1. Technical Scope

Greedy algorithms solve optimization problems by repeatedly selecting a locally optimal candidate according to a defined decision rule.

A greedy algorithm generally performs the following operations:

1. Establish a set of available candidates.
2. Evaluate candidates using a selection criterion.
3. Select the best currently eligible candidate.
4. Update the problem state.
5. Repeat until the termination condition is reached.

The main engineering question is whether locally optimal decisions produce a globally optimal solution.

This project implements three important greedy applications:

- Activity selection for interval scheduling.
- Fractional knapsack for resource allocation.
- Huffman coding for lossless prefix-code construction.

It also demonstrates a counterexample involving 0/1 knapsack, where the same value-to-weight greedy strategy does not guarantee an optimal result.

## 2. Greedy Algorithm Fundamentals

### 2.1 Greedy-choice property

The greedy-choice property states that an optimal solution can be constructed by making an appropriate locally optimal choice first and extending that choice into an optimal solution for the remaining problem.

The important distinction is that not every locally attractive decision is globally optimal.

A valid greedy algorithm requires a problem-specific justification for its selection rule.

For example:

| Problem | Greedy decision | Result |
|---|---|---|
| Activity selection | Select the compatible activity with earliest finishing time | Optimal maximum-cardinality schedule |
| Fractional knapsack | Select the item with highest value-to-weight ratio | Optimal fractional allocation |
| Huffman coding | Merge two minimum-frequency nodes | Optimal prefix-code tree |
| 0/1 knapsack | Select the highest value-to-weight ratio | Not generally optimal |

### 2.2 Optimal substructure

Optimal substructure means that an optimal solution contains optimal solutions to relevant smaller subproblems.

A greedy algorithm can exploit this property when its choices also preserve the possibility of completing an optimal solution.

Optimal substructure alone does not establish that a greedy strategy is correct.

### 2.3 Feasibility and objective functions

A greedy implementation must distinguish between:

- Feasibility: whether a candidate satisfies the problem constraints.
- Selection criterion: how eligible candidates are ranked.
- Objective function: what the complete solution attempts to maximize or minimize.
- State transition: how selecting a candidate changes the remaining problem.

For example, activity scheduling maximizes the number of non-overlapping activities, whereas fractional knapsack maximizes the total allocated value under a capacity constraint.

The algorithms therefore use different decision rules.

## 3. Activity Selection

### 3.1 Problem definition

Activity selection considers activities with starting and finishing times.

Two activities are compatible when their time intervals do not overlap.

For activities represented by intervals `[start, finish)`, compatibility is defined as:

`next.start >= previous.finish`

The objective is to select the maximum number of mutually compatible activities.

### 3.2 Greedy-choice rule

The optimal strategy is to select the compatible activity with the earliest finishing time.

The reasoning is that an activity finishing earlier leaves at least as much remaining time as an activity finishing later.

The earliest-finishing activity therefore preserves the largest possible scheduling opportunity for subsequent activities.

### 3.3 Algorithm workflow

The implementation follows this sequence:

1. Validate all activity records.
2. Reject duplicate identifiers.
3. Sort activities by finishing time.
4. Use starting time and identifier as deterministic tie-breakers.
5. Select the first compatible activity.
6. Update the last selected finishing time.
7. Reject activities that overlap the selected schedule.

The sorting operation determines the candidate order. The selection operation maintains the scheduling boundary.

### 3.4 Example

| Activity | Start | Finish |
|---|---:|---:|
| A101 | 1 | 4 |
| A102 | 3 | 5 |
| A103 | 0 | 6 |
| A104 | 5 | 7 |
| A105 | 8 | 9 |
| A106 | 5 | 9 |
| A107 | 2 | 3 |

The selected activities are:

`A107 -> A101 -> A104 -> A105`

The selected intervals do not overlap.

The algorithm returns both selected and rejected activities, allowing the complete decision process to be inspected.

### 3.5 Correctness argument

Consider an optimal schedule whose first activity finishes later than the earliest-finishing compatible activity.

Replacing that first activity with the earliest-finishing activity cannot reduce the available time for subsequent activities.

Therefore, there exists an optimal schedule containing the greedy first choice.

After selecting that activity, the remaining problem consists of selecting compatible activities beginning at or after its finishing time.

Applying the same argument recursively establishes the optimality of the algorithm.

### 3.6 Complexity

Let `n` represent the number of activities.

| Operation | Complexity |
|---|---|
| Validation | O(n) expected with hashing |
| Sorting | O(n log n) |
| Greedy selection | O(n) |
| Total time | O(n log n) |
| Auxiliary storage | O(n) |

If the activities are already sorted by finishing time, the selection phase requires O(n) time.

## 4. Fractional Knapsack

### 4.1 Problem definition

Fractional knapsack maximizes total value subject to a fixed weight capacity.

Each item has:

- A value.
- A weight.
- A value-to-weight ratio.

Unlike 0/1 knapsack, fractional knapsack permits partial allocation of an item.

For item \(i\), define:

\[
r_i = \frac{v_i}{w_i}
\]

where:

- \(v_i\) is the item's value.
- \(w_i\) is its weight.
- \(r_i\) is its value per unit of weight.

### 4.2 Greedy-choice rule

Select items in descending order of value-to-weight ratio.

Allocate the complete item when sufficient capacity remains.

Otherwise, allocate the maximum fraction that fits.

The algorithm stops when capacity is exhausted or no items remain.

### 4.3 Allocation formula

For an item with weight \(w_i\), remaining capacity \(C\), and available allocation fraction \(x_i\):

\[
x_i = \min\left(1,\frac{C}{w_i}\right)
\]

The allocated value is:

\[
V_i = x_i v_i
\]

The allocated weight is:

\[
W_i = x_i w_i
\]

The total objective is:

\[
V_{\text{total}} = \sum_i x_i v_i
\]

Subject to:

\[
\sum_i x_i w_i \leq C
\]

and:

\[
0 \leq x_i \leq 1
\]

### 4.4 Example

| Item | Value | Weight | Ratio |
|---|---:|---:|---:|
| Gold | 60 | 10 | 6 |
| Silver | 100 | 20 | 5 |
| Copper | 120 | 30 | 4 |

Available capacity: 50.

The allocation is:

- Gold: 100%.
- Silver: 100%.
- Copper: 66.67%.

The resulting value is:

\[
60 + 100 + 120\left(\frac{20}{30}\right)
= 240
\]

The remaining capacity is zero.

### 4.5 Why fractional allocation matters

The greedy strategy works because the decision can be expressed in terms of value per unit of weight.

If an allocation contains a lower-ratio item while a higher-ratio item remains partially unallocated, transferring weight toward the higher-ratio item improves or preserves the objective.

Repeated exchanges lead to an allocation ordered by decreasing ratio.

This reasoning depends on the ability to divide items.

### 4.6 Complexity

For `n` items:

- Validation: O(n).
- Sorting: O(n log n).
- Allocation: O(n).
- Total time: O(n log n).
- Auxiliary storage: O(n).

## 5. Greedy Algorithms and 0/1 Knapsack

### 5.1 Important distinction

In 0/1 knapsack, an item must either be selected completely or rejected.

Partial allocation is prohibited.

The constraints become:

\[
x_i \in \{0,1\}
\]

A value-to-weight ratio strategy is not generally optimal for this problem.

### 5.2 Counterexample

Consider:

| Item | Value | Weight | Ratio |
|---|---:|---:|---:|
| A | 60 | 10 | 6 |
| B | 100 | 20 | 5 |
| C | 120 | 30 | 4 |

Capacity: 50.

A ratio-based greedy algorithm selects A and B.

Its result is:

\[
60 + 100 = 160
\]

The optimal solution selects B and C:

\[
100 + 120 = 220
\]

The greedy selection is therefore suboptimal.

### 5.3 Dynamic programming comparison

The C++17 and Java 17 implementations include a one-dimensional dynamic programming solution.

Let:

\[
DP[w]
\]

represent the maximum value achievable with capacity `w`.

The recurrence is:

\[
DP[w] =
\max(DP[w], DP[w-weight_i]+value_i)
\]

Capacity is processed in descending order for each item.

Descending iteration prevents an item from being reused during the same iteration.

Complexity:

- Time: O(nC).
- Space: O(C).

Here, `C` is the integer capacity.

The comparison demonstrates that an algorithm's selection rule must be justified by the mathematical properties of its problem rather than by the apparent attractiveness of its heuristic.

## 6. Huffman Coding

### 6.1 Problem definition

Huffman coding is a lossless compression method that constructs variable-length binary codes using symbol frequencies.

Frequently occurring symbols receive shorter codewords.

Less frequent symbols generally receive longer codewords.

The objective is to minimize the weighted path length of the coding tree.

\[
L = \sum_{i=1}^{n} f_i l_i
\]

Where:

- \(f_i\) is the frequency of symbol \(i\).
- \(l_i\) is its codeword length.
- \(L\) is the total weighted path length.

### 6.2 Prefix-free property

A prefix-free code ensures that no complete codeword is the prefix of another codeword.

This property makes encoded sequences uniquely decodable without requiring separators between individual symbols.

For example, codewords such as:

| Symbol | Code |
|---|---|
| A | 0 |
| B | 10 |
| C | 110 |
| D | 111 |

are prefix-free.

### 6.3 Greedy construction

Huffman coding repeatedly performs the following operations:

1. Create one leaf node for each symbol.
2. Insert the nodes into a minimum-priority queue.
3. Extract the two nodes with the smallest frequencies.
4. Create a parent node with their combined frequency.
5. Attach the extracted nodes as its children.
6. Insert the parent node back into the queue.
7. Repeat until one root node remains.

The root represents the complete Huffman tree.

Left and right edges represent binary digits `0` and `1`.

The resulting root-to-leaf paths define the symbol codewords.

### 6.4 Example

The frequency distribution used in the implementations is:

| Symbol | Frequency |
|---|---:|
| a | 45 |
| b | 13 |
| c | 12 |
| d | 16 |
| e | 9 |
| f | 5 |

The algorithm repeatedly combines the two minimum-frequency nodes.

The tree is then traversed to generate codewords.

The implementation uses deterministic tie-breaking where possible. Different valid tie-breaking decisions can produce different code assignments while preserving the same optimal weighted path length.

### 6.5 Encoding and decoding

Encoding replaces each input symbol with its corresponding codeword.

Decoding traverses the tree:

- A zero follows the left edge.
- A one follows the right edge.
- Reaching a leaf produces a decoded symbol.
- Traversal then restarts at the root.

The implementations validate unknown symbols, invalid binary input, and incomplete codewords.

A single-symbol alphabet requires special handling because an ordinary root-to-leaf path would otherwise have length zero. The implementations assign that symbol the codeword `0`.

### 6.6 Complexity

For `n` distinct symbols and a message of length `m`:

| Operation | Complexity |
|---|---|
| Initial priority queue construction | O(n log n) |
| Tree construction | O(n log n) |
| Code generation | O(n) |
| Encoding | O(m + encoded output size) |
| Decoding | O(encoded bit count) |
| Tree storage | O(n) |

The Huffman tree contains `2n - 1` nodes for an alphabet containing `n` symbols.

## 7. Relationships Between the Three Greedy Algorithms

Although all three algorithms use locally optimal decisions, their decision criteria differ.

| Property | Activity selection | Fractional knapsack | Huffman coding |
|---|---|---|---|
| Optimization objective | Maximize activity count | Maximize total value | Minimize weighted code length |
| Greedy criterion | Earliest finish | Highest value-weight ratio | Two minimum frequencies |
| Main data structure | Sorted collection | Sorted collection | Minimum-priority queue |
| State change | Update scheduling boundary | Reduce remaining capacity | Merge two tree nodes |
| Output | Compatible intervals | Allocated item fractions | Prefix-free binary tree |
| Greedy optimality | Yes | Yes | Yes |

The common principle is that a locally optimal decision can be used safely when a correctness argument establishes that it preserves an optimal solution.

## 8. Python Implementation

File: `greedy_algorithms.py`

The Python implementation uses standard-library components.

| Component | Purpose |
|---|---|
| `dataclass` | Immutable activity and item records |
| `Enum` | Selection strategy classification |
| `heapq` | Huffman minimum-priority queue |
| `Counter` | Frequency calculation |
| `dict` | Symbol-to-code mapping |
| `set` | Duplicate and unknown-symbol detection |
| `json` | Structured reporting |
| `pathlib` | Report persistence |

### Activity selection

`ActivitySelector.select()` sorts activities and returns selected and rejected records.

The `SelectionResult` object exposes the selected count and both decision collections.

### Fractional knapsack

`FractionalKnapsack.solve()` sorts items by their value-to-weight ratio and calculates partial allocations.

It reports allocated fractions, values, used capacity, and remaining capacity.

### Huffman coding

`HuffmanCoding` builds the tree, generates codes, encodes messages, decodes binary sequences, and calculates weighted path length.

### Validation

The implementation checks:

- Duplicate activity identifiers.
- Invalid activity intervals.
- Negative or non-finite values.
- Non-positive item weights.
- Duplicate item identifiers.
- Invalid Huffman frequencies.
- Unknown input symbols.
- Invalid encoded sequences.

The test routine checks normal execution and selected failure conditions.

## 9. JavaScript Implementation

File: `greedy_algorithms.js`

The JavaScript implementation uses an event-driven scheduling model and an independently implemented minimum heap.

| Component | Purpose |
|---|---|
| `Activity` | Immutable scheduling record |
| `ActivityScheduler` | Event-driven activity selection |
| `EventEmitter` | Selection and rejection notifications |
| `MinHeap` | Huffman priority queue |
| `HuffmanCodec` | Prefix-code construction |
| `FractionalKnapsack` | Resource allocation |
| `Map` | Frequency and code storage |
| `Set` | Identifier uniqueness |
| `fs/promises` | Asynchronous report persistence |

### Event-driven scheduling

The scheduler emits:

- `selected` when an activity is accepted.
- `rejected` when an activity overlaps.
- `completed` when scheduling finishes.

This structure separates the optimization algorithm from consumers that may need to log, display, or process scheduling decisions.

### Asynchronous execution

The scheduling workflow demonstrates Promise-based execution.

File persistence uses Node.js asynchronous file operations.

The application handles persistence failures separately from optimization failures.

### Heap implementation

The JavaScript minimum heap implements insertion and extraction directly.

This avoids third-party dependencies and provides O(log n) insertion and extraction.

## 10. C++17 Implementation

File: `greedy_algorithms.cpp`

The C++ implementation emphasizes explicit ownership, STL algorithms, domain structures, and resource management.

| Component | Purpose |
|---|---|
| `Activity` | Scheduling domain record |
| `ActivityResult` | Selected and rejected collections |
| `Item` | Knapsack input |
| `KnapsackResult` | Allocation result |
| `HuffmanCoding` | Tree construction and traversal |
| `priority_queue` | Minimum-frequency selection |
| `unordered_map` | Symbol frequencies and codes |
| `unordered_set` | Uniqueness validation |
| `vector` | Dynamic storage |
| `ZeroOneKnapsack` | Exact dynamic programming comparison |

### Memory management

The Huffman tree uses dynamically allocated nodes.

The class owns the root and recursively releases the complete tree in its destructor.

Copy construction and copy assignment are disabled to prevent accidental shallow copies and double deletion.

Frequency addition is checked for unsigned integer overflow.

### Optimization comparison

The C++ implementation includes both fractional and 0/1 knapsack.

This makes the difference between divisible and indivisible allocation explicit.

## 11. Java 17 Implementation

File: `GreedyAlgorithms.java`

The Java implementation uses enterprise-oriented domain modeling and policy separation.

| Component | Purpose |
|---|---|
| Records | Immutable domain objects |
| `SelectionPolicy` | Strategy interface |
| `EarliestFinishPolicy` | Scheduling decision rule |
| `ActivitySchedulingService` | Scheduling workflow |
| `FractionalKnapsackService` | Allocation service |
| `HuffmanCodec` | Compression service |
| `PriorityQueue` | Huffman node selection |
| `Map` and `Set` | Data management |
| `ZeroOneKnapsackService` | Dynamic programming comparison |

### Policy separation

The `SelectionPolicy` interface separates the selection rule from the scheduling service.

`EarliestFinishPolicy` implements the scheduling condition.

This structure makes it possible to introduce other selection policies without embedding every decision rule directly inside the scheduling workflow.

A different policy must still be independently justified if optimality is required.

### Immutable domain objects

Java records provide immutable representations of activities, items, allocations, and reports.

Validation occurs during record construction.

The services return immutable collection snapshots where appropriate.

### Failure handling

The implementation uses a custom `AlgorithmException` for invalid domain input.

Arithmetic operations use checked operations where integer overflow is possible.

## 12. PostgreSQL Implementation

File: `greedy_algorithms.sql`

The database implementation stores algorithm runs, problem inputs, decisions, allocations, and Huffman-related records.

### Database schema

The `greedy_lab` schema contains:

| Table | Responsibility |
|---|---|
| `algorithm_runs` | Execution metadata and lifecycle |
| `activities` | Scheduling input |
| `activity_decisions` | Selected and rejected decisions |
| `knapsack_problems` | Capacity and optimization result |
| `knapsack_items` | Item values and weights |
| `knapsack_allocations` | Allocated fractions and contributions |
| `huffman_symbols` | Symbol frequencies |
| `huffman_nodes` | Huffman tree structure |
| `huffman_codes` | Generated binary codewords |

### Integrity enforcement

The schema uses:

- Primary keys for record identification.
- Foreign keys for relational consistency.
- Unique constraints for duplicate prevention.
- Check constraints for valid intervals, weights, frequencies, and allocation fractions.
- Generated columns for value-to-weight ratios.
- Indexes for ordered activity retrieval and ratio-based allocation.

The activity validation trigger prevents invalid time intervals.

The decision-integrity trigger prevents an activity decision from being associated with an unrelated algorithm run.

### Activity scheduling

`calculate_activity_selection()` uses ordered records and recursive SQL to identify compatible activities.

The stored `activity_decisions` table preserves the actual decisions made during the demonstration workflow.

### Fractional knapsack

`calculate_fractional_knapsack()` uses cumulative window calculations to determine how much capacity remains before each candidate item.

The allocation fraction is limited to the interval from zero to one.

### Huffman persistence

The schema separates symbol frequencies, tree nodes, and codewords.

`calculate_huffman_cost()` calculates weighted path length from persisted codewords.

The schema supports storing Huffman results, while the tree-construction and binary-code generation operations are implemented in the Python, JavaScript, C++, and Java programs.

### Transactions

The sample data-loading workflow runs inside a transaction.

A failure during the workflow prevents a partially committed demonstration dataset.

The SQL script also includes retrieval, aggregation, validation, and reporting queries.

## 13. Edge Cases and Failure Conditions

| Condition | Expected behavior |
|---|---|
| Empty activity collection | Return an empty schedule |
| Duplicate activity identifiers | Reject the input |
| Activity finish not greater than start | Reject the input |
| Activities with equal finishing times | Apply deterministic tie-breaking |
| Adjacent activity intervals | Permit selection |
| Zero knapsack capacity | Return zero allocation |
| Zero item value | Permit the item but allocate only if capacity remains |
| Zero or negative item weight | Reject the input |
| Fractional capacity | Support numeric allocation |
| Empty Huffman frequency table | Reject the input |
| Zero Huffman frequency | Reject the input |
| Unknown Huffman symbol | Reject encoding |
| Invalid binary digit | Reject decoding |
| Incomplete Huffman codeword | Reject decoding |
| Single-symbol alphabet | Use a one-bit codeword |
| Integer frequency overflow | Reject unsafe aggregation |

## 14. Security and Reliability Considerations

Although these algorithms are primarily computational, production implementations still require input and execution safeguards.

### Input validation

All externally supplied values must be validated before entering optimization routines.

Invalid numeric values, duplicate identifiers, negative capacities, and malformed encoded data must not be accepted silently.

### Numeric accuracy

Fractional knapsack uses floating-point or decimal arithmetic.

Floating-point comparisons may introduce small precision differences.

Financial or accounting applications should use fixed-precision decimal arithmetic and an explicitly defined rounding policy.

The PostgreSQL implementation uses `NUMERIC` for allocation and monetary-style values.

### Memory management

The C++ implementation explicitly manages Huffman tree ownership.

Java and Python use managed memory.

The JavaScript implementation validates frequency totals against the safe integer range.

### Resource consumption

Huffman coding requires storage proportional to the number of distinct symbols.

Large messages require additional memory for encoded output.

Production services should impose input-size limits, frequency limits, and execution time limits.

### Deterministic execution

Equal-priority candidates can create different but equally valid results.

Deterministic tie-breaking improves repeatability, debugging, and testing.

### Database reliability

Database constraints provide protection even when data is inserted outside the primary application.

Transactions protect multi-step operations from partial persistence.

Application-level validation and database-level integrity enforcement serve different purposes and should both be maintained.

## 15. Testing and Verification

The five source files contain executable implementations and validation mechanisms.

The following properties are particularly important.

### Activity selection

- Every selected interval is valid.
- Selected activities do not overlap.
- Selected activities follow finishing-time order.
- The selected count is maximal for unweighted interval scheduling.

### Fractional knapsack

- Every allocation fraction is between zero and one.
- Total allocated weight does not exceed capacity.
- Total value equals the sum of allocated item values.
- Items are processed in descending value-to-weight ratio.

### Huffman coding

- Every input symbol receives a codeword.
- Codewords are nonempty.
- The code is prefix-free.
- Encoding and decoding preserve the original message.
- Weighted path length corresponds to the sum of frequency-weighted code lengths.

### Dynamic programming comparison

The 0/1 knapsack example verifies that a ratio-based greedy solution can be suboptimal when items cannot be divided.

## 16. Execution

| File | Execution |
|---|---|
| Python | `python greedy_algorithms.py` |
| JavaScript | `node greedy_algorithms.js` |
| C++17 | `g++ -std=c++17 -O2 -Wall -Wextra greedy_algorithms.cpp -o greedy_algorithms` |
| C++17 execution | `./greedy_algorithms` |
| Java 17 | `javac GreedyAlgorithms.java` |
| Java execution | `java GreedyAlgorithms` |
| PostgreSQL | Execute `greedy_algorithms.sql` using a PostgreSQL client |

The Python and JavaScript implementations write a JSON execution report.

The C++17 and Java 17 implementations print scheduling, allocation, compression, and optimization results.

The PostgreSQL script creates the relational schema, inserts sample data, executes the demonstration workflow, and displays reports.

## 17. Practical Applications

| Algorithm | Application |
|---|---|
| Activity selection | Meeting scheduling, shared resource allocation, event planning |
| Fractional knapsack | Divisible resource distribution, capacity allocation, inventory valuation |
| Huffman coding | Lossless compression, data transmission, storage optimization |
| 0/1 dynamic programming comparison | Indivisible resource allocation and constrained selection |

The central engineering distinction is that a greedy algorithm is not defined merely by choosing the best available candidate. Its correctness depends on whether the decision rule preserves an optimal solution for the remaining problem.
