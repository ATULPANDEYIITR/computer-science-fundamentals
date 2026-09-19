# Assembly Language Basics

## Topic

Assembly Language Basics with emphasis on registers, instructions, labels, memory operations, arithmetic instructions, and practical use of MARS and RARS.

This study material uses MIPS-style assembly because MARS and RARS are educational simulators designed around the MIPS architecture and its instructional model. The accompanying Python and JavaScript programs implement a small MIPS-like interpreter, while the C++ program develops the same ideas into a realistic low-level data-processing case study.

The implementations deliberately focus on fundamental machine behavior rather than reproducing every instruction, pseudo-instruction, assembler directive, or simulator-specific system call.

## Introduction to assembly language

Assembly language is a low-level programming language that represents processor instructions with human-readable mnemonics.

A high-level statement such as:

`total = total + value`

hides several machine-level operations. At the assembly level, the programmer may need to load a value from memory, place it in a register, perform an arithmetic operation, and store the result.

A simplified sequence might look like:

`lw $t0, 0($a0)`

`add $t1, $t1, $t0`

`sw $t1, 0($a0)`

The exact machine instructions depend on the processor architecture.

Assembly language therefore exposes concepts that are usually hidden by languages such as Python, JavaScript, Java, or C++:

- registers
- memory addresses
- instruction encoding
- program counters
- branches
- jumps
- calling conventions
- stack frames
- integer representation
- alignment
- signed and unsigned arithmetic
- explicit data movement

## Why MIPS is useful for learning

MIPS has historically been used for computer architecture education because its instruction model is comparatively regular.

A basic MIPS-style instruction commonly has a small number of operands, such as:

`add $t0, $t1, $t2`

The instruction means that the processor should add the values in `$t1` and `$t2` and place the result in `$t0`.

The notation is compact enough to expose the relationship between source operands, destination operands, registers, and control flow.

MARS and RARS provide visual environments in which students can write MIPS-style assembly, assemble it, execute it step by step, inspect registers, inspect memory, and observe program execution.

## Core terminology

### Instruction

An instruction is an operation understood by the processor.

Examples include:

`add`

`sub`

`lw`

`sw`

`beq`

`j`

The instruction mnemonic represents the operation in assembly source code.

### Opcode

The opcode identifies the operation represented by an instruction.

For example, `add` identifies an addition operation.

At the machine-code level, instructions contain binary fields representing the operation and its operands.

### Operand

An operand identifies data used by an instruction.

For example:

`add $t0, $t1, $t2`

contains three register operands:

- `$t0`
- `$t1`
- `$t2`

### Register

A register is a small storage location directly accessible to the processor.

Registers are much closer to the arithmetic and control logic of a CPU than ordinary memory.

A typical 32-bit MIPS implementation has 32 general-purpose registers, each capable of holding a 32-bit value.

### Memory

Memory stores program data and instructions at addresses.

Unlike a register, memory is addressed using an address value.

For example:

`lw $t0, 8($sp)`

calculates an effective address using `$sp + 8` and loads a word from that location into `$t0`.

### Address

An address identifies a location in memory.

For a 32-bit integer array, consecutive elements normally occupy consecutive four-byte regions.

If the first integer begins at address `1000`, the next integers begin at:

`1004`

`1008`

`1012`

The four-byte spacing comes from the size of a 32-bit word.

### Label

A label is a symbolic name associated with an instruction address.

Example:

`loop:`

A branch can then refer to the label:

`bne $t0, $t1, loop`

The assembler resolves the symbolic label into the appropriate address or branch displacement.

### Program counter

The program counter, commonly called the PC, identifies the next instruction to execute.

Sequential instructions normally cause the PC to move to the next instruction.

Branches and jumps modify this normal control flow.

### Immediate

An immediate is a constant embedded directly in an instruction.

Example:

`addi $t0, $t1, 4`

The value `4` is an immediate operand.

### Word

In the MIPS educational environment, a word is commonly 32 bits, or four bytes.

Many fundamental MIPS instructions operate on words.

## Registers

MIPS provides 32 general-purpose registers.

Common register conventions include:

| Register | Typical role |
|---|---|
| `$zero` | Always contains zero |
| `$at` | Assembler temporary |
| `$v0-$v1` | Function return values |
| `$a0-$a3` | Function arguments |
| `$t0-$t9` | Temporary registers |
| `$s0-$s7` | Saved registers |
| `$k0-$k1` | Kernel-related registers |
| `$gp` | Global pointer |
| `$sp` | Stack pointer |
| `$fp` | Frame pointer |
| `$ra` | Return address |

