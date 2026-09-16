# Central Processing Unit and CPU Simulators

## Introduction

A Central Processing Unit (CPU) is the part of a computer responsible for executing instructions. At the conceptual level, a CPU repeatedly fetches an instruction, determines what that instruction means, performs the required operation, updates its internal state, and continues with the next instruction.

This project builds that idea into a working CPU simulator.

The implementations model a small educational processor containing:

- An Arithmetic Logic Unit (ALU)
- A Control Unit
- General-purpose registers
- A Program Counter (PC)
- An Instruction Register (IR)
- A Stack Pointer (SP)
- Main memory
- Status flags
- An instruction set
- A fetch-decode-execute cycle
- Conditional and unconditional branches
- Stack operations
- Procedure calls and returns
- Input and output
- Program validation
- Instruction tracing
- Simplified cycle accounting

The three implementations use the same architectural concepts while emphasizing different programming techniques.

The Python implementation is a detailed educational emulator with a small assembler.

The JavaScript implementation emphasizes object-oriented design, structured instruction objects, asynchronous execution, and application-level simulation.

The C++ implementation develops an industry-style sensor-controller case study using explicit types, arrays, classes, validation, and deterministic execution.

---

## Fundamental concepts

### Central Processing Unit

The CPU executes machine instructions. An instruction normally specifies an operation and the operands involved in that operation.

A simplified instruction execution process can be represented as:

`FETCH → DECODE → EXECUTE → STATE UPDATE → FETCH`

A real CPU performs many additional operations internally, but this cycle is a useful architectural abstraction.

### Arithmetic Logic Unit

The ALU performs operations such as:

- Addition
- Subtraction
- Multiplication
- Division
- AND
- OR
- XOR
- NOT
- Shifts
- Comparisons

The ALU does not normally decide which instruction should be executed next. It performs operations selected by the surrounding control logic.

### Control Unit

The Control Unit coordinates instruction execution.

Conceptually, it determines:

- Which operation is requested
- Which registers are read
- Which register receives a result
- Whether memory must be accessed
- Whether flags should be updated
- Whether the Program Counter should change
- Whether a stack operation is required

In a real processor, this functionality is implemented using complex hardware structures rather than a simple software `switch` statement.

### Registers

Registers are small, fast storage locations located inside the processor.

The simulated architecture contains eight general-purpose registers:

`R0` through `R7`

A register can hold an intermediate result, operand, address, counter, or other temporary state.

### Program Counter

The Program Counter, or PC, identifies the location of the next instruction to fetch.

For normal sequential execution:

`PC ← PC + 1`

A branch, jump, call, interrupt, or other control-flow event can replace the normal sequential value.

### Instruction Register

The Instruction Register, or IR, holds the instruction currently being processed.

In the simulator, the fetch stage copies the instruction addressed by the PC into the IR before execution.

### Memory

Memory stores data and, conceptually, instructions.

The educational CPU uses 256 memory locations.

Memory access is explicitly represented through `LOAD` and `STORE`.

Registers and memory serve different purposes. Registers are very small and directly integrated into CPU execution, while memory provides a larger storage space.

### Stack Pointer

The Stack Pointer, or SP, identifies the current position of the simulated stack.

The stack supports last-in-first-out behavior.

If values are pushed in this order:

`10 → 20 → 30`

the values are popped in this order:

`30 → 20 → 10`

The simulator uses the stack for explicit `PUSH` and `POP` instructions and also for return addresses during `CALL` and `RET`.

---

## CPU instruction cycle

### Fetch

The PC identifies the next instruction.

The simulator retrieves that instruction and places it into the IR.

The PC normally advances by one instruction.

### Decode

The opcode and operands are interpreted.

For example:

`ADD R2, R0, R1`

means that the CPU should:

1. Read `R0`.
2. Read `R1`.
3. Send the values to the ALU.
4. Perform addition.
5. Store the result in `R2`.
6. Update relevant flags.

### Execute

The selected functional component performs the operation.

Examples include:

- ALU arithmetic
- Register transfer
- Memory access
- Branching
- Stack manipulation
- Input
- Output

