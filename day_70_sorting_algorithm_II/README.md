# Sorting Algorithms II

## Merge Sort, Quick Sort and Heap Sort

This project implements three fundamental comparison-based sorting algorithms using Python, JavaScript, C++17, Java 17 and PostgreSQL.

The implementations examine different approaches to ordering data, memory management, partitioning, heap construction, stability, algorithmic complexity and performance measurement.

The central objective is to understand how sorting algorithms transform an unordered collection into an ordered sequence and how their internal mechanisms affect performance under different input conditions.

## 1. Sorting Fundamentals

Sorting arranges elements according to an ordering rule.

For numerical data, ascending sorting places smaller values before larger values. Descending sorting reverses that relationship.

For structured records, sorting may depend on a selected attribute such as salary, age, timestamp, priority or transaction value.

A comparison-based sorting algorithm determines element order through comparisons between pairs of elements.

### Important terminology

| Term | Meaning |
|---|---|
| Comparison | Determines the relative order of two elements |
| Swap | Exchanges the positions of two elements |
| Partition | Separates elements according to their relationship with a pivot |
| Pivot | Reference element used by quicksort |
| Merge | Combines two previously sorted sequences |
| Heap | Complete binary tree satisfying a heap-order property |
| Max heap | Parent values are greater than or equal to their children |
| Min heap | Parent values are smaller than or equal to their children |
| Stability | Preserves the relative order of equal-key elements |
| In-place sorting | Performs sorting using limited additional working memory |
| Auxiliary space | Additional memory required by an algorithm |
| Time complexity | Describes how execution work grows with input size |

## 2. Algorithm Comparison

The three algorithms use different mechanisms to achieve the same ordering objective.

| Property | Merge Sort | Quick Sort | Heap Sort |
|---|---|---|---|
| Design | Divide and conquer | Partition and conquer | Binary heap |
| Best time | O(n log n) | O(n log n) | O(n log n) |
| Average time | O(n log n) | O(n log n) | O(n log n) |
| Worst time | O(n log n) | O(n²) | O(n log n) |
| Auxiliary space | O(n) | O(log n) average with stack | O(1) |
| Stability | Yes | No | No |
| In-place | No | Yes, excluding stack | Yes |
| Main mechanism | Merging sorted partitions | Pivot partitioning | Heap construction and extraction |

The space figures describe the conventional algorithmic implementations. The supplied programs use defensive input copies, which add O(n) storage for the returned result.

## 3. Merge Sort

Merge sort is a divide-and-conquer algorithm.

It repeatedly divides an input sequence into smaller sections until each section contains one element. Individual elements are already sorted. The algorithm then combines these sections in sorted order.

### Working mechanism

Consider the input:

`[38, 27, 43, 3, 9, 82, 10, 3]`

The division process follows this structure:

    Original
    [38, 27, 43, 3, 9, 82, 10, 3]

    First division
    [38, 27, 43, 3] | [9, 82, 10, 3]

    Second division
    [38, 27] | [43, 3] | [9, 82] | [10, 3]

    Individual elements
    [38] [27] [43] [3] [9] [82] [10] [3]

    Merging
    [27, 38] | [3, 43] | [9, 82] | [3, 10]

    Further merging
    [3, 27, 38, 43] | [3, 9, 10, 82]

    Final result
    [3, 3, 9, 10, 27, 38, 43, 82]

### Important mechanisms

**Division**

The sequence is divided using a midpoint.

For a range from index `left` to index `right`:

`middle = (left + right) // 2`

The algorithm processes the two resulting sections independently.

**Merging**

Two sorted sections are compared element by element.

The smaller element is copied into the destination sequence. The process continues until one section becomes empty. Remaining elements from the other section are copied directly.

**Stability**

Merge sort is stable when equal elements from the left section are selected before equal elements from the right section.

This property is important when sorting records that contain multiple attributes.

For example, employees with identical salaries retain their original relative order.

### Complexity

| Operation | Complexity |
|---|---|
| Division levels | O(log n) |
| Merging at each level | O(n) |
| Total time | O(n log n) |
| Auxiliary memory | O(n) |

Merge sort provides predictable worst-case performance, making it appropriate when stable ordering and consistent execution time are important.

## 4. Quick Sort

Quick sort is a partition-based divide-and-conquer algorithm.

It selects a pivot and divides the sequence into sections according to the relationship between their elements and the pivot.

Unlike merge sort, quicksort does not merge sorted sections after processing them. Its partitions establish the ordering relationships required for the final result.

### Working mechanism

For the input:

`[38, 27, 43, 3, 9, 82, 10, 3]`

A pivot is selected from the input.

Using a pivot of `10`, the conceptual partition becomes:

    Elements smaller than pivot:
    [3, 9, 3]

    Pivot:
    [10]

    Elements greater than pivot:
    [38, 27, 43, 82]

The smaller and greater sections are partitioned again until all elements are correctly positioned.

### Pivot selection

Pivot selection affects partition quality.

A poor pivot can produce highly unbalanced partitions. Repeatedly processing such partitions increases execution time.

The supplied implementations use median-of-three selection.

The candidates are:

- First element.
- Middle element.
- Last element.

The median candidate is selected as the pivot.

This reduces sensitivity to certain ordered input patterns but does not eliminate worst-case behavior.

### Three-way partitioning

The implementations use three-way partitioning.

Each partition maintains three logical regions:

    [Elements smaller than pivot]
    [Elements equal to pivot]
    [Elements greater than pivot]

This is particularly useful when an input contains many repeated values.

Elements equal to the pivot are not repeatedly processed in smaller recursive partitions.

### Complexity

| Case | Complexity |
|---|---|
| Best | O(n log n) |
| Average | O(n log n) |
| Worst | O(n²) |
| Average auxiliary stack | O(log n) |

The supplied implementations use iterative partition processing to avoid dependence on the programming language's recursive call-stack limit.

Processing smaller partitions first and controlling the pending partition stack further reduces auxiliary stack requirements.

Quick sort is suitable when practical average-case performance and low additional working memory are important.

Its worst-case time complexity must still be considered.

## 5. Heap Sort

Heap sort uses a binary heap to organize elements.

A binary heap is a complete binary tree represented efficiently using an array.

A max heap maintains the following property:

`Parent >= Children`

The largest element is therefore located at the root.

### Array representation

For a zero-based array, the relationships are:

| Node | Index |
|---|---|
| Parent | `(i - 1) // 2` |
| Left child | `2 * i + 1` |
| Right child | `2 * i + 2` |

### Working mechanism

Heap sort has two principal phases.

**Phase 1: Heap construction**

The input is rearranged into a max heap.

The process begins with the last internal node and moves towards the root.

The heap property is restored using a downward adjustment operation called `sift-down`.

Building a heap using this bottom-up approach requires O(n) time.

**Phase 2: Maximum extraction**

The maximum element is exchanged with the final element of the current heap.

The heap's active size is reduced by one.

The root is adjusted again using `sift-down`.

This process continues until the entire array is ordered.

### Example

Initial input:

`[4, 10, 3, 5, 1]`

After max-heap construction, one possible representation is:

`[10, 5, 3, 4, 1]`

Maximum extraction moves the largest element into its final position.

The remaining active elements are reorganized into a valid max heap.

Repeated extraction produces:

`[1, 3, 4, 5, 10]`

### Complexity

| Operation | Complexity |
|---|---|
| Heap construction | O(n) |
| Single extraction | O(log n) |
| All extractions | O(n log n) |
| Total time | O(n log n) |
| Auxiliary space | O(1) |

Heap sort provides a guaranteed O(n log n) worst-case time bound without requiring a separate linear-size working array.

It is useful when predictable time complexity and limited auxiliary memory are priorities.

It is not stable.

## 6. Stability and Ordering Rules

Stability determines whether equal-key elements retain their original relative positions.

Consider these records:

| Original position | Employee | Salary |
|---|---|---:|
| 1 | Employee A | 80000 |
| 2 | Employee B | 70000 |
| 3 | Employee C | 80000 |
| 4 | Employee D | 70000 |

When sorting by salary in ascending order, a stable algorithm produces:

| Position | Employee | Salary |
|---|---|---:|
| 1 | Employee B | 70000 |
| 2 | Employee D | 70000 |
| 3 | Employee A | 80000 |
| 4 | Employee C | 80000 |

The relative ordering of employees with identical salaries remains unchanged.

Merge sort guarantees this behavior through its merge-selection rule.

Quick sort and heap sort do not guarantee stability.

Stability is particularly relevant to:

- Employee records.
- Financial transactions.
- Event timelines.
- Database reporting.
- Multi-attribute sorting.
- Priority-based processing.

## 7. Selecting an Appropriate Algorithm

The appropriate algorithm depends on workload characteristics and system constraints.

| Requirement | Suitable algorithm |
|---|---|
| Stable ordering | Merge sort |
| Guaranteed O(n log n) time | Merge sort or heap sort |
| Limited auxiliary working memory | Heap sort |
| Good average practical performance | Quick sort |
| Many duplicate values | Three-way quicksort |
| Predictable worst-case execution | Merge sort or heap sort |
| Sorting structured records with stability | Merge sort |

