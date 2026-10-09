# Memory Management: Allocation, Contiguous Allocation, and Fragmentation

## Scope

This project models memory management as a resource-allocation problem in which a fixed memory arena is divided between allocated and free regions.

The implementations focus on three closely related but distinct areas:

- **Memory allocation** determines how a request receives available memory.
- **Contiguous allocation** requires one process or object to occupy a single continuous address range.
- **Fragmentation** describes memory waste or unusable free space created by the allocation strategy.

The central constraint is important: having enough total free memory does not guarantee that a contiguous request can be satisfied. A request for 300 units needs one free region of at least 300 units, not several smaller regions whose combined capacity is 300 or more.

The six deliverables model the same subject from different technical perspectives. Python provides an executable allocator simulator, JavaScript emphasizes event-driven state changes, C++ presents a memory-management case study, Java models an enterprise allocation service, SQL represents memory state relationally, and this README connects the implementation decisions.

## Core Memory Model

A memory arena is represented as a sequence of blocks. Every block has:

- a starting address,
- a size,
- an allocation state,
- and, when allocated, an owner.

A layout can therefore look conceptually like:

`[Process A][FREE][Process B][FREE][Process C][FREE]`

The address ranges are adjacent even though the processes themselves may have very different sizes.

For variable-sized contiguous allocation, a request of size `N` can only use a free block whose size is at least `N`.

When a free block is larger than the request, it is split:

`[FREE 100]` receiving a request for 35 becomes `[ALLOCATED 35][FREE 65]`.

When an allocated block is released, the resulting free block can become adjacent to another free block. Coalescing combines adjacent free regions into a larger region without relocating allocated memory.

## Memory Allocation Strategies

### First Fit

First fit scans the memory layout from the beginning and selects the first adequate free block.

It is simple and generally has low search overhead because the allocator can stop as soon as a suitable region is found. Its decisions depend strongly on the order in which allocations and releases occur.

The Python and JavaScript implementations expose first fit as an explicit allocation strategy, while the C++ and Java implementations use it as one of the policy alternatives.

### Best Fit

Best fit selects the smallest free block that can satisfy the request.

The motivation is to avoid consuming a substantially larger region when a smaller adequate region exists. The trade-off is that repeatedly creating small remainders can produce many unusable holes.

The Python implementation searches candidate blocks by size. The Java service uses a comparator to select the smallest adequate block. The SQL implementation demonstrates the equivalent policy using `ORDER BY block_units LIMIT 1`.

### Worst Fit

Worst fit selects the largest available free block.

The policy deliberately leaves smaller holes untouched while allocating from the largest region. This can preserve medium-sized regions in some workloads, but it may also break up the largest region more aggressively.

The C++ and JavaScript implementations include worst-fit behavior so that the effect of policy selection can be observed rather than described only theoretically.

## Contiguous Allocation

Contiguous allocation gives each allocation a single interval of addresses.

If a process receives addresses 400 through 549, its allocation occupies one continuous 150-unit region.

This provides straightforward address calculations and a simple block representation, but allocation becomes sensitive to the shape of the free-space map.

A system can have:

`FREE 40 + FREE 70 + FREE 100`

with 210 total free units, while a 150-unit request still fails because no individual region is at least 150 units.

This distinction is demonstrated directly by the Python, C++, JavaScript, and Java implementations and is queried explicitly in SQL.

## External Fragmentation

External fragmentation occurs when free memory is distributed among separated regions.

For variable-sized contiguous allocation, a useful diagnostic is:

`external fragmentation = total free memory - largest free block`

This value does not describe every theoretical definition of fragmentation, but it is a practical indicator of how much free memory lies outside the largest immediately usable region.

For example:

| Free regions | Total free | Largest region | External-fragmentation indicator |
| --- | ---: | ---: | ---: |
| 120 | 120 | 120 | 0 |
| 40 + 80 | 120 | 80 | 40 |
| 20 + 30 + 70 | 120 | 70 | 50 |

The third arrangement has the same total free memory as the first two but provides substantially less contiguous capacity for a large request.

The implementations calculate this value after allocation and release operations.

## Internal Fragmentation

Internal fragmentation is different.

It occurs when an allocated unit is larger than the memory actually requested. Fixed-size partitions provide a clear example.

If every partition has 64 units and a process requests 7 units, the partition reserves 64 units and leaves 57 units unused inside the allocation.

For requests of 7, 31, 60, and 64 units:

- requested capacity is 162 units,
- reserved capacity is 256 units,
- internal fragmentation is 94 units.

The Python, C++, Java, and SQL deliverables contain explicit fixed-partition calculations to distinguish this phenomenon from external fragmentation.

Variable-size blocks in these implementations allocate the requested size exactly, so they do not intentionally introduce fixed-partition internal fragmentation.

