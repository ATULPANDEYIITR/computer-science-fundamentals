# Hash Tables: Collision Handling and Lookup Design

## Scope

This project studies hash tables through four core mechanisms:

- hash functions
- collision detection
- separate chaining
- open addressing with linear probing

The implementations also show how hash-based lookup supports a larger repository-governance scenario without confusing the storage mechanism with the business rules that consume it.

The central abstraction is:

Repository key → hash function → bucket or slot → stored value

A hash table aims to provide near-constant average-time insertion, lookup, and deletion. That performance depends on a suitable hash distribution, controlled load factor, correct collision handling, and appropriate resizing.

## Technical Model

A hash table maps a key `K` to a value `V`.

The basic operation is:

`index = hash(key) mod capacity`

Two different keys can produce the same index. This is a collision. Collisions are normal and must be handled explicitly.

The four major concepts in this project are distinct:

| Concept | Purpose |
|---|---|
| Hash function | Converts a key into a reproducible hash value |
| Collision | Occurs when different keys map to the same table position |
| Separate chaining | Stores multiple colliding entries in a bucket |
| Open addressing | Searches for another slot inside the table |

The implementations also track load factor because a growing occupancy ratio generally increases lookup cost.

`load factor = number of stored entries / table capacity`

A table that grows beyond its configured threshold is resized and its entries are rehashed.

## Separate Chaining

The Python implementation provides a generic `HashTable` using a list of buckets.

Each bucket contains `Entry` objects:

`bucket[index] -> Entry(key, value) -> Entry(key, value) -> ...`

When two keys map to the same index, both remain in the same bucket.

Insertion performs these operations:

1. Validate that the key is hashable.
2. Check whether resizing is necessary.
3. Compute the bucket index.
4. Search the bucket for an existing key.
5. Update the value when the key exists.
6. Otherwise append a new entry.
7. Record collision information when the bucket was already populated.

The implementation exposes:

- current size
- capacity
- load factor
- collision count
- rehash count
- bucket distribution
- longest chain

This makes the effect of hash distribution observable instead of treating the table as an opaque container.

### Complexity

With a reasonable hash function and controlled load factor:

| Operation | Average | Poor distribution |
|---|---:|---:|
| Lookup | O(1) | O(n) |
| Insert | O(1) | O(n) |
| Delete | O(1) | O(n) |
| Resize | O(n) | O(n) |

The worst case occurs when many keys repeatedly map to the same bucket.

## Open Addressing

The Python implementation also contains `OpenAddressingHashTable`.

Instead of storing lists inside buckets, every entry occupies a position directly in the table.

Linear probing searches:

`h(k), h(k)+1, h(k)+2, ...`

with positions wrapped around the table.

Three states are required:

| State | Meaning |
|---|---|
| `EMPTY` | No entry has occupied the slot |
| `OCCUPIED` | A live key/value pair is stored |
| `DELETED` | An entry was removed from the probe sequence |

The deleted state is important. Removing an entry by marking its position as completely empty could terminate a later search too early.

For example:

`A → collision → B → collision → C`

If `B` is removed and its position becomes `EMPTY`, a lookup for `C` may incorrectly stop at the old location of `B`.

A `DELETED` marker preserves the probe sequence.

Open addressing generally requires stricter load-factor control than chaining because performance deteriorates rapidly as the table becomes crowded.

## Python Implementation

The Python file contains two complete hash-table implementations.

### `HashTable`

`HashTable` uses separate chaining and generic type parameters.

Important mechanisms include:

- `dataclass` entries
- explicit validation
- custom exceptions
- dynamic resizing
- collision tracking
- load-factor control
- deletion
- lookup with defaults
- required lookup that raises an exception
- bucket-distribution diagnostics
- executable assertions

`put()` updates an existing key rather than creating duplicate entries.

`add()` has stricter semantics and raises `DuplicateKeyError` when the key already exists.

This distinction demonstrates two common dictionary APIs: replacement semantics and uniqueness-enforced insertion.

### `OpenAddressingHashTable`

The second implementation uses linear probing and explicitly tracks:

- occupied entries
- deleted slots
- probe counts
- rehashes
- capacity
- load factor

The implementation resizes when occupied and deleted slots would push the effective occupancy beyond the configured threshold.

### Validation and Failure Handling

The Python program exercises several failure cases:

- duplicate insertion
- missing required key
- non-hashable key
- deletion of an absent key
- invalid capacity
- invalid load-factor configuration

The executable assertions verify that updates, deletion, reinsertion, and lookup produce expected results.

## JavaScript Implementation

The JavaScript file takes a complementary approach.

`ChainedHashTable` implements separate chaining with explicit FNV-style integer hashing. JavaScript objects are not used as the underlying table so that the bucket mechanism remains visible.

The key representation includes the JavaScript type:

`type:key`

This prevents simple textual collisions such as treating numeric `10` and string `"10"` as the same logical key.

The implementation uses:

- classes
- `Map`
- `Set`
- `Symbol`
- asynchronous functions
- Promises
- event listeners
- explicit error classes
- structured policy objects

### Linear Probing