### State update

The resulting state may include changes to:

- Registers
- Memory
- PC
- SP
- Flags
- IR
- Output state

The cycle then repeats.

---

## Instruction set

The simulator uses a small educational instruction set.

| Instruction | Purpose |
|---|---|
| `NOP` | Perform no operation |
| `MOV` | Copy an immediate or register value into a register |
| `LOAD` | Load a memory value into a register |
| `STORE` | Store a register value in memory |
| `ADD` | Add two operands |
| `SUB` | Subtract two operands |
| `MUL` | Multiply two operands |
| `DIV` | Divide two operands |
| `INC` | Increment a register |
| `DEC` | Decrement a register |
| `AND` | Bitwise AND |
| `OR` | Bitwise OR |
| `XOR` | Bitwise XOR |
| `NOT` | Bitwise complement |
| `SHL` | Shift left |
| `SHR` | Shift right |
| `CMP` | Compare two values through subtraction |
| `JMP` | Unconditional jump |
| `JZ` | Jump if zero |
| `JNZ` | Jump if not zero |
| `JN` | Jump if negative |
| `JP` | Jump if non-negative |
| `PUSH` | Push a value onto the stack |
| `POP` | Pop a value from the stack |
| `CALL` | Save a return address and branch |
| `RET` | Restore a return address |
| `IN` | Read an input value |
| `OUT` | Produce an output value |
| `HALT` | Stop execution |

This instruction set is intentionally much smaller than a modern processor instruction set.

---

## CPU registers and state

The simulated machine maintains several categories of state.

### General-purpose registers

`R0` through `R7` hold temporary computational values.

For example:

`MOV R0, 12`

places the value `12` into `R0`.

Then:

`MOV R1, 30`

places `30` into `R1`.

Finally:

`ADD R2, R0, R1`

causes the ALU to calculate `12 + 30` and store `42` in `R2`.

### PC

The PC controls instruction sequencing.

A normal instruction increments the PC. A branch replaces it with another program address.

### IR

The IR contains the fetched instruction.

It represents the instruction currently being interpreted by the simulated CPU.

### SP

The SP identifies the simulated stack position.

The stack is particularly important for procedure calls because the CPU must preserve a return address while executing another section of code.

### Flags

The simulator contains four flags:

| Flag | Meaning |
|---|---|
| Z | Result is zero |
| N | Result has its sign bit set |
| C | Unsigned carry occurred |
| V | Signed overflow occurred |

Flags provide information that later instructions can use.

---

## Numeric representation

The simulator models a fixed-width 16-bit CPU.

The unsigned range is:

`0` through `65535`

A fixed-width machine cannot represent a value outside this range directly in a 16-bit register.

Therefore:

`65535 + 1`

wraps to:

`0`

The simulator masks arithmetic results so that values remain within the simulated word size.

This is different from ordinary Python integer behavior because Python integers can grow to arbitrary precision.

JavaScript uses the same general educational approach but has its own numeric semantics, so the JavaScript implementation restricts the simulated word size to 32 bits or less.

C++ uses `std::uint16_t` for the simulated word.

---

## Signed integers and two's complement

The same bit pattern can have different interpretations depending on whether it is treated as unsigned or signed.

For a 16-bit value:

`0xFFFF`

is:

`65535` unsigned

but:

`-1` signed

The simulator interprets the most significant bit as the sign bit when signed interpretation is required.

This is based on two's-complement representation, the standard representation used by modern general-purpose processors for signed integers.

---

## ALU operations

### Addition

For:

`12 + 30`

the ALU produces:

`42`

The zero, negative, carry, and overflow flags are updated according to the result.

### Subtraction

For:

`30 - 12`

the result is:

`18`

Subtraction is also used by `CMP`.

### Comparison

The `CMP` instruction does not need to store a normal result.

Instead, it performs a subtraction internally and updates the flags.

For:

`CMP R0, R1`

the CPU effectively evaluates:

`R0 - R1`

and uses the resulting flags for conditional branching.

### Logical operations

Bitwise operations manipulate individual bits.

For example:

`10101010 AND 11001100`

produces:

