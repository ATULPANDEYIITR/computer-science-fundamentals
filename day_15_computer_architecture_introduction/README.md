# Computer architecture introduction

## Topic scope

This study material introduces computer architecture from the level of binary data and digital logic through CPU components, instruction execution, memory, input/output, instruction sets, caching, pipelining and virtual memory.

The three implementations use the same broad subject from different perspectives:

- Python provides a highly readable educational CPU simulator and supporting models.
- JavaScript demonstrates the same architectural ideas in an executable application-oriented language, including event-driven I/O.
- C++ develops a more structured technical case study representing a small embedded sensor-processing system.

The central relationship is:

**software → ISA → CPU datapath and control → memory and I/O → physical hardware**

Understanding this relationship is fundamental to understanding how programs actually execute.

## Computer architecture and computer organization

Computer architecture describes the programmer-visible behavior of a computer.

Examples include:

- instruction set
- registers visible to programs
- instruction formats
- supported data types
- addressing modes
- memory-access rules
- exception and privilege behavior

Computer organization describes the internal implementation used to realize that architecture.

Examples include:

- ALU implementation
- pipeline stages
- cache hierarchy
- branch prediction
- number of execution units
- internal buses
- control logic
- physical memory technology

A useful distinction is that architecture describes **what the machine provides**, while organization describes **how the machine provides it**.

Two processors can implement the same ISA while having very different internal organizations. One implementation may have a short pipeline and simple cache structure, while another may use deeper pipelines, larger caches, multiple execution units and sophisticated branch prediction.

## Instruction Set Architecture

An Instruction Set Architecture, or ISA, defines the interface between software and a processor.

An ISA specifies concepts such as:

- available instructions
- registers
- operand types
- instruction encoding
- addressing modes
- memory-access semantics
- arithmetic behavior
- control-flow instructions
- exception mechanisms
- privilege mechanisms

The ISA is important because compiled programs depend on this contract.

A compiler can generate machine instructions for a particular ISA without needing to know every physical detail of the processor that will execute them.

The educational ISA implemented in all three deliverables is intentionally small. Its instructions include:

- `NOP`
- `LOAD_IMM`
- `LOAD`
- `STORE`
- `ADD`
- `SUB`
- `AND`
- `OR`
- `XOR`
- `SHL`
- `SHR`
- `JMP`
- `JZ`
- `CMP`
- `IN`
- `OUT`
- `HALT`

The simplified instruction format is 16 bits:

- high 8 bits: opcode
- low 8 bits: operand

For example, an instruction represented as `0x20C8` can be interpreted as opcode `0x20`, corresponding to `ADD`, with operand `0xC8`, corresponding to decimal address `200`.

Real ISAs are substantially more sophisticated. They may use multiple instruction formats, register fields, immediate fields, function fields, condition codes and architectural metadata.

## CPU fundamentals

The Central Processing Unit is responsible for executing instructions.

A simplified CPU contains:

- registers
- arithmetic logic unit
- control unit
- program counter
- instruction register
- memory interface
- I/O interface
- status flags

### Registers

Registers are small storage locations inside the processor.

The implementations use several conceptual registers.

`PC`, the program counter, contains the address of the next instruction.

`IR`, the instruction register, holds the instruction currently being processed.

`ACC`, the accumulator, holds an operand or intermediate result.

`MAR`, the memory address register, represents the address involved in a memory operation.

`MDR`, the memory data register, represents data transferred between CPU and memory.

Real processors usually contain many more registers, and modern ISAs frequently provide general-purpose registers rather than relying primarily on a single accumulator.

### ALU

The Arithmetic Logic Unit performs operations such as:

- addition
- subtraction
- AND
- OR
- XOR
- shifts

The Python and JavaScript implementations provide an explicit `ALU` class. The C++ case study implements the same functionality in an `ALU` class with an `ALUResult` structure.

An ALU operation may produce both a result and status information.

