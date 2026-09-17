# Instruction cycle: fetch, decode, execute, memory access, write back

## Introduction

The instruction cycle is the repeated sequence through which a processor processes machine instructions. At the conceptual level, an instruction passes through five major stages:

1. **Fetch**
2. **Decode**
3. **Execute**
4. **Memory access**
5. **Write back**

The stages describe the movement of an instruction from the program stored in instruction memory to the final architectural result, such as a changed register or a changed memory location.

A simplified sequence is:

`Program Counter → Fetch → Decode → Execute → Memory → Write Back → next instruction`

The Python and JavaScript implementations model this sequence directly. The C++ implementation applies the same ideas to an embedded telemetry processor that reads sensor values from memory, calculates an aggregate, evaluates a threshold, and stores a status value.

The exact organization of a real processor varies by architecture. Some processors combine, divide, rename, reorder, or extend these stages. Modern out-of-order superscalar processors can have many more internal stages. The five-stage model remains useful because it exposes the fundamental responsibilities of instruction processing.

## Fundamental terminology

### Instruction

An instruction is an encoded command that tells a processor what operation to perform.

Examples include:

`ADD R1, R2, R3`

`LOAD R4, [R5 + 8]`

`STORE R2, [R3 + 4]`

`BEQ 20`

A real instruction is normally represented as binary data. The educational implementations represent decoded instructions as structured objects.

### Opcode

The opcode identifies the operation.

Examples include:

- `ADD`
- `SUB`
- `LOAD`
- `STORE`
- `CMP`
- `BEQ`
- `HALT`

The opcode is one of the main pieces of information examined during instruction decoding.

### Register

A register is a small, fast storage location inside the processor.

The examples use eight general-purpose registers:

`R0` through `R7`.

Real architectures use different register counts and conventions. RISC-V, ARM, x86-64, and other architectures have different register organizations.

### Program counter

The program counter, commonly abbreviated as `PC`, identifies the address of the next instruction to fetch.

A simplified fetch operation is:

`instruction = instruction_memory[PC]`

The processor then advances the PC so that execution can continue with the following instruction unless a branch, jump, exception, interrupt, or other control-flow event changes it.

### ALU

The arithmetic logic unit performs operations such as:

- addition
- subtraction
- multiplication
- division
- bitwise AND
- bitwise OR
- bitwise XOR
- shifts
- comparisons

The exact operations provided by an ALU depend on the processor architecture.

### Data memory

Data memory stores values that instructions may read or modify.

A `LOAD` obtains data from memory.

A `STORE` places data into memory.

### Immediate

An immediate is a constant encoded directly in an instruction.

For example:

`ADDI R1, R2, 10`

means that the ALU adds the value in `R2` to the immediate value `10`.

Using an immediate avoids requiring a separate register for the constant.

### Effective address

A memory instruction commonly calculates an effective address using a base register and an offset.

For example:

`LOAD R1, [R2 + 8]`

conceptually calculates:

`effective_address = R2 + 8`

The resulting address is then used by the memory stage.

## The five stages

## Fetch

The fetch stage obtains the next instruction.

The program counter identifies the instruction location.

Conceptually:

`instruction = instruction_memory[PC]`

The PC is then advanced.

For a simple educational processor in which every instruction occupies one logical slot:

`PC = PC + 1`

Real processors usually use byte addresses. If an architecture has fixed-width four-byte instructions, a simplified PC update may look like:

`PC = PC + 4`

Variable-length instruction architectures require more complicated instruction-length handling.

### What fetch needs

Fetch normally requires:

- program counter
- instruction memory or instruction cache
- instruction address generation
- instruction retrieval logic

In modern processors, instruction fetching can be considerably more sophisticated because the processor may fetch several instructions per cycle and predict future control flow.

### Fetch example

For:

`MOVI R1, 10`

the fetch stage obtains the instruction associated with the current PC.

It does not yet need to perform the addition or modify the destination register.

## Decode

The decode stage determines what the fetched instruction means.

For:

`ADD R3, R1, R2`

decode identifies:

- opcode: `ADD`
- destination: `R3`
- source 1: `R1`
- source 2: `R2`

The control logic determines which hardware resources the instruction requires.

Possible control decisions include:

- ALU operation
- register reads
- register write
- memory read
- memory write
- branch operation
- immediate selection
- instruction completion behavior

The Python implementation represents these decisions with a dictionary. The C++ implementation uses a `ControlSignals` structure.

## Execute

The execute stage performs the operation selected during decoding.

For:

`ADD R3, R1, R2`

