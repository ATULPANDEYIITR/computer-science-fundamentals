# Sorting Algorithms I

## Technical Scope

This project implements three fundamental comparison-based sorting algorithms:

1. Bubble Sort
2. Selection Sort
3. Insertion Sort

The implementations demonstrate sorting integer datasets, arranging enterprise inventory records, collecting execution metrics, validating results, and comparing algorithm behavior.

The project contains five independent implementations:

| File | Implementation | Primary responsibility |
|---|---|---|
| Python | Python 3 | Algorithm implementation, benchmarking, and testing |
| JavaScript | Node.js | Event-driven sorting and asynchronous execution |
| C++17 | Standard C++ | Generic sorting and inventory management |
| Java 17 | Java 17 | Enterprise sorting service and procurement policies |
| PostgreSQL | PostgreSQL 14+ | Relational sorting workflows and analytical reporting |

## Sorting Fundamentals

Sorting arranges elements according to a defined ordering rule.

For ascending numerical order:

`[64, 34, 25, 12, 22]`

becomes:

`[12, 22, 25, 34, 64]`

For descending numerical order:

`[64, 34, 25, 12, 22]`

becomes:

`[64, 34, 25, 22, 12]`

A comparison determines which of two elements should appear first. The algorithms repeatedly compare elements and modify their positions until the required ordering is achieved.

The implementations support ascending and descending sorting, duplicate values, negative numbers, empty datasets, and single-element datasets.

## 1. Bubble Sort

Bubble Sort repeatedly compares adjacent elements and exchanges them when they violate the requested ordering.

### Mechanism

For ascending order:

1. Compare the first and second elements.
2. Exchange them if the first is larger.
3. Move to the next adjacent pair.
4. Continue until the end of the unsorted portion.
5. Repeat until all elements are ordered.

After each complete pass, the largest remaining element reaches its correct position at the end of the unsorted portion.

Example:

| Pass | Array |
|---|---|
| Initial | 5, 3, 8, 2 |
| Pass 1 | 3, 5, 2, 8 |
| Pass 2 | 3, 2, 5, 8 |
| Pass 3 | 2, 3, 5, 8 |

### Early termination

The Python, JavaScript, C++, and Java implementations maintain a swap indicator.

If an entire pass completes without a swap, the array is already sorted. Further passes are unnecessary.

This improves the best-case running time from quadratic to linear.

### Characteristics

- Stable sorting algorithm.
- In-place sorting.
- Adjacent element exchanges.
- Useful for understanding comparison and exchange operations.
- Inefficient for large datasets.

## 2. Selection Sort

Selection Sort repeatedly identifies the smallest element in the unsorted portion and places it at the next available position.

For descending order, the largest element is selected instead.

### Mechanism

1. Consider the complete array unsorted.
2. Find its smallest element.
3. Exchange it with the first element.
4. Exclude the first position from subsequent searches.
5. Find the smallest element in the remaining portion.
6. Repeat until the array is ordered.

Example:

| Pass | Array |
|---|---|
| Initial | 64, 25, 12, 22 |
| Pass 1 | 12, 25, 64, 22 |
| Pass 2 | 12, 22, 64, 25 |
| Pass 3 | 12, 22, 25, 64 |

### Characteristics

- Standard implementation is unstable.
- In-place sorting.
- Performs a predictable number of comparisons.
- Performs at most one exchange per pass.
- Does not benefit from an already sorted input in terms of comparison count.

Selection Sort can be useful when reducing the number of data exchanges is important.

## 3. Insertion Sort

Insertion Sort maintains a sorted portion of the array and inserts each subsequent element into its correct position.

### Mechanism

1. Treat the first element as sorted.
2. Select the next element as the current element.
3. Compare it with elements in the sorted portion.
4. Shift larger elements one position to the right.
5. Insert the current element into the available position.
6. Continue until all elements have been processed.

Example:

| Pass | Array |
|---|---|
| Initial | 5, 3, 8, 2 |
| Pass 1 | 3, 5, 8, 2 |
| Pass 2 | 3, 5, 8, 2 |
| Pass 3 | 2, 3, 5, 8 |

### Characteristics

- Stable sorting algorithm.
- In-place sorting.
- Efficient for small datasets.
- Efficient for nearly sorted datasets.
- Requires fewer operations when elements are already close to their correct positions.

Insertion Sort is particularly useful when processing small batches or maintaining a partially ordered collection.

## Complexity Comparison

Let `n` represent the number of elements.

| Property | Bubble Sort | Selection Sort | Insertion Sort |
|---|---:|---:|---:|
| Best time | O(n) | O(n²) | O(n) |
| Average time | O(n²) | O(n²) | O(n²) |
| Worst time | O(n²) | O(n²) | O(n²) |
| Auxiliary space | O(1) | O(1) | O(1) |
| Stable | Yes | No | Yes |
| In-place | Yes | Yes | Yes |
| Adaptive | Yes, with early termination | No | Yes |
| Exchanges or shifts | Adjacent exchanges | Limited exchanges | Element shifts |

The comparison counts and execution times are different measurements.

A comparison count measures how frequently the algorithm evaluates ordering conditions. Execution time also depends on memory access, runtime implementation, system load, and data representation.

## Important Terminology

| Term | Meaning |
|---|---|
| Comparison | Evaluating the relative ordering of two elements |
| Swap | Exchanging the positions of two elements |
| Shift | Moving an element to another position to make space |
| Pass | One iteration through the current unsorted portion |
| Stable sorting | Equal-key elements retain their original relative order |
| In-place sorting | Sorting uses constant auxiliary storage, excluding input storage |
| Adaptive sorting | Performance improves when input is already partially ordered |
| Comparator | A function defining the ordering of two elements |
| Key | A property extracted from an object for comparison |
| Best case | Input arrangement requiring the fewest operations |
| Worst case | Input arrangement requiring the most operations |

## Stability and Duplicate Values

Stability is important when sorting structured records.

Consider:

| Original position | Employee | Department |
|---|---|---|
| 1 | Alice | IT |
| 2 | Bob | Finance |
| 3 | Charlie | IT |
| 4 | David | Finance |

When sorting by department, a stable algorithm preserves the original relative order of employees within the same department.

The standard Bubble Sort and Insertion Sort implementations preserve this order because they exchange or shift elements only when their keys strictly violate the ordering.

The standard Selection Sort implementation can change the relative order of equal-key elements when it exchanges a selected element with an earlier position.

For example:

`[(4, A), (4, B), (3, C)]`

A selection operation can produce:

`[(3, C), (4, B), (4, A)]`

The relative order of A and B has changed.

## Python Implementation

The Python script provides a reusable `SortingEngine`.

### Implemented capabilities

- Separate functions for all three algorithms.
- `Algorithm` enumeration for selecting an algorithm.
- `SortMetrics` dataclass for execution measurements.
- `SortResult` dataclass for structured results.
- Custom sorting keys.
- Ascending and descending ordering.
- Inventory record sorting.
- Stability demonstrations.
- Randomized benchmark datasets.
- CSV benchmark export.
- Assertion-based validation.

The implementation copies input iterables into lists before sorting. This prevents unintended modification of the caller's original collection.

The inventory example prioritizes products by stock quantity.

The benchmark measures comparisons, swaps, shifts, passes, and elapsed time independently.

## JavaScript Implementation

The JavaScript implementation uses Node.js and an event-driven service model.

### Main components

| Component | Responsibility |
|---|---|
| `SortingService` | Executes the sorting algorithms |
| `SortingMetrics` | Tracks algorithm operations |
| `InventoryManager` | Validates and manages inventory records |
| `SortingError` | Represents invalid sorting operations |
| `runBenchmark` | Runs asynchronous benchmark operations |