For example, an 8-bit addition can produce a result that wraps around from 255 to 0. A carry flag can record that the mathematical result exceeded the available 8-bit range.

### Control unit

The control unit determines which internal actions must occur for an instruction.

For an addition instruction, a simplified control sequence could require:

1. fetch the instruction
2. decode the opcode
3. identify the source operand
4. obtain the required memory value
5. send operands to the ALU
6. write the ALU result into the destination
7. update status flags

The C++ implementation separates this idea into a `ControlUnit` and `ControlSignals` structure.

This separation illustrates an important architectural distinction between the **datapath**, which moves and transforms data, and the **control path**, which determines what the datapath should do.

## Instruction cycle

The basic instruction cycle is commonly described using these stages:

1. Fetch
2. Decode
3. Execute
4. Memory access when required
5. Write-back when required

The exact stages depend on the processor design.

### Fetch

The program counter identifies the next instruction address.

The CPU reads the instruction from memory and places it into the instruction register.

The program counter normally advances so execution can continue with the following instruction.

The educational CPUs use two-byte instructions, so the PC normally increases by two.

### Decode

The CPU determines which operation the instruction represents and interprets its operand fields.

For example:

`ADD 201`

means that the CPU should perform addition using the value stored at memory address 201.

### Execute

The CPU performs the requested operation.

For arithmetic instructions, the ALU usually performs the computation.

For branch instructions, the program counter may be changed.

For load and store instructions, the memory subsystem is involved.

### Memory access

Instructions that access memory require a transfer between CPU and memory.

A `LOAD` retrieves a value from memory.

A `STORE` writes a CPU value to memory.

### Write-back

The result of an instruction may be written into a register.

A real processor can combine or subdivide these activities in many ways.

## Memory

Memory provides addressable storage for instructions and data.

The examples model byte-addressable memory.

If a memory contains 256 bytes, valid addresses range from 0 through 255.

The memory model explicitly validates addresses. This is important because an invalid memory access is a fundamental failure condition.

The Python `Memory` class supports byte and 16-bit word operations.

The JavaScript implementation uses `Uint8Array`, which is particularly useful for representing byte-oriented memory because JavaScript normally uses general-purpose numeric values rather than fixed-width CPU registers.

The C++ implementation uses `std::vector<std::uint8_t>` to represent memory.

## Endianness

When a multi-byte value is stored in memory, the order of its bytes matters.

For the 16-bit value `0x1234`:

Big-endian representation stores:

`12 34`

Little-endian representation stores:

`34 12`

Endianness is important when:

- interpreting binary files
- communicating between systems
- implementing protocols
- reading memory dumps
- writing serialization code
- working with processors of different architectural conventions

The Python implementation explicitly demonstrates both forms.

## Binary and two's complement

Computers represent information using bits.

A byte contains eight bits and can represent 256 distinct bit patterns.

Unsigned 8-bit values range from:

`0` through `255`

Signed two's-complement 8-bit values range from:

`-128` through `127`

Two's complement allows subtraction and negative numbers to be handled using binary addition hardware.

The implementations also demonstrate fixed-width wraparound.

For example:

`250 + 10`

produces the 8-bit bit pattern corresponding to:

`4`

because 260 modulo 256 is 4.

This behavior is distinct from arbitrary-precision mathematical integers and must be considered whenever software models fixed-width hardware.

## Digital logic foundations

At the lowest conceptual level, processors are built from digital logic.

Important gates include:

- AND
- OR
- NOT
- XOR

These gates can be combined into larger circuits.

Examples include:

- half adders
- full adders
- multiplexers
- decoders
- encoders
- comparators
- registers
- ALUs

A simplified CPU datapath can therefore be viewed as a hierarchy:

**logic gates → arithmetic circuits → ALU/registers → datapath → CPU → computer system**

This relationship is particularly useful when studying CPU construction using circuit simulators such as Logisim.