`10001000`

The simulator implements:

- AND
- OR
- XOR
- NOT

### Shifts

A left shift moves bits toward the most significant position.

A right shift moves bits toward the least significant position.

Shifts are fundamental to bit manipulation, masking, encoding, low-level arithmetic, and hardware-oriented programming.

---

## Flags and control flow

Conditional branching depends on CPU state.

A typical sequence is:

`CMP R0, R1`

followed by:

`JZ target`

The comparison updates the zero flag.

If the values are equal, the zero flag becomes true and the branch changes the PC.

This demonstrates a key CPU principle:

**Data-processing instructions can influence later control-flow instructions through processor state.**

---

## Memory addressing

The simulator uses direct memory addresses.

For example:

`STORE R0, 100`

stores the contents of `R0` at memory address `100`.

Later:

`LOAD R1, 100`

loads the same value into `R1`.

This illustrates the basic relationship between registers and memory.

The simulator validates addresses before accessing memory. Attempting to access an invalid address produces a controlled error rather than silently corrupting state.

---

## Stack operations

The stack provides temporary storage.

`PUSH R0`

places the value of `R0` onto the stack.

`POP R1`

retrieves the most recently pushed value and places it into `R1`.

The stack is also used by `CALL` and `RET`.

### CALL

A `CALL` instruction:

1. Determines the target address.
2. Saves the current return address.
3. Changes the PC to the target.
4. Executes the called routine.

### RET

A `RET` instruction:

1. Retrieves the saved return address.
2. Places it into the PC.
3. Resumes execution after the original call.

This is the basic mechanism behind procedure calls in many instruction-set architectures.

---

# Python implementation

The Python implementation is the most extensive educational emulator in this project.

## Python architecture

The major classes are:

- `Opcode`
- `Instruction`
- `Flags`
- `ALU`
- `CPU`
- `Assembler`

### `Opcode`

`Opcode` is an enumeration containing the supported instruction names.

Using an enumeration prevents arbitrary strings from being silently interpreted as valid operations.

### `Instruction`

`Instruction` stores:

- Opcode
- Operand tuple

For example, the conceptual representation of:

`ADD R2, R0, R1`

is an instruction whose opcode is `ADD` and whose operands are `R2`, `R0`, and `R1`.

### `Flags`

The `Flags` dataclass represents CPU status information.

Its fields are:

- `zero`
- `negative`
- `carry`
- `overflow`

### `ALU`

The `ALU` class implements arithmetic and logical behavior.

It also handles:

- Word-size normalization
- Signed interpretation
- Carry detection
- Signed overflow detection
- Shift operations

### `CPU`

The `CPU` class combines the architecture.

Important state includes:

- `registers`
- `memory`
- `pc`
- `sp`
- `ir`
- `flags`
- `halted`
- `cycles`
- `instructions_executed`

The `fetch()` method models the fetch stage.

The `execute()` method models instruction execution.

The `step()` method combines one fetch-execute cycle.

The `run()` method repeatedly calls `step()` until `HALT`.

---

## Python instruction dispatch

The Python CPU uses opcode comparisons inside `execute()`.

For arithmetic instructions, operands are resolved first.

Register operands are read from the register file.

Immediate operands are treated as constants.

The resolved values are passed to the ALU.

The resulting value is written to the destination register.

This structure separates:

- Operand resolution
- ALU computation
- Register updates
- Control flow

That separation makes the simulator easier to inspect and extend.

---

## Python memory model

The Python simulator represents memory using a list.

Each location stores one simulated CPU word.

The methods:

- `read_memory()`
- `write_memory()`

perform address validation before access.

This is an important simulator-design principle. A CPU emulator should not allow an invalid virtual instruction or malformed program to silently corrupt its internal model.

---

## Python assembler

The `Assembler` class converts textual instructions into internal instruction objects.

The assembler performs two passes.

### First pass

The first pass records labels and their instruction addresses.

For example:

`loop:`

creates a symbolic name associated with the current instruction address.

### Second pass

The second pass parses instructions and resolves labels.

A source instruction such as:

`JNZ loop`

