# Functional Programming: Pure Functions, Higher-Order Functions, Immutability, and Lambda Expressions

## Scope

This project models functional programming through four closely related mechanisms:

- **Pure functions** compute results from explicit inputs without observable side effects.
- **Higher-order functions** accept functions as arguments or return functions as values.
- **Immutability** prevents an existing value from being changed after construction.
- **Lambda expressions** provide concise function values for predicates, transformations, and composition.

The implementations use these mechanisms in a consistent domain: **order processing**. Orders contain customers, line items, discounts, validation rules, and derived totals. This domain is useful because calculations can be expressed as transformations without requiring shared mutable state.

The implementations deliberately use different language-specific designs rather than translating the same program between languages.

## Functional Model

The central data flow is:

`Order values → validation → transformation → filtering → aggregation → derived result`

An order has an identity, customer, item prices, and a discount rate. Its subtotal and final total are derived values rather than independently stored mutable state.

The important distinction is between changing an existing order and deriving another order.

For example, adding an item conceptually performs:

`old order → new order`

The original order remains available. The same principle applies to changing a discount.

## Pure Functions

A pure function has two important properties:

| Property | Meaning |
|---|---|
| Deterministic result | Identical inputs produce the same result |
| No relevant side effect | The function does not modify external state |

The Python implementation uses `calculate_total()` and `apply_discount()` as pure calculations. The JavaScript implementation separates `subtotal()` and `total()` from validation and asynchronous orchestration. C++ calculates totals through `const` references without changing the supplied `Order`. Java uses methods on an immutable-style record to derive values.

The SQL implementation uses read-only functions such as `calculate_subtotal()` and `calculate_total()`. These functions derive values from relational data instead of changing the rows they inspect.

Pure functions make testing easier because their expected result can be determined entirely from their arguments.

## Higher-Order Functions

A higher-order function treats behavior as data.

Python provides `transform()`, `filter_orders()`, and `compose()`. `transform()` receives an operation and applies it to each value. `compose()` creates a new function by connecting two transformations.

JavaScript uses array `map()`, `filter()`, `reduce()`, and a custom `mapWith()` function. Arrow functions provide compact behavior values.

C++ uses templates so `mapValues()` and `filterValues()` can accept arbitrary callable objects. This demonstrates a language-specific form of generic higher-order processing.

Java uses `Function<T,R>` and `Predicate<T>`. The `transform()` method accepts a `Function`, while `select()` accepts a `Predicate`. This allows domain policies to be represented explicitly as behavior.

PostgreSQL is different. SQL is declarative and does not provide ordinary SQL functions as first-class values in the same manner as Python functions, JavaScript functions, or Java functional interfaces. The database therefore models functional behavior through deterministic functions and parameterized policy functions such as `qualifies_high_value()`.

## Immutability

Immutability means that an existing value is not changed after it has been created.

The Python `Order` is a frozen dataclass, and its item collection is a tuple. `add_item()` creates another `Order` rather than modifying the original object.

JavaScript uses `Object.freeze()` for orders and their item arrays. `addItem()` constructs a new object with a new item collection. This is important because JavaScript arrays are mutable by default.

C++ passes the source order as a `const` reference and returns a copied order when a transformation is required. The design avoids exposing mutation as the normal transformation mechanism.

Java uses a record with `List.copyOf()` for defensive copying. `withAdditionalItem()` and `withDiscount()` construct new records.

The SQL model naturally supports immutable-style calculations because queries derive results without modifying source rows. Database transactions are still required when stateful operations such as order-state changes occur.

## Lambda Expressions

Lambda expressions are anonymous functions that are useful when behavior is short and local.

Examples of their role include:

| Language | Functional mechanism |
|---|---|
| Python | `lambda`, `map`, `filter`, `reduce` |
| JavaScript | Arrow functions, `map`, `filter`, `reduce` |
| C++17 | Lambda expressions with STL algorithms |
| Java 17 | Lambda expressions with `Function` and `Predicate` |
| PostgreSQL | Declarative functions and query expressions rather than first-class lambda syntax |

The implementations avoid using lambdas merely for stylistic compression. They are used where passing behavior makes the operation reusable or expresses a domain rule clearly.

## Python Implementation

The Python file models orders with a frozen dataclass.

`calculate_total()` and `apply_discount()` are pure calculations. `transform()` demonstrates a higher-order function by receiving an operation. `filter_orders()` receives a predicate, while `compose()` combines two functions.

The `Order` value is immutable. Adding an item or changing the discount creates a new order.

The script also performs explicit validation:

- Order identifiers must be positive.
- Customer names cannot be empty.
- Orders must contain items.
- Item prices cannot be negative.
- Discount rates must remain between zero and one.
- Duplicate order identifiers are rejected.

The `reduce_total()` function demonstrates aggregation without storing a separate mutable running total outside the reduction operation.

## JavaScript Implementation

The JavaScript implementation uses Node.js-compatible syntax without external packages.

JavaScript's arrow functions provide concise function values, while `map`, `filter`, and `reduce` support transformation pipelines.

The implementation uses `Object.freeze()` to protect order objects and their item arrays. Since JavaScript normally allows array mutation, freezing both levels is significant.

`processOrders()` introduces an asynchronous boundary using a promise while keeping the actual domain transformations deterministic. This separates asynchronous orchestration from pure calculations.

