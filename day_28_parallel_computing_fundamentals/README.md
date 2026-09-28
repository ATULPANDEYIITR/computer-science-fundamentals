# Parallel Computing Fundamentals

## 1. Topic Introduction

Parallel computing is the practice of organizing computation so that multiple units of work can be executed during overlapping periods. The execution resources may be CPU cores, vector execution units, graphics processors, or distributed machines.

Four concepts are central to this topic:

- **Concurrency**: multiple activities can make progress during overlapping periods.
- **Parallelism**: multiple operations actually execute simultaneously.
- **Multicore processing**: a processor contains multiple CPU cores capable of executing instruction streams.
- **SIMD**: Single Instruction, Multiple Data, where one instruction operates on multiple data elements.
- **MIMD**: Multiple Instruction, Multiple Data, where different execution units can execute different instruction streams on different data.

Parallel programming is not simply a matter of creating more threads. A useful parallel design must consider workload decomposition, dependencies, synchronization, communication, memory behavior, load balancing, hardware topology, scheduling, correctness, and the overhead introduced by parallel execution.

---

## 2. Fundamental Terminology

### 2.1 Concurrency

Concurrency describes the organization of multiple tasks so that they can make progress during overlapping periods.

A concurrent program does not necessarily execute multiple tasks at exactly the same instant.

For example, an event loop can start one network request, perform other work, and later process the response. Multiple operations are in progress, but this does not imply that multiple CPU instructions are executing simultaneously on different cores.

### 2.2 Parallelism

Parallelism means that multiple operations execute simultaneously using multiple execution resources.

For example, four CPU cores may independently process four partitions of a dataset.

The distinction is important:

- concurrency concerns overlapping progress;
- parallelism concerns simultaneous execution.

A program can therefore be concurrent without being parallel.

### 2.3 Task Parallelism

Task parallelism assigns different operations to different workers.

For example:

- one worker calculates a total;
- another calculates an average;
- another counts high-value transactions.

This corresponds closely to the MIMD programming model.

### 2.4 Data Parallelism

Data parallelism applies the same operation to separate portions of a dataset.

For example, if one million transactions must be classified, the transactions can be divided into four partitions and each worker can execute the same classification algorithm on one partition.

Data parallelism is often easier to scale when data items are independent.

### 2.5 Process

A process is an operating-system execution context with its own virtual address space.

Separate processes provide stronger memory isolation but generally require explicit communication when exchanging data.

### 2.6 Thread

A thread is an execution path within a process.

Threads normally share the process's address space. Shared memory makes communication efficient but introduces synchronization concerns.

### 2.7 Worker

A worker is an execution resource assigned a unit of work. Depending on the system, a worker may be a thread, process, GPU execution unit, or another computational resource.

### 2.8 Synchronization

Synchronization coordinates concurrent execution.

Common mechanisms include:

- mutexes;
- locks;
- condition variables;
- barriers;
- semaphores;
- atomic operations.

Synchronization is necessary when multiple execution units interact in ways that could otherwise produce incorrect results.

---

## 3. Multicore Processors

A multicore processor contains multiple CPU cores.

A four-core processor can potentially execute four independent streams of instructions simultaneously, subject to the architecture, operating system, workload, and hardware resources.

A modern CPU can also contain:

- multiple cache levels;
- vector execution units;
- hardware threads;
- shared memory controllers;
- branch prediction mechanisms;
- out-of-order execution resources.

The presence of multiple cores does not automatically make an application faster.

A workload must contain enough independent computation to keep those cores occupied.

---

## 4. Parallel Decomposition

A parallel algorithm begins by identifying independent units of work.

Suppose a dataset contains 1,000,000 records.

A simple partitioning strategy could divide it into four ranges:

- worker 1: records 0 to 249,999;
- worker 2: records 250,000 to 499,999;
- worker 3: records 500,000 to 749,999;
- worker 4: records 750,000 to 999,999.

Each worker processes its partition independently.

The final results are then combined.

This design is attractive because workers can avoid writing to the same mutable state.

---

## 5. The Python Implementation

The Python program demonstrates parallel computing using the standard library.

### 5.1 Sequential Baseline

