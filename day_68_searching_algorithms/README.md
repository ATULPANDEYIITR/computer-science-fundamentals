# Searching Algorithms

## Technical Scope

This project implements three fundamental searching algorithms:

- Linear Search
- Binary Search
- Interpolation Search

The implementations demonstrate algorithm design, input validation, duplicate handling, performance measurement, inventory management, database operations, and automated testing.

The five source files use different engineering approaches:

| File | Implementation perspective |
|---|---|
| Python | Reusable search engine, result objects, inventory management, benchmarking |
| JavaScript | Event-driven search service, asynchronous batch execution, statistics |
| C++17 | Sensor registry, STL-based data management, efficient arithmetic |
| Java 17 | Enterprise product catalog, strategy interface, immutable results |
| PostgreSQL | Relational datasets, procedural search functions, execution history, reporting |

## 1. Linear Search

Linear Search examines elements sequentially until the target is found or the collection is exhausted.

### Mechanism

Given:

`[12, 24, 36, 48, 60, 72, 84]`

Target: `60`

The search evaluates:

`12 → 24 → 36 → 48 → 60`

The target is found at zero-based index `4`.

Linear Search does not require sorted data.

### Algorithm

1. Start at the first element.
2. Compare the current element with the target.
3. Return its index if a match is found.
4. Otherwise, continue to the next element.
5. Return not found after reaching the end.

### Complexity

| Case | Time complexity |
|---|---|
| Best | O(1) |
| Average | O(n) |
| Worst | O(n) |
| Auxiliary space | O(1) |

### Practical applications

- Small collections.
- Unsorted datasets.
- Sequential file processing.
- Simple inventory scans.
- Searching linked lists.

Linear Search is appropriate when maintaining sorted data would cost more than performing occasional sequential searches.

## 2. Binary Search

Binary Search repeatedly divides a sorted search interval into two halves.

It eliminates approximately half of the remaining candidates after each comparison.

### Preconditions

The collection must be sorted in ascending order.

For example:

`[10, 20, 30, 40, 50, 60, 70, 80]`

Target: `60`

The algorithm initially considers the middle element, then selects the appropriate half according to the comparison result.

### Mechanism

The search maintains three values:

| Variable | Purpose |
|---|---|
| `left` | First position in the active interval |
| `right` | Last position in the active interval |
| `middle` | Middle position of the active interval |

The middle position is calculated using:

`left + (right - left) // 2`

This avoids potential overflow associated with directly adding two large indices.

### Search decisions

- If the middle element equals the target, a match is found.
- If the middle element is smaller, search the right half.
- If the middle element is larger, search the left half.

The implementations continue searching to the left after finding a match. This guarantees the first occurrence when duplicate values exist.

### Complexity

| Case | Time complexity |
|---|---|
| Best | O(1) |
| Average | O(log n) |
| Worst | O(log n) |
| Auxiliary space | O(1) |

### Practical applications

- Sorted product catalogs.
- Employee identification records.
- Sorted database extracts.
- Numeric lookup tables.
- Static indexes.

Binary Search is particularly effective when a dataset is maintained in sorted order and queried frequently.

## 3. Interpolation Search

Interpolation Search estimates the probable position of a target using the numerical values at the boundaries of the active interval.

Unlike Binary Search, which always selects the midpoint, Interpolation Search estimates where the target should occur.

### Preconditions

The input must be sorted in ascending order.

It performs best when values are approximately uniformly distributed.

### Position estimation

The estimated position is:

\[
pos = low +
\frac{(target-A[low])(high-low)}
{A[high]-A[low]}
\]

Where:

- `low` is the lower boundary.
- `high` is the upper boundary.
- `target` is the search value.
- `A[low]` is the lower boundary value.
- `A[high]` is the upper boundary value.

The estimated position is checked against the actual value.

The search interval is then adjusted.

### Important edge cases

**Identical boundary values**

If both boundary values are identical, the denominator becomes zero.

The implementations handle this condition separately.

**Out-of-range target**