`LinearProbingHashTable` uses `Symbol` values for `EMPTY` and `DELETED`.

This avoids ambiguity between a legitimate stored value and an internal slot marker.

The implementation records probe counts to make clustering effects measurable.

### Event-Driven Policy Cache

`PolicyCache` demonstrates a practical use of hash-based lookup.

Repository policies are indexed by repository identifier. A cache miss invokes an asynchronous loader. Once loaded, the policy is stored in the hash table.

Policy changes generate events:

`policy-updated`

and invalidations generate:

`policy-invalidated`

This separates storage from event handling and prevents the cache from becoming responsible for unrelated policy decisions.

The asynchronous loader also illustrates why a hash table can be one component of an application without being the application's complete architecture.

## C++17 Implementation

The C++ program implements a generic `ChainedHashTable<Key, Value, Hash>`.

The table uses:

- `std::vector`
- `std::optional`
- `std::find_if`
- `std::any_of`
- custom exceptions
- templates
- explicit resize operations

The table accepts a custom hash functor.

`RepositoryKeyHash` combines the organization and repository name hashes so a repository can be identified by a composite domain key.

The storage layer is separated from governance logic.

### Governance Engine

`GovernanceEngine` maps:

`RepositoryKey → ReviewPolicy`

The merge-eligibility engine evaluates:

- pull-request state
- draft status
- merge conflicts
- required approvals
- reviewer eligibility
- dismissed approvals
- status checks
- resolved conversations

The hash table performs fast policy lookup while the governance engine evaluates the rules.

This separation is deliberate:

`Hash table = indexed storage`

`Governance engine = domain decision`

A data structure should not silently become the business-rule engine that uses it.

### Composite Keys

The C++ program demonstrates a repository key containing:

- organization
- repository name

The equality operator determines key identity, while `RepositoryKeyHash` determines the hash value.

Two repositories with the same repository name but different organizations therefore remain distinct.

## Java 17 Implementation

The Java program models a repository-governance workflow using explicit domain types.

Important records include:

- `RepositoryKey`
- `Branch`
- `Commit`
- `ReviewPolicy`
- `Reviewer`
- `Review`
- `StatusCheck`

The `PullRequest` class owns state transitions.

Its states are:

`DRAFT → OPEN → MERGED`

or:

`OPEN → CLOSED → OPEN`

Invalid transitions raise `IllegalStateException`.

This prevents application code from arbitrarily changing repository workflow state.

### Hash-Based Policy Index

`PolicyIndex` uses Java's `HashMap` to map:

`RepositoryKey → ReviewPolicy`

The application does not manually implement bucket management because Java's standard collection handles hashing, collisions, resizing, and internal bucket organization.

The domain code instead focuses on:

- key validation
- policy lookup
- reviewer eligibility
- approval counting
- stale approval exclusion
- status-check evaluation
- merge eligibility

This demonstrates an important engineering distinction between implementing a data structure and consuming a production-quality implementation of that data structure.

### Review Eligibility

A reviewer must hold a suitable repository role.

The governance service counts an approval only when:

- the review is approved
- the review is not stale
- the reviewer is eligible

A guest reviewer may submit an approval-like record but does not satisfy the repository's approval requirement.

This prevents raw approval counts from being treated as equivalent to valid approvals.

## PostgreSQL Model

The PostgreSQL implementation models a repository workflow relationally.

The main relationship is:

`Repository → Branch → Pull Request → Review → Review Comment`

Additional relationships connect:

- commits
- reviewers
- status checks
- branch-protection policies
- audit records

### Hash-Related Database Behavior

PostgreSQL uses indexes internally to accelerate equality and other predicates. The project deliberately models the logical domain relationally rather than attempting to recreate a general-purpose hash table in SQL.

The unique constraint on:

`repositories(organization, repository_name)`

creates an index-backed uniqueness guarantee.

The `EXPLAIN` query demonstrates how PostgreSQL can inspect the access path chosen for a repository lookup.

This illustrates the difference between:

`Application hash table`

and:

`Database index`

An application hash table is an in-memory data structure directly controlled by application code. A database index is managed by PostgreSQL as part of its storage and query-planning architecture.

## PostgreSQL Integrity Rules

The SQL schema uses database-level controls for important invariants.

Examples include:

- foreign keys
- unique constraints
- check constraints
- enumerated workflow states
- protected-branch policy validation
- review and comment relationships
- commit identity constraints
- status-check state validation

The `prevent_invalid_protection()` trigger prevents a restrictive governance policy from being attached to an unprotected branch.

The `audit_pull_request_changes()` trigger records significant pull-request state changes in `hash_table_audit`.

This keeps important integrity rules at the database boundary instead of relying only on application code.

## Merge Eligibility Workflow

The SQL function `merge_eligibility()` performs an explicit eligibility evaluation.

The logical sequence is:

`Pull Request`
→ `Target Branch`
→ `Protection Policy`
→ `Eligible Approvals`
→ `Status Checks`
→ `Unresolved Comments`
→ `Eligibility Decision`

An approval is counted only when the reviewer:

- is active
- has an accepted reviewer role
- submitted an approved review
- does not have a stale approval