## Coalescing

Releasing memory does not automatically make every free byte part of one region.

Suppose the layout is:

`[FREE 20][ALLOCATED 40][FREE 30]`

Releasing the middle allocation produces:

`[FREE 20][FREE 40][FREE 30]`

These regions are adjacent and can be coalesced into:

`[FREE 90]`

Coalescing is implemented in Python, JavaScript, C++, and Java.

The operation does not relocate an allocated object. It only combines neighboring free blocks. This makes it substantially cheaper than compaction when suitable adjacent blocks already exist.

## Compaction

Compaction addresses external fragmentation by relocating allocated regions toward one side of the memory arena.

A fragmented layout such as:

`[A][FREE][B][FREE][C][FREE]`

can become:

`[A][B][C][FREE]`

The result is one large free region.

Compaction is not equivalent to ordinary coalescing. Coalescing only combines adjacent free regions. Compaction moves allocated objects and therefore requires relocation support.

The Python implementation explicitly rebuilds the address layout. JavaScript emits a compaction event. C++ uses a build-server scenario to demonstrate why compaction can recover a large contiguous region. Java treats compaction as a service-level operation. SQL reconstructs allocated positions and creates the remaining free region.

In real systems, relocation can require updating references, page mappings, object metadata, or other address-dependent state. Compaction therefore has a cost and should not be treated as an instantaneous operation.

## Python Implementation

The Python program implements `ContiguousMemory` as a variable-partition allocator.

`Block` represents a physical region. It records the starting address, size, allocation state, and owner.

`Strategy` separates allocation policy from memory representation. `FIRST_FIT`, `BEST_FIT`, and `WORST_FIT` select different candidate regions without requiring three separate memory-management implementations.

The allocator validates:

- positive memory sizes,
- non-empty owners,
- duplicate ownership,
- release of unknown allocations,
- and requests for which no adequate contiguous region exists.

The `allocate()` method either consumes an exact free block or splits a larger free block into an allocated block and a remainder.

The `free()` method releases an allocation and immediately performs coalescing.

The `compact()` method relocates allocated blocks toward address zero and reconstructs the final free region.

The `simulate_random_workload()` function shows why fragmentation is workload-dependent. Repeated allocation and release operations can produce a memory layout that differs substantially from a simple static example.

## JavaScript Implementation

The JavaScript implementation models memory as an event-driven resource manager.

`MemoryManager` owns the block list and emits allocation, release, and compaction events. Subscribers can observe those events without becoming part of the allocator's core policy.

This separation is useful in applications where memory-management events might feed:

- monitoring,
- audit logging,
- operational metrics,
- debugging interfaces,
- or resource dashboards.

The JavaScript version also demonstrates asynchronous workload processing. Requests are executed after different delays, reflecting the event-driven nature of Node.js applications.

A failed allocation is represented by `AllocationError` rather than silently producing an invalid memory state.

The event listener is isolated from allocator execution. A monitoring listener that throws an exception does not invalidate the underlying allocation operation.

## C++ Case Study

The C++ implementation models a build server with a 1024-unit memory arena.

Build jobs such as `compiler-A`, `test-runner`, and `linker` receive contiguous memory regions. When jobs finish at different times, their regions are released.

The `BuildServerMemory` class maintains a vector of `Block` objects and supports:

- first-fit allocation,
- best-fit allocation,
- worst-fit allocation,
- release,
- coalescing,
- compaction,
- free-memory measurement,
- largest-contiguous-block measurement,
- and allocation feasibility checks.

The case study deliberately checks total free memory separately from the largest free block. This exposes the actual reason a large build job can fail despite substantial free capacity.

C++ is particularly appropriate for this case because the memory map is represented using explicit value types and a vector, while the implementation can control movement and rebuilding of the block collection directly.

The program uses exceptions for invalid requests and failed allocations and compiles using C++17.

## Java Implementation

The Java implementation models an enterprise analytics platform that runs memory-intensive jobs.

The domain is represented using explicit types:

- `AllocationRequest` represents validated requests.
- `MemoryBlock` represents physical regions.
- `BlockState` separates free and allocated state.
- `AllocationStrategy` expresses the allocation policy.
- `MemoryAllocationService` contains allocation, release, coalescing, compaction, and reporting behavior.

The Java record used for `AllocationRequest` provides an immutable request object with constructor validation.

The service keeps policy decisions separate from the representation of physical blocks. This makes it possible to change allocation policy without redesigning the domain model.

The scenario demonstrates a large model allocation failing before compaction and succeeding after the allocated regions have been compacted.

This implementation emphasizes domain modeling and explicit state rather than reproducing the lower-level C++ representation.

## SQL Data Model

The SQL implementation uses PostgreSQL-compatible DDL.

`memory_arenas` represents physical memory pools.

