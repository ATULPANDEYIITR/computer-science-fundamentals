# Memory Hierarchy

## Introduction

Memory hierarchy is the organization of computer storage into multiple levels with different capacities, access latencies, bandwidth characteristics, costs, and physical relationships to the processor.

A simplified hierarchy is:

- CPU registers
- L1 cache
- L2 cache
- L3 cache
- Main memory (RAM)
- SSD or HDD
- Other persistent or remote storage

The fundamental design principle is to keep frequently needed information in faster storage while retaining less frequently accessed information in larger, slower storage.

A modern processor does not normally retrieve every operand directly from RAM. It attempts to satisfy requests from registers or cache. When the required information is not present at a particular level, the request proceeds toward lower levels of the hierarchy.

The effectiveness of this design depends heavily on locality of reference.

The implementations in this repository study memory hierarchy from three complementary perspectives:

- Python provides executable conceptual models and simulations.
- JavaScript demonstrates memory-aware application behavior, typed arrays, caching, asynchronous storage, and runtime-level considerations.
- C++ develops an industry-style transaction analytics system and connects its data structures to cache locality, virtual memory, TLB behavior, and performance.

## Fundamental concepts

### What is memory hierarchy?

Memory hierarchy is a layered arrangement of storage technologies.

Higher levels are generally:

- smaller
- faster
- more expensive per byte
- physically closer to CPU execution

Lower levels are generally:

- larger
- slower
- cheaper per byte
- farther from CPU execution

The hierarchy allows a computer to combine the speed of small memories with the capacity of large memories.

The most important idea is not simply that one memory is faster than another. The hierarchy works because programs often exhibit predictable access patterns.

### Registers

Registers are very small storage locations directly available to processor instructions.

Examples include:

- general-purpose registers
- instruction pointer or program counter
- stack pointer
- status or flags registers
- control registers
- vector and SIMD registers

Registers are much smaller in aggregate capacity than RAM. Their purpose is to provide extremely fast working storage for active computation.

The Python implementation models registers with a dictionary to explain the conceptual role of register storage. This is a software abstraction rather than direct access to physical processor registers.

### Cache

A cache stores copies of recently or frequently used information closer to the CPU.

A cache is usually divided into cache lines. A cache line is the unit of data transfer between cache levels and is typically much larger than a single scalar variable.

A simplified cache contains:

- data
- a tag
- validity information
- sometimes a dirty state
- replacement information

The tag identifies which memory block is currently stored in a cache location.

### Cache hit

A cache hit occurs when the requested block is already available at the cache level being checked.

A hit avoids accessing lower levels.

### Cache miss

A cache miss occurs when the requested block is not present at the cache level being checked.

The processor or memory subsystem must obtain the required data from a lower level.

The classic three-category model is:

- compulsory miss
- capacity miss
- conflict miss

#### Compulsory miss

A compulsory miss occurs when a block is accessed for the first time and has never previously been loaded into the cache.

#### Capacity miss

A capacity miss occurs when the working data exceeds the capacity available at a cache level.

Even a well-designed cache cannot keep an unlimited working set resident.

#### Conflict miss

A conflict miss occurs when multiple blocks compete for the same cache location.

Conflict behavior is particularly visible in direct-mapped caches and becomes less restrictive as associativity increases.

## Locality of reference

Locality is one of the central principles behind memory hierarchy.

### Temporal locality

Temporal locality means that recently accessed data or instructions are likely to be accessed again soon.

For example, a loop that repeatedly updates the same variable has strong temporal locality.

A cache can exploit temporal locality by retaining recently used blocks.

### Spatial locality

Spatial locality means that memory locations near a recently accessed location are likely to be accessed soon.

A sequential scan through an array is a classic example.

If a processor requests one element from an array, the cache may fetch an entire cache line containing neighboring elements. Subsequent accesses to nearby elements can therefore be served without another trip to RAM.

The Python and JavaScript implementations demonstrate sequential, strided, and random access patterns. The C++ implementation uses contiguous `std::vector` storage for a transaction-processing workload.

### Locality is not guaranteed

Not every workload has strong locality.

Examples of potentially poor locality include:

- unpredictable pointer chasing
- large random-access datasets
- working sets much larger than cache capacity
- poorly organized data structures
- some graph algorithms
- irregular sparse computations

Good performance engineering therefore examines the actual access pattern rather than assuming that a particular data structure is always faster.