A passing status condition requires the relevant checks to be `PASSED`.

Unresolved review comments can prevent eligibility when the branch policy requires conversation resolution.

Merge conflicts immediately prevent eligibility.

The function returns both the decision and diagnostic values, including:

- approval count
- required approval count
- status-check result
- unresolved comment count
- failure reason

This makes the decision auditable rather than returning only a Boolean.

## Collision and Performance Considerations

Hash-table performance depends heavily on distribution and occupancy.

A poor hash function can transform an expected O(1) operation into O(n).

Separate chaining tolerates higher load factors because multiple entries can share a bucket, but long chains increase traversal cost.

Open addressing stores entries directly in the table and can have strong cache locality, but it becomes sensitive to clustering and high occupancy.

Linear probing has particularly simple memory behavior, yet adjacent occupied slots can form clusters.

Resizing reduces these effects by increasing capacity and recomputing positions.

Rehashing has O(n) cost, but resize operations are normally amortized across many insertions.

## Security Considerations

Hash-table correctness is not the same as security.

Important considerations include:

- untrusted keys should not be allowed to cause uncontrolled memory growth
- externally controlled inputs should have sensible size limits
- predictable or adversarial hash behavior can increase collision cost
- sensitive values should not be emitted in debug reports
- cache invalidation must prevent stale authorization or policy decisions
- authorization decisions should not rely solely on the presence of a hash-table entry
- database constraints should protect critical invariants even when application validation is bypassed

Hash flooding is a practical concern for services that accept large numbers of attacker-controlled keys. Production runtimes may use randomized or hardened hashing strategies to reduce predictable collision attacks.

## Edge Cases

The implementations explicitly address several edge conditions.

### Empty Tables

Lookup and reporting operate correctly when no entries exist.

### Missing Keys

Lookup APIs can return a default value, while required lookup APIs raise an explicit failure.

### Duplicate Keys

Replacement semantics are used by `put()`. The stricter `add()` operation rejects duplicates.

### Deleted Open-Addressing Slots

Deletion produces a `DELETED` state rather than `EMPTY`, preserving probe chains.

### Resizing

Entries are reinserted after capacity changes because their old positions are no longer necessarily valid.

### Stale Decisions

The governance examples distinguish an existing approval record from a currently valid approval.

### Conflicting Repository State

A pull request with merge conflicts remains ineligible even when approvals and status checks are otherwise valid.

## Relationship Between the Five Implementations

| Implementation | Primary perspective | Hash-table mechanism |
|---|---|---|
| Python | Explicit data-structure study | Chaining and linear probing |
| JavaScript | Event-driven application component | Chaining and linear probing |
| C++17 | Generic systems-oriented component | Template-based chaining |
| Java 17 | Enterprise domain model | `HashMap` policy index |
| PostgreSQL | Relational persistence and governance | Index-backed equality lookup |

The languages intentionally do not implement identical programs.

Python exposes the mechanics most directly.

JavaScript adds asynchronous loading and event-driven cache invalidation.

C++17 emphasizes generic storage, custom hashing, value semantics, and explicit control over the table.

Java 17 emphasizes domain types and controlled state transitions while delegating low-level hash-table management to `HashMap`.

PostgreSQL expresses the same repository concepts through relational integrity, indexes, transactions, triggers, functions, and reporting queries.

## Domain Workflow

The repository-oriented examples use a workflow in which hash-based lookup is one supporting mechanism:

Repository
→ Branch
→ Pull Request
→ Commits
→ Reviews
→ Review Comments
→ Status Checks
→ Protection Policy
→ Eligibility Evaluation
→ Merge

Each stage has a different responsibility.

A hash table provides efficient lookup.

A review represents an evaluation of proposed changes.

An approval is a particular review decision that can satisfy a policy requirement.

A status check represents automated validation.

A branch-protection policy establishes repository-level restrictions.

The final eligibility decision combines these independent conditions.

## Practical Trade-Offs

| Design | Strength | Limitation |
|---|---|---|
| Separate chaining | Simple deletion and flexible occupancy | Pointer/list traversal can reduce locality |
| Linear probing | Compact storage and strong locality | Sensitive to clustering and load factor |
| Standard library hash map | Mature implementation and optimized runtime behavior | Internal mechanics are less visible |
| Database index | Durable, query-planner-integrated lookup | Not equivalent to an application-memory hash table |
| Explicit policy index | Clear application-level separation | Requires cache invalidation and lifecycle management |

## File Behavior

The five source files are independently executable in their respective environments.

The Python program demonstrates two manually implemented hash-table strategies and validates them with assertions.

The JavaScript program adds asynchronous policy loading and event-based cache invalidation.

The C++17 program combines a generic hash table with a repository-governance engine and custom composite hashing.

The Java 17 program models repository workflow and review policy through records, enums, collections, and explicit state transitions.

The PostgreSQL script creates a complete relational schema, inserts representative data, enforces integrity rules, evaluates merge eligibility, reports review state, and demonstrates transactional behavior.

Together, the implementations distinguish hash-table mechanics from the higher-level systems that use efficient key-based lookup.