becomes a branch instruction containing the numeric address associated with `loop`.

This demonstrates the relationship between assembly language and machine-level instruction representation.

---

## Python trace mode

The Python simulator provides instruction tracing.

Trace output shows:

- Current PC
- Instruction
- Register state before execution
- Register state after execution
- Flags

This is useful for debugging:

- Incorrect branches
- Incorrect register values
- Infinite loops
- Unexpected flag changes
- Incorrect arithmetic
- Stack errors

A CPU simulator is particularly valuable because it makes otherwise invisible machine state observable.

---

## Python edge cases

The implementation explicitly handles:

- Invalid registers
- Invalid memory addresses
- Program addresses outside the loaded program
- Division by zero
- Stack underflow
- Stack overflow
- Negative shift amounts
- Unsupported instructions
- Excessive instruction execution
- Programs that exceed available memory

The execution limit is especially useful for accidental infinite loops.

---

# JavaScript implementation

The JavaScript implementation models the same CPU concepts using application-oriented JavaScript structures.

## JavaScript architecture

The principal classes are:

- `Flags`
- `ALU`
- `CPU`
- `Assembler`

Instructions are represented as JavaScript objects.

For example, an instruction can contain:

- `opcode`
- `operands`

This representation is natural for JavaScript because object literals provide a compact structure for dynamic records.

---

## JavaScript classes

The `CPU` class owns:

- Registers
- Memory
- Program state
- Flags
- ALU
- Input buffer
- Output buffer
- Cycle counters

The class methods provide controlled access to the machine state.

This prevents unrelated parts of the program from having to manipulate every internal field directly.

---

## JavaScript numeric behavior

JavaScript's normal numeric type is `Number`.

The simulator therefore performs explicit normalization for simulated CPU values.

For the educational architecture, bitwise operations and masks are used to reproduce fixed-width behavior.

The implementation deliberately limits the architecture to 32-bit-or-less words.

This distinction matters because a CPU simulator must define its numeric width explicitly instead of assuming that host-language arithmetic automatically behaves like CPU arithmetic.

---

## JavaScript asynchronous simulation

The JavaScript implementation contains `runAsync()`.

It executes instructions in batches and periodically yields using the Node.js event loop.

This is different from CPU architecture itself.

The CPU model remains sequential, but the host application can periodically give other event-loop work an opportunity to execute.

This pattern is useful when a simulator is embedded in:

- Interactive educational interfaces
- Browser applications
- Monitoring dashboards
- Debugging interfaces
- Long-running simulations

It prevents a large simulation from unnecessarily monopolizing the host JavaScript execution environment.

---

## JavaScript assembler

The assembler performs a label-resolution pass and an instruction-construction pass.

It supports:

- Decimal numbers
- Hexadecimal values
- Binary values
- Register operands
- Labels
- Comments

The use of `Map` for labels provides an efficient mapping from symbolic names to instruction addresses.

---

## JavaScript error handling

The implementation uses JavaScript exceptions for invalid execution conditions.

Examples include:

- Division by zero
- Invalid registers
- Invalid memory addresses
- Stack underflow
- Stack overflow
- Invalid program addresses
- Empty input buffers
- Unknown opcodes

This provides a clear boundary between valid CPU behavior and invalid simulator state.

---

# C++ case study

The C++ implementation develops an industry-style scenario rather than only presenting isolated CPU instructions.

## Problem being modeled

The case study models a simplified industrial sensor controller.

Three sensor values are stored in memory:

- Sensor 1 at address `100`
- Sensor 2 at address `101`
- Sensor 3 at address `102`

The CPU reads the sensors, calculates their aggregate, stores the result, compares it against a threshold, and records a status value.

The result is stored at:

`110`

The status is stored at:

`111`

The threshold is:

`300`

A status value of `1` means that the threshold was reached.

A status value of `0` means that the aggregate was below the threshold.

---

## Case-study execution

The program begins by loading sensor values into registers.

Conceptually:

`LOAD R0, [100]`

`LOAD R1, [101]`

`LOAD R2, [102]`

The CPU then computes:

`R3 = R0 + R1`

followed by:

`R3 = R3 + R2`

The aggregate is stored in memory.

The CPU then loads the threshold into another register and compares the aggregate with the threshold.

This demonstrates a complete path through:

`Memory → Registers → ALU → Registers → Memory → Control Flow`

That is substantially closer to an application-level processor workload than an isolated arithmetic example.

---

## C++ type design

C++ is useful for this case study because the simulated machine state can be represented using explicit fixed-width types.

The simulated word uses:

`std::uint16_t`

This makes the intended 16-bit representation explicit.

The register file uses:

`std::array<Word, REGISTER_COUNT>`

The memory uses:

`std::array<Word, MEMORY_SIZE>`

These structures communicate the fixed architectural limits directly in the type definitions.

---

## C++ operand model

The C++ implementation introduces:

`OperandType`

with:

- `REGISTER`
- `IMMEDIATE`
- `ADDRESS`

An `Operand` stores both its type and numeric value.

This prevents the simulator from treating every operand as the same kind of value.

For example:

`R2`

is a register operand.

`42`

is an immediate operand.

`[100]`

is an address operand.

Explicit operand types make instruction decoding easier to validate.

---

## C++ instruction representation

An `Instruction` contains:

- `Opcode`
- A vector of operands
- Source text

The source text is useful when tracing execution because the simulator can associate internal instructions with human-readable assembly-like descriptions.

---

## C++ ALU design

The C++ `ALU` class contains static operations for:

- Addition
- Subtraction
- Multiplication
- Division
- AND
- OR
- XOR
- NOT
- Left shift
- Right shift

Each operation can update the `Flags` structure.

The ALU is therefore separated from the CPU's instruction dispatch logic.

This mirrors an important architectural idea: the unit that performs arithmetic does not need to own the overall instruction sequence.

---

## C++ validation

The simulator validates:

- Register indices
- Memory addresses
- Program addresses
- Operand counts
- Division operations
- Stack operations
- Program size
- Input availability

Errors are represented with standard C++ exceptions such as:

- `std::out_of_range`
- `std::invalid_argument`
- `std::domain_error`
- `std::runtime_error`
- `std::length_error`

The `main()` function catches `std::exception` so unexpected simulator failures can be reported without uncontrolled termination.

---

## C++ instruction tracing

The C++ CPU provides a tracing mode.

Each instruction can report:

- PC
- Instruction
- Selected register values

Tracing provides a low-level view of the fetch-decode-execute process.

It is particularly useful for studying loops and branch behavior.

---

# Comparison of the three implementations

| Aspect | Python | JavaScript | C++ |
|---|---|---|---|
| CPU state | Dataclasses and classes | Classes and objects | Classes and fixed-width types |
| Instruction representation | Dataclass | Object | Struct/class |
| Opcode representation | Enum | Frozen object | Enum class |
| Memory | List | Array | `std::array` |
| Registers | List | Array | `std::array` |
| Numeric width | Explicit masking | Explicit masking | `std::uint16_t` |
| Assembly | Two-pass assembler | Two-pass assembler | Programmatic construction |
| Error handling | Exceptions | Exceptions | Standard exceptions |
| Tracing | Yes | Yes | Yes |
| Async simulation | No | Yes | No |
| Strong fixed-width typing | Moderate | Low | High |
| Educational flexibility | High | High | High |
| Systems-level modeling | Moderate | Moderate | High |

The same CPU architecture can therefore be implemented in several languages without changing its fundamental concepts.

The differences arise primarily from each language's type system, execution model, and standard programming abstractions.

---

# Advanced concepts

## Instruction set architecture

An Instruction Set Architecture, or ISA, defines the programmer-visible behavior of a processor.

An ISA specifies concepts such as:

- Available instructions
- Registers
- Operand formats
- Addressing modes
- Data widths
- Control-flow behavior
- Exception behavior
- Memory interaction

The simulator represents a small custom ISA.

It is not intended to reproduce x86-64, ARM, RISC-V, or another commercial architecture.

---

## Microarchitecture

ISA describes what the processor exposes.

Microarchitecture describes how a particular processor implements those operations internally.