## Cache organization

### Direct-mapped cache

A direct-mapped cache gives each memory block exactly one possible cache location.

A simplified mapping rule is:

`index = block_number % number_of_lines`

The tag identifies which block is currently occupying that location.

The Python, JavaScript, and C++ implementations all contain direct-mapped cache demonstrations.

The main advantage is simplicity. Lookup and hardware organization are comparatively straightforward.

The major limitation is conflict behavior. Two frequently used blocks that map to the same line can repeatedly replace each other.

### Set-associative cache

A set-associative cache divides the cache into sets.

A block maps to one set but can occupy one of several ways within that set.

For example, a two-way set-associative cache allows two different blocks that map to the same set to coexist.

Higher associativity generally reduces conflict misses, but it requires more tag comparisons and replacement logic.

The Python, JavaScript, and C++ implementations demonstrate set associativity with an LRU-style replacement mechanism.

### Fully associative cache

In a fully associative design, a block can be placed in any cache line.

This minimizes placement restrictions but requires substantially more comparison and replacement machinery.

Fully associative structures are therefore used selectively in real systems rather than as the default organization for every cache.

## Cache replacement

When a set is full and a new block must be inserted, an existing block must be selected for replacement.

Common replacement strategies include:

- LRU
- pseudo-LRU
- FIFO
- random replacement

### LRU

Least Recently Used replacement removes the entry that has not been accessed for the longest time.

LRU is conceptually useful because it corresponds closely to temporal locality.

The implementations use LRU-style logic in software simulations.

Real hardware often uses approximations because maintaining perfect LRU state for large, highly associative caches can be expensive.

## Cache lines

Caches normally operate on blocks rather than individual bytes.

A cache line contains a range of adjacent memory addresses.

This supports spatial locality.

Suppose a program accesses one element of a contiguous array. The processor may load a cache line containing that element and neighboring elements. If the program subsequently accesses nearby elements, those accesses may become cache hits.

This is one reason data layout matters.

## Cache tags and indexes

A simplified cache address can be divided into:

- tag
- index
- block offset

The block offset identifies a byte within the cache line.

The index identifies a set or cache location.

The tag identifies which memory block is represented by the selected cache location.

Real processors may have additional details such as physical versus virtual indexing, address hashing, sectoring, banking, and coherence state.

## Multi-level caches

Modern CPUs commonly use multiple cache levels.

A simplified path is:

`CPU → L1 → L2 → L3 → RAM`

L1 is generally smaller and faster than L2.

L2 is generally larger and slower than L1.

L3 is generally larger again and may be shared among multiple cores.

Exact cache organization varies significantly by processor generation and architecture.

The Python and C++ simulations model a simplified L1/L2/L3 hierarchy.

The purpose of the simulation is to understand the layered decision process rather than reproduce every feature of a particular commercial CPU.

## Average Memory Access Time

Average Memory Access Time, commonly abbreviated AMAT, is a useful performance model.

For a single cache level:

`AMAT = hit time + miss rate × miss penalty`

For example, if:

- hit time = 1 ns
- miss rate = 5%
- miss penalty = 10 ns

then:

`AMAT = 1 + 0.05 × 10`

which gives:

`1.5 ns`

For multiple cache levels, the miss penalty at one level includes the cost of searching lower levels.

A simplified model can be expressed as:

`L1 time + L1 miss rate × (L2 time + L2 miss rate × (L3 time + L3 miss rate × RAM penalty))`

This is a model rather than a complete hardware timing equation. Real processors include overlapping requests, queues, prefetching, out-of-order execution, memory-level parallelism, coherence traffic, and many other factors.

## Write policies

Cache writes introduce another important design choice.

### Write-through

With write-through caching, a write to the cache is also propagated to the next memory level.

Advantages include:

- simpler visibility to lower levels
- straightforward dirty-state management

Disadvantages include:

- potentially greater write traffic
- increased pressure on lower memory levels

### Write-back

With write-back caching, modified data can remain in the cache until the line is evicted or another operation requires propagation.

A dirty bit identifies modified data.

Advantages include:

- reduced lower-level write traffic
- efficient repeated modifications to the same cache line

Disadvantages include:

- more complex state management
- dirty-line tracking
- more complex eviction behavior

The Python, JavaScript, and C++ implementations contain simplified write-back demonstrations.

## Write allocation