These roles are conventions associated with common MIPS programming practice. They are not all independent hardware mechanisms.

### `$zero`

The `$zero` register always reads as zero.

A write such as:

`li $zero, 100`

does not make `$zero` contain 100.

The Python, JavaScript, and C++ implementations explicitly preserve this invariant.

### Temporary registers

Registers such as `$t0` through `$t9` are commonly used for intermediate calculations.

A programmer should not assume that a temporary register automatically preserves its value across a procedure call.

### Saved registers

Registers such as `$s0` through `$s7` are conventionally used for values that a called procedure is expected to preserve according to the applicable calling convention.

### Argument registers

`$a0` through `$a3` are commonly used for the first four arguments of a procedure.

Additional arguments may use the stack or other convention-defined mechanisms.

### Return-value registers

`$v0` and `$v1` are commonly used to return values from procedures.

## Arithmetic instructions

### Addition

A basic register addition is:

`add $t0, $t1, $t2`

Conceptually:

`$t0 = $t1 + $t2`

The Python simulator implements signed overflow detection for this instruction.

The C++ simulator also explicitly checks the mathematical result against the signed 32-bit range.

### Unsigned addition

`addu $t0, $t1, $t2`

is commonly used when unsigned wrapping behavior is appropriate.

A 32-bit value that exceeds the representable range wraps around modulo `2^32`.

### Subtraction

`sub $t0, $t1, $t2`

means:

`$t0 = $t1 - $t2`

Signed overflow is a relevant edge case.

### Multiplication

The `mul` instruction provides integer multiplication in common MIPS environments.

The exact multiplication instructions available can depend on the architecture level and simulator.

Historically, MIPS also exposes multiplication through the special `HI` and `LO` registers for certain multiply instructions.

The educational simulators in this project use the simpler `mul` form.

### Immediate arithmetic

`addi $t0, $t1, 10`

adds a constant to a register.

The immediate field is limited in size. A common MIPS immediate field is 16 bits, so an immediate is sign-extended when interpreted as a signed value.

The Python, JavaScript, and C++ implementations demonstrate this sign-extension behavior.

## Signed and unsigned integers

A 32-bit register stores a bit pattern.

That bit pattern can be interpreted as signed or unsigned.

For example:

`0xFFFFFFFF`

represents:

`4294967295` as an unsigned 32-bit value

and:

`-1` as a signed two's-complement value.

The bit pattern itself does not contain a separate "signed" flag.

The instruction being executed determines how the processor interprets the value.

## Two's-complement representation

Signed negative integers are normally represented using two's complement.

For a 32-bit integer:

`-1 = 0xFFFFFFFF`

`-2 = 0xFFFFFFFE`

`-3 = 0xFFFFFFFD`

The highest bit acts as the sign bit when the value is interpreted as signed.

The Python implementation provides `u32` and `s32` helper functions to make this distinction explicit.

The JavaScript implementation uses `Int32Array`, bitwise operations, and explicit unsigned conversions because JavaScript's ordinary `Number` type is not itself a 32-bit integer type.

The C++ implementation uses fixed-width integer types such as `std::int32_t` and `std::uint32_t`.

## Immediate versus register operands

Compare:

`add $t0, $t1, $t2`

with:

`addi $t0, $t1, 5`

The first obtains both arithmetic operands from registers.

The second obtains one operand from a register and the other from an instruction-encoded constant.

This distinction is important because instructions have fixed encoding formats and limited immediate fields.

## Logical instructions

MIPS provides bitwise operations such as:

`and`

`or`

`xor`

These operate on individual bits.

For example:

`and $t0, $t1, $t2`

sets each result bit according to the corresponding bits of the two source operands.

Bitwise operations are useful for:

- masks
- flags
- packed data
- permissions
- device registers
- protocol fields
- low-level algorithms

## Shift instructions

### Logical left shift

` sll $t0, $t1, 4`

moves the bits of `$t1` four positions to the left.

A left shift by four is closely related to multiplication by 16 when overflow and signed interpretation are not problematic.

### Logical right shift

` srl $t0, $t1, 4`

moves bits toward the least significant position and inserts zero bits from the left.

Shifts are frequently used for bit fields, address calculations, masks, and efficient arithmetic.

## Comparison

The `slt` instruction means "set on less than."

Example:

`slt $t0, $t1, $t2`

sets `$t0` to:

`1` if `$t1 < $t2`

or:

`0` otherwise.

This is important because assembly languages generally do not have the same high-level boolean expression syntax found in languages such as Python or JavaScript.

