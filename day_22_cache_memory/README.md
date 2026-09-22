# Cache Memory and Cache Simulators

## Topic scope

Cache memory is a small, fast memory system positioned between the CPU and main memory. Its purpose is to reduce the effective time required to access frequently or recently used data.

This implementation set studies cache memory from fundamental concepts through configurable cache simulation. The Python implementation provides the most extensive educational simulator, the JavaScript implementation presents the same core ideas in a runtime-oriented form, and the C++ implementation develops the concepts into an industry-style systems case study.

The central topics are:

- Cache hierarchy
- Cache lines and blocks
- Cache hits and misses
- Temporal locality
- Spatial locality
- Direct-mapped caches
- Fully associative caches
- Set-associative caches
- Tag, index, and offset
- Replacement policies
- LRU and FIFO
- Write-through and write-back
- Write-allocate and no-write-allocate
- Multi-level caches
- Cache statistics
- Miss classification
- Average Memory Access Time
- Memory-access traces
- Matrix traversal and locality
- Cache-aware performance analysis

---

## Fundamental concept

A processor can execute instructions much faster than data can be supplied from main memory. If every load or store required a main-memory access, processor performance would frequently be limited by memory latency.

Cache memory addresses this problem by keeping selected blocks of memory in a smaller and faster storage layer.

A simplified hierarchy is:

`CPU registers → L1 cache → L2 cache → L3 cache → RAM → storage`

The exact organization depends on the processor. Modern processors can contain multiple cache structures, separate instruction and data caches, shared caches, and additional mechanisms such as translation lookaside buffers and coherence protocols.

The essential principle remains the same: frequently useful information is kept closer to the processor.

---

## Cache levels

### L1 cache

L1 is normally the smallest and fastest conventional CPU cache.

A processor may have separate:

- L1 instruction cache
- L1 data cache

Keeping instruction and data accesses separate can allow simultaneous instruction fetching and data operations.

The small capacity is intentional. A smaller cache can generally be accessed with lower latency and can be implemented close to the execution core.

### L2 cache

L2 is usually larger than L1 and has higher access latency.

Many processors provide an L2 cache associated with an individual core, although the exact organization depends on the architecture.

L2 can contain data that was not found in L1.

### L3 cache

L3 is generally larger than L2 and slower than L2.

On many multicore processors, L3 is shared among multiple cores. Shared caches can help cores access common data, although cache coherence and contention become important architectural considerations.

### Main memory

RAM has much greater capacity than CPU caches but substantially higher access latency.

A cache miss that propagates through several cache levels can therefore have a significant performance cost.

---

## Cache blocks and cache lines

Memory is normally transferred between memory hierarchy levels in blocks.

A cache line is the storage location in the cache that contains one memory block.

For example, if the block size is 64 bytes, an access to address 100 may cause a block containing a range of addresses around 100 to be fetched into the cache.

This behavior is important because programs frequently demonstrate spatial locality.

A cache line commonly contains:

- Valid bit
- Tag
- Data block
- Dirty bit in designs supporting write-back
- Replacement metadata

The simulators in this repository model tags, validity, dirty state, and replacement metadata. They focus on cache behavior rather than storing the actual bytes of every simulated memory block.

---

## Cache hits

A cache hit occurs when the requested block is already present in the appropriate cache location.

For a hit:

1. The processor issues a memory address.
2. The cache determines the relevant set or location.
3. The cache compares the address tag with stored tag information.
4. A valid matching line is found.
5. The requested data can be supplied from the cache.

A high hit rate is generally desirable because cache access is much cheaper than accessing lower levels of the memory hierarchy.

---

## Cache misses

A cache miss occurs when the requested block is not available in the cache location determined by the mapping scheme.

The basic sequence is:

1. CPU issues an address.
2. Cache lookup occurs.
3. No matching valid line is found.
4. The next memory hierarchy level is accessed.
5. The requested block is fetched.
6. The cache may evict an existing block.
7. The new block is inserted.
8. The CPU receives the requested data.

The miss penalty is the additional latency associated with obtaining data from a lower level.

---

## Locality

Cache effectiveness depends heavily on locality.

Two important forms are temporal locality and spatial locality.

### Temporal locality

