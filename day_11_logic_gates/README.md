# Logic gates

## Introduction

Logic gates are fundamental building blocks of digital electronics and computer systems. They operate on binary values and produce binary outputs according to precisely defined logical rules.

Binary logic has two primary states:

- `0` represents LOW, OFF, or FALSE.
- `1` represents HIGH, ON, or TRUE.

The principal logic gates covered in this study are:

- AND
- OR
- NOT
- NAND
- NOR
- XOR
- XNOR

The Python script implements each gate directly, generates truth tables, verifies Boolean identities, constructs compound circuits, demonstrates universal-gate implementations, and applies the gates to adders, multiplexers, comparators, parity logic, and simple decision systems.

## Binary logic

Digital systems commonly represent information using two discrete states. Although physical implementations may use voltage ranges, the logical abstraction treats the states as binary values.

For a system containing `n` independent binary inputs, the number of possible input combinations is:

`2^n`

For example:

| Number of inputs | Possible combinations |
|---:|---:|
| 1 | 2 |
| 2 | 4 |
| 3 | 8 |
| 4 | 16 |
| 10 | 1,024 |

This relationship is important when constructing truth tables and performing exhaustive verification.

## Boolean algebra

Boolean algebra is the mathematical framework used to describe binary logic.

The basic operations are:

| Operation | Common notation | Meaning |
|---|---|---|
| AND | `A · B`, `AB` | Both conditions are true |
| OR | `A + B` | At least one condition is true |
| NOT | `A'`, `¬A` | Complement of a value |
| XOR | `A ⊕ B` | Inputs differ |
| XNOR | `(A ⊕ B)'` | Inputs are equal |

Boolean notation can resemble arithmetic notation, but Boolean operations are not ordinary arithmetic operations.

For example:

- Arithmetic: `1 + 1 = 2`
- Boolean OR: `1 OR 1 = 1`

The Python implementation represents Boolean results as integer bits, `0` and `1`, so the behavior is explicit and suitable for digital-logic demonstrations.

## AND gate

The AND gate produces `1` only when every input is `1`.

For two inputs:

`Y = A · B`

Truth table:

| A | B | AND |
|---:|---:|---:|
| 0 | 0 | 0 |
| 0 | 1 | 0 |
| 1 | 0 | 0 |
| 1 | 1 | 1 |

The AND operation models requirements where multiple conditions must be satisfied simultaneously.

For example:

`Access = ValidCard AND ValidPIN`

Access is permitted only when both conditions are true.

## OR gate

The OR gate produces `1` when at least one input is `1`.

For two inputs:

`Y = A + B`

Truth table:

| A | B | OR |
|---:|---:|---:|
| 0 | 0 | 0 |
| 0 | 1 | 1 |
| 1 | 0 | 1 |
| 1 | 1 | 1 |

OR is useful when multiple alternative conditions can independently cause an outcome.

For example:

`EmergencyAccess = Administrator OR EmergencyOverride`

## NOT gate

The NOT gate has one input and produces its complement.

`Y = A'`

Truth table:

| A | NOT A |
|---:|---:|
| 0 | 1 |
| 1 | 0 |

NOT is also called an inverter.

Unlike AND, OR, NAND, NOR, XOR, and XNOR, NOT is a unary operation because it operates on one input.

## NAND gate

NAND means NOT-AND.

`Y = (A · B)'`

The AND result is inverted.

Truth table:

| A | B | NAND |
|---:|---:|---:|
| 0 | 0 | 1 |
| 0 | 1 | 1 |
| 1 | 0 | 1 |
| 1 | 1 | 0 |

NAND is especially important because it is a universal gate.

## NOR gate

NOR means NOT-OR.

`Y = (A + B)'`

The OR result is inverted.

Truth table:

| A | B | NOR |
|---:|---:|---:|
| 0 | 0 | 1 |
| 0 | 1 | 0 |
| 1 | 0 | 0 |
| 1 | 1 | 0 |

NOR is also a universal gate.

## XOR gate

XOR means exclusive OR.

For two inputs, XOR produces `1` when the inputs are different.

`Y = A ⊕ B`

It can also be expressed using AND, OR, and NOT:

`A ⊕ B = A'B + AB'`

Truth table:

| A | B | XOR |
|---:|---:|---:|
| 0 | 0 | 0 |
| 0 | 1 | 1 |
| 1 | 0 | 1 |
| 1 | 1 | 0 |

A common mistake is to confuse XOR with OR.

OR asks:

> Is at least one input `1`?

XOR asks:

> Are the two inputs different?

Consequently:

`OR(1, 1) = 1`

but:

`XOR(1, 1) = 0`

XOR is particularly useful in binary addition, parity logic, difference detection, and comparison circuits.

## XNOR gate

XNOR is the complement of XOR.

`Y = (A ⊕ B)'`

For two inputs, XNOR produces `1` when the inputs are equal.

Truth table:

| A | B | XNOR |
|---:|---:|---:|
| 0 | 0 | 1 |
| 0 | 1 | 0 |
| 1 | 0 | 0 |
| 1 | 1 | 1 |

XNOR is therefore useful as an equality detector.

For two bits:

`A XNOR B = 1`

exactly when:

`A = B`

## Complete two-input truth table

The seven fundamental gates can be compared as follows:

| A | B | AND | OR | NOT A | NAND | NOR | XOR | XNOR |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 | 1 | 1 | 1 | 0 | 1 |
| 0 | 1 | 0 | 1 | 1 | 1 | 0 | 1 | 0 |
| 1 | 0 | 0 | 1 | 0 | 1 | 0 | 1 | 0 |
| 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 1 |

NOT has one input, so its truth table is independent of the two-input table.

## Multi-input logic

Logic operations can be extended to multiple inputs.

For AND:

`Y = A · B · C`

The output is `1` only when all inputs are `1`.

For OR:

`Y = A + B + C`

The output is `1` when at least one input is `1`.

For three binary inputs, there are:

`2^3 = 8`

possible combinations.

The Python script generates these combinations explicitly.

## Boolean identities

Boolean algebra provides identities that help analyze and simplify circuits.

### Identity laws

`A · 1 = A`

`A + 0 = A`

### Null laws

`A · 0 = 0`

`A + 1 = 1`

### Idempotent laws

`A · A = A`

`A + A = A`

### Complement laws

`A · A' = 0`

`A + A' = 1`

### Double negation

`(A')' = A`

### Commutative laws

`A · B = B · A`

`A + B = B + A`

### Associative laws

`(A · B) · C = A · (B · C)`

`(A + B) + C = A + (B + C)`

XOR is also associative:

`(A ⊕ B) ⊕ C = A ⊕ (B ⊕ C)`

### Distributive laws

`A · (B + C) = AB + AC`

`A + BC = (A + B)(A + C)`

These identities are useful when transforming a Boolean expression into an equivalent circuit.

## De Morgan's laws

De Morgan's laws are fundamental to Boolean logic.

The first law is:

`(AB)' = A' + B'`

The second law is:

`(A + B)' = A'B'`

The Python script verifies these laws for every possible two-input combination.

These relationships are especially important when converting between NAND, NOR, AND, OR, and NOT implementations.

## Universal gates

A universal gate is a gate type that can be used alone to construct other fundamental gates.

NAND and NOR are both universal.

### NOT using NAND

`NOT(A) = NAND(A, A)`

The same signal is connected to both NAND inputs.

### AND using NAND

First calculate:

`X = NAND(A, B)`

Then invert it:

`AND(A, B) = NAND(X, X)`

### OR using NAND

Using De Morgan's law:

`A + B = (A'B')'`

Therefore:

`OR(A, B) = NAND(NAND(A, A), NAND(B, B))`

### NOT using NOR

`NOT(A) = NOR(A, A)`

### OR using NOR

First calculate:

`X = NOR(A, B)`

Then invert it:

`OR(A, B) = NOR(X, X)`

### AND using NOR

Using De Morgan's law:

`AB = (A' + B')'`

Therefore:

`AND(A, B) = NOR(NOR(A, A), NOR(B, B))`

Universal gates are important in digital circuit design because they allow complete logic systems to be constructed from a single gate family.

## XOR implementations

