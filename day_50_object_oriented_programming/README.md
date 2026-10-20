# Object-Oriented Programming: Classes, Objects, Encapsulation, Inheritance, and Polymorphism

## Scope

This project models the four central object-oriented programming mechanisms through a consistent progression:

- **Classes** define the structure and behavior of domain entities.
- **Objects** are concrete runtime instances of those classes.
- **Encapsulation** protects internal state and exposes controlled operations.
- **Inheritance** allows specialized types to reuse and extend a common abstraction.
- **Polymorphism** allows code to operate through a common interface while concrete objects provide different behavior.

The implementations deliberately use different application domains so that the concepts are demonstrated rather than mechanically translated between languages.

## Conceptual Model

A class can be viewed as a behavioral contract for a family of objects.

    BankAccount / Employee / Shape
                  |
        ---------------------
        |         |         |
     subtype   subtype   subtype
        |         |         |
       Specialized behavior through
          polymorphic operations

The important distinction is that inheritance describes an **is-a** relationship, while object composition and references describe **has-a** relationships. Good object-oriented design uses inheritance when substitutability is meaningful rather than merely to reuse code.

## Classes and Objects

A class combines state with operations that work on that state.

In Python, `Account` stores an account number, owner, and protected balance. Concrete objects such as `SavingsAccount` and `CurrentAccount` represent independent accounts with their own state.

In JavaScript, `Employee` is the common class and `Engineer` and `Manager` create specialized objects.

In C++, `Shape` establishes an abstraction while `Rectangle` and `Circle` are concrete objects managed through owning smart pointers.

In Java, `BankAccount` defines the common account contract and concrete account objects maintain their own lifecycle state.

The SQL implementation represents persistent object-like state through relational rows. Each `bank_account` row represents an individual domain instance.

## Encapsulation

Encapsulation means that an object's internal representation is controlled rather than exposed for unrestricted modification.

The Python implementation uses a private-by-convention `_balance` attribute and exposes a read-only `balance` property. Deposits and withdrawals validate amounts before changing the balance.

JavaScript uses the stronger language-level private field `#salary`. Code outside the class cannot directly access that field. The public `salary` setter validates changes.

C++ stores shape dimensions in private fields. Clients cannot directly change dimensions and must use the validated `scale()` operation.

Java keeps account fields private and exposes controlled methods such as `deposit()`, `withdraw()`, `freeze()`, `activate()`, and `close()`.

PostgreSQL applies the same principle at the database boundary. `CHECK` constraints, triggers, and stored functions prevent invalid persistent states such as negative balances or closing an account with a non-zero balance.

Encapsulation is therefore not merely about hiding fields. Its important purpose is preserving invariants.

## Inheritance

Inheritance creates a specialized class from an existing abstraction.

The Python implementation derives `SavingsAccount` and `CurrentAccount` from `Account`. Both inherit common identity and balance behavior while implementing different withdrawal policies.

JavaScript derives `Engineer` and `Manager` from `Employee`. Both reuse employee validation and salary state but provide different bonus calculations.

C++ derives `Rectangle` and `Circle` from the abstract `Shape` class. Each concrete shape supplies its own area, perimeter, and scaling behavior.

Java derives `SavingsAccount` and `BusinessAccount` from `BankAccount`. The common account lifecycle is centralized while withdrawal rules differ by account type.

Inheritance is useful when a subtype can genuinely substitute for its parent abstraction. If two classes merely share implementation details without sharing the same conceptual contract, composition is often a better design.

## Polymorphism

Polymorphism allows the caller to use a common abstraction while the runtime selects specialized behavior.

In Python, `calculate_total_balance()` accepts `Account` objects without knowing their concrete types. Withdrawal behavior is resolved according to the actual account class.

In JavaScript, `PayrollService` calls `employee.calculateBonus()`. The same call produces different results for engineers and managers.

C++ demonstrates runtime polymorphism most explicitly. `ShapeRepository` stores `std::unique_ptr<Shape>`. Calls such as `area()`, `perimeter()`, and `scale()` are dispatched to the concrete shape implementation.

Java uses `BankAccount` references inside `BankingService`. The service can process savings and business accounts without duplicating collection logic for every subtype.