Temporal locality means that recently accessed information is likely to be accessed again.

For example:

`A → B → A → A → B`

The repeated accesses to `A` and `B` demonstrate temporal locality.

Loops frequently exhibit temporal locality because instructions and variables are repeatedly used.

### Spatial locality

Spatial locality means that an address near a recently accessed address is likely to be accessed soon.

For example:

`100 → 104 → 108 → 112 → 116`

Sequential array traversal commonly exhibits strong spatial locality.

A cache line exploits spatial locality by fetching multiple neighboring bytes together.

### Why locality matters

A program can perform a large number of memory accesses while requiring relatively few lower-level memory operations if those accesses exhibit strong locality.

Poor locality can result in frequent cache misses even when the program performs relatively simple operations.

---

## Address decomposition

A cache address can be conceptually divided into:

`[ tag | index | block offset ]`

The exact number of bits depends on:

- Address width
- Cache capacity
- Block size
- Number of sets
- Associativity

For a cache with:

- 64-byte capacity
- 8-byte blocks
- direct mapping

there are:

`64 / 8 = 8`

cache lines.

With direct mapping, there are eight sets.

The block number is:

`block number = address / block size`

The byte offset is:

`offset = address % block size`

The set index is:

`set index = block number % number of sets`

The tag is:

`tag = block number / number of sets`

The Python, JavaScript, and C++ implementations calculate these values directly.

---

## Direct-mapped cache

A direct-mapped cache allows each memory block to map to exactly one cache line.

The mapping can be represented as:

`cache line = block number % number of lines`

Advantages:

- Simple hardware
- Low lookup complexity
- Low metadata overhead
- Fast indexing

Disadvantages:

- Two frequently used blocks can map to the same cache line.
- Such blocks can repeatedly evict one another.

This is known as conflict behavior.

The Python and C++ implementations represent direct mapping using an associativity of one.

---

## Fully associative cache

In a fully associative cache, a memory block can be placed in any cache line.

There is no fixed single set for the block.

The cache must compare the requested tag against a larger collection of possible tags.

Advantages:

- Great flexibility in placement
- Fewer conflict misses

Disadvantages:

- More expensive lookup hardware
- More tag comparisons
- Replacement policy becomes important

The Python, JavaScript, and C++ demonstrations model a fully associative cache by setting associativity equal to the total number of cache lines.

---

## Set-associative cache

Set associativity provides a compromise between direct mapping and full associativity.

For a two-way set-associative cache, each set contains two possible lines.

A block maps to one set but can occupy either way in that set.

For a four-way cache, each set contains four possible lines.

The general relationship is:

`number of sets = number of cache lines / associativity`

Set associativity reduces conflict problems while avoiding the full comparison cost of a fully associative cache.

Common cache organizations include:

- 2-way
- 4-way
- 8-way
- Higher associativity in selected structures

---

## Replacement policies

When a set is full and another block must be inserted, one existing line must be selected for replacement.

### LRU

LRU means Least Recently Used.

The line that has gone unused for the longest time is selected for replacement.

The reasoning is based on temporal locality: recently used data may be more likely to be reused than data that has not been accessed for a long time.

The simulators maintain a logical access timestamp to model LRU behavior.

### FIFO

FIFO means First In, First Out.

The line that entered the set earliest is selected for replacement.

FIFO is simpler conceptually than LRU, but it does not directly measure recent usage.

The Python, JavaScript, and C++ implementations provide both LRU and FIFO for comparison.

---

## Cache miss categories

Cache misses are commonly discussed using three broad categories.

### Compulsory misses

A compulsory miss occurs the first time a block is accessed.

The block cannot already be present because it has never been requested previously.

These are sometimes called cold-start misses.

### Capacity misses

A capacity miss occurs because the working set cannot fit within the cache capacity.

Even with flexible placement, the cache may be unable to retain all required blocks.

### Conflict misses

Conflict misses occur when multiple blocks compete for the same cache location or set despite sufficient total cache capacity.

Direct-mapped caches are particularly susceptible to conflict behavior.

The simulators maintain educational miss classifications. Exact classification of a real trace can require a reference model because capacity and conflict effects can overlap.

---

## Cache mapping comparison

The implementations compare the same memory trace under different associativity values.