These are selection guidelines rather than universal performance rankings.

Actual execution time depends on input distribution, data representation, comparator cost, memory allocation and runtime implementation.

## 8. Python Implementation

The Python implementation provides three independently callable sorting functions.

### Main components

| Component | Responsibility |
|---|---|
| `Algorithm` | Identifies the available algorithms |
| `SortMetrics` | Stores operation counts and execution time |
| `merge_sort()` | Performs stable merge sorting |
| `quick_sort()` | Performs iterative three-way partitioning |
| `heap_sort()` | Performs max-heap sorting |
| `sort_data()` | Provides a common algorithm-selection interface |
| `verify_sort()` | Checks ordering and element preservation |
| `benchmark()` | Executes tests across different distributions |
| `export_benchmark()` | Exports benchmark records to CSV |

### Implementation decisions

Python uses lists for input storage and dictionaries for benchmark records.

A dataclass represents execution metrics.

The merge sort implementation uses a reusable buffer rather than repeatedly allocating separate arrays during merging.

The quicksort implementation uses an explicit stack instead of recursive calls.

The heap sort implementation modifies a defensive copy using index-based heap operations.

The `key` parameter supports sorting structured objects without requiring changes to the underlying sorting algorithms.

The `reverse` parameter supports descending order.

### Validation

The script checks:

- Empty input.
- Single-element input.
- Two-element input.
- Duplicate values.
- Negative values.
- Reverse-ordered input.
- Large input.
- Stability of equal-key records.
- Element preservation.
- Ascending and descending ordering.

Benchmark output is written to `sorting_benchmark.csv`.

## 9. JavaScript Implementation

The JavaScript implementation uses Node.js capabilities and an event-driven benchmarking workflow.

### Main components

| Component | Responsibility |
|---|---|
| `SortError` | Represents invalid sorting operations |
| `Metrics` | Tracks algorithm execution |
| `createContext()` | Configures comparison and metrics |
| `mergeSort()` | Implements iterative bottom-up merge sort |
| `quickSort()` | Implements iterative three-way quicksort |
| `heapSort()` | Implements heap construction and extraction |
| `sort()` | Selects the sorting strategy |
| `verifyResult()` | Validates the output |
| `benchmark()` | Executes asynchronous benchmark tasks |
| `exportBenchmark()` | Saves JSON benchmark records |

### Implementation decisions

The JavaScript merge sort uses bottom-up processing.

It repeatedly merges adjacent sections of increasing widths. This avoids recursive function calls and provides predictable processing depth.

The quicksort implementation uses a stack of partition boundaries.

The heap sort implementation uses array-based heap operations.

A comparator function supports different data types and business-specific ordering requirements.

The benchmark function uses asynchronous event-loop yielding between sorting operations.

`AbortSignal` provides a cancellation mechanism between benchmark tasks.

Benchmark records are exported to `sorting_benchmark.json`.

The benchmark is asynchronous, but each individual sorting operation executes synchronously on the Node.js thread. Cancellation does not interrupt an algorithm while it is running.

## 10. C++17 Implementation

The C++ implementation emphasizes generic programming, explicit memory management and reusable sorting components.

### Main components

| Component | Responsibility |
|---|---|
| `Algorithm` | Defines algorithm identifiers |
| `SortMetrics` | Records execution measurements |
| `SortResult<T>` | Combines sorted data and metrics |
| `Comparator<T>` | Defines ordering rules |
| `SortingEngine<T>` | Implements the sorting algorithms |
| `verifyResult()` | Validates sorted output |
| `runTests()` | Executes correctness tests |
| `runBenchmark()` | Compares algorithm performance |

### Implementation decisions

The sorting engine is templated to support different record types.

A comparator is supplied during engine construction.

The same engine can sort integers and structured employee records.

Merge sort uses a reusable temporary buffer.

Quick sort uses an explicit range stack and three-way partitioning.

Heap sort performs bottom-up heap construction and maximum extraction.

The employee example demonstrates sorting by salary without changing the employee domain model.

The C++ implementation uses standard-library containers and algorithms without external dependencies.

## 11. Java 17 Implementation

The Java implementation models sorting as an enterprise-oriented service.

The design separates algorithm selection, execution strategies, validation and result reporting.

### Main components