## Buses

A bus is a communication pathway between components.

Three conceptual categories are commonly introduced:

### Data bus

Carries data.

### Address bus

Carries addresses identifying memory or I/O locations.

### Control bus

Carries control information such as read, write and timing-related signals.

Modern processors do not necessarily implement these concepts as one simple shared physical bus. Internal interconnects can be considerably more complex.

The bus model remains useful because it establishes the fundamental idea of communication between CPU, memory and peripherals.

## Input and output

A computer must communicate with devices outside the CPU.

Examples include:

- keyboard
- display
- storage
- network interface
- sensors
- printers
- timers

Two important approaches are:

- programmed I/O
- interrupt-driven I/O

### Programmed I/O

The processor explicitly checks or accesses a device.

This can be simple but may waste CPU time when a device is slow.

### Interrupt-driven I/O

A device can request CPU attention through an interrupt.

The processor can perform other work and respond when the event occurs.

The Python implementation includes an `InterruptController`.

The JavaScript implementation uses an asynchronous event model to demonstrate a related software concept. JavaScript's event loop is not equivalent to a hardware interrupt controller, but it provides a useful comparison because both involve responding to events without requiring continuous synchronous polling.

The C++ case study models an embedded sensor and console device.

## Addressing modes

An addressing mode defines how an instruction identifies its operand.

Common categories include:

### Immediate addressing

The operand is included directly in the instruction.

Example:

`LOAD_IMM 42`

The value is 42.

### Direct addressing

The instruction contains a memory address.

Example:

`LOAD 200`

The CPU reads the value at memory address 200.

### Register addressing

The operand is located in a CPU register.

Example:

`ADD R1`

### Indirect addressing

A register or memory location contains the address of the actual operand.

Example concept:

`LOAD [R1]`

### Indexed addressing

An address can be computed from a base plus an index.

Example concept:

`LOAD [R1 + R2]`

### Relative addressing

The target is computed relative to the current program counter.

This is common for branches because code can be relocated while maintaining relative control flow.

### Stack addressing

The operand is implicitly obtained from the stack.

Addressing modes affect:

- instruction size
- hardware complexity
- compiler design
- code density
- execution behavior

## RISC and CISC

RISC means Reduced Instruction Set Computer.

CISC means Complex Instruction Set Computer.

Traditional distinctions include:

| Characteristic | RISC tendency | CISC tendency |
|---|---|---|
| Instruction philosophy | Simpler operations | More complex operations |
| Instruction length | Often regular | Often variable |
| Memory operations | Frequently load/store | May permit memory operands |
| Decoding | Often simpler | Can be more complex |
| Code density | May require more instructions | Can provide compact encodings |
| Hardware strategy | More regular datapath | More complex instruction handling |

The distinction should not be reduced to "RISC is fast and CISC is slow."

Modern processors can blur traditional categories. A processor can have a complex ISA while internally translating instructions into simpler internal operations.

## Accumulator, stack and register-based designs

The way an ISA represents operands affects the CPU architecture.

### Accumulator architecture

Many operations implicitly use a primary accumulator.

Example:

`LOAD A`

`ADD B`

The result is placed back into the accumulator.

The educational CPU follows this general model.

### Stack architecture

Operands are taken from a stack.

For:

`(2 + 3) * 4`

a stack machine can push 2, push 3, add, push 4 and multiply.

The Python implementation provides a `StackMachine`.

### Register-based architecture

Instructions explicitly identify registers.

For example:

`ADD R1, R2, R3`

could mean:

`R3 = R1 + R2`

Many modern general-purpose processors use register-oriented designs.

## Instruction formats

An instruction format defines how bits are divided among fields.

A typical instruction may contain:

- opcode
- source register
- destination register
- immediate value
- addressing-mode bits
- function code

The educational ISA uses a deliberately simple format:

`[ opcode: 8 bits ][ operand: 8 bits ]`