The trace contains addresses that intentionally map to competing cache locations.

A direct-mapped configuration can experience repeated replacement when several blocks map to the same line.

Increasing associativity allows several competing blocks to coexist in the same set.

A fully associative configuration provides the greatest placement flexibility.

The trade-off is that increased associativity can require more comparison and replacement logic.

---

## Write policies

Cache systems must define what happens when the processor modifies data.

Two important policies are write-through and write-back.

### Write-through

With write-through, a write to a cache line is also propagated to the next memory hierarchy level.

Advantages:

- Lower levels remain more immediately synchronized.
- Eviction does not require writing a dirty cache line solely because of earlier writes.

Disadvantages:

- More lower-level write traffic
- Potentially greater memory bandwidth consumption

### Write-back

With write-back, the cache modifies its local copy and marks the line dirty.

The modified data is written to the lower level when the dirty line is eventually evicted.

Advantages:

- Multiple writes to the same line can be combined.
- Lower-level write traffic can be reduced.

Disadvantages:

- Dirty-bit tracking is required.
- Eviction of a dirty line requires a write-back.
- Consistency and coherence become more complicated in multicore systems.

The Python, JavaScript, and C++ implementations model dirty lines and write-backs.

---

## Write allocation policies

A write miss also requires a decision about whether the missing block should be brought into the cache.

### Write-allocate

A write miss first loads the block into the cache and then performs the write.

This can be useful when the program is expected to access the same block again.

### No-write-allocate

A write miss bypasses the cache and writes to a lower memory level.

This can be useful when the data is unlikely to be reused.

Write-back caches are commonly associated conceptually with write-allocate, while write-through caches can be paired with either policy depending on the architecture.

The simulator keeps these policies independently configurable.

---

## Average Memory Access Time

A common simplified model is:

`AMAT = hit time + miss rate × miss penalty`

For example:

`hit time = 1 cycle`

`miss rate = 5%`

`miss penalty = 50 cycles`

Then:

`AMAT = 1 + 0.05 × 50`

`AMAT = 3.5 cycles`

The formula is a simplified analytical model. Real processors can have overlapping operations, multiple outstanding memory requests, prefetching, nonblocking caches, multiple miss classes, and other mechanisms that make real performance more complicated.

---

## Multi-level cache behavior

A multi-level cache can be viewed as a sequence of increasingly larger and slower storage layers.

For an access:

1. L1 is checked.
2. If L1 hits, the access completes using L1.
3. If L1 misses, L2 is checked.
4. If L2 hits, the block can be supplied from L2.
5. If L2 misses, a lower level such as L3 or RAM must provide the data.

The Python, JavaScript, and C++ examples implement a simplified L1/L2 hierarchy.

The simulation intentionally focuses on hit and miss flow rather than attempting to reproduce a particular commercial CPU.

Real processors can use substantially more sophisticated mechanisms.

---

## Python implementation

The Python script is the most extensive educational implementation.

Its principal class is `CacheSimulator`.

The constructor accepts parameters including:

- `cache_size`
- `block_size`
- `associativity`
- `hit_latency`
- `miss_latency`
- `replacement_policy`
- `write_policy`
- `allocation_policy`

The simulator validates cache geometry before constructing its sets.

For example, the cache size and block size must be powers of two in the implementation.

The cache is represented as a list of sets:

`sets[set_index][way]`

Each cache line stores:

- Valid state
- Tag
- Dirty state
- Last-used timestamp
- Insertion timestamp

The simulator can execute both reads and writes.

---

## Python address handling

The `address_fields()` function calculates:

- Block number
- Offset
- Set index
- Tag

The relationship is:

`block_number = address // block_size`

`offset = address % block_size`

`set_index = block_number % number_of_sets`

`tag = block_number // number_of_sets`

The `explain_address()` function exposes this decomposition in a learner-readable form.

---

## Python cache lookup

The `_find_line()` method searches the selected set for a valid line with the requested tag.

A matching valid line produces a hit.

On a hit:

- Hit count increases.
- LRU timestamp is updated.
- A write may set the dirty bit.
- The configured hit latency is returned.

On a miss, the simulator selects a victim and inserts the requested block.

---

## Python replacement logic