The function `sum_of_squares_sequential()` performs a simple calculation sequentially.

The sequential implementation is important because performance optimization requires a baseline.

The basic measurement is:

`speedup = sequential_time / parallel_time`

Without a baseline, it is impossible to determine whether parallelization actually improved execution time.

### 5.2 Thread-Based Concurrency

The Python implementation uses `ThreadPoolExecutor` for simulated I/O operations.

The example uses sleeping tasks to represent operations waiting for external resources.

This illustrates an important distinction:

Threads can provide useful concurrency even when the application does not perform CPU-bound parallel execution.

### 5.3 CPU-Bound Processing

The prime-counting example uses `ProcessPoolExecutor`.

Standard CPython has a Global Interpreter Lock, commonly called the GIL. CPU-bound Python bytecode executed by ordinary threads does not generally achieve the same multicore parallelism that independent processes can provide.

The process-based example therefore partitions a numerical range and sends different partitions to separate processes.

### 5.4 Data Parallelism

The Python program divides a sequence into chunks.

Each process receives a chunk and performs the same transformation.

The results are then flattened into a single output sequence.

The pattern is:

1. partition;
2. distribute;
3. compute;
4. collect;
5. combine.

This is a fundamental pattern in data-parallel computing.

### 5.5 SIMD Concept

The Python implementation contains a conceptual SIMD vector-add example.

It groups values into conceptual lanes.

The implementation demonstrates the programming model, but ordinary Python list operations do not guarantee that the processor executes one actual SIMD machine instruction for every group.

Real SIMD can be exposed through compiler vectorization, native code, CPU intrinsics, or optimized numerical libraries.

### 5.6 MIMD

The MIMD example runs different operations over the same dataset.

The workers perform:

- sum;
- maximum;
- sum of squares.

These are different computational tasks and therefore illustrate the MIMD idea.

### 5.7 Map-Reduce Pattern

The parallel summation example follows a map-reduce structure.

The map phase calculates partial sums.

The reduce phase combines those partial sums into one total.

This pattern is common in distributed and parallel data processing because many aggregation operations can be expressed as independent partial computations followed by a combination step.

---

## 6. The JavaScript Implementation

The JavaScript implementation demonstrates both event-loop concurrency and actual CPU parallelism through Node.js Worker Threads.

### 6.1 Event-Loop Concurrency

`Promise.all()` is used to start multiple simulated asynchronous tasks.

The timers overlap, demonstrating concurrency.

This does not mean that JavaScript arithmetic is automatically running simultaneously on multiple CPU cores.

The event loop provides a concurrency mechanism for asynchronous operations.

### 6.2 Worker Threads

Node.js Worker Threads provide separate JavaScript execution contexts.

The implementation uses workers for CPU-intensive prime calculations.

The main thread creates independent ranges and sends each range to a worker.

The worker performs the computation and sends the result back.

This is a practical example of multicore CPU parallelism in a JavaScript environment.

### 6.3 Data Parallel Vector Processing

The JavaScript implementation divides two vectors into matching chunks.

Each worker receives one pair of chunks and performs vector addition.

The worker results are combined with `flat()`.

This demonstrates data parallelism while also showing the cost of transferring data between execution contexts.

### 6.4 SIMD

The JavaScript SIMD demonstration models vector lanes conceptually.

Modern JavaScript engines can perform internal optimizations, but application code should not assume that a simple JavaScript loop corresponds directly to a specific SIMD machine instruction.

The conceptual distinction remains useful:

`scalar`: process one data element at a time.

`vector`: process multiple logically related elements using vector hardware.

### 6.5 MIMD

The JavaScript example performs different analytical operations through separate execution activities.

The purpose is to show that parallel workers do not necessarily have to perform identical algorithms.

---

## 7. The C++ Industry-Style Case Study

The C++ program models a transaction analytics engine.

Each transaction contains:

- an identifier;
- a monetary amount;
- a category.

The program generates a large dataset and applies computationally intensive analysis.

The architecture progresses from a sequential implementation to a multicore implementation.

---

## 8. C++ Case Study: Sequential Architecture

The function `analyzeSequential()` processes every transaction in one execution path.

For each transaction it calculates:

- total transaction value;
- maximum transaction amount;
- transaction count;
- high-value transaction count;
- an analytical CPU workload.

This implementation establishes the baseline.

---

## 9. C++ Case Study: Partitioning

The function `partitionRange()` divides the dataset into approximately equal index ranges.

For example, with four workers, the dataset can be partitioned into four ranges.

The partitioning algorithm calculates boundaries using integer arithmetic so that the ranges cover the complete dataset without overlap.

This is a form of static load distribution.

---

## 10. C++ Case Study: Parallel Workers

`analyzeParallel()` creates one `std::thread` for each partition.

Each worker calls `analyzeRange()`.

An important design choice is that every worker writes to its own `WorkerStatistics` object.

This avoids unnecessary shared-state synchronization.

The main thread waits for all workers using `join()` and then combines the partial results.

This design is preferable to having every worker repeatedly update one global object protected by a mutex.

---

## 11. Why Private Partial Results Matter

Consider two approaches.

### Shared result

Every worker modifies one global accumulator.

This requires synchronization.

The resulting lock may become a bottleneck.

### Private results

Each worker writes to its own result object.

The results are combined only after the workers finish.

This reduces contention and often scales better.

The second approach is an example of reducing shared mutable state.

---

## 12. Synchronization with a Mutex

The `ThreadSafeCounter` class demonstrates mutual exclusion.

The counter has a private mutex.

Every increment acquires the mutex before modifying the shared value.

The pattern prevents concurrent modifications from interfering with each other.

The trade-off is that synchronization has a cost.

If thousands of workers repeatedly contend for one lock, the lock can become a serialization point.

---

## 13. Condition Variables

The C++ program also demonstrates `condition_variable`.

A worker waits until the main thread signals that initialization is complete.

A condition variable is useful when a thread should sleep until a particular condition becomes true rather than continuously polling.

This can reduce unnecessary CPU consumption.

---

## 14. MIMD in the C++ Case Study

The MIMD demonstration launches different analytical tasks:

- total calculation;
- average calculation;
- high-value transaction counting.

These operations use different instruction paths.

The example therefore illustrates the MIMD concept at the application level.

The tasks are independent and can execute simultaneously when sufficient execution resources exist.

---

## 15. SIMD in the C++ Case Study

The vector-add example groups operations into four conceptual lanes.

For example:

`A0 + B0`

`A1 + B1`

`A2 + B2`

`A3 + B3`

can conceptually be represented by one four-lane vector operation on suitable hardware.

The C++ compiler may vectorize suitable loops when optimization is enabled.

The source code itself should not assume that manually grouping four scalar expressions guarantees SIMD instructions.

Actual SIMD depends on compiler behavior, target architecture, optimization settings, data types, aliasing information, and the generated machine code.

---

## 16. SIMD Versus MIMD

| Characteristic | SIMD | MIMD |
|---|---|---|
| Instruction streams | One logical instruction | Multiple instruction streams |
| Data | Multiple data elements | Potentially different data |
| Typical use | Numeric/vector operations | Independent tasks |
| Control flow | Usually similar across lanes | Can differ |
| Example | Vector addition | Analytics tasks |
| Main strength | Data-level parallelism | Task-level flexibility |

SIMD is particularly effective when many data elements require the same operation.

MIMD is more flexible when workers need to perform different operations.

Modern processors can combine both ideas. Multiple CPU cores can operate independently, while each core can contain SIMD/vector execution capabilities.

---

## 17. Amdahl's Law

Amdahl's Law models the theoretical speedup of a fixed-size workload.

The formula used by the implementations is:

`Speedup = 1 / (S + P/N)`

where:

- `S` is the serial fraction;
- `P` is the parallel fraction;
- `N` is the number of processors;
- `P = 1 - S`.

If 10% of a program is serial, increasing the number of processors indefinitely cannot produce infinite speedup.

With `S = 0.10`, the theoretical limit approaches 10x.

This demonstrates why eliminating unnecessary serial sections is important.

---

## 18. Gustafson's Law

Gustafson's Law considers a different situation: the workload grows as more processing resources become available.

The simplified expression used in the examples is:

`Speedup = N - S(N - 1)`