This makes instruction encoding and decoding easy to observe.

Real architectures generally require several instruction formats because different operations need different numbers and types of operands.

## Instruction decoding

Decoding transforms an encoded bit pattern into an operation the CPU understands.

The three implementations contain explicit decode logic.

For example:

`0x20C8`

is separated into:

- opcode = `0x20`
- operand = `0xC8`

The decoder maps `0x20` to `ADD`.

The operand `0xC8` represents address 200.

This demonstrates why ISA documentation and instruction encodings must be precise.

## Datapath and control

A CPU can be conceptually divided into two major structures.

### Datapath

The datapath contains components through which data moves or is transformed.

Examples:

- registers
- ALU
- multiplexers
- buses
- memory interfaces

### Control

The control logic determines which operations occur.

For example, an ADD instruction may require signals equivalent to:

- select source A
- select source B
- select ADD operation
- enable destination register
- update flags

The C++ `ControlUnit` demonstrates this concept through `ControlSignals`.

This is closely related to the circuits constructed in educational digital-logic environments.

## Logisim perspective

Logisim-style CPU construction makes architecture concrete by representing components visually.

A simplified educational CPU can contain:

- clock
- program counter
- instruction memory
- instruction register
- register file
- ALU
- multiplexers
- control logic
- data memory
- output devices

A typical data flow is:

**PC → instruction memory → instruction register → control logic → register/ALU datapath → memory/register write-back**

The Python and C++ models represent these components as software abstractions. A circuit simulator represents analogous components as interconnected digital circuits.

The software model is useful for understanding behavior.

The circuit model is useful for understanding how the behavior can be physically organized from logic components.

## CPU simulators

CPU simulators allow instructions to be executed without requiring a physical processor.

An educational simulator normally provides:

- registers
- memory
- instruction encoding
- instruction execution
- program counter
- status flags
- program loading
- tracing
- breakpoints or step execution

The Python `CPU` class demonstrates these principles directly.

Its `step()` method models one instruction cycle.

Its `run()` method repeatedly executes instructions until the CPU reaches `HALT` or a safety cycle limit is reached.

The cycle limit is an important defensive mechanism because an incorrectly written program can otherwise execute forever.

## Assembly-like programming

Assembly language provides a textual representation of machine instructions.

The examples support simple instructions such as:

`LOAD 200`

`ADD 201`

`STORE 202`

`OUT`

`HALT`

An assembler translates these textual representations into `Instruction` objects.

The process is conceptually:

**assembly source → parsing → opcode lookup → operand validation → machine encoding**

Real assemblers are much more sophisticated. They commonly support:

- labels
- symbolic constants
- macros
- directives
- relocation
- multiple sections
- symbol tables
- object files
- architecture-specific syntax

The educational assembler deliberately concentrates on the relationship between assembly mnemonics and encoded instructions.

## Branches and control flow

A CPU normally executes instructions sequentially until a control-flow instruction changes the program counter.

The educational ISA includes:

`JMP`

and:

`JZ`

`JMP` unconditionally changes the program counter.

`JZ` changes the program counter only when the zero flag is set.

The `CMP` instruction sets the zero flag when the accumulator and selected memory value are equal.

This establishes the foundation of conditional execution.

A high-level statement such as:

`if (a == b)`

eventually requires machine-level mechanisms for:

- comparison
- status information
- conditional control flow

## Pipelining

A processor can divide instruction execution into stages.

A common educational pipeline contains:

- IF: Instruction Fetch
- ID: Instruction Decode
- EX: Execute
- MEM: Memory
- WB: Write Back

Without pipelining, an instruction can occupy the complete datapath before the next instruction starts.

With pipelining, multiple instructions can occupy different stages simultaneously.

For example:

| Cycle | I1 | I2 | I3 |
|---|---|---|---|
| 1 | IF | | |
| 2 | ID | IF | |
| 3 | EX | ID | IF |
| 4 | MEM | EX | ID |
| 5 | WB | MEM | EX |