The `_choose_victim()` method first searches for an invalid line.

If every way is occupied, it applies the configured replacement policy.

For LRU:

`minimum(last_used)`

For FIFO:

`minimum(inserted_at)`

This demonstrates why replacement metadata is required for policies that depend on access history.

---

## Python write behavior

For write-back:

- A write hit marks the line dirty.
- A dirty line may require a write-back when evicted.

For write-through:

- The simulator does not retain a dirty state for ordinary writes because the lower level is considered updated immediately.

For write-allocate:

- A write miss installs the missing block.

For no-write-allocate:

- A write miss bypasses cache allocation.

---

## Python locality demonstrations

The Python implementation includes several workload patterns.

### Sequential access

Sequential addresses demonstrate spatial locality.

For example:

`0, 4, 8, 12, 16, 20`

When the block size is larger than the access stride, several accesses can refer to the same cache line.

### Repeated access

Repeated access demonstrates temporal locality:

`0, 4, 8, 0, 4, 8`

Once the relevant blocks are resident, subsequent accesses can hit.

### Strided access

Large strides can reduce the benefits of spatial locality because each access may land in a different block.

---

## Matrix traversal

Memory layout is especially important for arrays and matrices.

A row-major matrix stores adjacent columns next to each other in memory.

For a matrix:

`A[row][column]`

a row-wise traversal typically accesses nearby addresses:

`A[0][0], A[0][1], A[0][2], ...`

A column-wise traversal over a row-major layout can jump by an entire row between accesses.

The Python, JavaScript, and C++ implementations generate both patterns and pass them through a cache simulator.

This demonstrates that two algorithms performing the same logical work can produce different cache behavior because of memory-access order.

---

## JavaScript implementation

The JavaScript implementation provides an executable version of the cache simulator using standard JavaScript classes.

The main structures are:

- `CacheLine`
- `CacheStatistics`
- `CacheSimulator`

The simulator can run under a JavaScript runtime such as Node.js.

JavaScript's class syntax makes the simulator architecture explicit while retaining relatively compact implementation code.

The implementation includes:

- Address decomposition
- Cache lookup
- Replacement
- Statistics
- Writes
- Multi-level simulation
- AMAT
- Matrix traversal
- Validation

---

## JavaScript-specific implementation considerations

JavaScript numbers normally use IEEE 754 double-precision floating-point representation.

This is adequate for the relatively small educational addresses used by the simulator.

For a production simulator involving very large integer addresses, JavaScript `BigInt` may be appropriate.

That distinction matters because exact integer representation is limited for values beyond the safe integer range of ordinary JavaScript `Number`.

The JavaScript implementation intentionally uses ordinary integers because the educational traces remain within a safe and simple range.

---

## C++ case study

The C++ program develops the simulator as a systems-oriented case study.

The principal class is `CacheSimulator`.

The simulator uses:

- `vector`
- `unordered_set`
- `optional`
- `string`
- `algorithm`
- Structured bindings
- Enumerations
- Exception handling

The program is designed for C++17 or later.

---

## C++ system model

The simulated cache consists of a vector of sets.

Each set contains a vector of `CacheLine` objects.

A cache line stores:

- `valid`
- `dirty`
- `tag`
- `lastUsed`
- `insertedAt`

The architecture can therefore represent direct-mapped and set-associative caches.

A fully associative cache is represented by setting associativity equal to the total number of cache lines.

---

## C++ address calculation

The `decomposeAddress()` method returns an `AddressFields` structure containing:

- `blockNumber`
- `offset`
- `setIndex`
- `tag`

This makes address translation explicit rather than hiding it inside the cache lookup procedure.

The decomposition is based on the cache geometry.

This is important because the meaning of the index and tag fields is not universal. They depend on the cache's block size and number of sets.

---

## C++ victim selection

The `chooseVictim()` method performs two stages.

First, it searches for an invalid line.

If no invalid line exists, it chooses a line according to the replacement policy.

For LRU, the smallest `lastUsed` timestamp is selected.

For FIFO, the smallest `insertedAt` timestamp is selected.

This design separates cache lookup from victim selection and makes the simulator easier to extend.

---

## C++ validation

The simulator validates:

- Non-zero cache size
- Non-zero block size
- Non-zero associativity
- Power-of-two geometry
- Cache size greater than or equal to block size
- Associativity not exceeding the number of lines
- Number of lines divisible by associativity

Invalid configurations throw `std::invalid_argument`.

The `main()` function catches standard exceptions and reports the error.

This is preferable to allowing invalid cache geometry to produce misleading simulation results.

---

## Memory-reference traces

A cache simulator becomes particularly useful when it can consume a sequence of memory references.

For example:

`0, 8, 16, 24, 0, 8`

The simulator processes each reference in order.

For each access it can determine:

- Address
- Block
- Set
- Tag
- Hit or miss
- Latency
- Evicted tag
- Dirty eviction

A real simulator can extend this concept to traces containing:

- Program counter
- Read/write operation
- Virtual address
- Physical address
- Timestamp
- Thread identifier
- Core identifier

The educational implementations keep the trace format deliberately simple.

---

## Edge cases

Important edge cases include:

### Address zero

Address zero is valid and should not be confused with an invalid address.

### Address at the end of a block

If block size is 16, address 15 is still in the first block.

The next address, 16, begins the next block.

### Address crossing a block boundary

Sequential accesses can transition from one cache block to another.

This is a normal cache operation rather than an error.

### One cache line

A cache with one line behaves as a direct-mapped cache with one set.

### Full associativity

When associativity equals the number of cache lines, every block can theoretically be placed anywhere in the cache.

### Invalid configuration

A block size that does not produce a valid cache geometry should be rejected rather than silently rounded.

---

## Common mistakes

### Confusing cache lines with bytes

A cache line is a storage entry containing a block. Its size is measured in bytes, but the line itself is not equivalent to one byte.

### Forgetting the block offset

The cache must distinguish the requested byte within a cache block.

### Treating the index as a byte address

The index identifies a set, not an individual byte.

### Assuming every miss is a capacity miss

Miss causes can differ. A block can miss because it has never been referenced, because the cache cannot retain the working set, or because mapping constraints cause competition.

### Ignoring associativity

Cache capacity alone does not determine placement.

Two caches with identical total capacity can exhibit different behavior if their associativity differs.

### Ignoring write policy

Read behavior alone does not completely describe a cache.

Write-back and write-through systems produce different memory traffic.

### Assuming larger blocks are always better

Larger blocks can exploit spatial locality but can also:

- Consume cache capacity
- Increase transfer cost
- Fetch unused data
- Increase cache pollution

---

## Performance considerations

A cache simulator can calculate several useful measurements.

### Hit rate

`hit rate = hits / total accesses`

### Miss rate

`miss rate = misses / total accesses`

For a complete access stream:

`miss rate = 1 - hit rate`

### AMAT

`AMAT = hit time + miss rate × miss penalty`

A lower miss rate is not automatically sufficient to determine the best architecture.

A cache may achieve a lower miss rate while having a larger hit latency.

Likewise, increasing cache size can reduce misses while increasing physical area, power consumption, and access latency.

Cache design therefore involves trade-offs rather than a single universally optimal parameter.

---

## Complexity considerations

For a direct-mapped cache, lookup can conceptually identify one specific line after calculating the set index.

For a set-associative cache, the requested set must be searched across its ways.

If a set contains `W` ways, a simple software simulator can perform up to `O(W)` tag comparisons for a lookup.

For a fully associative cache containing `N` lines, a straightforward software lookup can require `O(N)` comparisons.

Real hardware does not necessarily implement these operations using ordinary sequential loops. Hardware can perform parallel tag comparisons and specialized replacement metadata management.

The software simulator is therefore an educational model, not a cycle-accurate hardware implementation.

---

## Replacement-policy trade-offs

LRU attempts to retain recently used blocks.

Its theoretical behavior is useful when temporal locality is strong.

The cost of implementing exact LRU increases with associativity because more ordering information must be maintained.

FIFO tracks insertion order rather than recent access order.

FIFO is conceptually simpler but can make replacement decisions that do not correspond closely to actual reuse patterns.

Real processors can use approximations or alternative policies instead of exact LRU.

---

## Cache pollution

Cache pollution occurs when data is brought into the cache but provides little useful future reuse.