A comparison often produces a register value that is then consumed by a branch instruction.

## Memory operations

### Load word

`lw $t0, 8($sp)`

loads a 32-bit word from memory.

The effective address is:

`$sp + 8`

The value at that address becomes the value of `$t0`.

### Store word

`sw $t0, 8($sp)`

stores the value of `$t0` into memory at:

`$sp + 8`

### Base-plus-offset addressing

The syntax:

`offset(base)`

is fundamental to MIPS memory access.

For:

`lw $t0, 12($s0)`

the processor calculates:

`address = $s0 + 12`

and loads a word from that address.

This addressing style is particularly useful for arrays and structures.

## Arrays in assembly

An array is not a special hardware object.

An array is a region of memory containing elements at predictable addresses.

For a 32-bit integer array:

`address_of_element_i = base_address + i * 4`

For example, if the base is `0x10010000`:

| Element | Address |
|---|---|
| `numbers[0]` | `0x10010000` |
| `numbers[1]` | `0x10010004` |
| `numbers[2]` | `0x10010008` |
| `numbers[3]` | `0x1001000C` |

The Python, JavaScript, and C++ implementations explicitly demonstrate this relationship.

## Alignment

A word normally occupies four bytes.

A word address is therefore expected to be aligned to a four-byte boundary in the simplified memory model.

An address such as:

`0x10010004`

is aligned.

An address such as:

`0x10010005`

is not aligned for a four-byte word.

The implementations reject unaligned word operations.

Actual hardware behavior depends on the architecture and specific instruction, and some systems may handle unaligned access differently.

## Labels and control flow

Assembly programs need a mechanism to represent destinations for branches and jumps.

A label provides a symbolic destination.

Example:

`loop:`

`add $t0, $t0, $t1`

`addi $t1, $t1, -1`

`bne $t1, $zero, loop`

The assembler resolves `loop` to the corresponding instruction location.

The Python, JavaScript, and C++ interpreters maintain a label-to-instruction-index mapping.

## Conditional branches

Two fundamental branch instructions are:

`beq`

and:

`bne`

Example:

`beq $t0, $t1, equal`

means that execution transfers to `equal` when the two registers contain equal values.

Example:

`bne $t0, $zero, loop`

means that execution transfers to `loop` when `$t0` is not zero.

Branches provide the low-level foundation for:

- `if`
- `while`
- `for`
- conditional processing
- repeated algorithms

## Loops

A high-level loop:

`while (count != 0)`

can be represented using:

`loop:`

`...`

`addi $t1, $t1, -1`

`bne $t1, $zero, loop`

The programmer explicitly controls:

- the loop counter
- the condition
- the update
- the branch target

The Python program demonstrates a sum loop.

The JavaScript program demonstrates the same basic control-flow mechanism.

The C++ case study uses a loop to process sensor measurements.

## Jumps

The `j` instruction transfers execution directly to a label.

Example:

`j program_end`

Jumps are useful for unconditional control flow.

They are also commonly used with conditional branches to implement high-level structures.

## Procedure calls

The instruction:

`jal function`

means "jump and link."

It transfers execution to the function and records a return address in `$ra`.

A procedure can return using:

`jr $ra`

A simplified call sequence is:

`jal function`

followed by execution inside the function.

The function eventually executes:

`jr $ra`

The Python and JavaScript examples implement a small square function.

The C++ simulator includes the same underlying mechanism in its instruction interpreter.

## The stack

The stack is a memory region commonly used for:

- saved registers
- return information
- local variables
- temporary data
- procedure-call state

The stack pointer is held in `$sp`.

A procedure may reserve stack space and save registers there.

A simplified example is:

`sw $ra, 0($sp)`

followed later by:

`lw $ra, 0($sp)`

The exact stack-frame layout depends on the calling convention and compiler or programmer.

## Calling conventions

A calling convention defines how procedures communicate.

Important questions include:

- Where are arguments stored?
- Where are return values stored?
- Which registers must a function preserve?
- Where is the return address stored?
- How is stack space managed?

Common MIPS conventions use:

- `$a0-$a3` for initial arguments
- `$v0-$v1` for return values
- `$ra` for the return address
- `$sp` for stack management
- `$t` registers for temporary values
- `$s` registers for values that must be preserved according to convention

Calling conventions allow separately written procedures to interact predictably.

## Pseudo-instructions

MARS and RARS support pseudo-instructions that make assembly programming easier.

For example, programmers commonly encounter:

`li`

`move`

These may be translated by the assembler into one or more actual machine instructions depending on the value and architecture.

