# Boolean simplification

## Topic introduction

Boolean simplification is the process of transforming a Boolean expression into an equivalent expression that is logically simpler, while preserving its output for every possible input combination.

Boolean algebra provides the mathematical rules used to perform these transformations. In digital electronics, these rules are used to simplify logic circuits, reduce gate requirements, decrease the number of literals, and potentially improve area, power consumption, and propagation delay.

The Python study script develops the subject progressively. It begins with Boolean values and truth tables, then establishes the fundamental Boolean identities, explains De Morgan's laws, develops symbolic simplification, constructs canonical forms, and introduces Quine-McCluskey minimization. It also connects the mathematical concepts with logic gates, majority circuits, half adders, and full adders.

The central principle is that simplification must preserve logical equivalence. An expression that looks shorter is useful only when it produces exactly the same output for every relevant input combination.

## Boolean values

Boolean algebra operates on two logical values:

- `0` represents false.
- `1` represents true.

A Boolean variable can therefore have only two possible states.

For example, if `A` is a Boolean variable:

`A = 0`

or

`A = 1`

A Boolean expression combines variables and constants using logical operators.

The three fundamental operations are:

- AND
- OR
- NOT

The script also demonstrates XOR, XNOR, and implication because they are closely related to Boolean expressions and circuit design.

## Boolean operators

### AND

AND produces `1` only when every input is `1`.

The two-variable truth table is:

| A | B | A · B |
|---|---|-------|
| 0 | 0 | 0 |
| 0 | 1 | 0 |
| 1 | 0 | 0 |
| 1 | 1 | 1 |

In Python, Boolean AND is represented by `and` when working with Boolean values and by `&` in the symbolic expression classes created in the script.

Mathematically:

`A · B`

can also be written as:

`AB`

### OR

OR produces `1` when at least one input is `1`.

| A | B | A + B |
|---|---|-------|
| 0 | 0 | 0 |
| 0 | 1 | 1 |
| 1 | 0 | 1 |
| 1 | 1 | 1 |

The plus symbol in Boolean algebra represents OR, not ordinary arithmetic addition.

### NOT

NOT reverses the value of its operand.

| A | A' |
|---|----|
| 0 | 1 |
| 1 | 0 |

The complement can be represented using a prime symbol:

`A'`

or using an overbar:

`Ā`

The Python script represents symbolic NOT using the `Not` expression class and the `~` operator.

## XOR and XNOR

XOR, or exclusive OR, is true when the inputs are different.

`A ⊕ B = A'B + AB'`

Its truth table is:

| A | B | A ⊕ B |
|---|---|-------|
| 0 | 0 | 0 |
| 0 | 1 | 1 |
| 1 | 0 | 1 |
| 1 | 1 | 0 |

XNOR is the complement of XOR.

`A ⊙ B = AB + A'B'`

XNOR is true when the inputs are equal.

These relationships are important because apparently specialized logical operations can be represented using fundamental Boolean operations.

## Truth tables

A truth table lists the output of a Boolean function for every possible input combination.

For `n` independent Boolean variables, the number of input combinations is:

`2^n`

Therefore:

| Variables | Rows |
|-----------|------|
| 1 | 2 |
| 2 | 4 |
| 3 | 8 |
| 4 | 16 |
| 5 | 32 |
| 10 | 1,024 |
| 20 | 1,048,576 |

Truth tables are exact and conceptually simple. They are particularly useful for verifying Boolean identities.

Their limitation is exponential growth. A function of 30 variables would require more than one billion input rows for exhaustive enumeration.

The script provides reusable functions for generating and printing truth tables and uses exhaustive evaluation to verify Boolean identities.

## Boolean identities

Boolean identities are equations that are true for every valid Boolean assignment.

They are the fundamental rules used to transform expressions.

### Identity laws

The identity laws state:

`A + 0 = A`

and

`A · 1 = A`

OR with zero does not change the value.

AND with one does not change the value.

### Domination laws

The domination laws are:

`A + 1 = 1`

and

`A · 0 = 0`

OR with one always produces one.

AND with zero always produces zero.