the ALU performs:

`R3 = R1 + R2`

The execute stage can also calculate addresses.

For:

`LOAD R3, [R1 + 8]`

the ALU can calculate:

`address = R1 + 8`

The actual memory read happens during the memory-access stage in the five-stage model.

### Branch execution

Conditional branches also require an execution decision.

For example:

`CMP R1, R2`

can establish condition information.

Then:

`BEQ target`

tests whether the values were equal.

A taken branch changes the program counter.

A branch not taken allows sequential control flow to continue.

## Memory access

The memory stage is used when an instruction needs data memory.

### Load

For:

`LOAD R3, [R1 + 8]`

the execute stage calculates the effective address.

The memory stage reads that address.

The resulting value is passed toward write back.

### Store

For:

`STORE R3, [R1 + 8]`

the execute stage calculates the effective address.

The memory stage writes the source value to that address.

A store normally does not need a register write-back operation.

### Instructions that do not use data memory

An arithmetic instruction such as:

`ADD R3, R1, R2`

does not require a data-memory operation.

Its memory stage can therefore perform no data-memory access and simply pass the result toward write back.

## Write back

Write back updates the architectural register state when an instruction produces a register result.

For:

`ADD R3, R1, R2`

the ALU produces the result and write back performs:

`R3 ← result`

For:

`LOAD R3, [R1]`

the memory stage obtains the value and write back performs:

`R3 ← loaded_value`

A `STORE` does not normally write a register, so its write-back stage does nothing.

## Python implementation

The Python implementation builds a complete educational processor around the five-stage model.

The central `SimpleCPU` class contains:

- eight registers
- a program counter
- flags
- data memory
- instruction memory
- execution statistics
- tracing information
- exception handling

The `Instruction` dataclass represents an instruction with fields such as:

- `opcode`
- `rd`
- `rs1`
- `rs2`
- `immediate`
- `target`

This representation corresponds closely to the logical fields found in real instruction encodings.

### Python fetch

The `fetch()` method uses `self.pc` to retrieve the current instruction and advances the program counter.

The method explicitly logs the instruction so that the instruction cycle can be observed.

### Python decode

The `decode()` method converts the opcode into control decisions.

For example, a `LOAD` activates:

- ALU/address calculation
- memory read
- write back

A `STORE` activates:

- address calculation
- memory write

but does not require register write back.

### Python execute

The `execute()` method implements the ALU behavior.

Examples include:

`ADD`

`SUB`

`MUL`

`DIV`

`AND`

`OR`

`XOR`

`SHL`

`SHR`

`ADDI`

`MOVI`

The same stage also calculates memory addresses and evaluates conditional branches.

### Python memory access

The `memory_access()` method distinguishes between loads and stores.

A load reads from the data-memory array.

A store writes into the data-memory array.

Memory bounds are explicitly validated. An invalid address raises `MemoryFault`.

### Python write back

The `write_back()` method writes results into the destination register for instructions that produce register values.

This makes the architectural state transition visible.

## A complete arithmetic cycle

Consider:

`MOVI R1, 10`

The processor conceptually performs:

**Fetch**

Obtain `MOVI R1, 10`.

**Decode**

Identify destination `R1` and immediate value `10`.

**Execute**

Select the immediate value as the result.

**Memory**

No data-memory operation is necessary.

**Write back**

Store `10` into `R1`.

The next instruction can then use the new value.

For:

`ADD R3, R1, R2`

the stages become:

**Fetch:** obtain the ADD instruction.

**Decode:** identify `R1`, `R2`, and `R3`.

**Execute:** calculate `R1 + R2`.

**Memory:** no data-memory operation.

**Write back:** store the result into `R3`.

## Load example

Consider:

`LOAD R3, [R1 + 4]`

The conceptual sequence is:

1. Fetch the LOAD instruction.
2. Decode the destination register, base register, and offset.
3. Execute effective-address calculation.
4. Read data memory at the calculated address.
5. Write the loaded value into `R3`.

The separation between address calculation and data-memory access is important in a classic five-stage pipeline.

## Store example

Consider:

`STORE R3, [R1 + 4]`

The sequence is:

1. Fetch the STORE instruction.
2. Decode source and base registers.
3. Execute effective-address calculation.
4. Write the source value to data memory.
5. No general-purpose register write is required.

This demonstrates why the five stages are conceptual responsibilities rather than five identical operations performed by every instruction.

## Branches and control flow

Branches introduce a control dependency.

For example:

`CMP R1, R2`

followed by:

`BEQ 20`

means that the next instruction address depends on the comparison result.

If the branch is taken:

`PC = 20`

If it is not taken, sequential execution continues.

Real processors face a performance problem because instruction fetch may already have fetched instructions after a branch before the branch outcome becomes known.

This leads to control hazards and branch prediction.

## Flags

The Python and C++ implementations model simplified flags:

- zero
- negative
- carry
- overflow

The exact meaning and update rules depend on the instruction-set architecture.

The zero flag can represent a result equal to zero.

The negative flag can represent a negative signed result.

Carry and overflow have architecture-specific behavior and are more subtle than simply checking whether a mathematical result looks unusual.

For educational clarity, the examples implement only a simplified version of these flags.

## Sequential execution versus pipelining

A sequential implementation completes the conceptual stages of one instruction before beginning the next.

For example:

`Instruction A: FETCH → DECODE → EXECUTE → MEMORY → WRITE`

then:

`Instruction B: FETCH → DECODE → EXECUTE → MEMORY → WRITE`

This model is easy to understand but does not exploit stage-level overlap.

A pipeline allows multiple instructions to occupy different stages at the same time.

For example:

| Cycle | Instruction A | Instruction B | Instruction C |
|---|---|---|---|
| 1 | Fetch | | |
| 2 | Decode | Fetch | |
| 3 | Execute | Decode | Fetch |
| 4 | Memory | Execute | Decode |
| 5 | Write back | Memory | Execute |
| 6 | | Write back | Memory |
| 7 | | | Write back |

The exact timing of real processors varies, but the fundamental concept is instruction overlap.

## Pipeline registers

A pipelined processor needs storage between stages.

Typical conceptual pipeline registers are:

- IF/ID
- ID/EX
- EX/MEM
- MEM/WB

They preserve the information produced by one stage until the next stage consumes it.

The Python `PipelineRegister` class models this concept.

A pipeline register may contain:

- instruction
- PC
- decoded information
- ALU result
- memory address
- write-back value
- validity information

A pipeline register is different from a general-purpose register such as `R1`. A general-purpose register is part of the programmer-visible architectural state, while a pipeline register is normally an internal implementation structure.

## Pipeline hazards

Pipelining creates situations where instructions cannot safely proceed without additional handling.

The three major categories are:

### Structural hazards

A structural hazard occurs when two operations require the same hardware resource at the same time.

A simple example would be a processor with a single memory interface that cannot simultaneously support the required instruction fetch and data-memory access.

Architectures can reduce such conflicts through resource duplication, scheduling, or separate instruction and data caches.

### Data hazards

A data hazard occurs when instructions depend on values produced by other instructions.

The important categories include:

- RAW: Read After Write
- WAR: Write After Read
- WAW: Write After Write

In a basic in-order five-stage pipeline, RAW dependencies are particularly important.

Example:

`ADD R3, R1, R2`

followed immediately by:

`ADD R4, R3, R5`

The second instruction needs the value produced by the first instruction.

If the register file still contains the old value, the second instruction could obtain an incorrect result.

### Control hazards

A control hazard occurs when the next instruction address depends on a branch or jump.

Example:

`BEQ target`

The processor may have already fetched sequential instructions before determining whether the branch is taken.

Incorrectly fetched instructions may need to be flushed.

## Forwarding

Forwarding, also called bypassing, allows a result to move directly from a later pipeline stage to an earlier stage that needs it without waiting for ordinary register write back.

Consider:

`ADD R3, R1, R2`

followed by:

`ADD R4, R3, R5`

The ALU result for `R3` can potentially be forwarded to the second ADD's ALU input.

The Python pipeline model contains a simple forwarding mechanism.

Forwarding reduces unnecessary stalls but requires additional hardware paths and control logic.

## Load-use hazard

A load creates a particularly important dependency.

Consider:

`LOAD R1, [R2]`

followed by:

`ADD R3, R1, R4`

The loaded value is not available until the memory stage.

A classic five-stage pipeline may therefore need a stall even when ALU-result forwarding is available.

The Python implementation explicitly detects this situation and inserts a bubble.

This illustrates an important distinction:

**Forwarding reduces many data hazards, but it does not automatically eliminate every hazard.**

## Pipeline stalls

A stall delays an instruction or stage until a required condition becomes safe.

A pipeline bubble is an empty stage slot created by such a delay.

For a load-use dependency, a simplified sequence can be:

`LOAD`

then:

`BUBBLE`

then:

`dependent instruction`

Stalls increase the number of cycles needed to execute the instruction stream.