| Component | Responsibility |
|---|---|
| `Algorithm` | Defines supported algorithms |
| `SortMetrics` | Immutable execution measurements |
| `SortResult<T>` | Immutable sorted result |
| `Employee` | Validated business record |
| `SortStrategy<T>` | Common sorting interface |
| `MergeSort<T>` | Stable merge sort implementation |
| `QuickSort<T>` | Partition-based implementation |
| `HeapSort<T>` | Heap-based implementation |
| `SortingService<T>` | Strategy registration and execution |
| `MetricsCollector` | Tracks algorithm operations |
| `SortingException` | Represents sorting-specific failures |

### Enterprise design decisions

The Strategy pattern separates the sorting algorithm from the service that selects it.

The sorting service maintains an immutable algorithm registry.

Java records represent immutable result and metric objects.

Generic comparators support multiple domain types.

The employee example demonstrates sorting business records by salary.

Input validation prevents null elements from entering algorithm execution.

The verification process checks both sorted order and preservation of the original elements.

This design supports adding further sorting strategies without requiring changes to the existing algorithm implementations.

## 12. PostgreSQL Implementation

The PostgreSQL implementation models algorithm execution as a relational benchmarking workflow.

It also provides executable PL/pgSQL implementations of all three sorting algorithms.

### Database schema

The project uses the `sorting_lab` schema.

| Table | Purpose |
|---|---|
| `sorting_algorithms` | Stores algorithm characteristics |
| `benchmark_datasets` | Stores input sequences and distribution types |
| `benchmark_runs` | Stores execution history and validation outcomes |

### Database relationships

    sorting_algorithms
           |
           | algorithm_id
           |
           v
      benchmark_runs
           |
           | dataset_id
           |
           v
     benchmark_datasets

Each benchmark run references one algorithm and one dataset.

The database uses primary keys, foreign keys, unique constraints and check constraints to enforce data integrity.

### Sorting functions

| Function | Responsibility |
|---|---|
| `merge_sort()` | Initiates recursive merge sorting |
| `merge_sort_range()` | Divides and merges array sections |
| `quick_sort()` | Initiates quicksort |
| `quick_sort_range()` | Performs pivot-based partitioning |
| `heap_sort()` | Builds and extracts from a max heap |
| `heap_sift_down()` | Restores the heap property |
| `execute_sort()` | Dispatches execution by algorithm identifier |
| `validate_sort_result()` | Checks ordering and element preservation |
| `record_benchmark()` | Records benchmark execution |

The PostgreSQL quicksort uses a middle-element pivot and two-sided partitioning. It is a conventional partition implementation and does not use the three-way partitioning mechanism employed by the application-language versions.

The PostgreSQL functions operate on integer arrays. They are educational implementations rather than substitutes for PostgreSQL's optimized native `ORDER BY` execution.

### Benchmark workflow

The database benchmark process follows this sequence:

    Dataset selection
          |
          v
    Algorithm selection
          |
          v
    Sorting function execution
          |
          v
    Output validation
          |
          v
    Execution time measurement
          |
          v
    Benchmark record insertion
          |
          v
    Reporting and comparison

The `record_benchmark()` function measures elapsed database execution time and records correctness.

Its comparison, swap and write counters are stored as zero because the PL/pgSQL implementations do not expose internal operation instrumentation. They must not be interpreted as measured operation counts.

### Reporting mechanisms

The `benchmark_comparison` view joins algorithm definitions, datasets and benchmark records.

The reporting queries demonstrate:

- Benchmark history retrieval.
- Average execution time.
- Successful execution counts.
- Dataset-specific comparison.
- Failed execution identification.
- Algorithm eligibility assessment.
- CTE-based ranking.
- Window-function reporting.

The database uses indexes on dataset history, algorithm history and successful execution records.

## 13. Benchmarking and Performance Analysis

A meaningful comparison requires multiple input distributions.

The implementations examine the following categories:

| Distribution | Characteristics | Purpose |
|---|---|---|
| Random | Unpredictable element order | General performance |
| Sorted | Already ordered elements | Ordered-input behavior |
| Reverse sorted | Descending initial order | Adverse ordering patterns |
| Duplicate-heavy | Many repeated values | Partition behavior |
| All equal | Identical values | Duplicate handling |
| Nearly sorted | Limited local disorder | Sensitivity to existing order |

### Metrics

The application implementations measure:

**Comparisons**

The number of element-order comparisons.

**Swaps**

The number of exchanges between array positions.

**Writes**

The number of recorded assignments or writes.

**Partitions**

The number of quicksort partition operations.

**Execution time**

The measured time spent in the sorting operation.