### Event-driven behavior

`SortingService` extends `EventEmitter`.

It publishes:

- `sortCompleted` when sorting succeeds.
- `sortError` when sorting fails.

This separates sorting logic from notification and reporting logic.

The asynchronous execution method uses a Promise and `setImmediate` to yield execution before performing the sorting operation.

The benchmark report is exported as JSON.

### Comparator design

The service accepts custom comparator functions.

A comparator returns:

- A negative value when the first element precedes the second.
- Zero when both elements have equivalent ordering.
- A positive value when the first element follows the second.

This permits sorting structured objects without changing the sorting algorithms.

## C++17 Implementation

The C++ program uses generic templates and STL containers.

### Main components

| Component | Responsibility |
|---|---|
| `Algorithm` | Identifies the sorting algorithm |
| `Metrics` | Stores operation counts |
| `SortResult` | Holds sorted values and measurements |
| `InventoryItem` | Represents a product record |
| `SortingEngine` | Implements generic sorting |
| `InventoryService` | Applies sorting to inventory data |

The algorithms accept comparator objects, allowing the same implementation to sort integers and structured records.

`std::less` provides ascending ordering, while `std::greater` provides descending ordering.

The inventory service demonstrates sorting by stock quantity and product price.

### Engineering decisions

- Input collections are passed by value to protect the caller's original data.
- `std::vector` provides contiguous storage.
- Templates avoid duplicating algorithm implementations for different data types.
- `std::chrono` measures execution duration.
- Exceptions report invalid inputs and failed validation.
- Randomized datasets provide repeatable benchmark scenarios through a fixed random seed.

The inventory validation also checks product identifiers for duplication.

## Java 17 Implementation

The Java implementation models sorting as an enterprise service.

### Domain model

| Type | Responsibility |
|---|---|
| `Algorithm` | Sorting strategy |
| `SortStatus` | Execution state |
| `Metrics` | Immutable performance measurements |
| `SortResult` | Immutable sorting result |
| `InventoryItem` | Validated inventory record |
| `ProcurementPolicy` | Procurement eligibility rules |
| `SortingService` | Sorting execution |
| `InventoryService` | Inventory operations |

### Records and immutable results

Java 17 records provide compact immutable representations for sorting metrics, results, inventory items, and procurement policies.

`SortResult` uses `List.copyOf()` to prevent callers from modifying the stored result through the returned list.

The inventory service similarly maintains an immutable snapshot.

### Procurement policy

A product becomes eligible for procurement when:

- Its stock quantity is at or below the configured critical threshold.
- Its unit price is at or below the configured maximum purchase price.

The policy is evaluated independently of the sorting algorithm.

This distinction separates business eligibility from data ordering.

### State and failure handling

The service returns a completed result with execution metrics.

It rejects invalid input, missing comparators, excessive dataset sizes, null elements, and invalid domain records.

Notification listener failures are handled independently so that a successfully completed sorting operation is not incorrectly reported as failed.

## PostgreSQL Implementation

The SQL implementation models sorting as a relational workflow.

### Database structure

The main schema is `sorting_lab`.

| Table | Purpose |
|---|---|
| `products` | Stores inventory records |
| `sorting_executions` | Records algorithm executions |
| `inventory_sort_jobs` | Tracks inventory sorting requests |
| `inventory_sort_results` | Stores ordered product positions |

The relationships are:

`Products → Inventory Sort Jobs → Inventory Sort Results`

`Sorting Executions` independently records algorithm-level operations.

### Database constraints

The schema applies:

- Primary keys for record identification.
- Foreign keys for relational integrity.
- Unique constraints for product identifiers.
- Check constraints for stock and price.
- Dataset size restrictions.
- Valid execution-state conditions.
- Unique product positions within each sorting job.

The timestamp trigger updates product modification times automatically.

### PL/pgSQL algorithms