`groupByCustomer()` uses a `Map`, which is appropriate for grouping dynamically named customers without relying on object-property coercion.

Validation checks JavaScript-specific failure conditions such as `NaN`, infinity, incorrect types, and invalid discount values.

## C++17 Implementation

The C++ implementation treats functional programming as a combination of immutable-style domain objects, generic algorithms, and callable parameters.

`std::transform`, `std::copy_if`, and `std::accumulate` provide the central processing mechanisms.

The generic `mapValues()` function accepts an operation as a template parameter. This avoids committing the function to one particular callable type.

The order transformations return new `Order` objects. The original object is passed through a `const` reference, which prevents accidental modification during the operation.

This design also exposes a practical trade-off. Returning new objects improves reasoning about state but may require additional allocations or copies. For small domain values this is usually straightforward. Large object graphs may require move semantics, structural sharing, or more specialized data structures.

## Java 17 Implementation

The Java implementation emphasizes explicit domain modeling.

The `Order` record provides immutable value semantics, while its compact constructor validates domain invariants. `List.copyOf()` prevents callers from retaining a mutable reference to the original item collection.

`OrderPolicy` is a functional interface. Different policies can therefore be supplied without changing the order-processing service.

`ProcessingState` makes the workflow state explicit:

`RECEIVED → VALIDATED → ELIGIBLE`

A policy failure produces `REJECTED`.

`Function<T,R>` and `Predicate<T>` represent transformation and selection behavior. Streams provide a declarative processing style for filtering, mapping, and grouping.

This approach is suitable for enterprise code where domain policies need explicit types rather than anonymous calculations scattered throughout application logic.

## PostgreSQL Implementation

The SQL model represents customers, orders, line items, and order-state events.

The main relationships are:

`customers → orders → order_items`

`orders → order_events`

Primary keys identify each entity, foreign keys preserve relationships, and check constraints enforce valid discounts and non-negative prices.

The `calculate_subtotal()` and `calculate_total()` functions derive order values. They do not mutate the underlying rows.

The `order_totals` view provides a reusable derived representation. The `eligible_high_value_orders` view applies a deterministic value policy.

The CTE query demonstrates a functional-style relational pipeline:

`computed → qualified → projection`

The first CTE derives totals, the second applies a predicate, and the final query selects the required result.

The database also demonstrates where functional purity stops being appropriate. Order-state changes are inherently stateful, so `set_order_state()` performs a transactional update and records an event. PostgreSQL triggers provide audit behavior when the state changes.

## Validation and Failure Behavior

Functional programming does not remove the need for validation. It changes where and how validation is expressed.

The implementations validate values before transformations occur. Invalid input is rejected rather than silently normalized.

Important failure cases include:

| Failure | Handling |
|---|---|
| Negative item price | Validation exception or database constraint |
| Invalid discount | Validation exception or `CHECK` constraint |
| Empty customer | Domain validation |
| Empty order | Domain validation |
| Invalid identifier | Domain validation |
| Missing database order | PostgreSQL exception |
| Invalid numeric JavaScript value | Explicit finite-number validation |
| Mutable collection exposure | Defensive copying or freezing |

The database adds a second enforcement layer. Application validation improves usability, while relational constraints protect data integrity even if another client bypasses the application.

## Functional Composition

Composition combines smaller transformations into a larger transformation.

A simplified conceptual pipeline is:

`amount → add service fee → apply tax → final amount`

Python implements this through `compose()`. JavaScript uses a variadic `compose()` function. C++ expresses the individual transformations as lambda expressions. Java uses `Function<Double, Double>`.

Composition is useful when each operation has a clear responsibility. It also makes testing easier because individual transformations can be tested independently.

## Performance Considerations

Functional style does not automatically mean better performance.

Mapping, filtering, and reduction generally require linear time:

`O(n)`

where `n` is the number of processed values.

Order subtotal calculation is also `O(k)`, where `k` is the number of line items.

Creating immutable-style values can increase memory use because modified values may require new collections or objects. This is the principal trade-off against direct mutation.

The SQL implementation benefits from an index on `orders.customer_id` and `order_items.order_id` because those columns participate in relationship lookups. An index is not added to every column because unnecessary indexes increase storage and write-maintenance cost.

## Security and Reliability Considerations

Functional programming can reduce accidental state corruption, but it does not automatically make a system secure.

Important controls in the examples include:

- Rejecting invalid numeric values.
- Enforcing domain invariants before calculations.
- Using database constraints as an independent integrity boundary.
- Avoiding accidental mutation of shared collections.
- Using transactions for state-changing database workflows.
- Recording state transitions for auditability.
- Avoiding dynamic SQL where ordinary parameterized functions and queries are sufficient.

Pure calculations should not be confused with authorization. A pure function can calculate a value correctly while an application still exposes that value to an unauthorized caller.

## Relationship Between the Four Core Concepts

The concepts reinforce one another but are not interchangeable.

**Pure functions** describe the behavior of a calculation.

**Higher-order functions** describe how behavior can be passed into another operation.

**Immutability** describes the lifetime and modification rules of data.

**Lambda expressions** provide one syntax for creating function values.

A lambda can be pure, but a lambda is not automatically pure. A higher-order function can invoke an impure function. Immutable data can still be processed by impure code. These distinctions matter when designing larger systems.

The strongest functional designs make dependencies explicit, minimize shared mutable state, isolate side effects, and compose deterministic transformations into larger workflows.