If the target is smaller than the lower boundary or larger than the upper boundary, searching stops.

**Duplicate values**

The implementations return the first occurrence.

**Highly nonuniform distributions**

Interpolation estimates can become inaccurate, causing additional iterations.

### Complexity

| Case | Time complexity |
|---|---|
| Best | O(1) |
| Average, approximately uniform distribution | O(log log n) |
| Worst | O(n) |
| Auxiliary space | O(1) |

The average-case advantage depends on the distribution of the stored values. Interpolation Search is not universally faster than Binary Search.

## 4. Algorithm Comparison

| Property | Linear | Binary | Interpolation |
|---|---|---|---|
| Requires sorted data | No | Yes | Yes |
| Search strategy | Sequential | Repeated halving | Position estimation |
| Best time | O(1) | O(1) | O(1) |
| Average time | O(n) | O(log n) | O(log log n), under suitable distributions |
| Worst time | O(n) | O(log n) | O(n) |
| Auxiliary space | O(1) | O(1) | O(1) |
| Distribution sensitivity | Low | Low | High |
| Duplicate handling | First occurrence | First occurrence | First occurrence |

### Selection criteria

Use Linear Search when:

- The dataset is small.
- The data is unsorted.
- Sorting would introduce unnecessary overhead.

Use Binary Search when:

- The dataset is sorted.
- Predictable logarithmic search performance is required.
- Values are not uniformly distributed.

Use Interpolation Search when:

- The dataset contains numeric values.
- Values are sorted.
- The distribution is approximately uniform.
- Position estimation is likely to be effective.

## 5. Python Implementation

The Python implementation uses a reusable `SearchEngine` class.

### Design

The implementation includes:

- `SearchAlgorithm` enumeration.
- `SearchResult` dataclass.
- Input validation.
- Three independent search methods.
- Comparison counting.
- Execution-time measurement.
- Duplicate-value handling.
- Inventory management.
- Benchmarking.
- Automated assertions.

### SearchResult

The result object records:

| Attribute | Description |
|---|---|
| `algorithm` | Algorithm used |
| `target` | Requested value |
| `index` | Matching zero-based position |
| `comparisons` | Number of recorded comparisons |
| `elapsed_microseconds` | Measured execution time |
| `found` | Whether a match exists |

### Inventory workflow

The `InventorySearch` class maintains sorted product identifiers.

Its operations include:

- Product lookup using Binary Search.
- Product insertion while maintaining sorted order.
- Product removal.
- Validation of product identifiers.

The insertion operation uses the standard-library `bisect` module.

Insertion into a Python list requires O(n) element movement in the worst case, even though the insertion position can be located in O(log n).

### Testing

The script tests:

- Successful searches.
- Missing values.
- Empty collections.
- Single-element collections.
- Duplicate values.
- Identical values.
- Unsorted input.
- Invalid element types.
- Inventory insertion and deletion.

The benchmark uses a large sorted collection and reports comparison counts and elapsed time.

## 6. JavaScript Implementation

The JavaScript implementation uses an event-driven service architecture.

### SearchService

The service extends Node.js `EventEmitter`.

It provides:

- Algorithm selection.
- Validation.
- Search execution.
- Event notifications.
- Statistics collection.
- Batch searching.

The `searchCompleted` event is emitted after each completed search.

### SearchResult

Search results are immutable objects.

The service records:

- Total searches.
- Successful matches.
- Total comparisons.

Statistics are stored using a `Map`, separating algorithm-specific measurements.

### Asynchronous execution

`runBatchSearch()` uses `Promise.all()` to process independent search requests through a common service interface.

The search algorithms themselves are synchronous CPU operations. Promise-based execution provides a convenient asynchronous interface but does not make these operations parallel.

### InventoryIndex

The inventory component uses binary insertion to maintain sorted identifiers.

The insertion position is located in O(log n), but JavaScript array insertion can require O(n) element movement.

### Numerical safety

JavaScript uses the `Number` type for ordinary numeric calculations.

