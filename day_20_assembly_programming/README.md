<!-- File: README.md -->
# MIPS Assembly Control Flow and Procedure Programming Lab

## Project purpose

This repository is a practical study project for MIPS assembly programming using the **MARS** and **RARS** simulators.

The project focuses on the core mechanisms required to write structured MIPS programs:

- sequential execution
- conditional branches
- comparison operations
- `if` and `if-else` logic
- `while` loops
- `for`-style loops
- counted loops
- nested loops
- functions and procedures
- argument passing
- return values
- stack frames
- saving and restoring registers
- procedure calls with `jal`
- returning with `jr`
- recursion
- array processing
- input validation
- error handling
- modular assembly program design
- debugging with registers and memory
- MARS and RARS execution

The repository uses small programs to introduce individual mechanisms and an integrated program to demonstrate how these mechanisms work together.

## Requirements

The examples are written for the MIPS instruction set used by MARS and RARS.

Required software:

- Java Runtime Environment
- MARS or RARS
- Git
- Python 3.11 or later for the repository validation tests

The assembly programs do not require a traditional compiler. They are loaded directly into MARS or RARS.

## MARS and RARS

MARS and RARS are educational MIPS simulators.

MARS is commonly used for the MIPS32 instruction set and provides a graphical debugger, register view, memory view, breakpoints, and syscall support.

RARS is a newer educational environment commonly used for RISC-V and also provides MIPS-related educational workflows depending on the configured version. The programs in this repository intentionally use the common MIPS instructions and basic console syscalls supported by the intended MIPS execution environment.

For the most predictable results, use a MIPS-enabled MARS or RARS configuration.

## Repository structure

`src/01_conditions.s` demonstrates comparisons and conditional branches.

`src/02_loops.s` demonstrates counted loops, `while`-style loops, and nested loops.

`src/03_functions.s` demonstrates procedures, arguments, return values, and `jal`.

`src/04_stack.s` demonstrates stack allocation, saved registers, local variables, and stack restoration.

`src/05_recursion.s` demonstrates recursive procedure calls and stack frames.

`src/06_array_processing.s` demonstrates arrays, indexed memory access, loops, functions, and validation.

`src/07_integrated_lab.s` combines conditions, loops, functions, stack operations, procedure calls, arrays, and input validation into one program.

`src/include/syscalls.inc` documents the console syscall interface used by the examples.

`tests/test_assembly_sources.py` validates repository structure and performs static checks on the assembly programs.

`scripts/check_sources.py` provides a command-line source validation tool.

`.github/workflows/ci.yml` runs the Python validation suite automatically.

`docs/architecture.md` explains how the examples are organized.

`docs/mips-fundamentals.md` explains the underlying assembly concepts.

`docs/control-flow.md` explains branches, loops, labels, and control-flow translation.

`docs/procedures-and-stack.md` explains procedure calls and stack frames.

`docs/mars-rars.md` explains simulator usage and debugging.

## MIPS register model used by this project

The examples primarily use the following registers.

| Register | Conventional purpose |
|---|---|
| `$zero` | Always contains zero |
| `$v0` | Return value and syscall number |
| `$a0` | First procedure argument and syscall argument |
| `$a1` | Second procedure argument |
| `$a2` | Third procedure argument |
| `$a3` | Fourth procedure argument |
| `$t0-$t9` | Temporary registers |
| `$s0-$s7` | Saved registers |
| `$sp` | Stack pointer |
| `$fp` | Frame pointer |
| `$ra` | Return address |
| `$gp` | Global pointer |
| `$k0-$k1` | Reserved for operating-system use |

The project follows the usual convention that a procedure preserves `$s` registers that it modifies.

Temporary `$t` registers may be changed by a called procedure.

## Fundamental instruction groups

### Loading constants

`li $t0, 10` loads an immediate value into `$t0`.

`move $t1, $t0` copies one register value to another.

`la $a0, message` loads the address of a label.

### Arithmetic

`add $t0, $t1, $t2` adds two registers.

`sub $t0, $t1, $t2` subtracts one register from another.

`addi $t0, $t0, 1` adds an immediate value.

`mul $t0, $t1, $t2` multiplies two registers.

`div $t1, $t2` performs integer division.

`mflo $t0` retrieves the quotient.

`mfhi $t0` retrieves the remainder.

### Comparison