This model is useful for understanding scalable workloads where additional processors are used to solve larger problems rather than merely finishing the same fixed problem faster.

---

## 19. Speedup and Efficiency

### Speedup

`Speedup = T1 / Tp`

where:

- `T1` is sequential execution time;
- `Tp` is parallel execution time.

A speedup of 4x means the parallel implementation took approximately one quarter of the sequential execution time under the measured conditions.

### Efficiency

`Efficiency = Speedup / P`

where `P` is the number of processors or workers.

Efficiency can also be expressed as a percentage:

`Efficiency percentage = Speedup / P × 100`

If four workers achieve 3.2x speedup:

`Efficiency = 3.2 / 4 = 0.8`

or 80%.

Perfect efficiency is difficult because real systems contain overhead and resource contention.

---

## 20. Parallel Overhead

Parallel execution introduces costs.

Important sources include:

- worker creation;
- thread scheduling;
- process creation;
- data copying;
- serialization;
- inter-thread communication;
- synchronization;
- result aggregation;
- cache-coherence traffic;
- memory bandwidth contention.

For a very small workload, these costs can exceed the useful computational savings.

Therefore:

**Parallelism is not automatically an optimization.**

The workload must be large enough and sufficiently independent to justify the overhead.

---

## 21. Load Balancing

Load balancing distributes work so that execution resources remain productively occupied.

Suppose three workers receive work costing:

- worker A: 100 units;
- worker B: 100 units;
- worker C: 1,000 units.

The first two workers will finish early and remain idle while the third continues.

This is poor load balance.

Equal numbers of data elements do not necessarily mean equal execution times.

Some records may require substantially more computation than others.

Dynamic scheduling can help when task costs are unpredictable.

---

## 22. Granularity

Granularity describes how much work is assigned to a parallel task.

### Fine-grained parallelism

Tasks are small.

Advantages:

- potentially good load balancing;
- more opportunities for parallel execution.

Disadvantages:

- higher scheduling overhead;
- more synchronization;
- more communication.

### Coarse-grained parallelism

Tasks are larger.

Advantages:

- lower scheduling overhead;
- fewer synchronization events.

Disadvantages:

- possible load imbalance;
- fewer independent tasks.

A useful design seeks a granularity large enough to amortize management costs while maintaining sufficient parallel work.

---

## 23. Race Conditions

A race condition occurs when the correctness of a program depends on the uncontrolled ordering of concurrent operations.

For example, an operation such as:

`counter = counter + 1`

is conceptually a read-modify-write sequence.

If multiple execution units perform it concurrently without suitable synchronization, updates can interfere.

Possible solutions include:

- mutexes;
- atomic operations;
- reduction into private results;
- message passing;
- immutable data structures.

The best solution depends on the workload.

---

## 24. Deadlocks

A deadlock occurs when execution units wait indefinitely for resources held by one another.

A common pattern is:

- thread A holds lock 1 and waits for lock 2;
- thread B holds lock 2 and waits for lock 1.

Neither can proceed.

Common prevention strategies include:

- consistent lock ordering;
- minimizing lock scope;
- avoiding unnecessary nested locks;
- using higher-level synchronization abstractions;
- reducing shared mutable state.

---

## 25. Atomic Operations

Atomic operations provide indivisible access to particular shared values.

C++ provides atomic types such as `std::atomic`.

Atomics can be much lighter than mutexes for certain simple counters and state variables.

They are not automatically a universal replacement for locks.

Complex invariants involving multiple variables often require stronger synchronization.

---

## 26. Cache Locality

Modern CPUs do not access main memory with uniform cost.

Data is moved through cache levels.

Typical systems contain:

- L1 cache;
- L2 cache;
- shared or partially shared L3 cache;
- main memory.

Programs often benefit when related data is accessed close together in time and memory.

This is called locality.

### Spatial locality

Accessing one memory location makes nearby locations likely to be useful soon.

### Temporal locality

Recently accessed data may be accessed again soon.

Parallel algorithms should therefore consider not only CPU operations but also memory access patterns.

---

## 27. False Sharing

False sharing occurs when independent variables modified by different cores occupy the same cache line.