These laws are also called null laws in some treatments.

### Idempotent laws

The idempotent laws are:

`A + A = A`

and

`A · A = A`

Repeating the same Boolean condition does not change the result.

This is different from ordinary arithmetic. In ordinary arithmetic, `A + A` is `2A`. In Boolean algebra, `A + A` is simply `A`.

### Complement laws

The complement laws are:

`A + A' = 1`

and

`A · A' = 0`

A variable and its complement cannot both be false, so their OR is always true.

They cannot both be true, so their AND is always false.

### Involution law

Double complementation returns the original value:

`(A')' = A`

This is called the involution law.

## Commutative laws

Boolean AND and OR are commutative.

For OR:

`A + B = B + A`

For AND:

`AB = BA`

The order of operands does not affect the result.

## Associative laws

OR and AND are also associative.

For OR:

`A + (B + C) = (A + B) + C`

For AND:

`A(BC) = (AB)C`

This allows groups of the same operation to be reorganized without changing the result.

Associativity should not be confused with distributivity. Associativity changes grouping, while distributivity changes the structural relationship between different operators.

## Distributive laws

Boolean algebra has two distributive laws.

The first is familiar from ordinary algebra:

`A(B + C) = AB + AC`

The second is particularly important because it does not behave like ordinary arithmetic:

`A + BC = (A + B)(A + C)`

Both are valid Boolean identities.

The second form is one reason Boolean algebra can transform between sum-of-products and product-of-sums representations.

## Absorption laws

The absorption laws are:

`A + AB = A`

and

`A(A + B) = A`

The first says that once `A` is already present in an OR expression, the additional condition `AB` cannot make the expression true when `A` is false.

The second is the dual relationship.

Absorption is one of the most useful simplification rules because it can remove entire terms without expansion.

For example:

`A + AB + AC`

contains `A` as a direct term.

Both `AB` and `AC` are already covered whenever `A` is true, so the expression reduces to:

`A`

## De Morgan's laws

De Morgan's laws describe how complementation interacts with AND and OR.

The first law is:

`(A + B)' = A'B'`

The second law is:

`(AB)' = A' + B'`

For more than two variables:

`(A + B + C)' = A'B'C'`

and:

`(ABC)' = A' + B' + C'`

The transformation has two simultaneous effects:

- OR changes to AND.
- AND changes to OR.
- Every operand is complemented.

A common error is to complement each operand while leaving the operator unchanged.

Incorrect:

`(A + B)' = A' + B'`

Correct:

`(A + B)' = A'B'`

Similarly:

`(AB)' = A' + B'`

De Morgan's laws are also fundamental in gate conversion, particularly when implementing logic with NAND or NOR gates.

## NAND and NOR relationships

NAND is the complement of AND:

`NAND(A,B) = (AB)'`

Using De Morgan's law:

`(AB)' = A' + B'`

NOR is the complement of OR:

`NOR(A,B) = (A+B)'`

Using De Morgan's law:

`(A+B)' = A'B'`

These relationships allow Boolean expressions to be transformed into equivalent circuits using different gate families.

NAND and NOR are particularly significant because complete digital logic systems can be constructed using either gate type as a universal gate.

## Consensus theorem

The consensus theorem is:

`AB + A'C + BC = AB + A'C`

The term `BC` is called the consensus term.

It is redundant because whenever `BC` is true, either `A` is true or `A'` is true:

- If `A = 1`, then `AB` is true because `B = 1`.
- If `A = 0`, then `A'C` is true because `C = 1`.

Therefore `BC` cannot create an output condition that is not already covered by the other two terms.

The dual form is:

`(A+B)(A'+C)(B+C) = (A+B)(A'+C)`

Consensus is useful when simplifying multi-term SOP and POS expressions.

## The theorem A + A'B

Another highly useful identity is:

`A + A'B = A + B`

Its dual is:

`A(A' + B) = AB`

This identity often appears when an expression contains a variable and a conditional term controlled by its complement.

For example:

`A + A'BC`

can be transformed into:

`A + BC`

This is a powerful alternative to blindly expanding an expression.