`beq $t0, $t1, label` branches when the values are equal.

`bne $t0, $t1, label` branches when the values are different.

`slt $t0, $t1, $t2` sets `$t0` to one when `$t1 < $t2`, otherwise zero.

Pseudo-instructions such as `blt`, `bgt`, `ble`, and `bge` may be available in MARS and RARS. The examples prefer basic instructions where practical so that the underlying comparison mechanism remains visible.

## How high-level conditions become assembly

A high-level condition such as:

`if (x < y)`

can be represented with:

`slt $t0, $t0, $t1`

followed by:

`bne $t0, $zero, less_than`

The processor does not execute a high-level `if` statement. It changes the program counter through branch instructions.

This distinction is important when learning assembly.

## How loops work

A loop normally consists of:

1. a condition check
2. a branch that exits the loop
3. the loop body
4. an update operation
5. a branch back to the condition

For example, a conceptual loop:

`while (counter < limit)`

becomes a label followed by comparison, conditional branch, body, increment, and an unconditional jump.

The program counter therefore moves backward when the loop repeats.

## Procedure calls

A procedure is a reusable block of instructions.

A caller normally places arguments in `$a0-$a3` and executes:

`jal procedure_name`

The `jal` instruction stores the return address in `$ra`.

The procedure eventually returns with:

`jr $ra`

A procedure that itself calls another procedure must protect its own return address because another `jal` changes `$ra`.

This is why stack frames are important.

## Stack operation

The stack grows toward lower memory addresses in the conventional MIPS calling convention.

A procedure can allocate space with:

`addi $sp, $sp, -16`

and restore the stack with:

`addi $sp, $sp, 16`

A saved register can be stored with:

`sw $ra, 12($sp)`

and restored with:

`lw $ra, 12($sp)`

The exact offsets are determined by the procedure's frame layout.

## Stack frame example

A procedure may use this conceptual layout:

`0($sp)` local storage

`4($sp)` saved `$s0`

`8($sp)` saved `$s1`

`12($sp)` saved `$ra`

After allocating 16 bytes, the procedure owns those locations until it restores `$sp`.

## Arrays

MIPS memory is byte-addressed.

A 32-bit integer occupies four bytes.

For an integer array, the address of element `i` is:

`base + i * 4`

A left shift can multiply an index by four:

`sll $t1, $t0, 2`

The resulting offset can then be added to the base address.

## Input validation

Assembly does not automatically protect a program from invalid user input.

The integrated example validates values before using them.

For an input range from 1 through 100, the program checks:

- whether the value is less than 1
- whether the value is greater than 100

Invalid input is rejected before the value enters the main calculation.

## Error handling

The examples use explicit branches for invalid conditions.

For example:

- invalid array size
- invalid menu choice
- invalid numeric range
- division by zero

The programs terminate through a controlled error path instead of continuing with invalid state.

## Running an example in MARS

Open MARS and load one of the `.s` files from `src`.

Select the MIPS configuration supported by your installation.

Assemble the program.

Run the program.

Use the Registers window to observe:

- `$v0`
- `$a0`
- `$t0-$t9`
- `$s0-$s7`
- `$sp`
- `$fp`
- `$ra`

Use breakpoints on labels such as:

`loop_condition`

`loop_body`

`procedure`

`function_return`

Step through one instruction at a time to observe how the program counter and registers change.

## Running an example in RARS

Open RARS and load an assembly source file.

Assemble the program and execute it.

The same general debugging approach applies:

- inspect registers
- inspect memory
- set breakpoints
- single-step through branches
- observe `$ra`
- observe `$sp`
- inspect stack memory

The exact menu names can vary between simulator versions.

## Console syscalls

The examples use the common educational MIPS syscall interface.

| `$v0` | Operation | Argument |
|---:|---|---|
| 1 | print integer | `$a0` |
| 4 | print string | `$a0` |
| 5 | read integer | none |
| 10 | exit | none |

Example:

`li $v0, 1`

`move $a0, $t0`

`syscall`

prints the integer contained in `$t0`.

The syscall interface is a simulator service. It is not a normal MIPS processor instruction.

## Running repository validation

From the repository root:

`python -m pytest`

The tests verify:

- expected files exist
- assembly files contain valid sections
- important instructions are present
- procedure examples contain calls and returns
- stack examples allocate and restore stack space
- loop examples contain backward control flow
- the integrated program contains the required mechanisms