This distinction is important:

- an assembly mnemonic may be a real instruction
- or it may be an assembler convenience that expands into another sequence

The educational interpreters treat selected pseudo-instructions as direct operations to keep the machine model readable.

## MARS and RARS

MARS and RARS provide interactive environments for writing and executing MIPS-style assembly.

Typical workflow:

1. Create an assembly source file.
2. Write instructions and labels.
3. Assemble the program.
4. Resolve syntax or assembly errors.
5. Run the program.
6. Step through instructions when debugging.
7. Inspect registers.
8. Inspect memory.
9. Observe program output.

The user interface and exact supported features can vary between versions.

## MARS versus RARS

Both tools are educational MIPS simulators, but they are not identical.

RARS is a modern educational environment commonly used for RISC-V and also associated with MIPS-oriented educational workflows depending on the version and configuration.

MARS is specifically well known as a Java-based MIPS simulator.

When working with a course or assignment, the instruction set, system-call numbers, pseudo-instructions, and simulator configuration specified by that course should take precedence over assumptions based on another simulator.

The central concepts demonstrated by both environments remain:

- registers
- instructions
- addresses
- memory
- labels
- branches
- procedure calls
- stack operations
- arithmetic

## Python implementation

The Python implementation defines four major components.

### RegisterFile

`RegisterFile` represents the processor's general-purpose registers.

Its `read` and `write` methods provide controlled access to registers.

The implementation specifically protects `$zero`.

This makes an architectural rule visible in ordinary Python code.

### Memory

`Memory` provides sparse byte-addressable storage.

It implements:

- `store_byte`
- `load_byte`
- `store_word`
- `load_word`

The implementation also checks word alignment.

### Instruction

`Instruction` stores:

- an opcode
- operands
- original source representation

This creates a simple internal representation of assembly instructions.

### MiniMIPS

`MiniMIPS` combines:

- registers
- memory
- program instructions
- labels
- program counter
- execution state

Its `step()` method executes one instruction.

Its `run()` method repeatedly executes instructions until the program ends or an execution limit is reached.

This structure resembles an interpreter.

## Python arithmetic example

The Python program demonstrates:

`li $t0, 25`

`li $t1, 17`

`add $t2, $t0, $t1`

`sub $t3, $t0, $t1`

`mul $t4, $t2, $t3`

The resulting register values can be inspected with the register dump.

The example demonstrates that arithmetic occurs through explicit register operands.

## Python memory example

The Python program places:

`10, 20, 30, 40`

into consecutive memory words.

It then calculates the address of the third element using:

`base + 8`

because element index 2 requires:

`2 * 4 = 8`

bytes of offset.

The program loads the value, adds five, and stores it back.

This demonstrates the relationship among:

- arrays
- addresses
- offsets
- registers
- `lw`
- `sw`

## Python loop example

The loop calculates:

`1 + 2 + 3 + 4 + 5`

The program uses registers for:

- current number
- accumulated sum
- loop limit
- comparison value

The branch instruction sends execution back to the `loop` label until the condition becomes false.

This demonstrates how a high-level loop is reduced to explicit machine-level state transitions.

## Python procedure example

The procedure example models:

`square_plus_one(x)`

The calling code places the argument in `$a0`.

It calls the function using `jal`.

The function calculates the result in registers and places the return value in `$v0`.

The return address is preserved through memory and restored before `jr $ra`.

This provides a concrete introduction to procedure-call mechanics.

## Python overflow example

The program tests:

`2147483647 + 1`

for signed 32-bit arithmetic.

This is outside the signed 32-bit range.

The educational implementation raises an exception for signed `add`.

The unsigned-style operation demonstrates 32-bit wrapping behavior.

This distinction is important because a register contains bits, while the instruction determines how those bits are interpreted.

## Python bitwise example

The program demonstrates:

- `and`
- `or`
- `xor`
- `sll`
- `srl`

These operations show how assembly can manipulate individual bits rather than only high-level numeric values.

## JavaScript implementation

The JavaScript implementation complements the Python implementation by using JavaScript's object and typed-array facilities to model the machine.

### Register representation

`RegisterFile` uses:

`Int32Array(32)`

This is particularly useful because JavaScript's ordinary `Number` type is a floating-point numeric type, whereas an assembly register has fixed-width integer semantics.

The implementation therefore uses:

- `Int32Array`
- `>>> 0`
- `| 0`
- explicit range checks

to make 32-bit behavior visible.

### JavaScript memory representation

The `Memory` class uses a `Map`.