This increases instruction throughput in an idealized system.

Pipelining does not mean that an individual instruction necessarily becomes five times faster.

## Pipeline hazards

Pipelining creates hazards.

### Data hazard

An instruction depends on the result of an earlier instruction that has not completed its required stage.

### Control hazard

A branch changes the instruction stream.

The processor may have already fetched instructions that should not execute.

### Structural hazard

Two operations require a hardware resource at the same time.

Possible solutions include:

- forwarding
- stalling
- instruction scheduling
- duplicated resources
- branch prediction
- speculative execution

The actual mechanisms depend on the processor architecture.

## Branch prediction

Branches can reduce pipeline efficiency because the CPU may not immediately know which instruction should execute next.

A branch predictor attempts to predict the direction of a branch.

The Python implementation contains a simple one-bit predictor.

A one-bit predictor remembers the most recent outcome.

Real processors can use considerably more advanced methods, including:

- two-bit predictors
- local history
- global history
- branch target buffers
- hybrid predictors

Incorrect predictions can cause pipeline work to be discarded.

## Memory hierarchy

Computer systems use multiple storage levels because no single technology simultaneously provides:

- very low latency
- very large capacity
- low cost
- low power consumption

A simplified hierarchy is:

1. Registers
2. L1 cache
3. L2 cache
4. L3 cache
5. RAM
6. SSD or HDD

Registers are extremely fast but very limited.

Main memory is much larger but slower.

Secondary storage is persistent and much larger but substantially slower than CPU-local storage.

## Cache memory

Caches exploit locality.

### Temporal locality

Data used recently may be used again.

Example:

A loop repeatedly reads the same variable.

### Spatial locality

Addresses near a recently accessed address may be used soon.

Example:

A program iterates through an array.

The cache examples implement a direct-mapped cache.

A direct-mapped cache determines a cache line using an index derived from the address.

A simplified address can be viewed as:

**tag | index | offset**

The educational cache uses one-byte blocks, so the offset is omitted from the implementation.

Important cache metrics include:

`hit rate = cache hits / total accesses`

`miss rate = cache misses / total accesses`

Cache misses can increase execution time because the processor must retrieve data from a slower level.

## Cache design trade-offs

Important cache decisions include:

- capacity
- line size
- associativity
- replacement policy
- write policy
- latency
- bandwidth

A larger cache can reduce capacity misses but may require more area and power.

Higher associativity can reduce conflict misses but makes lookup hardware more complex.

Larger cache lines can exploit spatial locality but may fetch unnecessary data.

## Memory performance

A useful simplified performance relationship is:

`CPU time = Instruction Count × CPI / Clock Frequency`

Where:

- Instruction Count is the number of executed instructions.
- CPI is average cycles per instruction.
- Clock Frequency is cycles per second.

Performance is therefore not determined solely by clock frequency.

Two processors operating at the same frequency can have different performance because of:

- different CPI
- different cache behavior
- different branch behavior
- different instruction counts
- different memory latency
- different execution width

## I/O architecture

Input/output connects the processor to external resources.

A device may be accessed through:

- special I/O instructions
- memory-mapped I/O
- interrupts
- DMA
- device controllers

### Memory-mapped I/O

Device registers occupy addresses in the processor's address space.

A store to a particular address can therefore cause a device operation instead of ordinary RAM storage.

The sensor case study conceptually represents device interaction while keeping the implementation simple.

## Interrupts

An interrupt is an event that requests processor attention.

A simplified sequence is:

1. device raises an interrupt
2. CPU recognizes it
3. CPU saves required execution state
4. CPU transfers control to an interrupt handler
5. handler services the device
6. CPU restores execution state
7. interrupted program resumes

Actual processors provide architectural mechanisms for interrupt vectors, privilege transitions, masking and saved state.