Write allocation is a separate decision from write-through or write-back policy.

With write-allocate:

- a write miss causes the block to be loaded into the cache
- the processor then modifies the cached block

With no-write-allocate:

- a write miss is sent directly to a lower level
- the block does not necessarily enter the cache

Write-back with write-allocate is a common conceptual combination, but real designs can use more specialized policies.

## Prefetching

Prefetching attempts to load data before the processor explicitly requests it.

Sequential access is a predictable pattern, so a processor may detect it and fetch subsequent cache lines.

Benefits can include:

- reduced effective latency
- better throughput for predictable scans

Costs can include:

- wasted bandwidth
- cache pollution
- unnecessary energy consumption
- displacement of useful data

The Python implementation contains a simple sequential prefetcher model.

A software simulation cannot reproduce a real processor's hardware prefetching algorithms, but it illustrates the basic trade-off.

## RAM

Random Access Memory, normally called RAM or main memory, provides much greater capacity than CPU caches.

RAM is slower than registers and CPU caches but substantially faster than persistent storage for ordinary memory accesses.

RAM is volatile, meaning its contents normally disappear when power is removed.

The operating system manages physical memory and provides processes with virtual address spaces.

## Virtual memory

Virtual memory allows a process to use virtual addresses rather than directly addressing physical RAM.

A simplified virtual memory system divides memory into pages.

Physical memory is divided into frames.

A page table maps virtual pages to physical frames.

For a page size of 4096 bytes:

`virtual_page = virtual_address / 4096`

`offset = virtual_address % 4096`

The physical address can then be represented as:

`physical_address = physical_frame × 4096 + offset`

The offset remains unchanged during ordinary page translation.

The Python, JavaScript, and C++ implementations model page-table translation.

## Page tables

A page-table entry can contain information such as:

- physical frame number
- present or absent state
- writable permission
- executable permission
- user/kernel accessibility
- accessed state
- dirty state
- architecture-specific control bits

The simplified implementations model only a subset of these concepts.

Real page tables can be multi-level or use other hierarchical structures to avoid allocating a giant flat table for every possible virtual address.

## Page faults

A page fault occurs when a required virtual page is not currently available in the required physical-memory state.

The operating system may need to:

- locate the page
- allocate a frame
- read data from storage
- update page-table state
- invalidate or update translation-cache state
- resume the interrupted instruction

A page fault is therefore fundamentally different from an ordinary CPU cache miss.

A cache miss can often be resolved through another cache level or RAM. A page fault can require operating-system intervention and potentially storage access.

## TLB

The Translation Lookaside Buffer, or TLB, caches recent virtual-to-physical address translations.

Without a TLB, repeated memory accesses could require page-table lookup operations.

With a TLB:

`virtual address → TLB lookup → physical address`

If the translation is present, the TLB provides it quickly.

If the translation is absent, the processor must perform the appropriate page-table translation process.

The Python, JavaScript, and C++ implementations contain simplified TLB simulations.

## Cache coherence

Multicore CPUs may contain private caches for individual cores.

Suppose two cores access the same memory location.

If one core modifies its cached copy, other cores cannot be allowed to continue indefinitely using stale copies.

Cache coherence protocols coordinate these copies.

The MESI family is a common conceptual model, with states such as:

- Modified
- Exclusive
- Shared
- Invalid

Real coherence systems can be significantly more complicated and may contain additional states and implementation-specific mechanisms.

## Memory consistency

Cache coherence and memory consistency are not the same concept.

Coherence asks questions about the value associated with a memory location across caches.

Memory consistency asks about the ordering in which memory operations become visible to different threads.

Concurrency systems therefore use mechanisms such as:

- atomic operations
- locks
- acquire/release ordering
- memory fences
- synchronization primitives

A program can have coherent caches while still requiring synchronization to establish the ordering guarantees expected by its threads.

## False sharing

A cache line may contain multiple independent variables.

Consider two threads:

- Thread A updates `counter_a`
- Thread B updates `counter_b`

If both variables share one cache line, updates to either variable can cause cache-line ownership traffic between cores.

The variables are logically independent, but the hardware operates on the cache line containing both.

This is called false sharing.

Possible techniques for reducing false sharing include:

- separating frequently modified data
- cache-line alignment
- padding
- changing data structures
- partitioning work by ownership

False sharing is especially important in high-throughput concurrent software.

## Stack and heap