Three independent functions implement the sorting algorithms:

| Function | Algorithm |
|---|---|
| `bubble_sort()` | Adjacent comparisons and exchanges |
| `selection_sort()` | Minimum or maximum selection |
| `insertion_sort()` | Ordered insertion using shifts |

Each function accepts an integer array and an ordering parameter.

The input validation function rejects null arrays and datasets exceeding the configured maximum.

### Execution workflow

`execute_sort()` provides a common interface for algorithm execution.

Its workflow is:

1. Validate the input.
2. Create an execution record.
3. Record the start time.
4. Select the requested algorithm.
5. Execute the sorting function.
6. Calculate elapsed time.
7. Save the sorted output.
8. Mark the execution as completed.

If an execution fails, the error handler records the failure message and completion timestamp before propagating the exception.

### Inventory processing

`process_inventory_sort()` creates inventory sorting jobs and stores the resulting product positions.

It supports stock-based and price-based ordering.

The ordering fields are restricted to explicitly supported values rather than being inserted directly into dynamically constructed SQL statements.

A product identifier provides deterministic tie-breaking when two products have equal sort values.

### Reporting and evaluation

The database includes queries for:

- Execution history.
- Sorted inventory retrieval.
- Output validation.
- Average execution time.
- Comparison and swap statistics.
- Dataset-size analysis.
- Procurement eligibility.
- Algorithm performance ranking.

The CTE-based performance report uses `RANK()` to order algorithms by average recorded duration.

## Cross-Implementation Comparison

| Feature | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| Bubble Sort | Yes | Yes | Yes | Yes | Yes |
| Selection Sort | Yes | Yes | Yes | Yes | Yes |
| Insertion Sort | Yes | Yes | Yes | Yes | Yes |
| Descending order | Yes | Yes | Yes | Yes | Yes |
| Custom ordering | Key | Comparator | Template comparator | Comparator | Fixed numeric ordering |
| Metrics | Yes | Yes | Yes | Yes | Execution records |
| Inventory workflow | Yes | Yes | Yes | Yes | Yes |
| Benchmarking | Yes | Yes | Yes | Yes | Yes |
| Validation | Yes | Yes | Yes | Yes | Yes |
| Persistent reporting | CSV | JSON | Console | Console | Relational tables |

## Practical Limitations

These algorithms are intended for foundational sorting practice and small datasets.

Their quadratic average and worst-case time complexity makes them unsuitable for large-scale production sorting.

For production systems, more efficient algorithms such as Merge Sort, Heap Sort, and Quick Sort are generally preferable.

Other practical considerations include:

- Comparator consistency.
- Duplicate-key handling.
- Stability requirements.
- Input size restrictions.
- Memory consumption.
- Data mutation.
- Deterministic tie-breaking.
- Runtime measurement accuracy.
- Concurrent modifications to shared datasets.

The database implementation also distinguishes algorithm execution from SQL inventory ordering. Its PL/pgSQL functions implement the three educational algorithms, while the inventory workflow uses PostgreSQL's native `ORDER BY` facility for relational processing.

## Execution Requirements

| Deliverable | Runtime |
|---|---|
| Python | Python 3.10+ |
| JavaScript | Node.js 18+ |
| C++17 | C++17-compatible compiler |
| Java | Java 17 |
| PostgreSQL | PostgreSQL 14+ |

Python generates `sorting_benchmark.csv`.

JavaScript generates `sorting_benchmark.json`.

C++17 and Java display benchmark measurements in the terminal.

PostgreSQL stores execution history, inventory sorting jobs, sorted positions, and reporting information in relational tables.

## Expected Learning Outcomes

The implementations demonstrate the operational differences between adjacent exchanges, minimum-element selection, and ordered insertion.

They also establish how the same algorithms can be integrated into different engineering environments through generic functions, comparator interfaces, domain models, asynchronous services, validation mechanisms, and database workflows.