## Pipeline flushing

When a branch is taken, instructions that were fetched along the wrong path may need to be discarded.

This is called a flush.

The Python pipeline implementation records branch flushes.

Modern processors use more sophisticated techniques, including branch prediction, speculative execution, reorder buffers, and recovery mechanisms.

## JavaScript implementation

The JavaScript implementation models the same fundamental processor concepts while exposing several mechanisms that are natural in JavaScript.

The `Instruction` class represents instructions.

The `CPU` class represents the processor.

JavaScript objects are used for:

- instruction fields
- control signals
- execution results
- flags

A `Map` is used for instruction statistics.

Arrays represent registers and memory.

## JavaScript fetch

The JavaScript `fetch()` method reads the instruction at the current PC and increments the PC.

It returns both the original PC and instruction.

Keeping the original PC is useful because branch targets and debugging information often depend on the instruction address at which an instruction was fetched.

## JavaScript decode

The JavaScript decoder creates a control object containing fields such as:

`alu`

`memoryRead`

`memoryWrite`

`writeBack`

`branch`

`halt`

This illustrates how a processor's control unit can conceptually convert an instruction into hardware control signals.

## JavaScript execute

The JavaScript execute stage uses a `switch` statement to implement the instruction set.

It demonstrates JavaScript bitwise operators such as:

`&`

`|`

`^`

It also demonstrates error handling for division by zero.

JavaScript's numeric model differs from a typical fixed-width integer CPU. JavaScript's ordinary `Number` type is a double-precision floating-point representation. Bitwise operations convert values to signed 32-bit integer representations. A real processor has architecture-defined integer widths and overflow behavior.

This difference is important when using JavaScript to simulate CPU arithmetic.

## JavaScript memory access

The memory stage accesses the JavaScript array representing data memory.

Bounds checks are explicitly performed rather than relying on normal array behavior.

This is important because a JavaScript array access outside the intended architectural memory range does not naturally produce the same behavior as a processor memory fault.

The simulator therefore implements its own architectural memory rules.

## JavaScript write back

The JavaScript implementation identifies instructions that produce register results and writes those values into the register array.

The write-back stage is therefore explicit rather than being hidden inside the ALU operation.

This separation makes the five-stage structure easier to inspect.

## JavaScript event-driven execution

The `TraceEmitter` class demonstrates an event-oriented way of observing a processor.

A component can register a listener for an event such as:

`fetch`

or:

`writeback`

This resembles patterns commonly used in application-level JavaScript systems.

A browser-based CPU visualizer could use a similar mechanism to update a user interface whenever the simulated CPU enters a new stage.

## JavaScript asynchronous execution

The `runCycleByCycle()` function demonstrates asynchronous observation using `async` and `await`.

The asynchronous delay is not part of CPU architecture. It is an observation mechanism.

The CPU remains logically deterministic while the JavaScript event loop gives external observers an opportunity to inspect each cycle.

This distinction is important:

**Asynchronous application execution is not the same concept as CPU pipeline parallelism.**

JavaScript asynchronous functions coordinate program tasks through the runtime's event loop. A processor pipeline is a hardware execution organization.

## C++ case study

The C++ program models an embedded telemetry processor.

The processor receives three sensor values in memory:

- sensor A
- sensor B
- sensor C

It calculates:

`aggregate = A + B + C`

It compares the aggregate with a threshold.

If the aggregate is below the threshold, the system can represent a low status.

If the aggregate reaches or exceeds the threshold, the system stores a high status.

The example stores the resulting status in memory.

This scenario connects the instruction cycle with an embedded-system workload.

## C++ system organization

The C++ implementation separates responsibilities into several components.

### Opcode

The `Opcode` enumeration defines the processor's instruction set.

### Instruction

The `Instruction` structure contains fields for:

- opcode
- destination register
- source registers
- immediate value
- branch target

### Flags

The `Flags` structure stores condition information.

### ControlSignals

The `ControlSignals` structure represents decode-stage decisions.

### ExecutionResult

The `ExecutionResult` structure carries information from execute toward memory and write back.

### CPU

The `CPU` class coordinates the complete instruction cycle.

This modular organization makes the stages explicit and allows each stage to be examined independently.

## C++ telemetry memory map

The case study uses the following logical memory locations:

| Address | Meaning |
|---:|---|
| 100 | Sensor A |
| 101 | Sensor B |
| 102 | Sensor C |
| 110 | Output status |

The processor first loads the sensor values into registers.

The values are then combined through ALU instructions.

This demonstrates a typical path:

`Memory → Register → ALU → Register → Memory`

That pattern appears frequently in real processor workloads.

## C++ instruction sequence

The telemetry program contains operations conceptually equivalent to:

`MOVI R1, 100`

`LOAD R2, [R1 + 0]`

`LOAD R3, [R1 + 1]`

`LOAD R4, [R1 + 2]`

`ADD R5, R2, R3`

`ADD R5, R5, R4`

`MOVI R6, 100`

`CMP R5, R6`

`BLT target`

`MOVI R7, 1`

`STORE R7, [R1 + 10]`

`HALT`

This sequence contains arithmetic, memory access, comparison, control flow, and program termination.

## Why the C++ case study is significant

C++ is useful for demonstrating processor-oriented systems because it provides:

- explicit data structures
- predictable integer types
- low-level memory-oriented programming
- deterministic control flow
- efficient compiled execution
- strong control over object representation

The program uses `std::int32_t` through the `Word` alias to make the intended integer width explicit.

This is closer to fixed-width machine arithmetic than JavaScript's default `Number` representation.

C++ still does not directly expose the host CPU's actual instruction pipeline through this program. It is a simulator. The compiler eventually translates the C++ program into machine instructions executed by the real processor.

## Instruction encoding

A real CPU normally does not store an instruction as a C++ or Python object.

A machine instruction is encoded into bits.

A conceptual instruction may contain:

`opcode | destination | source 1 | source 2 | immediate`

Different instruction classes need different fields.

An R-type arithmetic instruction might use:

`opcode + rd + rs1 + rs2`

An immediate instruction might use:

`opcode + rd + rs1 + immediate`

A load may use:

`opcode + rd + base + offset`

A branch may use:

`opcode + condition + target/offset`

The available bit widths are determined by the ISA.

## ISA versus microarchitecture

These concepts must be distinguished.

### Instruction-set architecture

The ISA defines the programmer-visible contract.

It can specify:

- instructions
- registers
- data types
- memory addressing
- privilege behavior
- exceptions
- instruction encodings
- visible architectural state

Examples include x86-64, ARM AArch64, and RISC-V.

### Microarchitecture

Microarchitecture describes how a processor implements the ISA.

It can include:

- pipeline depth
- cache hierarchy
- execution units
- branch predictors
- register renaming
- out-of-order scheduling
- speculative execution
- reorder buffers

Two processors can implement the same ISA while having very different microarchitectures.

The five-stage pipeline in this project is a teaching model of microarchitectural organization.

## Clock cycles and latency

A clock cycle is a unit of processor timing.

Pipeline stages are often designed so that each stage can complete its assigned work within a target clock period.

Latency describes how long an individual operation takes from start to completion.

Throughput describes how frequently completed operations can be produced.

These concepts are different.

A pipeline may have relatively high latency for an individual instruction while still achieving high throughput for a long stream of independent instructions.

## Pipeline fill and drain

A five-stage pipeline cannot produce a completed instruction on the first cycle if it starts empty.

It must fill:

- cycle 1: first instruction enters fetch
- cycle 2: first instruction enters decode
- cycle 3: first instruction enters execute
- cycle 4: first instruction enters memory
- cycle 5: first instruction enters write back

At the end of the program, the pipeline also needs time to drain.

A simplified idealized estimate for `N` instructions in a five-stage pipeline is:

`N + 4`

This assumes no stalls, no branch penalties, and a single instruction stream that keeps the pipeline occupied.

The exact performance of a real processor depends on many additional factors.

## CPI

CPI means cycles per instruction.

The basic relationship is:

`CPI = total cycles / completed instructions`

For an idealized pipeline processing a sufficiently long stream of independent instructions, average CPI can approach `1`.

A CPI greater than one can result from:

- cache misses
- branch mispredictions
- data hazards
- structural hazards
- pipeline bubbles
- long-latency operations
- interrupts
- resource contention

CPI is therefore a performance measurement rather than a universal property of an instruction.

## Throughput versus latency

Suppose a pipeline contains five stages.

An instruction might need several cycles to travel through the pipeline, but after the pipeline is full, multiple instructions can be in progress simultaneously.

The key improvement is throughput.

This is why pipeline design is valuable even though the pipeline itself does not necessarily reduce the intrinsic work required for one instruction.

## Common mistakes

### Thinking fetch means execution

Fetching an instruction only obtains it.

The CPU still needs to interpret and process it.

### Thinking every instruction performs a memory read

Only instructions that require data memory need a data-memory operation.

