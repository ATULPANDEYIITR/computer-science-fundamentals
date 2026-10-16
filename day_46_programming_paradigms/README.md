# Programming Paradigms: Procedural, Object-Oriented, Functional, and Declarative Programming

## Technical scope

Programming paradigms describe different ways of expressing computation, organizing state, and defining program behavior. Procedural, object-oriented, functional, and declarative programming are related approaches, but they answer different design questions.

This project examines the distinctions through a repository-quality and change-governance scenario. A proposed software change contains commits, modifies files, receives reviews, produces automated check results, and must satisfy repository policies before it can be merged.

The scenario makes the paradigms concrete:

- **Procedural programming** describes the sequence of operations required to calculate change metrics and coordinate a workflow.
- **Object-oriented programming** organizes repository entities and behavior into objects that maintain domain invariants.
- **Functional programming** transforms immutable inputs into derived metrics and decisions while limiting side effects.
- **Declarative programming** expresses conditions that must hold, leaving a rule evaluator to determine whether those conditions are satisfied.

The implementations use different architectural perspectives rather than forcing every language to reproduce the same design.

## The four paradigms and their distinctions

### Procedural programming

Procedural programming organizes a computation into operations performed in a defined sequence. Variables represent the current state of the computation, and control structures determine which operation runs next.

The Python implementation's `procedural_line_audit()` function illustrates this approach. It traverses a sequence of commits, accumulates additions and deletions, tracks distinct changed files in a set, and counts security-related commits. Each operation updates an accumulator or collection before the function returns the completed report.

This structure is useful when execution order is meaningful. A migration procedure, release pipeline, data-import job, or repository audit often needs explicit sequencing because later operations depend on earlier results.

Procedural code also makes some failure modes visible. If a mutable accumulator is initialized incorrectly, updated twice, or reused between independent runs, the final report can be wrong. Keeping accumulators local to the function reduces this risk.

### Object-oriented programming

Object-oriented programming combines state and behavior around domain entities. An object exposes operations that are valid for its state while protecting internal details from arbitrary modification.

The Python `Commit`, `PullRequest`, `Review`, and `ReviewPolicy` classes represent repository concepts. A commit validates its identity, author, file paths, and line counts at construction. A pull request verifies that its source and target branches differ and that it contains at least one commit.

The Java implementation develops this approach further. Its `PullRequest` class owns review submissions, status-check results, discussion state, and lifecycle transitions. Operations such as `markReady()`, `close()`, `reopen()`, and `merge()` reject invalid transitions instead of allowing callers to assign any state freely.

Object-oriented design is especially useful when a domain contains entities with related state and behavior. Its principal risk is excessive coupling: if every object directly controls every other object, a change to one rule can create unexpected effects across the system.

### Functional programming

Functional programming emphasizes transformations, composition, and predictable results. Pure functions calculate outputs from their inputs without modifying external state. Immutable values make those calculations easier to test and reason about.

The Python `functional_metrics()` function derives aggregate line changes, average additions and deletions, security-related commit IDs, and frequently modified file paths. It uses `map`, `filter`, `reduce`, and immutable commit records to make the data-processing steps explicit.

The JavaScript implementation uses `flatMap()` and `reduce()` in `summarizeChangedFiles()`. It converts commits into file-level records and combines those records into a report showing file-touch counts, contributing authors, and net line changes.

Functional transformations are useful for reporting, policy analysis, data pipelines, and parallelizable calculations. A pure transformation is easier to test because the same input produces the same result under the same rules. That guarantee does not automatically extend to timestamps, network calls, database operations, or other effects, which should be isolated from the transformation itself.

### Declarative programming

Declarative programming specifies desired conditions rather than describing every operational step required to achieve them.

The Python `Rule` type associates a rule name with a predicate and a failure message. `evaluate_declarative_rules()` applies these predicates to a pull request and collects the failed conditions. The caller specifies rules such as requiring a title, requiring commits, prohibiting draft merges, and requiring distinct source and target branches.

The PostgreSQL implementation expresses related policies through `CHECK` constraints, foreign keys, unique constraints, indexes, and a merge-eligibility view. The schema states which data relationships and conditions must hold. PostgreSQL enforces the database constraints regardless of whether a record is inserted by a Python application, a Java service, or a direct SQL client.

Declarative programming does not eliminate execution. A query planner must execute a SQL query, and a policy evaluator must evaluate predicates. The distinction is that the program's specification emphasizes the required result or valid condition instead of a manually prescribed sequence of state mutations.

## How the paradigms work together

A production system rarely needs to choose only one paradigm.

A repository governance service can use procedural orchestration to receive an event and coordinate operations, objects to represent the pull request and its reviews, functional transformations to calculate change statistics, and declarative policies to determine whether the proposed merge is allowed.