For example, a large sequential scan can replace frequently reused data with blocks that are accessed only once.

This is one reason cache-aware algorithm design considers:

- Working-set size
- Access order
- Blocking
- Tiling
- Stride
- Reuse distance

---

## Working set

A working set is the set of data and instructions that a program actively uses during a period of execution.

If the active working set fits effectively into a cache, repeated accesses can achieve a high hit rate.

If the working set is much larger than the cache, blocks may continuously replace each other.

The exact behavior also depends on mapping and access order.

---

## Stride

Stride describes the distance between successive memory accesses.

A small stride can provide strong spatial locality.

A stride equal to the cache block size means successive accesses can land in successive blocks.

A large stride can cause every access to touch a different block.

For example, with a 64-byte cache line:

`0, 4, 8, 12`

uses multiple bytes within the same cache line.

A trace such as:

`0, 64, 128, 192`

moves to a new 64-byte region on every access.

The useful locality therefore depends on both the access pattern and the cache block size.

---

## Blocking and tiling

Matrix algorithms can often be reorganized into smaller blocks.

Instead of processing a huge matrix region that exceeds the cache's effective working capacity, an algorithm can process a smaller tile and reuse it before moving to another tile.

This is known as blocking or tiling.

The principle is:

1. Load a small region.
2. Perform substantial computation using it.
3. Reuse the region while it remains cache-resident.
4. Move to the next region.

The matrix traversal examples demonstrate why access order matters, while tiling is a natural extension of the same locality principle.

---

## Hardware realities not modeled completely

The simulators intentionally simplify several real processor mechanisms.

They do not attempt to reproduce every detail of a particular CPU.

Important real-world mechanisms include:

- Hardware prefetching
- Multiple outstanding cache misses
- Nonblocking caches
- Miss status holding registers
- Store buffers
- Load buffers
- Memory-level parallelism
- Cache coherence
- Inclusive and exclusive cache policies
- Victim caches
- Instruction caches
- Data caches
- TLB interactions
- Virtual-to-physical address translation
- Speculative execution
- Out-of-order execution
- Bank conflicts
- Hardware-specific replacement algorithms

These mechanisms can significantly affect observed performance.

---

## Cache coherence

In multicore processors, multiple cores may cache the same memory block.

If one core modifies the block, other cores cannot continue indefinitely using stale copies.

Cache coherence protocols coordinate ownership and visibility.

Common protocol families include:

- MESI
- MOESI
- MSI

The basic simulator does not implement coherence because its primary purpose is to teach cache mapping, locality, replacement, and hit/miss behavior.

A production-level multicore cache simulator would need a much more detailed coherence model.

---

## Security considerations

Caches can reveal information about memory-access behavior.

Because cache hits and misses have different timing characteristics, attackers can sometimes infer information about another computation.

This is the foundation of several classes of microarchitectural side-channel attacks.

Relevant concepts include:

- Cache timing
- Prime-and-Probe
- Flush-and-Reload
- Eviction sets
- Cache contention
- Speculative execution side channels

The existence of a cache therefore has security implications in addition to performance implications.

The simulator itself does not perform attacks. Its configurable mapping and access-trace behavior can be used to understand why cache occupancy and timing can expose information.

---

## Implementation considerations

A realistic cache simulator should clearly define:

- Address width
- Cache capacity
- Block size
- Associativity
- Replacement policy
- Write policy
- Allocation policy
- Number of cache levels
- Latency assumptions
- Trace format
- Miss classification methodology

Without these definitions, two simulators may produce different results while both appear internally consistent.

For reproducible experiments, cache parameters and trace data should therefore be recorded alongside simulation results.

---

## Python, JavaScript, and C++ comparison

### Python

Python is particularly useful for experimentation and educational simulation.

Advantages include:

- Concise data structures
- Readable classes
- Fast development
- Easy trace generation
- Convenient statistics processing

The Python implementation is therefore the most detailed exploratory simulator in this set.

### JavaScript

JavaScript demonstrates how cache concepts can be represented using classes and ordinary runtime data structures.

It is useful for:

- Application-level simulations
- Browser-oriented educational interfaces
- Interactive visualization
- Web-based trace analysis

The implementation remains independent of browser-specific APIs so that it can execute under Node.js.