Arithmetic instructions can pass through the memory stage without accessing data memory.

### Confusing instruction memory with data memory

Instruction memory stores executable instructions.

Data memory stores application data.

Modern systems may use separate instruction and data caches even when both ultimately access the same main memory system.

### Assuming write back happens during execute

The execute stage produces an ALU result.

The architectural register update is represented separately as write back in the five-stage model.

### Assuming every CPU has exactly five stages

The five-stage pipeline is a classic educational model.

Real processors may have substantially different pipeline organizations.

### Assuming pipelining means multiple cores

Pipelining and multicore processing are different.

A single core can pipeline multiple instructions.

Multiple cores provide multiple instruction streams that can execute concurrently.

A processor can have both pipelining and multiple cores.

### Assuming forwarding eliminates all stalls

Forwarding reduces many data hazards.

A load-use dependency may still require a stall.

Branches can also require prediction and recovery.

### Assuming JavaScript numbers behave like CPU integers

JavaScript's ordinary `Number` is floating point.

Real CPUs commonly have fixed-width integer registers.

The JavaScript simulator therefore represents architectural rules explicitly rather than relying entirely on JavaScript's native numeric behavior.

## Edge cases

### Division by zero

The Python, JavaScript, and C++ examples explicitly detect division by zero.

A processor architecture may define a specific exception or trap behavior.

### Invalid register

The Python and C++ implementations validate register numbers.

An invalid register is rejected rather than silently producing undefined architectural state.

### Invalid memory address

The simulators explicitly validate memory addresses.

Real processors have much more complex memory protection mechanisms, including privilege checks, page translation, access permissions, and faults.

### Invalid branch target

A branch target outside the available instruction memory is rejected by the C++ implementation.

Real processors use architecture-specific rules for instruction addresses and exceptions.

### Empty program

A production-quality CPU implementation must define behavior for an empty instruction stream.

The educational simulator treats attempting to fetch beyond the available program as an execution fault.

### Infinite loop

A faulty branch can prevent `HALT` from ever being reached.

The Python and C++ implementations use execution limits or explicit validation to prevent an educational simulation from running indefinitely.

## Exceptions and faults

Processor execution can encounter conditions that prevent normal completion.

Examples include:

- divide by zero
- invalid instruction
- invalid memory access
- protection violation
- page fault
- alignment fault
- arithmetic exception

The exact mechanisms vary by architecture.

A real CPU may transfer control to an exception handler instead of simply raising a high-level programming-language exception.

The examples use Python exceptions, JavaScript errors, and C++ exceptions to make the corresponding failure conditions observable.

These programming-language exceptions are modeling tools. They are not literal representations of the CPU's internal exception hardware.

## Performance considerations

The basic sequential simulator is intentionally simple.

Its execution loop performs five conceptual operations for each instruction.

For `N` instructions, the sequential simulation performs approximately `O(N)` instruction-level work, assuming constant-time register and memory-array operations.

The pipeline model also processes the instruction stream in approximately `O(N)` simulation steps for the simple architecture, although each simulated cycle contains additional bookkeeping for hazards and pipeline registers.

Real processor performance depends on:

- clock frequency
- instruction throughput
- cache hit rates
- memory latency
- branch prediction
- dependency chains
- execution-unit availability
- instruction width
- compiler scheduling
- speculative execution
- out-of-order execution

## Cache behavior

The five-stage model abstracts away caches.

Real processors typically use one or more cache levels.

A cache can reduce the effective latency of frequently accessed instructions and data.

Instruction fetching therefore commonly involves:

`PC → instruction cache → instruction bytes`

Data loads can involve:

`effective address → data cache → loaded value`

A cache miss may require accessing a lower cache level or main memory.

This can introduce a much larger latency than the basic five-stage model suggests.

## Memory hierarchy

A simplified hierarchy is:

`Registers`

`L1 cache`

`L2 cache`

`L3 cache`

`Main memory`

`Storage`

The closer a level is to the CPU, the lower its typical access latency and smaller its capacity.

Instruction-cycle diagrams often simplify all memory into a single stage, but real hardware must manage this hierarchy.

## Security considerations

Instruction execution is closely connected to computer security.

Relevant mechanisms include:

- memory protection
- privilege levels
- virtual memory
- address-space isolation
- instruction permission controls
- exception handling
- speculative execution controls
- control-flow protection

A processor should not generally allow an ordinary application to modify arbitrary kernel memory.

Modern operating systems and processors therefore use privilege levels and memory-management mechanisms.