The key distinction is:

    Common contract
          |
          +---- concrete implementation A
          |
          +---- concrete implementation B
          |
          +---- concrete implementation C

    Caller uses the contract.
    The concrete object supplies the behavior.

## Python Implementation

The Python program uses a banking domain.

`Account` establishes the basic encapsulated state and validation rules. `SavingsAccount` adds interest behavior, while `CurrentAccount` changes withdrawal semantics through an overdraft limit.

`Reportable` is an abstract interface. `AccountReport` demonstrates multiple inheritance by combining account behavior with a reporting contract.

The program also demonstrates Python's duck-typing-friendly style through functions that accept iterables of domain objects. The `calculate_total_balance()` function does not need to know which account subclass it receives.

File output demonstrates a practical standard-library operation without introducing external dependencies.

Important failure cases include:

- Empty account identifiers
- Empty owners
- Negative opening balances
- Invalid interest rates
- Invalid deposits
- Invalid withdrawals
- Insufficient funds
- Invalid overdraft configuration
- File-writing failures

## JavaScript Implementation

The JavaScript program models payroll.

`Employee` owns private salary state through the ECMAScript `#salary` syntax. The getter and setter form a controlled public boundary.

`Engineer` and `Manager` override `calculateBonus()` and `describe()`. The payroll service interacts with employees through their common behavior instead of testing every subtype explicitly.

The implementation also uses asynchronous file I/O through Node.js `fs/promises`. This demonstrates how object-oriented domain logic can coexist with JavaScript's event-driven execution model.

Validation covers identifiers, names, salaries, specialties, team sizes, and tax rates.

The `PayrollService` performs type validation before calculating pay. This is important because JavaScript is dynamically typed and callers can otherwise pass structurally unrelated objects.

## C++ Implementation

The C++ implementation models a geometry engine.

`Shape` is an abstract class with pure virtual operations. `Rectangle` and `Circle` provide concrete implementations.

`ShapeRepository` owns its shapes using `std::unique_ptr`. This gives explicit ownership semantics and automatic destruction without manual `delete` operations.

The design demonstrates:

- Abstract classes
- Pure virtual functions
- Virtual destructors
- Runtime dispatch
- RAII
- Exclusive ownership
- Private state
- Exception-based validation

The repository does not need separate collections for rectangles and circles. It operates on `Shape`, which is the useful abstraction.

Complexity for reporting is **O(n)** for `n` stored shapes. Scaling all shapes is also **O(n)**. Memory usage is **O(n)** for the owned shape objects and their pointers.

## Java Implementation

The Java program models enterprise banking.

`Customer` is an immutable record containing validated customer identity.

`BankAccount` is an abstract domain type with private mutable state and explicit lifecycle transitions:

    ACTIVE <----> FROZEN
       |
       v
     CLOSED

Closure is permitted only when the balance is zero. Deposit and withdrawal operations require the account to be active.

`SavingsAccount` implements `InterestBearing` and calculates interest using its own policy.

`BusinessAccount` supports a credit limit and therefore has withdrawal behavior different from a savings account.

`BankingService` stores the common `BankAccount` abstraction and uses Java streams for filtering and aggregation. It also prevents duplicate account numbers.

The implementation uses Java 17 records, enums, interfaces, abstract classes, collections, streams, immutable customer data, exceptions, and explicit state transitions.

## PostgreSQL Implementation

The PostgreSQL model converts the object-oriented banking concepts into persistent relational structures.

The main entities are:

| Table | Purpose |
|---|---|
| `customer` | Stores customer identity |
| `bank_account` | Stores account state and subtype-specific attributes |
| `account_transaction` | Stores financial operations |

`account_type` represents the two concrete account categories:

- `SAVINGS`
- `BUSINESS`

`account_status` represents lifecycle state:

- `ACTIVE`
- `FROZEN`
- `CLOSED`

The `bank_account` constraints enforce subtype-specific invariants. A savings account must have an interest rate and no credit limit. A business account must have a credit limit and no interest rate.

Stored functions act as controlled domain operations:

- `deposit_money()`
- `withdraw_money()`
- `apply_savings_interest()`