A modern CPU can include:

- Instruction pipelines
- Multiple execution units
- Cache hierarchies
- Branch predictors
- Register renaming
- Out-of-order execution
- Reorder buffers
- Speculative execution
- SIMD/vector units
- Hardware prefetching
- Multiple cores

The simulator deliberately omits these mechanisms.

The goal is to make the architectural state and instruction cycle explicit.

---

## Pipelining

A pipelined CPU can overlap different stages of multiple instructions.

For example, while one instruction is executing, another may be decoding and another may be fetching.

The simple simulator executes one instruction at a time and therefore does not model pipeline overlap.

A real pipeline also introduces hazards.

Important hazard categories include:

### Data hazards

An instruction depends on the result of an earlier instruction.

### Control hazards

A branch changes the sequence of instructions that would otherwise be fetched.

### Structural hazards

Multiple operations require the same hardware resource simultaneously.

The educational simulator avoids these complexities by executing instructions sequentially.

---

## Branch prediction

Modern CPUs may predict whether a conditional branch will be taken.

The simulator directly evaluates the condition and changes the PC.

It does not model:

- Branch prediction tables
- Speculative execution
- Pipeline flushing
- Misprediction penalties

Therefore the simulator's cycle model is not a performance model for modern processors.

---

## Cache memory

Real processors commonly use several levels of cache.

Typical concepts include:

- L1 cache
- L2 cache
- L3 cache
- Cache lines
- Cache hits
- Cache misses
- Associativity
- Replacement policies

The educational simulator treats memory as a simple uniform array.

Consequently, `LOAD` and `STORE` do not model cache hierarchy or memory latency accurately.

---

## Virtual memory

Modern operating systems commonly provide processes with virtual address spaces.

Virtual addresses can be translated to physical addresses through mechanisms involving page tables and translation lookaside buffers.

The simulator uses direct addresses and does not model:

- Virtual address translation
- Page tables
- TLBs
- Page faults
- Process address spaces
- Memory protection domains

---

## Privilege levels

Production CPUs commonly distinguish privilege levels.

These mechanisms protect operating-system functionality from ordinary application code.

The simulator has no privilege rings or supervisor mode.

A production-quality CPU emulator would need to model privilege restrictions if software depended on them.

---

## Interrupts and exceptions

Real processors respond to external and internal events.

Examples include:

- Hardware interrupts
- Timer interrupts
- Invalid instructions
- Memory faults
- Arithmetic exceptions
- System calls

The educational simulator uses ordinary program execution and exceptions from the host language.

It does not model a hardware interrupt controller or interrupt-vector mechanism.

---

# Performance considerations

## Instruction count

The simulators count executed instructions.

Instruction count provides useful information about algorithmic work, but it does not directly equal execution time.

Different instructions may have different costs.

For example, the educational cycle model treats:

- `ADD` as inexpensive
- `MUL` as more expensive
- `DIV` as substantially more expensive
- Memory operations as more expensive than simple register operations

This is only an approximation.

---

## Algorithmic complexity

The factorial example uses repeated multiplication.

For an input `n`, the number of loop iterations is proportional to `n`.

Its time complexity is:

`O(n)`

The memory requirement is:

`O(1)`

when implemented iteratively using a fixed number of registers.

A CPU simulator can therefore be used not only to study hardware concepts but also to observe how an algorithm translates into instruction-level work.

---

## Simulator performance

The simulator itself introduces overhead that a real CPU does not have.

For example, the software emulator must:

1. Fetch an instruction object.
2. Interpret its opcode.
3. Resolve operand objects.
4. Perform host-language operations.
5. Update simulated state.
6. Repeat the process.

A real processor executes hardware operations directly.

This means simulator execution speed should not be interpreted as actual CPU performance.

---

# Edge cases and exceptions

## Division by zero

`DIV` must reject a zero divisor.

The implementations raise an error instead of producing an undefined CPU state.

## Invalid memory addresses

The memory size is limited.

Any address outside the simulated memory produces an error.

## Invalid registers

Only `R0` through `R7` exist.

An invalid register must be rejected.

## Stack underflow