Speculative execution has also created security concerns because transiently executed instructions can influence microarchitectural state such as caches. Attacks in this area demonstrate that architectural instruction semantics do not completely describe observable processor behavior.

The educational simulators intentionally omit those advanced mechanisms.

## Debugging considerations

Tracing each stage is useful for finding processor-simulation errors.

A useful trace can show:

`FETCH`

`DECODE`

`EXECUTE`

`MEMORY`

`WRITE`

For every instruction, a debugger can inspect:

- PC
- opcode
- source registers
- destination register
- ALU result
- memory address
- loaded value
- stored value
- branch decision
- flags

The Python implementation provides detailed tracing.

The C++ implementation provides stage-oriented trace output.

The JavaScript implementation supports synchronous and asynchronous observation.

## Data hazards and register dependencies

Consider:

`ADD R1, R2, R3`

`SUB R4, R1, R5`

The second instruction depends on `R1`.

This is a read-after-write dependency.

A dependency graph can conceptually represent:

`ADD → SUB`

The pipeline must ensure that the second instruction receives the correct value.

Possible solutions include:

- forwarding
- stalling
- compiler instruction scheduling
- register renaming in more advanced processors

## Compiler interaction

Compilers generate instruction sequences for processors.

The compiler must respect the target ISA.

At a simplified level:

`source code → compiler → machine instructions → processor`

The processor does not understand Python, JavaScript, or C++ source code directly.

It executes machine instructions generated by compilers, interpreters, virtual machines, or other execution systems.

The C++ case study is itself a program running on a real processor. Its `CPU` class simulates a second, fictional processor inside that program.

This creates two execution levels:

`Real CPU → C++ simulator → simulated CPU instructions`

## Superscalar execution

A superscalar processor can issue multiple instructions per cycle when sufficient execution resources are available.

For example, a processor with multiple execution units may execute independent arithmetic instructions concurrently.

The classic five-stage single-issue model does not fully represent this behavior.

Superscalar execution adds additional complexity involving:

- issue width
- dependency tracking
- scheduling
- execution ports
- retirement
- resource contention

## Out-of-order execution

A basic five-stage educational pipeline generally processes instructions in program order.

Modern high-performance processors can execute independent instructions out of order while maintaining architectural correctness.

Important mechanisms can include:

- register renaming
- reservation stations
- instruction queues
- reorder buffers
- dependency tracking
- speculative execution

The goal is to keep execution resources busy while preserving the required architectural behavior.

## Register renaming

Register renaming separates architectural register names from physical storage locations.

Suppose two instructions appear to reuse the same architectural register but do not have a true dependency.

Register renaming can eliminate certain false dependencies.

It is particularly important for advanced out-of-order processors.

The simple simulators intentionally use direct architectural registers and therefore do not model physical register renaming.

## Branch prediction

A branch creates uncertainty about which instruction should be fetched next.

A processor can predict whether a branch will be taken and what target it will use.

If the prediction is correct, the pipeline remains productive.

If the prediction is wrong, incorrectly fetched or speculatively executed instructions may be discarded.

The cost of a branch misprediction depends strongly on pipeline depth and microarchitecture.

The educational implementations use direct branch resolution instead of a sophisticated predictor.

## Superscalar, pipelined, and multicore distinctions

These concepts should not be treated as synonyms.

**Pipelining** overlaps different stages of multiple instructions.

**Superscalar execution** allows multiple instructions to be issued or executed in parallel within a core.

**Multicore processing** provides multiple processor cores.

A modern CPU can combine all three.

## Python, JavaScript, and C++ comparison

| Aspect | Python | JavaScript | C++ |
|---|---|---|---|
| Main implementation | Detailed CPU simulator | CPU plus event/asynchronous examples | Embedded telemetry case study |
| Instruction representation | Dataclass | Class | Struct |
| Registers | List | Array | `std::array` |
| Memory | List | Array | `std::array` |
| Error handling | Exceptions | Error subclasses | Exception classes |
| Control signals | Dictionary | Object | Struct |
| Statistics | Dictionary | Map | Map |
| Pipeline | Explicit five-stage model | Conceptual execution model | Pipeline analysis and hazard analysis |
| Numeric model | Python integers | JavaScript `Number` behavior | Fixed-width `int32_t` alias |
| Main educational focus | Detailed instruction-cycle mechanics | Application/event-driven observation | Systems-oriented architecture |

The implementations intentionally do not duplicate exactly the same program.

Python focuses on explicit instruction-cycle and pipeline mechanics.

JavaScript demonstrates how the model can interact with event-driven and asynchronous application behavior.

