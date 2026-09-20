# Control flow

## Sequential execution

Without a branch or jump, instructions execute in address order.

If three instructions are stored consecutively, execution normally moves from the first to the second and then to the third.

Branches change this behavior.

## If statement

A high-level statement such as:

`if (a == b)`

can be represented by:

`beq $t0, $t1, equal`

The `equal` label marks the beginning of the true branch.

## If-else

An if-else structure needs two paths.

A common structure is:

`beq condition, true_path`

`j false_path`

`true_path:`

true instructions

`j after_if`

`false_path:`

false instructions

`after_if:`

next instructions

The unconditional jumps prevent execution from falling through into the wrong branch.

## Less-than

MIPS provides `slt` for signed less-than comparison.

Example:

`slt $t2, $t0, $t1`

sets `$t2` to one when `$t0 < $t1`.

Then:

`bne $t2, $zero, less`

branches when the comparison succeeded.

## While loop

A high-level loop:

`while (counter < limit)`

has three important components:

- condition
- body
- update

The assembly structure is:

`loop_condition:`

compare

branch to exit

`loop_body:`

body

update

jump back to condition

`loop_exit:`

This means the condition is checked before each iteration.

## Do-while loop

A do-while loop executes the body before checking the condition.

Its assembly structure places the body before the conditional branch back to the beginning.

## For loop

A for loop:

`for (i = 0; i < n; i++)`

can be transformed into:

initialization

condition label

comparison

exit branch

body

increment

jump to condition label

The CPU does not have a dedicated `for` instruction.

The compiler or programmer builds the behavior from basic instructions.

## Nested loops

A nested loop contains one loop inside another.

The outer loop controls one variable.

The inner loop runs completely for each outer iteration.

For a square `n × n` traversal, the number of body executions is approximately `n²`.

## Loop invariants

A loop invariant is a property that remains true at important points in every iteration.

For an array-sum loop, a useful invariant is:

The accumulator contains the sum of all elements already processed.

At initialization, zero elements have been processed.

After each iteration, one additional element has been included.

When the loop terminates, every intended element has been processed.

## Off-by-one errors

Consider an array with five elements.

Valid indexes are:

`0, 1, 2, 3, 4`

An incorrect condition that permits index 5 accesses memory outside the array.

The usual pattern for `n` elements is:

`0 <= index < n`

## Infinite loops

A loop becomes infinite when its exit condition can never become true.

Common causes include:

- forgetting to update the counter
- updating the wrong register
- jumping to the wrong label
- reversing the branch condition

The MARS or RARS single-step debugger makes these errors visible.

## Branch debugging

When debugging a branch:

1. inspect the compared registers
2. inspect the comparison result
3. inspect the branch instruction
4. determine whether the target label should be reached
5. step once
6. inspect the program counter

This approach is more reliable than guessing from the source code alone.