These counters are implementation-specific. They should not be compared as if they represented identical machine instructions across different programming languages.

### Benchmark interpretation

Execution time depends on:

- Input size.
- Input distribution.
- Runtime optimization.
- Memory allocation.
- Cache behavior.
- Comparator implementation.
- Operating-system scheduling.
- Background processes.
- Hardware architecture.

Small datasets may produce misleading results because fixed execution overhead can dominate actual sorting work.

Reliable performance analysis should use repeated runs, consistent input data and controlled execution conditions.

The supplied benchmark programs provide reproducible datasets through fixed random seeds, but their measurements are exploratory rather than statistically conclusive.

## 14. Edge Cases and Failure Handling

The implementations account for several important input conditions.

| Condition | Expected behavior |
|---|---|
| Empty collection | Return an empty collection |
| One element | Return the original ordering |
| Duplicate elements | Preserve all occurrences |
| Negative numbers | Sort using numerical comparison |
| Already sorted data | Produce the same ordered result |
| Reverse-ordered data | Produce ascending output |
| Invalid algorithm identifier | Reject the request |
| Null input | Reject invalid input where supported |
| Invalid comparator | Report a comparison error |
| Large input | Apply appropriate memory and stack controls |

### Important implementation limitations

**Merge sort**

Requires additional working memory proportional to input size.

**Quick sort**

Median-of-three pivot selection reduces sensitivity to some input patterns but cannot guarantee O(n log n) worst-case performance.

**Heap sort**

Provides predictable time complexity but does not preserve equal-key ordering.

**PostgreSQL**

The recursive PL/pgSQL functions incur database function-call and array-manipulation overhead. They are intended for algorithmic study, not high-volume production sorting.

## 15. Security and Reliability Considerations

Sorting user-controlled data requires appropriate input validation.

Important considerations include:

- Enforcing input-size limits.
- Rejecting malformed input.
- Avoiding unbounded resource consumption.
- Using validated comparison functions.
- Preserving source collections when required.
- Handling cancellation at defined execution boundaries.
- Restricting benchmark output locations.
- Avoiding dynamic SQL constructed from untrusted input.
- Applying appropriate database permissions.
- Monitoring long-running database operations.

Sorting is not itself an authorization mechanism.

A correctly sorted dataset does not establish the authenticity, integrity or trustworthiness of its source records.

## 16. Execution Requirements

| Implementation | Runtime | External dependencies |
|---|---|---|
| Python | Python 3.10+ | None |
| JavaScript | Node.js 18+ | None |
| C++ | C++17 compiler | None |
| Java | Java 17 | None |
| PostgreSQL | PostgreSQL 15+ | None |

### Python

Run the Python source file directly.

The program executes automated tests, displays sample results, runs benchmarks and exports `sorting_benchmark.csv`.

### JavaScript

Run the JavaScript file using Node.js.

The program executes automated tests, displays sample results, performs asynchronous benchmarking and exports `sorting_benchmark.json`.

### C++17

Compile the source using a C++17-compatible compiler.

The program executes correctness tests, displays sorting results and performs a benchmark comparison.

### Java 17

Compile the source file named `SortingAlgorithmsII.java` and execute its main class.

The program validates all three algorithms and demonstrates sorting of employee records.

### PostgreSQL

Execute the SQL script in a PostgreSQL session.

The script creates the schema, tables, indexes, sorting functions, reporting view and sample datasets. It then runs correctness tests and benchmark-recording operations.

The script recreates its demonstration objects, so existing objects with the same names in the `sorting_lab` schema are replaced.

## 17. Educational Outcomes

The implementations establish the following technical distinctions:

| Concept | Practical understanding |
|---|---|
| Divide and conquer | Breaking a problem into smaller independent sections |
| Stable sorting | Preserving equal-key element ordering |
| Partitioning | Establishing element relationships around a pivot |
| Binary heaps | Maintaining an ordered tree structure using arrays |
| Iterative algorithms | Controlling execution without recursive call stacks |
| Generic sorting | Reusing algorithms with different data types |
| Comparator design | Defining application-specific ordering rules |
| Complexity analysis | Understanding how execution requirements grow |
| Benchmarking | Measuring algorithm behavior under controlled conditions |
| Validation | Confirming correctness and element preservation |
| Database functions | Implementing algorithmic operations within PostgreSQL |
| Performance reporting | Comparing execution results across datasets |

The three algorithms solve the same fundamental problem through different data-processing strategies. Their comparison demonstrates why algorithm selection must consider stability, worst-case complexity, memory requirements and the characteristics of the actual workload.