## Boolean duality

Boolean identities have a dual structure.

To obtain the dual of an identity:

`+ ↔ ·`

`0 ↔ 1`

while leaving variables unchanged.

For example:

`A + 0 = A`

has the dual:

`A · 1 = A`

Similarly:

`A + AB = A`

has the dual:

`A(A+B) = A`

The two Boolean distributive laws are also duals:

`A(B+C) = AB+AC`

and:

`A+BC = (A+B)(A+C)`

Duality is useful because a known identity can provide insight into another valid identity without independently deriving it from scratch.

## Symbolic Boolean expressions

Evaluating an expression for a particular input is different from manipulating the expression itself.

For example:

`(A+B)C'`

is a symbolic expression.

To simplify it, a program must understand its structure.

The script therefore defines symbolic classes for:

- constants
- variables
- NOT
- AND
- OR

An expression such as:

`(A+B)C'`

can be represented conceptually as:

`AND(OR(A,B), NOT(C))`

This structure is commonly described as an abstract syntax tree.

The symbolic representation makes it possible to inspect operands and apply algebraic transformations without evaluating the expression first.

## Structural simplification

The script implements a teaching-oriented symbolic simplifier.

It recognizes rules such as:

`A + 0 = A`

`A · 1 = A`

`A + 1 = 1`

`A · 0 = 0`

`A + A = A`

`A · A = A`

`A + A' = 1`

`A · A' = 0`

`(A')' = A`

`A + AB = A`

The simplifier also handles selected distributive patterns.

A critical engineering distinction is that a local symbolic simplifier is not necessarily a globally optimal Boolean minimizer.

An expression can be locally simplified while another sequence of transformations produces a smaller result.

## Equivalence checking

Two expressions are Boolean-equivalent when they produce the same output for every possible input combination.

For example:

`A + AB`

and:

`A`

are equivalent.

The script verifies this by constructing the union of their variables and testing every possible assignment.

For `n` variables, exhaustive verification requires up to:

`2^n`

evaluations.

This makes exhaustive truth-table verification exact but unsuitable for very large variable counts.

## Sum of Products

A Sum of Products, or SOP, is an OR of product terms.

Example:

`AB + A'C + BC`

The expression contains three product terms:

`AB`

`A'C`

`BC`

These terms are connected by OR.

SOP form is particularly useful for describing which input conditions should produce a `1`.

## Product of Sums

A Product of Sums, or POS, is an AND of sum terms.

Example:

`(A+B)(A'+C)(B+C)`

The three sum terms are:

`(A+B)`

`(A'+C)`

`(B+C)`

They are connected by AND.

POS form is particularly useful when describing the input conditions under which a function must remain `0`.

## Canonical forms

A canonical Boolean form follows a strict structure.

For a function involving variables `A`, `B`, and `C`, every canonical product term contains all three variables exactly once.

For example:

`A'BC`

`AB'C`

`ABC'`

are canonical product terms.

Every canonical sum term also contains every variable exactly once.

For example:

`(A+B+C')`

`(A+B'+C)`

`(A'+B+C)`

are canonical sum terms.

Canonical forms are standardized representations. They are not necessarily the most compact representations.

This distinction is important:

`canonical`

does not mean:

`minimal`

## Minterms

A minterm is a product term that is equal to `1` for exactly one input combination.

For variables `A`, `B`, and `C`, consider the input:

`A=1, B=0, C=1`

The corresponding minterm is:

`AB'C`

It is true only for that particular combination.

For three variables, there are eight possible minterms:

| Index | Binary | Minterm |
|-------|--------|---------|
| 0 | 000 | A'B'C' |
| 1 | 001 | A'B'C |
| 2 | 010 | A'BC' |
| 3 | 011 | A'BC |
| 4 | 100 | AB'C' |
| 5 | 101 | AB'C |
| 6 | 110 | ABC' |
| 7 | 111 | ABC |

The decimal index corresponds directly to the binary representation of the input combination.

## Minterm notation

A Boolean function can be represented using sigma notation:

`F(A,B,C) = Σm(1,2,5,7)`