`processes` represents entities requesting memory.

`memory_blocks` represents the actual allocation map. Its constraints enforce an important invariant:

- a free block cannot reference a process,
- an allocated block must reference a process.

The `memory_events` table provides an audit trail for allocation, release, compaction, and failure events.

The `fixed_partitions` table is intentionally separate because fixed partitions demonstrate internal fragmentation rather than the variable-partition model used by the primary allocator.

## Database-Level Enforcement

The database uses primary keys, foreign keys, `CHECK` constraints, uniqueness constraints, and indexes.

The state constraint on `memory_blocks` prevents an inconsistent combination such as:

`state = FREE` with a non-null process.

The address-range column uses PostgreSQL `int4range`. The GiST index makes range-overlap inspection practical for the address space.

The overlap query checks whether two blocks occupy overlapping address ranges. A correctly constructed memory map should return no rows.

This is an important distinction between application-level logic and database-level integrity. The allocator can decide where memory should go, but the database can still enforce structural invariants on the persisted representation.

## SQL Fragmentation Analysis

The SQL query that aggregates free blocks calculates:

- total free units,
- the largest free block,
- and the external-fragmentation indicator.

The values must not be collapsed into one metric because they answer different operational questions.

Total free memory answers:

`How much capacity remains?`

Largest free block answers:

`What is the largest contiguous request that can be satisfied immediately?`

External fragmentation indicates:

`How much free capacity exists outside the largest contiguous region?`

This distinction is central to contiguous allocation.

## Allocation and Fragmentation Relationship

Allocation strategy influences fragmentation but does not eliminate it.

First fit may leave many small regions near the beginning of the arena.

Best fit can preserve larger blocks but may create small remainders after repeated allocations.

Worst fit deliberately consumes the largest available region, which changes the distribution of remaining holes.

The best strategy therefore depends on workload characteristics, request-size distributions, allocation lifetime, and the cost of searching or compacting memory.

A strategy should not be judged from one allocation sequence alone.

## Failure Conditions

A robust contiguous allocator must distinguish several failure modes.

An invalid request such as zero or negative size is a validation failure.

A duplicate owner allocation is a state-management failure.

A release of an unknown owner is an invalid lifecycle operation.

A request that exceeds total memory is impossible regardless of fragmentation.

A request smaller than total free memory can still fail when no individual free block is large enough.

That last condition is the defining operational consequence of external fragmentation.

## Performance Considerations

A simple block-list allocator may scan every block to locate a suitable region.

First fit can stop at the first adequate block and therefore often performs less searching than policies that inspect all candidates.

Best fit and worst fit generally require evaluating the available candidates to determine the smallest or largest suitable region.

Coalescing requires examining neighboring blocks.

Compaction requires moving or rebuilding allocated regions and can therefore be considerably more expensive than ordinary allocation or release.

The exact performance characteristics depend on the representation. A production allocator may use more sophisticated free-space structures rather than scanning a linear list.

## Common Design Mistakes

Treating total free memory as sufficient evidence that an allocation will succeed is incorrect for contiguous allocation.

Confusing external fragmentation with internal fragmentation leads to incorrect diagnostics. External fragmentation concerns separated free regions, while internal fragmentation concerns unused capacity inside an allocated unit.

Freeing memory without coalescing can leave adjacent free regions represented separately and make the allocator's state unnecessarily fragmented.

Assuming compaction is free ignores the cost of relocating allocated objects.

Using application logic alone to maintain persistent memory-map invariants can allow inconsistent database records when multiple operations or services modify the data.

Choosing an allocation strategy without considering workload behavior can produce poor fragmentation characteristics.

## Security and Reliability Considerations

A real memory-management system must prevent one allocation from overlapping another because overlap can corrupt unrelated data.

Allocation sizes must be validated before arithmetic is performed. Low-level implementations must also guard against integer overflow when calculating address ranges.

Ownership must be explicit so that one process cannot release or manipulate another process's allocation.

Address information should not be exposed unnecessarily to untrusted callers. In systems with virtual memory, applications normally work with virtual addresses rather than direct physical-memory locations.

Audit events are useful when allocation failures or unexpected fragmentation need to be investigated.

## Practical Interpretation

The implementations demonstrate a progression from a simple block list to policy-driven allocation and then to persistence and operational analysis.

The core relationship is:

`allocation policy -> block layout -> release pattern -> fragmentation -> allocation success`

A process does not merely consume an abstract quantity of memory. Under contiguous allocation, the physical shape of free memory becomes part of the allocation decision.

That is why two memory states can contain exactly the same amount of free memory but provide different capabilities for future allocations.

The project keeps allocation, contiguous placement, internal fragmentation, external fragmentation, coalescing, and compaction distinct so that each mechanism can be evaluated according to its actual role in memory management.