Only addresses that have actually been written need to be stored.

This makes the educational memory model sparse rather than allocating a complete simulated address space.

### JavaScript instruction execution

`MiniMIPS.step()` uses a `switch` statement.

Each opcode selects the corresponding implementation.

For example:

`lw`

calls the memory model.

`add`

performs checked signed arithmetic.

`beq`

examines registers and potentially modifies the PC.

`jal`

writes the return address to `$ra`.

This is a direct illustration of an interpreter dispatch loop.

## JavaScript-specific considerations

JavaScript does not naturally behave like a 32-bit integer-only language.

The `Number` type normally uses IEEE 754 double-precision floating-point representation.

Bitwise operators convert operands to 32-bit signed integer representations for the operation.

The implementation therefore performs explicit conversions when modeling a 32-bit CPU.

This is a significant distinction from C++ using `std::int32_t` and from Python, where arbitrary-precision integers are the default.

## C++ implementation

The C++ program develops the same ideas into a larger technical case study.

The simulated machine contains:

- 32 registers
- sparse memory
- instructions
- labels
- a program counter
- arithmetic operations
- branch instructions
- jump instructions
- procedure-call primitives

The program is compiled using C++17 or a later standard.

## C++ register representation

The register file uses:

`std::array<UWord, REGISTER_COUNT>`

This provides a fixed-size storage structure corresponding closely to the fixed number of general-purpose registers.

The implementation separates:

`std::int32_t`

from:

`std::uint32_t`

to make signed and unsigned interpretations explicit.

## C++ memory representation

The memory system uses:

`std::map<Address, std::uint8_t>`

This represents memory as individually addressable bytes.

Four bytes are combined to form a word.

This is important because an integer is not inherently stored as a single indivisible physical object at the memory level.

The memory implementation also checks word alignment.

## C++ instruction representation

The `Instruction` structure contains:

- opcode
- operand list
- source representation

This allows the CPU to execute structured instructions while retaining readable assembly text for tracing.

## C++ program counter

The CPU stores the current instruction position in `pc`.

Normal execution performs:

`pc = pc + 1`

Branches and jumps replace that sequential destination.

This is the essential mechanism behind program control flow.

## C++ case study

The C++ case study models a sensor analytics routine.

The input consists of signed measurements such as:

`12, 27, -5, 31, 18, 42, 7, 24`

The simulated assembly routine calculates:

- total
- maximum
- minimum
- number of measurements above 20

The problem is deliberately chosen to require memory access, pointer arithmetic, comparisons, branches, counters, and multiple result registers.

## Case-study register allocation

The C++ case study assigns roles to registers:

| Register | Purpose |
|---|---|
| `$t0` | Current array pointer |
| `$t1` | Remaining element count |
| `$t2` | Running sum |
| `$t3` | Current measurement |
| `$t4` | Maximum |
| `$t5` | Minimum |
| `$t6` | Threshold |
| `$t7` | Count above threshold |
| `$t8` | Comparison result |
| `$t9` | Zero |
| `$v0` | Final sum |
| `$v1` | Final maximum |
| `$s0` | Final minimum |
| `$s1` | Threshold count |

This is an example of manual register allocation.

A compiler performs this kind of allocation automatically when translating a higher-level language into machine code.

## Case-study array traversal

The array is stored in consecutive memory words.

The pointer begins at the first element.

After processing an integer, the program executes:

`addi $t0, $t0, 4`

The four-byte increment is required because each element is a 32-bit word.

The count register is decremented using:

`addi $t1, $t1, -1`

The loop continues using:

`bne $t1, $t9, loop`

This creates a complete low-level traversal without a high-level `for` construct.

## Case-study maximum calculation

The maximum operation uses:

`slt $t8, $t4, $t3`

This asks whether:

`maximum < current`

If the result is one, the maximum register is updated.

A branch decides whether the assignment is necessary.

This shows how a high-level comparison and assignment are converted into several low-level operations.

## Case-study minimum calculation

The minimum operation reverses the comparison:

`slt $t8, $t3, $t5`

This asks whether:

`current < minimum`

If true, the current value replaces the minimum.

## Threshold counting

The program uses the threshold stored in `$t6`.

The comparison:

`slt $t8, $t6, $t3`

tests whether:

`threshold < current`

When true, `$t7` is incremented.

This demonstrates how a conditional counter can be implemented with a comparison, branch, and immediate addition.

## Validation

The C++ case study independently calculates the expected results using ordinary C++.

The assembly-simulation results are then compared with those expected results.

This is an important engineering technique because an interpreter can contain errors even when the test input appears correct.