The variables are logically independent, but cache-coherence mechanisms may repeatedly invalidate and transfer the cache line.

The result can be significant performance degradation.

A common mitigation is to separate frequently modified per-thread data so that unrelated workers do not repeatedly modify the same cache line.

---

## 28. Memory Bandwidth

Some applications are limited by memory bandwidth rather than CPU computation.

If several workers continuously read large arrays, adding more workers can eventually stop improving performance because the memory subsystem becomes saturated.

This is one reason why a program with more cores does not necessarily achieve proportional speedup.

---

## 29. CPU-Bound Versus I/O-Bound Work

### CPU-bound

Performance is primarily limited by computation.

Examples:

- numerical simulation;
- cryptographic computation;
- image processing;
- compression;
- scientific calculations.

Multicore CPU parallelism can be useful.

### I/O-bound

Performance is primarily limited by waiting for external resources.

Examples:

- network requests;
- disk operations;
- database requests.

Concurrency mechanisms can be highly effective because one task can make progress while another waits.

The appropriate model depends on the bottleneck.

---

## 30. Common Mistakes

### Mistake 1: Assuming more threads always mean more performance

Too many threads can cause:

- scheduling overhead;
- context switching;
- cache contention;
- memory contention.

### Mistake 2: Ignoring the sequential fraction

Amdahl's Law shows that serial work limits speedup.

### Mistake 3: Excessive synchronization

A lock around a large portion of the program can effectively serialize execution.

### Mistake 4: Sharing unnecessary state

Private worker results often reduce synchronization requirements.

### Mistake 5: Ignoring workload size

Parallel overhead may dominate small workloads.

### Mistake 6: Assuming equal task counts mean equal work

Individual tasks can have very different execution costs.

### Mistake 7: Confusing concurrency with parallelism

Asynchronous execution and simultaneous multicore execution are not identical.

### Mistake 8: Assuming conceptual SIMD guarantees hardware SIMD

Actual vectorization depends on the language runtime, compiler, architecture, and generated machine code.

---

## 31. Edge Cases

Parallel systems must handle:

- empty datasets;
- one-element datasets;
- fewer tasks than workers;
- invalid worker counts;
- mismatched vector lengths;
- worker exceptions;
- worker termination;
- partial failures;
- uneven task costs;
- very small workloads;
- very large workloads;
- resource exhaustion;
- synchronization failures.

The supplied implementations explicitly validate several of these cases.

---

## 32. Error Handling

Parallel error handling is more complicated than ordinary sequential error handling.

A worker can fail while other workers continue.

A robust design must decide:

- whether one worker failure cancels the entire computation;
- whether partial results are usable;
- how failures are reported;
- whether work should be retried;
- how worker resources are cleaned up.

The Python implementation demonstrates exception retrieval from futures.

The JavaScript implementation reports worker errors through messages and worker error events.

The C++ implementation catches exceptions at the main program boundary and validates inputs before starting operations.

---

## 33. Security Considerations

Parallel execution does not remove ordinary security requirements.

Important concerns include:

- validating input before distributing work;
- avoiding unsafe shared mutable state;
- limiting resource consumption;
- preventing untrusted workloads from creating excessive workers;
- protecting shared resources;
- handling worker failures safely;
- avoiding data races that could corrupt security-sensitive state.

Parallel programs can also increase the complexity of security testing because failures may depend on execution order.

---

## 34. Performance Considerations

A serious performance investigation should measure:

- wall-clock execution time;
- CPU utilization;
- memory utilization;
- worker count;
- throughput;
- latency;
- speedup;
- efficiency;
- cache behavior;
- memory bandwidth;
- synchronization overhead.

Measurements should be repeated because operating-system scheduling and other system activity can influence results.

The C++ case study uses a fixed random seed so that the generated workload is reproducible.

---

## 35. Python, JavaScript, and C++ Comparison

| Aspect | Python | JavaScript | C++ |
|---|---|---|---|
| Beginner accessibility | High | High | Moderate |
| Thread model | Threads and processes | Event loop and Worker Threads | Native threads |
| CPU parallelism | Commonly process-based for CPU-bound Python code | Worker Threads | `std::thread` |
| Memory model | High-level | High-level | Low-level control |
| SIMD control | Usually indirect | Usually indirect | Compiler/intrinsics can provide more control |
| Synchronization | Locks and concurrent futures | Worker communication and shared-memory mechanisms | Mutexes, atomics, condition variables |
| Performance control | Moderate | Moderate | High |
| Hardware-oriented programming | Limited at language level | Limited at language level | Strong |

