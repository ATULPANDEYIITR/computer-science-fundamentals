
# Error and Exception Handling

This project treats error and exception handling as a control-flow and reliability concern rather than as a collection of language-specific `try` and `catch` statements.

The implementations model a repository deployment service in which invalid input, missing resources, configuration failures, transient storage failures, and permanent operational failures have different recovery strategies.

The central distinction is:

- **Errors** describe conditions in which an operation cannot produce its intended result.
- **Exceptions** provide a structured mechanism for transferring control from the failure point to a layer capable of handling the condition.
- **Exception propagation** allows intermediate layers to avoid handling failures they cannot meaningfully recover from.
- **Defensive programming** prevents invalid state from entering the system and narrows the number of failure conditions that later code must handle.

## Failure Model

The implementations use several deliberately distinct failure classes.

| Failure | Meaning | Appropriate response |
|---|---|---|
| Validation failure | Input violates a domain rule | Reject immediately |
| Configuration failure | Required runtime configuration is invalid | Stop initialization or fail safely |
| Not found | Requested resource does not exist | Return a resource-specific failure |
| Persistence failure | Storage operation cannot complete | Translate and report the infrastructure failure |
| Transient failure | Operation may succeed if retried | Retry within a bounded policy |
| Permanent failure | Retrying is unlikely to help | Propagate to an appropriate boundary |

A useful failure path is:

`External Input → Validation → Domain Operation → Infrastructure Operation → Exception Propagation → Recovery Boundary`

Each layer should handle a failure only when it has enough information to recover correctly.

## Python Implementation

The Python program models repository persistence using `Repository`, `RepositoryStore`, and domain-specific exception classes.

`ValidationError`, `ConfigurationError`, `RepositoryNotFoundError`, and `RepositoryStorageError` establish meaningful exception categories instead of exposing every low-level failure directly to application code.

The persistence implementation uses a temporary file before replacing the destination. This reduces the chance of leaving a partially written JSON document when the process encounters a filesystem failure.

The `save()` and `load()` methods also demonstrate exception translation. A filesystem `OSError` becomes `RepositoryStorageError`, while a missing file becomes `RepositoryNotFoundError`. The original exception is retained through Python's exception chaining with `raise ... from exc`.

The resulting relationship is:

`OSError → RepositoryStorageError`

rather than exposing filesystem-specific details throughout the application.

The retry implementation deliberately retries storage failures but does not retry validation failures or missing resources. Retrying an invalid repository name does not change the input, so another attempt has no value.

The script also demonstrates the distinction between handling and propagation. `initialize_application()` does not catch `ConfigurationError` because it cannot repair missing configuration. The exception propagates to the application boundary where it can be logged and handled.

### Python defensive techniques

- Input validation occurs before domain objects are used.
- Domain exceptions describe failures at the business boundary.
- Low-level exceptions are translated rather than leaked.
- Exception chaining preserves diagnostic information.
- Retry attempts are bounded.
- Temporary file replacement reduces partial-write risk.
- Logging records operational failures without exposing unnecessary internal data.

## JavaScript Implementation

The JavaScript implementation uses Node.js event-driven behavior around a `RepositoryStore`.

Custom `Error` subclasses distinguish validation, configuration, storage, and missing-resource failures. This allows callers to make recovery decisions with `instanceof` instead of matching arbitrary error strings.

`async` and `await` are used to demonstrate asynchronous exception propagation. An exception thrown by `RepositoryStore.get()` can cross several asynchronous function boundaries and eventually be handled by the caller.

The store emits `saved` and `deleted` events after successful state changes. Events are therefore emitted only after the operation has passed its failure boundary.

The retry mechanism uses an explicit transient-error classifier. Only `StorageError` is retried. Validation and not-found failures are allowed to propagate immediately.

The `toSafeHttpResponse()` function provides an application boundary between internal exceptions and externally visible responses. Internal implementation details should not automatically become public error messages.

For example, an internal configuration exception produces a generic configuration response rather than exposing configuration contents.

The final `main().catch(...)` is an unhandled-rejection boundary. It ensures that an unexpected asynchronous failure is converted into a controlled process failure instead of silently becoming an unobserved rejection.

## C++17 Implementation

The C++ program models a repository catalog and deployment transaction.

The exception hierarchy separates:

- `ValidationError`
- `ConfigurationError`
- `RepositoryError`
- `RepositoryNotFound`
- `TransientStorageError`

The repository catalog uses `std::map` to provide deterministic lookup and storage behavior.

Validation occurs before insertion. This prevents malformed repository objects from becoming persistent domain state.

The deployment transaction demonstrates a failure-sensitive workflow. If a later staged repository cannot be inserted, the operation enters its recovery path and attempts to restore the catalog.

`AuditScope` demonstrates RAII. Its destructor is declared `noexcept`, ensuring that cleanup does not introduce a second exception while the program is already handling another failure.

This is important in C++ because an exception escaping a destructor during stack unwinding can terminate the process.

The C++ implementation also separates exception ownership from exception origin. A lower-level operation creates the exception, while `main()` provides the application-level handling boundary.

## Java 17 Implementation

The Java implementation represents an enterprise repository service using explicit domain types.

`Repository` is an immutable record containing the repository name, owner, default branch, and lifecycle state.

The `RepositoryState` enum makes the repository lifecycle explicit:

`ACTIVE → ARCHIVED`

An archived repository cannot be registered as an active repository. This is a domain rule rather than merely an input-format rule.