The implementation validates safe integers and uses `BigInt` for interpolation arithmetic to reduce intermediate integer-precision problems.

## 7. C++17 Implementation

The C++ implementation models a sensor registry.

Each sensor has an integer identifier, and the registry supports searching and updating its collection.

### Domain design

| Component | Responsibility |
|---|---|
| `SearchType` | Identifies the algorithm |
| `SearchResult` | Stores search metrics and outcome |
| `SensorRegistry` | Maintains sensor identifiers |
| `search()` | Executes the selected algorithm |
| `registerSensor()` | Adds a sensor |
| `unregisterSensor()` | Removes a sensor |

### STL integration

The implementation uses:

- `std::vector` for storage.
- `std::sort` for ordering.
- `std::is_sorted` for validation.
- `std::lower_bound` for insertion and deletion lookup.
- `std::chrono` for timing.
- `std::max` and `std::min` for interpolation bounds.

### Integer overflow protection

Interpolation Search multiplies the target difference by the interval length.

Using `int64_t` for intermediate calculations reduces overflow risk when working with ordinary 32-bit integer identifiers.

### Failure handling

Invalid sorted-data assumptions and failed tests are handled through standard C++ exceptions.

The main function reports errors and returns a nonzero exit status when execution fails.

## 8. Java 17 Implementation

The Java implementation models an enterprise product catalog.

It separates search algorithms from service-level selection and catalog management.

### Architecture

The `SearchStrategy` interface defines a common search operation.

Three classes implement this interface:

- `LinearSearch`
- `BinarySearch`
- `InterpolationSearch`

`SearchService` selects the required implementation using an `EnumMap`-compatible strategy registry.

The implementation uses a `TreeMap` to store the strategies.

### Domain modeling

Java records provide immutable search results.

`SearchStatus` distinguishes:

- `FOUND`
- `NOT_FOUND`

`SearchValidationException` represents invalid search requests and unsupported input conditions.

### ProductCatalog

The catalog maintains sorted product identifiers.

Its responsibilities include:

- Initializing product records.
- Locating products.
- Inserting products.
- Removing products.
- Returning immutable collection snapshots.

### Enterprise considerations

The separation between strategies and services allows individual algorithms to be tested independently.

It also provides a clean extension point for additional search strategies without changing the product catalog's public operations.

The example uses in-memory collections. A production catalog would need database transaction handling, concurrent-update controls, persistent indexing, and access authorization.

## 9. PostgreSQL Implementation

The PostgreSQL implementation represents search datasets and execution history using relational tables.

### Relational model

The database uses two primary tables.

**search_datasets**

Stores dataset metadata.

**search_values**

Stores individual values and their positions.

The relationship is:

`search_datasets (1) → search_values (many)`

Each value belongs to one dataset.

The unique constraint on `(dataset_id, position)` prevents duplicate positions within a dataset.

### Search history

The `search_history` table records individual search operations.

It stores:

- Dataset identifier.
- Algorithm.
- Target value.
- Result position.
- Comparison count.
- Execution time.
- Search outcome.
- Execution timestamp.

Check constraints restrict algorithm names and maintain consistency between the `found` flag and the result position.

### Database functions

| Function | Responsibility |
|---|---|
| `is_dataset_sorted()` | Checks ascending ordering |
| `linear_search()` | Sequential search |
| `binary_search()` | Midpoint-based search |
| `interpolation_search()` | Estimated-position search |
| `execute_search()` | Executes and records a search |

The `load_dataset()` procedure replaces dataset contents within the caller's transaction.

### Database indexing

The implementation defines two indexes on the search values table:

- `(dataset_id, position)`
- `(dataset_id, search_value)`

The first supports ordered retrieval within a dataset.

The second supports value-based filtering.

The procedural search functions demonstrate algorithm behavior, but they are not substitutes for PostgreSQL's native query planner and B-tree indexes.

For large production datasets, a query such as a parameterized indexed lookup is generally more appropriate than fetching values individually through procedural loops.

### Transaction handling

Dataset loading and sample data creation use PostgreSQL transactions.