Stack and heap are logical regions of a process's virtual address space.

They are not equivalent to cache levels.

A process may contain:

- executable code
- read-only data
- writable data
- heap
- stack
- shared libraries
- memory-mapped regions

Any of these regions may eventually be represented in physical memory and may be cached by the processor.

Therefore:

`stack ≠ cache`

and:

`heap ≠ RAM`

The stack and heap describe process memory organization, while the cache hierarchy describes the hardware path used to access data.

## Memory mapping

Memory-mapped files allow file-backed data to be represented through virtual memory mappings.

A process can access mapped regions through memory-like addresses while the operating system manages the relationship between virtual pages, physical frames, and file-backed storage.

This approach can be useful for:

- large files
- databases
- indexes
- shared memory
- persistent data structures

A mapped file is not necessarily loaded completely into RAM. Pages can be brought into physical memory as required.

## Secondary storage

Secondary storage includes persistent technologies such as:

- SSDs
- HDDs
- other persistent storage systems

Storage provides far more capacity than RAM but has much higher access latency.

An SSD generally has much lower latency than a mechanical HDD, but neither should be treated as equivalent to CPU cache or RAM.

Storage performance also depends on:

- sequential versus random access
- queue depth
- controller behavior
- filesystem
- device firmware
- interface
- workload size

## Latency versus bandwidth

Latency and bandwidth describe different properties.

Latency asks:

`How long does it take to obtain a result?`

Bandwidth asks:

`How much data can be transferred per unit of time?`

A system can have high bandwidth while still having substantial access latency.

Sequential workloads can often take advantage of high bandwidth because many adjacent bytes are transferred together.

Random workloads are often more sensitive to latency.

This distinction is important when evaluating memory and storage systems.

## Working set

The working set is the collection of data actively used during a period of execution.

If a program's working set fits into a cache level, that cache may be able to retain a substantial portion of the active data.

If the working set grows beyond the cache's capacity, capacity misses can increase.

If the working set exceeds physical RAM, the operating system may need to manage additional page movement and the performance impact can become much larger.

## Data structures and locality

Data structures affect memory behavior.

### Contiguous structures

Examples include:

- C++ `std::vector`
- C arrays
- JavaScript typed arrays

These can provide strong spatial locality when traversed sequentially.

### Pointer-heavy structures

Examples include:

- linked lists
- tree nodes allocated independently
- graph objects

These can involve indirect memory accesses.

The logical algorithm may be efficient while the physical access pattern remains difficult for caches and prefetchers.

This is why algorithmic complexity alone does not completely determine real performance.

## Python implementation

The Python implementation is a comprehensive conceptual laboratory.

It demonstrates:

- memory hierarchy fundamentals
- register concepts
- capacity and latency
- direct-mapped caches
- set-associative caches
- LRU replacement
- cache miss classification
- sequential and random access
- matrix traversal
- write-through behavior
- write-back behavior
- write allocation
- AMAT
- multi-level cache simulation
- prefetching
- virtual memory
- page tables
- TLBs
- page faults
- memory mapping
- working-set experiments
- alignment
- cache coherence concepts
- false sharing
- security considerations
- production considerations

### Direct-mapped cache

The Python `DirectMappedCache` class stores cache lines containing:

- valid state
- tag
- data
- dirty state

Its mapping uses the block number modulo the number of cache lines.

The implementation intentionally keeps the model small enough to inspect and understand.

### Set-associative cache

The `SetAssociativeCache` class divides blocks among sets and allows multiple ways within each set.

It tracks access time so that the least recently used entry can be evicted.

This demonstrates how associativity reduces some conflict behavior compared with a direct-mapped cache.

### Multi-level cache

`MultiLevelMemory` models:

`L1 → L2 → L3 → RAM`

The simulation records which level satisfies each access and calculates a simple cumulative latency.

The model does not claim to reproduce a specific processor.

### Virtual memory

The `PageTable` class maps virtual pages to physical frames.

The translation keeps the page offset unchanged.

The model raises a `MemoryError` when the requested page is absent.

This provides a simple representation of page faults.

### TLB

The `TLB` class caches page translations using an LRU policy.

Repeated page accesses can therefore obtain translations from the TLB rather than consulting the page table model every time.

### Security

The Python program explains the relationship between memory hierarchy and:

- process isolation
- page permissions
- executable memory
- ASLR
- cache side channels
- speculative execution
- secure memory handling