The checked exceptions represent service-level failure conditions:

- `DomainValidationException`
- `RepositoryNotFoundException`
- `PersistenceException`
- `TransientPersistenceException`

The persistence abstraction is represented by the `RepositoryRepository` interface. The in-memory implementation therefore behaves like an infrastructure adapter without coupling the service to a particular database.

`RepositoryService` owns the business workflow. It validates lifecycle state and applies a bounded retry policy to transient persistence failures.

The retry loop catches `TransientPersistenceException` specifically. A generic `Exception` catch would be dangerous because it could accidentally retry permanent failures such as invalid state or duplicate repository creation.

The implementation also demonstrates multi-catch handling at the application boundary, where domain and persistence failures can be reported differently from unexpected runtime programming errors.

## PostgreSQL Implementation

The PostgreSQL script moves part of the error model into the database itself.

The relational model contains:

- `repositories`
- `deployment_attempts`
- `error_events`

The `repository_state` enum prevents arbitrary lifecycle values.

Database constraints enforce invariants independently of application code. Repository names must follow a defined pattern, owners and branches cannot be empty, and deployment statuses are restricted to known values.

This is an important defensive-programming principle:

`Application validation + database constraints`

The database should not assume that every caller will correctly validate input.

### Trigger validation

The `repositories_validate_before_write` trigger performs validation that is associated directly with repository persistence.

This protects the table even when an operation does not originate from the expected application service.

### Stored exception handling

`archive_repository()` uses `RAISE EXCEPTION` for invalid state transitions and missing repositories.

`register_deployment_failure()` validates error information before inserting the deployment and error event records.

PostgreSQL transactions provide atomicity for state changes. A transaction can either commit a complete workflow or roll the database state back when an unhandled failure occurs.

### Error reporting

The `repository_error_summary` view aggregates total, transient, and permanent failures.

The CTE used for latest failures demonstrates a reporting pattern in which operational errors are separated from the current repository state.

## Exception Propagation

Propagation should move an exception toward a layer that has enough context to make a recovery decision.

    Input
      │
      ▼
    Validation
      │
      ├── invalid ───────────────► reject
      │
      ▼
    Domain operation
      │
      ├── domain failure ────────► business handler
      │
      ▼
    Infrastructure operation
      │
      ├── transient ─────────────► bounded retry
      │
      ├── not found ─────────────► resource handler
      │
      └── permanent ─────────────► application boundary

Catching an exception too early can be as problematic as failing to catch it.

A layer that cannot recover should normally propagate the exception rather than replacing it with an unrelated success value or silently ignoring the failure.

## Defensive Programming

Defensive programming is broader than exception handling.

The implementations apply it through:

- validating external values before use
- enforcing non-empty identifiers
- restricting lifecycle states
- distinguishing transient and permanent failures
- limiting retry counts
- preserving exception causes
- using database constraints
- avoiding broad exception catches
- preventing partial persistence where practical
- separating internal diagnostics from external error responses

Defensive programming should not mean catching every possible exception. It means designing the system so invalid assumptions are detected at the earliest useful boundary.

## Retry Semantics

Retrying is appropriate only when failure characteristics justify another attempt.

A transient storage timeout is a plausible retry candidate.

An invalid repository name is not.

A missing repository is normally not a transient condition either.

The general policy used by the implementations is:

| Condition | Retry |
|---|---|
| Invalid input | No |
| Invalid configuration | No |
| Missing resource | No |
| Duplicate resource | No |
| Temporary storage failure | Yes, bounded |
| Unknown programming failure | No automatic retry |

Retries should also be bounded. An unlimited retry loop can convert a recoverable failure into resource exhaustion.

## Exception Translation

Exception translation is useful at architectural boundaries.

For example:

`Filesystem OSError → RepositoryStorageError`

and:

`Transient persistence failure → service-level retry decision`

The translation should preserve the original cause whenever the language supports it. This provides useful diagnostics without forcing every layer to understand infrastructure-specific exception types.

## Security Considerations

Error messages can unintentionally disclose sensitive implementation information.

External responses should not expose:

- filesystem paths
- credentials
- connection strings
- internal stack traces
- secret configuration values
- database internals
- private infrastructure identifiers

Internal logs can contain more diagnostic information, but logging should still avoid credentials, tokens, session data, and other secrets.

Error handling is therefore also an information-disclosure boundary.

## Performance and Reliability

Exception handling should not be used as ordinary branching for expected high-frequency conditions.

Validation can often prevent predictable failures before expensive operations begin.

Database indexes are applied only to access patterns represented by the reporting queries. The deployment history index supports repository-specific recent-attempt lookups, while the error-code index supports operational error analysis.

Retry loops are bounded to prevent repeated failures from consuming unlimited resources.

In production systems, retry policies may also require delay, backoff, and a limit on concurrent retries. A retry policy should account for whether the underlying operation is safe to repeat.

## Failure Boundaries

The five implementations use different mechanisms but preserve the same architectural principle.

| Implementation | Primary failure boundary |
|---|---|
| Python | Domain exception translation and application handler |
| JavaScript | Async propagation and safe response conversion |
| C++ | RAII cleanup and application-level exception handling |
| Java | Service layer with typed checked exceptions |
| PostgreSQL | Constraints, triggers, functions, and transactions |

The objective is not to eliminate failures. The objective is to make failures explicit, classifiable, diagnosable, and recoverable when recovery is actually possible.