These responsibilities should remain distinguishable:

| Concern | Primary approach | Repository example |
|---|---|---|
| Operation sequence | Procedural | Aggregate commit metrics and coordinate processing |
| Domain state and invariants | Object-oriented | Represent commits, reviews, and pull-request lifecycle |
| Derived calculations | Functional | Compute file-level change reports without modifying source records |
| Required conditions | Declarative | Express merge requirements and database integrity rules |

These are not mutually exclusive categories. A method in an object-oriented program may use functional transformations. A procedural workflow may execute declarative SQL statements. A functional pipeline may evaluate predicates that represent a declarative policy.

The important design decision is which approach best expresses each responsibility.

## Python implementation

The Python script uses a single repository scenario to demonstrate four different forms of computation.

### Domain validation

The frozen `Commit`, `PullRequest`, `Review`, and `ReviewPolicy` data classes provide explicit domain structures. Their `__post_init__()` methods validate data at construction time.

Commit validation rejects negative line counts, duplicate paths, empty identifiers, and paths that attempt to traverse outside the repository. Pull-request validation rejects missing commits and identical source and target branches.

The `frozen=True` setting prevents ordinary field reassignment after object construction. It does not automatically make every nested object immutable, so the script uses tuples and frozen sets where collection immutability matters.

### Procedural metrics

`procedural_line_audit()` traverses commits and maintains local accumulators. Its result is a dictionary containing the number of commits, total additions, total deletions, net line change, distinct changed files, and security commits.

The set of file paths is important because the same file can appear in multiple commits. Summing the number of file entries would count repeated modifications more than once.

### Object-oriented policy evaluation

`RepositoryQualityService` combines a repository name, protected-branch set, and `ReviewPolicy`. Its `evaluate()` method returns a `MergeDecision` containing eligibility and explicit blocking reasons.

The service considers draft status, distinct valid approvals, active change requests, required status checks, unresolved conversations, and linear-history requirements. A missing check and a failing check both block the merge.

The example uses a simplified review-history model. A real service must identify the latest review using an authoritative timestamp or sequence number and must account for dismissals, reviewer permissions, changes to the reviewed commit, and policy changes.

### Functional metrics

`functional_metrics()` returns derived data rather than modifying the original commits. Its average calculations handle empty input, and its `reduce()` calls use explicit initial values so that empty sequences do not cause reduction errors.

The output also identifies files touched by multiple commits. Repeatedly modified files can indicate areas that deserve closer review, although repetition alone does not establish that a file is defective.

### Declarative rules

`build_declarative_rules()` defines structural requirements as predicates. The evaluator does not need to know how each condition is implemented; it only needs the predicate and its failure message.

The rule engine is intentionally separate from `RepositoryQualityService`. The former evaluates basic structural conditions, while the latter evaluates the wider merge-governance policy. Keeping these responsibilities separate prevents a basic validation rule from being mistaken for a complete repository protection mechanism.

## JavaScript implementation

The JavaScript file emphasizes event-driven behavior, lifecycle transitions, and immutable event records.

### Event-driven workflow

`RepositoryWorkflow` extends Node.js's `EventEmitter`. Its methods emit events when a pull request is opened, becomes ready, synchronizes with the base branch, receives a review, completes a status check, resolves a discussion, or is merged.

The workflow distinguishes commands from events. A method such as `recordCheck()` changes workflow state, while the emitted `status_check.completed` event describes the recorded outcome. An audit listener can collect events without embedding audit-reporting logic into every caller.

This separation helps reduce coupling between workflow behavior and downstream consumers. In a distributed system, an in-memory event emitter would not provide durable delivery, replay, or transactional guarantees. Those requirements would need a persistent event log or message-delivery mechanism.

### State and lifecycle validation

The implementation distinguishes draft, open, closed, and merged states. A draft can be marked ready, but a second attempt to mark an already-open pull request ready is rejected. Merging a closed or already merged request also fails.

Base synchronization requires the new revision to be greater than the recorded revision. Review submissions must reference a commit belonging to the pull request. These checks prevent invalid lifecycle operations from silently modifying the model.

### Event snapshots and mutation boundaries

The `#emitChange()` method constructs and freezes an event snapshot. Listeners receive event data rather than a direct reference to the mutable pull-request aggregate.

The `deepFreeze()` helper is suitable for this example's ordinary objects, arrays, and maps used as output data. Freezing a JavaScript `Map` does not prevent its entries from being changed through `set()` or `delete()`, so the workflow does not expose its internal maps directly.

The SHA-256 value generated for the demonstration merge result is an illustrative identifier, not a Git object ID. Real merge commits require Git's object format and commit metadata.

### Functional file analysis