C++ places the instruction cycle inside a realistic embedded telemetry scenario and emphasizes structured systems design.

## Limitations of the implementations

These programs are educational CPU models rather than hardware-accurate simulators.

They intentionally omit or simplify many real processor mechanisms.

Examples include:

- caches
- virtual memory
- translation lookaside buffers
- privilege levels
- interrupts
- DMA
- multiple execution units
- precise hardware timing
- speculative execution
- branch prediction
- out-of-order execution
- register renaming
- reorder buffers
- instruction decoding from actual binary encodings
- instruction-level parallelism beyond the simplified pipeline
- hardware coherence protocols

The five-stage pipeline is therefore a conceptual model rather than a representation of a particular commercial processor.

## Best practices for understanding the instruction cycle

A reliable way to analyze an instruction is to ask five questions.

**Fetch**

Where is the instruction located, and what is the current PC?

**Decode**

What opcode is this, and which operands does it use?

**Execute**

What computation or address calculation occurs?

**Memory**

Does the instruction read or write data memory?

**Write back**

Does a result modify a register?

For branches, add a sixth practical question:

**Control flow**

Does the instruction change the next PC?

## Practical applications

The instruction cycle is fundamental to:

- general-purpose CPUs
- embedded systems
- microcontrollers
- operating systems
- compilers
- virtual machines
- emulators
- computer architecture
- performance engineering
- hardware design
- debugging
- cybersecurity research

Understanding the instruction cycle helps connect high-level programs to the lower-level mechanisms that ultimately execute them.

## Relationship between software and hardware

A statement such as:

`total = a + b`

at a high level can eventually result in machine instructions that:

1. load values into registers,
2. execute an ALU operation,
3. store the result,
4. continue to the next instruction.

The instruction cycle provides the bridge between software instructions and processor operations.

The exact instructions depend on the compiler, optimization level, target ISA, data types, calling convention, and surrounding program.

## Production considerations

A production CPU is not implemented as a simple sequential loop like the educational Python class.

Hardware implements instruction processing using physical circuits, clocked storage elements, control logic, execution units, caches, buses, predictors, and memory-management hardware.

A hardware implementation must account for:

- timing closure
- power consumption
- area
- reliability
- thermal limits
- instruction compatibility
- exception precision
- memory consistency
- security
- manufacturing constraints

A software simulator instead prioritizes clarity, observability, and deterministic behavior.

## Conceptual execution trace

For:

`MOVI R1, 10`

the trace is:

`FETCH → DECODE → EXECUTE → MEMORY → WRITE BACK`

For:

`LOAD R2, [R1 + 4]`

the trace is:

`FETCH → DECODE → address calculation → MEMORY READ → WRITE BACK`

For:

`STORE R2, [R1 + 4]`

the trace is:

`FETCH → DECODE → address calculation → MEMORY WRITE → no register write`

For:

`BEQ target`

the trace is:

`FETCH → DECODE → branch condition evaluation → control-flow decision`

These examples demonstrate why the stages are architectural concepts rather than identical operations for every instruction.

## Key distinctions

### Fetch versus decode

Fetch obtains the instruction.

Decode determines its meaning.

### Execute versus memory access

Execute performs the ALU operation or address calculation.

Memory access performs the data-memory operation when required.

### Memory access versus write back

Memory access interacts with data memory.

Write back updates the destination register.

### Architectural state versus pipeline state

Architectural state includes programmer-visible registers and memory.

Pipeline state contains temporary internal information needed to keep multiple instructions moving through the processor.

### Latency versus throughput

Latency describes completion time for an individual operation.

Throughput describes how frequently operations can complete in a sustained stream.

### ISA versus microarchitecture

The ISA defines the programmer-visible instruction contract.

The microarchitecture defines how hardware implements that contract.

## Final implementation mapping

The complete learning path represented by the three programs is:

`Instruction`

`↓`

`Fetch`

`↓`

`Decode`

`↓`

`Execute`

`↓`

`Memory Access`

`↓`

`Write Back`

`↓`

`Architectural State`

The Python implementation makes this sequence explicit and extends it with pipeline hazards, forwarding, stalls, and flushing.

The JavaScript implementation demonstrates the same CPU concepts using classes, objects, arrays, maps, exceptions, event-driven tracing, and asynchronous cycle observation.

The C++ implementation embeds the instruction cycle into a sensor-telemetry processor, showing how arithmetic, memory access, comparison, branching, validation, diagnostics, and dependency analysis can be organized into a systems-oriented design.