A `POP` without a corresponding pushed value is invalid.

The simulator detects this condition.

## Stack overflow

A stack cannot grow beyond the available memory.

A simulator must protect its memory model from invalid stack growth.

## Infinite loops

A program such as:

`JMP loop`

can execute forever.

The Python and JavaScript implementations use a maximum instruction count.

The C++ `run()` method also accepts an execution limit.

This is an important simulator safety mechanism.

## Integer overflow

Fixed-width arithmetic can wrap around.

The simulator explicitly normalizes results to the CPU's word width.

Signed overflow is separately tracked through the overflow flag.

---

# Common mistakes

### Confusing PC with IR

The PC identifies the next instruction address.

The IR contains the instruction currently being executed.

They have different roles.

### Treating memory and registers as identical

Registers are part of the processor's immediate execution state.

Memory is the larger storage system accessed by explicit memory operations.

### Assuming all instructions have equal cost

Instruction count and execution cycles are not necessarily equivalent.

Memory, multiplication, division, branches, and other operations can have different hardware costs.

### Ignoring word size

A CPU operates on defined data widths.

An emulator that does not normalize values can behave differently from the processor it models.

### Forgetting that branches change PC

A branch is not simply another arithmetic instruction.

Its most important effect is modifying instruction sequencing.

### Ignoring stack boundaries

Incorrect stack handling can corrupt the simulator's memory state.

### Treating a simulator as a complete real CPU model

The project represents an architectural abstraction.

It does not reproduce the internal microarchitecture of modern commercial processors.

---

# Best practices for CPU simulator design

## Keep CPU state explicit

Registers, memory, PC, IR, SP, and flags should be clearly represented.

This makes debugging and verification easier.

## Separate responsibilities

The ALU should perform arithmetic and logical operations.

The CPU should manage instruction sequencing.

The assembler should translate source instructions.

Keeping these responsibilities separate makes the architecture easier to maintain.

## Validate all externally supplied values

Validate:

- Addresses
- Registers
- Opcodes
- Operands
- Program length
- Execution limits
- Input data

## Make execution deterministic

Given the same initial state and instruction sequence, the simulator should produce the same result.

Determinism is valuable for testing and debugging.

## Provide tracing

Instruction tracing exposes the relationship between:

`PC → instruction → registers → flags → next PC`

This is one of the most useful educational features of a CPU simulator.

## Limit resource consumption

Execution limits prevent accidental infinite loops from consuming unlimited host resources.

Memory and stack boundaries should also be enforced.

---

# Security considerations

A CPU simulator may execute code supplied by another person or system.

Therefore, a production emulator should treat programs as untrusted input.

Important protections include:

- Memory bounds checking
- Instruction-count limits
- Stack bounds checking
- Input validation
- Controlled I/O
- No unrestricted host-system access
- No direct execution of host machine instructions
- Resource quotas
- Isolation when executing untrusted workloads

The simulator in this project does not provide direct operating-system instructions, which helps keep the educational architecture isolated from the host environment.

A more advanced emulator that implements system calls would require a carefully designed security boundary.

---

# Implementation considerations

## Interpreter versus compiled simulation

These implementations are interpreters.

Each instruction is represented as data and dispatched at runtime.

An alternative approach is to compile a simulated instruction sequence into host-language operations.

An interpreter is easier to inspect and debug because each machine instruction remains visible.

A compiled simulator can potentially execute a large instruction stream more efficiently, but it introduces additional implementation complexity.

## Direct versus indirect threading

A basic interpreter can use opcode dispatch through:

- Conditionals
- Switch statements
- Function tables
- Other dispatch mechanisms

The Python implementation primarily uses opcode conditionals.

The JavaScript implementation uses a `switch`.

The C++ implementation also uses a `switch`.

This makes the execution mechanism easy to understand.

## Instruction representation

There are several possible instruction representations.

The project uses structured objects or structs.

An actual processor encodes instructions into binary fields.

A future binary ISA implementation could represent each instruction using fields such as:

- Opcode bits
- Register identifiers
- Immediate values
- Addressing-mode bits

That would move the simulator closer to a machine-code emulator.