`summarizeChangedFiles()` uses `flatMap()` to produce file-level change records and `reduce()` to combine them. The original commits remain unchanged, while the resulting report aggregates file touches, contributing authors, and net line changes.

This approach is appropriate for reporting because the transformation can be tested independently of the workflow's lifecycle operations.

## C++ case study

The C++ program models a governance engine for a software repository with protected `main` and `release` branches.

### Architecture and data structures

`Commit`, `Review`, `PullRequest`, `BranchPolicy`, and `Decision` are value-oriented structures. `GovernanceEngine` owns the policy and exposes an `evaluate()` operation.

The implementation uses:

- `std::vector` to preserve commit and review order.
- `std::set` to represent distinct authors, changed paths, approvers, and required checks.
- `std::map` to associate reviewers with their latest active review and check names with their outcomes.
- `std::find_if` to validate that each review references a commit included in the pull request.

These structures match the domain. Sets prevent duplicate approvals from the same reviewer from increasing the count, while maps make check lookup and reviewer-state replacement straightforward.

### Merge-eligibility algorithm

The evaluator validates the pull request, checks its lifecycle state, identifies the protected target branch, and calculates the latest active review for each reviewer.

It excludes commit authors from approval counting and blocks active change requests. It then verifies that the approval count reaches the configured threshold and that every required check has passed. Unresolved conversations and non-linear history also block a protected-branch merge when the policy requires those conditions to be satisfied.

For a pull request with \(C\) commits, \(R\) reviews, and \(F\) distinct file paths, ordered map and set operations generally add logarithmic lookup costs. Review processing is approximately \(O(R \log R)\) in the worst case for map insertion, while unique-file collection is approximately \(O(F \log F)\) for set insertion, apart from the cost of validating commit references. A production implementation could index commit IDs to avoid repeatedly scanning all commits.

### Protected-branch operations

The engine treats direct pushes, force pushes, and branch deletion as separate policy checks. This is deliberate: merge eligibility does not itself prevent a user from bypassing the pull-request workflow.

The boolean bypass parameter illustrates an administrative exception path. In production, the caller must establish authorization using trusted identity and repository permissions. A caller must not be allowed to self-declare that it has bypass privileges.

### Validation and limitations

The program rejects empty identifiers, negative line counts, duplicate commit IDs, missing commit contents, and paths that escape the repository. Its simplified path check is suitable for demonstrating an invariant but is not a complete filesystem canonicalization mechanism.

The case study also assumes that reviews arrive in chronological order. A production implementation should use authoritative timestamps or event sequence numbers and explicitly define the effect of a new commit on earlier approvals.

## Java implementation

The Java program emphasizes domain modeling and an enterprise-oriented policy service.

### Records and explicit domain types

The program uses Java 17 records for commits, reviews, review comments, branch protection policies, and merge decisions. Records make data structures concise and provide generated accessors and value-based equality.

Compact record constructors validate input before an instance is accepted. Collections are copied or wrapped to prevent callers from changing the validated collection through an external reference.

Enums represent change kinds, review states, pull-request states, and merge strategies. This is safer than using unrestricted strings for values that must belong to a known set.

### Lifecycle transitions

The `PullRequest` class controls transitions between draft, open, closed, and merged states. Methods such as `markReady()`, `close()`, `reopen()`, and `merge()` enforce the allowed transition rules.

A merge is rejected if the supplied `MergeDecision` is ineligible. The state change therefore depends on the result of the governance service instead of being exposed as an unrestricted field assignment.

The model records the base revision against which review took place. Synchronization advances that revision, making the state available for detecting a stale review baseline.

### Enterprise policy evaluation

`MergeEligibilityService` evaluates the branch protection policy against the pull request. The policy contains the required approval count, required status checks, eligible reviewers, conversation-resolution rule, linear-history rule, and administrative bypass setting.

Review history is sorted by submission time, after which the latest non-dismissed review for each reviewer is retained. Approval counting then excludes commit authors and reviewers who are not eligible under the policy.

Required checks are evaluated by name. A missing check is not treated as successful merely because no failure was recorded.

The administrator bypass path is explicitly configured rather than inferred from a username. In a production system, the bypass decision must be authorized by a trusted access-control layer and recorded in an audit trail.

### Type safety and exception handling

`DomainException` represents invalid domain operations, including illegal state transitions and malformed records. The use of enums, records, and validation methods prevents many invalid states from entering the model.

The current implementation is an educational domain model rather than a concurrent service. A multi-user repository service would also require concurrency control, persistent state, atomic merge operations, authorization checks, and a strategy for handling policy changes between evaluation and merge.

## PostgreSQL relational model

The SQL script represents repository governance as related tables and database-enforced constraints.

### Data model