This means the function is `1` for minterms 1, 2, 5, and 7.

The script can construct the canonical SOP directly from such minterm indices.

## Maxterms

A maxterm is a sum term that is equal to `0` for exactly one input combination.

The construction is opposite to the minterm convention.

For a particular input:

`A=1, B=0, C=1`

the corresponding maxterm is:

`(A' + B + C')`

At that input:

`A' = 0`

`B = 0`

`C' = 0`

so the entire sum is zero.

Every other input combination makes at least one literal true.

## Maxterm notation

A Boolean function can also be represented using product notation:

`F(A,B,C) = ΠM(0,3,4,6)`

This means the function is zero at maxterms 0, 3, 4, and 6.

Canonical SOP identifies the rows where the function is one.

Canonical POS identifies the rows where the function is zero.

For a function with `n` variables, the complete set of minterm indices is:

`0 through 2^n - 1`

The minterms where the function is one and the maxterms where it is zero are complementary sets.

## Conversion between binary indices and Boolean assignments

The script provides utilities for converting:

`decimal index → binary assignment`

and:

`Boolean assignment → decimal index`

For example, with variables:

`A, B, C`

index `5` is:

`101`

so:

`A = 1`

`B = 0`

`C = 1`

The corresponding minterm is:

`AB'C`

The index system depends on the variable ordering. Changing the variable order changes the interpretation of the binary positions.

This is an important practical detail when comparing truth tables, canonical expressions, or minimization results.

## Canonical SOP construction

To construct canonical SOP:

1. Evaluate the function for every input combination.
2. Identify every row whose output is `1`.
3. Construct the minterm for each such row.
4. OR all those minterms together.

For example, if:

`F = 1`

for minterms:

`1, 2, 5, 7`

then:

`F = Σm(1,2,5,7)`

and its canonical SOP is the OR of those four minterms.

## Canonical POS construction

To construct canonical POS:

1. Evaluate the function for every input combination.
2. Identify every row whose output is `0`.
3. Construct the corresponding maxterm for each row.
4. AND all those maxterms together.

The resulting POS is equivalent to the canonical SOP.

The two forms differ syntactically but represent the same Boolean function.

## Canonical versus reduced expressions

Consider a majority function:

`F = 1`

when at least two of `A`, `B`, and `C` are one.

The canonical SOP is:

`A'BC + AB'C + ABC' + ABC`

This contains four three-literal product terms.

It simplifies to:

`AB + AC + BC`

The reduced expression has fewer literals and a simpler structure.

Both expressions are logically equivalent.

This demonstrates why canonical representation and minimization have different purposes.

Canonical forms provide a systematic representation.

Reduced forms seek lower implementation complexity.

## Quine-McCluskey minimization

Quine-McCluskey is a systematic Boolean minimization method.

It is particularly useful for small and medium-sized Boolean functions when a tabular, algorithmic minimization process is desired.

The method works with minterms represented as binary patterns.

For example:

`100`

`101`

differ only in the last position.

They can be combined into:

`10-`

The dash indicates that the corresponding variable is no longer required.

If variables are:

`A B C`

then:

`10-`

represents:

`AB'`

because `C` has been eliminated.

## Implicants

An implicant is a product term that covers input combinations for which the function is permitted to be one.

For example:

`AB'`

covers all combinations where:

`A = 1`

`B = 0`

regardless of the value of other variables.

In a binary pattern:

`10-`

the dash represents the eliminated variable.

The number of fixed positions corresponds to the number of literals in the implicant.

## Prime implicants

A prime implicant cannot be expanded into a larger valid implicant without covering an input combination that is not allowed to be one.

In Quine-McCluskey minimization, repeatedly combining compatible implicants produces prime implicants.

Prime implicants are the main candidates used to construct a minimized SOP.

## Essential prime implicants

A prime implicant is essential when it is the only prime implicant covering at least one required minterm.

Such an implicant must be included in the final cover.

The script constructs a prime-implicant chart and identifies essential prime implicants automatically.

## Prime implicant chart

The chart represents relationships between:

- required minterms
- prime implicants

Each prime implicant covers one or more minterms.

The objective is to select a set of prime implicants that covers every required minterm.

The script first selects essential prime implicants and then uses a greedy selection procedure for remaining minterms.

This distinction is important because greedy selection is not a universal proof of global optimality.

## Exact minimization versus heuristic minimization

Boolean minimization can become computationally difficult as the number of variables increases.

Quine-McCluskey provides a systematic method, but the number of intermediate implicants can grow rapidly.

The script therefore uses Quine-McCluskey for prime implicant generation and an explicit covering strategy.

For larger industrial designs, specialized logic synthesis methods are often preferred because they scale better.

The important engineering lesson is that the mathematically cleanest algorithm is not necessarily the most scalable implementation.

## Don't-care conditions

A don't-care condition is an input combination whose output does not constrain the implementation.

Typical examples include:

- unused state encodings
- impossible input combinations
- unused BCD codes
- hardware configurations that cannot occur

Suppose:

`Required 1s = {1,3,7}`

`Don't cares = {5}`

The minimizer is allowed to treat minterm 5 as either zero or one when forming groups.

A don't-care may therefore help create a larger implicant.

The final expression must still:

- produce `1` for every required one
- produce `0` for every required zero
- remain unrestricted on don't-care inputs

Don't-care conditions can produce significantly smaller circuits.

## Simplification and circuit cost

A reduced Boolean expression is often associated with a simpler circuit, but "simpler" must be defined.

Possible cost measures include:

- number of literals
- number of AND gates
- number of OR gates
- number of NOT gates
- total gate count
- gate fan-in
- propagation delay
- silicon area
- dynamic power
- static power
- wiring complexity

For example, reducing literal count can be beneficial, but a transformation that increases gate depth may increase propagation delay.

Therefore, Boolean minimization is an optimization problem whose objective depends on the implementation technology.

## Gate count and structural cost

The script includes a structural cost estimator that counts:

- AND nodes
- OR nodes
- NOT nodes
- literals

These values are useful for comparing expressions conceptually.

They are not a physical hardware timing model.

A real implementation must account for:

- the available standard-cell library
- maximum gate fan-in
- gate delays
- wire delays
- inversion availability
- buffering
- loading
- power characteristics

Two expressions with the same number of Boolean operations may therefore have different physical characteristics.

## Majority function

The three-input majority function produces one when at least two inputs are one.

Its canonical SOP is:

`A'BC + AB'C + ABC' + ABC`

The minimized form is:

`AB + AC + BC`

This function appears in several digital logic contexts, including carry generation.

The expression demonstrates the value of simplification because four three-literal terms can be replaced by three two-literal terms.

## Half adder

A half adder adds two one-bit binary values.

Inputs:

`A`

`B`

Outputs:

`Sum`

`Carry`

The equations are:

`Sum = A XOR B`

`Carry = AB`

Expanding XOR:

`Sum = A'B + AB'`

Therefore a half adder can be described entirely with AND, OR, and NOT operations.

The carry expression is already a simple AND operation.

## Full adder

A full adder includes a carry input.

Inputs:

`A`

`B`

`Cin`

Outputs:

`Sum`

`Cout`

The sum is:

`Sum = A XOR B XOR Cin`

The carry output can be written as:

`Cout = AB + ACin + BCin`

The carry expression is a three-input majority function.

This connects Boolean simplification directly to binary arithmetic hardware.

## Common simplification patterns

Several patterns occur frequently.

### Complementary terms

`AB + AB' = A`

Factor `A`:

`A(B+B')`

Use the complement law:

`B+B' = 1`

Therefore:

`A·1 = A`

### Absorption

`A + AB = A`

The second term is unnecessary.

### Factoring

`AB + AC = A(B+C)`

Factoring can reduce repeated literals and may reduce circuit complexity.

### Conditional simplification

`A + A'B = A+B`

This identity can be especially useful when expressions contain complementary control conditions.

## Common mistakes

### Treating Boolean addition as arithmetic

Boolean:

`A + A = A`