---

# Real-world applications of CPU simulators

CPU simulators and emulators have practical uses in areas such as:

- Computer architecture education
- ISA experimentation
- Embedded-system development
- Operating-system research
- Firmware testing
- Debugger development
- Compiler validation
- Hardware verification
- Legacy-system preservation
- Architecture research
- Instruction-set experimentation

The complexity of a simulator depends on its purpose.

An educational simulator can model registers and instructions.

A sophisticated emulator may need to model complete processor architectures, memory-management units, peripheral devices, interrupts, timers, caches, and operating-system interfaces.

---

# Relationship between CPU simulators and compilers

A compiler transforms a high-level program into lower-level instructions.

A CPU simulator can then execute those instructions.

The conceptual pipeline is:

`High-level source`

→

`Compiler`

→

`Assembly`

→

`Machine instructions`

→

`CPU`

A CPU simulator can therefore serve as an experimental target for understanding compiler output and instruction-level execution.

The assembler included in the Python and JavaScript implementations demonstrates the smaller middle portion of this process.

---

# Relationship between CPU simulators and operating systems

Operating systems depend heavily on processor architecture.

Important CPU mechanisms include:

- Registers
- Memory access
- Interrupts
- Privilege levels
- Virtual memory
- System calls
- Context switching
- Exceptions

The simulator models only a subset of these concepts.

Its register and control-flow mechanisms provide a foundation for understanding how higher-level operating-system mechanisms eventually interact with processor hardware.

---

# Relationship between CPU simulators and debugging

A source-level debugger allows a programmer to inspect a program while it executes.

A CPU simulator can expose an even lower level.

Useful debugging information includes:

- Current PC
- Current IR
- Register contents
- Memory contents
- Stack contents
- Flags
- Instruction count
- Branch targets
- Output state

This makes it possible to identify the exact instruction that produced an unexpected state transition.

---

# Architecture limitations

This project intentionally simplifies several parts of real CPU design.

It does not accurately model:

- Modern pipelines
- Superscalar execution
- Out-of-order execution
- Register renaming
- SIMD
- Vector processing
- Cache hierarchy
- Branch prediction
- Speculative execution
- Virtual memory
- Hardware interrupts
- DMA
- Multicore execution
- Cache coherence
- Memory ordering
- Privilege levels
- Device buses
- Hardware timers
- Real machine-code encoding

The simplified architecture is valuable because it isolates the fundamental relationships among instructions, registers, memory, the ALU, control flow, and CPU state.

---

# Files

A practical repository layout can contain:

`cpu_simulator.py`

The Python educational emulator.

`cpu_simulator.js`

The JavaScript implementation.

`cpu_simulator.cpp`

The C++ industry-style case study.

`README.md`

This technical documentation.

---

# Execution

The Python implementation requires Python 3.9 or later because it uses modern type annotations and standard-library dataclasses.

The JavaScript implementation can run in a modern Node.js environment.

The C++ implementation requires a compiler supporting C++17 or later.

The C++ program can be compiled with:

`g++ -std=c++17 -O2 cpu_simulator.cpp -o cpu_simulator`

The resulting executable runs the CPU examples and the industrial sensor-controller case study.

---

# Educational significance

The central purpose of a CPU simulator is to make processor execution observable.

Instead of treating a program as a high-level sequence such as:

`calculate_total()`

the simulator exposes the lower-level operations required to accomplish the task:

- Move values into registers
- Load values from memory
- Perform ALU operations
- Update flags
- Compare results
- Change the PC
- Store results
- Use the stack
- Return from procedures
- Halt execution

This provides a direct connection between software instructions and processor state.

The three implementations demonstrate that the fundamental architecture remains the same even when the implementation language changes.

Python emphasizes clarity and experimentation.

JavaScript emphasizes structured application behavior and asynchronous execution.

C++ emphasizes explicit machine representation, fixed-width data, strong types, and systems-oriented implementation.

Together, the implementations provide a complete working model of the fundamental CPU execution process while maintaining a deliberate distinction between an educational architecture and the substantially more complex microarchitecture of modern processors.