| Table | Purpose |
|---|---|
| `repositories` | Identifies repositories and their default branches |
| `branches` | Stores branch names, revisions, and deletion state |
| `reviewers` | Stores reviewer identity, activity, and bypass capability |
| `branch_protection` | Defines branch-level approval, check, and operation policies |
| `pull_requests` | Records proposed changes, lifecycle state, and base revisions |
| `commits` | Stores commit metadata, author, change kind, and line counts |
| `pull_request_commits` | Associates commits with pull requests in a defined order |
| `status_checks` | Stores check outcomes against particular revisions |
| `reviews` | Records reviewer decisions and dismissal metadata |
| `review_comments` | Stores review discussion entries and resolution state |

Foreign keys preserve relationships between repositories, branches, pull requests, commits, and reviews. Unique constraints prevent duplicate branch names within a repository, duplicate pull-request numbers within a repository, duplicate commit positions within a pull request, and duplicate check results for the same pull request, check name, and revision.

`CHECK` constraints enforce local invariants, including valid lifecycle values, non-negative line counts, positive pull-request numbers, and valid review states.

### Trigger-based integrity

The `enforce_review_commit()` trigger function verifies that a review references a commit associated with its pull request. A foreign key alone cannot enforce this multi-table relationship because the required condition depends on the pull-request-to-commit association.

The trigger rejects an invalid review before it is stored. The application therefore cannot create a review against an unrelated commit simply by submitting a syntactically valid review record.

### Merge-eligibility view

The `merge_eligibility` view combines current pull-request state with review history, branch policy, and status-check outcomes.

Its `latest_reviews` common table expression selects the most recent review per reviewer. The approval calculation counts distinct active reviewers whose current decision is approval and who are not authors of commits in the pull request.

The check evaluation looks for successful results at the current base revision. A result from an older revision is not automatically accepted after the base branch changes.

The view produces an array of blocking reasons so that an application can display policy failures without reconstructing the entire decision from unrelated queries.

### Indexing and query performance

The indexes support common governance access patterns:

- `idx_pull_requests_target_state` supports searches for open pull requests targeting a branch.
- `idx_pull_request_commits_commit` supports reverse lookup from a commit to its associated pull requests.
- `idx_reviews_latest` supports reviewer-history lookups ordered by submission time.
- `idx_status_checks_latest` supports locating recent check results for a particular pull request and check name.
- `idx_unresolved_comments` is a partial index for unresolved review comments.

Indexes increase storage and write costs, so their usefulness depends on actual query patterns and table size. Execution plans and production workloads should guide further indexing.

### Transactions and merge integrity

The script runs its schema creation and sample-data workflow inside a transaction. This allows the setup to be committed as a unit or rolled back if a statement fails.

The merge-eligibility view is an evaluation mechanism, not an atomic merge operation. A production merge transaction must lock or otherwise coordinate the relevant records, recheck eligibility, verify the current base revision, and record the merge atomically. Merely reading an eligible result does not prevent a new review, failed check, or branch update from making the decision stale.

## Common implementation risks

### Confusing state with policy

A pull request being open does not mean that it is eligible for merging. Lifecycle state describes where the request is in its workflow; policy evaluation determines whether required conditions hold at a particular time.

### Counting historical approvals

Counting every approval ever submitted can incorrectly satisfy a review threshold. A dismissed approval or a later change request can alter the effective review state. The evaluator must use the current decision under an explicit ordering rule.

### Accepting stale evidence

A successful check for an earlier revision may not validate the current changes. Approval invalidation and check freshness depend on repository configuration and the relationship between the reviewed commit and the current proposed merge.

### Treating comments as approvals

A comment may explain a concern without recording an approval decision. Review content and review state must be represented separately. A system should not infer approval merely because a reviewer submitted a comment.

### Confusing validation with authorization

Checking that a reviewer name exists is not equivalent to verifying that the authenticated person is allowed to review a repository. Similarly, a policy flag describing administrator bypass does not prove that the caller is an administrator.

### Ignoring concurrency

Two users may evaluate the same pull request while its checks, reviews, or target branch are changing. A decision calculated from one snapshot can become invalid before a merge completes. Persistent implementations need an atomic merge procedure or equivalent concurrency controls.

## Practical applications

These four paradigms are useful in different parts of repository automation.

Procedural processing suits release orchestration, audit exports, and ordered migration tasks. Object-oriented models suit domain entities whose state must change through validated operations. Functional transformations suit code-change analytics, review metrics, and deterministic reports. Declarative rules suit repository policies, validation specifications, and database integrity constraints.

A well-designed implementation combines these approaches where they provide distinct value. The choice should follow the responsibility being implemented, the required state guarantees, the complexity of the rules, and the operational constraints of the system.