### C++

C++ is appropriate for systems-oriented cache simulation because it provides:

- Explicit data structures
- Low-level memory control
- Predictable object representation
- High execution performance
- Strong standard-library support
- Close alignment with systems programming concepts

The C++ implementation therefore emphasizes architecture, validation, data structures, and performance-oriented modeling.

---

## Important distinctions

### Cache capacity versus cache block size

Capacity determines how much data the cache can hold.

Block size determines how much data is transferred per cache line.

They influence locality in different ways.

### Capacity versus associativity

Capacity determines total storage.

Associativity determines how many locations within a set can compete for a block.

Two caches can have the same capacity but different conflict behavior because of different associativity.

### Hit rate versus latency

A cache can have a high hit rate but still have a higher access latency than a smaller cache.

Performance analysis must consider both.

### Write-back versus write-through

Write-back delays lower-level updates until eviction of dirty data.

Write-through propagates writes immediately to the lower level.

### LRU versus FIFO

LRU tracks recent use.

FIFO tracks insertion order.

They can make different replacement decisions for the same trace.

---

## Practical applications

Cache concepts are important in:

- CPU architecture
- Operating systems
- Compiler optimization
- Database systems
- High-performance computing
- Numerical computing
- Game engines
- Machine learning workloads
- Embedded systems
- Web browser engines
- Network processing
- Storage systems
- Concurrent applications
- Systems security

Cache-aware reasoning is particularly valuable when an application processes large arrays, matrices, graphs, database indexes, or other memory-intensive data structures.

---

## Production considerations

A production cache simulator normally requires more than the educational model implemented here.

A larger simulator may include:

- Configurable address widths
- Multiple CPU cores
- Multiple cache levels
- Separate instruction and data caches
- Coherence protocols
- Detailed memory hierarchy
- DRAM timing
- Hardware prefetching
- Out-of-order execution
- Branch prediction
- TLB simulation
- Virtual memory
- Trace-file ingestion
- Parallel simulation
- Warm-up periods
- Detailed latency modeling
- Energy estimates
- Hardware validation

The educational implementation deliberately keeps these dimensions separate so that fundamental cache behavior remains understandable.

---

## Core formulas

Number of cache lines:

`cache lines = cache size / block size`

Number of sets:

`sets = cache lines / associativity`

Block number:

`block = address / block size`

Block offset:

`offset = address % block size`

Set index:

`set = block % number of sets`

Tag:

`tag = block / number of sets`

Hit rate:

`hit rate = hits / accesses`

Miss rate:

`miss rate = misses / accesses`

Simplified AMAT:

`AMAT = hit time + miss rate × miss penalty`

These formulas form the mathematical foundation of the simulator implementations.

---

## Running the implementations

The Python program can be executed with a Python 3 interpreter.

The JavaScript program can be executed using Node.js.

The C++ program requires a compiler supporting C++17 or later.

The programs do not require external libraries.

Each implementation performs demonstrations automatically and prints cache configurations, address mappings, access results, statistics, locality comparisons, replacement behavior, write behavior, and multi-level cache behavior.

The C++ implementation also reports validation failures through exception handling.

---

## Educational interpretation of the simulator output

A typical access report contains values such as:

`address`

The requested byte address.

`block`

The memory block containing that address.

`set`

The cache set selected by the mapping function.

`tag`

The tag used to distinguish blocks that map to the same set.

`HIT`

The requested block was already present.

`MISS`

The requested block was not present and required lower-level service.

`evictedTag`

The tag of the line replaced during a miss when all candidate ways were occupied.

`dirtyWriteback`

Indicates that a dirty line was evicted under the write-back policy.

These fields allow cache behavior to be inspected one memory reference at a time rather than treating the cache as a black box.

---

## Relationship between code and concepts

The Python implementation emphasizes detailed experimentation.

The JavaScript implementation emphasizes executable object-oriented modeling in a language commonly used for web and application development.

The C++ implementation emphasizes systems programming structure and a configurable cache architecture.

All three implementations use the same conceptual model:

`address → block → set → tag → lookup → hit/miss → replacement → statistics`

That common structure makes it possible to compare the language implementations without losing the architectural meaning of the cache operations.