XOR can be constructed using basic gates:

`A ⊕ B = A'B + AB'`

This means:

1. Invert `A`.
2. AND `A'` with `B`.
3. Invert `B`.
4. AND `A` with `B'`.
5. OR the two results.

The Python script also implements XOR using NAND gates only.

A NAND-only implementation is:

`X1 = NAND(A, B)`

`X2 = NAND(A, X1)`

`X3 = NAND(B, X1)`

`XOR = NAND(X2, X3)`

The script verifies that these alternative implementations produce identical results for all two-input combinations.

## Compound logic circuits

Real digital systems are built by combining multiple gates.

For example:

`Y = (A AND B) OR (NOT C)`

The circuit can be divided into intermediate signals:

`X1 = A AND B`

`X2 = NOT C`

`Y = X1 OR X2`

Using named intermediate signals is useful for implementation and debugging because each stage can be inspected separately.

Another example in the script is:

`Y = ((A OR B) AND (NOT C)) XOR D`

Complex Boolean expressions should generally be decomposed into clear intermediate stages when they are being implemented or debugged.

## XOR and parity

XOR has an important parity property.

For multiple inputs:

`A XOR B XOR C ...`

the result is:

- `1` when an odd number of inputs are `1`
- `0` when an even number of inputs are `1`

For example:

`0 XOR 0 XOR 1 = 1`

because one input is `1`.

`1 XOR 1 XOR 0 = 0`

because two inputs are `1`.

This property makes XOR useful in parity generation and parity checking.

## Half adder

A half adder adds two one-bit binary values.

Inputs:

- `A`
- `B`

Outputs:

- Sum
- Carry

The equations are:

`Sum = A XOR B`

`Carry = A AND B`

Truth table:

| A | B | Sum | Carry |
|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 |
| 0 | 1 | 1 | 0 |
| 1 | 0 | 1 | 0 |
| 1 | 1 | 0 | 1 |

The `1 + 1` case demonstrates why two output bits are necessary:

`1 + 1 = 10₂`

The Sum is `0`, while the Carry is `1`.

## Full adder

A full adder extends the half adder by including a carry input.

Inputs:

- `A`
- `B`
- `Cin`

Outputs:

- Sum
- Carry-out

The equations are:

`Sum = A XOR B XOR Cin`

`Cout = AB + Cin(A XOR B)`

A full adder can be constructed from:

- Two half adders
- One OR gate

The Python implementation follows this structure rather than relying on ordinary integer addition.

The relationship can be verified numerically:

`A + B + Cin = Sum + 2 × Cout`

## Ripple-carry addition

Multi-bit binary addition can be constructed by connecting full adders.

The carry generated at one bit position becomes the carry input of the next position.

For example, the structure conceptually processes:

- Least significant bit
- Carry propagation
- Next bit
- Carry propagation
- Higher bits

This is called a ripple-carry arrangement because the carry signal propagates from one stage to another.

The Python implementation performs binary addition using the logical full-adder operations rather than Python's built-in integer addition.

For example:

`1010 + 0011 = 1101`

The implementation also verifies its result against Python's normal integer representation.

## Multiplexer

A multiplexer, commonly abbreviated as MUX, selects one input from multiple available inputs.

A 2-to-1 multiplexer has:

- `D0`
- `D1`
- Select signal `S`
- Output `Y`

Its Boolean equation is:

`Y = S'D0 + SD1`

When:

`S = 0`

the output is:

`Y = D0`

When:

`S = 1`

the output is:

`Y = D1`

The Python implementation directly models these two terms and combines them using OR.

Multiplexers are fundamental components in data routing and digital control systems.

## Multi-bit equality comparison

XNOR can be extended from individual bits to complete binary values.

Suppose two four-bit values are:

`A3 A2 A1 A0`

and:

`B3 B2 B1 B0`

Each corresponding pair can be compared using XNOR.

The complete equality condition is:

`(A3 XNOR B3) AND`

`(A2 XNOR B2) AND`

`(A1 XNOR B1) AND`

`(A0 XNOR B0)`

The final result is `1` only when every corresponding bit is equal.

The Python script implements this approach for binary strings.

## Compound decision logic