These topics demonstrate why memory hierarchy is relevant to both performance and security.

## JavaScript implementation

The JavaScript implementation complements the Python simulations by focusing on application-level runtime behavior.

It demonstrates:

- sequential and random access
- typed arrays
- JavaScript `Map`
- LRU caching
- direct-mapped caches
- set-associative caches
- virtual-memory translation
- TLB simulation
- write-back caching
- asynchronous storage
- application data processing
- runtime memory statistics
- error handling
- security considerations

### Typed arrays

The implementation uses `Float64Array`, `Int32Array`, and `Uint8Array`.

Typed arrays provide compact binary-oriented storage and are useful when applications process large numeric datasets.

The `Uint8Array` example also demonstrates how multiple-byte integer values occupy underlying bytes.

The exact physical layout and cache behavior remain implementation-dependent because JavaScript engines control object representation and execution.

### JavaScript Map as an application cache

The `LRUCache` class uses the ordering behavior of `Map`.

When an entry is accessed, it is removed and reinserted so that the newest entry appears at the end.

The oldest entry is then removed when the capacity is exceeded.

This is an application-level cache. It is not the CPU cache.

The distinction is important:

`JavaScript LRU cache ≠ CPU cache`

An application cache stores logical objects or values, while a CPU cache stores hardware-level copies of memory blocks.

### Asynchronous storage

The JavaScript implementation uses a simulated asynchronous storage operation.

The delay represents the conceptual fact that persistent storage has much higher latency than CPU-local memory.

The important programming distinction is:

`asynchronous waiting ≠ faster storage`

Asynchronous APIs allow an application to perform other work while waiting for I/O.

## C++ case study

The C++ implementation models a transaction analytics engine.

The system generates one million transaction records and performs aggregate analysis.

Each transaction contains:

- transaction ID
- account ID
- amount

The case study uses `std::vector<Transaction>` for the primary transaction dataset.

### Why vector?

`std::vector` stores elements contiguously.

For a sequential analytics operation, this provides several useful properties:

- adjacent records are stored close together
- hardware prefetching can often detect sequential access
- cache lines contain multiple neighboring records
- pointer indirection is avoided
- memory allocation behavior is predictable after `reserve`

The application can therefore process a large transaction set through a simple sequential scan.

### Transaction processing

The `TransactionAnalyticsEngine` provides:

- total transaction value
- totals grouped by account
- access to the transaction collection

The total-value operation scans the vector.

The grouping operation uses an `unordered_map`.

These two operations demonstrate different memory behaviors.

The vector scan is predictable and sequential.

The hash table introduces bucket lookup and less predictable memory access.

This illustrates an important performance principle:

A data structure affects both algorithmic complexity and memory-system behavior.

### Cache simulation

The C++ program includes:

- direct-mapped cache
- set-associative cache
- LRU replacement
- multi-level cache
- RAM access modeling

The cache models are deliberately simplified.

A real CPU may include:

- instruction and data caches
- nonblocking caches
- multiple outstanding misses
- hardware prefetchers
- coherence protocols
- write buffers
- victim caches
- inclusive or non-inclusive relationships
- multiple memory channels
- NUMA effects
- speculative execution

The simplified implementation isolates the fundamental mechanisms.

### Virtual memory and TLB

The C++ `PageTable` maps virtual pages to physical frames.

The `TLB` stores recent translations.

This produces the conceptual path:

`Virtual address → TLB → page table if necessary → physical address`

A real processor can perform these operations concurrently with other microarchitectural work, so the simple sequential model is educational rather than a cycle-accurate simulation.

## Important distinctions

### Cache versus RAM

| Property | Cache | RAM |
|---|---|---|
| Typical location | On or very close to CPU | Main memory subsystem |
| Capacity | Smaller | Larger |
| Latency | Lower | Higher |
| Primary purpose | Keep hot data close to CPU | Main working memory |
| Hardware management | Largely automatic | Managed by OS and memory controller |

### RAM versus storage

| Property | RAM | SSD/HDD |
|---|---|---|
| Volatile | Normally yes | No |
| Typical latency | Much lower | Much higher |
| Capacity | Lower | Much higher |
| CPU direct working memory | Yes | No, normally accessed through I/O and virtual-memory mechanisms |
| Persistence | No | Yes |

### Cache miss versus page fault

A cache miss occurs when a requested cache line is not present at a cache level.