The Python implementation models a basic interrupt queue.

## Virtual memory

Virtual memory allows programs to operate using virtual addresses that are translated into physical addresses.

A simplified virtual address can be divided into:

**virtual page number | page offset**

A page table maps a virtual page to a physical frame.

The Python and C++ implementations demonstrate this basic mapping.

For example, if the page size is 16 bytes:

Virtual address:

`20`

can be divided into:

- virtual page = 1
- offset = 4

If virtual page 1 maps to physical frame 2:

Physical address:

`2 × 16 + 4 = 36`

Real systems use structures such as:

- multi-level page tables
- translation lookaside buffers
- page permissions
- present bits
- dirty bits
- accessed bits
- page-fault handling

## C++ case study

The C++ implementation models a small embedded sensor-processing computer.

The system contains:

- sensor device
- console output device
- CPU
- memory
- ALU
- control unit
- instruction representation
- cache
- virtual memory model
- pipeline model

### Problem being modeled

Two sensor samples are obtained and added.

The processor stores the samples in memory, executes a machine-level program and writes the result to the console.

The conceptual application operation is:

`result = sample1 + sample2`

The machine-level sequence is:

`LOAD 400`

`ADD 401`

`STORE 402`

`OUT`

`HALT`

This demonstrates the transformation from an application requirement into ISA-level operations.

### Major components

`SensorDevice` represents an external input source.

`ConsoleDevice` represents an output device.

`Memory` provides byte-addressable storage.

`ALU` performs arithmetic and logic.

`Instruction` represents encoded ISA operations.

`ControlUnit` translates instructions into conceptual control signals.

`CPU` combines registers, memory, ALU operations, flags and instruction execution.

`DirectMappedCache` demonstrates locality and cache hits.

`PageTable` demonstrates virtual-to-physical address translation.

`PipelineModel` demonstrates idealized instruction overlap.

### Data flow

The case study follows this conceptual path:

**sensor → memory → CPU fetch/decode/execute → ALU → memory → console**

The CPU does not directly perform the high-level expression as a single abstract operation. It executes a sequence of ISA instructions.

### Instruction execution

The C++ CPU performs a simplified fetch/execute cycle.

During fetch:

1. PC identifies the instruction address.
2. Memory returns the encoded instruction.
3. IR receives the instruction.
4. PC advances.

During execution:

1. opcode is interpreted
2. operand is identified
3. memory or register data is obtained
4. ALU or control-flow operation occurs
5. registers, flags or memory are updated

### Why C++ is useful here

C++ provides explicit control over:

- fixed-width integer types
- object lifetimes
- data structures
- exception handling
- memory representations
- performance-sensitive implementation choices

`std::uint8_t` and `std::uint16_t` make the educational hardware widths explicit.

The standard library also provides containers such as `std::vector`, `std::queue` and `std::unordered_map`, which are useful for modeling memory, devices and page tables.

## Python implementation

The Python implementation is designed as a broad architecture laboratory.

Important classes include:

- `Register`
- `ALU`
- `Memory`
- `Instruction`
- `InputDevice`
- `OutputDevice`
- `CPU`
- `Assembler`
- `DirectMappedCache`
- `StackMachine`
- `SimplePageTable`
- `OneBitBranchPredictor`
- `Datapath`
- `ControlSignals`

The CPU model emphasizes readability.

Python is particularly suitable for studying architecture because complex concepts can be expressed with relatively little language overhead.

The implementation includes:

- binary representation
- two's complement
- fixed-width arithmetic
- memory access
- endianness
- instruction encoding
- instruction decoding
- assembly parsing
- instruction execution
- conditional control flow
- cache behavior
- interrupt concepts
- pipeline scheduling
- virtual memory
- branch prediction
- testing

## JavaScript implementation

The JavaScript implementation emphasizes application-oriented modeling and event-driven behavior.

Important classes and structures include:

- `Register`
- `ALU`
- `ByteMemory`
- `Instruction`
- `EducationalCPU`
- `DirectMappedCache`
- `InterruptController`
- `SimpleProcessorSystem`

JavaScript does not naturally provide fixed-width CPU registers for ordinary `Number` values, so the implementation explicitly masks values when modeling an 8-bit datapath.

`Uint8Array` is used for memory because it directly represents bytes.

The asynchronous I/O example demonstrates a conceptual relationship between hardware events and software event handling.

The example should not be interpreted as saying that JavaScript's event loop is equivalent to hardware interrupts. They operate at different abstraction levels.

## Important distinctions

### Architecture vs organization

Architecture defines the software-visible contract.

Organization defines the implementation.

### ISA vs microarchitecture

The ISA specifies instructions and programmer-visible behavior.

Microarchitecture specifies how those instructions are internally executed.

### RAM vs storage

RAM is working memory directly used by executing programs.

SSD and HDD storage are persistent secondary storage.

### Register vs cache

Registers are directly integrated into the CPU's instruction execution model.

Cache is a memory hierarchy mechanism that keeps selected data closer to execution hardware.

### Cache vs RAM

Cache is smaller and faster.

RAM is larger and slower.

### Instruction count vs clock frequency

A processor with a higher clock frequency is not necessarily faster because execution time also depends on instruction count and CPI.

### Latency vs throughput

Latency describes the time associated with an individual operation.

Throughput describes how many operations can be completed over a period.

Pipelining primarily improves throughput under suitable conditions.

## Edge cases

The implementations deliberately demonstrate failure conditions.

### Invalid memory address

Attempting to access memory outside its valid range is rejected.

This models the importance of address validation in a software simulator.

Actual hardware behavior depends on the architecture and operating environment. An invalid user-space access may result in a protection fault rather than a simple language exception.

### Invalid instruction

An unknown opcode cannot be safely executed by the educational CPU.

Real processors have architecture-specific behavior for undefined or reserved encodings.

### Arithmetic overflow

Fixed-width arithmetic can discard higher-order bits.

This is different from Python's ordinary integer arithmetic, which can represent integers with arbitrary precision.

### Stack underflow

A stack operation requiring a missing operand is invalid.

The Python implementation explicitly raises an exception.

### Page fault

A virtual address whose page is not mapped produces a simulated page fault.

Real operating systems may respond by loading a page, terminating a process or handling the condition in another architecture-specific way.

### Infinite execution

A program containing an unintended loop can execute indefinitely.

The CPU simulators therefore use a maximum cycle limit.

## Common mistakes

### Confusing architecture with organization

A cache size or pipeline depth is usually an implementation detail rather than the ISA itself.

### Assuming one instruction equals one clock cycle

Real processors may have variable instruction latency, pipelines, stalls, cache misses and multiple instructions in flight.

The educational CPU uses one high-level cycle per instruction for clarity.

### Treating memory as infinitely fast

Memory latency is a major factor in real computer performance.

### Ignoring locality

Sequential access patterns often interact differently with caches than irregular access patterns.

### Assuming all CPUs use the same instruction format

Different ISAs have different encoding schemes.

### Assuming assembly is machine code

Assembly is a human-readable representation of instructions. Machine code is the encoded binary representation consumed by the processor.

### Confusing a simulator with real hardware

The educational CPU is a behavioral model.

It does not reproduce transistor-level timing, electrical behavior, speculative execution, cache coherence, branch predictor internals or every architectural exception.

### Ignoring fixed-width behavior

Software using arbitrary-precision integers can hide behavior that becomes important on fixed-width processors.

## Performance considerations

Important architectural performance factors include:

- instruction count
- CPI
- clock frequency
- cache hit rate
- memory latency
- branch prediction accuracy
- pipeline stalls
- instruction-level parallelism
- execution width
- memory bandwidth

A simplified model is:

`CPU time = IC × CPI × clock cycle time`

Since:

`clock cycle time = 1 / clock frequency`

the relationship becomes:

`CPU time = IC × CPI / frequency`

This is a model rather than a complete real-world performance equation.

Modern systems require consideration of memory stalls, synchronization, multicore effects, operating-system overhead and other factors.

## Security considerations

Computer architecture also establishes important security mechanisms.

### Memory protection

Programs should not normally access arbitrary memory belonging to other programs.

### Privilege levels

Processors can distinguish privileged operating-system operations from ordinary application operations.

### Virtual memory isolation

Separate virtual address spaces help isolate processes.

### I/O protection

Applications should not normally have unrestricted control over hardware devices.

### Speculative execution

Modern processors may execute instructions speculatively to improve performance.

Incorrect speculative paths must not violate architectural correctness. Microarchitectural side effects can nevertheless create security concerns, which is why speculative execution is also an important security topic.

### Fault handling

Invalid instructions, memory accesses and privileged operations require controlled handling.

The simplified implementations demonstrate validation and explicit error handling, while real processors implement these mechanisms through architectural exceptions and privilege mechanisms.

## Design considerations

A processor designer must balance:

- performance
- power consumption
- silicon area
- complexity
- compatibility
- verification effort
- manufacturing cost
- software ecosystem
- reliability
- security

A design that maximizes one property may negatively affect another.

For example, increasing cache size can improve hit rates for some workloads but increases area and power consumption.

A deeper pipeline can increase clock frequency potential but can make branch penalties and hazard handling more complicated.

A complex ISA can provide compact instructions but can make decoding more complicated.

## Verification and debugging

CPU development requires extensive verification.

Useful techniques include:

- instruction-level tests
- register-state checks
- memory consistency checks
- randomized testing
- differential testing
- simulator traces
- assertions
- exception testing
- boundary testing

The three implementations include self-tests covering:

- memory reads and writes
- ALU arithmetic
- instruction encoding
- instruction decoding
- CPU execution
- cache behavior
- virtual address translation

Instruction tracing is particularly useful because it makes the relationship between PC, instruction and CPU state visible.

A trace such as:

`cycle=001 PC=000 LOAD 200`

can be used to follow execution instruction by instruction.

## Complexity considerations

Different components have different algorithmic behavior.

A direct array-based memory access is conceptually constant time:

`O(1)`

A direct-mapped cache lookup is also modeled as:

`O(1)`

A page-table lookup in the C++ example uses an unordered map and is expected average:

`O(1)`

A pipeline schedule for `n` instructions and `k` stages requires:

`O(n × k)`

in the educational schedule-generation model.

Real hardware complexity is not completely described by software Big-O notation because circuit area, propagation delay, transistor count and energy are also important.

## Practical applications

Computer architecture concepts appear in:

- desktop processors
- laptops
- smartphones
- servers
- cloud infrastructure
- embedded systems
- automobiles
- robotics
- networking equipment
- game consoles
- industrial controllers
- data-center accelerators
- storage controllers
- IoT devices

The same principles recur at different scales.

An embedded microcontroller may have a relatively small CPU and memory system.

A server processor may contain many cores, large cache hierarchies, sophisticated branch prediction and advanced memory subsystems.

## Relationship to Logisim and CPU simulators

A useful conceptual progression is:

**logic gates → registers → ALU → datapath → control unit → CPU → memory → I/O → complete computer**

Logisim-style circuit construction is particularly useful for observing how individual digital components are connected.

A CPU simulator is useful for observing how instructions change machine state.

The Python implementation is primarily a behavioral CPU simulator.

The JavaScript implementation adds application-level and event-driven perspectives.

The C++ implementation integrates the architecture concepts into a more structured embedded-system case study.

Together, the implementations show that computer architecture is not simply the study of CPUs. It is the study of the interfaces and mechanisms connecting instructions, computation, memory and external devices.