Arithmetic intuition would incorrectly suggest:

`2A`

Boolean OR does not behave like ordinary numerical addition.

### Incorrect De Morgan transformation

Incorrect:

`(A+B)' = A'+B'`

Correct:

`(A+B)' = A'B'`

### Confusing minterms and maxterms

A minterm is associated with exactly one input row where the term is `1`.

A maxterm is associated with exactly one input row where the term is `0`.

### Confusing canonical and minimal form

A canonical expression deliberately contains every variable in each canonical term.

A minimal expression removes unnecessary literals or terms.

Canonical does not mean optimized.

### Assuming fewer symbols always means faster hardware

A shorter expression can still have:

- greater gate depth
- larger fan-in
- more difficult routing
- unfavorable technology mapping

Boolean simplification is a logical optimization, while physical circuit optimization has additional constraints.

### Ignoring variable ordering

Minterm indices depend on variable order.

For:

`A,B,C`

index `5` represents:

`101`

But if the ordering changes, the meaning of the index changes.

This is especially important when implementing canonical-form utilities.

## Edge cases

Several constant cases deserve special attention.

For OR:

`A + 0 = A`

`A + 1 = 1`

For AND:

`A · 0 = 0`

`A · 1 = A`

For complements:

`A + A' = 1`

`A · A' = 0`

For double complements:

`(A')' = A`

A Boolean function that is never true has canonical SOP:

`0`

A Boolean function that is always true has canonical SOP containing every minterm, which simplifies to:

`1`

The script explicitly demonstrates these cases.

## Validation of simplification

A reliable simplification workflow should verify that a transformed expression is equivalent to the original.

The script uses exhaustive truth-table comparison.

For each assignment:

`original output == simplified output`

must hold.

If even one input combination differs, the simplification is incorrect.

This is particularly valuable when transformations become complicated or when implementing an automated simplifier.

## Testing Boolean identities

The script includes a regression test suite covering identities such as:

`A + 0 = A`

`A · 1 = A`

`A + 1 = 1`

`A · 0 = 0`

`A + A = A`

`A · A = A`

`A + A' = 1`

`A · A' = 0`

`(A')' = A`

It also tests:

`(A+B)' = A'B'`

`(AB)' = A'+B'`

`A+AB = A`

`A(A+B) = A`

`A(B+C) = AB+AC`

`A+BC = (A+B)(A+C)`

Automated identity testing is useful because a symbolic simplifier can produce syntactically plausible but logically incorrect results if its transformation rules are implemented incorrectly.

## Implementation considerations

The script deliberately separates several responsibilities.

Truth-table evaluation handles numerical Boolean behavior.

Symbolic expression classes represent Boolean structure.

Simplification routines transform expression trees.

Canonical-form functions construct standardized representations.

Quine-McCluskey functions perform systematic minimization.

Equivalence functions validate logical correctness.

This separation makes the implementation easier to inspect and test.

The symbolic representation uses immutable data classes. This makes expression nodes stable and allows structural representations to be used safely as dictionary keys or set-like identifiers through their textual patterns.

## Performance considerations

Truth-table enumeration has exponential complexity:

`O(2^n)`

for `n` variables, ignoring the internal cost of evaluating each expression.

This is manageable for small Boolean functions but becomes expensive quickly.

Quine-McCluskey also faces rapid growth in intermediate implicants. Its systematic nature is valuable for learning and small functions, but it is not a universal solution for large industrial circuits.

The script therefore demonstrates both exhaustive verification and algorithmic minimization while making their scalability limitations explicit.

## Security considerations

Boolean simplification itself is not generally a security-sensitive operation, but implementation choices can matter when Boolean expressions are supplied as external input.

An application should not directly execute arbitrary text as programming language expressions merely to evaluate Boolean logic.

A production parser should:

- tokenize input explicitly
- validate operators
- validate identifiers
- reject unexpected syntax
- limit expression size
- avoid arbitrary code execution
- handle malformed expressions safely

The symbolic classes in the script avoid evaluating arbitrary Python source. They operate on explicitly constructed expression objects.

## Design considerations for production systems