A page fault occurs when a virtual page cannot currently be satisfied from the required resident memory state.

A cache miss is generally a hardware-level event.

A page fault requires operating-system involvement.

### Cache coherence versus memory consistency

Cache coherence concerns agreement about the values of memory locations across caches.

Memory consistency concerns the ordering and visibility of memory operations.

They are related but distinct concepts.

### Application cache versus CPU cache

An application cache is explicitly represented in software.

A CPU cache is part of the processor's hardware memory system.

The application cache may store objects, database records, HTTP responses, or computed results.

The CPU cache stores memory blocks and is normally managed automatically by hardware.

## Edge cases

The implementations explicitly validate several failure conditions.

Examples include:

- zero-sized cache
- invalid page size
- negative addresses
- invalid cache capacity
- invalid miss rate
- zero stride
- unmapped virtual pages
- out-of-range mapped-memory operations

These checks are important because memory-related code is particularly sensitive to incorrect assumptions.

## Common mistakes

### Assuming RAM is the fastest memory

Registers and CPU caches are faster and much smaller.

### Treating cache latency as constant

Actual latency depends on processor architecture, cache level, access type, contention, frequency, and other conditions.

### Confusing latency with bandwidth

High bandwidth does not eliminate access latency.

### Assuming bigger cache always means better performance

A larger cache can reduce some misses but consumes area, power, and design resources. Larger structures can also have different access-time characteristics.

### Ignoring locality

Two algorithms with similar computational complexity can have very different performance because their memory access patterns differ.

### Ignoring data layout

The physical organization of data can influence cache behavior, prefetching, TLB behavior, and memory bandwidth.

### Confusing virtual and physical addresses

Applications generally operate with virtual addresses. Hardware and operating-system mechanisms translate these to physical memory locations.

### Confusing page faults with cache misses

They operate at different layers and have very different performance implications.

### Assuming a software cache is a hardware cache

An application-level cache and CPU cache solve related but different problems.

### Ignoring false sharing

Multithreaded applications can experience severe performance effects when independent variables share a frequently modified cache line.

## Performance considerations

Memory performance depends on several interacting factors.

### Cache hit rate

A higher hit rate generally reduces the number of accesses that must proceed to lower levels.

### Miss penalty

A miss becomes expensive when the next level is substantially slower.

### Working-set size

A working set that fits within a cache level can behave differently from one that exceeds that level's capacity.

### Access pattern

Sequential access generally has strong spatial locality.

Random access can be more latency-sensitive.

### Data structure

Contiguous structures can provide predictable memory access.

Pointer-heavy structures can increase indirection.

### Alignment

Alignment can affect access efficiency and is especially important when working with cache-line boundaries and concurrent data.

### TLB behavior

Large working sets may require many page translations.

If the active translations exceed TLB capacity, additional translation work can occur.

### Prefetching

Predictable access patterns can benefit from prefetching.

Incorrect prefetching can consume cache capacity and memory bandwidth.

## Benchmarking limitations

The timing experiments in these files are educational experiments rather than hardware certification tests.

Measurements can be affected by:

- compiler optimization
- interpreter and JIT behavior
- garbage collection
- operating-system scheduling
- CPU frequency scaling
- cache warm-up
- TLB state
- branch prediction
- hardware prefetching
- memory contention
- NUMA placement
- measurement overhead
- background processes

A reliable performance study should use repeated measurements and representative workloads.

Hardware performance counters can provide more direct information about cache misses, branch behavior, memory traffic, and other microarchitectural events when available.

## Security considerations

Memory hierarchy has security implications beyond performance.

### Process isolation

Virtual memory allows operating systems to isolate processes from one another.

### Page permissions

Memory pages can have restrictions such as read-only or non-executable permissions.

### ASLR

Address Space Layout Randomization changes important virtual address locations, making some memory-exploitation techniques more difficult.

### Cache side channels

Cache timing can sometimes reveal information about another computation.

An attacker may infer whether certain data was accessed by observing timing differences.

### Speculative execution

Modern processors can execute instructions speculatively. Although architectural permission checks remain part of the processor's correctness model, speculative execution can interact with microarchitectural state in ways relevant to side-channel security.

### Sensitive data

Sensitive values can exist in multiple locations during program execution:

- registers
- caches
- RAM
- memory-mapped regions
- swap
- storage

Removing one copy does not necessarily remove every representation.