The tests are source-level repository checks. They do not replace execution inside MARS or RARS.

## Running the source checker directly

Run:

`python scripts/check_sources.py`

A successful run reports the number of assembly source files checked.

## Architecture

The repository uses a progressive architecture.

The first programs isolate one concept at a time.

The middle programs combine related concepts.

The integrated program uses a small menu-driven application to connect the concepts into one execution flow.

The assembly layer remains the authoritative implementation. Python is used only for repository validation, because Python is not required to execute MIPS assembly.

## Conditions and branches

A branch changes control flow.

A conditional branch has the form:

`branch condition, target`

The target is normally a label.

An unconditional jump uses:

`j target`

A function call uses:

`jal target`

A procedure return normally uses:

`jr $ra`

These mechanisms form the foundation of structured control flow in MIPS.

## Loops and complexity

A loop that visits every element of an array of `n` integers normally performs `O(n)` iterations.

A nested loop where each loop processes approximately `n` elements can perform `O(n²)` iterations.

The assembly implementation does not change the underlying algorithmic complexity.

Assembly does make individual memory accesses, arithmetic operations, branches, and register transfers explicit.

## Stack and recursion

Recursion is implemented through repeated procedure calls.

Every recursive call requires its own state.

That state can include:

- return address
- arguments
- saved registers
- local values

The stack provides storage for these call frames.

A recursive function that fails to reach a base case can continue allocating stack frames until the available stack space is exhausted.

The recursive example therefore contains an explicit base case.

## Memory safety considerations

The examples use statically allocated arrays where possible.

When an array is accessed, the index is checked before address calculation.

The project does not accept arbitrary memory addresses from users.

The assembly language itself does not provide automatic bounds checking.

A programmer must establish the bounds before performing `lw` or `sw`.

## Performance considerations

Important costs include:

- branch instructions
- memory loads and stores
- multiplication
- division
- repeated procedure calls
- unnecessary memory traffic

Register values can be accessed without a memory load, but registers are limited.

The stack is useful for preserving state but should not be used for every temporary value when registers are sufficient.

Division is generally more expensive than simple addition or subtraction on many processor designs, although simulator execution timing should not be interpreted as a hardware benchmark.

## Common mistakes

### Forgetting that `$ra` can be overwritten

A procedure that calls another procedure with `jal` must preserve its own return address.

### Forgetting to restore `$sp`

Every stack allocation must be balanced by a corresponding stack restoration.

### Using the wrong branch condition

A single reversed comparison can completely change the behavior of a loop.

### Off-by-one loop errors

Check whether the intended range is:

`0 <= i < n`

or:

`0 <= i <= n`

These are not equivalent.

### Confusing an address with a value

`la` loads an address.

`lw` loads a word from memory.

### Forgetting the word size

A 32-bit integer occupies four bytes, so array indexes normally need to be multiplied by four.

### Modifying saved registers

A procedure should restore `$s` registers that it modifies when following the standard calling convention.

### Dividing by zero

The divisor must be checked before performing division.

## Production considerations

Educational MIPS programs differ from operating-system and embedded production code.

The examples focus on explicit control flow and procedure mechanics rather than hardware-specific startup code, interrupt handling, device drivers, linker scripts, or operating-system ABIs.

For larger MIPS programs, additional concerns include:

- ABI compatibility
- register preservation
- stack alignment
- reentrancy
- memory layout
- interrupt safety
- exception handling
- calling conventions
- linker behavior
- executable format
- target processor differences

MARS and RARS abstract many of these concerns.

## Real-world applications

The concepts demonstrated here transfer directly to lower-level programming tasks such as:

- embedded systems
- firmware
- operating-system components
- compiler backends
- virtual machines
- CPU architecture education
- reverse engineering
- performance-sensitive code
- hardware-software interfaces

The exact instructions and calling conventions differ between architectures, but the concepts of control flow, procedures, registers, memory, stack frames, and calling conventions remain fundamental.

## File execution order

A useful study sequence is:

`src/01_conditions.s`

`src/02_loops.s`

`src/03_functions.s`

`src/04_stack.s`

`src/05_recursion.s`

`src/06_array_processing.s`

`src/07_integrated_lab.s`

The examples are independent programs. Assemble and execute one source file at a time.
