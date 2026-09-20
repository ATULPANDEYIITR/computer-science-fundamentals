<!-- File: docs/procedures-and-stack.md -->
# Procedures and stack operations

## Procedure

A procedure is a named block of instructions that performs a specific operation.

A caller transfers control with:

`jal procedure`

The processor stores a return address in `$ra`.

The procedure returns with:

`jr $ra`

## Why `$ra` must sometimes be saved

Suppose procedure A calls procedure B.

A enters through:

`jal A`

The return address for A is placed in `$ra`.

If A executes:

`jal B`

the return address for A is replaced by the return address for B.

A therefore needs to save its original `$ra` before calling B.

The stack is a natural place to store it.

## Basic stack frame

A procedure can reserve 16 bytes:

`addi $sp, $sp, -16`

It can save `$ra` at:

`12($sp)`

and restore it later.

The frame must be released before returning:

`addi $sp, $sp, 16`

## Caller-saved and callee-saved concepts

Temporary registers are generally considered caller-saved.

A caller cannot assume that a procedure will preserve `$t0-$t9`.

Saved registers are callee-saved.

A procedure that changes an `$s` register should preserve the original value and restore it before returning.

The educational examples use this distinction consistently.

## Arguments

The first four standard arguments are passed in:

`$a0-$a3`

If more arguments are required, a larger calling convention and stack-based argument area may be needed.

The repository keeps procedures small enough to use the standard argument registers.

## Return values

A single integer return value is placed in `$v0`.

The caller must move or consume the result before making another call if the value needs to survive.

## Local variables

A local variable can live in:

- a temporary register
- a saved register
- stack memory

The appropriate choice depends on lifetime and calling requirements.

A value that must survive another procedure call should not be left only in a temporary register.

## Recursion

A recursive procedure calls itself.

Each invocation needs its own return address and state.

For factorial:

`factorial(n) = n * factorial(n - 1)`

with:

`factorial(0) = 1`

The base case stops recursion.

Each recursive invocation has a separate stack frame.

## Stack correctness

A procedure should maintain this invariant:

The stack pointer after returning must equal the stack pointer observed by the caller before the procedure call.

If a procedure allocates 16 bytes and fails to restore them, repeated calls can move the stack into unintended memory.

## Common stack mistakes

### Saving `$ra` too late

If a procedure calls another procedure before saving `$ra`, the original return address may be lost.

### Restoring into the wrong register

The register used by the rest of the procedure must match the register that was saved.

### Incorrect offset

`sw $ra, 12($sp)` must correspond to the same location used by `lw $ra, 12($sp)`.

### Unbalanced stack

A 16-byte allocation requires a 16-byte restoration.

### Recursive state corruption

Every recursive invocation needs its own saved state.

A value stored in a shared register without preservation can be overwritten by a deeper invocation.