## Implementation considerations

### Python

Python is useful for memory-hierarchy education because classes and standard data structures allow cache algorithms, page tables, and replacement policies to be expressed clearly.

The trade-off is that Python introduces interpreter/runtime behavior that makes it unsuitable for direct physical cache-latency measurement.

### JavaScript

JavaScript is useful for demonstrating how application-level data structures interact with runtime-managed memory.

Typed arrays are particularly useful for numeric data.

The JavaScript runtime also makes asynchronous storage behavior easy to demonstrate.

The CPU cache remains below the JavaScript abstraction layer.

### C++

C++ is particularly suitable for performance-oriented memory studies because developers can explicitly choose data structures, control object lifetime, use contiguous storage, and measure native execution.

C++ still does not provide complete portable control over CPU cache hardware. Actual cache behavior remains architecture-dependent.

## Practical applications

Memory hierarchy principles are relevant to:

- operating systems
- databases
- compilers
- high-performance computing
- gaming engines
- scientific computing
- financial analytics
- machine learning systems
- web servers
- storage systems
- networking software
- embedded systems
- distributed systems
- cybersecurity
- virtualization
- database indexing
- real-time systems

Examples of practical optimization include:

- choosing contiguous data layouts
- batching operations
- reducing pointer chasing
- keeping hot data compact
- improving temporal reuse
- exploiting sequential access
- reducing unnecessary memory allocation
- avoiding false sharing
- understanding working-set size
- considering TLB behavior
- measuring cache misses when appropriate

## Relationship between software and hardware

A programmer generally does not explicitly control every cache operation.

Instead, software influences cache behavior indirectly through:

- data structures
- memory layout
- access patterns
- loop ordering
- allocation strategy
- working-set size
- concurrency design

The processor then uses hardware mechanisms such as:

- caches
- cache-line transfers
- replacement logic
- prefetching
- branch prediction
- TLBs
- coherence protocols
- memory controllers

The operating system contributes mechanisms such as:

- virtual memory
- page tables
- page permissions
- demand paging
- memory mapping
- process isolation

Memory hierarchy is therefore a cross-layer subject connecting application software, operating systems, processor architecture, and persistent storage.

## Implementation correspondence

| Concept | Python | JavaScript | C++ |
|---|---|---|---|
| Registers | Conceptual model | Runtime explanation | Architectural explanation |
| Direct-mapped cache | Yes | Yes | Yes |
| Set associativity | Yes | Yes | Yes |
| LRU | Yes | Yes | Yes |
| Multi-level cache | Yes | Conceptual/application examples | Yes |
| Write-back | Yes | Yes | Yes |
| AMAT | Yes | Yes | Yes |
| Virtual memory | Yes | Yes | Yes |
| TLB | Yes | Yes | Yes |
| Page faults | Yes | Conceptual translation model | Translation model |
| Locality | Yes | Yes | Yes |
| Typed/contiguous data | Python data structures | Typed arrays | `std::vector` |
| Application workload | Database-style examples | Transaction processing | Transaction analytics engine |
| Performance measurement | Yes | Yes | Yes |
| Security considerations | Yes | Yes | Yes |

## Real-world relevance

A modern application's performance is rarely determined solely by the number of arithmetic operations it performs.

A program can execute relatively few instructions while spending substantial time waiting for data.

This is why memory hierarchy is central to performance engineering.

A database query, image-processing operation, scientific simulation, financial calculation, or machine-learning workload may repeatedly access large datasets. The organization and reuse of that data can determine whether the processor obtains most values from nearby cache levels or repeatedly waits for lower levels.

The core relationship can be represented as:

`Good locality → more useful cache hits → fewer expensive lower-level accesses → better effective memory performance`

The relationship is not absolute because real systems contain many interacting mechanisms, but locality remains one of the fundamental principles of computer architecture.

## Key formulas and relationships

### Direct mapping

`cache_line = block_number mod number_of_lines`

### Page translation

`virtual_page = virtual_address div page_size`

`offset = virtual_address mod page_size`

`physical_address = physical_frame × page_size + offset`

### Single-level AMAT

`AMAT = hit_time + miss_rate × miss_penalty`

### Temporal locality

`recently used data → likely future reuse`

### Spatial locality

`nearby data → likely future access`

These relationships form the conceptual foundation for understanding registers, caches, RAM, virtual memory, and persistent storage as one integrated memory system.