The validation checks:

- sum
- maximum
- minimum
- threshold count

## Error handling

The implementations demonstrate several failure conditions.

### Unknown register

An invalid register name raises an exception.

### Invalid memory operand

Malformed expressions such as an invalid base-plus-offset form are rejected.

### Unaligned word access

Word accesses at addresses that are not four-byte aligned are rejected.

### Unknown label

Branches and jumps referencing undefined labels produce an error.

### Unsupported opcode

The interpreter reports an instruction that it does not implement.

### Signed overflow

The educational `add` and `sub` implementations detect signed overflow.

### Infinite execution

The interpreters impose a maximum instruction count.

This prevents a programming mistake such as:

`loop:`

`j loop`

from causing the educational program to execute indefinitely.

## Common mistakes

### Confusing registers with memory

A register is not a memory address.

For example:

`add $t0, $t1, $t2`

does not access ordinary memory.

By contrast:

`lw $t0, 0($t1)`

uses `$t1` as part of an address calculation.

### Forgetting word size

For a 32-bit integer array, the next element is normally four bytes away.

Using an offset of one byte instead of four bytes produces an incorrect address.

### Writing to `$zero`

Writing to `$zero` has no persistent effect.

### Incorrect branch condition

Assembly branches compare explicit operands.

A reversed comparison can cause a loop to execute the wrong number of times.

### Incorrect label placement

A branch destination must correspond to the intended instruction address.

### Forgetting to preserve required registers

Procedure code must respect the applicable calling convention.

### Losing the return address

A nested procedure call can overwrite `$ra`.

A procedure that needs to preserve its return address must save it according to the calling convention.

### Assuming all assembly mnemonics are real machine instructions

Some mnemonics are pseudo-instructions.

The assembler may translate them into one or more actual instructions.

### Ignoring signedness

The same 32-bit bit pattern can represent very different signed and unsigned values.

### Ignoring alignment

A word access should use an appropriate word-aligned address in the simplified model.

## Edge cases

Important edge cases include:

- zero-length arrays
- arrays containing only negative values
- arrays containing one element
- maximum signed integer
- minimum signed integer
- arithmetic overflow
- zero loop counts
- negative immediate values
- unaligned addresses
- unknown labels
- invalid registers
- infinite loops
- branch conditions that are always true
- branch conditions that are never true

The C++ case study explicitly rejects an empty sensor array because maximum and minimum require an initial element.

## Exceptions and overflow

A 32-bit signed integer ranges from:

`-2147483648`

through:

`2147483647`

Attempting to represent a larger signed result requires behavior defined by the particular instruction and architecture.

The educational implementations distinguish signed arithmetic from wrapping unsigned-style arithmetic.

This distinction prevents the common mistake of assuming that all integer operations automatically behave identically.

## Performance considerations

Assembly language exposes performance-relevant operations more directly than high-level languages.

Important considerations include:

- number of instructions executed
- memory accesses
- register reuse
- branch frequency
- arithmetic operations
- instruction dependencies
- cache behavior on real hardware
- pipeline behavior
- branch prediction
- alignment

The simulators in this project do not model modern processor pipelines, caches, branch predictors, superscalar execution, or out-of-order execution.

Consequently, their execution count should not be interpreted as a direct measurement of real CPU performance.

## Algorithmic complexity of the case study

The sensor analytics routine visits every input element once.

For `n` measurements:

- time complexity: `O(n)`
- extra algorithmic storage: `O(1)`

The input array itself requires `O(n)` memory.

The calculation maintains only a fixed number of registers for the running results.

This is a useful example of a streaming algorithm.

## Memory complexity

Each 32-bit measurement requires four bytes.

For `n` measurements:

`memory = 4n bytes`

in the simplified data representation.

The simulator's sparse memory model stores only initialized addresses, but the logical array still represents a contiguous sequence of word-sized elements.

## Python versus JavaScript

The Python implementation emphasizes readability and explicit modeling.

Python's arbitrary-precision integers make it necessary to deliberately constrain values to 32 bits when simulating a 32-bit CPU.

The JavaScript implementation has a different issue.

JavaScript's ordinary numeric type is a double-precision floating-point `Number`, so typed arrays and explicit conversions are useful for representing CPU-style integer behavior.

The two implementations therefore demonstrate the same machine concepts while exposing different host-language numeric models.

## Python versus C++

Python is concise and convenient for building an interpreter.

C++ provides fixed-width integer types, explicit memory-oriented structures, and lower-level control over representation.