These functions update account state and transaction history together.

The withdrawal function uses `SELECT ... FOR UPDATE`, which prevents concurrent transactions from modifying the same account based on stale balance information.

The trigger function prevents invalid closure and reinforces account-specific rules.

## Constraints and Invariants

An invariant is a condition that should remain true throughout the object's valid lifetime.

Examples implemented across the project include:

| Invariant | Enforcement |
|---|---|
| Account balance cannot be negative | Python/Java/C++ validation and SQL `CHECK` |
| Deposit must be positive | Domain methods and SQL function |
| Withdrawal must be positive | Domain methods and SQL function |
| Closed account must have zero balance | Java state transition and PostgreSQL trigger |
| Savings account requires interest rate | Constructor validation and SQL constraint |
| Business account requires credit limit | Constructor validation and SQL constraint |
| Duplicate account numbers are forbidden | Java service and SQL `UNIQUE` |
| Invalid shape dimensions are rejected | C++ constructor |
| Invalid employee salary is rejected | JavaScript private-state setter |

Keeping invariants close to the object or database boundary reduces the chance that unrelated application code can create invalid state.

## Inheritance Versus Composition

Inheritance is appropriate when the subtype satisfies the parent abstraction.

For example:

    SavingsAccount is a BankAccount
    Engineer is an Employee
    Circle is a Shape

Composition would be preferable when an entity simply uses another entity:

    BankingService has accounts
    PayrollService has payroll rules
    Repository has shapes

This distinction prevents large inheritance hierarchies from becoming the default mechanism for every relationship.

## Error Handling

Each implementation rejects invalid domain operations rather than silently correcting them.

Python uses `ValueError` subclasses and explicit exception handling.

JavaScript uses a custom `ValidationError` and rejected asynchronous operations.

C++ uses `ValidationError` derived from `std::runtime_error`.

Java uses `IllegalArgumentException` for invalid construction and `IllegalStateException` for invalid lifecycle operations.

PostgreSQL raises exceptions from domain functions and uses constraints and triggers for database-level enforcement.

Different failure mechanisms are appropriate to each runtime, but the domain principle remains the same: invalid state should be rejected at a controlled boundary.

## Performance Considerations

Most collection operations are linear in the number of objects.

The Python balance aggregation is **O(n)**.

The JavaScript payroll calculation is **O(n)** for `n` employees.

The C++ repository report and scaling operations are **O(n)**. `std::unique_ptr` avoids ownership ambiguity without requiring garbage collection.

The Java service uses stream operations with linear traversal for filtering and aggregation.

The PostgreSQL model indexes customer references, account status, and transaction history. The transaction-history index supports account-specific recent-history queries without indexing every column unnecessarily.

## Security and Reliability Considerations

Object-oriented encapsulation is not a complete security boundary by itself. It primarily protects invariants inside an application process.

Production financial systems would also require authorization, authentication, audit controls, concurrency policies, encryption, transaction isolation decisions, idempotency, monitoring, and regulatory controls.

The SQL implementation demonstrates one important reliability mechanism: row locking during withdrawal. Without appropriate concurrency control, two simultaneous withdrawals could both observe the same available balance and produce an invalid result.

The JavaScript implementation validates runtime inputs because JavaScript does not provide compile-time enforcement of domain types.

C++ requires careful ownership design because incorrect raw-pointer management can cause memory leaks or use-after-free errors. `std::unique_ptr` makes ownership explicit.

## Relationship Between the Five Implementations

The implementations are deliberately not line-for-line translations.

| Language | Domain perspective | Main OOP emphasis |
|---|---|---|
| Python | Banking accounts | Encapsulation, inheritance, abstract interfaces |
| JavaScript | Payroll | Private fields, overriding, asynchronous processing |
| C++17 | Geometry engine | Abstract classes, virtual dispatch, RAII |
| Java 17 | Enterprise banking | Domain modeling, state transitions, interfaces, records |
| PostgreSQL | Persistent banking model | Constraints, functions, triggers, transactions |

Together they show that object-oriented programming is not a single syntax pattern. The central design concern is the relationship between state, behavior, abstraction, specialization, and controlled state transitions.