The example also demonstrates a savepoint during inventory maintenance.

Changes can be committed or rolled back as a unit.

### Reporting

The `search_performance_report` view provides:

- Total searches.
- Successful searches.
- Failed searches.
- Average comparisons.
- Average execution time.
- Last execution timestamp.

A CTE groups execution history to support algorithm-level evaluation.

## 10. Validation and Failure Conditions

| Condition | Expected behavior |
|---|---|
| Empty collection | Return not found |
| Missing target | Return not found |
| Duplicate target | Return first occurrence |
| Single element | Search normally |
| Identical values | Avoid interpolation division by zero |
| Unsorted input with Linear Search | Search normally |
| Unsorted input with Binary Search | Reject input |
| Unsorted input with Interpolation Search | Reject input |
| Invalid numeric input | Reject input |
| Unsupported algorithm | Report validation error |
| Missing database dataset | Raise database exception |

Validation is performed before executing algorithms that depend on sorted input.

This prevents incorrect search results caused by violated preconditions.

## 11. Performance Measurement

The implementations record comparison counts and execution time.

Comparison counts provide a useful way to examine algorithm behavior independently of many machine-specific timing factors.

Execution time is affected by:

- Processor architecture.
- Memory layout.
- Runtime optimization.
- Collection size.
- Data distribution.
- Operating-system scheduling.
- Database execution overhead.

A fair comparison should use identical datasets and targets.

The dataset should be prepared outside the timed search operation.

For meaningful benchmarking:

- Test multiple collection sizes.
- Include successful and unsuccessful searches.
- Include uniform and nonuniform distributions.
- Test duplicate-heavy collections.
- Repeat measurements.
- Compare median execution times.
- Separate sorting costs from searching costs.

The measured comparison count is an implementation-level metric. Exact counts can differ because of validation, boundary checks, and duplicate-handling logic.

## 12. Security and Production Considerations

Searching algorithms are not authentication or authorization mechanisms.

A successful search only establishes that a value exists in the examined collection.

It does not establish whether the requesting user has permission to access the corresponding record.

Production implementations should consider:

- Validate all externally supplied identifiers.
- Apply authorization after record identification.
- Use parameterized SQL queries.
- Avoid constructing SQL statements through untrusted string concatenation.
- Apply database constraints to preserve data integrity.
- Control concurrent modifications to sorted collections.
- Use appropriate transaction isolation.
- Avoid exposing sensitive search results through error messages.
- Apply pagination and resource limits to large retrieval operations.
- Monitor unusual query patterns and excessive requests.

The Python and JavaScript implementations use in-memory lists and arrays. Their insertion and deletion operations can require O(n) element movement.

For frequently modified, large datasets, database indexes, balanced search trees, hash-based indexes, or other specialized structures may be more suitable.

## 13. Execution Requirements

| Deliverable | Runtime |
|---|---|
| Python | Python 3.10 or later |
| JavaScript | Node.js 18 or later |
| C++17 | C++17-compatible compiler |
| Java | Java 17 |
| PostgreSQL | PostgreSQL 14 or later |

The Python, JavaScript, C++, and Java programs use standard language or runtime facilities without third-party dependencies.

The PostgreSQL script creates its schema, tables, indexes, functions, procedures, views, and sample datasets.

Java assertions should be enabled when executing the test suite.

## 14. Educational Assessment

The implementations demonstrate several important algorithmic distinctions:

- Sequential comparison versus interval reduction.
- Midpoint selection versus numerical position estimation.
- Sorted-data requirements.
- Average-case and worst-case complexity.
- Duplicate-value handling.
- Input validation.
- Arithmetic overflow prevention.
- Search-result modeling.
- Performance measurement.
- Data structure maintenance.
- Relational data management.
- Database indexing and query execution.

A key design decision is that algorithm selection depends on the properties of the dataset, not simply the number of available search algorithms.

The most appropriate algorithm is determined by ordering guarantees, data distribution, collection size, update frequency, and operational requirements.