The C++ case study therefore provides a closer conceptual connection to systems programming concerns.

The Python program is easier to inspect and modify.

The C++ implementation makes data representation and type boundaries more explicit.

## JavaScript versus C++

JavaScript is convenient for implementing a simulator that could later be connected to a browser interface.

C++ provides strong static typing and direct access to low-level data structures.

The JavaScript program demonstrates how an interpreter can be implemented with objects, maps, typed arrays, and a `switch` dispatcher.

The C++ program demonstrates a more systems-oriented implementation using fixed-width integers, standard containers, exceptions, and explicit memory representation.

## Security considerations

Assembly programming requires careful treatment of memory and control flow.

Important security concepts include:

- invalid memory access
- buffer overflows
- stack corruption
- incorrect pointer arithmetic
- corrupted return addresses
- integer overflow
- unintended control-flow changes
- privilege boundaries

The simplified educational simulators do not reproduce a complete operating-system memory-protection model.

Real systems can include:

- virtual memory
- page permissions
- user/kernel privilege levels
- stack protections
- address-space randomization
- executable-memory restrictions
- hardware security features

The educational implementations should therefore be viewed as conceptual models rather than security-complete CPU emulators.

## Debugging assembly programs

Assembly debugging benefits from observing machine state directly.

Useful state includes:

- current PC
- current instruction
- register contents
- relevant memory addresses
- branch decisions
- stack contents
- return address

The Python and JavaScript interpreters include optional tracing.

The C++ interpreter also supports instruction tracing through `setTrace`.

A useful debugging method is to execute one instruction at a time and verify the expected change in machine state.

## Trace-based debugging

For a loop, a useful trace might conceptually show:

`PC -> instruction -> register state -> next PC`

This helps identify:

- incorrect branches
- counters that never reach zero
- pointers that advance incorrectly
- values loaded from the wrong offset
- overwritten registers

Tracing is often more informative in assembly than immediately examining only the final output.

## Design considerations in the implementations

The three implementations separate the machine into logical components.

The primary components are:

- register file
- memory
- instruction representation
- program
- label table
- program counter
- execution engine

This separation makes the simulator easier to reason about.

For example, memory behavior can be tested without executing a complete program.

Register behavior can also be tested independently.

This is an example of modular design applied to a low-level systems model.

## Limitations of the implementations

These programs intentionally do not attempt to implement the complete MARS or RARS environment.

They do not reproduce every feature such as:

- the complete MIPS instruction set
- every pseudo-instruction
- assembler directives
- floating-point coprocessor behavior
- complete exception processing
- complete operating-system interaction
- all system calls
- memory-mapped I/O
- instruction encoding and binary assembly
- pipeline simulation
- cache simulation
- branch prediction
- virtual memory
- privilege levels

The purpose is to expose the fundamental mechanisms in a compact executable form.

## Real-world relevance

Assembly concepts remain relevant in areas where understanding machine behavior matters.

Examples include:

- operating systems
- embedded systems
- firmware
- compilers
- reverse engineering
- cybersecurity
- digital forensics
- device drivers
- performance engineering
- computer architecture
- processor design
- debugging
- binary analysis

Most application software is written in higher-level languages, but those languages ultimately depend on machine instructions and memory operations.

Understanding registers, instructions, addresses, branches, and procedure calls therefore provides a foundation for understanding how software is executed.

## Conceptual mapping from high-level code to assembly

Consider the high-level idea:

`sum = sum + value`

The low-level implementation may require:

`lw $t0, 0($a0)`

`add $t1, $t1, $t0`

The first instruction retrieves data from memory.

The second performs the arithmetic operation.

A high-level language hides these details through its compiler or interpreter.

Assembly exposes them.

## Conceptual mapping for an if statement

A high-level statement such as:

`if (value > threshold) count += 1`

can be represented by:

`slt $t0, $threshold, $value`

`beq $t0, $zero, skip`

`addi $count, $count, 1`

`skip:`

The comparison produces a Boolean-like integer value.

The branch determines whether the update occurs.

This demonstrates the low-level structure underlying conditional logic.

## Conceptual mapping for a loop

A high-level loop:

`while (count != 0)`

can be represented by:

`loop:`

`...`

`addi $count, $count, -1`

`bne $count, $zero, loop`

The loop is therefore constructed from ordinary instructions rather than being a special high-level object.

## Relationship between labels and addresses

A label is convenient for the programmer, but the processor ultimately operates using addresses or instruction locations.

The assembler performs symbolic resolution.

For example:

`loop:`

can become an instruction address.