A production Boolean simplifier may need capabilities beyond the teaching implementation, including:

- robust lexical parsing
- operator precedence
- parenthesis validation
- canonical serialization
- expression hashing
- memoization
- common-subexpression detection
- exact minimization
- heuristic minimization
- technology-aware optimization
- gate-library mapping
- timing optimization
- area optimization
- power optimization

For larger logic systems, a truth table may itself become impractical.

Alternative representations can include:

- binary decision diagrams
- algebraic decision diagrams
- symbolic representations
- logic networks
- specialized synthesis data structures

The appropriate representation depends on the size and characteristics of the Boolean function.

## Practical relevance

Boolean simplification is directly relevant to:

- digital logic design
- combinational circuits
- sequential circuit design
- arithmetic circuits
- processors
- memory controllers
- embedded systems
- finite-state machines
- FPGA logic
- ASIC synthesis
- control systems
- hardware verification

The same Boolean function may be represented in several mathematically equivalent ways, and choosing an appropriate representation can have substantial consequences for implementation cost.

## Relationship between mathematical and physical optimization

Boolean algebra operates at the logical level.

Physical circuit design introduces additional constraints.

For example, consider two equivalent expressions:

`F = AB + AC`

and:

`F = A(B+C)`

They are logically equivalent.

Depending on the available gate library, one implementation may be preferable.

If a technology provides efficient multi-input gates, one representation may map naturally.

If only certain gate types are available, another representation may require fewer transformations.

Therefore, algebraic simplification is an important foundation for digital design, but physical optimization requires technology-specific analysis.

## What the Python script demonstrates

The complete script contains executable demonstrations of:

- Boolean values
- AND, OR, NOT
- XOR and XNOR
- implication
- truth-table generation
- Boolean identity verification
- identity laws
- domination laws
- idempotent laws
- complement laws
- involution
- commutativity
- associativity
- distributivity
- absorption
- De Morgan's laws
- consensus theorem
- Boolean duality
- symbolic expression trees
- structural simplification
- equivalence checking
- canonical SOP
- canonical POS
- minterms
- maxterms
- decimal and binary index conversion
- prime implicants
- essential prime implicants
- prime-implicant charts
- Quine-McCluskey minimization
- don't-care conditions
- expression-cost comparison
- NAND and NOR relationships
- majority logic
- half adders
- full adders
- edge cases
- validation
- automated regression testing

The implementations are designed so that the mathematical rules are demonstrated through executable behavior rather than treated only as definitions.

## Core notation reference

| Boolean concept | Standard notation | Meaning |
|---|---|---|
| AND | `AB` or `A·B` | Both conditions must be true |
| OR | `A+B` | At least one condition is true |
| NOT | `A'` | Complement of the variable |
| XOR | `A⊕B` | Inputs are different |
| XNOR | `A⊙B` | Inputs are equal |
| Minterm | `m_i` | Product term true for exactly one row |
| Maxterm | `M_i` | Sum term false for exactly one row |
| SOP | Sum of Products | OR of AND terms |
| POS | Product of Sums | AND of OR terms |
| Canonical SOP | `Σm(...)` | Sum of all required minterms |
| Canonical POS | `ΠM(...)` | Product of all required maxterms |
| Prime implicant | Pattern with fixed and eliminated variables | Non-expandable valid implicant |
| Don't-care | `X` or `d` | Input condition that does not constrain the result |

## Important identities reference

`A + 0 = A`

`A · 1 = A`

`A + 1 = 1`

`A · 0 = 0`

`A + A = A`

`A · A = A`

`A + A' = 1`

`A · A' = 0`

`(A')' = A`

`A + B = B + A`

`AB = BA`

`A + (B+C) = (A+B)+C`

`A(BC) = (AB)C`

`A(B+C) = AB+AC`

`A+BC = (A+B)(A+C)`

`A+AB = A`

`A(A+B) = A`

`(A+B)' = A'B'`

`(AB)' = A'+B'`

`A + A'B = A+B`

`A(A'+B) = AB`

`AB + A'C + BC = AB + A'C`