Each language highlights a different aspect of parallel computing.

Python emphasizes high-level task distribution.

JavaScript demonstrates the distinction between asynchronous concurrency and worker-based CPU parallelism.

C++ exposes threads, synchronization primitives, memory behavior, and hardware-oriented optimization more directly.

---

## 36. Practical Applications

Parallel computing is used in many technical domains.

### Scientific computing

Large numerical simulations can divide independent calculations across CPU cores or accelerator devices.

### Financial analytics

Independent calculations over large collections of transactions, prices, scenarios, or simulations can be parallelized.

### Machine learning

Training and inference workloads often exploit data parallelism, vector operations, multiple CPU cores, and specialized accelerators.

### Image processing

Individual pixels, image regions, or frames can often be processed independently.

### Video processing

Different frames or regions can be processed concurrently.

### Search and indexing

Large collections of records can be partitioned among workers.

### Engineering simulation

Independent simulation scenarios can execute concurrently.

### Data analytics

Aggregation and transformation workloads frequently use partitioning and map-reduce-style architectures.

---

## 37. Production Design Considerations

A production parallel system should define:

1. the workload;
2. the dependency structure;
3. the unit of parallel work;
4. the worker model;
5. the synchronization strategy;
6. the failure model;
7. the load-balancing mechanism;
8. the memory-access strategy;
9. the performance metrics;
10. the scalability limits.

A correct sequential algorithm should generally be established before introducing concurrency or parallelism.

Parallelization should then be guided by measurements and dependency analysis.

---

## 38. Important Conceptual Relationships

### Concurrency and parallelism

Concurrency is about managing multiple activities.

Parallelism is about simultaneous execution.

### Data parallelism and SIMD

Both involve applying similar operations across multiple data elements.

SIMD is a hardware-oriented execution model, while data parallelism is a broader algorithmic concept.

### MIMD and multicore CPUs

A multicore processor naturally supports multiple instruction streams, making it a common platform for MIMD-style computation.

### Threads and processes

Threads generally share memory within a process.

Processes generally provide stronger isolation.

The choice depends on the programming environment, workload, communication requirements, and failure model.

---

## 39. Core Lessons Demonstrated by the Implementations

The Python implementation demonstrates:

- sequential computation;
- thread-based concurrency;
- process-based CPU parallelism;
- data partitioning;
- data parallel transformations;
- conceptual SIMD;
- MIMD;
- map-reduce;
- Amdahl's Law;
- Gustafson's Law;
- load balancing;
- exception handling.

The JavaScript implementation demonstrates:

- event-loop concurrency;
- asynchronous operations;
- Worker Threads;
- CPU-bound parallelism;
- data partitioning;
- vector operations;
- conceptual SIMD;
- MIMD;
- worker failure handling;
- performance considerations.

The C++ implementation demonstrates:

- sequential baselines;
- native threads;
- multicore execution;
- data parallelism;
- task parallelism;
- mutex synchronization;
- condition variables;
- MIMD-style analytical tasks;
- SIMD-style vector processing;
- workload partitioning;
- load balancing;
- speedup;
- efficiency;
- Amdahl's Law;
- validation;
- performance measurement;
- memory and cache considerations.

---

## 40. Final Technical Perspective

Effective parallel computing requires more than dividing code into multiple threads.

The central engineering problem is to find independent work, distribute it efficiently, coordinate only where necessary, and minimize the costs introduced by parallel execution.

The most important relationships are:

`Concurrency → overlapping progress`

`Parallelism → simultaneous execution`

`Multicore → multiple CPU execution resources`

`SIMD → one instruction across multiple data lanes`

`MIMD → multiple instruction streams across multiple data`

A scalable parallel system therefore depends on algorithmic independence, appropriate granularity, balanced workloads, controlled synchronization, efficient memory access, and empirical performance measurement.