A branch referring to `loop` is then encoded according to the instruction's branch format.

The Python, JavaScript, and C++ programs simplify this process by mapping label strings directly to instruction indices.

## Why explicit memory operations matter

High-level languages commonly make memory management and data movement less visible.

Assembly makes these operations explicit.

When executing:

`lw $t0, 8($sp)`

the processor must:

1. read the base register
2. sign-extend or otherwise interpret the offset
3. calculate the effective address
4. access memory
5. retrieve the word
6. place the result in the destination register

Similarly, `sw` performs the reverse direction.

Understanding these steps is essential for reasoning about pointers, arrays, structures, stacks, and low-level data structures.

## Instruction execution model

A simplified processor repeatedly performs a cycle resembling:

1. Fetch an instruction.
2. Decode its operation and operands.
3. Read required registers.
4. Perform an arithmetic, logical, memory, or control operation.
5. Write results where required.
6. Determine the next PC.

Real processors implement this through complex hardware pipelines and additional mechanisms.

The `MiniMIPS` classes in the three implementations reduce this to an educational interpreter loop.

## Testing strategy

The programs include tests for:

- register reads and writes
- `$zero` behavior
- memory round trips
- arithmetic
- branching
- overflow
- alignment

The C++ program also validates the complete sensor-analysis result against independently calculated expected values.

Testing is particularly important for an interpreter because an error in instruction semantics can produce incorrect results across many programs.

## Practical study sequence

A useful conceptual progression through these implementations is:

1. Understand the register file.
2. Examine `li`.
3. Examine `add`, `sub`, and `mul`.
4. Examine immediate arithmetic.
5. Examine `lw` and `sw`.
6. Understand base-plus-offset addressing.
7. Examine labels.
8. Trace a branch.
9. Trace a loop.
10. Examine `jal` and `jr`.
11. Examine stack storage.
12. Study signed and unsigned behavior.
13. Study bitwise operations.
14. Examine the complete C++ case study.

This sequence follows the increasing complexity of the machine model.

## Key distinctions

| Concept | Meaning |
|---|---|
| Register | Small processor storage location |
| Memory | Addressable storage outside the register file |
| Immediate | Constant encoded in an instruction |
| Label | Symbolic name for an instruction location |
| Address | Identifier of a memory location |
| PC | Location of the next instruction |
| Opcode | Operation represented by an instruction |
| Branch | Conditional control-flow transfer |
| Jump | Direct control-flow transfer |
| `lw` | Load a word from memory |
| `sw` | Store a word to memory |
| `jal` | Jump and save return address |
| `jr` | Jump to an address stored in a register |
| `$sp` | Stack pointer |
| `$ra` | Return address register |

## Files and their roles

The Python file is a compact educational MIPS interpreter with examples covering arithmetic, memory, labels, loops, procedures, overflow, bit operations, and arrays.

The JavaScript file implements a similar interpreter while emphasizing JavaScript's typed arrays, maps, object-oriented structure, and explicit 32-bit numeric conversion.

The C++ file implements the most detailed case study. It includes a register file, memory subsystem, instruction interpreter, tests, overflow checks, branch handling, and a sensor analytics workload.

The three implementations therefore demonstrate the same architectural principles through different programming-language mechanisms.

## Implementation boundaries

The Python, JavaScript, and C++ interpreters model a small educational instruction subset.

The supported conceptual operations include:

`li`

`move`

`add`

`addu`

`sub`

`mul`

`addi`

`addiu`

`and`

`or`

`xor`

`sll`

`srl`

`slt`

`lw`

`sw`

`beq`

`bne`

`j`

`jal`

`jr`

`nop`

This subset is sufficient to demonstrate a substantial portion of the basic concepts associated with introductory MIPS assembly programming.

## Relationship to MARS and RARS

The source code in this project is not intended to be copied directly as a MARS or RARS program.

Instead, it provides an executable conceptual model of mechanisms encountered when writing MIPS-style assembly in those environments.

When using MARS or RARS, the simulator itself performs instruction decoding, register updates, memory access, label resolution, and control-flow handling.

The Python, JavaScript, and C++ programs reproduce simplified versions of those mechanisms so that the underlying concepts can be studied programmatically.

## Important architectural lesson

Assembly language exposes the state of a computer more directly than most high-level programming languages.

A small algorithm can require explicit decisions about:

- where data resides
- which register contains each value
- which memory address is accessed
- how many bytes an element occupies
- how a condition is represented
- which instruction changes control flow
- where a return address is stored
- which values must survive a procedure call

That explicitness is the central educational value of assembly programming.
