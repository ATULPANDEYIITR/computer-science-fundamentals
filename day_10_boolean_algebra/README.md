# Boolean algebra

## Topic introduction

Boolean algebra is the mathematical system used to represent and manipulate logical values. Classical Boolean algebra has two possible values:

- `0` represents false
- `1` represents true

Boolean algebra provides the foundation for digital logic, computer hardware, programming conditions, control systems, databases, computer architecture, embedded systems, and many areas of computer science.

The Python script develops Boolean algebra from basic Boolean values and logical operators to truth tables, Boolean identities, logic-gate implementations, circuit construction, adders, multiplexers, decoders, bitwise operations, Boolean-function verification, Karnaugh-map concepts, and practical decision logic.

The script also connects mathematical Boolean expressions with the way a digital circuit can be represented in a tool such as Logisim.

## Boolean values

A Boolean variable can contain one of two classical values:

- `True`
- `False`

Python represents these values with the built-in `bool` type.

Boolean values are commonly used to represent conditions such as:

- whether a user is authenticated
- whether an account is active
- whether a value is valid
- whether a permission exists
- whether a machine should run
- whether a transaction is allowed

Python also has the concept of truthiness. Objects such as non-empty strings and non-zero numbers can be interpreted as true in conditional expressions even though they are not themselves Boolean objects.

This distinction is important when strict Boolean input validation is required.

## Basic Boolean operators

The three fundamental Boolean operations are AND, OR, and NOT.

### AND

AND produces true only when every required input is true.

Mathematical notation:

`A · B`

Python:

`A and B`

Truth table:

| A | B | A AND B |
|---|---|---------|
| 0 | 0 | 0 |
| 0 | 1 | 0 |
| 1 | 0 | 0 |
| 1 | 1 | 1 |

AND is useful when several conditions must simultaneously be satisfied.

For example, an authorization condition may require both authentication and permission.

### OR

OR produces true when at least one input is true.

Mathematical notation:

`A + B`

Python:

`A or B`

Truth table:

| A | B | A OR B |
|---|---|--------|
| 0 | 0 | 0 |
| 0 | 1 | 1 |
| 1 | 0 | 1 |
| 1 | 1 | 1 |

OR is useful when multiple alternative conditions can independently produce a successful result.

### NOT

NOT reverses a Boolean value.

Mathematical notation:

`A'`

Python:

`not A`

| A | NOT A |
|---|-------|
| 0 | 1 |
| 1 | 0 |

NOT is particularly important for representing exclusions, such as "account is not locked" or "emergency stop is not active."

## XOR

XOR means exclusive OR.

It produces true when the inputs are different.

| A | B | A XOR B |
|---|---|---------|
| 0 | 0 | 0 |
| 0 | 1 | 1 |
| 1 | 0 | 1 |
| 1 | 1 | 0 |

In Python, XOR for Boolean values can be represented by:

`A != B`

XOR is fundamental to binary addition, parity calculations, error detection, comparison logic, and many digital circuits.

The script implements XOR directly and also constructs it using AND, OR, and NOT:

`(A OR B) AND NOT(A AND B)`

## Derived gates

Several important logic gates are derived from the fundamental operations.

### NAND

NAND means NOT-AND:

`NOT(A AND B)`

NAND is true except when both inputs are true.

### NOR

NOR means NOT-OR:

`NOT(A OR B)`

NOR is true only when both inputs are false.

### XNOR

XNOR is the complement of XOR:

`NOT(A XOR B)`

XNOR is true when the inputs are equal.

| A | B | NAND | NOR | XNOR |
|---|---|------|-----|------|
| 0 | 0 | 1 | 1 | 1 |
| 0 | 1 | 1 | 0 | 0 |
| 1 | 0 | 1 | 0 | 0 |
| 1 | 1 | 0 | 0 | 1 |

## Truth tables

A truth table lists every possible combination of Boolean inputs and the corresponding output of a Boolean function.

For `n` independent Boolean variables, the number of combinations is:

`2^n`

Therefore:

| Variables | Combinations |
|-----------|--------------|
| 1 | 2 |
| 2 | 4 |
| 3 | 8 |
| 4 | 16 |
| 10 | 1,024 |
| 20 | 1,048,576 |
| 30 | 1,073,741,824 |

The exponential growth is one of the main limitations of exhaustive truth-table analysis.