Logic gates can represent simple decision rules.

For example:

`Alarm = DoorOpen AND SystemArmed`

The alarm activates only when both conditions are true.

Another example is:

`EmergencyAccess = Administrator OR EmergencyOverride`

This demonstrates how Boolean expressions can represent conditions in digital control systems.

The same basic principles appear in hardware control circuits, embedded systems, processors, and other digital systems.

## Gate properties

The script tests several mathematical properties.

### Commutativity

For the two-input gates demonstrated:

`AND(A, B) = AND(B, A)`

`OR(A, B) = OR(B, A)`

`NAND(A, B) = NAND(B, A)`

`NOR(A, B) = NOR(B, A)`

`XOR(A, B) = XOR(B, A)`

`XNOR(A, B) = XNOR(B, A)`

### Associativity

AND, OR, and XOR are associative.

For example:

`(A XOR B) XOR C = A XOR (B XOR C)`

NAND, NOR, and XNOR do not generally have this property.

The distinction matters when restructuring Boolean expressions or designing circuits.

## Input validation

A digital-logic implementation should distinguish binary values from arbitrary Python truthy or falsy objects.

For example, Python considers a non-empty string such as `"0"` to be truthy.

Therefore:

`bool("0")`

evaluates to `True`.

That is not the intended interpretation of the binary digit `0`.

The script uses explicit validation so that logic inputs must be:

- `0`
- `1`
- `False`
- `True`

Values such as `2`, `-1`, `"0"`, `"1"`, `0.5`, and `None` are rejected.

This is an important implementation practice when simulating digital systems.

## Edge cases

Important edge cases include:

- No inputs supplied to a multi-input operation
- Non-binary inputs
- Empty binary strings
- Binary strings containing characters other than `0` and `1`
- Binary values of unequal length
- Missing or excessive gate arguments
- Confusing Boolean OR with arithmetic addition
- Confusing XOR with OR

Explicit validation prevents invalid data from silently producing misleading results.

## Truth-table verification

Truth tables provide an exhaustive way to verify small Boolean circuits.

For `n` binary inputs, there are:

`2^n`

possible input combinations.

For a two-input gate there are only four combinations, so exhaustive verification is trivial.

For a ten-input circuit there are:

`2^10 = 1,024`

combinations.

For twenty inputs:

`2^20 = 1,048,576`

combinations.

The exponential growth means exhaustive testing becomes increasingly expensive as the number of independent inputs increases.

For larger systems, more advanced verification approaches may be required.

## Testing methodology

The Python script contains assertions that verify:

- Fundamental truth tables
- NAND-derived gates
- NOR-derived gates
- XOR implementations
- XNOR behavior
- De Morgan's laws
- Half-adder arithmetic
- Full-adder arithmetic
- Multiplexer selection
- Binary equality comparison
- Ripple-carry addition

Exhaustive testing is particularly appropriate for small logic functions because the complete input space can be evaluated.

## Object-oriented representation

The script also models gates using Python classes.

A base `LogicGate` class defines a common interface.

Specialized classes represent:

- `AndGate`
- `OrGate`
- `NotGate`
- `NandGate`
- `NorGate`
- `XorGate`
- `XnorGate`

This demonstrates how logic gates can be represented as reusable software components.

The callable interface allows a gate object to be used similarly to a function.

This approach becomes useful when representing larger circuits as collections of interconnected components.

## Combinational logic

Combinational logic produces an output based only on current inputs.

Examples include:

- Adders
- Comparators
- Multiplexers
- Encoders
- Decoders

The same input state produces the same logical output, assuming ideal Boolean behavior.

The compound circuits in the Python script are examples of combinational logic.

## Sequential logic

Sequential logic differs because it incorporates state or memory.

Examples include:

- Latches
- Flip-flops
- Registers
- Counters
- Memory elements

A simple Boolean gate does not itself provide memory. Storage requires appropriate circuit structures, generally involving feedback and controlled state transitions.

This distinction is fundamental in digital system design.

## Real hardware considerations

The Python functions represent ideal Boolean behavior. Physical gates have additional characteristics that are not captured by these simple functions.

Important hardware considerations include:

### Propagation delay

A physical gate requires a finite amount of time for an input change to affect its output.

### Rise and fall time

Signals do not normally transition instantaneously between voltage levels.

### Fan-in

Fan-in describes the number of inputs handled by a gate or logic structure.

### Fan-out

Fan-out concerns how many downstream inputs a signal can reliably drive.

### Noise margins

Physical systems must tolerate some degree of unwanted electrical disturbance without interpreting a signal incorrectly.

### Power consumption

Digital gates consume energy, including dynamic energy associated with signal transitions and other forms of circuit power consumption.

### Area

Physical circuit implementations occupy silicon or board area.

### Supply voltage

Real digital circuits operate within specified voltage ranges rather than abstract mathematical `0` and `1` values.

## Propagation delay and hazards

A Boolean expression describes logical behavior, but it does not fully describe physical timing behavior.

When signals travel through different paths with different delays, a circuit can temporarily produce an unintended transition.

These transient behaviors are commonly called glitches or hazards.

Therefore:

`Boolean correctness != complete hardware timing correctness`

A production hardware design must consider both logical correctness and physical timing.

## Performance considerations

Individual Boolean gate evaluation in this Python implementation is effectively constant-time because each gate performs a fixed number of operations.

The major scalability issue occurs when generating exhaustive truth tables.

The number of combinations grows exponentially:

`2^n`

Consequently, exhaustive simulation is appropriate for small circuits but may become computationally expensive for larger circuits.

The choice of verification method should therefore depend on circuit size and complexity.

## Security considerations

Logic gates themselves are fundamental mathematical and hardware concepts rather than security mechanisms.

They do, nevertheless, appear inside security-related hardware and systems, including:

- Access-control logic
- Authentication hardware
- Secure processors
- Cryptographic circuits
- Error-detection mechanisms
- Hardware control systems

A Boolean rule such as:

`ValidCard AND ValidPIN`

can model a simple authorization condition, but a production authentication system requires considerably more protection than a Boolean expression alone.

Security requirements include reliable input validation, correct state management, resistance to fault conditions, secure implementation, and appropriate protection of sensitive information.

## Common mistakes

### Confusing OR with XOR

OR returns `1` when at least one input is `1`.

XOR returns `1` when the two inputs are different.

Therefore:

`OR(1, 1) = 1`

while:

`XOR(1, 1) = 0`

### Treating Boolean addition as arithmetic addition

Boolean OR is not ordinary integer addition.

`1 OR 1 = 1`

not `2`.

### Forgetting inversion

NAND is the inverse of AND.

NOR is the inverse of OR.

### Misunderstanding XNOR

XNOR is not another form of OR. It detects equality for two inputs.

### Assuming arbitrary Python truthiness is binary validation

Python accepts many values as truthy or falsy. Digital-logic simulation should validate binary inputs explicitly.

### Ignoring physical timing

A mathematically correct Boolean expression does not automatically guarantee correct behavior in physical hardware.

## Important distinctions

| Concept | Meaning |
|---|---|
| AND | All required conditions are true |
| OR | At least one condition is true |
| XOR | Inputs differ |
| XNOR | Inputs are equal |
| NAND | Inverted AND |
| NOR | Inverted OR |
| Combinational logic | Output depends on current inputs |
| Sequential logic | Output depends on current inputs and state |
| Boolean model | Abstract logical behavior |
| Physical circuit | Logical behavior plus electrical and timing characteristics |

## Real-world relevance

Logic gates form the foundation of digital computing.

They are used directly or indirectly in:

- Central processing units
- Arithmetic logic units
- Memory systems
- Digital controllers
- Microcontrollers
- Microprocessors
- Graphics processors
- Communication hardware
- Embedded systems
- Digital sensors
- Comparators
- Adders
- Multiplexers
- Decoders
- Encoders
- Error-detection circuits
- Programmable logic systems
- Finite-state machines

Large digital systems are constructed by combining relatively simple logical operations into increasingly complex structures.

The Python implementation demonstrates this progression from an individual gate to compound Boolean circuits, adders, multiplexers, parity logic, binary comparators, and multi-bit arithmetic.