Truth tables are particularly useful for:

- understanding a logic function
- checking circuit behavior
- proving equivalence between small expressions
- finding incorrect gate connections
- testing digital circuits
- deriving canonical Boolean forms

## Boolean expressions

A Boolean expression combines Boolean variables and operators.

For example:

`F = (A AND B) OR C`

can be represented in Python as:

`F = (A and B) or C`

Parentheses are important because they explicitly define the intended grouping.

Python's Boolean operator precedence is:

1. `not`
2. `and`
3. `or`

Therefore:

`A or B and C`

is interpreted as:

`A or (B and C)`

rather than:

`(A or B) and C`

For complex expressions, explicit parentheses improve readability and reduce the chance of logical errors.

## Comparison operators

Python comparison expressions produce Boolean values.

Examples include:

- `==`
- `!=`
- `<`
- `<=`
- `>`
- `>=`

For example:

`age >= 18`

returns either `True` or `False`.

Comparison expressions can be combined with Boolean operators:

`age >= 18 and has_id`

This makes Boolean algebra directly relevant to everyday programming.

## Boolean algebra laws

Boolean algebra provides formal identities for manipulating expressions.

### Identity laws

`A + 0 = A`

`A · 1 = A`

In programming terms:

- `A OR False = A`
- `A AND True = A`

### Null or domination laws

`A + 1 = 1`

`A · 0 = 0`

Thus:

- `A OR True` is always true
- `A AND False` is always false

### Idempotent laws

`A + A = A`

`A · A = A`

Repeating the same Boolean condition does not change the result.

### Complement laws

`A + A' = 1`

`A · A' = 0`

A value OR its complement is always true, while a value AND its complement is always false.

### Double negation

`(A')' = A`

Applying NOT twice restores the original value.

### Commutative laws

`A + B = B + A`

`A · B = B · A`

The order of operands does not affect AND or OR.

### Associative laws

`(A + B) + C = A + (B + C)`

`(A · B) · C = A · (B · C)`

Grouping can be changed without changing the result.

### Distributive laws

`A · (B + C) = A·B + A·C`

and:

`A + B·C = (A+B)·(A+C)`

Boolean algebra has two forms of distributive law, unlike ordinary arithmetic where multiplication distributes over addition but addition does not distribute over multiplication in the same Boolean sense.

### Absorption laws

`A + A·B = A`

`A·(A+B) = A`

These laws eliminate redundant conditions.

The script verifies these laws exhaustively by testing all possible Boolean combinations.

## De Morgan's laws

De Morgan's laws are among the most important Boolean transformations.

The first law is:

`NOT(A AND B) = NOT A OR NOT B`

The second law is:

`NOT(A OR B) = NOT A AND NOT B`

These laws are useful when moving NOT operations through Boolean expressions and when converting between different gate structures.

They are also important when designing circuits using NAND or NOR gates.

The script verifies both laws for every possible two-input combination.

## Boolean expression equivalence

Two Boolean expressions are equivalent when they produce the same output for every possible input combination.

For small expressions, exhaustive truth-table comparison provides a direct way to verify equivalence.

For example:

`A AND (A OR B)`

is equivalent to:

`A`

The script evaluates both expressions for every possible combination of `A` and `B` and confirms that their outputs always match.

This provides a practical method for testing proposed Boolean simplifications.

## Simplification

Boolean simplification reduces an expression while preserving its logical behavior.

Consider:

`AB + A'B`

Factor `B`:

`B(A + A')`

Using the complement law:

`A + A' = 1`

Therefore:

`B(1) = B`

So:

`AB + A'B = B`

Simplification can reduce the number of gates and logic levels required to implement a circuit.

The script verifies the original and simplified forms through exhaustive truth-table comparison.

## Consensus theorem

The consensus theorem states:

`AB + A'C + BC = AB + A'C`

The `BC` term is redundant in this expression.

Removing unnecessary terms can reduce circuit complexity.

The script verifies the theorem for every possible combination of three Boolean variables.

## Sum-of-products

A Sum-of-Products, or SOP, expression is an OR of product terms.

For example:

`AB + A'C`

contains two AND terms joined by OR.

Canonical SOP uses minterms. A minterm contains every variable exactly once, either complemented or uncomplemented.

For three variables, there are eight possible minterms:

`m0` through `m7`

The script maps truth-table combinations to minterm indices and identifies which minterms produce an output of `1`.

SOP representations are important in digital logic because they provide a systematic way to translate a truth table into a Boolean expression.

## Product-of-sums

A Product-of-Sums, or POS, expression is an AND of sum terms.

For example:

`(A+B)(A'+C)`

contains OR terms multiplied together through AND.

Canonical POS is based on maxterms, which correspond to input combinations for which the Boolean function is `0`.

SOP and POS provide complementary ways to represent the same Boolean function.

## Universal gates

NAND and NOR are universal gates.

A universal gate is capable of constructing any Boolean function using only that gate type.

### NAND implementation

NOT can be constructed as:

`A NAND A`

AND can be constructed by NANDing the NAND result with itself.

OR can be constructed using De Morgan's law:

`A OR B = NAND(NAND(A,A), NAND(B,B))`

### NOR implementation

NOT can be constructed as:

`A NOR A`

OR can be constructed by NORing the NOR result with itself.

AND can be constructed through De Morgan's law:

`A AND B = NOR(NOR(A,A), NOR(B,B))`

Universal gates are important in digital circuit design because they allow complex logic to be built from a single basic gate family.

## Logic gates as Python classes

The script defines an abstract `LogicGate` concept and implementations for:

- AND
- OR
- NOT
- XOR

This demonstrates an important programming relationship: a digital circuit can be modeled as a collection of components with defined inputs and outputs.

A gate can be treated as a callable object, allowing circuit descriptions to resemble the structure of actual logic networks.

## Combinational circuits

A combinational circuit produces an output based only on its current inputs.

Typical examples include:

- adders
- multiplexers
- decoders
- encoders
- comparators
- arithmetic circuits
- parts of arithmetic logic units

The script represents a combinational circuit as a composition of Boolean functions.

For example:

`F = (A AND B) OR C`

can be implemented through an AND operation followed by an OR operation.

## Half adder

A half adder adds two one-bit values.

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
|---|---|-----|-------|
| 0 | 0 | 0 | 0 |
| 0 | 1 | 1 | 0 |
| 1 | 0 | 1 | 0 |
| 1 | 1 | 0 | 1 |

The half adder demonstrates how Boolean operations directly implement binary arithmetic.

## Full adder

A full adder adds three one-bit values:

- A
- B
- Carry-in

It produces:

- Sum
- Carry-out

A full adder can be constructed from two half adders and an OR operation.

This is the fundamental building block for larger binary adders.

## Ripple-carry addition

Multiple full adders can be connected so that the carry output of one position becomes the carry input of the next position.

The script implements binary addition using full-adder logic rather than simply converting the entire binary strings to Python integers.

This demonstrates how arithmetic can be constructed from Boolean operations.

A ripple-carry design is simple but has a propagation-delay limitation because each carry may need to travel through several stages.

## Multiplexer

A multiplexer selects one input from multiple available inputs.

For a two-to-one multiplexer:

- `D0` is selected when `S = 0`
- `D1` is selected when `S = 1`

The Boolean expression is:

`Y = (NOT S AND D0) OR (S AND D1)`

Multiplexers are widely used in processors, data paths, communication systems, and digital switching networks.

## Decoder

A decoder converts an encoded input into one of several output signals.

A two-to-four decoder has:

- two input bits
- four outputs

For every valid input combination, exactly one output is active.

The script implements all four output conditions using Boolean expressions.

Decoders are commonly used in address selection, memory systems, instruction decoding, and digital control systems.

## Comparators

A one-bit comparator can determine whether:

- A is greater than B
- A equals B
- A is less than B

The equality condition can be implemented using XNOR.

The greater-than condition is:

`A AND NOT B`

The less-than condition is:

`NOT A AND B`

Larger digital comparators can be constructed from smaller comparison circuits.

## Bitwise Boolean operations

Python provides bitwise operators for integer values:

- `&` for bitwise AND
- `|` for bitwise OR
- `^` for bitwise XOR
- `~` for bitwise NOT
- `<<` for left shift
- `>>` for right shift

These operators are different from:

- `and`
- `or`
- `not`

For example:

`5 = 0101`

`3 = 0011`

Therefore:

`5 & 3 = 0001`

which is decimal `1`.

Bitwise operations are fundamental to:

- binary manipulation
- processor operations
- network masks
- permissions
- embedded systems
- device registers
- compression
- low-level programming

## Logical versus bitwise operations

Logical operations operate on conditions and use short-circuit evaluation.

Bitwise operations manipulate individual bits of integer representations.

For example:

`True and False`

is a logical operation.

`5 & 3`

is a bitwise operation.

Confusing these operators is a common programming mistake.

## Fixed-width bitwise NOT

Mathematical Boolean circuits normally operate on a defined number of bits.

Python integers are not restricted to a fixed width, so Python's `~` operator can produce results that appear different from a simple fixed-width binary complement.

For example, a four-bit complement of:

`0101`

is:

`1010`

The script implements a fixed-width NOT operation by applying a mask.

This distinction is important when modeling hardware behavior in software.

## Bit masks

A bit mask uses individual bits to represent independent Boolean flags.

For example:

- bit 0 = READ
- bit 1 = WRITE
- bit 2 = EXECUTE

A permission set can then be represented by one integer.

Bitwise OR adds a flag:

`permissions |= FLAG`

Bitwise AND tests a flag:

`permissions & FLAG`

A flag can be removed using an appropriate complement mask.

Bit masks are efficient because many Boolean states can be stored in a compact integer representation.

## Short-circuit evaluation

Python's `and` and `or` operators use short-circuit evaluation.

For AND:

If the left side is false, Python does not need to evaluate the right side.

For OR:

If the left side is true, Python does not need to evaluate the right side.

This behavior can improve performance and can also be used to safely guard operations.

For example:

`number != 0 and 100 / number > 1`

prevents the division from being attempted when `number` is zero.

Short-circuit behavior should be considered when Boolean expressions contain function calls or other expressions with side effects.

## Boolean truth tables and computational complexity

Truth-table generation has exponential complexity.

For `n` variables, exhaustive enumeration requires:

`O(2^n)`

This is practical for small Boolean functions but becomes expensive for larger functions.

For example, 30 variables already produce more than one billion combinations.

For large logic systems, alternative methods may be required, including symbolic representations and specialized logic-synthesis techniques.

## Karnaugh maps

A Karnaugh map, or K-map, is a graphical Boolean simplification technique.

The important principles include:

- each cell corresponds to a minterm
- neighboring cells differ in one variable
- groups contain powers of two cells
- groups should generally be as large as possible
- groups can wrap around map edges
- groups may overlap
- variables that change within a group are eliminated
- variables that remain constant form the simplified term

K-maps use Gray-code ordering so adjacent cells differ by only one variable.

For two-bit Gray-code ordering:

`00, 01, 11, 10`

The script calculates Hamming distances to demonstrate the one-bit adjacency property.

K-maps are particularly useful for small Boolean functions. They become cumbersome as the number of variables grows.

## Don't-care conditions

A don't-care condition is an input state for which the output is irrelevant or the state is guaranteed not to occur.

It is often represented as `X`.

During simplification, a don't-care condition can sometimes be treated as either `0` or `1` if that produces a simpler circuit.

This must be based on a valid system assumption. A state should not be declared a don't-care merely because it is inconvenient.

A common example involves invalid BCD combinations. Four bits can represent sixteen binary values, while standard decimal BCD uses only ten valid combinations.

The six remaining combinations can sometimes be treated as don't-care states when the circuit specification guarantees that they will never occur.

## Boolean function classification

The script classifies Boolean functions into three broad categories.

### Tautology

A tautology is always true.

Example:

`A OR NOT A`

### Contradiction

A contradiction is always false.

Example:

`A AND NOT A`

### Contingent function

A contingent function is true for some inputs and false for others.

XOR is an example.

Classification can be performed exhaustively for small functions.

## Boolean function equivalence

A function can be tested against another implementation by evaluating both on every possible input combination.

This is useful for:

- verifying circuit implementations
- validating simplifications
- testing alternative gate designs
- debugging Logisim circuits
- checking refactored program conditions

For small functions, exhaustive verification is highly reliable because every input combination is tested.

## Input sensitivity

An input is influential for a particular assignment when changing that input changes the function's output.

This concept is related to Boolean sensitivity and Boolean derivatives.

It helps analyze which inputs actually affect a circuit under particular conditions.

For example, in a majority function, changing an input may or may not change the output depending on the states of the other inputs.

## Monotone Boolean functions

A Boolean function is monotone increasing when changing an input from `0` to `1` cannot cause the output to change from `1` to `0`.

AND and OR are monotone increasing functions.

XOR is not monotone.

The script checks this property through exhaustive comparison of ordered input assignments.

## Functions as Boolean components

The script treats Boolean functions as first-class Python objects.

This allows a generic function to receive another Boolean function as an argument.

The approach demonstrates how logic components can be represented programmatically and composed into larger systems.

This abstraction is useful for:

- testing
- simulation
- circuit modeling
- reusable logic components
- automated verification

## Logisim relationship

Logisim represents digital logic graphically.

A Boolean circuit can generally be understood as:

`Inputs → Gates → Intermediate signals → Output`

For example:

`F = (A AND B) OR (NOT C)`

can be constructed using:

- input pins for A, B, and C
- an AND gate
- a NOT gate
- an OR gate
- wires connecting the components
- an output pin

The Python implementation represents the same logical behavior using functions.

The conceptual correspondence is:

| Logisim concept | Python representation |
|------------------|------------------------|
| Input pin | Function parameter |
| Wire | Variable |
| Logic gate | Function or class |
| Intermediate wire | Intermediate variable |
| Output pin | Function return value |
| Truth table | Generated Python table |
| Circuit testing | Exhaustive function testing |

A useful circuit-development method is to first define the Boolean equation, derive the truth table, construct the circuit, and then compare the circuit output against the expected truth table.

## Combinational versus sequential logic

The examples in the script primarily represent combinational logic.

Combinational logic depends only on current inputs.

Sequential logic introduces state or memory. Its output can depend on previous events as well as current inputs.

Examples associated with sequential logic include:

- latches
- flip-flops
- registers
- counters
- finite-state machines

The distinction is important because a simple Boolean expression is not sufficient to describe a stateful system.

## Logic hazards and propagation delay

Mathematical Boolean algebra describes logical relationships but does not automatically describe physical timing.

Real digital circuits have:

- propagation delay
- fan-in
- fan-out
- power consumption
- wiring delay
- signal integrity constraints

Two expressions can be logically equivalent but have different hardware implementations.

Different signal paths may also have different propagation delays. When multiple inputs change, temporary incorrect intermediate states can produce glitches.

These effects are called hazards and are particularly important in hardware design.

## Security considerations

Boolean conditions frequently control security-sensitive decisions.

Examples include:

`authenticated AND has_permission`

and:

`verified AND account_active`

Important practices include:

- use explicit security conditions
- distinguish authentication from authorization
- test both allowed and denied cases
- avoid accidental use of OR where AND is required
- use parentheses for complex conditions
- validate inputs where Boolean type matters
- make failure conditions explicit
- avoid relying solely on generic truthiness for authorization decisions

Boolean correctness does not by itself guarantee application security. The surrounding authentication, authorization, input validation, state management, and system design must also be correct.

## Debugging Boolean expressions

Complex Boolean expressions can be difficult to debug when written as one long condition.

The script demonstrates exposing intermediate signals.

For example:

`signal_1 = A AND B`

`signal_2 = NOT C`

`signal_3 = signal_1 OR signal_2`

`output = NOT signal_3`

Breaking an expression into intermediate signals makes it easier to identify which part of a circuit is producing an unexpected value.

The same approach can be applied in Logisim by observing intermediate wires and gate outputs.

## Input validation

Python considers several non-Boolean values truthy or falsy.

For example:

- `1` is truthy
- `0` is falsy
- non-empty strings are truthy
- empty strings are falsy

This is convenient for general programming but may be inappropriate for a circuit model that specifically requires Boolean inputs.

The script includes strict validation that accepts actual `bool` values and rejects values such as integer `1`.

This distinction is useful when correctness depends on the exact input type.

## Empty Boolean collections

Python has defined behavior for empty collections:

`all([])` returns `True`.

`any([])` returns `False`.

These results are mathematically consistent with empty conjunction and disjunction, but an application-level logic-gate API may reasonably reject empty input because a physical gate specification may require at least one input.

The script demonstrates this distinction between language behavior and application design.

## Three-valued and multi-valued logic

Classical Boolean algebra has two values only:

`0` and `1`

Real digital and information systems can involve states such as:

- unknown
- uninitialized
- high impedance
- invalid
- don't care

Some hardware and database systems therefore use logic models that extend beyond two-valued Boolean algebra.

A don't-care condition is not the same as an ordinary third Boolean value. It represents a specification condition in which either output may be acceptable.

## Practical applications

Boolean algebra appears throughout computing and digital technology.

### Programming

Conditional statements use Boolean expressions:

`if authenticated and active:`

### Databases

Database filtering uses combinations of conditions such as:

`age >= 18 AND active = true`

### Digital electronics

Logic gates form the basic building blocks of:

- processors
- memory systems
- controllers
- arithmetic units
- communication hardware

### Computer architecture

Boolean logic is used in:

- instruction decoding
- arithmetic operations
- control units
- registers
- multiplexers
- address selection

### Embedded systems

Boolean conditions can control:

- sensors
- motors
- safety systems
- hardware states
- device registers

### Networking and systems programming

Bitwise Boolean operations are used for:

- network masks
- permissions
- flags
- protocol fields
- hardware registers

### Security

Boolean conditions form part of:

- access-control decisions
- validation rules
- authentication checks
- security policies

## Common mistakes

### Confusing OR with XOR

OR is true when one or both inputs are true.

XOR is true only when the inputs differ.

### Confusing logical and bitwise operators

`and` is not the same operation as `&`.

`or` is not the same operation as `|`.

`not` is not the same operation as `~`.

### Ignoring precedence

An expression such as:

`A or B and C`

may not mean what the programmer intended.

Explicit parentheses are preferable for complex conditions.

### Overcomplicating Boolean expressions

Redundant conditions can make software and circuits harder to understand and maintain.

Boolean identities should be used to simplify expressions where appropriate.

### Assuming logical equivalence means identical hardware

Two equivalent expressions may require different numbers of gates, logic levels, wires, or physical resources.

### Treating truth tables as infinitely scalable

Truth tables grow exponentially with the number of variables.

Exhaustive enumeration is appropriate for small functions but becomes impractical for large ones.

### Misusing don't-care conditions

An input is not a don't-care merely because its behavior has not been considered.

The system specification must justify the assumption.

### Ignoring physical timing

A truth table describes logical behavior but does not reveal propagation delays or transient glitches in physical hardware.

## Performance considerations

The main computational limitation in the script is exhaustive Boolean enumeration.

For `n` variables, exhaustive evaluation requires:

`2^n`

function evaluations.

This makes truth-table-based methods practical for small Boolean functions but unsuitable for very large systems.

For larger Boolean systems, more specialized techniques can be used, such as symbolic representations, Boolean decision diagrams, SAT-based reasoning, or dedicated logic-synthesis algorithms.

For ordinary Python conditions involving only a few Boolean operations, performance is generally not the primary concern. Clarity, correctness, and maintainability are usually more important.

## Implementation considerations

A robust Boolean implementation should:

- use meaningful Boolean variable names
- use parentheses for complex expressions
- separate complicated logic into intermediate signals
- validate inputs where strict types are required
- test all combinations for small functions
- compare alternative implementations against a reference
- document important assumptions
- distinguish logical operations from bitwise operations
- consider physical hardware constraints when translating software logic into circuits

The script uses functions, classes, truth-table generators, validation functions, circuit models, and assertions to demonstrate these implementation principles.

## Testing and verification

Boolean systems are particularly suitable for exhaustive testing when the number of inputs is small.

The script verifies:

- Boolean algebra identities
- De Morgan's laws
- absorption
- distributive laws
- consensus theorem
- XOR implementations
- XNOR implementations
- NAND-only circuits
- NOR-only circuits
- half adders
- full adders
- binary addition
- circuit equivalence

For a small Boolean function, exhaustive testing provides complete coverage of its possible input combinations.

For larger systems, exhaustive testing becomes computationally expensive, so additional formal or symbolic methods may be necessary.

## Real-world relevance

Boolean algebra provides the conceptual connection between high-level logical decisions and low-level digital hardware.

A programmer may write:

`authenticated and active`

A digital designer may construct:

`A AND B`

A circuit simulator may display:

`Input → AND gate → Output`

A processor ultimately implements Boolean operations using physical electronic components.

The mathematical rules remain the same even though the representation changes between programming languages, circuit diagrams, logic simulators, and physical hardware.
